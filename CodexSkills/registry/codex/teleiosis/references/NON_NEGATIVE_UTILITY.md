# Non-Negative Utility Guard

## Principle

A Candidate is not better merely because it is different, larger, or has more tests. Inspired by the defensive fallback in the public `Curzibn/Luban` image-compression library - where an output larger than the original should not replace the original - Teleiosis applies the same invariant to Skill evolution:

> A Candidate with a protected regression is reverted; a Candidate without a material measured gain falls back to the Baseline.

## Decisions

| Decision | Condition |
|---|---|
| `KEEP_CANDIDATE` | At least one material measured gain and no protected/hard regression |
| `KEEP_BASELINE` | No protected regression, but no material gain worth the added burden |
| `REVERT` | Any protected check regresses or any hard metric exceeds its tolerance |

Hard dimensions are non-compensatory. A large soft gain cannot offset a security, provenance, protected-task, Genesis, install, or rollback failure.

## Contract

Each metric declares:

- stable `metric_id`;
- direction (`higher`, `lower`, or `equal`);
- Baseline and Candidate value;
- whether it is hard;
- explicit regression tolerance;
- evidence reference.

Unknown, boolean, NaN, infinity, or missing values are rejected rather than converted to zero.

## Command

```bash
python3 scripts/wbi.py utility-gate \
  --contract templates/utility-guard-contract.json \
  --output /absolute/external/utility-result.json
```

The result contains the contract SHA-256, per-metric deltas, protected-check results and a content-bound decision.

## What it does not prove

The utility guard proves decision consistency under supplied evidence. It does not prove that the evidence came from a fair real-runtime benchmark; benchmark sealing, raw traces and external review remain separate gates.
