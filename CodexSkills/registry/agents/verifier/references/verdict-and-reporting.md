# 裁决与报告：先让 Owner 做决定，再让开发复现

## 第一屏固定内容

`VERDICT.md` 第一屏按顺序回答：

1. 验的是哪个项目、哪个任务包摘要、哪个不可变 Subject、什么 decision scope；
2. 结论：本范围通过 / 带风险继续 / 不能接受 / 无法判断 / 危险停止；
3. 实际完成的核心用户和世界状态结果；
4. 最大 1–3 个问题或残余风险；
5. 任务包/追溯覆盖以及没有验什么；
6. Owner 现在只做一个动作；
7. evidence root 与 Test Result attestation。

不得要求 Owner 阅读日志才能理解结论。

## Verdict 与 ACTION

| verdict | ACTION | 含义 |
|---|---|---|
| PASS | NONE | 本 decision scope 所有必要门通过，无有效残余风险 |
| PASS_WITH_RISKS | ACT | 无不可豁免阻断；存在明确、限时、有人负责的残余风险 |
| FAIL | ACT | 一个或多个交付门失败，修复后再验 |
| BLOCKED | ESCALATE | 身份、任务包、环境、权限、需求、阈值、追溯或证据不足 |
| UNSAFE | STOP | 继续测试、发布或运行可能造成不可接受损害 |

`developer_check PASS` 不等于正式可发布；`release_candidate PASS` 只表示可进入受控发布；只有 `post_deploy PASS` 说明锁定部署在实际观察窗达到本次放行门。

## 严重度

| 级别 | 人话 | 默认门 |
|---|---|---|
| L0 阻断 | 核心任务不可用，或数据/权限/安全/恢复存在重大风险 | FAIL/UNSAFE，不可豁免 |
| L1 应修 | 主要功能、数据、容量、兼容、恢复或可用性明显不达标 | 默认 FAIL；仅可豁免类可限时接受 |
| L2 打磨 | 非核心、低风险、有可行绕过 | 可 PASS_WITH_RISKS |

严重度看用户、业务、数据、安全和爆炸半径，不看代码改动大小。

## 不可豁免类别

- `ARTIFACT_IDENTITY`
- `DELIVERY_CONTENT_MISMATCH`
- `TASKPACK_INTEGRITY`
- `ACCEPTANCE_ORACLE_DRIFT`
- `TRACEABILITY_GAP`
- `CORE_JOURNEY`
- `DATA_LOSS_OR_CORRUPTION`
- `AUTHZ_BYPASS`
- `SECRET_OR_PRIVACY_LEAK`
- `UNRECOVERABLE_MIGRATION`
- `UNBOUNDED_SIDE_EFFECT_OR_COST`
- `EVIDENCE_INTEGRITY`
- `CRITICAL_FLAKY`
- `NO_SAFE_RECOVERY`

L0 永远不可豁免；以上类别即使标 L1 也不能转成 PASS_WITH_RISKS。

## PASS 语义门

所有 PASS 必须：

- 目标项目、最小验收闭包和不可变 Subject 明确；
- 有权威任务包时，完整快照、完整包/七角色双摘要、授权摘要、Acceptance 与 Task 清单完整，兼容与无漂移均有独立证据；
- Requirement→Acceptance→Oracle→Task→Test→Evidence→Subject 完整闭合；
- change-impact 至少一条，阻断 Acceptance 行全部 PASS；
- 核心 journey、数据/产物和 changed-scope regression 通过；
- 无 blocking FAIL/BLOCKED/NOT_RUN、有效 waiver 或开放 L0/L1；
- AI 适用时，多trial、阈值、安全、成本和 grader 独立性通过；
- 发布范围时，candidate identity 绑定 digest，运营/恢复/灰度门满足；
- 证据脱敏、finalizer 与 `--verify` 通过。

通过率不能抵消关键失败。

## PASS_WITH_RISKS

- 无 L0、不可豁免 finding 或 blocking FAIL/BLOCKED/NOT_RUN；
- 每个风险有 finding、Owner、适用 identity、补偿控制、残余风险、到期和复验计划；
- 第一屏明确写风险和接受动作；
- 任务包/追溯/身份/证据门仍不可降级；
- finalizer 成功。

WAIVED 不等于测试通过，整体不得写 PASS。

## FAIL / BLOCKED / UNSAFE

- FAIL：至少一个 blocking gate FAIL 或开放 L0/L1产品缺陷；已授权任务包的完整性和兼容性仍须可证明，才能判断“产品不符合”。
- BLOCKED：关键条件无法判断，例如任务包授权/完整性/兼容性、Subject、环境或追溯缺失；只说明最小补充条件。
- UNSAFE：有实际危险信号或继续执行会放大损害；立即停止并记录 abort/incident。

失败和阻塞也应封存证据包。

## 单项目边界与缺陷报告

每份报告明确目标项目/Subject、最小验收闭包和未验收项目。只有仓库确实只有一个项目且它就是目标对象时，才可说整个仓库通过。

`DEFECT_REPORT.md` 必填：ID、类型、严重度、类别、关联 Requirement/Acceptance/Oracle/Task/Test、用户影响、Target identity、环境、最短复现、Expected/Actual、原始证据、推测根因及置信度、必须达到的结果、新增回归 Oracle、禁止破坏行为、最小复验闭包和扩大范围条件。

## 豁免与 Evidence root

豁免绑定 finding、Owner、适用 identity、补偿控制、残余风险、到期和复验计划。匿名、永久、跨版本或无补偿控制的豁免无效。

最终报告引用 `FINAL_DECISION.json.evidence_root_sha256` 和 `ACCEPTANCE_ATTESTATION.intoto.json`。哈希或 attestation 变化意味着证据包/裁决配置变化；需要新结论时创建新 run。

## 默认交付收敛：一个开发可执行 ZIP

finalizer 与 `--verify` 通过后，运行：

```bash
python3 scripts/package_review_taskpack.py <run-dir> --json
```

对 Owner 的默认文件交付只能有一个：`*_acceptance_review_taskpack.zip`。ZIP 根目录的 `README_FIRST.md` 指挥开发 agent 依次读取 verdict、defect、modification、test matrix 和 evidence；完整 sealed run 作为其只读附件。内部报告与截图不在默认最终回复中逐项链接，除非 Owner 明确要求展开。

创建 ZIP 不得改变 sealed run；脚本必须先复验 evidence root、FINAL_DECISION、attestation 与逐文件校验和，拒绝 symlink、非普通文件、覆盖已有 ZIP 或把输出写入 sealed run。打包失败表示本轮交付未完成，不能退化为多个散落交付物。
