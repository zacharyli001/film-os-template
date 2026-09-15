# 成员提案区

这里是团队成员唯一可以向正式仓库新增内容的区域。成员不能修改、删除或重命名任何已有文件。

免费 GitHub 模式下，成员不拥有导演正式仓库写权限。成员可以使用两种交付方式：

1. **成员交付仓库模式（推荐）**：成员仓库的 `main` 只做正式基线镜像；每次提案使用独立分支，例如 `proposal/<GitHub用户名>/<UTC时间>`。导演端只读同步提案分支，不自动合并、不自动采用。
2. **完整成员包模式**：由 Codex 导出包含 `00_正式基线只读/` 和 `01_个人增量/` 的完整包；适用于成员没有独立交付仓库或需要离线交付时。

成员仓库的 `main` 不是第二个正式主线。无论采用哪种方式，成员内容都默认是 `non_canonical_proposal`。

## 一个想法对应一个提案包

```text
submissions/
└── GitHub用户名/
    └── 20260913T120000Z_简短英文名/
        ├── PROPOSAL.yaml
        ├── 01_剧本增量提案.md
        ├── storyboard/
        ├── assets/
        ├── prompts/
        └── notes/
```

目录名中的时间使用 UTC，格式为 `YYYYMMDDTHHMMSSZ`。`PROPOSAL.yaml` 会记录作者、创建时间、基于哪个 main 版本，以及该提案产生了哪些衍生成果。

如果成员因为一个剧本新想法继续制作分镜、资产或 Prompt，这些成果必须继续放在同一个提案包内。它们只对这条提案子线有效，不能写进正式 `scenes/`、`registry/`、`项目工作区/` 或其他主线目录。

导演审核后有三种处理：

- 不采用：提案保留为历史，不进入主线。
- 继续探索：所有新成果仍留在原提案包。
- 采用：由导演在正式目录创建新的主线版本，并记录批准；不是把成员文件自动变成真理。

只有通过本地导演钥匙验证的正式工作区可以执行采用或替代。成员包、成员 GitHub 仓库和成员 Codex 中的内容永远默认是 `non_canonical_proposal`。

## 交付仓库模式的最短流程

```text
成员首次开工：
python3 tools/member_workspace_start.py --member-id <GitHub用户名> --canonical-url <正式仓库地址> --adopt-main

成员收工：
python3 tools/member_workspace_finish.py --member-id <GitHub用户名>

导演审核：
python3 tools/sync_member_repositories.py --project <正式项目目录>
```

首次使用 `--adopt-main` 前，成员仓库必须还没有导入正式基线；流程会先归档旧 `main`，再把它设为正式基线镜像。收工默认只提交本地提案分支，由 GitHub Desktop 执行最终 Push origin；只有显式使用 `--push` 才允许脚本直接推送。

如果成员 `main` 已经存在正式资料，但被工具判定为旧式同步提交、落后镜像或没有共同祖先，运行：

```bash
python3 tools/member_workspace_start.py --member-id <GitHub用户名> --realign-main --push-main
```

流程会先备份旧 `main`，再建立同时连接旧历史和正式基线的只读镜像；不会删除历史或提案分支。
