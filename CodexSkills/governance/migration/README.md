# Read-only migration and cutover

Status: **DRAFT_NON_ACTIVE / CURRENT_CUTOVER_BLOCKED**

`read_only_cutover.py` is the pure Mechanism M-065 gate. It consumes only
immutable, public-safe evidence and recomputes:

- all four source states;
- protected-source pre/post immutability;
- file, byte, regular-file, symlink, tree-digest, and link-digest parity;
- old/new dual-read result equality;
- delete, move, truncate, write, chmod, chown, and target-delete audit counts;
- a new-commit-only, source-preserving rollback contract.

The module has no filesystem, Git, network, state, lock, publisher, copy,
move, truncate, delete, or activation capability. A complete synthetic
evidence set can produce `CUTOVER_ELIGIBLE`, but never execution authority:
`current_cutover_permitted` remains false.

The checked-in current observation is intentionally blocked. It records the
facts available from immutable repository evidence without inventing missing
local-source snapshots or a dual-read run:

- no distinct M-014 source-migration receipt is present;
- complete M-015 local source-target parity has not been proven;
- the historical `CODEX` source/target Git trees differ;
- resolver source-root and whole-source parity remain false;
- resolver production trust remains false;
- no real dual-read, migration, rollback, or local mutation was executed.

The historical path consolidation is evidence, not a grandfathered migration
receipt. Three tree objects are equal, while the `CODEX` tree is not. The old
repository paths were removed in that historical commit, so it cannot prove
that the four external local source roots remained unchanged.

Artifacts:

- `read-only-migration-observation.json`
- `read-only-cutover-plan.json`
- `read-only-migration-cutover-readiness.json`
- `schemas/read-only-migration-observation.schema.json`
- `schemas/read-only-cutover-plan.schema.json`
- `schemas/read-only-migration-cutover-readiness.schema.json`

Reproduce:

```bash
/usr/bin/python3 -B \
  CodexSkills/governance/tools/build_read_only_migration_cutover.py --check
/usr/bin/python3 -B -m unittest \
  CodexSkills.governance.tests.test_read_only_migration_cutover
```

M-065 does not modify Auto, OpenAIDatabase, local source roots, run data,
legacy data, state, watermarks, `CodexSkills/VERSION`, or canonical
publication. Its only successor is M-066,
`MECHANISM_PERFORMANCE_CAPACITY_BUDGETS`.
