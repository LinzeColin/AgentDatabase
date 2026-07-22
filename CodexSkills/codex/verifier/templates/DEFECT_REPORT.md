# 开发修复单 — <目标项目> <失败Subject>

> 可直接交给新的开发线程。它定义必须修成的结果和复验 Oracle，不替 builder 臆测实现方案，也不修改 Product-Design-Taskpack。

## 总览

- 目标项目 / 路径 / 决策范围：
- Taskpack version / digest：
- 失败 Subject / 环境 / config / flags：
- 当前结论：`修复后再验 | 环境问题 | 任务包/需求待确认 | 无产品缺陷`

| L0 | L1 | L2 | 产品 | 测试 | 环境 | 需求 | Flaky |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

---

## <FINDING-ID> — <用人话描述问题>

- Type：`PRODUCT_DEFECT | TEST_DEFECT | ENVIRONMENT_DEFECT | REQUIREMENT_GAP | FLAKY_UNRESOLVED | OBSERVATION`
- Severity：`L0 | L1 | L2`
- Category：`ARTIFACT_IDENTITY | DELIVERY_CONTENT_MISMATCH | TASKPACK_INTEGRITY | ACCEPTANCE_ORACLE_DRIFT | TRACEABILITY_GAP | CORE_JOURNEY | DATA_LOSS_OR_CORRUPTION | AUTHZ_BYPASS | SECRET_OR_PRIVACY_LEAK | UNRECOVERABLE_MIGRATION | UNBOUNDED_SIDE_EFFECT_OR_COST | EVIDENCE_INTEGRITY | CRITICAL_FLAKY | NO_SAFE_RECOVERY | OTHER`
- Status：`OPEN | CONFIRMED | WAIVED | RETEST_PENDING | CLOSED`
- Non-waivable：`YES | NO`
- Requirement / Acceptance / Oracle / Task / Test IDs：
- 受影响用户/任务：
- **用户会遇到什么：**
- **为什么必须处理：**
- Reproduction：`<例如2/2; F/F>`

### 最短复现

前置：`<角色、数据、Subject、flags；不写秘密值>`

1.
2.
3.

### Expected / Actual

- Expected（引用锁定 Acceptance/Oracle）：
- Actual：

### 证据

| Path | SHA-256 | 证明内容 |
|---|---|---|
|  |  |  |

### 归因

- Classification evidence：
- Possible cause：`<INFERRED 或 unknown>`
- Confidence：`low | medium | high`
- Workaround / residual risk：

## 直接交给开发线程的任务

- **必须修成的用户/系统结果：**
- **必须新增/保留的回归 Oracle：**
- **不能破坏的既有行为：**
- 可能涉及模块：`<INFERRED；未知可空>`
- 数据/API/兼容/迁移影响：
- AI model/prompt/tool/retrieval影响（适用时）：
- 发布/回滚/前滚要求（适用时）：
- Taskpack / Oracle drift：`无 | 有；见finding`
- Taskpack规则：`不得在实现线程静默放宽/删除/替换 Acceptance；确需变更必须回到Owner重新授权新版本`
- Builder完成条件：`新不可变Subject + 修复测试 + 实际结果证据`

## 修复后 verifier 最少复验闭包

1. 新 Subject 和 source/snapshot→artifact→deployment 映射；
2. 任务包 digest、兼容性及 Oracle 漂移复核；
3. 原失败最小复现；
4. 新回归 Oracle；
5. 目标项目核心 journey；
6. 被修改表面的 affected checks 与 change-impact；
7. 失效的发布/运营/AI门。

### 自动扩大复验的条件

- API/schema/data/migration/auth/权限变化；
- shared/runtime dependency、Feature Flag、配置变化；
- model/prompt/tool/retrieval/policy变化；
- 修复跨出原最小闭包；
- Taskpack/Acceptance/Oracle发生变化；
- 旧证据或 baseline 已失效。

## 优先级

- ROI：`high | medium | low`
- 不修风险：`high | medium | low`
- 可立即执行程度：`high | medium | low`
