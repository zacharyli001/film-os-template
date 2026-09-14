#!/usr/bin/env python3
"""Validate, commit, and prepare one isolated Film OS member proposal."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

from member_common import (
    changed_paths,
    current_branch,
    diff_paths,
    git,
    git_text,
    paths_outside,
    read_scalar_file,
    session_path,
    top_level_scalars,
    utc_now,
    validate_member_id,
    write_scalar_file,
    yaml_scalar,
)


PLACEHOLDER_MARKERS = (
    "请在提交前填写",
    "replace-with",
    "replace me",
    "pending_member",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="提交当前成员提案与全部衍生产出。")
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--member-id", required=True)
    parser.add_argument(
        "--push",
        action="store_true",
        help="允许脚本直接推送提案分支；默认只提交本地，由 GitHub Desktop 推送当前分支。",
    )
    return parser.parse_args()


def replace_scalar(text: str, key: str, value: str) -> str:
    pattern = re.compile(rf"(?m)^{re.escape(key)}:\s*.*$")
    replacement = f"{key}: {yaml_scalar(value)}"
    if pattern.search(text):
        return pattern.sub(replacement, text, count=1)
    return text.rstrip() + "\n" + replacement + "\n"


def validate_manifest(manifest: Path, member_id: str, session: dict[str, str]) -> dict[str, str]:
    text = manifest.read_text(encoding="utf-8")
    fields = top_level_scalars(text)
    if fields.get("schema_version") != "film-os/proposal/v1":
        raise RuntimeError("PROPOSAL.yaml 的 schema_version 不是 film-os/proposal/v1。")
    if fields.get("proposal_id") != session.get("proposal_id"):
        raise RuntimeError("PROPOSAL.yaml 的 proposal_id 与本次会话不一致。")
    author = fields.get("author_github", "")
    if author.lower() != member_id.lower():
        raise RuntimeError("PROPOSAL.yaml 的作者与本次成员 ID 不一致。")
    if fields.get("base_main_commit") != session.get("base_main_commit"):
        raise RuntimeError("PROPOSAL.yaml 的基线提交与开工会话不一致。")
    if fields.get("status") not in {"draft", "proposed"}:
        raise RuntimeError("提案状态不是可提交状态。")
    proposal_type = fields.get("proposal_type", "")
    if not proposal_type or "pending_member" in proposal_type:
        raise RuntimeError("请在 PROPOSAL.yaml 中填写 proposal_type。")
    summary = fields.get("summary", "")
    combined = summary + "\n" + text
    if not summary or any(marker in combined for marker in PLACEHOLDER_MARKERS):
        raise RuntimeError("请在 PROPOSAL.yaml 中填写真实的 summary 和提案说明。")
    return fields


def main() -> int:
    args = parse_args()
    workspace = args.workspace.expanduser().resolve()
    try:
        member_id = validate_member_id(args.member_id)
        session_file = session_path(workspace)
        if not session_file.is_file():
            raise RuntimeError("找不到开工会话；请先运行 member_workspace_start.py。")
        session = read_scalar_file(session_file)
        if session.get("member_id") != member_id:
            raise RuntimeError("成员 ID 与开工会话不一致。")
        branch = current_branch(workspace)
        expected_branch = session.get("branch", "")
        if branch != expected_branch:
            raise RuntimeError(f"当前分支是 {branch or '(detached)'}，不是本次提案分支。")
        proposal_dir = workspace / session.get("proposal_dir", "")
        manifest = proposal_dir / "PROPOSAL.yaml"
        if not proposal_dir.is_dir() or not manifest.is_file():
            raise RuntimeError("提案目录或 PROPOSAL.yaml 缺失。")

        status = session.get("status")
        if status == "local_commit_ready" and args.push:
            pushed = git(workspace, "push", "-u", "origin", branch, check=False)
            if pushed.returncode != 0:
                message = (pushed.stderr or pushed.stdout).strip()
                raise RuntimeError(message or "推送提案分支失败。")
            session["status"] = "pushed"
            session["pushed_at"] = utc_now()
            write_scalar_file(session_file, session)
            print(
                json.dumps(
                    {
                        "status": "pushed",
                        "branch": branch,
                        "proposal_dir": session.get("proposal_dir"),
                        "canonical_unchanged": True,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0
        if status != "working":
            raise RuntimeError("当前会话已经提交或结束，不能重复收工。")

        prefix = proposal_dir.relative_to(workspace).as_posix()
        outside_worktree = paths_outside(changed_paths(workspace), prefix)
        if outside_worktree:
            raise RuntimeError(
                "检测到提案目录外的改动；为保护正式基线，请移入本次提案目录后再提交："
                + "、".join(outside_worktree[:12])
            )
        base = session.get("base_main_commit", "")
        if not base:
            raise RuntimeError("开工会话缺少基线提交。")
        outside_commits = paths_outside(diff_paths(workspace, base, "HEAD"), prefix)
        if outside_commits:
            raise RuntimeError(
                "提案分支包含提案目录外的历史改动，已停止："
                + "、".join(outside_commits[:12])
            )

        validate_manifest(manifest, member_id, session)
        submitted = utc_now()
        text = manifest.read_text(encoding="utf-8")
        text = replace_scalar(text, "status", "proposed")
        text = replace_scalar(text, "submitted_at", submitted)
        text = replace_scalar(text, "submission_branch", branch)
        manifest.write_text(text, encoding="utf-8")

        git(workspace, "add", "--", str(proposal_dir.relative_to(workspace)))
        committed = git(workspace, "commit", "-m", f"Submit member proposal {session['proposal_id']}", check=False)
        if committed.returncode != 0:
            raise RuntimeError((committed.stderr or committed.stdout).strip() or "成员提案提交失败。")
        proposal_commit = git_text(workspace, "rev-parse", "HEAD")

        session["status"] = "local_commit_ready"
        session["submitted_at"] = submitted
        session["proposal_commit"] = proposal_commit
        write_scalar_file(session_file, session)

        pushed = False
        push_error = ""
        if args.push:
            pushed_result = git(workspace, "push", "-u", "origin", branch, check=False)
            pushed = pushed_result.returncode == 0
            if pushed:
                session["status"] = "pushed"
                session["pushed_at"] = utc_now()
                write_scalar_file(session_file, session)
            else:
                push_error = (pushed_result.stderr or pushed_result.stdout).strip()

        print(
            json.dumps(
                {
                    "status": "pushed" if pushed else "submitted_locally",
                    "member_id": member_id,
                    "branch": branch,
                    "proposal_id": session.get("proposal_id"),
                    "proposal_commit": proposal_commit,
                    "proposal_dir": session.get("proposal_dir"),
                    "pushed_to_origin": pushed,
                    "push_error": push_error or None,
                    "canonical_unchanged": True,
                    "next": (
                        "通知导演审核提案分支。"
                        if pushed
                        else "在 GitHub Desktop 中确认当前提案分支，并执行 Push origin。"
                    ),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0 if not args.push or pushed else 1
    except Exception as exc:
        print(f"Film OS member finish stopped safely: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

