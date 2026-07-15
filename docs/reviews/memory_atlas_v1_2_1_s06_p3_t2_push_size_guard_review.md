# Memory Atlas v1.2.1 S06-P3-T2 Push Size Guard Review

## Scope

- Task: `S06-P3-T2`
- Acceptance: `ACC-MA-V121-S06-P3-T2`
- Original TaskPack: `v1.2.1_四线16Stage质量收敛升级_TaskPack.zip`
- TaskPack SHA-256: `db59f4db3ac02845fb3cde346a301cba64146c81c7ba19168f52c27e82ddd0f1`
- Completed here: staged Git object size guard, deterministic recovery-unit planning, pending whole-commit batch planning, remote checkpoint validation and resumable recomputation.
- Excluded: real fetch/push, force/LFS/history rewrite, direct-main executor or scheduler, remote reconciliation, and `S06-P3-T3` full raw contract fixtures.

## Requirement Trace

- TaskPack `02_Roadmap_16Stage_Phase_Task.md` requires a normal single push target below 1.5 GiB and ordered batching instead of force after an over-limit failure.
- TaskPack `07_自动同步Raw公开与Main直推规范.md` requires 45 MiB deterministic parts, split before a normal Git blob exceeds 50 MiB, a hard stop at 100 MiB, no default LFS, and complete recoverable batches.
- The S06 validation matrix requires a staged blob/push-size preflight. Direct-main execution remains separately gated by clean main, fresh fetch, remote-race stop, validation, credential, restore and post-push equality checks.

## Estimation And Limits

- `config/data_sources/push_size_guard.json` is the canonical T2 contract.
- The estimate sums each unique Git object's uncompressed size once, then adds 8 MiB per batch and 256 bytes per object for protocol/framing reserve. This is intentionally conservative relative to normal pack compression and delta reuse.
- A staged blob strictly above 50 MiB is `split_required`; an ordinary blob at or above 100 MiB is a hard stop. Every planned batch must be strictly below 1,610,612,736 bytes.
- The same 50/100 MiB checks apply to pending unique blobs. A violation in existing local history produces no push batches and requires a reviewed recommit; it is never hidden inside an otherwise sub-1.5-GiB batch.
- The audit obtains staged object IDs from the index and sizes from `git cat-file`; it does not open staged worktree files. Pending objects come from `origin/main..HEAD` reachability and are deduplicated by object ID.
- All guard Git reads use `--no-replace-objects`, `GIT_NO_LAZY_FETCH=1` and disabled terminal prompts. Local replacement refs cannot alter evidence, and a partial clone with a missing object fails closed instead of contacting a promisor remote.

## Batching And Resume

- Staged paths are grouped deterministically. A raw archive source/archive directory is one atomic recovery unit; public-raw sources remain together; ordinary paths are individual units. An atomic unit at or above the target fails rather than being split blindly.
- A staged plan may validly report multiple batches, but `github_backup --apply` requires `single_commit_ready=true`; it stops before creating one oversized, later-unsplittable commit.
- Pending history uses oldest-first first-parent commits that are valid fast-forward boundaries from the checkpoint. Side-branch objects enter at their merge boundary, so every intermediate batch tip contains all prior batches; batching never targets an unrelated topo-order sibling.
- Each pending batch contains a non-force argv targeting `<tip>:main`. The tool never executes it.
- Resume state is Git-native: fetch, confirm the expected `origin/main` OID, push one reviewed batch in the later authorized executor, fetch again, and recompute. A changed checkpoint, behind/diverged history, non-main branch, missing object or oversized whole commit fails closed.

## Local Backup Integration

- Existing staged changes are rejected before backup staging, preventing unrelated user work from entering the local backup commit. Backup targets are lexically repository-local and every target path component must be non-symlink.
- Main/contract preflight runs before index mutation. After explicit backup targets are staged, the complete staged report runs again.
- A failing size/blob guard or a multi-batch plan stops the commit. The latter truthfully reports that the index changed through explicit staging so an owner can preserve and split the exact candidate.
- The index tree OID is recorded before and after the guard. Any change fails; otherwise `commit-tree` binds the exact audited tree and `update-ref <new> <old>` advances `refs/heads/main` with an old-HEAD CAS. Every backup Git invocation overrides `core.hooksPath=/dev/null`, so neither commit nor reference-transaction hooks execute, and a concurrent later index change cannot enter the audited commit.
- Any exception after staging reports `writes_files=true`, actual `index_changed` and current staged paths. If the ref CAS already succeeded, a later inspection error reports `committed=true` with commit/tree/parent OIDs rather than inviting a duplicate commit. No remote command, lazy fetch, merge, rebase, LFS or force behavior was added to `github_backup.py`.

## Validation So Far

- Dedicated push-size and local-backup tests: 28/28 PASS.
- Full Python suite: 443/443 PASS.
- Public profiles: fast 6/6, sync 7/7, UI 14/14 and release 1/1 PASS. The release final audit includes the repository privacy gate and reports `raw_mutation=false` and `remote_push=false`.
- Static compilation and `git diff --check`: PASS.
- Canonical governance render is deterministic under Python 3.13 and 3.12 with zero drift or reference issues.
- The exact product-reviewed staged candidate audit passed in one batch with `single_commit_ready=true`, no blob violation and no body/index/remote write. The final governance-only record update is re-audited before commit.
- Current pending audit: expected FAIL_CLOSED because local `main` and the locally known `origin/main` have diverged. No fetch or reconciliation was attempted; this is a real final-delivery blocker, not an implementation-test failure.
- The governance-only final record candidate was re-staged and re-audited as one `single_commit_ready` batch after all suites, deterministic checks and independent reviews completed.

## Independent Review

- Initial engineering/security review found 0 Critical, 4 Important and 1 Minor. The first rerun closed four original findings and found one reference-transaction-hook Important plus one truthful post-commit-state Minor. After regression-backed remediation, the third and final engineering/security review closed at 0 Critical, 0 Important and 0 Minor.
- Product/scope review closed at 0 Critical, 0 Important and one non-blocking documentation-freshness Minor. This final record update removes the stale future-tense wording identified by that Minor; no code or scope finding remained.

## Risk And Recovery

- The estimate is a conservative policy upper bound, not a byte-for-byte prediction of a particular remote pack negotiation. The strict threshold and reserves intentionally trade some capacity for safety.
- A pending batch plan is not authorization to push. The later executor must fetch immediately before each batch and pass the returned checkpoint as the expected remote OID.
- In a partial clone, missing objects fail locally under `GIT_NO_LAZY_FETCH=1`; the audit never hydrates them from a promisor remote. Final delivery must explicitly fetch under its own later authorization before rerunning the plan.
- Existing commits cannot be split by the guard. An oversized commit must be reconstructed before any remote write; force and history rewriting remain forbidden without separate authorization.
- Before commit, roll back only the T2 patch. After local commit, use `git revert <S06-P3-T2 commit>`; do not delete raw or relax thresholds.

## Decision

Local S06-P3-T2 acceptance is complete: implementation, full validation, dual-runtime governance, exact staged-scope inspection and both independent reviews are closed. The next Task must remain `S06-P3-T3` and is not implemented here; remote history reconciliation and upload remain prohibited in this run.
