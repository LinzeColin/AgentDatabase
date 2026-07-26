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
- `tools/validate_au040_semantic_acceptance.py`: exact 365-day and
  shard/index/manifest/publication cross-artifact gates.
- `tests/test_mechanism_contract.py`: positive, negative, and fault gates.
- `tests/test_activation_contract.py`: M0c activation cycle, provider, and
  byte-binding gates.
- `tests/test_au040_semantic_policy_acceptance.py`: policy-version,
  retention-boundary, manifest-chain, physical-byte, and transaction-closure
  regressions.
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
  --schema-dir CodexSkills/registry/auto/schemas/public \
  --schema-dir CodexSkills/registry/auto/schemas/public-v2
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

The successor control binds the exact final candidate and V2 consumer plus
Auto corrective object `sha1:3feb585…`, runtime-interface digest `3ca77e…`,
and 29 declared module digests. It independently verifies that the corrective
preserved the exact interface materialized at `sha1:6fe7c09…`, as well as the
immutable predecessor controls, Mechanism runtime blobs, and writer,
publisher, repository-binding, Registry, and resolver snapshots. The working
tree is never substituted as historical evidence.

The control records writer, publisher-v2, repository binding, and BOUND
resolver Auto integration as complete. It establishes
`repository_bound=true`,
`bound_reference_resolver_gate_satisfied=true`,
`runtime_state_write_permitted=true`, and
`effective_runtime_state_write_permitted=true`, with
`runtime_state_write_gate_status=ENABLED_BY_CONTROL`. Resolver production
trust still yields only `UNKNOWN/MAPPING_NOT_PROVABLE` for all 88 current
Versions because `binding_eligible_version_count=0`;
`current_snapshot_can_emit_bound=false` remains mandatory. Auto's historical
materialization snapshots stay `current_auto_runtime_control_bound=false` and
are not rewritten into successor authority. No state root, lock, worktree,
mutable Git, Gmail, outbox, watermark, shard, publisher, activation, or
VERSION instance is created here. Activation and canonical publication remain
forbidden. The only next Phase is the read-only
`MECHANISM_EXTERNAL_RUNTIME_READINESS_PREFLIGHT`.

The bundle-outside Registry contract is under
`CodexSkills/governance/registry/`. It materializes four draft source catalogs
and one immutable snapshot from pinned Git object `sha1:44a38890…`, with 89
separate Identity/Instance/Version records and explicit owner-review
candidates for same-name cross-source identities. The successor Auto evidence
at `sha1:b5a32c81…` proves the reserved `_catalog`/`_global` namespaces and
20/20 source/mirror alias parity, but the current source set is 88 roots:
`codex/context-kernel` is absent and `codex/graphify`,
`codex/persona-distiller-group`, and `codex/verifier` have exact content drift
pending Auto sync. The missing root is recorded as `UNOBSERVED`; its historical
Identity/Instance/Version records are retained, with no inferred lifecycle
transition. The new reconciliation artifact is non-promotable, all historical
89 versions remain quarantined, binding eligibility is zero, and real
resolution returns `UNKNOWN/MAPPING_NOT_PROVABLE`. A separate registered
fixture proves the same resolver's exact seven-field BOUND output, including
controlled-invocation, content/tree, version-record, and snapshot digests.

The Auto sync executor now excludes the reserved Registry namespaces from
Skill enumeration and deletion. No final catalog or snapshot artifact has
been generated, and the incomplete 44a materialization remains historical,
non-promotable evidence. The next Auto phase must exact-sync the three drifted
source roots without fabricating the missing root. Mechanism must then rebuild
from that successor Git object; exact-byte promotion applies only after full
current-source closure. Implementation or path reservation alone does not
satisfy the resolver gate.
Schedule authority, resolver Auto integration and production trust, external
Gmail/state readiness, runtime state-instance creation, AU-040 completion,
M0c-B, ACTIVE trust, canonical shard creation, and canonical publication
remain false.
