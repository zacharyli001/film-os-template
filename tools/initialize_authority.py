#!/usr/bin/env python3
"""Add authority records to an existing Film OS production without overwriting data."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import re
import secrets
import shutil
import sys


SOURCE_ROOT = Path(__file__).resolve().parents[1]
GITHUB_USER = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$")


def project_id_from(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"^\s*id:\s*([A-Z0-9][A-Z0-9_]{1,63})\s*$", text, re.MULTILINE)
    if not match:
        raise RuntimeError("PROJECT.yaml 中找不到有效 project.id。")
    return match.group(1)


def add_from_source(source: Path, target: Path) -> None:
    if target.exists():
        raise FileExistsError(f"为避免覆盖，初始化已停止：{target} 已存在。")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Initialize Film OS director authority safely.")
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument("--director-github", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        target = args.target.expanduser().resolve()
        director = args.director_github.strip()
        if not GITHUB_USER.fullmatch(director):
            raise ValueError("导演 GitHub 用户名格式无效。")
        project_yaml = target / "PROJECT.yaml"
        if not project_yaml.is_file():
            raise RuntimeError("目标不是 Film OS 作品项目：缺少 PROJECT.yaml。")

        project_id = project_id_from(project_yaml)
        authority_target = target / "governance/AUTHORITY.yaml"
        submissions_target = target / "submissions/README.md"
        key_path = target / ".film-os-local/DIRECTOR.key"
        for path in (authority_target, submissions_target):
            if path.exists():
                raise FileExistsError(f"为避免覆盖，初始化已停止：{path} 已存在。")
        if key_path.exists():
            raise FileExistsError(f"为避免覆盖，初始化已停止：{key_path} 已存在。")

        for relative, old, new in (
            (".github/CODEOWNERS", "* @zacharyli001", f"* @{director}"),
            (
                ".github/workflows/film-os-authority-guard.yml",
                '--director "zacharyli001"',
                f'--director "{director}"',
            ),
        ):
            path = target / relative
            if path.is_file():
                text = path.read_text(encoding="utf-8")
                if new not in text and old not in text:
                    raise RuntimeError(f"{relative} 已有无法识别的权限定制，未覆盖。")

        add_from_source(SOURCE_ROOT / "templates/AUTHORITY.yaml", authority_target)
        add_from_source(SOURCE_ROOT / "templates/SUBMISSIONS_README.md", submissions_target)

        authority_text = authority_target.read_text(encoding="utf-8")
        authority_text = authority_text.replace("project_id: DEMO", f"project_id: {project_id}", 1)
        authority_text = authority_text.replace(
            "  github_username: zacharyli001", f"  github_username: {director}", 1
        )
        local_secret = secrets.token_urlsafe(48)
        secret_hash = hashlib.sha256(local_secret.encode("utf-8")).hexdigest()
        authority_text = authority_text.replace(
            "  local_key_sha256: null", f"  local_key_sha256: {secret_hash}", 1
        )
        authority_target.write_text(authority_text, encoding="utf-8")

        member_config = target / "governance/MEMBER_DELIVERY_REPOSITORIES.yaml"
        if not member_config.is_file():
            member_config.parent.mkdir(parents=True, exist_ok=True)
            member_text = (SOURCE_ROOT / "templates/MEMBER_DELIVERY_REPOSITORIES.yaml").read_text(
                encoding="utf-8"
            )
            member_text = member_text.replace("project_id: DEMO", f"project_id: {project_id}", 1)
            member_config.write_text(member_text, encoding="utf-8")

        key_path.parent.mkdir(parents=True, exist_ok=True)
        key_path.write_text(local_secret + "\n", encoding="utf-8")
        key_path.chmod(0o600)

        for relative, old, new in (
            (".github/CODEOWNERS", "* @zacharyli001", f"* @{director}"),
            (
                ".github/workflows/film-os-authority-guard.yml",
                '--director "zacharyli001"',
                f'--director "{director}"',
            ),
        ):
            path = target / relative
            if not path.is_file():
                add_from_source(SOURCE_ROOT / relative, path)
            text = path.read_text(encoding="utf-8")
            if new not in text:
                path.write_text(text.replace(old, new, 1), encoding="utf-8")

        pr_template = target / ".github/pull_request_template.md"
        if not pr_template.exists():
            add_from_source(SOURCE_ROOT / ".github/pull_request_template.md", pr_template)

        print(f"Film OS authority initialized for {project_id}; director: @{director}")
        print("下一步：在 GitHub 为 main 开启服务器端分支保护。")
        return 0
    except Exception as exc:
        print(f"Film OS authority initialization stopped safely: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
