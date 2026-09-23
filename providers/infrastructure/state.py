#!/usr/bin/env python3
"""Private local persistence for non-secret provider IDs and audit events."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any


SENSITIVE_KEY = re.compile(r"(?i)(?:^|_)(?:api_?token|secret(?:_?value)?|password|cookie|authorization|private_?key|credential_?value)(?:$|_)")
SENSITIVE_VALUE = re.compile(r"(?i)(?:bearer\s+\S+|(?:gh[pousr]_|github_pat_|sk_live_|sk_test_)\S+)")
AUDIT_FIELDS = {"projectId", "timestamp", "actor", "operation", "previousState", "desiredState", "actualResult", "verification", "error"}
SAFE_ERROR_CODE = re.compile(r"^[A-Z][A-Z0-9_]{1,63}$")


def default_state_dir() -> Path:
    configured = os.environ.get("PPF_INFRA_STATE_DIR")
    return Path(configured).expanduser() if configured else Path.home() / ".ppf" / "infrastructure"


def _check_safe(value: Any, path: str = "<root>") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if SENSITIVE_KEY.search(str(key)):
                raise ValueError(f"secret-bearing field is prohibited in integration state: {path}.{key}")
            _check_safe(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _check_safe(child, f"{path}[{index}]")
    elif isinstance(value, str) and SENSITIVE_VALUE.search(value):
        raise ValueError(f"credential-like value is prohibited in integration state: {path}")


class IntegrationStateStore:
    def __init__(self, root: Path | None = None):
        self.root = (root or default_state_dir()).expanduser()

    def _project_path(self, project_id: str) -> Path:
        if not project_id or not re.fullmatch(r"[A-Za-z0-9._-]+", project_id):
            raise ValueError("projectId must contain only letters, digits, dot, underscore, or hyphen")
        return self.root / f"{project_id}.json"

    def write(self, project_id: str, state: dict[str, Any]) -> Path:
        _check_safe(state)
        if state.get("projectId") != project_id:
            raise ValueError("state.projectId must match the file identity")
        path = self._project_path(project_id)
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.root, 0o700)
        data = json.dumps(state, ensure_ascii=False, indent=2) + "\n"
        fd, temp_name = tempfile.mkstemp(prefix=".state-", suffix=".tmp", dir=self.root)
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, path)
            os.chmod(path, 0o600)
        finally:
            try:
                os.unlink(temp_name)
            except FileNotFoundError:
                pass
        return path

    def read(self, project_id: str) -> dict[str, Any] | None:
        path = self._project_path(project_id)
        if path.is_symlink():
            raise ValueError("integration state must not be a symbolic link")
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return None
        except json.JSONDecodeError as exc:
            raise ValueError("integration state is not valid JSON") from exc
        if not isinstance(value, dict) or value.get("projectId") != project_id:
            raise ValueError("integration state project identity does not match")
        if os.stat(path).st_mode & 0o077:
            raise ValueError("integration state permissions are broader than owner-only")
        _check_safe(value)
        return value

    def append_audit(self, event: dict[str, Any]) -> Path:
        missing = AUDIT_FIELDS - set(event)
        if missing:
            raise ValueError("audit event missing fields: " + ", ".join(sorted(missing)))
        error = event.get("error")
        if error is not None and (not isinstance(error, dict) or set(error) != {"code"} or not isinstance(error["code"], str) or not SAFE_ERROR_CODE.fullmatch(error["code"])):
            raise ValueError("audit errors must use a sanitized error code without provider response text")
        _check_safe(event)
        path = self.root / "audit.jsonl"
        if path.is_symlink():
            raise ValueError("audit log must not be a symbolic link")
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.root, 0o700)
        fd = os.open(path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
        try:
            os.fchmod(fd, 0o600)
            payload = (json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
            os.write(fd, payload)
            os.fsync(fd)
        finally:
            os.close(fd)
        return path
