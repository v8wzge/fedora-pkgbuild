#!/usr/bin/env python3
"""Probe WPS Office Linux official download page."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import emit, fail, fetch, first

PAGE = "https://linux.wps.cn/"

html = fetch(PAGE)
# Version is embedded in the RPM filename, e.g.
# wps-office-12.1.2.29183.AK....x86_64.rpm
rpm = first(r'(https://[^"\'\s>]+\.rpm)', html)
version = first(r'wps-office-(\d+\.\d+\.\d+\.\d+)', rpm)

# WPS's CDN requires a time-limited MD5 signature. The secret key is shipped
# publicly in the download page's inline JavaScript; read it from there so a
# key rotation is picked up automatically. It is not a credential.
sign_key = first(r'var\s+secrityKey\s*=\s*"([0-9a-f]+)"', html)

arch = "x86_64"
if "aarch64" in rpm or "arm64" in rpm:
    arch = "aarch64"
elif "loongarch" in rpm.lower():
    arch = "loongarch64"

emit({
    "package": "wps-office",
    "name": "WPS Office Linux 版",
    "version": version,
    "homepage": PAGE,
    "source": PAGE,
    "packages": [{
        "arch": arch,
        "format": "rpm",
        "url": rpm,
        "sign": "wps-md5-path-ts",
        "sign_key": sign_key,
    }],
})
