# Memory Atlas v1.2.1 S06-P2-T1 Raw Ledger Review

## Scope

- Task: `S06-P2-T1`
- Acceptance: `ACC-MA-V121-S06-P2-T1`
- Completed here: source stat before/after guards, SHA-256 content hashes, append-only ledger, exclusive append lock, idempotent deduplication, and ChatGPT/Codex/generic-agent adapter integration.
- Explicitly excluded: deterministic 45 MiB splitting (`S06-P2-T2`), restore/verify (`S06-P2-T3`), push, deploy, branch, PR, cache cleanup, and any real raw/source mutation.

## Contract And Implementation

- `config/data_sources/raw_ledger.json` is the strict canonical contract and is referenced by the source registry.
- Source guards compare device, inode, mode, size, mtime_ns and ctime_ns; file-set sources also require an unchanged directory inventory and reject symlinks.
- `raw_ledger.py` hashes in 1 MiB blocks, validates exact five-field legacy-compatible rows, derives immutable dedupe keys, and appends only under an exclusive fail-closed lock with `fsync`.
- `raw_archive_manifest.py` rejects changed/deleted historical rows and unledgered pre-existing raw before adapter writes. Existing ledger bytes are never replaced.
- If raw output may have been appended before ledger registration fails, adapters report that partial append-only state truthfully and stop before processed/derived outputs.

## Acceptance Evidence

- Focused implementation, adapter, manifest, integrity and governance suites pass.
- Real ledger audit: 512 ledger rows and 512 raw files; source stat verified 512; drift 0; deleted 0; unledgered 0.
- Ledger identity before and after the real audit is identical: 128,209 bytes, inode `156668907`, mtime_ns `1783818229381278488`, SHA-256 `1a4fa71303903ca896c82640f7b4550cee47f3cc8ec600f81d03f7603e120c96`.
- Public raw audit: 512 files / 452,781,632 bytes, with credential, nonportable path, invalid JSON, invalid binary marker and oversize counts all zero.
- Privacy scan: 513 tracked raw/control files, 35 large files, no skipped large file, no credential-like path or high-risk secret hit.
- The complete privacy scan measured 356.46 seconds in isolation, so its unchanged critical command now has a 600-second validator budget instead of an insufficient 300-second budget; no scan scope or assertion was relaxed.
- `validate:sync`: 7/7 PASS; critical skips 0; `raw_mutation=false`; `remote_push=false`.
- Validator/profile governance tests: 35/35 PASS; `validate:fast`: 4/4 PASS; `validate:ui`: 14/14 PASS; complete Python suite: 384/384 PASS.
- Command workflow browser fixture now includes the same raw-ledger evidence directory as the full installed source workspace; all six local commands pass and hosted-static command POST remains zero.
- Python 3.13 and 3.12 deterministic governance render both report drift 0 and reference issue 0.
- Independent engineering/security and product/scope reviews both closed at Critical 0, Important 0 and Minor 0 after remediation. The final full suite also exposed and closed four legacy fixture gaps by installing the target-database raw-ledger contract in three Codex sync cases and the release-audit positive case.

## Risk And Recovery

- Concurrent or stale lock state fails closed; an operator must verify process and ledger identity before removing a stale lock.
- A post-raw ledger failure can leave only append-only raw additions. Re-run after resolving the ledger error; do not rewrite ledger bytes or delete historical raw to force success.
- Roll back only this Task diff or use `git revert` on its local commit. Existing raw, ledger and unrelated worktree changes are out of rollback scope.

## Decision

`S06-P2-T1` satisfies its local acceptance contract. The phase remains in progress; the next and only eligible Task is `S06-P2-T2`.
