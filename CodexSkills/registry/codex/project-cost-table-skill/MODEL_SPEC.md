# Model Specification

Canonical proposed product model: `MODEL-KMFA-PROJECT-COST-002-PROPOSED`.

The model is a deterministic, versioned accounting/event pipeline. It does not use ML or LLM inference to create financial facts. Inputs are sufficiency reports, governed source records, explicit input resolutions, evidence-backed mappings, company-policy references, formula/rate profiles, and mode/Metric/basis/as-of selectors. Outputs are validated lifecycle facts, reconciliations, named Metrics, blockers, final or diagnostic artifacts, absolute output indexes, company-process handoffs, and review tasks.

Core invariants:

1. input sufficiency before business processing;
2. immutable source and input-resolution history;
3. project/entity/WBS identity before inclusion;
4. same-stage dedup and cross-stage links;
5. integer minor-unit conservation;
6. Metric/basis/lifecycle compatibility;
7. job-cost-incurred and GL-recognized-COGS views remain separate;
8. independent recomputation;
9. validated data triggers final generation;
10. company internal approval remains outside the Skill;
11. absolute output discovery on every run;
12. unknown or unsafe input fails closed.

The product model is `RELEASED_R12_FAIL_CLOSED_CURRENT_INPUT_GATED` at version `0.2.0`. Deterministic boundaries, security/money primitives, input sufficiency, manifest selection, inventory views, immutable lineage envelopes, effective project identity, the governed Kingdee/WIP bridge, four lifecycle source readers, candidate-stage separation, exact export aliases, generic same-stage dedup, typed cross-stage links, connected match groups, source conservation, event- and Metric-level dual-channel aggregation, evidence-bound formula/rate selection, fully loaded payroll allocation, project-tax control, capital-interest intervals, append-only adjustment validation, four independent status planes, values-only workbook generation, atomic final/blocked/failed artifacts, hash-bound private reference replay isolated from calculate, exact current-source expected-block regression, adversarial release tests, bound-snapshot performance and staged privacy governance are implemented. Release applies to the fail-closed workflow, not the current business result: current calculation remains `BLOCKED_SOURCE`, and only a fully validated calculate final-generation result can create a formal-looking workbook. The package contains no company approval state.

## R1 supporting policy

`POLICY-KMFA-ARTIFACT-BOUNDARY-001` is a deterministic safety policy, not a financial model.

- Status: `IMPLEMENTED_R1`.
- Input: a normalized module-relative path, optional Git index mode, and file bytes.
- Output: `PUBLIC_SAFE`, `PRIVATE_RUNTIME`, `RAW_SOURCE`, or a blocking finding.
- Default: unclassified paths, unreadable public content, symlinks, and configured sensitive signatures are rejected.
- Numeric parameter: `ARTIFACT_MAX_TEXT_BYTES`, registered in `parameter_registry.csv`.
- Change control: policy, implementation, tests, and traceability must change together.

## R2 deterministic primitives

### `POLICY-KMFA-MONEY-STRICT-001`

- Storage: signed integer CNY minor units; binary float paths are prohibited.
- Accepted source types: strict ASCII amount text, `Decimal`, integer, or an explicitly handled blank.
- Rounding: `ROUND_HALF_UP` at one named layer; ambient Decimal context cannot change results.
- Technical ceilings: 38-digit context, maximum six source decimal places, signed 64-bit minor-unit range.
- Audit fields: input scale, rounding layer, whether rounding occurred, negative-zero input, and blank input.
- Unknown text, Unicode-confusable signs, nonfinite values, excessive scale, and overflow produce structured blockers without echoing the source amount.

### `POLICY-KMFA-FILE-SECURITY-001`

- Governed inputs must be regular single-link files inside an explicit allowed root.
- ZIP-family inputs are checked for portable paths, normalized collisions, encryption, symlinks/special members, approved compression, count/size/ratio ceilings, CRC, recursive budget, and nesting depth before business parsing.
- Nested ZIP/XLSX verification requires an explicit existing private scratch directory; no implicit system-temp spill is permitted.
- OOXML inspection rejects macros/VBA/ActiveX/OLE, external relationships, connections, formulas, DDE, autorun defined names, and image-only sheets; hidden sheets and ordinary named ranges remain explicit warnings.
- Legacy XLS is a hard block until a locked read-only reader exists. PDF receives signature, EOF, encryption, and active-content gates but remains non-structured container evidence.
- Untrusted spreadsheet text is apostrophe-escaped at the output boundary; numeric amounts must stay numeric.

### `POLICY-KMFA-ATOMIC-PATHS-001`

- Input resolution rejects traversal, root escape, symlinks, hardlinks, special files, and size overflow.
- Output files are written and fsynced under a non-final-looking sibling, then published with an exclusive hard-link operation that cannot overwrite an existing target.
- Output directories are built under a non-final-looking sibling and renamed only on successful context exit.
- Failure and publish races clean only artifacts created by the current operation; another writer's target is preserved.

## R3 deterministic input and lineage policies

### `POLICY-KMFA-INPUT-SUFFICIENCY-001`

- Every operation derives a checklist from mode, requested Metrics and basis IDs, project scope, as-of date, policies, manifest, raw-root metadata and output destination before any raw source body is opened.
- Missing items produce one compact matrix. No response is not permission. `NON_WAIVABLE` items cannot use optional omission, and scope reduction must remove every affected Metric from the resulting request.
- A resolution preserves the exact user instruction and evidence refs. It binds the prior sealed incomplete-report request hash, current request hash, manifest hash and requirements hash. Claimed supply or alternate evidence remains missing until a rescan observes `PRESENT`.
- Each run atomically writes a private report, optional exact resolution record, human/machine absolute output indexes and a detached non-cyclic seal. Input-gate outputs never masquerade as final financial workbooks.

### `POLICY-KMFA-MANIFEST-SELECTION-001`

- Every required slot needs explicit patterns and one or more explicitly selected opaque source ID/full-SHA256 locks, plus expected schema fingerprint, reader version and logical source period. Batch selection is permitted only when the reader contract supports a source set.
- Formal selection reopens and rehashes the selected single-link regular file. Cached digest, mtime and enumeration order have no business authority.
- Reference-report slots are structurally prohibited in `calculate`; replay request validation does not force a calculate Metric match.
- Private full inventory contains paths, identities and digests only in private runtime. Public inventory output contains aggregate counts/statuses only.

### `MODEL-KMFA-SOURCE-LAYERS-001`

- `SOURCE_RECORD`, `CANDIDATE`, `DECISION` and `APPROVED_FACT` are separate immutable envelopes with exclusive append-only writes and explicit lineage constraints.
- `APPROVED_FACT` means a validated data-layer fact; it is not a finance-owner, authorized-person or company-approval state.
- Supersession creates a new record and preserves the prior record; no source or decision history is overwritten.

## R4 deterministic identity policy

### `POLICY-KMFA-IDENTITY-MASTER-001`

- Canonical aggregation key: `canonical_project_id + legal_entity_id + wbs_or_cost_code + valid_at`.
- Final resolution order: exact canonical scope, exact contract ID, exact governed source-system ID, then evidence-qualified explicit mapping resolution.
- Project code, name, customer, free-text and amount similarity are candidate-only; fuzzy final matching and unresolved final mappings are prohibited.
- Effective `valid_to` is inclusive. Overlapping active periods, one-to-many aliases, multiple active matches, contract/project disagreement, identifier conflict, cross-entity ambiguity, stale mappings, incomplete keys and unmapped records fail closed as `BLOCKED_IDENTITY`.
- The identity-master hash binds the locked policy-file SHA together with every mapping, period, resolution and evidence reference; mutable record containers and stale snapshot hashes are rejected.
- Every blocker creates an opaque candidate and `P0` data-governance review task in append-only private runtime. Public summaries expose counts only.
- Cross-entity views retain entity, WBS/cost-code and identity-record dimensions. Destructive cross-entity normalization is prohibited.
- `identity_status=APPROVED` means only evidence-qualified data mapping. The model has no finance owner, authorized person, assignee or company approval workflow.

## R5 deterministic ledger and accounting-basis policies

### `POLICY-KMFA-KINGDEE-READER-001`

- Input: exactly one R3 manifest-selected `general_ledger` source plus active reader/schema, R2 security and R2 money profiles.
- Supported structured path: value-only `.xlsx` after a complete OOXML preflight; formulas, active content and external relationships are blocked before parsing. Legacy `.xls` remains a hard block.
- Output: immutable source records preserving all governed identifiers, dates, debit/credit/balance, currency, status and row kind, plus row and amount-side source controls.
- Missing stays null. The reader never classifies a row into a final Metric, never guesses headers or status semantics and never uses source free text to map a project.
- Business fingerprints use normalized record content and locked reader/schema profiles, not filesystem paths, row enumeration or harmless ZIP package metadata.

### `POLICY-KMFA-KINGDEE-BUNDLE-001`

- Input: exactly one manifest-selected ZIP plus an `ACTIVE` container profile that binds its digest and every workbook member's digest, disposition and evidence.
- Every `.xlsx`/`.xls` member must be declared. Every included `.xlsx` is independently preflighted and read with its exact active reader profile; any missing/unlisted member or partial read blocks the full ledger slot.
- `EXCLUDE_QUALIFIED_SCOPE` is permitted only with a reason and hash-bound evidence. Excluded `.xlsx` still receives the full OOXML security preflight. An included legacy `.xls` blocks the full slot until a locked reader exists.
- Extraction uses an exclusive empty private scratch directory outside the read-only input root. Emitted records retain opaque container and member lineage; public output contains aggregate member/row counts only.

### `POLICY-KMFA-ACCOUNTING-BASIS-WIP-001`

- Inputs: reader records, one R4 identity/contract binding per in-period business row, an effective `ACTIVE` account/status/row-kind/period/valuation policy, a posting-date period/cutoff and one or more exact requested canonical project + entity + WBS + contract scopes.
- `JOB_COST_INCURRED`: additions + adjustments + transfer-in - true reversals - transfers to another scope. A same-project WIP-to-COGS transfer is not another cost.
- `GL_RECOGNIZED_COGS`: recognized COGS - COGS reversals. WIP balances are not added.
- Main control: opening WIP + additions + adjustments + transfer-in - reversals - other transfers - net recognized COGS - closing WIP = 0 cents.
- Companion control: net 5001-to-6401 transfer - net recognized 6401 COGS = 0 cents. Both controls are non-waivable and block both named views when non-zero.
- Account-level debit/credit/semantic controls remain available beside bridge-group results. Classification also conserves every input row and both ledger sides.
- Only exact requested scopes enter basis views; other resolved scopes remain conserved exclusions. Requested scopes deterministically form the scope fingerprint. Closed periods require a content-addressed prior snapshot bound to that fingerprint, start and close date. New, removed or changed lines require `restate` with a superseded-run reference; prior snapshots are not overwritten.
- Product `0.2` is CNY-only. Unknown status, row kind, account, identity, date, currency, valuation or policy evidence fails closed.
- Status `R5_RECONCILED_NOT_FINAL` cannot be promoted to a formal operating, performance or payroll result. The policy neither appoints an approver nor manages company internal approval.

## R6 deterministic lifecycle source policies

### `POLICY-KMFA-LIFECYCLE-READERS-001`

- Inputs: one or more R3 manifest-selected XLSX sources in `project_billing`, `cash_out`, `contract_and_changes` or `cash_in`, plus slot-compatible `ACTIVE` reader profiles and the R2 security/money profiles.
- Each profile locks reader version `2.0.0`, exact sheet/header order, every canonical binding, date mode, required fields and evidence-backed exact source status/event-type/row-kind rules. Public templates remain inactive.
- Outputs preserve immutable source records, source identities, stable document/line keys, all relevant dates, CNY integer-minor amounts, gross/net/tax, source arithmetic delta, row action and unbound-column digest. Null and malformed values are never coerced to zero.
- Unknown semantics, missing required fields, profile/schema/identity drift, unsafe OOXML, legacy XLS and non-CNY fail closed. Control rows require explicit evidence rules and remain in row/amount controls.
- The reader cannot automatically assign a project or decide final Metric inclusion. Free text is candidate-only.

### `MODEL-KMFA-ECONOMIC-EVENT-CANDIDATE-001`

- Billing emits only `REVENUE/BILLED`; payment only `CASH_OUT/PAID`; collection only `CASH_IN/COLLECTED`; contract/change only `REVENUE/CONTRACT_VALUE` or `COST/COMMITMENT`.
- Stage-specific dates are mandatory. `SOURCE_REVERSED` requires an original-source key and reversal date. Evidence-backed negative multipliers preserve credit/refund/reduction signs.
- Source gross/net/tax arithmetic remains visible as `BALANCED`, `SOURCE_ARITHMETIC_DELTA`, `INCOMPLETE` or `NOT_APPLICABLE`; it is not silently corrected.
- Every R6 event keeps `identity_status=PENDING_IDENTITY` and `metric_inclusion_status=NOT_EVALUATED_R6`. Status `R6_LIFECYCLE_CANDIDATES_NOT_FINAL` has no formal operating authority.

### `POLICY-KMFA-EXACT-EXPORT-DUPLICATE-001`

- Equal whole exports require the same slot, locked reader/profile/schema semantics and identical normalized business-record multiset. Filesystem path, row order and harmless ZIP metadata have no business authority.
- Exact aliases are counted once at the event layer while every source-record reference remains preserved. Pre-dedup count/amount must equal emitted plus suppressed count/amount with zero minor-unit delta.
- Adding another exact download alias cannot change the batch business fingerprint.
- Changed status/amount, partial overlap and duplicate rows inside one export are not silently deduplicated by R6. R7 models their versions, links, allocations and residuals without changing the R6 source facts.

## R7 deterministic dedup, event-link and reconciliation policies

### `POLICY-KMFA-SAME-STAGE-DEDUP-001`

- Every R7 relation view binds an immutable economic event to one full R4 canonical scope or the explicit state `ALLOCATION_REQUIRED`; partial canonical identity assertions are prohibited.
- Pair comparison first partitions by legal entity, canonical project, WBS/cost code, contract, direction and lifecycle stage. The governed ceiling is 1,000,000 candidate pairs; exceeding it blocks before comparison. Cross-stage events are always distinct for dedup purposes.
- Classes are `BYTE_DUPLICATE`, `BUSINESS_CONTENT_DUPLICATE`, `SAME_KEY_SAME_VERSION`, `SAME_KEY_CHANGED_VERSION`, `POSSIBLE_DUPLICATE` and `DISTINCT`.
- Same key and same normalized source version may deterministically select one canonical row while retaining aliases. Same key with changed digest blocks all versions until an exact event-set/version resolution binds the selected version, superseded versions and hash evidence.
- Equal business content under different keys is not automatically excluded. It requires an exact event-set equivalence resolution, input-resolution reference and hash-bound evidence. Amount/date/counterparty/document/text similarity remains `POSSIBLE_DUPLICATE` and creates a review task only.
- Supersession preserves the prior event. Events are never overwritten or deleted, and adding an exact alias does not change the deduplicated business fingerprint.

### `MODEL-KMFA-EVENT-LINK-001`

- Governed relation types are `DERIVED_FROM`, `FULFILLS_COMMITMENT`, `ACCRUAL_FOR`, `REVERSES`, `SUPERSEDES`, `INVOICES`, `POSTS_TO_GL`, `SETTLES`, `ALLOCATES_TO`, `TRANSFERRED_BETWEEN` and `REFERENCES_ONLY`.
- Match priority is stable identifier, validated identity/contract, then explicit evidence-backed allocation resolution. Amount/date/text similarity can create only a `CANDIDATE`; it cannot create an approved data link.
- Allocations use nonnegative absolute CNY minor-unit magnitudes while the underlying events retain their signed amounts. Source and target allocation totals must be equal. One-to-many and many-to-one links are supported.
- A single link exposes its residuals, but completion is decided across the connected match group on the same relation axis. This allows two explicit 60/40 links to complete one 100% group without false residuals while still blocking same-axis over-allocation. The same event may participate on different axes, for example contract-to-invoice and invoice-to-GL, without cross-axis double-counting.
- Scope mismatch or unresolved identity is allowed only for `SETTLES`, `ALLOCATES_TO` or `TRANSFERRED_BETWEEN`, and only with an explicit input-resolution reference plus hash-bound evidence. No residual is automatically spread.
- `REVERSES` is one-to-one, binds `reversal_of_event_id`, preserves opposite signs and must net to zero cents. `SUPERSEDES` is nonfinancial and requires a version-resolution match method.
- Every R7 link has `metric_inclusion_status=NOT_EVALUATED_R7`. Approved here means only evidence-qualified data linkage; it is not company approval.

### `POLICY-KMFA-SOURCE-CONSERVATION-001`

- Every emitted relation event has exactly one disposition: included, excluded, or pending. A known parse-error amount occupies a separate parse-error pool; missing/invalid rows are never silently zeroed.
- Signed and absolute equations are both required: `source_control = included + excluded + pending + parse_error`, with zero minor-unit delta.
- Channel A directly iterates included events. Channel B independently starts from source control and subtracts excluded, pending and parse-error pools. Both signed and absolute channel deltas must be zero.
- Link reconciliation separately enforces source-to-target allocation conservation, per-event capacity on each relation axis and connected match-group residuals. Candidate links, unresolved residuals and over-allocation remain explicit blockers.
- Event-level reconciliation completion does not grant named Metric inclusion. Metric-level independent aggregation remains R9, and R7 does not generate a formal workbook or manage an internal approval workflow.

## R8 deterministic formula, payroll and policy-input controls

### `POLICY-KMFA-FORMULA-RATE-001`

- Only `RATE_TIMES_BASE`, `APPROVED_TIME_PRORATION`, `SIMPLE_INTEREST_DAILY` and the deferred FX expression are registered. Evaluation uses integer numerators/denominators and symmetric half-up rounding; arbitrary expressions, float inputs and historical backsolves are absent.
- Every active formula profile binds exact canonical scope, inclusive effective dates, CNY, one registered rounding layer, authority mode, request/input/config hashes, evidence and at least one executable test vector.
- Selection requires one applicable active profile. Unknown IDs, inactive/reference/superseded/deferred profiles, overlapping active scope/date ranges, failed vectors, missing evidence or request drift block before calculation.
- Supersession is append-only and ordered. The historical management-rate observation remains inactive. FX activation is blocked for CNY-only product 0.2.
- Formula-readiness emits structured missing-input choices and `user_action_required`; silence and generic omission cannot waive an affected non-waivable Metric input.

### `POLICY-KMFA-FULLY-LOADED-PAYROLL-001`

- The component registry assigns every observed source component exactly one effective treatment. Unknown components and external labor in employee payroll fail closed; missing components are never zero.
- Payroll, approved-time and control records share legal entity, opaque employee and period keys. Project time requires canonical project, WBS and identity-resolution evidence; cross-entity allocation blocks.
- All component records reconcile to the payroll control, all project plus unallocated time reconciles to the approved-time control, and project allocations plus the visible unallocated payroll pool reconciles to fully loaded employer cost.
- Corrections, retroactive records and reversals preserve lineage; reversals exactly negate the target. There is no guessed day rate or automatic residual spreading.
- If independent half-up project lines exceed allocable employer cost, a signed unallocated diagnostic remains visible and the group blocks. The engine never reallocates a cent merely to make the total look clean.

### `POLICY-KMFA-TAX-INTEREST-001`

- Project tax priority is direct project evidence, governed project ledger, then an evidence-backed project allocation policy. Company-level tax controls cannot default into project values.
- Source tax, recomputed tax, tax delta, gross arithmetic delta, rate, invoice type and recoverability remain separate. A mismatch blocks and never overwrites source arithmetic.
- Interest is calculated over explicit principal intervals. The input binds opening principal, receipt/payment/prepayment movements, same-day ordering, start/end dates, annual-rate fraction, day-count denominator, rounding, policy and evidence. Missing inputs or negative principal blocks.

### `MODEL-KMFA-MANUAL-ADJUSTMENT-001`

- An adjustment is a candidate with explicit sign, nonzero amount, reason, canonical scope, evidence, formula profile, policy or qualified resolution, effective dates, expiry, reversal policy and request/input/config hashes.
- Supersession and reversal are append-only, stay within one Metric/lifecycle/entity/project/WBS/category scope, and cannot form a cycle. A reversal exactly negates its target; expired active records block.
- Every R8 object stays `NOT_EVALUATED_R8`. R9 decides named-Metric inclusion and final generation only after all independent controls pass. The Skill neither assigns internal roles nor manages the existing company process.

## R9 deterministic Metric and generation policies

### `MODEL-KMFA-NAMED-METRIC-001`

- R7 relation events require complete validated identity plus an explicit content-addressed R9 inclusion decision and evidence before promotion. R5 basis components require exact one-to-one bridge lineage; missing or surplus lineage blocks.
- Each fact binds one named Metric, one accounting basis, one lifecycle stage, one metric-specific date, exact entity/project/WBS scope, integer CNY minor units, disposition, source refs, mapping/formula/parameter/policy/resolution refs and immutable evidence.
- Direct channel A iterates included facts. Direct channel B starts from immutable count/signed/absolute source controls and subtracts excluded, pending and parse-error pools. Both signed and absolute deltas must be zero.
- Source, recomputed and calculated values and both deltas remain separate. A supplied source value that differs by one minor unit blocks; it is never overwritten.
- Derived accounting and cash margins use registered component graphs only. Components must be individually validated and share as-of and scope. Job-cost and GL-recognized-COGS margins remain separate.
- Requesting actual project cost forces both `JOB_COST_INCURRED` and `GL_RECOGNIZED_COGS` snapshots into the required set.

### `POLICY-KMFA-FOUR-STATUS-PLANES-001`

- Execution, input readiness, calculation and generation are separate enums and independently serialized.
- `FINAL_GENERATED` is valid only with succeeded execution, sufficient or sufficient-with-documented-scope input and validated calculation.
- Input/business blockers produce `BLOCKED_DIAGNOSTICS_GENERATED`; renderer/export failures produce `FAILED`. Neither state can publish an `.xlsx` or internal-process handoff.
- Company approval is not a status plane. The Skill neither assigns finance roles nor waits for internal approval before generating a validated final.

### `POLICY-KMFA-SAFE-WORKBOOK-001`

- The only authoring runtime is an explicitly injected Codex-bundled Node executable plus `@oai/artifact-tool`; system/global/repository spreadsheet libraries are not searched or installed.
- The workbook contains exactly eight visible sheets and writes values only. Integer minor units are the exact monetary truth; derived yuan display strings do not participate in arithmetic.
- Every sheet is rendered before export acceptance. OOXML validation rejects formulas, errors, macros, DDE, active content, connections and external relationships and records a semantic workbook hash without recalc.
- Untrusted text is spreadsheet-escaped before the writer receives it.

### `POLICY-KMFA-FINAL-GENERATION-001`

- Sufficient input and validated Metrics trigger immediate generation. There is no approval wait state.
- Blocked runs always publish explicit input/action diagnostics and no workbook. Renderer/export failures atomically remove staged final artifacts and publish a sealed failure diagnostic.
- Business outputs are written before the manifest; human index, machine index and detached seal follow a non-cyclic order. The seal covers every finalized file except itself and is verified before atomic no-replace publication.
- Every state returns absolute result, output directory, primary output, human index and next-step locators.
- `INTERNAL_PROCESS_HANDOFF.md` exists only for final generation and instructs the invoking Codex/operator to continue the existing company process outside the Skill. It stores no owner, authorized person or approval status.

## R10 deterministic private reference replay

### `POLICY-KMFA-REFERENCE-REPLAY-ISOLATION-001`

- Reference baseline/PDF readers and CLI are isolated from calculate imports. Calculate modules cannot import replay, and replay cannot import accounting, formula, payroll, adjustment, Metric, workbook or final-generation modules.
- Replay values cannot populate a calculate request, Metric fact or source adapter. Static import inspection, isolated-process probes and behavioral tests enforce the boundary.
- Replay uses `calculation_status=NOT_EVALUATED` and `generation_status=NOT_GENERATED`; it cannot emit a formal workbook or company-process handoff.
- A hash, security or line-fidelity conflict blocks before reference values are written. Success, blocked and failure controls remain atomic, no-replace, sealed and absolutely locatable.

### `MODEL-KMFA-REFERENCE-REPLAY-001`

- Input is a private import manifest binding one strict integer-minor-unit baseline plus the expected project count, followed by safe read and full-digest verification of every relative reference PDF.
- The full baseline digest is verified before JSON parsing. Every project/PDF binding is unique; missing optional values remain missing and explicit nulls remain null.
- Replay requires exact line-value reproduction and zero line-to-source-total delta. It preserves source revenue, total cost, profit and displayed rate while independently computing profit and the source arithmetic delta.
- A known nonzero source arithmetic delta yields `SOURCE_ARITHMETIC_DIFFERENCE` alongside `replay_fidelity_status=EXACT`; neither value is overwritten. Drift from the bound expected delta blocks.
- R10 private acceptance reproduced 8/8 projects and 68/68 line items with all PDF hashes matching. This proves historical fidelity only; current calculate truth remains an independent R11 gate.

## R11 deterministic current-source expected block

### `MODEL-KMFA-CURRENT-SOURCE-CONTRACT-001`

- Private preparation verifies the sealed Task Pack before parsing current seeds, inventories the read-only root, and full-hashes current sources. It binds exact metadata identity plus the selected non-reference source digests in a private current-source contract.
- Full inventory drift is compared as a digest multiset and independently per governed slot. R11 accepts only reviewed out-of-scope inventory drift with every slot digest multiset exact and `snapshot_overwritten=false`; any in-scope drift blocks a new contract.
- The contract requests `COST_POSTED_ACTUAL` with both `JOB_COST_INCURRED` and `GL_RECOGNIZED_COGS`, carries only generic evidence statuses, and explicitly forbids baseline values, report line items and replay adapters.
- Production rechecks the contract digest, input root, as-of, metadata fingerprint and every selected source digest. A mismatch becomes an explicit blocker; it never rewrites the contract or falls back to mtime/reference totals.

### `POLICY-KMFA-CURRENT-EXPECTED-BLOCK-001`

- The reviewed expected-block contract is written and sealed before production. Production imports only `current_reconstruction`; it cannot import the regression harness or load its expectation.
- Current full-scope missing/conflicting evidence produces exactly nine generic blocker codes covering manifest, identity, reader/accounting basis, payroll/time, payroll policy, tax, interest and payment mapping. A reference-total delta is explicitly excluded.
- Production returns exit 3 with `NEEDS_USER_INPUT / BLOCKED_NON_WAIVABLE / BLOCKED_SOURCE / BLOCKED_DIAGNOSTICS_GENERATED`, an explicit supplement/alternate/scope/stop prompt, no workbook and no company-process handoff.
- The independent harness returns exit 0 and `EXPECTED_BLOCKED` only when production exit, all four planes, exact blocker set, request/source bindings, absolute indexes, detached seal and zero replay/reference data flow match. Test success is not calculation success or production authority.
- Every output exposes absolute locators. When all real inputs and validation gates later pass, R9 directly generates the final two-basis workbook; the Skill still assigns no finance owner/authorized person and manages no company approval state.

## R12 deterministic release and performance policy

### `POLICY-KMFA-RELEASE-PERFORMANCE-001`

- `config/performance_budgets.yml` is strictly loaded without aliases, duplicate keys, bool/int coercion or unknown fields. The regression factor cannot exceed `1.50`; candidate pairs cannot exceed 1,000,000; global unpartitioned matching and application digest caching are forbidden.
- The bound current snapshot baseline runs in independent processes. One cold application-process run is followed by three same-scope subsequent runs. Every selected source is reopened and fully hashed exactly once in every process; source names, locators, hashes and business values never enter the aggregate performance summary. The evidence binds product version, exact release-workload code fingerprint and governed budget digest.
- Every subsequent wall time and peak RSS must remain within `1.50×` of the cold baseline. Digest count, full-digest completion, candidate pair, cache and algorithm-shape violations independently fail the release result.
- Current business parsing remains prohibited while its input gate is blocked. The performance result therefore states `real_calculation_baseline_status=NOT_EVALUATED_BLOCKED_SOURCE`, with zero business files, archive members and rows parsed. Actual bundled workbook generation is exercised separately by the required R9 synthetic integration tests.
- Release requires the adversarial, property and metamorphic matrix, full tests, real bundled workbook runtime, R10 reference replay, R11 direct production/independent expected-block harness, public package validator, staged privacy scan, Git overlap review and remote/main parity.
- Product release does not relax per-run sufficiency. Missing inputs still require supplement, qualified alternate evidence, actual scope reduction or remaining blocked; silence is not permission and non-waivable requirements cannot be omitted.
- A validated calculate run directly generates its final two-basis workbook and absolute output locators. Release adds no finance owner, authorized person or company approval status. Global installation is not part of R12 and remains a separate post-parity run.
