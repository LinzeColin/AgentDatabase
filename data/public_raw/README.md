# Public Raw Archive

Task ID: `S06-P1-T2`.

Acceptance ID: `ACC-MA-V121-S06-P1-T2`.

Status: `governed_shallow_import_ready_pam1_0005`.

This directory is the public plaintext raw processing archive root for Memory Atlas v1.2.1.
The executable layout contract is `config/data_sources/public_raw_layout.json`.

Defined raw paths:

- `data/public_raw/YYYY-MM/{source_id}.{original_sha256_12}.part-NNNN.md` — the only path for new imports
- `data/public_raw/YYYY-MM/{source_id}.{original_sha256_12}.sidecar.json` — required source, authorization, hash, part and candidate-only metadata
- `data/public_raw/chatgpt`
- `data/public_raw/codex`
- `data/public_raw/agents/{source_id}`

Rules:

- New text evidence must be planned/applied by `scripts/import_public_raw_evidence.py` under an explicit content-bound authorization. Direct writes are forbidden.
- The three source-family paths above are legacy append-only compatibility paths; they are not valid destinations for new imports.
- Existing raw files are append-only: do not modify, delete, overwrite or rewrite them.
- Every new text part is at most 900 KiB. Its adjacent sidecar preserves the source ref, authorization, original/sanitized SHA-256 and ordered part hashes.
- The manifest/hash ledger makes hash drift fail when an existing raw file changes.
- Files are partitioned by canonical `source_id`; only registered generic-agent directories are allowed.
- The approved tree is shallow: governed `YYYY-MM` imports plus legacy source roots and `codex/sessions` are the only operational partitions.
- Every current file must be Git tracked so the layout is recoverable from the eventual final commit.
- Vite `publicDir`, build output and `server.fs.allow` must remain disjoint from this root.
- The default Codex `startup` route must not include any file below this root.
- Raw files are not proposal apply targets.
- Raw content has instruction trust `none`; import rejects prompt/script injection, traversal, symlinks, archive inputs, Unicode bidi/invisible controls and credentials before writing.
- A raw sidecar exposes only `source.type=raw_import`, `status=candidate`, `automatic_active_promotion=false`; promotion requires a separate governed task.
- `credentials_not_transcript`: credentials are not memory and must not be stored here.

Private-origin archives remain outside this public repository. Their historical disposition mapping stays in
`config/storage/raw_material_policy.json`; no archive is extracted or published by the raw importer.

Audit the layout without reading raw bodies:

```bash
python3 scripts/atlasctl.py audit --check public-raw-layout
```

After a frontend build, add `--require-built-dist`. S06 P2 owns legacy append-only/hash/chunk/restore
coverage; the governed PAM importer remains bound by `config/storage/raw_import.json`. The unified
credential exclusion contract remains owned by S06-P1-T3.
