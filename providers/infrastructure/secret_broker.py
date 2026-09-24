"""Trusted secret-broker orchestration for project-scoped deployment credentials.

This module deliberately separates orchestration from provider-specific credential
minting/encryption. A trusted runtime injects a Cloudflare token issuer and a
GitHub Actions secret writer. Token plaintext is never returned by this module.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


TOKEN_SECRET = "CLOUDFLARE_API_TOKEN"
ACCOUNT_SECRET = "CLOUDFLARE_ACCOUNT_ID"
EXPECTED_SECRETS = (TOKEN_SECRET, ACCOUNT_SECRET)


class BrokerError(RuntimeError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass
class MintedCredential:
    token_id: str
    worker_id: str
    role: str
    value: bytearray


class WorkerTokenIssuer(Protocol):
    def mint_worker_editor_token(self, *, worker_id: str, worker_name: str, token_name: str) -> MintedCredential:
        """Return an account-owned credential scoped to one existing Worker with Editor role."""

    def revoke_token(self, token_id: str) -> None:
        """Revoke a previously minted token by non-secret identifier."""


class RepositorySecretWriter(Protocol):
    def secret_exists(self, *, owner: str, repository: str, name: str) -> bool:
        """Read only secret metadata; never return a secret value."""

    def put_secret(self, *, owner: str, repository: str, name: str, value: memoryview) -> None:
        """Encrypt/write a secret through the provider's protected secret API."""

    def delete_secret(self, *, owner: str, repository: str, name: str) -> None:
        """Delete a secret installed by this broker during rollback."""


def _validate_request(request: dict[str, Any]) -> tuple[str, str, str, str, str]:
    if request.get("schema") != "ppf/secret-broker-request/v1":
        raise BrokerError("INVALID_REQUEST_SCHEMA")
    if request.get("provider") != "cloudflare" or request.get("tokenOwner") != "account":
        raise BrokerError("INVALID_PROVIDER_OR_TOKEN_OWNER")

    credential = request.get("credential")
    target = request.get("target")
    rules = request.get("rules")
    if not isinstance(credential, dict) or not isinstance(target, dict) or not isinstance(rules, dict):
        raise BrokerError("INVALID_REQUEST_SHAPE")
    if credential.get("scope") != "individual-worker" or credential.get("role") != "Editor":
        raise BrokerError("UNSAFE_CREDENTIAL_SCOPE")
    worker_id = credential.get("workerId")
    worker_name = credential.get("workerName")
    if not isinstance(worker_id, str) or not worker_id or not isinstance(worker_name, str) or not worker_name:
        raise BrokerError("WORKER_IDENTITY_REQUIRED")

    if target.get("provider") != "github-actions":
        raise BrokerError("UNSUPPORTED_SECRET_TARGET")
    repository = target.get("repository")
    names = target.get("secretNames")
    if not isinstance(repository, str) or repository.count("/") != 1:
        raise BrokerError("INVALID_REPOSITORY")
    owner, repo_name = repository.split("/", 1)
    if not owner or not repo_name:
        raise BrokerError("INVALID_REPOSITORY")
    if not isinstance(names, list) or set(names) != set(EXPECTED_SECRETS) or len(names) != 2:
        raise BrokerError("INVALID_SECRET_SET")

    required_rules = (
        "plaintextMustNotEnterModelContext",
        "plaintextMustNotEnterGit",
        "discardPlaintextAfterEncryptedWrite",
    )
    if any(rules.get(key) is not True for key in required_rules):
        raise BrokerError("PLAINTEXT_BOUNDARY_NOT_ENFORCED")
    return owner, repo_name, worker_id, worker_name, repository


def _wipe(value: bytearray) -> None:
    for index in range(len(value)):
        value[index] = 0


class TrustedSecretBroker:
    """Atomic broker state machine.

    The broker refuses to overwrite existing target secrets. This avoids deleting
    pre-existing credentials if a later write fails and rollback is required.
    """

    def __init__(self, issuer: WorkerTokenIssuer, writer: RepositorySecretWriter):
        self.issuer = issuer
        self.writer = writer

    def execute(self, request: dict[str, Any], *, cloudflare_account_id: str) -> dict[str, Any]:
        owner, repository, worker_id, worker_name, repository_full_name = _validate_request(request)
        if not isinstance(cloudflare_account_id, str) or len(cloudflare_account_id) != 32:
            return _result(
                "BLOCKED",
                repository_full_name,
                worker_id,
                error="INVALID_CLOUDFLARE_ACCOUNT_ID",
            )

        existing = [
            name for name in EXPECTED_SECRETS
            if self.writer.secret_exists(owner=owner, repository=repository, name=name)
        ]
        if existing:
            return _result(
                "BLOCKED",
                repository_full_name,
                worker_id,
                error="TARGET_SECRET_ALREADY_EXISTS",
                installed=existing,
            )

        minted: MintedCredential | None = None
        installed: list[str] = []
        rollback_errors: list[str] = []
        try:
            minted = self.issuer.mint_worker_editor_token(
                worker_id=worker_id,
                worker_name=worker_name,
                token_name=f"ppf-{worker_name}-github-actions",
            )
            if minted.worker_id != worker_id or minted.role != "Editor":
                try:
                    self.issuer.revoke_token(minted.token_id)
                finally:
                    _wipe(minted.value)
                return _result(
                    "BLOCKED",
                    repository_full_name,
                    worker_id,
                    token_id=minted.token_id,
                    error="ISSUER_SCOPE_MISMATCH",
                )

            self.writer.put_secret(
                owner=owner,
                repository=repository,
                name=TOKEN_SECRET,
                value=memoryview(minted.value),
            )
            installed.append(TOKEN_SECRET)
            self.writer.put_secret(
                owner=owner,
                repository=repository,
                name=ACCOUNT_SECRET,
                value=memoryview(bytearray(cloudflare_account_id.encode("ascii"))),
            )
            installed.append(ACCOUNT_SECRET)

            verified = all(
                self.writer.secret_exists(owner=owner, repository=repository, name=name)
                for name in EXPECTED_SECRETS
            )
            if not verified:
                raise BrokerError("SECRET_METADATA_VERIFICATION_FAILED")

            return _result(
                "INSTALLED",
                repository_full_name,
                worker_id,
                token_id=minted.token_id,
                installed=installed,
                verified=True,
            )
        except Exception as exc:
            code = exc.code if isinstance(exc, BrokerError) else "SECRET_BROKER_EXECUTION_FAILED"
            for name in reversed(installed):
                try:
                    self.writer.delete_secret(owner=owner, repository=repository, name=name)
                except Exception:
                    rollback_errors.append(f"delete:{name}")
            if minted is not None:
                try:
                    self.issuer.revoke_token(minted.token_id)
                except Exception:
                    rollback_errors.append("revoke:cloudflare-token")
            return _result(
                "ROLLBACK_INCOMPLETE" if rollback_errors else "ROLLED_BACK",
                repository_full_name,
                worker_id,
                token_id=minted.token_id if minted else None,
                error=code,
                rollback_errors=rollback_errors,
            )
        finally:
            if minted is not None and any(minted.value):
                _wipe(minted.value)


def _result(
    status: str,
    repository: str,
    worker_id: str,
    *,
    token_id: str | None = None,
    error: str | None = None,
    installed: list[str] | None = None,
    verified: bool = False,
    rollback_errors: list[str] | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "schema": "ppf/secret-broker-result/v1",
        "status": status,
        "repository": repository,
        "workerId": worker_id,
        "installedSecretNames": list(installed or []),
        "secretMetadataVerified": verified,
        "plaintextReturned": False,
        "rollbackState": "incomplete" if status == "ROLLBACK_INCOMPLETE" else (
            "completed" if status == "ROLLED_BACK" else "not-required"
        ),
    }
    if token_id is not None:
        result["tokenId"] = token_id
    if error is not None:
        result["error"] = error
    if rollback_errors:
        result["rollbackErrors"] = list(rollback_errors)
    return result
