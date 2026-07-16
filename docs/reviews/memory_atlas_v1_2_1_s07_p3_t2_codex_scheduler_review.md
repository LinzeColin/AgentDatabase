# Memory Atlas v1.2.1 S07-P3-T2 Codex Scheduler Review

## Scope

- Task: `S07-P3-T2`
- Acceptance: `ACC-MA-V121-S07-P3-T2`
- Output: `Codex scheduler profile`
- Task Pack SHA-256: `db59f4db3ac02845fb3cde346a301cba64146c81c7ba19168f52c27e82ddd0f1`
- Implementation commit: `7e4dc636605ad5fae150c50e7c70b6551e63f0f1`

This run implements only the portable Codex scheduler profile and its guarded
owner-run state machine. It does not install or enable launchd, cron or another
OS scheduler, execute a production sync/push, or implement the S07-P3-T3 empty
directory restore proof. No GitHub fetch/push, deploy, branch, PR, merge, rebase,
force operation or general cleanup occurred.

## Profile And Parameters

The registered `codex-scheduler` profile defaults to:

- `Australia/Sydney` owner timezone;
- a 900-second observation cadence;
- a 300-second quiet window;
- a 1,800-second maximum pending window;
- a 3,600-second minimum interval after a successful run;
- at most one `S07-P3-T1` invocation and one ordinary push attempt per owner run.

The coalescing formula is:

`source changed AND ((same metadata observations >= 2 AND quiet >= 300s) OR pending >= 1800s) AND success interval >= 3600s`.

Metadata churn resets the quiet window but preserves the first pending time, so
the 30-minute maximum is a real max-wait rather than a dead parameter. T1 still
owns source-before/after stability, validation, Git and remote-race gates.

## State And Invocation Safety

Runtime state is machine-local and outside both the Git worktree and every
configured Codex source. The default macOS location is under
`~/Library/Application Support/Memory Atlas/scheduler/codex`; an explicit
absolute location may be supplied for an authorized runner. Relative paths,
direct symlinks, repository/source containment and unsafe state permissions fail
closed before a source or repository write.

State contains only source metadata digest/counts, timestamps, bounded owner-run
ids and child effect flags. It stores no source content or absolute paths. State
files are mode `0600`, written by fsync plus atomic replace; the enclosing
directory and nonblocking lock are private. The active owner-run id is persisted
before T1 is invoked. Duplicate, concurrent, clock-regressed, incomplete or
Git-effect-uncertain runs cannot automatically invoke T1 again.

The T1 child result must match the exact S07-P3-T1 schema and consistent
`NO_CHANGES`, `PUSHED_MAIN` or fail-closed semantics. Fetch, force, branch, PR,
merge and rebase flags are forbidden. A malformed or effectful failure requires
manual intervention; dry-run performs discovery and T1 preflight but writes no
state and makes no push attempt.

## Regression Evidence

- Test-first regressions reproduced missing dry-run evidence, ignored
  scheduler-only Owner Daily arguments, false child PASS semantics, ineffective
  max-wait and relative-source write ordering before each correction.
- Dedicated scheduler suite: `20/20 PASS`, covering profile/model drift,
  coalescing, continuous churn, throttle, no-change and pushed child outcomes,
  duplicate owner runs, nonblocking lock, private atomic state, clock/path
  rejection, incomplete/effectful attempts, finalize uncertainty and CLI
  isolation.
- Related scheduler/registry/modular-CLI/validator suite: `56/56 PASS` before the
  final hardening; governance and script inventory suite: `36/36 PASS`; final
  source/validator/governance focused suite: `44/44 PASS`.
- Canonical dirty-tree CLI smoke correctly returned
  `push_main_dry_run_not_ready` with child reason `initial_worktree_not_clean`,
  zero state, zero sync invocation and zero push attempt.
- Canonical broad sync units ran `207` tests; only the unrelated untracked
  `data/public_raw/.DS_Store` caused the two public-layout assertions. The
  canonical fast profile was independently blocked only by the pre-existing
  tracked raw deletions. Those external changes remained untouched and unstaged.

## Exact-Tree Acceptance

A task-owned `--shared` sparse clone checked out local `main` at
`HEAD=origin/main=7e4dc6366`, installed `154` packages from the lockfile and
passed:

- scheduler CLI dry-run: `DRY_RUN_READY`; decision `COALESCING`; child T1
  `DRY_RUN_READY`; zero state, sync invocation, push attempt or scheduler install;
- `validate:fast`: `6/6 PASS` in `34.694s`;
- `validate:sync`: `10/10 PASS` in `180.380s`, including `207` sync tests,
  append-only raw audit and the complete `134.160s` credential scan;
- GitHub Actions raw-isolated sparse audit: PASS with no raw content read, raw
  mutation or remote push.
- Final closeout regression: `93/93 PASS`; human-plane, test-value, script
  migration, staged push-size and complete privacy scans passed. Python 3.13 and
  3.12 deterministic renders both reported zero drift/reference issues, and all
  `47` governance event rows parsed as JSONL.

The clone remained clean and was deleted with its task-owned state/output paths.
Its origin was the local canonical repository, not GitHub; this evidence is not
represented as a real remote upload.

## Boundary And Result

`S07-P3-T2` is complete local-only at `53/149`; S07 is `8/9` and P3 is `2/3`.
`S07-P3-T3` is the next and only eligible Task. Scheduler installation/enabling,
production sync/push and full restore proof remain unimplemented and unclaimed.

Rollback is a precise `git revert` of the T2 local commits or disabling the
profile before any later authorized installation. Never delete raw, scheduler
state or uncertain Git evidence to simulate rollback.
