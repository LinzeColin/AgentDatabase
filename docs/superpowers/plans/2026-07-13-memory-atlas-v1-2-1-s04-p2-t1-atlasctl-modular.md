# Memory Atlas v1.2.1 S04-P2-T1 Modular atlasctl Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the 2,692-line `atlasctl.py` implementation monolith with a thin compatible facade and six responsibility modules.

**Architecture:** Keep one argparse and constants source, move existing functions without changing behavior, dispatch through an explicit table, and re-export the historical Python API from the facade. Validators read the aggregate runtime source instead of assuming every implementation literal remains in the facade.

**Tech Stack:** Python 3 standard library, Node.js CommonJS validators, unittest, npm/Vite.

## Global Constraints

- Complete only `S04-P2-T1`; do not begin `S04-P2-T2`.
- Preserve all existing CLI commands, options, defaults, outputs and exit codes.
- Do not add logging, error-code, run-state or configuration-loading infrastructure.
- Do not stage, modify or revert the five dirty `WDA/docs/governance/*` files.
- Do not push, deploy, create a branch/PR, reinstall dependencies or clean caches.
- Finish with one bounded local commit after fresh verification.

---

### Task 1: Define and Prove the Structural Contract

**Files:**
- Create: `tests/test_atlasctl_modular_cli.py`
- Create: `docs/superpowers/specs/2026-07-13-memory-atlas-v1-2-1-s04-p2-t1-atlasctl-modular-design.md`
- Create: `docs/superpowers/plans/2026-07-13-memory-atlas-v1-2-1-s04-p2-t1-atlasctl-modular.md`

**Interfaces:**
- Consumes: current `scripts/atlasctl.py` public commands and direct imports.
- Produces: executable acceptance checks for package layout, thin facade and compatible output.

- [x] **Step 1: Write the failing structural test**

Require the six responsibility modules plus parser/constants/dispatch, a facade
under 100 lines with only `main`, and historical callable re-exports.

- [x] **Step 2: Run RED**

Run:

```bash
python3 -B -m unittest OpenAIDatabase.tests.test_atlasctl_modular_cli -v
```

Expected: failure because `scripts/memory_atlas_cli` does not exist and
`atlasctl.py` still contains implementation functions.

### Task 2: Split the CLI Without Behavioral Changes

**Files:**
- Create: `scripts/memory_atlas_cli/__init__.py`
- Create: `scripts/memory_atlas_cli/constants.py`
- Create: `scripts/memory_atlas_cli/parser.py`
- Create: `scripts/memory_atlas_cli/sync.py`
- Create: `scripts/memory_atlas_cli/analyze.py`
- Create: `scripts/memory_atlas_cli/build.py`
- Create: `scripts/memory_atlas_cli/validate.py`
- Create: `scripts/memory_atlas_cli/push.py`
- Create: `scripts/memory_atlas_cli/apply.py`
- Create: `scripts/memory_atlas_cli/dispatch.py`
- Modify: `scripts/atlasctl.py`

**Interfaces:**
- Consumes: existing function bodies and constants without semantic edits.
- Produces: `dispatch(args: argparse.Namespace) -> int`, historical re-exports,
  and `main(argv: list[str] | None = None) -> int`.

- [x] **Step 1: Move constants and parser ownership**

Move every path/contract constant once into `constants.py`; move the unchanged
argument parser to `parser.py`.

- [x] **Step 2: Move runner groups by responsibility**

Move existing function bodies into the six required modules. Keep owner-daily
under `sync`, final/specialized audits under `validate`, personalization and
deep-explore under `build`, and proposal inspection/application under `apply`.

- [x] **Step 3: Add dispatch and thin facade**

Implement a fixed runner map and make `atlasctl.py` a compatibility facade with
only `main` as a local function.

- [x] **Step 4: Run GREEN**

Run the targeted unittest and compare deterministic dry-run hashes for three
sync sources, build-atlas, personalization and deep-explore.

### Task 3: Migrate Validator Source Ownership

**Files:**
- Modify: affected `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_*.cjs` files only when their source-location assumptions fail.

**Interfaces:**
- Consumes: aggregate facade/package runtime source.
- Produces: the same existing validator ids and subprocess behavior checks.

- [x] **Step 1: Run source-sensitive validators and isolate the prerequisite failure**

Execute the existing source-sensitive validators. The current historical chain
reaches `s01_p1` and fails on owner-file Stage text removed before this Task;
record that prerequisite instead of restoring obsolete prose.

- [x] **Step 2: Replace stale single-file reads**

Read `scripts/atlasctl.py` plus `scripts/memory_atlas_cli/*.py` in deterministic
filename order. Do not weaken fragments or remove runtime checks.

- [x] **Step 3: Verify every migrated source contract independently**

Extract every existing `hasAll(atlasctl...)` fragment array and require the
aggregate helper output to satisfy it. Keep the full-chain `s01_p1` blocker open
for the explicit `S04-P3-T2` low-value-test cleanup Task.

### Task 4: Regression, Review and Local Commit

**Files:**
- Modify: `功能清单.md`
- Modify: `开发记录.md`
- Modify: `模型参数文件.md`

**Interfaces:**
- Consumes: completed module split and fresh validation evidence.
- Produces: durable task record and one local commit; no remote state change.

- [x] **Step 1: Run compatibility regression**

Run Python unit discovery, representative CLI dry-runs, aggregate validator
source contracts and the Memory Atlas production build. Record the historical
Stage-chain blocker separately.

- [x] **Step 2: Review the diff**

Check module boundaries, duplicate implementations, hidden API regressions,
unrelated paths, secrets and accidental WDA changes.

- [x] **Step 3: Record and commit**

Update the three governed development records with task scope, architecture,
validation and stop boundary. Stage only `OpenAIDatabase` task files and commit
with message:

```text
refactor(memory-atlas): modularize atlasctl (S04-P2-T1)
```

- [x] **Step 4: Stop before the next Task**

Verify local commit scope and that no push, deploy, branch/PR or cache cleanup
occurred.

## Execution Evidence

- Structural RED: package missing and 47 facade-local functions, as expected.
- Structural GREEN: 25-line facade, six responsibility modules, one constants
  owner, one parser and one dispatch owner.
- AST equivalence: all 46 prior business functions moved exactly once with no
  function-body changes.
- CLI compatibility: 11 command ids/aliases parse; 14 representative dry-run
  paths preserve no-write safety; six deterministic stdout hashes are unchanged.
- Python regression: 232 tests passed.
- Frontend: TypeScript lint and Vite production build passed; existing chunk-size
  warning remains non-blocking.
- Validator migration: 14 source-sensitive validators use the aggregate helper;
  all their existing atlasctl fragments pass. Full historical chaining stops at
  the pre-existing `s01_p1` owner-text assertion.
- Review: one Medium facade-symbol export finding was fixed; follow-up reviewer
  reported no remaining Critical, High or Medium findings.
- Delivery boundary: local commit only; WDA changes excluded; no push, deploy,
  branch/PR or cache cleanup.
