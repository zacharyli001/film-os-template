#!/usr/bin/env python3
"""Read-only local preflight for Film OS Blender previsualization."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import platform
import re
import shutil


def executable_candidate(name: str) -> str | None:
    """Find a CLI on PATH or in the standard per-user install directory."""
    resolved = shutil.which(name)
    if resolved:
        return resolved
    user_local = Path.home() / ".local" / "bin" / name
    return str(user_local) if user_local.is_file() else None


def blender_candidates() -> list[Path]:
    candidates: list[Path] = []
    executable = shutil.which("blender")
    if executable:
        candidates.append(Path(executable))
    if platform.system() == "Darwin":
        candidates.extend(
            [
                Path("/Applications/Blender.app/Contents/MacOS/Blender"),
                Path.home() / "Applications/Blender.app/Contents/MacOS/Blender",
            ]
        )
    unique: list[Path] = []
    for path in candidates:
        if path not in unique:
            unique.append(path)
    return unique


def adapter_version_files() -> list[Path]:
    if platform.system() != "Darwin":
        return []
    roots = [
        Path("/Applications/Blender.app/Contents/Resources"),
        Path.home() / "Applications/Blender.app/Contents/Resources",
    ]
    matches: list[Path] = []
    for root in roots:
        if root.is_dir():
            matches.extend(root.glob("*/python/lib/python*/site-packages/dcc_mcp_blender/__version__.py"))
    return matches


def read_adapter_version() -> str | None:
    for version_file in adapter_version_files():
        match = re.search(r'^__version__\s*=\s*["\']([^"\']+)["\']', version_file.read_text(), re.MULTILINE)
        if match:
            return match.group(1)
    return None


def startup_compatibility_fix_installed() -> bool:
    if platform.system() != "Darwin":
        return False
    startup_root = Path.home() / "Library/Application Support/Blender"
    for hook in startup_root.glob("*/scripts/startup/dcc_mcp_blender_startup.py"):
        source = hook.read_text()
        if "BlenderUiDispatcher" in source and "_dispatcher.start()" in source:
            return True
    return False


def inspect() -> dict[str, object]:
    installed = [str(path) for path in blender_candidates() if path.is_file()]
    dcc_cli = executable_candidate("dcc-mcp-cli")
    compatible_cli = executable_candidate("blender-mcp")
    adapter_version = read_adapter_version()
    compatibility_fix = startup_compatibility_fix_installed()
    return {
        "platform": platform.platform(),
        "blender_installed": bool(installed),
        "blender_paths": installed,
        "dcc_mcp_cli_installed": bool(dcc_cli),
        "dcc_mcp_cli_path": dcc_cli,
        "dcc_mcp_blender_adapter_version": adapter_version,
        "dcc_mcp_blender_024_compatibility_fix_installed": compatibility_fix,
        "compatible_blender_mcp_cli_installed": bool(compatible_cli),
        "compatible_blender_mcp_cli_path": compatible_cli,
        "live_blender_control_verified": False,
        "viewport_capture_verified": False,
        "note": "This read-only check does not launch Blender or claim a live MCP connection.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check local Blender previz prerequisites without changing the machine.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    args = parser.parse_args()
    result = inspect()
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("Film OS Blender 预演只读检查")
        print(f"- Blender 已安装：{'是' if result['blender_installed'] else '否'}")
        print(f"- DCC-MCP CLI 已安装：{'是' if result['dcc_mcp_cli_installed'] else '否'}")
        print(f"- Blender Adapter 版本：{result['dcc_mcp_blender_adapter_version'] or '未检测到'}")
        if result["dcc_mcp_blender_adapter_version"] == "0.2.4":
            print(
                "- 0.2.4 主线程兼容修复："
                f"{'已安装' if result['dcc_mcp_blender_024_compatibility_fix_installed'] else '未安装'}"
            )
        print(
            "- 兼容 Blender MCP CLI 已安装："
            f"{'是' if result['compatible_blender_mcp_cli_installed'] else '否'}"
        )
        print("- 实际控制与截图：尚未验证（需要打开 Blender 后另做连接测试）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
