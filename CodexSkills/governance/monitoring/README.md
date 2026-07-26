# Freshness and drift monitoring

This directory materializes the Mechanism-owned, non-active implementation of
Task Pack `M-058`.

`freshness_drift.py` is a pure monitor. It consumes an exact EvalProfile,
Scorecard, and content-addressed observation, then deterministically produces
the only valid report for that input. The report covers:

- UTC expiry from both `freshness_valid_until` and
  `freshness_policy.max_age_days`;
- all seven Scorecard behavior dimensions;
- p95 latency regression and minimum-sample shortfall;
- Skill, model, tool, dependency, dataset, evaluator, policy, and environment
  context changes;
- critical incidents; and
- missing EvalProfile retest triggers that would otherwise suppress a
  required re-evaluation.

The observation and report schemas are bundle-external. A caller must pin
their canonical schema digests explicitly before adding them to a trusted
offline Registry. Neither repository presence nor a self-consistent document
is a trust root.

`validate_freshness_drift_report()` recomputes the complete report and requires
exact RFC 8785 JCS equivalence. Deleting alerts, changing a gate result, using
another Scorecard/Profile/observation/decision digest, or moving the
observation after the decision fails closed.

`append_monitored_promotion_decision()` is the canonical M-058 promotion
entrypoint. A `PROMOTE` decision requires one exact `PROMOTION_GATE` report per
referenced Scorecard, with `status=PASS`, no alerts, current freshness, exact
decision binding, and observation time no later than decision time. Only then
is the immutable M-056 append function called. A caller cannot use the lower
level M-056 function as evidence that the M-058 freshness gate passed.

The M-056 and M-057 source objects remain immutable predecessor evidence.
This Phase creates no state, Registry mutation, Git write, notification,
`CodexSkills/VERSION`, activation, or canonical publication. The real
registered snapshot has no evaluated champion or challenger, so real monitor
or promotion execution remains forbidden.

Reproduce the generated schemas and readiness material from the repository
root:

```bash
/usr/bin/python3 -B \
  CodexSkills/governance/tools/build_freshness_drift_monitor.py --check
/usr/bin/python3 -B -m unittest \
  CodexSkills.governance.tests.test_freshness_drift_monitor
```
