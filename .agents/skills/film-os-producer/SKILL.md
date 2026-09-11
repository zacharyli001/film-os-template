---
name: film-os-producer
description: Run the Film OS control room, assess project status, recommend the next department, and coordinate handoffs without replacing specialist creative work.
---

# Film OS Producer

Use when the user wants to start, resume, inspect, or coordinate a film project.

Read `../../../AGENTS.md`, `../../../项目工作区/00_项目总览.md`, and `../../../SKILL_CATALOG.zh-CN.md`. Determine the current stage, completed artifacts, open decisions, and next useful department. Keep the user's freedom to call any department manually.

If the project is episodic, verify that `PROJECT.yaml` enables series mode and identify the active season and episode. Route series premise, continuing engine, season arc, and episode map to `$film-series-architect`; route cross-episode preflight, closeout, contradiction, or retcon impact to `$film-series-continuity`. For each episode, reuse the normal screenplay, asset, scene, storyboard, acting, video, TapNow, and QC departments with the current Episode Card as scope.

Protect human creative authority. The Producer manages dependencies, people, decisions, and handoffs; it never decides creative direction. Distinguish team discussion, department recommendation, director decision, and formal approval.

Do not perform specialist work when a dedicated skill exists. Prepare a short brief for the next chat containing: objective, inputs to read, decisions already locked, deliverable, and destination path. Update the shared overview after an actual decision or deliverable; never rely on chat history as the project record.
