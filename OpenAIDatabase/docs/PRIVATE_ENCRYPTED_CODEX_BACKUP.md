# Private Encrypted Codex Backup

`config/storage/private_encrypted_backup_policy.json` governs the scheduled, ciphertext-only Memory Atlas source backup channel for the owner-controlled private `LinzeColin/Private-Database` Release surface.

## Boundary

- Raw payload bytes and ciphertext are private GitHub Release assets only. The private Git tree may contain the separately verified JSON fact bundle and a non-sensitive Release receipt; plaintext raw payloads, ciphertext, credentials, and key material are never Git tracked.
- The same approved public recipient policy supplies the one `key_id`; the corresponding private identity stays in macOS Keychain or an owner-controlled secret manager and is never copied to a file or this repository.
- Packaging streams through `gzip` and `age`; every ciphertext part is at most 90 MiB. A plaintext archive is never persisted, and source deletion is never automatic.
- The scheduler may use only one fresh system temporary directory per run. Runtime SQLite, work snapshots, remote readback, ciphertext parts, and isolated restore output all stay inside that directory and are removed on success, failure, or bounded timeout. The shared working directory, task worktrees, session records, and other thread state remain read-only.
- A private draft Release may be created only after local preflight and source-integrity checks pass. The job must verify every remote ciphertext hash and size, perform an isolated hash-exact restore with the Keychain identity, then publish. Retention affects only completed automatic Releases with the `memory-atlas-auto-backup-` tag prefix and keeps the latest three; manual, draft, and nonmatching Releases are immutable to the job.
- The current key is `agentdatabase-public-backup-v2`; it supersedes v1 without deleting or overwriting the historical key identity or assets.

## Fail-Closed Operations

- If the approved private identity is unavailable, fail before creating a Release; do not retry automatically, create a follow-up task, or persist an executor state file.
- If a source snapshot is unstable or a remote hash differs, emit `ACTION: STOP` and leave remote state unchanged except for the already-created draft that requires owner review.
- This policy does not permit an Auto-generated/untracked local backup script, launchd item, login item, service, daemon, cron job, private repository clone, or any payload write into a shared Codex workspace. The only executor is the reviewed repository entrypoint `scripts/memory_atlas_source_capture_entry.py`.

## Validation

```sh
python3 -B scripts/validate_private_encrypted_backup_policy.py --database-dir . --require-ready
python3 -m unittest tests.test_private_encrypted_backup_policy -q
```

The checks are governance-only: they do not read Codex source content, access a private identity, create a Release, or upload an asset.
