# Memory Atlas v1.2.1 S08-P3-T1 Export Archive Review

## Scope and current result

- Task: `S08-P3-T1`
- Acceptance: `ACC-MA-V121-S08-P3-T1`
- Result: `PARTIAL_WAITING_REAL_EXPORT`
- Project count: `60/149`, unchanged

The append-only ChatGPT export archive capability is implemented and covered by synthetic regression. The current production state is `IDLE`, so no real private export ZIP was available and no production ChatGPT archive was written. This review does not close the Task and does not make `S08-P3-T2` eligible.

## Implementation

`atlasctl chatgpt-export-archive` supports read-only `--inspect` and explicitly confirmed `--archive --confirm-archive`. A noneligible state exits before private runtime or raw archive access. An eligible run accepts only the verified repository-external ZIP returned by `load_private_downloaded_export`, binds request and download metadata to tracked state, and uses `chatgpt-export-{download_sha256}` as the archive identity.

The S06 chunk contract now supports an explicit forced archive for packages at or below 45 MiB while preserving the old default no-copy behavior. Larger packages retain deterministic 45 MiB parts. The S06 restore verifier must reproduce the exact package hash and byte size before a request-specific public provenance index is written. That index excludes private paths, raw account values and the one-time URL, enters the immutable public-raw ledger, and supplies the evidence hash for the final `DOWNLOADED -> ARCHIVED` transition.

Replaying `ARCHIVED` does not call the private loader. A state-write failure after archive/index publication is retryable without rewriting either artifact. A later request for the same download hash reuses one archive and appends separate request provenance.

## Live boundary

The tracked state remains `IDLE / revision 0`, SHA-256 `da9b7f188ad0da9cb3dd482748b2d44ddfc65c4fc340b1214ad21d0a36b78aa3`. Live inspect returns `STATE_NOT_ELIGIBLE`, with zero private runtime reads, zero raw reads and no raw writes. There is no production private ZIP, ChatGPT archive, P3 public index or new P3 raw-ledger row.

Synthetic fixtures prove implementation behavior only. They cannot satisfy the TaskPack requirement to archive one real official export batch with request and download provenance.

## Verification and safety

- Dedicated archive regression: `9/9 PASS`.
- Archive chunking/restore/raw fixture regression: `31/31 PASS`.
- Source registry, modular CLI and archive regression: `30/30 PASS`.
- Final focused related regression: `175/175 PASS`.
- `ruff` and Python compile checks: `PASS` for changed production and test modules.
- `validate:fast`: `6/6 PASS` in `29.217s`.
- `validate:sync`: `10/10 PASS` in `194.608s`, including sync unit tests in
  `50.485s` and the complete credential scan in `137.382s`; the profile reports
  `raw_mutation=false`, `remote_push=false` and `shell=false`.

No production raw/archive data, private ZIP, absolute private path, account value, URL, cookie, credential or browser profile entered tracked output. No fetch, push, deploy, branch, PR, merge or rebase occurred.

## Stop condition

`S08-P3-T1` remains the only eligible Task. A later continuation must first move the real export lifecycle through request, notification discovery and verified download, then run the archive command and verify the resulting archive, public provenance and ledger. Until then, completion remains prohibited.
