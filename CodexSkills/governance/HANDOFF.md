# Mechanism handoff

- State: DRAFT_NON_ACTIVE
- Phase: MECHANISM_M0B
- Task Pack authority: immutable CodexSkills-Mechanism-Design-TaskPack-v0.0.0.2
- Protocol: urn:linzecolin:agentdatabase:skillops:protocol:cross-pack:v1
- SRV candidate: v0.0.0.3
- Candidate manifest: CodexSkills/governance/bundles/schema-bundle-manifest.v1.json
- Candidate bundle digest: fd1df66e240695bd376803423bd09f9f341f7542f74a6ed92b0f79b0af4dc5e1

## Pinned inputs

- Auto A1a verified Git object:
  sha1:7ebf23576cace9dcaeec598fb6b376840e89b4b5
- Auto interface raw SHA-256:
  7e3b87e1a468be73ce15daced6bf85f776a2ebf96fb02fa50774206e3b60b718
- Mechanism interface raw SHA-256:
  0f4837d9cec37c845cd5e9e799b5f572944cf8fe2457e8b95f696db3b9c03998

## Completed in M0b

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

## Explicitly not active

M0b does not create CodexSkills/VERSION, an ACTIVE manifest, canonical data, a
public receipt, a runtime watermark, or publication authority. The manifest
is trusted only when a caller supplies the repo-external tuple of verified M0b
Git object, the exact candidate digest above, the canonical manifest path, and
mode CANDIDATE. Missing external state fails closed.

## Next exact action

Auto A1b must start from the verified M0b main commit and consume the exact
candidate digest and protocol. It may implement candidate-only integration but
must not publish canonical data or claim ACTIVE. Mechanism M0c activation
remains a later independent controlled run.
