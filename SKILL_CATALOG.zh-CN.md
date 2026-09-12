# Film OS Skills 部门清单

在同一个 Codex 项目中开新聊天，把 `$skill-name` 放在第一句话即可手动调用。每个聊天都读取同一份 `项目工作区/00_项目总览.md`，所以成果可以接力，但各部门不会依赖其他聊天的记忆。

所有创意部门都遵守同一原则：人的意图是源头，AI 输出默认只是提案，只有人明确确认后才进入正式项目。你可以在指令中加上 `镜像模式`、`扩展模式`、`挑战模式` 或 `执行模式`。

## 总控

| 手动调用 | 部门 | 适合什么时候 |
|---|---|---|
| `$film-project-launcher` | 项目启动器 | 从母版自动建立独立电影/剧集文件夹、Git 仓库和项目记录 |
| `$film-os-producer` | 制片总控 | 不知道下一步、检查全项目、准备跨部门交接 |
| `$film-production-supervisor` | 生产监督 | 版本、审核、Prompt Audit、Take QC、返工 |

## 从想法到剧本

| 手动调用 | 部门 | 产出 |
|---|---|---|
| `$film-concept-lab` | 创意开发室 | 把一句想法发展成创意简报 |
| `$film-series-architect` | 剧集架构室 | 连载剧集圣经、持续故事引擎、季弧线和分集表 |
| `$film-series-continuity` | 连续性编辑室 | 跨集正史、人物知识/状态、关系、资产状态和伏笔回收 |
| `$film-story-architect` | 故事架构室 | 世界、人物、故事梗概、结构、分场大纲 |
| `$film-screenplay-writer` | 剧本室 | Treatment、场景、对白、剧本版本 |
| `$film-script-doctor` | 剧本医生 | 诊断和优化已有剧本 |
| `$film-scene-engine` | 场次拆解室 | 场次事实、转折、连续性、资产需求 |

## 从剧本到资产

| 手动调用 | 部门 | 产出 |
|---|---|---|
| `$film-asset-architect` | 资产规划室 | 决定需要哪些人物、状态、服装、地点和道具 |
| `$film-lira` | 图像 Prompt 室 | 使用原始 LIRA 生成或修复资产 Prompt |

## 从场次到镜头

| 手动调用 | 部门 | 产出 |
|---|---|---|
| `$film-storyboard-director` | 分镜导演室 | Shotlist、Coverage、构图、剪辑关系 |
| `$film-spatial-system` | 空间设计室 | Location Map、轴线、视线、Blocking、First Frame |
| `$film-acting` | 表演导演室 | 使用原始 ACTING 设计人物行为和表演节拍 |

## 从镜头到生成

| 手动调用 | 部门 | 产出 |
|---|---|---|
| `$film-cinedance` | 视频 Prompt 室 | 使用原始 CINEDANCE 编译单个镜头 Prompt |
| `$film-tapnow-bridge` | TapNow 执行室 | 把资产/镜头 Prompt 整理成 TapNow 任务单 |

## 后期

| 手动调用 | 部门 | 产出 |
|---|---|---|
| `$film-sound-director` | 声音设计室 | 声音圣经、对白/环境/效果/音乐和静默设计 |
| `$film-edit-director` | 剪辑导演室 | Approved Takes 的剪辑结构、节奏和装配说明 |

## 重要说明

- 不必每次按固定顺序调用，也不必使用全部 Skills。
- 创作探索可以来回反复；一旦改变已确认内容，Codex 会提示受影响的下游成果。
- 想手动控制就直接点名 Skill；不确定时才找 `$film-os-producer`。
- LIRA、ACTING、CINEDANCE 保留上传原始规则，外围 Skills 不重写它们。
- 连载项目先建立剧集圣经和季结构；之后每一集重复使用原有剧本、资产、分镜、表演、视频和审核部门。
