# Failure Modes

| Failure | Detection | Response |
|---|---|---|
| Genesis/source drift | external hash or one-line transition mismatch | fail closed; no auto-sign |
| Baseline/control plane changed | tree hash mismatch | restore frozen copy and invalidate run |
| Candidate edits its exam | contract/holdout/control hash mismatch | invalidate run |
| Five links masquerade as peers | evidence profile/commit/artifact missing | exclude and block quota |
| Local fixture counted as real peer | `production_eligible=false` | exclude |
| Green CI but stale output | live artifact/time/reproduction mismatch | live gate FAIL |
| Weighted score hides regression | hard gate or protected subgroup | reject candidate |
| Same actor modifies and verifies | actor/context/provider ID collision | review gate BLOCKED |
| Reviewer fallback called independent | mode/capability mismatch | `INDEPENDENT_REVIEW_UNAVAILABLE` |
| Third-party code runs implicitly | process/security record | discard environment, security FAIL |
| Long prompt grows without utility | token/file delta with no measured gain | REVERT/NO_CHANGE |
| Loop repeats state | repeated tree hash/no-gain/budget | SATURATED or BLOCKED |
| Install self-test recurses | installer invokes a full suite that re-enters package/install tests | split structural/release/deep; release smoke is non-recursive |
| Source archive changes during installation | private before/copy/after snapshot hash mismatch | abort before extraction; no transaction switch |
| Internal lock/transaction path is a symlink | no-follow/private controller-path check | block before writes; do not follow external path |
| Archive/root/destination/rollback symlink or secret | package/install preflight | block; rebuild or select a canonical non-symlink path |
| Caller dies after predecessor rename but before backup receipt | transaction predecessor hash matches generated backup | reconstruct receipt and restore; otherwise remain `BLOCKED` |
| Caller dies with a pre-switch incoming copy | bounded generated incoming path plus no destination/backup switch | remove partial copy and mark `ABORTED_NO_SWITCH` |
| Caller dies after atomic switch | stdout missing but durable transaction exists | query `install-status`; commit valid switched hash or run safe recovery |
| Concurrent install/recovery | process-scoped root lock unavailable | return `BLOCKED`; never mutate concurrently |
| Backup manifest changed | schema 1.1 full restored-tree hash mismatch | reject rollback; retain current installation |
| Old schema 1.0 backup | explicit legacy receipt path | allow only identity/hash-compatible rollback and mark `legacy_receipt=true` |
| “Best” claim outlives evidence | validity/reheat check | `REHEAT_REQUIRED` |
