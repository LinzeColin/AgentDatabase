# Memory Atlas v1.2.1 S04-P2-T1 Modular atlasctl Design

## Scope

This design completes only Task `S04-P2-T1`: turn `scripts/atlasctl.py` into a
thin compatible entry point and split its implementations by the required
`sync`, `analyze`, `build`, `validate`, `push` and `apply` responsibilities. It
does not begin the unified logging, error-code, run-state or configuration work
reserved for `S04-P2-T2`.

The public command surface remains unchanged:

```text
run, sync, build-atlas, analyze, audit, push,
generate-personalization-prompt, chatgpt-deep-explore, deep-explore,
proposals, apply
```

Arguments, defaults, stdout JSON contracts, exit codes, no-write dry-runs and
fail-closed behavior must remain compatible.

## Selected approach

Create the internal `scripts/memory_atlas_cli` package with these ownership
boundaries:

- `constants.py`: one source of truth for repository paths and contract ids.
- `parser.py`: the existing argparse command and option contract.
- `sync.py`: owner-daily profile and all source-sync contracts/runners.
- `analyze.py`: derived behavior-intelligence contracts and dispatch.
- `build.py`: atlas build, personalization export and deep-explore runners.
- `validate.py`: final audit planning/execution and specialized audit runners.
- `push.py`: GitHub backup command adapter.
- `apply.py`: proposal inspection and proposal-apply command adapters.
- `dispatch.py`: explicit command-to-runner mapping.

`scripts/atlasctl.py` imports and re-exports the prior callable API for existing
tests and external Python consumers, defines only `main`, and delegates parsing
and dispatch. No implementation or path constant is duplicated in the facade.

Two rejected alternatives are:

1. Move the monolith to `atlasctl_legacy.py` and wrap it. This changes the
   filename but does not create internal module boundaries or remove duplicate
   ownership.
2. Add a dynamic plugin/command registry. The command set is fixed and an
   extension framework would widen this structural task without acceptance
   value.

## Dependency direction

All command modules may import `constants.py`; `parser.py` imports only
`constants.py` and owner-daily option ids. `dispatch.py` imports runners from
the six responsibility modules. The facade imports the public functions and
`dispatch`, but no package module imports the facade. This acyclic direction
keeps each module independently importable.

The established sibling modules `memory_atlas_owner_daily.py` and
`memory_atlas_r8_acceptance.py` remain unchanged. Their APIs are consumed only
by `sync.py` and `validate.py`, respectively.

## Compatibility contract

Compatibility is checked at three levels:

1. Parser tests cover every historical command and option shape.
2. Existing direct imports continue to resolve, including `parse_args`,
   `run_profile`, `final_audit_gate_plan` and `compact_tail`.
3. Representative deterministic dry-run stdout remains byte-for-byte stable;
   data-dependent commands are checked by status, safety fields and exit code.

Old v1.2 validators that inspect only `scripts/atlasctl.py` are updated to read
the facade plus the internal package. Their behavioral subprocess checks stay
intact. This is a location migration, not the validator consolidation reserved
for `S04-P3`.

## Error handling and safety

This refactor deliberately preserves current error and subprocess propagation.
It adds no logging layer, error taxonomy, global configuration loader or run
state, because those are explicit `S04-P2-T2` responsibilities. Dry-run safety,
raw-data mutation boundaries, proposal approval checks and remote-push gates are
unchanged.

## Verification and stop

Use test-first development: the new structural test must fail while the package
is absent and the facade is monolithic, then pass after the split. Run direct
imports, representative CLI contracts, affected v1.2 validators, Python unit
tests and the Memory Atlas production build. Review the final diff for duplicate
implementations and imports.

Create one bounded local commit and stop. Do not push, deploy, create a branch or
PR, clean caches, or begin `S04-P2-T2`.
