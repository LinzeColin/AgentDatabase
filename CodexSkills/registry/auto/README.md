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
/usr/bin/python3 -B -m unittest discover \
  -s CodexSkills/registry/auto/tests -p 'test_*.py'
```

All entrypoints use the repository-pinned canonicalizer and offline validator
from `CodexSkills/governance/tools/`. They do not implement JCS independently,
resolve schemas over the network, or install dependencies at runtime.

## Runtime entrypoints

- `tools/runtime_preflight.py` requires two repo-external trust tuples: the
  candidate content tuple and the Mechanism control tuple. It runs
  capability/vendor/offline-Registry checks before any runtime-state write.
- `runtime/state.py` implements atomic writes, non-stealing single-flight
  leases, explicit stale reconciliation, and readback-gated lane watermarks.
- `runtime/source.py` implements lstat-first source inventory, exact policy
  exclusions, safe same-root aliases, deterministic tree digests, and public
  inventory/coverage projection.
- `runtime/privacy.py` and `runtime/queue.py` enforce serialized public-value
  scanning and an atomic public-safe-only queue.
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
- `runtime/retention.py` keeps persistent raw disabled by default and can act
  only on validated, owned managed segments under retention policy/receipt v3.
  GIT current-tree pruning remains fail closed until the AU-040 writer is
  independently integrated.
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
  --verified-control-git-object-id sha1:66d5bafadca508cad825b4ce49a42e81e8b66ef7 \
  --expected-control-interface-raw-sha256 86e4d625bdab87261a39c949883d410822e25e0222dbab6a333d171ce420c614 \
  --canonical-control-interface-path CodexSkills/governance/activation/control-interface.json \
  --control-mode DRAFT_NON_ACTIVE_CONTROL
```

This command is read-only. The current control explicitly reports
`auto_runtime_integration_complete=false`, so it returns a shadow preflight
proof while every state-writing orchestrator/notification/activation
entrypoint fails before state creation. Neither checkout self-reporting nor a
caller boolean/digest map can replace either tuple.

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
Control object `66d5bafa...`, raw SHA-256 `86e4d625...`, binds the same
candidate and consumer. The runtime-interface builder verifies all three
Git-object blobs independently.

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
  --verified-git-object-id sha1:5ee37d7499c62ec19381dac7eb95cb12743ad2d5 \
  --expected-bundle-digest 36f0c66dd54d36365700a13f614a8c9bfa9619fb7c532af77566a858175b835e \
  --canonical-manifest-path CodexSkills/governance/bundles/schema-bundle-manifest.v1.json \
  --mode CANDIDATE \
  --verified-control-git-object-id sha1:66d5bafadca508cad825b4ce49a42e81e8b66ef7 \
  --expected-control-interface-raw-sha256 86e4d625bdab87261a39c949883d410822e25e0222dbab6a333d171ce420c614 \
  --canonical-control-interface-path CodexSkills/governance/activation/control-interface.json \
  --control-mode DRAFT_NON_ACTIVE_CONTROL
```

The preflight first binds the authenticated profile to the private owner
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
retention receipt v3. No shard/manifest/index instance or runtime writer was
created; `repository_bound=false` and canonical publication remains false.

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

The exact final 31/5 candidate, V2 consumer, and current control now exist and
the Auto loader accepts that exact bundle. The next phase is
`MECHANISM_POST_AUTO_INTEGRATION_CONTROL_SYNC`: Mechanism must independently
read back this Auto object and issue a successor control binding the new
runtime-interface tuple. Until that successor sets
`auto_runtime_integration_complete=true`, runtime state writes and settlement
remain fail closed. Publisher v2, daily shard writer, `repository_bound`,
AU-040 completion, activation, and canonical publication remain false.

The schedule conflict remains unresolved. The external Gmail readiness gate
remains false until the Owner injects the repo-external state root and the
controlled preflight succeeds.
Never invoke the verifier during development; the Owner selects a fresh
verifier only after both planes finish.
