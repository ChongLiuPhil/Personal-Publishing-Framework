#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

QUARTO_BIN="$(bash scripts/ensure_quarto.sh)"
QUARTO="${QUARTO_BIN}" make web-publish-check
