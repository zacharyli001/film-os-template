#!/usr/bin/env python3
"""Identify whether this local Film OS workspace holds the director key."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys


def authority_hash(path: Path) -> str | None:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"^\s*local_key_sha256:\s*([0-9a-f]{64}|null)\s*$", text, re.MULTILINE)
    if not match or match.group(1) == "null":
        return None
    return match.group(1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, default=Path.cwd())
    args = parser.parse_args()
    root = args.project.expanduser().resolve()
    authority = root / "governance/AUTHORITY.yaml"
    key = root / ".film-os-local/DIRECTOR.key"

    expected = authority_hash(authority) if authority.is_file() else None
    actual = None
    if key.is_file():
        actual = hashlib.sha256(key.read_text(encoding="utf-8").strip().encode("utf-8")).hexdigest()
    is_director = bool(expected and actual and expected == actual)
    result = {
        "role": "director" if is_director else "contributor",
        "canonical_write_allowed": is_director,
        "member_package_mode_required": not is_director,
        "reason": "local_director_key_verified" if is_director else "verified_director_key_not_present",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if is_director else 2


if __name__ == "__main__":
    raise SystemExit(main())
