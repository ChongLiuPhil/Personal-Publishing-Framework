"""Provider-backed doctor/plan/apply/verify/rollback orchestration.

The account-wide Access baseline is intentionally an owner-operated UI gate. Per-project
operations refuse to run until the baseline is discovered and verified.
"""
from __future__ import annotations
import argparse
import fcntl
import json
import os
import urllib.error
import urllib.request
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from providers.infrastructure.api import ProviderError
from providers.infrastructure.cloudflare import AccessAdapter, WorkersAdapter, WorkersBuildsAdapter
from providers.infrastructure.github import GitHubAdapter
from providers.infrastructure.manifest import load_manifest
from providers.infrastructure.plan import plan_reconciliation
from providers.infrastructure.state import IntegrationStateStore


@contextmanager
def _lock(directory: Path):
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd = os.open(directory / ".apply.lock", os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


class Coordinator:
    def __init__(self, github: GitHubAdapter, workers: WorkersAdapter,
                 builds: WorkersBuildsAdapter, access: AccessAdapter,
                 store: IntegrationStateStore | None = None):
        self.github, self.workers, self.builds, self.access = github, workers, builds, access
        self.store = store or IntegrationStateStore()

    def read_actual(self, manifest: dict[str, Any]) -> dict[str, Any]:
        owner, repository = manifest["github"]["owner"], manifest["github"]["repository"]
        repo = self.github.read_repository(owner, repository)
        worker = self.workers.read_worker(manifest["cloudflare"]["worker"])
        actual: dict[str, Any] = {
            "github": {
                "repositoryExists": repo is not None,
                "repositoryId": str(repo["id"]) if repo and repo.get("id") is not None else None,
                "repositoryVisibility": ("private" if repo.get("private") else "public") if repo else None,
            },
            "cloudflare": {
                "workerExists": worker is not None,
                "workerId": worker.get("id") if worker else None,
                "workerTag": worker.get("tag") if worker else None,
            },
            "builds": {},
            "inventory": {"workerNames": sorted(x.get("id", "") for x in self.workers.inventory())},
        }
        if repo is not None:
            try:
                actual["github"]["deploymentSecrets"] = self.github.deployment_secret_status(owner, repository)
            except ProviderError as exc:
                actual["github"]["deploymentSecrets"] = None
                actual["github"]["deploymentSecretReadError"] = exc.code
        try:
            hostname = os.environ.get("PPF_PRODUCTION_HOSTNAME")
            if worker and hostname:
                actual["cloudflare"].update(self.access.worker_state(worker.get("id", ""), hostname))
                public_probe = _anonymous_probe("https://" + hostname.removeprefix("https://").removeprefix("http://"))
                actual["cloudflare"]["publicAnonymousReachable"] = public_probe.get("statusCode") == 200
            else:
                baseline = self.access.account_baseline()
                actual["cloudflare"]["accountWideProtection"] = baseline is not None
                actual["cloudflare"]["accountAccessAppId"] = baseline.get("id") if baseline else None
            control_url = os.environ.get("PPF_CONTROL_WORKER_URL")
            if control_url:
                probe = _anonymous_probe("https://" + control_url.removeprefix("https://").removeprefix("http://"))
                actual["cloudflare"]["controlPrivateWorkerAnonymousDenied"] = probe.get("denied") is True
        except ProviderError as exc:
            actual["cloudflare"]["accountWideProtection"] = None
            actual["cloudflare"]["accessReadError"] = exc.code
        if worker and worker.get("tag"):
            config = self.builds.read_config(worker["tag"])
            triggers = self.builds.triggers(worker["tag"])
            actual["builds"].update({
                "workerConfig": config,
                "repositoryConnectionUuid": (config or {}).get("repo_connection_uuid"),
                "productionTriggerUuid": next((x.get("uuid") for x in triggers if x.get("production_branch")), None),
                "previewTriggerUuid": next((x.get("uuid") for x in triggers if x.get("preview_branch_includes")), None),
                "productionBranch": (config or {}).get("production_branch"),
            })
        return actual

    def doctor(self, manifest: dict[str, Any]) -> dict[str, Any]:
        actual = self.read_actual(manifest)
        baseline = actual["cloudflare"]["accountWideProtection"]
        return {
            "status": "READY" if baseline is True else "ACCOUNT_ACCESS_REQUIRED" if baseline is False else "ACCESS_READ_BLOCKED",
            "projectId": manifest["project"]["id"],
            "workerInventory": actual["inventory"]["workerNames"],
            "targetWorkerExists": actual["cloudflare"]["workerExists"],
            "accountWideAccess": baseline,
            "accessReadError": actual["cloudflare"].get("accessReadError"),
            "actual": actual,
            "mutationsApplied": False,
        }

    def plan(self, manifest: dict[str, Any], release_gate: dict[str, Any] | None = None,
             website_gate: dict[str, Any] | None = None) -> dict[str, Any]:
        return plan_reconciliation(manifest, self.read_actual(manifest), release_gate, website_gate)

    def apply(self, manifest: dict[str, Any], release_gate: dict[str, Any] | None = None,
              website_gate: dict[str, Any] | None = None, build_config: dict[str, Any] | None = None,
              triggers: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        before = self.read_actual(manifest)
        report = plan_reconciliation(manifest, before, release_gate, website_gate)
        if report["blockers"]:
            return {"status": "BLOCKED", "completed": [], "report": report,
                    "blocker": "RELEASE_OR_SECURITY_GATE"}
        if before["cloudflare"].get("accountWideProtection") is not True:
            return {"status": "BLOCKED", "completed": [], "report": report,
                    "blocker": "ACCOUNT_ACCESS_REQUIRED"}
        worker = before["cloudflare"]
        if not worker.get("workerExists"):
            return {"status": "BLOCKED", "completed": [], "report": report,
                    "blocker": "WORKER_DEPLOYMENT_REQUIRED"}
        if not isinstance(build_config, dict) or not isinstance(triggers, list) or not triggers:
            return {"status": "BLOCKED", "completed": [], "report": report,
                    "blocker": "BUILD_CONFIG_AND_TRIGGERS_REQUIRED"}
        _reject_build_secrets(build_config)
        production_branch = manifest["deployment"]["productionBranch"]
        if not any(production_branch in (item.get("branch_includes") or []) for item in triggers):
            return {"status": "BLOCKED", "completed": [], "report": report,
                    "blocker": "PRODUCTION_TRIGGER_REQUIRED"}
        if manifest["deployment"]["previewDeployments"] and not any(
            production_branch not in (item.get("branch_includes") or []) for item in triggers
        ):
            return {"status": "BLOCKED", "completed": [], "report": report,
                    "blocker": "PREVIEW_TRIGGER_REQUIRED"}
        # Serialize writers, then re-read to avoid applying a plan made against stale state.
        completed: list[str] = []
        state: dict[str, Any] = {
            "projectId": manifest["project"]["id"], "source": "provider-read",
            "previous": _state_snapshot(before), "desired": {
                "repositoryVisibility": manifest["github"]["repositoryVisibility"],
                "applicationVisibility": manifest["cloudflare"]["applicationVisibility"],
            }, "completed": completed,
        }
        with _lock(self.store.root):
            now = self.read_actual(manifest)
            if now != before:
                return {"status": "CONCURRENT_CHANGE", "completed": [], "report": report}
            try:
                repo = before["github"]
                if repo.get("repositoryVisibility") != manifest["github"]["repositoryVisibility"]:
                    self.github.ensure_repository(manifest["github"]["owner"], manifest["github"]["repository"],
                                                  manifest["github"]["repositoryVisibility"], release_gate)
                    completed.append("github.repository_visibility")
                if manifest["cloudflare"]["applicationVisibility"] == "public":
                    hostname = os.environ.get("PPF_PRODUCTION_HOSTNAME", "")
                    if not hostname:
                        raise ProviderError("PRODUCTION_HOSTNAME_REQUIRED")
                    self.access.reconcile_worker_visibility(worker["workerId"], hostname, "public", website_gate)
                    completed.append("cloudflare.production_public_exception")
                elif manifest["cloudflare"]["applicationVisibility"] == "private":
                    hostname = os.environ.get("PPF_PRODUCTION_HOSTNAME", "")
                    if hostname:
                        self.access.reconcile_worker_visibility(worker["workerId"], hostname, "private")
                        completed.append("cloudflare.production_public_exception_removed")
                if build_config is not None:
                    tag = worker.get("workerTag")
                    if not tag:
                        raise ProviderError("WORKER_TAG_UNAVAILABLE")
                    previous = before.get("builds", {}).get("workerConfig")
                    self.builds.ensure_config(tag, build_config)
                    state["previousWorkerBuildConfig"] = _without_secret_build_variables(previous)
                    completed.append("workers_builds.config")
                    connection_uuid = None
                    repository_config = build_config.get("git_repository")
                    if repository_config:
                        connection = self.builds.ensure_connection(repository_config)
                        connection_uuid = connection.get("uuid") or connection.get("repo_connection_uuid")
                    for trigger in triggers or []:
                        actual_trigger = dict(trigger)
                        if connection_uuid:
                            actual_trigger.setdefault("repo_connection_uuid", connection_uuid)
                        self.builds.ensure_trigger(tag, actual_trigger)
                        completed.append("workers_builds.trigger")
            except ProviderError as exc:
                state["completed"] = completed
                self.store.write(manifest["project"]["id"], state)
                self.store.append_audit(_event(manifest, "apply", completed, "FAILED", exc.code))
                return {"status": "PARTIAL_FAILURE" if completed else "FAILED",
                        "completed": completed, "error": exc.code}
            state["completed"] = completed
            self.store.write(manifest["project"]["id"], state)
            self.store.append_audit(_event(manifest, "apply", completed, "APPLIED", None))
        return {"status": "APPLIED", "completed": completed}

    def verify(self, manifest: dict[str, Any]) -> dict[str, Any]:
        actual = self.read_actual(manifest)
        report = plan_reconciliation(manifest, actual)
        probes: dict[str, Any] = {}
        urls = {
            "production": os.environ.get("PPF_PRODUCTION_HOSTNAME"),
            "preview": os.environ.get("PPF_PREVIEW_URL"),
            "controlWorker": os.environ.get("PPF_CONTROL_WORKER_URL"),
        }
        for label, url in urls.items():
            if url:
                probes[label] = _anonymous_probe("https://" + url.removeprefix("https://").removeprefix("http://"))
        public_ok = probes.get("production", {}).get("statusCode") == 200
        protected_ok = all(
            bool(urls[key]) and probes.get(key, {}).get("denied") is True
            for key in ("preview", "controlWorker")
        )
        verified = report["status"] == "PLAN_READY" and not report["operations"] and public_ok and protected_ok
        return {"status": "VERIFIED" if verified else "NOT_VERIFIED", "actual": actual, "plan": report,
                "anonymousProbes": probes,
                "missingProbeInputs": [key for key, value in urls.items() if not value]}

    def rollback(self, manifest: dict[str, Any]) -> dict[str, Any]:
        state = self.store.read(manifest["project"]["id"])
        if not state or not state.get("completed"):
            return {"status": "NOTHING_TO_ROLL_BACK"}
        completed = []
        previous = state.get("previous", {})
        try:
            gh = previous.get("github", {})
            if "github.repository_visibility" in state["completed"] and gh.get("repositoryVisibility"):
                self.github.rollback_visibility(manifest["github"]["owner"], manifest["github"]["repository"],
                                                gh["repositoryVisibility"])
                completed.append("github.repository_visibility")
            if "cloudflare.production_public_exception" in state["completed"]:
                hostname = os.environ.get("PPF_PRODUCTION_HOSTNAME", "")
                worker_id = previous.get("cloudflare", {}).get("workerId")
                was_public = previous.get("cloudflare", {}).get("applicationVisibility") == "public"
                if hostname and worker_id and not was_public:
                    self.access.reconcile_worker_visibility(worker_id, hostname, "private")
                    completed.append("cloudflare.production_public_exception")
            tag = previous.get("cloudflare", {}).get("workerTag")
            if "workers_builds.config" in state["completed"] and tag:
                self.builds.rollback_config(tag, state.get("previousWorkerBuildConfig"))
                completed.append("workers_builds.config")
        except ProviderError as exc:
            self.store.append_audit(_event(manifest, "rollback", completed, "FAILED", exc.code))
            return {"status": "PARTIAL_FAILURE" if completed else "FAILED", "completed": completed, "error": exc.code}
        self.store.append_audit(_event(manifest, "rollback", completed, "ROLLED_BACK", None))
        return {"status": "ROLLED_BACK", "completed": completed}


def _event(manifest: dict[str, Any], operation: str, completed: list[str], result: str, error: str | None) -> dict[str, Any]:
    return {
        "projectId": manifest["project"]["id"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "actor": "ppf-infrastructure-agent",
        "operation": operation,
        "previousState": {},
        "desiredState": {"completed": list(completed)},
        "actualResult": result,
        "verification": "pending",
        "error": {"code": error} if error else None,
    }


def _anonymous_probe(url: str) -> dict[str, Any]:
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None
    opener = urllib.request.build_opener(NoRedirect)
    request = urllib.request.Request(url, headers={"User-Agent": "PPF-infrastructure-verifier/1"})
    try:
        with opener.open(request, timeout=15) as response:
            code, location = response.status, response.headers.get("Location", "")
    except urllib.error.HTTPError as exc:
        code, location = exc.code, exc.headers.get("Location", "")
    except Exception:
        return {"reachable": False, "denied": False, "error": "NETWORK_ERROR"}
    denied = code in {401, 403} or (code in {301, 302, 303, 307, 308} and "/cdn-cgi/access/login" in location)
    return {"reachable": True, "statusCode": code, "denied": denied}


def _without_secret_build_variables(config: dict[str, Any] | None) -> dict[str, Any] | None:
    if config is None:
        return None
    safe = dict(config)
    # Secret build values are not retrievable for a safe rollback snapshot.
    safe.pop("environment_variables", None)
    return safe


def _state_snapshot(actual: dict[str, Any]) -> dict[str, Any]:
    snapshot = dict(actual)
    builds = dict(snapshot.get("builds", {}))
    builds["workerConfig"] = _without_secret_build_variables(builds.get("workerConfig"))
    snapshot["builds"] = builds
    return snapshot


def _reject_build_secrets(config: dict[str, Any]) -> None:
    variables = config.get("previews_base_config", {}).get("environment_variables", {})
    production = config.get("production_settings", {}).get("environment_variables", {})
    for values in (variables, production):
        if isinstance(values, dict) and any(
            isinstance(value, dict) and value.get("is_secret") is True for value in values.values()
        ):
            raise ProviderError("SECRET_DIRECT_INPUT_REQUIRED")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("doctor", "plan", "apply", "verify", "rollback"))
    parser.add_argument("manifest", nargs="?", type=Path, default=Path("project.infrastructure.json"))
    parser.add_argument("--release-gate", type=Path)
    parser.add_argument("--website-gate", type=Path)
    parser.add_argument("--build-config", type=Path)
    parser.add_argument("--triggers", type=Path)
    args = parser.parse_args(argv)
    try:
        manifest = load_manifest(args.manifest)
        release = json.loads(args.release_gate.read_text()) if args.release_gate else None
        website = json.loads(args.website_gate.read_text()) if args.website_gate else None
        build_config = json.loads(args.build_config.read_text()) if args.build_config else None
        triggers = json.loads(args.triggers.read_text()) if args.triggers else None
        coordinator = Coordinator(GitHubAdapter.from_env(), WorkersAdapter.from_env(),
                                  WorkersBuildsAdapter.from_env(), AccessAdapter.from_env())
        result = (coordinator.doctor(manifest) if args.command == "doctor" else
                  coordinator.plan(manifest, release, website) if args.command == "plan" else
                  coordinator.apply(manifest, release, website, build_config, triggers) if args.command == "apply" else
                  coordinator.verify(manifest) if args.command == "verify" else
                  coordinator.rollback(manifest))
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result.get("status") in {"READY", "PLAN_READY", "VERIFIED", "APPLIED", "ROLLED_BACK", "NOTHING_TO_ROLL_BACK"} else 2
    except (ValueError, OSError, ProviderError) as exc:
        code = exc.code if isinstance(exc, ProviderError) else "CONFIGURATION_ERROR"
        print(json.dumps({"status": "BLOCKED", "error": code}, indent=2))
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
