#!/usr/bin/env bash
# Publish the generated download index into the gh-pages repository.
#
# Usage:
#   publish-index.sh REPO_DIR INDEX_FILE
#
# Uses the same repository and the same `rpm-build` concurrency group as the
# RPM builders, so publishes never race on the gh-pages branch.
set -Eeuo pipefail

REPO=$1
INDEX=$2

mkdir -p "$REPO/downloads"
cp -f "$INDEX" "$REPO/downloads/index.json"

git -C "$REPO" add -A downloads/index.json
if git -C "$REPO" diff --cached --quiet; then
    echo "Download index unchanged; nothing to publish"
    exit 0
fi

git -C "$REPO" \
    -c user.name="fedora-pkgbuild bot" \
    -c user.email="bot@users.noreply.github.com" \
    commit -q -m "Update official download index"

git -C "$REPO" fetch --quiet origin gh-pages
if ! git -C "$REPO" merge-base --is-ancestor origin/gh-pages HEAD; then
    git -C "$REPO" pull --rebase --quiet origin gh-pages || {
        echo "ERROR: gh-pages changed concurrently; publish aborted" >&2
        exit 1
    }
fi

git -C "$REPO" push --quiet origin HEAD:gh-pages
echo "Published download index to $REPO/downloads/index.json"
