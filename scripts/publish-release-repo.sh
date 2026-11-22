#!/usr/bin/env bash
# Publish freshly built RPMs to the shared GitHub Release and refresh the dnf
# metadata in the gh-pages branch. Binary packages never enter git; repodata's
# location href points straight at the Release assets to stay below the
# repository size limit.
#
# Usage:
#   publish-release-repo.sh REPO_DIR ARTIFACT_DIR PACKAGE STATE_FILE
set -Eeuo pipefail

REPO=$1
ARTIFACTS=$2
PACKAGE=$3
STATE_FILE=$4
RELEASE_TAG=${RELEASE_TAG:-packages}
RELEASE_PREFIX=${RELEASE_PREFIX:-https://github.com/${GITHUB_REPOSITORY}/releases/download/${RELEASE_TAG}}

HERE=$(cd "$(dirname "$0")" && pwd)
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

command -v createrepo_c >/dev/null || { echo "createrepo_c is required" >&2; exit 1; }

# Assets previously owned by this package can be removed once the new manifest
# is uploaded (publish_release.py skips names that are still referenced).
STALE="$WORK/stale.json"
python3 - "$REPO/state/assets/$PACKAGE.json" "$STALE" <<'PY'
import json, pathlib, sys
old = pathlib.Path(sys.argv[1])
names = list(json.loads(old.read_text(encoding="utf-8")).keys()) if old.is_file() else []
pathlib.Path(sys.argv[2]).write_text(json.dumps(names), encoding="utf-8")
PY

python3 "$HERE/publish_release.py" "$RELEASE_TAG" "$ARTIFACTS" \
    "$WORK/urls.json" "$STALE"

mkdir -p "$REPO/state/assets"
cp -f "$WORK/urls.json" "$REPO/state/assets/$PACKAGE.json"

# Collect every package's current asset URLs, download the RPMs into one staging
# directory and generate a single repository that still contains all packages.
python3 - "$REPO/state/assets" > "$WORK/assets.tsv" <<'PY'
import json, pathlib, sys
folder = pathlib.Path(sys.argv[1])
for manifest in sorted(folder.glob("*.json")):
    for name, url in json.loads(manifest.read_text(encoding="utf-8")).items():
        print(f"{name}\t{url}")
PY

if [[ ! -s "$WORK/assets.tsv" ]]; then
    echo "No repository assets registered" >&2
    exit 1
fi

mkdir -p "$WORK/allrpms"
while IFS=$'\t' read -r name url; do
    if [[ ! -f "$WORK/allrpms/$name" ]]; then
        echo "Fetching metadata for $name"
        curl --fail --location --silent --show-error "$url" -o "$WORK/allrpms/$name"
    fi
done < "$WORK/assets.tsv"

# Source RPMs stay in the Release but should not appear in the binary repo.
mkdir -p "$WORK/srpms"
find "$WORK/allrpms" -maxdepth 1 -type f -name '*.src.rpm' \
    -exec mv -t "$WORK/srpms" {} +

createrepo_c --database --location-prefix "$RELEASE_PREFIX" "$WORK/allrpms"

mkdir -p "$REPO"
rm -rf "$REPO/repodata"
cp -a "$WORK/allrpms/repodata" "$REPO/repodata"

cp -f "$STATE_FILE" "$REPO/state/$PACKAGE.json"

# Keep the installable .repo file on the Pages site so clients never need to
# reach raw.githubusercontent.com (which is unreliable in some networks).
if [[ -f "$HERE/../repo/v8wzge-fedora.repo" ]]; then
    cp -f "$HERE/../repo/v8wzge-fedora.repo" "$REPO/v8wzge-fedora.repo"
fi

# Old-style in-repo RPM directories are obsolete; remove them if present.
for dir in x86_64 noarch SRPMS; do
    if [[ -d "$REPO/$dir" ]]; then
        git -C "$REPO" rm -r -q --cached "$dir" 2>/dev/null || true
        rm -rf "$REPO/$dir"
    fi
done

git -C "$REPO" add -A
if git -C "$REPO" diff --cached --quiet; then
    echo "No repository changes to publish for $PACKAGE"
    exit 0
fi

git -C "$REPO" \
    -c user.name="fedora-pkgbuild bot" \
    -c user.email="bot@users.noreply.github.com" \
    commit -q -m "Update $PACKAGE RPM repository metadata"

git -C "$REPO" fetch --quiet origin gh-pages
if ! git -C "$REPO" merge-base --is-ancestor origin/gh-pages HEAD; then
    git -C "$REPO" pull --rebase --quiet origin gh-pages || {
        echo "ERROR: gh-pages changed concurrently; publish aborted" >&2
        exit 1
    }
fi

git -C "$REPO" push --quiet origin HEAD:gh-pages
echo "Published $PACKAGE metadata; RPMs live at $RELEASE_PREFIX"
