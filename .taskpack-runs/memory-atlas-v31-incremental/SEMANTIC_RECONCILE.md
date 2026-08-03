# Memory Atlas v0.0.0.31 — Semantic Reconcile ledger

Taskpack: `MemoryAtlas_v0.0.0.31_CLAUDECODE_INCREMENTAL_TASKPACK_v0.0.0.5`
Baseline: `origin/main` = `d8e343c7590ed41344522abb4f63a9bf32c67f62` (clean, HEAD == origin/main at Stage 0)

The taskpack overlay contains 66 files. Byte comparison against the moving `main`:
**18 identical, 17 missing, 31 different.** Nothing was overwritten.

## Verdicts

### SATISFIED (18) — identical bytes, no action
`memory_atlas_private/{__init__,__main__,access_auth,action_queue,api_server,cli,hashing,manifest,normalization,object_store,sqlite_snapshot}.py`,
`ops/memory-atlas/{backup.sh,configure_cloudflare_edge.py,docker-compose.yml,restore-drill.sh}`,
`ops/memory-atlas/systemd/{action-worker,reconcile,selfheal}.timer`.

### APPLY (17) — absent on main, added verbatim
- `MemoryAtlas/src/features/v31/` (10 files: 3 views, theme provider, private-analytics provider, theme controls, shared, contracts, index, CSS)
- `MemoryAtlas/scripts/validate_memory_atlas_v31_{incremental,incremental_browser,typescript}.cjs`
- `ops/memory-atlas/SOURCE_RUNNER_POLICY.md`, `ops/memory-atlas/source-runner/{run_due,manage_crontab}.py`

The CSS was then **extended** (see ADAPT below); everything else was applied as shipped.

### OBSOLETE (30) — main already carries a strictly newer implementation; taskpack bytes discarded
In every one of these the repo file is a superset of the candidate. Sampled proof:
- `memory_atlas_private/models.py`: repo adds `github_private_release_backup`
- `memory_atlas_private/restore.py`: repo adds `"state": "PASS"` to the restore receipt
- `ops/memory-atlas/start.sh` / `stop.sh`: repo manages `memory-atlas-api-proxy.socket` and probes `:8766` + `10.0.0.1:18766`; the candidate still probes the retired `:8765`
- `test_memory_atlas_private_v31.py`: 81.7 KB in repo vs 43.4 KB in the pack (81 tests, all green)

Overwriting any of these would have removed the api-proxy socket, the GitHub private release backup and half the regression suite.

### ADAPT (6) — intent carried into the evolved structure
| Target | Why not verbatim | What was done |
|---|---|---|
| `src/types.ts`, `shared/atlas/constants.tsx`, `app/routeRegistry.tsx`, `app/AppProviders.tsx`, `app/MemoryAtlasShell.tsx` | patch targets exist and have moved on | hand-applied the same five patches; nav labels follow the repo's question-phrased `uiCopy.navigation.views` convention instead of the pack's hard-coded strings |
| `MemoryAtlas/package.json` | the pack's `patch_package` rewrites the whole 17 KB file through `json.dumps` | added only the three `validate:v31:*` scripts, formatting untouched |
| `src/features/v31/v31Incremental.css` | the pack's own comment: *"Claude Code must extend them for any moving-main component discovered during browser acceptance"* | a real-browser audit over all 13 routes found 64 element families still painting near-black in light mode and 32 painting light text on light; both were closed to 9 and 7, the residue being the visualisation canvases and accent chips that must stay as they are (see `LIGHT_MODE_AUDIT.md`) |
| `MemoryAtlas/scripts/validate_memory_atlas_v31.cjs` | `UI-008` asserted `app.includes("V31App")`, i.e. the architecture the owner has since forbidden — **it was already failing on `origin/main`** | all twenty UI-0xx guarantees kept, re-pointed from the unreachable `src/v31/` wrapper to the shipped `src/features/v31/`; `UI-007` now proves the old asset is still on disk |
| `ops/memory-atlas/source-registry.json` | repo has `github_private_mirror` + `local_payload_retention` the pack lacks; pack would demote `codex_automations` to optional | added only the pack's `source_runner` policy line. `codex_automations` stays `required: true`: `~/.codex/automations` exists with 15 entries, so the stricter gate is satisfied and weakening it would hide a future disappearance |
| `.github/workflows/memory-atlas-v31.yml` | the pack ships a **second** workflow pinning actions by floating tag (`@v4`, `@v5`) | folded the new gates into the existing workflow, which pins every action by SHA. `verification_policy` enforces `unpinned_ci_action_count == 0`, so the pack's workflow would have failed the repo's own governance gate |

### Newly registered (2) — required by the repo's governance, not by the taskpack
- `OpenAIDatabase/tests/test_memory_atlas_source_runner_v31.py` added to `verification_policy.json` integration tier and the `82 → 83` counts in `test_verification_policy.py`; an unowned test file is a hard `FAIL` for `validate:whole-project`.
- `audit_memory_atlas_visual_acceptance.py` pinned `visualFocusViews` as one frozen literal, so adding any view broke `contribution_grid_uses_full_scene_layout` and, through it, the whole acceptance audit. The check now asserts membership of the original nine instead of the exact array — same guarantee, additive-safe.

### CONFLICT / BLOCKED
No CONFLICT. Blocked items are environment-level and are recorded in `BLOCKED.md`; none of them is a code conflict.

## Deliberate non-actions

- `MemoryAtlas/src/v31/**` (9 files, 726 lines) is **retained untouched**. It is orphaned — nothing outside the directory imports it — but it is a v0.0.0.31 asset and deleting it is forbidden. It still type-checks under `tsc -b`.
- `ops/memory-atlas/automation_lifecycle.py` keeps its `install-new` command even though `SOURCE_RUNNER_POLICY.md` says there is deliberately none. The repo implementation is the newer one and removing a command is not additive; the divergence is recorded rather than resolved.
- `MemoryAtlas/public/` does not exist in this repository. It is inventoried as absent, before and after, rather than created.
