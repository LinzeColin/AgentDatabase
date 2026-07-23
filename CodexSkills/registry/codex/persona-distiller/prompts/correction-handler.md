# Correction Handler

## Objective

Translate a user's correction or new evidence into an append-only correction event and a bounded model update.

## Procedure

1. Classify scope: facts, persona, work, boundary, hypothesis, or evaluation.
2. Separate the user's desired model behavior from a historical factual assertion.
3. Ask for or locate evidence only when a factual Claim about a third party changes; do not block a user preference correction for their own private/self model.
4. Record affected Claim IDs, source IDs, rationale, status, superseded correction, and impacted suites.
5. Run `correction_manager.py add` and regenerate `ACTIVE.md`.
6. Snapshot before editing model files.
7. Apply the smallest affected change.
8. Re-run impacted tests plus boundary and fact-preservation smoke cases.
9. Promote or rollback; retain the correction event either way with its final status.

Corrections have precedence over lower-confidence persona patterns but cannot override objective facts, safety rules, or legal boundaries without evidence and review.
