# Project Cost Table Skill Handoff

## Current objective and status

Task Pack `1.2.0` Runs R0–R12 are implemented for product `0.2.0`. The fail-closed Skill workflow is release-ready; global installation is `MACHINE_LOCAL_EXTERNAL`: R12 did not perform it, and any machine-level completion must be proven after Git remote/main parity by that machine's discovery and sealed install receipt.

This product release is not a current business-result approval. Current calculate remains `NEEDS_USER_INPUT / BLOCKED_NON_WAIVABLE / BLOCKED_SOURCE / BLOCKED_DIAGNOSTICS_GENERATED`, with no final workbook and no internal-process handoff.

## Immutable operating decisions

- Every operation starts with input sufficiency. Missing or conflicting input requires an auditable supplement, qualified alternate evidence, actual scope reduction or a decision to remain blocked. Silence is not permission; non-waivable inputs cannot be omitted while retaining the affected Metric.
- Every final, blocked or failed run reports absolute `OUTPUT_DIR`, `PRIMARY_OUTPUT` and `OUTPUT_INDEX` locations.
- Actual project cost always carries both `JOB_COST_INCURRED` and `GL_RECOGNIZED_COGS`; the two views are never collapsed into an unnamed total.
- When real calculate inputs and all gates pass, the R9 path directly generates the final values-only workbook. The Skill does not assign a finance owner/authorized person and does not manage company approval; the calling Codex/operator continues the existing process outside the Skill.
- Reference replay is private audit/display only. It cannot seed, repair or calibrate calculate.
- Expected-block success proves truthful blocking only. Production exit `3` remains a business block; harness exit `0` means only exact expectation match.
- Raw inputs are read-only. Source, contract, expectation and evidence changes are append-only and require a new binding; no snapshot or expected value is silently overwritten.

## R12 release implementation

- Added strict `config/performance_budgets.yml`, `schemas/performance_budget.schema.json` and `schemas/performance_summary.schema.json`.
- Added `src/project_cost_table/release.py` with exact factor comparison, independent-process samples, same-scope consistency, full-digest-once checks, candidate-pair/global-matching/cache gates, aggregate-only evidence, code/budget binding, atomic publication and detached-seal verification.
- Added `scripts/run_release_benchmark.py`. One cold process and three subsequent processes each rescan the bound snapshot and fully hash every selected non-reference source; application digest caching is forbidden.
- Added `scripts/validate_skill_package.py` for release/version/model/formula/traceability/schema/test-matrix and optional working-tree/staged private-boundary checks.
- Added `config/release_test_matrix.yml`, adversarial/property/metamorphic release tests and `references/RELEASE_PERFORMANCE_AND_OPERABILITY.md`.
- Released governance, model/formula/parameter registries and traceability at `0.2.0`; `GLOBAL_INSTALL` is machine-local external state and was not performed by R12.

## Verified R12 evidence

- Full pytest with explicitly injected Codex bundled spreadsheet runtime: `285 passed, 1 skipped, 0 failed`. The only skip is the known host filesystem Unicode-normalization condition; both workbook rendering/final-generation tests ran rather than skipped.
- Independent unittest: `286 run, 1 skipped, 0 failed` with the same host condition.
- The first full-suite release attempt correctly failed because a new privacy test contained a forbidden private-root token as contiguous public test text. The test corpus was repaired; the boundary then passed. This is retained as evidence that the scanner is active.
- Bound snapshot performance: `PASS`, one cold plus three subsequent independent processes, 58 metadata entries, 9 selected sources and 9 full digests per process; each selected source was fully hashed once per process. Total across four processes was 36 digests and 77,773,080 bytes. Application cache hits, candidate pairs, parsed business files/members and emitted rows were zero because current business parsing remains blocked.
- Cold wall time was 20,397,333 ns and cold peak RSS 29,409,280 bytes. Maximum subsequent wall time was 17,866,084 ns and peak RSS 32,129,024 bytes, both within the exact `1.50×` ceiling. The summary schema, code fingerprint, budget digest and detached seal reverified.
- Private reference replay reran under `0.2.0`: 8/8 projects and 68/68 line items exact, with three source arithmetic differences preserved, no calculate data flow, no workbook and no internal-process handoff.
- Direct current production reran under `0.2.0` and returned exit `3` with the exact nine reviewed generic blockers. An independent second-production harness returned exit `0` only as `EXPECTED_BLOCKED`. Both production directories and the harness directory had valid seals and no final-looking workbook/handoff.
- The current raw metadata binding and all selected source full digests remained exact during performance and private regression runs; no raw write occurred.

## Residual business blockers and limits

- Current full-scope calculation still needs or must resolve: v3 manifest, canonical identity evidence, active Kingdee reader profile, 5001/6401/WIP accounting-basis policy, payroll plus approved time, fully loaded payroll policy, project tax policy/direct ledger, capital-interest policy and deterministic payment-to-project mapping.
- The real business parse/final-calculate performance baseline is intentionally `NOT_EVALUATED_BLOCKED_SOURCE`; release performance covers the exact current source-binding gate. Synthetic tests cover the real bundled workbook runtime. Do not extrapolate a real end-to-end calculate throughput claim.
- Normalized facts are produced once at the reader stage and reused by downstream Metric views in one run; the current product uses no application digest cache. If a future persistent normalized cache is added, it must remain private, hash-bound and must not replace final-generation source rehash.
- Reference presentation defects and historical source arithmetic differences remain source evidence, not permission to infer or overwrite values.

## Git and installation boundary

R12 close requires the staged public-boundary scan, canonical package validator, Git overlap review, commit/push/merge evidence and clean remote/main parity. Those facts are recorded outside the public package in the sealed R12 acceptance evidence; do not infer them from this handoff alone.

On a machine without a valid install receipt, the next and only allowed post-parity run is global Skill installation from the clean main repository followed by discoverability and behavioral parity validation. A machine with a valid receipt verifies it instead of reinstalling. Never copy private runtime, raw inputs or release evidence into the global Skill package.

A global Skill copy has no `.git` metadata. When it is registered at `$CODEX_HOME/skills/project-cost-table-skill`, `run_input_preflight.py` treats the validated module root as the protected public boundary, permits outputs only outside it or under its local `private_runtime`, and rejects incomplete/tampered or unregistered standalone copies before creating runtime state. Repository checkouts continue to use the discovered Git root.
