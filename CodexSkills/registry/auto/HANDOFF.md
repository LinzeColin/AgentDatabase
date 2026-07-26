# Auto Teleiosis source-sync handoff

- State: `DRAFT_NON_ACTIVE_TELEIOSIS_REGISTRY_REBUILD_REQUIRED`
- Phase: `AUTO_TELEIOSIS_SOURCE_CONTENT_SYNC`
- Source material Git object:
  `sha1:a8f1f6ff8003db43fad722a5afd3b19615dd325e`
- Auto runtime-interface raw SHA-256:
  `3e91bf41c9550fa48264db3b72ee102b0acec65b883374d2735fbd7169801d9e`
- Auto module count: `29`
- Exact next Phase:
  `MECHANISM_REGISTRY_TELEIOSIS_PARITY_MATERIALIZATION`

## Exact source and mirror closure

The Teleiosis registration adds one real Codex source root and one exact
Registry mirror root:

```text
source_relative_path=codex/teleiosis
regular_file_count=104
alias_count=0
byte_count=598392
content_digest=
  252e9cf65b991dd7bd7c36734257b0b5da47689cbf2d1c7d7bb4ca766aa93bcb
```

The current source/mirror inventory is now:

```text
AGENTS=24
CLAUDE=3
CODEX=56
CODEX_SYSTEM=6
total=89
tracked aliases=20
missing historical source root=codex/context-kernel
added current source root=codex/teleiosis
```

The live `sync_skills.py --dry-run` inventory closes at 89 and reports no
mirror change. Two Teleiosis installer nodes are explicitly classified as
non-Skill operational evidence while remaining inside source-coverage scans:

```text
.wbi-install-transactions
.wbi-install.lock
```

The delivery evidence namespace
`CodexSkills/registry/codex/_delivery-backups/**` is now reserved outside
Skill enumeration and deletion, alongside the four `_catalog` namespaces and
the global Registry snapshot namespace. Unknown dot entries still fail closed.

## Registry and runtime disposition

The existing registered Mechanism snapshot is immutable 88-root evidence. It
does not contain Teleiosis and therefore is not compatible with the current
89-root source set:

```text
registered_registry_snapshot_source_skill_count=88
registry_current_source_skill_count=89
registered_registry_snapshot_current_source_compatible=false
registered_registry_snapshot_rebuild_required=true
bound_reference_resolver_readonly_preflight_verified=true
current_source_bound_reference_resolver_readonly_preflight_verified=false
bound_reference_resolver_gate_satisfied=false
runtime_state_write_permitted=false
```

Historical 88-root resolver evidence remains readable from its named Git
object. It is not rewritten or misrepresented as current. The working-tree
Auto interface is not control-bound, so production paths continue to fail
closed before state, lock, watermark, recipient mapping, Gmail, worktree,
mutable Git, outbox, or publisher access.

## Closed gates

```text
current_auto_runtime_control_bound=false
registered Registry 89-root rebuild=false
runtime_state_instance_created=false
repository_bound=false
consumer_first_repository_shards_permitted=false
canonical_publication_permitted=false
au_040_daily_jsonl_shard_complete=false
au_040_complete=false
external_gmail_ready_gate_satisfied=false
notification_real_message_metadata_readback_verified=false
m0c_b_permitted=false
schedule_authority_resolved=false
schedule_complete=false
ACTIVE / activation=false
```

No VERSION, state, lock, watermark, queue/outbox item, shard, index, daily
manifest, retention receipt, Gmail/network operation, activation, canonical
publication, automation, App action, verifier call, or history replay occurs
in this Phase.

## Validation

```text
Auto full suite: 207/207 PASS
fault/privacy seed 271828: 156/156 PASS
fault/privacy seed 314159: 156/156 PASS
OpenAIDatabase consumer + architecture: 23/23 PASS
consumer CLI: PASS; errors=[]; canonical publication=false
Mechanism transition tree: 89 tests PASS plus the one exact expected
  cross-owner transition error ACTIVATION_AUTO_INTERFACE_CURRENT_DRIFT
candidate trust/builders: 31 schemas / 5 policies PASS
Auto schemas/transport/promotion/runtime builders and lints: PASS
Mechanism candidate/resolver/release-foundation builders: PASS
live source dry-run: 89 instances / 74 names / aliases 20/20 /
  no mirror change / no write
```

## Next exact action

Mechanism must consume the exact remotely verified Auto successor object and
runtime-interface bytes, rebuild the four catalogs and global snapshot from
the 89-root source material object above, preserve immutable 88-root lineage,
add Teleiosis Identity/Instance/Version records as non-binding-eligible, and
keep every write/activation gate closed. Auto runtime/control sync is a later
separate Phase.
