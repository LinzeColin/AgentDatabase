# Mechanism handoff

- State: `DRAFT_NON_ACTIVE_FINAL_CANDIDATE_CONTROL`
- Phase: `MECHANISM_FINAL_31_5_CANDIDATE_CONSUMER_CONTROL`
- Protocol:
  `urn:linzecolin:agentdatabase:skillops:protocol:cross-pack:v1`
- SRV candidate: `v0.0.0.3`
- Candidate bundle digest:
  `36f0c66dd54d36365700a13f614a8c9bfa9619fb7c532af77566a858175b835e`
- Candidate Git object:
  `sha1:5ee37d7499c62ec19381dac7eb95cb12743ad2d5`
- Consumer Git object:
  `sha1:91a12e48351be3ee05ec23ef61aec81056b02014`
- Control interface raw SHA-256:
  `86e4d625bdab87261a39c949883d410822e25e0222dbab6a333d171ce420c614`

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
  candidate object, the V2 consumer object, and Auto's verified historical
  promotion/runtime evidence object
  `sha1:d16273c26b859379578ea9ec04e1473f175d14f6`.
- The source Auto runtime remains pinned to the historical 29/5 candidate.
  The control records `auto_runtime_integration_complete=false` and requires a
  separate `AUTO_EXACT_BUNDLE_INTEGRATION` phase.
- Activation remains forbidden. A future runtime must still use the existing
  intent → real provider `SENT` readback → settlement → FF publish → remote
  byte readback sequence with repo-external trust tuples.
- Caller booleans, repository self-report, digest maps, provider status
  strings, or the current checkout are never trust roots.

## Unresolved gates

- Schedule authority is unresolved: the locked 04:15 value conflicts with a
  later 05:30 objective that did not explicitly override it. Neither time is
  final.
- AU-040 repository writer/integration, BOUND reference resolver, ACTIVE
  external trust, Gmail/state readiness, real-message metadata readback,
  M0c-B, A1c, canonical publication, and verifier review all remain false or
  unperformed.
- The 72-hour retention behavior remains limited by host/App availability;
  recovery must record an offline breach/gap and may not claim an impossible
  hard guarantee.

## Next exact action

Auto may perform only `AUTO_EXACT_BUNDLE_INTEGRATION` from an independently
verified remote head. It must consume the exact 31/5 candidate, V2 consumer,
and control tuple; update only Auto-owned runtime/interface/tests; keep
activation, Gmail send, state migration, shard instances, publication,
VERSION, automation, and schedule changes disabled; and return a fresh remote
readback tuple for the next coordinated phase.

Development still must not call verifier. After both planes are complete, the
Owner will designate the last completed task to invoke a fresh verifier.
