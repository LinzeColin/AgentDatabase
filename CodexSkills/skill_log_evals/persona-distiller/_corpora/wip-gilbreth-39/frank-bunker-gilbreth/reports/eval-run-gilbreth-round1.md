# Evaluation aggregate

- Run: `run-gilbreth-round1`
- Profile: `quick`
- Result: **PASS**
- Candidate overall: `0.9047`
- Baseline overall: `0.4427`
- Delta: `0.4620`

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
    "baseline": 0.4025,
    "candidate": 0.9
  },
  "boundary": {
    "baseline": 0.4075,
    "candidate": 0.9125
  },
  "voice": {
    "baseline": 0.465,
    "candidate": 0.905
  },
  "trajectory": {
    "baseline": 0.4425,
    "candidate": 0.9075
  },
  "contrast": {
    "baseline": 0.5475,
    "candidate": 0.9
  },
  "fact-preservation": {
    "baseline": 0.275,
    "candidate": 0.925
  },
  "style-decoy": {
    "baseline": 0.3375,
    "candidate": 0.8975
  },
  "task-completion": {
    "baseline": 0.425,
    "candidate": 0.91
  },
  "planning-fidelity": {
    "baseline": 0.485,
    "candidate": 0.9025
  },
  "tool-use": {
    "baseline": 0.395,
    "candidate": 0.9125
  },
  "capability-calibration": {
    "baseline": 0.475,
    "candidate": 0.895
  },
  "refusal-stop": {
    "baseline": 0.5425,
    "candidate": 0.905
  },
  "long-horizon": {
    "baseline": 0.5425,
    "candidate": 0.9
  },
  "identity-routing": {
    "baseline": 0.5,
    "candidate": 0.8925
  },
  "anonymous-fidelity": {
    "baseline": 0.54,
    "candidate": 0.8925
  },
  "token-efficiency": {
    "baseline": 0.3,
    "candidate": 0.9175
  }
}
```

## Critical failures

- None

## Errors

- None
