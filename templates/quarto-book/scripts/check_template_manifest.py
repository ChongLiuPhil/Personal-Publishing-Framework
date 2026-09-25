#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
manifest=ROOT/"template-manifest.yaml"
body=manifest.read_text(encoding="utf-8")
for marker in (
    "template_version: 0.1.3-draft",
    "upstream_managed:",
    "merge_managed:",
    "project_owned:",
    "package-lock.json",
    "preserve-human-publication-authorization",
    "preserve-provider-actual-state",
    "never-write-secrets-to-git",
    "installable-template-does-not-imply-publication-authorization",
):
    if marker not in body:
        print(f"ERROR: template manifest missing {marker}",file=sys.stderr)
        raise SystemExit(1)
for path in (
    "project.infrastructure.json",
    "ci-cost-policy.yaml",
    ".gitignore",
    "publishing.yaml","cloudflare-builds.yaml","wrangler.jsonc","Makefile",
    "package.json","package-lock.json",
    "scripts/cloudflare_build.sh","scripts/ensure_quarto.sh",
    ".github/workflows/project-check.yml",
    ".github/workflows/web.yml",".github/workflows/cloudflare-contract-ci.yml",
    ".github/workflows/deploy-cloudflare.yml",
):
    if not (ROOT/path).is_file():
        raise SystemExit(f"ERROR: reference template missing {path}")
print("PPF template upgrade contract passed.")
