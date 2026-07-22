# Development Log

## 2026-07-17 — R1 Public/private skeleton

- Contract: Task Pack `1.2.0`, proposed product `0.2.0`, Run `R1` only.
- Status: implemented; acceptance evidence is produced outside the repository after validation.
- Added a development-only Skill entrypoint and module skeleton.
- Added default-deny artifact classification for `PUBLIC_SAFE`, `PRIVATE_RUNTIME`, and `RAW_SOURCE` planes.
- Added working-tree and staged-index scanners; staged content is read from the Git index rather than the mutable working tree.
- Added private runtime initialization for `cache`, `runs`, `decisions`, and `reference_baseline` without tracked placeholders.
- Added public synthetic tests and governance registries.
- Added explicit ignores for private runtime, private seed, pytest cache, and Python cache.
- Reused canonical Task Pack feature, acceptance, and model identifiers; no parallel identifier namespace was created.

### Deliberately not implemented in R1

- Decimal money types, archive/path hardening, source readers, project identity, deduplication, payroll, formulas, workbook generation, CLI execution, performance profiling, release, and global installation.
- No raw or private finance input was opened, copied, transformed, or embedded.

### Planned run history

| Run | State at R1 close | Purpose |
| --- | --- | --- |
| R0 | complete | Repository and governance preflight |
| R1 | complete | Public/private skeleton |
| R2–R12 | not_started | Must execute sequentially, one Run Contract per iteration |
| Global install | not_started | Allowed only after R12 release gates |

## 2026-07-17 — R2 Money, path, and file safety

- Contract: Task Pack `1.2.0`, product `0.2.0-dev.2`, Run `R2` only.
- Status: complete; full R2 acceptance evidence is produced outside the repository.
- Added strict CNY `Decimal` to integer-minor-unit parsing, explicit blank policies, explicit rounding layers, negative-zero audit state, scale/overflow ceilings, and environment-independent rounding context.
- Added governed input containment and rollback-safe atomic file/directory publishing with no-overwrite behavior and publish-race protection.
- Added ZIP path/type/resource/CRC gates and recursive nested archive verification that requires explicit private scratch.
- Added OOXML active-content and ambiguity inspection, explicit unsupported-XLS blocking, conservative PDF container gates, and spreadsheet text injection escaping.
- Added public synthetic malicious fixtures generated only in temporary test directories; no binary fixture is tracked.
- First test run exposed macOS lexical `/var` versus resolved `/private/var` alias handling. The path resolver now aligns trusted lexical and real roots without weakening traversal or symlink checks.
- Completion audit added recursive archive budgets, PDF active-content gates, autorun/DDE defined-name checks, external Decimal-context invariance, and atomic publish-race preservation.

### Deliberately not implemented in R2

- Source manifest/selection, source readers, project identity, event lifecycle, dedup/linking, payroll/formulas, Metrics, workbooks, private regression, performance release gate, Git release, and global installation.
- No raw or private finance file body was opened, copied, transformed, or embedded.

### Run history at R2 implementation

| Run | State | Purpose |
| --- | --- | --- |
| R0 | complete | Repository and governance preflight |
| R1 | complete | Public/private skeleton |
| R2 | complete | Money, path, file, and OOXML safety |
| R3–R12 | not_started | Must execute sequentially, one Run Contract per iteration |
| Global install | not_started | Allowed only after R12 release gates |

## 2026-07-17 — R3 Input gate, manifest and inventory

- Contract: Task Pack `1.2.0`, product `0.2.0-dev.3`, Run `R3` only.
- Status: complete; full R3 acceptance evidence is produced outside the repository after validation.
- Added strict operation-request, input-manifest, sufficiency-report and input-resolution contracts plus public empty templates.
- Added metadata-first inventory scanning, opaque normalized source IDs, single-link/type checks, private full inventory and aggregate-only public summary.
- Added deterministic manifest selection with explicit selection even for one candidate, complete digest revalidation, schema/reader/security locks and mtime-independent business fingerprint.
- Added mode/Metric/basis-specific input sufficiency, fully loaded payroll input dependencies, one compact missing-input matrix and fail-closed resolution rules.
- Explicit handling now binds the previous sealed incomplete report, resulting request, manifest and requirements; it writes the exact resolution into the new sealed output directory.
- Added immutable source/candidate/decision/validated-fact lineage envelopes without company approval fields.
- Added atomic input-gate reports, optional resolution evidence, absolute output locators/indexes and detached seals; no R3 operation creates a final-looking workbook.
- A focused audit found and fixed macOS `/var` alias containment, stale-resolution binding, relaxed reference-report slot flags, Unicode-normalized source-ID collisions and a false security-capability check based only on module-file existence.

### Deliberately not implemented in R3

- Project identity resolution, business source readers, event lifecycle, accounting bridges, dedup/linking, payroll allocation, formulas, Metrics, workbooks, private regression, performance release gate, Git release and global installation.
- No raw or private finance source body was opened, copied, transformed or embedded.

### Run history at R3 implementation

| Run | State | Purpose |
| --- | --- | --- |
| R0 | complete | Repository and governance preflight |
| R1 | complete | Public/private skeleton |
| R2 | complete | Money, path, file and OOXML safety |
| R3 | complete | Input sufficiency, manifest, inventory and source layers |
| R4–R12 | not_started | Must execute sequentially, one Run Contract per iteration |
| Global install | not_started | Allowed only after R12 release gates |

## 2026-07-18 — R4 Project identity master and conflict gate

- Contract: Task Pack `1.2.0`, product `0.2.0-dev.4`, Run `R4` only.
- Status: complete; full R4 acceptance evidence is produced outside the repository after validation.
- Added a strict effective project identity master keyed by canonical project, legal entity, WBS/cost code and cutoff date, with evidence-bound contract, source-system and mapping-resolution aliases.
- Added deterministic match priority and prohibited fuzzy final mapping. Project code, name, customer and free text produce candidates only, including when an alias text matches exactly.
- Added indexed effective-period and alias conflict detection plus hard blockers for multiple matches, contract/project disagreement, identifier disagreement, cross-entity ambiguity, stale mappings, incomplete keys and unmapped records.
- Added append-only, physically separated private approved, candidate/non-active and historical identity records plus `P0` review tasks; public identity summaries contain aggregate counts only.
- Added a cross-entity view that preserves legal-entity, WBS/cost-code and identity-record dimensions rather than destructively merging them.
- Added locked policy, project-record/review-task Schemas, an empty public template, operating reference and public synthetic tests.
- Kept `APPROVED` explicitly scoped to evidence-qualified data mappings and required every such mapping to bind at least one contract and one hash-bound evidence reference. No finance owner, authorized person, assignee or company approval workflow was added.

### Deliberately not implemented in R4

- Business source readers, period/accounting bridges, event lifecycle, dedup/linking, payroll allocation, formulas, Metrics, workbooks, private regression, performance release gate, Git release and global installation.
- No raw or private finance source body was opened, copied, transformed or embedded. The known private identity conflict remains unresolved and must block a later calculate run until qualified evidence is supplied.

### Run history at R4 implementation

| Run | State | Purpose |
| --- | --- | --- |
| R0 | complete | Repository and governance preflight |
| R1 | complete | Public/private skeleton |
| R2 | complete | Money, path, file and OOXML safety |
| R3 | complete | Input sufficiency, manifest, inventory and source layers |
| R4 | complete | Effective project identity and conflict gate |
| R5–R12 | not_started | Must execute sequentially, one Run Contract per iteration |
| Global install | not_started | Allowed only after R12 release gates |

## 2026-07-18 — R5 Kingdee reader and accounting-basis bridge

- Contract: Task Pack `1.2.0`, product `0.2.0-dev.5`, Run `R5` only.
- Status: complete; full R5 acceptance evidence is produced outside the repository after validation.
- Added a dependency-free, value-only OOXML reader after the existing R2 preflight. It binds the R3 selected source digest, reader version, schema fingerprint, exact sheet/header layout and canonical field mapping before emitting any record.
- Added a manifest-selected Kingdee bundle reader that binds the exact workbook inventory and each member digest/disposition/evidence. It independently preflights every XLSX, reads every included XLSX, hard-blocks any included legacy XLS, and rejects partial success.
- Required an exclusive empty private scratch directory outside the read-only input root and retained opaque container/member lineage without exposing paths or hashes in public summaries.
- Preserved entity/project/WBS/contract source keys, account, voucher line, three date types, debit, credit, balance, currency, source status and row kind. Missing remains null; strict money and governed ISO/Excel-serial dates fail closed.
- Added per-source row/empty/error and debit/credit/balance controls, deterministic normalized business digests and aggregate-only public status output. Harmless ZIP metadata and row enumeration do not change the reader business fingerprint.
- Added evidence-backed, effective status, row-kind, account, period and valuation policies. Public policy/reader files are non-runnable templates; active private policies require hash-bound evidence.
- Added separate `JOB_COST_INCURRED` and `GL_RECOGNIZED_COGS` views. The WIP closing equation and the 5001-to-6401 transfer control both require zero-cent deltas, preventing lifecycle transfers from being double-counted.
- Required one effective R4 identity + contract binding for every included/control ledger row and retained account-level controls beside cross-account bridge groups.
- Added posting-date cutoff, source-classification conservation and content-addressed, scope/period-bound closed-period snapshots. Changed closed facts require a superseding `restate` run and never overwrite history.
- Added public synthetic XLSX/bundle, policy, identity, cutoff, restatement, malformed-source, unknown-semantics, non-CNY, missing-identity and non-zero-bridge tests. Bundle tests cover all-approved-member conservation, unclassified workbooks, member digest drift, formula blocking, legacy-XLS full-slot blocking, evidence-qualified exclusion and scratch isolation. No private finance body was opened.

### Deliberately not implemented in R5

- RedCircle/contract/revenue/cash readers, event linking, deduplication, payroll/tax/interest/management formulas, named Metrics, workbooks, private replay/current regression, release/performance gates, Git release and global installation.
- R5 basis views are `R5_RECONCILED_NOT_FINAL`; they cannot be used as a formal operating, performance or payroll artifact.

### Run history at R5 implementation

| Run | State | Purpose |
| --- | --- | --- |
| R0–R4 | complete | Governance, safety, input, lineage and identity foundations |
| R5 | complete | Kingdee value-only reader, WIP bridge, period/status/account controls |
| R6–R12 | not_started | Must execute sequentially, one Run Contract per iteration |
| Global install | not_started | Allowed only after R12 release gates |

## 2026-07-18 — R6 Lifecycle source readers and exact export duplicates

- Contract: Task Pack `1.2.0`, product `0.2.0-dev.6`, Run `R6` only.
- Status: complete; full R6 acceptance evidence is produced outside the repository after validation.
- Extended the R3 manifest with backward-compatible, explicit multi-source locks per slot. Every selected source retains its own opaque ID, SHA256 and file identity, while the slot still has one locked reader/schema/period contract.
- Added one dependency-free value-only XLSX engine with four hard-separated reader identities: project invoice, payment, contract/change and collection. Active private profiles must bind exact headers, fields, dates, required values, status/type/row semantics and hash-bound evidence.
- Added immutable source records and economic-event candidates. Billing emits only `REVENUE/BILLED`, payment only `CASH_OUT/PAID`, collection only `CASH_IN/COLLECTED`, and contract/change only `REVENUE/CONTRACT_VALUE` or `COST/COMMITMENT`.
- Kept every candidate at `PENDING_IDENTITY / NOT_EVALUATED_R6`; free text cannot assign a project and no reader can grant final Metric inclusion.
- Preserved gross/net/tax, source arithmetic deltas, seven date families and source statuses. Timestamps are not silently truncated, and a reversed source event requires both the original-source key and reversal date.
- Added row and business/control amount-partition conservation. Unknown headers/status/event types/row kinds, invalid money/dates, non-CNY, dangerous OOXML and legacy XLS fail closed without a partial event result.
- Added exact whole-export duplicate detection using locked profile semantics and a normalized business-record multiset. Exact aliases count once, retain all source refs and do not change the business fingerprint; changed status/amount and partial overlap remain distinct for R7.
- Added inactive public templates, three JSON Schemas, governance/parameter/model/feature/traceability updates, an operating contract and public synthetic tests. No real/private source body was opened.

### Deliberately not implemented in R6

- Generic same-stage row/version dedup, cross-stage links, one-to-many/many-to-one allocation, residual pools, reversal-chain reconciliation and independent aggregation belong to R7.
- Payroll/tax/interest/management formulas, named Metrics, final workbooks, private replay/current regression, performance/release gates, Git release and global installation remain R8–R12.
- Public templates do not assert real RedCircle/company headers, status meanings or sign conventions. Those require private evidence before a real run.

### Run history at R6 implementation

| Run | State | Purpose |
| --- | --- | --- |
| R0–R5 | complete | Governance, safety, input, identity and ledger/accounting foundations |
| R6 | complete | Lifecycle source readers, candidates and exact export duplicates |
| R7–R12 | not_started | Must execute sequentially, one Run Contract per iteration |
| Global install | not_started | Allowed only after R12 release gates |

## 2026-07-18 — R7 Event dedup, typed links and reconciliation

- Contract: Task Pack `1.2.0`, product `0.2.0-dev.7`, Run `R7` only.
- Status: complete; full R7 acceptance evidence is produced and sealed outside the repository after validation.
- Added an immutable relation-event view that binds R6 candidates or other governed source events to a complete R4 canonical scope or explicit `ALLOCATION_REQUIRED`. Partial scope assertions, final Metric inclusion and company approval state are prohibited.
- Added six-class same-stage dedup. Exact same-key/same-version aliases select one canonical event; changed versions and cross-key business equivalence require exact event-set, input-resolution and hash-evidence bindings. Similar amount/date/counterparty/document data stays candidate-only.
- Partitioned candidate comparison by entity/project/WBS/contract/direction/stage and activated a 1,000,000 pair ceiling. Cross-stage dedup is prohibited.
- Added eleven typed relations, evidence/match priority, lifecycle compatibility, explicit scope-resolution gates, 1:N/N:1 and partial allocations, reversal/supersession lineage, and per-axis capacity controls.
- Completion uses connected same-axis match groups. A completion audit found and fixed a false-block surprise where two explicit 60/40 links each looked partial but together allocated 100%; global group completion now passes while true residuals and over-allocation still block.
- Added signed and absolute source-control equations over included/excluded/pending/parse-error pools. Channel A directly sums included rows; Channel B independently subtracts other pools from source control. Both require zero minor-unit deltas.
- Added four locked Schemas, an operating reference, public/redacted summaries, governance/model/feature/parameter/traceability updates and public synthetic unit, property and metamorphic tests. No private finance source body was opened.

### Deliberately not implemented in R7

- Payroll/tax/interest/management formulas and allocation policies belong to R8.
- Named Metric inclusion, final workbooks/output artifacts and automatic final generation belong to R9; R7 event-level reconciliation does not imply formal readiness.
- Private replay/current-data regression, reference/calculate isolation completion, release/performance gates, Git release and global installation remain R10–R12.
- Real company link keys, allocation semantics and ambiguous scope resolutions remain input-dependent and must block until qualified private evidence is supplied.

### Run history at R7 implementation

| Run | State | Purpose |
| --- | --- | --- |
| R0–R6 | complete | Governance, safety, input, identity, ledger and lifecycle foundations |
| R7 | complete | Same-stage dedup, typed links, match groups and event-level reconciliation |
| R8–R12 | not_started | Must execute sequentially, one Run Contract per iteration |
| Global install | not_started | Allowed only after R12 release gates |

## 2026-07-18 — R8 Formula, fully loaded payroll and policy inputs

- Contract: Task Pack `1.2.0`, product `0.2.0-dev.8`, Run `R8` only.
- Status: complete at implementation level; full R8 acceptance evidence is produced and sealed outside the repository after validation.
- Added an allowlisted formula/rate engine with integer-rational half-up evaluation, exact scope/effective-date selection, request/input/config hash binding, evidence/authority modes, executable test vectors and append-only supersession. Unknown or overlapping active formulas fail closed.
- Registered the historical management-rate observation as inactive regression evidence, never a calculate default. Registered FX as deferred and made active FX impossible in CNY-only product 0.2.
- Added formula-readiness output with explicit supply, qualified-alternate, scope-reduction or blocked choices. No response is not permission, and R8 objects cannot claim named-Metric inclusion.
- Added effective pay-component registries, employee/external-labor separation, payroll/control/approved-time records, correction/reversal/retroactive lineage and approved-time allocation to a visible unallocated payroll pool.
- Enforced component-to-payroll-control, project-plus-unallocated-time, and allocation-plus-unallocated-payroll equations. Cross-entity/missing-WBS allocations, unknown components, guessed rates and automatic residual spreading block.
- An adversarial one-cent/two-project case exposed independent half-up over-allocation. R8 retains the signed diagnostic residual and blocks instead of silently moving a cent.
- Added project-tax source/recomputed/gross controls with recoverability and evidence priority, plus interval-based capital interest with explicit principal movements, day-count basis and same-day cash ordering.
- Added append-only manual adjustments with explicit sign/reason/evidence, effective/expiry dates, request/input/config hashes and strict supersession/reversal scope.
- Added inactive public YAML templates, three CSV intake headers, eight JSON Schemas, one operating contract, governance/model/feature/parameter/traceability updates and public synthetic tests. No raw company source body was required for R8 acceptance.

### Deliberately not implemented in R8

- Named Metric construction, four-plane statuses, independent Metric-level aggregation, final workbook/output artifacts and automatic final generation belong to R9.
- Private reference/current regression and reference-calculate isolation completion belong to R10–R11; performance, release, Git and global-install gates belong to R12 and the final install step.
- Public templates do not assert real company component names, rates, time units, payroll controls, tax treatment, interest policy or adjustment authority. Real runs remain blocked until those private inputs are supplied or scope is explicitly reduced.

### Run history at R8 implementation

| Run | State | Purpose |
| --- | --- | --- |
| R0–R7 | complete | Governance, safety, input, identity, ledger, lifecycle and event-control foundations |
| R8 | complete | Evidence-bound formulas, fully loaded payroll, tax/interest and adjustments |
| R9–R12 | not_started | Must execute sequentially, one Run Contract per iteration |
| Global install | not_started | Allowed only after R12 release gates |

## 2026-07-18 — R9 Named Metrics and final workbook generation

- Contract: Task Pack `1.2.0`, product `0.2.0-dev.9`, Run `R9` only.
- Status: complete at implementation level; full R9 acceptance evidence is produced and sealed outside the repository after validation.
- Added four independent status planes for execution, input readiness, calculation and generation. Final output requires the exact valid combination `SUCCEEDED + SUFFICIENT + VALIDATED + FINAL_GENERATED`.
- Added governed direct and derived named Metrics with accounting basis, lifecycle, as-of, scope, source/recomputed/calculated values, exact fact hashes and explicit decision/evidence lineage.
- Added independent signed and absolute aggregation channels. Channel A sums included facts; Channel B subtracts excluded, pending and parse-error pools from source control. Any non-zero delta blocks.
- Forced actual cost to carry both `JOB_COST_INCURRED` and `GL_RECOGNIZED_COGS`; final output never collapses the two bases into one unexplained number.
- Enforced per-run input sufficiency before calculation. Incomplete input cannot carry calculated Metric facts and produces only a compact numbered supplement/alternate/scope/optional-display/stop prompt plus diagnostics.
- Added direct final generation when all in-scope data and validation gates pass. The Skill neither sets a finance owner/authorized person nor manages company approval; it writes a location/evidence handoff for the calling Codex/operator to continue the existing process outside the Skill.
- Added atomic final, blocked and generation-failure publication with no overwrite, non-cyclic manifest/index order, absolute output locators and detached seals.
- Added a values-only eight-sheet workbook through the explicitly injected bundled `@oai/artifact-tool` runtime. Integer minor units remain authoritative; deterministic yuan text is display-only. OOXML macros, external links, DDE, formulas and active content are rejected.
- Added full Metric facts, snapshots, lineage, traceability, review queue, performance/privacy summaries, run manifest, output indexes and internal-process handoff artifacts.
- Visual QA found and fixed two empty-looking sheets and overlong hash rows. Explicit not-in-scope/no-difference rows and shortened display fingerprints preserve readability without losing full JSON/CSV evidence.
- Full pytest passed 254 tests with one filesystem-normalization skip; independent unittest ran 255 tests, OK with the same skip. Static schema/config/code checks, JavaScript syntax, Skill validation, Git whitespace, privacy boundary, all three generation paths, all seals/indexes and all eight visual previews passed.

### Deliberately not implemented in R9

- No real/private raw finance body was read. Synthetic generation is not proof of current company-source readiness or production correctness.
- `reference-replay` versus `calculate` private isolation belongs to R10; current-data regression belongs to R11; performance/release, Git commit/push/merge and global installation belong to R12/final install.
- The Skill does not automate, assign or record the company internal approval workflow.

### Run history at R9 implementation

| Run | State | Purpose |
| --- | --- | --- |
| R0–R8 | complete | Governance, safety, inputs, identity, source/event and formula foundations |
| R9 | complete | Named Metrics, four statuses, dual-channel reconciliation and atomic workbook generation |
| R10–R12 | not_started | Must execute sequentially, one Run Contract per iteration |
| Global install | not_started | Allowed only after R12 release gates |

## 2026-07-18 — R10 private reference replay and calculate isolation

- Contract: Task Pack `1.2.0`, product `0.2.0-dev.10`, Run `R10` only.
- Status: implementation and private truth replay complete; final full-suite/static/privacy evidence is refreshed at R10 close.
- Added a strict private import manifest and baseline parser that verifies the full baseline digest before JSON parsing, permits only bounded integer minor units, preserves optional-field absence and explicit nulls, and rejects extra or malformed fields.
- Added safe relative PDF resolution, active-content/resource preflight and full digest verification for the complete reference set before any reference values are emitted.
- Added independent replay-fidelity and source-quality statuses. Exact line/total reproduction can coexist with a preserved source arithmetic difference; the source and independently recomputed values are never overwritten.
- Added replay-only output contracts with `calculation_status=NOT_EVALUATED`, `generation_status=NOT_GENERATED`, no workbook and no internal-process handoff. Every terminal state is atomic, no-replace, sealed and reports absolute output locators.
- Hardened unexpected writer failures: unpublished partial staged artifacts are removed before sealed failure evidence is created.
- Added AST and isolated-process tests proving calculate modules cannot import replay and replay cannot import accounting, formulas, payroll, adjustments, Metrics, workbook or final-generation adapters.
- Private acceptance reproduced 8/8 projects and 68/68 line items with every bound PDF hash matching. Known source arithmetic differences were preserved, calculate data-flow use stayed false and no raw/private artifact entered tracked paths.
- PDF visual QA rendered all 13 pages. Ten were fully readable; three source presentation warnings were retained: one overflow marker, one sparse residual page and one blank source page. The blank page contained neither text nor embedded images.
- Final dev.10 close passed 266 pytest tests with one known skip and 267 unittest cases with the same skip. Python/JSON/Schema/strict-YAML/CSV/JavaScript, Git whitespace, private-boundary, absolute-index and detached-seal checks passed; sealed aggregate evidence was produced outside the repository.
- The Skill remains development-only. R10 exact replay is not current calculate or production acceptance.

### Deliberately not implemented in R10

- No current-source calculate run or blocker snapshot was imported; that belongs to R11.
- No performance/release, commit, push, merge or global-install action was taken; those belong to R12/final install.
- No company approval role, assignment or workflow state was added.

### Run history after R10

| Run | State | Purpose |
| --- | --- | --- |
| R0–R9 | complete | Governance, safety, input, identity, source/event, formula, Metric and generation foundations |
| R10 | complete | Hash-bound private reference replay, anomaly preservation and calculate isolation |
| R11–R12 | not_started | Current calculate regression, then security/performance/release |
| Global install | not_started | Allowed only after R12 release gates |

## 2026-07-18 — R11 current-source production block and independent harness

- Contract: Task Pack `1.2.0`, product `0.2.0-dev.11`, Run `R11` only.
- Status: implementation and private exact expected-block regression complete; final full-suite/static/privacy evidence is refreshed at R11 close.
- Added a private preparation path that validates the complete sealed Task Pack before reading current seeds, then full-hashes the read-only current inventory. It creates a new no-overwrite current-source contract, expected-block contract, drift review, import manifest, absolute indexes and detached seal under gitignored runtime.
- Compared the sealed and current full inventories by digest multiset and every governed source slot. The observed global drift consisted only of items matching no governed slot; all slot candidate digest multisets remained exact. The result is recorded as `OUT_OF_SCOPE_INVENTORY_DRIFT`, with `snapshot_overwritten=false`.
- Bound current metadata identity and all nine selected non-reference production sources. Reference-report slots, PDF paths, baseline values and replay adapters are structurally prohibited from the calculate contract.
- Added a production current-source command that reads only the current contract, rechecks its digest/root/as-of/metadata and every selected source full digest, derives the input-sufficiency report and writes sealed blocked diagnostics with absolute locators.
- The direct private production run returned exit 3 with `NEEDS_USER_INPUT / BLOCKED_NON_WAIVABLE / BLOCKED_SOURCE / BLOCKED_DIAGNOSTICS_GENERATED` and the exact reviewed nine-code blocker set. It emitted no workbook and no `INTERNAL_PROCESS_HANDOFF.md`.
- Added an expected-block contract frozen before production plus an independent harness. The harness runs the production command as a subprocess and returns 0 only when the real exit 3, all four status planes, exact blocker list, request/source bindings, no-reference boundary, indexes and detached seal match; its success label is `EXPECTED_BLOCKED`, never `READY` or `FINAL_GENERATED`.
- Added source-contract, expected-contract and validation schemas plus synthetic tests for ambient-PDF isolation, forbidden source slots, metadata/hash drift, import-graph separation, exact production block, exact harness behavior, no final-looking artifacts and absolute locators.
- Input prompts explicitly require supplement, qualified alternate evidence, scope reduction or retaining the block. Silence is not permission and non-waivable gaps cannot be omitted. Skill role/approval fields remain absent.
- A public-only stranger forward test first found that preparation and harness were not fully discoverable from the two entry documents. `SKILL.md` and the R11 reference now provide the copyable preparation → direct production → second-production harness sequence, every CLI argument and exit `3/0/1` semantics. The repeated forward test passed with no material ambiguity; no private source was read.
- After the prompt wording changed, authoritative private production and harness evidence was regenerated append-only in new v3 directories. Direct production still exited 3, the independent harness still exited 0 only as `EXPECTED_BLOCKED`, and neither path emitted a workbook or internal-process handoff.

### Deliberately not implemented in R11

- Current raw sources were not parsed into final facts because required manifest, identity, reader/accounting, payroll/time, tax, interest and payment-mapping evidence is missing or conflicting. No reference delta was used as a substitute.
- R11 expected-block success is not current calculation success, production authority, release acceptance or company-process completion.
- Adversarial release corpus, cold/warm performance baseline, release governance, Git commit/push/merge and global installation remain R12/final-install work.

### Run history after R11

| Run | State | Purpose |
| --- | --- | --- |
| R0–R10 | complete | Governance through private reference replay |
| R11 | complete | Current production exit 3 plus exact independent expected-block harness |
| R12 | not_started | Security, performance, release and Git integration |
| Global install | not_started | Allowed only after R12 release gates |

## 2026-07-18 — R12 security, performance and release

- Contract: Task Pack `1.2.0`, product `0.2.0`, Run `R12` only.
- Added strict release performance budgets, schemas, a bound-snapshot independent-process benchmark, aggregate-only performance evidence, code/budget fingerprint binding, an R12 test matrix and a package/staged-boundary validator.
- Added fail-closed checks for exact `1.50×` wall/RSS limits, same-scope workload drift, one selected-source full digest per process, application-cache prohibition, 1,000,000 candidate-pair ceiling and global-unpartitioned matching prohibition.
- Added adversarial, property and metamorphic release tests. A first full-suite run was correctly blocked when a new test itself contained a forbidden private-root token; after repairing the public test fixture, the privacy boundary passed.
- Restored and explicitly injected the Codex bundled spreadsheet runtime. Final pytest ran 285 passed with one known host Unicode-normalization skip; independent unittest ran 286 with the same single skip. Workbook rendering and final generation were executed, not skipped.
- The bound current snapshot performance gate passed with one cold and three subsequent processes. Each process rescanned 58 entries and fully hashed 9 selected sources exactly once; no application cache, candidate matching or business parsing occurred. Wall and peak RSS stayed inside the `1.50×` budget.
- Reran private reference replay at `0.2.0`: 8/8 projects and 68/68 lines exact, with three source arithmetic differences preserved. Reran current production and the independent harness: production exit 3 retained the exact nine blockers; harness exit 0 meant only `EXPECTED_BLOCKED`; no workbook or internal-process handoff was emitted.
- Updated governance, model/formula/parameter registries, traceability, Skill instructions, release/operability reference and handoff for the fail-closed `0.2.0` release. Current real calculation remains `BLOCKED_SOURCE`.
- R12 does not install globally. Global installation is a separate next run after commit/push/merge and clean remote/main parity are proven.

### Run history after R12 implementation

| Run | State | Purpose |
| --- | --- | --- |
| R0–R11 | complete | Governance through private current expected-block regression |
| R12 | complete | Security corpus, performance baseline, release governance and Git integration gate |
| Global install | not_started | Separate post-parity run |

## 2026-07-18 — Post-R12 global-install portability repair

- Contract: Task Pack `1.2.0`, product `0.2.0`, separate global-install Run after R12 and clean-main parity.
- The first repo-native global copy was byte-exact, but its installed-directory full suite exposed two failures: `run_input_preflight.py` required a Git repository root even though a global Skill intentionally has no `.git` metadata.
- Added a fail-closed standalone-package fallback. A complete, non-symlinked `$CODEX_HOME/skills/project-cost-table-skill` root becomes the protected output boundary when Git is unavailable; incomplete or unregistered copies fail before `private_runtime` creation.
- Added subprocess tests for the repo-less success path and incomplete-package rejection. Repository checkout behavior and raw/private containment remain unchanged.
- Machine-local installation completion is not claimed by this source change; it still requires post-merge reinstall, full installed-directory tests, byte parity, discoverability metadata and a sealed external acceptance record.
- Completion audit found that copying the historical `GLOBAL_INSTALL: NOT_STARTED` value into an installed Skill would create a false dynamic instruction. Repository governance now uses `MACHINE_LOCAL_EXTERNAL`; R12's no-install invariant remains independently locked while each machine proves installation through its own discovery and sealed receipt.
