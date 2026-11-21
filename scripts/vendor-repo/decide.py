#!/usr/bin/env python3
"""Compare probed versions with the last published state.

Usage:
    decide.py INDEX_FILE STATE_FILE

Prints tab-separated key=value lines for GITHUB_OUTPUT:
    changed=true|false
    fingerprint=<sha256 over (package, status, version, artifact URLs)>

The fingerprint is computed from the probe result alone -- BEFORE any large
download. Vendor URLs embed build identifiers (QQ's release hash, WPS's build
number), so a repackaged build at the same advertised version still changes
the URL and is detected. Only WeChat uses a fixed URL, where a same-version
repack cannot be distinguished from the version string; use a forced
workflow_dispatch run for that case.
"""
import hashlib
import json
import os
import pathlib
import sys

index = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
state_file = pathlib.Path(sys.argv[2])

pairs = []
for item in index.get("packages", []):
    urls = sorted(
        artifact.get("url", "")
        for artifact in item.get("packages", [])
        if artifact.get("format") == "rpm"
    )
    pairs.append([
        item.get("package", "?"),
        item.get("status", "?"),
        item.get("version", item.get("error", "")),
        urls,
    ])
if not pairs:
    sys.exit("probe produced no packages")

fingerprint = hashlib.sha256(
    json.dumps(pairs, ensure_ascii=False, sort_keys=True).encode()
).hexdigest()

last = ""
if state_file.is_file():
    try:
        last = json.loads(state_file.read_text(encoding="utf-8")).get("fingerprint", "")
    except Exception:
        last = ""

force = os.environ.get("FORCE", "").strip().lower() == "true"
changed = force or fingerprint != last

print(f"changed={'true' if changed else 'false'}\tfingerprint={fingerprint}")
