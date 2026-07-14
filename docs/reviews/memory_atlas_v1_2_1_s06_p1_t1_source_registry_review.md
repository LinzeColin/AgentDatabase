# Memory Atlas v1.2.1 S06-P1-T1 Review

- Scope: S06-P1-T1 only
- Result: PASS locally; 37/149 Tasks complete
- Stage result: S06 1/9 complete locally
- Next gate: S06-P1-T2, not started in this run

## Acceptance

`config/data_sources/source_registry.json` remains the only current executable
source registry. It now contains a versioned `sync_contract` and configuration
records for ChatGPT official export, Codex local data, a generic-agent template,
and the existing Codex reviewer source. Every sync record defines the TaskPack
fields for discovery, source-relative raw paths, credential-contract reference,
parser, schedule, state path, archive path, derived outputs and push policy.

The generic loader fails closed on missing fields, duplicate IDs, unsupported
source types, POSIX/Windows/UNC absolute paths, parent traversal, parser/type
mismatches, adapter-path drift and push-policy drift. `atlasctl sync` resolves
source type and parser entrypoint from the registry instead of hard-coding
source-specific script paths. Registered environment discovery fills only an
unset matching CLI argument, while an explicit operator argument retains priority.
The runtime also rechecks the final-delivery-only push policy before dispatch.

A new standard local generic-agent source can therefore reuse the generic adapter
by adding one registry record. Its registered `source_id` drives raw records and
derived summaries, and a concrete source cannot be redirected into another
namespace with `--agent-id`; the legacy/template command cannot claim a concrete
registered namespace, including through path-like values that normalize to the
same ID, case-only aliases on case-insensitive filesystems, leading/trailing
whitespace, or Windows reserved device basenames such as `con`, `nul`, `com1`
and `lpt1`. Source and agent IDs
must already be lowercase portable canonical values. Non-canonical sources are
generic-only, and reserved CLI aliases cannot become registry IDs. JSON/JSONL input requires at least one valid
event and rejects non-object JSONL rows with a line-numbered error before writes.
The existing `chatgpt`, `codex` and `future-agent` commands retain their prior
dry-run contracts.

The old `机器治理/同步与备份/sync_source_registry.json` remains historical material
but has no live script, test, application or configuration references. The active
raw archive policy now references the canonical registry. The historical file was
not deleted in this Task.

## Validation

| Check | Result |
|---|---|
| Source registry contract regressions | 14/14 PASS |
| Focused registry/CLI/profile/sync regressions | 103/103 PASS |
| `validate:sync` | 6/6 PASS in 34.842s; raw mutation false; remote push false |
| `validate:fast` | 4/4 PASS in 12.184s |
| Full Python suite from canonical package root | 346/346 PASS in 169.527s |
| Script migration hash governance | 12/12 PASS |

Two independent read-only reviews identified unsupported discovery
arguments, inert environment candidates, generic namespace drift, loose parser
binding, one stale active-policy reference, explicit/environment input conflicts,
missing JSONL behavior, canonical ID/type swaps, generic provenance spoofing,
template/concrete namespace collisions, empty or invalid JSONL acceptance,
non-canonical namespace conflicts, incomplete legacy-reference scanning and stale
validation claims. Path-like, trailing-delimiter, case-only, whitespace-padded and
Windows reserved device-name agent aliases were also closed. A stale owner-map sentence was explicitly relabeled as an S05-P1-T3
snapshot. The implementation and tests above remediate those findings without
widening into S06-P1-T2 or S06-P1-T3.

## Boundaries

This Task did not create or modify a public raw file, source-data file, sync-state file,
manifest, chunk, restore artifact or credential exclusion implementation. It did
not run an applied connector, push, deploy, create a branch/PR, merge/rebase or
clean caches. S06-P1-T2 still owns the shallow public raw layout, and S06-P1-T3
still owns the unified credential exclusion contract.
