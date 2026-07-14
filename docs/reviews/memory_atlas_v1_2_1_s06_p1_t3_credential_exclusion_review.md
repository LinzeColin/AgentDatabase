# Memory Atlas v1.2.1 S06-P1-T3 Review

- Scope: S06-P1-T3 only
- Result: PASS locally; 39/149 Tasks complete
- Phase result: S06-P1 3/3 complete locally
- Stage result: S06 3/9 complete locally
- Next gate: S06-P2-T1, not started in this run

## Acceptance

`config/data_sources/credential_exclusion.json` is the canonical
`credentials_not_transcript` contract. It permits authorized plaintext
transcript, email, phone, ordinary personal/business discussion and safe
placeholders in public raw. It blocks only seven account-control categories:
API keys, cookies, session tokens, passwords, private keys, OAuth tokens and
browser credential stores. Source registry entries now activate this single
contract instead of deferring to a future Task.

Credential-like public-raw filenames fail closed. Local absolute paths remain
disallowed by the repository portability boundary and are replaced separately;
they are explicitly not a credential category. Private import continues its
existing broad email, phone, secret and local-path redaction, so this Task does
not weaken private-input handling.

The public sanitizer scans before write, does not mutate source bytes and does
not echo credential values in findings. The repository scan includes every
tracked public-raw file regardless of the former 1 MiB shortcut. A staged
credential-like fixture is rejected, while ordinary conversation/session paths
remain valid.

## Real Data Evidence

The content audit parsed 512 JSON/JSONL public-raw files totaling 452,781,632
bytes and accepted 23,893 correctly formed binary omission markers. Credential
files, credential-like paths, nonportable local paths, unmarked binary, invalid
JSON and oversize files were all zero.

The repository scan covered 513 tracked public-raw files, including 35 files
larger than 1 MiB, with `public_raw_large_files_skipped=false`. Credential hits,
credential-like path hits, tracked private roots and missing `.gitignore`
requirements were all zero. No raw, derived, sync-state, ledger, chunk or
restore artifact changed.

## Validation

| Gate | Result |
| --- | --- |
| S06-P1-T3 credential exclusion regression | 8/8 PASS |
| Public raw content audit | PASS; 512 files / 452,781,632 bytes |
| Repository credential scan | PASS; 513 tracked files / 35 large files / skip=false |
| Task-focused Python suites | 75/75 PASS |
| `validate:sync` | 7/7 PASS in 167.371s; raw mutation=false; remote push=false |
| `validate:fast` | 4/4 PASS in 10.230s |
| `validate:ui` | 14/14 PASS in 341.195s |
| Full Python suite | 365/365 PASS in 301.899s |
| Script migration hash governance | PASS |
| Human-plane + dual-runtime deterministic render | PASS; 0 drift, 0 reference issues |

The first focused run exposed `pwd="..."` in an authorized transcript. `pwd`
can denote a working directory, so the detector preserves path-like values,
ordinary working-directory text and safe placeholders while excluding
high-signal account-control values. The first full suite exposed a release-audit
fixture that omitted the new canonical contract; the fixture now copies and
stages the contract, preserving fail-closed release behavior. A second full
suite invocation used the wrong working directory and produced ten package
import errors; the canonical repository-root invocation then passed 365/365
without implementation changes.

## Boundaries

This Task did not implement S06-P2 ledger/hash/dedupe/chunk/restore behavior. It
did not modify source or public-raw bytes, model formulas or business parameter
values. It did not push, deploy, create a branch/PR, merge/rebase or clean
caches.

Before the local commit, rollback means reversing only the exact S06-P1-T3
patch. After commit, rollback is `git revert <S06-P1-T3 commit>`; neither path
rewrites history or touches unrelated KMFA changes.

## Independent Review

Product/scope review: Critical 0 / Important 0 / Minor 0. Its earlier Important
finding about `pwd=` coverage is closed by the contextual high-signal rule.

Engineering/security review: Critical 0 / Important 0 / Minor 0. Its earlier
Critical structured-field bypass and Important hidden-file omission are closed
by key/value-aware field classification and independent all-file enumeration.
Both reviewers repeated the real public-raw audit and repository credential
scan read-only; both returned PASS without modifying files or Git state.
