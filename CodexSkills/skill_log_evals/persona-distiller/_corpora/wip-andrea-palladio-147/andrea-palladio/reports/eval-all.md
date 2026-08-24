# Evaluation aggregate

- Run: `all`
- Profile: `quick`
- Result: **PASS**
- Candidate overall: `0.9916`
- Baseline overall: `0.6853`
- Delta: `0.3063`

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
    "candidate": 1.0
  },
  "boundary": {
    "baseline": 1.0,
    "candidate": 1.0
  },
  "voice": {
    "baseline": 0.5,
    "candidate": 1.0
  },
  "trajectory": {
    "baseline": 0.5,
    "candidate": 0.95
  },
  "contrast": {
    "baseline": 1.0,
    "candidate": 1.0
  },
  "fact-preservation": {
    "baseline": 1.0,
    "candidate": 1.0
  },
  "style-decoy": {
    "baseline": 1.0,
    "candidate": 1.0
  },
  "task-completion": {
    "baseline": 0.45,
    "candidate": 1.0
  },
  "planning-fidelity": {
    "baseline": 1.0,
    "candidate": 1.0
  },
  "tool-use": {
    "baseline": 0.15,
    "candidate": 1.0
  },
  "capability-calibration": {
    "baseline": 0.5,
    "candidate": 1.0
  },
  "refusal-stop": {
    "baseline": 0.5,
    "candidate": 1.0
  },
  "long-horizon": {
    "baseline": 0.5,
    "candidate": 1.0
  },
  "identity-routing": {
    "baseline": 1.0,
    "candidate": 0.95
  },
  "anonymous-fidelity": {
    "baseline": 0.915,
    "candidate": 0.965
  },
  "token-efficiency": {
    "baseline": 0.45,
    "candidate": 1.0
  }
}
```

## Critical failures

- None

## Errors

- None
