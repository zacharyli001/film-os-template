#!/usr/bin/env python3
"""Inspect a member package from a verified director workspace; never apply it."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

from check_local_authority import authority_hash


def scalar_fields(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line[0].isspace():
            continue
        match = re.match(r"^([a-z_]+):\s*[\"']?(.*?)[\"']?\s*$", line)
        if match:
            result[match.group(1)] = match.group(2)
    return result


def director_verified(project: Path) -> bool:
    expected = authority_hash(project / "governance/AUTHORITY.yaml")
    key = project / ".film-os-local/DIRECTOR.key"
    if not expected or not key.is_file():
        return False
    actual = hashlib.sha256(key.read_text(encoding="utf-8").strip().encode("utf-8")).hexdigest()
    return actual == expected


def snapshot_matches_commit(project: Path, snapshot: Path, commit: str) -> tuple[bool, list[str]]:
    tree = subprocess.run(
        ["git", "ls-tree", "-r", "--full-tree", "-z", commit],
        cwd=project,
        check=True,
        capture_output=True,
    ).stdout
    expected: dict[str, str] = {}
    for record in tree.split(b"\0"):
        if not record:
            continue
        metadata, raw_path = record.split(b"\t", 1)
        _mode, kind, object_id = metadata.decode("ascii").split()
        if kind == "blob":
            expected[raw_path.decode("utf-8")] = object_id

    actual_paths = {
        path.relative_to(snapshot).as_posix()
        for path in snapshot.rglob("*")
        if path.is_file() and not path.is_symlink()
    }
    problems: list[str] = []
    for missing in sorted(set(expected) - actual_paths):
        problems.append(f"基线缺少：{missing}")
    for extra in sorted(actual_paths - set(expected)):
        problems.append(f"基线多出：{extra}")
    for relative in sorted(set(expected) & actual_paths):
        object_id = subprocess.run(
            ["git", "hash-object", str(snapshot / relative)],
            cwd=project,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        if object_id != expected[relative]:
            problems.append(f"基线被改动：{relative}")
    return not problems, problems


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--package", required=True, type=Path)
    args = parser.parse_args()
    try:
        project = args.project.expanduser().resolve()
        package = args.package.expanduser().resolve()
        if not director_verified(project):
            raise PermissionError("当前工作区没有通过导演本地钥匙验证，只能保持成员增量模式。")
        manifest = package / "PACKAGE.yaml"
        snapshot = package / "00_正式基线只读"
        delta = package / "01_个人增量"
        if not manifest.is_file() or not snapshot.is_dir() or not delta.is_dir():
            raise RuntimeError("交付包结构不完整。")
        fields = scalar_fields(manifest)
        if fields.get("status") != "non_canonical_proposal":
            raise RuntimeError("交付包状态无效；外部包必须是 non_canonical_proposal。")
        base = fields.get("base_commit", "")
        exists = subprocess.run(
            ["git", "cat-file", "-e", f"{base}^{{commit}}"], cwd=project, capture_output=True
        ).returncode == 0
        if not exists:
            raise RuntimeError("成员包声称的正式基线在当前导演项目中不存在。")
        snapshot_ok, snapshot_problems = snapshot_matches_commit(project, snapshot, base)
        if not snapshot_ok:
            raise RuntimeError("成员包的正式基线不是原始快照：" + "；".join(snapshot_problems[:10]))
        current = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=project, check=True, capture_output=True, text=True
        ).stdout.strip()
        files = [str(path.relative_to(delta)) for path in delta.rglob("*") if path.is_file()]
        report = {
            "role": "director_verified",
            "package_id": fields.get("package_id"),
            "author_id": fields.get("author_id"),
            "package_status": "non_canonical_proposal",
            "base_commit_exists_in_canonical_project": exists,
            "base_snapshot_exact": snapshot_ok,
            "base_is_current_head": base == current,
            "delta_files": files,
            "action": "review_only_no_canonical_files_changed",
        }
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(f"Film OS package inspection stopped safely: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
