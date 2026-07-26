# SkillOps operational dashboard

Status: **DRAFT_NON_ACTIVE_ALERTS_PRESENT**

This is a deterministic, non-active evidence projection. It is not live telemetry and does not send notifications.

## Views

| View | Status | Evidence |
|---|---|---|
| HEALTH | CRITICAL | [CAPACITY](../performance/performance-capacity-readiness.json), [FRESHNESS](freshness-drift-readiness.json), [MANAGED_RAW](../retention/managed-raw-72h-readiness.json), [ACTIVE_TREE](../retention/git-active-tree-365d-readiness.json) |
| PRIVACY | CRITICAL | [MANAGED_RAW](../retention/managed-raw-72h-readiness.json) |
| FRESHNESS | WARNING | [FRESHNESS](freshness-drift-readiness.json) |
| RETENTION | CRITICAL | [ACTIVE_TREE](../retention/git-active-tree-365d-readiness.json) |
| CAPACITY | WARNING | [CAPACITY](../performance/performance-capacity-readiness.json) |

## Actionable alerts

| Severity | Category | Owner | Action | Evidence |
|---|---|---|---|---|
| WARNING | FRESHNESS | MECHANISM | `REGISTER_EVALUATED_VERSION_AND_RUN_FRESHNESS_MONITOR` | [FRESHNESS](freshness-drift-readiness.json) |
| CRITICAL | PRIVACY | AUTO | `BIND_MANAGED_RAW_EXECUTOR_AND_CERTIFY_RUNTIME` | [MANAGED_RAW](../retention/managed-raw-72h-readiness.json) |
| CRITICAL | RETENTION | AUTO | `BIND_ACTIVE_TREE_EXECUTOR_AND_VALIDATE_LEDGER` | [ACTIVE_TREE](../retention/git-active-tree-365d-readiness.json) |
| WARNING | CAPACITY | MECHANISM | `CAPTURE_REAL_COLD_WARM_CAPACITY_BASELINES` | [CAPACITY](../performance/performance-capacity-readiness.json) |

Every alert above has an accountable owner, one fixed action code, and at least one digest-bound evidence link.
