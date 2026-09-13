#!/usr/bin/env python3
"""Plan and apply non-destructive Film OS template upgrades."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Any


SOURCE_ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = SOURCE_ROOT / "upgrade/POLICY.json"
INSTALLATION_PATH = Path(".film-os/INSTALLATION.json")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_release(root: Path) -> str:
    text = (root / "FILM_OS_VERSION.yaml").read_text(encoding="utf-8")
    match = re.search(r"^release:\s*[\"']?([^\"'\s]+)", text, re.MULTILINE)
    if not match:
        raise RuntimeError("FILM_OS_VERSION.yaml 缺少 release 字段。")
    return match.group(1)


def validate_relative(value: str) -> Path:
    rel = Path(value)
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError(f"升级策略包含不安全路径：{value}")
    return rel


def managed_files(root: Path, policy: dict[str, Any]) -> list[str]:
    results: set[str] = set()
    for value in policy["managed_files"]:
        rel = validate_relative(value)
        path = root / rel
        if path.is_file() and not path.is_symlink():
            results.add(rel.as_posix())
    for value in policy["managed_directories"]:
        rel = validate_relative(value)
        directory = root / rel
        if not directory.is_dir() or directory.is_symlink():
            continue
        for path in directory.rglob("*"):
            if path.is_file() and not path.is_symlink() and path.name != ".DS_Store" and "__pycache__" not in path.parts:
                results.add(path.relative_to(root).as_posix())
    return sorted(results)


def source_hashes(root: Path, policy: dict[str, Any]) -> dict[str, str]:
    return {rel: sha256_file(root / rel) for rel in managed_files(root, policy)}


def git_output(root: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args], cwd=root, check=True, capture_output=True, text=True
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def git_clean(root: Path) -> bool:
    status = git_output(root, "status", "--porcelain")
    return status == ""


def git_paths_clean(root: Path, paths: list[str]) -> bool:
    status = git_output(root, "status", "--porcelain", "--", *paths)
    return status == ""


def hashes_from_ref(ref: str, paths: list[str]) -> dict[str, str]:
    if git_output(SOURCE_ROOT, "rev-parse", "--verify", ref) is None:
        raise RuntimeError(f"找不到母版历史版本：{ref}")
    hashes: dict[str, str] = {}
    for rel in paths:
        try:
            result = subprocess.run(
                ["git", "show", f"{ref}:{rel}"],
                cwd=SOURCE_ROOT,
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError:
            continue
        hashes[rel] = sha256_bytes(result.stdout)
    return hashes


def installation_record(target: Path) -> dict[str, Any] | None:
    path = target / INSTALLATION_PATH
    return load_json(path) if path.is_file() else None


def build_plan(
    target: Path,
    baseline_ref: str | None = None,
    baseline_version: str | None = None,
) -> dict[str, Any]:
    target = target.expanduser().resolve()
    if (SOURCE_ROOT / "PROJECT.yaml").exists():
        raise RuntimeError("当前不是 Film OS 母版，升级已停止。")
    if target == SOURCE_ROOT or SOURCE_ROOT in target.parents:
        raise RuntimeError("目标不能是母版本身或母版内部文件夹。")
    if not (target / "PROJECT.yaml").is_file():
        raise RuntimeError("目标不是有效的 Film OS 作品项目：缺少 PROJECT.yaml。")

    policy = load_json(POLICY_PATH)
    current_hashes = source_hashes(SOURCE_ROOT, policy)
    record = installation_record(target)
    if record:
        baseline_hashes = dict(record.get("source_hashes", {}))
        installed_version = record.get("installed_version", "unknown")
        baseline_kind = "installation_record"
    elif baseline_ref:
        candidate_paths = sorted(set(current_hashes) | set(managed_files(SOURCE_ROOT, policy)))
        baseline_hashes = hashes_from_ref(baseline_ref, candidate_paths)
        installed_version = baseline_version or "legacy"
        baseline_kind = f"git_ref:{baseline_ref}"
    else:
        baseline_hashes = {}
        installed_version = "unknown"
        baseline_kind = "missing"

    changes: list[dict[str, str]] = []
    conflicts: list[dict[str, str]] = []
    preserved: list[dict[str, str]] = []
    unchanged: list[str] = []

    for rel, source_hash in current_hashes.items():
        target_path = target / rel
        target_hash = sha256_file(target_path) if target_path.is_file() else None
        old_hash = baseline_hashes.get(rel)
        if target_hash == source_hash:
            unchanged.append(rel)
        elif target_hash is None:
            if old_hash is not None:
                conflicts.append({"path": rel, "reason": "作品项目曾删除此系统文件"})
            else:
                changes.append({"path": rel, "action": "add"})
        elif old_hash is None:
            conflicts.append({"path": rel, "reason": "缺少可验证的旧版本基线"})
        elif target_hash == old_hash:
            changes.append({"path": rel, "action": "update"})
        elif source_hash == old_hash:
            preserved.append({"path": rel, "reason": "作品项目的本地定制，母版本次未改动"})
        else:
            conflicts.append({"path": rel, "reason": "作品项目和母版都修改了同一系统文件"})

    retired: list[dict[str, str]] = []
    for rel, old_hash in baseline_hashes.items():
        if rel in current_hashes:
            continue
        target_path = target / rel
        if target_path.is_file():
            reason = "旧系统文件已退出母版，但为安全起见保留，不自动删除"
            if sha256_file(target_path) != old_hash:
                reason = "已退出母版的本地定制文件，保留不删除"
            retired.append({"path": rel, "reason": reason})

    clean = git_clean(target)
    source_clean = git_paths_clean(SOURCE_ROOT, sorted(current_hashes))
    has_upgrade_work = bool(changes) or installed_version != read_release(SOURCE_ROOT)
    ready = not conflicts and clean and source_clean and baseline_kind != "missing" and has_upgrade_work
    return {
        "status": "ready" if ready else ("up_to_date" if not has_upgrade_work and not conflicts else "review_required"),
        "source_root": str(SOURCE_ROOT),
        "target_root": str(target),
        "installed_version": installed_version,
        "target_version": read_release(SOURCE_ROOT),
        "baseline": baseline_kind,
        "git_clean": clean,
        "source_git_clean": source_clean,
        "changes": changes,
        "preserved_local_customizations": preserved,
        "retired_files_preserved": retired,
        "conflicts": conflicts,
        "protected_files": policy["protected_files"],
        "protected_directories": policy["protected_directories"],
        "unchanged_count": len(unchanged),
    }


def source_identity() -> dict[str, Any]:
    policy = load_json(POLICY_PATH)
    paths = managed_files(SOURCE_ROOT, policy)
    return {
        "repository": git_output(SOURCE_ROOT, "config", "--get", "remote.origin.url"),
        "revision": git_output(SOURCE_ROOT, "rev-parse", "HEAD"),
        "managed_source_dirty": not git_paths_clean(SOURCE_ROOT, paths),
    }


def write_installation_record(target: Path, version: str, hashes: dict[str, str]) -> None:
    overrides = []
    for rel, expected_hash in hashes.items():
        target_path = target / rel
        if target_path.is_file() and sha256_file(target_path) != expected_hash:
            overrides.append(rel)
    data = {
        "schema_version": "film-os/installation/v1",
        "installed_version": version,
        "installed_at": utc_now(),
        "source": source_identity(),
        "source_hashes": hashes,
        "local_overrides": sorted(overrides),
    }
    path = target / INSTALLATION_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def initialize_installation(target: Path) -> None:
    policy = load_json(POLICY_PATH)
    write_installation_record(target, read_release(SOURCE_ROOT), source_hashes(SOURCE_ROOT, policy))


def append_upgrade_log(target: Path, from_version: str, to_version: str, actor: str) -> None:
    path = target / "registry/VERSION_LOG.yaml"
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    numbers = [int(value) for value in re.findall(r"entry_id:\s*VL-(\d+)", text)]
    entry_id = f"VL-{(max(numbers, default=0) + 1):04d}"
    block = [
        f"  - entry_id: {entry_id}",
        f"    timestamp: {json.dumps(utc_now())}",
        f"    actor: {json.dumps(actor, ensure_ascii=False)}",
        "    entity_type: system",
        "    entity_id: FILM_OS",
        "    season_id: null",
        "    episode_id: null",
        f"    from_version: {json.dumps(from_version)}",
        f"    to_version: {json.dumps(to_version)}",
        "    action: system_upgraded",
        "    changed_variable: film_os_version",
        f"    summary: {json.dumps(f'Upgraded Film OS from {from_version} to {to_version}.')}",
        "    related_gate: null",
        "    approval: null",
    ]
    path.write_text(text.rstrip() + "\n" + "\n".join(block) + "\n", encoding="utf-8")


def apply_plan(plan: dict[str, Any], actor: str) -> dict[str, Any]:
    if plan["status"] != "ready":
        raise RuntimeError("当前检查结果不是 ready，未写入任何升级文件。")
    target = Path(plan["target_root"])
    if not git_clean(target):
        raise RuntimeError("作品项目出现新的未保存修改，升级已停止。")
    for item in plan["changes"]:
        rel = item["path"]
        source_path = SOURCE_ROOT / rel
        target_path = target / rel
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)
    policy = load_json(POLICY_PATH)
    hashes = source_hashes(SOURCE_ROOT, policy)
    write_installation_record(target, plan["target_version"], hashes)
    append_upgrade_log(target, plan["installed_version"], plan["target_version"], actor)
    result = dict(plan)
    result["status"] = "applied"
    result["applied_at"] = utc_now()
    result["actor"] = actor
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Safely plan or apply a Film OS project upgrade.")
    parser.add_argument("mode", choices=("plan", "apply"))
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument("--baseline-ref")
    parser.add_argument("--baseline-version")
    parser.add_argument("--actor", default="film-os-upgrader")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        plan = build_plan(args.target, args.baseline_ref, args.baseline_version)
        result = apply_plan(plan, args.actor) if args.mode == "apply" else plan
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(f"Film OS upgrade stopped safely: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
