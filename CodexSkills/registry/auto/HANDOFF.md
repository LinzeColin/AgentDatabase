# Auto AU-040 repository-binding integration handoff

- State: `DRAFT_NON_ACTIVE`
- Phase: `AUTO_AU040_REPOSITORY_BINDING`
- Phase base Git object:
  `e6438db785c2f3f38da59be7ba9c1cd46651d7ea`
- Predecessor control Git object:
  `sha1:e6438db785c2f3f38da59be7ba9c1cd46651d7ea`
- Predecessor control raw SHA-256:
  `28a35148cc18362de4fc53b508754f263a015cf33e4cd187314cf48c767b6920`
- Control external mode: `DRAFT_NON_ACTIVE_CONTROL`
- Control root status: `DRAFT_NON_ACTIVE`
- Control-bound Auto Git object:
  `sha1:85edc67df48d4e5bc783f89ed3f3371f25f288e1`
- Control-bound Auto runtime-interface raw SHA-256:
  `ce3aae7a22419c3a01455e8e83cc67b23eeb2ada3f3c17e57590a890c0fdef31`
- Control-bound Auto module count: `25`
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
  `c7af9d1406fe2ed084d5a30fab6cded3897a83c1602e6c40587cf28c75a2c75c`
- Current Auto module count: `26`

## Completed in this Phase

Repository-binding code is integrated without claiming repository authority or
creating a canonical run-log artifact:

1. Production trust remains the external candidate tuple plus the external
   control tuple. Bootstrap now also parses and validates the exact
   Mechanism-owned V2 consumer bytes, including its candidate tuple, status,
   run-log root, and three closed publication gates.
2. `repository_binding.py` consumes a successor control decision before doing
   any local repository probe. It requires
   `repository_binding_integration_complete=true`,
   `repository_bound=true`, and the distinct Mechanism-owned
   `bound_reference_resolver_gate_satisfied=true`.
3. Only after those control facts pass does a no-network probe verify the
   repository root is a real directory, the exact top-level is selected,
   object format is SHA-1, reference branch is clean `main`, fetch and push
   URLs are both exactly
   `git@github.com:LinzeColin/AgentDatabase.git`, local
   `refs/heads/main` equals the repo-external per-transaction expected head,
   and scratch/state roots are external, real, and non-overlapping.
4. The probe issues a sealed in-process permit bound to the exact
   `BootstrapContext`, expected head, repo root, and external roots. A caller
   boolean, URL, digest map, forged object, or permit from another context is
   rejected.
5. Orchestrator, notification/Gmail, activation, and physical ACTIVE
   publication paths now require repository authorization before state root,
   lock, recipient mapping, Gmail client, outbox, worktree, `ls-remote`, or
   mutable Git backend access.
6. The ACTIVE publisher admits only the canonical
   `OpenAIDatabase/data/run_logs/skills_runs/YYYY/MM/DD/` closure:
   part/index JSONL at 20 MiB, daily manifest/retention receipt JCS objects at
   1 MiB, Sydney calendar date, 0001..9999 logical numbering, immutable PUT,
   and DELETE only for a part.
7. A part DELETE must be closed by a new daily manifest plus an exact
   retention receipt. Before mutation the runtime revalidates the prior part,
   prior manifest self-digest/schema/privacy, and retained index physical
   digest/bytes/record count/schema/privacy.
8. The Auto adapter does not create or authenticate a BOUND resolver.
   `CodexSkills/registry/index.json` remains only a compatibility index. The
   absent global identities, four source catalogs, versioned registry
   snapshot, and Mechanism resolver remain explicit blockers.

## Authority separation

The machine interface records:

```text
repository_binding_integration_complete=true
repository_binding_readonly_preflight_verified=false
repository_binding_materialization_snapshot.as_of_phase=
  AUTO_AU040_REPOSITORY_BINDING
repository_binding_materialization_snapshot.semantic_scope=
  INTERFACE_MATERIALIZATION_ONLY
repository_binding_materialization_snapshot.predecessor_control_git_object_id=
  sha1:e6438db785c2f3f38da59be7ba9c1cd46651d7ea
repository_binding_materialization_snapshot.current_auto_runtime_control_bound=false
repository_binding_materialization_snapshot.repository_bound=false
repository_binding_materialization_snapshot.bound_reference_resolver_gate_satisfied=false
repository_binding_materialization_snapshot.runtime_state_write_permitted=false
repository_binding_materialization_snapshot.canonical_publication_permitted=false
```

`repository_binding_readonly_preflight_verified=false` is deliberate. No
environment-dependent probe result is serialized as a persistent trust root.
The positive probe is covered with isolated temporary repositories; the real
production probe remains per transaction and cannot run until a successor
control grants both repository and resolver authority.

When a future Mechanism resolver cannot prove identity → instance → version
through an immutable externally pinned registry snapshot, projection must
remain `binding_state=UNKNOWN` with one schema-approved reason and without
`skill_ref` or `controlled_invocation`. Path, slug, name, or compatibility
index inference is forbidden. An already published event is immutable and may
only be superseded by a later `BINDING_CORRECTION`.

## Machine facts

```text
auto_exact_bundle_integration_complete=true
runtime_shard_writer_integration_complete=true
publisher_v2_runtime_integration_complete=true
repository_binding_integration_complete=true
current_auto_runtime_control_bound=false
runtime_state_write_permitted=false
repository_bound=false
bound_reference_resolver_gate_satisfied=false
consumer_first_repository_shards_permitted=false
canonical_publication_permitted=false
au_040_daily_jsonl_shard_complete=false
au_040_complete=false
runtime_state_instance_created=false
external_gmail_ready_gate_satisfied=false
notification_real_message_metadata_readback_verified=false
m0c_b_permitted=false
schedule_authority_resolved=false
schedule_complete=false
next_phase=MECHANISM_POST_AU040_REPOSITORY_BINDING_CONTROL_SYNC
```

No VERSION, state instance, lock, watermark, queue/outbox entry, shard, index,
daily manifest instance, retention receipt instance, Gmail/network operation,
activation, publication, automation, App action, verifier call, history
replay, or added time window was performed. The three PAUSED automations were
not touched.

## Validation

The complete Auto suite is green:

```text
/usr/bin/python3 -B -m unittest discover \
  -s CodexSkills/registry/auto/tests -p 'test_*.py'
Ran 178 tests
OK
```

The repository-binding tests include exact SSH fetch/push URLs, clean `main`,
object format and expected-head checks; URL/head/dirty/symlink/root
containment negatives; unforgeable context-bound permits; exact writer
part/index/manifest closure; Sydney date and path restrictions; resolver gate
ordering; and positive/negative receipt-backed part pruning with retained
index and prior manifest revalidation.

The development-only closure emits:

```text
AUTO_AU040_REPOSITORY_BINDING_SHADOW
status=UNBOUND_REPOSITORY_CONTROL_SYNC_PENDING
schemas=31 policies=5 modules=26
resolver=UNSATISFIED repository_bound=FALSE
state_write=FORBIDDEN canonical_write=FORBIDDEN
```

The production preflight with exact candidate A and predecessor e643 control
fails as the expected safety assertion:

```text
BOOTSTRAP_AUTO_RUNTIME_INTERFACE_LOCAL_DRIFT
```

The pre-push cross-plane gates are:

```text
Mechanism: 60 run; 59 pass; one expected cross-owner transition error
  test_02a_integrated_auto_interface_and_modules_are_exact
  ACTIVATION_AUTO_INTERFACE_CURRENT_DRIFT
OpenAIDatabase consumer + architecture: 23/23 PASS
OpenAIDatabase consumer CLI: PASS; errors=[]; canonical publication=false
fault/privacy seed 271828: 127/127 PASS
fault/privacy seed 314159: 127/127 PASS
candidate builder/trust: 31 schemas / 5 policies PASS
activation control builder/lint: PASS; predecessor raw unchanged
AU-040 semantic acceptance builder/lint: PASS
Auto runtime-interface builder: byte-equivalent
```

Detached GitHub object/raw readback and owned cleanup remain completion-time
evidence and are reported only after the ordinary FF-safe push succeeds.

## Next exact action

The next owner is Mechanism and the only next phase is
`MECHANISM_POST_AU040_REPOSITORY_BINDING_CONTROL_SYNC`. It must independently
read back the verified Auto object/interface/26 modules and decide any
successor repository/resolver authority from its own evidence. It must not
generate canonical shards, publish, activate, touch Gmail/state, create
VERSION, change schedule or automation, call verifier, or replay history.

After successor control sync, AU-040 daily completion, the BOUND resolver,
consumer repository-shard permission, canonical publication, Gmail/state
readiness, M0c-B, ACTIVE, and schedule authority remain false until their
separately authorized phases and external facts are complete.
