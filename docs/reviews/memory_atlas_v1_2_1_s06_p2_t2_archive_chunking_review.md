# Memory Atlas v1.2.1 S06-P2-T2 Archive Chunking Review

## Scope

- Task: `S06-P2-T2`
- Acceptance: `ACC-MA-V121-S06-P2-T2`
- Original TaskPack filename: `v1.2.1_四线16Stage质量收敛升级_TaskPack.zip`
- Original TaskPack SHA-256: `db59f4db3ac02845fb3cde346a301cba64146c81c7ba19168f52c27e82ddd0f1`
- Completed here: strict 45 MiB contract, deterministic fixed-byte splitting, ordered bytes/SHA-256 manifest, no-overwrite/idempotent publication, source-stat protection, fail-closed lock handling, and truthful partial-publication errors.
- Explicitly excluded: restore/verify (`S06-P2-T3`), migration or rewriting of legacy archives, real source/public-raw/ledger mutation, push, deploy, branch, PR, rebase, and cache cleanup.

## Requirement Trace

- TaskPack `02_Roadmap_16Stage_Phase_Task.md` requires packages above the threshold to use deterministic 45 MiB parts and a manifest recording order, bytes, and SHA-256.
- Task acceptance requires every new part to remain below the GitHub 50 MiB warning line and forbids ordinary Git blobs above 100 MiB.
- TaskPack `07_自动同步Raw公开与Main直推规范.md` repeats the 45 MiB ordinary-Git rule, requires per-part SHA-256/bytes/order, and keeps Git LFS disabled by default.
- The Stage validation calls for a fixture-based 45 MiB chunk and restore round trip. This Task closes only the chunk/manifest half; restore remains the next Task.

## Contract And Implementation

- `config/data_sources/archive_chunking.json` is the strict canonical contract and is referenced by `source_registry.json`.
- `archive_chunking.py` reads the source under a device/inode/mode/size/mtime/ctime guard, hashes in 1 MiB blocks, emits zero-padded six-digit names, and writes the deterministic manifest last.
- Publication traverses the archive root with `dir_fd`, `O_NOFOLLOW`, and directory file descriptors. The final archive directory is reserved with exclusive `mkdir`; no `lexists` plus rename overwrite window remains.
- Every part and the manifest use exclusive creation and `fsync`. Existing archives are verified byte-for-byte and hash-for-hash without rewrite before an idempotent replay can pass.
- Failure cleanup is limited to the still-open directory inode reserved by the current run and rejects unknown names, symlinks, non-regular parts, or changed directory identity. A replaced output or lock is preserved and reported for manual verification.
- Parent-directory durability failure after manifest publication is distinct from an incomplete-reservation failure. The CLI reports these states conservatively and never claims a remote push.

## Real Inventory Boundary

- `data/public_raw` contains zero files above 45 MiB; no newly registered source package currently requires a production archive in this Task.
- The OpenAIDatabase tracked inventory has 37 files above 45 MiB and zero at or above 100 MiB. All 37 are immutable pre-v1.2.1 90 MiB archive/session-history parts; the maximum is 94,371,840 bytes.
- The original v1.2.1 TaskPack is 94,595 bytes and does not require splitting.
- Reassembling or migrating the old 90 MiB archives would require the `S06-P2-T3` restore/verify path. This Task therefore does not manufacture a new production archive or rewrite historical evidence.

## Acceptance Evidence

- Fourteen dedicated tests write and hash real fixture bytes across the 45 MiB boundary. They prove deterministic manifests/parts, exact-threshold no-op, idempotent replay, conflict preservation, source-stat failure, symlink rejection, exclusive locking, directory/part identity-gated cleanup, and CLI post-publication truthfulness.
- Ninety-seven related archive, source-registry, raw-ledger, public-layout, credential, manifest, integrity, and test-governance tests pass; 51 focused validator/profile governance tests also pass.
- Python compilation and `git diff --check` pass.
- The script migration hash for the changed test-value audit is synchronized; 17 consolidation/audit regressions pass.
- The real public-raw ledger remains byte-identical at 128,209 bytes, inode `156668907`, mtime `1783818229.381278488`, and SHA-256 `1a4fa71303903ca896c82640f7b4550cee47f3cc8ec600f81d03f7603e120c96`.
- No `data/public_raw` file, ledger row, archive part, source package, restore artifact, or remote state changed. Only the archive control README changed under `data/raw_archives`.
- The canonical full Python suite passes 398/398; `validate:sync` passes 7/7, `validate:fast` passes 4/4, and `validate:ui` passes 14/14 with zero critical skips, raw mutation, or remote push.
- Python 3.13 and 3.12 deterministic governance render both report drift 0 and reference issue 0.
- Final independent engineering/security and product/scope reviews both report Critical 0, Important 0, and Minor 0 after the directory, part-file, and lock replacement findings were remediated.

## Risk And Recovery

- A stale, replaced, unreadable, or identity-drifted lock/output fails closed and requires manual verification; automatic removal is forbidden when ownership cannot be proven.
- Output without `manifest.json` is incomplete and invalid. A valid chunk archive is not recovery-ready until `S06-P2-T3` restores and verifies the original package hash.
- Roll back only this Task diff or use `git revert` on its local commit. Existing archives, public raw, ledger, source packages, and unrelated worktree changes are outside rollback scope.

## Decision

`S06-P2-T2` satisfies its local Task acceptance contract. The phase remains in progress; the next and only eligible Task is `S06-P2-T3`, and it did not start in this run.
