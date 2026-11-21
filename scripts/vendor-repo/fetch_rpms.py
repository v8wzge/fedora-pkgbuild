#!/usr/bin/env python3
"""Download the official x86_64 RPM referenced by the download index.

Usage:
    fetch_rpms.py INDEX_FILE STAGING_DIR [ARCH ...]

Only x86_64 is mirrored by default: pulling every architecture multiplies the
download volume (300-600 MB each) and raises the risk of vendor rate-limiting
or IP bans. Pass extra architectures explicitly if you ever need them.

Signing happens HERE at build time, not on the client. The RPM is stored in
STAGING_DIR under a stable filename::

    <package>-<version>-<arch>.rpm

A manifest.json is written into STAGING_DIR describing the staged files;
the publish step uploads them as GitHub Release assets and generates
repodata whose ``location`` points at those assets. That is how dnf ends up
fetching vendor RPMs from a stable URL with no client-side signature logic.
"""
import datetime
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import sys
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from sign_url import sign

UA = "Mozilla/5.0 (X11; Linux x86_64) fedora-pkgbuild vendor-repo/1.0"
RPM_MAGIC = b"\xed\xab\xee\xdb"
DOWNLOAD_TIMEOUT = 900  # vendor files are 300-600 MB


def safe_component(value):
    """Keep only characters safe in a release asset filename."""
    return re.sub(r"[^A-Za-z0-9._+~-]", "_", str(value))


def verify_rpm(path):
    with open(path, "rb") as handle:
        return handle.read(4) == RPM_MAGIC


def sha256_of(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def query_nevra(path):
    """Read the RPM's own NEVRA (authoritative for dnf's dependency solver)."""
    try:
        out = subprocess.check_output(
            ["rpm", "-qp", "--qf", "%{NAME}\t%{VERSION}\t%{RELEASE}\t%{ARCH}", str(path)],
            text=True,
        ).strip()
        name, version, release, arch = out.split("\t")
        return {"name": name, "version": version, "release": release, "arch": arch}
    except Exception:
        return None


def download(url, destination):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=DOWNLOAD_TIMEOUT) as response:
        with open(destination, "wb") as handle:
            shutil.copyfileobj(response, handle, length=1024 * 1024)


def main():
    index_file = pathlib.Path(sys.argv[1])
    staging = pathlib.Path(sys.argv[2])
    # Default to x86_64 only; extra architectures require an explicit opt-in.
    wanted_arches = set(sys.argv[3:]) if len(sys.argv) > 3 else {"x86_64"}
    staging.mkdir(parents=True, exist_ok=True)

    index = json.loads(index_file.read_text(encoding="utf-8"))
    entries = []
    failures = []

    for item in index.get("packages", []):
        if item.get("status") != "ok":
            failures.append({"package": item.get("package", "?"), "error": item.get("error", "stale probe")})
            continue
        for artifact in item.get("packages", []):
            if artifact.get("format") != "rpm":
                continue
            arch = artifact["arch"]
            if arch not in wanted_arches:
                print(f"Skipping {item['package']}/{arch} (not in requested arches: {','.join(sorted(wanted_arches))})")
                continue
            package = item["package"]
            version = item["version"]
            # Stage under the probe-based name first; after download we rename
            # to the RPM's own NEVRA (see below) so the asset filename reflects
            # the real package, not a possibly-drifted probe version string.
            probe_filename = f"{safe_component(package)}-{safe_component(version)}-{safe_component(arch)}.rpm"
            target = staging / probe_filename
            try:
                signed = sign(artifact["url"], artifact.get("sign", "none"), artifact.get("sign_key", ""))
                print(f"Downloading {package} {version} ({arch}) ...", flush=True)
                download(signed, target)
                if not verify_rpm(target):
                    raise RuntimeError("downloaded file is not an RPM (bad magic)")
                nevra = query_nevra(target)
                if nevra:
                    canonical = (
                        f"{safe_component(nevra['name'])}-{safe_component(nevra['version'])}-"
                        f"{safe_component(nevra['release'])}-{safe_component(nevra['arch'])}.rpm"
                    )
                    if canonical != probe_filename:
                        print(f"  NEVRA filename {canonical} (probe said {probe_filename})")
                        target.rename(target.with_name(canonical))
                        target = target.with_name(canonical)
                filename = target.name
                entries.append({
                    "package": package,
                    "name": item.get("name", package),
                    "version": version,
                    "arch": arch,
                    "filename": filename,
                    "size": target.stat().st_size,
                    "sha256": sha256_of(target),
                    "nevra": nevra,
                    "source": artifact["url"],
                    "sign": artifact.get("sign", "none"),
                })
                print(f"  -> {filename} ({target.stat().st_size / 1024 / 1024:.1f} MiB)", flush=True)
            except Exception as exc:  # keep unrelated artifacts usable
                target.unlink(missing_ok=True)
                message = f"{package}/{arch}: {type(exc).__name__}: {exc}"
                print(f"ERROR {message}", file=sys.stderr, flush=True)
                failures.append({"package": f"{package}/{arch}", "error": str(exc)})

    if not entries:
        sys.exit("No RPMs could be downloaded; refusing to publish an empty repository")

    manifest = {
        "schema_version": 1,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "description": "Official vendor RPMs staged for the v8wzge-vendor dnf repository.",
        "packages": sorted(entries, key=lambda e: (e["package"], e["arch"])),
        "failures": failures,
    }
    out = staging / "manifest.json"
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Staged {len(entries)} RPMs, {len(failures)} failures -> {out}")


if __name__ == "__main__":
    main()
