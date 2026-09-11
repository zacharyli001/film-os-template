# Unified data protocol

All YAML begins with `schema_version: film-os/v1`, uses stable IDs, ISO-8601 UTC timestamps, explicit `null`, and controlled enum states from `AGENTS.md`. References use IDs plus versions, never filenames alone.

Series projects use four canon layers: Series Bible for durable show rules, Season Map for the current season plan, Episode Card for one episode's dramatic contract, and Series Continuity Ledger for facts proven or changed on screen. Lower layers may elaborate but may not silently contradict higher approved layers. `series_id`, `season_id`, and `episode_id` must be explicit on series Scene Cards, Shot Cards, takes, and TapNow records.

An asset is `descriptor + image reference + state + lineage`; an image without a descriptor is not a production asset. Every reference job declares what it controls and what it must not inject. Every promoted artifact carries its source versions.

Scene Cards contain dramatic facts. ACTING owns interpretation. Shot Cards contain directorial intent and references. Shot Packs are compiled, sealed, current-shot views. TapNow manifests map execution nodes; they never replace Registry state.

Required integrity rules:

- Every referenced ID resolves exactly once.
- Every active state has an identity root or location/prop parent where applicable.
- Every locked entity has a human approval record.
- Every take resolves to one released prompt and one TapNow node.
- Every retake declares exactly one changed variable and its preserved variables.
- Every series scene and shot resolves to exactly one Episode Card.
- Every approved episode updates the continuity ledger before the next episode reaches G1.
- Every planted thread has an owner, status, first episode, and intended payoff window; a proposal is not a canonical payoff.
