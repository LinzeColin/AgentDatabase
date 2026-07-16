# Memory Atlas v1.2.1 S08-P2-T1 Notification Connector Review

## Scope and acceptance

- Task: `S08-P2-T1`
- Acceptance: `ACC-MA-V121-S08-P2-T1`
- Output: a pluggable read-only notification connector with at least one real adapter configured in the user environment.
- Selected adapter: `apple-mail-local`; Apple Mail delegates account credentials to macOS/OS Keychain. The connector never reads, receives or stores credential values.

This Task stops at transport readiness. OpenAI notification recognition, account/time/status validation, message-field inspection and one-time link extraction remain `S08-P2-T2` and are not implemented or claimed here.

## Implementation

`chatgpt-notification-connector --configure|--inspect` loads exact tracked contract/model files and dispatches through the standard `atlasctl` runtime. The adapter registry is explicit and currently contains one production adapter. A later adapter can implement the same bounded probe contract without changing CLI or result semantics.

The Apple Mail probe executes a fixed `/usr/bin/osascript` argv with `shell=false`, a ten-second timeout and an allowlisted child environment. Its only Mail operations are:

1. count configured accounts;
2. count enabled accounts;
3. verify that Inbox message count is readable.

It does not request account names, addresses, message ids, sender, subject, dates, body/source/content or links. Only one of four short readiness tokens is accepted; stderr and unknown stdout are discarded and mapped to path-free error codes.

A successful live `READY` probe is required before configuration. The adapter selection is atomically written outside the repository in a dedicated `0700` runtime directory and a `0600` JSON file. The file contains only schema, adapter id, read-only flag, credential policy and `stores_credentials=false`; it contains no Mail value, absolute path or secret. Reconfiguration is byte-idempotent and inspection is read-only.

## Real environment evidence

- Apple Mail application: available.
- Configured and enabled account: present, identity not read or emitted.
- Inbox count capability: readable, count not emitted.
- First command result: `CONFIGURED / READY / PASS`.
- Read-only follow-up: `INSPECTED_NO_CHANGES / READY / PASS`.
- Repeated configuration: `ALREADY_CONFIGURED / READY / PASS`.
- Machine-local config: 210 bytes, mode `0600`, SHA-256 `aee4abeb98e5fca795a62e67824842e3e0cf2f2b2aa9a0806237671ee2661cd8`.

No Mail value, account count, mailbox count, credential, local path or process stderr is retained in tracked evidence.

## Verification

- Test-first proof: the dedicated test initially failed with `ModuleNotFoundError: memory_atlas_cli.chatgpt_notification_connector`.
- Dedicated connector regression: `11/11 PASS`.
- ChatGPT P1/T1 plus CLI/profile focused regression: `102/102 PASS`.
- `validate:fast`: `6/6 PASS` in 29.266 seconds.
- `validate:sync`: `10/10 PASS` in 183.127 seconds; credential scan passed in 130.163 seconds.
- Both validator profiles report `raw_mutation=false`, `remote_push=false`, and `shell=false`.

The first fast-profile attempt failed only because the isolated worktree intentionally had `data/public_raw` and `data/raw_archives` unmaterialized. After applying the exact validation sparse layout, the unchanged implementation passed all six steps. Raw content was not modified.

## Safety and rollback

- No message metadata/content/link discovery, export download, raw write, Git remote action, branch, PR or deployment occurred.
- The local adapter config is runtime state, not a GitHub artifact. GitHub carries the connector source, exact contract, model parameters, tests and deterministic configure command needed to recreate it on a new machine after Apple Mail is configured.
- Rollback: revert the local Task commit and remove only the credential-free machine-local connector config. Never delete or alter Apple Mail accounts, Mail data or OS Keychain entries.

Result: `S08-P2-T1` is complete locally. `S08-P2-T2` is the next and only eligible Task in a later run.
