# Gates, audit, and QC

At each gate the owner reviews the named deliverable, records `approved`, `rejected`, or `waived`, their name, UTC timestamp, and note. Rejection returns the entity to the owning upstream state; it does not erase history.

## Prompt Audit checklist

1. Schema/version and all IDs resolve.
2. Only current-shot cast, props, tags, and reference versions appear.
3. Each reference has one job plus explicit non-inheritance where needed.
4. First frame, geography, axis, screen direction, eyelines, and blocking agree.
5. Timeline is serializable; triggers follow causes; dialogue fits.
6. Physics, hands, prop ownership, and object permanence are plausible.
7. Lighting/audio are executable and do not contradict references.
8. Continuity-in/out and positive desired-state locks are explicit.
9. No `same as before`, `continues`, `last shot`, stale tags, scene chatter, or unused entities.
10. Retake changes one primary variable and preserves all approved variables.

Hero performance must meet the ACTING engine's own QC threshold; do not invent a substitute scale.

