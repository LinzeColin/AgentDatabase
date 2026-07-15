# Memory Atlas v1.2.1 S07-P1-T2 Codex Public Raw Archive Review

## Status

- Task: `S07-P1-T2`
- Acceptance: `ACC-MA-V121-S07-P1-T2`
- Result: `COMPLETE_LOCAL_ONLY`
- Task Pack progress: `47/149` (`31.54%`)
- Stage / phase progress: S07 `2/9`; S07-P1 `2/3`
- Next and only eligible Task: `S07-P1-T3`

## Scope

This Task converts the S07-P1-T1 eligible Codex sessions, logs and history into an
append-only, recoverable public package. It does not create a cursor, deduplicate by
content, resume an interrupted run, build derived data, fetch, push, deploy, create a
branch/PR, merge/rebase, or implement `S07-P1-T3`.

## Acceptance Evidence

| Requirement | Evidence | Result |
|---|---|---|
| Source hash/stat unchanged | 430 stable files have identical pre/post aggregate SHA-256 and six-field stat tuples | PASS |
| In-flight data is not falsely certified | 4 recent active sessions are deferred with `hash_stat_claim=false` | PASS |
| Recoverable public package | 432 regular members form one 558,731,407-byte tar.gz package in 12 ordered parts | PASS |
| Credential and local-path exclusion | Recursive JSONL/SQLite sanitization plus output safety checks; binary bodies become hash/size markers | PASS |
| Append-only publication | Explicit archive ID, exclusive lock, no overwrite, manifest last, public index and immutable ledger | PASS |
| Recovery is fail closed | Package hash, exact member count, uniqueness, `codex/` root and safe regular-member paths precede atomic output publication | PASS |
| Public registration is auditable | Archive audit requires the exact public index plus a byte-identical 513-row immutable raw manifest / ledger preflight | PASS |
| T3 remains unimplemented | Contract and output explicitly report no cursor, content dedupe, resume or derived build | PASS |

The real archive is `codex-public-raw-20260715t1300z`. Its stable source digest before
and after is `c1e284843c4d3171b49ac84bc682a564279f822a502a7d4e4a9fb768d30cd061`.
The package SHA-256 is
`e1406eea8b67ffdac96fb41f26f821696389b6eb5ed9ef069b1b42b186d1f174`; the manifest
SHA-256 is `6640cbdeed803df4c3090aaa2e51350d68210bf059bdcafe5ec65f40561cef81`.
The public index SHA-256 is
`d5f946b5ec04c3babe3f24babc624fd342ad8876b6f539a357bfed4cd434825a`.
The immutable 513-row raw manifest is byte-identical to the append-only ledger and
has SHA-256
`05ecc7c521214bd513b6ae6101b1c2ecd49c58dfcbf96fe2c2a0ad9c17c90478`.

## Validation

- Dedicated archive tests: `14/14` PASS.
- Focused archive, privacy, manifest and release-contract tests: `54/54` PASS.
- Real archive audit: PASS for all 12 parts, manifest, hardened restore helper, public index and raw ledger.
- Raw append-only audit: PASS with 513 raw files / 513 ledger rows and drift/deleted/new all zero.
- Deterministic owner renderer and human-plane audit: PASS with `47/149` and `S07-P1-T3` current.
- Full Python: `475/475` PASS; `validate:fast`: `6/6` PASS; `validate:sync`: `8/8` PASS;
  `validate:ui`: `14/14` PASS. Each passing profile reports zero critical skip,
  `raw_mutation=false` and `remote_push=false` where applicable.
- Exact-commit tracked-only recovery: PASS. The Git tar stream covered 1,665
  `OpenAIDatabase` tracked files while historical bulk paths were streamed without a
  second disk copy. Current Codex archive/public raw, source packages, release and
  frontend were materialized; 513 current raw files equal 513 ledger rows, the
  immutable 512-row release manifest remains a verified subset, fresh `npm ci` and
  production build pass, and Pages snapshot parity is exact.
- `validate:release`: `1/1` PASS on the exact commit. All 17
  final-audit gates and 58/58 requirement reconciliation pass with
  `raw_mutation=false` and `remote_push=false`.

## Independent Engineering And Security Review

The first pass found 0 Critical, 2 Important and 1 Minor. Important findings were that
the generated helper called `tar -xzf` without enforcing the contract's safe-member
rule, and the custom archive audit could pass after public-index or ledger loss. The
Minor was that quiescence retry rediscovered sources without reclassifying a newly
recent active session.

Remediation replaced direct extraction with validated staging plus atomic publication,
made the audit require exact public registration, and reapplied in-flight partitioning
on retry. Regression tests prove `../` members leave no partial output, index/ledger
loss fails closed, and a newly active session is deferred. A second pass found two
additional Minors: source-relative filenames were not explicitly safety-scanned and
manifest authorization/content/restore fields were under-validated. Both are now
validated. The post-remediation implementation review is 0 Critical, 0 Important and
0 Minor, subject to the final validation matrix below.

Post-commit recovery exposed two additional operational defects. Process-group
termination could raise `EPERM` and hide the extractor failure, and whole-tree
materialization exceeded the temporary disk budget. Recovery now falls back to direct
child termination when group signalling is denied, reads historical bulk paths through
the exact Git stream without duplicating them, and materializes every path needed for
current Codex archive/raw/release/build verification. It also distinguishes the
immutable 512-row release manifest from the append-only 513-row current ledger. The 22
recovery regressions and real exact-commit rehearsal pass after these fixes.

## Independent Product And Scope Review

The product pass found 0 Critical, 0 Important and 0 Minor. The output is a public,
recoverable point-in-time package for every stable S07-P1-T1 eligible file, not a
credential-inclusive byte clone. It retains ordinary transcript content, clearly marks
four deferred active sessions and advances owner/governance state by exactly one Task.

One residual boundary is explicit rather than hidden: active-session tails and SQLite
WAL sidecars are not certified as stable T1 sources, so this package is not continuous
sync or a guarantee of the newest runtime tail. Cursor, dedupe and interrupted-run
resume remain solely `S07-P1-T3`. This does not weaken T2's source hash/stat acceptance.

## Residual Boundaries And Rollback

- The real 3.8 GB logical source set is verified and package-hash recoverable; the
  full empty-directory rebuild rehearsal remains a later recovery/sync gate, while T2
  exercises actual fixture restore and real package/restore-helper verification.
- Public transcript content is intentionally recoverable; credential values, local
  absolute paths and binary bodies are not.
- The archive, public index and ledger are append-only. Rollback uses a corrective
  commit for code/config and must retain these immutable evidence files.
- Local `main` remains divergent from the locally known remote state. Remote access and
  upload remain prohibited until all 149 Tasks plus final review/remediation complete.
