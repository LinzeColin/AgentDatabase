# Public Encrypted Codex Backup

This repository may publish a ciphertext-only backup of Codex memories, session records, and session attachments only when
`config/storage/public_encrypted_backup_policy.json` is `READY` and every required preflight passes.

## Boundary

- Public GitHub carries Release assets only; no ciphertext, plaintext, source files, key material, or
  source-path manifest is Git tracked.
- The public asset is encrypted with `age-x25519-v1`. One active `key_id` governs all batches; the private
  identity stays in macOS Keychain or an owner-controlled secret manager and is never exported to this repo.
- Source packaging must stream directly into encryption. A plaintext archive must never be persisted.
- The public manifest may contain only the policy-approved batch, key, ciphertext-hash, and part metadata.
- The historical R8 Memory Atlas product-release acceptance is not applicable to this separate backup channel;
  the checked-in owner override is narrow and does not weaken encryption, unified-key, Release-only, remote-hash,
  or no-source-deletion controls. Local source deletion is never automatic.

## Provisioning Gate

The policy starts as `UNPROVISIONED` before key provisioning. Provisioning requires a public `age` recipient
and its SHA-256 fingerprint, plus an independently recoverable private identity in the approved key store; only
then may it be committed as `READY`. Until then, `--require-ready` must fail and no automation may upload anything.

## Future Automation Contract (Not Scheduled)

No Codex automation is created by this change. Any future job must validate this policy, encrypt the three logical
source groups through a streaming `tar | gzip | age` pipeline with the checked-in public recipient, publish only a
temporary `.age` asset and allowed-field manifest to a GitHub Release, fetch the remote GitHub asset metadata to
verify its server-calculated hash and size, and only then remove its local ciphertext. It must never persist a
plaintext archive, use a different recipient, publish a path/name/content-bearing manifest, or delete original
Codex data.

## Validation

```sh
python3 -B scripts/validate_public_encrypted_backup_policy.py --database-dir .
python3 -m unittest tests.test_public_encrypted_backup_policy -q
```

These checks validate governance only. They do not read Codex session content, generate key material, or upload
an asset.
