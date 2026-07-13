# Memory Atlas v1.2.1 S04-P2-T3 Script Consolidation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Consolidate repeated CLI child-script execution and establish an enforceable migration map without deleting scripts that still own unique behavior or active callers.

**Architecture:** A small `child_process.py` adapter preserves child streams and exit codes for existing command modules. A strict JSON migration map plus `script_migrations.py` validator records the four audited families and prevents any future script deletion without an equivalent command, migrated callers and parity tests.

**Tech Stack:** Python 3 standard library, JSON, `unittest`, existing Node/Vite frontend toolchain.

## Global Constraints

- Complete only `S04-P2-T3`; do not start `S04-P3-T1`.
- Do not delete a script that still has direct callers or unique behavior.
- Every future deleted script must have an equivalent command and automated parity coverage.
- Preserve public commands, stdout/stderr bytes, exit codes and dry-run behavior.
- Do not mutate raw data, push, deploy, merge/rebase, create a branch/PR, or clean caches.
- Do not touch the five user-owned WDA changes.

---

### Task 1: Lock consolidation and deletion gates with failing tests

**Files:**
- Create: `tests/test_atlasctl_script_consolidation.py`

**Interfaces:**
- Consumes: current command modules and the audited script inventory.
- Produces: executable expectations for `run_child_command()`, migration-map loading/validation, four-family coverage and zero unsafe deletion.

- [x] **Step 1: Write child stream and exit-code tests**

Run a real Python child that emits distinct stdout/stderr bytes and exits 7.
Require the adapter to preserve all three values exactly.

- [x] **Step 2: Write migration map and deletion-policy tests**

Require the four families, current inventory count, retained-path blockers and
zero deletions. Inject an invalid removed entry and require explicit errors for
missing command, tests, caller migration and parity evidence.

- [x] **Step 3: Run RED**

Run: `python3 -m unittest tests.test_atlasctl_script_consolidation -v`

Expected: FAIL because `child_process.py`, `script_migrations.py` and
`config/atlasctl_script_migrations.json` do not exist.

### Task 2: Implement the migration contract

**Files:**
- Create: `config/atlasctl_script_migrations.json`
- Create: `scripts/memory_atlas_cli/script_migrations.py`
- Test: `tests/test_atlasctl_script_consolidation.py`

**Interfaces:**
- Consumes: a database directory and the tracked JSON map.
- Produces: `load_script_migration_map(database_dir)` and
  `validate_script_migration_map(payload, database_dir) -> list[str]`.

- [x] **Step 1: Record inventory facts and family dispositions**

Record exact scan scope/count, a complete path/hash/family/disposition baseline,
no exact duplicates, no current deletions, canonical command direction,
representative direct-caller blockers and the P3 deferral.

- [x] **Step 2: Implement fail-closed schema and deletion validation**

Validate identity, family coverage, summary counts, full inventory equality,
baseline path-manifest continuity, retained paths, blockers, deleted-path
absence, executable registered tests and parity/caller flags.

- [x] **Step 3: Run migration tests**

Run: `python3 -m unittest tests.test_atlasctl_script_consolidation.ScriptMigrationMapTests -v`

Expected: migration-map tests PASS.

### Task 3: Merge repeated child-process execution

**Files:**
- Create: `scripts/memory_atlas_cli/child_process.py`
- Modify: `scripts/memory_atlas_cli/analyze.py`
- Modify: `scripts/memory_atlas_cli/apply.py`
- Modify: `scripts/memory_atlas_cli/build.py`
- Modify: `scripts/memory_atlas_cli/push.py`
- Modify: `scripts/memory_atlas_cli/sync.py`
- Test: `tests/test_atlasctl_script_consolidation.py`

**Interfaces:**
- Consumes: a command sequence, cwd and optional output streams.
- Produces: `run_child_command(command, cwd, stdout_stream=None, stderr_stream=None) -> int`.

- [x] **Step 1: Implement exact stream forwarding**

Use `subprocess.run(..., text=True, capture_output=True, check=False)`, write
non-empty stdout/stderr to their assigned streams and return the child code.

- [x] **Step 2: Replace all five exact duplicate blocks**

Keep command construction untouched and delegate only execution/forwarding.

- [x] **Step 3: Run focused GREEN**

Run: `python3 -m unittest tests.test_atlasctl_script_consolidation tests.test_atlasctl_modular_cli tests.test_atlasctl_runtime_core -v`

Expected: all focused tests PASS and deterministic CLI stdout hashes remain
unchanged.

### Task 4: Record and verify the bounded Task

**Files:**
- Modify: `功能清单.md`
- Modify: `开发记录.md`
- Modify: `模型参数文件.md`

**Interfaces:**
- Consumes: verified inventory, map and regression evidence.
- Produces: owner-visible `25/149` local-only status and exact next-Task boundary.

- [x] **Step 1: Update owner records**

Record zero unsafe deletions, five command modules/eight execution blocks, migration gate,
remote-lineage deferral and no-push/no-deploy/no-cleanup boundary.

- [x] **Step 2: Run focused and full verification**

Run focused Python tests, full Python discovery, frontend lint/build,
`py_compile`, migration-map validation, representative CLI paths,
`git diff --check` and a changed-path/security scan.

- [x] **Step 3: Request two independent reviews**

Review once for Task-Pack/spec compliance and once for correctness, security,
compatibility and missing tests. Resolve all Critical/Important findings and
rerun affected verification.

- [x] **Step 4: Create one local commit and stop**

Commit only declared OpenAIDatabase paths with message:
`refactor(memory-atlas): consolidate script execution (S04-P2-T3)`.

Expected: local `main` ahead only; no push, deploy, merge/rebase, branch, PR,
cache cleanup or `S04-P3-T1` work.
