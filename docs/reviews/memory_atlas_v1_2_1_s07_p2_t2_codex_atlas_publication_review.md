# Memory Atlas v1.2.1 S07-P2-T2 Codex Atlas Publication Review

## Status

- Task: `S07-P2-T2`
- Acceptance: `ACC-MA-V121-S07-P2-T2`
- Result: `COMPLETE_LOCAL_ONLY`
- Task Pack progress: `50/149` (`33.56%`)
- Stage / phase progress: S07 `5/9`; S07-P2 `2/3`
- Next and only eligible Task after closeout: `S07-P2-T3`

## Scope

This Task publishes the canonical S07-P2-T1 events and facets into the Memory
Atlas snapshot, weekly report and an independent Codex Atlas publication state.
It exposes source/session/evidence provenance in Search 2.0 and Inspector, and
keeps the same node selected across search, starfield and Memory River actions.
It does not migrate legacy Codex summary semantics reserved for `S07-P2-T3`,
read live Codex source files, mutate raw/archive/ledger data, push or deploy.

## Published Result

The real publication consumed exactly 432 canonical events and 432 facets. The
snapshot contains 717 memory nodes, 756 total nodes, 4,106 edges and 379
conversation/activity records. Its size is 3,327,670 bytes and SHA-256 is
`1e826049d89be4195740e276fe99a89e58d849b1f793f9ab724ebd6f4352bd92`.
The 2026-07-13 weekly report is 14,582 bytes and its SHA-256 is
`b9007b66b6c2bde7201be3a05e1c592516ed3953e318fcea7c6c3dbe217ef2e6`.

The newest published event is
`codex_session_92f328412ed73c231096`, from session
`019f6688-1b1e-72f3-8dee-6352e2e7dd6f`, updated at
`2026-07-15T16:07:29.848000Z` and labeled
`Codex session 归档备份删除`. It has two verified archive evidence references.
An immediate exact replay returned `NO_CHANGES`, `changed_paths=[]` and
`writes_files=false`.

## Acceptance Evidence

| Requirement | Evidence | Result |
|---|---|---|
| Canonical identity | Every published Codex node uses `event_id` as its unique identity while retaining `session_id` as source record identity | PASS |
| Atomic publication | Snapshot, weekly report and publication state use a process lock, safe path checks, temporary files, atomic replace, parent fsync and rollback | PASS |
| State truth | State binds exact contract/model, T1 input hashes, output hashes/counts and dynamic publication truth | PASS |
| Exact repeat | Immediate real replay validates current outputs and performs zero writes | PASS |
| User discovery | Exact Search 2.0 query returns the newest session first, displays archive evidence and preserves the node through starfield, river and Inspector actions | PASS |
| Responsive visualization | Memory River retains risk/cooling exemplars after Codex growth; Obsidian local graph waits for a real edge and local/hub label | PASS |
| Phase boundary | Raw, public raw, raw manifest, ledger, original Codex sync state and six legacy T3 consumer outputs remain unchanged | PASS |

The browser evidence used the exact newest-session query and expected node ID.
The first result and evidence reference matched, all three navigation actions
preserved the node, the screenshot was 473,740 bytes, and there were no
actionable console or network errors. The screenshot was visually inspected for
overlap.

## Validation And Remediation

- Dedicated publication tests: `9/9` PASS.
- Focused Codex/registry/CLI/runtime/consolidation suite: `131/131` PASS.
- Full Python suite: `505/505` PASS in 262.126 seconds after the fail-closed
  acceptance/inventory remediation below; the failed first candidate is retained
  as diagnostic evidence and is not counted as acceptance.
- `validate:fast`: `6/6` PASS in 33.333 seconds; `validate:sync`: `10/10`
  PASS in 207.566 seconds;
  final `validate:ui`: `14/14` PASS.
- Frontend lint and production build: PASS.
- Python 3.13/3.12 deterministic governance has zero drift/reference issue;
  privacy, built-dist raw isolation, exact raw/legacy diff and real publication
  `NO_CHANGES` pass.
- Full pre-commit `validate:release` passed `1/1` in 1,018.082 seconds with
  `failed_count=0`, `skipped_critical_count=0`, `raw_mutation=false` and
  `remote_push=false`.
- Implementation commit `02564125e47cfa35cfd68845ac1c5f0f30085205` was
  created locally. Its first exact-tree release ran 1,104.548 seconds and failed
  closed at `tracked_only_recovery`; downstream reconciliation was therefore
  `55/58`. Raw mutation and remote push remained false.
- The corrected recovery gate passes `23/23` focused tests and independently
  recovers that same commit: 1,694 tracked files, two source packages, 514/514
  current raw-ledger entries, the immutable release, 432/432 canonical
  publication, fresh frontend build and current snapshot Pages parity all pass.
- The corrective full Python suite passes `506/506` in 286.449 seconds.
- Corrective `validate:release` passes `final_audit` `1/1` in 1,268.493 seconds
  with `failed_count=0`, `skipped_critical_count=0`, `raw_mutation=false` and
  `remote_push=false`; aggregate recovery and requirement reconciliation pass.
- Corrective local commit `f597a31f18d0e827c579cf0a564311b1d2d03d89`
  passed exact-tree `validate:release` `1/1` in 980.106 seconds with
  `failed_count=0`, `skipped_critical_count=0`, `raw_mutation=false` and
  `remote_push=false`. This closes the local-only Task gate.

The implementation review found and closed these candidate defects:

| Finding | Remediation | Status |
|---|---|---|
| Session IDs could collide as public identities and state/output fsync failures could leave ambiguous truth | Publish by `event_id`, bind state to current output truth, register replacements before fsync and transactionally restore on failure | CLOSED |
| New tests were absent from the value inventory | Register the retained suite and update deterministic inventory expectations | CLOSED |
| Machine field names leaked into direct UI semantics | Introduce descriptive local aliases and explicit Chinese labels without hiding provenance | CLOSED |
| The newest 260 events displaced Memory River risk/cooling exemplars | Preserve a bounded exemplar sample while keeping the visible window capped at 260 | CLOSED |
| Obsidian validation sampled progressive reveal before any edge existed | Wait for a real edge and local/hub label, with bounded diagnostics on failure | CLOSED |
| The old acceptance audit coupled the new Atlas session count to T3 legacy recommendations | When T2 state exists, run the canonical publisher in dry-run mode and require exact `NO_CHANGES`; retain the legacy recommendation contract as a separate gate | CLOSED |
| The new publication model file was absent from the protected machine-plane inventory | Register the exact 157-file / 31-active-config bytes and manifest, retaining strict drift rejection | CLOSED |
| Tracked-only recovery required the current derived snapshot to equal the older immutable release | Keep immutable release verification intact; allow a newer current snapshot only when the recovered canonical publisher dry-run returns exact `NO_CHANGES`, then build and compare Pages against that validated hash | CLOSED |

Current review finding count after remediation is
`0 Critical / 0 Important / 0 Minor`. This count covers the current candidate;
any final release failure reopens the Task.

## Rollback And Boundaries

- Before commit, reverse only this Task's code/config/UI/governance patch and
  restore the previous snapshot, weekly pointer and Codex Atlas state.
- After commit, use a corrective local commit; do not rewrite shared history.
- Never remove or rewrite canonical T1 derived files, raw/archive/public index,
  ledger, original `data/sync_state/codex.json` or T3 legacy consumers.
- No fetch, push, deploy, branch, PR, merge, rebase or general cache cleanup is
  permitted during staged delivery.
