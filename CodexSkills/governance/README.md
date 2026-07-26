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

`codex/context-kernel` remains absent and `UNOBSERVED`. Its older records are
retained only through the immutable historical reconciliation object; no
current catalog entry, deletion transition, promotion, or binding is
fabricated. Current 89-root source/mirror parity is complete, while historical
whole-source/root parity remains false.

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
