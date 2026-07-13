# Memory Atlas v1.2.1 S04-P2-T2 Runtime Core Design

## Scope

This design completes only Task `S04-P2-T2`: establish one configuration
loader, run-state model, error-code taxonomy and machine-log channel for the
modular `atlasctl` CLI. The Task Pack acceptance is exact: machine logs must not
enter the human primary output.

The public command surface, arguments, business JSON written to stdout, child
process return codes and no-write dry-run behavior remain compatible. This Task
does not merge or delete build, sync, audit or validator scripts; that work is
reserved for `S04-P2-T3`.

## Selected approach

Create `scripts/memory_atlas_cli/runtime.py` and a tracked strict default config
at `config/atlasctl_runtime.json`.

- Business payloads remain byte-for-byte on stdout.
- Runtime events are compact JSONL on stderr when enabled.
- The config can set `machine_log_destination` to `off` for quiet embedding.
- Runtime events are never persisted to files by this layer, so dry-run remains
  no-write and existing source-specific audit logs keep their ownership.
- `dispatch.py` wraps the selected runner; it does not change command routing.
- `atlasctl.py` remains a thin facade and handles only parser/config bootstrap
  rejection so those failures also receive stable codes.

Writing runtime metadata into stdout was rejected because it would mix machine
and human contracts and invalidate existing consumers. Writing a new JSONL file
was rejected because it would turn no-write dry-runs into filesystem mutations.

## Configuration contract

The config is a small UTF-8 JSON object with exactly these keys:

```json
{
  "schema_version": "memory_atlas_cli_runtime_config.v1_2_1_s04_p2_t2",
  "machine_log_destination": "stderr",
  "emit_started_event": true,
  "exception_detail": "type_only"
}
```

`MEMORY_ATLAS_RUNTIME_CONFIG` may select an alternate config for local
embedding and tests. Loading fails closed when the file is absent, a symlink,
larger than 16 KiB, invalid JSON, has unknown/missing keys, uses wrong types, or
contains unsupported values. No config value may contain a log path.

## Run-state and error contract

`RuntimeState` starts at `CREATED`, moves once to `RUNNING`, then ends in one of
`SUCCEEDED`, `FAIL_CLOSED`, `FAILED` or `REJECTED`. Illegal transitions raise a
runtime-state error rather than silently changing evidence.

The stable error codes are:

| Code | Meaning |
|---|---|
| `MA_OK` | Runner returned 0. |
| `MA_ARGUMENT_INVALID` | argparse rejected the command line. |
| `MA_CONFIG_INVALID` | Runtime config could not be trusted. |
| `MA_FAIL_CLOSED` | Runner returned the established fail-closed exit 2. |
| `MA_COMMAND_FAILED` | Runner returned another non-zero code. |
| `MA_UNHANDLED_EXCEPTION` | Runner raised unexpectedly. |

The wrapper preserves runner exit codes. Unexpected exceptions are logged with
their Python type only and then re-raised, preserving the existing traceback
contract without copying exception messages into machine events.

## Machine event contract

Each enabled invocation emits `run_started` and one terminal event as JSONL.
Events include only schema version, UTC timestamp, opaque run id, allowlisted
command name, event, level, status, stable error code, exit code, dry-run flag
and terminal duration. They never include child stdout/stderr, exception
messages, command options, environment values, repository paths or secrets.

The stderr transport is best-effort: `OSError`, `BrokenPipeError`, closed-stream
`ValueError` or flush failure disables later events for that invocation but can
never replace the runner's stdout, return code or original exception. A broken
telemetry transport therefore reduces observability without changing business
behavior.

Bootstrap rejection emits one `run_rejected` event. argparse usage remains on
stderr because it is the CLI error channel, while stdout stays empty. Consumers
that need only the primary human/business result continue parsing stdout. This
bootstrap event deliberately uses a minimal safe fallback even when the runtime
config requests `off`, because parsing has failed before a trusted invocation
config exists; the event contains only an allowlisted command or `unparsed`.

## Compatibility and verification

The six deterministic dry-run stdout SHA-256 values remain unchanged. Runtime
tests cover strict configuration, legal states, exit-code mapping, exception
redaction, logging-off behavior, parser rejection and invalid-config rejection.
Existing direct imports, Owner Daily, R8 acceptance and source-sensitive
validators remain compatible.

Create one bounded local commit and stop. Do not push, deploy, create a branch
or PR, clean caches, or begin `S04-P2-T3`.
