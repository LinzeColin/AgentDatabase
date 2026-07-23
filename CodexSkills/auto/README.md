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
- `tools/notification_transport_cli.py` is the only production notification
  entrypoint. It consumes the same external candidate/active trust tuple,
  resolves only the fixed repo-external paths below, verifies the authenticated
  Gmail profile matches the owner mapping, renders the locked MAJOR template
  from public-safe structured facts, and returns a public-safe receipt.
- `runtime/publication.py` permits only expected-head FF pushes followed by
  remote byte readback. Candidate runtime publication is impossible; the
  coordinated-activation path additionally requires a verified,
  content-addressed envelope plus provider `SENT` evidence.
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
the coordinated M0c envelope, write a production watermark, or update the
automation. A later coordinated M0c activation is required. Never invoke the
verifier during development; the Owner selects a fresh verifier only after
both planes finish.
