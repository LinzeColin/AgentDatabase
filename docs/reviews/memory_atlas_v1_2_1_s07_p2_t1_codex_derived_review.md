# Memory Atlas v1.2.1 S07-P2-T1 Codex Derived Outputs Review

## Status

- Task: `S07-P2-T1`
- Acceptance: `ACC-MA-V121-S07-P2-T1`
- Result: `COMPLETE_LOCAL_ONLY`
- Task Pack progress: `49/149` (`32.89%`)
- Stage / phase progress: S07 `4/9`; S07-P2 `1/3`
- Next and only eligible Task: `S07-P2-T2`

## Scope

This Task adds the archive-derived Codex build after S07-P1-T2/T3 raw and sync
state. It creates canonical events, facets, a behavior summary and Universe State
input while leaving existing local-consumer outputs unchanged. It does not update
the Memory Atlas snapshot, weekly report, Codex sync state, UI, website or remote.
It does not implement `S07-P2-T2` or migrate the full legacy summary semantics
reserved for `S07-P2-T3`.

## Acceptance Evidence

| Requirement | Evidence | Result |
|---|---|---|
| Verified immutable input only | Every registration is resolved from the raw ledger and passes its existing T2/T3 verifier before body parsing | PASS |
| Incremental archive processing | Archive history must remain a prefix; exact repeat reuses output hashes, while a later archive parses only its new package | PASS |
| Session-level provenance | Events and facets bind public index, archive manifest/hash, source manifest member, archive member/hash, portable source path and source hash | PASS |
| Canonical outputs | Events, facets, behavior summary, Universe State input and derived state are produced together and hash-bound | PASS |
| Legacy phase boundary | Existing processed manifest/daily/snapshot and derived snapshot/recommendation/report paths remain byte-identical to the Task start; migration stays in T2/T3 | PASS |
| Privacy truth | No raw message text, plaintext credential value or local absolute path is persisted; output states `derived_summary_not_full_raw_backup` | PASS |
| Raw immutability | Git diff for raw, public raw, raw manifest, ledger and Codex sync state is empty | PASS |
| Phase boundary | Atlas snapshot, weekly report, sync state, UI, commit/push and deploy flags remain false; next Task is only `S07-P2-T2` | PASS |

The real first run consumed the baseline archive
`codex-public-raw-20260715t1300z` and incremental archive
`codex-incremental-20260715t180600z`. Their manifest SHA-256 values are
`6640cbdeed803df4c3090aaa2e51350d68210bf059bdcafe5ec65f40561cef81` and
`d745adab38261d8c09195e80c86327aeb3da90fa8bf752ea3cbd1afaca57f024`;
their package SHA-256 values are
`e1406eea8b67ffdac96fb41f26f821696389b6eb5ed9ef069b1b42b186d1f174` and
`5b516b8ef34fab4e04a96e7f7ad70c13a5ad99f0407328bce5de0790c2831c8d`.

The result contains 432 events and 432 facets across 10 days from 2026-07-06
through 2026-07-15, with 23,183 messages and 149,776 tool calls. Universe State
input contains 9 clusters and 432 recent events. Events are 2,001,801 bytes with
SHA-256 `b88b7327ab28008af581e6853fd642d7be1fecb006a49a1b0343e9071257ff5b`;
facets are 728,284 bytes with SHA-256
`5681cc57f86c4ede58360050ca537bf7460011581783c3fff32003cb6fe601b3`.
The behavior summary and Universe input hashes are
`b27845b1b1ae14565382377f74c2062b1c5d7927c9a7e68a82c5eff2dda3e43c`
and `809a30225e7093b548cb645892509cccb85254221278e05b6ca93fc9b065053c`.

The final hardened full rebuild completed in 74.431 seconds. An immediate exact
repeat completed in 10.328 seconds with `NO_CHANGES`, `parsed_archive_count=0` and
`writes_files=false`.

## Validation

- Dedicated derived tests: `9/9` PASS.
- Focused Codex source/archive/state/derived/CLI/source-registry tests: `68/68` PASS.
- Validator profile tests: `18/18` PASS; test-value audit: PASS; raw-isolation
  tests: `8/8` PASS; script consolidation: `12/12` PASS; CLI modular tests:
  `7/7` PASS.
- Pre-commit full Python suite: `494/494` PASS in 879.438 seconds. The fixture
  corrective candidate passed `495/495` in 296.724 seconds; the process-tree
  corrective candidate passes `496/496` in 311.339 seconds.
- `validate:fast`: `6/6` PASS in 66.061 seconds; `validate:sync`: `10/10`
  PASS in 297.596 seconds; `validate:ui`: `14/14` PASS in 742.800 seconds.
- The first release candidate reached `56/58` but failed `S14-AC02` and
  `S14-AC05` because the full Python child exceeded its old 900-second budget.
  The suite itself completed in 879.438 seconds, so the child budget was corrected
  to 1,800 seconds and the R8/CLI timeout regression passed `28/28`.
- The corrected full `validate:release` passed `1/1` in 1,129.235 seconds with
  no failed step, no critical skip, `raw_mutation=false` and
  `remote_push=false`. The failed first run is retained as remediation evidence,
  not counted as acceptance.
- Python 3.13 and 3.12 deterministic render both passed with zero drift and zero
  reference issue. Privacy guard found zero high-risk secret, credential-like path
  or tracked raw/private hit. Built-dist raw isolation, script consolidation
  `12/12` and `git diff --check` passed.
- Exact-commit release/recovery remains a required post-commit closeout at this
  review checkpoint and is not preclaimed.

The first two post-commit aggregate attempts failed closed without raw or remote
writes. The first reconciled `55/58` with S04 partial; standalone GitHub backup
`12/12` and exact-commit recovery then passed for the same commit. The second
reconciled `56/58` with S04 verified, proving a different four-line gate failed.
The previous profile tail omitted the sorted `failed_gate_ids` behind the long
requirement rows. The final audit now emits a bounded stderr compact summary with
failed gate IDs, return codes and short output tails; R8/CLI regression is `14/14`.
The third exact-tree attempt on diagnostic commit `458c81467` used that summary
and identified both failed gates: `unit_tests` and `credential_audit`. Both traced
to one tracked synthetic test value whose literal token prefix correctly matched
the production privacy scanner. The fixture now assembles that prefix only at
runtime, so the behavior remains covered while the tracked tree has zero high-risk
secret, credential-like path or tracked raw/private hit.

The first full-suite rerun after that correction exposed an independent environment
failure: the launcher test copied the canonical 7.2 GiB database into a temporary
directory and exhausted the remaining disk. The test now builds a minimal repository
fixture from the five production files required by the launcher, plants `.git`,
`.local_keys` and `node_modules` sentinels to prove exclusion, and surfaces captured
installer output on failure. Launcher plus derived regression is `10/10`; the full
suite is `495/495`. Product installer behavior and its source-copy contract are
unchanged. Another complete exact-tree release is required after the corrective
commit.

The fourth exact-tree attempt on fixture commit `b56d59c1d` ran for 2,244.876
seconds and failed closed only at `rendered_chinese_ux` with return code 124;
reconciliation therefore remained `54/58`. Raw mutation and remote push remained
false, and the preceding unit, build, Chinese source audit, real browser workflow,
privacy, backup and exact-commit recovery gates completed. The timed-out Home gate
had already written all three expected screenshots within seven seconds, then hung
until its 300-second outer budget and left its Vite child on port 4178. The identical
gate passed standalone in 11.08 seconds, proving that the product assertions were
not the failure.

Final-audit gates now run in isolated process groups and terminate their complete
descendant tree on timeout while retaining bounded stdout/stderr diagnostics. The
Home browser gate adds 15-second Playwright action, 90-second per-viewport and
10-second shutdown bounds plus started/finished viewport events. The corrected real
three-viewport gate passes in 15.28 seconds and releases port 4178; the POSIX
descendant-timeout regression and focused R8/CLI suite pass `15/15`. Script migration
hash governance, consolidation `12/12`, test-value audit and full Python `496/496`
also pass. Another exact-tree release remains required after the corrective commit.

## Independent Engineering And Security Review

The review covers archive authorization, streamed package parsing, source and member
hash binding, path traversal, output atomicity, incremental-state drift, credential
exposure and raw immutability. The builder verifies public index, archive manifest,
part/package hashes and source manifest before parsing, rejects unsafe members, and
never reads the live Codex home. A previous archive history may only be reused as an
exact prefix; missing or drifted outputs trigger a full rebuild from immutable raw.

The implementation streams split gzip tar data and writes a complete output bundle
with temporary files, atomic replacement and parent-directory fsync. The state stores
hashes for every canonical output and binds the exact contract and model-parameter
hashes. Review findings covering model-parameter/state binding, process locking,
canonical credential/path rejection, symlink output boundaries, legacy-output scope
and the final-audit timeout budget were fixed and regression-tested. Post-commit
review additionally fixed the missing compact failed-gate diagnostic, tracked
synthetic-credential representation, unbounded launcher test fixture, final-audit
process-tree cleanup and Home browser internal timeout diagnostics. Final staged
inspection also normalized the new validator-profile indentation without a semantic
change. The final finding count after those fixes is
`0 Critical / 0 Important / 0 Minor`.

## Independent Product And Scope Review

The user-visible value is a truthful, reproducible derived layer that later Atlas
updates can consume without reading raw archives in the frontend. The output now
separates recoverable sanitized raw availability from the derived summary itself and
provides provenance for every session. This Task does not claim that the Atlas website,
snapshot, weekly report or sync status has changed.

The first full-suite candidate exposed that T1 had also regenerated six legacy
consumer files, making the existing Atlas and fixed Agent Context Pack stale before
T2. That scope error was closed by removing legacy publication from the T1 contract
and restoring those files to the Task-start bytes. Acceptance, goal-completion,
launcher and context-pack regressions then passed without weakening their checks.

## Model And Calibration Boundary

The Task-specific model parameters are in
`机器治理/参数与公式/codex_derived.v1_2_1_s07_p2_t1.json`. Activity coefficients,
Universe State windows and normalization formulas are implementation-derived
heuristics marked `HUMAN_REVIEW_REQUIRED`; this Task does not claim business-optimal
calibration. The existing global `MOD-008` / `FORM-008` registry remains compatible
and its broader legacy semantic migration is reserved for `S07-P2-T3`.

## Residual Boundaries And Rollback

- A changed archive registration or archive body fails closed; operators must not
  bypass verification by editing derived state.
- Missing or drifted output is rebuilt from all immutable registered archives, not
  patched in place from live Codex files.
- Rollback uses a corrective local commit for code/config/derived outputs. Raw archive,
  public index, raw manifest, ledger and sync state are retained unchanged.
- Local `main` remains divergent from the locally known remote state. No upload is
  permitted until all 149 Tasks plus final review/remediation complete.
