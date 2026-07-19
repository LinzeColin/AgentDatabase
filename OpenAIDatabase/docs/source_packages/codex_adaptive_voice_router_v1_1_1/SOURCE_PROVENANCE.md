# Codex Adaptive Human Voice Router v1.1.1 Source Provenance

## Current Conclusion

This directory publishes the reviewed v1.1.1 installer as a small,
repository-portable source package. The archive is intended for a global
Codex Hook-only installation:

```bash
python3 install.py --no-skill
```

The recommended path does not modify `~/.codex/config.toml` and does not
install the optional Skill.

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `codex-adaptive-human-voice-router-v1.1.1.zip` | 31,551 | `f4e46d9e281b69c7cbc25f333933ab9c24772ae1fc476e300badf47fa6202449` |

## Source And Changes

The package was derived from the user-supplied v1.1.0 archive with SHA-256
`d14fd4a095477235d56c13b722db45d7fd0ba11fc8c92ef21713e52ca12de994`.
The reviewed v1.1.1 delta is intentionally narrow:

- `max_discourse_markers` defaults to JSON `null`, meaning no fixed numerical
  maximum. A numeric value remains supported as a backward-compatible cap.
- The voice contract now asks for a visible but context-sensitive natural
  bridge in ordinary conversation, explanation, debugging, decision and
  creative responses. It forbids filler and quota-driven catchphrases.
- `--no-skill` is the documented safe default; `--configure-codex` remains
  optional and is not required for Hook-only operation.
- The stale generated PDF and its report generator were excluded from the
  distributable; `REPORT.md` is the canonical report.

## Verification Evidence

- ZIP integrity check: passed.
- Unsafe member path and symlink check: 0 findings across 25 ZIP entries.
- Embedded file checksums: 18/18 matched.
- Package acceptance tests: 14/14 passed.
- Public-content scan: no credentials, chat/session exports, private raw data,
  browser state or local absolute paths found.

SHA-256 proves byte integrity, not publisher identity. Review the Hook source
and definitions before trusting them in Codex.

## Public Boundary

This source package contains only code, tests, examples and documentation. It
does not contain user prompts, response history, account data, cookies,
tokens, credentials or machine-specific configuration.
