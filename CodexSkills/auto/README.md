# SkillOps Auto contracts and runtime safety kernel

State: `DRAFT_NON_ACTIVE`.

This Auto-owned directory contains eight public schemas, four Auto-private
schemas, deterministic builders/validators, and the non-active runtime safety
kernel. The public set belongs to the exact Mechanism M0b shared candidate;
the private set never enters the shared bundle.

Deterministic contract entrypoints:

```bash
/usr/bin/python3 -B CodexSkills/auto/tools/build_schemas.py --check
/usr/bin/python3 -B CodexSkills/auto/tools/build_runtime_interface.py --check
/usr/bin/python3 -B CodexSkills/auto/tools/validate_auto.py lint-draft
/usr/bin/python3 -B -m unittest discover \
  -s CodexSkills/auto/tests -p 'test_*.py'
```

All entrypoints use the repository-pinned canonicalizer and offline validator
from `CodexSkills/governance/tools/`. They do not implement JCS independently,
resolve schemas over the network, or install dependencies at runtime.

## Runtime entrypoints

- `tools/runtime_preflight.py` consumes the repo-external trust tuple and runs
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
  an owner-held OAuth credential, searches `in:sent` by deterministic RFC822
  Message-ID, verifies the exact private payload-digest header, sends only
  after an unambiguous `NOT_FOUND`, and reads the provider message back before
  returning `SENT`. Provider timeouts, ambiguity, header mismatch, or missing
  scopes block the planned write without sending again.
- `runtime/activation.py` consumes both the external candidate trust tuple and
  the external M0c-A control tuple. It verifies the local Mechanism activation
  runtime against the selected Git object before loading the exact 31-schema /
  five-policy offline closure. Intent, receipt, and settlement reads are
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
  preflight/non-activation entrypoint. It consumes the same external
  candidate/active trust tuple,
  resolves only the fixed repo-external paths below, verifies the authenticated
  Gmail profile matches the owner mapping, renders the locked MAJOR template
  from public-safe structured facts, and returns a public-safe receipt. It
  rejects `planned_action=ACTIVATE`; activation cannot bypass the verified
  intent entrypoint.
- `runtime/publication.py` permits only expected-head FF pushes followed by
  remote byte readback. Candidate runtime publication is impossible. The
  coordinated-activation path no longer accepts caller booleans, caller digest
  maps, caller `SENT` strings, or caller shared-gate status maps; it derives
  those facts from the externally trusted settlement, exact bytes, live lock,
  path gates, policy/privacy validation, and remote head.
- `runtime/retention.py` keeps persistent raw disabled by default and can act
  only on validated, owned managed segments. UTC wall-clock and active-tree
  retention claims are explicit.
- `runtime/schedule.py` freezes Australia/Sydney 04:15, Sunday forced full,
  DST-safe UTC conversion, manual parity, and no late-start rejection.

Run the exact candidate preflight from the repository root with the explicitly
provisioned interpreter:

```bash
/usr/bin/python3 -B CodexSkills/auto/tools/runtime_preflight.py \
  --repo-root . \
  --verified-git-object-id sha1:4b1e1a318c8f9e1014839a8a3a46e057679c4b6b \
  --expected-bundle-digest fd1df66e240695bd376803423bd09f9f341f7542f74a6ed92b0f79b0af4dc5e1 \
  --canonical-manifest-path CodexSkills/governance/bundles/schema-bundle-manifest.v1.json \
  --mode CANDIDATE
```

This command is read-only. It does not accept the checkout's manifest or
VERSION as a self-declared trust root, install packages, access a network
resolver, create state, publish, notify, or update an automation.

## M0c activation control

The activation control interface remains `DRAFT_NON_ACTIVE` at
`CodexSkills/governance/activation/control-interface.json`. Runtime use
requires all four external values: the verified M0c-A Git object, expected raw
interface SHA-256, canonical interface path, and
`DRAFT_NON_ACTIVE_CONTROL` mode. Repository self-reporting is never sufficient.

The two-stage production CLI is intentionally not demonstrated with a live
instance here. A later independent run must first land the Mechanism-owned
consumer-first change, then separately prove the repo-external state root,
recipient mapping, Gmail OAuth scopes, authenticated recipient binding, and
provider readback readiness. Only a later M0c-B run may create an intent, send
the notification, create a settlement, or invoke `publish-settlement`.

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
/usr/bin/python3 -B CodexSkills/auto/tools/notification_transport_cli.py \
  preflight \
  --repo-root . \
  --state-root "$SKILLOPS_STATE_ROOT" \
  --verified-git-object-id sha1:4b1e1a318c8f9e1014839a8a3a46e057679c4b6b \
  --expected-bundle-digest fd1df66e240695bd376803423bd09f9f341f7542f74a6ed92b0f79b0af4dc5e1 \
  --canonical-manifest-path CodexSkills/governance/bundles/schema-bundle-manifest.v1.json \
  --mode CANDIDATE
```

There is no launchd job, local daemon, background retry loop, or runtime
package installation. The Codex automation invokes the entrypoint directly;
manual and scheduled runs use the same path.

`DRAFT_NON_ACTIVE` code must not create or update `CodexSkills/VERSION`, claim
ACTIVE state, publish canonical data, send a production notification without
the coordinated M0c intent, write a production watermark, or update the
automation. The Mechanism-owned consumer-first gate is not complete. AU-040 is
also not complete: `skills_runs/example.json` is only prior scaffolding, never
the final run-layout contract. The immutable Task Pack requires bounded daily
JSONL shards and a manifest under
`OpenAIDatabase/data/run_logs/skills_runs/YYYY/MM/DD/part-NNNN.jsonl`.
Never invoke the verifier during development; the Owner selects a fresh
verifier only after both planes finish.
