#!/usr/bin/env python3
"""Shared helpers for per-package download probes.

Each probe prints ONE JSON object to stdout describing the newest official
Linux RPM. The schema is stable so the aggregator does not need to know
anything about individual vendors.

Schema:
  package     short package id (matches the probe filename)
  name        display name
  version     upstream version string
  homepage    official product page
  source      human-readable version source
  updated     ISO-8601 timestamp of the check (UTC)
  packages    list of artifacts:
    arch      x86_64 / aarch64 / loongarch64 ...
    format    rpm / deb / appimage
    url       direct official download URL
"""
import datetime
import json
import re
import sys
import urllib.error
import urllib.request

UA = "Mozilla/5.0 (X11; Linux x86_64) fedora-pkgbuild download-index/1.0"


def fetch(url, timeout=30, encoding="utf-8"):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        data = response.read()
    if encoding:
        return data.decode(encoding, errors="replace")
    return data


def emit(record):
    record.setdefault("updated", datetime.datetime.now(datetime.timezone.utc).isoformat())
    json.dump(record, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


def fail(message):
    print(f"probe error: {message}", file=sys.stderr)
    raise SystemExit(1)


def first(pattern, text, group=1, flags=0):
    match = re.search(pattern, text, flags)
    if not match:
        fail(f"pattern not found: {pattern}")
    return match.group(group).strip()


__all__ = ["fetch", "emit", "fail", "first", "UA"]
