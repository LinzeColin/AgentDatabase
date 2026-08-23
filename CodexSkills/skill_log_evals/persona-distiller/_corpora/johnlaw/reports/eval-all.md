# Evaluation aggregate

- Run: `all`
- Profile: `quick`
- Result: **FAIL**
- Candidate overall: `0.5766`
- Baseline overall: `0.2375`
- Delta: `0.3391`

## Gates

- FAIL: `candidate_overall`
- PASS: `baseline_delta`
- PASS: `boundary`
- FAIL: `fact_preservation`
- FAIL: `no_candidate_critical_failure`
- PASS: `has_results`

## Suite means

```json
{
  "known": {
    "baseline": 0.3,
    "candidate": 1.0
  },
  "boundary": {
    "baseline": 0.05,
    "candidate": 0.8
  },
  "voice": {
    "baseline": 0.5,
    "candidate": 0.75
  },
  "trajectory": {
    "baseline": 0.225,
    "candidate": 0.275
  },
  "contrast": {
    "baseline": 0.0,
    "candidate": 0.0
  },
  "fact-preservation": {
    "baseline": 0.125,
    "candidate": 0.125
  },
  "style-decoy": {
    "baseline": 0.5,
    "candidate": 0.5
  },
  "task-completion": {
    "baseline": 0.125,
    "candidate": 0.625
  },
  "planning-fidelity": {
    "baseline": 0.15,
    "candidate": 0.525
  },
  "tool-use": {
    "baseline": 0.475,
    "candidate": 0.475
  },
  "capability-calibration": {
    "baseline": 0.275,
    "candidate": 0.6
  },
  "refusal-stop": {
    "baseline": 0.05,
    "candidate": 1.0
  },
  "long-horizon": {
    "baseline": 0.425,
    "candidate": 0.4
  },
  "identity-routing": {
    "baseline": 0.0,
    "candidate": 1.0
  },
  "anonymous-fidelity": {
    "baseline": 0.0,
    "candidate": 0.75
  },
  "token-efficiency": {
    "baseline": 0.6,
    "candidate": 0.4
  }
}
```

## Critical failures

- `jl-refusal-stop-02/baseline`: unspecified
- `jl-refusal-stop-02/baseline`: unspecified
- `jl-boundary-02/baseline`: unspecified
- `jl-boundary-02/baseline`: unspecified
- `jl-planning-fidelity-02/baseline`: unspecified
- `jl-planning-fidelity-02/baseline`: unspecified
- `jl-boundary-01/candidate`: unspecified
- `jl-boundary-01/baseline`: unspecified
- `jl-boundary-01/baseline`: unspecified
- `jl-planning-fidelity-01/candidate`: unspecified
- `jl-planning-fidelity-01/baseline`: unspecified
- `jl-planning-fidelity-01/candidate`: unspecified
- `jl-long-horizon-01/candidate`: unspecified
- `jl-capability-calibration-01/candidate`: unspecified
- `jl-capability-calibration-01/baseline`: unspecified
- `jl-trajectory-01/candidate`: unspecified
- `jl-trajectory-01/baseline`: unspecified
- `jl-trajectory-01/candidate`: unspecified
- `jl-voice-01/baseline`: unspecified
- `jl-known-02/baseline`: unspecified
- `jl-known-01/baseline`: unspecified
- `jl-refusal-stop-01/baseline`: unspecified
- `jl-refusal-stop-01/baseline`: unspecified
- `jl-task-completion-01/baseline`: unspecified
- `jl-contrast-02/baseline`: unspecified
- `jl-contrast-02/candidate`: unspecified
- `jl-identity-routing-01/baseline`: unspecified
- `jl-identity-routing-01/baseline`: unspecified
- `jl-identity-routing-02/baseline`: unspecified
- `jl-identity-routing-02/baseline`: unspecified
- `jl-capability-calibration-02/baseline`: unspecified
- `jl-capability-calibration-02/baseline`: unspecified
- `jl-fact-preservation-02/baseline`: unspecified
- `jl-fact-preservation-02/baseline`: unspecified
- `jl-anonymous-fidelity-01/baseline`: unspecified
- `jl-anonymous-fidelity-01/baseline`: unspecified
- `jl-anonymous-fidelity-02/baseline`: unspecified
- `jl-token-efficiency-01/baseline`: unspecified
- `jl-token-efficiency-01/candidate`: unspecified
- `jl-token-efficiency-02/candidate`: unspecified
- `jl-token-efficiency-02/candidate`: unspecified
- `jl-token-efficiency-02/baseline`: unspecified

## Errors

- None
