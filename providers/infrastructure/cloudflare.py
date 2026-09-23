"""Cloudflare Workers, Workers Builds, and Access API adapters."""
from __future__ import annotations
import os
from typing import Any
from urllib.parse import quote
from providers.infrastructure.api import ApiClient, ProviderError

def _client_from_env() -> tuple[ApiClient, str]:
    account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
    if not account_id:
        raise ProviderError("ACCOUNT_ID_MISSING")
    return ApiClient.from_env("https://api.cloudflare.com/client/v4", "CLOUDFLARE_API_TOKEN"), account_id

class WorkersAdapter:
    def __init__(self, client: ApiClient, account_id: str):
        self.client, self.account_id = client, account_id

    @classmethod
    def from_env(cls) -> "WorkersAdapter":
        return cls(*_client_from_env())

    def inventory(self) -> list[dict[str, Any]]:
        result = self.client.request("GET", f"/accounts/{self.account_id}/workers/scripts")
        return result if isinstance(result, list) else []

    def read_worker(self, name: str) -> dict[str, Any] | None:
        return next((x for x in self.inventory() if x.get("id") == name or x.get("script") == name), None)

    def require_existing(self, name: str) -> dict[str, Any]:
        result = self.read_worker(name)
        if result is None:
            raise ProviderError("WORKER_DEPLOYMENT_REQUIRED")
        return result

class WorkersBuildsAdapter:
    def __init__(self, client: ApiClient, account_id: str):
        self.client, self.account_id = client, account_id

    @classmethod
    def from_env(cls) -> "WorkersBuildsAdapter":
        return cls(*_client_from_env())

    def read_config(self, worker_tag: str) -> dict[str, Any] | None:
        path = f"/accounts/{self.account_id}/builds/workers/{quote(worker_tag, safe='')}"
        try:
            return self.client.request("GET", path)
        except ProviderError as exc:
            if exc.status == 404:
                return None
            raise

    def triggers(self, worker_tag: str) -> list[dict[str, Any]]:
        path = f"/accounts/{self.account_id}/builds/workers/{quote(worker_tag, safe='')}/triggers"
        result = self.client.request("GET", path)
        return result if isinstance(result, list) else []

    def ensure_config(self, worker_tag: str, config: dict[str, Any]) -> dict[str, Any]:
        path = f"/accounts/{self.account_id}/builds/workers/{quote(worker_tag, safe='')}"
        current = self.read_config(worker_tag)
        if current is None:
            return self.client.request("POST", f"/accounts/{self.account_id}/builds/workers",
                                       {**config, "script_tag": worker_tag})
        if _normalized(current) == _normalized(config):
            return current
        return self.client.request("PATCH", path, config)

    def ensure_trigger(self, worker_tag: str, trigger: dict[str, Any]) -> dict[str, Any]:
        current = self.triggers(worker_tag)
        found = next((x for x in current if _trigger_matches(x, trigger)), None)
        if found:
            return found
        return self.client.request("POST", f"/accounts/{self.account_id}/builds/triggers",
                                   {**trigger, "external_script_id": worker_tag})

    def ensure_connection(self, connection: dict[str, Any]) -> dict[str, Any]:
        required = {"provider_type", "provider_account_id", "provider_account_name", "repo_id", "repo_name"}
        if not required.issubset(connection):
            raise ValueError("repository connection is missing required provider fields")
        # This provider endpoint is an upsert keyed by the source-control repository.
        return self.client.request("PUT", f"/accounts/{self.account_id}/builds/repos/connections", connection)

    def rollback_config(self, worker_tag: str, previous_config: dict[str, Any] | None) -> None:
        path = f"/accounts/{self.account_id}/builds/workers/{quote(worker_tag, safe='')}"
        if previous_config is None:
            self.client.request("DELETE", path)
        else:
            self.client.request("PATCH", path, previous_config)

class AccessAdapter:
    def __init__(self, client: ApiClient, account_id: str):
        self.client, self.account_id = client, account_id

    @classmethod
    def from_env(cls) -> "AccessAdapter":
        return cls(*_client_from_env())

    def inventory(self) -> list[dict[str, Any]]:
        result = self.client.request("GET", f"/accounts/{self.account_id}/access/apps?per_page=1000")
        return result if isinstance(result, list) else []

    def account_baseline(self) -> dict[str, Any] | None:
        rows = [app for app in self.inventory()
                if any(x.get("type") == "all_workers" for x in app.get("destinations", []))]
        if len(rows) > 1:
            raise ProviderError("ACCESS_BASELINE_CONFLICT")
        return rows[0] if rows else None

    def worker_state(self, worker_id: str, production_hostname: str) -> dict[str, Any]:
        apps = self.inventory()
        baseline = self.account_baseline()
        production_public = any(
            dest.get("type") == "public" and dest.get("uri") == production_hostname
            and any(policy.get("decision") == "bypass" for policy in app.get("policies", []))
            for app in apps for dest in app.get("destinations", [])
        )
        preview_protected = baseline is not None or any(
            dest.get("type") in {"all_preview_workers", "preview_worker"}
            and (dest.get("type") == "all_preview_workers" or dest.get("worker_id") == worker_id)
            for app in apps for dest in app.get("destinations", [])
        )
        return {
            "accountWideProtection": baseline is not None,
            "accountWideAccessAppId": baseline.get("id") if baseline else None,
            "applicationVisibility": "public" if production_public else "private" if baseline else None,
            "previewVisibility": "private" if preview_protected else None,
            "publicExceptionAppExists": production_public,
        }

    def create_account_baseline(self, policy: dict[str, Any]) -> dict[str, Any]:
        # This account-wide security change must be committed by the owner in Cloudflare UI.
        raise ProviderError("ACCOUNT_SECURITY_UI_APPROVAL_REQUIRED")

    def reconcile_worker_visibility(self, worker_id: str, production_hostname: str, visibility: str,
                                    publication_gate: dict[str, Any] | None = None) -> dict[str, Any] | None:
        if visibility not in {"private", "public"}:
            raise ValueError("unsupported Worker visibility")
        apps = self.inventory()
        app_name = f"PPF public production {worker_id}"
        matches = [app for app in apps if app.get("name") == app_name]
        if len(matches) > 1:
            raise ProviderError("ACCESS_APP_CONFLICT")
        current = matches[0] if matches else None
        exact_host_apps = [app for app in apps if any(
            dest.get("type") == "public" and dest.get("uri") == production_hostname
            for dest in app.get("destinations", [])
        )]
        if visibility == "public":
            for existing in exact_host_apps:
                if existing.get("id") != (current or {}).get("id"):
                    if any(policy.get("decision") == "bypass" for policy in existing.get("policies", [])):
                        return existing
                    raise ProviderError("ACCESS_APP_CONFLICT")
        if visibility == "private":
            if current is None:
                return None
            if not any(d.get("type") == "public" and d.get("uri") == production_hostname for d in current.get("destinations", [])):
                raise ProviderError("ACCESS_APP_OWNERSHIP_CONFLICT")
            self.client.request("DELETE", f"/accounts/{self.account_id}/access/apps/{quote(current['id'], safe='')}")
            return None
        if not (isinstance(publication_gate, dict) and publication_gate.get("allowed") is True
                and publication_gate.get("approvalId")):
            raise ProviderError("PUBLICATION_APPROVAL_REQUIRED")
        if current and current.get("destinations") == [self.public_production_destination(production_hostname)]:
            return current
        payload = {
            "name": app_name,
            "type": "self_hosted",
            "domain": production_hostname,
            "destinations": [self.public_production_destination(production_hostname)],
            "policies": [{"name": f"PPF public production {worker_id}",
                          "decision": "bypass", "include": [{"everyone": {}}]}],
        }
        if current is None:
            return self.client.request("POST", f"/accounts/{self.account_id}/access/apps", payload)
        return self.client.request("PUT", f"/accounts/{self.account_id}/access/apps/{quote(current['id'], safe='')}", payload)

    @staticmethod
    def public_production_destination(hostname: str) -> dict[str, str]:
        return {"type": "public", "uri": hostname}

def _normalized(value: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in value.items() if k not in {"id", "created_on", "modified_on", "external_script_id"}}

def _trigger_matches(actual: dict[str, Any], desired: dict[str, Any]) -> bool:
    keys = ("trigger_name", "build_command", "deploy_command", "root_directory",
            "repo_connection_uuid", "external_script_id")
    if not all(actual.get(k) == desired.get(k) for k in keys if k in desired):
        return False
    branches = desired.get("branch_includes")
    return branches is None or actual.get("branch_includes") == branches
