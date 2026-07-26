# Mechanism Teleiosis Registry handoff

- State: `DRAFT_NON_ACTIVE_TELEIOSIS_PARITY_MATERIALIZED`
- Phase: `MECHANISM_REGISTRY_TELEIOSIS_PARITY_MATERIALIZATION`
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
- Exact next Phase:
  `AUTO_TELEIOSIS_REGISTRY_EXACT_TUPLE_INTEGRATION`

All Git objects above are immutable evidence, not self-authorizing trust
roots. A runtime consumer must receive the final Mechanism successor object,
snapshot digest, canonical path, schema ID, and `REGISTERED` mode from
repo-external trusted state.

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
Registry sync tests: 10/10 PASS
complete Mechanism suite: 91/91 PASS
candidate trust: 31 schemas / 5 policies PASS
Mechanism draft/candidate/resolver/release/AU-040 builders and lints: PASS
schema-set lint: 38 schemas PASS
OpenAIDatabase consumer + architecture: 23/23 PASS
consumer CLI: PASS / errors=[] / canonical publication=false
live source dry-run:
  89 instances / 74 names / aliases 20/20 / mirror unchanged / no write
diff-check, Python 3.9 compilation, public literal scan: PASS
```

The unchanged predecessor Auto checkout at
`sha1:1c829553996c792e46cedc4570b30545fba9e071` remains green:

```text
complete Auto suite: 207/207 PASS
fault/privacy seed 271828: 156/156 PASS
fault/privacy seed 314159: 156/156 PASS
Auto schema/transport/promotion/runtime builders and lints: PASS
```

The same standard Auto command against the 89-root successor
correctly does **not** pass: it ran 200 tests with four failures and 20 errors.
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

The next Auto Phase may only bind the exact remotely verified Mechanism
successor tuple and update Auto-owned 89-root resolver expectations. A later,
separate Mechanism control sync may restore the production resolver gate.
The queued `MECHANISM_VERSION_POLICY_V3_DRAFT` must be re-landed only after
that cross-owner tuple chain is coherent. Development still must not call the
verifier.
