#!/usr/bin/env python3
"""Check a declared model/client runtime against Film OS task requirements."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {"supported", "unsupported", "unknown"}


def parse_policy(path: Path) -> dict[str, dict[str, object]]:
    """Read the small task_profiles subset without third-party packages."""
    lines = path.read_text(encoding="utf-8").splitlines()
    profiles: dict[str, dict[str, object]] = {}
    in_profiles = False
    current: str | None = None
    current_list: str | None = None
    for line in lines:
        if line == "task_profiles:":
            in_profiles = True
            continue
        if in_profiles and line and not line.startswith(" "):
            break
        match = re.match(r"^  ([a-z0-9_]+):$", line)
        if in_profiles and match:
            current = match.group(1)
            profiles[current] = {"required": [], "preferred": []}
            current_list = None
            continue
        match = re.match(r"^    (required|preferred):$", line)
        if current and match:
            current_list = match.group(1)
            continue
        match = re.match(r"^      - ([a-z0-9_]+)$", line)
        if current and current_list and match:
            profiles[current][current_list].append(match.group(1))  # type: ignore[union-attr]
            continue
        match = re.match(r"^    fallback:\s*(\S+)\s*$", line)
        if current and match:
            profiles[current]["fallback"] = match.group(1)
            current_list = None
    if not profiles:
        raise RuntimeError(f"模型策略缺少 task_profiles：{path}")
    return profiles


def parse_capabilities(path: Path) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    capabilities: dict[str, str] = {}
    in_capabilities = False
    for line in lines:
        if line == "capabilities:":
            in_capabilities = True
            continue
        if in_capabilities and line and not line.startswith(" "):
            break
        match = re.match(r"^  ([a-z0-9_]+):\s*(\S+)\s*$", line)
        if in_capabilities and match:
            capabilities[match.group(1)] = match.group(2)
    if not capabilities:
        raise RuntimeError("能力报告缺少 capabilities。")
    return capabilities


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Film OS model runtime compatibility.")
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--task", required=True)
    parser.add_argument("--policy", type=Path, default=ROOT / "MODEL_POLICY.yaml")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        profiles = parse_policy(args.policy)
        if args.task not in profiles:
            raise RuntimeError(f"未知任务类型：{args.task}")
        capabilities = parse_capabilities(args.report)
        invalid = sorted(key for key, value in capabilities.items() if value not in ALLOWED)
        if invalid:
            raise RuntimeError("能力值无效：" + ", ".join(invalid))
        profile = profiles[args.task]
        required = list(profile.get("required", []))
        preferred = list(profile.get("preferred", []))
        missing = [name for name in required if capabilities.get(name, "unknown") != "supported"]
        preferred_missing = [name for name in preferred if capabilities.get(name, "unknown") != "supported"]
        status = "compatible" if not missing else "restricted"
        print(f"status={status}")
        print(f"task={args.task}")
        if missing:
            print("missing_required=" + ",".join(missing))
            print("fallback=" + str(profile.get("fallback", "stop")))
        if preferred_missing:
            print("missing_preferred=" + ",".join(preferred_missing))
        return 0 if not missing else 2
    except Exception as exc:
        print(f"Film OS model compatibility check failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
