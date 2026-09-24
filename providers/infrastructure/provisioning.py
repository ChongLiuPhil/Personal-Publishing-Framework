#!/usr/bin/env python3
"""Provision a new PPF project with the minimum-human external-CI profile.

This module never creates or returns deployment credential values. When a
project-scoped Cloudflare token is needed it emits a secretBrokerRequest that a
trusted tool must execute atomically outside model/chat context.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
import urllib.error
import urllib.request

from providers.infrastructure.api import ProviderError
from providers.infrastructure.cloudflare import AccessAdapter, WorkersAdapter
from providers.infrastructure.github import GitHubAdapter
from providers.infrastructure.manifest import load_manifest


REQUIRED_SECRETS = ("CLOUDFLARE_API_TOKEN", "CLOUDFLARE_ACCOUNT_ID")


def _profile_ok(manifest: dict[str, Any]) -> bool:
    deployment = manifest.get("deployment", {})
    return (
        deployment.get("provider") == "github-actions-cloudflare-workers"
        and deployment.get("securityProfile") == "agent-provisioned-external-ci"
        and deployment.get("credentialStrategy") == "project-scoped-account-token"
        and deployment.get("secretBroker") is True
    )


class ProjectProvisioner:
    def __init__(self, github: GitHubAdapter, workers: WorkersAdapter, access: AccessAdapter):
        self.github = github
        self.workers = workers
        self.access = access

    def _read(self, manifest: dict[str, Any]) -> dict[str, Any]:
        owner = manifest["github"]["owner"]
        repository = manifest["github"]["repository"]
        worker_name = manifest["cloudflare"]["worker"]
        repo = self.github.read_repository(owner, repository)
        worker = self.workers.read_worker(worker_name)
        baseline = self.access.account_baseline()
        secrets: dict[str, bool] | None = None
        secret_error: str | None = None
        if repo is not None:
            try:
                secrets = self.github.deployment_secret_status(owner, repository)
            except ProviderError:
                secret_error = "GITHUB_SECRET_METADATA_PERMISSION_REQUIRED"
        return {
            "repository": repo,
            "worker": worker,
            "accountWideAccess": baseline is not None,
            "accountAccessAppId": baseline.get("id") if baseline else None,
            "deploymentSecrets": secrets,
            "deploymentSecretReadError": secret_error,
        }

    def plan(self, manifest: dict[str, Any]) -> dict[str, Any]:
        if not _profile_ok(manifest):
            return {"status": "UNSUPPORTED_PROFILE", "mutationsApplied": False, "operations": []}
        actual = self._read(manifest)
        operations: list[dict[str, Any]] = []
        if not actual["accountWideAccess"]:
            return {
                "status": "PLATFORM_BOOTSTRAP_REQUIRED",
                "mutationsApplied": False,
                "operations": [],
                "blocker": "ACCOUNT_WIDE_ACCESS_NOT_VERIFIED",
            }
        if actual["repository"] is None:
            operations.append({"operation": "create-private-github-repository", "mutating": False})
        if actual["worker"] is None:
            operations.append({"operation": "create-private-by-default-worker", "mutating": False})
        secrets = actual["deploymentSecrets"]
        if actual["repository"] is not None and (secrets is None or not all(secrets.values())):
            operations.append({"operation": "install-project-scoped-deployment-credential", "mutating": False})
        return {
            "status": "PLAN_READY",
            "mutationsApplied": False,
            "actual": actual,
            "operations": operations,
        }

    def apply(self, manifest: dict[str, Any]) -> dict[str, Any]:
        if not _profile_ok(manifest):
            return {"status": "UNSUPPORTED_PROFILE", "completed": []}
        if manifest["github"]["repositoryVisibility"] != "private":
            return {"status": "BLOCKED", "blocker": "NEW_PROJECT_REPOSITORY_MUST_START_PRIVATE", "completed": []}
        if manifest["cloudflare"]["applicationVisibility"] != "private":
            return {"status": "BLOCKED", "blocker": "NEW_PROJECT_WORKER_MUST_START_RESTRICTED", "completed": []}

        before = self._read(manifest)
        if not before["accountWideAccess"]:
            return {"status": "BLOCKED", "blocker": "ACCOUNT_WIDE_ACCESS_NOT_VERIFIED", "completed": []}

        owner = manifest["github"]["owner"]
        repository = manifest["github"]["repository"]
        worker_name = manifest["cloudflare"]["worker"]
        completed: list[str] = []

        repo = before["repository"]
        if repo is None:
            repo = self.github.ensure_repository(
                owner,
                repository,
                "private",
                owner_type=manifest["github"].get("ownerType", "user"),
            )
            completed.append("github.repository")

        worker = before["worker"]
        if worker is None:
            worker = self.workers.ensure_worker(worker_name)
            completed.append("cloudflare.worker")

        try:
            secret_status = self.github.deployment_secret_status(owner, repository)
        except ProviderError:
            return {
                "status": "BLOCKED",
                "blocker": "GITHUB_SECRET_METADATA_PERMISSION_REQUIRED",
                "completed": completed,
            }

        if not all(secret_status.values()):
            return {
                "status": "SECRET_BROKER_REQUIRED",
                "completed": completed,
                "secretBrokerRequest": {
                    "schema": "ppf/secret-broker-request/v1",
                    "provider": "cloudflare",
                    "tokenOwner": "account",
                    "credential": {
                        "scope": "individual-worker",
                        "workerId": worker.get("id") or worker.get("name") or worker_name,
                        "workerName": worker.get("name") or worker_name,
                        "role": "Editor",
                    },
                    "target": {
                        "provider": "github-actions",
                        "repository": f"{owner}/{repository}",
                        "secretNames": list(REQUIRED_SECRETS),
                    },
                    "rules": {
                        "plaintextMustNotEnterModelContext": True,
                        "plaintextMustNotEnterGit": True,
                        "discardPlaintextAfterEncryptedWrite": True,
                    },
                },
            }

        return {
            "status": "READY_FOR_CI",
            "completed": completed,
            "repositoryId": str(repo.get("id")) if repo.get("id") is not None else None,
            "workerId": worker.get("id"),
            "workerName": worker.get("name") or worker_name,
            "deploymentSecrets": secret_status,
        }


def verify_restricted_url(url: str) -> dict[str, Any]:
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    opener = urllib.request.build_opener(NoRedirect)
    request = urllib.request.Request(url, headers={"User-Agent": "PPF-project-provisioner/1"})
    try:
        with opener.open(request, timeout=15) as response:
            code = response.status
            location = response.headers.get("Location", "")
    except urllib.error.HTTPError as exc:
        code = exc.code
        location = exc.headers.get("Location", "")
    except Exception:
        return {"status": "NOT_VERIFIED", "error": "NETWORK_ERROR"}
    denied = code in {401, 403} or (
        code in {301, 302, 303, 307, 308} and "/cdn-cgi/access/login" in location
    )
    return {"status": "VERIFIED_RESTRICTED" if denied else "NOT_VERIFIED", "statusCode": code, "anonymousDenied": denied}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("plan", "apply", "verify-restricted"))
    parser.add_argument("manifest", nargs="?", type=Path, default=Path("project.infrastructure.json"))
    parser.add_argument("--url")
    args = parser.parse_args(argv)
    try:
        manifest = load_manifest(args.manifest)
        provisioner = ProjectProvisioner(
            GitHubAdapter.from_env(),
            WorkersAdapter.from_env(),
            AccessAdapter.from_env(),
        )
        if args.command == "plan":
            result = provisioner.plan(manifest)
        elif args.command == "apply":
            result = provisioner.apply(manifest)
        else:
            if not args.url:
                raise ValueError("--url is required for verify-restricted")
            result = verify_restricted_url(args.url)
    except (ValueError, OSError, ProviderError) as exc:
        code = exc.code if isinstance(exc, ProviderError) else "CONFIGURATION_ERROR"
        result = {"status": "BLOCKED", "error": code}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("status") in {
        "PLAN_READY", "READY_FOR_CI", "SECRET_BROKER_REQUIRED", "VERIFIED_RESTRICTED"
    } else 2


if __name__ == "__main__":
    raise SystemExit(main())
