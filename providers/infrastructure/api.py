"""Small injectable HTTP client with credential-safe errors for provider APIs."""
from __future__ import annotations
import json
import os
from dataclasses import dataclass
from typing import Any, Callable, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

class ProviderError(RuntimeError):
    def __init__(self, code: str, status: int | None = None):
        self.code, self.status = code, status
        super().__init__(code)

Transport = Callable[[str, str, dict[str, str], Optional[Any]], tuple[int, Any]]

def urllib_transport(url: str, method: str, headers: dict[str, str], body: Any | None) -> tuple[int, Any]:
    request = Request(url, data=None if body is None else json.dumps(body).encode(), headers=headers, method=method)
    try:
        with urlopen(request, timeout=20) as response:
            raw = response.read()
            return response.status, json.loads(raw) if raw else None
    except HTTPError as exc:
        raise ProviderError("HTTP_ERROR", exc.code) from None
    except (URLError, TimeoutError):
        raise ProviderError("NETWORK_ERROR") from None

@dataclass
class ApiClient:
    base_url: str
    token: str
    transport: Transport = urllib_transport

    @classmethod
    def from_env(cls, base_url: str, variable: str) -> "ApiClient":
        token = os.environ.get(variable)
        if not token:
            raise ProviderError("CREDENTIAL_MISSING")
        return cls(base_url, token)

    def request(self, method: str, path: str, body: Any | None = None) -> Any:
        headers = {"Authorization": f"Bearer {self.token}", "Accept": "application/json", "Content-Type": "application/json"}
        try:
            status, payload = self.transport(self.base_url.rstrip("/") + path, method, headers, body)
        except ProviderError:
            raise
        except Exception:
            raise ProviderError("TRANSPORT_ERROR") from None
        if not 200 <= status < 300:
            raise ProviderError("HTTP_ERROR", status)
        if isinstance(payload, dict) and payload.get("success") is False:
            raise ProviderError("PROVIDER_REJECTED", status)
        return payload.get("result", payload) if isinstance(payload, dict) else payload
