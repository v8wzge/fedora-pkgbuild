#!/usr/bin/env bash
# Download the newest GitHub release asset into an rpmbuild SOURCES staging dir.
#
# Usage:
#   prepare-release-source.sh REPO ASSET_NAME OUT_NAME OUTDIR [INCLUDE_PRERELEASE]
set -Eeuo pipefail

REPO=$1
ASSET_NAME=$2
OUT_NAME=$3
OUTDIR=$4
INCLUDE_PRE=${5:-true}

HERE=$(cd "$(dirname "$0")" && pwd)
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

read -r TAG VERSION URL ASSET_ID UPDATED < <(
    python3 "$HERE/find_release.py" "$REPO" "$ASSET_NAME" "$INCLUDE_PRE"
)

curl --fail --location --silent --show-error "$URL" -o "$WORK/$OUT_NAME"

mkdir -p "$OUTDIR"
cp "$WORK/$OUT_NAME" "$OUTDIR/$OUT_NAME"
printf '%s\n' "$VERSION" > "$OUTDIR/.version"
printf '%s\n' "$TAG" > "$OUTDIR/.tag"
printf '%s:%s:%s\n' "$TAG" "$ASSET_ID" "$UPDATED" > "$OUTDIR/.fingerprint"

echo "Prepared $OUT_NAME from $REPO $TAG"
