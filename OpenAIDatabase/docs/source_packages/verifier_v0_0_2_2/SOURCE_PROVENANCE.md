# Verifier Skill v0.0.2.2 Source Provenance

## Current conclusion

This directory publishes the latest Verifier v0.0.2.2 release as a
repository-portable, single-root ZIP. The package was supplied by the Owner
and received one metadata-only adaptation: the Codex interface display name
is now exactly `verifier skill v0.0.2.2`.

The machine-readable Skill identifier remains `verifier`, so natural-language
requests such as “验收一下” and the `$verifier` route continue to work. The
default external deliverable remains exactly one builder-ready
`*_acceptance_review_taskpack.zip`; internal evidence stays inside the sealed
run and is not emitted as separate default files.

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `verifier-skill-v0.0.2.2.zip` | 533,392 | `50b31394df54bb6433d0e4266afaafa2ff6820b8594c3ff0430c3cc9528eb1b1` |

The unmodified Owner-supplied input archive had SHA-256
`6ae909291e8419c045a9571918fbcc7b6171e11029fe55a1e068277bc4f932d2`.

## Install and verify

From the extracted `verifier-skill-v0.0.2.2` root, use the exact target root
you intend to update:

```bash
python3 -B install.py inspect --target-root "$CODEX_SKILLS_ROOT"
python3 -B install.py install --target-root "$CODEX_SKILLS_ROOT" --replace
python3 -B install.py verify --target-root "$CODEX_SKILLS_ROOT" --selftest
```

The installer performs manifest/checksum verification before payload execution,
stages atomically, and retains a managed backup when replacing an existing
installation. Use only the exact rollback path printed by the installer.

## Verification evidence

- Outer archive integrity: PASS; 135 members.
- Distribution validator and distribution wrapper: PASS.
- Verifier payload tests: 75/75.
- Installer tests: 14/14.
- Release-wrapper tests: 16/16.
- Isolated install and self-test: PASS.
- Post-install global verify and self-test: PASS.
- Release tree seal unchanged after all checks: PASS.
- Recursive archive safety: 0 unsafe paths and 0 symlinks.

One unit test contains a deliberately synthetic bearer-token-shaped string so
the evidence privacy guard can prove it blocks and redacts such data. It is a
public test fixture, not an account token or credential.

SHA-256 proves byte integrity, not publisher identity. Review the installer
and Skill source before trusting it in a global Codex environment.

## Public boundary

The package contains code, tests, templates, documentation, and redacted
validation material only. It contains no real credentials, account data,
browser state, private raw data, acceptance-run evidence, chat/session exports,
or machine-specific absolute paths.
