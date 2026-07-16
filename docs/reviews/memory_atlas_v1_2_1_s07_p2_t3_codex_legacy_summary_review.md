# Memory Atlas v1.2.1 S07-P2-T3 Codex Legacy Summary Review

## Status

- Task: `S07-P2-T3`
- Acceptance: `ACC-MA-V121-S07-P2-T3`
- Delivery: complete local-only; exact implementation commit and release acceptance passed
- Implementation commit: `c226e4d13e39dea5f8025de47689be435d97fd7f`
- Task Pack progress: `51/149`; S07 is `6/9` and S07-P2 is `3/3` complete.
- This run does not enter `S07-P3-T1`, fetch, push, deploy, create a branch/PR, or clean general caches.

## Scope

This Task preserves the six historical Codex summary surfaces and their legacy
schema versions while adding explicit, additive truth metadata. A legacy
snapshot, daily row, session manifest row, recommendation bundle, or behavior
report is a redacted derived summary. It is not a full raw backup and cannot by
itself restore Codex source data.

The separate canonical source of truth remains the verified recoverable
sanitized Codex archives and their T1 derived state. The real migration binds
that truth as two archives and 432 canonical sessions without changing raw,
public raw, the raw ledger, or the original Codex incremental sync state.

## Acceptance Evidence

| Criterion | Evidence | Candidate result |
|---|---|---|
| Legacy consumers continue to read existing schemas and fields | Six legacy files retain `codex_session_manifest.v1`, `codex_activity_snapshot.v1`, and `codex_agent_recommendations.v1`; regression fixtures retain unknown existing fields | PASS |
| Summary and raw-backup semantics are unambiguous | `summary_semantics` fixes `artifact_role=redacted_derived_summary`, `output_policy=derived_summary_not_full_raw_backup`, `full_raw_backup=false`, and `recoverable_raw_backup=false` | PASS |
| Canonical truth is independently bound | Migration verifies the T1 behavior-summary hash/state and records two archives plus 432 canonical sessions | PASS |
| Current consumers expose the same truth | Memory Atlas source contract/publication and Agent Context JSON/Markdown expose the compatibility boundary | PASS |
| Migration is safe and repeatable | Atomic multi-file replace, parent/target safety, process lock, rollback regression, immediate `NO_CHANGES` replay | PASS |
| Raw and remote boundaries remain closed | Protected raw/public-raw/manifest tree digest and original sync-state/ledger hashes are unchanged; result reports `raw_mutation=false`, `remote_push=false` | PASS |

## Real Migration

- Legacy sessions: 128
- Legacy activity days: 7
- Current recommendations: 7
- Canonical recoverable archives: 2
- Canonical sessions: 432
- Changed paths on first apply: 11 derived, consumer, and T3 state paths
- Immediate T3 dry-run replay: `NO_CHANGES`, `changed_paths=[]`, zero writes
- Immediate T2 publisher dry-run replay: `NO_CHANGES`, 432 events/facets, zero writes
- Agent Context canonical rebuild comparison: JSON and Markdown both byte-identical

The protected combined raw/public-raw/raw-manifest digest remained
`3916cf9752d8398b1f4482564efc58d10d61ec274c68809366b2020d525e3053`.
`data/sync_state/codex.json` remained
`b072fbd85ae8054401a38fd19777d81fd1fe2250c22246264da2baf755c765dc`,
and the raw ledger remained
`6603507dbb6702b1a773e0fdb30445d8f4e9f3b99f5d5aa484ae9f279ce88134`.

## Validation

- Dedicated compatibility migration: 6/6 PASS.
- Codex, source registry, Atlas, Agent Context, CLI and sync focused suite: 91/91 PASS.
- Acceptance, human-plane inventory, test-value and script-consolidation suite: 43/43 PASS.
- Latest combined T3/governance suite: 50/50 PASS.
- Post-closeout T3/acceptance/human-plane/test-value/script-consolidation suite:
  49/49 PASS. Python 3.13 and 3.12 deterministic `check-render` both report
  zero drift and zero reference issues; all 45 event rows parse as the required
  JSONL schema; the real T3 dry-run remains `NO_CHANGES` with zero writes.
- Broad `lean_governance validate --project OpenAIDatabase` remains nonzero on
  pre-existing cross-project/root baselines: 62 sync diagnostics under KMFA/root
  and 35 root/registered-path diagnostics. None names a T3 file or new evidence
  reference, and this Task does not modify or claim to resolve those scopes.
- The first full-suite invocation from the database subdirectory was invalid and
  is not counted: 502 tests ran with 10 historical absolute-package import
  errors caused by the wrong current working directory.
- The canonical repository-root invocation ran 512 tests. 508 passed; four raw
  layout/isolation checks failed only because external working-tree changes
  created ignored `.DS_Store` files and deleted the tracked ChatGPT archive
  directory during the run. Those unrelated changes are not restored, deleted,
  staged, or included in this Task.
- A tracked-path exact-commit projection then ran both complete public-raw layout
  and raw-isolation modules: 18/18 PASS. It materialized all 570 exact raw path
  names without reading raw content and confirmed that the four prior failures
  were caused only by the external main-worktree state.

## Exact Commit Closeout

Tracked-only recovery of `c226e4d13e39dea5f8025de47689be435d97fd7f`
passed with 1,700 tracked files, both original source packages, 514 current raw
files and 514 ledger entries, 432 canonical events/facets, a fresh `npm ci` and
production build, and exact Pages parity against snapshot SHA-256
`9788facd01bb2177035868068fec9324ca6e676839e4463c2f704a53ffbafa3d`.
The recovery workspace and npm cache were removed by the auditor.

The first full exact-tree release correctly failed closed for two acceptance
topology/runtime reasons: the detached worktree made the staged push-size test
report `branch_is_not_main`, and Chromium close exceeded 10 seconds once after
all three Home viewports had passed. The exact failure was reproduced as 511/512
unit tests with only the detached-branch test failing. The Home gate then passed
standalone across 1470x661, 1440x900 and 390x844, including server shutdown.

The final isolated shared clone used a local `main` with
`HEAD=origin/main=c226e4d13`, no canonical or remote branch creation, and no
network operation. The previously failing push-size test passed 1/1. Complete
`validate:release` then passed `final_audit` 1/1 in 928.103 seconds with
`failed_count=0`, `skipped_critical_count=0`, `commands_audited=true`,
`raw_mutation=false`, `remote_push=false`, and `shell=false`. All task-owned
worktrees, clones, recovery directories, browser artifacts and logs were removed.

## Risk And Rollback

The compatibility layer fails closed on a positive full/raw-recoverability
claim, unsafe or missing inputs, stale canonical hashes, stale Atlas publication,
unsafe output paths, lock contention, or transactional write failure.

Before a local commit, reverse only the T3 code/config/derived/governance patch.
After a local commit, use a corrective commit. Never delete or rewrite canonical
raw archives, public indexes, raw manifests, the raw ledger, or the original
Codex incremental sync state as rollback.

## Stop Boundary

`S07-P3-T1` remains unimplemented and is only eligible in the next run.
`S07-P2-T3` closes local-only at 51/149; no remote upload is allowed before all
149 Tasks and the final review/remediation close.
