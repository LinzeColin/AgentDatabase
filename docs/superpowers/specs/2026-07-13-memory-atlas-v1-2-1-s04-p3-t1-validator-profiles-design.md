# Memory Atlas v1.2.1 S04-P3-T1 Validator Profiles Design

## Scope

This design completes only `S04-P3-T1`. It replaces the default public surface
of 178 version, Stage and browser validation commands with four stable,
configuration-driven profiles: `fast`, `sync`, `ui` and `release`.

This Task does not delete historical validator files or low-value tests. It
does not create the legacy command migration table. Those changes remain in
`S04-P3-T2` and `S04-P3-T3` respectively.

## Selected Approach

Create one strict Python runner, `scripts/memory_atlas_validator_profiles.py`,
and one tracked JSON configuration,
`config/memory_atlas_validator_profiles.json`. The package exposes exactly the
four validation profiles in addition to its existing development commands.

The alternatives were rejected:

- adding four wrappers while retaining all 178 public aliases would not reduce
  the maintenance or discovery surface;
- deleting historical validators now would cross the T2/T3 boundary and remove
  evidence before the migration map and high-value test review exist.

Historical validator files therefore remain available as internal
implementations. Critical current gates are invoked directly by the profiles
or by the existing final audit, not through public historical npm aliases.

## Profile Contract

`fast` is the low-cost developer loop. It runs the validator-profile contract
tests, modular CLI/runtime/script-consolidation regressions, frontend typecheck,
feature-boundary validation and mounted-path validation.

`sync` proves no-write ChatGPT, Codex and future-Agent paths plus sync/raw
tests, append-only integrity and credential scanning.

`ui` performs the production build and real browser gates for the three Home
viewports, visual workflows, command workflows, proposal workflow, Owner Daily,
canvas rendering/performance/privacy-accessibility, Obsidian behavior, visual
semantics and model contracts.

`release` invokes the existing fail-closed final audit. That audit retains its
individual gate IDs but calls validator files directly, so it no longer
depends on removed historical npm aliases.

Every profile step has a stable ID, command argv, allowlisted working-directory
key, timeout and `critical=true`. The loader requires the exact audited
`(profile, step ID, cwd, argv)` policy for all 23 steps before it marks a
configuration trusted. Commands use `shell=false`; the configuration cannot
interpolate environment values or accept command overrides.

## Runtime Behavior

The runner accepts only `--profile fast|sync|ui|release` and an optional
`--plan` flag. It loads a regular, non-symlinked, size-bounded UTF-8 JSON file,
rejects unknown fields and validates the complete four-profile contract before
executing anything.

Child stdout/stderr is drained concurrently into fixed-size byte tails, so
large output cannot accumulate in runner memory before result truncation.
Every child starts in an isolated process group; timeout cleanup terminates the
group so Vite, Playwright or other descendants cannot survive the failed step.
Signal permission or cleanup errors become bounded diagnostics instead of
escaping the one-JSON result contract.
Successful steps emit only a concise status line to stderr. Failed, timed-out
or unlaunchable steps include bounded diagnostics, stop the profile immediately
and make the runner exit 1. Invalid arguments or configuration exit 2. Stdout
contains one machine-readable result object.

The result records the profile, status, step counts, duration, each executed
step's exit code and `shell=false`. Exact canonical configs additionally report
`commands_audited=true`, `remote_push=false` and `raw_mutation=false`;
programmatic test configs report the latter two facts as unknown rather than
making an unsupported safety claim. Plan mode executes no child process and
reports the same ordered step IDs.

## Compatibility Boundary

The web application, CLI product commands, raw data, derived data and deployed
runtime are unchanged. Existing historical validator files remain tracked.
Only their default npm discovery surface is removed.

Any code path that still needs a critical historical validator is migrated to
its direct file command or one of the four profiles in this Task. Documentation
of every old npm alias and temporary compatibility policy remains exclusively
`S04-P3-T3`.

During implementation, the prior canonical worktree was externally retired.
The task was recovered from the retirement rescue bundle only after every
listed SHA-256 checksum passed, the four prerequisite S04 commits were replayed
onto the new canonical `main`, and the bounded T1 patch was validated against
that current tree. No branch, PR, push, deployment, raw/derived mutation or
cache cleanup was introduced by the recovery. The rescue archive remains
retained as recovery evidence.

The owner-facing feature, development and model-parameter documents are Lean
governance render outputs. Their authoritative inputs are
`docs/governance/project.yaml`, `roadmap.yaml` and `events.jsonl`; T1 records
`26/149`, leaves T2/T3 planned and adds no model, formula or business parameter.

## Verification

Acceptance requires:

1. an observed RED test before implementation;
2. exactly four `validate:*` package scripts;
3. strict config tamper, audited-command rejection, unknown-profile, pass,
   failure, multi-megabyte bounded-output, process-tree timeout, launch-error
   and plan tests;
4. actual `fast`, `sync` and `ui` profile runs with zero failed or skipped
   critical steps;
5. a release plan plus the final release profile when the current intermediate
   repository state permits its remote/recovery gates;
6. full Python tests, frontend lint/build and existing final-audit plan tests;
7. two independent reviews with all Critical and Important findings resolved;
8. one local commit, with no push, deploy, merge/rebase, branch, PR, raw/data
   mutation or cache cleanup.

## Stop Boundary

Stop after the local `S04-P3-T1` commit. Do not delete low-value tests, build a
legacy command migration map or begin `S04-P3-T2`/`S04-P3-T3`.
