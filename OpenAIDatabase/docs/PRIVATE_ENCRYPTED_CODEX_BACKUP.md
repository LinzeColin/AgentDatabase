# Private Encrypted Codex Backup

`config/storage/private_encrypted_backup_policy.json` governs the scheduled, ciphertext-only Codex backup channel for the owner-controlled private `LinzeColin/Private-Database` Release surface.

## Boundary

- The target is private GitHub Release assets only. No payload, manifest, plaintext, source path, source file name, credential, or key material is Git tracked.
- The same approved public recipient policy supplies the one `key_id`; the corresponding private identity stays in macOS Keychain or an owner-controlled secret manager and is never copied to a file or this repository.
- Packaging streams through `gzip` and `age`. A plaintext archive is never persisted, and source deletion is never automatic.
- The scheduler may use only one fresh system temporary directory per run. The shared working directory, task worktrees, session records, and other thread state are read-only and must not receive scripts, staging files, locks, manifests, or persistent state.
- A private draft Release may be created only after every preflight passes. The job must verify the remote ciphertext hash and size before removing its own temporary ciphertext. Retention may affect only the three oldest completed automatic Releases with the `codex-auto-backup-` tag prefix; manual, draft, and nonmatching Releases are immutable to the job.

## Fail-Closed Operations

- If the approved private identity is unavailable, emit `ACTION: ESCALATE`; do not create a Release, retry automatically, create a follow-up task, or persist an executor state file.
- If a source snapshot is unstable or a remote hash differs, emit `ACTION: STOP` and leave remote state unchanged except for the already-created draft that requires owner review.
- This policy does not permit a local backup script, launchd item, login item, service, daemon, cron job, private repository clone, or any write into a shared Codex workspace.

## Validation

```sh
python3 -B scripts/validate_private_encrypted_backup_policy.py --database-dir . --require-ready
python3 -m unittest tests.test_private_encrypted_backup_policy -q
```

The checks are governance-only: they do not read Codex source content, access a private identity, create a Release, or upload an asset.
