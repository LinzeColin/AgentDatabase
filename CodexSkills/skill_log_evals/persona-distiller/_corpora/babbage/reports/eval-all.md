# Evaluation aggregate

- Run: `all`
- Profile: `quick`
- Result: **PASS**
- Candidate overall: `0.9930`
- Baseline overall: `0.8352`
- Delta: `0.1578`

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
    "candidate": 1.0
  },
  "boundary": {
    "baseline": 0.8875,
    "candidate": 0.9875
  },
  "voice": {
    "baseline": 0.8,
    "candidate": 0.9875
  },
  "trajectory": {
    "baseline": 0.9875,
    "candidate": 0.9875
  },
  "contrast": {
    "baseline": 0.9875,
    "candidate": 0.975
  },
  "fact-preservation": {
    "baseline": 1.0,
    "candidate": 1.0
  },
  "style-decoy": {
    "baseline": 0.8125,
    "candidate": 0.9875
  },
  "task-completion": {
    "baseline": 0.975,
    "candidate": 0.9875
  },
  "planning-fidelity": {
    "baseline": 0.5,
    "candidate": 1.0
  },
  "tool-use": {
    "baseline": 0.675,
    "candidate": 1.0
  },
  "capability-calibration": {
    "baseline": 0.9375,
    "candidate": 0.9875
  },
  "refusal-stop": {
    "baseline": 1.0,
    "candidate": 1.0
  },
  "long-horizon": {
    "baseline": 1.0,
    "candidate": 1.0
  },
  "identity-routing": {
    "baseline": 0.525,
    "candidate": 1.0
  },
  "anonymous-fidelity": {
    "baseline": 0.75,
    "candidate": 0.9875
  },
  "token-efficiency": {
    "baseline": 0.55,
    "candidate": 1.0
  }
}
```

## Critical failures

- None

## Errors

- None
