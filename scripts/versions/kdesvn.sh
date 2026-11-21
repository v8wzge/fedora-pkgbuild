#!/usr/bin/env bash
set -Eeuo pipefail
# kdesvn keeps its version in CMakeLists.txt as three separate macros.
exec python3 - <<'PY'
import pathlib
import re

text = pathlib.Path("CMakeLists.txt").read_text(encoding="utf-8")
parts = dict(re.findall(r"set\(KDESVN_VERSION_(MAJOR|MINOR|PATCH)\s+(\d+)\)", text))
if set(parts) != {"MAJOR", "MINOR", "PATCH"}:
    raise SystemExit("cannot determine kdesvn version")
print(".".join(parts[k] for k in ("MAJOR", "MINOR", "PATCH")))
PY
