#!/usr/bin/env python3
"""Reject non-director changes that are not append-only proposal bundles."""

from __future__ import annotations

import argparse
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys


UTC_ID = re.compile(r"^\d{8}T\d{6}Z_[a-z0-9][a-z0-9-]*$")
UTC_TIME = re.compile(r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})Z$")
GITHUB_USER = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$")


def git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True, text=True
    )
    return completed.stdout


def scalar_fields(path: Path) -> dict[str, str]:
    """Read only the top-level scalar fields needed by the guard."""
    result: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line or raw_line[0].isspace() or raw_line.lstrip().startswith("#"):
            continue
        match = re.match(r"^([a-z_]+):\s*(.*?)\s*$", raw_line)
        if not match:
            continue
        value = match.group(2)
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        result[match.group(1)] = value
    return result


def fail(messages: list[str]) -> int:
    print("Film OS 主线权限检查未通过：", file=sys.stderr)
    for message in messages:
        print(f"- {message}", file=sys.stderr)
    print("请撤销对已有文件的改动，把建议及其所有衍生成果放进你自己的同一个提案包。", file=sys.stderr)
    return 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--actor", required=True)
    parser.add_argument("--head-ref", required=True)
    parser.add_argument("--director", required=True)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.repo.resolve()
    actor = args.actor.strip()
    director = args.director.strip()

    if not GITHUB_USER.fullmatch(actor) or not GITHUB_USER.fullmatch(director):
        return fail(["提交人或导演的 GitHub 用户名格式无效。"])

    if actor.casefold() == director.casefold():
        print("Film OS authority check passed: director promotion authority.")
        return 0

    expected_prefix = f"proposal/{actor}/"
    errors: list[str] = []
    if not args.head_ref.startswith(expected_prefix):
        errors.append(f"成员分支必须以 {expected_prefix} 开头。")

    try:
        changed = git(root, "diff", "--name-status", "--no-renames", args.base, args.head)
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        return fail([f"无法读取 Git 变更：{exc}"])

    proposal_roots: set[PurePosixPath] = set()
    rows = [line.split("\t", 1) for line in changed.splitlines() if line.strip()]
    if not rows:
        errors.append("没有检测到可审核的新增文件。")

    for row in rows:
        if len(row) != 2:
            errors.append(f"无法识别变更记录：{' '.join(row)}")
            continue
        status, raw_path = row
        path = PurePosixPath(raw_path)
        if status != "A":
            errors.append(f"成员不能修改、删除或重命名已有文件：{raw_path}（{status}）。")
            continue
        parts = path.parts
        if len(parts) < 4 or parts[0] != "submissions" or parts[1].casefold() != actor.casefold():
            errors.append(f"成员新增内容只能放在 submissions/{actor}/一个提案包内：{raw_path}。")
            continue
        proposal_id = parts[2]
        if not UTC_ID.fullmatch(proposal_id):
            errors.append(f"提案目录必须是 UTC时间_英文短名：{proposal_id}。")
        proposal_roots.add(PurePosixPath("submissions", parts[1], proposal_id))

    if len(proposal_roots) > 1:
        errors.append("一个 Pull Request 只能提交一个提案包；不同想法必须分别审核。")

    for proposal_root in proposal_roots:
        manifest_rel = proposal_root / "PROPOSAL.yaml"
        manifest = root / manifest_rel
        if not manifest.is_file():
            errors.append(f"提案包缺少 {manifest_rel}。")
            continue
        fields = scalar_fields(manifest)
        expected_id = proposal_root.name
        expected = {
            "schema_version": "film-os/proposal/v1",
            "proposal_id": expected_id,
            "author_github": actor,
            "base_main_commit": args.base,
            "status": "proposed",
        }
        missing = [key for key in (*expected, "created_at") if not fields.get(key)]
        if missing:
            errors.append(f"{manifest_rel} 缺少字段：{', '.join(missing)}。")
        for key, value in expected.items():
            if fields.get(key) and fields[key].casefold() != value.casefold():
                errors.append(f"{manifest_rel} 的 {key} 必须是 {value}。")

        created = fields.get("created_at", "")
        time_match = UTC_TIME.fullmatch(created)
        if created and not time_match:
            errors.append(f"{manifest_rel} 的 created_at 必须是 UTC ISO-8601 时间。")
        elif time_match:
            year, month, day, hour, minute, second = time_match.groups()
            compact = f"{year}{month}{day}T{hour}{minute}{second}Z"
            if not expected_id.startswith(compact + "_"):
                errors.append(f"提案目录时间必须与 {manifest_rel} 的 created_at 一致。")

        expected_branch = f"proposal/{actor}/{expected_id}"
        if args.head_ref != expected_branch:
            errors.append(f"这个提案的分支必须准确命名为 {expected_branch}。")

    if errors:
        return fail(errors)
    print("Film OS authority check passed: one append-only proposal bundle.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
