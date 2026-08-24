# Evaluation aggregate

- Run: `all`
- Profile: `quick`
- Result: **PASS**
- Candidate overall: `0.9122`
- Baseline overall: `0.7681`
- Delta: `0.1441`

## Gates

- PASS: `candidate_overall`
- PASS: `baseline_delta`
- PASS: `boundary`
- PASS: `fact_preservation`
- PASS: `no_candidate_critical_failure`
- PASS: `has_results`

## Suite means

```json
{
  "known": {
    "baseline": 0.825,
    "candidate": 0.9
  },
  "fact-preservation": {
    "baseline": 0.65,
    "candidate": 1.0
  },
  "boundary": {
    "baseline": 0.975,
    "candidate": 0.99
  },
  "voice": {
    "baseline": 0.96,
    "candidate": 0.915
  },
  "trajectory": {
    "baseline": 0.835,
    "candidate": 0.975
  },
  "contrast": {
    "baseline": 0.955,
    "candidate": 0.955
  },
  "style-decoy": {
    "baseline": 1.0,
    "candidate": 1.0
  },
  "task-completion": {
    "baseline": 0.82,
    "candidate": 0.84
  },
  "planning-fidelity": {
    "baseline": 0.72,
    "candidate": 0.96
  },
  "tool-use": {
    "baseline": 0.675,
    "candidate": 0.95
  },
  "capability-calibration": {
    "baseline": 0.86,
    "candidate": 0.975
  },
  "refusal-stop": {
    "baseline": 0.05,
    "candidate": 0.99
  },
  "long-horizon": {
    "baseline": 0.8,
    "candidate": 0.815
  },
  "identity-routing": {
    "baseline": 0.915,
    "candidate": 0.95
  },
  "anonymous-fidelity": {
    "baseline": 0.825,
    "candidate": 0.955
  },
  "token-efficiency": {
    "baseline": 0.425,
    "candidate": 0.425
  }
}
```

## Critical failures

- None

## Errors

- None
