# Memory Atlas v1.2.1 S07-P1-T3 Codex Sync State Review

## Status

- Task: `S07-P1-T3`
- Acceptance: `ACC-MA-V121-S07-P1-T3`
- Result: `COMPLETE_LOCAL_ONLY`
- Task Pack progress: `48/149` (`32.21%`)
- Stage / phase progress: S07 `3/9`; S07-P1 `3/3`
- Next and only eligible Task: `S07-P2-T1`

## Scope

This Task adds the incremental cursor, cross-archive content-hash deduplication and
interrupted-run resume layer on top of the immutable S07-P1-T2 archive. It writes one
real incremental archive and canonical local state. It does not build derived data,
change model/formula/business-threshold semantics, fetch, push, deploy, create a
branch/PR, merge/rebase, clean project caches, or implement `S07-P2-T1`.

## Acceptance Evidence

| Requirement | Evidence | Result |
|---|---|---|
| Portable cursor | State keys sources by kind and relative path; absolute paths are never serialized | PASS |
| Cross-history content dedupe | `content_index` is keyed by source SHA-256 and bootstraps all 430 T2 objects | PASS |
| No duplicate on exact repeat | Static fixture returns `NO_CHANGES`, performs zero writes and preserves state bytes/archive/index/ledger | PASS |
| Alias-safe dedupe | Two paths with identical bytes produce one package object and restore both paths from the source manifest | PASS |
| Interrupted-run resume | Four persisted phases resume with the same archive ID and verify/reuse published outputs without overwrite | PASS |
| Source drift fails closed | Planned source mutation retains the journal and publishes no additional archive, index or ledger row | PASS |
| Published artifact integrity | Verifier binds manifest/schema, part inventory/types/hashes and exact README/restore helper bytes; tamper and symlink regressions fail closed | PASS |
| Append-only T2 compatibility | The immutable T2 registration manifest remains a byte prefix of the later raw ledger | PASS |
| Phase boundary | Output declares no derived build, commit/push or deploy; next Task is only `S07-P2-T1` | PASS |

The real run is `codex-incremental-20260715t180600z`. It observed 435 stable files and
3,972,466,441 source bytes while deferring two recent active sessions. Stable pre/post
inventory SHA-256 is
`9f8dd012ef39cc51d81e9cea8c36f8e183797345a8b42fde22469060949d46e5` and
`source_mutation=false`. Seven new paths produced seven unique content objects. The
16,157,223-byte package has nine members in one part and SHA-256
`5b516b8ef34fab4e04a96e7f7ad70c13a5ad99f0407328bce5de0790c2831c8d`; archive
manifest SHA-256 is
`d745adab38261d8c09195e80c86327aeb3da90fa8bf752ea3cbd1afaca57f024`.

Canonical state is revision 6 with cursor sequence 2, 435 paths, 437 historical content
hashes, two deferred sources and `active_run=null`. The immediate second real run found
zero new path/content and produced no archive; it updated only deferred cursor metadata.
The static fixture separately proves an exact stable repeat leaves state bytes unchanged.

## Validation

- Dedicated sync-state tests: `10/10` PASS.
- Focused source/archive/sync-state tests: `33/33` PASS; governance/privacy focused:
  `54/54` PASS.
- Real T3 sync-state audit: PASS with state revision 6, 437 content hashes, archive
  mutation false and raw-manifest prefix verified. T2 archive compatibility: PASS.
  Raw append-only audit: PASS with 514 raw files / 514 ledger rows and drift,
  deletion and unledgered counts all zero.
- Full Python: `485/485` PASS after all remediations.
- `validate:fast`: `6/6` PASS; `validate:sync`: `9/9` PASS; `validate:ui`:
  `14/14` PASS. Each reports zero critical skips, `raw_mutation=false` and
  `remote_push=false`.
- Pre-commit `validate:release`: `1/1` PASS in 910.926 seconds. All 17 final-audit
  gates and 58/58 requirement reconciliation pass with `raw_mutation=false` and
  `remote_push=false`. Exact committed-tree recovery is rerun after the one local
  Task commit and is not preclaimed by this pre-commit review.

## Independent Engineering And Security Review

The implementation is reviewed against process concurrency, state durability, source
immutability, archive overwrite, credential exposure and recovery boundaries. The
post-remediation review currently finds 0 Critical, 0 Important and 0 Minor. In
particular, state publication uses a temporary file, atomic replace and parent-directory
fsync; a process-scoped advisory lock serializes runs; every published archive/index is
verified before reuse; and source drift keeps the active journal for explicit recovery.

The T2 verifier was intentionally widened only from exact-ledger equality to a verified
byte-prefix rule. It still executes current raw-ledger preflight, so historical evidence
cannot authorize deletion, mutation or insertion before the T2 boundary. T3 privacy
metadata permits numeric redaction counters only for the two validated Codex archive
manifest schemas; string secret material remains blocked.

Two integration findings were found by the public profiles and closed. First,
`validate:sync` imported the new test from the database working directory and exposed a
repo-root-only fixture import; the test now imports through its own directory and passes
from both entry points. Second, the final audit retained a 180-second credential-scan
budget while the same canonical 514-file scan measured 273.482 seconds. The audit still
runs the complete scan, now with the already-audited 600-second budget, and a regression
pins that lower bound. The failed first release was not counted as acceptance; the fixed
rerun is the `1/1` result above.

The final manual security pass found one additional Important issue: the T3 archive
verifier checked package/object hashes but did not bind the published `restore.sh` and
`README.md` bytes or reject a symlinked parts directory/part. The verifier now enforces
the exact manifest/source-manifest schemas, split and part inventories, regular-file
types, object/path mappings and generated helper bytes. A regression proves restore
tamper and a symlinked part fail closed. The real archive passes the hardened verifier;
the final review is therefore 0 Critical, 0 Important and 0 Minor.

## Independent Product And Scope Review

The product/scope pass finds 0 Critical, 0 Important and 0 Minor. The user-visible value
of this Task is operational: repeat synchronization no longer republishes unchanged
content, interrupted publication can resume without duplicate raw objects, and the next
derived-data Task has one canonical provenance state. It advances exactly one Task and
does not claim that Atlas-derived data or the website has changed.

## Residual Boundaries And Rollback

- A changing deferred active session may update cursor metadata without creating an
  archive; only a byte-identical stable inventory qualifies for zero-write `NO_CHANGES`.
- Recovery requires the same archive ID. Operators must not delete `active_run` or copy
  published pieces manually to bypass a failed verification.
- State is rebuildable from immutable raw, but archive/public index/raw ledger evidence
  is append-only. Rollback uses a corrective commit for code/config and must retain raw.
- Local `main` remains divergent from the locally known remote state. Remote access and
  upload remain prohibited until all 149 Tasks plus final review/remediation complete.
