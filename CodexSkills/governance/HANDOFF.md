# Mechanism handoff

- State: DRAFT_NON_ACTIVE
- Phase: MECHANISM_CONSUMER_FIRST
- Task Pack authority: immutable CodexSkills-Mechanism-Design-TaskPack-v0.0.0.2
- Protocol: urn:linzecolin:agentdatabase:skillops:protocol:cross-pack:v1
- SRV candidate: v0.0.0.3
- Candidate manifest: CodexSkills/governance/bundles/schema-bundle-manifest.v1.json
- Candidate bundle digest: 2704ed797c843f969965db600747abcdcd217550522e6479aab6817ef5a86ef5

## Pinned inputs

- Auto activation-handshake corrective verified Git object:
  sha1:ee6f046619cb7f5584c89e1dbb81d5bd5c602a2b
- Auto runtime interface raw SHA-256:
  cdd4c11e412045bd1ee36b6af7e9b1aa35a4f125681568955aa5796710414922
- Mechanism interface raw SHA-256:
  0f4837d9cec37c845cd5e9e799b5f572944cf8fe2457e8b95f696db3b9c03998
- M0c-A activation control interface raw SHA-256:
  24af49e7f3c0ecac85154a2a9741d9d8ceb16368224cbf7900eceac9fe66e0f7

## Completed through M0b

- The complete candidate contains exactly 21 Mechanism schemas, eight
  Auto-public schemas, and five Mechanism policies.
- All entries are ASCII-ID sorted, content-addressed with RFC 8785 canonical
  SHA-256, owned by one plane, bound to an exact path, and marked EXACT_ONLY.
- The four Auto-private schemas are excluded from the shared bundle.
- The manifest digest excludes only /bundle_digest. Member and policy digests
  remain covered by the manifest digest.
- The candidate uses exact protocol and bundle-digest compatibility with no
  accepted predecessor bundle.
- The deterministic builder pins both machine-interface byte digests and
  refuses interface drift, ACTIVE VERSION state, member-count drift, path or
  owner mismatch, private-schema inclusion, digest mismatch, and malformed
  public values.
- Local draft loading structurally validates a candidate but returns only the
  21-schema Mechanism draft. It never upgrades repository self-reporting into
  a trusted complete bundle.

## Completed in M0c-A

- A field-level audit proved the existing single-artifact envelope cannot bind
  the complete activation write set, and the existing publisher must not trust
  a caller-supplied verification boolean or digest map.
- `activation-intent:v1` freezes the full planned path set before notification,
  including the exact VERSION bytes and explicit post-provider-derived paths.
- `activation-settlement:v1` is created only after a real `PRE_WRITE` provider
  `SENT` receipt. It binds the exact intent and receipt evidence plus every
  final artifact's physical SHA-256.
- The settlement is a distinguished control artifact and cannot list its own
  physical digest. The final publisher must require request paths equal the
  settlement artifact set plus the settlement path and recompute every byte.
- The Mechanism Handoff may reference the settlement path but cannot embed the
  settlement digest, preventing a handoff/settlement digest cycle.
- Both bootstrap-control schemas are versioned and digest-pinned outside the
  unchanged 29-schema/5-policy candidate bundle. The complete machine interface
  is `CodexSkills/governance/activation/control-interface.json`.
- That control interface and its two schemas gain runtime trust only through an
  external tuple of verified M0c-A Git object, expected raw interface SHA-256,
  canonical interface path, and mode `DRAFT_NON_ACTIVE_CONTROL`; repository
  self-reporting is insufficient.
- The validator loads the 29 schemas and five policies only from the externally
  pinned candidate Git object and trust tuple; a later working-tree change
  cannot silently replace activation semantics.
- Public JSON intent, notification receipt, and settlement bytes are RFC 8785
  JCS UTF-8 with no BOM or trailing newline. Reads traverse descriptor-relative
  `O_NOFOLLOW` gates and reject symlink roots, parents, and files.
- Notification metadata exposes only the conservative public scopes
  `CodexSkills/VERSION` and `CodexSkills/governance`; the intent digest binds
  the exact five-path write set without leaking high-entropy receipt paths.
- Positive, negative, privacy, path, ordering, provider-state, evidence-binding,
  physical-digest, and cycle fixtures are executable offline.

## Completed in consumer-first

- The sibling task-run validator now enumerates only the four legacy task-run
  categories. It cannot glob or reinterpret recursive SkillOps shards as
  `task_run` rows.
- `OpenAIDatabase/config/evaluation/skill_run_consumer.json` pins the exact
  candidate Git object, bundle digest, manifest path, protocol, schema ID,
  Australia/Sydney shard calendar, RFC 8785 per-line framing, gapless
  `part-NNNN.jsonl` layout, and 20 MiB part budget. Its raw SHA-256 is
  `94a5186aeaad6947eec19ef67539e3f03c0db06d47292d58088fdc4ee8bb53c6`.
- Consumer bootstrap rejects duplicate keys, invalid I-JSON, untrusted bundle
  IDs, unknown URNs, unsafe roots, symlink/special-file entries, invalid
  dates, direct-root event files, unexpected directories, and every
  unapproved path. Descriptor-relative `O_NOFOLLOW` reads close the config and
  log-tree path race; fixed entry/error budgets bound hostile tree scans.
- `tools/validate_public_run_event.py` applies schema, contextual bundle
  equality, self-digest, public-value scanning, binding surface/role,
  controlled-invocation time/surface, correction, and token-measurement
  semantics without importing Auto runtime code or modifying M0c-A-pinned
  validator bytes.
- The canonical repository run root still contains only its README. Synthetic
  final-layout records can be validated, but repository shards remain
  unconditionally blocked.
- OpenAIDatabase lifecycle, minimum validation, harness, README, and regression
  tests now identify `skills_runs` as a separate consumer surface.

## Explicitly not active / current capability state

M0c-A does not create `CodexSkills/VERSION`, an ACTIVE manifest, activation
intent instance, notification receipt, settlement instance, canonical data,
runtime watermark, or publication authority. It sends no email. The candidate
manifest remains byte-identical and is trusted only when a caller supplies the
repo-external tuple of verified M0b Git object, exact candidate digest,
canonical manifest path, and mode CANDIDATE.

The production Gmail implementation now exists, but readiness of the
repo-external state root, recipient mapping, and OAuth credential is `UNKNOWN`
in this Mechanism run because `SKILLOPS_STATE_ROOT` is not provisioned in the
runtime environment. A connected Gmail App is not a substitute for that
production trust root. Missing external state fails closed.

This phase does not claim AU-040. The shared v0.0.0.3 candidate has individual
`public-run-event:v2` records and a transaction-level
`publication-manifest:v1`, but no proven daily JSONL shard/manifest payload
contract. BOUND events also remain blocked from canonical publication until
the Registry-backed exact reference resolver lands.

## Next exact action

A separate read-only capability gate must prove the owner-held state root,
recipient mapping, Gmail OAuth scopes, authenticated-recipient binding, and
provider lookup/readback are ready. If any fact remains absent, the only next
action is owner provisioning; no intent instance or email may be fabricated.

Only after that gate is READY may an independent M0c-B run create the intent,
obtain a real provider `SENT` receipt, settle, FF-safe publish, remotely read
back, and establish the external ACTIVE trust tuple. AU-040 and the BOUND
reference resolver remain later blockers for canonical run-log publication
even after v0.0.0.3 activation.
