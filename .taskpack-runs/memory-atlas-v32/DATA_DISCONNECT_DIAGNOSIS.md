# Why memoryatlas shows July data — measured, 2026-08-04

Read-only diagnosis. Corrects my own earlier claim.

## My earlier explanation was wrong

I reported that `memory_atlas.json` was stale because the builder had not run
since 2026-07-16. That is not the cause. Running
`build_memory_atlas_data.py --database-dir OpenAIDatabase` against current data
produces **byte-identical output** — same 1,035,746 bytes, same 6 active
memories, 156 nodes, 720 edges, 379 conversations. Only `generated_at` moves.

The snapshot is frozen because **its input is frozen**:

| Input | Files changed since 2026-07-20 | Newest |
|---|---|---|
| `OpenAIDatabase/data/memory` | **0** | Jul 17 |
| `OpenAIDatabase/data/processed` | **0** | Jul 17 |
| `OpenAIDatabase/data/derived` | 15 | Jul 24 |

Re-running the builder, or scheduling it, would change nothing but a timestamp.

## The actual shape of the problem: two disconnected planes

**Plane A — what the original ten views read**

```
OpenAIDatabase/data/  →  build_memory_atlas_data.py  →  memory_atlas.json  →  10 views
```
Frozen since 2026-07-17. Model: an atlas **graph** — memories, themes, nodes, edges.

**Plane B — what the three v31 views read**

```
Codex capture → R2 canonical (122,080 events) → Private-Database facts
             → memory_atlas_private_analytics.json → /api/v31/status → 3 views
```
Live. Measured on the origin at 2026-08-03T21:35:15Z:
`run.state = REBUILT_FROM_AUTHORITIES`, **112,290 events**, 10 source coverages,
29 failure-compound incidents, regenerating about every 15 minutes.

Both planes already reach the browser. They simply never meet: the ten original
views consume A, the three new views consume B.

## Why this is not a configuration fix

The planes use **different data models**. Plane B holds normalized *events*
(`event_id`, `activity`, `outcome_state`, `effort_minutes`). Plane A holds a
*graph* (`nodes`, `edges`, `memory_tier`, `theme`). Feeding B into A is not a
path change or a cron entry — it needs an adapter that maps events onto the
graph model.

That adapter is exactly what v0.0.0.32 T03 specifies (`live_snapshot_adapter.py`,
`live_snapshot_store.py`). The Owner has fenced v0.0.0.32 off as a separate
task, so it is **not** started here. This document records the measured cause so
that work starts from fact rather than from my earlier wrong explanation.

## What is true right now

- The product is not "not synced". It is showing a **genuine historical slice**
  from Plane A while a **live plane** runs beside it.
- Nothing in the UI says so. The topbar shows `快照生成时间` but nothing marks
  the ten views as historical, so "6 memories" reads as current truth.
- v0.0.0.32 Stage 0 independently classified this as
  `static_snapshot_truthful_label: adapt` against
  `MemoryAtlas/src/providers/AtlasDataProvider.tsx` — the same conclusion from a
  different direction.

## Bounded options, for the Owner to pick

1. **Label honestly** (small, no v0.32 scope): mark the ten views as a historical
   slice with its real cut-off, and surface the live counts that already exist in
   Plane B. Stops the product implying the July numbers are current. Does not
   make the graph current.
2. **Bridge the planes** (this is v0.0.0.32 T03): build the event→graph adapter so
   the ten views render current data. Correct end state; belongs to that task.
3. **Restart Plane A's source**: find why `OpenAIDatabase/data/memory` and
   `data/processed` stopped receiving writes on Jul 17 and resume that feed.
   Requires knowing what used to write there — not determined here.

Option 3 was not investigated far enough to recommend; it is listed because it
may be the cheapest real fix if that writer still exists.
