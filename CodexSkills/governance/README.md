# SkillOps Mechanism governance

Status: **DRAFT_NON_ACTIVE**

This directory is the Mechanism half of the SkillOps v0.0.0.3 contract. It
contains only Mechanism-owned schemas, policy instances, deterministic
canonicalization, offline validation, provenance, fixtures, and tests. It is
not an active release and is not a second Registry or run-log fact source.

Key entrypoints:

- `tools/canonical_json.py`: strict I-JSON input and RFC 8785 canonical bytes.
- `tools/validate_mechanism.py`: unique offline schema/policy/artifact gate.
- `tools/build_draft.py`: deterministic materialization and byte check.
- `tools/build_candidate_bundle.py`: deterministic complete candidate manifest.
- `tools/build_activation_control.py`: deterministic two-stage activation
  control schemas and pinned interface.
- `tools/validate_activation.py`: offline intent/receipt/settlement and physical
  write-set validator.
- `tools/validate_public_run_event.py`: Mechanism-owned semantic consumer for
  the Auto-owned `public-run-event:v2` schema.
- `tools/build_au040_semantic_acceptance.py`: deterministic, loader-isolated
  AU-040 policy/schema acceptance materialization.
- `tools/build_bound_reference_resolver.py`: immutable source-catalog,
  Registry-snapshot, and source-drift reconciliation materialization.
- `release/foundations.py`: pure unbounded-SRV allocation, impact,
  policy-precedence, and machine-readable Handoff gates.
- `tools/build_release_foundations.py`: deterministic non-active M0 foundation
  interface and policy-reconciliation evidence.
- `release/version_policy_v3/contract.py`: exact v2→v3 compatibility,
  locked-impact, SRV/daily-transaction separation, notification, and unresolved
  schedule gates.
- `release/version_policy_v3/consumer.py`: externally trusted, explicit
  v2/v3 dual-read selection with hybrid and schedule fail-closed gates.
- `tools/build_version_policy_v3_draft.py`: deterministic bundle-external
  version-policy v3 draft and consumer-first handoff.
- `tools/build_version_policy_v3_consumer_readiness.py`: deterministic
  Mechanism dual-read readiness and actual cross-plane consumer inventory.
- `promotion/controller.py`: pure append-only `PROMOTE` / `REJECT`
  controller with complete Registry, evaluation, evidence, and decision
  closure; no state writer or activation authority.
- `tools/build_promotion_controller.py`: deterministic M-056 readiness bound
  to the final candidate and registered read-only Registry snapshot.
- `promotion/rollback_controller.py`: pure mixed lifecycle-ledger replay for
  `PROMOTE`, `REJECT`, `ROLLBACK`, and `REVOKE`, with prior-champion proof,
  restore-drill closure, revoked-target exclusion, and notification ordering.
- `tools/build_rollback_revocation_controller.py`: deterministic M-057
  bundle-external drill schema and readiness bound to the immutable M-056
  predecessor, final candidate, and registered read-only Registry snapshot.
- `monitoring/freshness_drift.py`: pure M-058 stale/behavior/latency/context
  monitor and exact report-recomputation gate in front of M-056 promotion.
- `tools/build_freshness_drift_monitor.py`: deterministic M-058
  bundle-external observation/report schemas and non-active readiness bound to
  the immutable M-056/M-057 predecessors.
- `release/policy_protection.py`: pure M-059 protected-surface classifier,
  seven-operation optimizer access-denial gate, and exact M-059 → M-058 →
  M-056 promotion delegation.
- `tools/build_evaluator_release_protection.py`: deterministic M-059
  bundle-external observation/report schemas and non-active readiness bound to
  the candidate, M-056, M-058, and version-policy v3 trust roots.
- `retention/root_lifecycle.py`: pure M-060 realpath-aware protected-local,
  managed-raw, and public-queue scope classifier; private paths are never
  serialized and its only positive result is later M-061 time evaluation.
- `tools/build_protected_local_raw_boundary.py`: deterministic M-060
  bundle-external observation/report schemas and non-active readiness bound to
  the exact candidate, retention-policy:v3, raw-segment:v2, and
  public-run-event:v2 contracts.
- `retention/managed_raw_policy.py`: pure M-061 UTC elapsed-time stages,
  exact 72-hour boundary, offline-breach evidence, deterministic action plan,
  and receipt-to-M-060 scope binding; no physical path or mutation authority.
- `tools/build_managed_raw_72h_policy.py`: deterministic M-061
  bundle-external observation/plan/readiness schemas bound to the exact
  candidate, immutable M-060 predecessor, retention-policy:v3,
  raw-segment:v2, and retention-receipt:v3 contracts.
- `tools/validate_au040_semantic_acceptance.py`: exact 365-day and
  shard/index/manifest/publication cross-artifact gates.
- `tests/test_mechanism_contract.py`: positive, negative, and fault gates.
- `tests/test_activation_contract.py`: M0c activation cycle, provider, and
  byte-binding gates.
- `tests/test_au040_semantic_policy_acceptance.py`: policy-version,
  retention-boundary, manifest-chain, physical-byte, and transaction-closure
  regressions.
- `tests/test_version_policy_v3_draft.py`: v2 gap closure, impact
  non-downgrade, schedule-authority, notification, privacy, and
  candidate/control non-mutation regressions.
- `tests/test_version_policy_v3_consumer_readiness.py`: immutable external
  trust tuples, v2/v3 selection, schedule fail-closed, and actual Auto
  v2-only transition evidence.
- `draft-interface.json`: exact M0a interface for Auto A1a.
- `bundles/schema-bundle-manifest.v1.json`: final non-active 31/5 candidate
  manifest.
- `activation/control-interface.json`: non-active successor control binding the
  final candidate, V2 consumer, and exact integrated Auto runtime interface.
- `au040/semantic-policy-acceptance.json`: non-active handoff that accepts the
  four exact Auto transport-schema byte digests and freezes the two versioned
  Mechanism policy replacements plus seven production semantic guards.
- `OpenAIDatabase/scripts/validate_skill_run_logs.py`: four-artifact daily
  ledger consumer and pre-activation publication block.

Run from the repository root with the explicitly provisioned interpreter:

```bash
/usr/bin/python3 -B CodexSkills/governance/tools/build_draft.py --check
/usr/bin/python3 -B CodexSkills/governance/tools/build_candidate_bundle.py --check
/usr/bin/python3 -B \
  CodexSkills/governance/tools/build_activation_control.py --check
/usr/bin/python3 -B \
  CodexSkills/governance/tools/build_bound_reference_resolver.py --check
/usr/bin/python3 -B \
  CodexSkills/governance/tools/build_release_foundations.py --check
/usr/bin/python3 -B \
  CodexSkills/governance/tools/build_version_policy_v3_draft.py --check
/usr/bin/python3 -B \
  CodexSkills/governance/tools/build_version_policy_v3_consumer_readiness.py \
  --check
/usr/bin/python3 -B \
  CodexSkills/governance/tools/build_promotion_controller.py --check
/usr/bin/python3 -B \
  CodexSkills/governance/tools/build_rollback_revocation_controller.py \
  --check
/usr/bin/python3 -B \
  CodexSkills/governance/tools/build_freshness_drift_monitor.py --check
/usr/bin/python3 -B \
  CodexSkills/governance/tools/build_evaluator_release_protection.py \
  --check
/usr/bin/python3 -B \
  CodexSkills/governance/tools/build_protected_local_raw_boundary.py \
  --check
/usr/bin/python3 -B \
  CodexSkills/governance/tools/build_managed_raw_72h_policy.py --check
/usr/bin/python3 -B CodexSkills/governance/tools/validate_mechanism.py lint-draft
/usr/bin/python3 -B \
  CodexSkills/governance/tools/validate_activation.py lint-control
/usr/bin/python3 -B \
  CodexSkills/governance/tools/build_au040_semantic_acceptance.py --check
/usr/bin/python3 -B \
  CodexSkills/governance/tools/validate_au040_semantic_acceptance.py \
  lint-acceptance
/usr/bin/python3 -B CodexSkills/governance/tools/validate_mechanism.py \
  lint-schema-set --schema-dir CodexSkills/governance/schemas
/usr/bin/python3 -B CodexSkills/governance/tools/validate_mechanism.py \
  lint-schema-set --schema-dir CodexSkills/governance/schemas \
  --schema-dir CodexSkills/governance/schemas-v2 \
  --schema-dir CodexSkills/governance/release/schemas \
  --schema-dir CodexSkills/registry/auto/schemas/public \
  --schema-dir CodexSkills/registry/auto/schemas/public-v2
/usr/bin/python3 -B CodexSkills/governance/tools/validate_mechanism.py \
  lint-schema-set \
  --schema-dir CodexSkills/governance/schemas \
  --schema-dir CodexSkills/governance/release/version_policy_v3/schemas
/usr/bin/python3 -B -m unittest discover \
  -s CodexSkills/governance/tests -p 'test_*.py'
```

No command in this directory downloads dependencies or resolves schemas over
the network. The final candidate assembles exactly 21 Mechanism schemas, ten
Auto-public schemas, and five Mechanism policies. The four Auto-private
schemas are never bundle members.

The two schemas under `activation/schemas/` are bootstrap-control contracts,
not members of the 31-schema runtime bundle. This is deliberate: activation
cannot trust the bundle it is in the process of activating. Their exact IDs,
paths, canonical schema digests, self-digest pointers, candidate bundle, and
Auto transport interface are pinned in `activation/control-interface.json`.
Runtime consumers must additionally supply the repo-external verified M0c-A
Git object, expected raw control-interface SHA-256, canonical interface path,
and `DRAFT_NON_ACTIVE_CONTROL` mode. The checkout cannot trust its own control
interface by self-report.

Activation is a mandatory two-stage transaction. A pre-notification intent
binds the complete planned path set and every pre-send-known digest. Only after
the production provider returns `SENT` and exact readback may a settlement bind
the notification receipt and all final artifact bytes. The settlement excludes
itself from its artifact list to avoid a self-hash cycle; the publisher must
recompute it as a distinguished control artifact and require the final request
paths to equal `settlement.artifacts + settlement`. A caller-supplied
`activation_envelope_verified` boolean is never a trust root.

The notification carries only conservative low-entropy path scopes; the intent
digest binds the exact receipt filenames. Public JSON activation artifacts use
RFC 8785 JCS UTF-8 bytes without a BOM or trailing newline. Physical reads are
descriptor-relative and fail closed on symlink roots, parents, or files.

Runtime artifacts are validated only against a caller-selected trusted schema
ID and external expected bundle digest. Candidate/ACTIVE bootstrap additionally
requires a repo-external tuple of verified Git object ID, expected bundle
digest, canonical manifest path, and mode. Losing that external state fails
closed; the current checkout cannot promote its own manifest to trusted.

The final manifest and coordinated control interface remain
`DRAFT_NON_ACTIVE`. They do not create
`CodexSkills/VERSION`, authorize canonical publication, or establish an ACTIVE
trust root. After commit, verify it with `trust-bundle` using the externally
read-back commit, candidate digest, canonical manifest path, and
`mode=CANDIDATE`.

The consumer-first gate is separately installed under OpenAIDatabase. It
recognizes recursive `part-NNNN.jsonl`, retained `index-NNNN.jsonl`,
`manifest-NNNN.json`, and `retention-receipt-NNNN.json` artifacts while
leaving the four sibling task-run categories unchanged. The repository run
root must remain README-only until ACTIVE external trust, Auto AU-040
writer/integration, and a production-trusted Mechanism BOUND resolver gate all
exist.
Synthetic complete daily trees may be tested; this draft does not authorize
canonical run-log publication.

The final candidate consumes the exact promoted Auto schema bytes under
`schemas/public-v2/` plus the accepted Mechanism policy schemas and instances
under `schemas-v2/` and `policies-v2/`. It is exactly 31 schemas and five
policies: both policy contracts and both replaced Auto transport contracts are
versioned replacements, never in-place mutations. The old 29/5 candidate
remains readable only through its exact historical object/digest; hybrid sets
are rejected and no predecessor ACTIVE compatibility is implied.

Schema shape alone is insufficient for the daily ledger. Production must also
consume the Mechanism semantic guard set: exact 365 elapsed days from
`first_published_at`, strict post-boundary eligibility, exact predecessor
manifest chaining, immutable part metadata, index/event/manifest and physical
byte closure, paired part/index/manifest publication, and paired
part-delete/retention-receipt/manifest publication. The Auto draft validator
is useful draft evidence but is explicitly not a production trust root.

The previously synchronized control remains immutable historical evidence,
but the later Teleiosis source addition invalidates its 88-root Registry tuple.
It must not be treated as authority for the current working tree or the new
snapshot. Until a later Auto exact-tuple integration and a separate Mechanism
control sync both finish, `bound_reference_resolver_gate_satisfied`,
`runtime_state_write_permitted`, and `production_trust_permitted` remain
false. No state root, lock, worktree, mutable Git, Gmail, outbox, watermark,
shard, publisher, activation, or VERSION instance is created here.

The isolated version-policy v3 draft under
`CodexSkills/governance/release/version_policy_v3/` closes the six MAJOR
trigger codes omitted by v2, preserves all seven existing MAJOR codes, and
makes the global SRV / daily `auto_transaction_uid` separation explicit.
Unknown or duplicate trigger codes fail closed and impact cannot be
downgraded. Planned MAJOR writes still require provider `SENT`; owner approval
and reply remain false, while the actual recipient mapping remains
repo-external.

This draft deliberately records both observed schedule candidates (`04:15`
and `05:30`) without choosing between them. Its authority state is
`UNRESOLVED`, `daily_schedule_local=null`, and
`schedule_activation_permitted=false`. The Mechanism dual-read consumer now
accepts exact v2 as `PREDECESSOR_READ_ONLY` and exact v3 as
`SUCCESSOR_SHADOW`; it rejects implicit or hybrid selection and keeps both
schedule reads non-authorizing. The v3 schema and policy are not members of
the trusted 31/5 candidate, the activation control remains byte-identical,
and `CodexSkills/VERSION` remains absent.

The bundle-outside Registry contract is under
`CodexSkills/governance/registry/`. Its current materialization consumes
source object `sha1:a8f1f6ff…` and immutable Auto evidence
`sha1:1c829553…`. It produces four draft catalogs, four byte-identical
registered catalogs, and one 89-root registered snapshot. Counts close at
24 AGENTS + 3 CLAUDE + 56 CODEX + 6 CODEX_SYSTEM, with 20/20 aliases,
zero invalid metadata roots, and zero binding-eligible Versions.

The registered 88-root predecessor is loaded only from
`sha1:df63339e…`. All 88 assignments, Identity records, Instance records,
and Version records are preserved byte-for-byte. The only new record chain is
`codex/teleiosis`; it is `QUARANTINED/UNVERIFIED`, has no EvalProfile or
PromotionDecision, and cannot emit BOUND. Real resolution therefore remains
`UNKNOWN/MAPPING_NOT_PROVABLE`. A separate synthetic registered fixture still
proves the resolver's exact seven-field BOUND output, including
controlled-invocation, content/tree, version-record, and snapshot digests.

At the registered 89-root object, `codex/context-kernel` is absent and
`UNOBSERVED`; its older records remain only in immutable historical evidence.
The later external `dd338e1` commit restored a working-tree mirror path without
adding a catalog assignment or registered snapshot record. That unreconciled
path does not create a deletion transition, registration, promotion, or
binding. Registered-snapshot/current-tree parity is therefore false.

Two independent prerequisite lanes remain explicit:

- Registry/control: `AUTO_TELEIOSIS_REGISTRY_EXACT_TUPLE_INTEGRATION` may bind
  only the remotely verified Mechanism successor object, resolver-interface
  bytes, and registered snapshot digest.
- Version policy:
  `MECHANISM_VERSION_POLICY_V3_CONSUMER_FIRST_READINESS` proves the Mechanism
  consumer and inventories the real unchanged Auto consumers. Auto schedule
  and notification remain v2-only and Auto bootstrap remains candidate-only,
  so cross-plane readiness is false and v3 may not join the candidate. The
  only handoff is `AUTO_VERSION_POLICY_V3_DUAL_READ_INTEGRATION`.

Schedule authority, resolver production trust, external Gmail/state readiness,
runtime state-instance creation, AU-040 completion, M0c-B, ACTIVE trust,
canonical shard creation, and canonical publication remain false.

The M-058 monitor is also bundle-external and non-active. It never trusts a
stored `freshness_state` alone: UTC age/date expiry, behavior scores, latency
sample/p95 evidence, execution context, incidents, and EvalProfile trigger
coverage are recomputed into one exact report. A `PROMOTE` append must enter
through the monitored wrapper with one `PROMOTION_GATE/PASS` report per
Scorecard; the immutable M-056 function is called only after that closure
passes. Repository presence, a caller-supplied clear flag, or an omitted
retest trigger cannot authorize promotion.

M-059 adds a second bundle-external gate in front of that monitored promotion
path. It validates exact denied attempts for optimizer reads of sealed labels
and writes to evaluator, EvalProfile, rubric, hard gates, promotion controller,
and release policy. Actor references must be distinct, the change-origin role
must bind its exact actor, and the isolation digest is recomputed rather than
trusted from a caller flag.

EvalProfile, judge, holdout, promotion-controller, and all five release-policy
descriptors are compared deterministically. Every detected protected change is
classified through the exact version-policy v3 vocabulary and must resolve to
`MAJOR`. An optimizer-originated change is blocked; an independently
originated change is isolated to a separate MAJOR release and still cannot
reuse the Skill promotion transaction. Only an unchanged protected snapshot
with a complete access-denial audit may delegate to M-058. The guard returns
canonical evidence only and does not authorize release writes, notification,
Registry/state mutation, activation, or publication.

The M-060 root-lifecycle guard is likewise bundle-external and non-active. Its
physical `RootBinding.path` values stay in memory and are replaced in evidence
by low-entropy refs. `SKILL_SOURCE`, `RUN_SOURCE`, and `LEGACY_DATA` always map
to `PROTECTED_LOCAL_DATA`; their TTL selection and delete budget are both zero.
`PUBLIC_QUEUE` remains a non-raw queue retained until remote verification.
Only `STAGING` maps to `MANAGED_RAW_SPOOL`, and even there the guard requires
the exact private `raw-segment:v2` schema, recomputed ownership marker, and
payload byte/digest closure.

An M-060 positive result is
`ELIGIBLE_FOR_M061_TIME_EVALUATION`, not expiry or delete authority. Persistent
raw remains disabled by default, production certification is pending M-061,
offline hard-guarantee claims remain false, and M-060 performs no clock
evaluation, receipt generation, mutation, publication, state write, or
activation.
