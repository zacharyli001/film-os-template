# AIGC FILM OS v1 完整使用教程

这份手册面向导演、编剧、资产负责人、Prompt 工程师、TapNow 操作员和制片监督。团队不需要理解代码，但必须遵守审批、命名、版本和单变量返工规则。

连载剧集请先阅读 `SERIES_MODE.zh-CN.md`。剧集模式在本系统上增加 Series Bible、Season Map、Episode Card 和连续性台账；每一集仍然复用同一套剧本、资产、分镜、表演、视频、TapNow和五个 Gate。

> 这是管理员进阶手册。普通团队成员只需阅读 `START_HERE.md` 和 `TEAM_QUICK_CARD.md`，不需要阅读本文件，也不需要接触 YAML。

---

## 1. Film OS 到底是什么

Film OS 不是一组散装提示词，而是一个以 Codex 为总控、以 TapNow 为执行画布的电影生产系统。

```text
剧本
  ↓
剧本诊断与锁定
  ↓
场次事实拆解
  ↓
资产清单 → LIRA → TapNow 图像生成 → 资产锁定
  ↓
镜头设计 + 空间系统 + ACTING 表演设计
  ↓
复杂镜头可选：Blender 白模预演
  ↓
Shot Packager 隔离当前镜头上下文
  ↓
CINEDANCE 编译视频 Prompt
  ↓
Prompt Audit → TapNow 视频生成
  ↓
镜头 QC → 单变量返工 → Approved Take
```

职责分工：

- Codex：读取项目资料，维护 YAML，调用正确 Skill，检查依赖，生成与审计 Prompt，记录版本和审批。
- TapNow：保存参考图、连接节点、运行图像和视频生成、导出结果。
- 人：做创作决策、审批 Gate、判断素材是否真正可用。

三个核心引擎互不替代：

- LIRA：图像资产 Prompt、图像编辑 Prompt、图像模型路由。
- ACTING：人物目标、障碍、策略、节拍、潜台词、身体与眼神行为、表演 QC。
- CINEDANCE：把当前镜头的完整事实编译成视频生成 Prompt。

外围 Skills 只负责组织生产，不重写三个核心引擎的专业规则。

---

## 2. 第一次使用前的准备

### 2.1 建立新项目副本

普通团队成员不要手动复制文件。在 `film-os-template` 母版聊天中直接说：

```text
$film-project-launcher 新建剧集项目：项目名称
```

电影项目把“剧集”改成“电影”。Codex会自动建立独立文件夹、项目记录和 Git 版本；需要三人同步时，在同一句话加上“建立私有 GitHub 仓库并同步”。不要直接在母版仓库里做真实项目。每部独立电影或独立剧集使用一个仓库，同一剧集的所有季和所有集共用这个仓库。

### 2.2 创建项目工作文件

项目启动器会自动完成本节，不需要团队手动操作。以下仅供系统管理员排查时参考：

```text
templates/PROJECT.yaml
→ PROJECT.yaml

templates/ASSET_REGISTRY.yaml
→ registry/ASSET_REGISTRY.yaml

templates/VERSION_LOG.yaml
→ registry/VERSION_LOG.yaml
```

场次开始制作时再复制：

```text
templates/SCENE_CARD.yaml
→ scenes/S001/SCENE_CARD.yaml

templates/SHOT_CARD.yaml
→ scenes/S001/shots/S001_SH010.yaml
```

### 2.3 放入基础资料

建议准备：

```text
script/screenplay_v01.md
bible/VISUAL_BIBLE.md
bible/CHARACTER_BIBLE.md
bible/LOCATION_BIBLE.md
bible/SOUND_BIBLE.md
```

剧本可以先用 Markdown 或纯文本。团队已有的视觉参考、角色设定和场景设定可以先写入对应 Bible；未确定的地方明确写 `T`，不要让 Codex暗自补成事实。

### 2.4 填写 PROJECT.yaml

至少填写：

- 项目 ID 与名称
- 类型与目标时长
- 画幅
- 语言
- 剧本路径和版本
- 项目负责人
- 项目当前状态

项目 ID 使用简短英文大写代号，例如 `NFY`。一旦开始生产，不再修改 ID。

### 2.5 在 Codex 中打开项目

将新项目文件夹作为 Codex 项目打开。Codex 会读取根目录的 `AGENTS.md`，从而获得完整路由、状态机、审批和审计规则。

第一次可以直接说：

```text
初始化这个 Film OS 项目。检查 PROJECT、剧本和所有 Bible，列出缺失信息，但暂时不要生成任何正式资产或视频 Prompt。
```

---

## 3. 文件的权威关系

发生冲突时，按以下优先级判断：

1. 人工审批记录与 Approved Take
2. 当前 Scene Card / Shot Card
3. Asset Registry
4. PROJECT 与 Bible
5. 原始剧本
6. 已生成 Prompt、旧输出、聊天记录

这意味着旧 Prompt 不能覆盖已经锁定的 Registry，也不能因为 TapNow 某个节点成功运行就自动认定资产通过。

### 3.1 各文件负责什么

| 文件 | 作用 | 不负责 |
|---|---|---|
| `PROJECT.yaml` | 项目级设置、路径、五个 Gate | 具体镜头细节 |
| `SERIES_BIBLE.yaml` | 剧集承诺、持续故事引擎、世界正史、长期人物弧线 | 单集完整剧本 |
| `SEASON_MAP.yaml` | 季弧线、分集功能、伏笔与回收窗口 | 镜头执行 |
| `EPISODE_CARD.yaml` | 单集承诺、钩子、故事线、状态变化和五个分集 Gate | 全剧永久正史 |
| `SERIES_CONTINUITY.yaml` | 已批准成片形成的跨集正史、人物知识与资产状态 | 未批准计划 |
| `ASSET_REGISTRY.yaml` | 资产身份、状态、版本、描述、审批 | 镜头调度 |
| `SCENE_CARD.yaml` | 场次事实、转折、连续性、所需资产 | 表演解释和摄影设计 |
| `SHOT_CARD.yaml` | 镜头功能、构图、空间、时间、锁定项 | 全项目上下文 |
| `SHOT_PACK.yaml` | 当前镜头唯一允许送入 CINEDANCE 的上下文 | 项目数据库 |
| `VERSION_LOG.yaml` | 所有晋级、修改、审批和返工记录 | 创作内容本身 |
| `CANVAS_MANIFEST.yaml` | Film OS 与 TapNow 画布的对应关系 | 人工审批 |
| `NODE_MAP.yaml` | TapNow 节点依赖和输入输出追踪 | 替代 Asset Registry |

---

## 4. 完整生产流程

## 阶段 A：剧本诊断与 G1 剧本锁定

### A1. 运行 Script Doctor

对 Codex 说：

```text
使用 film-os-script-doctor 检查 script/screenplay_v01.md。分析结构、因果、人物弧线、信息释放、场次功能和 AI 制作风险。先给修改建议，不要直接改剧本。
```

你会得到：

- 整体诊断
- 场次索引
- 结构问题与修改建议
- 连续性风险
- 资产或生成难点
- 需要导演回答的问题

### A2. 修改并确认剧本

导演/编剧确认建议后，再要求：

```text
接受第 1、3、4 项修改，拒绝第 2 项。生成 screenplay_v02.md，保留 v01，并更新 Version Log。
```

不要覆盖旧剧本。每次正式版本都使用 `v01`、`v02`。

### A3. 审批 G1

确认故事、场次边界和 Canon 后说：

```text
我以导演身份批准 screenplay_v02，审批 G1_SCRIPT_LOCK。审批人：张三。记录当前 UTC 时间，并更新项目状态。
```

G1 没通过之前：

- 可以讨论、测试和修改剧本。
- 不能生产正式资产。
- 不能建立正式视频 Prompt。

---

## 阶段 B：场次拆解

### B1. 建立 Scene Card

对单场戏说：

```text
处理 S001。使用 scene-engine 根据已锁定剧本建立 Scene Card，只记录场次事实，不写表演策略、镜头或 Prompt。
```

Scene Engine 应填写：

- `scene_event`：这场戏真正发生了什么
- `value_start / value_end`：价值状态如何改变
- `turn`：转折点
- `information_revealed`：观众或人物新知道什么
- `character_conflict`：人物冲突事实
- `physical_situation`：人物和环境的客观状态
- `continuity_in / continuity_out`：进场和出场状态
- 场次所需人物、地点、道具与状态版本

### B2. 检查 Scene Card

重点检查：

- 是否把推测写成事实
- 是否漏掉入场状态和出场状态
- 是否把“悲伤、愤怒”误写成表演指令
- 是否漏掉关键道具的持有手、位置或状态

如果场次事实还不确定，就保留为 unresolved，不要进入正式资产规划。

---

## 阶段 C：资产规划、LIRA 与 G2 资产锁定

### C1. 建立资产需求

对 Codex 说：

```text
使用 asset-architect 分析所有已锁定 Scene Card。先复用 Registry 中兼容资产，再列出必须新增的角色身份、角色状态、地点、道具和服装资产。
```

资产架构师决定“需要什么”，而不是“Prompt 怎么写”。

核心规则：

- 图片不是完整资产；资产必须同时有文字 Descriptor 和图像参考。
- 一个状态就是一个资产。
- 人物身份根固定，湿身、受伤、变异等状态建立子资产。
- 已锁定资产不能原地覆盖，只能创建新版本。

示例：

```text
@char_PC_Aya_base_v01
@char_PC_Aya_wet_v01
@char_PC_Aya_wounded_v01
```

### C2. 让 LIRA 生成资产 Prompt

逐个或按相容批次处理：

```text
为 @char_PC_Aya_base_v01 调用 film-os-lira。读取 Asset Registry 和 Character Bible，输出模型路由、正式英文 Prompt、所需视图和 QC 标准。不要改变资产规格。
```

LIRA 会根据原始 Skill 决定适合的模型和 Prompt 结构。外围系统不能擅自指定一套与 LIRA 冲突的方法。

### C3. 建立 TapNow 资产 Canvas

```text
使用 tapnow-bridge，把 S001 所需的待生成资产转换为 TapNow 资产 Canvas Manifest 和 Node Map。每个节点绑定资产 ID 与版本。
```

推荐一类资产一个 Canvas，或一组强相关资产一个 Canvas：

```text
NFY_char_Aya_assets_v01
NFY_loc_ControlRoom_assets_v01
NFY_S001_props_v01
```

### C4. 在 TapNow 中生成

TapNow 操作员：

1. 按 Manifest 创建 Canvas。
2. 按 Node Map 建立参考输入、生成、编辑和 Review 节点。
3. 原封不动使用已经发布的资产 Prompt。
4. 将输出绑定回对应资产 ID 和版本。
5. 不要因为节点显示成功就把资产标成 locked。

### C5. 资产 QC

按 Registry 的接受标准检查：

- 人物身份是否一致
- 所需视图是否齐全
- 服装、伤口、道具状态是否正确
- 地点固定结构是否稳定
- 是否有文字、手指、纹理和材质伪影
- 图片是否与 Descriptor 同时成立

失败时明确一个主要问题：

```text
@char_PC_Aya_base_v01 正面和侧面身份一致，但背面发型结构错误。只修改 hair_back_structure，保留 identity、face、wardrobe、lighting 和 sheet layout。
```

### C6. 审批 G2

所有本场需要的正式资产都通过后：

```text
批准 S001 所需资产，审批 G2_ASSET_LOCK。审批人：李四。锁定当前资产版本并更新 Registry 与 Version Log。
```

---

## 阶段 D：镜头设计、空间系统与 G3 镜头锁定

### D1. 设计覆盖方案

```text
使用 storyboard-director 为 S001 设计最少但完整的镜头方案。每个镜头说明戏剧功能、时长、主体、构图、事件、第一帧、摄影意图和剪辑关系。
```

Storyboard Director 不应直接写 CINEDANCE 最终 Prompt。

### D2. 使用镜头编号

镜头按十递增：

```text
S001_SH010
S001_SH020
S001_SH030
```

需要中间插入镜头时可用 `S001_SH015`，不用重命名后面全部镜头。

### D3. 建立 Spatial Map

```text
使用 spatial-system 为 S001 建立 SPATIAL.yaml，并为每个镜头生成空间切片。检查固定地标、人物位置、180 度轴、视线、左右关系、进出路径和前中后景。
```

空间系统至少要回答：

- 门、窗、桌、椅等固定地标在哪里
- 人物站在哪里、朝向哪里
- 摄影机在哪一侧
- 谁在画面左/右
- 人物视线指向哪里
- 是否跨轴，若跨轴是否是明确设计
- 道具放在哪里、由谁持有

### D4. 设计 First Frame

每个 Shot Card 必须明确第一帧。复杂镜头可以同时写：

- 三维空间位置
- 摄影机位置、高度、倾角
- FOV 度数与全画幅等效焦距
- 二维画面区域
- 前景遮挡、景深和焦点

FOV 控制画面看到多宽；摄影机距离控制透视；构图控制人物在画面多大；景深单独控制。不要让一个 `85mm` 承担全部作用。

### D5. 必要时进行 Blender 白模预演

普通镜头跳过这一步。跨空间长镜头、复杂环绕/升降、多人交叉走位、精确遮挡、严格首尾衔接，或因空间运动歧义而反复失败的镜头，可以说：

```text
$film-blender-previz 判断 S001_SH010 是否需要白模预演。先给我预演范围和审核问题，不要直接操作。
```

确认后，Codex 使用本机 Blender 控制器搭建最少白模、占位人物、摄影机路径和必要动作，输出预览视频、首尾帧与参数。只审核镜头、空间、走位、遮挡和节奏；不要把白模人物、灰色材质或预览灯光当成美术参考。

如果接受，预演结果会绑定到当前 Shot Card，并进入同一个 G3；系统不会增加第六个 Gate。完整安装和团队使用见 `BLENDER_PREVIZ.zh-CN.md`。

### D6. 调用 ACTING

先为常驻人物建立 Master Profile，再为具体场次建立适配：

```text
调用 film-os-acting。读取 Aya 的 Character Bible 和 S001 Scene Card，为 Aya 建立这场戏的表演适配。保持摄影、服装和灯光信息在外部。
```

ACTING 的输出要回答行为问题，而不是只写情绪：

- 人物此刻想从谁那里得到什么
- 什么阻挡了他/她
- 代价是什么
- 每个 Beat 使用什么策略
- 潜台词是什么
- 眼神、身体、呼吸、停顿如何体现思考

### D7. 审批 G3

导演检查：

- 镜头是否都具有明确功能
- 是否存在重复覆盖
- 第一帧是否可执行
- 空间、轴线和视线是否一致
- 表演与场次转折是否匹配
- 镜头时长是否容纳动作与对白
- 如标记为必须预演，当前 Blender 预演版本是否已接受

批准时说：

```text
批准 S001 的镜头表、空间系统和表演方向，审批 G3_SHOT_LOCK。审批人：张三。
```

---

## 阶段 E：Shot Packager、CINEDANCE 与 G4 Prompt 发布

### E1. 打包单个镜头

```text
使用 production-supervisor 打包 S001_SH010 v01。只保留当前镜头需要的已批准信息，生成 sealed Shot Pack，不要先调用 CINEDANCE。
```

Shot Pack 可以读取整个项目，但输出只允许包含：

- 当前 Shot ID 与版本
- 当前镜头的场景事实
- 当前镜头使用的已批准参考及其职责
- 当前镜头使用的空间切片
- 当前镜头已接受的 Blender 预演事实、共享参考和禁止继承项（如有）
- First Frame
- Blocking、eyeline 和 screen direction
- 当前镜头的 ACTING 表演适配
- Camera、动作时间、Physics、Lighting、Audio
- Continuity in/out
- Positive Locks
- 如果是返工：唯一允许改变的变量

禁止进入 Shot Pack：

- 不在当前画面的角色和道具
- 旧资产版本
- 其他场次资料
- 旧 Prompt 或被拒绝的 Take
- 生产聊天和临时讨论
- `same as before`
- `continues`
- `previous scene`
- `from last shot`
- 没有绑定资产的 @tag

### E2. 检查参考图职责

每张参考都必须说明：

- 它控制什么
- 哪些东西不能从它继承

例如：

```text
@loc_ControlRoom_night_v01 controls the room architecture, panoramic window and material language only. Do not inherit its camera angle, framing, character placement or temporary props.
```

### E3. 调用 CINEDANCE

```text
对 sealed S001_SH010 v01 Shot Pack 调用 film-os-cinedance。严格遵守原始 CINEDANCE Skill，只输出最终英文视频 Prompt。
```

CINEDANCE 是 Compiler，不负责重新决定剧本、资产身份、镜头功能或人工审批。

### E4. Prompt Audit

```text
使用 production-supervisor 审计 S001_SH010_video_v01。逐项写入 prompt_audit；发现问题就阻止发布，不要自动放行。
```

必须检查十项：

1. 所有 ID 与版本能唯一解析。
2. 只有当前镜头的角色、道具和 tags。
3. 每张参考职责明确。
4. 第一帧、空间、轴线、视线、Blocking 一致。
5. 动作顺序和触发关系明确，对白放得下。
6. 物理、手、道具归属和物体连续性合理。
7. 灯光与声音可执行且不冲突。
8. Continuity 和 Positive Locks 完整。
9. 没有跨镜头语言、旧 tags、场次编号垃圾或生产备注。
10. 返工只改变一个变量，其他锁定变量被明确保留。

### E5. 审批 G4

审计通过后由 Prompt Lead 审批：

```text
批准 S001_SH010_video_v01 发布到 TapNow，审批该镜头的 G4_PROMPT_RELEASE。审批人：王五。
```

---

## 阶段 F：TapNow 视频生成、QC 与 G5

### F1. 建立视频 Canvas

```text
使用 tapnow-bridge 为已发布的 S001_SH010_video_v01 更新 Canvas Manifest 和 Node Map。绑定全部参考资产版本、Shot Pack、Prompt ID 和输出 Take ID。
```

推荐一个镜头一个视频 Canvas：

```text
NFY_S001_SH010_video_v01
```

### F2. 生成并登记 Take

TapNow 输出使用：

```text
S001_SH010_TK001_v01
S001_SH010_TK002_v01
```

然后告诉 Codex：

```text
登记 S001_SH010_TK001_v01。来源节点 TN_NFY_S001_SH010_GEN_v01，使用 Prompt S001_SH010_video_v01。进入 QC，不要自动批准。
```

### F3. Take QC

推荐按以下顺序看：

1. 身份和资产状态
2. 第一帧与空间关系
3. 人物位置、视线、手和道具
4. 表演节拍和反应
5. 摄影机运动与构图
6. 动作顺序、时机和对白
7. 物理和材质
8. 灯光、声音和整体连续性

不要只写“感觉不对”。把问题写成可观察事实。

坏不要这样写：

```text
人物怪怪的，空间也不对，镜头不够电影感，再做一个。
```

应该这样写：

```text
S001_SH010_TK001_v01：Aya 身份、服装、表演和时机通过；主要失败是人物进入后房间尺度缩小，门到椅子的距离少约 30%。下一版只修改 location/spatial scale，保留 identity、wardrobe、composition、camera、performance、timing、lighting 和 audio。
```

### F4. 单变量返工

允许的主变量：

```text
identity
wardrobe_state
location
composition
camera
blocking
performance
timing
physics
lighting
audio
continuity_lock
```

一次只选一个。Production Supervisor 根据变量路由：

- `identity / wardrobe_state / location` 的图像或参考问题 → LIRA
- `performance` → ACTING
- 空间地理问题 → Spatial System，再交 CINEDANCE
- `camera / blocking / timing / physics / lighting / audio / continuity_lock` → CINEDANCE

如果同一 Take 有三个问题，先选择最上游、影响最大的一个。例如身份错时先修身份，不要同时微调灯光。

### F5. 审批 G5

Take 真正可进入剪辑时：

```text
批准 S001_SH010_TK003_v01 为 Approved Take。审批 G5_TAKE_APPROVAL，审批人：张三。更新 Shot Card、Node Map 和 Version Log；不要删除失败 Take。
```

失败 Take 保留追踪记录，但不能作为后续参考输入，除非人工明确指定某个局部可复用。

---

## 5. 五个 Gate 一览

| Gate | 审批内容 | 常见审批人 | 未通过时禁止 |
|---|---|---|---|
| G1 Script Lock | 剧本、场次边界、Canon | 导演/编剧 | 正式资产生产 |
| G2 Asset Lock | 人物身份、状态、地点、英雄道具 | 美术/资产负责人 | 正式镜头生成 |
| G3 Shot Lock | Shotlist、空间、First Frame、表演方向 | 导演 | 视频 Prompt 编译 |
| G4 Prompt Release | Sealed Shot Pack 与 Prompt Audit | AI 导演/Prompt Lead | TapNow 视频生成 |
| G5 Take Approval | 可进入剪辑的最终 Take | 导演/剪辑 | 标记镜头完成 |

Gate 可以 `pending / approved / rejected / waived`。`waived` 仍然必须写明审批人和原因。

---

## 6. 常用 Codex 指令模板

### 项目状态

```text
检查整个 Film OS 项目，告诉我当前状态、下一道 Gate、阻塞项、未锁定资产和等待 QC 的镜头。不要修改文件。
```

### 处理一场戏

```text
处理 S024：先检查 G1 和依赖；建立或更新 Scene Card；列出资产缺口。到需要人工决定或审批时停止。
```

### 资产阶段

```text
列出 S024 所需资产，区分可复用、需新增、需状态版本和信息不足。不要生成 Prompt。
```

```text
为 S024 所有已批准资产规格调用 LIRA，生成 TapNow 可执行的资产任务；每项保留 Asset ID、版本和 QC 标准。
```

### 镜头阶段

```text
为 S024 设计镜头覆盖和空间图。先给导演审阅，不调用 CINEDANCE。
```

```text
为 S024_SH030 建立 ACTING 场次适配；只写可表演行为，不加入摄影、服装或灯光。
```

### Prompt 阶段

```text
打包 S024_SH030 v03。清除不活跃人物、旧 @tag、其他镜头信息、旧 Prompt 和生产备注。输出 sealed Shot Pack。
```

```text
调用 CINEDANCE 编译这个 sealed Shot Pack，然后执行 Prompt Audit。审计没通过就不要申请 G4。
```

### 返工阶段

```text
S024_SH030_TK002_v01：人物身份、构图、表演均通过，但气瓶落在人物左侧，违反空间图。新版本只修改 blocking；保留 identity、location、composition、camera、performance、timing、physics、lighting 和 audio。登记失败、生成返工包并重新审计。
```

---

## 7. 一个完整的小型示例

假设 S024 的剧情是：林原进入地下车站，看见失踪的妹妹站在轨道另一边；她没有回应，列车灯从隧道出现。

### 7.1 Scene Engine 输出事实

```yaml
scene_event: 林原找到妹妹，但两人被轨道隔开
value_start: 希望
value_end: 即将失去
turn: 隧道里出现列车灯
physical_situation: 两人分别站在同一股轨道两侧
continuity_in:
  - 林原右手有新鲜伤口
continuity_out:
  - 妹妹仍在对面站台
  - 列车已经接近
```

### 7.2 Asset Architect 建立需求

```text
@char_PC_Linyuan_wounded_hand_v01
@char_SC_Sister_station_v01
@loc_UndergroundStation_abandoned_v01
@prop_TrainHeadlight_approaching_v01
```

### 7.3 Storyboard Director 设计镜头

```text
S024_SH010：林原进入，建立空间
S024_SH020：妹妹在对面站台，视线不回应
S024_SH030：双人远景，灯光进入隧道深处
S024_SH040：林原反应特写
```

### 7.4 Spatial System 锁定

```text
林原在轨道南侧站台，画面左
妹妹在北侧站台，画面右
轨道横向隔开两人
隧道口在妹妹后方深景
摄影机在南侧，不跨轴
```

### 7.5 ACTING 处理 S024_SH040

ACTING 不写“林原非常悲伤”，而是把表演转成行为：林原试图让妹妹看向自己；先压低声音避免惊动她，发现列车灯后策略转为急促命令；眼睛先锁妹妹，再被隧道灯短暂拉走，回看时呼吸中断。

### 7.6 Shot Packager 隔离 S024_SH040

该镜头是林原特写，因此不能把妹妹的图像 tag 或列车完整资产塞进 Prompt。可以保留：妹妹是林原画外视线目标、列车灯造成的画外变化和声音。这样能避免模型在特写里错误生出妹妹或列车。

### 7.7 第一版失败

如果结果中人物正确，但她从一开始就在哭，问题属于 `performance`。只让 ACTING/CINEDANCE修正节拍，明确前段压制、后段才失控；不要同时改变镜头、身份或灯光。

---

## 8. 团队管理规则

### 8.1 每天开工

Production Supervisor 先让 Codex输出：

- 今天可执行的镜头
- 各镜头当前状态
- 缺失依赖
- 等待谁审批
- TapNow 中需要生成或 QC 的节点

### 8.2 每次交接

统一格式：

```text
实体 + 版本 — 观察结果 — 唯一修改项 — 必须保留项 — 负责人
```

例：

```text
S024_SH030 v03 — 身份和时机通过，空间尺度小 30% — 修改 location — 保留 identity、blocking、camera、performance、timing — Spatial/LIRA
```

### 8.3 每天收工

要求 Codex：

```text
执行收工检查：验证 YAML，列出今天的版本变化、审批、失败 Take、未完成节点和明天的首要阻塞。缺失的记录补入 Version Log，但不要替任何人审批。
```

---

## 9. 常见错误与处理

### 错误：让 Codex 一口气从剧本生成最终视频 Prompt

这会跳过资产、空间、表演和审批。应按 Gate 逐步推进。

### 错误：用 `same as before`

视频模型没有可靠的“before”。Shot Pack 必须重新声明当前镜头需要的全部事实。

### 错误：把整部影片资料交给 CINEDANCE

会造成旧 tag、角色、道具和空间污染。必须先建立 sealed Shot Pack。

### 错误：一个人物 tag 承担所有状态

湿身、受伤、变异、不同服装分别建状态资产，并指回同一 identity root。

### 错误：失败后同时改五个地方

这样无法知道哪个修改有效，还会破坏已通过部分。一次只改一个主变量。

### 错误：TapNow 节点成功就算审批成功

技术运行成功不等于美术或导演验收。审批只能由人在 Film OS 记录。

### 错误：覆盖 Approved 文件

Approved 记录不可原地修改。创建下一版本，并在 Version Log 写明父版本和修改变量。

### 错误：把表演写成情绪标签

“愤怒、伤心、邪恶”不可执行。交给 ACTING 转成目标、策略、节拍、视线、身体和声音行为。

---

## 10. 项目完成条件

只有满足以下条件，镜头才算完成：

- G1、G2、G3、G4 均有合法审批记录
- 当前 Shot Card 和所有资产 ID 可解析
- Released Prompt 与 TapNow 节点一一对应
- Take 完成 QC
- G5 有人工审批人和时间
- Approved Take 已写回 Shot Card、Node Map 和 Version Log
- 没有用失败或旧版本输出替代当前批准素材

项目交付前，Production Supervisor 应运行仓库校验，并输出最终资产清单、Approved Take 清单、未解决例外和完整版本记录。

---

## 11. 推荐的首次实战方式

不要第一次就跑完整长片。选择一场包含两个人物、一个关键道具、明确空间关系和 3–5 个镜头的戏，完整跑过五个 Gate。

推荐测试目标：

1. 角色身份跨镜头是否稳定。
2. 位置、方向和视线是否稳定。
3. ACTING 的节拍能否被视频 Prompt准确执行。
4. Shot Pack 是否真正隔离了旧上下文。
5. 单变量返工能否保住已经通过的部分。
6. TapNow Node Map 是否能追踪每个结果来自哪个 Prompt 和资产版本。

完成第一次压力测试后，只修改被真实失败证明有问题的规则，不要因为个人偏好不断给系统增加全局限制。
