# Genesis Constitution

- `GENESIS_SOURCE...` is the exact uploaded candidate baseline.
- `GENESIS_LOCKED...` differs only by the user-authorized status transition to `LOCKED_GENESIS`.
- `genesis-lock.json` binds source, locked baseline, requirement order and hashes.
- `requirements.json` is a machine-readable projection; the locked Markdown remains authoritative.
- No script may auto-resign or silently rewrite Genesis.
- Strong tamper detection requires the external release receipt or registry anchor supplied with the release.
