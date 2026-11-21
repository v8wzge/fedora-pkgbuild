#!/usr/bin/env python3
"""Probe QQ Linux official download configuration."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import emit, fail, fetch

# Official config used by https://im.qq.com/linux ; primary CDN with
# Tencent proxy as fallback (mirrors the vendor page's own loader).
URLS = [
    "https://qq-web.cdn-go.cn/im.qq.com_new/latest/rainbow/pcConfig.json",
    "https://im.qq.com/proxy/domain/qq-web.cdn-go.cn/im.qq.com_new/latest/rainbow/pcConfig.json",
]

config = None
last_error = None
for url in URLS:
    try:
        config = json.loads(fetch(url))
        break
    except Exception as exc:  # noqa: BLE001 - try next mirror
        last_error = exc
if config is None:
    fail(f"could not load QQ config: {last_error}")

linux = config.get("Linux")
if not isinstance(linux, dict):
    fail("QQ config has no Linux section")

version = str(linux.get("version", "")).strip()
if not version:
    fail("QQ config has no Linux version")

packages = []
for arch, key in (("x86_64", "x64DownloadUrl"), ("aarch64", "armDownloadUrl")):
    entry = linux.get(key)
    if isinstance(entry, dict) and entry.get("rpm"):
        packages.append({"arch": arch, "format": "rpm", "url": entry["rpm"]})

if not packages:
    fail("no official RPM links found in QQ config")

emit({
    "package": "qq",
    "name": "QQ Linux 版",
    "version": version,
    "homepage": "https://im.qq.com/linux",
    "source": URLS[0],
    "packages": packages,
})
