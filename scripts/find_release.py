#!/usr/bin/env python3
"""Find the newest GitHub release that contains a given asset.

Prints five tab-separated fields:
    tag  version  asset_url  asset_id  updated_at

Releases are returned newest-first by the GitHub API and prereleases are
included by default, so this also picks up beta releases.
"""
import json
import os
import sys
import urllib.request

repo = sys.argv[1]
asset_name = sys.argv[2]
include_pre = sys.argv[3].lower() in {"1", "true", "yes"} if len(sys.argv) > 3 else True

headers = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "fedora-pkgbuild",
}
token = os.environ.get("GITHUB_TOKEN", "")
if token:
    headers["Authorization"] = f"Bearer {token}"

url = f"https://api.github.com/repos/{repo}/releases?per_page=100"
request = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(request, timeout=60) as response:
    releases = json.load(response)


def rpm_version(tag):
    # RPM forbids '-' in Version, and '~' gives correct prerelease ordering.
    return tag.lstrip("vV").replace("-", "~")


for release in releases:
    if release.get("draft"):
        continue
    if release.get("prerelease") and not include_pre:
        continue
    asset = next((a for a in release.get("assets", []) if a["name"] == asset_name), None)
    if asset is None:
        continue
    print("\t".join([
        release["tag_name"],
        rpm_version(release["tag_name"]),
        asset["browser_download_url"],
        str(asset["id"]),
        asset.get("updated_at", ""),
    ]))
    break
else:
    raise SystemExit(f"no release of {repo} contains asset {asset_name}")
