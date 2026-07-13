# Memory Atlas v1.2.1 S04-P2-T3 Script Consolidation Design

## Scope

This design completes only Task `S04-P2-T3`: identify duplicate build, sync,
audit and validator script surfaces, merge proven duplicate execution logic,
and publish a migration map whose deletion gate requires an equivalent command
and automated parity test for every removed script.

The inventory covers tracked top-level files in `scripts/` and
`apps/memory-atlas/scripts/` whose names contain `build`, `sync`, `audit` or
`validate`. SHA-256 and normalized-source inspection found no exact duplicate
files. Standalone scripts remain unique implementations or retain direct CI,
installer, runtime, test or package callers. Under the owner's deletion rule,
none is safe to remove in this Task.

This Task does not create the `fast`, `sync`, `ui` or `release` validator
profiles. That work remains exclusively `S04-P3-T1`.

## Selected approach

Create one internal `child_process.py` adapter for the byte-preserving
`subprocess.run` pattern currently repeated by build, sync, analyze, proposal
and backup command modules. The adapter owns only child execution and stream
forwarding:

- command arguments and working directory are passed through unchanged;
- child stdout is copied to the supplied human/business stdout stream;
- child stderr is copied to the supplied error stream;
- the exact child exit code is returned;
- no output parsing, logging, retry, timeout, write or exception suppression is
  added.

Create `config/atlasctl_script_migrations.json` as the machine-readable
migration map. It records the four audited families, the canonical
`atlasctl` direction, a complete 208-row path/SHA-256/family/disposition
inventory, representative caller blockers, the exact inventory method, zero
current deletions, and the `S04-P3-T1` validator boundary. A fixed baseline
path-manifest digest prevents an existing candidate from disappearing or being
silently replaced in the map; newly scoped scripts must also be mapped.
`script_migrations.py` validates this map and fails closed if a future removed
entry lacks all of:

1. an absent legacy path;
2. a non-empty equivalent command;
3. one or more registered equivalence test IDs;
4. explicit caller migration evidence;
5. explicit behavior parity evidence.

## Rejected approaches

Deleting standalone sync/build scripts now was rejected because the modular
CLI still invokes them and tests, CI and installers call or import them
directly. Moving those implementations in this Task would widen the blast
radius and require family-by-family fixture parity first.

Merging historical Stage validators was rejected because their profile and
public-package consolidation is the next Task, `S04-P3-T1`. Removing them now
would collapse two Task boundaries and make acceptance ambiguous.

Creating compatibility wrappers at deleted paths was rejected because a
wrapper is still a script and would not reduce the public surface.

## Migration states

Representative family entries are classified as one of:

- `retained_unique_implementation`: the script owns behavior still invoked by
  the CLI or another runtime caller;
- `retained_partial_cli_coverage`: an `atlasctl` route exists but does not yet
  expose every direct-script argument or import contract;
- `retained_no_equivalent_command`: no behavior-equivalent `atlasctl` command
  exists yet;
- `deferred_to_s04_p3_t1`: validator profile consolidation is intentionally
  outside this Task.

These states are not completion claims for later removal. A script can move to
`removed` only after callers and behavior parity are independently verified.
The exhaustive inventory uses only `retained` and `deleted`; every deleted row
must remain in the baseline manifest and have a matching proof record.

## Compatibility and safety

Existing public scripts, package commands, CLI commands, stdout bytes, stderr
bytes, exit codes and dry-run behavior remain unchanged. No raw data,
personalization output, deployment configuration, branch, PR, remote ref,
installed app or cache is modified.

Remote `origin/main` contains provider-neutral personalization work not present
in local HEAD. It does not touch the CLI/runtime files changed here, so this
Task may remain local-only. That remote lineage must be reconciled before any
personalization acceptance, deployment, app reinstall or final GitHub upload.

Create one bounded local commit and stop. Do not begin `S04-P3-T1`.
