#!/usr/bin/env bash
# Publish the vendor repodata + state into the gh-pages branch.
#
# Usage:
#   publish-vendor.sh REPO_DIR [STATE_FILE]
#
# STATE_FILE is optional and only copied when it differs from the in-repo
# destination. The workflow normally writes state directly into
# REPO_DIR/state/vendor.json, so no copy is needed there.
set -Eeuo pipefail

REPO=$1
STATE=${2:-}

mkdir -p "$REPO/state"
if [[ -n "$STATE" && "$STATE" != "$REPO/state/vendor.json" ]]; then
    cp -f "$STATE" "$REPO/state/vendor.json"
fi

git -C "$REPO" add -A vendor state/vendor.json
if git -C "$REPO" diff --cached --quiet; then
    echo "Vendor repository unchanged; nothing to publish"
    exit 0
fi

git -C "$REPO" \
    -c user.name="fedora-pkgbuild bot" \
    -c user.email="bot@users.noreply.github.com" \
    commit -q -m "Update vendor RPM repository (WeChat/QQ/WPS)"

git -C "$REPO" fetch --quiet origin gh-pages
if ! git -C "$REPO" merge-base --is-ancestor origin/gh-pages HEAD; then
    git -C "$REPO" pull --rebase --quiet origin gh-pages || {
        echo "ERROR: gh-pages changed concurrently; publish aborted" >&2
        exit 1
    }
fi

git -C "$REPO" push --quiet origin HEAD:gh-pages
echo "Published vendor dnf repository"
