# RELEASE ASSURANCE — <目标项目> <候选Subject>

> `NOT_APPLICABLE` 必须写原因；有发布意图时不得空着。

## 授权与身份链

- Product-Design-Taskpack version / full-pack digest / seven-role contract digest：
- Authorization reference / evidence：
- Candidate identity（必须等于 artifact SHA-256 或 image digest）：

| Subject | Identity | Mapping evidence | Status |
|---|---|---|---|
| Authorized Taskpack |  |  |  |
| Source snapshot / revision |  |  |  |
| Build |  |  |  |
| Artifact/Image |  |  |  |
| Deployment |  |  |  |
| Runtime config / flags / schema |  |  |  |
| SBOM / provenance / signature |  |  |  |

## Acceptance 与变更影响

- Acceptance覆盖：`<mapped>/<declared>`
- Task引用完整性：
- Change-impact records：
- Taskpack compatibility evidence：
- Drift evidence / result：
- Taskpack / release contract drift：`无 | 有；见finding`

## Baseline / Control

- 上一已接受版本 / root hash：
- Control identity：
- 无 baseline 的原因与补偿：

## 运营就绪

| Gate | Expected | Actual | Status | Evidence/Owner |
|---|---|---|---|---|
| Owner / on-call / escalation |  |  |  |  |
| Dashboard / logs / traces / queries |  |  |  |  |
| Alert trigger and delivery |  |  |  |  |
| SLO / health objectives |  |  |  |  |
| Capacity / rate / quota / cost |  |  |  |  |
| Runbook / known failure modes |  |  |  |  |
| Backup / restore |  |  |  |  |

## 兼容、迁移与恢复

| Check | Expected | Actual | Status | Evidence |
|---|---|---|---|---|
| Fresh install / upgrade |  |  |  |  |
| Old↔new / mixed-version |  |  |  |  |
| Migration idempotency / resume |  |  |  |  |
| Partial deployment failure |  |  |  |  |
| Rollback |  |  |  |  |
| Roll-forward / restore |  |  |  |  |
| Data invariants after recovery |  |  |  |  |

## 渐进发布

- Strategy：`canary | ring | blue-green | rolling | not-applicable`
- Candidate / control / rollout groups：
- Health signals / business invariants / taskpack success metrics：
- Abort conditions / continuous window / kill action：
- Required bake：

| Group | Exposure | Start/End | Observed bake | Health | Business | Contract drift | Decision | Evidence |
|---|---|---|---:|---|---|---|---|---|
|  |  |  |  |  |  |  |  |  |

## Post-deploy

- Actual deployment identity / mapping evidence：
- Runtime config/model/prompt/tool/schema drift：
- Observation window / core journey sample：
- Alerts/incidents/rollback events：
- Decision：`PROMOTE | HOLD | ROLLBACK | NOT_APPLICABLE`
- Evidence：
