from pathlib import Path
import re
import subprocess
import sys
import tempfile

import yaml


ROOT = Path(__file__).resolve().parents[1]
CORE_REPOSITORIES = [
    "https://github.com/ChongLiuPhil/AI-Assisted-Human-Inquiry-and-Creation-Protocol",
    "https://github.com/ChongLiuPhil/Personal-Publishing-Framework",
    "https://github.com/ChongLiuPhil/Vault-interface",
    "https://github.com/ChongLiuPhil/Inquiry-Publishing-Project-Starter",
]


def main() -> int:
    manifest = yaml.safe_load((ROOT / "ecosystem.yaml").read_text())
    if not isinstance(manifest, dict):
        raise SystemExit("ecosystem.yaml must contain a mapping")
    if not any(key in manifest for key in ("agent_entrypoint", "ecosystem_entrypoint", "canonical_entrypoint")):
        raise SystemExit("ecosystem.yaml is missing an agent/ecosystem entrypoint")
    public_delivery = manifest.get("public_delivery")
    if not isinstance(public_delivery, dict):
        raise SystemExit("ecosystem.yaml is missing public_delivery")
    if public_delivery.get("current_provider") != "github-pages":
        raise SystemExit("PPF must keep GitHub Pages current before verified cutover")
    if public_delivery.get("preferred_provider") != "cloudflare-workers":
        raise SystemExit("PPF preferred public delivery for new projects must be Cloudflare Workers")
    if public_delivery.get("cutover_rule") != "keep-current-public-urls-until-verified-cloudflare-deployment":
        raise SystemExit("PPF public URL cutover rule is missing or unsafe")
    cloudflare = manifest.get("cloudflare", {})
    if cloudflare.get("integration_standard") != "docs/GITHUB_CLOUDFLARE_INTEGRATION.md":
        raise SystemExit("ecosystem.yaml must point to the GitHub–Cloudflare integration standard")
    for relative in ("docs/GITHUB_CLOUDFLARE_INTEGRATION.md", "docs/GITHUB_CLOUDFLARE_INTEGRATION.zh-CN.md"):
        if not (ROOT / relative).is_file():
            raise SystemExit(f"missing GitHub–Cloudflare integration guide: {relative}")

    manifest_text = (ROOT / "ecosystem.yaml").read_text()
    for repository in CORE_REPOSITORIES:
        if repository not in manifest_text:
            raise SystemExit(f"ecosystem.yaml is missing {repository}")
    for relative in ("README.md", "README.zh-CN.md"):
        text = (ROOT / relative).read_text()
        if "ecosystem.yaml" not in text and "docs/ECOSYSTEM" not in text:
            raise SystemExit(f"{relative} does not point to the ecosystem entrypoint")
    page = (ROOT / "docs/index.html").read_text(encoding="utf-8")
    if '<main id="zh" class="lang active">' not in page:
        raise SystemExit("PPF homepage must keep Chinese visible as a no-JavaScript fallback")
    required_homepage_markers = [
        "Source · 源内容",
        "Build · 构建",
        "Publish · 发布",
        "Release · 版本",
        "Archive · 归档",
        "https://chongliuphil.github.io/Inquiry-Publishing-Project-Starter/agent/",
    ]
    for marker in required_homepage_markers:
        if marker not in page:
            raise SystemExit(f"homepage is missing required architecture/discovery marker: {marker}")

    scripts = re.findall(r"<script>(.*?)</script>", page, flags=re.DOTALL)
    if not scripts:
        raise SystemExit("PPF homepage has no inline script to validate")
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".js", delete=False) as handle:
        handle.write("\n".join(scripts))
        script_path = handle.name
    try:
        check = subprocess.run(["node", "--check", script_path], capture_output=True, text=True, check=False)
    except FileNotFoundError as exc:
        raise SystemExit("Node.js is required to validate homepage JavaScript") from exc
    if check.returncode != 0:
        raise SystemExit("PPF homepage JavaScript syntax error:\n" + check.stderr)

    print("ecosystem + homepage validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
