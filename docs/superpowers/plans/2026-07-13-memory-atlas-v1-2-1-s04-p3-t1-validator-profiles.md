# Memory Atlas v1.2.1 S04-P3-T1 Validator Profiles Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace 178 public validation commands with four strict, configuration-driven profiles while preserving all current critical validation behavior.

**Architecture:** A Python runner loads a bounded JSON contract, requires the exact audited cwd/argv policy for every configured step, resolves only three allowlisted working directories and executes argv arrays with `shell=false`. `package.json` exposes only `validate:fast`, `validate:sync`, `validate:ui` and `validate:release`; historical validator files remain internal until later Tasks.

**Tech Stack:** Python 3 standard library, JSON, `unittest`, npm, Node.js, existing Playwright/Vite validators.

## Global Constraints

- Complete only `S04-P3-T1`; do not start `S04-P3-T2` or `S04-P3-T3`.
- Preserve user-facing application, CLI, sync, raw, derived and deployment behavior.
- Do not delete historical validator files or low-value tests in this Task.
- Do not mutate raw/derived data, push, deploy, merge/rebase, create a branch/PR or clean caches.
- Keep all unrelated canonical-worktree changes untouched and unstaged,
  including the pre-existing KMFA files and OpenAIDatabase session-history
  temporary files present after the external worktree relocation.
- Use one final local commit only.

---

### Task 1: Lock the public and runtime contracts with RED tests

**Files:**
- Create: `tests/test_memory_atlas_validator_profiles.py`
- Modify: `tests/test_memory_atlas_v1_2_home_layout_contract.py`

**Interfaces:**
- Consumes: `package.json`, the profile JSON, runner module and real child processes.
- Produces: executable contracts for exact public profile names, strict configuration, plan mode, exit codes and fail-fast behavior.

- [ ] **Step 1: Write public-surface and config tests**

Require the package validation-key set to equal:

```python
{"validate:fast", "validate:sync", "validate:ui", "validate:release"}
```

Require config schema `memory_atlas.validator_profiles.v1_2_1_s04_p3_t1`,
ordered profile IDs `fast/sync/ui/release`, unique step IDs, argv arrays,
allowlisted cwd values, bounded timeouts and all critical steps.

- [ ] **Step 2: Write real runner behavior tests**

Use temporary in-memory profile mappings with `sys.executable -c` children to
prove PASS, non-zero failure, process-tree timeout cleanup, launch-error JSON,
bounded multi-megabyte stdout/stderr tails, no execution after a critical
failure and plan mode no-write behavior. Reject unknown profile, unknown config
fields, symlink config, shell-like strings and commands outside the exact
audited policy.

- [ ] **Step 3: Update the Home browser gate test**

Require `ui/home_multiviewport` to point directly to
`validate_memory_atlas_v1_2_home_multiviewport.cjs` instead of requiring the
removed historical package alias.

- [ ] **Step 4: Run RED**

Run:

```bash
python3 -m unittest tests.test_memory_atlas_validator_profiles tests.test_memory_atlas_v1_2_home_layout_contract -v
```

Expected: FAIL because the runner/config/four public scripts do not exist and
the Home test still sees the 178-command package surface.

### Task 2: Implement the strict config-driven runner

**Files:**
- Create: `config/memory_atlas_validator_profiles.json`
- Create: `scripts/memory_atlas_validator_profiles.py`
- Test: `tests/test_memory_atlas_validator_profiles.py`

**Interfaces:**
- Produces: `load_validator_profile_config(database_dir, path=None)`.
- Produces: `build_profile_plan(config, profile_name, database_dir)`.
- Produces: `run_validator_profile(config, profile_name, database_dir, *, plan_only=False)`.
- CLI: `python3 scripts/memory_atlas_validator_profiles.py --profile <name> [--plan]`.

- [ ] **Step 1: Implement strict configuration loading**

Use `os.open(..., O_NOFOLLOW)`, require a regular UTF-8 JSON file no larger
than 64 KiB, reject unknown/missing keys, duplicate step IDs, unsupported cwd,
non-array commands, unbounded timeout or non-critical steps. For file-loaded
configs, require the exact 23-step `(profile, ID, cwd, argv)` audited policy
before emitting no-push/no-raw-mutation safety facts.

- [ ] **Step 2: Implement process execution**

Resolve `@python` to `sys.executable`, use `subprocess.Popen(...,
shell=False, start_new_session=True)` on POSIX, preserve exit code, terminate
the whole process group on timeout, convert launch `OSError` to a fail-closed
step result, stop after the first failure, and keep at most 8,000 characters
from each diagnostic stream. Drain both streams concurrently into fixed-size
byte tails instead of retaining complete child output. Convert cleanup
`OSError`/`PermissionError` to bounded warnings without breaking the result
JSON. Use a descendant-safe Windows fallback.

- [ ] **Step 3: Implement CLI and machine result**

Return 0 on PASS, 1 on child failure/timeout and 2 on argument/config errors.
Emit one JSON object on stdout and concise step status/failure tails on stderr.
Plan mode reports ordered steps without invoking a child.

- [ ] **Step 4: Run runner tests GREEN**

Run:

```bash
python3 -m unittest tests.test_memory_atlas_validator_profiles -v
```

Expected: all runner and configuration tests PASS.

### Task 3: Collapse package commands and migrate critical callers

**Files:**
- Modify: `apps/memory-atlas/package.json`
- Modify: `scripts/memory_atlas_cli/validate.py`
- Modify: `scripts/audit_memory_atlas_visual_acceptance.py`
- Modify: `scripts/build_memory_atlas_self_iteration.py`
- Modify: `scripts/memory_atlas_cli/script_migrations.py`
- Modify: `tests/test_memory_atlas_v1_2_home_layout_contract.py`
- Modify: `tests/test_atlasctl_script_consolidation.py`
- Modify: `config/atlasctl_script_migrations.json`
- Modify: `docs/governance/delivery_tasks.yaml`

**Interfaces:**
- Public npm commands: `validate:fast`, `validate:sync`, `validate:ui`, `validate:release`.
- Existing final-audit gate IDs remain unchanged.
- Existing historical validator files remain tracked and executable directly.

- [ ] **Step 1: Replace the package validation surface**

Retain `dev/build/preview/lint`, remove all 178 historical `validate:*` keys and
add only four commands invoking the Python runner.

- [ ] **Step 2: Preserve final-audit behavior**

Replace the eight `npm run validate:<historical>` commands in
`final_audit_gate_plan()` with equivalent direct `node scripts/<file>` argv.
Do not change gate IDs, explanations, timeouts or R8 acceptance semantics.

- [ ] **Step 3: Migrate visual acceptance registration checks**

Load the profile JSON and require the relevant `ui` step IDs rather than old
package-script strings. Keep all real source/browser contract assertions.

- [ ] **Step 4: Refresh current migration and governance contracts**

Refresh SHA-256 rows for modified scoped validators, record that four public
profiles now exist, and replace the four representative removed aliases with
their `fast`/`ui` profile commands. Keep all 208 historical paths, retained
dispositions and deletion count unchanged; defer the comprehensive old-command
table to `S04-P3-T3`. Replace any active delivery command that still invokes a
removed alias with the behavior-equivalent direct validator command.

- [ ] **Step 5: Run focused GREEN**

Run profile tests, Home contract tests, modular CLI/runtime tests and visual
acceptance audit tests. Expected: all PASS with exactly four public validation
commands and no deleted validator files.

### Task 4: Record, review, verify and commit the bounded Task

**Files:**
- Modify: `功能清单.md`
- Modify: `开发记录.md`
- Modify: `模型参数文件.md`
- Modify: `docs/governance/project.yaml`
- Modify: `docs/governance/roadmap.yaml`
- Modify: `docs/governance/events.jsonl`
- Create: `docs/superpowers/specs/2026-07-13-memory-atlas-v1-2-1-s04-p3-t1-validator-profiles-design.md`
- Create: `docs/superpowers/plans/2026-07-13-memory-atlas-v1-2-1-s04-p3-t1-validator-profiles.md`

**Interfaces:**
- Records `26/149`, four profiles, old/new public command counts, exact tests,
  local-only status and next Task `S04-P3-T2`.
- Treats the three Lean governance machine sources as authoritative and renders
  the three owner-facing Markdown files with `lean_governance.py render`.

- [ ] **Step 1: Run actual profiles**

Run `validate:fast`, `validate:sync` and `validate:ui`. Run
`validate:release -- --plan` first; execute the full release profile if current
intermediate remote/recovery gates are applicable. Any failed critical step is
not waived.

- [ ] **Step 2: Run full regression and build**

Run full Python discovery, frontend lint/build, `py_compile`, JSON/schema
validation, `git diff --check`, deleted-path check, raw/data scope check and a
high-confidence secret scan.

- [ ] **Step 3: Request two independent reviews**

One reviewer checks Task-Pack/spec compliance and one checks correctness,
security, compatibility and missing tests. Resolve every Critical/Important
finding and rerun affected validation.

- [ ] **Step 4: Verify remote and staged scope**

Fetch/read remote main without merging, verify no Task-path conflict, open PR
count zero, one local branch, and stage only declared OpenAIDatabase paths.

- [ ] **Step 5: Create one local commit and stop**

Commit message:

```text
refactor(memory-atlas): add validator profiles (S04-P3-T1)
```

Stop before `S04-P3-T2`; do not push or deploy.
