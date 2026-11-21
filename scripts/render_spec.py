#!/usr/bin/env python3
"""Render a spec file for a build by replacing Version and snapshot globals."""
import argparse
import pathlib
import re

parser = argparse.ArgumentParser()
parser.add_argument("--spec", required=True)
parser.add_argument("--out", required=True)
parser.add_argument("--version", required=True)
parser.add_argument("--commit")
parser.add_argument("--date")
args = parser.parse_args()

text = pathlib.Path(args.spec).read_text(encoding="utf-8")


def replace_once(pattern, replacement, label):
    global text
    text, count = re.subn(pattern, replacement, text, flags=re.MULTILINE)
    if count != 1:
        raise SystemExit(f"expected exactly one {label} line, found {count}")


replace_once(r"^Version:\s*\S+\s*$", f"Version:        {args.version}", "Version:")
if args.commit:
    replace_once(r"^%global commit\s+\S+\s*$", f"%global commit  {args.commit}", "%global commit")
if args.date:
    replace_once(r"^%global commitdate\s+\S+\s*$", f"%global commitdate  {args.date}", "%global commitdate")

out = pathlib.Path(args.out)
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(text, encoding="utf-8")
print(f"Rendered {out}")
