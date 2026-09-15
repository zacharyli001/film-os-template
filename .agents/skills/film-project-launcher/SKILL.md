---
name: film-project-launcher
description: Create a clean standalone Film OS film or series project from the master template, initialize records and Git, and prepare optional private GitHub team setup.
---

# Film Project Launcher

Use only from the master template when the user asks to start a new independent film or series. Read `../../../NEW_PROJECT_WORKFLOW.zh-CN.md` and confirm that root `PROJECT.yaml` is absent. If it exists, this is already a production project: do not create a nested project.

The minimum inputs are project title and production type (`film` or `series`). Infer the type from “电影” or “剧集”; ask one concise question only if type is genuinely unclear. Use the repository owner's confirmed GitHub username as the exclusive director authority; never guess a different owner. Project code, folder name, and unset production specifications are technical details Codex may generate or leave `null`. Never invent premise, characters, episode count, runtime, platform, visual language, or other creative facts.

Before creating the project, ask the director this team-onboarding set once:

1. 导演怎么称呼？
2. 团队一共有多少人，包括导演？
3. 除导演外，每位主创怎么称呼、GitHub 用户名、主要负责什么、是否已有交付仓库？

If any answer is not yet known, use `待补充` and record it for later `$film-team-setup`; do not invent a person. Then run:

```bash
python3 tools/create_project.py \
  --title "<项目名>" \
  --type <film|series> \
  --director-github "<导演账号>" \
  --director-name "<导演称呼>" \
  --expected-size <团队总人数> \
  --member "<主创称呼>|<GitHub用户名>|<负责内容>|<交付仓库地址或空>"
```

Repeat `--member` for each主创. Optional confirmed fields may use `--project-id`, `--episode-count`, `--episode-runtime`, and `--orientation`. Do not hand-copy the repository when the initializer is available. The initializer must refuse an existing target and must never modify the template.

After creation, run the new project's `tools/validate_repo.py`, verify `PROJECT.yaml`, `governance/TEAM.yaml`, `项目工作区/00_团队与权限.md`, and that demo scenes/assets/nodes are absent, then report the new folder, generated project ID, team size, and any “待补充” fields in plain Chinese. If Git initialization could not commit, complete the initial commit without changing project content.

Create or push a GitHub repository only when the current user request explicitly includes GitHub/team synchronization or confirms that final external step. Default to a private canonical repository, verify the exact remote name does not already exist, never overwrite an existing remote, then connect `origin` and push `main`. In free-GitHub package mode, do not invite members with write access to the canonical repository. Publish a project snapshot for member use; contributors upload self-contained packages to their own delivery repositories. GitHub branch protection remains optional defense-in-depth. Images and videos remain in TapNow, not GitHub.

Add the new folder to Codex or create department tasks only when the user asks. Suggested first task is Film OS Producer initialization; series projects then route through Concept Lab and Series Architect. External repository creation, collaborator invitations, and task creation remain separate authorized actions.
