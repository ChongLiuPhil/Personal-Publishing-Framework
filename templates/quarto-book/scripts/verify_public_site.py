#!/usr/bin/env python3
"""Read-only runtime probe for a PPF Web publication.

This is a reference helper, not a PPF conformance requirement. It verifies
HTTP success, UTF-8 HTML, representative paths, optional text markers, and a
bounded sample of local assets. Git/provider revision provenance must be
verified separately from provider build/deployment metadata.
"""

from __future__ import annotations

import argparse
import html.parser
import sys
import urllib.error
import urllib.parse
import urllib.request

USER_AGENT = "ppf-reference-runtime-probe/1.0"
TIMEOUT = 25


class AssetParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.refs: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = dict(attrs)
        for key in ("href", "src"):
            value = attr_map.get(key)
            if value:
                self.refs.add(value)


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def fetch(url: str, max_bytes: int | None = None) -> tuple[int, bytes, str]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            status = getattr(response, "status", 200)
            body = response.read(max_bytes) if max_bytes else response.read()
            return status, body, response.geturl()
    except (urllib.error.URLError, TimeoutError) as exc:
        fail(f"{url}: {exc}")
    raise AssertionError("unreachable")


def local_asset(ref: str) -> bool:
    parsed = urllib.parse.urlparse(ref)
    if parsed.scheme or parsed.netloc:
        return False
    clean = ref.split("#", 1)[0].split("?", 1)[0]
    if not clean:
        return False
    return clean.endswith(
        (".css", ".js", ".png", ".jpg", ".jpeg", ".svg", ".webp", ".woff", ".woff2")
    ) or "site_libs/" in clean


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("base_url")
    parser.add_argument(
        "--path",
        action="append",
        dest="paths",
        help="Representative path to verify; repeat as needed. Defaults to /.",
    )
    parser.add_argument(
        "--expect",
        action="append",
        default=[],
        help="UTF-8 text marker expected in the first verified page; repeat as needed.",
    )
    parser.add_argument("--asset-limit", type=int, default=20)
    args = parser.parse_args()

    paths = args.paths or ["/"]
    base = args.base_url.rstrip("/") + "/"
    html_by_path: dict[str, str] = {}

    for path in paths:
        url = urllib.parse.urljoin(base, path.lstrip("/"))
        status, body, final_url = fetch(url)
        if status != 200:
            fail(f"{url}: expected HTTP 200, got {status}")
        try:
            text = body.decode("utf-8")
        except UnicodeDecodeError as exc:
            fail(f"{url}: response is not valid UTF-8: {exc}")
        html_by_path[path] = text
        print(f"PASS page {path} -> {status} ({final_url})")

    first = html_by_path[paths[0]]
    for marker in args.expect:
        if marker not in first:
            fail(f"{paths[0]}: missing expected text marker {marker!r}")

    assets: set[str] = set()
    for body in html_by_path.values():
        p = AssetParser()
        p.feed(body)
        assets.update(ref for ref in p.refs if local_asset(ref))

    checked = 0
    for ref in sorted(assets)[: max(args.asset_limit, 0)]:
        url = urllib.parse.urljoin(base, ref)
        status, _, final_url = fetch(url, max_bytes=4096)
        if status != 200:
            fail(f"asset {url}: expected HTTP 200, got {status}")
        checked += 1
        print(f"PASS asset {ref} -> {status} ({final_url})")

    print(
        f"Runtime probe passed for {base}: {len(paths)} page(s), "
        f"{checked} local asset(s), UTF-8 content verified."
    )
    print(
        "NOTE: verify expected Git/source revision and incumbent-production health "
        "from provider/repository evidence separately before cutover."
    )


if __name__ == "__main__":
    main()
