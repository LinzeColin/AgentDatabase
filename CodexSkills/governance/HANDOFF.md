# Mechanism handoff

- State: `DRAFT_NON_ACTIVE_PARITY_COMPLETE_MATERIALIZED`
- Phase: `MECHANISM_REGISTRY_PARITY_COMPLETE_MATERIALIZATION`
- Protocol:
  `urn:linzecolin:agentdatabase:skillops:protocol:cross-pack:v1`
- SRV candidate: `v0.0.0.3`
- Candidate bundle digest:
  `36f0c66dd54d36365700a13f614a8c9bfa9619fb7c532af77566a858175b835e`
- Candidate Git object:
  `sha1:5ee37d7499c62ec19381dac7eb95cb12743ad2d5`
- Consumer Git object:
  `sha1:91a12e48351be3ee05ec23ef61aec81056b02014`
- Source-content-sync Auto Git object:
  `sha1:dc653654603f5bfee3bd41890b49cfad700cf541`
- Source-content-sync Auto runtime-interface raw SHA-256:
  `7f2e335b682ec98c15f2e21e74bc0c2af24768cda7e5ed1ddc1b5e341449ac84`
- Source-content-sync Auto module count: `27`
- Current Auto corrective Git object:
  `sha1:bea0f6c172362223325f9a8033c6c498bcdde6df`
- Current Auto runtime-interface raw SHA-256:
  `8aa7a179ee7374de974c145017fd671c764a42e073b577ab4b0b4081ff5784b2`
- Current Auto module count: `27`
- Control interface raw SHA-256:
  `72a0c4c2ad6c810f2b0cd7eb0fb46bb168b7315c15807838f7a988d759f5cb6f`
- Resolver interface raw SHA-256:
  `9351465917c344269b37f470bd30d127afe764bae223ba0368e39d9d9a64af41`
- Resolver interface self digest:
  `e67799c396a49d42b49c2e1960f760fbdb23dd32496575b7bbd81bd388026ae8`
- Registered Registry snapshot self digest:
  `10979826bf63b49fbde8da6ece51d6ead6909225b3c62af994e110dea31e1718`

These Git objects are ordinary ancestors in the coordinated commit chain.
Every production consumer must independently fetch them and receive its
expected candidate, control, and Registry snapshot tuples from repo-external
trusted state. The current checkout and any artifact self-report are not trust
roots.

## Registered current Registry

The current materialization reads only immutable Git object
`sha1:dc653654603f5bfee3bd41890b49cfad700cf541`. It contains exactly 88 current
Skill roots:

```text
AGENTS=24
CLAUDE=3
CODEX=55
CODEX_SYSTEM=6
total=88
tracked aliases=20
metadata-invalid roots=0
```

The four final source catalogs and global snapshot are:

```text
CodexSkills/registry/agents/_catalog/catalog.v1.json
CodexSkills/registry/claude/_catalog/catalog.v1.json
CodexSkills/registry/codex/_catalog/catalog.v1.json
CodexSkills/registry/codex-system/_catalog/catalog.v1.json
CodexSkills/registry/_global/registry-snapshot.v1.json
```

All five final artifacts have status `REGISTERED`. The global snapshot closes
88 Identity, 88 Instance, and 88 current Version records; all Versions remain
`QUARANTINED/UNVERIFIED`, so `binding_eligible_version_count=0`.
`source_mirror_parity.status=COMPLETE`,
`source_mirror_parity.binding_eligible=true`, aliases close at `20 == 20`, and
`reason_codes=[]`. The parity boolean means the source/mirror prerequisite is
closed; it does not make any Version eligible or permit BOUND.

The registered snapshot is loaded only with this repo-external tuple shape:

```text
verified_git_object_id=sha1:<this Mechanism successor commit>
canonical_snapshot_digest=
  10979826bf63b49fbde8da6ece51d6ead6909225b3c62af994e110dea31e1718
canonical_snapshot_path=
  CodexSkills/registry/_global/registry-snapshot.v1.json
canonical_snapshot_schema_id=
  urn:linzecolin:agentdatabase:skillops:schema:registry-snapshot:v1
mode=REGISTERED
```

The final commit ID is deliberately external to the snapshot bytes and is
filled only after the ordinary commit is remotely verified. The artifact's
`source_material_git_object_id` remains the distinct Auto source object
`sha1:dc653654…`.

Governance draft catalogs and the draft snapshot are rebuilt from the same
current tree under `CodexSkills/governance/registry/materialized/**`, with
status `DRAFT_NON_ACTIVE`. The registered files are not accepted by the draft
trust mode, and draft files are not accepted by `REGISTERED` mode.
The registered candidate bytes are also retained under
`CodexSkills/governance/registry/materialized/registered/**`; each is exactly
byte-equal to its final Registry artifact, so the promotion claim is
independently reproducible rather than inferred from matching semantic fields.

## Immutable lineage

The historical 89-root snapshot remains immutable at Mechanism Git object
`sha1:5db5beecf3de7ac916020ca988f6e875891e19b1`, with self digest
`31f49c8ffa3bd2d268feec49b2869f409d61a5bfbb0b03f382bc562996b7fa76`.
The current builder verifies that object and preserves every unchanged
SkillVersion record byte-for-byte.

Of the 88 current paths, 74 keep their exact historical Version record. Fourteen
paths receive a new content-addressed Version and an exact
`supersedes_version_uid`:

```text
codex/frontend-slides
codex/graphify
codex/gsap-core
codex/gsap-frameworks
codex/gsap-performance
codex/gsap-plugins
codex/gsap-react
codex/gsap-scrolltrigger
codex/gsap-skills
codex/gsap-timeline
codex/gsap-utils
codex/guizang-ppt-skill
codex/persona-distiller-group
codex/verifier
```

The changed set covers the three source-content corrections and the Skills
whose versioned tree now includes the 20 verified aliases. No unchanged
Version UID maps to changed record bytes.

`codex/context-kernel` remains absent from current source, mirror, catalog,
assignment, and snapshot records. Its historical Identity/Instance/Version
references are retained only in
`CodexSkills/governance/registry/source-drift-reconciliation.v1.json`, pinned
to the historical Mechanism object. Its current observation stays
`UNOBSERVED`; no lifecycle transition, deletion, promotion, or binding is
inferred. Therefore historical `source_root_parity_satisfied` and
`whole_source_parity_satisfied` remain false even though current 88-root
source/mirror parity is complete.

## Control and closed gates

The resolver lineage verifies source-sync evidence only from immutable Auto
object `sha1:dc653654…`; it does not require the current checkout to equal that
historical interface or module set. The successor control separately
exact-binds the current Auto corrective object `sha1:bea0f6c…`, interface, and
27 modules. It records:

```text
repository_bound=true
runtime_state_write_permitted=true
effective_runtime_state_write_permitted=false
bound_reference_resolver_implementation_complete=true
bound_reference_resolver_auto_integration_complete=false
bound_reference_resolver_gate_satisfied=false
runtime_state_write_gate_status=
  BOUND_REFERENCE_RESOLVER_AUTO_INTEGRATION_PENDING
```

The first two values are control-level prerequisites already reached; they do
not authorize side effects. Until Auto consumes the exact registered snapshot
and resolver contract, effective state, lock, worktree, mutable Git, Gmail,
outbox, watermark, publisher, and canonical publication remain blocked before
side effects.

The following also remain false or unperformed:

```text
production_trust_permitted
current_snapshot_can_emit_bound
consumer_first_repository_shards_permitted
au_040_daily_jsonl_shard_complete
au_040_complete
runtime_state_instance_created
external state/Gmail READY
notification real-message metadata readback
m0c_b_permitted
ACTIVE / activation
canonical publication
schedule_authority_resolved
schedule_complete
```

No `CodexSkills/VERSION`, canonical run artifact, state instance, Gmail or
network action, automation change, App action, history replay, or verifier
call occurred.

## Next exact action

After this Mechanism commit is FF-pushed and independently read back, the only
next phase is `AUTO_BOUND_REFERENCE_RESOLVER_INTEGRATION`.

That Auto-owned phase must consume:

- the exact successor control tuple;
- the exact candidate 31/5 tuple;
- the registered snapshot tuple above, using the verified successor commit;
- all four registered catalogs and the three Registry schemas from that same
  Git object.

It must prove deterministic `UNKNOWN/MAPPING_NOT_PROVABLE` for all real
current versions because the binding-eligible set is empty, keep every
state/mutable-Git/network side effect fail-closed until its successor control
sync, and must not fabricate BOUND, activate, publish, create VERSION, resolve
the schedule conflict, touch the three PAUSED automations, or call verifier.

Development still must not call verifier. After both planes are complete, the
Owner designates the final task that may invoke a fresh verifier.
