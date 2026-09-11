# TapNow Node Map specification

Every TapNow node has one primary Film OS responsibility.

Node types: `reference_input`, `image_generate`, `image_edit`, `storyboard`, `video_generate`, `frame_extract`, `review`, `export`. A node record contains `node_id`, `canvas_id`, `node_type`, `input_entity_ids`, `input_versions`, `prompt_id`, `depends_on`, `output_targets`, `status`, and optional `iteration`.

Allowed dependency flow:

```text
approved reference_input → generate/edit/storyboard → review → approved registry asset
released shot pack + approved references → video_generate → frame_extract/review → take QC
```

For a retake, create a new versioned generation node. `iteration.change_variable` must contain exactly one enum from `AGENTS.md`; `iteration.preserve` lists the locked variables. Never reconnect an obsolete or rejected asset silently.

