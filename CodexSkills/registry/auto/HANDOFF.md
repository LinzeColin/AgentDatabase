# Auto Registry catalog path reservation handoff

- State: `DRAFT_NON_ACTIVE_REGISTRY_CATALOG_RESERVED_SOURCE_DRIFT_PENDING`
- Phase: `AUTO_REGISTRY_CATALOG_PATH_RESERVATION`
- Phase base / predecessor control Git object:
  `sha1:488321c83b2a669ea964873e22a94b8e65429350`
- Predecessor control raw SHA-256:
  `6f7a2bdedfc7c388c4b6e1c2345855e110305b7ed906874676a5ba6daf7779f2`
- Predecessor resolver interface raw SHA-256:
  `0fe26ab55d92a1c6f5628e2a8d27becbdcc839ccfd73372150a2339ffe7eb4cb`
- Control external mode: `DRAFT_NON_ACTIVE_CONTROL`
- Control root status: `DRAFT_NON_ACTIVE`
- Control-bound Auto Git object:
  `sha1:49ac09dbd9c8a2e18d5a199088a910dc77e7d365`
- Control-bound Auto runtime-interface raw SHA-256:
  `c7af9d1406fe2ed084d5a30fab6cded3897a83c1602e6c40587cf28c75a2c75c`
- Control-bound Auto module count: `26`
- Current Auto runtime-interface raw SHA-256:
  `e88ec8c711434619756ee8f91c451e941501764e30e4a7fff310d8685b02140a`
- Current Auto module count: `27`
- Current sync executor raw SHA-256:
  `1fd015a043dfe48034df03d8a821cda5793c90694191a8b629672efaf33283ac`

## Completed

The Auto-owned sync plane now reserves, but does not create, every future
Mechanism control namespace:

```text
CodexSkills/registry/agents/_catalog/**
CodexSkills/registry/claude/_catalog/**
CodexSkills/registry/codex/_catalog/**
CodexSkills/registry/codex-system/_catalog/**
CodexSkills/registry/_global/**
```

Enumeration, compatibility-index generation, deletion propagation and prune
selection exclude those paths. A reserved path that is a symlink or special
node fails closed.

Before any mirror deletion or replacement, `sync_skills.py` now performs a
full lstat-first source preflight. Source roots, skill roots and parents must
be real contained directories; unclassified dot roots, special nodes,
unsafe/dangling/escaping aliases, unreadable nodes and non-policy oversize
files fail closed. Oversize content is never silently skipped. The credential
gate admits only the exact registered relative aliases and scans their target
bytes through the ordinary real-file traversal.

The exact frozen alias set is restored in the repository without dereference:

```text
expected aliases=20
observed source aliases=20
observed mirror aliases=20
directory aliases=2
regular-file aliases=18
alias_set_digest=
  75f6db86e5a18cc000985dc32a719ac7e0bc15b22b2e3f20c0d32d3138f27387
source_alias_parity_satisfied=true
mirror_alias_parity_satisfied=true
```

Each interface entry binds source namespace, alias path, raw relative link
target, normalized same-root target, target type, metadata digest and target
content digest. Git object readback must additionally prove mode `120000`.

## Source-root drift and mirror removal

Alias parity is deliberately separate from whole-source parity:

```text
historical source material Git object=
  sha1:44a38890ec38ceb24ccae1ec6f5b1fc8e93aefa1
historical source roots=89
current source roots=88
delta=-1
missing exact root=[codex/context-kernel]
source_root_parity_satisfied=false
whole_source_parity_satisfied=false
```

The existing local→repository deletion-propagation contract removed that
exact mirror root and regenerated only the Auto-owned compatibility
`CodexSkills/index.json` / `README.md`. The interface binds the historical
byte count and SHA-256 of all three removed paths from object `488321c...`;
the current mirror and compatibility index both contain 88 roots and no
`codex/context-kernel`.

The source dry-run also observed three non-alias content drifts which this
bounded Phase did not copy:

```text
codex/graphify
codex/persona-distiller-group
codex/verifier
```

Mechanism must reconcile those facts and the missing root before deciding
identity/version lifecycle or producing a successor catalog/snapshot.

## Authority separation

No final source catalog, global identity, Registry snapshot or resolver
payload was generated or promoted. The incomplete 44a materialization remains
non-promotable. The existing Mechanism resolver implementation remains
present but is not Auto-integrated and cannot satisfy the BOUND gate.

```text
catalog_path_reservation_complete=true
bound_reference_resolver_implementation_complete=true
bound_reference_resolver_auto_integration_complete=false
bound_reference_resolver_gate_satisfied=false
current_auto_runtime_control_bound=false
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
next_phase=MECHANISM_REGISTRY_SOURCE_DRIFT_RECONCILIATION
```

No VERSION, state instance, lock, watermark, queue/outbox entry, shard, index
shard, daily manifest instance, retention receipt instance, Gmail/network
operation, activation, canonical publication, automation, App action,
verifier call, history replay or added time window was performed. The three
PAUSED automations were not touched.

## Validation

```text
Auto full suite: 190/190 PASS
sync + dynamic-profile integration: 15/15 PASS
fault/privacy seed 271828: 139/139 PASS
fault/privacy seed 314159: 139/139 PASS
OpenAIDatabase consumer + architecture: 23/23 PASS
consumer CLI: PASS; errors=[]; canonical publication=false
Mechanism: 72 run; 71 pass; one expected cross-owner transition error
  test_02a_integrated_auto_interface_and_modules_are_exact
  ACTIVATION_AUTO_INTERFACE_CURRENT_DRIFT
candidate builder/trust: 31 schemas / 5 policies PASS
activation control builder/lint: PASS; predecessor raw unchanged
BOUND resolver builder: byte-equivalent; frozen 89-root draft unchanged
AU-040 semantic acceptance builder/lint: PASS
Auto schema/draft/promotion/runtime builders: byte-equivalent
Auto draft/promotion validators: PASS
Broad command ownership retains the pre-existing external baseline failure:
  top-level script entrypoints: expected 84, observed 90
  (this Phase changes no OpenAIDatabase path)
```

Detached GitHub object/raw readback and owned cleanup are completion-time
evidence and must only be appended to the external handoff after the ordinary
FF-safe push succeeds.

## Next exact action

The next owner is Mechanism and the only next phase is
`MECHANISM_REGISTRY_SOURCE_DRIFT_RECONCILIATION`. It must independently read
back the verified Auto successor object, its runtime interface, 27 modules,
sync artifact, 20 Git symlink blobs and three exact removals. It then owns the
source-drift/lifecycle ruling and any complete catalog/snapshot
rematerialization decision.

This handoff does not authorize resolver Auto integration, BOUND, state,
canonical run logs, AU-040 completion, Gmail, M0c-B, ACTIVE, schedule changes,
VERSION, automation, verifier or history replay.
