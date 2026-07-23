# Task Pack and Run Contract

Use this reference only for `CONTROLLED_RUN` requests.

## Default Task Pack Structure

Default to the compact `5+1` structure:

```text
outputs/task_pack/
  00_RUN_CONTRACT.md
  01_REQUIREMENTS_AND_SCOPE.md
  02_ARCHITECTURE_DATA_API.md
  03_STAGE_PHASE_TASKS.md
  04_ACCEPTANCE_VALIDATION_STOP.md
  CHANGELOG.md
```

Expand beyond this only when the user explicitly asks for a larger package or
the project already requires a larger schema.

## Run Contract

Every implementation run should define:

1. Goal.
2. Minimum scope.
3. Non-goals.
4. Files or directories to inspect.
5. Files that may be modified.
6. Validation commands.
7. Risks and rollback.
8. Stop conditions.

## Execution Rules

- Execute at most one stage, phase, or task group per run unless the user
  explicitly widens scope.
- Prefer small, high-confidence diffs.
- Preserve unrelated local changes.
- Do not replace real validation with string or marker checks.
- Report changed files, commands run, results, and residual risks.

## Package or Handoff Requests

If the user asks to package or deliver, keep it lightweight by default:

- Include only requested artifacts and validation evidence.
- Do not create PDF or ZIP outputs unless explicitly requested.
- Do not invent release readiness; state blockers plainly.

