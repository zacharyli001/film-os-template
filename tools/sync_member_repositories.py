#!/usr/bin/env python3
"""Sync configured member delivery repositories for director review only."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

from member_common import (
    commit_exists,
    git,
    git_text,
    parse_repository_config,
    project_id_from_text,
    remote_key,
    top_level_scalars,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="只读同步成员交付仓库并列出提案分支。"
    )
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--cache-root", type=Path, default=Path.home() / "Documents/GitHub")
    parser.add_argument("--no-network", action="store_true", help="只检查本地克隆，不访问 GitHub。")
    return parser.parse_args()


def authority_check(project: Path) -> dict[str, Any]:
    result = subprocess.run(
        [sys.executable, str(project / "tools/check_local_authority.py"), "--project", str(project)],
        cwd=project,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise PermissionError("当前不是已验证的导演工作区，不能同步成员交付仓库。")
    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("导演权限验证返回了无法识别的结果。") from exc
    if report.get("role") != "director" or not report.get("canonical_write_allowed"):
        raise PermissionError("当前不是已验证的导演工作区，不能同步成员交付仓库。")
    return report


def safe_local_path(cache_root: Path, local_dir: str) -> Path:
    relative = Path(local_dir)
    if relative.is_absolute() or relative in (Path("."), Path("..")) or ".." in relative.parts:
        raise ValueError(f"成员本地目录必须是缓存根目录下的相对路径：{local_dir}")
    target = (cache_root / relative).resolve()
    target.relative_to(cache_root.resolve())
    return target


def remote_refs(repo: Path, prefix: str) -> list[tuple[str, str]]:
    raw = git_text(
        repo,
        "for-each-ref",
        "--format=%(refname:short) %(objectname)",
        "refs/remotes/origin",
    )
    results: list[tuple[str, str]] = []
    for line in raw.splitlines():
        if " " not in line:
            continue
        ref, commit = line.split(" ", 1)
        short = ref.removeprefix("origin/")
        if short == "main" or short == "HEAD":
            continue
        if short.startswith(prefix):
            results.append((ref, commit))
    return results


def tree_paths(repo: Path, ref: str) -> list[str]:
    raw = git_text(repo, "ls-tree", "-r", "--name-only", ref)
    return [line for line in raw.splitlines() if line]


def proposal_records(repo: Path, canonical: Path, ref: str, commit: str, canonical_head: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    paths = [
        path
        for path in tree_paths(repo, ref)
        if path.startswith("submissions/") and path.endswith("/PROPOSAL.yaml")
    ]
    for path in sorted(paths):
        try:
            text = git_text(repo, "show", f"{ref}:{path}")
        except Exception as exc:
            records.append(
                {
                    "manifest": path,
                    "branch": ref,
                    "branch_commit": commit,
                    "status": "invalid_manifest",
                    "error": str(exc),
                    "review_only": True,
                }
            )
            continue
        fields = top_level_scalars(text)
        base = fields.get("base_main_commit", "")
        changed_files: list[str] = []
        base_in_member = bool(base) and commit_exists(repo, base)
        if base_in_member:
            raw = git(
                repo,
                "diff",
                "--name-only",
                "--no-renames",
                base,
                ref,
                check=False,
            ).stdout
            changed_files = [line for line in raw.splitlines() if line]
        records.append(
            {
                "manifest": path,
                "branch": ref,
                "branch_commit": commit,
                "proposal_id": fields.get("proposal_id"),
                "author": fields.get("author_github"),
                "status": fields.get("status"),
                "proposal_type": fields.get("proposal_type"),
                "target_scope": fields.get("target_scope"),
                "summary": fields.get("summary"),
                "base_commit": base,
                "base_exists_in_member_repo": base_in_member,
                "base_exists_in_canonical": bool(base) and commit_exists(canonical, base),
                "base_is_current_canonical_head": bool(base and base == canonical_head),
                "changed_files": changed_files,
                "review_only": True,
            }
        )
    return records


def sync_one(
    canonical: Path,
    cache_root: Path,
    config: dict[str, Any],
    entry: dict[str, str],
    no_network: bool,
) -> dict[str, Any]:
    branch = config.get("default_branch", "main")
    prefix = config.get("proposal_branch_prefix", "proposal/")
    remote = entry.get("remote_url", "")
    target = safe_local_path(cache_root, entry.get("local_dir", ""))
    result: dict[str, Any] = {
        "member_id": entry.get("member_id"),
        "display_name": entry.get("display_name"),
        "remote_url": remote,
        "local_dir": str(target),
        "default_branch": branch,
        "proposal_branch_prefix": prefix,
        "action": None,
        "status": None,
    }
    try:
        if not target.exists():
            if no_network:
                result.update(action="clone_skipped", status="missing_local_clone")
                return result
            target.parent.mkdir(parents=True, exist_ok=True)
            clone = git(cache_root, "clone", remote, str(target), check=False)
            if clone.returncode != 0:
                result.update(action="clone_failed", status="sync_error", error=(clone.stderr or clone.stdout).strip())
                return result
            result["action"] = "cloned"
        else:
            actual_remote = git_text(target, "remote", "get-url", "origin", check=False)
            if remote_key(actual_remote) != remote_key(remote):
                result.update(action="stopped", status="remote_mismatch", actual_remote=actual_remote)
                return result
            dirty = git_text(target, "status", "--porcelain=v1", check=False)
            if dirty:
                result.update(action="stopped", status="blocked_local_changes", changed_files=dirty.splitlines())
                return result
            if no_network:
                result["action"] = "local_check_only"
            else:
                fetched = git(
                    target,
                    "fetch",
                    "--prune",
                    "origin",
                    "+refs/heads/*:refs/remotes/origin/*",
                    check=False,
                )
                if fetched.returncode != 0:
                    result.update(action="fetch_failed", status="sync_error", error=(fetched.stderr or fetched.stdout).strip())
                    return result
                result["action"] = "fetched_all_branches"

        main_ref = f"refs/remotes/origin/{branch}"
        main_commit = git_text(target, "rev-parse", "--verify", f"{main_ref}^{{commit}}", check=False)
        main_tree = git_text(target, "rev-parse", f"{main_ref}^{{tree}}", check=False) if main_commit else ""
        canonical_head = git_text(canonical, "rev-parse", "HEAD")
        canonical_tree = git_text(canonical, "rev-parse", f"{canonical_head}^{{tree}}")
        result.update(
            status="ready_for_review",
            main_commit=main_commit or None,
            main_is_exact_canonical_commit=bool(main_commit and main_commit == canonical_head),
            main_tree_matches_canonical=bool(main_tree and main_tree == canonical_tree),
            proposals=[],
        )
        for ref, commit in remote_refs(target, prefix):
            result["proposals"].extend(
                proposal_records(target, canonical, ref, commit, canonical_head)
            )
        return result
    except (OSError, subprocess.CalledProcessError, ValueError) as exc:
        result.update(action="stopped", status="sync_error", error=str(exc))
        return result


def main() -> int:
    args = parse_args()
    project = args.project.expanduser().resolve()
    try:
        if not (project / "PROJECT.yaml").is_file():
            raise RuntimeError("--project 必须指向正式 Film OS 作品项目。")
        authority_check(project)
        config_path = project / "governance/MEMBER_DELIVERY_REPOSITORIES.yaml"
        if not config_path.is_file():
            raise RuntimeError("缺少 governance/MEMBER_DELIVERY_REPOSITORIES.yaml 成员仓库登记表。")
        config = parse_repository_config(config_path.read_text(encoding="utf-8"))
        project_id = project_id_from_text((project / "PROJECT.yaml").read_text(encoding="utf-8"))
        if config.get("project_id") != project_id:
            raise RuntimeError("成员仓库登记表的 project_id 与 PROJECT.yaml 不一致。")
        repositories = config.get("repositories", [])
        if not repositories:
            print(
                json.dumps(
                    {
                        "review_trigger": "member_proposal_review",
                        "status": "no_member_repositories_configured",
                        "canonical_head": git_text(project, "rev-parse", "HEAD"),
                        "canonical_files_changed": False,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0
        cache_root = args.cache_root.expanduser().resolve()
        if cache_root == project or cache_root.is_relative_to(project) or project.is_relative_to(cache_root):
            raise RuntimeError("成员仓库缓存目录不能与正式项目目录相同或互相嵌套。")
        reports = [
            sync_one(project, cache_root, config, entry, args.no_network)
            for entry in repositories
        ]
        output = {
            "review_trigger": "member_proposal_review",
            "checked_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "authority": "director_verified",
            "canonical_head": git_text(project, "rev-parse", "HEAD"),
            "action": "review_only_no_canonical_files_changed",
            "repositories": reports,
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0 if all(item.get("status") == "ready_for_review" for item in reports) else 1
    except Exception as exc:
        print(f"Film OS member review sync stopped safely: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
