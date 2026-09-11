# TapNow Canvas Manifest specification

One manifest is the execution ledger between Film OS and TapNow. A canvas groups one bounded purpose: asset batch, storyboard batch, or one shot's video/retakes. Do not mix unrelated scenes or approved and experimental branches.

Required canvas fields: `canvas_id`, `display_name`, `project_id`, `purpose`, `scene_id`, optional `shot_id`, `version`, `status`, `film_os_sources`, `node_ids`, `created_by`, `created_at`, and `notes`. `display_name` is the readable Chinese TapNow title defined in `bible/NAMING.md`; `canvas_id` is the stable internal ID. Source entries must include entity ID and version. Canvas status is `planned | active | complete | archived`; it is not an approval state.

For series work, also record `series_id`, `season_id`, and `episode_id`. Keep permanent character/location/prop asset canvases reusable at series scope, but create storyboard and formal shot canvases inside one episode scope. A shot canvas must never mix takes from another episode, even when locations and cast are identical.

Outputs are imported back by adding their URI/path, node ID, generated timestamp, and target Film OS entity/version. Human QC then changes Registry/Shot state separately.
