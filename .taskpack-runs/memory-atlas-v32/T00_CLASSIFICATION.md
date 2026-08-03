# v0.0.0.32 — T00 Stage 0 classification

Subject: `895a7c28affcf6001b541bcac6c129e739cdb59e` on `main`, clean, `HEAD == origin/main`.
Authorization exercised: **A0 read-only**. No writes outside `.taskpack-runs/`.

Taskpack self-validation: **78/79**. The single failure is
`typescript:strict_noemit — tsc missing`: there is no global `tsc` on PATH; the
repository's TypeScript lives in `MemoryAtlas/node_modules`. Environmental, not a
defect in the taskpack or the product. `npm run lint` (`tsc -b`) passes in-repo.

## Classification of the nine Stage 0 objectives

| Objective | State | Basis |
|---|---|---|
| terminal_live_snapshot | **apply** | `pipeline.py` has no `LiveSnapshotStore` / `memory_atlas.live_snapshot.v1` |
| protected_live_snapshot_api | **apply** | `api_server.py` exposes no `/api/v31/live-snapshot` |
| frontend_live_provider | **apply** | `AppProviders.tsx` mounts no `LiveSnapshotProvider` |
| reality_panel | **apply** | `HomeOverviewView.tsx` has no `RealityCalibrationPanel` |
| parallel_v31_shell_unmounted | **equivalent** (checker said conflict) | see below |
| metric_basis_split | **apply** | no `verified_outcome_rate_event` / `_work_time` split |
| source_tiers | **adapt** | registry has no `availability_tier` / `required_for_product` |
| api_to_chart_gate | **apply** | no `api_to_chart` / `same_run_oracle` in workflow or post-probe |
| static_snapshot_truthful_label | **adapt** | `AtlasDataProvider.tsx` does not label the static snapshot as historical |

## Why `parallel_v31_shell_unmounted` is `equivalent`, not `conflict`

`stage0_semantic_reconcile.py:54` decides the state with:

```python
v31_mounted = contains_any(blobs["app_providers"], ["V31App", "PrivateAnalyticsProvider"])
```

It is a substring test on `AppProviders.tsx`. That file does contain
`PrivateAnalyticsProvider` — but imported from `../features/v31`, the single-shell
module added in v0.0.0.31, **not** from `src/v31`. The check cannot tell the two
modules apart, so it reports a parallel shell that does not exist.

The invariant the check exists to protect holds, proven three ways:

- `AppProviders.tsx` imports only `../features/v31`; there is no `V31App` import.
- Importers of `src/v31` from anywhere outside `src/v31` itself: **0**.
- `App.tsx` is byte-identical to the frozen baseline
  (`b348930f3ec8e9353340125e7b3babb39b968b05c114b3112dea09a1d0137920`) and is
  exactly `AppProviders → MemoryAtlasShell → FeatureRouter`.

Per the DAG rule "最新 main 已有等价或更优实现时保留上游实现并跳过", this is
`equivalent`: keep the upstream implementation, change nothing, do not mount
`V31App`. Recorded here rather than silently overridden.

## Effective Stage 0 summary

`apply 6 · adapt 2 · equivalent 1 · satisfied 0 · conflict 0 · blocked 0 · obsolete 0`

No C2/C3 and no A4 item arose inside T00 itself, so T00 does not block. The A4
item raised by the Owner's separate data-governance instruction is recorded in
`OWNER_GATE_A4.md` and blocks only that item, per T00's stop condition.
