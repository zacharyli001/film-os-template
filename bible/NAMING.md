# Naming standard

IDs are stable ASCII; labels may use any language. Use uppercase project/scene/shot codes, lowercase asset categories, and two-digit versions.

- Scene: `S001`, `S024`
- Shot: `S001_SH010`; number by tens to allow inserts.
- Take: `S001_SH010_TK001_v01`
- Character identity: `@char_PC_Aya_base_v01`
- Character state: `@char_PC_Aya_wet_v01`
- Location: `@loc_ControlRoom_night_v01`
- Prop: `@prop_SteelCylinder_clean_v01`
- Wardrobe: `@ward_PC_Aya_uniform_v01`
- Prompt: `S001_SH010_video_v01`
- TapNow canvas: follow the strict Canvas ID rules below.
- TapNow node: `TN_DEMO_S001_SH010_GEN_v01`

Never use `final`, `latest`, `new`, `same`, or `copy` as versions. A state change creates a new asset; an approved record is immutable.

## Strict TapNow Canvas ID

The TapNow canvas title and the Film OS `canvas_id` must be identical:

`[PROJECT]_[SCOPE]_[PURPOSE]_v[NN]`

Rules:

- `PROJECT`: 2–8 uppercase ASCII letters/numbers, fixed when the project starts. Example: `NF01`.
- `SCOPE`: exactly one approved Film OS scope listed below.
- `PURPOSE`: exactly one lowercase purpose code listed below.
- `vNN`: two digits beginning at `v01`; increment only when creating a replacement canvas or a separate creative branch.
- Use ASCII letters, digits, and underscores only. No spaces, Chinese characters, punctuation, dates, operator names, or status words.
- The title is an ID, not a description. Put readable Chinese descriptions, owners, and status in the Canvas Manifest or TapNow notes.
- Do not rename a canvas after work has begun. If its scope or purpose was wrong, archive it and create the next version.
- Takes do not create a new canvas version. Keep shot takes inside the same shot canvas and name outputs with the Take ID.

Approved `SCOPE` values:

- Whole project: `GLOBAL`
- Scene: `S001`
- Shot: `S001_SH010`
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
- `NF01_S001_SH010_compare_v01`
- `NF01_GLOBAL_delivery_v01`

Invalid examples:

- `林渊人物最终版`
- `S1镜头3新版`
- `NF01_video_20260912`
- `NF01_S001_SH010_video_ZhangSan`
- `NF01_S001_SH010_video_final2`
