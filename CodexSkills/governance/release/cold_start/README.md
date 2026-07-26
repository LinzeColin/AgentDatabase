# Mechanism cold-start release review

Status:
`DRAFT_NON_ACTIVE_MECHANISM_TASKPACK_RELEASE_REVIEW_COMPLETE_WITH_BLOCKERS`

This directory implements the final Mechanism Task Pack task, M-069. It
materializes:

- `evidence-index.json`: 23 sorted, unique, external-Git-bound evidence
  records spanning the candidate, consumer, Registry/resolver, controlled
  iteration, retention, migration, operations, and representative pilots;
- `cold-start-handoff.json`: the exact machine state, blockers, nonmutation
  boundary, validation baseline, and stop decision;
- two closed bundle-external schemas for those artifacts.

The deterministic builder also produces the human cold-start entry
`CodexSkills/HANDOFF.md` and `CodexSkills/CHANGELOG.md`. A new agent needs no
chat context: it can run the two commands in the human Handoff and reconstruct
the same machine state from repository bytes and named Git objects.

M-069 is Task Pack completion evidence, not production readiness. The package
ends at M-069; no M-070 exists. Registry/mirror parity, resolver/control/Auto
integration, schedule authority, external Gmail/state readiness, production
pilots, ACTIVE trust, VERSION, canonical publication, migration execution,
and activation remain blocked or false. The only next action after remote
readback is `OWNER_SELECT_AND_RUN_FRESH_VERIFIER`.

Validate from the repository root:

```bash
/usr/bin/python3 -B \
  CodexSkills/governance/tools/build_cold_start_release_review.py --check
/usr/bin/python3 -B -m unittest \
  CodexSkills.governance.tests.test_cold_start_release_review
```
