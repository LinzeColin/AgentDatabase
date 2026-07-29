# Environment Doctor and Capability Truth

## Purpose

A deployment should adapt to a runtime rather than hard-switching assumptions into production. The `doctor` command inspects minimum engineering capabilities before orchestration and separates them from formal-review capabilities.

## Checks

- Python 3.9+ and Git availability;
- atomic file replacement, advisory locking and file `fsync`;
- case sensitivity and symlink capability as observations;
- optional `cryptography` and `jsonschema` modules;
- presence, not contents, of a GitHub token;
- external review contract and persona team-index bindings.

It does not expose secret values and does not silently probe the network.

## Command

```bash
python3 scripts/wbi.py doctor \
  --workspace /absolute/external/doctor-work \
  --output /absolute/external/environment-report.json
```

Optional formal inputs:

```bash
python3 scripts/wbi.py doctor \
  --workspace /absolute/external/doctor-work \
  --review-contract /absolute/external/review-contract.json \
  --persona-index /absolute/external/team-index.json \
  --output /absolute/external/environment-report.json
```

## Status separation

`engineering: READY` may coexist with `formal: BLOCKED`. Missing external review or persona routing must not prevent local engineering verification, and local engineering success must not be promoted to external independence.
