---
name: codex-dev-orchestrator
description: Use when the user asks to plan, scope, package, or deliver a multi-step software/product/system build, especially PRD, MVP, or controlled implementation workflows. Classify the request first, then load only the matching reference. Do not use for narrow bug fixes, simple edits, command output, or ordinary Q&A.
---

# Codex Dev Orchestrator

Use this skill as a token-light router for controlled multi-step software,
product, or system delivery. Keep the main file small: classify the request,
load only the matching reference, and avoid turning small edits into heavy
research or packaging workflows.

Follow the user's project instructions and personalization for general
engineering discipline, verification, reporting, and failure handling.

## Classify First

Before loading details, classify the active request:

- `PLAN_SCOPE`: PRD, MVP scope, roadmap, requirements, user stories,
  information architecture, acceptance criteria, or stop conditions.
  Read `references/planning-prd-mvp.md`.

- `CONTROLLED_RUN`: Codex-ready Task Pack, run contract, bounded implementation
  stage/phase/task, package handoff, delivery evidence, or executing an
  already-approved plan. Read `references/task-pack-and-run-contract.md`.

- `SMALL_EDIT`: typo, narrow bug fix, simple file edit, command output,
  translation, ordinary Q&A, or local diagnosis that does not need product
  orchestration. Do not use this workflow; answer directly.

If the request is ambiguous, choose the lightest viable classification. Ask one
short question only when the next action cannot be inferred safely.

## Core Gates

- For planning, produce concise structured outputs and avoid long free-text
  interviews.
- For implementation, work from one bounded run contract at a time.
- Before mutating files for a controlled run, state a compact execution contract:
  goal, scope, non-goals, files, validation, risks, rollback, stop condition.
- If repository identity, task scope, handoff state, or acceptance criteria
  conflict, stop and label facts as `VERIFIED`, `INFERRED`, or `UNKNOWN`.
- Do not claim completion without the requested validation evidence.

## Output Discipline

Keep chat summaries short. Put long PRDs, task packs, run contracts, acceptance
tables, and handoff material in files when the user asks for durable artifacts.
