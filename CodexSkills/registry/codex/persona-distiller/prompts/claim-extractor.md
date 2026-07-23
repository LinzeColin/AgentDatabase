# Claim Extractor

## Objective

Convert source-linked observations into atomic, falsifiable Claim records without writing polished persona prose.

## Rules

- One Claim should express one proposition.
- Use `fact`, `pattern`, `hypothesis`, or `unknown`; do not inflate status.
- A model/heuristic pattern needs independent clusters and different contexts before release.
- Holdout IDs are forbidden in supporting sources.
- Record counterevidence and credible alternatives.
- Add time and applicability scope.
- Define what evidence would downgrade or falsify the Claim.
- Avoid trait labels such as “visionary,” “rational,” or “empathetic” unless translated into observable decision rules.
- Separate public role behavior from claimed private motives.
- Never infer diagnosis, protected attributes, or intimate facts without explicit authorized evidence.

## Output contract

Append valid JSON objects to `evidence/claims.jsonl` using `scripts/ledger.py claim-add` where practical. Then produce a review table:

```text
claim_id | status | category | proposition | support clusters | contexts | counterevidence | confidence | time scope | decision
```

Mark insufficient candidates as `unknown` or reject them; do not force the target number of models.
