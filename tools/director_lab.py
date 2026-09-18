#!/usr/bin/env python3
"""Manage a director-only exploration repository and curated team discussions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

from member_common import git, git_text, project_id_from_text, top_level_scalars, utc_now, yaml_scalar


LAB_SCHEMA = "film-os/director-lab/v1"
EXPLORATION_SCHEMA = "film-os/exploration/v1"
DISCUSSION_SCHEMA = "film-os/exploration-discussion/v1"
PROMOTION_SCHEMA = "film-os/exploration-promotion/v1"
DISCUSSION_ROOT = Path("02_团队审核/探索讨论")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="管理导演私密探索区和团队讨论版。")
    parser.add_argument("command", choices=("init", "new", "list", "share", "park", "mark-promoted"))
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--lab", type=Path, help="导演探索仓库路径；默认是项目同级的 <项目名>-导演探索。")
    parser.add_argument("--title")
    parser.add_argument("--id", dest="exploration_id")
    parser.add_argument("--note")
    parser.add_argument("--canonical-summary")
    parser.add_argument("--remote", help="初始化时给导演探索仓库设置私有远程。")
    parser.add_argument("--push", action="store_true", help="把导演探索仓库的提交推送到它自己的 origin。")
    parser.add_argument("--commit-main", action="store_true", help="把团队讨论版提交到正式项目 main。")
    parser.add_argument("--push-main", action="store_true", help="提交后推送正式项目 main。")
    parser.add_argument("--force", action="store_true", help="覆盖已存在的讨论版目录。")
    return parser.parse_args()


def authority_check(project: Path) -> dict:
    script = project / "tools/check_local_authority.py"
    if not script.is_file():
        raise RuntimeError("项目缺少 tools/check_local_authority.py，无法验证导演权限。")
    result = subprocess.run(
        [sys.executable, str(script), "--project", str(project)],
        cwd=project,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise PermissionError("当前不是已验证的导演工作区，不能使用导演探索区。")
    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("导演权限验证返回了无法识别的结果。") from exc
    if report.get("role") != "director":
        raise PermissionError("当前不是已验证的导演工作区，不能使用导演探索区。")
    return report


def resolve_project(value: Path) -> Path:
    project = value.expanduser().resolve()
    if not (project / "PROJECT.yaml").is_file():
        raise RuntimeError("目标不是 Film OS 作品项目：缺少 PROJECT.yaml。")
    return project


def project_id(project: Path) -> str:
    return project_id_from_text((project / "PROJECT.yaml").read_text(encoding="utf-8"))


def resolve_lab(project: Path, explicit: Path | None) -> Path:
    lab = explicit.expanduser().resolve() if explicit else (project.parent / f"{project.name}-导演探索").resolve()
    if lab == project or project in lab.parents:
        raise RuntimeError("导演探索仓库必须在正式项目文件夹之外。")
    return lab


def ensure_lab(project: Path, lab: Path, remote: str | None = None) -> None:
    if lab.exists():
        if not (lab / ".git").is_dir():
            raise RuntimeError(f"目录已存在但不是 Git 仓库：{lab}")
        lab_file = lab / "LAB.yaml"
        if lab_file.is_file():
            fields = top_level_scalars(lab_file.read_text(encoding="utf-8"))
            if fields.get("project_id") and fields["project_id"] != project_id(project):
                raise RuntimeError("导演探索仓库属于另一个项目，已停止。")
        return
    lab.mkdir(parents=True)
    git(lab, "init", "-q", "-b", "main")
    (lab / "LAB.yaml").write_text(
        "\n".join(
            [
                f"schema_version: {LAB_SCHEMA}",
                f"project_id: {project_id(project)}",
                f"project_path: {yaml_scalar(str(project))}",
                f"created_at: {yaml_scalar(utc_now())}",
                "visibility: director_only",
                "note: 导演私密探索仓库；不得直接镜像给成员。",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (lab / "README.md").write_text(
        "# 导演探索区\n\n"
        "这是导演私密探索仓库，不属于正式项目正史。\n\n"
        "默认不分享给成员；只有导演明确要求时，才生成团队讨论版。\n\n"
        "## 探索素材的来源\n\n"
        "- 探索可以引用成员提案、成员原话或 AI 推演；每一条都要写明来源：谁先说的（zac／Yoe／Sarah／AI），一行即可。\n"
        "- 标明来源不构成采纳：不改变成员提案的审核状态（例如“已阅，继续探索”保持不变），也不使任何内容进入主线。\n"
        "- 成员内容要进主线，只能走“纳入正式”：由导演明确指定，只写入批准的部分、建立新版本、更新版本记录。\n"
        "- 探索区保持私密，不向成员镜像；生成团队讨论版时同样保留来源标注。\n",
        encoding="utf-8",
    )
    (lab / "探索").mkdir()
    (lab / "探索/README.md").write_text(
        "# 探索记录\n\n每个探索使用 `EX-XXX_短名/`，包含 `EXPLORATION.yaml` 和 `探索.md`。\n",
        encoding="utf-8",
    )
    git(lab, "add", "-A")
    committed = git(lab, "commit", "-m", "chore: initialize director exploration lab", check=False)
    if committed.returncode != 0:
        raise RuntimeError((committed.stderr or committed.stdout).strip() or "导演探索仓库初始化提交失败。")
    if remote:
        git(lab, "remote", "add", "origin", remote)
        git(lab, "push", "-u", "origin", "main")


def exploration_dirs(lab: Path) -> list[Path]:
    root = lab / "探索"
    if not root.is_dir():
        return []
    return sorted(
        [path for path in root.iterdir() if path.is_dir() and re.match(r"^EX-\d{3,}", path.name)],
        key=lambda path: path.name,
    )


def next_exploration_id(lab: Path) -> str:
    numbers: list[int] = []
    for path in exploration_dirs(lab):
        match = re.match(r"^EX-(\d{3,})", path.name)
        if match:
            numbers.append(int(match.group(1)))
    return f"EX-{max(numbers, default=0) + 1:03d}"


def slug_for_title(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.strip().lower()).strip("-")
    return slug or utc_now().replace(":", "").replace("-", "")


def find_exploration(lab: Path, exploration_id: str) -> Path:
    matches = [path for path in exploration_dirs(lab) if path.name.startswith(f"{exploration_id}_") or path.name == exploration_id]
    if not matches:
        raise RuntimeError(f"找不到探索记录：{exploration_id}")
    if len(matches) > 1:
        raise RuntimeError(f"探索 ID 不唯一：{exploration_id}")
    return matches[0]


def write_exploration(exploration_dir: Path, project: Path, exploration_id: str, title: str) -> None:
    exploration_dir.mkdir(parents=True, exist_ok=False)
    (exploration_dir / "EXPLORATION.yaml").write_text(
        "\n".join(
            [
                f"schema_version: {EXPLORATION_SCHEMA}",
                f"exploration_id: {yaml_scalar(exploration_id)}",
                f"project_id: {project_id(project)}",
                f"title: {yaml_scalar(title)}",
                "status: exploring",
                "visibility: director_only",
                f"created_at: {yaml_scalar(utc_now())}",
                f"updated_at: {yaml_scalar(utc_now())}",
                "human_intent: >-",
                "  待导演补充：这次真正想探索什么。",
                "sources: []",
                "ai_expansion: []",
                "open_questions: []",
                "possible_directions: []",
                "human_decisions: []",
                "shared_copy: null",
                "promotion_status: pending",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (exploration_dir / "探索.md").write_text(
        f"# {exploration_id} {title}\n\n"
        "> 私密探索，不是正式设定，未进入主线。\n\n"
        "## 人的原始意图\n\n待补充。\n\n"
        "## AI 扩展与可能方向\n\n待补充。\n\n"
        "## 待回答的问题\n\n待补充。\n\n"
        "## 导演决定\n\n暂无。\n",
        encoding="utf-8",
    )


def update_exploration_fields(exploration_dir: Path, updates: dict[str, str]) -> None:
    path = exploration_dir / "EXPLORATION.yaml"
    text = path.read_text(encoding="utf-8")
    for key, value in updates.items():
        pattern = re.compile(rf"(?m)^{re.escape(key)}:\s*.*$")
        replacement = f"{key}: {yaml_scalar(value)}"
        text = pattern.sub(replacement, text, count=1) if pattern.search(text) else text.rstrip() + "\n" + replacement + "\n"
    path.write_text(text, encoding="utf-8")


def commit_lab(lab: Path, message: str, push: bool) -> None:
    git(lab, "add", "-A")
    committed = git(lab, "commit", "-m", message, check=False)
    if committed.returncode != 0:
        raise RuntimeError((committed.stderr or committed.stdout).strip() or "导演探索仓库提交失败。")
    if push:
        pushed = git(lab, "push", "origin", "main", check=False)
        if pushed.returncode != 0:
            raise RuntimeError((pushed.stderr or pushed.stdout).strip() or "导演探索仓库推送失败。")


def new_exploration(project: Path, lab: Path, title: str, push: bool) -> dict:
    ensure_lab(project, lab)
    exploration_id = next_exploration_id(lab)
    slug = slug_for_title(title)
    exploration_dir = lab / "探索" / f"{exploration_id}_{slug}"
    write_exploration(exploration_dir, project, exploration_id, title)
    commit_lab(lab, f"explore: add {exploration_id} {title}", push)
    return {
        "status": "created",
        "exploration_id": exploration_id,
        "title": title,
        "path": str(exploration_dir),
        "visibility": "director_only",
    }


def list_explorations(project: Path, lab: Path) -> dict:
    ensure_lab(project, lab)
    rows = []
    for path in exploration_dirs(lab):
        manifest = path / "EXPLORATION.yaml"
        fields = top_level_scalars(manifest.read_text(encoding="utf-8")) if manifest.is_file() else {}
        rows.append(
            {
                "exploration_id": fields.get("exploration_id", path.name.split("_", 1)[0]),
                "title": fields.get("title", path.name),
                "status": fields.get("status", "unknown"),
                "visibility": fields.get("visibility", "unknown"),
                "shared_copy": fields.get("shared_copy") or None,
                "path": str(path),
            }
        )
    return {"status": "listed", "count": len(rows), "explorations": rows}


def share_exploration(
    project: Path,
    lab: Path,
    exploration_id: str,
    force: bool,
    commit_main: bool,
    push_main: bool,
    push_lab: bool,
) -> dict:
    ensure_lab(project, lab)
    exploration_dir = find_exploration(lab, exploration_id)
    manifest = exploration_dir / "EXPLORATION.yaml"
    notes = exploration_dir / "探索.md"
    if not manifest.is_file():
        raise RuntimeError(f"探索记录缺少 EXPLORATION.yaml：{exploration_id}")
    fields = top_level_scalars(manifest.read_text(encoding="utf-8"))
    discussion_dir = project / DISCUSSION_ROOT / f"{exploration_id}_讨论版"
    if discussion_dir.exists():
        if not force:
            raise RuntimeError(f"团队讨论版已经存在：{discussion_dir}；如需覆盖请使用 --force。")
        shutil.rmtree(discussion_dir)
    discussion_dir.mkdir(parents=True)
    shutil.copy2(manifest, discussion_dir / "探索原始记录.yaml")
    if notes.is_file():
        shutil.copy2(notes, discussion_dir / "导演探索.md")
    (discussion_dir / "DISCUSSION.yaml").write_text(
        "\n".join(
            [
                f"schema_version: {DISCUSSION_SCHEMA}",
                f"exploration_id: {yaml_scalar(exploration_id)}",
                f"project_id: {project_id(project)}",
                f"shared_at: {yaml_scalar(utc_now())}",
                "status: team_discussion_non_canonical",
                "canon_status: not_canon",
                "director_decision: pending",
                "",
            ]
        ),
        encoding="utf-8",
    )
    def scalar_or_placeholder(value: str, placeholder: str) -> str:
        return placeholder if not value or value in {"[]", "{}", "null"} else value

    (discussion_dir / "讨论版.md").write_text(
        f"# {exploration_id} 团队讨论版\n\n"
        "> 探索版，不是正式设定，未进入主线。\n\n"
        "## 导演希望讨论什么\n\n"
        f"{scalar_or_placeholder(fields.get('open_questions', ''), '待导演补充。')}\n\n"
        "## 人的原始意图\n\n"
        f"{scalar_or_placeholder(fields.get('human_intent', ''), '待导演补充。')}\n\n"
        "## 可能方向\n\n"
        f"{scalar_or_placeholder(fields.get('possible_directions', ''), '待导演补充。')}\n\n"
        "## 讨论边界\n\n"
        "- 这不是正式决定，也不解锁任何 Gate。\n"
        "- 成员反馈请放入自己的提案分支，不要直接修改本讨论版。\n"
        "- 只有导演明确纳入正式后，内容才可能进入主线。\n",
        encoding="utf-8",
    )
    relative_copy = str(discussion_dir.relative_to(project))
    update_exploration_fields(
        exploration_dir,
        {
            "visibility": "team_discussion",
            "shared_copy": relative_copy,
            "updated_at": utc_now(),
        },
    )
    commit_lab(lab, f"share: {exploration_id} for team discussion", push_lab)
    if commit_main:
        git(project, "add", "--", str(discussion_dir.relative_to(project)))
        committed = git(project, "commit", "-m", f"docs: share {exploration_id} for team discussion", check=False)
        if committed.returncode != 0:
            raise RuntimeError((committed.stderr or committed.stdout).strip() or "团队讨论版提交失败。")
    if push_main:
        pushed = git(project, "push", "origin", "main", check=False)
        if pushed.returncode != 0:
            raise RuntimeError((pushed.stderr or pushed.stdout).strip() or "正式项目推送失败。")
    return {
        "status": "shared",
        "exploration_id": exploration_id,
        "discussion_path": relative_copy,
        "canon_status": "not_canon",
    }


def park_exploration(project: Path, lab: Path, exploration_id: str, note: str, push: bool) -> dict:
    ensure_lab(project, lab)
    exploration_dir = find_exploration(lab, exploration_id)
    update_exploration_fields(
        exploration_dir,
        {"status": "paused", "updated_at": utc_now()},
    )
    if note:
        with (exploration_dir / "探索.md").open("a", encoding="utf-8") as handle:
            handle.write(f"\n## 暂停记录\n\n{note}\n")
    commit_lab(lab, f"park: {exploration_id}", push)
    return {"status": "paused", "exploration_id": exploration_id}


def mark_promoted(
    project: Path,
    lab: Path,
    exploration_id: str,
    note: str,
    canonical_summary: str,
    commit_main: bool,
    push_main: bool,
    push_lab: bool,
) -> dict:
    ensure_lab(project, lab)
    exploration_dir = find_exploration(lab, exploration_id)
    update_exploration_fields(
        exploration_dir,
        {
            "status": "adopted",
            "visibility": "closed",
            "promotion_status": "promoted",
            "updated_at": utc_now(),
        },
    )
    promotion_text = "\n".join(
        [
            f"schema_version: {PROMOTION_SCHEMA}",
            f"exploration_id: {yaml_scalar(exploration_id)}",
            f"project_id: {project_id(project)}",
            f"promoted_at: {yaml_scalar(utc_now())}",
            f"canonical_summary: {yaml_scalar(canonical_summary)}",
            "status: promoted",
            "note: >-",
            f"  {note or '导演已将选中的探索内容纳入正式主线。'}",
            "",
        ]
    )
    (exploration_dir / "PROMOTION.yaml").write_text(promotion_text, encoding="utf-8")
    commit_lab(lab, f"promote: {exploration_id}", push_lab)
    discussion_dir = project / DISCUSSION_ROOT / f"{exploration_id}_讨论版"
    if discussion_dir.is_dir():
        (discussion_dir / "PROMOTION.yaml").write_text(promotion_text, encoding="utf-8")
        if commit_main:
            git(project, "add", "--", str(discussion_dir.relative_to(project)))
            committed = git(project, "commit", "-m", f"docs: record promotion decision for {exploration_id}", check=False)
            if committed.returncode != 0:
                raise RuntimeError((committed.stderr or committed.stdout).strip() or "纳入记录提交失败。")
    if push_main:
        pushed = git(project, "push", "origin", "main", check=False)
        if pushed.returncode != 0:
            raise RuntimeError((pushed.stderr or pushed.stdout).strip() or "正式项目推送失败。")
    return {
        "status": "promoted",
        "exploration_id": exploration_id,
        "canonical_summary": canonical_summary,
    }


def main() -> int:
    args = parse_args()
    project = resolve_project(args.project)
    lab = resolve_lab(project, args.lab)
    try:
        authority_check(project)
        if args.command == "init":
            ensure_lab(project, lab, args.remote)
            result = {"status": "initialized", "lab": str(lab), "visibility": "director_only"}
        elif args.command == "new":
            if not args.title:
                raise RuntimeError("新建探索需要 --title。")
            result = new_exploration(project, lab, args.title, args.push)
        elif args.command == "list":
            result = list_explorations(project, lab)
        elif args.command == "share":
            if not args.exploration_id:
                raise RuntimeError("分享探索需要 --id。")
            result = share_exploration(
                project,
                lab,
                args.exploration_id,
                args.force,
                args.commit_main or args.push_main,
                args.push_main,
                args.push,
            )
        elif args.command == "park":
            if not args.exploration_id:
                raise RuntimeError("暂停探索需要 --id。")
            result = park_exploration(project, lab, args.exploration_id, args.note or "", args.push)
        elif args.command == "mark-promoted":
            if not args.exploration_id:
                raise RuntimeError("纳入正式需要 --id。")
            result = mark_promoted(
                project,
                lab,
                args.exploration_id,
                args.note or "",
                args.canonical_summary or "",
                args.commit_main or args.push_main,
                args.push_main,
                args.push,
            )
        else:
            raise RuntimeError(f"未知命令：{args.command}")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(f"Film OS director lab stopped safely: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
