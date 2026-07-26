# Auto BOUND reference resolver integration handoff

- State: `DRAFT_NON_ACTIVE_BOUND_REFERENCE_RESOLVER_INTEGRATED_CONTROL_SYNC_PENDING`
- Phase: `AUTO_BOUND_REFERENCE_RESOLVER_INTEGRATION`
- Phase base / predecessor control Git object:
  `sha1:df63339e1bb6106250ce169241477191744c254f`
- Predecessor control raw SHA-256:
  `72a0c4c2ad6c810f2b0cd7eb0fb46bb168b7315c15807838f7a988d759f5cb6f`
- Control-bound Auto Git object:
  `sha1:bea0f6c172362223325f9a8033c6c498bcdde6df`
- Control-bound Auto runtime-interface raw SHA-256:
  `8aa7a179ee7374de974c145017fd671c764a42e073b577ab4b0b4081ff5784b2`
- Control-bound Auto module count: `27`
- Current Auto runtime-interface raw SHA-256:
  `3ca77e4670f1d891a280e3932d92ce1dfa17b3c95f2645174bf5ae72b8570173`
- Current Auto module count: `29`

## Exact immutable Registry closure

The Auto runtime consumes the Mechanism-owned resolver only through three
repo-external trust tuples: final candidate, control, and registered Registry
snapshot. The registered tuple is exact:

```text
verified Git object:
  sha1:df63339e1bb6106250ce169241477191744c254f
snapshot path:
  CodexSkills/registry/_global/registry-snapshot.v1.json
snapshot schema:
  urn:linzecolin:agentdatabase:skillops:schema:registry-snapshot:v1
mode:
  REGISTERED
snapshot self digest:
  10979826bf63b49fbde8da6ece51d6ead6909225b3c62af994e110dea31e1718
snapshot raw SHA-256:
  217bcecc0057c271171cfd00169fe99c039dced478c2f1ef1c2cb2527f3c76f2
resolver interface path:
  CodexSkills/governance/registry/resolver-interface.json
resolver interface raw SHA-256:
  9351465917c344269b37f470bd30d127afe764bae223ba0368e39d9d9a64af41
resolver interface self digest:
  e67799c396a49d42b49c2e1960f760fbdb23dd32496575b7bbd81bd388026ae8
```

The adapter verifies the pinned four catalogs, four resolver schemas, two
Mechanism runtime modules, 88 Identity records, 88 Instance records, 88
Version records, and the snapshot self digest entirely from Git. Unknown
objects, tuple substitutions, local Mechanism runtime drift, malformed
requests, or unbound successor controls fail closed.

The registered snapshot has zero binding-eligible versions. A complete
projection of all 88 current catalog entries therefore returns only:

```json
{"binding_state":"UNKNOWN","unknown_reason_code":"MAPPING_NOT_PROVABLE"}
```

No source path/name match is treated as identity evidence, no `skill_ref` is
invented, and no current entry can emit `BOUND`.

## Production ordering

`runtime/binding_resolver.py` is the only Auto adapter for the Mechanism
resolver. `tools/bound_reference_resolver_cli.py` is the production read-only
entrypoint. Runtime preflight, the orchestrator, activation, notification,
repository binding, and canonical-publication paths now require the external
registered snapshot tuple. The resolver gate is checked before state root,
lock, watermark, recipient mapping, Gmail client, outbox, worktree,
`ls-remote`, mutable Git backend, or publisher access.

The current Auto bytes are intentionally not bound by the predecessor
control. The predecessor still binds the 27-module `bea0f6c...` Auto object.
Consequently production entrypoints fail with exact local Auto drift until a
successor Mechanism control binds this Auto commit, its runtime-interface raw
digest, and all 29 module digests.

## Closed gates

This phase is implementation evidence, not production authority:

```text
current_auto_runtime_control_bound=false
bound_reference_resolver_auto_integration_complete=true
bound_reference_resolver_readonly_preflight_verified=true
bound_reference_resolver_gate_satisfied=false
effective_runtime_state_write_permitted=false
runtime_state_write_permitted=false
repository_bound=false
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

No VERSION, state, lock, watermark, queue/outbox item, shard, index, daily
manifest, retention receipt, Gmail/network operation, activation, canonical
publication, automation, App action, verifier call, or history replay occurs
in this phase. The three PAUSED automations remain untouched.

## Validation and next exact action

Pre-commit completion gates:

```text
Auto full suite: 204/204 PASS
fault/privacy seed 271828: 153/153 PASS
fault/privacy seed 314159: 153/153 PASS
OpenAIDatabase consumer + architecture: 23/23 PASS
consumer CLI: PASS; errors=[]; canonical publication=false
Mechanism transition tree: 73 tests PASS plus the one exact expected
  cross-owner transition error ACTIVATION_AUTO_INTERFACE_CURRENT_DRIFT
candidate trust: 31 schemas / 5 policies PASS
Auto, Mechanism, activation, resolver, AU-040 builders/lints:
  byte-equivalent / PASS
Python 3.9 AST and exact 17-path Auto ownership boundary: PASS
stale predecessor production preflight/resolver CLI:
  BOOTSTRAP_AUTO_RUNTIME_INTERFACE_LOCAL_DRIFT before side effects
Broad command ownership retains the pre-existing external baseline failure:
  top-level script entrypoints: expected 84, observed 90
```

Ordinary FF-safe push, detached GitHub object/raw readback, and owned cleanup
remain completion-time evidence and are reported externally.

The only next phase is
`MECHANISM_POST_BOUND_REFERENCE_RESOLVER_CONTROL_SYNC`. It must bind the new
Auto object, runtime-interface raw digest, and all 29 modules while keeping
canonical publication, AU-040 completion, Gmail/state readiness, M0c-B,
ACTIVE, VERSION, and the unresolved schedule false. This handoff does not
authorize that successor phase automatically.
