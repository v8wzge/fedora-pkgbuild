#!/usr/bin/env bash
# Generate vendor repodata whose package locations point at the GitHub
# Release assets, then stage it into the gh-pages checkout.
#
# Usage:
#   generate_repodata.sh STAGING_DIR REPO_DIR PREFIX
#
#   STAGING_DIR  directory holding the staged *.rpm + manifest.json
#   REPO_DIR     gh-pages checkout; repodata is written to REPO_DIR/vendor/
#   PREFIX       release download URL prefix, e.g.
#                https://github.com/OWNER/REPO/releases/download/vendor-rpms/
#
# createrepo_c reads each RPM's own NEVRA for dependency resolution but uses
# the on-disk filename for <location href>. With --location-prefix that href
# becomes an absolute Release URL, so dnf downloads the package from GitHub
# (fast, stable, no vendor signature) instead of from this git repository.
set -Eeuo pipefail

STAGING=$1
REPO=$2
PREFIX=${3%/}   # strip trailing slash; createrepo joins with "/filename"

command -v createrepo_c >/dev/null || { echo "createrepo_c is required" >&2; exit 1; }
[[ -d "$STAGING" ]] || { echo "staging dir missing: $STAGING" >&2; exit 1; }

rpm_count=$(find "$STAGING" -maxdepth 1 -type f -name '*.rpm' | wc -l)
if [[ "$rpm_count" -eq 0 ]]; then
    echo "No staged RPMs in $STAGING" >&2
    exit 1
fi

# Write repodata into the staging dir itself (it contains only our RPMs plus
# two JSON manifests, which createrepo ignores).
createrepo_c --database --location-prefix "$PREFIX" "$STAGING"

mkdir -p "$REPO/vendor"
rm -rf "$REPO/vendor/repodata"
cp -a "$STAGING/repodata" "$REPO/vendor/repodata"

echo "Staged repodata for $rpm_count vendor RPMs -> $REPO/vendor/repodata"
echo "Sample location href:"
python3 - "$STAGING/repodata" <<'PY' || true
import glob, gzip, re, sys, zstandard
folder = sys.argv[1]
primary = glob.glob(folder + "/*primary.xml.*")
if not primary:
    sys.exit(0)
raw = open(primary[0], "rb").read()
if primary[0].endswith(".gz"):
    raw = gzip.decompress(raw)
elif primary[0].endswith(".zst"):
    raw = zstandard.ZstdDecompressor().decompress(raw)
text = raw.decode(errors="replace")
for href in re.findall(r'<location href="([^"]+)"', text)[:3]:
    print("  " + href)
PY
