# Auto AU-040 publisher-v2 runtime integration handoff

- State: `DRAFT_NON_ACTIVE`
- Phase: `AUTO_AU040_PUBLISHER_V2_RUNTIME_INTEGRATION`
- Phase base Git object:
  `cf48f1a03050859f4abab9a39202a41c3d9a4d29`
- Predecessor control Git object:
  `sha1:fb9b99c36cb870b04f34b5ed3bcb75aeae52c296`
- Predecessor control raw SHA-256:
  `3929db4e818864d02a596efe3e1aaae1af71a765cfafaf7b22f26157135d7953`
- Control external mode: `DRAFT_NON_ACTIVE_CONTROL`
- Control root status: `DRAFT_NON_ACTIVE`
- Control-bound Auto Git object:
  `sha1:7f1bd87652f7cc88fbf2f6b542f9feb57750bf0d`
- Control-bound Auto runtime-interface raw SHA-256:
  `f1f9331df1b56c80e2fa7415fe2fe3d714dcd831cec94390afa43c078dedf38b`
- Control-bound Auto module count: `24`
- Final candidate Git object:
  `sha1:5ee37d7499c62ec19381dac7eb95cb12743ad2d5`
- Final candidate bundle digest:
  `36f0c66dd54d36365700a13f614a8c9bfa9619fb7c532af77566a858175b835e`
- Final candidate manifest raw SHA-256:
  `66ad125629cab71739ff2bc266219f995f7a45998936ca720c6db678ee77e65a`
- Final candidate size: `31 schemas / 5 policies`
- Consumer V2 Git object:
  `sha1:91a12e48351be3ee05ec23ef61aec81056b02014`
- Consumer interface raw SHA-256:
  `189a47300fc1aa6012e87feb6184833cb717cdbe2b9dc9be6db89197f579939c`
- Current Auto runtime-interface raw SHA-256:
  `ce3aae7a22419c3a01455e8e83cc67b23eeb2ada3f3c17e57590a890c0fdef31`
- Current Auto module count: `25`

## Completed in this Phase

The distinct publication-manifest:v2 runtime contract is implemented without
creating or publishing a canonical artifact:

1. `build_publication_manifest_v2_payload()` derives every PUT/DELETE
   descriptor from the physical request. Caller-provided digest maps and
   booleans are not accepted as trust roots.
2. The runtime recomputes the six ordered shared-gate evidence digests from
   the exact bundle, expected head, validated lock identity, path/operation
   set, canonical policy bytes, and schema/privacy-validated artifacts.
3. PUT payloads use an explicit
   `RFC8785_JCS_OBJECT|RFC8785_JCS_PER_LINE_LF` discriminator. JSON objects
   must equal their RFC 8785 bytes exactly. JSONL is bounded to 20 MiB and
   10,000 records, requires one JCS object per LF line, and validates every
   line against its declared record schema and public-value policy.
4. DELETE has no payload or new digest. Only a run-log `part-NNNN.jsonl`
   deletion is accepted. Before mutation the publisher reads the existing
   file through a non-following regular-file gate and revalidates its exact
   prior digest, byte count, record count, schema, privacy, and framing.
5. The physical backend supports exact PUT/DELETE changed-path closure,
   append-only run-log PUT paths, FF-only push, post-push byte/absence
   readback, and crash reconciliation. Parent symlinks and non-regular targets
   fail closed.
6. A production ACTIVE publication requires a real `BootstrapContext`, exact
   successor control binding with
   `publisher_v2_runtime_integration_complete=true`, and separate
   `repository_bound=true` plus
   `canonical_publication_permitted=true`. The current predecessor has
   publisher-v2 false, so execution stops before lock, worktree, state, or Git
   backend access.

The final Auto semantic validator now recognizes
`publication-manifest:v2` independently of v1. It enforces operation
conditionals, lane/path/schema/serialization closure, exact artifact counts,
ordered unique paths and UIDs, and the complete ordered shared-gate set.

## Stable cross-owner transition

The runtime-interface builder consumes the predecessor control only from its
verified Git object and exact raw digest. It never requires the current
working-tree control or Mechanism runtime bytes to remain equal to that
historical object.

The writer materialization snapshot remains byte-for-byte historical as
required by current Mechanism control. A separate publisher snapshot records:

```text
publisher_v2_runtime_materialization_snapshot.as_of_phase=
  AUTO_AU040_PUBLISHER_V2_RUNTIME_INTEGRATION
publisher_v2_runtime_materialization_snapshot.predecessor_control_git_object_id=
  sha1:fb9b99c36cb870b04f34b5ed3bcb75aeae52c296
publisher_v2_runtime_materialization_snapshot.current_auto_runtime_control_bound=false
publisher_v2_runtime_materialization_snapshot.runtime_state_write_permitted=false
publisher_v2_runtime_materialization_snapshot.repository_bound=false
publisher_v2_runtime_materialization_snapshot.canonical_publication_permitted=false
```

The development-only publisher shadow validates the immutable predecessor
control, its exact 7f1/f1f/24-module Auto closure, the final 31/5 candidate,
the current 25-module interface, and all current local module digests. It
returns `UNBOUND_CONTROL_SYNC_PENDING`, never a production
`BootstrapContext`, and cannot access state, Gmail, outbox, worktree, or Git
remote backends.

Production stale-tuple tests compute one exact expected error from byte
equality. Before the successor control lands, the predecessor tuple fails
`BOOTSTRAP_AUTO_RUNTIME_INTERFACE_LOCAL_DRIFT`; after a successor changes the
working-tree control, the same tuple fails
`BOOTSTRAP_CONTROL_INTERFACE_LOCAL_DRIFT`. Side-effect sentinels remain
untouched in both states.

## Machine facts

```text
auto_exact_bundle_integration_complete=true
runtime_shard_writer_integration_complete=true
publisher_v2_runtime_integration_complete=true
publisher_v2_runtime_materialization_snapshot.current_auto_runtime_control_bound=false
runtime_state_write_permitted=false
control_sync_required_before_state_write=true
au_040_daily_jsonl_shard_complete=false
au_040_complete=false
repository_bound=false
canonical_publication_permitted=false
external_gmail_ready_gate_satisfied=false
m0c_b_permitted=false
schedule_authority_resolved=false
schedule_complete=false
next_phase=MECHANISM_POST_AU040_PUBLISHER_V2_CONTROL_SYNC
```

No VERSION, state instance, lock, watermark, queue/outbox entry, shard, index,
daily manifest instance, retention receipt, Gmail/network operation,
activation, publication, automation, App action, verifier call, history
replay, or added time window was performed. The three PAUSED automations were
not touched.

## Validation

The complete Auto suite is green:

```text
/usr/bin/python3 -B -m unittest discover \
  -s CodexSkills/registry/auto/tests -p 'test_*.py'
Ran 170 tests
OK
```

The suite includes exact manifest/physical closure, malformed conditional,
whole-JSONL-as-object, missing LF, count/digest drift, unlisted DELETE,
symlink parent, immutable-path, remote readback, control authority, and
side-effect sentinel negatives.

The development-only closure emits:

```text
AUTO_AU040_PUBLISHER_V2_SHADOW
status=UNBOUND_CONTROL_SYNC_PENDING
schemas=31 policies=5 modules=25
state_write=FORBIDDEN canonical_write=FORBIDDEN
```

The production preflight with exact candidate A and predecessor control fails
as the expected safety assertion:

```text
BOOTSTRAP_AUTO_RUNTIME_INTERFACE_LOCAL_DRIFT
```

The Mechanism suite retains one required cross-owner transition error:

```text
Ran 60 tests
59 passed
1 error=test_02a_integrated_auto_interface_and_modules_are_exact
error_code=ACTIVATION_AUTO_INTERFACE_CURRENT_DRIFT
```

The directly related OpenAIDatabase consumer/architecture suite is `23/23`
green. Its real consumer CLI returns `status=PASS`, `errors=[]`, and
`canonical_publication_permitted=false`.

Deterministic fault/privacy runs are both green:

```text
seed=271828 tests=119 failures=0 errors=0
seed=314159 tests=119 failures=0 errors=0
```

Candidate/control/acceptance/promotion/runtime builders are byte-equivalent;
candidate trust remains exact `31 schemas / 5 policies`.

The broad command-ownership baseline is the same on phase base and this tree:
`top-level script entrypoints: expected 84, observed 90`. It is not reported
as PASS and this Phase has no `OpenAIDatabase/**` diff. The broad
OpenAIDatabase privacy guard is PASS with zero high-risk hits on both trees.

## Next exact action

The next owner is Mechanism and the only next phase is
`MECHANISM_POST_AU040_PUBLISHER_V2_CONTROL_SYNC`. It must independently read
back the verified Auto object/interface/modules and issue a successor control
binding them. It must not perform repository binding, create canonical
shards, publish, activate, touch Gmail/state, create VERSION, modify schedule
or automation, call verifier, or replay history.

After successor control sync, AU-040 daily completion, repository binding,
canonical publication, Gmail/state readiness, M0c-B, ACTIVE, and schedule
authority remain false until their separately authorized phases and external
facts are complete.
