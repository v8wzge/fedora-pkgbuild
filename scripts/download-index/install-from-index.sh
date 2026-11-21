#!/usr/bin/env bash
# Install an official Linux RPM by looking it up in the hosted download index.
#
# The index only stores vendor URLs; the RPM itself is downloaded directly
# from the vendor. Some vendors require a time-limited signed URL, which is
# generated on the client at download time (never stored in the index).
#
# Usage:
#   install-from-index.sh PACKAGE [arch]
#   install-from-index.sh --list
set -Eeuo pipefail

INDEX_URL="${DOWNLOAD_INDEX_URL:-https://raw.githubusercontent.com/v8wzge/fedora-pkgbuild/gh-pages/downloads/index.json}"
CACHE="${XDG_CACHE_HOME:-$HOME/.cache}/v8wzge-download-index.json"

command -v curl >/dev/null || { echo "curl is required" >&2; exit 1; }
command -v dnf >/dev/null || { echo "dnf is required" >&2; exit 1; }
PY=/usr/bin/python3
command -v "$PY" >/dev/null || PY=python3

mkdir -p "$(dirname "$CACHE")"
curl -fsSL "$INDEX_URL" -o "$CACHE.tmp" || {
    echo "Could not fetch the download index from $INDEX_URL" >&2
    exit 1
}
mv -f "$CACHE.tmp" "$CACHE"

if [[ "${1:-}" == "--list" ]]; then
    "$PY" - "$CACHE" <<'PYCODE'
import json, sys
index = json.load(open(sys.argv[1]))
for item in index["packages"]:
    if item.get("status") != "ok":
        print(f"{item['package']:<12} ERROR: {item.get('error','unknown')}")
        continue
    arches = ",".join(p["arch"] for p in item["packages"] if p["format"] == "rpm")
    print(f"{item['package']:<12} {item['version']:<20} [{arches}]  {item['name']}")
PYCODE
    exit 0
fi

PACKAGE="${1:-}"
if [[ -z "$PACKAGE" ]]; then
    echo "Usage: $0 PACKAGE [arch]  |  $0 --list" >&2
    exit 1
fi
ARCH="${2:-$(uname -m)}"

# Resolve the unsigned vendor URL and the signing method from the index.
read -r URL FILENAME SIGN_METHOD SIGN_KEY < <("$PY" - "$CACHE" "$PACKAGE" "$ARCH" <<'PYCODE'
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
print(rpm["url"], rpm["url"].rsplit("/", 1)[-1],
      rpm.get("sign", "none"), rpm.get("sign_key", ""), sep="\t")
PYCODE
)

# Apply the vendor's time-limited signing scheme, if the entry needs one.
# Signing happens here so the signature is always fresh; the index only
# stores stable unsigned URLs and the signing recipe.
FINAL_URL=$("$PY" - "$URL" "$SIGN_METHOD" "$SIGN_KEY" <<'PYCODE'
import hashlib, json, sys, time, urllib.parse, urllib.request
url, method, key = sys.argv[1], sys.argv[2], sys.argv[3]
if method == "none" or not method:
    print(url)
elif method == "wps-md5-path-ts":
    # WPS: MD5(secret + pathname + unix_ts) appended as ?t=&k=
    path = urllib.parse.urlparse(url).path
    ts = int(time.time())
    sig = hashlib.md5((key + path + str(ts)).encode()).hexdigest()
    print(f"{url}?t={ts}&k={sig}")
elif method == "qq-urlsign":
    # QQ: POST to the official noauth UrlSign RPC used by im.qq.com/linux.
    endpoint = "https://im.qq.com/http2rpc/gotrpc/noauth/trpc.qqntv2.urlsign.UrlSign/GetSign"
    body = json.dumps({"url": url}).encode()
    req = urllib.request.Request(endpoint, data=body, method="POST", headers={
        "Content-Type": "application/json",
        "x-oidb": '{"uint32_command":"0x9b8e","uint32_service_type":1}',
        "User-Agent": "Mozilla/5.0",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        result = json.loads(r.read())
    if result.get("retcode") != 0 or not result.get("data", {}).get("url"):
        sys.exit(f"QQ URL signing failed: {result}")
    print(result["data"]["url"])
else:
    sys.exit(f"Unknown sign method: {method}")
PYCODE
)

TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT
FILE="$TMPDIR/$FILENAME"

echo "Downloading $PACKAGE ($ARCH) from the official vendor URL..."
curl -fL --retry 3 --progress-bar -A "Mozilla/5.0" "$FINAL_URL" -o "$FILE"

echo "Installing $FILE with dnf (this will request sudo if needed)..."
if [[ $EUID -eq 0 ]]; then
    dnf -y install "$FILE"
else
    sudo dnf -y install "$FILE"
fi
