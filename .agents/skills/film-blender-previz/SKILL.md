---
name: film-blender-previz
description: Plan and execute optional Blender whitebox previsualization for Film OS shots whose camera path, blocking, depth, or spatial continuity cannot be specified reliably with text and storyboards alone.
---

# Blender Previsualization

Read `../../../orchestration/blender-previz/SKILL.md`, `../../../BLENDER_PREVIZ.zh-CN.md`, the Creative North Star, the current Scene Card, Shot Card, and relevant Spatial Map. This is an optional technical-previsualization department, not a creative-authority engine and not a replacement for Storyboard Director, Spatial System, ACTING, CINEDANCE, LIRA, or TapNow.

Diagnose whether 3D previsualization is justified before operating Blender. You may recommend it when a shot has complex camera travel, multi-subject blocking, occlusion, depth changes, multi-space continuity, precise timing, or repeated generation failures caused by spatial ambiguity. Do not send ordinary static, close-up, or simple dialogue shots through Blender merely because the tool is available.

Explain in plain Chinese what the previsualization will resolve and obtain human confirmation before creating or changing a Blender scene. That confirmation authorizes only the stated previsualization scope; it is not a Film OS gate approval. The accepted result is reviewed as part of G3 分镜确认.

Prefer the installed DCC-MCP typed Blender tools. A compatible structured Blender bridge may be used when DCC-MCP is unavailable. Before claiming execution, verify observable Blender control and viewport/render capture. If no compatible controller is available, create only a Previz Card and setup brief; never claim a `.blend`, preview, screenshot, or camera path was produced.

Use low-detail geometry, neutral materials, named landmarks, proxy performers, and an explicit camera path. The previsualization controls only the declared jobs—normally geometry, camera, blocking, occlusion, depth, and timing. It must not silently control character identity, wardrobe design, surface detail, color, lighting style, performance nuance, or final visual treatment.

Store the human-readable review sheet under `../../../项目工作区/05_分镜与空间/Blender预演/` and the technical card under the current scene's `previz/` directory. Store heavy `.blend`, image-sequence, and video media in the declared TapNow/team-media location plus milestone backup; keep stable IDs, shared URIs, checksums when available, and approval records in Film OS. Never make one teammate's absolute local path the only shared reference.

Before any production write, run the local authority check. A contributor must keep the Previz Card, Blender plan, previews, and every downstream artifact based on them inside one new proposal bundle. Only a verified director may promote an accepted version to canonical scene records.

Do not download third-party models, enable telemetry, expose a network bridge beyond localhost, or execute arbitrary Blender Python by default. Raw scripting requires a specific human confirmation after the exact need and risk are explained, and it may not exceed the approved shot scope.
