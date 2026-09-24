#!/usr/bin/env python3
"""Create a read-only reconciliation plan from desired and observed state."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from providers.infrastructure.manifest import load_manifest


RELEASE_CHECKS = ("contentReady", "licenseReady", "privacyReady", "secretAuditReady")


def plan_reconciliation(
    desired: dict[str, Any],
    actual: dict[str, Any] | None,
    release_gate: dict[str, Any] | None = None,
    website_gate: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if actual is None:
        return {
            "projectId": desired["project"]["id"],
            "status": "READ_REQUIRED",
            "mutationsApplied": False,
            "blockers": ["Provider actual state must be read before resource creation or update."],
            "operations": [],
        }

    github = actual.get("github") or {}
    cloudflare = actual.get("cloudflare") or {}
    builds = actual.get("builds") or {}
    desired_github = desired["github"]
    desired_cf = desired["cloudflare"]
    desired_build = desired["deployment"]
    operations: list[dict[str, str]] = []
    blockers: list[str] = []
    warnings: list[str] = []
    security_drift: list[str] = []

    def op(name: str, reason: str) -> None:
        operations.append({"operation": name, "reason": reason, "mutating": False})

    if not github.get("repositoryExists", False):
        op("create-private-repository", "Repository is absent; the create operation must explicitly set private=true.")
    elif github.get("repositoryVisibility") != desired_github["repositoryVisibility"]:
        observed = github.get("repositoryVisibility")
        wanted = desired_github["repositoryVisibility"]
        if observed == "public" and wanted == "private":
            security_drift.append("GitHub repository is public while desired state is private.")
            op("make-repository-private", "Restore the more private desired state; public copies may remain.")
            warnings.append("Restricting a repository cannot recall previously cloned, forked, cached, or downloaded copies.")
        elif observed == "private" and wanted == "public":
            if _release_gate_ok(release_gate, require_explicit_approval=True):
                op("make-repository-public", "Explicit open-source release gate passed; re-read the repository after changing visibility.")
            else:
                blockers.append("Repository publication requires explicit approval and all publicationReleaseGate checks.")

    if not cloudflare.get("workerExists", False):
        op("create-worker", "Worker is absent; create or import it from the intended repository before claiming deployment readiness.")

    access_mode = desired_cf["accessMode"]
    if access_mode == "account-wide-access":
        access_ready = cloudflare.get("accountWideProtection") is True
        if not access_ready:
            blockers.append("BOOTSTRAP_REQUIRED: account-wide Access protection is not verified.")
    else:
        access_ready = cloudflare.get("workerScopedProtection") is True
        if cloudflare.get("workerExists") and not access_ready:
            blockers.append("PROJECT_ACCESS_REQUIRED: protect the target Worker with Cloudflare Access before claiming private readiness.")
            op("protect-target-worker", "Enable Worker-scoped Cloudflare Access for production and previews, then verify anonymous denial.")
        elif not cloudflare.get("workerExists"):
            op("protect-target-worker-after-creation", "After the Worker exists, enable Worker-scoped Cloudflare Access before treating the Web publication as private.")

    if access_ready and cloudflare.get("workerExists"):
        if cloudflare.get("applicationVisibility") != desired_cf["applicationVisibility"]:
            observed = cloudflare.get("applicationVisibility")
            wanted = desired_cf["applicationVisibility"]
            if observed == "public" and wanted == "private":
                security_drift.append("Worker is anonymously reachable while desired application visibility is private.")
                if access_mode == "account-wide-access":
                    op("remove-worker-public-bypass", "Remove only the target Worker's bypass; keep account-wide Access enabled.")
                else:
                    op("protect-target-worker", "Enable Worker-scoped Access for the target Worker and verify anonymous denial.")
            elif observed == "private" and wanted == "public":
                if not _website_gate_ok(website_gate):
                    blockers.append("Website publication requires explicit approval and a passing websitePublicationGate.")
                if cloudflare.get("controlPrivateWorkerAnonymousDenied") is not True:
                    blockers.append("A control private Worker must be verified as anonymously denied before making this Worker public.")
                if not blockers:
                    if access_mode == "account-wide-access":
                        op("add-worker-public-bypass", "Add a bypass scoped only to this Worker, then verify anonymous access and the private control Worker.")
                    else:
                        op("remove-target-worker-access", "Remove only this Worker's Access protection after explicit publication approval, then verify anonymous access.")
        if cloudflare.get("previewVisibility") != desired_cf["previewVisibility"]:
            wanted = desired_cf["previewVisibility"]
            if wanted == "public":
                blockers.append("Public previews require a separate explicit approval; production visibility does not authorize them.")
            else:
                op("protect-previews", "Protect preview URLs independently from production visibility.")

    if desired_build["provider"] == "cloudflare-workers-builds":
        if not builds.get("repositoryConnectionUuid"):
            op("ensure-repository-connection", "Read the existing repository connections before creating one; reuse its stable UUID.")
        if not builds.get("productionTriggerUuid"):
            op("ensure-production-trigger", "Create only if no trigger already matches this Worker, repository, and branch.")
        elif builds.get("productionBranch") != desired_build["productionBranch"]:
            op("reconcile-production-trigger", "Patch the existing trigger to the declared production branch and verify it.")
        if desired_build["previewDeployments"] and not builds.get("previewTriggerUuid"):
            op("ensure-preview-trigger", "Create or reuse the preview trigger; its URLs must stay protected.")
    else:
        deployment_secrets = github.get("deploymentSecrets") or {}
        if not all(deployment_secrets.get(name) is True for name in ("CLOUDFLARE_API_TOKEN", "CLOUDFLARE_ACCOUNT_ID")):
            op(
                "install-project-scoped-deployment-credential",
                "Use the platform secret broker to create an account-owned token scoped to this Worker with Editor role and write it directly to GitHub Actions secrets without exposing plaintext to the model.",
            )
    status = "SECURITY_DRIFT" if security_drift else "PERMISSION_REQUIRED" if blockers else "PLAN_READY"
    return {
        "projectId": desired["project"]["id"],
        "status": status,
        "mutationsApplied": False,
        "repositoryVisibility": {"desired": desired_github["repositoryVisibility"], "actual": github.get("repositoryVisibility")},
        "applicationVisibility": {"desired": desired_cf["applicationVisibility"], "actual": cloudflare.get("applicationVisibility")},
        "previewVisibility": {"desired": desired_cf["previewVisibility"], "actual": cloudflare.get("previewVisibility")},
        "accessMode": desired_cf["accessMode"],
        "accountWideProtection": cloudflare.get("accountWideProtection"),
        "workerScopedProtection": cloudflare.get("workerScopedProtection"),
        "securityDrift": security_drift,
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys(warnings)),
        "operations": operations,
    }


def _release_gate_ok(gate: dict[str, Any] | None, require_explicit_approval: bool) -> bool:
    if not isinstance(gate, dict) or gate.get("allowed") is not True:
        return False
    if require_explicit_approval and not gate.get("approvalId"):
        return False
    checks = gate.get("checks")
    return isinstance(checks, dict) and all(checks.get(name) is True for name in RELEASE_CHECKS)


def _website_gate_ok(gate: dict[str, Any] | None) -> bool:
    return isinstance(gate, dict) and gate.get("allowed") is True and bool(gate.get("approvalId"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", nargs="?", type=Path, default=Path("project.infrastructure.json"))
    parser.add_argument("--actual", type=Path, help="JSON snapshot returned by read-only provider adapters")
    parser.add_argument("--release-gate", type=Path)
    parser.add_argument("--website-gate", type=Path)
    args = parser.parse_args(argv)
    try:
        desired = load_manifest(args.manifest)
        actual = json.loads(args.actual.read_text(encoding="utf-8")) if args.actual else None
        release_gate = json.loads(args.release_gate.read_text(encoding="utf-8")) if args.release_gate else None
        website_gate = json.loads(args.website_gate.read_text(encoding="utf-8")) if args.website_gate else None
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "CONFIGURATION_ERROR", "error": str(exc)}, indent=2))
        return 2
    report = plan_reconciliation(desired, actual, release_gate, website_gate)
    print(json.dumps(report, indent=2))
    return 0 if report["status"] in {"READ_REQUIRED", "PLAN_READY"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
