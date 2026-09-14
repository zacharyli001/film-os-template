# TapNow Node Map specification

Every TapNow node has one primary Film OS responsibility.

Node types: `reference_input`, `previz_reference`, `image_generate`, `image_edit`, `storyboard`, `video_generate`, `frame_extract`, `review`, `export`. A node record contains `node_id`, `canvas_id`, `node_type`, `input_entity_ids`, `input_versions`, `prompt_id`, `depends_on`, `output_targets`, `status`, and optional `iteration`.

A `previz_reference` resolves to one human-accepted current-shot Blender Previz Card. Its default declared job is `motion_geometry`; it controls only the listed camera, geometry, blocking, occlusion, depth, and timing facts. It must include a `non_inheritance` list excluding proxy identity/body/wardrobe, whitebox materials, preview lighting, and viewport artifacts. Attach a preview video only when the selected TapNow model has verified support for that input; otherwise use the minimum extracted frames plus explicit timing facts.

Allowed dependency flow:

```text
approved reference_input → generate/edit/storyboard → review → approved registry asset
accepted previz_reference + released shot pack + approved references → video_generate → frame_extract/review → take QC
released shot pack + approved references → video_generate → frame_extract/review → take QC
```

For a retake, create a new versioned generation node. `iteration.change_variable` must contain exactly one enum from `AGENTS.md`; `iteration.preserve` lists the locked variables. Never reconnect an obsolete or rejected asset silently.
