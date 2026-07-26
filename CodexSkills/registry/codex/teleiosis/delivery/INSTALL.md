# Install — Teleiosis v0.0.0.2

Canonical archive:

```text
White-Box-Iteration-Skill-Teleiosis-v0.0.0.2-final.zip
```

## 1. Verify external anchors

```bash
BASE_GENESIS="14ab08b9053db4ca87140e59a49f1de8105a718a87ec2d55590c6487c1a77086"
EFFECTIVE_GENESIS="fe80c467f8ecbe8343ef0c09ef5e6f9fd9683803c8260c9188998c7e3dfca0a2"
ARCHIVE="/absolute/path/White-Box-Iteration-Skill-Teleiosis-v0.0.0.2-final.zip"
ARCHIVE_SHA256="<copy from the external SHA256SUMS file>"

shasum -a 256 "$ARCHIVE"
```

Do not obtain the expected archive hash from inside the archive itself.

## 2. Verify extracted source

```bash
python3 scripts/wbi.py verify-self --strict \
  --expected-genesis-hash "$BASE_GENESIS" \
  --expected-effective-genesis-hash "$EFFECTIVE_GENESIS"
python3 scripts/wbi.py self-test --timeout 900
```

## 3. Atomic release install

```bash
python3 scripts/wbi.py install "$ARCHIVE" \
  --skills-root /absolute/path/to/CodexSkills/registry/codex \
  --profile optimizer --verification-level release \
  --expected-genesis-hash "$BASE_GENESIS" \
  --expected-effective-genesis-hash "$EFFECTIVE_GENESIS" \
  --expected-archive-sha256 "$ARCHIVE_SHA256" \
  --result-file /absolute/external/install-result.json
```

Use `--replace` only for an explicit upgrade; the installer creates a content-bound predecessor backup and rollback command.

## 4. Inspect/recover/rollback

```bash
python3 scripts/wbi.py install-status --skills-root /absolute/path/to/registry/codex \
  --verify-installed --expected-genesis-hash "$BASE_GENESIS" \
  --expected-effective-genesis-hash "$EFFECTIVE_GENESIS" --profile optimizer

python3 scripts/wbi.py recover-install --skills-root /absolute/path/to/registry/codex \
  --expected-genesis-hash "$BASE_GENESIS" \
  --expected-effective-genesis-hash "$EFFECTIVE_GENESIS" --profile optimizer

python3 scripts/wbi.py rollback-install --destination <installed-path> --backup <receipt-bound-backup-path>
```

`structural` is suitable for local development. `release` is the normal install gate. `deep` additionally runs the full regression suite before the atomic switch.
