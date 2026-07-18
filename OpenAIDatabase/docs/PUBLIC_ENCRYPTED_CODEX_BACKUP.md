# Public Encrypted Codex Backup

This repository may publish a ciphertext-only backup of Codex memories and session records only when
`config/storage/public_encrypted_backup_policy.json` is `READY` and every required preflight passes.

## Boundary

- Public GitHub carries Release assets only; no ciphertext, plaintext, source files, key material, or
  source-path manifest is Git tracked.
- The public asset is encrypted with `age-x25519-v1`. One active `key_id` governs all batches; the private
  identity stays in macOS Keychain or an owner-controlled secret manager and is never exported to this repo.
- Source packaging must stream directly into encryption. A plaintext archive must never be persisted.
- The public manifest may contain only the policy-approved batch, key, ciphertext-hash, and part metadata.
- R8 must pass before upload. Local source deletion is never automatic.

## Provisioning Gate

The checked-in policy intentionally starts as `UNPROVISIONED`. Provisioning requires a public `age` recipient
and its SHA-256 fingerprint, plus an independently recoverable private identity in the approved key store.
Until then, `--require-ready` must fail and no automation may upload anything.

## Validation

```sh
python3 -B scripts/validate_public_encrypted_backup_policy.py --database-dir .
python3 -m unittest tests.test_public_encrypted_backup_policy -q
```

These checks validate governance only. They do not read Codex session content, generate key material, or upload
an asset.
