# Memory Atlas v1.2 Remediation Handoff

> **Current v1.2.1 note (2026-07-17 04:42 +10:00):** The v1.2.1 Task Pack is
> 57/149 complete locally. This run completes only `S08-P1-T3`; S08-P1 is 3/3
> and complete, while S08 remains in progress. `S08-P2-T1` is the next/only
> eligible Task in a later run and no P2 implementation starts here. The
> ChatGPT export connector now detects only four exact visible/official auth
> challenges: login, two-factor, CAPTCHA and account confirmation. Detection
> stops before any export click, credential field interaction, private API or
> account-content capture and persists `FAILED_NEEDS_HUMAN_AUTH` plus a
> `HUMAN_AUTH_REQUIRED` dispatch. A stateful request, including dry-run, is
> suppressed while paused. Resume is explicit, revision-bound and requires a
> SHA-256 evidence file; it never retries the browser action automatically.
> The generic state transition still cannot exit the human-auth pause.
> Regression is 115/115; the browser fixture covers 10 page scenarios and four
> official auth URLs with zero credential-store/private-API access. Final
> `validate:fast` is 6/6 in 23.091 seconds; the earlier final-scope
> `validate:sync` is 10/10 in 201.924 seconds. Test-value, human-plane,
> script-migration, renderer and required project-governance checks pass; the
> latter reports zero errors/warnings. Machine truth is 168 files, 38 active
> configs and 128 evidence payloads. The tracked ChatGPT sync baseline remains
> IDLE at revision 0 and byte-identical. No fetch, push, deploy, branch/PR,
> merge/rebase, live login, export request or shared cleanup occurred. Real
> GitHub upload remains prohibited until all 149 Tasks plus final
> review/remediation close. Do not start `S08-P2-T1` in this run.
>
> **Current v1.2.1 note (2026-07-17 01:49 +10:00):** The v1.2.1 Task Pack is
> 54/149 complete locally. This run completes only `S07-P3-T3`; S07 is 9/9 and
> S07-P3 is 3/3. `S08-P1-T1` is the next/only eligible Task in a later run and
> no S08 connector, browser or notification work starts here. Implementation
> commit `9b9e6a1d4` adds an isolated Codex restore proof. Two sequential runs
> each began from an existing empty task-owned directory, byte-copied and
> reverified immutable baseline archive `codex-public-raw-20260715t1300z`, ran
> its verifier-bound `restore.sh`, and called production `build_codex_derived`
> inside a database registering only that archive. Each run restored 432 files,
> including 430 data files and 2,068,870,942 data bytes, then rebuilt 427 events
> and 427 facets with 427/427 provenance coverage. Both initial outcomes were
> `BUILT_FROM_IMMUTABLE_RAW`; immediate replays were `NO_CHANGES`; all five
> derived output bytes and hashes matched. The tracked machine proof SHA-256 is
> `6dd8139b48ba528015a6d42e069048e4565b9d7cee1dc89b13f5470ad0afa7eb`.
> This is deliberately one-baseline-archive evidence: its 427 events are not
> claimed to equal the current canonical two-archive 432 events. Dedicated
> regression is 4/4 and the expanded related suite is 105/105. A fresh exact
> clone of `9b9e6a1d4` reproduced the proof byte-for-byte, passed fast 6/6 in
> 31.224 seconds and sync 10/10 in 214.895 seconds. The raw-isolated CI audit
> passed only after applying the exact GitHub Actions sparse patterns; 570
> tracked raw paths remained unmaterialized and raw bodies were not read. The
> final related closeout rerun is 105/105; human-plane and test-value pass with
> 162 machine files, 35 active configs and 125 evidence payloads. Script
> migration validation has zero errors, project governance required validation
> has zero errors/warnings, renderer has zero drift/reference issues, and all
> 48 governance event rows are valid JSONL. The optional all-repository semantic
> command still returns nonzero only for 62 pre-existing root/KMFA manifest and
> private-runtime reference errors; its OpenAIDatabase section is zero-error.
> A complete 180.39-second privacy scan covers 515 public raw files and reports
> zero high-risk secrets, credential-like paths, tracked private raw or value
> echo.
> The proof uses task-owned `HOME`, `CODEX_HOME`, temp and XDG paths, loads no user
> site/PYTHONPATH, requires no live Codex home/cache or network, leaves source
> archive identity and canonical raw/derived unchanged, and empties both run
> workspaces. No task-owned command invoked fetch, push, deploy, branch/PR,
> merge/rebase, scheduler install or general cleanup. A separate concurrent
> canonical-worktree flow did run `fetch --prune origin` at 01:32 and
> `pull --rebase --autostash origin main` at 01:33, rebasing unrelated S04
> commits onto fetched `origin/main=8b6b301d3` and leaving that shared worktree
> detached at `216bc36ac`. It did not move this Task's `main` ref or upload;
> S07-P3-T3 therefore closed in an isolated clean main worktree. Real GitHub
> upload remains prohibited until all 149 Tasks plus final review/remediation
> close. Do not start `S08-P1-T1` in this run.
>
> **Current v1.2.1 note (2026-07-17 00:39 +10:00):** The v1.2.1 Task Pack is
> 53/149 complete locally. This run completes only `S07-P3-T2`; S07 is 8/9,
> S07-P3 is 2/3 and remains in progress, and `S07-P3-T3` is the next/only
> eligible Task in a later run. Implementation commit `7e4dc6366` adds the
> portable `codex-scheduler` profile: 900-second cadence, 300-second quiet,
> 1,800-second max-wait and 3,600-second minimum success interval. Metadata
> churn resets quiet time while preserving the first pending deadline. Private
> machine-local `0600` atomic state, a nonblocking lock and a persisted active
> owner-run id enforce at most one T1 invocation and one ordinary push attempt
> per owner run. Profile/model/path/clock/duplicate/concurrency/incomplete/T1
> schema or Git-effect uncertainty fails closed; no fetch, force, branch, PR,
> merge, rebase or automatic retry path exists. Test-first hardening closed
> dry-run evidence loss, Owner Daily argument leakage, false child PASS
> semantics, dead max-wait and relative-source write ordering. Dedicated
> scheduler regression is 20/20; implementation focused regression is 44/44
> and final closeout regression is 93/93. A fresh
> local-main exact clone at `HEAD=origin/main=7e4dc6366` passes scheduler
> `DRY_RUN_READY` with decision `COALESCING` and zero state/sync/push/install,
> fast 6/6 in 34.694 seconds, sync 10/10 in 180.380 seconds including 207 sync
> tests and a 134.160-second credential scan, plus the raw-isolated CI audit.
> Machine inventory is exactly 160 files and 34 active configs; human-plane,
> test-value, script migration, staged push-size and complete privacy audits
> pass. Dual-runtime render has zero drift/reference issues and all 47 event
> rows are valid JSONL. The canonical dirty-tree smoke
> correctly stops at `initial_worktree_not_clean`; its broad-profile failures
> are solely the pre-existing raw deletions and `.DS_Store`, which remain
> untouched and unstaged. The task-owned clone/state/output paths were removed.
> No OS scheduler was installed or enabled; no real sync, fetch, GitHub push,
> deploy, canonical branch/PR, merge/rebase or general cleanup occurred. Real
> GitHub upload remains prohibited until all 149 Tasks plus final
> review/remediation close. Do not start `S07-P3-T3` in this run; empty-directory
> archive restore and derived snapshot proof remain unimplemented and unclaimed.
>
> **Current v1.2.1 note (2026-07-16 23:28 +10:00):** The v1.2.1 Task Pack is
> 52/149 complete locally. This run completes only `S07-P3-T1`; S07 is 7/9,
> S07-P3 is 1/3 and remains in progress, and `S07-P3-T2` is the next/only
> eligible Task in a later run. Implementation commits `6d92fac69` and
> `c9ad18547` add the exact `sync codex --push-main` command and its corrected
> audited script hash. Before any source or Git write the command requires
> branch `main`, a completely clean worktree/index including untracked files,
> `HEAD=refs/remotes/origin/main=live origin/main`, exactly one origin push URL
> and successful credential-excluding Codex discovery. It reuses the existing
> raw, derived, Atlas and legacy pipeline, stages only Codex allowlisted output,
> then runs complete sync validation, secret/path, append-only, single-commit
> push-size, stable-index/source/base and remote-race gates. It creates one
> single-parent CAS commit and permits at most one ordinary direct-main push.
> There is no fetch, force, branch, PR, merge, rebase, history rewrite or
> automatic retry. A rejected push preserves the local commit and fails closed;
> dry-run is zero-write. Dedicated isolated Git regression is 13/13, candidate
> related regression is 133/133 and final focused regression is 50/50. A fresh
> exact local-main clone of `c9ad18547` passes fast 6/6 in 29.431 seconds, sync
> 10/10 in 188.949 seconds and dedicated 13/13 in 15.195 seconds; exact dry-run
> returns `DRY_RUN_READY` for 176 eligible files with zero writes/push attempts.
> The canonical worktree smoke correctly stops at `initial_worktree_not_clean`.
> Closeout command/governance regression passes 86/86. The new model parameter
> legitimately increments machine inventory to 159 files and 33 active configs;
> the inventory contract, frozen audit baseline and audited script SHA-256 now
> match that measured set. Human-plane audit passes, dual-runtime deterministic
> render has zero drift/reference issues, and all 46 event rows are valid JSONL.
> Broad root changed-only governance validation remains fail-closed solely on
> 36 pre-existing sparse-root/registry diagnostics, checks no project and names
> no S07-P3-T1 path; this Task does not modify or claim those root baselines.
> All push tests use task-owned local bare origins only; no real fetch, GitHub
> push, deploy, canonical branch/PR, merge/rebase or general cleanup occurred.
> External `.codex`, KMFA, raw/session_history deletions and `.DS_Store` remain
> unstaged and untouched. Real GitHub upload remains prohibited until all 149
> Tasks plus final review/remediation close. Do not start `S07-P3-T2` in this
> run; scheduler/coalescing and full restore proof remain unimplemented.
>
> **Current v1.2.1 note (2026-07-16 22:13 +10:00):** The v1.2.1 Task Pack is
> 51/149 complete locally. This run completes only `S07-P2-T3`; S07 is 6/9,
> S07-P2 is 3/3 and closed, and `S07-P3-T1` is the next/only eligible Task in a
> later run. Six legacy Codex outputs keep their original schemas and fields but
> now carry additive `summary_semantics` declaring
> `redacted_derived_summary`, `derived_summary_not_full_raw_backup`,
> `full_raw_backup=false` and `recoverable_raw_backup=false`. The compatibility
> layer binds to two verified recoverable archives and 432 canonical sessions;
> real migration preserves 128 legacy sessions, seven activity days and seven
> recommendations. First apply atomically changed 11 legacy/Atlas/Agent
> Context/state paths. Immediate T3 and T2 publisher replays both return
> `NO_CHANGES`, `changed_paths=[]` and zero writes; Agent Context JSON/Markdown
> canonical rebuilds are byte-identical. Protected raw/public-raw/manifest,
> original `codex.json` and raw ledger hashes are unchanged. Dedicated 6/6,
> Codex/Atlas/registry/Agent Context 91/91, governance 43/43 and latest combined
> 50/50 pass. The main worktree full suite reached 508/512; four failures were
> caused only by externally created `.DS_Store` files and deleted tracked raw
> paths, which remain untouched. Exact-commit public-raw/raw-isolation modules
> pass 18/18. Implementation commit `c226e4d13` passes tracked-only recovery of
> 1,700 files, both source packages, 514/514 raw ledger, 432/432 publication,
> fresh build and snapshot parity at
> `9788facd01bb2177035868068fec9324ca6e676839e4463c2f704a53ffbafa3d`.
> A first detached release correctly failed only because push-size requires
> branch `main` and one Chromium close exceeded 10 seconds after all viewports
> passed. The exact unit rerun was 511/512 with only detached branch identity;
> the Home gate then passed standalone including server shutdown. A task-only
> shared clone with local `main` and `HEAD=origin/main=c226e4d13` closed both
> conditions; complete release `final_audit` 1/1 passed in 928.103 seconds with
> failed=0, critical skip=0, raw mutation=false and remote push=false. All
> task-owned worktrees, clones, recovery/browser artifacts and logs were
> removed. Post-closeout focused 49/49 and Python 3.13/3.12 deterministic render
> pass with zero drift/reference issues. Broad governance validation remains
> blocked only by pre-existing root/KMFA baselines (62 sync and 35 root/registry
> diagnostics), which this Task does not modify or claim to close. External
> `.codex`, KMFA, raw/session_history deletions and `.DS_Store`
> files remain unstaged and untouched. No fetch, push, deploy, canonical branch,
> PR, merge/rebase or general cleanup occurred. Do not start `S07-P3-T1` in this
> run and do not upload before all 149 Tasks plus final review/remediation close.
>
> **Current v1.2.1 note (2026-07-16 19:17 +10:00):** The v1.2.1 Task Pack is
> 50/149 complete locally. This run completes only `S07-P2-T2`; S07 is 5/9,
> S07-P2 is 2/3, and `S07-P2-T3` is next only after this Task closes. The
> canonical T1 432 events/facets publish by `event_id` into a 3,327,670-byte
> Memory Atlas snapshot with 717 memory nodes, 756 total nodes and 4,106 edges;
> SHA-256 is `1e826049d89be4195740e276fe99a89e58d849b1f793f9ab724ebd6f4352bd92`.
> The 14,582-byte 2026-07-13 weekly report SHA-256 is
> `b9007b66b6c2bde7201be3a05e1c592516ed3953e318fcea7c6c3dbe217ef2e6`.
> Independent `data/sync_state/codex_atlas.json` binds contract/model, canonical
> input and output hashes/counts. Immediate real replay is `NO_CHANGES` with
> `changed_paths=[]` and zero writes. Exact browser Search 2.0 finds newest
> `Codex session 归档备份删除` first, exposes two archive evidence refs and preserves
> the node through starfield, Memory River and Inspector; screenshot inspection
> found no overlap or actionable console/network error. Dedicated 9/9, focused
> 131/131, lint/build, fast 6/6, sync 10/10 and final ui 14/14 pass. Publication
> growth exposed and closed bounded Memory River evidence sampling and Obsidian
> progressive-reveal validation regressions. Raw, public raw, raw manifest,
> ledger, original Codex sync state and T3 legacy consumers remain unchanged.
> Full Python initially failed closed because acceptance still coupled the new
> Atlas count to T3 legacy recommendations and the protected machine inventory
> omitted the new publication parameter file. The acceptance audit now requires
> the canonical publisher dry-run to return exact `NO_CHANGES`, while the legacy
> recommendation gate remains separate; machine inventory is exactly 157 files
> and 31 active configs. Related 47/47 and final full Python 505/505 pass in
> 262.126 seconds. Dual-runtime render, privacy, built-dist raw isolation,
> raw/legacy diff, fast 6/6 and sync 10/10 pass. Full pre-commit release
> `final_audit` 1/1 passes in 1,018.082 seconds with no failed/critical-skipped
> gate, raw mutation or remote push. Implementation commit `02564125e` was then
> created locally. Its first exact-tree release ran 1,104.548 seconds and failed
> closed because tracked-only recovery still forced the new derived snapshot to
> equal the older immutable release; downstream reconciliation was 55/58, with
> raw mutation and remote push false. Recovery now keeps immutable release
> verification intact and only accepts a newer current snapshot when the
> recovered canonical publisher dry-run returns exact `NO_CHANGES`; fresh Pages
> build parity targets that validated hash. Recovery regression 23/23 and
> consolidation/test-value 17/17 pass. The same failed commit now independently
> recovers 1,694 tracked files, both source packages, 514/514 current raw ledger,
> 432/432 publication and fresh build with exact snapshot parity; cleanup passes.
> Corrective full Python 506/506 passes in 286.449 seconds. Corrective full release
> `final_audit` 1/1 passes in 1,268.493 seconds with no failed/critical-skipped
> gate, raw mutation or remote push; aggregate recovery and reconciliation pass.
> Corrective commit `f597a31f1` then passed exact-tree full release 1/1 in
> 980.106 seconds with no failed/critical-skipped gate, raw mutation or remote
> push. `S07-P2-T2` is complete local-only at 50/149. This run stops before
> `S07-P2-T3`; no upload is allowed before all 149 Tasks and final review close.
> No fetch, push, deploy, branch/PR, merge/rebase or general cleanup
> occurred. Do not start `S07-P2-T3` in this run and do not upload before all 149
> Tasks plus final review/remediation are complete.
>
> **Current v1.2.1 note (2026-07-16 15:14 +10:00):** The v1.2.1 Task Pack is
> 49/149 complete locally. This run completed only `S07-P2-T1`; S07 is 4/9,
> S07-P2 is 1/3, and `S07-P2-T2` is the next/only eligible Task. The canonical
> archive-derived builder consumes only raw-ledger registrations that pass the
> T2/T3 verifiers. The real build used two immutable archives and produced 432
> events, 432 facets, a 10-day behavior summary and 9 Universe State clusters,
> covering 2026-07-06 through 2026-07-15, 23,183 messages and 149,776 tool calls.
> Every session binds public index, archive manifest/hash, source manifest member,
> archive member/hash, portable source path and source SHA-256 provenance. Output
> is explicitly `derived_summary_not_full_raw_backup`; no raw message text,
> credential value or local absolute path is persisted. The final hardened full
> rebuild completed in 74.431 seconds; the immediate replay completed in 10.328 seconds with
> `NO_CHANGES`, zero parsed archives and zero file writes. Git diff for raw,
> public raw, raw manifest, ledger, Codex sync state and six legacy consumer files
> is empty. Dedicated 9/9, Codex focused 68/68, pre-commit full Python 494/494,
> fixture-corrective full Python 495/495, process-tree-corrective full Python
> 496/496, fast 6/6,
> sync 10/10 and ui 14/14 passed. The first release correctly failed because its
> 900-second unit-test child budget was below the measured 879.438-second suite
> runtime; the budget is now 1,800 seconds with 28/28 timeout regressions. The
> corrected full release passed 1/1 in 1,129.235 seconds with no critical skip,
> raw mutation or remote push. Python 3.13/3.12 deterministic render, privacy,
> built-dist raw isolation, script consolidation and diff whitespace checks passed.
> The first local commit is `04ecf4ab5`. Its first two exact-tree release attempts
> failed closed at 55/58 and 56/58 with different aggregate gate coverage, while
> standalone GitHub backup 12/12 and exact-commit recovery both passed for the same
> commit. The old profile tail hid `failed_gate_ids`; final audit now emits a bounded
> stderr compact summary, covered by R8/CLI 14/14. The third exact-tree attempt on
> diagnostic commit `458c81467` then identified `unit_tests` and `credential_audit`:
> one synthetic credential fixture contained a literal scanner-recognized token.
> It is now assembled only at runtime; the tracked-tree privacy guard is clean. The
> first 495-test rerun then exposed disk exhaustion in a launcher test that copied
> the 7.2 GiB canonical database. That test now uses the five required production
> files plus ignored-path sentinels, preserves production installer behavior, emits
> captured diagnostics, and passes with the derived regression at 10/10; full Python
> is 495/495 in 296.724 seconds. Two task-only failed-test temp directories were
> removed to recover disk; no general cache cleanup occurred. Fixture commit
> `b56d59c1d` then completed unit/build, browser workflows, privacy, backup and exact
> recovery but its 2,244.876-second exact-tree release failed closed only because
> `rendered_chinese_ux` hung after writing all three screenshots and hit the
> 300-second outer timeout; reconciliation was 54/58, raw mutation and remote push
> were false. The timed-out parent left its Vite child on 4178; that exact task-owned
> process was terminated and the identical gate passed standalone in 11.08 seconds.
> Final-audit gates now use isolated process groups with complete timeout cleanup,
> and Home validation has bounded Playwright action/viewport/shutdown operations plus
> progress events. The corrected real gate passes in 15.28 seconds, focused R8/CLI
> passes 15/15, consolidation 12/12, test-value and full Python 496/496 in 311.339
> seconds pass. A corrective local commit and one complete exact-tree release still
> remain closeout work in this same Task. Unrelated
> KMFA and automation changes remain unstaged and untouched. No
> Atlas snapshot, weekly report, sync-state, UI, fetch, push, deploy, branch/PR,
> merge/rebase or cache cleanup changed. Do not start more than `S07-P2-T2` next,
> and do not upload before all 149 Tasks plus final review/remediation are complete.
>
> **Current v1.2.1 note (2026-07-16 05:38 +10:00):** The v1.2.1 Task Pack is
> 48/149 complete locally. This run completed only `S07-P1-T3`; S07 is 3/9,
> S07-P1 is 3/3 and closed, and `S07-P2-T1` is the next/only eligible Task.
> Canonical `data/sync_state/codex.json` bootstraps the immutable T2 archive and
> is revision 6 with cursor sequence 2, 435 portable paths, 437 historical
> source-content hashes, two deferred active sessions and `active_run=null`.
> Real incremental archive `codex-incremental-20260715t180600z` observed 435
> stable files and 3,972,466,441 source bytes with identical before/after digest
> `9f8dd012ef39cc51d81e9cea8c36f8e183797345a8b42fde22469060949d46e5`.
> Seven new paths produced seven unique objects; the 16,157,223-byte one-part,
> nine-member package has SHA-256
> `5b516b8ef34fab4e04a96e7f7ad70c13a5ad99f0407328bce5de0790c2831c8d`.
> Exact static replay is zero-write `NO_CHANGES`; identical path aliases store one
> object, and four persisted phases resume the same archive ID without overwrite.
> T3/T2/raw audits pass with 514/514 ledger parity and zero drift/deletion/new raw.
> Dedicated 10/10, Codex focused 33/33, governance/privacy focused 54/54, final
> Python 485/485, fast 6/6, sync 9/9, ui 14/14 and pre-commit release 1/1 passed.
> The first sync run exposed and closed a profile-CWD test import defect; the first
> release exposed and closed a stale 180-second credential budget against a
> 273.482-second real scan, preserving the complete scan with a 600-second budget.
> Final security review also closed an Important verifier gap by binding exact
> README/restore bytes and rejecting unsafe manifest/part inventory or symlinks.
> Engineering/security and product/scope review are 0 Critical / 0 Important /
> 0 Minor after remediation. The one local Task commit must still receive its
> post-commit exact-tree release/recovery rerun; this pre-commit note does not
> preclaim that result. Six unrelated files (two `.codex` automation-state and
> four KMFA files) remain unstaged. No fetch, push, deploy, branch/PR,
> merge/rebase or cache cleanup occurred. Do not start more than `S07-P2-T1`
> next, and do not upload before all 149 Tasks plus final review/remediation are
> complete.
>
> **Current v1.2.1 note (2026-07-16 01:28 +10:00):** The v1.2.1 Task Pack is
> 47/149 complete locally. This run completed only `S07-P1-T2`; S07 is 2/9,
> S07-P1 is 2/3, and `S07-P1-T3` is the next/only eligible Task. Real archive
> `codex-public-raw-20260715t1300z` contains 430 stable eligible files and
> 3,884,927,678 source bytes; four recent active sessions are deferred without a
> hash/stat claim. Stable before/after digest is
> `c1e284843c4d3171b49ac84bc682a564279f822a502a7d4e4a9fb768d30cd061` and
> source mutation is false. The 558,731,407-byte recoverable sanitized package
> has 432 members, SHA-256
> `e1406eea8b67ffdac96fb41f26f821696389b6eb5ed9ef069b1b42b186d1f174`
> and 12 parts at or below 45 MiB. Its public index is the 513th raw-ledger row;
> the exact 513-row immutable raw manifest is byte-identical to the ledger with
> SHA-256 `05ecc7c521214bd513b6ae6101b1c2ecd49c58dfcbf96fe2c2a0ad9c17c90478`.
> Restore now validates package hash, exact unique safe regular members and the
> source manifest before atomic publication. Dedicated 14/14, focused 54/54,
> recovery 22/22, full Python 475/475, fast 6/6, sync 8/8 and ui 14/14 passed.
> Exact-commit tracked-only recovery reads 1,665 OpenAIDatabase Git-stream files,
> validates current raw/ledger 513/513 while preserving the immutable 512-row
> release manifest as a verified subset, and passes fresh build/Pages parity.
> Final `validate:release` passed 1/1 on the exact commit: all 17 final-audit gates,
> 58/58 requirement reconciliation, raw-mutation=false and remote-push=false passed.
> Engineering/security review closed 0 Critical / 0 Important /
> 0 Minor after all findings were fixed; product/scope review is also clean.
> Cursor, content dedupe, interrupted-run resume and derived output remain T3 or
> later. Four unrelated KMFA changes remain unstaged. No fetch, push, deploy,
> branch/PR, merge/rebase or project cache cleanup occurred. Do not start more
> than `S07-P1-T3` next, and do not upload before all 149 Tasks plus final
> review/remediation are complete.
>
> **Current v1.2.1 note (2026-07-15 22:19 +10:00):** The v1.2.1 Task Pack is
> 46/149 complete locally. This run completed only `S07-P1-T1`; S07 is 1/9,
> S07-P1 is 1/3, and `S07-P1-T2` is the next/only eligible Task. The canonical
> discovery order is explicit `--codex-home`, `MEMORY_ATLAS_CODEX_HOME`,
> `CODEX_HOME`, then home-relative `.codex`; invalid explicit candidates fail
> closed. The allowlist contains session index, active/archived session JSONL,
> history/transcription history, JSONL logs and the two canonical `logs_2.sqlite`
> paths. Auth/config/installation id, private keys, OAuth locks, browser credential
> stores and common credential names are excluded. Discovery reads metadata only,
> emits `[CODEX_HOME]` plus counts/bytes/digest, and performs no archive, cursor,
> derived, network or remote Git write. The non-normative local observation at
> `2026-07-15T12:15:15Z` was 433 files, 5 non-empty source kinds, 4,265,648,215
> bytes, 7 excluded entries and metadata digest
> `90bd0f6124a78d03ffcb57be0c72ae81b48c3b891015fbbf824034d1d5afb474`;
> these values will drift with normal Codex activity and are not acceptance
> thresholds. Dedicated 9/9, focused 54/54, full Python 456/456, fast 6/6, sync
> 7/7, ui 14/14, release 1/1, privacy and Python 3.13/3.12 deterministic render
> passed. Engineering/security and product/scope reviews both closed at 0 Critical /
> 0 Important / 0 Minor after all findings were remediated. The supplemental root
> governance validator is not claimed as PASS because this sparse checkout omits
> its root templates and other project directories; no sparse settings were changed
> to manufacture a result. Exact final staging is re-audited immediately before the
> local commit rather than copied into this self-referential note. Four unrelated
> KMFA changes remain unstaged. No source body, public raw, archive, state, derived
> data, fetch, push, deploy, branch/PR, merge/rebase or cache cleanup changed. Do
> not start more than `S07-P1-T2` next, and do not upload before all 149 Tasks plus
> final review/remediation are complete.
>

> **Current v1.2.1 note (2026-07-15 20:32 +10:00):** The v1.2.1 Task Pack is
> 45/149 complete locally. This run completed only `S06-P3-T3`, closed
> `S06-P3` at 3/3 and S06 at 9/9, and left `S07-P1-T1` as the next/only eligible
> Task. A temp-only cross-contract fixture matrix calls the production raw-ledger,
> 45 MiB chunk, restore and credential contracts for append, duplicate, same-size
> tamper, 45 MiB+17-byte split, exact restore, manifest tamper and synthetic
> credential blocking. It reads no real raw/private credential and performs no
> network or remote operation. Dedicated 4/4, focused 93/93, full Python 447/447,
> fast 6/6, sync 7/7, UI 14/14 and release 1/1 passed; privacy, built-dist raw
> isolation and Python 3.13/3.12 deterministic render passed. The real 512-row
> ledger remains 128,209 bytes, inode 156668907, mtime 1783818229.381278488 and
> SHA-256 `1a4fa71303903ca896c82640f7b4550cee47f3cc8ec600f81d03f7603e120c96`.
> Engineering/security and product/scope reviews both closed at 0 Critical / 0
> Important / 0 Minor. Real pending audit remains fail-closed because the locally
> known `origin/main` and local `main` diverge; no fetch, reconciliation, push,
> deploy, branch/PR or cache cleanup occurred. The final exact staged audit passed
> over 17 OpenAIDatabase paths as one `single_commit_ready` batch with 776,798 unique
> object bytes and a 9,169,758-byte conservative upper bound. Do not
> start more than `S07-P1-T1` next and do not upload before all 149 Tasks plus the
> final overall review are complete.
>
> **Current v1.2.1 note (2026-07-15 18:31 +10:00):** The v1.2.1 Task Pack is
> 44/149 complete locally. This run completed only `S06-P3-T2`; `S06-P3` is 2/3
> and the next/only eligible Task is `S06-P3-T3`. The canonical push-size guard
> fixes 45 MiB recommended chunks, staged/pending `>50 MiB` split-required,
> `>=100 MiB` ordinary-blob hard stop and strict `<1.5 GiB` batches using unique
> Git object bytes plus 8 MiB/batch and 256 bytes/object reserves. Pending plans
> use first-parent fast-forward boundaries and checkpoint recomputation. Audits
> use no-replace/no-lazy-fetch and never fetch or push. Local backup rejects
> pre-existing staged changes and symlink targets, binds the guard to one exact
> index tree, disables all Git hooks, and uses commit-tree plus old-HEAD update-ref
> CAS with truthful post-commit states. Final tests are dedicated 28/28, full
> Python 443/443, fast 6/6, sync 7/7, UI 14/14 and release 1/1; engineering/security
> review closed at 0 Critical / 0 Important / 0 Minor. Exact staged audit passed
> as one `single_commit_ready` batch; product/scope review allowed local commit with
> no blocking finding, and its one documentation-freshness Minor was closed in the
> final record update. Real pending audit
> remains fail-closed because locally known `origin/main` and `main` diverge; no
> fetch, reconciliation, push, deploy, branch/PR or cache cleanup occurred. Do not
> start more than `S06-P3-T3` next, and do not upload before all 149 Tasks plus the
> final overall review are complete.
>
> **Current v1.2.1 note (2026-07-15 15:15 +10:00):** The v1.2.1 Task Pack is
> 43/149 complete locally. This run completed only `S06-P3-T1`; `S06-P3` is 1/3
> and the next/only eligible Task is `S06-P3-T2`. The canonical
> `raw_isolation.json` contract binds default rg exclusions, all eight Codex
> resource routes, root/standalone non-cone sparse CI checkouts and a pre-enforced
> Vite import/load/transform guard. Default worktree/project searches expose zero
> raw paths; explicit `rg --no-ignore` and Git still identify all 549 tracked raw
> paths. Production dist audit reports six regular files, 3,249,771 bytes, zero raw
> path components and zero collisions against 512 raw-ledger hashes without reading
> raw bodies. Dedicated tests are 8/8, focused tests 58/58, full Python 419/419,
> fast 5/5, sync 7/7, ui 14/14 and release 1/1; frontend lint/build and an actual
> sparse-CI checkout with fresh npm install pass. No raw/public archive/ledger/source
> package, remote, deployment, branch/PR or cache was changed. Independent review is
> recorded in the T1 review artifact. Do not start more than `S06-P3-T2` in the next
> run and do not push before the entire Task Pack plus final review closes.
>
> **Prior v1.2.1 T2 note (2026-07-15):** This file preserves the earlier v1.2 R7
> handoff below. Memory Atlas is executing the v1.2.1 Task Pack with one Task per run.
> S04 and S05 are complete locally; S06-P1, S06-P2-T1 and S06-P2-T2 are complete
> locally and the next Task is only S06-P2-T3. `S06-P2-T2` adds the canonical
> 45 MiB archive chunking contract, deterministic ordered bytes/SHA-256 manifests,
> dir_fd/O_NOFOLLOW no-overwrite publication, manifest-last durability, idempotent
> replay and identity-gated cleanup. The real inventory has no new eligible
> over-threshold source package: data/public_raw has zero files above 45 MiB, while
> all 37 tracked files above 45 MiB are immutable pre-v1.2.1 90 MiB parts and none
> reaches 100 MiB. T2 did not rewrite or migrate them; restore/verify remains T3.
> Fourteen dedicated and 97 related tests pass; full Python is 398/398, sync is
> 7/7, fast is 4/4, UI is 14/14, and Python 3.13/3.12 deterministic render is clean.
> Final engineering/security and product/scope reviews are both 0 Critical / 0
> Important / 0 Minor. `S06-P2-T1` adds the canonical immutable raw-ledger
> contract, source-stat guards, SHA-256 fingerprints, exclusive append locking,
> append-only/idempotent registration and three-adapter integration. The real
> 512-row ledger passed with zero drift/deletion/unledgered files and unchanged
> bytes, inode and mtime; no public raw or source file changed. Its historical gates passed
> sync 7/7, fast 4/4, UI 14/14 and the complete Python suite 384/384. The full
> credential scan covered all 513 tracked raw/control files including 35 large files;
> its unchanged critical command received a 600-second budget after a measured
> 356.46-second run exceeded the old 300-second budget. Independent engineering/security
> and product/scope reviews both closed at 0 Critical / 0 Important / 0 Minor.
> S05-P1 compressed the human
> plane to seven shallow Chinese files, compressed the three root owner entries, and
> added the deterministic v1.2.1 change/five-workflow map. `S05-P2-T1` added
> `config/memory_atlas_machine_truth_index.json` and deterministically renders
> `机器治理/README.md` as a 72-line/4,702-byte shallow index over exactly five domains
> and 11 canonical targets. The index stores paths, responsibilities and mutability
> only; it does not copy parameter values, formula expressions, runtime status, test
> assertions or data. `S05-P2-T2` then used
> `config/memory_atlas_machine_plane_cleanup.json` to delete exactly eight approved
> Stage-era nested READMEs (1,948 lines / 90,721 bytes). It preserved byte-identical
> sets of 29 active configs, one current release and 122 evidence payloads, migrated
> the only executable README evidence reference to `docs/governance/roadmap.yaml`,
> migrated the same three stale references in the tracked derived collaboration report
> without changing scores or business values, and permanently verifies all eight Git
> restore paths from commit `187577cc9`.
> `S05-P3-T1` keeps `apps/memory-atlas/src/i18n/zh-CN.ts` as the only typed
> human-interface copy source. Version
> `memory_atlas.zh_cn_copy.v1_2_1_s05_p3_t3` now provides the visible glossary
> explanations, 11 field labels, nine enum groups and a Chinese unknown-value
> fallback. Help, runtime status, Inspector and proposal surfaces consume the same
> source; code/API/schema/data attributes, persistence fields and exported payload
> keys remain English and unchanged. The shared fail-closed audit/tests remain
> `scripts/audit_memory_atlas_human_plane.py` and
> `tests/test_memory_atlas_human_plane.py`; the new copy-source suite has 6 tests,
> while 65 focused tests, 325 full Python tests, fast 4/4, ui 12/12, frontend
> lint/build, dual-runtime deterministic render and desktop/mobile Help browser checks
> passed. `S05-P3-T2` adds a TypeScript AST semantic-readability rule without a
> new public profile. It scans 83 UI source files for mojibake, default-visible
> machine fields, actionless errors and English empty states. The exact baseline is
> 79 findings (78 machine-field/enum points and one actionless error); mojibake and
> English empty states are zero. Any new, missing-unreconciled or fingerprint-drifted
> finding fails. UI executes the rule as `semantic_readability`; release executes the
> same rule through its existing final-audit Chinese UX gate. `S05-P3-T3` then
> remediated all 79 findings: finding, known-finding and known-T3-debt counts are zero,
> and `semantic_readability_clean=true`. Core default-visible fields, statuses, risk,
> tier, sync, proposal, formula and canvas labels use Chinese humanizers; API, schema,
> data attributes, internal enums, persistence and export payload keys remain English.
> Seven semantic tests, 35 governance/profile tests, 332 full Python tests, fast 4/4,
> ui 13/13, frontend lint/build and the release profile plan passed. Real Home browser gates
> passed at 1470x661, 1440x900 and 390x844 with no section overlap, horizontal overflow,
> console error or failed response. Data Guide structure and detail/proposal browser
> gates also passed with raw edge/ID evidence and version strings excluded from the
> default-visible surface. Independent engineering/governance and product/UI reviews
> both closed at 0 Critical / 0 Important / 0 Minor.
> `S06-P1-T1` extends the sole canonical
> `config/data_sources/source_registry.json` with the 11 TaskPack sync fields for
> ChatGPT official export, Codex local data, generic agents and the existing
> codex-reviewer source. Discovery and data paths are portable and repository-relative;
> parsers, schedules, state/archive/derived paths and final-delivery-only push policy
> are explicit. `atlasctl sync` now dispatches through registered `source_type` and
> `parser.entrypoint`; a standard generic source can reuse the generic adapter by
> configuration. Environment candidates now drive the matching adapter argument;
> concrete generic sources cannot redirect `source_id`/`agent_id`, and parser/type,
> state/archive/derived conventions plus push policy fail closed. The active raw policy
> points to the canonical registry; the old machine-governance registry has no live
> script/test/app/config references and remains historical. The protected active-config
> manifest was updated for that one reviewed reference change. Explicit generic input
> blocks a conflicting environment candidate, and the generic adapter now parses
> multi-record JSONL. Canonical ID/type/status, non-canonical generic-only IDs, reserved
> aliases, non-lowercase/non-portable agent IDs, case-only and whitespace-padded
> namespace aliases, Windows reserved device basenames,
> template/concrete namespace collisions, direct adapter provenance and empty/invalid
> JSONL all fail closed. The owner change map now
> explicitly labels its unfinished-route prose as the S05-P1-T3 historical snapshot.
> Fourteen registry tests, 103 focused tests,
> sync 6/6, fast 4/4 and 346 full Python tests passed. No public raw, source data,
> state, manifest, chunk or restore artifact changed.
> `S06-P1-T2` adds `config/data_sources/public_raw_layout.json` and the
> `atlasctl audit --check public-raw-layout` gate. The existing tree is now bounded to
> five shallow directories and 513 tracked files: one control README plus 512 raw
> files split across ChatGPT 379, Codex 132 and Codex reviewer 1. The audit reads no
> raw bodies, rejects unknown/deep/symlink paths, and preserves config-only sources
> before their first sync. Real Vite resolution keeps publicDir and server allow on
> derived/app paths; a six-file production dist has no symlink or public_raw path, and the real
> startup route returns zero raw sources. Only the public-raw control README changed;
> no raw data file changed. T3 credential exclusions and P2 ledger/chunk/restore remain
> unimplemented. Ten layout tests, 99 focused tests, sync 7/7, fast 4/4, ui 14/14,
> 356 full Python tests, frontend build, script-hash governance and dual-runtime
> deterministic render passed; audit safety remained raw mutation=false and remote
> push=false. Historical source/release/recovery evidence remains unchanged. The next
> Task is only `S06-P1-T3`; it has not started.
>
> The only public validator profiles are `validate:fast`, `validate:sync`,
> `validate:ui`, and `validate:release`. Commands in the older "Verified Commands"
> section are historical evidence, not current package aliases. Use
> `docs/remediation/memory_atlas_v1_2_1/S04_P3_T3_COMMAND_MIGRATION.md` for old-command
> lookup. No v1.2.1 work has been pushed or deployed; do not create a branch or PR,
> and do not clean TaskPack, recovery evidence, raw/derived data, or machine caches.

## Current Goal

Complete reopened v1.2 remediation R0-R8 with at most one phase per run and one final
GitHub main upload only after R8 passes.

## Current State

- R0-R7: complete locally; this does not mean the release is complete.
- R7 public raw: 512 sanitized files / 452,781,632 bytes; manifest and ledger each have
  512 entries with 0 drift, deletion or unledgered files.
- R7 immutable release: `memory-atlas-v1-2-r7-20260710`; snapshot SHA-256
  `b608631fded9e116d350895be20e6e61be3c7e42ba651ccdf7fc52afd8fefcbc`.
- Snapshot: 278 active memories / 379 conversations / 128 Codex sessions / 435 nodes /
  2,325 edges; derived/release/local candidate/Pages candidate bytes match.
- Tracked-only recovery: PASS for functional candidate `f65668b9`; 8,372 tracked files,
  0 working-tree-only files, two source packages restored, fresh npm install/build and
  Pages parity PASS. Exact pushed-remote clone recovery is not yet proven.
- Requirements after R7: `VERIFIED 53 / PARTIAL 2 / FAILED 3 / NOT_VERIFIED 0`.
- Release: `FAIL_REMEDIATION_REQUIRED`.
- GitHub push, app reinstall and Cloudflare deployment: not performed.
- Online website and installed app: still the prior release; do not present them as R7.
- Final fetch: `origin/main=37d757be958e1546b5263e86d2193663b184bbe8`;
  before R7 record commit local `main` was ahead 52 / behind 17.

## Key Decisions

- Rendered/runtime evidence is required; source markers and document presence are not
  product acceptance.
- Required browser viewports remain `1470x661`, `1440x900` and `390x844`.
- Public transcript recovery is sanitized and credential-free. Private source paths,
  credentials, original binary bodies and private export bytes are intentionally absent.
- Raw acceptance requires non-empty source families, byte-wise privacy audit, immutable
  manifest and a drift/deletion/new-file ledger audit; vacuous zero-row PASS is invalid.
- One immutable release snapshot drives derived, local candidate and Pages candidate
  bytes; install/deploy scripts must consume that release rather than rebuild ad hoc.
- Recovery proof distinguishes the functional candidate `f65668b9` from later evidence
  binders. Exact final pushed HEAD recovery is an R8 gate.
- Hosted static remains read-only. Command/proposal/Owner Daily execution remains
  local-app only and all R3-R6 security boundaries remain in force.
- Incoming remote history must be preserved. R8 may reconcile it, but must not force-push.

## Read First

- `docs/remediation/memory_atlas_v1_2/R7_DATA_PARITY_RAW_EVIDENCE_AND_RECOVERY.md`
- `机器治理/证据与日志/remediation/v1_2_r7/status.json`
- `机器治理/证据与日志/remediation/v1_2_r7/browser_regression.json`
- `机器治理/证据与日志/remediation/v1_2_r7/recovery/status.json`
- `机器治理/证据与日志/remediation/v1_2_r7/source_provenance.json`
- `docs/remediation/memory_atlas_v1_2/R0_SOURCE_RECOVERY_AND_GAP_BASELINE.md`
- `docs/superpowers/plans/2026-07-10-memory-atlas-v1-2-remediation.md`

## Verified Commands

- `python3 -m unittest tests.test_memory_atlas_r7_public_raw tests.test_memory_atlas_r7_raw_integrity tests.test_memory_atlas_r7_release_parity tests.test_memory_atlas_r7_recovery -q`
- `python3 scripts/audit_memory_atlas_public_raw.py --database-dir .`
- `python3 scripts/raw_archive_manifest.py audit --database-dir .`
- `python3 scripts/materialize_memory_atlas_release.py verify --database-dir .`
- `python3 scripts/audit_memory_atlas_snapshot_parity.py --database-dir . --local-runtime <prepared-local-runtime> --pages-candidate apps/memory-atlas/dist/memory_atlas.json`
- `python3 scripts/privacy_guard.py --database-dir . --scan-only`
- `npm run lint`
- `npm run build`
- `npm run validate:v1.2-visual-models`
- `npm run validate:v1.2-visual-workflows`
- `npm run validate:v1.2-home-multiviewport`
- `npm run validate:v1.2-command-workflows`
- `npm run validate:v1.2-proposal-e2e`
- `npm run validate:v1.2-owner-daily-e2e`
- `npm run validate:stage7-visual`
- `npm run validate:stage7`

## Remaining Risks

- Five requirements remain non-VERIFIED: `S03-AC05`, `S04-AC04`, `S10-AC04`,
  `S14-AC02`, `S14-AC05`.
- Overall final audit does not yet require all new R1-R7 gates in one fail-closed chain.
- Local and remote histories diverge; R8 must preserve both before the single push.
- Remote clone recovery, exact pushed commit install, exact pushed commit deployment and
  online multi-viewport/workflow acceptance are not yet proven.
- Installed app and online site are intentionally unchanged.

## Next Phase

Run only `R8_OVERALL_ACCEPTANCE_AND_SINGLE_FINAL_DELIVERY`: reconcile both histories,
wire and pass all 58 requirements, perform the one authorized GitHub main push, recover
from that exact remote HEAD, reinstall/deploy that exact commit and repeat browser/workflow
acceptance online. Do not mark the goal complete unless every R8 gate passes.
