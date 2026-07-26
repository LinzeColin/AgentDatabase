# Mechanism handoff

- State: `DRAFT_NON_ACTIVE_SOURCE_DRIFT_RECONCILED`
- Phase: `MECHANISM_REGISTRY_SOURCE_DRIFT_RECONCILIATION`
- Protocol:
  `urn:linzecolin:agentdatabase:skillops:protocol:cross-pack:v1`
- SRV candidate: `v0.0.0.3`
- Candidate bundle digest:
  `36f0c66dd54d36365700a13f614a8c9bfa9619fb7c532af77566a858175b835e`
- Candidate Git object:
  `sha1:5ee37d7499c62ec19381dac7eb95cb12743ad2d5`
- Consumer Git object:
  `sha1:91a12e48351be3ee05ec23ef61aec81056b02014`
- Integrated Auto Git object:
  `sha1:b5a32c817e4016f595fa33caed6bce1d51199e63`
- Integrated Auto runtime-interface raw SHA-256:
  `e88ec8c711434619756ee8f91c451e941501764e30e4a7fff310d8685b02140a`
- Control interface raw SHA-256:
  `a31751bf1258f646412aba84e0b5c46f84f09b77e33156caea372873b819ff36`
- Resolver interface raw SHA-256:
  `38c7952ae712e6d4543bb4f4c1f3e5f8a98b00b36780c99bfce6944a722eabf0`
- Source-drift reconciliation self digest:
  `24d02db5182463912074c109f2b5be350126d62340f58e6463755edbad1b799c`
- Draft Registry snapshot digest:
  `31f49c8ffa3bd2d268feec49b2869f409d61a5bfbb0b03f382bc562996b7fa76`

These Git objects are ordinary ancestors in the coordinated local commit
chain. A downstream consumer must independently fetch and read them back from
the remote before treating either as an external trust root.

## Final candidate

- The manifest contains exactly 21 Mechanism schemas, ten Auto-public schemas,
  and five Mechanism policies. Four Auto-private schemas remain excluded.
- It replaces, rather than mutates, `public-value-policy:v1`,
  `retention-policy:v2`, `publication-manifest:v1`, and
  `retention-receipt:v2`.
- The replacements are `public-value-policy:v2`, `retention-policy:v3`,
  `publication-manifest:v2`, and `retention-receipt:v3`; the bundle also adds
  `daily-run-shard-manifest:v1` and `run-event-index-entry:v1`.
- Every member is bound to one canonical owner path and canonical RFC 8785
  digest. The trusted loader accepts only the exact historical 29/5 profile or
  this exact final 31/5 profile; hybrid member sets fail closed.
- The historical non-active 29/5 candidate remains readable only through its
  exact old Git object and digest. It is not an accepted predecessor ACTIVE
  bundle and is not implicitly compatible.
- The manifest remains `DRAFT_NON_ACTIVE`. No `CodexSkills/VERSION`, ACTIVE
  trust state, activation artifact, or canonical publication was created.

## AU-040 consumer

- `OpenAIDatabase/config/evaluation/skill_run_consumer.json` revision V2 pins
  the final candidate Git object, digest, manifest path, and protocol.
- The consumer closes four distinct daily artifacts:
  `part-NNNN.jsonl` (`public-run-event:v2`),
  `index-NNNN.jsonl` (`run-event-index-entry:v1`),
  `manifest-NNNN.json` (`daily-run-shard-manifest:v1`), and
  `retention-receipt-NNNN.json` (`retention-receipt:v3`).
- Synthetic validation binds RFC 8785 bytes, event/index rows, physical
  digests and sizes, Sydney day, immutable manifest revisions, retained
  indexes, pruned-part absence, and exact receipt links.
- The canonical run-log root remains README-only.
  `repository_shards_permitted=false` and
  `canonical_publication_permitted=false`; path/schema closure does not claim
  Auto writer, publisher, retention executor, or AU-040 completion.

## Activation control

- `CodexSkills/governance/activation/control-interface.json` pins the final
  candidate object, the V2 consumer object, the integrated Auto object
  `sha1:b5a32c817e4016f595fa33caed6bce1d51199e63`, and its exact
  runtime-interface bytes.
- Mechanism independently verifies all 27 Auto module digests declared by that
  interface against the pinned Git object. It also verifies Auto's historical
  control observation, including predecessor control
  `sha1:e6438db785c2f3f38da59be7ba9c1cd46651d7ea`, its exact bound
  `85edc67d…` / `ce3aae7a…` / 25-module Auto tuple, and four Mechanism
  runtime blobs, from immutable Git objects rather than from the working tree.
  The separate writer, publisher, and repository-binding materialization
  snapshots remain historical evidence. The historical 29/5 tuple remains
  lineage only.
- The successor control records `auto_runtime_integration_complete=true` and
  `runtime_shard_writer_integration_complete=true` together with
  `publisher_v2_runtime_integration_complete=true` and
  `repository_binding_integration_complete=true`. It establishes the exact
  repository authority as `repository_bound=true`, while keeping
  `bound_reference_resolver_gate_satisfied=false`.
- It now also binds the byte-equivalent Mechanism resolver interface and
  records `bound_reference_resolver_implementation_complete=true`.
  `bound_reference_resolver_auto_integration_complete=false` remains
  truthful: implementation is not the same as an Auto-consumed production
  gate.
- The control-level `runtime_state_write_permitted=true` means only that the
  exact candidate/control tuple has reached the state-writing gate. Effective
  state writing is separately recorded as
  `effective_runtime_state_write_permitted=false` with status
  `BOUND_REFERENCE_RESOLVER_SOURCE_CONTENT_SYNC_PENDING`; state, lock,
  worktree, mutable Git, Gmail, outbox, watermark, and publisher access remain
  blocked before side effects with `BOUND_REFERENCE_RESOLVER_NOT_SATISFIED`.
- Auto's
  `runtime_interface_materialization_snapshot.current_auto_runtime_control_bound=false`
  and
  `publisher_v2_runtime_materialization_snapshot.current_auto_runtime_control_bound=false`
  and
  `repository_binding_materialization_snapshot.current_auto_runtime_control_bound=false`
  remain truthful historical snapshots of their materialization points. None
  is rewritten or treated as the successor control's authorization value.
- Activation remains forbidden. A future runtime must still use the existing
  intent → real provider `SENT` readback → settlement → FF publish → remote
  byte readback sequence with repo-external trust tuples.
- Caller booleans, repository self-report, digest maps, provider status
  strings, or the current checkout are never trust roots.

## Registry and BOUND resolver

- `CodexSkills/governance/registry/resolver-interface.json` binds four
  bundle-outside schemas, the resolver/builder bytes, four historical source
  catalogs, one immutable historical Registry snapshot, and the current
  source-drift reconciliation. Production loading requires a
  repo-external candidate tuple and a separate snapshot tuple containing the
  verified Git object, snapshot digest, canonical path, schema ID, and mode.
- The pinned source observation is Git object `sha1:44a38890…`: 89 Skill
  roots close to 89 distinct Identity, Instance, and Version records
  (`agents=24`, `claude=3`, `codex=56`, `codex-system=6`). Same names across
  sources remain separate; 14 name groups are explicit owner-review merge
  candidates.
- Every observed version is `QUARANTINED/UNVERIFIED`, with unknown permission
  and provenance fields represented explicitly. The single invalid metadata
  root is `codex/context-kernel`; no eval profile or promotion decision is
  fabricated.
- Auto object `sha1:b5a32c81…` proves that `_catalog` and `_global` are
  reserved and that source/mirror aliases close exactly at 20/20. Current
  source and mirror roots close at 88, not the historical 89:
  `codex/context-kernel` is absent. The reconciliation records that absence as
  `UNOBSERVED`, retains its historical Identity/Instance/Version references,
  and forbids inferred lifecycle transition, binding, or promotion.
- Exact live-source content drift remains for `codex/graphify`,
  `codex/persona-distiller-group`, and `codex/verifier`. Until Auto performs
  the exact content sync and Mechanism rebuilds from its successor Git object,
  the historical snapshot remains `INCOMPLETE`, non-promotable, and at zero
  binding-eligible versions. Real requests deterministically return
  `UNKNOWN/MAPPING_NOT_PROVABLE`; no real `skill_ref` is emitted.
- A registered synthetic fixture proves the same implementation emits BOUND
  only after `REGISTERED + COMPLETE` parity, known provenance/permissions,
  eligible lifecycle state, exact controlled-invocation self digest, and
  unique identity → instance → version/content/tree/record digest closure.
- Draft catalogs stay under
  `CodexSkills/governance/registry/materialized/**`. Auto's sync executor now
  excludes the reserved Registry namespaces from Skill enumeration and
  deletion, but no final Registry catalog or snapshot artifact exists. The
  incomplete 44a materialization is explicitly historical and
  non-promotable. After Auto closes the three exact content drifts, Mechanism
  must rebuild from that successor Git object; exact-byte promotion applies
  only to the complete successor.

## Unresolved gates

- Schedule authority is unresolved: the locked 04:15 value conflicts with a
  later 05:30 objective that did not explicitly override it. Neither time is
  final.
- AU-040 completion, source-content parity, promotable Registry rebuild,
  resolver Auto integration, production Registry trust, ACTIVE external trust,
  Gmail/state readiness, real-message metadata readback, runtime
  state-instance creation, M0c-B, A1c, canonical publication, and verifier
  review all remain false or unperformed. No canonical shard, index, daily
  manifest, retention receipt, or BOUND run event was created.
- The 72-hour retention behavior remains limited by host/App availability;
  recovery must record an offline breach/gap and may not claim an impossible
  hard guarantee.

## Next exact action

After this control is committed, FF-pushed, and independently read back, the
only machine next phase is `AUTO_REGISTRY_SOURCE_CONTENT_SYNC`. That
Auto-owned phase must exact-sync `codex/graphify`,
`codex/persona-distiller-group`, and `codex/verifier`, preserve the reserved
Registry namespaces and 20 aliases, and represent the absent
`codex/context-kernel` source root truthfully without restoring it from
historical mirror evidence. It must not generate or promote Registry
catalogs/snapshots, treat resolver implementation or repository binding as
AU-040 completion, create canonical shards, publish, touch Gmail/state,
activate, create VERSION, change automation, or resolve the schedule conflict.

Development still must not call verifier. After both planes are complete, the
Owner will designate the last completed task to invoke a fresh verifier.
