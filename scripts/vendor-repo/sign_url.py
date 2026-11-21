#!/usr/bin/env python3
"""Produce a downloadable URL for a vendor RPM.

Two callers share these recipes:

* ``install-from-index.sh`` signs on the client (kept inline there so the
  script stays standalone when fetched with curl | bash).
* ``fetch_rpms.py`` signs at BUILD time. The downloaded RPM is then re-hosted
  in a GitHub Release, so the dnf client never sees an expiring URL.

Supported schemes:
  none             fixed URL, no signature (WeChat)
  wps-md5-path-ts  MD5(secKey + path + unix_ts) -> ?t=&k= (WPS)
  qq-urlsign       official noauth UrlSign RPC (QQ)
"""
import hashlib
import json
import sys
import time
import urllib.parse
import urllib.request


def sign(url, method, key=""):
    if not method or method == "none":
        return url

    if method == "wps-md5-path-ts":
        path = urllib.parse.urlparse(url).path
        ts = int(time.time())
        sig = hashlib.md5((key + path + str(ts)).encode()).hexdigest()
        return f"{url}?t={ts}&k={sig}"

    if method == "qq-urlsign":
        endpoint = (
            "https://im.qq.com/http2rpc/gotrpc/noauth/"
            "trpc.qqntv2.urlsign.UrlSign/GetSign"
        )
        body = json.dumps({"url": url}).encode()
        req = urllib.request.Request(endpoint, data=body, method="POST", headers={
            "Content-Type": "application/json",
            "x-oidb": '{"uint32_command":"0x9b8e","uint32_service_type":1}',
            "User-Agent": "Mozilla/5.0",
        })
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read())
        if result.get("retcode") != 0 or not result.get("data", {}).get("url"):
            raise RuntimeError(f"QQ URL signing failed: {result}")
        return result["data"]["url"]

    raise ValueError(f"Unknown sign method: {method}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit("usage: sign_url.py URL METHOD [KEY]")
    print(sign(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else ""))
