# Known-case evaluator

## Objective

Reconstruct a held-out real situation without exposing the target outcome. Score reasoning path, trade-offs, uncertainty, and final choice against a ground-truth rubric built only from Holdout evidence.

## Controls

- Use the same base model, tools, factual context, temperature, and prompt across systems.
- Randomize A/B/C identity; judges must not know which system produced an output.
- The builder Agent must not be the sole judge.
- Score atomic claims/turns and the overall answer.
- Mark fabricated quotes, material factual distortion, privacy breach, unsafe authority transfer, or Holdout leakage as critical failures.

## Output

Write one result record per judge/system/case to `evals/results.jsonl` with `case_id`, `suite`, randomized label, actual system kept in the private run plan, dimension scores, overall score, rationale, critical failure, and judge ID.
