---
name: film-asset-architect
description: Plan a film's character, state, wardrobe, location, prop, and reference assets; decide what must be generated, reused, or locked before prompts are written.
---

# Asset Architect

Read `../../../orchestration/asset-architect/SKILL.md` and follow it. Accept rough descriptions and inspiration references; classify them as inspiration, candidate, or production-ready. Create a simple human review sheet under `../../../项目工作区/04_资产/` and maintain the technical Registry behind it. This skill decides what is needed; LIRA decides how to prompt it.

For a series, separate reusable show-level identity/location/prop/wardrobe bases from episode-specific state deltas. Reuse only locked assets whose state is valid for the current episode. Never mutate a base asset to represent injury, age, dirt, weather, damage, disguise, or another continuity change; create a traceable state version and link it to the Episode Card.
