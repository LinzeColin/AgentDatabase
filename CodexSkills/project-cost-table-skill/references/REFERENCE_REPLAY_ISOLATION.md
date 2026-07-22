# Reference Replay Isolation Contract

## Purpose and authority

`reference-replay` reproduces a hash-bound historical report for private audit and display. It is not a current-source calculation, a formal workbook, a company approval record or evidence that `calculate` is ready.

Reference values may never repair, seed, calibrate or backsolve a calculate result. The mode boundary is both an import boundary and a data-flow boundary.

## Required preflight

Every replay run must validate all of the following before exposing any reference values:

1. a new, absolute, non-existing private output directory;
2. a single-link regular private import manifest with the exact v1 field set;
3. a single-link regular baseline whose full SHA256 equals the manifest binding;
4. the locked expected project count;
5. each baseline-bound relative PDF path, PDF security preflight and full SHA256;
6. integer-minor-unit values, strict baseline shape, unique project/PDF bindings and exact line-item sum.

A missing or conflicting requirement produces diagnostics and a supplement/qualified-evidence/scope-reduction/stop next step. Silence is not permission. Baseline/PDF hash, file safety, integer money and fidelity are non-waivable; user authorization cannot convert them into success.

## Fidelity and source quality

Replay fidelity and source quality are separate:

- `replay_fidelity_status=EXACT` means every bound PDF digest matches and every line sum equals the bound source total.
- `source_quality_status=CONSISTENT` means the source profit equals independently recomputed revenue minus cost.
- `source_quality_status=SOURCE_ARITHMETIC_DIFFERENCE` preserves both source and recomputed profit plus their delta. It is an expected source-quality observation, not a replay failure.
- Hash or line drift produces `BLOCKED_HASH` or `BLOCKED_LINE_DELTA`; reference values are not emitted.

Missing optional fields remain missing and explicit `null` remains `null`. The replay layer does not guess notes, percentages, categories or amounts.

## Mode isolation

- Calculate modules must not import `project_cost_table.reference_replay` or the replay CLI.
- Replay code must not import accounting-basis aggregation, formulas, payroll, adjustments, named Metrics, workbook generation or final-generation adapters.
- Replay artifacts declare `calculation_status=NOT_EVALUATED`, `generation_status=NOT_GENERATED` and `reference_values_available_to_calculate=false`.
- Replay emits no `.xlsx` and no `INTERNAL_PROCESS_HANDOFF.md`.
- A private baseline file placed beside a calculate request cannot alter calculate request fields, imports or results.

These rules are covered by AST inspection, isolated subprocess imports and behavioral regression tests.

## Output contract

Success writes private replay results, input sufficiency, validation, review tasks, traceability, performance/privacy summaries, run manifest, human/machine indexes and a detached seal. Blocked and failed runs omit reference values and publish only diagnostics and controls.

All paths in `run_manifest.json`, `OUTPUT_INDEX.md` and `output_index.json` are absolute. The CLI repeats:

```text
OUTPUT_DIR: /absolute/private/run
PRIMARY_OUTPUT: /absolute/private/run/reference_replay_results.json
OUTPUT_INDEX: /absolute/private/run/OUTPUT_INDEX.md
```

Publication is atomic and no-replace. If an unexpected error occurs after staging begins, partial staged files are removed before sealed failure evidence is generated.

## R10 acceptance boundary

The locked private acceptance set replayed 8/8 projects and 68/68 line items exactly, with all bound PDF hashes matching. Known source arithmetic differences were preserved separately. Calculate import/data-flow access remained zero.

Manual PDF QA rendered every bound page. Ten pages were fully readable; three source pages carried presentation warnings: one overflow marker, one sparse residual page and one source-blank page. The blank page was independently confirmed to contain neither text nor embedded images. These are source presentation limitations, not renderer loss and not permission to infer missing values.

R10 remains development-only. R11 must independently run current `calculate` inputs and verify the exact blocker contract without importing reference values.
