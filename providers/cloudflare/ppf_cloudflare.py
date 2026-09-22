#!/usr/bin/env python3
"""PPF lifecycle commands for a Workers Static Assets project."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
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
    if visibility in {"restricted", "private"} and access not in {"authenticated", "selected-audience", "shared-password", "other"}:
        raise ValueError("restricted/private publication requires an explicit access mode")
    if access == "shared-password":
        assets = wrangler.get("assets", {})
        limits = wrangler.get("ratelimits", [])
        if (web.get("access") or {}).get("implementation") != "ppf-worker-gate":
            raise ValueError("shared-password requires access.implementation: ppf-worker-gate")
        if not wrangler.get("main", "").endswith("password_gate.mjs"):
            raise ValueError("shared-password requires the PPF password gate Worker module")
        if assets.get("binding") != "ASSETS" or assets.get("run_worker_first") is not True:
            raise ValueError("shared-password requires the ASSETS binding and assets.run_worker_first: true")
        if not any(item.get("name") == "LOGIN_LIMIT" for item in limits):
            raise ValueError("shared-password requires the LOGIN_LIMIT binding")
    if visibility not in {"public", "restricted", "private"}:
        raise ValueError("web.visibility must be public, restricted, or private")
    return build, publishing, wrangler, output


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
    key = "holding_deploy" if holding else "deploy"
    command = build.get("commands", {}).get(key)
    if not command:
        print(f"BLOCKED: no {key} command is configured")
        return 2
    if not os.environ.get("CLOUDFLARE_API_TOKEN") or not os.environ.get("CLOUDFLARE_ACCOUNT_ID"):
        print("BLOCKED: Cloudflare deploy credentials are not available; no changes made")
        return 2
    result = subprocess.run(shlex.split(command), cwd=root, check=False)
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
        _, _, wrangler, _ = load_contract(root)
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"BLOCKED: {exc}")
        return 2
    if state.get("worker") != wrangler["name"]:
        print("BLOCKED: verified deployment record belongs to a different Worker; no changes made")
        return 2
    result = subprocess.run(["npx", "wrangler", "rollback", version_id, "--name", wrangler["name"]], cwd=root, check=False)
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
