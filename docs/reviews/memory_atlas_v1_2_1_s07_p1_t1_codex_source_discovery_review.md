# Memory Atlas v1.2.1 S07-P1-T1 Codex Source Discovery Review

## Status

- Task: `S07-P1-T1`
- Acceptance: `ACC-MA-V121-S07-P1-T1`
- Result: `COMPLETE_LOCAL_ONLY`
- Task Pack progress: `46/149` (`30.87%`)
- Stage / phase progress: S07 `1/9`; S07-P1 `1/3`
- Next and only eligible Task: `S07-P1-T2`

## Scope

This Task establishes portable, metadata-only discovery of local Codex source files. It does not
archive public raw, write sync state, build derived data, fetch, push, deploy, create a branch or PR,
or implement `S07-P1-T2` / `S07-P1-T3`.

## Acceptance Evidence

| Requirement | Evidence | Result |
|---|---|---|
| No hard-coded user path | Ordered candidates are `--codex-home`, `MEMORY_ATLAS_CODEX_HOME`, `CODEX_HOME`, then home-relative `.codex` | PASS |
| Explicit invalid candidates fail closed | Missing, relative, non-directory and symlink roots do not fall through | PASS |
| Only Codex transcript/log families are eligible | Exact session index/history/sqlite paths plus recursive active/archived session and JSONL log trees | PASS |
| Authentication and secret stores are excluded | Allowlist-only policy plus 23 blocked name patterns and `private_keys`, `mcp-oauth-locks`, `browser` segments | PASS |
| No source body or local path is exposed | Discovery uses directory enumeration and stat metadata; output serializes `[CODEX_HOME]`, counts, bytes and digest only | PASS |
| No later-phase writes | Contract reports no raw archive, cursor, derived, network or remote Git writes and names `S07-P1-T2` next | PASS |

The real local metadata-only audit at `2026-07-15T12:15:15Z` returned PASS with metadata digest
`90bd0f6124a78d03ffcb57be0c72ae81b48c3b891015fbbf824034d1d5afb474`, 433 eligible files,
5 non-empty source kinds, 4,265,648,215 bytes and 7 excluded entries. These are volatile,
non-normative observations bound to that run; they are not acceptance thresholds.

## Validation

- Dedicated discovery tests: `9/9` PASS.
- Full Python suite: `456/456` PASS.
- `validate:fast`: `6/6` PASS.
- `validate:sync`: `7/7` PASS.
- `validate:ui`: `14/14` PASS.
- `validate:release`: `1/1` PASS; final audit completed tracked-only recovery.
- Privacy scan: PASS with zero high-risk or credential-like path findings and zero tracked raw/private files.
- The pre-review implementation candidate, before this review artifact was added, passed staged size audit with 22 entries, 1,536,516 unique object bytes, a 9,930,756-byte conservative upper bound, one batch and `single_commit_ready=true`. Final evidence-only additions are re-audited before commit.
- Python 3.13 and 3.12 deterministic renderer checks: PASS with zero drift or reference issues.

The supplemental root `validate_project_governance.py --project OpenAIDatabase` command is not
reported as PASS: this checkout intentionally uses sparse paths `.github`, `KMFA`, `OpenAIDatabase`,
`governance` and `scripts`, so the validator reported 35 missing sparse-excluded root templates and
project directories. The canonical project renderer is the applicable local gate here; full release
recovery separately proved the tracked repository can be reconstructed. This Task did not change
sparse-checkout configuration to manufacture a green result.

The focused fixture patches all common source content-read APIs and proves discovery still succeeds.
It also compares every fixture file's size, mtime and SHA-256 before and after discovery. Eligible
symlinks fail closed without changing their target.

## Independent Review And Remediation

The first engineering/security review found 0 Critical, 1 Important and 0 Minor: canonical evidence
referenced this review before the file existed. The first product/scope review found 0 Critical,
2 Important and 0 Minor: the same missing artifact plus volatile local counts without a timestamp and
digest anchor. This artifact closes the missing reference. Canonical governance now binds the local
observation to an exact UTC timestamp and metadata digest and labels it non-normative.

Product/scope second review closed at 0 Critical, 0 Important and 0 Minor. Engineering/security
second review closed the prior Important and found one Minor because the pre-review 22-entry size
audit was not clearly scoped after this artifact became entry 23. The validation line now identifies
that historical candidate explicitly and requires a final staged re-audit. The engineering/security
final spot review then closed at 0 Critical, 0 Important and 0 Minor. Both reviewers allow a local-only
commit and prohibit remote upload.

## Residual Boundaries

- Discovery does not prove content-level credential cleanliness; later archive work must run the
  canonical credential scan before public raw publication.
- Counts and metadata digest can change whenever Codex writes sessions or logs.
- Archive append-only semantics, source hash guards, dedupe, cursor and resume remain `S07-P1-T2/T3`.
- Local `main` remains divergent from the locally known `origin/main`; remote upload is prohibited
  until all 149 Tasks and final review/remediation are complete.

Before commit, unstage/reverse only the S07-P1-T1 patch. After the local commit, use `git revert` on
that Task commit; do not delete existing raw or source files as rollback.
