#!/usr/bin/env python3
"""Publish staged RPMs to one shared GitHub Release and write a URL manifest.

Usage:
    publish_release.py TAG STAGING_DIR MANIFEST_OUT [DELETE_LIST]

Environment:
    GITHUB_TOKEN      token with `contents: write` on GITHUB_REPOSITORY
    GITHUB_REPOSITORY owner/repo (falls back to the workflow's repository)

All packages share a single Release so the dnf repository only needs one
release-download URL prefix. Assets are named after the RPM file itself, so a
new upstream version creates a new stable URL and old assets can be removed
once no repository metadata references them.
"""
import json
import os
import pathlib
import sys
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.github.com"
UPLOADS = "https://uploads.github.com"


def api(method, path, token, payload=None, raw=None, content_type=None,
        host=API, allow_404=False):
    url = host + path
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "fedora-pkgbuild",
    }
    data = None
    if payload is not None:
        data = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json"
    elif raw is not None:
        data = raw
        headers["Content-Type"] = content_type or "application/octet-stream"

    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=300) as response:
            body = response.read()
            return json.loads(body) if body else None
    except urllib.error.HTTPError as exc:
        if allow_404 and exc.code == 404:
            return None
        detail = exc.read().decode(errors="replace")
        raise RuntimeError(
            f"GitHub API {method} {path} -> HTTP {exc.code}: {detail}"
        ) from exc


def main():
    tag, staging_dir, manifest_out = sys.argv[1:4]
    staging = pathlib.Path(staging_dir)
    delete_list = pathlib.Path(sys.argv[4]) if len(sys.argv) > 4 else None

    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        sys.exit("GITHUB_TOKEN is required")
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if "/" not in repo:
        sys.exit("GITHUB_REPOSITORY must be OWNER/REPO")
    owner, repo_name = repo.split("/", 1)

    rpms = sorted(staging.glob("*.rpm"))
    if not rpms:
        sys.exit(f"no RPMs staged in {staging}")

    release = api("GET", f"/repos/{owner}/{repo_name}/releases/tags/{tag}",
                  token, allow_404=True)
    if release is None:
        release = api("POST", f"/repos/{owner}/{repo_name}/releases", token, payload={
            "tag_name": tag,
            "name": "Built RPM packages",
            "body": "Binary and source RPMs published by the fedora-pkgbuild "
                    "workflows. Install through the dnf repository; the repodata "
                    "in the gh-pages branch points at these assets.",
            "draft": False,
            "prerelease": False,
        })
    release_id = release["id"]

    existing = api("GET", f"/repos/{owner}/{repo_name}/releases/{release_id}/assets",
                   token) or []
    current = {asset["name"]: asset for asset in existing}

    urls = {}
    for path in rpms:
        # GitHub Release normalizes '~' in asset names to '.', so the
        # manifest key (and therefore repodata location href) must use
        # the same sanitized name. Keep '~' in the RPM header Version
        # for correct prerelease ordering.
        name = path.name.replace("~", ".")
        if name in current:
            # The filename encodes the upstream version, but a rebuild of the
            # same version can still change content (e.g. an updated grammar
            # model). Always replace so the Release never serves stale bytes.
            print(f"Replacing existing asset {name}")
            api("DELETE",
                f"/repos/{owner}/{repo_name}/releases/assets/{current[name]['id']}",
                token)
        print(f"Uploading {name} ({path.stat().st_size / 1024 / 1024:.1f} MiB) ...",
              flush=True)
        with open(path, "rb") as handle:
            data = handle.read()
        asset = api(
            "POST",
            f"/repos/{owner}/{repo_name}/releases/{release_id}/assets?name="
            + urllib.parse.quote(name),
            token, raw=data, content_type="application/octet-stream", host=UPLOADS,
        )
        urls[name] = asset["browser_download_url"]

    if delete_list and delete_list.is_file():
        stale = json.loads(delete_list.read_text(encoding="utf-8"))
        for name in stale:
            asset = current.get(name)
            if asset and name not in urls:
                print(f"Deleting stale asset {name}")
                api("DELETE",
                    f"/repos/{owner}/{repo_name}/releases/assets/{asset['id']}",
                    token)

    pathlib.Path(manifest_out).write_text(
        json.dumps(urls, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Published {len(urls)} assets -> {manifest_out}")


if __name__ == "__main__":
    main()
