"""GitHub repository adapter. Repository visibility is reconciled independently."""
from __future__ import annotations
from typing import Any
from urllib.parse import quote
from providers.infrastructure.api import ApiClient, ProviderError

class GitHubAdapter:
    def __init__(self, client: ApiClient):
        self.client = client

    @classmethod
    def from_env(cls) -> "GitHubAdapter":
        return cls(ApiClient.from_env("https://api.github.com", "GITHUB_TOKEN"))

    def read_repository(self, owner: str, repository: str) -> dict[str, Any] | None:
        path = f"/repos/{quote(owner, safe='')}/{quote(repository, safe='')}"
        try:
            return self.client.request("GET", path)
        except ProviderError as exc:
            if exc.status == 404:
                return None
            raise

    def ensure_repository(self, owner: str, repository: str, visibility: str,
                          approval: dict[str, Any] | None = None) -> dict[str, Any]:
        if visibility not in {"private", "public"}:
            raise ValueError("unsupported GitHub visibility")
        current = self.read_repository(owner, repository)
        if current is None:
            _require_public_approval(visibility, approval)
            identity = self.client.request("GET", "/user")
            create_path = "/user/repos" if identity.get("login", "").casefold() == owner.casefold() else f"/orgs/{quote(owner, safe='')}/repos"
            return self.client.request("POST", create_path, {
                "name": repository, "private": visibility == "private", "auto_init": False,
            })
        actual = "private" if current.get("private") else "public"
        if actual == visibility:
            return current
        _require_public_approval(visibility, approval)
        path = f"/repos/{quote(owner, safe='')}/{quote(repository, safe='')}"
        self.client.request("PATCH", path, {"private": visibility == "private"})
        return self.read_repository(owner, repository) or {}

    def rollback_visibility(self, owner: str, repository: str, previous_visibility: str) -> dict[str, Any]:
        if previous_visibility not in {"private", "public"}:
            raise ValueError("rollback requires a recorded previous visibility")
        return self.ensure_repository(owner, repository, previous_visibility)

def _require_public_approval(visibility: str, approval: dict[str, Any] | None) -> None:
    if visibility == "public" and not (
        isinstance(approval, dict) and approval.get("allowed") is True and approval.get("approvalId")
    ):
        raise ProviderError("PUBLICATION_APPROVAL_REQUIRED")
