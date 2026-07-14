# Memory Atlas v1.2.1 S04-P3-T2 Test Value Implementation Plan

**Goal:** Keep regression coverage tied to user journeys, data integrity or
release risk while removing low-value historical/source-marker tests.

**Boundary:** Complete only `S04-P3-T2`; do not start `S04-P3-T3`, push,
deploy, mutate data, create a branch/PR or clean caches.

## 1. Lock the value contract RED

- Inventory the 177 Node validators and 51 Python test files at `31e217c9c`.
- Classify every retained/deleted path with explicit risk and recovery fields.
- Add fail-closed tests for schema drift, missing risk bindings, current callers,
  deleted-path return and retained-path loss.
- Observe RED before the audit implementation and before candidate deletion.

## 2. Delete only approved low-value assets

- Remove 139 version/Stage/source-marker Node validators.
- Remove the product-identity source test and source-level visual wrapper only
  after binding their risks to retained real-browser and acceptance coverage.
- Migrate the self-iteration builder caller to the direct S09-P2 behavioral
  regression.
- Keep Git restore commands for every deleted path.

## 3. Make the review continuous

- Implement `scripts/audit_memory_atlas_test_value.py`.
- Register the audit test in `validate:fast` and the audited command policy.
- Preserve deleted entries in `atlasctl_script_migrations.json` with one
  registered parity test, migrated callers and behavior-parity facts.
- Update active governance references that named removed low-value tests.

## 4. Verify and record

- Run focused value/profile/migration tests and the full Python suite.
- Run `validate:fast`, relevant frontend lint/build and profile plans/actual
  gates available in the current environment.
- Run schema/JSON, compile, diff, scope, secret and remote hygiene checks.
- Render the three owner-facing governance documents from canonical YAML/JSONL.
- Resolve two independent reviews, create one local Task commit and stop.

## Stop Condition

Stop immediately if a candidate is the only current proof of a user journey,
data-integrity boundary or release risk; if a current executable caller cannot
be migrated; or if restoration cannot be proven. Otherwise stop after the
local `S04-P3-T2` commit with `S04-P3-T3` still planned.
