#!/usr/bin/env python3
"""Real and fallback YAML checks used by the Film OS repository validator."""

from __future__ import annotations

from pathlib import Path
import re
import shutil
import subprocess

try:
    import yaml as _pyyaml
except ImportError:
    _pyyaml = None


def minimal_yaml_error(text: str) -> str | None:
    """Catch the common structural error of an indented bare text line."""
    block_indent: int | None = None
    for line_number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        if block_indent is not None:
            if indent > block_indent:
                continue
            block_indent = None
        if re.match(r"^[^:#][^:]*:\s*[|>][-+]?\s*$", stripped):
            block_indent = indent
            continue
        allowed_prefixes = ("-", "?", ":", "---", "...", "[", "{", '"', "'")
        if ":" not in stripped and not stripped.startswith(allowed_prefixes):
            return (
                "possible YAML structure error: bare text line without ':' "
                f"at line {line_number} column {indent + 1}"
            )
    return None


def _ruby_parse_error(path: Path) -> str | None:
    ruby = shutil.which("ruby")
    if not ruby:
        return None
    result = subprocess.run(
        [ruby, "-ryaml", "-e", "YAML.load_file(ARGV[0])", str(path)],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode == 0:
        return None
    message = (result.stderr or result.stdout).strip().splitlines()
    return message[0] if message else "YAML parser returned an unknown error"


def parse_yaml_file(path: Path) -> str | None:
    text = path.read_text(encoding="utf-8")
    if _pyyaml is not None:
        try:
            _pyyaml.safe_load(text)
        except Exception as exc:  # noqa: BLE001 - parser errors are reported to the user
            return str(exc).splitlines()[0]
        return None
    ruby_error = _ruby_parse_error(path)
    if ruby_error is not None:
        return ruby_error
    if shutil.which("ruby"):
        return None
    return minimal_yaml_error(text)


def yaml_parser_name() -> str:
    if _pyyaml is not None:
        return "PyYAML"
    if shutil.which("ruby"):
        return "Ruby YAML"
    return "minimal"


def parse_all_yaml(root: Path, paths: list[Path]) -> tuple[list[str], str]:
    errors: list[str] = []
    parser = yaml_parser_name()
    for path in paths:
        error = parse_yaml_file(path)
        if error:
            errors.append(f"YAML parse error {path.relative_to(root)}: {error}")
    return errors, parser


def demo_project_id_files(root: Path, paths: list[Path]) -> list[str]:
    pattern = re.compile(r"(?m)^\s*project_id:\s*DEMO\s*$")
    return [
        path.relative_to(root).as_posix()
        for path in paths
        if pattern.search(path.read_text(encoding="utf-8"))
    ]
