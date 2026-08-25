# Static Evidence Control Console

The control console reduces operator ambiguity without becoming a second source of truth. It is generated from machine-readable data, uses no external scripts, escapes all supplied text and does not mutate evidence.

```bash
python3 scripts/wbi.py render-dashboard \
  --input templates/dashboard-data.json \
  --output /absolute/external/teleiosis-dashboard.html
```

The cyan-blue default is deliberately restrained and can be replaced by downstream CSS. The console presents:

- seven independent status domains;
- material improvements;
- unresolved blockers;
- accountable next actions;
- evidence metrics and references.

A green card is a rendering of a supplied state, not a verdict. `OUTCOME_NOT_PROVEN`, `REVIEW_UNAVAILABLE`, and `FORMAL_PROMOTION_BLOCKED` remain visible even when engineering checks pass.
