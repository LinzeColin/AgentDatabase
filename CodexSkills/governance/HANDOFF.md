# Mechanism promotion-controller handoff

- State: `DRAFT_NON_ACTIVE_PROMOTION_CONTROLLER_READY`
- Phase: `MECHANISM_PROMOTION_CONTROLLER`
- Task Pack task completed: `M-056`
- Required output: `APPEND_ONLY_CHAMPION_REJECT_DECISION`
- Done gate:
  `NO_GATE_BYPASS_AND_ONE_CHAMPION_PER_SCOPE`
- Controller:
  `CodexSkills/governance/promotion/controller.py`
- Controller content SHA-256:
  `bcc39aaa1e6c817fb321a8772996a05fffffe947cd8bbc218a5f7bad16db3e53`
- Readiness raw SHA-256:
  `d54d577bf53e155c1eb6215db388d9f7939f91e21d6af938242c49928b44d1ae`
- Readiness self digest:
  `152afb30ca521bdbf6fe954f0afd408cc238119183d55b782c1ffcfdbadff53b`
- Readiness schema canonical SHA-256:
  `51bbf66eb8f91e4b7243d2d68ab413d36ffa943d3f6baf00331efda51e943693`
- Real Registry observation:
  `89 identities / 89 instances / 89 versions / 0 CHALLENGER / 0 CHAMPION`
- Real promotion execution permitted: `false`
- Pending Task Pack task: `M-057`
- Exact next Phase: `MECHANISM_ROLLBACK_REVOCATION_CONTROLLER`

The M-056 controller is a pure function. It verifies the trusted 31/5
candidate, externally pinned Registry snapshot, version-to-instance-to-identity
scope, four-cell causal eval closure, scorecards, hard gates, notification
receipt semantics, evidence self-digest, decision self-digest, strict ledger
time order, unique decision/evidence use, an externally pinned predecessor
ledger digest, and exactly one champion per Identity scope. The ledger digest
binds the Registry snapshot plus the full ordered decision-digest history. The
controller returns canonical JCS event bytes but never persists them.

`ROLLBACK` and `REVOKE` fail closed with
`PROMOTION_ROLLBACK_REVOCATION_PHASE_REQUIRED`. No Registry/state/Git/VERSION
write, activation, canonical publication, Auto mutation, or verifier call is
part of this Phase.

## Prior version-policy v3 consumer-readiness handoff

- State: `DRAFT_NON_ACTIVE_MECHANISM_CONSUMER_READY`
- Phase: `MECHANISM_VERSION_POLICY_V3_CONSUMER_FIRST_READINESS`
- Protocol:
  `urn:linzecolin:agentdatabase:skillops:protocol:cross-pack:v1`
- SRV candidate: `v0.0.0.3`
- Candidate bundle:
  `sha1:5ee37d7499c62ec19381dac7eb95cb12743ad2d5` /
  `36f0c66dd54d36365700a13f614a8c9bfa9619fb7c532af77566a858175b835e`
- Auto Teleiosis source-sync object:
  `sha1:1c829553996c792e46cedc4570b30545fba9e071`
- Auto runtime-interface raw SHA-256:
  `3e91bf41c9550fa48264db3b72ee102b0acec65b883374d2735fbd7169801d9e`
- Auto module count: `29`
- Source material object:
  `sha1:a8f1f6ff8003db43fad722a5afd3b19615dd325e`
- Registered predecessor:
  `sha1:df63339e1bb6106250ce169241477191744c254f` /
  `10979826bf63b49fbde8da6ece51d6ead6909225b3c62af994e110dea31e1718`
- Current Registry snapshot digest:
  `7b5a74bd459a4737299444b68439c1799ba8a2159032636a24a987113eee9d12`
- Resolver-interface raw SHA-256:
  `f83032d5cb8c9dda9c6e903bb9dc5bf4f2a5de8bd687beeb010047f9e6b3ba2a`
- Resolver-interface self digest:
  `d75e9b1d112b95d7ce0c5b9579140e78847ebc228b7347df7340e211522c0077`
- Version-policy v3 draft interface raw SHA-256:
  `0fa8303981a1b263c835e74cc864fb114c4e1d4eb1a5e8c317c140754b84b8f7`
- Version-policy v3 draft interface self digest:
  `6b2772b30521da9ab3c513d7907448744bff90c1c650ae6ad8c35e5da1497d46`
- Version-policy v3 canonical policy digest:
  `5ea6047446ef26ab39d0e284f37619859d57c8c419daa1cffefffdc12935cfe0`
- Consumer-readiness raw SHA-256:
  `6866a2ca9485d57d065c4954e8452b567c37b738bc32397d17316dfceb623632`
- Consumer-readiness self digest:
  `dec3be6196954320a24a5b9a87c39ac9c8a3ec530216a5b1650797f90046b532`
- Consumer-readiness schema canonical SHA-256:
  `888ad26980f01be14c72d55d7fc514225b3988d64c9034243604f2112c7dcc14`
- Version-policy next Phase:
  `AUTO_VERSION_POLICY_V3_DUAL_READ_INTEGRATION`
- Registry/control pending Phase:
  `AUTO_TELEIOSIS_REGISTRY_EXACT_TUPLE_INTEGRATION`

All Git objects above are immutable evidence, not self-authorizing trust
roots. A runtime consumer must receive the final Mechanism successor object,
snapshot digest, canonical path, schema ID, and `REGISTERED` mode from
repo-external trusted state.

## Version-policy v3 draft

The bundle-external v3 draft closes the six MAJOR codes omitted by the current
v2 policy:

```text
AUTOMATIC_SIDE_EFFECT_CHANGE
EVALUATOR_OR_HOLDOUT_CHANGE
HARD_GATE_CHANGE
MIGRATION_OR_DELETE_SEMANTICS_CHANGE
NETWORK_OR_PERMISSION_CHANGE
PRIVACY_POLICY_CHANGE
```

All seven predecessor MAJOR codes remain present, producing an exact
13-code set. Unknown or duplicate trigger codes fail closed; a MAJOR trigger
cannot be downgraded by combining it with a weaker trigger.

Global SkillOps revision allocation and daily execution identity are now
explicitly separate:

```text
transaction_semantics=ONE_SRV_PER_ACCEPTED_CANONICAL_TRANSACTION
daily_run_increments_srv=false
srv_revision_used_as_daily_sequence=false
daily_transaction_uid_separate=true
daily_transaction_uid_kind=AUTO_TRANSACTION_UID
```

Planned MAJOR writes still require provider `SENT` before the write. Owner
approval and reply are not required, emergency containment may precede
notification, and the actual recipient mapping remains repo-external.

Schedule authority remains fail-closed:

```text
timezone=Australia/Sydney
daily_schedule_authority_state=UNRESOLVED
daily_schedule_candidate_local_times=[04:15,05:30]
daily_schedule_local=null
schedule_activation_permitted=false
```

The draft Schema and policy are not candidate members. Candidate 31/5,
activation control raw bytes, and `CodexSkills/VERSION` are unchanged. The
draft interface records `consumer_first_verified=false`,
`candidate_materialization_permitted=false`,
`promotion_to_candidate_performed=false`, and
`release_write_permitted=false`.

## Mechanism consumer-first readiness

The dual-read consumer selects exactly one policy and one mode:

```text
version-policy:v2 -> PREDECESSOR_READ_ONLY
version-policy:v3 -> SUCCESSOR_SHADOW
```

Implicit selection, policy-object merging, unknown policy IDs, duplicate
triggers, and v2 attempts to classify one of the six v3-only MAJOR triggers
all fail closed. Both policy reads expose the observed schedule value but
normalize schedule authority to `UNRESOLVED`; neither may authorize activation.

The loader verifies two independent repo-external trust roots:

```text
v2 candidate:
  sha1:5ee37d7499c62ec19381dac7eb95cb12743ad2d5
  raw manifest=66ad125629cab71739ff2bc266219f995f7a45998936ca720c6db678ee77e65a
  bundle=36f0c66dd54d36365700a13f614a8c9bfa9619fb7c532af77566a858175b835e
v3 draft:
  sha1:07f7925185f7e1486f808042a10c383ba52d572f
  raw interface=0fa8303981a1b263c835e74cc864fb114c4e1d4eb1a5e8c317c140754b84b8f7
```

The actual Auto consumer inventory is pinned to `sha1:1c829553…`.
`runtime/schedule.py` and `runtime/notification.py` remain v2-only, while
bootstrap and shared-contract loading remain candidate-bundle-only. Tests
execute those real consumer paths: v2 is accepted, v3 schedule and a v3-only
MAJOR notification code are rejected. Therefore:

```text
mechanism_consumer_first_verified=true
auto_consumer_first_verified=false
cross_plane_consumer_first_complete=false
candidate_materialization_permitted=false
```

## 89-root materialization

The four registered source catalogs and the global Registry snapshot now
close the current source set:

```text
AGENTS=24
CLAUDE=3
CODEX=56
CODEX_SYSTEM=6
total=89
tracked aliases=20
metadata-invalid roots=0
binding-eligible versions=0
```

The final artifacts remain:

```text
CodexSkills/registry/agents/_catalog/catalog.v1.json
CodexSkills/registry/claude/_catalog/catalog.v1.json
CodexSkills/registry/codex/_catalog/catalog.v1.json
CodexSkills/registry/codex-system/_catalog/catalog.v1.json
CodexSkills/registry/_global/registry-snapshot.v1.json
```

Their governance draft and registered-candidate copies are generated from the
same deterministic builder. Registered-candidate bytes equal final Registry
bytes exactly. The candidate bundle remains 31 schemas / five policies; the
four Registry schemas stay bundle-external bootstrap contracts.

## Exact predecessor preservation

The builder loads the registered 88-root predecessor only from
`sha1:df63339…`, verifies its raw and canonical snapshot digests, and then
proves all 88 predecessor assignments, Identity records, Instance records,
and Version records are byte-identical in the 89-root successor. No existing
UID is silently rewritten with a new observation timestamp or provenance
object.

The only new current record chain is:

```text
source_relative_path=codex/teleiosis
skill_identity_uid=ski_6E4M0H86C26YQQPZ0GQ4MGE8ZS
skill_instance_uid=skinst_2MQKB8MH3WP7GQJT017WRD1X4G
skill_version_uid=skv_091PBMDHKAXFWC5K9C580Y59NJ
version_record_digest=
  57c3145fbf3eaa8433c193416d3ad9025f32038491666846bc475888204b11e9
regular_file_count=104
alias_count=0
byte_count=598392
content_digest=
  dbfbb07976a375a6d1b3e563476d2041bfabd772597aeb8a0925a1800d4b4364
tree_digest=
  079d557cefe596f5285ca6389b069c553efab1ced342824f0370151883941d35
```

The Auto content-sync digest
`252e9cf65b991dd7bd7c36734257b0b5da47689cbf2d1c7d7bb4ca766aa93bcb`
and the Mechanism policy-scoped content/tree digests intentionally use their
separately declared domains. Both bind the same immutable source object and
104-file / 598392-byte physical closure.

Teleiosis is `QUARANTINED/UNVERIFIED`, has no EvalProfile or PromotionDecision,
has `supersedes_version_uid=null`, and is not binding eligible. The resolver
therefore continues to return `UNKNOWN/MAPPING_NOT_PROVABLE`; no `skill_ref`
or BOUND event can be emitted from the real snapshot.

## Historical missing-root lineage

`codex/context-kernel` remains absent from the current source, mirror,
catalogs, assignments, and snapshot. Its older 89-root record chain remains
available only through immutable object `sha1:5db5beec…` and
`source-drift-reconciliation.v1.json`. Its observation remains `UNOBSERVED`;
no deletion, lifecycle transition, promotion, or binding is inferred.

Thus current source/mirror parity is complete for 89 roots, while historical
whole-source/root parity remains false because the old missing root is not
fabricated.

## Closed gates

This Phase does not update the activation control or Auto runtime tuple. The
previous resolver/control tuple is historical and cannot authorize the new
snapshot. These facts remain false:

```text
auto_integration_complete
production_trust_permitted
bound_reference_resolver_gate_satisfied
runtime_state_write_permitted
runtime_state_instance_created
version_policy_v3_auto_consumer_first_verified
version_policy_v3_cross_plane_consumer_first_complete
version_policy_v3_candidate_materialization_permitted
release_write_permitted
consumer_first_repository_shards_permitted
au_040_daily_jsonl_shard_complete
au_040_complete
external state/Gmail READY
notification real-message metadata readback
m0c_b_permitted
ACTIVE / activation
canonical publication
schedule_authority_resolved
schedule_complete
```

No `CodexSkills/VERSION`, state, lock, watermark, queue/outbox item, shard,
index, daily manifest, retention receipt, Gmail/network operation, automation
change, App action, history replay, or verifier call belongs to this Phase.

## Validation

Pre-push local gates:

```text
bound resolver builder:
  PASS / 89 roots / 4 catalogs / 0 binding eligible
  snapshot=7b5a74bd459a4737299444b68439c1799ba8a2159032636a24a987113eee9d12
  interface_raw=f83032d5cb8c9dda9c6e903bb9dc5bf4f2a5de8bd687beeb010047f9e6b3ba2a
version-policy v3 builder:
  PASS / 13 MAJOR codes / schedule unresolved / candidate membership=false
version-policy v3 targeted tests: 12/12 PASS
version-policy consumer-readiness builder:
  PASS / Mechanism dual-read / Auto v2-only / cross-plane incomplete
version-policy consumer-readiness targeted tests: 8/8 PASS
Registry sync tests: 10/10 PASS
complete Mechanism suite: 111/111 PASS
candidate trust: 31 schemas / 5 policies PASS
Mechanism draft/candidate/resolver/release/AU-040 builders and lints: PASS
v3 isolated / combined schema-set lint: 24 / 41 schemas PASS
OpenAIDatabase consumer + architecture: 23/23 PASS
consumer CLI: PASS / errors=[] / canonical publication=false
candidate/control/VERSION path non-mutation: PASS
diff-check, Python 3.9 compilation, public scanner, URI rebinding: PASS
```

The unchanged predecessor Auto checkout at
`sha1:1c829553996c792e46cedc4570b30545fba9e071` remains green:

```text
complete Auto suite: 207/207 PASS
fault/privacy seed 271828: 156/156 PASS
fault/privacy seed 314159: 156/156 PASS
Auto schema/transport/promotion/runtime builders and lints: PASS
```

The same standard Auto command against the 89-root successor plus this
Mechanism-only readiness artifact correctly does **not** pass: it ran 200
tests with four failures and 20 errors.
All observed failures stop at the cross-owner transition boundary:

```text
BOUND_REFERENCE_RESOLVER_RUNTIME_LOCAL_DRIFT
AUTO_BOUND_REFERENCE_RESOLVER_INTERFACE_DRIFT
ACTIVATION_CONTROL_INTERFACE_SEMANTIC_MISMATCH
```

No Auto production or test file is changed to hide that result. The current
activation builder and activation lint likewise exit 2 with exact
`ACTIVATION_BOUND_RESOLVER_INTERFACE_CONTRACT_MISMATCH`; the Mechanism test
suite separately proves that this stale production tuple fails closed before
state, Git, Gmail, or publisher authority.

Final acceptance additionally requires FF-safe push plus a fresh detached
GitHub object/blob readback of every changed path.

The Registry Auto Phase may only bind the exact remotely verified Mechanism
89-root tuple and update Auto-owned resolver expectations. A later, separate
Mechanism control sync may restore the production resolver gate.

The only version-policy next Phase is the Auto-owned
`AUTO_VERSION_POLICY_V3_DUAL_READ_INTEGRATION`. It may teach the actual Auto
consumers to read v2 and v3 but must keep v3 shadow-only, candidate
materialization false, schedule unresolved, VERSION absent, and activation
forbidden. Development still must not call the verifier.
