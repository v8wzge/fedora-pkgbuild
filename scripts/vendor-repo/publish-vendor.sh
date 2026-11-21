#!/usr/bin/env bash
# Publish the vendor repodata + state into the gh-pages branch.
#
# Usage:
#   publish-vendor.sh REPO_DIR STATE_FILE
#
# Shares the `rpm-build` concurrency group with every other publisher, and
# guards against a concurrent push the same way scripts/publish-repo.sh does.
set -Eeuo pipefail

REPO=$1
STATE=$2

mkdir -p "$REPO/state"
cp -f "$STATE" "$REPO/state/vendor.json"

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
