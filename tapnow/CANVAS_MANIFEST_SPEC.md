# TapNow Canvas Manifest specification

One manifest is the execution ledger between Film OS and TapNow. A canvas groups one bounded purpose: asset batch, storyboard batch, or one shot's video/retakes. Do not mix unrelated scenes or approved and experimental branches.

Required canvas fields: `canvas_id`, `project_id`, `purpose`, `scene_id`, optional `shot_id`, `version`, `status`, `film_os_sources`, `node_ids`, `created_by`, `created_at`, and `notes`. Source entries must include entity ID and version. Canvas status is `planned | active | complete | archived`; it is not an approval state.

Outputs are imported back by adding their URI/path, node ID, generated timestamp, and target Film OS entity/version. Human QC then changes Registry/Shot state separately.

