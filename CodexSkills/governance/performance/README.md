# M-066 performance and capacity budgets

Status: **DRAFT_NON_ACTIVE / UNCALIBRATED**

This directory implements the Mechanism-owned, bundle-external M-066
performance and capacity contract. It turns the Task Pack's provisional
thresholds into deterministic completeness and over-budget decisions without
claiming that a real production baseline already exists.

The pure guard in `capacity_budgets.py` accepts immutable profile objects. It
has no clock, profiler, filesystem, Git, cache, state, watermark, shard writer,
publisher, or network capability. The builder pins the immutable M-063 and
M-065 evidence, the M-043 scorecard schema, the M-028 global-index bytes, the
final 31/5 candidate, and the 20 MiB daily-shard contract. The M-028
delete/rebuild gate and current source freshness are not replayed or inferred
by this Phase.

## Fixed provisional thresholds

- Registry fast path: at most 60 seconds.
- Complete four-source inventory: at most 5 minutes.
- Exactly 10,000 public-safe events: at most 10 minutes and 512 MiB peak
  memory.
- One Git shard: at most 20 MiB; overage rotates a new shard.
- One canonical transaction: at most one commit.
- Repository growth forecast: at least 90 days of warning.
- Capability graph: filter candidates before pair analysis.
- Evaluation cache: bind Skill version, model snapshot, environment, evaluator
  manifest, dataset manifest, and tool manifest digests.

These thresholds are integrity guards, not a production SLA. A later
calibration needs real hardware and workload manifests plus both cold and warm
profiles. The checked-in readiness therefore remains
`BLOCKED_UNCALIBRATED`, with zero real profiles.

## Completeness before speed

Every profile must account for all inputs. `processed_count` must equal
`input_count`; `skipped_count` and `sampled_count` must be zero; truncation is
forbidden; Registry and inventory profiles must close all four source classes.
A failed or incomplete profile cannot advance a watermark. Over-budget
profiles return the exact remediation: diagnose without skipping, apply
backpressure/rotation without dropping events, abort the transaction, or raise
a MAJOR architecture proposal.

The profile schema is an evidence contract only. M-066 does not execute a real
profile, write a cache or shard, mutate state, publish, activate, or create
`CodexSkills/VERSION`.

## Reproduce

Run from the repository root with the provisioned interpreter:

```bash
/usr/bin/python3 -B \
  CodexSkills/governance/tools/build_performance_capacity_budgets.py --check
/usr/bin/python3 -B -m unittest \
  CodexSkills.governance.tests.test_performance_capacity_budgets
```

The next Phase is M-067,
`MECHANISM_DASHBOARDS_ACTIONABLE_ALERTS`.
