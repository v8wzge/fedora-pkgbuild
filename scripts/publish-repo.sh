#!/usr/bin/env bash
# Copy freshly built RPMs into the gh-pages dnf repository and publish it.
#
# Usage:
#   publish-repo.sh REPO_DIR ARTIFACT_DIR PACKAGE STATE_FILE
set -Eeuo pipefail

REPO=$1
ARTIFACTS=$2
PACKAGE=$3
STATE_FILE=$4

mkdir -p "$REPO"/{x86_64,noarch,SRPMS,state}

# Drop previous builds of this package so only one version is served.
find "$REPO" -maxdepth 2 -type f -name "${PACKAGE}-*.rpm" -delete

shopt -s nullglob
for rpm in "$ARTIFACTS"/*.rpm; do
    case "$rpm" in
        *.src.rpm)    target="$REPO/SRPMS/" ;;
        *.noarch.rpm) target="$REPO/noarch/" ;;
        *)            target="$REPO/x86_64/" ;;
    esac
    cp -f "$rpm" "$target"
done
shopt -u nullglob

cp -f "$STATE_FILE" "$REPO/state/$PACKAGE.json"

(
    cd "$REPO"
    createrepo_c --database .
)

git -C "$REPO" add -A
if git -C "$REPO" diff --cached --quiet; then
    echo "No repository changes to publish for $PACKAGE"
    exit 0
fi

git -C "$REPO" \
    -c user.name="fedora-pkgbuild bot" \
    -c user.email="bot@users.noreply.github.com" \
    commit -q -m "Update $PACKAGE RPM"

git -C "$REPO" push --quiet
echo "Published $PACKAGE to the RPM repository"
