# Memory Atlas v1.2.1 S07-P2-T3 Codex Legacy Summary Review

## Status

- Task: `S07-P2-T3`
- Acceptance: `ACC-MA-V121-S07-P2-T3`
- Delivery: local implementation candidate; exact-commit closeout pending
- Task Pack progress remains `50/149` until the exact committed tree passes release acceptance.
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
- The first full-suite invocation from the database subdirectory was invalid and
  is not counted: 502 tests ran with 10 historical absolute-package import
  errors caused by the wrong current working directory.
- The canonical repository-root invocation ran 512 tests. 508 passed; four raw
  layout/isolation checks failed only because external working-tree changes
  created ignored `.DS_Store` files and deleted the tracked ChatGPT archive
  directory during the run. Those unrelated changes are not restored, deleted,
  staged, or included in this Task. Exact-commit validation remains required.

## Risk And Rollback

The compatibility layer fails closed on a positive full/raw-recoverability
claim, unsafe or missing inputs, stale canonical hashes, stale Atlas publication,
unsafe output paths, lock contention, or transactional write failure.

Before a local commit, reverse only the T3 code/config/derived/governance patch.
After a local commit, use a corrective commit. Never delete or rewrite canonical
raw archives, public indexes, raw manifests, the raw ledger, or the original
Codex incremental sync state as rollback.

## Stop Boundary

`S07-P3-T1` remains unimplemented. This Task can move to 51/149 only after its
exact local commit passes tracked-only recovery and the final release gates from
a complete committed tree. No remote upload is allowed before all 149 Tasks and
the final review/remediation close.
