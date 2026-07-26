# Auto Registry source-content sync handoff

- State: `DRAFT_NON_ACTIVE_REGISTRY_SOURCE_CONTENT_SYNCED_CONTROL_PENDING`
- Phase: `AUTO_REGISTRY_SOURCE_CONTENT_SYNC`
- Phase base / predecessor control Git object:
  `sha1:5db5beecf3de7ac916020ca988f6e875891e19b1`
- Predecessor control raw SHA-256:
  `a31751bf1258f646412aba84e0b5c46f84f09b77e33156caea372873b819ff36`
- Predecessor resolver raw SHA-256:
  `38c7952ae712e6d4543bb4f4c1f3e5f8a98b00b36780c99bfce6944a722eabf0`
- Predecessor reconciliation raw SHA-256:
  `f36f20f8ee8551eae155c5b58ba0d776cc4fdd2b9f08d3186519ce052a297120`
- Reconciliation self digest:
  `24d02db5182463912074c109f2b5be350126d62340f58e6463755edbad1b799c`
- Control-bound Auto Git object:
  `sha1:b5a32c817e4016f595fa33caed6bce1d51199e63`
- Control-bound Auto runtime-interface raw SHA-256:
  `e88ec8c711434619756ee8f91c451e941501764e30e4a7fff310d8685b02140a`
- Control-bound Auto module count: `27`
- Current Auto runtime-interface raw SHA-256:
  `7f2e335b682ec98c15f2e21e74bc0c2af24768cda7e5ed1ddc1b5e341449ac84`
- Current Auto module count: `27`

## Exact source-content closure

Only the three paths authorized by the predecessor control were synchronized:

```text
codex/graphify
  regular files=695
  aliases=0
  bytes=13373911
  content digest=
    816bfb795d8998983a3df2b8786a2d1c691e9e2280dd7be2bdc07acd47775587

codex/persona-distiller-group
  regular files=35
  aliases=0
  bytes=1064137
  content digest=
    eaf8f8e32b1ade683387346adec8a21b241541567e910609247426ec3626b921

codex/verifier
  regular files=61
  aliases=0
  bytes=525884
  content digest=
    7727bcfb4d03bcc97fafeedea1f8e773945e6be70f0351e8ca32525ff1e8d556
```

Each content digest is computed by the existing lstat-first sync contract over
the complete source-relative path/kind/content set. Source and mirror digests
are equal. The materialization builder additionally requires the complete
physical mirror set for all three paths to be Git tracked; ignored fixture
cache objects and distribution ZIP files therefore cannot silently disappear
from the committed tree.

The final full-source dry-run reports no additions, updates, or removals:

```text
source roots=88
source counts=agents:24,claude:3,codex:55,codex-system:6
source aliases=20/20
mirror aliases=20/20
remaining source/mirror content drift=[]
source_mirror_parity_satisfied=true
```

## Historical-root and ownership truth

The missing `codex/context-kernel` root remains absent from both current source
and mirror. It remains `UNOBSERVED` under the Mechanism reconciliation; Auto
did not restore it, infer a lifecycle transition, or modify historical
Identity/Instance/Version references.

Historical 89-root parity is therefore deliberately still false:

```text
historical source roots=89
current source roots=88
missing exact root=[codex/context-kernel]
source_root_parity_satisfied=false
whole_source_parity_satisfied=false
```

The five reserved namespaces remain protected and physically absent:

```text
CodexSkills/registry/agents/_catalog/**
CodexSkills/registry/claude/_catalog/**
CodexSkills/registry/codex/_catalog/**
CodexSkills/registry/codex-system/_catalog/**
CodexSkills/registry/_global/**
```

No catalog, global Identity record, Registry snapshot, resolver payload, or
promotion artifact was generated. The historical incomplete materialization
remains non-promotable.

## Closed gates

This materialization is not a new production trust root:

```text
current_auto_runtime_control_bound=false
runtime_state_write_permitted=false
repository_bound=false
bound_reference_resolver_auto_integration_complete=false
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
```

No VERSION, state instance, lock, watermark, queue/outbox entry, shard, index
shard, daily manifest, retention receipt, Gmail/network operation, activation,
canonical publication, automation, App action, verifier call, history replay,
or added time window occurred. The three PAUSED automations were untouched.

## Validation

Completion requires and records:

```text
Auto full suite: 192/192 PASS
Registry sync + dynamic-profile integration: 15/15 PASS
fault/privacy seed 271828: 141/141 PASS
fault/privacy seed 314159: 141/141 PASS
OpenAIDatabase consumer + architecture: 23/23 PASS
consumer CLI: PASS; errors=[]; canonical publication=false
Mechanism base 5db: 73/73 PASS
Mechanism transition tree: exact expected cross-owner failures only
  REGISTRY_AUTO_RESERVATION_INTERFACE_CURRENT_DRIFT
  ACTIVATION_BOUND_RESOLVER_GENERATED_DRIFT:
    REGISTRY_AUTO_RESERVATION_INTERFACE_CURRENT_DRIFT
candidate builder/trust: 31 schemas / 5 policies PASS
activation, resolver, AU-040 and Auto builders/lints: byte-equivalent
external full-source dry-run: 88 roots / 20 aliases / no drift
Git tracked closure: all three synchronized trees exact
Registry credential scan: PASS; hits=0; aliases=20
Python 3.9 AST: 19 changed Python files PASS
Broad command ownership retains the pre-existing external baseline failure:
  top-level script entrypoints: expected 84, observed 90
```

Detached GitHub object/raw readback and owned cleanup are completion-time
evidence and are reported externally after the FF-safe push.

## Next exact action

The only next phase is
`MECHANISM_REGISTRY_PARITY_COMPLETE_MATERIALIZATION`. Mechanism must
independently read back the verified Auto successor object and exact current
interface, then rebuild the four source catalogs and global snapshot from the
current 88-root content-closed tree. It must retain the reconciled historical
`context-kernel` references without fabricating a current source root.

This handoff does not authorize resolver Auto integration, BOUND, state,
canonical run logs, AU-040 completion, Gmail, M0c-B, ACTIVE, schedule changes,
VERSION, automation, verifier, or history replay.
