#!/usr/bin/env python3
"""Find the newest GitHub release asset matching a filename pattern.

Prints six tab-separated fields:
    tag  version  asset_url  asset_id  updated_at  filename

Used for upstream projects that publish ready-made RPMs whose filenames embed
the version (e.g. Clash.Verge-2.5.10-1.x86_64.rpm).
"""
import json
import os
import sys
import urllib.request

repo = sys.argv[1]
prefix = sys.argv[2]
suffix = sys.argv[3] if len(sys.argv) > 3 else ".rpm"
include_pre = (sys.argv[4].lower() in {"1", "true", "yes"}
               if len(sys.argv) > 4 else True)

headers = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "fedora-pkgbuild",
}
token = os.environ.get("GITHUB_TOKEN", "")
if token:
    headers["Authorization"] = f"Bearer {token}"

url = f"https://api.github.com/repos/{repo}/releases?per_page=100"
with urllib.request.urlopen(
    urllib.request.Request(url, headers=headers), timeout=60
) as response:
    releases = json.load(response)


def rpm_version(tag):
    return tag.lstrip("vV").replace("-", "~")


for release in releases:
    if release.get("draft"):
        continue
    if release.get("prerelease") and not include_pre:
        continue
    asset = next(
        (a for a in release.get("assets", [])
         if a["name"].startswith(prefix) and a["name"].endswith(suffix)
         and not a["name"].endswith(".sig")),
        None,
    )
    if asset is None:
        continue
    print("\t".join([
        release["tag_name"],
        rpm_version(release["tag_name"]),
        asset["browser_download_url"],
        str(asset["id"]),
        asset.get("updated_at", ""),
        asset["name"],
    ]))
    break
else:
    raise SystemExit(
        f"no release of {repo} contains an asset matching {prefix}*{suffix}"
    )
