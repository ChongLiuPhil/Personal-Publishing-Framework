#!/usr/bin/env python3
"""Minimal provider-independent validation for a rendered PPF Web artifact."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / "_book"


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    index = BOOK / "index.html"
    if not index.is_file():
        fail("_book/index.html is missing")

    html_files = list(BOOK.rglob("*.html"))
    if not html_files:
        fail("no rendered HTML files found under _book/")

    forbidden = {".epub", ".pdf", ".docx", ".tex"}
    unexpected = [
        path.relative_to(BOOK)
        for path in BOOK.rglob("*")
        if path.is_file() and path.suffix.lower() in forbidden
    ]
    if unexpected:
        fail(
            "non-Web publication artifact(s) found inside _book/: "
            + ", ".join(str(item) for item in unexpected)
        )

    print(
        f"Web artifact verification passed: {len(html_files)} HTML file(s); "
        "no EPUB/PDF/DOCX/LaTeX artifact leaked into _book/."
    )


if __name__ == "__main__":
    main()
