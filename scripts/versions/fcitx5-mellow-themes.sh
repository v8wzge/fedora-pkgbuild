#!/usr/bin/env bash
# Print a sortable snapshot version for fcitx5-mellow-themes.
# The upstream repository has no tags or releases, so use the commit date.
git log -1 --date=format:%Y%m%d --format=%cd
