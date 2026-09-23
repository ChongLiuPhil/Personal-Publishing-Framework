#!/usr/bin/env python3
"""PPF lifecycle commands for a Workers Static Assets project."""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import quote, urlsplit
import urllib.error
import urllib.request

import yaml


def load_contract(root: Path):
    build_path, publishing_path = root / "cloudflare-builds.yaml", root / "publishing.yaml"
    wrangler_path = root / "wrangler.jsonc"
    missing = [p.name for p in (build_path, publishing_path, wrangler_path) if not p.is_file()]
    if missing:
        raise ValueError("missing contract file(s): " + ", ".join(missing))
    build = yaml.safe_load(build_path.read_text(encoding="utf-8"))
    publishing = yaml.safe_load(publishing_path.read_text(encoding="utf-8"))
    # Wrangler JSONC permits comments; project templates use strict JSON-compatible JSONC.
    wrangler = json.loads(wrangler_path.read_text(encoding="utf-8"))
    if not all(isinstance(value, dict) for value in (build, publishing, wrangler)):
        raise ValueError("project contract files must each contain a mapping")
    if build.get("mode") != "workers-builds-git":
        raise ValueError("unsupported mode; expected workers-builds-git")
    access_baseline = build.get("platform_security", {}).get("worker_access", {})
    if access_baseline != {
        "baseline": "account-wide",
        "destination": "all_workers",
        "private_by_default": True,
        "public_exception": "worker-scoped-bypass",
        "previews_protected_by_default": True,
        "bootstrap_required_before_worker_creation": True,
    }:
        raise ValueError("platform_security.worker_access must require the account-wide private-by-default Access baseline")
    worker = build.get("worker", {})
    if not worker.get("name") or worker["name"] != wrangler.get("name"):
        raise ValueError("worker.name must match the Wrangler config")
    output = (root / worker.get("static_assets_directory", "")).resolve()
    assets_dir = wrangler.get("assets", {}).get("directory")
    if not assets_dir or (root / assets_dir).resolve() != output:
        raise ValueError("static assets output differs between build contract and Wrangler config")
    web = publishing.get("publication", {}).get("web", {})
    visibility = web.get("visibility")
    access = (web.get("access") or {}).get("mode")
    if visibility == "public" and access != "none":
        raise ValueError("public publication requires access.mode: none")
    if visibility in {"restricted", "private"} and access not in {"authenticated", "selected-audience", "other"}:
        raise ValueError("restricted/private publication requires an explicit access mode")
    if visibility not in {"public", "restricted", "private"}:
        raise ValueError("web.visibility must be public, restricted, or private")
    commands = build.get("commands", {})
    for key, expected in {
        "deploy": "wrangler deploy",
        "holding_deploy": "wrangler deploy",
        "preview_deploy": "wrangler versions upload",
    }.items():
        if key in commands and commands[key] != expected:
            raise ValueError(f"commands.{key} must be the fixed Wrangler operation: {expected}")
    return build, publishing, wrangler, output


def _wrangler_argv(root: Path, build: dict, args: list[str]) -> list[str]:
    """Resolve only the project-pinned Wrangler entrypoint; never run a repo npm script."""
    version = build.get("toolchain", {}).get("wrangler")
    if not isinstance(version, str) or not version:
        raise ValueError("toolchain.wrangler must pin the Wrangler version")
    package_path = root / "package.json"
    lock_path = root / "package-lock.json"
    try:
        package = json.loads(package_path.read_text(encoding="utf-8"))
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        raise ValueError("package.json and package-lock.json are required to verify the pinned Wrangler tool") from None
    if not isinstance(package, dict) or not isinstance(lock, dict):
        raise ValueError("package.json and package-lock.json must contain mappings")
    package_dev = package.get("devDependencies") if isinstance(package.get("devDependencies"), dict) else {}
    package_prod = package.get("dependencies") if isinstance(package.get("dependencies"), dict) else {}
    lock_packages = lock.get("packages") if isinstance(lock.get("packages"), dict) else {}
    lock_root = lock_packages.get("") if isinstance(lock_packages.get(""), dict) else {}
    lock_root_dev = lock_root.get("devDependencies") if isinstance(lock_root.get("devDependencies"), dict) else {}
    lock_root_prod = lock_root.get("dependencies") if isinstance(lock_root.get("dependencies"), dict) else {}
    lock_entry = lock_packages.get("node_modules/wrangler") if isinstance(lock_packages.get("node_modules/wrangler"), dict) else {}
    package_version = package_dev.get("wrangler") or package_prod.get("wrangler")
    lock_root_version = lock_root_dev.get("wrangler") or lock_root_prod.get("wrangler")
    lock_version = lock_entry.get("version")
    if package_version != version or lock_root_version != version or lock_version != version:
        raise ValueError("Wrangler package and lockfile must match toolchain.wrangler")
    resolved_url = lock_entry.get("resolved", "")
    integrity = lock_entry.get("integrity", "")
    try:
        if not isinstance(resolved_url, str) or not isinstance(integrity, str):
            raise ValueError("invalid Wrangler package lock metadata")
        resolved = urlsplit(resolved_url)
        digest = base64.b64decode(integrity.removeprefix("sha512-"), validate=True) if integrity.startswith("sha512-") else b""
    except (ValueError, TypeError):
        resolved = urlsplit("")
        digest = b""
    if (resolved.scheme, resolved.hostname, resolved.path) != ("https", "registry.npmjs.org", f"/wrangler/-/wrangler-{version}.tgz") or len(digest) != 64:
        raise ValueError("package-lock.json must pin Wrangler to its npm registry URL and SHA-512 integrity")
    node = shutil.which("node")
    entrypoint = root / "node_modules" / "wrangler" / "bin" / "wrangler.js"
    try:
        installed_package = json.loads((root / "node_modules" / "wrangler" / "package.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        installed_package = {}
    if not node or not entrypoint.is_file() or not isinstance(installed_package, dict) or installed_package.get("version") != version:
        raise ValueError("the pinned Wrangler installation is missing; install project dependencies before deployment")
    return [str(Path(node).resolve()), str(entrypoint.resolve()), *args]


def _run_wrangler(root: Path, build: dict, args: list[str]):
    """Run the pinned Wrangler entrypoint with only the credentials it needs."""
    command = _wrangler_argv(root, build, args)
    token = os.environ.get("CLOUDFLARE_API_TOKEN")
    account = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
    if not token or not account:
        raise ValueError("Cloudflare deploy credentials are not available; no changes made")
    with tempfile.TemporaryDirectory(prefix="ppf-wrangler-") as config_dir:
        child_env = {
            "CLOUDFLARE_API_TOKEN": token,
            "CLOUDFLARE_ACCOUNT_ID": account,
            "PATH": os.defpath,
            "HOME": config_dir,
            "XDG_CONFIG_HOME": config_dir,
            "TMPDIR": config_dir,
            "TEMP": config_dir,
            "TMP": config_dir,
        }
        if os.name == "nt":
            for key in ("SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT"):
                if os.environ.get(key):
                    child_env[key] = os.environ[key]
        return subprocess.run(command, cwd=root, env=child_env, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def api_get(root: Path, path: str):
    account = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
    token = os.environ.get("CLOUDFLARE_API_TOKEN")
    if not account or not token:
        return None, "API inspection needs CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN"
    if len(account) != 32 or any(char not in "0123456789abcdefABCDEF" for char in account):
        return None, "CLOUDFLARE_ACCOUNT_ID is not a valid 32-character account identifier"
    request = urllib.request.Request(
        f"https://api.cloudflare.com/client/v4/accounts/{account}{path}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            result = json.loads(response.read())
    except urllib.error.HTTPError as exc:
        return None, f"Cloudflare API HTTP {exc.code}; response body suppressed"
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None, "Cloudflare API unavailable or returned invalid JSON"
    if not result.get("success"):
        return None, "Cloudflare API rejected the request; error details suppressed"
    return result.get("result"), None


def doctor(root: Path) -> int:
    try:
        build, publishing, wrangler, output = load_contract(root)
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"BLOCKED: {exc}")
        return 2
    print(f"PASS: contract valid for Worker {wrangler['name']}")
    print(f"{'PASS' if output.is_dir() else 'INFO'}: output directory {'ready' if output.is_dir() else 'not built yet'}")
    account = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
    if not account or not os.environ.get("CLOUDFLARE_API_TOKEN"):
        print("BLOCKED: Cloudflare API credentials are not available to this process")
        return 2
    scripts, error = api_get(root, "/workers/scripts")
    if error:
        print(f"BLOCKED: live Worker inventory failed: {error}")
        return 2
    worker = next((item for item in (scripts or []) if item.get("id") == wrangler["name"] or item.get("script_name") == wrangler["name"]), None)
    triggers, trigger_error = (None, None)
    if worker:
        tag = worker.get("tag") or worker.get("script_tag")
        if not tag:
            print("BLOCKED: Worker response has no Builds script tag; cannot inspect trigger state")
            return 2
        triggers, trigger_error = api_get(root, f"/builds/workers/{quote(tag, safe='')}/triggers")
    if trigger_error:
        print(f"BLOCKED: build trigger inspection failed: {trigger_error}")
        return 2
    print(f"PASS: account API accessible; target_exists={worker is not None}")
    print(f"INFO: worker_build_triggers={len(triggers or [])}; match repository and branch before claiming Git integration")
    print("INFO: GitHub App repository authorization must be verified separately")
    print(f"INFO: visibility={publishing['publication']['web']['visibility']}")
    return 0


def plan(root: Path) -> int:
    try:
        build, publishing, wrangler, output = load_contract(root)
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"BLOCKED: {exc}")
        return 2
    report = {
        "operation": "workers-static-assets",
        "worker": wrangler["name"],
        "repository": build.get("git", {}).get("repository"),
        "branch": build.get("git", {}).get("production_branch"),
        "build_command": build.get("commands", {}).get("build"),
        "deploy_command": build.get("commands", {}).get("deploy"),
        "output_directory": str(output),
        "visibility": publishing["publication"]["web"]["visibility"],
        "previews_enabled": bool(wrangler.get("preview_urls", False)),
        "canonical_cutover": publishing.get("deployment", {}).get("web", {}).get("cutover_state") == "ACTIVE",
        "preserves_existing_provider_and_dns": True,
        "requires_workers_builds_github_app": True,
    }
    print(json.dumps(report, indent=2))
    return 0


def apply(root: Path, holding: bool = False) -> int:
    try:
        build, _, _, output = load_contract(root)
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"BLOCKED: {exc}")
        return 2
    if not output.is_dir():
        print("BLOCKED: build output is missing; run the configured build first")
        return 2
    key = "holding_deploy" if holding and "holding_deploy" in build.get("commands", {}) else "deploy"
    if not build.get("commands", {}).get(key):
        print(f"BLOCKED: no {key} command is configured")
        return 2
    if not os.environ.get("CLOUDFLARE_API_TOKEN") or not os.environ.get("CLOUDFLARE_ACCOUNT_ID"):
        print("BLOCKED: Cloudflare deploy credentials are not available; no changes made")
        return 2
    try:
        result = _run_wrangler(root, build, ["deploy"])
    except ValueError as exc:
        print(f"BLOCKED: {exc}")
        return 2
    if result.returncode:
        print(f"FAILED: configured {key} command exited with status {result.returncode}")
        return result.returncode
    print(f"PASS: configured {key} command completed")
    return 0


def verify(url: str, root: Path) -> int:
    try:
        _, publishing, wrangler, _ = load_contract(root)
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"BLOCKED: {exc}")
        return 2

    production_url = publishing.get("deployment", {}).get("web", {}).get("production_url")
    expected_origin = https_origin(production_url) if isinstance(production_url, str) else None
    if expected_origin is None:
        print("BLOCKED: deployment.web.production_url must be a valid HTTPS Worker URL")
        return 2
    if https_origin(url) != expected_origin:
        print("FAIL: verification URL must match the configured production Worker origin")
        return 2
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "PPF-Cloudflare-Verify/1.0"})
        with urllib.request.urlopen(request, timeout=20) as response:
            status, final_url = response.status, response.geturl()
    except urllib.error.HTTPError as exc:
        status, final_url = exc.code, exc.geturl()
    except (urllib.error.URLError, TimeoutError, ValueError):
        print("FAIL: candidate URL could not be reached")
        return 1
    if https_origin(final_url) != expected_origin:
        print("FAIL: verification redirected outside the configured production Worker origin")
        return 1
    ok = 200 <= status < 300
    record = {
        "checked_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "url": final_url,
        "http_status": status,
        "source_revision": os.environ.get("GITHUB_SHA"),
        "result": "PASS" if ok else "FAIL",
    }
    state_path = root / ".ppf" / "cloudflare-deployment.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        previous = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
    except json.JSONDecodeError:
        previous = {}
    verified = previous.get("verified_version_ids", [])
    if ok and os.environ.get("CLOUDFLARE_API_TOKEN") and os.environ.get("CLOUDFLARE_ACCOUNT_ID"):
        deployments, deployment_error = api_get(root, f"/workers/scripts/{quote(wrangler['name'], safe='')}/deployments")
        if deployment_error:
            record["deployment_version_check"] = "unavailable"
        else:
            active = sorted((deployments or {}).get("deployments", []), key=lambda item: item.get("created_on", ""), reverse=True)
            versions = active[0].get("versions", []) if active else []
            fully_active = [item.get("version_id") for item in versions if item.get("percentage") == 100 and item.get("version_id")]
            record["active_version_id"] = fully_active[0] if len(fully_active) == 1 and len(versions) == 1 else None
            if record["active_version_id"] and record["active_version_id"] not in verified:
                verified.append(record["active_version_id"])
    record["verified_version_ids"] = verified
    record["worker"] = wrangler["name"]
    record["history"] = (previous.get("history", []) + [{key: value for key, value in record.items() if key != "history"}])[-25:]
    state_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=2))
    return 0 if ok else 1


def https_origin(url: str):
    try:
        parsed = urlsplit(url)
        if parsed.scheme.lower() != "https" or not parsed.hostname or parsed.username or parsed.password:
            return None
        return parsed.scheme.lower(), parsed.hostname.lower().rstrip("."), parsed.port or 443
    except (AttributeError, TypeError, ValueError):
        return None


def rollback(version_id: str, root: Path) -> int:
    allowed = set("0123456789abcdef-")
    if len(version_id) != 36 or not set(version_id.lower()) <= allowed:
        print("BLOCKED: rollback requires an explicit Worker version UUID")
        return 2
    if not os.environ.get("CLOUDFLARE_API_TOKEN") or not os.environ.get("CLOUDFLARE_ACCOUNT_ID"):
        print("BLOCKED: Cloudflare deploy credentials are not available; no changes made")
        return 2
    state_path = root / ".ppf" / "cloudflare-deployment.json"
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        print("BLOCKED: no verified deployment record exists; no changes made")
        return 2
    if version_id not in state.get("verified_version_ids", []):
        print("BLOCKED: requested version is not recorded as successfully verified; no changes made")
        return 2
    try:
        build, _, wrangler, _ = load_contract(root)
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"BLOCKED: {exc}")
        return 2
    if state.get("worker") != wrangler["name"]:
        print("BLOCKED: verified deployment record belongs to a different Worker; no changes made")
        return 2
    try:
        result = _run_wrangler(root, build, ["rollback", version_id, "--name", wrangler["name"]])
    except ValueError as exc:
        print(f"BLOCKED: {exc}")
        return 2
    if result.returncode:
        print(f"FAILED: Wrangler rollback exited with status {result.returncode}")
        return result.returncode
    print("PASS: rollback requested; run verify against the deployed URL")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    commands = parser.add_subparsers(dest="operation", required=True)
    for name in ("doctor", "plan"):
        commands.add_parser(name)
    apply_parser = commands.add_parser("apply")
    apply_parser.add_argument("--holding", action="store_true")
    verify_parser = commands.add_parser("verify")
    verify_parser.add_argument("--url", required=True)
    rollback_parser = commands.add_parser("rollback")
    rollback_parser.add_argument("--version-id", required=True)
    args = parser.parse_args()
    if args.operation == "doctor":
        return doctor(args.root)
    if args.operation == "plan":
        return plan(args.root)
    if args.operation == "apply":
        return apply(args.root, args.holding)
    if args.operation == "verify":
        return verify(args.url, args.root)
    return rollback(args.version_id, args.root)


if __name__ == "__main__":
    sys.exit(main())
