# Memory Atlas v1.2.1 S04-P3-T2 Test Value Design

## Scope

This design completes only `S04-P3-T2`. It retains tests that prove a user
journey, data integrity boundary, or release risk and removes validators/tests
whose only remaining value is file existence, historical Stage wording, or
source-marker matching.

`S04-P3-T3` remains out of scope. This Task does not create legacy aliases,
publish a comprehensive old-command compatibility policy, push, deploy, mutate
raw/derived data, or clean caches.

## Evidence Baseline

The pre-change baseline at local commit `31e217c9c` contains 177 Node validator
files (2,902,666 bytes) and 51 Python test files. The machine review contract is
`config/memory_atlas_test_value_review.json`; it records the source TaskPack
SHA-256, every retained asset, and every deletion candidate using the exact
TaskPack candidate fields:

`path`, `category`, `references`, `runtime_dependency`, `replacement_source`,
`reason`, `restore_method`, `batch`, `validation`, and `approval`.

The approved result removes 139 historical Node validators and two Python
tests. It retains 38 Node validators and 49 baseline Python tests, then adds one
continuous value-audit test for a current total of 50 Python test files.

## Risk Binding

Retained coverage is grouped by acceptance risk instead of Stage labels:

- user journeys: real multi-viewport Home, command, proposal, Owner Daily,
  visual workflow, Obsidian and canvas browser paths;
- data integrity: raw append-only, redaction/privacy, source sync, deterministic
  build and recovery contracts;
- release risk: lint/build, privacy/accessibility, visual/performance and final
  release audit gates;
- architecture/runtime: feature boundaries, mounted paths, shared state,
  modular CLI, runtime core and script migration behavior.

The removed product-identity source test is superseded by real Home browser
identity assertions. The removed source-level visual-acceptance wrapper is
superseded by retained browser workflow gates plus the retained acceptance
audit. The deleted Stage validators are mapped to one of the four audited
profiles and are absent only when no current executable caller remains.

One current caller required migration:
`build_memory_atlas_self_iteration.py` now invokes the direct behavioral
`tests.test_s09p2_self_iteration` regression instead of the deleted
`validate_memory_atlas_v1_2_s09_p2.cjs` source-marker validator.

## Fail-Closed Contract

`scripts/audit_memory_atlas_test_value.py` loads a bounded, regular,
non-symlinked UTF-8 JSON contract and fails when:

- the schema, counts, baseline partition, approval or risk bindings drift;
- a retained asset disappears or a deleted asset returns;
- any deleted path has a current executable caller;
- the current validator/test sets differ from the reviewed sets; or
- a candidate lacks an approved replacement and Git recovery command.

`tests/test_memory_atlas_test_value_audit.py` proves the current contract,
synthetic schema/risk failures, synthetic caller failures, exact Git baseline
identity and replacement-profile plans.
It is part of `validate:fast`, so this is a continuous gate rather than a
one-time deletion report. `atlasctl_script_migrations.json` keeps all historical
validator rows with `disposition=deleted` and binds them to the registered T2
low-value retirement evidence test. These rows explicitly set
`behavior_parity_verified=false`; deletion is permitted through the approved
low-value retirement contract, not through a false stdout/exit-code parity
claim.

## Recovery

Every deletion candidate has a path-specific command restoring it from
`31e217c9c`. The whole Task can be reverted through its local Task commit. The
retirement rescue archive remains retained and checksum-verified; this Task
does not delete source packages, recovery evidence, raw/derived data or caches.

## Acceptance

Acceptance requires the strict value audit, profile contracts, script migration
contracts, focused/full Python regressions, frontend lint/build and actual
profile checks to pass. Two independent reviewers must find no unresolved
Critical or Important issue. The run ends with one local commit and no push,
deploy, branch, PR or T3 work.
