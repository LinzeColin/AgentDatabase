# SkillOps Auto contracts and runtime safety kernel

State: `DRAFT_NON_ACTIVE`.

This Auto-owned directory contains the historical eight-schema public set,
four promoted public-v2 schemas, four Auto-private schemas, deterministic
builders/validators, and the non-active runtime safety kernel. The final
candidate uses six surviving historical Auto schemas plus all four promoted
schemas inside an exact 31-schema / five-policy shared bundle. The private set
never enters the shared bundle.

`transport-draft/` preserves the four accepted AU-040 source schemas.
`schemas/public-v2/` contains their promoted exact-byte copies and a separate
promotion interface. Both roots are outside the recursive public-schema
loader used by the historical 29/5 candidate. The final manifest explicitly
names the promoted stable paths; the historical loader contract remains
immutable evidence.

Deterministic contract entrypoints:

```bash
/usr/bin/python3 -B CodexSkills/registry/auto/tools/build_schemas.py --check
/usr/bin/python3 -B CodexSkills/registry/auto/tools/build_transport_draft.py --check
/usr/bin/python3 -B CodexSkills/registry/auto/tools/build_schema_promotion.py --check
/usr/bin/python3 -B CodexSkills/registry/auto/tools/build_runtime_interface.py --check
/usr/bin/python3 -B CodexSkills/registry/auto/tools/validate_auto.py lint-draft
/usr/bin/python3 -B CodexSkills/registry/auto/tools/validate_transport_draft.py lint-draft
/usr/bin/python3 -B CodexSkills/registry/auto/tools/validate_schema_promotion.py lint-promotion
/usr/bin/python3 -B CodexSkills/registry/auto/tools/validate_au040_writer.py --help
/usr/bin/python3 -B CodexSkills/registry/auto/tools/validate_au040_publisher.py --help
/usr/bin/python3 -B -m unittest discover \
  -s CodexSkills/registry/auto/tests -p 'test_*.py'
```

All entrypoints use the repository-pinned canonicalizer and offline validator
from `CodexSkills/governance/tools/`. They do not implement JCS independently,
resolve schemas over the network, or install dependencies at runtime.

## Runtime entrypoints

- `tools/runtime_preflight.py` requires three repo-external trust tuples: the
  candidate content tuple, the Mechanism control tuple, and the immutable
  registered Registry snapshot tuple. It runs capability/vendor/offline
  Registry and all-current-version resolver checks before any runtime-state
  write.
- `runtime/binding_resolver.py` is the only Auto adapter for the
  Mechanism-owned resolver. It verifies the pinned resolver interface, four
  catalogs, four schemas, two Mechanism runtime modules, and registered
  snapshot from Git. The registered 88-version snapshot has zero
  binding-eligible versions, so its exhaustive historical projection is
  `UNKNOWN/MAPPING_NOT_PROVABLE`; it cannot invent a `skill_ref` or emit
  `BOUND`. The exact Teleiosis source/mirror sync now makes the current source
  set 89 roots, so that 88-version snapshot is explicitly stale and cannot
  satisfy the current resolver gate until Mechanism rebuilds it.
- `tools/bound_reference_resolver_cli.py` is the production read-only
  resolution entrypoint. It requires all three external tuples and a successor
  control with the resolver integration and gate enabled.
- `runtime/state.py` implements atomic writes, non-stealing single-flight
  leases, explicit stale reconciliation, and readback-gated lane watermarks.
- `runtime/source.py` implements lstat-first source inventory, exact policy
  exclusions, safe same-root aliases, deterministic tree digests, and public
  inventory/coverage projection.
- `runtime/catalog_reservation.py` reserves every
  `registry/<source>/_catalog/**` path, `registry/_global/**`, and the
  Teleiosis `registry/codex/_delivery-backups/**` evidence outside Skill
  enumeration/deletion, and binds the exact 20-entry relative-symlink alias
  set. It also classifies `.wbi-install-transactions` and
  `.wbi-install.lock` as explicit non-Skill operational nodes that remain
  covered by source scanning rather than being silently skipped.
  `CodexSkills/sync_skills.py` consumes that contract with a full-source
  lstat/containment/size/special-node preflight before any mirror removal or
  replacement; registered aliases are preserved without dereference and
  unregistered aliases fail closed.
- `runtime/privacy.py` and `runtime/queue.py` enforce serialized public-value
  scanning and an atomic public-safe-only queue.
- `runtime/run_log_writer.py` validates an existing daily tree through
  descriptor-relative `O_NOFOLLOW` reads and deterministically plans exact
  JCS-per-LF event shards, persistent index shards, and append-only daily
  manifest revisions. It returns in-memory PUT artifacts only; it has no
  publisher, queue, canonical-repository write, or state-root entrypoint.
- `runtime/writer_shadow.py` is development-only. It proves the exact
  e643/85ed historical Git-object closure and current repository-binding byte
  self-consistency without requiring current working-tree control/Mechanism
  bytes to equal e643. It returns
  `UNBOUND_TELEIOSIS_REGISTRY_REBUILD_PENDING` and can never
  return a production
  `BootstrapContext`.
- `runtime/notification.py` keeps the actual recipient and provider payload in
  a repo-external outbox; public receipts contain only `recipient_ref`.
- `runtime/gmail_api.py` is the production Gmail API transport. It refreshes
  an owner-held OAuth credential. Its no-send preflight verifies the
  authenticated profile and performs one fixed `users.messages.list` query
  for a reserved `.invalid` RFC822 Message-ID. Transactional lookup separately
  searches `in:sent` by the real deterministic RFC822 Message-ID, verifies the
  exact private payload-digest header, sends only after an unambiguous
  `NOT_FOUND`, and reads the provider message back before returning `SENT`.
  Provider timeouts, malformed query responses, ambiguity, header mismatch, or
  missing scopes block the planned write without sending again.
- `runtime/activation.py` consumes both the external candidate trust tuple and
  the external control tuple. It verifies the local Mechanism activation
  runtime against the selected control Git object before loading the exact
  31-schema / five-policy candidate closure plus two bundle-external
  activation schemas. Intent, receipt, and settlement reads are
  descriptor-relative `O_NOFOLLOW`; public JSON must be exact RFC 8785 JCS
  bytes without a BOM or trailing newline.
- `tools/activation_handshake_cli.py` is the production activation entrypoint.
  `notify-intent` derives all notification metadata from a verified intent,
  checks the live remote head, and then invokes Gmail. `publish-settlement`
  revalidates every physical byte, proves the live single-flight lock, requires
  the exact four settlement artifacts plus the distinguished settlement
  itself, performs an ordinary expected-head FF push, and remotely reads every
  byte back.
- `tools/notification_transport_cli.py` remains the generic transport
  preflight/non-activation entrypoint. It consumes the same external candidate
  and control trust tuples,
  resolves only the fixed repo-external paths below, verifies the authenticated
  Gmail profile matches the owner mapping, proves the Gmail query endpoint
  accepts the fixed no-send capability probe, renders the locked MAJOR
  template from public-safe structured facts, and returns a public-safe
  receipt. It rejects `planned_action=ACTIVATE`; activation cannot bypass the
  verified intent entrypoint.
- `runtime/publication.py` permits only expected-head FF pushes followed by
  remote byte readback. Candidate runtime publication is impossible. The
  coordinated-activation path no longer accepts caller booleans, caller digest
  maps, caller `SENT` strings, or caller shared-gate status maps; it derives
  those facts from the externally trusted settlement, exact bytes, live lock,
  path gates, policy/privacy validation, and remote head.
- `runtime/repository_binding.py` keeps repository integration distinct from
  repository authority. It requires the exact external candidate, control,
  and V2 consumer closure already proved by bootstrap, consumes the
  Mechanism-owned `BOUND_REFERENCE_RESOLVER` decision, and only then checks a
  clean real-directory `main` reference, exact SSH fetch/push URL, SHA-1
  object format, repo-external scratch/state roots, and per-transaction
  expected head without network access. A sealed in-process permit is required
  before state, lock, Gmail, worktree, `ls-remote`, or canonical publisher
  access. Caller booleans, URLs, digest maps, and `registry/index.json` cannot
  create that permit.
- `runtime/retention.py` keeps persistent raw disabled by default and can act
  only on validated, owned managed segments under retention policy/receipt v3.
  Final v3 receipt semantics now validate exact current-tree part/index
  evidence, 365-day anchors, 24-hour deadlines, and truthful breach codes.
  The GIT current-tree executor remains absent and fail closed.
- `runtime/schedule.py` currently implements the frozen Australia/Sydney
  04:15 contract, Sunday forced full, DST-safe UTC conversion, manual parity,
  and no late-start rejection. A later Auto goal says 05:30 but does not
  explicitly supersede the earlier Owner-locked 04:15 value, so schedule
  authority remains unresolved and this implementation is not claimed as the
  final schedule.

Run the exact candidate preflight from the repository root with the explicitly
provisioned interpreter:

```bash
/usr/bin/python3 -B CodexSkills/registry/auto/tools/runtime_preflight.py \
  --repo-root . \
  --verified-git-object-id sha1:5ee37d7499c62ec19381dac7eb95cb12743ad2d5 \
  --expected-bundle-digest 36f0c66dd54d36365700a13f614a8c9bfa9619fb7c532af77566a858175b835e \
  --canonical-manifest-path CodexSkills/governance/bundles/schema-bundle-manifest.v1.json \
  --mode CANDIDATE \
  --verified-control-git-object-id sha1:df63339e1bb6106250ce169241477191744c254f \
  --expected-control-interface-raw-sha256 72a0c4c2ad6c810f2b0cd7eb0fb46bb168b7315c15807838f7a988d759f5cb6f \
  --canonical-control-interface-path CodexSkills/governance/activation/control-interface.json \
  --control-mode DRAFT_NON_ACTIVE_CONTROL \
  --verified-registry-git-object-id sha1:df63339e1bb6106250ce169241477191744c254f \
  --expected-registry-snapshot-digest 10979826bf63b49fbde8da6ece51d6ead6909225b3c62af994e110dea31e1718 \
  --canonical-registry-snapshot-path CodexSkills/registry/_global/registry-snapshot.v1.json \
  --canonical-registry-snapshot-schema-id urn:linzecolin:agentdatabase:skillops:schema:registry-snapshot:v1 \
  --registry-mode REGISTERED
```

This command is read-only, but the predecessor control binds exact Auto object
`bea0f6c1...`, runtime-interface raw `8aa7a179...`, and 27 modules. The current
checkout is deliberately not that byte set, so production preflight
fails with `BOOTSTRAP_AUTO_RUNTIME_INTERFACE_LOCAL_DRIFT` before state, lock,
watermark, recipient, Gmail, outbox, or publisher access. Development-only
repository evidence is obtained with the existing bounded
`validate_au040_publisher.py` shadow entrypoint; it must not be
interpreted as `TRUSTED`, `READY`, or a production preflight PASS. Neither
checkout self-reporting nor a caller boolean/digest map can replace any
external tuple. Once a successor control changes the working-tree control
bytes, the stale df633 tuple instead fails earlier with the exact
`BOOTSTRAP_CONTROL_INTERFACE_LOCAL_DRIFT` code; the historical builder and
shadow evidence remain stable because they read their named immutable objects
exclusively from Git.

## M0c activation control

The activation control interface remains `DRAFT_NON_ACTIVE` at
`CodexSkills/governance/activation/control-interface.json`. Runtime use
requires all four external values: the verified control Git object, expected raw
interface SHA-256, canonical interface path, and
`DRAFT_NON_ACTIVE_CONTROL` mode. Repository self-reporting is never sufficient.

The two-stage production CLI is intentionally not demonstrated with a live
instance here. The final Mechanism-owned consumer V2 was independently
GitHub-read back at object
`91a12e48351be3ee05ec23ef61aec81056b02014`; raw SHA-256
`189a47300fc1aa6012e87feb6184833cb717cdbe2b9dc9be6db89197f579939c`.
It binds candidate `5ee37d74...` / `36f0c66d...`, daily part/index/manifest
and retention-receipt contracts, while keeping both publication gates false.
Control object `df63339e...`, raw SHA-256 `72a0c4c2...`, binds the same
candidate and consumer plus predecessor Auto object `bea0f6c1...`, interface
raw `8aa7a179...`, and 27 modules. It also pins the registered 88-version
Registry snapshot and Mechanism resolver. The runtime-interface builder
verifies those exact Git blobs while reporting, in an
`INTERFACE_MATERIALIZATION_ONLY` snapshot, the current 29-module Auto
integration as unbound.

That gate does not permit canonical publication. The consumer still declares
`canonical_publication_permitted=false` and
`repository_shards_permitted=false`. A later independent run must also prove
the repo-external state root, recipient mapping, Gmail OAuth scopes,
authenticated-recipient binding, and query endpoint readiness. Only a later
M0c-B run may create an intent, send the notification, create a settlement,
or invoke `publish-settlement`.

## Production Gmail private-path contract

The production state root is repo-external and owner-only (`0700`). Its
notification directories are created by `StateLayout`; the Owner provisions
the two files as regular `0600` files:

```text
state-root/private/notification/recipient-mapping.v1.json
state-root/private/notification/gmail-api.v1.json
```

The recipient file uses private schema
`skillops.private-recipient-mapping.v1` and binds `owner-primary` to the actual
Gmail address. The Gmail file uses private schema
`skillops.private-gmail-api-config.v1`, `user_id=me`, an OAuth client/refresh
credential, and a sorted scope list containing both a send scope and a
query/read scope. Actual addresses, client credentials, refresh/access tokens,
provider message IDs, email bodies, and absolute paths never enter Git or a
public receipt.

The provider preflight is explicit and performs no send:

```bash
/usr/bin/python3 -B CodexSkills/registry/auto/tools/notification_transport_cli.py \
  preflight \
  --repo-root . \
  --state-root "$SKILLOPS_STATE_ROOT" \
  --scratch-root "$SKILLOPS_SCRATCH_ROOT" \
  --expected-remote-head "$SKILLOPS_EXPECTED_REMOTE_HEAD" \
  --verified-git-object-id sha1:5ee37d7499c62ec19381dac7eb95cb12743ad2d5 \
  --expected-bundle-digest 36f0c66dd54d36365700a13f614a8c9bfa9619fb7c532af77566a858175b835e \
  --canonical-manifest-path CodexSkills/governance/bundles/schema-bundle-manifest.v1.json \
  --mode CANDIDATE \
  --verified-control-git-object-id sha1:df63339e1bb6106250ce169241477191744c254f \
  --expected-control-interface-raw-sha256 72a0c4c2ad6c810f2b0cd7eb0fb46bb168b7315c15807838f7a988d759f5cb6f \
  --canonical-control-interface-path CodexSkills/governance/activation/control-interface.json \
  --control-mode DRAFT_NON_ACTIVE_CONTROL \
  --verified-registry-git-object-id sha1:df63339e1bb6106250ce169241477191744c254f \
  --expected-registry-snapshot-digest 10979826bf63b49fbde8da6ece51d6ead6909225b3c62af994e110dea31e1718 \
  --canonical-registry-snapshot-path CodexSkills/registry/_global/registry-snapshot.v1.json \
  --canonical-registry-snapshot-schema-id urn:linzecolin:agentdatabase:skillops:schema:registry-snapshot:v1 \
  --registry-mode REGISTERED
```

After a future Mechanism control sync, the preflight first binds the
authenticated profile to the private owner
mapping, then calls `users.messages.list` with `maxResults=1` and the fixed
query
`in:sent rfc822msgid:<skillops-query-capability-v1@notification.skillops.invalid>`.
The reserved Message-ID contains no recipient, credential, mailbox content, or
transaction identifier. The response is shape-checked and discarded; no
provider message ID is returned. This proves only query-endpoint capability.
It does not claim that a real sent message or its metadata headers were read
back. Exact metadata readback remains mandatory after the real M0c-B send
before a receipt can become `SENT`.

There is no launchd job, local daemon, background retry loop, or runtime
package installation. The Codex automation invokes the entrypoint directly;
manual and scheduled runs use the same path.

`DRAFT_NON_ACTIVE` code must not create or update `CodexSkills/VERSION`, claim
ACTIVE state, publish canonical data, send a production notification without
the coordinated M0c intent, write a production watermark, or update the
automation. The Mechanism-owned consumer-first trust tuple is complete, but
its preactivation publication gates remain closed.

AU-040 is not complete: `skills_runs/example.json` is only prior scaffolding,
never the final run-layout contract. The final candidate and consumer now bind
bounded daily part/index JSONL, append-only daily manifest revisions, and
retention receipt v3. The deterministic runtime writer and
publication-manifest:v2 publisher and repository-binding adapter are
integrated, but no
shard/manifest/index instance was created. The publisher recomputes its exact
manifest from physical PUT/DELETE descriptors, validates JSONL per RFC 8785
JCS line, re-reads prior part/index/manifest bytes before DELETE, and admits
only the exact daily run-log path/schema/serialization closure. Production
still fails before state, lock, Gmail, worktree, `ls-remote`, or Git backend
access until a successor control binds the new Auto object and separately
provides Mechanism-owned repository and resolver authority. This materialized
interface deliberately keeps `repository_bound=false`,
`bound_reference_resolver_gate_satisfied=false`,
`au_040_daily_jsonl_shard_complete=false`, and
`canonical_publication_permitted=false`; physical publication stays disabled.

Mechanism Authority Audit Revision 6 is represented by the Auto-owned source
schemas under `transport-draft/`: daily manifest v1, persistent event index
v1, publication manifest v2, and retention receipt v3. The draft validator
tests JCS-per-line framing, exact byte evidence, daily arithmetic, persistent
index closure, and receipt-backed pruning.

Mechanism independently accepted those exact bytes, the ten-field public-value
allowlist delta, `public-value-policy:v2`, `retention-policy:v3`, and seven
cross-artifact semantic guards. Auto then promoted the four unchanged schema
files to `schemas/public-v2/`. The promotion interface binds both source
interfaces, every raw and canonical digest, the stable final paths, and the
guard-code set. Its validator proves exact-byte equality and the offline 31/5
target closure. The historical 29/5 candidate is proved from the exact
manifest blob at candidate object `899a4374...`; exact equality with the same
blob at promotion object `ab49666...` proves that the Auto promotion did not
change it. The validator deliberately does not use the current working-tree
manifest as historical truth, so the authorized Mechanism 31/5
materialization can follow without invalidating promotion evidence.

The exact final 31/5 candidate, V2 consumer, and predecessor control remain
unchanged. The Registry reservation materialization records exact alias parity
as 20/20 while separately recording source-root drift: the historical source
object had 89 roots and the current source has 88, with
`codex/context-kernel` missing. Mechanism records that missing root as
`UNOBSERVED`, retains its historical references, and forbids inferred
lifecycle or promotion.

The bounded source-content phase exact-synced only `codex/graphify`,
`codex/persona-distiller-group`, and `codex/verifier`. Its machine evidence
binds every mirror file through the existing lstat-first digest contract,
requires the complete physical set to be Git tracked, and proves no remaining
current source/mirror content drift. The 88-root/20-alias closure is distinct
from historical 89-root parity: `source_mirror_parity_satisfied=true` while
`source_root_parity_satisfied=false` and
`whole_source_parity_satisfied=false`. No reserved catalog/global namespace,
catalog, or Registry snapshot was created.

The next phase is
`MECHANISM_REGISTRY_PARITY_COMPLETE_MATERIALIZATION`: Mechanism must
independently read back this Auto object, rebuild the four catalogs and
snapshot from the current 88-root successor, retain the reconciled historical
`context-kernel` references without restoring a source root, and decide
promotion. The Auto interface contains 27 runtime modules and a separately
digested sync executor. It keeps
`bound_reference_resolver_auto_integration_complete=false`,
`bound_reference_resolver_gate_satisfied=false`,
`current_auto_runtime_control_bound=false`,
`runtime_state_write_permitted=false`, `repository_bound=false`, AU-040
completion, activation, and canonical publication all false.

The schedule conflict remains unresolved. The external Gmail readiness gate
remains false until the Owner injects the repo-external state root and the
controlled preflight succeeds.
Never invoke the verifier during development; the Owner selects a fresh
verifier only after both planes finish.
