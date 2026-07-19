# Verifier v2.1 Product-Design-Aligned Source Provenance

## Current Conclusion

This directory publishes the reviewed verifier v2.1 incremental installer as
a small, repository-portable recovery source package. It contains the complete
v2.1 Skill payload, the exact v2 baseline fixture, the fail-closed installer,
tests, research notes, and installation verification records.

The installer applies only to the exact v2 baseline recorded in
`PATCH_MANIFEST.json`. Unknown, partial, or already modified targets are
rejected rather than merged.

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `verifier-v2.1-product-design-aligned-single-review.zip` | 196,507 | `170272ac6a59faa5e72fe93f231e5103cb8431dc59c69709ff6f236786d38285` |

## Product Behavior Preserved

For the ordinary request “验收一下”, verifier still performs the full
evidence-driven acceptance workflow internally. Its default external file
deliverable is exactly one `*_acceptance_review_taskpack.zip`, designed to be
handed directly to a development agent for remediation and re-review.

This packaging rule does not convert unrun, blocked, thresholdless, or
unauthorized checks into PASS. Production load, concurrency, fault injection,
active security scans, and destructive data operations remain authorization
gated.

## Inspection And Upgrade Sequence

After downloading and checking `SHA256SUMS`, extract the archive and enter its
single root directory. For an existing exact v2 installation, use:

```bash
python3 -B apply_patch.py --json inspect \
  --target "$HOME/.codex/skills/verifier"
python3 -B apply_patch.py --json apply \
  --target "$HOME/.codex/skills/verifier" --dry-run
python3 -B apply_patch.py --json apply \
  --target "$HOME/.codex/skills/verifier"
```

The archive also carries the complete v2.1 payload under `payload/`, so the
reviewed files remain recoverable even when the original local installer and
rollback copy are removed. Validate that payload before any manual recovery:

```bash
python3 -B payload/scripts/validate_pack.py --json payload
python3 -B -m unittest payload.tests.test_tools -q
```

## Verification Evidence

- Outer ZIP integrity and every embedded checksum passed.
- Recursive archive safety scan found 0 unsafe paths and 0 symlinks.
- Public-content scan found 0 machine-specific path or credential patterns.
- Installer tests passed 7/7; payload tests passed 35/35.
- An isolated exact-v2 inspect, dry-run, apply, v2.1 inspect, and post-apply
  payload validation all passed.

SHA-256 proves byte integrity, not publisher identity. Review the installer
and Skill source before trusting them in a global Codex environment.

## Public Boundary

This source package contains code, tests, templates, documentation, and
redacted validation output only. It contains no acceptance-run evidence, user
or account data, prompts, response history, cookies, tokens, credentials,
browser state, private raw data, or machine-specific absolute paths.
