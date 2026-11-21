#!/usr/bin/env python3
"""Probe WeChat Linux official download page."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import emit, fail, fetch, first

PAGE = "https://linux.weixin.qq.com/"

html = fetch(PAGE)
version = first(r'class="main-section__bd-version"[^>]*>([^<]+)<', html)
urls = [
    ("x86_64", "rpm", "https://dldir1v6.qq.com/weixin/Universal/Linux/WeChatLinux_x86_64.rpm"),
    ("aarch64", "rpm", "https://dldir1v6.qq.com/weixin/Universal/Linux/WeChatLinux_arm64.rpm"),
    ("loongarch64", "rpm", "https://dldir1v6.qq.com/weixin/Universal/Linux/WeChatLinux_LoongArch.rpm"),
]

# The page advertises the links; only keep architectures actually present.
packages = []
for arch, fmt, url in urls:
    marker = url.rsplit("/", 1)[-1]
    if marker in html:
        packages.append({"arch": arch, "format": fmt, "url": url})

if not packages:
    fail("no official RPM links found on WeChat page")

emit({
    "package": "wechat",
    "name": "微信 Linux 版",
    "version": version,
    "homepage": PAGE,
    "source": PAGE,
    "packages": packages,
})
