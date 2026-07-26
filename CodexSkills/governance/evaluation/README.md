# Failure-to-Test conversion

Status:
`DRAFT_NON_ACTIVE_FAILURE_TO_TEST_CONVERSION_READY_SHADOW_FIXTURE_ONLY`

This directory implements the Mechanism-owned M-046 conversion boundary:

- `confirmed-failure-incident.json` is a synthetic, public-safe metadata
  fixture with confirmed privacy triage and root cause.
- `confirmed-regression-case.json` is its deterministic, lineage-bound
  regression metadata.
- `failure_to_test.py` is a pure converter and recomputation gate. It cannot
  read raw incident material, sealed-holdout content or labels, Git, runtime
  state, or a network.
- `failure-to-test-readiness.json` records the exact non-active trust and
  nonmutation state.

The fixtures prove the contract, not a production incident conversion. The
standalone M-045 repository artifact was not present when this corrective was
performed; its functional input requirements are reconstructed in a closed
incident schema and enforced fail-closed. A real incident, evaluator profile
update, regression execution, publication, or activation remains outside this
Phase.

Rebuild and verify from the repository root:

```bash
/usr/bin/python3 -B \
  CodexSkills/governance/tools/build_failure_to_test.py --check
/usr/bin/python3 -B -m unittest \
  CodexSkills.governance.tests.test_failure_to_test
```
