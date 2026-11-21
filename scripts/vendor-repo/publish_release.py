#!/usr/bin/env python3
"""Mirror staged vendor RPMs into a dedicated GitHub Release.

Usage:
    publish_release.py REPO TAG STAGING_DIR

Environment:
    GITHUB_TOKEN   token with `contents: write` on REPO

Called after fetch_rpms.py. We keep exactly one asset per staged filename:
stale versions are deleted so the release never grows without bound, and each
remaining asset URL is stable across runs (the filename encodes
package-version-arch). That stable URL is what createrepo_c writes into the
repodata as location href, so dnf fetches from here instead of the vendor.
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
        with urllib.request.urlopen(req, timeout=180) as response:
            body = response.read()
            return json.loads(body) if body else None
    except urllib.error.HTTPError as exc:
        if allow_404 and exc.code == 404:
            return None
        detail = exc.read().decode(errors="replace")
        raise RuntimeError(f"GitHub API {method} {path} -> HTTP {exc.code}: {detail}") from exc


def main():
    repo, tag, staging_dir = sys.argv[1], sys.argv[2], pathlib.Path(sys.argv[3])
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        sys.exit("GITHUB_TOKEN is required")
    if "/" not in repo:
        sys.exit("REPO must be OWNER/REPO")

    manifest = json.loads((staging_dir / "manifest.json").read_text(encoding="utf-8"))
    staged = {item["filename"]: item for item in manifest["packages"]}
    if not staged:
        sys.exit("manifest has no packages")

    owner, repo_name = repo.split("/", 1)
    release = api("GET", f"/repos/{owner}/{repo_name}/releases/tags/{tag}",
                  token, allow_404=True)
    if release is None:
        release = api("POST", f"/repos/{owner}/{repo_name}/releases", token, payload={
            "tag_name": tag,
            "name": "Official vendor RPMs (WeChat / QQ / WPS)",
            "body": "Mirror of official Linux RPMs for the v8wzge-vendor dnf repository. "
                    "Install through the dnf repo, not by direct asset download.",
            "draft": False,
            "prerelease": False,
        })
    release_id = release["id"]

    existing = api("GET", f"/repos/{owner}/{repo_name}/releases/{release_id}/assets", token) or []
    current = {asset["name"]: asset for asset in existing}

    for asset in existing:
        if asset["name"] not in staged:
            print(f"Deleting stale asset {asset['name']}")
            api("DELETE", f"/repos/{owner}/{repo_name}/releases/assets/{asset['id']}", token)

    urls = {}
    for filename, item in sorted(staged.items()):
        if filename in current:
            # Same version already hosted; bytes are unchanged, so no re-upload.
            urls[filename] = current[filename]["browser_download_url"]
            print(f"Asset {filename} already current")
            continue
        path = staging_dir / filename
        print(f"Uploading {filename} ({path.stat().st_size / 1024 / 1024:.1f} MiB) ...", flush=True)
        with open(path, "rb") as handle:
            data = handle.read()
        query = urllib.parse.quote(filename)
        asset = api(
            "POST",
            f"/repos/{owner}/{repo_name}/releases/{release_id}/assets?name={query}",
            token, raw=data, content_type="application/octet-stream", host=UPLOADS,
        )
        urls[filename] = asset["browser_download_url"]

    out = staging_dir / "release-urls.json"
    out.write_text(json.dumps(urls, indent=2) + "\n", encoding="utf-8")
    print(f"Published {len(urls)} assets -> {out}")


if __name__ == "__main__":
    main()
