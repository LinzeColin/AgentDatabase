# Persistent Strategy Memory

## Problem

Artifact-only optimization retains the latest Skill but loses why prior changes were kept, rejected or judged neutral. Later agents then repeat failed edits, oscillate between two designs, or infer a false rationale from the final diff.

Teleiosis v0.0.0.2 adds a minimal persistent decision history inspired by SkillOpt's rejected-edit evidence and SkillHone's cross-session decision history. It stores structured outcomes and evidence bindings, not private chain-of-thought.

## Event contract

Each `strategy-update` record contains:

- candidate ID;
- exact scope;
- mechanism family;
- `KEEP`, `REVERT` or `NO_CHANGE`;
- change ratio;
- metric deltas;
- failure tags;
- known cost and explicit unknowns;
- one or more evidence paths relative to the workspace.

The controller resolves each evidence file, stores path/hash/size bindings, and appends an event to a hash chain. Changing an earlier event breaks `event_hash`, every later `previous_event_hash`, or the memory head.

## Rejected-edit buffer

The latest rejected and neutral attempts remain visible. A mechanism is suppressed after two recent `REVERT/NO_CHANGE` events, unless new research or a materially different contract justifies retrying it. Suppression is a recommendation, not a permanent ban.

## Oscillation and saturation

The deterministic strategy selector detects:

- same scope with alternating mechanism sequence A/B/A/B: `oscillation_detected=true`, freeze the scope and reframe the objective;
- three recent no-progress attempts across at least two mechanisms: `SATURATED`, `REHEAT_REQUIRED`;
- retained small attributable change: continue the same mechanism only with a small learning rate and measured marginal benefit;
- regression: reduce edit magnitude and switch mechanism family.

These rules stop token-consuming churn without declaring the target globally optimal.

## Trust boundary

Strategy memory cannot:

- replace sealed benchmark results;
- authorize a production mutation;
- count as independent review;
- reveal or require private reasoning;
- turn unknown cost into zero;
- permit a candidate to overwrite the baseline or holdout.

## Usage

```bash
cp templates/strategy-record.json /external/path/strategy-record.json

python3 scripts/wbi.py strategy-update /external/path/wbi-run \
  --record /external/path/strategy-record.json

python3 scripts/wbi.py strategy-next /external/path/wbi-run
```

The memory is stored at `wbi-run/control/strategy-memory.json`. Evidence referenced by the record must already exist inside the external workspace.
