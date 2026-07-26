# SkillOps Mechanism cold-start handoff

Status: `DRAFT_NON_ACTIVE_MECHANISM_TASKPACK_RELEASE_REVIEW_COMPLETE_WITH_BLOCKERS`

This is the canonical human cold-start entry for Mechanism Task Pack v0.0.0.2.
The pack ends at M-069; there is no M-070. A new agent can recover the exact
state from this repository without chat history by running:

```bash
/usr/bin/python3 -B \
  CodexSkills/governance/tools/build_cold_start_release_review.py --check
/usr/bin/python3 -B -m unittest \
  CodexSkills.governance.tests.test_cold_start_release_review
```

## Exact trust roots

- Reviewed predecessor: `sha1:1fb0f80a3f90bf1e1dfc41d04556f7088b004b2d`
- Candidate bundle: `36f0c66dd54d36365700a13f614a8c9bfa9619fb7c532af77566a858175b835e` (31 schemas / 5 policies / CANDIDATE)
- Evidence index: `CodexSkills/governance/release/cold_start/evidence-index.json`
- Evidence index self digest: `e708086479475b13189c75be328524868d8495a7c527ae0c7ccbeaf3e9fc8a53`
- Repository self-report is not a trust root; the builder verifies every indexed
  path against its external Git object and the reviewed predecessor.

## Current truthful state

- Registry Identity/Instance/Version: `89/89/89`; binding-eligible: `0`.
- Registered snapshot vs current mirror instances: `89/90`; parity: `false`.
- Representative pilots: `3` pilots / `9` stable metadata-only Shadow cycles
  / `9` synthetic rollback drills; no production pilot ran.
- Schedule authority remains unresolved between `04:15` and `05:30` Australia/Sydney.
- `CodexSkills/VERSION` is absent. ACTIVE trust, runtime state, canonical
  shards/publication, Gmail readiness, migration, and activation remain false.
- M-069 completes the Task Pack review artifact, not production activation.

## Known fail-closed blockers

- `ACTIVATION_CONTROL_INTERFACE_SEMANTIC_MISMATCH`
- `ACTIVE_TRUST_ABSENT`
- `AUTO_REGISTRY_MIRROR_SKILL_COUNT_DRIFT`
- `BOUND_REFERENCE_RESOLVER_RUNTIME_LOCAL_DRIFT`
- `EXTERNAL_GMAIL_STATE_READINESS_UNVERIFIED`
- `PRODUCTION_PILOTS_NOT_RUN`
- `SCHEDULE_AUTHORITY_UNRESOLVED`

## Last accepted validation baseline

- M-068 target: `20/20 PASS`
- Complete Mechanism before M-069: `307/307 PASS`
- Schema sets: `21 / 41 / 24 / 85`; candidate trust: `31 / 5`.
- OpenAIDatabase consumer: `23/23 PASS`; canonical publication=false.
- Auto transition baseline: `200 tests / 5 failures / 20 errors`.
- Fault/privacy seeds 271828 and 314159: each `149 / 5 failures / 25 errors`.

## Stop condition and next action

Mechanism development stops after M-069 remote readback. No further Mechanism
Task Pack phase exists. Do not activate, publish, create VERSION, change schedule,
repair Auto-owned files, or call a development verifier. The only next action is:

`OWNER_SELECT_AND_RUN_FRESH_VERIFIER`

The machine handoff is at `CodexSkills/governance/release/cold_start/cold-start-handoff.json`; the release changelog is at `CodexSkills/CHANGELOG.md`.
