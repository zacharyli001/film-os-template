# Naming standard

IDs are stable ASCII; labels may use any language. Use uppercase project/scene/shot codes, lowercase asset categories, and two-digit versions.

- Scene: `S001`, `S024`
- Shot: `S001_SH010`; number by tens to allow inserts.
- Take: `S001_SH010_TK001_v01`
- Series: `SERIES01`
- Season: `SE01`
- Episode: `SE01_E001`
- Series scene: `SE01_E001_S001`
- Series shot: `SE01_E001_S001_SH010`
- Series take: `SE01_E001_S001_SH010_TK001_v01`
- Character identity: `@char_PC_Aya_base_v01`
- Character state: `@char_PC_Aya_wet_v01`
- Location: `@loc_ControlRoom_night_v01`
- Prop: `@prop_SteelCylinder_clean_v01`
- Wardrobe: `@ward_PC_Aya_uniform_v01`
- Prompt: `S001_SH010_video_v01`
- TapNow canvas: follow the strict Canvas ID rules below.
- TapNow node: `TN_DEMO_S001_SH010_GEN_v01`

Never use `final`, `latest`, `new`, `same`, or `copy` as versions. A state change creates a new asset; an approved record is immutable.

## TapNow dual-layer naming

TapNow is operated manually by a Chinese-speaking team, so the visible canvas title prioritizes human readability. Film OS keeps a separate stable `canvas_id` for machine tracking. They are mapped one-to-one in the Canvas Manifest.

### Human-facing TapNow canvas title

Use exactly five segments:

`[项目简称]-[阶段号+类型]-[对象编号]-[中文内容]-v[NN]`

Examples:

- `夜航-01创意-全片-核心概念-v01`
- `夜航-01视觉-全片-风格探索-v01`
- `夜航-02人物-PC01-林渊基础造型-v01`
- `夜航-02人物-PC01-林渊湿身状态-v01`
- `夜航-02服装-WD01-林渊黑色制服-v01`
- `夜航-03场景-LOC01-控制室夜景-v01`
- `夜航-03道具-PR01-钢制圆筒完好-v01`
- `夜航-04分镜-S001-控制室对峙-v01`
- `夜航-05镜头-S001_SH010-林渊推门-v01`
- `夜航-04分镜-SE01_E001-首集分镜-v01`
- `夜航-05镜头-SE01_E001_S001_SH010-林渊推门-v01`
- `夜航-06返工-S001_SH010-镜头运动对比-v01`
- `夜航-07交付-全片-审核通过镜头-v01`

The five segments always mean: **哪个项目—哪个阶段—哪个对象—画布里是什么—第几个版本**.

Human-title rules:

- Use the ordinary half-width hyphen `-` between segments. Do not mix `_`, spaces, brackets, or multiple separators.
- Keep the project short name at 2–6 Chinese characters and never change it after kickoff.
- The stage/type must come from the fixed list below; never invent synonyms.
- Use `全片` when the work is not tied to one numbered entity.
- The Chinese-content segment should be 2–12 Chinese characters and describe what a person will find inside.
- Do not include dates, operator names, status, `最终版`, `最新版`, `新的`, `复制`, or emotional comments.
- Do not rename a canvas after production begins. If the scope or direction changes materially, archive it and create the next version.
- New takes stay inside the same shot canvas and do not increment the canvas version.

Fixed stage/type list:

- `01创意`: idea, theme, world, story exploration
- `01视觉`: overall look development and visual language
- `02人物`: character identity and character states
- `02服装`: reusable wardrobe assets
- `03场景`: reusable location assets
- `03道具`: reusable prop assets
- `04分镜`: scene storyboards and coverage
- `05镜头`: one formal production shot and its takes
- `06返工`: controlled comparison or major rework
- `07交付`: approved exports and delivery assembly

### Internal Film OS Canvas ID

Codex creates and maintains this automatically; TapNow operators do not need to memorize it:

`[PROJECT]_[SCOPE]_[PURPOSE]_v[NN]`

Rules:

- `PROJECT`: 2–8 uppercase ASCII letters/numbers, fixed when the project starts. Example: `NF01`.
- `SCOPE`: exactly one approved Film OS scope listed below.
- `PURPOSE`: exactly one lowercase purpose code listed below.
- `vNN`: two digits beginning at `v01`; increment only when creating a replacement canvas or a separate creative branch.
- Use ASCII letters, digits, and underscores only. No spaces, Chinese characters, punctuation, dates, operator names, or status words.
- Put the internal Canvas ID on the first line of the TapNow canvas description/notes when that field is available.
- Takes do not create a new canvas version. Keep shot takes inside the same shot canvas and name outputs with the Take ID.

Approved `SCOPE` values:

- Whole project: `GLOBAL`
- Season: `SE01`
- Episode: `SE01_E001`
- Scene: `S001`
- Shot: `S001_SH010`
- Series scene: `SE01_E001_S001`
- Series shot: `SE01_E001_S001_SH010`
- Character: `char_PC_Aya`
- Character state: `char_PC_Aya_wet`
- Location: `loc_ControlRoom_night`
- Prop: `prop_SteelCylinder_clean`
- Wardrobe: `ward_PC_Aya_uniform`

Approved `PURPOSE` values:

- `concept`: early concept exploration
- `lookdev`: visual language and style exploration
- `assets`: reusable asset generation or locking
- `storyboard`: scene storyboard and coverage
- `video`: one shot's production video and takes
- `compare`: controlled A/B or retake comparison
- `delivery`: approved exports and delivery assembly

Canonical examples:

- `NF01_GLOBAL_concept_v01`
- `NF01_GLOBAL_lookdev_v01`
- `NF01_char_PC_Aya_assets_v01`
- `NF01_char_PC_Aya_wet_assets_v01`
- `NF01_loc_ControlRoom_night_assets_v01`
- `NF01_prop_SteelCylinder_clean_assets_v01`
- `NF01_ward_PC_Aya_uniform_assets_v01`
- `NF01_S001_assets_v01`
- `NF01_S001_storyboard_v01`
- `NF01_S001_SH010_video_v01`
- `NF01_SE01_E001_storyboard_v01`
- `NF01_SE01_E001_S001_SH010_video_v01`
- `NF01_S001_SH010_compare_v01`
- `NF01_GLOBAL_delivery_v01`

Invalid examples:

- `林渊人物最终版`
- `S1镜头3新版`
- `NF01_video_20260912`
- `NF01_S001_SH010_video_ZhangSan`
- `NF01_S001_SH010_video_final2`
