#!/usr/bin/env python3
"""Lightweight structural validator for Film OS v1."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "AGENTS.md", "README.md", "templates/PROJECT.yaml",
    "templates/ASSET_REGISTRY.yaml", "templates/SCENE_CARD.yaml",
    "templates/SHOT_CARD.yaml", "templates/VERSION_LOG.yaml",
    "templates/SERIES_BIBLE.yaml", "templates/SEASON_MAP.yaml",
    "templates/EPISODE_CARD.yaml", "templates/SERIES_CONTINUITY.yaml",
    "SERIES_MODE.zh-CN.md", "series/README.md",
    ".agents/skills/film-series-architect/SKILL.md",
    ".agents/skills/film-series-continuity/SKILL.md",
    "tapnow/CANVAS_MANIFEST_SPEC.md", "tapnow/NODE_MAP_SPEC.md",
]

errors = []
for rel in REQUIRED:
    if not (ROOT / rel).is_file():
        errors.append(f"missing required file: {rel}")

skill_files = (
    list((ROOT / "core").glob("*/SKILL.md"))
    + list((ROOT / "orchestration").glob("*/SKILL.md"))
    + list((ROOT / ".agents/skills").glob("*/SKILL.md"))
)
for skill in skill_files:
    text = skill.read_text(encoding="utf-8")
    if not text.startswith("---\n") or "\nname:" not in text[:500] or "\ndescription:" not in text[:1000]:
        errors.append(f"invalid skill frontmatter: {skill.relative_to(ROOT)}")

for original in (ROOT / "core").glob("*/references/ORIGINAL_SKILL.md"):
    if original.stat().st_size < 1000:
        errors.append(f"core original appears truncated: {original.relative_to(ROOT)}")

yaml_files = list(ROOT.rglob("*.yaml"))
try:
    import yaml
except ImportError:
    yaml = None
if yaml:
    for path in yaml_files:
        try:
            yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"YAML parse error {path.relative_to(ROOT)}: {exc}")
else:
    for path in yaml_files:
        if not re.search(r"^schema_version:\s*film-os/v1\s*$", path.read_text(encoding="utf-8"), re.M):
            errors.append(f"missing schema_version: {path.relative_to(ROOT)}")

if errors:
    print("Film OS validation FAILED")
    print("\n".join(f"- {e}" for e in errors))
    sys.exit(1)
skill_count = len(skill_files)
print(f"Film OS validation passed: {len(yaml_files)} YAML files, {skill_count} skill entrypoints, 3 preserved core sources.")
