#!/usr/bin/env python3
"""Validate the generic PPF Quarto + Cloudflare reference contract."""

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
    # Publication intent stays private/restricted until a durable authorization is materialized.
    require("publishing.yaml", "integration_mode: workers-builds-git")
    require("publishing.yaml", 'canonical_publish_gate: "make web-publish-check"')
    require("publishing.yaml", "authorization_state: not-authorized")
    require("publishing.yaml", "visibility: restricted")
    require("publishing.yaml", "enabled: false")
    require("publishing.yaml", "github_app: project-authorization-required")
    require("publishing.yaml", "repository_connection: unverified")
    require("publishing.yaml", "build_token: provider-managed-user-token")

    # The installable reference defaults to one guided Workers Builds connection per project.
    require("cloudflare-builds.yaml", "mode: workers-builds-git")
    require("cloudflare-builds.yaml", "production_profile: workers-builds-native")
    require("cloudflare-builds.yaml", "default: worker-scoped")
    require("cloudflare-builds.yaml", "cloudflare_git_authorization: human-assisted-once-per-project")
    require("cloudflare-builds.yaml", "build_token: provider-managed-user-token")
    require("cloudflare-builds.yaml", "non_production_branch_builds: false")
    require("cloudflare-builds.yaml", "enabled_by_default: false")
    require("cloudflare-builds.yaml", "workers_builds_native:")
    require("cloudflare-builds.yaml", "status: preferred-guided-project-setup")

    # Hardened external CI remains available, but explicitly optional.
    require("cloudflare-builds.yaml", "external_ci:")
    require("cloudflare-builds.yaml", "status: optional-advanced")
    require("cloudflare-builds.yaml", "workflow: .github/workflows/deploy-cloudflare.yml")
    require("cloudflare-builds.yaml", "plaintext_must_not_enter_model_context: true")
    require("cloudflare-builds.yaml", "hardened_external_ci:")
    require("cloudflare-builds.yaml", "requires_secret_broker: true")
    require("cloudflare-builds.yaml", "acceptance: pending-live-provider-verification")

    # Both profiles share the same repository-owned build gate and pinned toolchain.
    require("cloudflare-builds.yaml", 'build: "bash scripts/cloudflare_build.sh"')
    require("cloudflare-builds.yaml", 'deploy: "npx wrangler deploy"')
    require("cloudflare-builds.yaml", 'preview_deploy: "npx wrangler preview"')
    require("Makefile", "web-publish-check:")
    require("Makefile", "$(QUARTO) render --profile web")
    require("Makefile", "python3 scripts/verify_web_output.py")
    require("scripts/cloudflare_build.sh", "make web-publish-check")
    require("scripts/ensure_quarto.sh", "sha256sum --check --status")

    # Optional external-CI deployment remains fail-closed and secret-backed.
    require(".github/workflows/deploy-cloudflare.yml", "authorization_state")
    require(".github/workflows/deploy-cloudflare.yml", "CLOUDFLARE_API_TOKEN")
    require(".github/workflows/deploy-cloudflare.yml", "CLOUDFLARE_ACCOUNT_ID")
    require(".github/workflows/deploy-cloudflare.yml", "npx wrangler deploy")

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

    print("PPF Cloudflare reference contract validation passed.")


if __name__ == "__main__":
    main()
