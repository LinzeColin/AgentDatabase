# Evaluation aggregate

- Run: `all`
- Profile: `quick`
- Result: **PASS**
- Candidate overall: `0.9456`
- Baseline overall: `0.6356`
- Delta: `0.3100`

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
    "baseline": 0.975,
    "candidate": 0.965
  },
  "boundary": {
    "baseline": 0.44,
    "candidate": 0.975
  },
  "voice": {
    "baseline": 0.81,
    "candidate": 0.94
  },
  "trajectory": {
    "baseline": 0.25,
    "candidate": 0.84
  },
  "contrast": {
    "baseline": 0.955,
    "candidate": 0.955
  },
  "fact-preservation": {
    "baseline": 0.91,
    "candidate": 1.0
  },
  "style-decoy": {
    "baseline": 0.125,
    "candidate": 0.95
  },
  "task-completion": {
    "baseline": 0.76,
    "candidate": 0.815
  },
  "planning-fidelity": {
    "baseline": 0.785,
    "candidate": 0.955
  },
  "tool-use": {
    "baseline": 0.175,
    "candidate": 0.925
  },
  "capability-calibration": {
    "baseline": 0.525,
    "candidate": 0.975
  },
  "refusal-stop": {
    "baseline": 0.225,
    "candidate": 0.95
  },
  "long-horizon": {
    "baseline": 0.8,
    "candidate": 0.955
  },
  "identity-routing": {
    "baseline": 0.905,
    "candidate": 0.975
  },
  "anonymous-fidelity": {
    "baseline": 0.93,
    "candidate": 0.955
  },
  "token-efficiency": {
    "baseline": 0.6,
    "candidate": 1.0
  }
}
```

## Critical failures

- None

## Errors

- None
