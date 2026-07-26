# Installation

## Inputs

- final ZIP and external SHA-256/receipt;
- locked Genesis anchor `14ab08b9053db4ca87140e59a49f1de8105a718a87ec2d55590c6487c1a77086`;
- operator-selected runtime Skill root;
- an external path for the CLI result file.

`~/.codex/skills` is only an example. Project-scoped Agent Skills commonly use `<project>/.agents/skills/teleiosis/`; follow the target runtime's documented root.

## Verification tiers

| Tier | Purpose | Executes Teleiosis code | Full regression |
|---|---|---:|---:|
| `structural` | generic package/internal staging | no for generic targets | no |
| `release` | normal final package/install | trusted `verify-self` + non-recursive `release-smoke` | package: once; install: no |
| `deep` | explicit pre-switch requalification | yes | install: once before switch |

`release-smoke` never calls the full suite and never recursively tests the installer through itself. This prevents test amplification while keeping archive, CLI, generic package/install, transaction and rollback primitives covered.

## Verify and install atomically

From an extracted trusted copy:

```bash
SKILLS_ROOT="/absolute/runtime-specific/skills-root"
ARCHIVE="/absolute/path/White-Box-Iteration-Skill-Teleiosis-v0.0.0.1-final.zip"
RESULT="/absolute/external/path/teleiosis-install-result.json"
GENESIS="14ab08b9053db4ca87140e59a49f1de8105a718a87ec2d55590c6487c1a77086"
ARCHIVE_SHA256="<copy from SHA256SUMS.txt>"

python3 scripts/wbi.py install "$ARCHIVE" \
  --skills-root "$SKILLS_ROOT" \
  --profile optimizer \
  --verification-level release \
  --result-file "$RESULT" \
  --expected-genesis-hash "$GENESIS" \
  --expected-archive-sha256 "$ARCHIVE_SHA256"

python3 scripts/wbi.py install-status \
  --skills-root "$SKILLS_ROOT" \
  --verify-installed \
  --profile optimizer \
  --expected-genesis-hash "$GENESIS"
```

For an existing install add `--replace`. The installer:

1. obtains a process-scoped, no-follow non-blocking root lock;
2. reconciles any interrupted transaction;
3. verifies the caller-supplied external SHA-256 trust anchor, then freezes the source ZIP to a private snapshot, verifies its before/copy/after hash and enforces an archive-byte ceiling;
4. safely extracts and validates only the frozen snapshot;
5. writes a private, durable transaction receipt;
6. freezes the predecessor tree hash before moving the prior install to a timestamped backup;
7. copies the incoming tree and verifies its hash;
8. atomically switches the canonical directory;
9. validates/smokes the installed copy;
10. commits the transaction and returns the rollback pointer.

It rejects symlinked archive, Skill root, destination, internal lock/transaction controls and rollback paths. New backup receipt schema 1.1 covers the manifest; legacy 1.0 receipts are accepted only through an explicit compatibility path. If interruption occurs after the predecessor rename but before its receipt is written, recovery may reconstruct that receipt only when the pre-frozen predecessor hash exactly matches the generated backup. An incomplete incoming copy is removed only when its parent and generated name are provably bounded to the same Skill root.

## Interrupted caller or missing stdout

Installation truth does not depend on the final terminal line. Query the durable receipt:

```bash
python3 scripts/wbi.py install-status \
  --skills-root "$SKILLS_ROOT" --verify-installed --profile optimizer \
  --expected-genesis-hash "$GENESIS"
```

If the latest transaction is non-terminal or ambiguous:

```bash
python3 scripts/wbi.py recover-install \
  --skills-root "$SKILLS_ROOT" --profile optimizer \
  --destination-name teleiosis \
  --expected-genesis-hash "$GENESIS"
```

Recovery commits only a strictly valid switched tree whose hash matches the receipt, or restores a valid generated backup. Ambiguous evidence remains `BLOCKED`.

## Rollback

Use the exact paths returned by installation:

```bash
python3 scripts/wbi.py rollback-install \
  --destination "/runtime/skills/teleiosis" \
  --backup "/runtime/skills/.teleiosis.backup.TIMESTAMP"
```

The backup name, destination identity, receipt schema and content hash must match. Arbitrary same-parent directories and modified backups are rejected.

## Manual placement

The ZIP has exactly one root: `teleiosis/`. Manual placement is allowed only when the runtime requires it. After placement run `verify-self --strict` with the external Genesis hash, then `release-smoke`. Do not rename the directory, create `teleiosis/teleiosis`, copy `.git`/cache files, auto-sign Genesis or delete the rollback backup before acceptance evidence is stored.
