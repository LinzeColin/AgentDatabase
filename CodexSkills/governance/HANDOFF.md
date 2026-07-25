# Mechanism handoff

- State: `DRAFT_NON_ACTIVE_POST_AU040_REPOSITORY_BINDING_CONTROL_SYNC`
- Phase: `MECHANISM_POST_AU040_REPOSITORY_BINDING_CONTROL_SYNC`
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
  `sha1:49ac09dbd9c8a2e18d5a199088a910dc77e7d365`
- Integrated Auto runtime-interface raw SHA-256:
  `c7af9d1406fe2ed084d5a30fab6cded3897a83c1602e6c40587cf28c75a2c75c`
- Control interface raw SHA-256:
  `db9b83ac2e841300bf7cf1150cad989d609128cffb40160cd17c426d326490d3`

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
  `sha1:49ac09dbd9c8a2e18d5a199088a910dc77e7d365`, and its exact
  runtime-interface bytes.
- Mechanism independently verifies all 26 Auto module digests declared by that
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
- The control-level `runtime_state_write_permitted=true` means only that the
  exact candidate/control tuple has reached the state-writing gate. Effective
  state writing is separately recorded as
  `effective_runtime_state_write_permitted=false` with status
  `BOUND_REFERENCE_RESOLVER_PENDING`; state, lock, worktree, mutable Git,
  Gmail, outbox, watermark, and publisher access remain blocked before side
  effects with `BOUND_REFERENCE_RESOLVER_NOT_SATISFIED`.
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

## Unresolved gates

- Schedule authority is unresolved: the locked 04:15 value conflicts with a
  later 05:30 objective that did not explicitly override it. Neither time is
  final.
- AU-040 completion, BOUND reference resolver, ACTIVE external trust,
  Gmail/state readiness, real-message metadata readback, runtime
  state-instance creation, M0c-B, A1c, canonical publication, and verifier
  review all remain false or unperformed. No canonical shard, index, daily
  manifest, or retention receipt instance was created.
- The 72-hour retention behavior remains limited by host/App availability;
  recovery must record an offline breach/gap and may not claim an impossible
  hard guarantee.

## Next exact action

After this control is committed, FF-pushed, and independently read back, the
only machine next phase is
`MECHANISM_BOUND_REFERENCE_RESOLVER_IMPLEMENTATION`. That future Mechanism
phase must build the immutable Registry snapshot tuple and exact
identity → instance → version resolver closure required by the Auto dependency
contract. It must not treat repository binding as AU-040 completion or
permission to create canonical shards, publish, touch Gmail/state, activate,
create VERSION, change automation, or resolve the schedule conflict.

Development still must not call verifier. After both planes are complete, the
Owner will designate the last completed task to invoke a fresh verifier.
