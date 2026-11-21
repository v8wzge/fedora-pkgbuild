#!/usr/bin/env bash
# Build binary and source RPMs from a staged SOURCES directory.
#
# Usage:
#   build-rpm.sh SPEC SOURCES_DIR OUT_DIR [rpmbuild extra args...]
set -Eeuo pipefail

SPEC=$1
SOURCES=$2
OUTDIR=$3
shift 3

TOP=${RPM_TOP:-"$PWD/.rpmbuild"}
mkdir -p "$TOP"/{BUILD,BUILDROOT,RPMS,SOURCES,SPECS,SRPMS}

# Only real files: the staging dir also holds hidden .commit/.version markers.
find "$SOURCES" -maxdepth 1 -type f ! -name '.*' -exec cp -a {} "$TOP/SOURCES/" \;
cp -a "$SPEC" "$TOP/SPECS/"

SPECNAME=$(basename "$SPEC")
dnf -y --setopt=install_weak_deps=False builddep "$TOP/SPECS/$SPECNAME" >/dev/null

rpmbuild -ba --define "_topdir $TOP" "$TOP/SPECS/$SPECNAME" "$@"

mkdir -p "$OUTDIR"
find "$TOP/RPMS" -type f -name '*.rpm' -exec cp -a {} "$OUTDIR/" \;
find "$TOP/SRPMS" -type f -name '*.src.rpm' -exec cp -a {} "$OUTDIR/" \;

echo "Built RPMs in $OUTDIR"
