#!/usr/bin/env bash
# Install an official Linux RPM by looking it up in the hosted download index.
#
# The index only contains vendor URLs; the RPM itself is downloaded directly
# from the vendor, never through this repository.
#
# Usage:
#   install-from-index.sh PACKAGE [arch]
#
# Examples:
#   install-from-index.sh wechat
#   install-from-index.sh qq aarch64
#   install-from-index.sh --list
set -Eeuo pipefail

INDEX_URL="${DOWNLOAD_INDEX_URL:-https://v8wzge.github.io/fedora-pkgbuild/downloads/index.json}"
CACHE="${XDG_CACHE_HOME:-$HOME/.cache}/v8wzge-download-index.json"

command -v curl >/dev/null || { echo "curl is required" >&2; exit 1; }
command -v dnf >/dev/null || { echo "dnf is required" >&2; exit 1; }

mkdir -p "$(dirname "$CACHE")"
curl -fsSL "$INDEX_URL" -o "$CACHE.tmp" || {
    echo "Could not fetch the download index from $INDEX_URL" >&2
    exit 1
}
mv -f "$CACHE.tmp" "$CACHE"

if [[ "${1:-}" == "--list" ]]; then
    /usr/bin/python3 - "$CACHE" <<'PY'
import json, sys
index = json.load(open(sys.argv[1]))
for item in index["packages"]:
    if item.get("status") != "ok":
        print(f"{item['package']:<12} ERROR: {item.get('error','unknown')}")
        continue
    arches = ",".join(p["arch"] for p in item["packages"] if p["format"] == "rpm")
    print(f"{item['package']:<12} {item['version']:<20} [{arches}]  {item['name']}")
PY
    exit 0
fi

PACKAGE="${1:-}"
if [[ -z "$PACKAGE" ]]; then
    echo "Usage: $0 PACKAGE [arch]  |  $0 --list" >&2
    exit 1
fi
ARCH="${2:-$(uname -m)}"

read -r URL FILENAME < <(/usr/bin/python3 - "$CACHE" "$PACKAGE" "$ARCH" <<'PY'
import json, sys
index = json.load(open(sys.argv[1]))
package, arch = sys.argv[2], sys.argv[3]
item = next((p for p in index["packages"] if p["package"] == package), None)
if item is None:
    sys.exit(f"Package '{package}' is not in the index (try --list)")
if item.get("status") != "ok":
    sys.exit(f"Package '{package}' has a stale probe: {item.get('error','unknown')}")
rpm = next((p for p in item["packages"] if p["format"] == "rpm" and p["arch"] == arch), None)
if rpm is None:
    available = ",".join(p["arch"] for p in item["packages"] if p["format"] == "rpm")
    sys.exit(f"No RPM for {package} on {arch} (available: {available})")
print(rpm["url"], rpm["url"].rsplit("/", 1)[-1])
PY
)

TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT
FILE="$TMPDIR/$FILENAME"

echo "Downloading $PACKAGE ($ARCH) from the official vendor URL..."
curl -fL --retry 3 --progress-bar "$URL" -o "$FILE"

echo "Installing $FILE with dnf (this will request sudo if needed)..."
if [[ $EUID -eq 0 ]]; then
    dnf -y install "$FILE"
else
    sudo dnf -y install "$FILE"
fi
