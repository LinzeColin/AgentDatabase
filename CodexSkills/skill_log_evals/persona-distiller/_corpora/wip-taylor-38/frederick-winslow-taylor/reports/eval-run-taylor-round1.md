# Evaluation aggregate

- Run: `run-taylor-round1`
- Profile: `quick`
- Result: **PASS**
- Candidate overall: `0.8569`
- Baseline overall: `0.6942`
- Delta: `0.1627`

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
    "baseline": 0.6325,
    "candidate": 0.8825
  },
  "boundary": {
    "baseline": 0.695,
    "candidate": 0.8875
  },
  "voice": {
    "baseline": 0.4425,
    "candidate": 0.7525
  },
  "trajectory": {
    "baseline": 0.6875,
    "candidate": 0.875
  },
  "contrast": {
    "baseline": 0.75,
    "candidate": 0.805
  },
  "fact-preservation": {
    "baseline": 0.7,
    "candidate": 0.82
  },
  "style-decoy": {
    "baseline": 0.75,
    "candidate": 0.8825
  },
  "task-completion": {
    "baseline": 0.7575,
    "candidate": 0.84
  },
  "planning-fidelity": {
    "baseline": 0.7125,
    "candidate": 0.875
  },
  "tool-use": {
    "baseline": 0.7325,
    "candidate": 0.875
  },
  "capability-calibration": {
    "baseline": 0.77,
    "candidate": 0.87
  },
  "refusal-stop": {
    "baseline": 0.75,
    "candidate": 0.8825
  },
  "long-horizon": {
    "baseline": 0.725,
    "candidate": 0.86
  },
  "identity-routing": {
    "baseline": 0.745,
    "candidate": 0.855
  },
  "anonymous-fidelity": {
    "baseline": 0.72,
    "candidate": 0.88
  },
  "token-efficiency": {
    "baseline": 0.5375,
    "candidate": 0.8675
  }
}
```

## Critical failures

- None

## Errors

- None
