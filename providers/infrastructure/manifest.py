#!/usr/bin/env python3
"""Validate a project's intended GitHub and Cloudflare infrastructure state."""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "schema" / "project.infrastructure.schema.json"


def load_manifest(path: Path, schema_path: Path = SCHEMA_PATH) -> dict[str, Any]:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read infrastructure manifest or schema: {exc}") from exc
    if not isinstance(manifest, dict):
        raise ValueError("project.infrastructure.json must contain a JSON object")
    errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(manifest),
        key=lambda error: (list(error.absolute_path), error.message),
    )
    if errors:
        rendered = []
        for error in errors:
            location = ".".join(str(part) for part in error.absolute_path) or "<root>"
            rendered.append(f"{location}: {error.message}")
        raise ValueError("invalid project.infrastructure.json:\n" + "\n".join(rendered))
    validate_semantics(manifest)
    return manifest


def validate_semantics(manifest: dict[str, Any]) -> None:
    project = manifest["project"]
    github = manifest["github"]
    cloudflare = manifest["cloudflare"]
    deployment = manifest["deployment"]
    release = manifest["release"]

    if github["repository"].lower() != project["slug"]:
        raise ValueError("github.repository must match project.slug")
    if cloudflare["worker"] != project["slug"]:
        raise ValueError("cloudflare.worker must match project.slug")
    if github["productionBranch"] != deployment["productionBranch"]:
        raise ValueError("GitHub and Workers Builds productionBranch must match")
    if manifest["policy"]["privateByDefault"] is not True:
        raise ValueError("policy.privateByDefault must remain true")
    if cloudflare["applicationVisibility"] == "private" and cloudflare["publicBypass"]:
        raise ValueError("a private Worker must not have a public bypass")
    if cloudflare["applicationVisibility"] == "public" and not cloudflare["publicBypass"]:
        raise ValueError("a public Worker under account-wide Access requires a Worker-specific public bypass")
    if cloudflare["previewVisibility"] == "private" and not deployment["previewProtection"]:
        raise ValueError("private previews must have previewProtection enabled")
    if cloudflare["previewVisibility"] == "public" and deployment["previewProtection"]:
        raise ValueError("public preview visibility conflicts with previewProtection")
    if cloudflare["applicationVisibility"] == "public" and release["state"] != "public":
        raise ValueError("public application visibility requires release.state: public")
    if github["repositoryVisibility"] == "public" and not release["openSource"]:
        raise ValueError("public GitHub visibility requires release.openSource: true")
    if github["repositoryVisibility"] == "public" and release["state"] != "public":
        raise ValueError("public GitHub visibility requires release.state: public")
    if release["openSource"] and github["repositoryVisibility"] != "public":
        raise ValueError("release.openSource requires github.repositoryVisibility: public")
    if release["state"] in {"private", "release_candidate", "release_blocked"} and (
        github["repositoryVisibility"] == "public" or cloudflare["applicationVisibility"] == "public"
    ):
        raise ValueError("non-public release states cannot declare public repository or application visibility")
    if deployment["previewDeployments"] and cloudflare["previewVisibility"] == "private" and not deployment["previewProtection"]:
        raise ValueError("preview deployments cannot be enabled without preview protection")
    if cloudflare["customDomain"] and re.search(r"(?i)(^|\.)workers\.dev$", cloudflare["customDomain"]):
        raise ValueError("workers.dev cannot be declared as a custom domain")


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", nargs="?", type=Path, default=Path("project.infrastructure.json"))
    parser.add_argument("--schema", type=Path, default=SCHEMA_PATH)
    args = parser.parse_args(argv)
    try:
        manifest = load_manifest(args.manifest, args.schema)
    except ValueError as exc:
        print(f"CONFIGURATION_ERROR: {exc}")
        return 2
    print(json.dumps({"status": "valid", "projectId": manifest["project"]["id"], "slug": manifest["project"]["slug"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
