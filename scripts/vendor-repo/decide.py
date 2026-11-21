#!/usr/bin/env python3
"""Compare probed versions with the last published state.

Usage:
    decide.py INDEX_FILE STATE_FILE [ARCH ...]

Default architecture set is x86_64 only, matching fetch_rpms.py. The
fingerprint must cover exactly the artifacts the build would download,
otherwise an aarch64-only change would trigger a pointless rebuild.
"""
import hashlib
import json
import os
import pathlib
import sys

index = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
state_file = pathlib.Path(sys.argv[2])
wanted_arches = set(sys.argv[3:]) if len(sys.argv) > 3 else {"x86_64"}

pairs = []
for item in index.get("packages", []):
    urls = sorted(
        artifact.get("url", "")
        for artifact in item.get("packages", [])
        if artifact.get("format") == "rpm" and artifact.get("arch") in wanted_arches
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
