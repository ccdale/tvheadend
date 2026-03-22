#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$script_dir"

tmp_file="$(mktemp)"
trap 'rm -f "$tmp_file"' EXIT

makepkg --printsrcinfo > "$tmp_file"

if cmp -s "$tmp_file" .SRCINFO; then
    echo ".SRCINFO is in sync with PKGBUILD"
    exit 0
fi

echo ".SRCINFO is out of sync with PKGBUILD"
echo "Run: makepkg --printsrcinfo > .SRCINFO"
diff -u .SRCINFO "$tmp_file" || true
exit 1
