---
name: film-director-lab
description: Manage the director's private exploration repository, optionally share selected explorations for team discussion, collect member feedback as proposals, and promote only explicitly approved parts into canon. Use when the director wants to brainstorm, compare directions, park ideas, or decide what to share with the team.
---

# Film Director Lab

导演探索区不是正式主线。它保护导演的发散思考，避免它们因为一次聊天就自动变成正史。

## 开始前

读取：

- `AGENTS.md`
- `项目工作区/00_项目总览.md`
- `项目工作区/00_创意北极星.md`
- `项目工作区/00_创意决策记录.md`
- `governance/TEAM.yaml`（若存在）

确认当前是导演工作区：`python3 tools/check_local_authority.py`。

## 默认边界

- 探索区是导演私密仓库，默认不分享给成员。
- 不把私密探索镜像、复制或打包进成员仓库和成员包。
- 探索内容默认不是正史，不解锁任何 Gate。
- 只有导演明确说“分享给团队讨论”时才生成讨论版。
- 只有导演明确说“纳入正式”时才可能进入主线。
- 成员反馈是提案，不是采纳。
- 引用成员提案、成员原话或 AI 推演时，必须写明来源；标注来源不等于采纳。

## 探索素材的来源

- 探索可以引用成员提案、成员原话或 AI 推演；每一条都要写明来源：谁先说的（zac／Yoe／Sarah／AI），一行即可。
- 标明来源不构成采纳：不改变成员提案的审核状态（例如“已阅，继续探索”保持不变），也不使任何内容进入主线。
- 成员内容要进主线，只能走“纳入正式”：由导演明确指定，只写入批准的部分、建立新版本、更新版本记录。
- 探索区保持私密，不向成员镜像；生成团队讨论版时同样保留来源标注。

## 常用命令

```bash
python3 tools/director_lab.py init --project .
python3 tools/director_lab.py new --project . --title "探索标题"
python3 tools/director_lab.py list --project .
```

分享给团队讨论：

```bash
python3 tools/director_lab.py share --project . --id EX-001 --commit-main --push-main
```

暂停或放弃：

```bash
python3 tools/director_lab.py park --project . --id EX-001 --note "暂时搁置的原因"
```

记录纳入正式：

```bash
python3 tools/director_lab.py mark-promoted --project . --id EX-001 \
  --note "纳入原因" --canonical-summary "实际纳入的内容" --commit-main --push-main
```

## 分享给团队时

生成的是团队讨论版，放在：

```text
02_团队审核/探索讨论/EX-XXX_讨论版/
```

讨论版必须标注：

- 探索版，不是正式设定
- 未进入主线
- 不解锁任何 Gate

成员通过自己的提案分支反馈，不直接编辑讨论版。

## 纳入正式时

`mark-promoted` 只是记录决定，不等于内容已经自动进入主线。正确顺序：

1. 导演明确说“纳入正式”。
2. Codex 只选择批准的部分，按 Film OS 规则写入正式目录并创建新版本。
3. 更新 `VERSION_LOG.yaml` 和受影响记录。
4. 运行 `mark-promoted` 记录探索 ID、纳入摘要和留下的内容。
5. 私密探索原始记录保留，不删除。

## 导演普通聊天中的探索

如果导演只是在聊天里说“我有个想法”“也许可以这样”，默认按探索处理。不要直接写成正式设定；可以先总结，并询问是否：

- 放进导演探索区
- 分享给团队讨论
- 纳入正式
