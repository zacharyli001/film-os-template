# 从母版自动建立新项目

`film-os-template` 是永久母版，不承载真实作品。每部独立电影或每个独立剧集建立一个新的私有 GitHub 仓库；一个连载剧集的所有季和所有集保留在同一个仓库中。

## 团队日常只需这样说

```text
$film-project-launcher
新建剧集项目：项目名称
```

或：

```text
$film-project-launcher
新建电影项目：项目名称
```

只有项目名称也可以。Codex 自动生成技术代号和本地文件夹名。剧集的横竖屏、集数、单集时长、连续/单元结构与平台尚未确定时，先保留“待定”，不阻止创意开发。

## Codex 自动完成什么

1. 确认当前仓库是 Film OS 母版。
2. 在母版旁边的 `Film Projects` 文件夹建立独立项目副本。
3. 保留 Film OS、所有 Skills、模板与团队规则。
4. 清除演示场次、演示资产、演示节点和演示 Take。
5. 建立正式 `PROJECT.yaml`、空 Asset Registry、Version Log 和 TapNow Manifest。
6. 如果是剧集，建立 Series Bible、第一季 Season Map、第一集 Episode Card 与连续性台账。
7. 初始化独立 Git 仓库并保存第一个版本。
8. 在用户明确要求团队同步时，建立新的 GitHub Private 仓库并上传。
9. 在用户明确要求时，将新文件夹加入 Codex 并创建标准部门聊天。

## 安全规则

- 绝不在 `film-os-template` 中写真实剧本或资产记录。
- 目标文件夹已存在时立即停止，绝不覆盖。
- 新项目不复制母版的 `.git` 历史。
- 默认 GitHub 仓库为 Private。
- 不把图片和视频上传 GitHub；生产媒体仍放 TapNow。
- GitHub 创建、团队邀请和上传属于外部操作；Codex在执行前必须有用户本次明确指令。

## 推荐项目命名

- GitHub：简短英文或拼音，例如 `series-night-ferry`。
- 本地文件夹：可以直接使用中文项目名，例如 `夜航-FilmOS`。
- Film OS 项目代号：由 Codex 自动生成2—8位大写字母数字组合，建立后保持不变。

## 创建完成后的第一句话

电影：

```text
$film-concept-lab 我目前只有一个想法：……
```

剧集：

```text
$film-os-producer 初始化这个连载剧集，只确认制作规格，不替我设计故事。
```
