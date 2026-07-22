# Auto A1a handoff

- State: `DRAFT_NON_ACTIVE`
- Phase: `AUTO_A1A`
- Protocol: `urn:linzecolin:agentdatabase:skillops:protocol:cross-pack:v1`
- Base Mechanism main: `sha1:37d07a47ae87fcf246046d1611d3e00f000d1fa4`
- Public schema owner: `CodexSkills/auto/schemas/public/`
- Private schema owner: `CodexSkills/auto/schemas/private/`
- Machine interface: `CodexSkills/auto/draft-interface.json`
- Machine interface raw SHA-256: `7e3b87e1a468be73ce15daced6bf85f776a2ebf96fb02fa50774206e3b60b718`

## A1a boundary

A1a materializes schemas and tests only. It does not implement adapters,
queues, locks, publishers, notification transports, retention execution, Git
transactions, canonical data, or the production automation prompt.

The public set contains exactly eight schema IDs and self-digest pointers
frozen by Mechanism. The private set contains exactly four operational schema
IDs and is explicitly excluded from the shared bundle. No `VERSION`, bundle
manifest, canonical artifact, or watermark is created in A1a.

The public contract keeps actual recipients repo-external, rejects
unapproved digest fields after serialization, separates notification timing
from provider outcome, permits independent lane settlement behind shared
gates, and restricts queued/published artifacts to the shared schema set and
approved canonical write roots. `MANUAL` and `SCHEDULED` use the same artifact
contract; there is no late-start window. The consumed version policy remains
Australia/Sydney daily 04:15 with Sunday forced full.

## Validation

- Mechanism draft: byte-equivalent; 21-schema offline closure; 15 tests pass.
- Auto draft: byte-equivalent; 29 shared + 4 private schema closure; 14 tests pass.
- Both immutable v0.0.0.2 Task Packs: all checksums, package validators, and
  cross-pack validator pass. Newer frozen Revision 5.2 decisions take
  precedence over conflicting baseline examples.
- Production-only privacy scan, staged-path boundary, and `git diff --check`
  pass. No actual recipient, absolute local path, cache, active manifest, or
  `CodexSkills/VERSION` is present.

## Next exact action

After this phase is on verified main, Mechanism M0b consumes both ownership
sets and materializes the complete non-active candidate manifest/digest. Auto
A1b must target that exact candidate and must not publish canonical data.
