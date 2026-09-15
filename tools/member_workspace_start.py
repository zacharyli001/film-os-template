#!/usr/bin/env python3
"""Open one isolated Film OS member proposal against the newest canonical baseline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

from member_common import (
    archive_session,
    branch_exists,
    changed_paths,
    commit_exists,
    config_path,
    current_branch,
    ensure_local_exclude,
    git,
    git_text,
    project_id_from_ref,
    remote_key,
    session_path,
    utc_compact,
    utc_now,
    validate_member_id,
    write_scalar_file,
    yaml_scalar,
    read_scalar_file,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="以正式基线镜像开启一次新的 Film OS 成员提案。"
    )
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--member-id", required=True)
    parser.add_argument("--canonical-url", help="首次运行时必须提供正式仓库地址。")
    parser.add_argument("--canonical-branch", default="main")
    parser.add_argument("--slug", help="提案目录使用的简短英文名。")
    parser.add_argument("--no-network", action="store_true", help="只使用已有的 canonical 远程引用。")
    parser.add_argument("--resume", action="store_true", help="恢复当前尚未提交的提案会话。")
    parser.add_argument(
        "--adopt-main",
        action="store_true",
        help="仅用于 main 尚未包含 PROJECT.yaml 的空成员仓库：先归档旧 main，再把 main 设为正式基线镜像。",
    )
    parser.add_argument(
        "--realign-main",
        action="store_true",
        help="一次性修复旧式同步提交、落后镜像或无共同祖先的成员 main，不删除历史和提案分支。",
    )
    parser.add_argument("--push-main", action="store_true", help="完成 main 镜像后立即推送到成员自己的 origin。")
    return parser.parse_args()


def safe_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9-]+", "-", value.strip().lower()).strip("-")
    if not slug:
        raise ValueError("提案短名只能使用英文字母、数字和连字符。")
    return slug


def read_config(workspace: Path) -> dict[str, str]:
    return read_scalar_file(config_path(workspace))


def resolve_canonical_url(workspace: Path, args: argparse.Namespace, config: dict[str, str]) -> str:
    configured = config.get("canonical_url", "").strip()
    provided = (args.canonical_url or "").strip()
    if configured and provided and remote_key(configured) != remote_key(provided):
        raise RuntimeError("本次提供的正式仓库地址与已有成员配置不一致。")
    canonical_url = configured or provided
    if not canonical_url:
        raise RuntimeError("首次开工必须提供 --canonical-url，之后会保存在本地成员配置中。")
    return canonical_url


def ensure_origin(workspace: Path, canonical_url: str) -> str:
    origin = git_text(workspace, "remote", "get-url", "origin", check=False)
    if not origin:
        raise RuntimeError("成员仓库缺少 origin 远程；请先从自己的 GitHub 交付仓库克隆。")
    if remote_key(origin) == remote_key(canonical_url):
        raise RuntimeError("检测到 origin 是正式主库；成员流程不能在正式主库中运行。")
    return origin


def fetch_canonical(workspace: Path, canonical_url: str, branch: str, no_network: bool) -> str:
    existing = git(workspace, "remote", "get-url", "canonical", check=False)
    if existing.returncode == 0 and remote_key(existing.stdout.strip()) != remote_key(canonical_url):
        raise RuntimeError("canonical 远程地址与配置不一致，已停止。")
    if existing.returncode != 0:
        git(workspace, "remote", "add", "canonical", canonical_url)
    ref = f"canonical/{branch}"
    if not no_network:
        fetched = git(workspace, "fetch", "--prune", "canonical", branch, check=False)
        if fetched.returncode != 0:
            raise RuntimeError((fetched.stderr or fetched.stdout).strip() or "同步正式基线失败。")
    if not commit_exists(workspace, ref):
        raise RuntimeError("没有可用的正式基线引用；请去掉 --no-network 后重试。")
    return git_text(workspace, "rev-parse", f"{ref}^{{commit}}")


def fetch_origin(workspace: Path, no_network: bool) -> None:
    if no_network:
        if not commit_exists(workspace, "origin/main"):
            raise RuntimeError("没有可用的 origin/main 引用；请去掉 --no-network 后重试。")
        return
    fetched = git(workspace, "fetch", "--prune", "--tags", "origin", check=False)
    if fetched.returncode != 0:
        raise RuntimeError((fetched.stderr or fetched.stdout).strip() or "同步成员交付仓库失败。")
    if not commit_exists(workspace, "origin/main"):
        raise RuntimeError("成员交付仓库缺少 origin/main。")


def sync_local_main_with_origin(workspace: Path, allow_local_ahead: bool) -> str:
    if not branch_exists(workspace, "main"):
        return "no_local_main"
    git(workspace, "switch", "main")
    local = git_text(workspace, "rev-parse", "main")
    remote = git_text(workspace, "rev-parse", "origin/main")
    if local == remote:
        return "already_synced"
    local_ancestor = git(
        workspace, "merge-base", "--is-ancestor", local, "origin/main", check=False
    ).returncode == 0
    remote_ancestor = git(
        workspace, "merge-base", "--is-ancestor", "origin/main", local, check=False
    ).returncode == 0
    if local_ancestor:
        merged = git(workspace, "merge", "--ff-only", "origin/main", check=False)
        if merged.returncode != 0:
            raise RuntimeError((merged.stderr or merged.stdout).strip() or "本地 main 快进失败。")
        return "fast_forwarded_to_origin"
    if remote_ancestor:
        if allow_local_ahead:
            return "local_ahead"
        unpushed = git_text(workspace, "log", "--oneline", "origin/main..main")
        raise RuntimeError(
            "本地 main 领先 origin/main，存在未推送提交；流程不会丢弃任何内容。"
            + (f"\n{unpushed}" if unpushed else "")
        )
    raise RuntimeError(
        "本地 main 与 origin/main 已分叉。请运行 "
        "member_workspace_start.py --realign-main 修复；流程不会自动覆盖。"
    )


def next_backup_tag(workspace: Path) -> str:
    base = f"archive/member-main-before-mirror-{utc_compact()}"
    candidate = base
    counter = 1
    while git(workspace, "rev-parse", "--verify", f"refs/tags/{candidate}", check=False).returncode == 0:
        counter += 1
        candidate = f"{base}-{counter}"
    return candidate


def release_from_ref(workspace: Path, ref: str) -> str:
    text = git_text(workspace, "show", f"{ref}:FILM_OS_VERSION.yaml", check=False)
    match = re.search(r'^release:\s*["\']?([^"\'\s]+)', text, re.MULTILINE)
    return match.group(1) if match else ""


def version_hint(workspace: Path, canonical_ref: str) -> str | None:
    local_version = release_from_ref(workspace, "main")
    canonical_version = release_from_ref(workspace, canonical_ref)
    if local_version and canonical_version and local_version != canonical_version:
        return (
            f"提示：成员仓库 main 的 Film OS 版本为 {local_version}，"
            f"正式基线为 {canonical_version}。若工具仍无法开工，请运行 --realign-main。"
        )
    return None


def realign_main(
    workspace: Path,
    canonical_ref: str,
    canonical_head: str,
    push_main: bool,
) -> dict[str, str | bool]:
    if not branch_exists(workspace, "main"):
        git(workspace, "switch", "-C", "main", canonical_ref)
        pushed = False
        if push_main:
            result = git(workspace, "push", "--force-with-lease", "origin", "main", check=False)
            if result.returncode != 0:
                raise RuntimeError((result.stderr or result.stdout).strip() or "推送 main 失败。")
            pushed = True
        return {"action": "created", "pushed": pushed}

    git(workspace, "switch", "main")
    main_head = git_text(workspace, "rev-parse", "main")
    if main_head == canonical_head:
        return {"action": "already_exact", "pushed": False}
    main_tree = git_text(workspace, "rev-parse", "main^{tree}")
    canonical_tree = git_text(workspace, "rev-parse", f"{canonical_ref}^{{tree}}")
    if main_tree == canonical_tree:
        return {"action": "already_mirror", "pushed": False}

    ancestor = git(
        workspace, "merge-base", "--is-ancestor", main_head, canonical_ref, check=False
    ).returncode == 0
    if ancestor:
        merged = git(workspace, "merge", "--ff-only", canonical_ref, check=False)
        if merged.returncode != 0:
            raise RuntimeError((merged.stderr or merged.stdout).strip() or "main 快进到正式基线失败。")
        pushed = False
        if push_main:
            result = git(workspace, "push", "--force-with-lease", "origin", "main", check=False)
            if result.returncode != 0:
                raise RuntimeError((result.stderr or result.stdout).strip() or "推送 main 失败。")
            pushed = True
        return {"action": "fast_forwarded", "pushed": pushed}

    tag = next_backup_tag(workspace)
    git(
        workspace,
        "tag",
        "-a",
        "-m",
        "成员 main 对齐正式基线镜像前的完整备份",
        tag,
        "main",
    )
    pushed_tag = git(workspace, "push", "origin", f"refs/tags/{tag}", check=False)
    if pushed_tag.returncode != 0:
        raise RuntimeError(
            (pushed_tag.stderr or pushed_tag.stdout).strip()
            or "备份标签推送失败；为避免无远程备份，main 未改写。"
        )
    mirror_commit = git_text(
        workspace,
        "commit-tree",
        canonical_tree,
        "-p",
        "main",
        "-p",
        canonical_ref,
        "-m",
        "chore: realign member main to canonical baseline",
    )
    git(workspace, "reset", "--hard", mirror_commit)
    pushed = False
    if push_main:
        pushed_main = git(workspace, "push", "--force-with-lease", "origin", "main", check=False)
        if pushed_main.returncode != 0:
            raise RuntimeError(
                (pushed_main.stderr or pushed_main.stdout).strip()
                or "main 镜像已在本机建立，但推送失败；远程未被覆盖。"
            )
        pushed = True
    return {
        "action": "mirror_rebuilt",
        "backup_tag": tag,
        "mirror_commit": mirror_commit,
        "pushed": pushed,
    }


def ensure_mirror_main(
    workspace: Path,
    canonical_ref: str,
    canonical_head: str,
    adopt_main: bool,
) -> None:
    if not branch_exists(workspace, "main"):
        git(workspace, "switch", "-C", "main", canonical_ref)
        return
    git(workspace, "switch", "main")
    main_head = git_text(workspace, "rev-parse", "main")
    if main_head == canonical_head:
        return
    main_tree = git_text(workspace, "rev-parse", "main^{tree}")
    canonical_tree = git_text(workspace, "rev-parse", f"{canonical_ref}^{{tree}}")
    if main_tree == canonical_tree:
        return
    ancestor = git(
        workspace,
        "merge-base",
        "--is-ancestor",
        main_head,
        canonical_ref,
        check=False,
    ).returncode == 0
    if not ancestor:
        merge_base_result = git(
            workspace,
            "merge-base",
            main_head,
            canonical_ref,
            check=False,
        )
        if merge_base_result.returncode == 0:
            merge_base = merge_base_result.stdout.strip()
            mirror_diff = git(
                workspace,
                "diff",
                "--name-only",
                "--no-renames",
                merge_base,
                "main",
                check=False,
            )
            if mirror_diff.returncode == 0 and not mirror_diff.stdout.strip():
                mirror_commit = git_text(
                    workspace,
                    "commit-tree",
                    canonical_tree,
                    "-p",
                    "main",
                    "-p",
                    canonical_ref,
                    "-m",
                    "chore: 将成员 main 快进到最新正式基线镜像",
                )
                git(workspace, "reset", "--hard", mirror_commit)
                return
        if adopt_main:
            has_project = git(workspace, "cat-file", "-e", "main:PROJECT.yaml", check=False).returncode == 0
            if has_project:
                raise RuntimeError(
                    "成员 main 已包含正式项目资料；请改用 --realign-main 修复，"
                    "不要使用 --adopt-main。"
                )
            tag = f"archive/member-main-before-adopt-{utc_compact()}"
            git(
                workspace,
                "tag",
                "-a",
                "-m",
                "成员仓库首次接入正式基线前的本地 main 备份",
                tag,
                "main",
            )
            mirror_commit = git_text(
                workspace,
                "commit-tree",
                canonical_tree,
                "-p",
                "main",
                "-p",
                canonical_ref,
                "-m",
                "chore: 将成员 main 对齐正式基线只读镜像",
            )
            git(workspace, "reset", "--hard", mirror_commit)
            return
        canonical_is_ancestor = git(
            workspace,
            "merge-base",
            "--is-ancestor",
            canonical_ref,
            main_head,
            check=False,
        ).returncode == 0
        if canonical_is_ancestor:
            raise RuntimeError(
                "成员 main 已接入正式历史，但工作内容仍不是正式基线镜像；"
                "请运行 python3 tools/member_workspace_start.py "
                "--workspace <成员仓库> --member-id <成员ID> --realign-main 修复后再开工。"
            )
        raise RuntimeError(
            "成员仓库 main 不是正式基线的干净镜像。请运行 "
            "python3 tools/member_workspace_start.py --workspace <成员仓库> "
            "--member-id <成员ID> --realign-main 修复；"
            "--adopt-main 只适用于尚未导入正式基线的空成员仓库。"
        )
    git(workspace, "switch", "main")
    merged = git(workspace, "merge", "--ff-only", canonical_ref, check=False)
    if merged.returncode != 0:
        raise RuntimeError((merged.stderr or merged.stdout).strip() or "main 快进到正式基线失败。")


def write_proposal_bundle(
    workspace: Path,
    member_id: str,
    proposal_id: str,
    base_commit: str,
    created_at: str,
) -> Path:
    bundle = workspace / "submissions" / member_id / proposal_id
    bundle.mkdir(parents=True, exist_ok=False)
    (bundle / "PROPOSAL.yaml").write_text(
        "\n".join(
            [
                "schema_version: film-os/proposal/v1",
                f"proposal_id: {yaml_scalar(proposal_id)}",
                f"author_github: {yaml_scalar(member_id)}",
                f"created_at: {yaml_scalar(created_at)}",
                f"base_main_commit: {base_commit}",
                "status: draft",
                "proposal_type: pending_member_choice",
                "changes_existing_canon: false",
                "target_scope: pending_member_description",
                "summary: >-",
                "  请在提交前填写这份提案要解决的问题和希望导演审核的内容。",
                "reason: >-",
                "  请在提交前填写依据、风险与预期影响。",
                "source_files: []",
                "derived_outputs: []",
                "model_runtime:",
                "  provider: unknown",
                "  model_id: unknown",
                "  client: codex_desktop",
                "  capability_report: MODEL_RUNTIME.yaml",
                "  capability_report_status: unverified",
                "director_decision:",
                "  status: pending",
                "  decided_by: null",
                "  decided_at: null",
                "  notes: null",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (bundle / "DELTA.md").write_text(
        "# 本次成员提案\n\n"
        "请写清楚：改了什么、为什么改、希望导演看什么、有哪些风险。\n\n"
        "所有剧本、资产、分镜、Prompt 和测试产出都放在本提案目录内；"
        "不要改动提案目录之外的正式基线文件。\n",
        encoding="utf-8",
    )
    (bundle / "MODEL_RUNTIME.yaml").write_text(
        "schema_version: film-os/model-capability-report/v1\n"
        "provider: unknown\n"
        "model_id: unknown\n"
        "client: codex_desktop\n"
        "capability_report_status: unverified\n"
        f"base_commit: {base_commit}\n",
        encoding="utf-8",
    )
    return bundle


def main() -> int:
    args = parse_args()
    workspace = args.workspace.expanduser().resolve()
    try:
        member_id = validate_member_id(args.member_id)
        if not (workspace / ".git").is_dir():
            raise RuntimeError("工作目录不是 Git 仓库。")
        ensure_local_exclude(workspace)
        config = read_config(workspace)
        canonical_url = resolve_canonical_url(workspace, args, config)
        ensure_origin(workspace, canonical_url)

        session_file = session_path(workspace)
        if args.resume:
            if not session_file.is_file():
                raise RuntimeError("找不到可恢复的成员会话 SESSION.yaml。")
            session = read_scalar_file(session_file)
            if session.get("status") != "working":
                raise RuntimeError("当前会话已经提交或结束，不能继续恢复。")
            if session.get("member_id") != member_id:
                raise RuntimeError("成员 ID 与当前会话不一致。")
            branch = session.get("branch", "")
            proposal_dir = workspace / session.get("proposal_dir", "")
            if not branch or not proposal_dir.is_dir():
                raise RuntimeError("成员会话记录不完整，已停止。")
            if current_branch(workspace) != branch:
                git(workspace, "switch", branch)
            print(
                json.dumps(
                    {
                        "status": "resumed",
                        "member_id": member_id,
                        "branch": branch,
                        "proposal_dir": str(proposal_dir.relative_to(workspace)),
                        "base_main_commit": session.get("base_main_commit"),
                        "next": "继续只在提案目录内工作，然后运行 member_workspace_finish.py。",
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0

        if session_file.is_file():
            session = read_scalar_file(session_file)
            if session.get("status") == "working":
                raise RuntimeError("已有未结束的成员提案；请使用 --resume，或先完成当前提案。")
            archive_session(workspace)

        dirty = changed_paths(workspace)
        if dirty:
            raise RuntimeError(
                "开工前工作区必须干净；请先处理这些未提交内容：" + "、".join(dirty[:12])
            )

        fetch_origin(workspace, args.no_network)
        canonical_head = fetch_canonical(
            workspace,
            canonical_url,
            args.canonical_branch,
            args.no_network,
        )
        canonical_ref = f"canonical/{args.canonical_branch}"
        realign_result: dict[str, str | bool] | None = None
        if args.realign_main:
            sync_local_main_with_origin(workspace, allow_local_ahead=True)
            hint = version_hint(workspace, canonical_ref)
            if hint:
                print(hint, file=sys.stderr)
            realign_result = realign_main(
                workspace,
                canonical_ref,
                canonical_head,
                args.push_main,
            )
        else:
            sync_local_main_with_origin(workspace, allow_local_ahead=False)
            hint = version_hint(workspace, canonical_ref)
            if hint:
                print(hint, file=sys.stderr)
            ensure_mirror_main(workspace, canonical_ref, canonical_head, args.adopt_main)
            if args.push_main:
                pushed_main = git(workspace, "push", "origin", "main", check=False)
                if pushed_main.returncode != 0:
                    raise RuntimeError(
                        (pushed_main.stderr or pushed_main.stdout).strip() or "推送正式基线镜像 main 失败。"
                    )
        project_id = project_id_from_ref(workspace, canonical_ref)

        compact = utc_compact()
        slug = safe_slug(args.slug) if args.slug else member_id.lower()
        proposal_id = f"{compact}_{slug}"
        branch = f"proposal/{member_id}/{proposal_id}"
        if branch_exists(workspace, branch):
            raise RuntimeError("相同时间的提案分支已经存在，请稍后重试。")
        git(workspace, "switch", "-c", branch, canonical_ref)
        bundle = write_proposal_bundle(
            workspace,
            member_id,
            proposal_id,
            canonical_head,
            utc_now(),
        )
        write_scalar_file(
            config_path(workspace),
            {
                "schema_version": "film-os/member-workspace-config/v1",
                "member_id": member_id,
                "canonical_url": canonical_url,
                "canonical_branch": args.canonical_branch,
                "project_id": project_id,
                "updated_at": utc_now(),
            },
        )
        write_scalar_file(
            session_file,
            {
                "schema_version": "film-os/member-session/v1",
                "member_id": member_id,
                "branch": branch,
                "proposal_id": proposal_id,
                "proposal_dir": str(bundle.relative_to(workspace)),
                "base_main_commit": canonical_head,
                "canonical_url": canonical_url,
                "canonical_branch": args.canonical_branch,
                "started_at": utc_now(),
                "status": "working",
            },
        )
        print(
            json.dumps(
                {
                    "status": "ready_for_member_work",
                    "action": "started",
                    "member_id": member_id,
                    "project_id": project_id,
                    "branch": branch,
                    "proposal_id": proposal_id,
                    "proposal_dir": str(bundle.relative_to(workspace)),
                    "base_main_commit": canonical_head,
                    "canonical_url": canonical_url,
                    "realign": realign_result,
                    "version_hint": hint,
                    "next": "只在 proposal_dir 内完成提案与衍生产出，然后运行 member_workspace_finish.py。",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    except Exception as exc:
        print(f"Film OS member start stopped safely: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
