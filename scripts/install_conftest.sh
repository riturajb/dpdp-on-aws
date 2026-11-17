#!/usr/bin/env bash
# Installs conftest, which runs the Rego rules in policies/rego against Terraform plans.
#
# What:        Downloads the conftest version named in config/tool-versions.env from its GitHub
#              release, checks the download against the release's published SHA-256 checksum,
#              and installs it in ~/.local/bin.
# Why:         The plan check (scripts/plan_check.sh) and test T12 need it. Pinning the version
#              and checking the checksum means the same, untampered tool runs everywhere.
# Who runs it: Anyone, once per laptop; GitHub Actions runs it in every check.
# When:        Release 3, Step 2.
# Reads:       config/tool-versions.env.   Writes: ~/.local/bin/conftest.
# Changes AWS: No.
#
#   scripts/install_conftest.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/config/tool-versions.env"
V="${CONFTEST_VERSION:?CONFTEST_VERSION is not set in config/tool-versions.env}"
DEST="$HOME/.local/bin"

case "$(uname -m)" in
  x86_64) ARCH="x86_64" ;;
  aarch64 | arm64) ARCH="arm64" ;;
  *) echo "STOP: unsupported machine type $(uname -m)"; exit 1 ;;
esac
FILE="conftest_${V}_Linux_${ARCH}.tar.gz"
URL="https://github.com/open-policy-agent/conftest/releases/download/v${V}"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
if ! curl -fsSL -o "$TMP/$FILE" "$URL/$FILE" || ! curl -fsSL -o "$TMP/checksums.txt" "$URL/checksums.txt"; then
  echo "STOP: could not download conftest v${V}."
  echo "Check that this version exists at https://github.com/open-policy-agent/conftest/releases"
  echo "and, if not, set CONFTEST_VERSION in config/tool-versions.env to a listed version."
  exit 1
fi
# The download must match the checksum published with the release.
(cd "$TMP" && grep " ${FILE}\$" checksums.txt | sha256sum -c --quiet -) \
  || { echo "STOP: checksum mismatch for $FILE. Nothing was installed."; exit 1; }

mkdir -p "$DEST"
tar -xzf "$TMP/$FILE" -C "$TMP" conftest
install -m 0755 "$TMP/conftest" "$DEST/conftest"
echo "Installed: $("$DEST/conftest" --version | head -1)"
case ":$PATH:" in
  *":$DEST:"*) ;;
  *) echo "Note: $DEST is not on your PATH yet. Close and reopen the terminal, or run: export PATH=\"$DEST:\$PATH\"" ;;
esac
