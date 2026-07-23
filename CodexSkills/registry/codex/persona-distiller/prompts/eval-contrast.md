# Contrast evaluator

## Objective

Compare candidate with no-skill baseline and a similar-person foil on a case where decision structure should differ. Score target-specific reasoning rather than general answer quality.

## Controls

- Use the same base model, tools, factual context, temperature, and prompt across systems.
- Randomize A/B/C identity; judges must not know which system produced an output.
- The builder Agent must not be the sole judge.
- Score atomic claims/turns and the overall answer.
- Mark fabricated quotes, material factual distortion, privacy breach, unsafe authority transfer, or Holdout leakage as critical failures.

## Output

Write one result record per judge/system/case to `evals/results.jsonl` with `case_id`, `suite`, randomized label, actual system kept in the private run plan, dimension scores, overall score, rationale, critical failure, and judge ID.
