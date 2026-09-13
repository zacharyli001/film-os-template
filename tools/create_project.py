#!/usr/bin/env python3
"""Create a clean Film OS production project from this template repository."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import sys

from upgrade_project import initialize_installation


TEMPLATE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PARENT = TEMPLATE_ROOT.parent / "Film Projects"


def yaml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def clean_title(value: str) -> str:
    title = value.strip()
    if not title or title in {".", ".."} or any(char in title for char in ("/", "\\", "\0")):
        raise ValueError("项目名称不能为空，也不能包含路径符号。")
    return title


def folder_name_for(title: str) -> str:
    name = re.sub(r"\s+", "-", title.strip())
    name = re.sub(r"[^\w\-\u3400-\u9fff]+", "-", name, flags=re.UNICODE)
    name = re.sub(r"-+", "-", name).strip("-._")
    return f"{name or 'film-project'}-FilmOS"


def generated_project_id(title: str) -> str:
    stamp = datetime.now(timezone.utc).isoformat()
    digest = hashlib.sha1(f"{title}|{stamp}".encode("utf-8")).hexdigest()[:7]
    return f"P{digest}".upper()


def validate_project_id(value: str) -> str:
    project_id = value.strip().upper()
    if not re.fullmatch(r"[A-Z0-9]{2,8}", project_id):
        raise ValueError("项目代号必须是2—8位大写英文字母或数字。")
    return project_id


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"母版缺少预期字段：{label}")
    return text.replace(old, new, 1)


def copy_template(target: Path) -> None:
    """Copy the Film OS system tree and materialize the project scaffold.

    The master repository keeps reusable Film OS code/rules at its root and
    keeps project-only scaffolding under ``project_template/``.  A production
    repository must receive the scaffold at its normal runtime paths, but must
    never receive the master-only ``project_template`` wrapper directory.
    """
    ignored = shutil.ignore_patterns(
        ".git", ".DS_Store", "__pycache__", "*.pyc", "~$*", "work",
        "project_template", "Film OS 团队使用说明书.docx"
    )
    shutil.copytree(TEMPLATE_ROOT, target, ignore=ignored)

    project_source = TEMPLATE_ROOT / "project_template"
    for item in project_source.iterdir():
        # This master-only guide explains the scaffold itself; it must not
        # replace the production repository's system README.
        if item.name == "README.md":
            continue
        destination = target / item.name
        if item.is_dir():
            shutil.copytree(item, destination, dirs_exist_ok=True)
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, destination)


def configure_project_yaml(
    target: Path,
    title: str,
    project_id: str,
    production_type: str,
    episode_count: int | None,
    episode_runtime: int | None,
    orientation: str | None,
) -> None:
    text = (target / "templates/PROJECT.yaml").read_text(encoding="utf-8")
    text = replace_once(text, "  id: DEMO", f"  id: {project_id}", "project.id")
    text = replace_once(text, "  title: Replace Me", f"  title: {yaml_string(title)}", "project.title")
    text = replace_once(text, "  production_type: film", f"  production_type: {production_type}", "production_type")

    if production_type == "series":
        text = replace_once(text, "  format: short_film", "  format: episodic_series", "project.format")
        text = replace_once(text, "  enabled: false", "  enabled: true", "series_mode.enabled")
        text = replace_once(text, "  series_id: null", "  series_id: SERIES01", "series_mode.series_id")
        text = replace_once(text, "  current_season_id: null", "  current_season_id: SE01", "current_season_id")
        text = replace_once(text, "  current_episode_id: null", "  current_episode_id: SE01_E001", "current_episode_id")
        text = replace_once(
            text,
            "  planned_episode_count: null",
            f"  planned_episode_count: {episode_count if episode_count is not None else 'null'}",
            "planned_episode_count",
        )
        text = replace_once(
            text,
            "  target_episode_runtime_seconds: null",
            f"  target_episode_runtime_seconds: {episode_runtime if episode_runtime is not None else 'null'}",
            "target_episode_runtime_seconds",
        )
        text = replace_once(
            text,
            "  orientation: null",
            f"  orientation: {orientation or 'null'}",
            "orientation",
        )
        text = replace_once(text, "  series_bible: null", "  series_bible: series/SERIES_BIBLE.yaml", "series_bible")
        text = replace_once(text, "  season_map: null", "  season_map: series/SE01/SEASON_MAP.yaml", "season_map")
        text = replace_once(
            text,
            "  continuity_ledger: null",
            "  continuity_ledger: registry/SERIES_CONTINUITY.yaml",
            "continuity_ledger",
        )

    (target / "PROJECT.yaml").write_text(text, encoding="utf-8")


def initialize_registry(target: Path, project_id: str, production_type: str) -> None:
    series_value = "SERIES01" if production_type == "series" else "null"
    (target / "registry/ASSET_REGISTRY.yaml").write_text(
        "\n".join(
            [
                "schema_version: film-os/v1",
                f"project_id: {project_id}",
                f"series_id: {series_value}",
                "assets: []",
                "",
            ]
        ),
        encoding="utf-8",
    )
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    (target / "registry/VERSION_LOG.yaml").write_text(
        "\n".join(
            [
                "schema_version: film-os/v1",
                f"project_id: {project_id}",
                "entries:",
                "  - entry_id: VL-0001",
                f"    timestamp: {yaml_string(timestamp)}",
                "    actor: film-project-launcher",
                "    entity_type: project",
                f"    entity_id: {project_id}",
                "    season_id: null",
                "    episode_id: null",
                "    from_version: null",
                "    to_version: v01",
                "    action: created",
                "    changed_variable: null",
                "    summary: Initialized production project from film-os-template.",
                "    related_gate: null",
                "    approval: null",
                "",
            ]
        ),
        encoding="utf-8",
    )


def initialize_tapnow(target: Path, project_id: str, production_type: str) -> None:
    series_value = "SERIES01" if production_type == "series" else "null"
    season_value = "SE01" if production_type == "series" else "null"
    episode_value = "SE01_E001" if production_type == "series" else "null"
    header = [
        "schema_version: film-os/v1",
        f"project_id: {project_id}",
        f"series_id: {series_value}",
        f"season_id: {season_value}",
        f"episode_id: {episode_value}",
    ]
    (target / "tapnow/CANVAS_MANIFEST.yaml").write_text("\n".join(header + ["canvases: []", ""]), encoding="utf-8")
    (target / "tapnow/NODE_MAP.yaml").write_text("\n".join(header + ["nodes: []", ""]), encoding="utf-8")


def customize_series_file(
    source: Path,
    destination: Path,
    project_id: str,
    title: str,
    episode_count: int | None,
    episode_runtime: int | None,
    orientation: str | None,
) -> None:
    text = source.read_text(encoding="utf-8")
    text = text.replace("project_id: DEMO", f"project_id: {project_id}")
    text = text.replace("title: Replace Me", f"title: {yaml_string(title)}")
    text = text.replace(
        "planned_episode_count: 8",
        f"planned_episode_count: {episode_count if episode_count is not None else 'null'}",
    )
    text = text.replace(
        "target_episode_runtime_seconds: 900",
        f"target_episode_runtime_seconds: {episode_runtime if episode_runtime is not None else 'null'}",
    )
    text = text.replace(
        "target_runtime_seconds: 900",
        f"target_runtime_seconds: {episode_runtime if episode_runtime is not None else 'null'}",
    )
    text = text.replace("orientation: horizontal", f"orientation: {orientation or 'null'}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text, encoding="utf-8")


def initialize_series(
    target: Path,
    project_id: str,
    title: str,
    episode_count: int | None,
    episode_runtime: int | None,
    orientation: str | None,
) -> None:
    customize_series_file(
        target / "templates/SERIES_BIBLE.yaml",
        target / "series/SERIES_BIBLE.yaml",
        project_id,
        title,
        episode_count,
        episode_runtime,
        orientation,
    )
    customize_series_file(
        target / "templates/SEASON_MAP.yaml",
        target / "series/SE01/SEASON_MAP.yaml",
        project_id,
        title,
        episode_count,
        episode_runtime,
        orientation,
    )
    customize_series_file(
        target / "templates/EPISODE_CARD.yaml",
        target / "series/SE01/episodes/SE01_E001/EPISODE_CARD.yaml",
        project_id,
        title,
        episode_count,
        episode_runtime,
        orientation,
    )
    customize_series_file(
        target / "templates/SERIES_CONTINUITY.yaml",
        target / "registry/SERIES_CONTINUITY.yaml",
        project_id,
        title,
        episode_count,
        episode_runtime,
        orientation,
    )


def update_overview(target: Path, title: str, production_type: str) -> None:
    path = target / "项目工作区/00_项目总览.md"
    text = path.read_text(encoding="utf-8")
    text = text.replace("## 项目名称\n\n待定", f"## 项目名称\n\n{title}", 1)
    project_form = "连载剧集" if production_type == "series" else "单部影片"
    text = text.replace("## 项目形态\n\n待定（单部影片 / 连载剧集）", f"## 项目形态\n\n{project_form}", 1)
    current_scope = "第一季 / 第一集（创意开发中）" if production_type == "series" else "不适用"
    text = text.replace("## 当前季与当前集\n\n不适用或待定", f"## 当前季与当前集\n\n{current_scope}", 1)
    path.write_text(text, encoding="utf-8")


def configure_authority(target: Path, project_id: str, director_github: str) -> None:
    authority = target / "governance/AUTHORITY.yaml"
    text = authority.read_text(encoding="utf-8")
    text = replace_once(text, "project_id: DEMO", f"project_id: {project_id}", "authority.project_id")
    text = replace_once(
        text,
        "  github_username: zacharyli001",
        f"  github_username: {director_github}",
        "authority.director.github_username",
    )
    local_secret = secrets.token_urlsafe(48)
    secret_hash = hashlib.sha256(local_secret.encode("utf-8")).hexdigest()
    text = replace_once(
        text,
        "  local_key_sha256: null",
        f"  local_key_sha256: {secret_hash}",
        "authority.director.local_key_sha256",
    )
    authority.write_text(text, encoding="utf-8")

    key_path = target / ".film-os-local/DIRECTOR.key"
    key_path.parent.mkdir(parents=True, exist_ok=True)
    key_path.write_text(local_secret + "\n", encoding="utf-8")
    key_path.chmod(0o600)

    codeowners = target / ".github/CODEOWNERS"
    owner_text = codeowners.read_text(encoding="utf-8")
    owner_text = owner_text.replace("* @zacharyli001", f"* @{director_github}")
    codeowners.write_text(owner_text, encoding="utf-8")

    workflow = target / ".github/workflows/film-os-authority-guard.yml"
    workflow_text = workflow.read_text(encoding="utf-8")
    workflow_text = workflow_text.replace('--director "zacharyli001"', f'--director "{director_github}"')
    workflow.write_text(workflow_text, encoding="utf-8")


def initialize_git(target: Path) -> tuple[bool, str]:
    try:
        subprocess.run(["git", "init", "-b", "main"], cwd=target, check=True, capture_output=True, text=True)
        subprocess.run(["git", "add", "."], cwd=target, check=True, capture_output=True, text=True)
        subprocess.run(
            ["git", "commit", "-m", "chore: initialize Film OS project"],
            cwd=target,
            check=True,
            capture_output=True,
            text=True,
        )
        return True, "initial commit created"
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        return False, f"project created; Git commit needs Codex follow-up: {exc}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a Film OS production project from the master template.")
    parser.add_argument("--title", required=True, help="Human-readable project title")
    parser.add_argument("--type", choices=("film", "series"), required=True, dest="production_type")
    parser.add_argument("--output-parent", type=Path, default=DEFAULT_PARENT)
    parser.add_argument("--folder-name")
    parser.add_argument("--project-id")
    parser.add_argument("--episode-count", type=int)
    parser.add_argument("--episode-runtime", type=int, help="Target episode runtime in seconds")
    parser.add_argument("--orientation", choices=("horizontal", "vertical"))
    parser.add_argument(
        "--director-github",
        default="zacharyli001",
        help="GitHub username with exclusive canonical promotion authority",
    )
    parser.add_argument("--no-git", action="store_true", help="Skip local Git initialization")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        title = clean_title(args.title)
        project_id = validate_project_id(args.project_id) if args.project_id else generated_project_id(title)
        if args.episode_count is not None and args.episode_count < 1:
            raise ValueError("计划集数必须大于0。")
        if args.episode_runtime is not None and args.episode_runtime < 1:
            raise ValueError("单集时长必须大于0秒。")
        if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?", args.director_github):
            raise ValueError("导演 GitHub 用户名格式无效。")
        folder_name = clean_title(args.folder_name) if args.folder_name else folder_name_for(title)
        parent = args.output_parent.expanduser().resolve()
        target = (parent / folder_name).resolve()
        if target == TEMPLATE_ROOT or TEMPLATE_ROOT in target.parents:
            raise ValueError("新项目不能建立在母版文件夹内部。")
        if target.exists():
            raise FileExistsError(f"目标文件夹已经存在，未覆盖任何内容：{target}")
        parent.mkdir(parents=True, exist_ok=True)
        copy_template(target)
        demo_scene = target / "scenes/S001"
        if demo_scene.exists():
            shutil.rmtree(demo_scene)
        configure_project_yaml(
            target,
            title,
            project_id,
            args.production_type,
            args.episode_count,
            args.episode_runtime,
            args.orientation,
        )
        initialize_registry(target, project_id, args.production_type)
        initialize_tapnow(target, project_id, args.production_type)
        if args.production_type == "series":
            initialize_series(
                target,
                project_id,
                title,
                args.episode_count,
                args.episode_runtime,
                args.orientation,
            )
        else:
            series_ledger = target / "registry/SERIES_CONTINUITY.yaml"
            if series_ledger.exists():
                series_ledger.unlink()
        update_overview(target, title, args.production_type)
        configure_authority(target, project_id, args.director_github)
        initialize_installation(target)
        git_ok, git_note = (False, "Git initialization skipped") if args.no_git else initialize_git(target)
        result = {
            "status": "created",
            "title": title,
            "project_id": project_id,
            "production_type": args.production_type,
            "project_path": str(target),
            "git_initialized": git_ok,
            "git_note": git_note,
            "github_remote": None,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(f"Film OS project creation stopped safely: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
