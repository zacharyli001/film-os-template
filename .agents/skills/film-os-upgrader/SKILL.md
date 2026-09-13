---
name: film-os-upgrader
description: Safely inspect and upgrade a standalone Film OS production project from the master template while preserving all creative and production data. Use for Film OS version checks, mother-template synchronization, and production-project upgrades; do not use for ordinary project content changes.
---

# Film OS Upgrader

Use only from the `film-os-template` master repository, identified by the absence of root `PROJECT.yaml`. Read `../../../UPGRADE_GUIDE.zh-CN.md` before acting. A target must be a separate production repository with root `PROJECT.yaml`; never upgrade the master from a production project.

Treat “检查升级”, “能否升级”, and “同步母版功能” as permission for a read-only plan only. Run `python3 tools/upgrade_project.py plan --target "<exact project path>"`. For projects created before installation records existed, read `../../../upgrade/KNOWN_BASELINES.json` and pass the appropriate `--baseline-ref` and `--baseline-version`. If the baseline is ambiguous, stop and ask for the exact project origin rather than guessing.

Present one short Chinese approval sheet containing: current/target version, files to add, files to update, local customizations preserved, conflicts, protected production areas, and whether both the released mother template and project are clean enough to upgrade. Do not expose checksums unless requested. Never apply from an uncommitted mother-template working tree.

Apply only after a named human with project authority explicitly approves that exact plan in the same conversation. Re-run the plan immediately before applying; if the plan or Git state changed, invalidate the approval and present the new plan. Apply with `python3 tools/upgrade_project.py apply ... --actor "<approver>"` using the same baseline arguments.

Never force overwrite a conflict, delete a target file, edit a protected production record except the append-only system upgrade log entry, or treat a successful check as approval. A dirty target repository blocks application. Resolve any system-file conflict individually and obtain a new approval.

After applying, run the target's `tools/validate_repo.py`, confirm `.film-os/INSTALLATION.json` records the new version, and show the resulting Git changes. Do not commit or push unless the user separately requests it. The final response must state that scripts, canon, assets, shots, approvals, and TapNow records were preserved.
