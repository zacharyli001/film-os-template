# Unified data protocol

All YAML begins with `schema_version: film-os/v1`, uses stable IDs, ISO-8601 UTC timestamps, explicit `null`, and controlled enum states from `AGENTS.md`. References use IDs plus versions, never filenames alone.

An asset is `descriptor + image reference + state + lineage`; an image without a descriptor is not a production asset. Every reference job declares what it controls and what it must not inject. Every promoted artifact carries its source versions.

Scene Cards contain dramatic facts. ACTING owns interpretation. Shot Cards contain directorial intent and references. Shot Packs are compiled, sealed, current-shot views. TapNow manifests map execution nodes; they never replace Registry state.

Required integrity rules:

- Every referenced ID resolves exactly once.
- Every active state has an identity root or location/prop parent where applicable.
- Every locked entity has a human approval record.
- Every take resolves to one released prompt and one TapNow node.
- Every retake declares exactly one changed variable and its preserved variables.

