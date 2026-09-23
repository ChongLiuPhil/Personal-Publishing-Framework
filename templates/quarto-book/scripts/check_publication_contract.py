#!/usr/bin/env python3
"""Validate the generic PPF Quarto + Workers Builds reference contract."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)

def require(path: str, marker: str) -> None:
    target = ROOT / path
    if not target.is_file():
        fail(f"missing required file: {path}")
    if marker not in target.read_text(encoding="utf-8"):
        fail(f"{path} is missing required marker: {marker}")

def main() -> None:
    require("publishing.yaml", "integration_mode: workers-builds-git")
    require("publishing.yaml", 'canonical_publish_gate: "make web-publish-check"')
    require("publishing.yaml", "authorization_state: not-authorized")
    require("cloudflare-builds.yaml", "mode: workers-builds-git")
    require("cloudflare-builds.yaml", 'build: "bash scripts/cloudflare_build.sh"')
    require("cloudflare-builds.yaml", 'deploy: "wrangler deploy"')
    require("cloudflare-builds.yaml", 'preview_deploy: "wrangler versions upload"')
    require("Makefile", "web-publish-check:")
    require("Makefile", "$(QUARTO) render --profile web")
    require("Makefile", "python3 scripts/verify_web_output.py")
    require("scripts/cloudflare_build.sh", "make web-publish-check")
    require("scripts/ensure_quarto.sh", "sha256sum --check --status")
    require("cloudflare-builds.yaml", "production_profile: human-selection-required")
    require("cloudflare-builds.yaml", "workers_builds_native:")
    require("cloudflare-builds.yaml", "hardened_external_ci:")
    require("cloudflare-builds.yaml", "future_native_granular:")
    require("cloudflare-builds.yaml", "workers-builds-account-owned-token-not-yet-supported")

    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    if package.get("devDependencies", {}).get("wrangler") != "4.135.0":
        fail("package.json must pin Wrangler 4.135.0")
    lock = json.loads((ROOT / "package-lock.json").read_text(encoding="utf-8"))
    if lock.get("lockfileVersion") != 3:
        fail("package-lock.json must use npm lockfileVersion 3")
    wrangler = lock.get("packages", {}).get("node_modules/wrangler", {}).get("version")
    if wrangler != "4.135.0":
        fail("package-lock.json must resolve Wrangler 4.135.0")
    if (ROOT / ".nvmrc").read_text(encoding="utf-8").strip() != "24":
        fail(".nvmrc must pin Node 24")

    print("PPF Workers Builds reference contract validation passed.")

if __name__ == "__main__":
    main()
