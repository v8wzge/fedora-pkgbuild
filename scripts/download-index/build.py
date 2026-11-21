#!/usr/bin/env python3
"""Aggregate all per-package probes into one downloads index.

Usage:
    build.py PROBES_DIR OUT_FILE

Runs every ``*.py`` probe in PROBES_DIR (except common.py), collects the
JSON records, and writes a single index file. A failing probe is recorded
in the index with an ``error`` field instead of aborting the whole run, so
one vendor changing its page cannot break the others.
"""
import datetime
import json
import pathlib
import subprocess
import sys

probes_dir = pathlib.Path(sys.argv[1])
out_file = pathlib.Path(sys.argv[2])

python = sys.executable
packages = []
errors = []

for probe in sorted(probes_dir.glob("*.py")):
    if probe.name in ("common.py", "__init__.py"):
        continue
    package_id = probe.stem
    try:
        result = subprocess.run(
            [python, str(probe)],
            capture_output=True, text=True, timeout=90, check=True,
        )
        record = json.loads(result.stdout)
        record["status"] = "ok"
    except Exception as exc:  # noqa: BLE001 - keep other packages usable
        stderr = ""
        if hasattr(exc, "stderr") and exc.stderr:
            stderr = exc.stderr.strip().splitlines()[-1]
        record = {
            "package": package_id,
            "status": "error",
            "error": stderr or str(exc),
        }
        errors.append(package_id)
        print(f"WARNING: probe {package_id} failed: {record['error']}", file=sys.stderr)
    packages.append(record)

index = {
    "schema_version": 1,
    "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "description": "Official Linux RPM download addresses. Clients fetch these URLs directly from the vendor.",
    "packages": sorted(packages, key=lambda item: item.get("package", "")),
}

out_file.parent.mkdir(parents=True, exist_ok=True)
out_file.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Wrote {out_file} ({len(packages)} packages, {len(errors)} errors)")
if errors:
    print(f"Failed probes: {', '.join(errors)}", file=sys.stderr)
