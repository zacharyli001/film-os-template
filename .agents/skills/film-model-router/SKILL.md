---
name: film-model-router
description: Verify a model-and-client runtime against Film OS task requirements, route work by observed capabilities, and record provider-neutral provenance. Use when a team member changes models, connects DeepSeek or another provider, or needs to know which Film OS tasks the current runtime may safely perform.
---

# Film Model Router

Read `../../../MODEL_POLICY.yaml` and the current production authority before assigning work. Provider and model names are metadata, never proof of capability or authority.

For a production project, run the local authority check first. A verified director may maintain `governance/MODEL_RUNTIME.yaml`; a contributor must place `MODEL_RUNTIME.yaml` only inside the contributor's current proposal bundle. Never place API keys, tokens, endpoint credentials, or hidden reasoning in a report.

Assess the combined runtime, not the language model alone: model capabilities plus the Codex client, compatible harness, filesystem access, and available tools. Prefer observable checks over claims:

- read one permitted project file;
- produce a small valid structured record;
- create a disposable file only in an authorized proposal area when write testing is necessary;
- run one harmless validator when tool execution is claimed;
- inspect an actual test image before marking vision as supported.
- inspect a live Blender scene through the configured controller before marking Blender scene control as supported;
- obtain and inspect a real viewport or render capture before marking viewport capture as supported.

Do not mutate canonical content during preflight. Record each capability as `supported`, `unsupported`, or `unknown`; unknown is treated as unsupported. Use `templates/MODEL_CAPABILITY_REPORT.yaml`, then run `python3 tools/check_model_compatibility.py --report <path> --task <profile>` for the requested task profile.

If required capabilities are missing, follow the policy fallback. A text-only model may draft scripts and prompts but may not claim visual inspection. A runtime without file or tool access may return a human-readable draft but may not claim it wrote, validated, packaged, or synchronized anything.

For Blender previz, `python3 tools/check_blender_runtime.py` is only a read-only prerequisite check. It cannot prove a live connection. Mark `blender_scene_control` and `viewport_capture` supported only after observable live tests; otherwise allow a Previz Card/plan but do not claim Blender outputs.

Every routed deliverable must retain provider, model ID, client, capability-report status, and canonical base commit. These fields provide traceability only. They never convert AI output into canon and never replace director approval.
