# Memory Atlas v1.2.1 S08-P2-T3 Export Download Review

## Scope and acceptance

- Task: `S08-P2-T3`
- Acceptance: `ACC-MA-V121-S08-P2-T3`
- Output: download one validated, account-bound export link into a private ZIP, verify the ZIP, and make retries hash-idempotent.

This Task implements the private download capability. It does not parse the export, write the P3 public raw archive, commit raw data, push, deploy or claim that a production export has already been downloaded.

## Implementation

`chatgpt-export-download` has two bounded modes. `--inspect` is read-only and uses no network. `--download --confirm-download` is permitted only from `LINK_READY`; it revalidates the T2 request id, salted account digest and link lifetime before starting the download. A noneligible state exits before private runtime access or network activity.

The transport performs a standard-library HTTPS GET with ambient proxies disabled and no browser cookie, browser profile, `Authorization`, proxy authorization or credential access. The initial and redirected targets must remain HTTPS global hostnames with no userinfo, IP literal, local/private address or protocol downgrade. Redirect count, socket timeout, total duration, stream chunk size, response bytes and a 512 MiB disk reserve are bounded by the exact T3 model.

The response is streamed to a unique `0600` partial file inside a repository-external `0700` directory. Validation rejects oversized, malformed, encrypted, symlinked, unsafe-path, Unicode/case-duplicate and excessive-ratio members; it requires at least one `conversations.json` or numbered variant and verifies CRC for every member without extraction. The final filename is `chatgpt-export-{zip_sha256}.zip`.

Private metadata stores request/link/account digests, ZIP hash, byte/member counts and a relative private filename, never the URL, raw account, absolute path or ZIP bytes. If the ZIP and metadata are durable but the tracked state write fails, a retry validates and reuses the existing file, including after link expiry, then advances `LINK_READY` to `DOWNLOADED` without a second network call. Repeating the command from `DOWNLOADED` is also zero-network and never creates a second file for the same hash. `load_private_downloaded_export` is the only downstream in-process path for P3 to obtain the verified private ZIP; CLI output remains sanitized.

## Current live boundary

The canonical production state remains `IDLE / revision 0`, SHA-256 `da9b7f188ad0da9cb3dd482748b2d44ddfc65c4fc340b1214ad21d0a36b78aa3`.

- `chatgpt-export-download --inspect`: `PASS / STATE_NOT_ELIGIBLE / IDLE`.
- Private runtime reads on that path: `0`.
- Network download attempts: `0`.
- Production private ZIP or download metadata: absent.
- Production export downloaded: no.

This is the required live fail-closed result because no production request or T2 private link exists. The Task is accepted as an implemented and fixture-verified downloader; `S08-P3-T3` remains responsible for one genuine official export end-to-end proof and must stay waiting if OpenAI has not produced it.

## Verification

- Test-first: the dedicated module initially failed with `ModuleNotFoundError: memory_atlas_cli.chatgpt_export_download`.
- Dedicated regression: `11/11 PASS`.
- ChatGPT P1/P2, CLI, profile, test-value and script-migration focused regression: `102/102 PASS`.
- Production modules compile with `py_compile`.
- The live IDLE inspect command passes without private or network effects.
- `validate:fast`: `6/6 PASS` in `31.879s`.
- Final `validate:sync`: `10/10 PASS` in `466.111s`; sync unit tests passed in `106.110s` and the complete credential scan passed in `347.133s`. The profile reports `raw_mutation=false`, `remote_push=false` and `shell=false`.

The fixture matrix covers exact contract/model drift, IDLE zero-access, successful private download, account mismatch, expiry, invalid ZIP retry, state-write interruption, recovery after expiry, repeated zero-network execution, unsafe/duplicate/missing members, disabled proxy/cookie/auth transport and private-host rejection. It does not substitute fixture bytes for a real export claim.

The first full-profile attempt correctly rejected `.DS_Store` files introduced into the task-owned CoW validation copy. The second reached the historical Codex archive gate and exposed a pre-existing truncated part in the shared checkout. The Git object for that tracked part remained complete and manifest-identical, so only the task-owned validation copy was restored from `HEAD`; the shared checkout and source data were not changed. The final full profile then passed all ten gates. This prerequisite incident is not counted as product implementation progress and should be considered when creating another validation worktree from the shared checkout.

## Findings, safety and rollback

Review findings after remediation: `0 Critical / 0 Important / 0 Minor` in the current implementation scope. The review closed logical ZIP path collisions and made the disk reserve an actual byte budget rather than a start-only observation.

- No real account, one-time link, ZIP, browser state, cookie or credential entered Git, stdout, evidence or this review.
- No raw/public-raw/archive file was materialized or changed.
- Rollback: revert only the local T3 commit and delete only T3-owned unverified partial files. Preserve any verified private ZIP and metadata until the owner deliberately archives or discards them; never touch browser profiles, Keychain, Mail or shared caches.

Result: `S08-P2-T3` is complete locally as a private, retryable and hash-idempotent downloader with a truthful live `IDLE` gate. `S08-P3-T1` is the next and only eligible Task in a later run.
