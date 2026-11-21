#!/usr/bin/env bash
set -Eeuo pipefail
sed -n 's/^set(PROJECT_VERSION "\([^"]*\)").*/\1/p' CMakeLists.txt | head -n1
