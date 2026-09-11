# AIGC FILM OS v1

Film OS is a Codex-operated production repository for standalone films and episodic series. It turns human-approved creative intent into controlled TapNow asset and video work while preserving three specialist engines—LIRA (images), ACTING (performance), and CINEDANCE (video prompt compilation).

## 团队请从这里开始

**这是一个可以从“一句话想法”开始的电影制作工作室，不要求先有剧本。** 你可以在同一个 Codex 项目里开不同聊天，手动调用不同部门 Skill。所有聊天共享 `项目工作区` 里的项目资料。

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
- 极简入门：[`START_HERE.md`](START_HERE.md)
- 连载剧集模式：[`SERIES_MODE.zh-CN.md`](SERIES_MODE.zh-CN.md)
- 详细手册（管理员需要时再看）：[`USER_GUIDE.zh-CN.md`](USER_GUIDE.zh-CN.md)

下面内容是系统维护说明，普通团队成员可以不看。

## Start here

1. Copy `templates/PROJECT.yaml`, `ASSET_REGISTRY.yaml`, and `VERSION_LOG.yaml` to the repository root/`registry/` as shown below.
2. Put the screenplay in `script/` and complete project/bible facts.
3. Ask Codex: `运行 script-doctor，建立 Film OS 项目。` Review and approve G1.
4. Ask: `处理 S001 到资产锁定。` Codex creates scene facts, asset requests, LIRA prompts, and TapNow asset nodes. Approve G2.
5. Ask: `为 S001 设计并锁定镜头。` Codex creates shot cards and spatial records. Approve G3.
6. Ask: `打包并审计 S001_SH010。` Codex builds a sealed Shot Pack, invokes ACTING/CINEDANCE at their boundaries, and requests G4.
7. Generate in TapNow, then say: `登记 S001_SH010 take v01 的结果。` Production Supervisor records QC; approve or request a single-variable retake at G5.

Useful commands are natural language: `处理 S024`, `列出未锁定资产`, `审计 S024_SH030`, or `S024_SH030 v03 人物对了，但空间尺度错了`. Codex must resolve these through `AGENTS.md`, not improvise a parallel workflow.

## Repository map

```text
core/                 immutable source skills + thin Codex wrappers
orchestration/        workflow skills
bible/                canon, visual, character, location, sound standards
registry/             project-wide source-of-truth YAML
series/               series bible, season maps, episode cards
scenes/Sxxx/          scene card, spatial map, shot cards
prompts/shot-packs/   sealed current-shot inputs/compiled prompts
tapnow/               Canvas Manifest and Node Map
takes/                take metadata/QC, not raw media by default
templates/            copyable protocol templates
tools/                 local validation
```

## Install/use in Codex

Open this folder as the project. Codex automatically reads `AGENTS.md`. Each local skill is discoverable by path; tell Codex which production stage to run, or name the relevant skill. The core wrappers require reading their preserved original reference in full.

To start a real production, copy the template files, replace `DEMO`/example IDs, and keep the templates unchanged for future projects. Run `python3 tools/validate_repo.py` after structural changes.

## Team roles

- Director/Writer approves G1 and G3.
- Art/Asset Lead approves G2.
- AI Director or Prompt Lead approves G4.
- Director/Editor approves G5.
- Production Supervisor owns registries, versions, and rejects untraceable work.

One person may hold several roles, but every approval still needs a named human and timestamp.
