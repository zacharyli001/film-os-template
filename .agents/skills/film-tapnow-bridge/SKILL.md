---
name: film-tapnow-bridge
description: Convert approved Film OS asset and shot prompts into clear TapNow task sheets, canvas plans, node mappings, and result handoffs.
---

# TapNow Bridge

Read `../../../orchestration/tapnow-bridge/SKILL.md` and the TapNow specifications. Hide technical mapping from non-technical users and create a plain task sheet under `../../../项目工作区/07_TapNow结果/`. Maintain manifests automatically. A generated result is not an approval.

For series production, label every task sheet with season and episode, reuse only locked series-level assets, and keep each formal shot canvas inside one episode. Do not make the operator reconstruct cross-episode continuity from memory.

For series work, create bounded canvases by episode and purpose. Keep reusable show assets in the Team Library/Elements, but keep formal shot generation and retakes inside the current episode/shot scope. Include season and episode IDs in every manifest record; do not mix two episodes in one production-shot canvas.

When a current accepted Blender previz is attached, map it as a `previz_reference` whose sole default job is `motion_geometry`. Use its preview video only when the selected TapNow model actually accepts motion/video reference; otherwise extract the minimum first/intermediate/last frames and compile its timing facts into the task. Always carry the previz non-inheritance list so whitebox style and proxy appearance cannot become accidental art direction.
