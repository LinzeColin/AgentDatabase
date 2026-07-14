# Memory Atlas v1.2.1 S06-P1-T2 Review

- Scope: S06-P1-T2 only
- Result: PASS locally; 38/149 Tasks complete
- Stage result: S06 2/9 complete locally
- Next gate: S06-P1-T3, not started in this run

## Acceptance

`config/data_sources/public_raw_layout.json` is the executable shallow-layout
contract linked from the canonical source registry. It permits only
`data/public_raw/chatgpt`, `data/public_raw/codex`, the operational
`data/public_raw/codex/sessions` directory, and
`data/public_raw/agents/<registered-source>`. Directories deeper than two levels,
unknown sources, symlinks, missing active source roots and files outside a source
partition fail closed. A configured Agent may wait for its first sync without a
placeholder file, preserving the S06-P1-T1 config-only extension contract.

The metadata-only audit finds five directories and 513 Git-tracked files: one
control README plus 512 raw data files partitioned as ChatGPT 379, Codex 132 and
Codex reviewer 1. It reads paths and file metadata only, never raw bodies, and
does not mutate raw, source, derived or sync-state data.

The same audit resolves the real Vite configuration through Vite itself. The
resolved `publicDir` is `data/derived/visualization`; `server.fs.allow` contains
only the app and derived visualization roots. A production build followed by
`--require-built-dist` found six regular dist files, no symlinks and no
`public_raw` path. The real
Codex `startup` route returns only AGENTS and derived profile/personalization
summaries, with zero public-raw sources.

## Validation

| Gate | Result |
| --- | --- |
| S06-P1-T2 layout regression | 10/10 PASS in 0.986s |
| Task-focused Python suite | 99/99 PASS in 20.823s |
| Real metadata/Vite/startup audit | PASS; raw content read=false |
| Production build + post-build isolation | PASS; 6 dist files, 0 raw paths |
| `validate:sync` | 7/7 PASS in 37.162s; raw mutation=false; remote push=false |
| `validate:fast` | 4/4 PASS in 12.568s |
| `validate:ui` | 14/14 PASS in 384.449s |
| Full Python suite | 356/356 PASS in 172.542s |
| Human-plane + dual-runtime deterministic render | 24/24 PASS; 0 drift, 0 reference issues |
| Script migration hash governance | 12/12 PASS |

The first full-suite attempt exposed stale rendered owner text after the reviewer
rollback wording fix; deterministic render corrected it. A later run exposed an
isolated launcher installer error; the identical installer command and the
launcher test both passed on immediate controlled rerun. The final complete suite
then passed 356/356. No product code was changed for that environmental failure.

## Boundaries

Within the public-raw data plane, this Task changed only the control README; none
of the 512 raw data files changed. It did not implement S06-P1-T3 credential exclusions or the S06-P2
append-only ledger, dedupe, 45 MiB chunking or restore command. It did not push,
deploy, create a branch/PR, merge/rebase or clean caches.

Before the local commit, rollback means reversing only the exact S06-P1-T2 Task
patch. After commit, rollback is `git revert <S06-P1-T2 commit>`; neither path
rewrites history or touches unrelated KMFA changes.

## Independent Review

The product/scope reviewer and engineering/security reviewer both closed the
latest diff at Critical 0 / Important 0 / Minor 0. Engineering initially found a
renamed-path dist-symlink bypass in the post-build audit. The final implementation
rejects every dist symlink and non-regular entry, its regression passes, and both
reviewers confirmed the finding closed on the refreshed diff.
