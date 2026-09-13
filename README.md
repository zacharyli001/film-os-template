# AIGC FILM OS v1

Film OS is a Codex-operated production repository for standalone films and episodic series. It turns human-approved creative intent into controlled TapNow asset and video work while preserving three specialist engines—LIRA (images), ACTING (performance), and CINEDANCE (video prompt compilation).

## 团队请从这里开始

**这是一个可以从“一句话想法”开始的电影制作工作室，不要求先有剧本。** 在由母版创建的独立作品仓库中，你可以开不同聊天，手动调用不同部门 Skill；所有聊天共享该作品仓库的 `项目工作区` 资料。母版自身不承载真实作品。

```text
$film-concept-lab 我只有一个想法：……，帮我一起发展
```

也可以让制片总控告诉你下一步：

```text
$film-os-producer 检查项目，告诉我现在适合进入哪个部门
```

- 多聊天工作室用法：[`MULTI_CHAT_GUIDE.zh-CN.md`](MULTI_CHAT_GUIDE.zh-CN.md)
- 全部 Skills 清单：[`SKILL_CATALOG.zh-CN.md`](SKILL_CATALOG.zh-CN.md)
- 人本创作原则：[`CREATIVE_CONSTITUTION.zh-CN.md`](CREATIVE_CONSTITUTION.zh-CN.md)
- 团队协作制度：[`TEAM_COLLABORATION.zh-CN.md`](TEAM_COLLABORATION.zh-CN.md)
- 跨电脑协作设置：[`CROSS_COMPUTER_SETUP.zh-CN.md`](CROSS_COMPUTER_SETUP.zh-CN.md)
- 三人独立 Codex 设置：[`THREE_PERSON_CODEX_SETUP.zh-CN.md`](THREE_PERSON_CODEX_SETUP.zh-CN.md)
- 主线只读与导演收束：[`AUTHORITY_GUARD.zh-CN.md`](AUTHORITY_GUARD.zh-CN.md)
- 极简入门：[`START_HERE.md`](START_HERE.md)
- 自动新建项目：[`NEW_PROJECT_WORKFLOW.zh-CN.md`](NEW_PROJECT_WORKFLOW.zh-CN.md)
- 母版维护与安全升级：[`UPGRADE_GUIDE.zh-CN.md`](UPGRADE_GUIDE.zh-CN.md)
- 连载剧集模式：[`SERIES_MODE.zh-CN.md`](SERIES_MODE.zh-CN.md)
- 详细手册（管理员需要时再看）：[`USER_GUIDE.zh-CN.md`](USER_GUIDE.zh-CN.md)

下面内容是系统维护说明，普通团队成员可以不看。

## Administrator/manual fallback

1. In a production repository, copy `templates/PROJECT.yaml`, `ASSET_REGISTRY.yaml`, and `VERSION_LOG.yaml` to the repository root/`registry/` as shown below. In the master, let `$film-project-launcher` materialize `project_template/` instead of manually creating production records.
2. Put the screenplay in `script/` and complete project/bible facts.
3. Ask Codex: `运行 script-doctor，建立 Film OS 项目。` Review and approve G1.
4. Ask: `处理 S001 到资产锁定。` Codex creates scene facts, asset requests, LIRA prompts, and TapNow asset nodes. Approve G2.
5. Ask: `为 S001 设计并锁定镜头。` Codex creates shot cards and spatial records. Approve G3.
6. Ask: `打包并审计 S001_SH010。` Codex builds a sealed Shot Pack, invokes ACTING/CINEDANCE at their boundaries, and requests G4.
7. Generate in TapNow, then say: `登记 S001_SH010 take v01 的结果。` Production Supervisor records QC; approve or request a single-variable retake at G5.

Useful commands are natural language: `处理 S024`, `列出未锁定资产`, `审计 S024_SH030`, or `S024_SH030 v03 人物对了，但空间尺度错了`. Codex must resolve these through `AGENTS.md`, not improvise a parallel workflow.

## Repository map

```text
.agents/skills/        Codex可发现的 Film OS Skill 入口
core/                 immutable source skills + thin Codex wrappers
orchestration/        workflow skills
bible/                canon, visual, character, location, sound standards
templates/            copyable protocol templates
tools/                 local validation
upgrade/              mother-template upgrade policy and tools
project_template/     project-only scaffold; expanded into each new production repo
.github/              optional GitHub Pro defense-in-depth
```

母版与作品项目是两棵树：母版根目录只维护 Film OS 系统；`project_template/` 只保存新作品需要的空白项目骨架。运行 `$film-project-launcher` 时，Codex 会把 `project_template/` 展开到新的独立作品仓库根目录，因此真实项目资料不会留在母版中，也不会被母版升级覆盖。

独立作品仓库展开后，才会出现下面这些项目资料路径：

```text
PROJECT.yaml
registry/             project-wide source-of-truth YAML
series/               series bible, season maps, episode cards
scenes/Sxxx/          scene card, spatial map, shot cards
prompts/shot-packs/   sealed current-shot inputs/compiled prompts
tapnow/               Canvas Manifest and Node Map
takes/                take metadata/QC, not raw media by default
项目工作区/             human-readable shared project memory
governance/           named director and canonical promotion authority
submissions/          append-only member proposals and proposal-derived work
.film-os-local/        unshared local director key; never committed
```

## Install/use in Codex

Open this folder as the project. Codex automatically reads `AGENTS.md`. Each local skill is discoverable by path; tell Codex which production stage to run, or name the relevant skill. The core wrappers require reading their preserved original reference in full.

The steps above describe the underlying protocol for maintenance and recovery. For normal team use, do not copy or edit files manually. From this master template say `$film-project-launcher 新建电影项目：项目名` or `$film-project-launcher 新建剧集项目：项目名`. Codex creates a clean separate production repository. Run `python3 tools/validate_repo.py` only after structural maintenance.

## Team roles

- Director/Writer approves G1 and G3.
- Art/Asset Lead approves G2.
- AI Director or Prompt Lead approves G4.
- Director/Editor approves G5.
- Production Supervisor owns registries, versions, and rejects untraceable work.

One person may hold several roles, but every approval still needs a named human and timestamp.

## Mother template upgrades

Develop reusable Film OS features only in this master repository. Production-specific rules stay in that production repository's `project_extensions/`. Use `$film-os-upgrader` from the master to inspect an upgrade; it may apply changes only after a human approves the exact impact list. Project scripts, canon, registries, scenes, approvals, TapNow records, and media are protected.
