# Current reconstruction and expected-block contract

## Purpose

R11 proves that current `calculate` fails closed for the exact current evidence gaps. It does not make missing data look complete, does not compare against reference totals to manufacture a delta, and does not grant production authority.

The production command and regression harness are separate trust paths:

1. private preparation verifies the sealed Task Pack and current read-only inventory, reviews source drift, and freezes a current-source contract plus an expected-block contract;
2. production reads only the current-source contract and returns its real status/exit code;
3. the harness reads the already frozen expectation after production and returns 0 only for an exact match.

Production must never import the harness, expected-block contract, private reference baseline, PDF line items or replay adapter.

## Pre-run sufficiency and source checks

Before business calculation, production requires:

- a new absolute private output directory outside the raw input root;
- exact current-source contract digest, input root and as-of binding;
- exact metadata fingerprint, entry count, size total and unsafe-entry count;
- a full digest match for every selected non-reference calculate source;
- both actual-cost bases: `JOB_COST_INCURRED` and `GL_RECOGNIZED_COGS`;
- all evidence requirements below.

Every unresolved item is `NON_WAIVABLE` while its affected Metric remains in scope. The output prompt offers: supplement, qualified alternate evidence, explicit scope reduction or remain blocked. Silence is not permission; optional-display omission cannot waive a source, identity, policy, formula, security or reconciliation gate.

## Reviewed current blocker contract

The current full-scope expectation contains exactly these generic public-safe codes:

```text
ACCOUNTING_BASIS_POLICY_MISSING
CAPITAL_INTEREST_POLICY_MISSING
CURRENT_INPUT_MANIFEST_V3_MISSING
FULLY_LOADED_PAYROLL_POLICY_MISSING
KINGDEE_READER_PROFILE_MISSING
PAYMENT_PROJECT_MAPPING_CONFLICT
PAYROLL_AND_TIME_SOURCE_MISSING
PROJECT_IDENTITY_EVIDENCE_CONFLICT
PROJECT_TAX_POLICY_OR_DIRECT_LEDGER_MISSING
```

These are a frozen R11 regression expectation, not universal defaults. If any code, evidence status, source digest or current inventory binding changes, the harness must fail and require review. It cannot update the expectation automatically.

If every frozen evidence requirement becomes present, the R11 regression entry raises `CURRENT_R11_EXPECTATION_STALE` before publishing a success-shaped result. The old expected-block contract must be retired. The caller then runs the governed normal calculate pipeline; if its complete source, calculation, reconciliation and output gates pass, R9 generates the final workbook immediately.

The legacy observation that one account total does not reconstruct a reference report is excluded from calculate blockers. It is reference comparison evidence only and cannot seed, repair or backsolve current values.

## Source drift

The sealed package snapshot and current raw inventory are compared by full digest multiset and by every governed slot. A drift can be accepted for R11 only when all slot candidate digest multisets remain exact and the changed inventory items match no slot. The review records counts/fingerprints, classification and `snapshot_overwritten=false`.

In-scope slot drift, unsafe input or an unreviewed fingerprint change blocks preparation/production. Old snapshots are immutable; a new reviewed contract must be written to a new private directory.

## Production versus harness status

The production current run returns exit `3` and writes:

```text
execution_status=NEEDS_USER_INPUT
input_readiness_status=BLOCKED_NON_WAIVABLE
calculation_status=BLOCKED_SOURCE
generation_status=BLOCKED_DIAGNOSTICS_GENERATED
```

It emits no workbook and no `INTERNAL_PROCESS_HANDOFF.md`.

The harness may return exit `0` only when production exit `3`, all four production status planes, the exact blocker list, source binding set, request binding, output index, detached seal and calculate data-flow boundary match. Its execution label is `EXPECTED_BLOCKED`; that means the test passed, not that calculation passed.

## Copyable three-step R11 workflow

Run all commands from the Skill root. Every output directory below must be an absolute, new, non-existing private path. Preparation must finish before either production command; copy the two contract SHA256 values printed by preparation without editing either contract.

### 1. Prepare and freeze both contracts

```bash
python3 scripts/prepare_current_regression.py \
  --task-pack-root /ABSOLUTE/SEALED/TASK_PACK_ROOT \
  --input-root /ABSOLUTE/READ_ONLY/INPUT_ROOT \
  --output-dir /ABSOLUTE/PRIVATE/NEW_BINDING_DIR \
  --contract-id <NEW_CONTRACT_ID> \
  --as-of YYYY-MM-DD
```

Expected exit is `0`. The terminal JSON prints the absolute current-source and expected-block contract paths plus both SHA256 values.

### 2. Run production directly once

```bash
python3 scripts/run_current_source_reconstruction.py \
  --run-id <NEW_DIRECT_PRODUCTION_RUN_ID> \
  --input-root /ABSOLUTE/READ_ONLY/INPUT_ROOT \
  --current-source-contract /ABSOLUTE/PRIVATE/NEW_BINDING_DIR/current_source_contract.private.json \
  --current-source-contract-sha256 <CURRENT_SOURCE_CONTRACT_SHA256> \
  --as-of YYYY-MM-DD \
  --output-dir /ABSOLUTE/PRIVATE/NEW_DIRECT_PRODUCTION_OUTPUT_DIR
```

Expected exit is `3`: this is the real business result `BLOCKED_SOURCE`, not a command failure to hide or convert to zero.

### 3. Run the independent exact-match harness

```bash
python3 scripts/validate_current_expected_block.py \
  --run-id <NEW_HARNESS_PRODUCTION_RUN_ID> \
  --input-root /ABSOLUTE/READ_ONLY/INPUT_ROOT \
  --current-source-contract /ABSOLUTE/PRIVATE/NEW_BINDING_DIR/current_source_contract.private.json \
  --current-source-contract-sha256 <CURRENT_SOURCE_CONTRACT_SHA256> \
  --expected-block-contract /ABSOLUTE/PRIVATE/NEW_BINDING_DIR/expected_block_contract.private.json \
  --expected-block-contract-sha256 <EXPECTED_BLOCK_CONTRACT_SHA256> \
  --as-of YYYY-MM-DD \
  --production-output-dir /ABSOLUTE/PRIVATE/NEW_HARNESS_PRODUCTION_OUTPUT_DIR \
  --harness-output-dir /ABSOLUTE/PRIVATE/NEW_HARNESS_OUTPUT_DIR
```

The harness does **not** inspect the direct-production directory from step 2. It launches a second production run into its own new `--production-output-dir`, then validates that run against the already frozen expectation. Harness exit `0` means exact `EXPECTED_BLOCKED` regression behavior and remains `NO_GO_PRODUCTION`; exit `1` means expectation mismatch and requires review. Other nonzero exits are preparation, production-contract or atomic-publication failures and must retain their emitted diagnostics.

## Output location and company-process boundary

Preparation, production and harness each atomically publish a new no-overwrite directory with `OUTPUT_INDEX.md`, `output_index.json` and `run_seal.sha256`. Terminal output repeats absolute `OUTPUT_DIR`, `PRIMARY_OUTPUT`, `OUTPUT_INDEX` and `NEXT_STEP` so the user can find every artifact.

When data and all calculation/output gates eventually pass, R9 directly generates the final two-basis workbook and `INTERNAL_PROCESS_HANDOFF.md`. The Skill does not set a finance owner or authorized person and does not represent/manage company approval; the invoking Codex/operator continues the existing company process outside the Skill.
