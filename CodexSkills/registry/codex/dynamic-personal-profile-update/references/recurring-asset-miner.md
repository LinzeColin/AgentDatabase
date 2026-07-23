# Recurring Asset Miner

This is the accepted Stage 1 opportunity. It is an extraction workflow, not an automatic publisher.

## Input

- Dynamic profile entries with evidence from the fixed v0.0.0.1 derived allowlist.
- User instructions, revisions, successful deliveries, and failure repairs supplied in the current task context.

## Procedure

1. Group repeated behavior by task intent, not by identical wording only.
2. Separate evidence from the proposed reusable asset.
3. Classify the repeated shape:
   - repeated wording without a fixed sequence → Prompt Template;
   - stable input → action → output sequence → Workflow;
   - tool choice, judgment, exceptions, verification, or cross-context transfer → Skill;
   - date-only repetition → Schedule/Recurring Prompt;
   - analysis or speculation without a repeatable action → observation.
4. Produce one candidate with trigger, input, steps, output, exceptions, verification, evidence, confidence, and expiry.
5. Use the candidate once in a real task. Record whether it reduced clarification, rework, or context reconstruction. Do not automatically install, publish, or promote it.

## Candidate template

```text
asset_id:
asset_type: prompt_template | workflow | skill | schedule | observation
trigger:
user_problem:
inputs:
steps:
output:
exceptions:
verification:
evidence:
counterevidence:
confidence:
expiry_or_review_date:
validation_result: pending
promotion_decision: pending
```

There is no separate trial project or directory. A candidate remains pending until one real task demonstrates measurable usefulness; this validation is part of the miner, not another opportunity.
