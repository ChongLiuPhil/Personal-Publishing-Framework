#!/usr/bin/env bash
set -euo pipefail

VERSION="${QUARTO_VERSION:-1.10.18}"
CACHE_ROOT="${PPF_TOOL_CACHE_DIR:-${HOME}/.cache/ppf}"
INSTALL_DIR="${CACHE_ROOT}/quarto/${VERSION}"
QUARTO_BIN="${INSTALL_DIR}/bin/quarto"

if [[ -x "${QUARTO_BIN}" ]]; then
  printf '%s\n' "${QUARTO_BIN}"
  exit 0
fi

case "$(uname -m)" in
  x86_64|amd64)
    ASSET="quarto-${VERSION}-linux-amd64.tar.gz"
    SHA256="afad071b5bd22c02f2d300695743189d3650e0537a53073e654b630cff2b0c73"
    ;;
  aarch64|arm64)
    ASSET="quarto-${VERSION}-linux-arm64.tar.gz"
    SHA256="f6a07df68e25330b5df34f65d3df66bca605acce3b830c593a58e91884d4cf6c"
    ;;
  *)
    echo "Unsupported architecture for pinned Quarto installer: $(uname -m)" >&2
    exit 1
    ;;
esac

URL="https://github.com/quarto-dev/quarto-cli/releases/download/v${VERSION}/${ASSET}"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT

curl --fail --location --retry 3 "${URL}" --output "${TMP_DIR}/${ASSET}"
printf '%s  %s\n' "${SHA256}" "${TMP_DIR}/${ASSET}" | sha256sum --check --status

mkdir -p "${INSTALL_DIR}"
tar -xzf "${TMP_DIR}/${ASSET}" -C "${INSTALL_DIR}" --strip-components=1

test -x "${QUARTO_BIN}"
printf '%s\n' "${QUARTO_BIN}"
