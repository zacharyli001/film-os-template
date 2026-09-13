#!/usr/bin/env python3
"""Build a self-contained Film OS member package without changing canonical files."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import io
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tarfile


ROOT = Path(__file__).resolve().parents[1]
AUTHOR = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]{0,38}$")


def git(root: Path, *args: str, binary: bool = False):
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return result.stdout if binary else result.stdout.decode("utf-8").strip()


def safe_extract_git_archive(data: bytes, destination: Path) -> None:
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:") as archive:
        for member in archive.getmembers():
            path = PurePosixPath(member.name)
            if path.is_absolute() or ".." in path.parts or member.issym() or member.islnk():
                raise RuntimeError(f"正式基线含不安全路径，已停止：{member.name}")
        try:
            archive.extractall(destination, filter="data")
        except TypeError:
            archive.extractall(destination)


def copy_delta(source_root: Path, relative: str, destination_root: Path) -> None:
    source = source_root / relative
    if source.is_symlink():
        raise RuntimeError(f"成员包不接受符号链接：{relative}")
    if source.is_file():
        destination = destination_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a Film OS member delivery package.")
    parser.add_argument("--project", type=Path, default=ROOT)
    parser.add_argument("--author", required=True)
    parser.add_argument("--base", default="origin/main")
    parser.add_argument("--output-parent", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        project = args.project.expanduser().resolve()
        author = args.author.strip()
        if not AUTHOR.fullmatch(author):
            raise ValueError("成员 ID 只能使用英文字母、数字和连字符。")
        if not (project / "PROJECT.yaml").is_file() or not (project / ".git").is_dir():
            raise RuntimeError("必须在一个已有 Git 历史的 Film OS 作品项目中制作成员包。")

        base_commit = git(project, "rev-parse", "--verify", f"{args.base}^{{commit}}")
        base_tree = git(project, "rev-parse", f"{base_commit}^{{tree}}")
        stamp = datetime.now(timezone.utc).replace(microsecond=0)
        compact = stamp.strftime("%Y%m%dT%H%M%SZ")
        created_at = stamp.strftime("%Y-%m-%dT%H:%M:%SZ")
        package_id = f"{compact}_{author.lower()}"
        output_parent = (
            args.output_parent.expanduser().resolve()
            if args.output_parent
            else project.parent / "FilmOS成员交付包"
        )
        package = output_parent / package_id
        if package.exists():
            raise FileExistsError(f"交付包已经存在，未覆盖：{package}")

        snapshot = package / "00_正式基线只读"
        modified = package / "01_个人增量/修改建议"
        added = package / "01_个人增量/新增内容"
        package.mkdir(parents=True)
        safe_extract_git_archive(git(project, "archive", "--format=tar", base_commit, binary=True), snapshot)

        changed_text = git(project, "diff", "--name-status", "--no-renames", base_commit)
        changed = [line.split("\t", 1) for line in changed_text.splitlines() if line.strip()]
        deleted: list[str] = []
        delta_files: list[str] = []
        for row in changed:
            if len(row) != 2:
                continue
            status, relative = row
            if relative.startswith((".film-os-local/", "incoming_packages/")):
                continue
            if status == "D":
                deleted.append(relative)
            elif status == "A":
                copy_delta(project, relative, added)
                delta_files.append(f"新增内容/{relative}")
            else:
                copy_delta(project, relative, modified)
                delta_files.append(f"修改建议/{relative}")

        untracked_text = git(
            project,
            "ls-files",
            "--others",
            "--exclude-standard",
            "--",
            ":(exclude).film-os-local/**",
            ":(exclude)incoming_packages/**",
        )
        for relative in [line for line in untracked_text.splitlines() if line.strip()]:
            copy_delta(project, relative, added)
            delta_files.append(f"新增内容/{relative}")

        delta_root = package / "01_个人增量"
        delta_root.mkdir(parents=True, exist_ok=True)
        (delta_root / "删除建议.txt").write_text(
            "\n".join(deleted) + ("\n" if deleted else ""), encoding="utf-8"
        )
        manifest = [
            "schema_version: film-os/member-package/v1",
            f"package_id: {package_id}",
            f"author_id: {author}",
            f"created_at: {json.dumps(created_at)}",
            f"base_commit: {base_commit}",
            f"base_tree: {base_tree}",
            "status: non_canonical_proposal",
            "contains_full_canonical_snapshot: true",
            "delta_root: 01_个人增量",
            "derived_work_is_non_canonical: true",
            f"delta_file_count: {len(delta_files)}",
            f"deletion_proposal_count: {len(deleted)}",
            "director_review:",
            "  status: pending",
            "  reviewed_by: null",
            "  reviewed_at: null",
            "  decision: null",
            "",
        ]
        (package / "PACKAGE.yaml").write_text("\n".join(manifest), encoding="utf-8")
        (package / "README.md").write_text(
            "# Film OS 成员交付包\n\n"
            "`00_正式基线只读/` 是制作本次工作的正式资料快照；"
            "`01_个人增量/` 是成员建议和全部衍生成果。"
            "整个包都不是正式主线，只有导演工作区可以归束。\n",
            encoding="utf-8",
        )
        print(json.dumps({"status": "created", "package": str(package), "package_id": package_id}, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(f"Film OS member package stopped safely: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
