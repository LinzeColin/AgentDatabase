# Memory Atlas v1.2.1 S04-P2-T2 Runtime Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add one strict atlasctl configuration, state, error-code and machine-log layer without placing machine logs in stdout.

**Architecture:** A focused `runtime.py` owns the contract and wraps the existing fixed dispatch runner. The thin facade handles only parser/config bootstrap rejection; stdout remains the untouched business channel and compact JSONL runtime events use stderr or are disabled by config.

**Tech Stack:** Python 3 standard library, `argparse`, `dataclasses`, `enum`, `json`, `unittest`.

## Global Constraints

- Complete only Task `S04-P2-T2`; do not start `S04-P2-T3`.
- Preserve all existing public commands, runner exit codes and deterministic stdout bytes.
- Machine logs must not enter stdout and must not be written to files.
- Dry-run must remain no-write.
- Do not mutate raw data, push, deploy, create a branch/PR, or clean caches.

---

### Task 1: Lock the runtime contract with failing tests

**Files:**
- Create: `tests/test_atlasctl_runtime_core.py`
- Modify: `tests/test_atlasctl_modular_cli.py`

**Interfaces:**
- Consumes: `scripts/atlasctl.py`, `scripts/memory_atlas_cli/dispatch.py` and the existing stdout hashes.
- Produces: executable expectations for `RuntimeConfig`, `RuntimeState`, `RuntimeErrorCode`, `load_runtime_config()`, `execute_with_runtime()` and CLI JSONL events.

- [ ] **Step 1: Write focused configuration, state, event and subprocess tests**

Add tests for default config, strict invalid config rejection, legal transitions,
success/nonzero/exception mapping, `off`, stdout hash preservation, argparse
rejection and invalid-config rejection.

- [ ] **Step 2: Run the new suite to verify RED**

Run: `python3 -m unittest tests.test_atlasctl_runtime_core -v`

Expected: FAIL because `memory_atlas_cli.runtime` and
`config/atlasctl_runtime.json` do not exist.

### Task 2: Implement the standalone runtime core

**Files:**
- Create: `scripts/memory_atlas_cli/runtime.py`
- Create: `config/atlasctl_runtime.json`
- Test: `tests/test_atlasctl_runtime_core.py`

**Interfaces:**
- Consumes: `ROOT` from `memory_atlas_cli.constants`, an argparse namespace and a runner callable.
- Produces: `RuntimeConfig`, `RuntimeState`, `RuntimeErrorCode`, `RuntimeConfigError`, `RuntimeStateError`, `load_runtime_config(path=None, env=None)`, `execute_with_runtime(args, runner, ...)`, `command_from_argv(argv)` and `emit_bootstrap_rejection(...)`.

- [ ] **Step 1: Implement strict config loading**

Reject missing, symlinked, oversized, malformed or schema-invalid files. Accept
only `stderr|off`, boolean `emit_started_event`, and `type_only` exception detail.

- [ ] **Step 2: Implement state and event serialization**

Allow only `CREATED -> RUNNING -> terminal`; emit sorted compact JSON with no
payload, path, environment or exception message fields.

- [ ] **Step 3: Implement runner wrapping**

Map `0 -> MA_OK`, `2 -> MA_FAIL_CLOSED`, other nonzero codes to
`MA_COMMAND_FAILED`; log and re-raise unexpected exceptions.

- [ ] **Step 4: Run standalone unit tests**

Run: `python3 -m unittest tests.test_atlasctl_runtime_core.RuntimeCoreUnitTests -v`

Expected: unit-level config/state/session tests PASS; CLI integration tests may
still fail until Task 3.

### Task 3: Integrate dispatch and facade without stdout drift

**Files:**
- Modify: `scripts/memory_atlas_cli/dispatch.py`
- Modify: `scripts/atlasctl.py`
- Modify: `tests/test_atlasctl_modular_cli.py`
- Test: `tests/test_atlasctl_runtime_core.py`

**Interfaces:**
- Consumes: `execute_with_runtime()` and bootstrap rejection helpers from Task 2.
- Produces: runtime-wrapped `dispatch(args, ...)` and compatible `main(argv=None) -> int`.

- [ ] **Step 1: Wrap the fixed runner in dispatch**

Keep the `RUNNERS` map unchanged, select one runner, and pass it with the parsed
namespace to `execute_with_runtime()`.

- [ ] **Step 2: Add facade bootstrap rejection handling**

Catch argparse `SystemExit` only to preserve its code while adding
`MA_ARGUMENT_INVALID`; catch `RuntimeConfigError` to return 2 with
`MA_CONFIG_INVALID`. Keep help exit 0 unlogged.

- [ ] **Step 3: Update compatibility assertions**

Require `runtime.py`, preserve the six stdout hashes, and parse two structured
stderr events for successful default-config dry-runs.

- [ ] **Step 4: Run RED-to-GREEN integration tests**

Run: `python3 -m unittest tests.test_atlasctl_runtime_core tests.test_atlasctl_modular_cli -v`

Expected: all tests PASS and every locked stdout SHA remains unchanged.

### Task 4: Record owner-facing state and verify the bounded Task

**Files:**
- Modify: `功能清单.md`
- Modify: `开发记录.md`
- Modify: `模型参数文件.md`

**Interfaces:**
- Consumes: verified runtime behavior and Task Pack acceptance.
- Produces: current owner summary at `24/149`, runtime parameters and an explicit `S04-P2-T3` stop boundary.

- [ ] **Step 1: Update the three required owner records**

Record the exact config/event schemas, six error codes, state transitions,
stdout/stderr boundary, no-write behavior, test evidence and local-only status.

- [ ] **Step 2: Run focused and related regression**

Run: `python3 -m unittest tests.test_atlasctl_runtime_core tests.test_atlasctl_modular_cli tests.test_memory_atlas_owner_daily tests.test_memory_atlas_r8_acceptance -v`

Run from the canonical `CodexProject` root:
`python3 -m unittest discover -s OpenAIDatabase/tests -p 'test_*.py' -v`

Run from the canonical `CodexProject` root:
`npm --prefix OpenAIDatabase/apps/memory-atlas run lint`

Run from the canonical `CodexProject` root:
`npm --prefix OpenAIDatabase/apps/memory-atlas run build`

Expected: all commands exit 0; any known unrelated historical validator blocker
is reported separately and does not get hidden or changed in this Task.

- [ ] **Step 3: Inspect scope and security**

Run: `git diff --check`

Run: `git diff --name-only -- OpenAIDatabase`

Run: `rg -n '(api[_-]?key|token|password|secret|BEGIN .*PRIVATE KEY)' config/atlasctl_runtime.json scripts/memory_atlas_cli/runtime.py`

Expected: only declared Task paths, no credential material, no raw or WDA edits.

- [ ] **Step 4: Request independent code review and address findings**

Review the diff against Task Pack `S04-P2-T2`, stdout compatibility, strict
loading, state legality, event redaction and one-Task boundary. Resolve every
Critical/Important issue and rerun affected tests.

- [ ] **Step 5: Create one local commit and stop**

```bash
git add OpenAIDatabase/config/atlasctl_runtime.json \
  OpenAIDatabase/scripts/atlasctl.py \
  OpenAIDatabase/scripts/memory_atlas_cli/dispatch.py \
  OpenAIDatabase/scripts/memory_atlas_cli/runtime.py \
  OpenAIDatabase/tests/test_atlasctl_runtime_core.py \
  OpenAIDatabase/tests/test_atlasctl_modular_cli.py \
  OpenAIDatabase/docs/superpowers/specs/2026-07-13-memory-atlas-v1-2-1-s04-p2-t2-runtime-core-design.md \
  OpenAIDatabase/docs/superpowers/plans/2026-07-13-memory-atlas-v1-2-1-s04-p2-t2-runtime-core.md \
  OpenAIDatabase/功能清单.md OpenAIDatabase/开发记录.md OpenAIDatabase/模型参数文件.md
git commit -m "refactor(memory-atlas): add atlasctl runtime core (S04-P2-T2)"
```

Expected: one local commit on `main`; no push, deploy, branch, PR, cache cleanup
or `S04-P2-T3` work.
