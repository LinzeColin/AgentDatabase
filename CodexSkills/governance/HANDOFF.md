# Mechanism read-only migration/cutover handoff

- State:
  `DRAFT_NON_ACTIVE_READ_ONLY_MIGRATION_CUTOVER_IMPLEMENTED_BLOCKED`
- Phase: `MECHANISM_READ_ONLY_MIGRATION_CUTOVER`
- Task Pack task implemented: `M-065`
- M-065 dependencies: `M-014`, `M-015`, `M-060`
- Production dependency state: `BLOCKED_FAIL_CLOSED`
- Required output: `DUAL_READ_PARITY_CUTOVER_ROLLBACK`
- Done gate: `NO_LOCAL_DATA_MUTATION_DELETE_BUDGET_ZERO`
- Acceptance criteria: `AC-07`, `AC-08`, `AC-09`, `AC-15`
- Pure guard:
  `CodexSkills/governance/migration/read_only_cutover.py`
- Pure guard raw SHA-256:
  `0fccde44c02f8d4ad76ae2aca9e428a8a1c64855e0660027449035861911b9a1`
- Current observation:
  `CodexSkills/governance/migration/read-only-migration-observation.json`
- Observation raw SHA-256:
  `333c6dd0cff6b891924601f8419d1ca659e5b097eaa26540c8a30b0e96508e4a`
- Observation self digest:
  `9c09dbed1e97c5d598d5f46eb9265d9270fe0119b5d21a3fac289ca4436b02c9`
- Observation schema canonical SHA-256:
  `6d769bd378ee2526155fbfab29de89ec7754b41c026104a989a164a980505a97`
- Current plan:
  `CodexSkills/governance/migration/read-only-cutover-plan.json`
- Plan raw SHA-256:
  `20f177d523096f5333bb8210447fe0ace822c3e8e4deb4ea2fd86c8feae6c494`
- Plan self digest:
  `bf32c6c378d9f4d971a12dc26538ea23f9b90107bde7db2a0849de59ab8081f1`
- Plan schema canonical SHA-256:
  `f800865090ce43f86ab78d69f306592a801f40faaad3bc2a167f20ecb3209d39`
- M-065 readiness:
  `CodexSkills/governance/migration/read-only-migration-cutover-readiness.json`
- Readiness raw SHA-256:
  `839b363d904116d8657f78e10b53a1cd11c86f1d64f06064090e5a71b24ca02c`
- Readiness self digest:
  `049809b3292f5591fc63f899c2172e67da66bb0a152998e04a341bda401d1228`
- Readiness schema canonical SHA-256:
  `d63de0996742f8943f905827b4eeb35ba0137b09b10acd3a84e45460ba717e9e`
- Immutable M-064 predecessor:
  `sha1:9b8f20f3ab97a7ec06aedfbe53670569ac036f9b`
- Immutable M-060 protected-local boundary:
  `sha1:21235d49fca818b74677172711cfe279d2da68a6`
- Immutable candidate:
  `sha1:5ee37d7499c62ec19381dac7eb95cb12743ad2d5`
- Immutable candidate bundle digest:
  `36f0c66dd54d36365700a13f614a8c9bfa9619fb7c532af77566a858175b835e`
- Current decision: `BLOCKED`
- Current cutover mode: `SHADOW_ONLY`
- Current cutover permitted: `false`
- Delete budget: `0`
- Local data mutation performed: `false`
- Real migration / dual read / rollback executed: `false / false / false`
- Pending Task Pack task: `M-066`
- Exact next Phase: `MECHANISM_PERFORMANCE_CAPACITY_BUDGETS`

M-065 implements the evidence contract without inventing completion evidence.
Every `COMPLETE` source must close its pre, post, and target snapshots over
file count, bytes, regular files, symlinks, tree digest, and link digest.
Missing, empty, or errored sources, pre/post drift, any parity mismatch,
missing or different dual-read results, an incomplete audit, a forbidden
command, any mutating audit counter, or a nonzero delete budget blocks.

The checked-in observation is intentionally blocked. There is no distinct
M-014 source-migration receipt or complete M-015 external local-source parity
proof. Immutable history also proves that the historical `CODEX` source and
Registry target trees differ. The current resolver states source-root parity,
whole-source parity, and production trust are false. The old repository paths
were removed by the historical consolidation commit, so that commit is not
grandfathered as proof that external local roots stayed unchanged.

A complete synthetic evidence set produces `CUTOVER_ELIGIBLE`, proving the
positive contract. Even then, the pure plan remains `SHADOW_ONLY` and
`current_cutover_permitted=false`; it cannot execute a cutover. Rollback is a
new ordinary commit only, retains the prior read route and evidence, forbids
local source deletion, and forbids rebase, force-push, and history rewrite.

M-065 has no filesystem, Git, network, state, lock, publisher, migration,
copy, move, truncate, delete, or activation capability. It creates no
VERSION, state, watermark, canonical artifact, or publication. Auto and
OpenAIDatabase are unchanged.

## M-065 validation

```text
M-065 targeted parity/mutation/rollback/negative tests: 17/17 PASS
complete Mechanism suite: 237/237 PASS
M-065 builder/schema/observation/plan/readiness: BYTE_EQUIVALENT
complete synthetic parity + dual-read: CUTOVER_ELIGIBLE / execution false
current evidence: BLOCKED / SHADOW_ONLY / delete budget 0
candidate trust: 31 schemas / 5 policies PASS
schema-set lint:
  base 21 / candidate-compatible 41 / version 24 /
  M-065 full closure 78 PASS
OpenAIDatabase consumer + architecture: 23/23 PASS
consumer CLI: PASS / errors=[] / canonical publication=false
```

The pre-existing cross-owner transition remains fail-closed and is not
modified or relabeled by M-065:

```text
complete Auto suite: 200 tests / 5 failures / 20 errors
fault/privacy seed 271828: 149 tests / 5 failures / 25 errors
fault/privacy seed 314159: 149 tests / 5 failures / 25 errors
AUTO_REGISTRY_MIRROR_SKILL_COUNT_DRIFT
BOUND_REFERENCE_RESOLVER_RUNTIME_LOCAL_DRIFT
ACTIVATION_CONTROL_INTERFACE_SEMANTIC_MISMATCH
```

The Registry compatibility index remains `90` while Auto is pinned to `89`.
Those exact failures are the M-064 baseline and occur outside the M-065
changed path set. No Auto file may be changed in this Mechanism Phase.

Final acceptance additionally requires an ordinary commit, FF-safe
`HEAD:main` push, and fresh detached GitHub object/raw-byte readback of every
changed path. No verifier call, historical Task Pack replay, real local-source
scan, migration, cutover, rollback, publication, activation, or follow-on
Phase belongs to this run.

## Prior M-064 Git-history persistence disclosure handoff

- State: `DRAFT_NON_ACTIVE_GIT_HISTORY_PERSISTENCE_DISCLOSURE_READY`
- Phase: `MECHANISM_GIT_HISTORY_PERSISTENCE_DISCLOSURE`
- Task Pack task completed: `M-064`
- M-064 dependency: `M-063`
- Required output: `OPERATOR_USER_DISCLOSURE`
- Done gate: `SYSTEM_NEVER_CLAIMS_HARD_DELETION`
- Acceptance criterion: `AC-19`
- M-064 pure guard:
  `CodexSkills/governance/retention/git_history_disclosure.py`
- M-064 pure guard raw SHA-256:
  `f45d8fd67fa52a8eac0305af0e6f47c47fd91a2052fa9915eb82a7128754c792`
- Canonical bilingual disclosure:
  `CodexSkills/governance/retention/GIT_HISTORY_PERSISTENCE_DISCLOSURE.md`
- Bilingual disclosure raw SHA-256:
  `429433091272a378793f9b4b2577994d60509c16b2fc7a628abd70e0ea264484`
- Structured disclosure:
  `CodexSkills/governance/retention/git-history-persistence-disclosure.json`
- Structured disclosure raw SHA-256:
  `6972902c9b54918b392c54cc18645260168cdc942719ff2555aa541c607a47a5`
- Structured disclosure self digest:
  `7a43821d89e63393f2c1cf952a79d788777e606d546b3e15787e4bebddf470b0`
- Disclosure schema canonical SHA-256:
  `7afb8cfa3f4039d91b272307f5d92a162e0d85ed972589bba1289c01fc74d440`
- M-064 readiness:
  `CodexSkills/governance/retention/git-history-persistence-readiness.json`
- M-064 readiness raw SHA-256:
  `3cb7f9b6c5528f6c7415fa45c53da1fd38f2dbb7561f8d123b56769e96db567f`
- M-064 readiness self digest:
  `b94cfab93ad5383dda32b45506f267cf126c7400925fd4d371278bde392a007e`
- Readiness schema canonical SHA-256:
  `247053b03b42750fd2bdf76732ee311967850661b97fe9181b722a8b5d677351`
- Immutable M-063 predecessor:
  `sha1:039f3844b36961f1d8432b9c0d86d6cda408f430`
- Immutable candidate:
  `sha1:5ee37d7499c62ec19381dac7eb95cb12743ad2d5`
- Immutable candidate bundle digest:
  `36f0c66dd54d36365700a13f614a8c9bfa9619fb7c532af77566a858175b835e`
- Retention scope: `GIT_CURRENT_TREE_ONLY`
- Receipt proof scope: `CURRENT_TREE_TRANSITION_ONLY`
- Git history, fork, clone, cache, archive, and provider-backup
  persistence: `MAY_RETAIN_INDEFINITELY`
- Hard-deletion claim: `false`
- Automatic history rewrite: `false`
- User/UI runtime integration: `NOT_BOUND`
- Pending Task Pack task: `M-065`
- Exact next Phase: `MECHANISM_READ_ONLY_MIGRATION_CUTOVER`

M-064 turns the Task Pack's retention caveat into an exact operator/user
contract. The 365-day rule covers full-fidelity artifacts in the Git current
tree only. Strictly post-boundary eligibility permits only a later
current-tree transition. It does not make Git history, forks, clones, caches,
archives, provider backups, or third-party copies disappear.

The canonical English and zh-CN disclosure states that a retention receipt
proves only the audited current-tree transition. The bounded pure guard rejects
affirmative claims of completed permanent deletion, history erasure, all-copy
removal, or irrecoverability. Self-consistent weakening of the structured
text is rejected by both semantic validation and the const-closed schema.

M-064 has no filesystem, Git, network, state, queue, lock, publisher,
deletion, history-rewrite, or repository-rotation capability. It creates no
real retention artifact, VERSION, activation, or canonical publication. A
future hard-erasure design requires separate Owner authorization and MAJOR
governance; M-064 neither implements nor promises it.

## M-064 validation

```text
M-064 targeted disclosure/persistence/negative tests: 15/15 PASS
complete Mechanism suite: 220/220 PASS
M-064 builder/schema/readiness/Markdown: BYTE_EQUIVALENT
English and zh-CN affirmative hard-erasure claims: FAIL_CLOSED
self-consistent disclosure weakening: FAIL_CLOSED
all declared governance/Auto/run-log Markdown surfaces: PASS
candidate trust: 31 schemas / 5 policies PASS
schema-set lint:
  base 21 / candidate-compatible 41 / version 24 /
  M-064 full closure 75 PASS
OpenAIDatabase consumer + architecture: 23/23 PASS
consumer CLI: PASS / errors=[] / canonical publication=false
```

The pre-existing cross-owner transition remains fail-closed and is not
modified or relabeled by M-064:

```text
complete Auto suite: 200 tests / 5 failures / 20 errors
fault/privacy seed 271828: 149 tests / 5 failures / 25 errors
fault/privacy seed 314159: 149 tests / 5 failures / 25 errors
AUTO_REGISTRY_MIRROR_SKILL_COUNT_DRIFT
BOUND_REFERENCE_RESOLVER_RUNTIME_LOCAL_DRIFT
ACTIVATION_CONTROL_INTERFACE_SEMANTIC_MISMATCH
activation builder/lint:
  ACTIVATION_BOUND_RESOLVER_INTERFACE_CONTRACT_MISMATCH
```

The mirror count remains `90` while Auto is pinned to `89`. These failures are
the exact M-063 baseline and occur outside the M-064 changed path set. Final
acceptance additionally requires an ordinary commit, FF-safe push, and fresh
GitHub detached object/raw-byte readback of every changed path.

No Auto, candidate-bundle, policy, OpenAIDatabase, automation, or VERSION path
change belongs to M-064. No verifier call, historical Task Pack replay, real
current-tree removal, Git-history rewrite, repository rotation, activation,
or canonical publication belongs to this development Phase.

## Prior M-063 Git active-tree 365-day policy handoff

- State: `DRAFT_NON_ACTIVE_GIT_ACTIVE_TREE_365D_READY`
- Phase: `MECHANISM_GIT_ACTIVE_TREE_365D_POLICY`
- Task Pack task completed: `M-063`
- M-063 dependency: `M-062`
- Required output: `DAILY_SHARDS_INDEX_PRUNE_RECEIPTS`
- Done gate: `DAY_364_AND_365_RETAINED_AFTER_365_ELIGIBLE`
- M-063 policy guard:
  `CodexSkills/governance/retention/git_active_tree_policy.py`
- M-063 policy guard raw SHA-256:
  `5789e1051c3060cfb1d221c710a51f47a631174708248a633e1e13c9becf8421`
- M-063 readiness:
  `CodexSkills/governance/retention/git-active-tree-365d-readiness.json`
- M-063 readiness raw SHA-256:
  `91592f339854fb205993e96a67698d7b6ce8fc54afd3b226f3090dfd49ab86f2`
- M-063 readiness self digest:
  `0bb6c1fb335115785495805ed001d6747a311dd1cbee335547beccaf8501df88`
- Retention-observation schema canonical SHA-256:
  `69858467989a55491ac8a8fe5654084fd94bc486a8d7c02ca732d2b62795af1a`
- Prune-plan schema canonical SHA-256:
  `d1487922673949f63b4701c1f8988b5acec8a2a13011f231f85c56a874767b0c`
- Readiness schema canonical SHA-256:
  `17699af2a0967df8b7160cb1f3e4fd1e452a8e69eadce0dbe56cf9c1e03aa168`
- Immutable M-062 predecessor:
  `sha1:72fd98353fa7065e520067c221e8689435dffd4c`
- Immutable candidate:
  `sha1:5ee37d7499c62ec19381dac7eb95cb12743ad2d5`
- Immutable candidate bundle digest:
  `36f0c66dd54d36365700a13f614a8c9bfa9619fb7c532af77566a858175b835e`
- Retention policy:
  `urn:linzecolin:agentdatabase:skillops:policy:retention:v3`
- Daily-manifest schema canonical SHA-256:
  `e9214388da78376da47770934454d65a57659d1dde33fa0cb4e36b79e4665337`
- Index-entry schema canonical SHA-256:
  `27663e9da3d9511cf9a03d1fe6f4b3779b1bbdab8f2f8adb94a274b8653a1433`
- Retention-receipt schema canonical SHA-256:
  `81435881fbc5e1ced14975edbedee63ca6555674db36f906bdfdee20eb317c45`
- Publication-manifest:v2 schema canonical SHA-256:
  `e7f8c4dd623379052829a21e3fcae77a98f14b3da1d79bb8f1d416f828063346`
- Clock basis: `UTC_WALL_CLOCK`
- Active-tree scope: `GIT_CURRENT_TREE`
- Real execution permitted: `false`
- Git-history rewrite or hard-delete claim: `false`
- Auto executor integration: `NOT_BOUND`
- Pending Task Pack task: `M-064`
- Exact next Phase: `MECHANISM_GIT_HISTORY_PERSISTENCE_DISCLOSURE`

M-063 validates the complete current-tree daily ledger instead of trusting one
manifest snapshot. Manifest history must begin at revision one, remain
gapless, chain by exact prior digest, preserve immutable part descriptors, and
contain each ACTIVE-to-PRUNED transition exactly once. Every pruned shard's
receipt remains bound to the exact predecessor manifest and Auto transaction
where that transition first occurred. Later revisions cannot rebind an old
receipt or silently discard its evidence.

The retention clock is recomputed from `first_published_at`.
`retention_not_before` is exactly 365 elapsed 24-hour days later. Day 364 and
the exact day-365 boundary both retain the full shard. Only a strictly later
observation is eligible for current-tree pruning. The retained index remains
mandatory and cannot embed a full event payload or substitute an aggregate
for the original shard during the 365-day interval.

An eligible observation produces only a deterministic plan. A valid execution
claim must delete the exact prior shard bytes while publishing the successor
daily manifest, `publication-manifest:v2`, and `retention-receipt:v3` as one
closed transaction. Equality at the +24-hour prune deadline is on time; a
later execution requires the fixed deadline-breach reason. M-063 has no
filesystem, Git, state, lock, network, publisher, or delete capability and
creates no real artifact instance. It makes no claim that pruning the current
tree removes bytes from Git history; M-064 is the separate disclosure Phase.

## M-063 validation

```text
M-063 targeted boundary/history/receipt tests: 16/16 PASS
complete Mechanism suite: 205/205 PASS
M-063 builder/schema/readiness: BYTE_EQUIVALENT
day 364 KEEP / exact day 365 KEEP / after day 365 ELIGIBLE: PASS
manifest history and original prune-receipt binding: PASS
candidate trust: 31 schemas / 5 policies PASS
schema-set lint:
  base 21 / candidate-compatible 41 / version 24 /
  M-063 full closure 73 PASS
OpenAIDatabase consumer + architecture: 23/23 PASS
consumer CLI: PASS / errors=[] / canonical publication=false
```

The pre-existing cross-owner transition remains fail-closed and is not
modified or relabeled by M-063:

```text
complete Auto suite: 200 tests / 5 failures / 20 errors
fault/privacy seed 271828: 149 tests / 5 failures / 25 errors
fault/privacy seed 314159: 149 tests / 5 failures / 25 errors
AUTO_REGISTRY_MIRROR_SKILL_COUNT_DRIFT
BOUND_REFERENCE_RESOLVER_RUNTIME_LOCAL_DRIFT
ACTIVATION_CONTROL_INTERFACE_SEMANTIC_MISMATCH
activation builder/lint:
  ACTIVATION_BOUND_RESOLVER_INTERFACE_CONTRACT_MISMATCH
```

The mirror count remains `90` while Auto is pinned to `89`. These failures are
the exact M-062 baseline and occur outside the M-063 changed path set. Final
acceptance additionally requires an ordinary commit, FF-safe push, and fresh
detached GitHub object/raw-byte readback of every changed path.

No Auto, candidate-bundle, policy, retention-receipt, OpenAIDatabase,
automation, or VERSION path change belongs to M-063. No verifier call,
historical Task Pack replay, real shard/index/manifest/receipt instance,
current-tree mutation, Git-history rewrite, or canonical publication belongs
to this development Phase.

## Prior M-062 public-safe queue lifecycle handoff

- State: `DRAFT_NON_ACTIVE_PUBLIC_SAFE_QUEUE_LIFECYCLE_READY`
- Phase: `MECHANISM_PUBLIC_SAFE_QUEUE_LIFECYCLE`
- Task Pack task completed: `M-062`
- M-062 dependencies: `M-031`, `M-061`
- Required output: `QUEUE_UNTIL_REMOTE_VERIFICATION`
- Done gate: `CONTAINS_NO_RAW_OR_PRIVATE_FIELDS`
- M-062 guard:
  `CodexSkills/governance/retention/public_safe_queue.py`
- M-062 guard raw SHA-256:
  `920c086674753d3e3226e1cb1ff2a2c1317e0a8049ead1819daf6e6552e0e20f`
- M-062 readiness:
  `CodexSkills/governance/retention/public-safe-queue-lifecycle-readiness.json`
- M-062 readiness raw SHA-256:
  `cf7193aa6057647ad48dd7c74ce133faaa138a49311322d13599f8329525712f`
- M-062 readiness self digest:
  `96f9ba8496f3e6496924c5c7cfb2536c3aeb694eacef202758365046d2093373`
- Queue-observation schema canonical SHA-256:
  `62b2eaa0e8e977850f05b97c437f09a22436fa7b9aebf2d64c458ff6c2eb9fa2`
- Remote-readback schema canonical SHA-256:
  `0963016596308548aadfe69ffbc230521e05b3bcd7171dfb40693799dd6b86f8`
- Lifecycle-plan schema canonical SHA-256:
  `5643a4881b5dfb19967a7ade5b46f60c19b6d7f850c5051aefd1ea8a3adb6c34`
- Readiness schema canonical SHA-256:
  `7b301a22ce6095e3108aaabe955d17082f47c6cc29276315d2e971aed070f42c`
- Immutable M-061 predecessor:
  `sha1:b023ac71c5c7852a95f4b87a56981fe7a42c32d9`
- Immutable candidate:
  `sha1:5ee37d7499c62ec19381dac7eb95cb12743ad2d5`
- Immutable candidate bundle digest:
  `36f0c66dd54d36365700a13f614a8c9bfa9619fb7c532af77566a858175b835e`
- Trusted private queue schema:
  `urn:linzecolin:agentdatabase:skillops:schema:public-queue-envelope:v2`
- Trusted public payload schema:
  `urn:linzecolin:agentdatabase:skillops:schema:public-run-event:v2`
- Queue owner plane: `AUTO`
- Lifecycle-policy owner plane: `MECHANISM`
- Real remote reader integration: `NOT_BOUND`
- Real queue settlement permitted: `false`
- Queue delete authority: `false`
- Watermark advance authority: `false`
- Pending Task Pack task: `M-063`
- Exact next Phase: `MECHANISM_GIT_ACTIVE_TREE_365D_POLICY`

M-062 keeps the private physical queue and its implementation entirely
Auto-owned. The Mechanism guard receives no queue root or physical path. It
validates the exact private envelope with the public scanner and requires its
payload to be one canonical `public-run-event:v2`; therefore a stored queue
artifact cannot contain raw prompt/output/reasoning, credentials, absolute
paths, unknown fields, or other private material. Envelope lane, bundle,
schema, UID, digest, Sydney day, and final part path must all bind exactly.

A READY entry without remote evidence returns `RETAIN_READY`. A SETTLED entry
without evidence fails closed. The settlement path has no
`remote_readback_verified` argument: a repository-external reader must first
resolve `origin/main` to a valid advanced Git object, then read the queued
path from that exact object. The complete bounded JSONL blob is checked for
JCS-per-line/LF framing and every record passes the public schema and privacy
consumer. The target event must occur exactly once and match UID, digest, and
bytes; a duplicate, missing event, same-as-expected remote head, mixed Git
algorithm, invalid sibling record, or caller-only digest claim fails closed.

The output is immutable public-safe observation/readback/plan evidence only.
It grants no deletion, state write, watermark advance, Git publication, or
activation. Daily shard manifest/index closure and the 365-day active-tree
boundary are deliberately deferred to M-063. No real remote call is made by
this readiness Phase and the real reader/Auto executor binding remains
`NOT_BOUND`.

## M-062 validation

```text
M-062 targeted queue/privacy/readback tests: 16/16 PASS
complete Mechanism suite: 189/189 PASS
M-062 builder/schema/readiness: BYTE_EQUIVALENT
candidate trust: 31 schemas / 5 policies PASS
schema-set lint:
  base 21 / candidate-compatible 41 / version 24 /
  M-062 full closure 70 PASS
OpenAIDatabase consumer + architecture: 23/23 PASS
consumer CLI: PASS / errors=[] / canonical publication=false
```

The pre-existing cross-owner transition remains fail-closed and is not
modified or relabeled by M-062:

```text
complete Auto suite: 200 tests / 5 failures / 20 errors
fault/privacy seed 271828: 149 tests / 5 failures / 25 errors
fault/privacy seed 314159: 149 tests / 5 failures / 25 errors
AUTO_REGISTRY_MIRROR_SKILL_COUNT_DRIFT
BOUND_REFERENCE_RESOLVER_RUNTIME_LOCAL_DRIFT
ACTIVATION_CONTROL_INTERFACE_SEMANTIC_MISMATCH
activation builder/lint:
  ACTIVATION_BOUND_RESOLVER_INTERFACE_CONTRACT_MISMATCH
```

The mirror count remains `90` while Auto is pinned to `89`. These failures
are identical to the M-061 baseline and occur outside the M-062 changed path
set. Final acceptance additionally requires an FF-safe push and a fresh
detached GitHub object/raw-byte readback of every changed path.

No Auto, candidate-bundle, public-value-policy, public-run-event,
queue-envelope, OpenAIDatabase, automation, or VERSION path change belongs to
M-062. No verifier call, historical Task Pack replay, real queue entry, state
write, remote network read, or canonical publication belongs to this
development Phase.

## Prior M-061 managed-raw 72-hour policy handoff

- State: `DRAFT_NON_ACTIVE_MANAGED_RAW_72H_POLICY_READY`
- Phase: `MECHANISM_MANAGED_RAW_72H_POLICY`
- Task Pack task completed: `M-061`
- M-061 dependency: `M-060`
- Required output: `SEGMENT_MARKERS_RECEIPTS_CLOCK_TESTS`
- Done gate: `71_59_59_KEEP_AND_72_00_00_EXPIRE`
- M-061 policy guard:
  `CodexSkills/governance/retention/managed_raw_policy.py`
- M-061 policy guard raw SHA-256:
  `d18da577b0530c319579ca95c77d6126cee0e56de9552a13965c2fbd2eadaf66`
- M-061 readiness:
  `CodexSkills/governance/retention/managed-raw-72h-readiness.json`
- M-061 readiness raw SHA-256:
  `d60a71554ffbe4bde30fbd639e723086598df22b69b4ceee04b070dd4ddb6e0f`
- M-061 readiness self digest:
  `dad952d9df1523bb63765dc028a4f3609251834dcb52dfa06a085341f555f774`
- Clock-observation schema canonical SHA-256:
  `3d136e72d7758cfb4d23d5356110ae12c73eabaf6033e4202d661d4ffac7131e`
- Retention-plan schema canonical SHA-256:
  `9ebc4777898d2804cc68bf6c17dfbc995110c6ff0baf30e4b0de814c7f1071cc`
- Readiness schema canonical SHA-256:
  `d43ac89cab969eca94ec0a80789e3deda242e114d919cba77dc89df8aca01ddb`
- Immutable M-060 predecessor:
  `sha1:21235d49fca818b74677172711cfe279d2da68a6`
- Immutable candidate:
  `sha1:5ee37d7499c62ec19381dac7eb95cb12743ad2d5`
- Immutable candidate bundle digest:
  `36f0c66dd54d36365700a13f614a8c9bfa9619fb7c532af77566a858175b835e`
- Retention policy:
  `urn:linzecolin:agentdatabase:skillops:policy:retention:v3`
- Retention policy canonical SHA-256:
  `bcad1e50a847e040d1350ca2fd977503b4ae642deabd727266e9dbbd26acb7ce`
- Retention receipt schema:
  `urn:linzecolin:agentdatabase:skillops:schema:retention-receipt:v3`
- Retention receipt schema canonical SHA-256:
  `81435881fbc5e1ced14975edbedee63ca6555674db36f906bdfdee20eb317c45`
- Persistent managed raw default enabled: `false`
- Production certification granted: `false`
- Real retention execution permitted: `false`
- Pending Task Pack task: `M-062`
- Exact next Phase: `MECHANISM_PUBLIC_SAFE_QUEUE_LIFECYCLE`

M-061 adds a pure UTC elapsed-time policy over candidates already authorized
by the immutable M-060 protected-root guard. It revalidates the exact
`raw-segment:v2` schema, ownership marker, candidate set, selection report,
and M-060 scope authorization before it evaluates time. A supplied receipt
must close back to the same M-060 report; a self-consistent replacement
observation, plan, and receipt cannot detach from that protected-root proof.

The clock is anchored to `created_at + 72 elapsed hours`.
`sealed_at` cannot extend TTL. The exact stages are immediate projection,
24-hour warning, 48-hour critical, 60-hour emergency catch-up, and 72-hour
hard expiry. `71:59:59` is `KEEP`; `72:00:00` is `EXPIRE`. Exact expiry is
not itself a breach. Any later observation requires an explicit recovery
cycle and last-runtime evidence at or before expiry; otherwise evaluation
fails closed. A truthful recovery receipt must carry
`OFFLINE_TTL_BREACH`.

An expiry plan freezes the required order: reproject public-safe evidence,
record `RAW_EXPIRED_UNPUBLISHED` if reprojection fails, delete only the owned
segment, then emit `retention-receipt:v3`. For an offline breach,
`OFFLINE_TTL_BREACH` is recorded first. The plan deliberately grants no
delete authority and emits no receipt itself. M-061 creates no persistent raw
segment, state, lock, watermark, queue record, receipt instance, Registry
write, Git publication, VERSION, activation, notification, or canonical run
artifact. Production certification and Auto executor binding remain false.

## M-061 validation

```text
M-061 targeted clock/scope/receipt tests: 13/13 PASS
complete Mechanism suite: 173/173 PASS
M-061 builder/schema/readiness: BYTE_EQUIVALENT
71:59:59 KEEP / 72:00:00 EXPIRE: PASS
offline overdue without gap evidence: FAIL_CLOSED
forged M-060 report binding: FAIL_CLOSED
candidate trust: 31 schemas / 5 policies PASS
Mechanism draft/candidate/resolver/release/v3/promotion/rollback/
  freshness/evaluator-protection/AU-040/M-060/M-061 builders: PASS
schema-set lint:
  base 21 / candidate-compatible 35 / version 24 / Registry 25 /
  Auto closure 37 / M-061 full closure 43 PASS
OpenAIDatabase consumer + architecture: 23/23 PASS
consumer CLI: PASS / errors=[] / canonical publication=false
```

The pre-existing cross-owner transition remains fail-closed and is not
modified or relabeled by M-061:

```text
complete Auto suite: 200 tests / 5 failures / 20 errors
fault/privacy seed 271828: 149 tests / 5 failures / 25 errors
fault/privacy seed 314159: 149 tests / 5 failures / 25 errors
AUTO_REGISTRY_MIRROR_SKILL_COUNT_DRIFT
BOUND_REFERENCE_RESOLVER_RUNTIME_LOCAL_DRIFT
ACTIVATION_CONTROL_INTERFACE_SEMANTIC_MISMATCH
activation builder/lint:
  ACTIVATION_BOUND_RESOLVER_INTERFACE_CONTRACT_MISMATCH
```

The mirror count is `90` while Auto remains pinned to `89`. These failures
are identical to the M-061 base and occur entirely outside the M-061 changed
path set.

No Auto, candidate-bundle, policy, retention-receipt, OpenAIDatabase,
automation, or VERSION path change belongs to M-061. No verifier call,
historical Task Pack replay, persistent raw write, real receipt emission, or
destructive action belongs to this development Phase.

## Prior M-060 protected-local / managed-raw boundary handoff

- State: `DRAFT_NON_ACTIVE_PROTECTED_LOCAL_MANAGED_RAW_BOUNDARY_READY`
- Phase: `MECHANISM_PROTECTED_LOCAL_DATA_MANAGED_RAW_BOUNDARY`
- Task Pack task completed: `M-060`
- M-060 dependencies: `M-003`, `M-031`
- Required output: `ROOT_TYPING_AND_LIFECYCLE_CONTRACT`
- Done gate: `LEGACY_LOCAL_SOURCE_NEVER_SELECTED_BY_72H_JOB`
- M-060 guard:
  `CodexSkills/governance/retention/root_lifecycle.py`
- M-060 guard raw SHA-256:
  `0b2436b889c7ff386f0468c2bfb7012159706784c830daa0ef1c19df4c663bf2`
- M-060 readiness:
  `CodexSkills/governance/retention/protected-local-managed-raw-readiness.json`
- M-060 readiness raw SHA-256:
  `6376e6776b6f23cf45080f5d3a9191fcdf0238168032b14356da8b88dd45bef4`
- M-060 readiness self digest:
  `b7c1ba479d0a47b97cb00b0556b2bf5db5b035bc156c9ae4e3bdc71337707080`
- Observation schema canonical SHA-256:
  `333c91ababd47048e809dd18b5589efabda7c44cc53a9827cc576be0d14959ca`
- Selection-report schema canonical SHA-256:
  `45120d6472a3fd2bb2206fa6047cba53e0918beb6cd80acf139efa693e68081b`
- Readiness schema canonical SHA-256:
  `a4bf03f6cf1c244952a5f99b33f37d61fe71d840b661f340db0b64dffeb8479b`
- Immutable candidate:
  `sha1:5ee37d7499c62ec19381dac7eb95cb12743ad2d5`
- Immutable candidate bundle digest:
  `36f0c66dd54d36365700a13f614a8c9bfa9619fb7c532af77566a858175b835e`
- Trusted private raw schema:
  `urn:linzecolin:agentdatabase:skillops:schema:raw-segment:v2`
- Trusted private raw schema canonical SHA-256:
  `032bdfb38c704a031e6c6f9c2f84dfbc82c9cc13af89e01723d8f439dff47dd5`
- Protected lifecycle classes:
  `SKILL_SOURCE`, `RUN_SOURCE`, `LEGACY_DATA`
- Managed raw lifecycle class: `STAGING`
- Public-safe non-raw queue class: `PUBLIC_QUEUE`
- Protected selected count: `0`
- Real retention execution permitted: `false`
- Pending Task Pack task: `M-061`
- Exact next Phase: `MECHANISM_MANAGED_RAW_72H_POLICY`

M-060 introduces a pure, realpath-aware root and candidate classifier. Private
physical paths remain in memory only. Symlinked roots or candidates, root
overlap, sibling-prefix confusion, traversal, special files, incomplete
payload closure, and time-of-check/time-of-use changes all fail closed.

`SKILL_SOURCE`, `RUN_SOURCE`, and `LEGACY_DATA` are always
`PROTECTED_LOCAL_DATA`: the guard does not parse them, select them for TTL, or
grant any delete/move/truncate budget. `PUBLIC_QUEUE` is explicitly separate
from raw retention. Only an exact `raw-segment:v2` in `STAGING`, with verified
schema, bundle, ownership marker, payload size, and payload digest, may return
`ELIGIBLE_FOR_M061_TIME_EVALUATION`.

That positive result is not expiry or deletion authority. Persistent raw is
disabled by default; production certification, 72-hour clock evaluation,
offline breach/gap receipts, expiry ordering, and any destructive operation
belong to M-061. The owner-locked offline contract remains truthful: the
72-hour target is enforceable only while the Mac/App runtime is available,
and the first recovery run must record any gap or
`OFFLINE_TTL_BREACH`. M-060 writes no state, Registry, Git publication,
VERSION, receipt, notification, activation, or canonical run artifact.

## M-060 validation

```text
M-060 targeted boundary tests: 10/10 PASS
complete Mechanism suite: 160/160 PASS
M-060 builder/schema/readiness: BYTE_EQUIVALENT
candidate trust: 31 schemas / 5 policies PASS
Mechanism draft/candidate/resolver/release/v3/promotion/rollback/
  freshness/evaluator-protection/AU-040 builders and lints: PASS
schema-set lint:
  base 21 / complete candidate 41 / version 24 / lifecycle 36 /
  Registry 25 / Auto-schema closure 37 / M-060 full closure 40 PASS
OpenAIDatabase consumer + architecture: 23/23 PASS
consumer CLI: PASS / errors=[] / canonical publication=false
```

The pre-existing cross-owner transition remains fail-closed and is not
modified or relabeled by M-060:

```text
complete Auto suite: 200 tests / 5 failures / 20 errors
fault/privacy seed 271828: 149 tests / 5 failures / 25 errors
fault/privacy seed 314159: 149 tests / 5 failures / 25 errors
AUTO_REGISTRY_MIRROR_SKILL_COUNT_DRIFT
BOUND_REFERENCE_RESOLVER_RUNTIME_LOCAL_DRIFT
ACTIVATION_CONTROL_INTERFACE_SEMANTIC_MISMATCH
activation builder/lint:
  ACTIVATION_BOUND_RESOLVER_INTERFACE_CONTRACT_MISMATCH
```

The mirror-count drift is now `90` versus Auto's pinned `89` after the
independent Teleiosis delivery on the M-060 base. No Auto, resolver,
activation-control, candidate-bundle, policy, OpenAIDatabase, automation, or
VERSION path change belongs to M-060. No verifier call or historical Task Pack
replay belongs to development.

## Prior M-059 evaluator/release-policy protection handoff

- State: `DRAFT_NON_ACTIVE_EVALUATOR_RELEASE_POLICY_PROTECTION_READY`
- Phase: `MECHANISM_EVALUATOR_RELEASE_POLICY_PROTECTION`
- Task Pack tasks completed: `M-056`, `M-057`, `M-058`, `M-059`
- M-059 dependencies: `M-051`, `M-056`
- Required output: `MAJOR_CLASSIFIER_AND_CHANGE_ISOLATION`
- Done gate: `OPTIMIZER_SELF_JUDGE_BLOCKED`
- M-056 immutable predecessor:
  `sha1:3cc02c15359d5204ad34fc9c20edbc02ec3802f0`
- M-058 immutable predecessor:
  `sha1:3d3c202ee629d79eadfb027da131e1afcb88a1f2`
- M-059 guard:
  `CodexSkills/governance/release/policy_protection.py`
- M-059 guard raw SHA-256:
  `13728feaaed54fefe1e43d2c7edc4b2777917b5237bee266bc897aa06ef65743`
- M-059 readiness:
  `CodexSkills/governance/release/evaluator-release-protection-readiness.json`
- M-059 readiness raw SHA-256:
  `344eaace3906bc03ede4520512887939c10fb37cea073ddbac306dccfd364f5f`
- M-059 readiness self digest:
  `b77cc4f395f4247b43fbeceee88ab34ccc2bae4ef5d2899a9932856b0cbebbb8`
- Observation schema canonical SHA-256:
  `f080f5bbcad6f49b084a02e6f8abc91a2b7899da3c849a31d96ba546e76a99d9`
- Report schema canonical SHA-256:
  `c6ffeb9b74014dfc7b63dd0bd887d5c759213be18085d6a79097da9d24ddef28`
- Readiness schema canonical SHA-256:
  `c18b4ccf071684913a6a4e3cea291e56e67c6d77b6cc1834492389d197ea2c12`
- Classifier policy:
  `urn:linzecolin:agentdatabase:skillops:policy:version:v3`
- Classifier policy canonical SHA-256:
  `5ea6047446ef26ab39d0e284f37619859d57c8c419daa1cffefffdc12935cfe0`
- Real Registry observation:
  `89 identities / 89 instances / 89 versions / 0 CHALLENGER / 0 CHAMPION`
- Registered snapshot/current working-tree parity: `false`
- Real protection/promotion execution permitted: `false`
- Pending Task Pack task: `M-060`
- Exact next Phase:
  `MECHANISM_PROTECTED_LOCAL_DATA_MANAGED_RAW_BOUNDARY`

M-059 adds two bundle-external, exact-digest-pinned contracts and one pure
guard. The observation contains complete baseline/proposed EvalProfiles,
five release-policy descriptors, promotion-controller bytes, change-origin
role binding, and an exact seven-operation access-denial audit. Optimizer
attempts to read sealed labels or write evaluator, EvalProfile, rubric, hard
gates, promotion controller, or release policy must all be `DENIED` with
distinct evidence; missing, reordered, allowed, reused, late, or cross-role
claims fail closed.

The guard recomputes every protected difference. Evaluator/holdout/judge,
weights/hard gates, promotion-controller, notification, privacy, retention,
source-material, and version-policy changes map to the locked version-policy
v3 MAJOR trigger vocabulary. Impact cannot be supplied or downgraded by the
caller. An optimizer-originated change is blocked; an independently originated
change is isolated to a separate MAJOR release and remains ineligible for the
Skill promotion transaction.

Only an unchanged protected snapshot with an exact audit may delegate through
the immutable M-058 freshness gate, which then delegates to M-056. A forged
PASS report is recomputed and rejected. The guard returns canonical report and
authorization bytes only. It never writes Registry, state, Git, VERSION,
notification, activation, or public artifacts.

The real registered snapshot still has no evaluated champion or challenger.
The later `dd338e1` context-kernel mirror remains absent from catalogs,
assignments, and the pinned registered snapshot, so no real M-059 execution or
BOUND attribution is inferred.

## M-059 validation

```text
M-059 targeted protection tests: 10/10 PASS
complete Mechanism suite: 150/150 PASS
M-059 builder/schema/readiness: BYTE_EQUIVALENT
candidate trust: 31 schemas / 5 policies PASS
Mechanism draft/candidate/resolver/release/v3/promotion/rollback/
  freshness/AU-040 builders and lints: PASS
schema-set lint: 21 / 41 / 24 / 30 schemas PASS
OpenAIDatabase consumer + architecture: 23/23 PASS
consumer CLI: PASS / errors=[] / canonical publication=false
```

The pre-existing cross-owner transition remains fail-closed and is not
modified or relabeled by M-059:

```text
complete Auto suite: 200 tests / 5 failures / 20 errors
fault/privacy seed 271828: 149 tests / 5 failures / 25 errors
fault/privacy seed 314159: 149 tests / 5 failures / 25 errors
AUTO_REGISTRY_MIRROR_SKILL_COUNT_DRIFT
BOUND_REFERENCE_RESOLVER_RUNTIME_LOCAL_DRIFT
AUTO_BOUND_REFERENCE_RESOLVER_INTERFACE_DRIFT
ACTIVATION_CONTROL_INTERFACE_SEMANTIC_MISMATCH
activation builder/lint:
  ACTIVATION_BOUND_RESOLVER_INTERFACE_CONTRACT_MISMATCH
```

No Auto, resolver, activation-control, candidate-bundle, policy,
OpenAIDatabase, or VERSION path changes belong to M-059. No verifier call or
historical Task Pack replay belongs to development.

## Prior M-058 freshness/drift-monitor handoff

- State: `DRAFT_NON_ACTIVE_FRESHNESS_DRIFT_MONITOR_READY`
- Phase: `MECHANISM_FRESHNESS_DRIFT_MONITOR`
- Task Pack tasks completed: `M-056`, `M-057`, `M-058`
- Required output: `STALE_BEHAVIOR_LATENCY_ALERTS`
- Done gate: `STALE_SCORE_CANNOT_INDEPENDENTLY_PROMOTE`
- M-056 immutable predecessor:
  `sha1:3cc02c15359d5204ad34fc9c20edbc02ec3802f0`
- M-057 immutable predecessor:
  `sha1:6d263e02ca6104abca5ae930b5eaa0944d8d5960`
- M-058 monitor:
  `CodexSkills/governance/monitoring/freshness_drift.py`
- M-058 monitor raw SHA-256:
  `ef703ede2b18c91f907ab6e9db1fedb2923b5fc2a9d456becae4b27a087af1a3`
- M-058 readiness:
  `CodexSkills/governance/monitoring/freshness-drift-readiness.json`
- M-058 readiness raw SHA-256:
  `416beacd6a72d3d5517211a3758452228bd445ab10fc887928b0575e2865d812`
- M-058 readiness self digest:
  `8864203d59f925f8f3110ff1e779ebdb19d26818a337de764596de2de1afa96d`
- Observation schema canonical SHA-256:
  `ebda03e6ad49a2fef25b14f5b587bdddbed1075f6fc3fe175b16366b227fca50`
- Report schema canonical SHA-256:
  `2b529885458798f070d089bdee8e3fbfa032072a3f74c0c43c8de236c7e57581`
- Readiness schema canonical SHA-256:
  `0a6dd000ba0fe23489061cb5332db03361e0714da83370024670a316bea744cc`
- Real Registry observation:
  `89 identities / 89 instances / 89 versions / 0 CHALLENGER / 0 CHAMPION`
- Post-M-057 working-tree drift:
  `sha1:dd338e19ce2e470863e14783c068f194f64c71c4` restored
  `registry/codex/context-kernel` without adding it to the four catalogs,
  assignments, or registered snapshot
- Registered snapshot/current working-tree parity: `false`
- Real monitor/promotion execution permitted: `false`
- Pending Task Pack task: `M-059`
- Exact next Phase: `MECHANISM_EVALUATOR_RELEASE_POLICY_PROTECTION`

M-058 adds bundle-external, exact-digest-pinned observation and report
contracts. It recomputes UTC age/date expiry, all seven behavior dimensions,
p95 latency and sample sufficiency, Skill/model/tool/dependency/dataset/
evaluator/policy/environment context, incidents, and EvalProfile trigger
coverage. Any alert requires re-evaluation. An omitted retest trigger becomes
its own blocking `PROFILE_RETEST_TRIGGER_GAP`; profile omissions cannot hide
real drift.

The canonical M-058 promotion wrapper requires one recomputed
`PROMOTION_GATE/PASS` report per Scorecard, exact observation/Profile/
Scorecard/decision digest closure, and an observation no later than the
decision. It delegates to the immutable M-056 append function only after those
checks pass. A stale Scorecard therefore cannot promote merely because its
stored `freshness_state` still says `FRESH`.

The monitor returns canonical evidence bytes and a deterministic authorization
digest only. No Registry/state/Git/VERSION write, activation, canonical
publication, Auto mutation, notification, or verifier call is part of this
Phase. The real registered snapshot contains no evaluated champion or
challenger, so execution remains false.

## M-058 validation

```text
M-058 targeted monitor tests: 10/10 PASS
complete Mechanism suite: 140/140 PASS
M-058 builder/schema/readiness: BYTE_EQUIVALENT
candidate trust: 31 schemas / 5 policies PASS
Mechanism draft/candidate/resolver/release/v3/promotion/AU-040 builders: PASS
schema-set lint: 21 / 38 / 24 schemas PASS
OpenAIDatabase consumer + architecture: 23/23 PASS
consumer CLI: PASS / errors=[] / canonical publication=false
Auto draft/transport/promotion builders and lints: PASS
```

The unchanged cross-owner transition remains explicitly non-green:

```text
complete Auto suite: 200 tests / 5 failures / 20 errors
fault/privacy seed 271828: 149 tests / 5 failures / 25 errors
fault/privacy seed 314159: 149 tests / 5 failures / 25 errors
root fail-closed codes:
  AUTO_REGISTRY_MIRROR_SKILL_COUNT_DRIFT
  BOUND_REFERENCE_RESOLVER_RUNTIME_LOCAL_DRIFT
  AUTO_BOUND_REFERENCE_RESOLVER_INTERFACE_DRIFT
  ACTIVATION_CONTROL_INTERFACE_SEMANTIC_MISMATCH
activation builder/lint:
  ACTIVATION_BOUND_RESOLVER_INTERFACE_CONTRACT_MISMATCH
```

M-058 changes no Auto, resolver, activation-control, or OpenAIDatabase path and
does not hide or relabel those predecessor transition failures.

## Prior M-057 rollback/revocation-controller handoff

- State: `DRAFT_NON_ACTIVE_ROLLBACK_REVOCATION_CONTROLLER_READY`
- Phase: `MECHANISM_ROLLBACK_REVOCATION_CONTROLLER`
- Task Pack tasks completed: `M-056`, `M-057`
- Required output: `NEW_EVENT_ROLLBACK_AND_DRILL_EVIDENCE`
- Done gate:
  `NO_HISTORY_REWRITE_AND_PRIOR_CHAMPION_RESTORABLE`
- M-056 predecessor object:
  `sha1:3cc02c15359d5204ad34fc9c20edbc02ec3802f0`
- M-056 controller raw SHA-256:
  `bcc39aaa1e6c817fb321a8772996a05fffffe947cd8bbc218a5f7bad16db3e53`
- M-057 controller:
  `CodexSkills/governance/promotion/rollback_controller.py`
- M-057 controller raw SHA-256:
  `44bd788038cadc6dd89810fbaebf9cefdc5351af96871e982193769eb2ececd2`
- M-057 readiness:
  `CodexSkills/governance/promotion/rollback-controller-readiness.json`
- M-057 readiness raw SHA-256:
  `9ecdbc1f5cd103d6420cdd2d81b4ab14e94ce50668c6fabfe96ba05a9fd22494`
- M-057 readiness self digest:
  `3cf47b465f46a458b2c16b57599462ca6638076cb32ab0e57ab2c86d6c41a93b`
- Bundle-external drill schema:
  `urn:linzecolin:agentdatabase:skillops:schema:rollback-drill-evidence:v1`
- Drill schema raw / canonical SHA-256:
  `fb0741973e1889e3dc8ac73dd5f1cdcf7c8afc7a34419c669b35ae83b048f0d9` /
  `05ccf4edce100c3ac1502d7dec3d64418a090a9d38ff5acb04282f488ac7edea`
- Readiness schema raw / canonical SHA-256:
  `ef95d965462bf67ee1af9d75951b3e41d1d47856ee206e63bc539e940eb3bb43` /
  `e945d9df234aba24f38141000f5b26570862c275bf4c063c9ba216de18ea978c`
- Lifecycle ledger domain: `SKILLOPS_LIFECYCLE_LEDGER_V1`
- Real Registry observation:
  `89 identities / 89 instances / 89 versions / 0 CHALLENGER / 0 CHAMPION`
- Real rollback/revocation execution permitted: `false`
- Pending Task Pack task: `M-058`
- Exact next Phase: `MECHANISM_FRESHNESS_DRIFT_MONITOR`

The M-057 controller is a pure function. It keeps M-056 immutable and delegates
every `PROMOTE` / `REJECT` step to it against the current derived champion
map. It adds deterministic `ROLLBACK` / `REVOKE` steps to the same ordered
lifecycle ledger, so a promotion may still be validated after a restore.

Each rollback/revocation decision is a new `promotion-decision:v1` event. Its
drill evidence binds the exact Registry snapshot, predecessor lifecycle-ledger
digest, current champion, restore target, record/model/event provenance,
notification receipt, and five-kind verification closure. The restore target
must be derived from the base champion plus ordered prior events in the same
Identity scope; caller-provided target claims are insufficient. Revoked
versions are permanently ineligible as restore targets.

Planned actions require `PRE_WRITE_SENT` before the event. Emergency
containment requires observed containment evidence and
`POST_CONTAINMENT_SENT`. A failed drill, incomplete reference set, altered
history, stale predecessor digest, cross-scope target, notification-order
swap, or post-decision drill fails closed.

The drill and readiness schemas are bundle-external and require explicit
canonical schema-digest trust. The controller only returns RFC 8785 JCS event
and evidence bytes plus an immutable derived view. No Registry/state/Git/
VERSION write, activation, canonical publication, Auto mutation, notifier
call, or verifier call is part of this Phase.

## M-057 validation

```text
M-057 targeted controller tests: 10/10 PASS
complete Mechanism suite: 130/130 PASS
M-057 builder/schema/readiness: BYTE_EQUIVALENT
candidate trust: 31 schemas / 5 policies PASS
Mechanism draft/candidate/resolver/release/v3/promotion/AU-040 builders: PASS
schema-set lint: 21 / 38 / 24 schemas PASS
OpenAIDatabase consumer + architecture: 23/23 PASS
consumer CLI: PASS / errors=[] / canonical publication=false
Auto draft/transport/promotion builders and lints: PASS
```

The unchanged cross-owner transition remains explicitly non-green:

```text
complete Auto suite: 200 tests / 4 failures / 20 errors
fault/privacy seed 271828: 149 tests / 4 failures / 25 errors
fault/privacy seed 314159: 149 tests / 4 failures / 25 errors
root fail-closed codes:
  BOUND_REFERENCE_RESOLVER_RUNTIME_LOCAL_DRIFT
  AUTO_BOUND_REFERENCE_RESOLVER_INTERFACE_DRIFT
  ACTIVATION_CONTROL_INTERFACE_SEMANTIC_MISMATCH
activation builder/lint:
  ACTIVATION_BOUND_RESOLVER_INTERFACE_CONTRACT_MISMATCH
```

M-057 changes no Auto path and does not hide or relabel those existing
transition failures. The broad OpenAIDatabase command-ownership audit also
retains its unrelated baseline mismatch (`expected 84, observed 90`).

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

At the registered 89-root object, `codex/context-kernel` was absent from the
source, mirror, catalogs, assignments, and snapshot. Its older record chain
remains available through immutable object `sha1:5db5beec…` and
`source-drift-reconciliation.v1.json`.

The later external `dd338e1` commit restored a working-tree mirror path only;
it still has no catalog assignment or registered record in the pinned
snapshot. M-058 does not infer a deletion, registration, evaluation,
promotion, or BOUND transition from that unreconciled path. Registered-
snapshot/current-tree parity is therefore false.

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
