# Memory Atlas v1.2.1 S08-P2-T2 Export Link Discovery Review

## Scope and acceptance

- Task: `S08-P2-T2`
- Acceptance: `ACC-MA-V121-S08-P2-T2`
- Output: identify an official OpenAI export notification, verify state, account and time, then keep exactly one validated link outside Git.

This Task implements and verifies the link-discovery path. It does not download a ZIP, write raw archives, push, deploy or start `S08-P2-T3`.

## Implementation

`chatgpt-export-link` adds three bounded modes:

1. `--bind-account-from-env` normalizes the account only in process memory and stores a random salt plus digest in the configured repository-external runtime;
2. `--inspect` reads no Mail content and reports whether the durable export state is eligible;
3. `--discover` runs only from `WAITING_FOR_EXPORT`, rechecks the configured T1 adapter, scans a fixed recent Mail window and advances to `LINK_READY` only after one candidate passes every check.

The Apple Mail program is a fixed `osascript` argv with `shell=false`, a 15-second timeout, an allowlisted child environment, at most eight official-sender candidates and at most 512 KiB per source. The script and Python result never print sender, recipient, subject, body, account or URL values. The source exists only in process memory.

Validation requires the current documented sender `noreply@tm.openai.com`, ChatGPT/data/export plus ready/download subject markers, a recipient matching the machine-local salted account binding, a message time after the tracked request and no more than seven days later, a still-live 24-hour window, and one first-party HTTPS `openai.com` or `chatgpt.com` export/download URL. Missing, invalid or multiple candidates fail closed.

The actual URL is atomically stored only in a mode `0600` runtime file outside the repository. Tracked export state records only a SHA-256 evidence digest. If the private write succeeds and the state write fails, a later retry recognizes the same request/link/source/account record and completes the transition without replacing it.

## Current live boundary

The canonical production state is still `IDLE / revision 0`, SHA-256 `da9b7f188ad0da9cb3dd482748b2d44ddfc65c4fc340b1214ad21d0a36b78aa3`. No production export request exists in this state.

- `chatgpt-export-link --inspect`: `PASS / STATE_NOT_ELIGIBLE / IDLE`.
- `chatgpt-export-link --discover`: `FAIL_CLOSED / link_discovery_state_not_eligible`.
- Mail message-source reads: `0`.
- Production account binding file: absent.
- Production private link file: absent.
- Production link discovered: no.

This is intentional fail-closed behavior, not evidence of a real export email. A future legitimate `WAITING_FOR_EXPORT` cycle must establish the account binding and execute discovery before T3 can load the private URL.

## Verification

- Test-first proof: the dedicated test initially failed with `ModuleNotFoundError: memory_atlas_cli.chatgpt_export_link_discovery`.
- Dedicated regression: `12/12 PASS`, including state-write fault injection and retry recovery.
- ChatGPT P1/P2 plus CLI/profile focused regression: `94/94 PASS`.
- The fixed AppleScript compiled with macOS `osacompile` without executing Mail.
- `validate:fast`: `6/6 PASS` in 22.861 seconds.
- `validate:sync`: `10/10 PASS` in 184.549 seconds; 260 sync tests passed and the credential scan passed in 130.230 seconds.
- Both profiles report `raw_mutation=false`, `remote_push=false`, and `shell=false`.
- Human-plane and test-value audits, 49 human/test-value/script-migration regressions, deterministic render check and required project governance all pass. Machine truth is 172 files, 40 active configs and 130 evidence payloads; 53 governance events are valid JSONL.

The first fast/sync attempts exposed only isolated-worktree prerequisites: excluded raw roots, a stale audit-script hash after registering the new test, less than the restore-proof 1 GiB free-space floor, and absent/out-of-root Vite dependencies. The final runs used materialized tracked raw plus a task-owned local dependency clone and passed unchanged product logic. No raw byte was modified.

## Safety and rollback

- No real Mail body, account identity, credential or one-time URL entered Git, stdout, machine evidence or the review.
- The repository contains only synthetic test fixtures; no production notification was scanned.
- GitHub recovery includes source, exact contract/model, tests and deterministic commands. Machine-local account binding and link files must be recreated from the user environment and are intentionally not portable secrets.
- Rollback: revert the local Task commit and remove only this Task's private account-binding/link files if they exist. Never alter Apple Mail, OS Keychain or user messages.

Result: `S08-P2-T2` is complete locally as an implemented and fixture-verified capability with a live `IDLE` zero-scan gate. `S08-P2-T3` is the next and only eligible Task in a later run.
