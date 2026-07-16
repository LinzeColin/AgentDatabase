# Memory Atlas v1.2.1 S07-P3-T1 Codex Push Main Review

## Scope

- Task: `S07-P3-T1`
- Acceptance: `ACC-MA-V121-S07-P3-T1`
- Output: `sync codex --push-main`
- Task Pack SHA-256: `db59f4db3ac02845fb3cde346a301cba64146c81c7ba19168f52c27e82ddd0f1`
- Implementation commits: `6d92fac69e0eadcb4fb3ef3378edd2ac258f163b`, `c9ad185475d0c2f48819d6b07c3eab981c9759fe`

This run implements only the Codex validate, commit and direct-main push command.
It does not implement the S07-P3-T2 scheduler/coalescing profile or the
S07-P3-T3 empty-directory restore proof. It performs no canonical GitHub push,
fetch, deploy, branch, PR, merge, rebase, force operation or general cleanup.

## Command Contract

`python3 -B scripts/atlasctl.py sync codex --push-main` now implies the existing
incremental raw, derived, Atlas and legacy-truth pipeline. An explicit
`--archive-id` remains available for deterministic retries; otherwise a UTC id
is generated. `--source codex` remains compatible with the prior CLI surface.

The command stops before source or Git writes unless all initial terms hold:

1. symbolic branch is exactly `main`;
2. the complete worktree and index are clean, including untracked files;
3. `HEAD`, `refs/remotes/origin/main` and a live `git ls-remote origin
   refs/heads/main` result are equal;
4. exactly one origin push URL exists;
5. the Codex source can be discovered under the existing credential-exclusion
   contract.

The write path is fixed as:

1. incremental Codex raw sync;
2. Codex derived build;
3. Atlas and weekly publication;
4. legacy summary truth migration;
5. exact Codex-output staging;
6. complete `sync` validator profile;
7. staged push-size gate;
8. one-parent CAS commit of the audited tree;
9. a second remote-race check;
10. at most one ordinary `git push origin <commit>:refs/heads/main`;
11. live remote HEAD verification.

There is no fetch, force, branch creation, PR, merge, rebase, history rewrite or
automatic push retry path. A rejected push preserves the one local commit and
returns `FAIL_CLOSED`; the command never guesses a conflict resolution.

## Scope And Safety Gates

Only Codex runtime outputs are eligible for staging:

- append-only `data/raw_archives/codex/**` and `data/public_raw/codex/**`;
- the append-only T3 raw manifest and raw ledger;
- Codex derived, processed, weekly, Atlas, Agent Context and sync-state outputs.

Any change outside this list, modification/deletion of an append-only path,
rename/copy/unmerged entry, symlink/submodule staged object, validation write,
source metadata drift, branch/HEAD/tracking change, remote race, secret scan
failure or multi-batch push-size result stops before push. The audited index tree
must remain byte-identical through validation and commit.

## Regression Evidence

- Dedicated isolated Git tests: `13/13 PASS` in `15.195s` on exact commit
  `c9ad18547`. They use task-owned temporary repositories and a local bare
  origin to prove one successful push and one injected rejection without any
  network remote write.
- Dedicated coverage includes exact positional/legacy CLI parsing, contract
  drift, main/dirty/stale-base rejection, source drift, hidden local commit,
  out-of-scope change, append-only modification, validation failure, push-size
  failure, validator side effect, remote race, idempotent no-change, dry-run,
  one ordinary push and rejection without retry.
- Related candidate regression: `133/133 PASS` across the new command, source
  registry, modular CLI, validator profiles, test-value audit, push-size guard,
  S04 Git backup and all S07 raw/derived/Atlas/legacy modules.
- Final focused governance/CLI regression before the implementation commit:
  `50/50 PASS`.
- Closeout command/governance regression: `86/86 PASS`. The first run exposed
  the expected machine-plane inventory increment from the new model parameter;
  the bounded inventory contract and audit hash were updated to the measured
  `159` files and `33` active configs. Human-plane audit then passed with no
  errors.
- Deterministic governance render passes under Python 3.13 and 3.12 with zero
  drift/reference issues; all `46` governance events parse as JSONL.
- Broad root `lean_governance validate --changed-only` remains fail-closed on
  `36` pre-existing sparse-root/registry diagnostics and checks no project;
  none names an S07-P3-T1 file. This Task does not modify or claim those
  cross-project/root baselines.
- Staged privacy scan: `PASS`, `0` high-risk secret hits, `0` credential-like
  path hits, `515` public-raw files scanned.
- Staged push-size audit: `PASS`, exactly `15` Task paths, `432,382` unique
  object bytes, one batch, no blob violation and `single_commit_ready=true`.

## Exact-Commit Validation

The first clean clone `validate:sync` correctly failed because dependencies were
not installed and Vite could not be resolved. After lockfile-driven `npm ci`
installed `154` packages, commit `6d92fac69` passed all `10/10` sync steps in
`234.950s` with no failed or skipped critical gate.

The first fast run then found one real governance drift: the modified test-value
audit script hash was stale in `atlasctl_script_migrations.json`. Corrective
commit `c9ad18547` changed only that reviewed SHA-256. A fresh clean local-main
clone of the corrective commit then passed:

- `validate:fast`: `6/6 PASS` in `29.431s`;
- `validate:sync`: `10/10 PASS` in `188.949s`;
- exact command dry-run: `DRY_RUN_READY`, `main`, clean worktree,
  `HEAD=origin/main=c9ad18547`, live remote probe equal, `176` eligible Codex
  files and zero writes/push attempts;
- final clone status: clean `main...origin/main`.

Both profiles report `commands_audited=true`, `raw_mutation=false`,
`remote_push=false` and `shell=false`. The canonical dirty worktree smoke also
correctly returned `initial_worktree_not_clean`, zero writes and zero push
attempts before any remote probe.

## Boundary And Result

The local-bare-origin tests prove the executable direct-main behavior without
violating the owner instruction to defer the one real GitHub upload until all
149 Tasks and final remediation close. They are not represented as a production
GitHub push. Current canonical external `.codex`, KMFA, raw/session-history
deletions and `.DS_Store` changes remain untouched and unstaged.

`S07-P3-T1` is complete local-only at `52/149`. `S07-P3-T2` is the next and only
eligible Task. Scheduler coalescing and the full restore rehearsal remain
unimplemented and unclaimed.
