# Recurring Asset Miner

This is the accepted Stage 1 opportunity. It is an extraction workflow, not an automatic publisher.

## Input

- Dynamic profile entries with evidence.
- Existing redacted derived behavior, recommendation, timeline, and personalization reports.
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
5. Run one low-cost real trial. Record pass/fail in the Skill evaluation area. Do not automatically install, publish, or promote it.

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
trial_result: pending
promotion_decision: pending
```

`Emerging Capability Trial` is retained only as this one-trial gate. It is not an independent project or directory.
