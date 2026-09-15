#!/usr/bin/env python3
"""Create or update a production project's team roster without hand-editing YAML."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

from member_common import (
    parse_repository_config,
    project_id_from_text,
    unquote_yaml_scalar,
    utc_now,
    yaml_scalar,
)


GITHUB_USER = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$")
TEAM_START = "<!-- TEAM:START -->"
TEAM_END = "<!-- TEAM:END -->"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="建立或更新 Film OS 团队名单。")
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--director-name")
    parser.add_argument("--director-github")
    parser.add_argument(
        "--member",
        action="append",
        default=[],
        help="主创格式：显示名称|GitHub用户名|负责内容|交付仓库地址（后两项可省略）",
    )
    parser.add_argument("--expected-size", type=int)
    parser.add_argument("--replace-members", action="store_true")
    parser.add_argument("--default-branch", default="main")
    parser.add_argument("--no-delivery-config", action="store_true")
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
        raise PermissionError("当前不是已验证的导演工作区，不能修改团队名单。")
    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("导演权限验证返回了无法识别的结果。") from exc
    if report.get("role") != "director":
        raise PermissionError("当前不是已验证的导演工作区，不能修改团队名单。")
    return report


def parse_team_yaml(text: str) -> dict:
    result: dict = {"director": {}, "members": []}
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        top = re.match(r"^([A-Za-z0-9_]+):\s*(.*?)\s*$", line)
        if not top:
            index += 1
            continue
        key, raw = top.group(1), top.group(2)
        if key == "director":
            block: dict[str, str] = {}
            index += 1
            while index < len(lines) and (not lines[index] or lines[index][0].isspace()):
                field = re.match(r"^\s+([A-Za-z0-9_]+):\s*(.*?)\s*$", lines[index])
                if field:
                    block[field.group(1)] = unquote_yaml_scalar(field.group(2))
                index += 1
            result["director"] = block
            continue
        if key == "members":
            members: list[dict[str, str]] = []
            current: dict[str, str] | None = None
            if raw.strip() in {"", "[]"}:
                index += 1
                while index < len(lines) and (not lines[index] or lines[index][0].isspace()):
                    item = re.match(r"^\s*-\s+([A-Za-z0-9_]+):\s*(.*?)\s*$", lines[index])
                    if item:
                        if current:
                            members.append(current)
                        current = {item.group(1): unquote_yaml_scalar(item.group(2))}
                    else:
                        field = re.match(r"^\s+([A-Za-z0-9_]+):\s*(.*?)\s*$", lines[index])
                        if field and current is not None:
                            current[field.group(1)] = unquote_yaml_scalar(field.group(2))
                    index += 1
                if current:
                    members.append(current)
                result["members"] = members
                continue
        result[key] = unquote_yaml_scalar(raw)
        index += 1
    return result


def authority_director(project: Path) -> str:
    path = project / "governance/AUTHORITY.yaml"
    if not path.is_file():
        return ""
    text = path.read_text(encoding="utf-8")
    match = re.search(r"(?ms)^director:\s*\n(?:.*\n)*?\s+github_username:\s*([^\s#]+)", text)
    return unquote_yaml_scalar(match.group(1)) if match else ""


def parse_member_arg(value: str) -> dict[str, str]:
    parts = [part.strip() for part in value.split("|")]
    if len(parts) < 2 or not parts[0] or not parts[1]:
        raise ValueError("主创格式必须是：显示名称|GitHub用户名|负责内容|交付仓库地址")
    display_name, github_username = parts[0], parts[1]
    if not GITHUB_USER.fullmatch(github_username):
        raise ValueError(f"GitHub 用户名格式无效：{github_username}")
    return {
        "display_name": display_name,
        "github_username": github_username,
        "role": parts[2] if len(parts) > 2 and parts[2] else "待补充",
        "delivery_repo": parts[3] if len(parts) > 3 else "",
    }


def repo_name_from_url(url: str) -> str:
    name = url.strip().rstrip("/").split("/")[-1]
    return name[:-4] if name.endswith(".git") else name


def write_team(project: Path, project_id: str, director: dict[str, str], members: list[dict[str, str]]) -> dict:
    team_size = 1 + len(members)
    setup_status = "complete" if director.get("display_name") and director["display_name"] != "待补充" else "pending"
    lines = [
        "schema_version: film-os/team/v1",
        f"project_id: {project_id}",
        f"setup_status: {setup_status}",
        f"team_size: {team_size}",
        "director:",
        f"  display_name: {yaml_scalar(director.get('display_name', '待补充'))}",
        f"  github_username: {yaml_scalar(director.get('github_username', ''))}",
        "  role: 导演",
    ]
    if not members:
        lines.append("members: []")
    else:
        lines.append("members:")
        for member in members:
            lines.extend(
                [
                    f"  - display_name: {yaml_scalar(member.get('display_name', '待补充'))}",
                    f"    github_username: {yaml_scalar(member.get('github_username', ''))}",
                    f"    role: {yaml_scalar(member.get('role', '待补充'))}",
                    (
                        f"    delivery_repo: {yaml_scalar(member['delivery_repo'])}"
                        if member.get("delivery_repo")
                        else "    delivery_repo: null"
                    ),
                ]
            )
    lines.extend(
        [
            f"updated_at: {yaml_scalar(utc_now())}",
            f"updated_by: {yaml_scalar(director.get('github_username', ''))}",
        ]
    )
    path = project / "governance/TEAM.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "team_size": team_size,
        "setup_status": setup_status,
        "director": director,
        "members": members,
    }


def render_team_block(team: dict) -> str:
    director = team["director"]
    members = team["members"]
    lines = [
        TEAM_START,
        "## 团队名单",
        "",
        f"- 导演：{director.get('display_name', '待补充')}（GitHub: {director.get('github_username', '待补充')}）",
        f"- 团队人数：{team['team_size']}",
    ]
    if members:
        lines.append("- 主创：")
        for member in members:
            repo = member.get("delivery_repo") or "未登记"
            lines.append(
                f"  - {member.get('display_name', '待补充')}"
                f"（GitHub: {member.get('github_username', '待补充')}）"
                f"｜负责：{member.get('role', '待补充')}｜交付仓库：{repo}"
            )
    else:
        lines.append("- 主创：暂无，待补充")
    lines.extend(
        [
            "",
            "## 身份边界",
            "",
            "- 导演拥有导演端、最终决定和审批权。",
            "- 主创指除导演之外的所有人员，不拥有导演权限。",
            "- 只有导演端可以归整和发布正式主线。",
            TEAM_END,
        ]
    )
    return "\n".join(lines)


def write_team_markdown(project: Path, team: dict) -> Path:
    path = project / "项目工作区/00_团队与权限.md"
    block = render_team_block(team)
    if path.is_file():
        text = path.read_text(encoding="utf-8")
        pattern = re.compile(rf"{re.escape(TEAM_START)}.*?{re.escape(TEAM_END)}", re.DOTALL)
        text = pattern.sub(block, text) if pattern.search(text) else text.rstrip() + "\n\n" + block + "\n"
    else:
        text = "# 团队与权限\n\n" + block + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def write_delivery_config(project: Path, project_id: str, team: dict, default_branch: str) -> Path | None:
    path = project / "governance/MEMBER_DELIVERY_REPOSITORIES.yaml"
    existing: dict = {"repositories": []}
    if path.is_file():
        existing = parse_repository_config(path.read_text(encoding="utf-8"))
    existing_by_id = {
        item.get("member_id", "").lower(): dict(item)
        for item in existing.get("repositories", [])
        if item.get("member_id")
    }
    roster_ids: list[str] = []
    for member in team["members"]:
        member_id = member.get("github_username", "")
        repo = member.get("delivery_repo", "")
        if not member_id or not repo:
            continue
        roster_ids.append(member_id.lower())
        old = existing_by_id.get(member_id.lower(), {})
        existing_by_id[member_id.lower()] = {
            "member_id": member_id,
            "display_name": member.get("display_name", member_id),
            "remote_url": repo,
            "local_dir": old.get("local_dir") or repo_name_from_url(repo),
        }
    if not existing_by_id:
        return None
    ordered = [existing_by_id.pop(key) for key in roster_ids if key in existing_by_id]
    ordered.extend(existing_by_id.values())
    if not path.is_file() and not ordered:
        return None
    lines = [
        "schema_version: film-os/member-delivery-repositories/v1",
        f"project_id: {project_id}",
        "review_trigger:",
        "  phrases:",
        "    - 需要审批",
        "    - 审核成员提案",
        "  behavior: fetch_all_then_review_only",
        f"default_branch: {default_branch}",
        "proposal_branch_prefix: proposal/",
        "repositories:",
    ]
    if not ordered:
        lines.append("  []")
    else:
        for item in ordered:
            lines.extend(
                [
                    f"  - member_id: {yaml_scalar(item.get('member_id', ''))}",
                    f"    display_name: {yaml_scalar(item.get('display_name', ''))}",
                    f"    remote_url: {yaml_scalar(item.get('remote_url', ''))}",
                    f"    local_dir: {yaml_scalar(item.get('local_dir', ''))}",
                ]
            )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> int:
    args = parse_args()
    project = args.project.expanduser().resolve()
    try:
        project_yaml = project / "PROJECT.yaml"
        if not project_yaml.is_file():
            raise RuntimeError("目标不是 Film OS 作品项目：缺少 PROJECT.yaml。")
        authority_check(project)
        project_id = project_id_from_text(project_yaml.read_text(encoding="utf-8"))
        team_path = project / "governance/TEAM.yaml"
        existing = parse_team_yaml(team_path.read_text(encoding="utf-8")) if team_path.is_file() else {}
        existing_director = existing.get("director", {})
        director_name = args.director_name or existing_director.get("display_name") or "待补充"
        director_github = (
            args.director_github
            or existing_director.get("github_username")
            or authority_director(project)
        )
        if not director_github:
            raise RuntimeError("缺少导演 GitHub 用户名。")
        if not GITHUB_USER.fullmatch(director_github):
            raise ValueError("导演 GitHub 用户名格式无效。")

        members = [] if args.replace_members else list(existing.get("members", []))
        for raw in args.member:
            parsed = parse_member_arg(raw)
            match = next(
                (
                    index
                    for index, member in enumerate(members)
                    if member.get("github_username", "").lower() == parsed["github_username"].lower()
                ),
                None,
            )
            if match is None:
                members.append(parsed)
            else:
                members[match] = parsed

        expected_size = 1 + len(members)
        if args.expected_size is not None and args.expected_size != expected_size:
            raise RuntimeError(
                f"团队人数不一致：你填写 {args.expected_size} 人，当前名单计算为 {expected_size} 人。"
            )
        team = write_team(
            project,
            project_id,
            {"display_name": director_name, "github_username": director_github},
            members,
        )
        markdown = write_team_markdown(project, team)
        delivery = None
        if not args.no_delivery_config:
            delivery = write_delivery_config(project, project_id, team, args.default_branch)
        print(
            json.dumps(
                {
                    "status": "updated",
                    "project_id": project_id,
                    "team_size": team["team_size"],
                    "setup_status": team["setup_status"],
                    "team_yaml": str(team_path.relative_to(project)),
                    "team_markdown": str(markdown.relative_to(project)),
                    "delivery_config": str(delivery.relative_to(project)) if delivery else None,
                    "director": team["director"],
                    "members": team["members"],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    except Exception as exc:
        print(f"Film OS team setup stopped safely: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
