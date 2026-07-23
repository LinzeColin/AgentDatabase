# Auto A1b + Gmail transport corrective handoff

- State: `DRAFT_NON_ACTIVE`
- Phase: `AUTO_A1B_GMAIL_TRANSPORT_CORRECTIVE`
- Protocol: `urn:linzecolin:agentdatabase:skillops:protocol:cross-pack:v1`
- Verified M0b Git object:
  `sha1:4b1e1a318c8f9e1014839a8a3a46e057679c4b6b`
- Exact candidate bundle digest:
  `fd1df66e240695bd376803423bd09f9f341f7542f74a6ed92b0f79b0af4dc5e1`
- Candidate manifest:
  `CodexSkills/governance/bundles/schema-bundle-manifest.v1.json`
- A1a schema interface remains immutable:
  `CodexSkills/auto/draft-interface.json`
- A1b machine interface:
  `CodexSkills/auto/runtime-interface.json`

## Completed in A1b

- Shared validation consumes only the caller-supplied external trust tuple and
  verifies the exact 29-schema/5-policy Git object before composing the four
  Auto-private schemas.
- Startup checks Python/dependency ranges, vendored canonicalizer bytes,
  canonicalization smoke vectors, and offline Registry closure before any
  queue, watermark, lock, or other state write.
- Repo-external owner-only state, atomic fsync+rename, single-flight leases,
  explicit stale recovery, protected-root guards, and lane-local verified
  watermarks are implemented.
- Source inventory is lstat-first, excludes only frozen policy material,
  accounts exclusions, never silently skips oversized/errors/special files,
  permits only safe same-root relative aliases, and binds the policy digest
  into the tree domain.
- Public serialization is reparsed, exact-schema validated, and privacy
  rescanned before the atomic public-safe queue. Raw persistence remains
  disabled by default.
- Planned MAJOR notification uses a transactional private outbox, external
  recipient mapping, provider reconciliation, and public-safe receipts. No
  production notification was sent in A1b.
- The corrective adds a concrete Gmail API transport and executable CLI. Its
  repo-external path refs are
  `state-root/private/notification/recipient-mapping.v1.json` and
  `state-root/private/notification/gmail-api.v1.json`; no actual recipient,
  credential, provider ID, body, or absolute path is stored in Git.
- Only an unambiguous provider `NOT_FOUND` permits send. `UNKNOWN`, `FAILED`,
  multiple matches, missing OAuth scopes, authenticated-recipient mismatch,
  or header/readback mismatch block without sending. A deterministic RFC822
  Message-ID and private payload-digest header permit post-crash lookup;
  provider readback is required before public `SENT`.
- `FakeNotificationTransport` remains test-only and is explicitly not a
  production capability. The implementation contains no launchd/local
  scheduler, daemon, background retry loop, or runtime package installation.
- Physical publication enforces exact shared gates, expected remote head,
  fresh worktree, allowed path set, ordinary FF push, and remote byte readback.
  Candidate runtime publication is blocked. Coordinated activation additionally
  requires a verified envelope digest/artifact digest set and provider `SENT`.
- UTC retention, Sydney 04:15/DST, Sunday forced full, manual parity, no late
  window, lock-busy defer, and lane-isolation behaviors have deterministic
  fake-clock/fault tests.

## Explicitly not done

A1b and the corrective did not create `CodexSkills/VERSION`, activate the
candidate, publish canonical data, send a real notification, create a
production state root,
scan/migrate the real Skill sources, rebuild the 3,365 Registry views, modify
OpenAIDatabase, update or run an automation, backfill historical runs, or call
the verifier.

## Next exact action

After this corrective is FF-safe pushed and remotely read back, Mechanism M0c
must produce the content-addressed activation envelope. Auto may invoke the
production entrypoint only for that exact envelope and may transport the
activation only after Gmail `SENT` plus exact provider readback and all shared
gates pass. After activation remote readback, Auto A1c may bootstrap the exact
ACTIVE tuple. Registry A2 and consumer/automation A3 remain later independent
CONTROLLED_RUN phases.
