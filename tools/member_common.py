#!/usr/bin/env python3
"""Shared helpers for Film OS member delivery repositories.

Member repositories are convenience workspaces, not canonical repositories.
They keep ``main`` as a read-only mirror of the director's canonical baseline
and put each proposal on an isolated proposal branch.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Any, Iterable


SESSION_DIR = ".film-os-member"
CONFIG_FILE = "CONFIG.yaml"
SESSION_FILE = "SESSION.yaml"
HISTORY_DIR = "history"
MEMBER_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9-]{0,38}$")
PROJECT_ID_RE = re.compile(r"^[A-Z0-9][A-Z0-9_]{1,63}$")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def utc_compact() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def yaml_scalar(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def git(
    cwd: Path,
    *args: str,
    check: bool = True,
    binary: bool = False,
) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        cwd=cwd,
        capture_output=True,
        text=not binary,
        check=check,
    )


def git_text(cwd: Path, *args: str, check: bool = True) -> str:
    return git(cwd, *args, check=check).stdout.strip()


def git_bytes(cwd: Path, *args: str, check: bool = True) -> bytes:
    return git(cwd, *args, check=check, binary=True).stdout


def current_branch(cwd: Path) -> str:
    return git_text(cwd, "branch", "--show-current")


def branch_exists(cwd: Path, branch: str) -> bool:
    return git(cwd, "rev-parse", "--verify", f"refs/heads/{branch}", check=False).returncode == 0


def commit_exists(cwd: Path, ref: str) -> bool:
    return git(cwd, "cat-file", "-e", f"{ref}^{{commit}}", check=False).returncode == 0


def remote_key(url: str) -> str:
    value = url.strip().rstrip("/")
    if value.endswith(".git"):
        value = value[:-4]
    return value


def validate_member_id(value: str) -> str:
    member_id = value.strip()
    if not MEMBER_ID_RE.fullmatch(member_id):
        raise ValueError("成员 ID 只能使用英文字母、数字和连字符，长度 1-39。")
    return member_id


def validate_project_id(value: str) -> str:
    project_id = value.strip().upper()
    if not PROJECT_ID_RE.fullmatch(project_id):
        raise ValueError("项目代号必须由大写英文字母、数字和下划线组成，长度 2-64，且不能以下划线开头。")
    return project_id


def unquote_yaml_scalar(value: str) -> str:
    value = value.strip()
    if value in {"", "null", "~"}:
        return ""
    if len(value) >= 2 and value[0] == value[-1] == '"':
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value[1:-1]
    if len(value) >= 2 and value[0] == value[-1] == "'":
        return value[1:-1].replace("''", "'")
    return value


def top_level_scalars(text: str) -> dict[str, str]:
    """Read simple top-level ``key: value`` fields, including block scalars."""
    result: dict[str, str] = {}
    lines = text.splitlines()
    for index, line in enumerate(lines):
        match = re.match(r"^([A-Za-z0-9_]+):\s*(.*?)\s*$", line)
        if not match:
            continue
        key, raw = match.group(1), match.group(2)
        if raw in {">", ">-", "|", "|-"}:
            continuation: list[str] = []
            for following in lines[index + 1 :]:
                if following and not following[0].isspace():
                    break
                if following.strip():
                    continuation.append(following.strip())
            result[key] = " ".join(continuation) if raw.startswith(">") else "\n".join(continuation)
        else:
            result[key] = unquote_yaml_scalar(raw)
    return result


def project_id_from_text(text: str) -> str:
    lines = text.splitlines()
    in_project = False
    for line in lines:
        if re.match(r"^project:\s*$", line):
            in_project = True
            continue
        if in_project:
            if line and not line[0].isspace():
                break
            match = re.match(r"^\s+id:\s*([A-Z0-9_]+)\s*$", line)
            if match:
                return match.group(1)
    raise ValueError("PROJECT.yaml 中找不到有效的 project.id。")


def project_id_from_ref(workspace: Path, ref: str) -> str:
    text = git_text(workspace, "show", f"{ref}:PROJECT.yaml")
    return project_id_from_text(text)


def session_root(workspace: Path) -> Path:
    return workspace / SESSION_DIR


def config_path(workspace: Path) -> Path:
    return session_root(workspace) / CONFIG_FILE


def session_path(workspace: Path) -> Path:
    return session_root(workspace) / SESSION_FILE


def read_scalar_file(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    return top_level_scalars(path.read_text(encoding="utf-8"))


def write_scalar_file(path: Path, values: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(f"{key}: {yaml_scalar(str(value))}" for key, value in values.items())
    path.write_text(text + "\n", encoding="utf-8")


def archive_session(workspace: Path) -> Path | None:
    path = session_path(workspace)
    if not path.is_file():
        return None
    archive_dir = session_root(workspace) / HISTORY_DIR
    archive_dir.mkdir(parents=True, exist_ok=True)
    archived = archive_dir / f"{utc_compact()}_SESSION.yaml"
    counter = 1
    while archived.exists():
        archived = archive_dir / f"{utc_compact()}_{counter:02d}_SESSION.yaml"
        counter += 1
    os.replace(path, archived)
    return archived


def ensure_local_exclude(workspace: Path) -> None:
    exclude = workspace / ".git" / "info" / "exclude"
    exclude.parent.mkdir(parents=True, exist_ok=True)
    existing = exclude.read_text(encoding="utf-8") if exclude.is_file() else ""
    entry = f"/{SESSION_DIR}/"
    if entry not in existing.splitlines():
        with exclude.open("a", encoding="utf-8") as handle:
            if existing and not existing.endswith("\n"):
                handle.write("\n")
            handle.write(f"# Film OS member session (local only)\n{entry}\n")


def changed_paths(workspace: Path) -> list[str]:
    """Return every changed or untracked path, without collapsing directories."""
    raw = git_bytes(
        workspace,
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
    )
    tokens = raw.split(b"\0")
    paths: list[str] = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        index += 1
        if not token:
            continue
        record = token.decode("utf-8", errors="surrogateescape")
        if len(record) < 4:
            continue
        status = record[:2]
        path = record[3:]
        if status[0] in {"R", "C"} and index < len(tokens):
            old_path = tokens[index].decode("utf-8", errors="surrogateescape")
            index += 1
            paths.append(old_path)
        paths.append(path)
    return paths


def diff_paths(workspace: Path, base: str, head: str = "HEAD") -> list[str]:
    raw = git_bytes(
        workspace,
        "diff",
        "--name-only",
        "--no-renames",
        "-z",
        base,
        head,
    )
    return [
        item.decode("utf-8", errors="surrogateescape")
        for item in raw.split(b"\0")
        if item
    ]


def paths_outside(paths: Iterable[str], prefix: str) -> list[str]:
    normalized = prefix.rstrip("/") + "/"
    return [path for path in paths if not path.startswith(normalized)]


def parse_repository_config(text: str) -> dict[str, Any]:
    scalars = top_level_scalars(text)
    repositories: list[dict[str, str]] = []
    lines = text.splitlines()
    starts = [
        index
        for index, line in enumerate(lines)
        if re.match(r"^\s*-\s+member_id:\s*", line)
    ]
    for position, start in enumerate(starts):
        end = starts[position + 1] if position + 1 < len(starts) else len(lines)
        block = "\n".join(lines[start:end])
        fields: dict[str, str] = {}
        for key in ("member_id", "display_name", "remote_url", "local_dir"):
            match = re.search(rf"(?m)^\s*-?\s*{re.escape(key)}:\s*(.*?)\s*$", block)
            fields[key] = unquote_yaml_scalar(match.group(1)) if match else ""
        if fields["member_id"]:
            repositories.append(fields)
    return {
        "schema_version": scalars.get("schema_version", ""),
        "project_id": scalars.get("project_id", ""),
        "default_branch": scalars.get("default_branch", "main") or "main",
        "proposal_branch_prefix": scalars.get("proposal_branch_prefix", "proposal/") or "proposal/",
        "repositories": repositories,
    }

