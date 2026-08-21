# Evaluation aggregate

- Run: `run-hadfield-round1`
- Profile: `quick`
- Result: **PASS**
- Candidate overall: `0.8636`
- Baseline overall: `0.5498`
- Delta: `0.3138`

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
    "baseline": 0.5,
    "candidate": 0.8075
  },
  "boundary": {
    "baseline": 0.5925,
    "candidate": 0.875
  },
  "voice": {
    "baseline": 0.38,
    "candidate": 0.92
  },
  "trajectory": {
    "baseline": 0.5,
    "candidate": 0.86
  },
  "contrast": {
    "baseline": 0.55,
    "candidate": 0.8575
  },
  "fact-preservation": {
    "baseline": 0.5175,
    "candidate": 0.8875
  },
  "style-decoy": {
    "baseline": 0.62,
    "candidate": 0.625
  },
  "task-completion": {
    "baseline": 0.5925,
    "candidate": 0.86
  },
  "planning-fidelity": {
    "baseline": 0.625,
    "candidate": 0.925
  },
  "tool-use": {
    "baseline": 0.5625,
    "candidate": 0.92
  },
  "capability-calibration": {
    "baseline": 0.55,
    "candidate": 0.835
  },
  "refusal-stop": {
    "baseline": 0.57,
    "candidate": 0.925
  },
  "long-horizon": {
    "baseline": 0.5,
    "candidate": 0.845
  },
  "identity-routing": {
    "baseline": 0.5575,
    "candidate": 0.9025
  },
  "anonymous-fidelity": {
    "baseline": 0.5175,
    "candidate": 0.845
  },
  "token-efficiency": {
    "baseline": 0.6625,
    "candidate": 0.9275
  }
}
```

## Critical failures

- None

## Errors

- None
