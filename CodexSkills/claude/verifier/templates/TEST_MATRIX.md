# TEST MATRIX — <目标项目> <锁定Subject>

## 本次裁决边界

- Decision scope：`developer_check | release_candidate | staged_release | post_deploy`
- 仓库 / 目标项目 / 路径：
- Product-Design-Taskpack version / full-pack digest / contract digest / source snapshot：
- 不可变 Subject identity：
- 最小验收闭包 / 本次未验收项目：
- Risk / Profile / Baseline：
- Traceability：`<mapped>/<declared> Acceptance；change-impact=<n>`
- Change impact evidence：

状态只使用：`PLANNED | RUNNING | PASS | FAIL | BLOCKED | NOT_RUN | NOT_APPLICABLE | WAIVED`。

## 核心门

| ID | Gate | Blocking | 要证明什么 | Expected | Actual | Status | Evidence | Finding/Reason |
|---|---|---:|---|---|---|---|---|---|
| G-001 | taskpack_integrity | conditional | 完整源快照、完整包/七角色双摘要、授权和ID清单可信 |  |  | PLANNED |  |  |
| G-002 | taskpack_compatibility | conditional | 任务包适用于目标、Subject和范围 |  |  | PLANNED |  |  |
| G-003 | taskpack_drift | conditional | 实现/配置/Oracle未偏离授权包 |  |  | PLANNED |  |  |
| G-004 | traceability | yes | Acceptance→Task→Test→Evidence→Subject闭合 |  |  | PLANNED |  |  |
| G-005 | subject_identity | yes | source/snapshot、制品和部署身份一致 |  |  | PLANNED |  |  |
| G-006 | build_start_health | yes | 可构建/启动/健康，或有明确N/A |  |  | PLANNED |  |  |
| G-007 | core_journey | yes | 用户核心结果真实完成 |  |  | PLANNED |  |  |
| G-008 | data_or_output | yes | 数据/文件/API/下游世界状态正确 |  |  | PLANNED |  |  |
| G-009 | changed_scope_regression | yes | 变更没有破坏关键既有行为 |  |  | PLANNED |  |  |
| G-010 | safety_security | conditional | 权限、安全、隐私和副作用边界 |  |  | PLANNED |  |  |
| G-011 | operational_readiness | release | 监控、告警、Owner、容量和恢复就绪 |  |  | PLANNED |  |  |
| G-012 | rollback_or_rollforward | release | 失败后可验证恢复 |  |  | PLANNED |  |  |
| G-013 | staged_release_observation | staged/post | 灰度、bake和业务不变量达标 |  |  | PLANNED |  |  |
| G-014 | ai_eval | AI | 多trial、独立grader、安全和成本达标 |  |  | PLANNED |  |  |

> Gate ID 可按项目调整；`RUN_MANIFEST.results[].gate` 的语义名必须保持稳定。

## 详细检查

| Test ID | Req | Acceptance | Oracle | Task IDs | Dim | Risk | Method/Command | Expected | Actual | Attempts | Status | Evidence | Finding |
|---|---|---|---|---|---|---|---|---|---|---:|---|---|---|
| J-001 |  |  |  |  | F/D | high |  |  |  | 0 | PLANNED |  |  |

## 适用性覆盖

| Dimension/Gate | Applicable | Passed | Failed | Blocked/Not run | Reason/Notes |
|---|---:|---:|---:|---:|---|
| F 功能 |  |  |  |  |  |
| D 数据 |  |  |  |  |  |
| A API/集成 |  |  |  |  |  |
| B 边界/负向 |  |  |  |  |  |
| C 并发 |  |  |  |  |  |
| P 性能 |  |  |  |  |  |
| R 韧性/恢复 |  |  |  |  |  |
| H 真人/a11y |  |  |  |  |  |
| X 兼容/交付 |  |  |  |  |  |
| S 安全/隐私 |  |  |  |  |  |
| T 任务包 |  |  |  |  |  |
| Q Oracle/追溯 |  |  |  |  |  |
| I 身份/供应链 |  |  |  |  |  |
| E 证据/Attestation |  |  |  |  |  |
| O 运营/发布 |  |  |  |  |  |
| M AI/Agent |  |  |  |  |  |

## NOT_APPLICABLE / WAIVED

| ID | Type | Reason | Owner | Applies-to identity | Residual risk | Expires | Retest plan |
|---|---|---|---|---|---|---|---|
