#!/usr/bin/env python3
"""Lightweight structural validator for Film OS v1."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "AGENTS.md", "README.md", "FILM_OS_VERSION.yaml",
    "UPGRADE_GUIDE.zh-CN.md", "CHANGELOG.zh-CN.md",
    "MODEL_POLICY.yaml", "MODEL_COMPATIBILITY.zh-CN.md",
    "BLENDER_PREVIZ.zh-CN.md",
    "upgrade/POLICY.json", "upgrade/KNOWN_BASELINES.json",
    "templates/PROJECT.yaml",
    "templates/ASSET_REGISTRY.yaml", "templates/SCENE_CARD.yaml",
    "templates/SHOT_CARD.yaml", "templates/VERSION_LOG.yaml",
    "templates/BLENDER_PREVIZ_CARD.yaml",
    "templates/SERIES_BIBLE.yaml", "templates/SEASON_MAP.yaml",
    "templates/EPISODE_CARD.yaml", "templates/SERIES_CONTINUITY.yaml",
    "SERIES_MODE.zh-CN.md",
    "NEW_PROJECT_WORKFLOW.zh-CN.md", "tools/create_project.py",
    "tools/upgrade_project.py",
    "tools/check_authority_guard.py", "tools/check_local_authority.py",
    "tools/create_member_package.py", "tools/inspect_member_package.py",
    "tools/initialize_authority.py",
    "tools/member_common.py", "tools/member_workspace_start.py",
    "tools/member_workspace_finish.py", "tools/sync_member_repositories.py",
    "tools/test_member_workspace.py", "tools/test_project_id.py",
    "AUTHORITY_GUARD.zh-CN.md",
    ".github/CODEOWNERS", ".github/pull_request_template.md",
    ".github/workflows/film-os-authority-guard.yml",
    "templates/PROPOSAL_BUNDLE.yaml", "templates/MEMBER_PACKAGE.yaml",
    "templates/MEMBER_DELIVERY_REPOSITORIES.yaml",
    "templates/AUTHORITY.yaml",
    "templates/MODEL_CAPABILITY_REPORT.yaml",
    "templates/SUBMISSIONS_README.md",
    ".agents/skills/film-project-launcher/SKILL.md",
    ".agents/skills/film-os-upgrader/SKILL.md",
    ".agents/skills/film-series-architect/SKILL.md",
    ".agents/skills/film-series-continuity/SKILL.md",
    ".agents/skills/film-model-router/SKILL.md",
    ".agents/skills/film-blender-previz/SKILL.md",
    ".agents/skills/film-blender-previz/agents/openai.yaml",
    ".agents/skills/film-master-reference/SKILL.md",
    ".agents/skills/film-master-reference/agents/openai.yaml",
    ".agents/skills/film-master-reference/references/chekhov.md",
    ".agents/skills/film-master-reference/references/ozu.md",
    ".agents/skills/film-master-reference/references/succession.md",
    ".agents/skills/film-master-reference/references/comparison.md",
    "tools/check_model_compatibility.py", "tools/test_model_compatibility.py",
    "tools/check_blender_runtime.py",
    "tapnow/CANVAS_MANIFEST_SPEC.md", "tapnow/NODE_MAP_SPEC.md",
]

# The master validates its separated project scaffold.  A generated
# production repository materializes that scaffold at its normal root paths
# and therefore must not be expected to contain the master-only wrapper.
errors = []
if not (ROOT / "PROJECT.yaml").is_file():
    REQUIRED.extend([
        "project_template/README.md", "project_template/series/README.md",
        "project_template/governance/AUTHORITY.yaml",
        "project_template/governance/MEMBER_DELIVERY_REPOSITORIES.yaml",
        "project_template/submissions/README.md",
    ])
else:
    REQUIRED.extend([
        "governance/AUTHORITY.yaml", "submissions/README.md",
    ])

    authority_path = ROOT / "governance/AUTHORITY.yaml"
    if authority_path.is_file():
        authority_text = authority_path.read_text(encoding="utf-8")
        if not re.search(r"^\s*local_key_sha256:\s*[0-9a-f]{64}\s*$", authority_text, re.MULTILINE):
            errors.append("production authority must contain a director local-key fingerprint")

for rel in REQUIRED:
    if not (ROOT / rel).is_file():
        errors.append(f"missing required file: {rel}")

workflow_path = ROOT / ".github/workflows/film-os-authority-guard.yml"
if workflow_path.is_file():
    workflow_text = workflow_path.read_text(encoding="utf-8")
    if "authority-base/tools/check_authority_guard.py" not in workflow_text:
        errors.append("authority workflow must execute the guard from the trusted main checkout")
    if "--repo candidate" not in workflow_text:
        errors.append("authority workflow must inspect the proposed branch in a separate checkout")

skill_files = (
    list((ROOT / "core").glob("*/SKILL.md"))
    + list((ROOT / "orchestration").glob("*/SKILL.md"))
    + list((ROOT / ".agents/skills").glob("*/SKILL.md"))
)
for skill in skill_files:
    text = skill.read_text(encoding="utf-8")
    if not text.startswith("---\n") or "\nname:" not in text[:500] or "\ndescription:" not in text[:1000]:
        errors.append(f"invalid skill frontmatter: {skill.relative_to(ROOT)}")

master_reference_policy = ROOT / ".agents/skills/film-master-reference/agents/openai.yaml"
if master_reference_policy.is_file():
    policy_text = master_reference_policy.read_text(encoding="utf-8")
    if not re.search(r"^\s*allow_implicit_invocation:\s*true\s*$", policy_text, re.MULTILINE):
        errors.append("film-master-reference must recognize human natural-language triggers")

master_reference_skill = ROOT / ".agents/skills/film-master-reference/SKILL.md"
if master_reference_skill.is_file():
    master_reference_text = master_reference_skill.read_text(encoding="utf-8")
    required_activation_guards = [
        "## Activation gate (mandatory)",
        "do not read any reference file",
        "a later human message in the same conversation",
        "cannot supply the trigger or the confirmation",
    ]
    for guard in required_activation_guards:
        if guard not in master_reference_text:
            errors.append(f"film-master-reference activation guard missing: {guard}")

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
        if path.name == "openai.yaml" and path.parent.name == "agents":
            continue
        if not re.search(r"^schema_version:\s*film-os/[^\s]+\s*$", path.read_text(encoding="utf-8"), re.M):
            errors.append(f"missing schema_version: {path.relative_to(ROOT)}")

if errors:
    print("Film OS validation FAILED")
    print("\n".join(f"- {e}" for e in errors))
    sys.exit(1)
skill_count = len(skill_files)
print(f"Film OS validation passed: {len(yaml_files)} YAML files, {skill_count} skill entrypoints, 3 preserved core sources.")
