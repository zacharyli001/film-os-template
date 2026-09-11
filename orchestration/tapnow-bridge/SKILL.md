---
name: film-os-tapnow-bridge
description: Translate approved Film OS asset and shot work into traceable TapNow canvases, nodes, dependencies, and result mappings.
---

# TapNow Bridge

Read `tapnow/CANVAS_MANIFEST_SPEC.md` and `tapnow/NODE_MAP_SPEC.md`. Create/update manifest records; map every node to a Film OS entity/version and every output back to its source node. Never treat a successful generation as approval. Do not overwrite locked assets or approved takes. For retakes, clone or version the node and record the single changed variable.

For a series, reuse approved show-level asset canvases through stable asset IDs and create episode-scoped storyboard/shot canvases using the full season/episode/scene/shot ID. Attach only the current episode's valid state versions. Keep future episode plans and past episode prompts out of the canvas.
