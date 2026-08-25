# Codex Task Pack v0.0.0.1

## Goal

Install and register the supplied `teleiosis/` package exactly as delivered. Codex does not repeat research, redesign the Skill, rewrite Genesis, manufacture independent-review evidence or choose a different architecture.

## Inputs

- `White-Box-Iteration-Skill-Teleiosis-v0.0.0.1-final.zip`;
- external release receipt and SHA-256 list;
- locked Genesis anchor `14ab08b9053db4ca87140e59a49f1de8105a718a87ec2d55590c6487c1a77086`;
- operator-approved Registry and Skill installation roots.

## Actions

1. Verify archive SHA-256 against the external receipt and SHA-256 list.
2. Safely extract to a temporary path; require one top-level `teleiosis/` directory and no traversal, duplicate, symlink, device, cache, `.git`, secret or nested Skill root.
3. Run `verify-self --strict --expected-genesis-hash 14ab08b9053db4ca87140e59a49f1de8105a718a87ec2d55590c6487c1a77086`.
4. Confirm the supplied release evidence records one complete post-extract regression run for the exact archive tree; do not rerun it merely to duplicate evidence. Use `deep` only when local policy requires pre-switch requalification.
5. Install atomically with `--profile optimizer --verification-level release --result-file <external-path>`; use `--replace` only when preserving an existing install as a backup.
6. Run `install-status --verify-installed`; if the caller was interrupted or a transaction is non-terminal, run `recover-install` and do not infer success from directory presence alone.
7. Retain the exact transaction ID, result file and rollback pointer. Verify rollback in an isolated acceptance root before deleting any prior backup.
8. Store the release receipt, Genesis anchor, archive hash, install transaction, test evidence and formal-promotion status in Registry/run-log metadata.
9. Do not push, merge, tag, publish, deploy or delete prior releases without separate authorization.

## Acceptance

- engineering archive and install status: PASS;
- strict validation and bundled tests: PASS;
- post-install verification: PASS;
- deterministic archive claim reproduced;
- previous installation preserved when replaced;
- no unrecorded mutation.

The absence of a trusted independent-review runtime may leave **formal autonomous promotion** as `BLOCKED` while engineering installation remains PASS. Codex must preserve that distinction and must not convert role simulations into approval evidence.

## Stop conditions

Hash/Genesis mismatch, unsafe archive member, test failure, missing install root, permission failure, invalid Registry path or inconsistent receipt: return `BLOCKED` with raw evidence; do not improvise a bypass.
