# Auto successor-control test fixture corrective handoff

- State: `DRAFT_NON_ACTIVE`
- Phase: `AUTO_SUCCESSOR_CONTROL_TEST_FIXTURE_CORRECTIVE`
- Phase base Git object:
  `2a64469d7da908b88b555a437fdcfdaf8cc3fb6e`
- Runtime writer integration Git object:
  `2a64469d7da908b88b555a437fdcfdaf8cc3fb6e`
- Historical control observation Git object:
  `sha1:00c4a52d177898b1999b87b29ddb480e89908729`
- Historical control observation raw SHA-256:
  `31602443a685cc12a1eebd51ea8e0801ffd399c16a33186c372b7b81e8e46409`
- Control external mode: `DRAFT_NON_ACTIVE_CONTROL`
- Control root status: `DRAFT_NON_ACTIVE`
- Control-bound Auto object:
  `sha1:7ed9e761921f557887440803d1fc7327f3e986a9`
- Control-bound Auto interface raw SHA-256:
  `09af0c00273825e90a489f413a2f0bb6995042e5b4eea17973ce7582eab66340`
- Control-bound module count: `21`
- Final candidate Git object:
  `sha1:5ee37d7499c62ec19381dac7eb95cb12743ad2d5`
- Final candidate bundle digest:
  `36f0c66dd54d36365700a13f614a8c9bfa9619fb7c532af77566a858175b835e`
- Final candidate manifest raw SHA-256:
  `66ad125629cab71739ff2bc266219f995f7a45998936ca720c6db678ee77e65a`
- Final candidate size: `31 schemas / 5 policies`
- Consumer V2 Git object:
  `sha1:91a12e48351be3ee05ec23ef61aec81056b02014`
- Consumer raw SHA-256:
  `189a47300fc1aa6012e87feb6184833cb717cdbe2b9dc9be6db89197f579939c`
- Current Auto runtime interface raw SHA-256:
  `f1f9331df1b56c80e2fa7415fe2fe3d714dcd831cec94390afa43c078dedf38b`
- Current Auto module count: `24`

## Completed in this corrective

Auto's test fixtures now keep three trust views separate without changing any
production gate:

1. The historical 00c4/3160 control fixture reads its complete ten-path
   Mechanism runtime closure from the verified Git object. Candidate-specific
   functional negatives may expose those exact blobs as a test-only historical
   local view; the helper never returns a production bootstrap result.
2. Candidate-tuple negative tests run inside that consistent historical
   closure, so they reach and assert their exact candidate error rather than
   being preempted by an unrelated later working-tree control drift.
3. Activation functional tests derive a test-only tuple from the exact current
   committed `HEAD`, require local control bytes to equal that Git blob, and
   then execute the real handshake constructor. A later Mechanism successor
   therefore becomes the functional fixture only after it has a local commit
   object; uncommitted drift is never trusted.
4. Production stale-tuple tests use the real working tree. They still require
   exactly `BOOTSTRAP_AUTO_RUNTIME_INTERFACE_LOCAL_DRIFT` when local control is
   00c4, or `BOOTSTRAP_CONTROL_INTERFACE_LOCAL_DRIFT` after a successor changes
   it, and all state/Gmail/publisher sentinels remain uncalled.

The successor-binding regression now derives a distinct external control
object from current `HEAD`, binds the unchanged current runtime-interface and
24-module set, and simulates the complete ten-path successor Mechanism
Git/local closure. The exact successor passes. Forged Auto Git bytes, Auto
local bytes, Mechanism Git bytes, and Mechanism local bytes each fail with
their exact production drift code. No production verifier function is patched
out and no arbitrary exception is accepted.

## Preserved runtime writer integration

The runtime-interface builder consumes 00c4 only as a historical Git-object
observation. It reads the control and the four observed Mechanism runtime blobs
only with `git show 00c4:path`, verifies the exact raw digest and frozen
contract, and never requires the current working-tree control or Mechanism
runtime to equal 00c4. The machine interface separates that immutable evidence
from the interface-materialization snapshot:

```text
historical_control_observation.verified_git_object_id=sha1:00c4a52d...
historical_control_observation.interface_raw_sha256=31602443...
historical_control_observation.observed_auto_runtime_integration_complete=true
historical_control_observation.observed_runtime_state_write_permitted=true
historical_control_observation.bound_auto_git_object_id=sha1:7ed9e761...
historical_control_observation.bound_auto_runtime_interface_raw_sha256=09af0c00...
historical_control_observation.bound_auto_module_count=21
runtime_interface_materialization_snapshot.semantic_scope=INTERFACE_MATERIALIZATION_ONLY
runtime_interface_materialization_snapshot.current_auto_runtime_control_bound=false
runtime_state_write_permitted=false
control_sync_required_before_state_write=true
```

Production `bootstrap_runtime` remains exact-byte fail closed. Because 00c4
binds 7ed9/09af/21 modules rather than this writer candidate, production
preflight, orchestrator, notification, and activation entrypoints fail before
state root, lock, watermark, recipient mapping, Gmail client/query, outbox, Git
backend, or publisher access. While the working-tree control still equals
00c4, the exact code is `BOOTSTRAP_AUTO_RUNTIME_INTERFACE_LOCAL_DRIFT`; after a
successor control changes the local bytes, the same stale 00c4 tuple fails
earlier with `BOOTSTRAP_CONTROL_INTERFACE_LOCAL_DRIFT`. Tests compute and
assert exactly one of those codes from byte equality; they do not catch a
generic exception. The existing interface/module/trusted-runtime drift codes
remain unchanged.

`runtime/writer_shadow.py` and `tools/validate_au040_writer.py` provide the only
unbound development proof. They independently verify:

1. the exact candidate A 31/5 content tuple;
2. exact historical control 00c4/raw 3160 and its Git-contained Mechanism
   runtime observations, without using current working-tree bytes as evidence;
3. the historical 7ed9/09af interface and all 21 declared Git blobs;
4. current runtime-interface byte equivalence and all 24 local module digests.

The result is `UNBOUND_CONTROL_SYNC_PENDING`. It is not a production
`BootstrapContext`, never reports `TRUSTED`, `READY`, or production preflight
PASS, and has no state/Gmail/outbox/publication backend path.

`runtime/run_log_writer.py` now implements deterministic AU-040 byte planning:

- validates public-run-event:v2 through the final 31/5 Registry and v2 public
  scanner;
- derives the actual Australia/Sydney calendar date from `occurred_at`;
- orders records by `(occurred_at,event_uid)`;
- emits RFC 8785 JCS per LF line for `part-NNNN.jsonl` and the paired persistent
  `index-NNNN.jsonl`, each bounded to 20 MiB;
- enforces exact event UID/digest dedupe and exact BINDING_CORRECTION
  supersession evidence;
- keeps part numbers gapless/non-reused and rejects late insertions that would
  rewrite an immutable prior part;
- creates append-only `manifest-NNNN.json` revisions with exact predecessor
  digest, physical byte/count arithmetic, 365-day retention anchors, and
  self-digest;
- reads existing daily trees descriptor-relatively with `O_NOFOLLOW`, bounded
  enumeration, exact JCS/JSONL framing, physical digest closure, persistent
  index closure, manifest part immutability, predecessor-chain checks, and
  receipt-backed PRUNED transitions.

The writer returns in-memory PUT artifacts only. It has no canonical repository
write, state-root write, queue, publication-manifest:v2, Git push, or remote
readback integration.

Final Auto semantic validation now recognizes daily-run-shard-manifest:v1,
run-event-index-entry:v1, and exact GIT_CURRENT_TREE retention-receipt:v3
evidence. It enforces strict 365-day anchors, 24-hour prune deadlines, the
deadline equality boundary, and truthful
`GIT_CURRENT_TREE_PRUNE_DEADLINE_BREACH` reporting. The current-tree retention
executor remains absent.

## Machine facts

```text
auto_exact_bundle_integration_complete=true
runtime_shard_writer_integration_complete=true
runtime_interface_materialization_snapshot.current_auto_runtime_control_bound=false
runtime_state_write_permitted=false
publisher_v2_runtime_integration_complete=false
au_040_daily_jsonl_shard_complete=false
au_040_complete=false
repository_bound=false
canonical_publication_permitted=false
external_gmail_ready_gate_satisfied=false
m0c_b_permitted=false
schedule_authority_resolved=false
schedule_complete=false
next_phase=MECHANISM_POST_AU040_WRITER_CONTROL_SYNC
```

No VERSION, state instance, intent, receipt, settlement, shard, index, daily
manifest instance, Gmail/network operation, activation, publication, watermark,
automation, App action, verifier call, history replay, or added time window was
performed. The three PAUSED automations were not touched.

## Validation

The complete Auto suite is green:

```text
/usr/bin/python3 -B -m unittest discover \
  -s CodexSkills/registry/auto/tests -p 'test_*.py'
Ran 157 tests
OK
```

The suite includes a successor simulation that changes the working-tree
control raw bytes and Mechanism control builder bytes. Runtime-interface render
and the development-only functional shadow remain byte-stable, while
production bootstrap with the stale 00c4 tuple fails exactly with
`BOOTSTRAP_CONTROL_INTERFACE_LOCAL_DRIFT`.

The same complete 157-test suite also passes under a coherent test-only
successor Git/local overlay that changes both exact paths before test
discovery while retaining every production verifier:

```text
CodexSkills/governance/activation/control-interface.json
CodexSkills/governance/tools/build_activation_control.py
Ran 157 tests
OK
```

A separate successor-binding simulation proves that production bootstrap can
consume a future externally pinned control that binds this exact interface and
24-module set. Bootstrap no longer treats the prior
`MECHANISM_POST_AUTO_INTEGRATION_CONTROL_SYNC` phase string as a trust
condition; it instead re-reads every declared module from the control-bound
Auto Git object, verifies its declared digest, and then requires the local byte
to equal that Git blob. A forged bound-object module fails exactly with
`BOOTSTRAP_AUTO_RUNTIME_MODULE_GIT_DIGEST_MISMATCH`; forged Auto local,
Mechanism Git, and Mechanism local bytes fail exactly with
`BOOTSTRAP_AUTO_RUNTIME_MODULE_LOCAL_DRIFT` and
`BOOTSTRAP_TRUSTED_RUNTIME_LOCAL_DRIFT`.

The Mechanism suite truthfully remains in the expected cross-owner transition:

```text
Ran 59 tests
58 passed
1 error=test_02a_integrated_auto_interface_and_modules_are_exact
error_code=ACTIVATION_AUTO_INTERFACE_CURRENT_DRIFT
```

That error is the required fail-closed evidence that current writer bytes are
not represented by 00c4's 7ed9/09af/21-module binding. Auto does not alter
Mechanism-owned tests or control to conceal it; the later exact successor
control sync is the only permitted closure.

OpenAIDatabase's directly related consumer/architecture suite is `22/22`
green, and its real consumer CLI returns `status=PASS`, `errors=[]`,
`canonical_publication_permitted=false`. Deterministic fault/privacy runs are
both green:

```text
seed=271828 tests=106 failures=0 errors=0
seed=314159 tests=106 failures=0 errors=0
```

The development-only closure emits:

```text
AUTO_AU040_WRITER_SHADOW
status=UNBOUND_CONTROL_SYNC_PENDING
schemas=31 policies=5 modules=24 state_write=FORBIDDEN
```

The production preflight with exact candidate A and successor control 00c4
fails as the expected safety assertion:

```text
BOOTSTRAP_AUTO_RUNTIME_INTERFACE_LOCAL_DRIFT
```

The broad command-ownership baseline on phase base e2c remains the unrelated
exact failure `top-level script entrypoints: expected 84, observed 88`; this
phase changes no `OpenAIDatabase/**` path and does not report that check as
PASS.

The broad OpenAIDatabase privacy guard likewise retains the phase-base e2c
signature `high_risk_secret_hit_count=3`, limited to the upstream recurring
prompt fixture/test (`session-a.part-0001.jsonl` twice and
`test_recurring_prompt_analysis.py` once, pattern=`api_keys`). This Phase has
zero `OpenAIDatabase/**` diff and does not report that broad check as PASS.

## Next exact action and publication freeze

After ordinary FF-safe push and independent GitHub detached-object readback,
the publication window immediately freezes again. Do not start, delegate,
request, or push any successor Auto or Mechanism phase before Dynamic Stage 1
authoritative verifier + GitHub upload completes or that task explicitly
releases the window.

The exact later owner is Mechanism and the exact phase string is
`MECHANISM_POST_AU040_WRITER_CONTROL_SYNC`. It may only bind the verified new
Auto object/interface/modules into successor control. It must not perform
publisher-v2 integration, Gmail/state readiness, M0c-B, activation, canonical
shard publication, VERSION, schedule resolution, automation, or verifier work.

The Owner must still resolve 04:15 versus 05:30 explicitly and provision the
repo-external owner-only state root before any later Gmail readiness or M0c-B.
