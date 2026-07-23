# Mechanism handoff

- State: DRAFT_NON_ACTIVE
- Phase: MECHANISM_M0C_A_ACTIVATION_PROTOCOL
- Task Pack authority: immutable CodexSkills-Mechanism-Design-TaskPack-v0.0.0.2
- Protocol: urn:linzecolin:agentdatabase:skillops:protocol:cross-pack:v1
- SRV candidate: v0.0.0.3
- Candidate manifest: CodexSkills/governance/bundles/schema-bundle-manifest.v1.json
- Candidate bundle digest: fd1df66e240695bd376803423bd09f9f341f7542f74a6ed92b0f79b0af4dc5e1

## Pinned inputs

- Auto Gmail transport corrective verified Git object:
  sha1:1836c44fe83bb911b0a5ca5d97b8e59ff2df84ab
- Auto runtime interface raw SHA-256:
  d38eae81ef4aa45ac119bcb3fefa3b67c3f9609ef2fe281bb7dcf5b68c60c838
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

## Next exact action

Auto must start from the verified M0c-A main commit, consume the exact
`activation/control-interface.json`, and implement a production activation
handshake/publisher that validates intent and settlement bytes, derives the
notification request from the intent, recomputes the final physical write set,
and removes caller-asserted envelope trust. It must not create VERSION or claim
ACTIVE.

After that corrective, a separate capability gate must prove the owner-held
state root, mapping, Gmail OAuth scopes, authenticated-recipient binding, and
provider lookup/readback are ready. Only then may a later independent M0c-B run
create the intent, obtain a real provider `SENT` receipt, settle, FF-safe
publish, remotely read back, and establish the external ACTIVE trust tuple.
