#!/usr/bin/env bash
# Build a source tarball from a git branch snapshot.
#
# Usage:
#   prepare-git-source.sh GIT_URL BRANCH NAME VERSION_SCRIPT OUTDIR
#
# VERSION_SCRIPT is executed with the checkout as its working directory and
# must print the upstream version to stdout.
set -Eeuo pipefail

GIT_URL=$1
BRANCH=$2
NAME=$3
VERSION_SCRIPT=$4
OUTDIR=$5

WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

git clone --quiet --depth 1 --branch "$BRANCH" "$GIT_URL" "$WORK/checkout"

COMMIT=$(git -C "$WORK/checkout" rev-parse HEAD)
SHORT=${COMMIT:0:7}
DATE=$(git -C "$WORK/checkout" log -1 --date=format:%Y%m%d --format=%cd)
VERSION=$(cd "$WORK/checkout" && bash "$VERSION_SCRIPT" | tail -n1)
[[ -n "$VERSION" ]] || { echo "ERROR: empty version from $VERSION_SCRIPT" >&2; exit 1; }

STAGE="$WORK/$NAME-$VERSION"
mkdir -p "$STAGE"
cp -a "$WORK/checkout/." "$STAGE/"
rm -rf "$STAGE/.git"

mkdir -p "$OUTDIR"
tar -C "$WORK" -czf "$OUTDIR/$NAME-$VERSION.tar.gz" "$NAME-$VERSION"

printf '%s\n' "$COMMIT"   > "$OUTDIR/.commit"
printf '%s\n' "$SHORT"    > "$OUTDIR/.shortcommit"
printf '%s\n' "$DATE"     > "$OUTDIR/.date"
printf '%s\n' "$VERSION"  > "$OUTDIR/.version"

echo "Prepared $NAME-$VERSION from $BRANCH@$SHORT"
