---
module_name: product-reality-lab
description: Discover unknown product failures and market gaps before formal verification by combining provenance-safe competitor and open-source research, product surface/state/fault modeling, deterministic and model-assisted exploration, frontend/backend/data/performance/security/chaos experiments, poka-yoke audits, staged real-user feedback, defect convergence, and evidence-backed handoff to an independent verifier. Never issues PASS.
metadata:
  version: 0.0.0.3
  status: integrated_internal_module
  source_lineage: product-reality-lab-v0.0.0.1
  registry_entry: false
  display_name: Product Reality Lab｜产品现实试炼场
  aliases:
    - reality-lab
    - product-gauntlet
    - 产品现实试炼场
---

# Product Reality Lab

## 0. Mission

Find high-impact unknown defects, user failure paths, competitive gaps, and unsafe operations **before** formal release adjudication. Build a reproducible reality model, execute controlled experiments, collect synthetic and field evidence, close defects, then hand the exact frozen subject to an independent `verifier`.

This Skill is a discovery and experimentation layer. It is not a release judge.

## 1. Position in the system

```text
requirements / product intent / competitors / code / runtime
                           ↓
                product-reality-lab
      recon → census → model → experiments → field → evidence
                           ↓
                    repair agent
                           ↓
       frozen subject + claims + evidence + residual risk
                           ↓
                       verifier
                           ↓
                independent PASS / FAIL
```

Related Skills:

- `verifier`: final independent adjudication of an exact frozen subject and acceptance contract.
- `webapp-testing`: may serve as a basic Playwright adapter; it is not the whole Reality Lab.
- `teleiosis`: evolves this Skill as a Skill candidate; do not use it as a substitute for product testing.
- `persona-distiller-group`: use only when actual independent dossiers, claim IDs, counterevidence and adjudication are produced.
- `context-kernel`: use for durable cross-run governance; drafts are `PROPOSED_NOT_COMMITTED` unless a real write-back path succeeds.
- `grilling`: pressure-test unresolved decisions one branch at a time; inspect code/evidence instead of asking the owner for facts that can be discovered.
- `i-have-adhd`: lead run reports with the next concrete action, preserve visible state, and suppress tangents.

## 2. Invocation triggers

Use this Skill when one or more apply:

- “Test everything”, “click every place”, “find all bugs”, “simulate real users”.
- Competitive analysis, capability parity, open-source analogues, or workflow imitation.
- A release needs broader discovery before `verifier`.
- A product has recurring field escapes, confusing operations, data mismatch, or recovery failures.
- Frontend, backend, API, data, infrastructure and market evidence must be connected.
- The user wants lab data plus real market feedback.

Do not invoke merely to run one known unit test or to adjudicate an already frozen acceptance claim.

## 3. Non-negotiable invariants

### I-01 Discovery is not adjudication

Never emit `PASS`, `VERIFIED`, `PRODUCTION_READY`, or equivalent. Allowed terminal states:

- `READY_FOR_VERIFIER`
- `MORE_EVIDENCE_REQUIRED`
- `FIELD_VALIDATION_PENDING`
- `BLOCKED`

### I-02 Models are explorers, not sole oracles

A model may generate hypotheses, tasks, personas, boundary cases, and usability findings. A critical conclusion requires an independent oracle: business invariant, schema, database/world state, differential result, trace, deterministic assertion, authorized human observation, or field metric.

### I-03 Synthetic is not field evidence

Every result must carry one evidence class:

- `SYNTHETIC`
- `CONTROLLED_HUMAN`
- `FIELD_OBSERVED`

Never promote one class to another.

### I-04 Inventory before coverage

Do not claim coverage until source-visible and runtime-visible surfaces are inventoried and reconciled.

### I-05 Coverage is a vector

Gate critical coverage separately across:

`surface, state, transition, role, data, fault, oracle, evidence`

Do not average away a zero or weak dimension.

Every dimension uses an item-level inventory. Numeric totals are derived caches, not owner-entered claims. The catalog, `items[]`, evidence references and waivers must reconcile exactly; manual counter inflation or denominator deletion is a blocking integrity error.

### I-06 Test the tests

For critical behavior, use mutation testing, response mutation, fault injection, or equivalent negative controls to prove the suite fails when the subject is intentionally broken.

### I-07 Safe experimentation

Active security, load, chaos, destructive actions, production writes, or competitor automation require explicit scope, authorization, blast-radius control, abort and rollback.

### I-08 Provenance-safe competitive learning

Observe and benchmark public or authorized behavior. Reuse open-source code only with exact origin/version/license/notice/modification records. Do not bypass access controls or copy protected branding, private data or private APIs.

### I-09 Field completion is derived

`field_validation_complete` is not a self-attested checkbox. It is true only when a completed `FIELD_OBSERVED` experiment references indexed artifacts whose own evidence class is `FIELD_OBSERVED`, and the field-feedback decision is recorded.

## 4. Operating modes

| Mode | Purpose | Typical output |
|---|---|---|
| `RECON` | Competitor, substitute, OSS and user-pain research | competitor evidence, benchmark tasks, provenance ledger |
| `CENSUS` | Source/runtime inventory and diff | surface graph, inventory diff |
| `MODEL` | Journey/state/fault/oracle model | state graph, fault graph, oracle catalog |
| `LAB` | Deterministic and model-assisted experiments | traces, test results, defects, coverage ledger |
| `POKA_YOKE` | Misoperation prevention and recovery | poka-yoke audit, destructive-action proof |
| `FIELD` | Dogfood, beta, canary and market observation | field experiment and feedback ledgers |
| `CONVERGE` | Fix/retest/defect-yield convergence | closed defects, residual risk, readiness state |
| `FULL` | All phases in risk-controlled order | verifier-ready evidence bundle |
| `DELTA` | Changed surfaces plus affected neighborhood | release-delta coverage and regression evidence |

Default to `FULL` for a new product and `DELTA` for a release candidate with a trusted baseline.

## 5. Required inputs and discovery behavior

### 5.1 Inspect before asking

Read available code, routes, schemas, data migrations, feature flags, permissions, docs, tests, deployment manifests and telemetry before asking the owner. Use a single owner question only when a high-risk decision cannot be inferred, especially authorization, real-money behavior, production blast radius, personal data or irreversible action.

### 5.2 Run Contract

Create `run_contract.json` with:

- exact subject name, repo, commit/deployment digest and environment;
- scope, non-goals and acceptance/claims known so far;
- roles, tenants, flags, devices, browsers, locales and time zones;
- allowed data fixtures and destructive actions;
- authorization, risk tier, budget, token/compute kill switch;
- rollback/restore path and evidence root;
- whether real field validation is required.

If the exact subject changes mid-run, mark the run `BLOCKED` until a new run contract is created.

## 6. Phase protocol

### Phase 0 — Safety envelope

1. Freeze the Run Contract.
2. Classify environment `R0`–`R4` using `references/risk-controls.md`.
3. Prove backup/rollback where destructive actions are permitted.
4. Create evidence and ledger directories.
5. Record tool/model/prompt/config versions.

### Phase 1 — Reality census

Build source and runtime inventories for:

- routes, pages, components, forms, dialogs, menus, shortcuts, uploads/downloads;
- API operations, webhooks, background jobs, queues, schedules and events;
- database entities, constraints, migrations and derived reports;
- roles, permission rules, tenants, auth states and feature flags;
- devices, browsers, viewport classes, locale, timezone and accessibility modes;
- external dependencies, storage, cache, identity, notification and payment systems.

Runtime crawler behavior:

1. Discover interactive elements from DOM and accessibility tree.
2. Canonicalize state using URL, key DOM/AX structure, visible controls, selected business state and network/world-state markers.
3. Deduplicate equivalent states.
4. Label destructive edges and require a disposable fixture or rollback proof.
5. Compare source-visible and runtime-visible inventories.

Do not equate DOM element count with useful coverage.

### Phase 2 — Competitive and OSS recon

Map five reference classes:

1. direct competitors;
2. adjacent competitors;
3. substitutes;
4. manual/internal workarounds;
5. open-source analogues.

For each source, record timestamp, version, source type, public/authorized status, claim, evidence, confidence, task benchmark and provenance. Prefer official docs, changelogs, demos, public issue trackers and original repositories.

Create same-task benchmarks:

- input and starting state;
- steps and decision points;
- task success and time-to-value;
- error prevention and recovery;
- output quality and observability;
- limitations, cost and user complaints;
- what to adopt, reject, or differentiate.

Capability imitation is permitted; untracked copying is not.

### Phase 3 — Product digital twin

Create:

- `surface_graph.json`
- `journey_state_graph.json`
- `fault_graph.json`
- `oracle_catalog.json`

After catalogs and evidence exist, run `sync-coverage`. It creates stable Coverage Item IDs and derives the eight dimension totals. `--auto-cover-evidenced` may mark an item covered only when that catalog item already references indexed evidence; it never invents evidence.

A state node should minimally identify route/task, role, auth, tenant, flags, data fixture, device/browser, locale/timezone and key world state. An edge identifies action, precondition, side effect, expected next state, recovery path and oracle.

Coverage strategy:

- Full enumeration for critical paths and small state spaces.
- t-way combinatorial coverage for high-dimensional configuration factors.
- sequence covering for event/order bugs.
- property/state-machine generation for data and API transitions.
- model-guided and stochastic exploration for unknown/semantic regions.
- field operational profiles to reweight future exploration.

### Phase 4 — Test universe and prioritization

Every test maps:

```text
requirement/claim
  → risk
  → surface/state/edge
  → data/fault condition
  → action sequence
  → oracle
  → evidence artifact
  → result/defect
```

Prioritize by:

```text
expected_loss
× real_usage_probability
× change_heat
× historical_defect_density
× inverse_recoverability
```

Use risk-adjusted priority; do not distribute effort evenly across pages.

### Phase 5 — Lab execution

#### Frontend and operations

- deterministic Playwright journeys across applicable Chromium/Firefox/WebKit;
- desktop/mobile, keyboard, zoom, focus, long text, loading/empty/error states;
- back/refresh/multi-tab/stale page/session expiry/network changes;
- trace, DOM/AX snapshots, network, console, screenshots and videos as appropriate;
- visual and accessibility checks plus manual sampling for issues automation cannot detect.

#### API and backend

- schema/contract, auth, status/error semantics and rate limits;
- property-based and stateful API chains using real response data;
- invalid, boundary, duplicate, malformed, Unicode and time-based data;
- idempotency, retry, ordering, concurrency, locks and transactions;
- jobs, queues, webhooks, cache consistency and dependency failure.

#### Data and world state

- constraints, migrations, summaries and business/financial invariants;
- import/export, backup, restore, partial restore and audit trail;
- cross-system reconciliation where the product promises data coupling;
- prove effects in database/storage/messages/reports, not only UI.

#### Performance

Select by risk: smoke, average-load, stress, spike, breakpoint, soak. Bind load to real user operations and record latency, throughput, error rate, saturation, queue depth, resource use, degradation and recovery.

#### Security, privacy and supply chain

- static code/security analysis;
- passive dynamic scanning by default;
- active scanning only on authorized targets;
- permission boundaries, secrets, session, input handling and data minimization;
- dependency/SBOM and open-source license/provenance scan.

#### Resilience and chaos

Before each fault experiment define steady state, hypothesis, blast radius, abort, rollback and evidence. Cover applicable process/pod, CPU, memory, disk, network, DNS, dependency, cache, queue and storage failures.

#### AI/Agent extension

Record model/prompt/tool/policy versions and cost. Test multi-turn state, tool failure, prompt injection, permission escalation, retries, hallucinated world state, latency and budget. Use repeated trials and an independent judge/oracle.

### Phase 6 — Poka-yoke audit

For each high-loss action assess:

1. applicability visibility;
2. safe defaults;
3. immediate format/business validation;
4. constrained input;
5. impact preview;
6. deliberate confirmation;
7. idempotency/de-dup/double-click protection;
8. undo/rollback/draft/recovery point;
9. actionable error and recovery guidance;
10. permission, audit and accountable owner.

Attack the flow with misclicks, rapid clicks, back, refresh, timeout, weak network, stale/multiple tabs, wrong role, expired session, duplicate upload, extreme input, partial failure and retry.

### Phase 7 — Field reality

Use a staged sequence:

1. dogfood;
2. controlled representative-user tasks;
3. closed beta;
4. feature-flagged canary;
5. segmented expansion with rollback/kill switch.

Observe task success, time-to-value, abandonment, recovery, repeated actions, errors, support burden, adoption, retention and business-specific outcomes. Correlate user events/session replay with traces, logs, feature flags and world-state invariants. Apply privacy masking, access control and sampling.

If field evidence is required but unavailable, terminal state is `FIELD_VALIDATION_PENDING`.

### Phase 8 — Defect convergence

Each valid defect has a stable ID and includes:

- expectation source and severity rationale;
- minimal reproducible fixture and actions;
- expected vs actual;
- subject/environment/tool versions;
- evidence references and hashes;
- user/business impact;
- root-cause hypothesis and confidence;
- owner, fix reference and regression oracle;
- duplicate/root-cause grouping.

After a fix run target regression, affected-neighborhood regression, critical-flow suite, then mutation/fault proof where applicable.

Track unique valid defect yield, duplicate/false-positive rate, cost per defect and field escape rate. Reweight low-yield strategies rather than endlessly repeating them.

### Phase 9 — Handoff

Generate `verifier_intake.json` only when readiness gates are met. Include exact subject, claims, coverage vector, waivers, evidence index, defect status, field evidence class, residual risk and run/tool hashes.

Invoke `verifier` in a separate adjudication context. Reality Lab evidence is input, not a verdict.

## 7. Default critical gates

- Exact frozen subject and reproducible environment.
- Zero open P0/P1; closed P0/P1 have regression evidence.
- 100% critical surface/state/transition/role/data/fault/oracle/evidence closure or explicit owner waiver per item.
- Zero unexplained source/runtime inventory difference.
- Zero unresolved contradictory evidence.
- At least two consecutive deep runs with no new P0/P1.
- Required field validation complete.
- Residual risks, non-critical gaps and waivers are machine-readable.

A project may raise these gates. Lowering a gate requires an owner waiver with scope, reason, expiry, compensating control and evidence.

## 8. Stop and abort rules

Abort immediately if:

- authorization or target identity is uncertain;
- real money, private data or production state may be affected outside scope;
- rollback/abort fails;
- blast radius exceeds contract;
- P0, data leak, unauthorized access or broad corruption is observed;
- subject changes without a new run contract;
- cost/token kill switch triggers.

Stop exploration and prepare handoff when critical gates close, defect yield converges, negative controls remain effective and residual risk is explicit. Do not continue solely to inflate action counts.

## 9. Anti-gaming rules

- Never reduce inventory totals to improve coverage without evidence.
- Never hand-edit derived coverage counters or field-completion booleans to simulate closure.
- Never leave a catalog object outside the item-level coverage inventory.
- Never count duplicate symptoms as unique defects.
- Never treat screenshots, 2xx responses or “no exception” as sufficient business correctness.
- Never let the test generator be the only judge.
- Never label simulated behavior as market validation.
- Never hide waivers in prose.
- Never use a weighted average to mask a failed critical dimension.
- Never claim competitor parity without same-task evidence.

## 10. Tool routing

Use existing project tooling when capable. Otherwise select adapters from `references/tool-routing.md`. Pin versions in the run manifest. The Skill must remain tool-agnostic; tools may change without changing the evidence contract.

Model-assisted tools are optional. Deterministic coverage, evidence integrity and safety gates are mandatory.

## 11. Required outputs

At minimum:

```text
run_contract.json
surface_graph.json
inventory_diff.json
journey_state_graph.json
fault_graph.json
oracle_catalog.json
competitor_evidence.json
provenance_ledger.json
test_matrix.json
coverage_ledger.json
defect_ledger.json
poka_yoke_audit.json
field_experiment.json
field_feedback.json
residual_risk.md
evidence/index.json
```

When ready:

```text
verifier_intake.json
```

Use schemas and templates bundled with this Skill. Evidence files must have stable paths and hashes.

Recommended CLI order:

```text
init → build catalogs/run experiments → index-evidence
→ sync-coverage --auto-cover-evidenced → validate → score
→ handoff (only when READY_FOR_VERIFIER)
```

## 12. Reporting contract

Lead with:

1. current terminal status;
2. next concrete action;
3. new P0/P1 findings;
4. eight-dimensional coverage gaps;
5. field evidence state;
6. cost/defect yield and stop decision.

Keep exploration details in artifacts, not in a noisy chat transcript.
