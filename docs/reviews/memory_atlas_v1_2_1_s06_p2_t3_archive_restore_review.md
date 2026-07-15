# Memory Atlas v1.2.1 S06-P2-T3 Archive Restore Review

## Scope

- Task: `S06-P2-T3`
- Acceptance: `ACC-MA-V121-S06-P2-T3`
- Original TaskPack: `v1.2.1_四线16Stage质量收敛升级_TaskPack.zip`
- TaskPack SHA-256: `db59f4db3ac02845fb3cde346a301cba64146c81c7ba19168f52c27e82ddd0f1`
- Completed here: manifest-bound `verify` and `restore`, ordered per-part and whole-package verification, safe no-replace output publication, and read-only support for the two registered legacy manifest schemas.
- Excluded: archive migration or re-chunking, `S06-P3`, raw/ledger/source mutation, push, deploy, branch, PR, rebase, and cache cleanup.

## Requirement Trace

- TaskPack `02_Roadmap_16Stage_Phase_Task.md` requires restore/verify from parts with per-file/package validation and equality with the archive manifest.
- Stage validation requires a real `45 MiB chunk + restore round trip`.
- TaskPack `07_自动同步Raw公开与Main直推规范.md` requires each snapshot to carry a manifest, hashes, parts and restore instructions, and makes restore a direct-main precondition.
- Acceptance matrix S06 requires split, manifest, dedupe and restore tests to pass and stops when restore verification fails or a manifest is incomplete.

## Contract And Implementation

- `config/data_sources/archive_restore.json` is the canonical T3 contract. It fixes supported schemas, 1 MiB streaming reads, exact ordered inventory, per-part and package SHA-256/bytes, explicit output, no-overwrite publication, durability and the next-Task boundary.
- `raw_archive_manifest.py verify` performs a write-free streaming reconstruction. `restore` requires `--output` under an existing non-symlink parent outside the archive directory.
- Archive traversal and part reads use `dir_fd` and `O_NOFOLLOW`; source directories, control files, manifest, parts and already-read part identities are checked again before PASS.
- Restore writes an exclusive mode-0600 temporary inode, verifies all archive bytes while writing, fsyncs the output, publishes with hard-link no-replace, unlinks the temporary name and fsyncs the parent. Different existing content fails unchanged; byte-identical output is an idempotent replay.
- Cleanup removes only a temporary name still bound to the inode created by the current run. Partial and post-publish states are separate errors with conservative CLI fields.
- Legacy `restore_command` and `verify_command` strings are validated only as metadata text and are never executed.

## Real Recovery Evidence

- Canonical fixture: `45 MiB + 123 bytes`, two parts, exact source/restored bytes and SHA-256, idempotent replay, unchanged source and archive identities.
- ChatGPT legacy archive: 16/16 parts, 1,473,421,021 bytes, package SHA-256 `52f204dd8d78b76a79c6fc37e3e09987d3ab682c87098da017b894dd88c3a868`.
- Remote-branch Git bundle: 13/13 parts, 1,161,813,692 bytes, package SHA-256 `ec03e395898169ff1a625732bb1cb1582c5576e0f611c1be91d7ffad78f928e6`.
- The 35 historical archive files had the same bytes/inode/mtime metadata digest before and after both real verify commands: `f2def36b6456f3beae8d0f54fc8bba6c1119a97c36837400face9c78fd2db955`. Their Git diff was empty.
- No full historical package was materialized: real verification was streaming and write-free. Restore publication is proven by the canonical and legacy test fixtures.

## Validation

- Dedicated restore tests: 13/13 PASS, including published-output mutation and parent-fsync-plus-mutation truthfulness regressions added from independent review.
- T2/T3/source-registry combined tests: 41/41 PASS.
- Script migration/test-value/profile governance: 43/43 PASS.
- Full Python suite: 411/411 PASS in 243.033 seconds on the final candidate tree.
- `validate:fast`: 4/4 PASS.
- `validate:sync`: 7/7 PASS; complete credential scan 133.092 seconds.
- `validate:ui`: 14/14 PASS.
- `validate:release`: 1/1 PASS; final audit 915.893 seconds.
- Every profile reported audited commands, zero critical skips, `raw_mutation=false`, `remote_push=false`, and `shell=false`.

## Independent Review

- Engineering/security first pass found 0 Critical / 2 Important / 1 Minor: final output lacked a post-publication content recheck, an existing conflicting output was reported as absent, and the new-publication race lacked a regression. All three were fixed with final-path byte/SHA/identity verification, `ArchiveRestoreOutputConflictError`, truthful CLI fields and a same-inode mutation test.
- Engineering/security second pass found one new Minor in the parent-fsync failure race. The exception branch now immediately re-verifies output content and degrades a changed file to PartialWrite with `output_complete=false`; the combined fsync/mutation regression passes. Final engineering/security result: **0 Critical / 0 Important / 0 Minor**.
- Product/scope first pass found 0 Critical / 2 Important / 0 Minor. The implementation itself had no product defect; findings required excluding four unrelated KMFA user changes from the T3 commit and replacing this document's temporary "reviews running" state. Final staging is restricted to `OpenAIDatabase`; the reviewer independently confirmed no cached `KMFA/` or non-`OpenAIDatabase/` path and consistent review/roadmap/HANDOFF state. Final product/scope result: **0 Critical / 0 Important / 0 Minor**.

## Risk And Recovery

- Supported legacy schemas are intentionally limited to the two immutable manifests already registered in Git. Unknown schema versions fail closed.
- The tool proves byte-for-byte package recovery, not application-specific semantic validity such as ZIP extraction or `git bundle verify`; those historical command strings are not executed for security. Exact known package SHA-256 preserves the archived package identity.
- A partial/post-publish error requires manual inspection. Do not remove an unknown temporary path, overwrite an output, or rerun with shell-evaluated manifest commands.
- Before commit, roll back only the exact T3 patch. After the local commit, use `git revert <S06-P2-T3 commit>`; historical archives and unrelated KMFA worktree changes remain out of scope.

## Decision

Implementation and automated acceptance evidence satisfy the T3 contract. Engineering/security and product/scope are both final at 0/0/0. `S06-P2-T3` is accepted locally; the next and only eligible Task is `S06-P3-T1`.
