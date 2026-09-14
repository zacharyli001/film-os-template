---
name: film-os-spatial-system
description: Define stable location topology, landmarks, character positions, axis, eyelines, screen direction, depth, and first-frame geometry for Film OS shots.
---

# Spatial System

Create a scene location map and per-shot spatial slice. Establish one coordinate convention, fixed landmarks, actor/prop anchors, 180-degree axis, eyelines, entry/exit paths, foreground/midground/background, and any useful normalized screen coordinates. Treat reference framing as non-binding unless explicitly inherited. Detect contradictions before shot lock. If camera clearance, occlusion, moving eyelines, depth transitions, or intersecting paths remain uncertain, route a bounded question to Blender Previz and incorporate only a human-accepted result. Do not write performance or final prompts.
