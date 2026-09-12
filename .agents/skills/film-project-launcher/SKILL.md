---
name: film-project-launcher
description: Create a clean standalone Film OS film or series project from the master template, initialize records and Git, and prepare optional private GitHub team setup.
---

# Film Project Launcher

Use only from the master template when the user asks to start a new independent film or series. Read `../../../NEW_PROJECT_WORKFLOW.zh-CN.md` and confirm that root `PROJECT.yaml` is absent. If it exists, this is already a production project: do not create a nested project.

The minimum inputs are project title and production type (`film` or `series`). Infer the type from “电影” or “剧集”; ask one concise question only if type is genuinely unclear. Project code, folder name, and unset production specifications are technical details Codex may generate or leave `null`. Never invent premise, characters, episode count, runtime, platform, visual language, or other creative facts.

Run `python3 tools/create_project.py --title "<项目名>" --type <film|series>` from the template root. Optional confirmed fields may use `--project-id`, `--episode-count`, `--episode-runtime`, and `--orientation`. Do not hand-copy the repository when the initializer is available. The initializer must refuse an existing target and must never modify the template.

After creation, run the new project's `tools/validate_repo.py`, verify `PROJECT.yaml` and that demo scenes/assets/nodes are absent, then report the new folder and generated project ID in plain Chinese. If Git initialization could not commit, complete the initial commit without changing project content.

Create or push a GitHub repository only when the current user request explicitly includes GitHub/team synchronization or confirms that final external step. Default to a private repository, verify the exact remote name does not already exist, never overwrite an existing remote, then connect `origin` and push `main`. Images and videos remain in TapNow, not GitHub.

Add the new folder to Codex or create department tasks only when the user asks. Suggested first task is Film OS Producer initialization; series projects then route through Concept Lab and Series Architect. External repository creation, collaborator invitations, and task creation remain separate authorized actions.
