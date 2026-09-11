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
- TapNow canvas: `DEMO_S001_assets_v01` or `DEMO_S001_SH010_video_v01`
- TapNow node: `TN_DEMO_S001_SH010_GEN_v01`

Never use `final`, `latest`, `new`, `same`, or `copy` as versions. A state change creates a new asset; an approved record is immutable.

