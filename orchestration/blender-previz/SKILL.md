---
name: film-os-blender-previz
description: Decide, specify, execute, and review bounded Blender whitebox previsualization for a Film OS shot before its spatial and camera intent is locked.
---

# Blender Previsualization Orchestrator

Blender previz is an optional bridge between storyboard/spatial design and the existing G3 shot lock. It provides measurable spatial and motion evidence; it does not create canon, final art, or a sixth approval gate.

## Entry decision

Recommend previz when at least one high-risk condition or two ordinary conditions are present:

- the camera crosses rooms, floors, doors, windows, vehicles, or several depth planes;
- the move combines crane, orbit, dolly, handheld pursuit, rapid reframing, or a lens/axis change;
- several performers cross, exchange props, occlude one another, or must hit timed marks;
- foreground objects, reflections, narrow passages, or set boundaries create collision risk;
- adjacent shots require exact entry/exit geometry or a repeatable camera path;
- a generated take failed primarily because text could not express the intended spatial motion.

Do not recommend it for a static setup, ordinary close-up, single uncomplicated move, or a problem owned by identity, styling, dialogue, acting nuance, or image quality.

## Preconditions

Require an approved scene basis, a draft Shot Card with dramatic function and duration, and a current Spatial Map or an explicit request to build one. Resolve the intended subject, first frame, last frame, camera objective, key blocking, landmarks, duration, frame rate, aspect ratio, and the question the previz must answer. Unresolved creative choices remain human decisions.

## Human authorization

Present one short proposal containing: why previz is useful, what Blender will build, what it will not decide, expected outputs, and the review question. Do not operate Blender until a person confirms this bounded proposal. This operational confirmation does not approve G3.

## Runtime and safety

1. Verify the combined runtime for the `blender_previz` task profile and verify a live Blender session by observable inspection.
2. Prefer DCC-MCP typed tools for geometry, camera, animation, render, capture, and save operations. Otherwise use a compatible structured local bridge.
3. Bind services to localhost. Use a new versioned `.blend` file or Save As before changing an existing scene.
4. Use primitives and locally approved assets. Do not browse, download, upload, or install assets without separate authorization.
5. Prefer typed/structured operations. If raw Python is the only practical route, explain the exact action and ask for a separate confirmation immediately before execution.
6. Capture the adapter, Blender version, client, model provenance, and observed capability status. A model name alone is not evidence of Blender control.

## Build contract

Create only enough geometry to answer the approved shot question:

- use one consistent coordinate system and real or explicitly normalized scale;
- name fixed landmarks, proxy performers, hero props, cameras, and paths with Film OS IDs;
- use neutral, non-authoritative materials and simple proxy silhouettes;
- place first-frame and last-frame markers plus only the necessary intermediate beats;
- set lens/FOV, camera height, target/aim behavior, frame rate, frame range, and interpolation deliberately;
- animate blocking and prop transfers only when they affect camera or spatial readability;
- detect wall/object intersections, unintended occlusion, axis violations, speed spikes, and impossible movement;
- produce a fast viewport/Workbench preview before any higher-cost render.

Do not beautify the scene into an accidental art-direction reference. Do not infer facial acting from proxy motion; ACTING remains authoritative for performance.

## Required outputs

Create one versioned Previz Card using `templates/BLENDER_PREVIZ_CARD.yaml`, plus:

- a human-readable review sheet;
- a versioned `.blend` working file URI;
- a preview video or image sequence;
- explicit first and last frames;
- camera/lens/frame-rate/duration data;
- blocking landmarks and timed beats;
- a list of what the preview controls and must not control;
- runtime provenance and source versions.

If an output was not observed, mark it missing. Never fabricate an export or shared URI.

## Review and G3

Ask the human to review only the declared questions: spatial clarity, camera path, framing, collisions/occlusion, blocking, timing, and continuity. Record `accepted`, `revision_requested`, or `rejected` on the Previz Card. Acceptance makes the preview eligible as a G3 reference; it does not independently lock the shot.

When G3 is approved, bind the accepted Previz Card version to the Shot Card. A later change to camera, blocking, duration, lens, geometry, or spatial continuity creates a new Shot Card and Previz Card version and requires renewed G3 review. Cosmetic Blender changes that do not alter a declared control job do not create a new canonical shot version.

## TapNow handoff

Declare the previz as a `motion_geometry` reference. If the selected TapNow model accepts video/motion reference, attach the preview through a `previz_reference` node. Otherwise extract only the necessary first/intermediate/last frames and translate the camera path into explicit timing constraints. In both cases state that neutral materials, proxy faces/bodies, placeholder wardrobe, preview lighting, viewport artifacts, and whitebox styling must not be inherited.

The Shot Pack receives only the accepted current-shot preview facts and shared reference URI. Exclude the `.blend` scene history, discarded paths, other shots, technical chatter, and rejected previews.

## Iteration

Previz revisions follow the normal single-variable discipline. Choose one primary variable from the Film OS list—normally `composition`, `camera`, `blocking`, `timing`, `physics`, or `continuity_lock`—and preserve every accepted variable. A requested rebuild across several variables requires explicit human authorization and a new version.
