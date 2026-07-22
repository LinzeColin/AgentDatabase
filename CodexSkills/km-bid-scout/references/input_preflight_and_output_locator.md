# Input preflight and output locator

本契约适用于路由器和 8 个领域 Skill 的每一次运行，包括直接调用、自动化触发、重试和只读研究。

## 1. 输入状态

每个被检查字段必须记录一个状态：

- `PRESENT_VERIFIED`：已由用户、当前文件、当前 Git/DWS/source probe 或一手来源验证；
- `PRESENT_UNVERIFIED`：值存在但真实性/新鲜度不足；对高影响结论仍视为阻塞；
- `DERIVED_SAFE`：仅对 run_id、哈希、输出根等非业务决策字段做确定性推导，并显示推导；
- `MISSING_REQUIRED`：缺失会让当前 mode 不能真实执行或不能支持输出结论；
- `MISSING_OPTIONAL`：不阻塞，但必须显示造成的能力/覆盖损失；
- `EXPLICITLY_WAIVED`：Owner 对该字段和本次 scope 明确授权一种降级处理；
- `NOT_APPLICABLE`：本 mode 不需要，必须给出理由。

不得用默认值把 `MISSING_REQUIRED` 静默改成 `PRESENT_VERIFIED`。

## 2. 公共必检项

| 输入 | 允许安全推导 | 缺失处理 |
|---|---|---|
| 一句话 goal 与本轮唯一 mode | mode 仅在用户意图唯一时可推导 | 歧义则 BLOCKED |
| stable run/trigger id 与原始触发时间 | 可确定性生成 run_id；不得伪造 scheduler 时间 | 保留 UNKNOWN 或 BLOCKED |
| canonical repo/path 与当前 Git 状态 | 只读命令验证；开工/写入前/结束三次快照 | 路径/治理或并发漂移冲突则停止并刷新证据 |
| source/data scope 与访问授权 | 否 | 涉及真实访问则 BLOCKED |
| query/page/byte/time budget | 否；离线静态检查可明确 0 外部预算 | 无界外部运行则 BLOCKED |
| `external_effects=deny` | 否 | 非 deny 立即停止 |
| delivery 与绝对 `output_root` | 可在当前受控 workspace 下生成并展示 | 无法安全定位则 BLOCKED |
| 当前 Phase/Gate、allowed changes、验证与停止条件 | 可从已验证任务包读取 | 范围不明则 BLOCKED |

## 3. Mode 专用 required 输入

| Mode/步骤 | Required 输入 |
|---|---|
| FULL_DISCOVERY | 已批准 SourceRegistry、明确 source_scope、查询/页/字节/时长预算、条款/robots/授权状态 |
| INCREMENTAL_DISCOVERY | FULL 所需项 + cursor/watermark；缺 cursor 不得默认为全量 |
| EVIDENCE_BACKFILL | candidate/官方 URL 或 notice/lot 身份、待补字段、附件访问边界 |
| DEADLINE_WATCH | notice_version/lot 身份、当前 deadline 原文与 offset/source-zone 证据 |
| AUDIT_ONLY | 原始 EvidenceBundle、结构化前序决策、规则/version；不得用前序自然语言辩护代替 |
| BRIEF_ONLY | 已审计结构化决策、coverage、deadline evidence、输出受众与脱敏级别 |
| qualify 步骤 | 唯一 legal_entity、当前 company profile、as_of/valid_until/source、商务/产能 Owner 边界 |
| DINGTALK_SYNC | 已安装 DWS 的 version/help/schema、企业管理员授权、精确 profile/corpId、enterprise、conversation id、只读操作范围 |
| OUTCOME_WATCH | DWS 门（如使用）+ 项目/lot/官方结果来源身份；无结果保持 OUTCOME_PENDING |
| EVOLVE_SHADOW | 时间切片标签、ACTIVE manifest、评估集边界、sealed holdout 隔离、预算和禁止发布声明 |

DWS CLI 可执行不代表企业授权完成；`authenticated=false` 时不得读取目标企业数据。

## 4. 缺失时的唯一允许流程

1. 在任何领域动作前生成 preflight。
2. 若有 `MISSING_REQUIRED`，返回 `BLOCKED`，列出编号、为什么必需、最小补充格式和不补充的影响。
3. Owner 可补充，或对每个字段明确授权以下一种处理：
   - `OMIT`：本轮明确不产出依赖该字段的能力/结论；
   - `BOUNDED_ASSUMPTION`：使用写明上下界、证据和影响的临时假设；
   - `PUBLIC_SAFE_PLACEHOLDER`：仅搭结构/测试，不冒充真实业务证据；
   - `DEFER_PHASE`：跳过整个依赖 Phase，不把 SKIPPED 报成 PASS。
4. 授权记录必须含 `authorization_id`、field、treatment、authorized_by、authorized_at_raw、scope、impact、expires_at_raw。
5. 授权默认只对当前 run 有效；没有明确持久政策不得复用。
6. 降级后不再存在未处理的 `missing_required`，但对应 item 保留 `EXPLICITLY_WAIVED`，run status 至多为 `PARTIAL`。

## 5. 不可豁免

以下缺失不能以“可省略”继续：

- 企业管理员/目标数据访问权限、精确 DWS profile/enterprise/conversation 绑定；
- 来源条款、robots、订阅/登录/API 权限和服务稳定性预算；
- P0/P1 的官方源、关键证据、唯一法律主体和独立审计；
- secret、凭据、个人信息、私有数据与公共 Git/外部模型边界；
- 外部写操作、报名、购标、支付、CA、签章、提交或发消息的独立授权；
- ACTIVE/holdout/evaluator/硬排除规则发布与 Owner 最终 GO 签收；
- 无 offset/source-zone 却计算精确剩余时间。

## 6. Preflight 输出最小格式

```yaml
input_preflight:
  status: SUFFICIENT | BLOCKED | PROCEED_WITH_AUTHORIZED_DEGRADATION
  checked_at_raw: original value
  can_proceed: false
  items:
    - name: source_scope
      requirement: required
      state: MISSING_REQUIRED
      source: none
      evidence: null
      blocking: true
  missing_required: [source_scope]
  authorizations: []
```

## 7. OUTPUT_LOCATOR

最终用户回复必须包含：

- output root 的绝对路径；
- 每个文件的绝对路径、`CREATED | UPDATED | REUSED | FAILED`、种类和本地/外部可见性；
- 主要交付物的 SHA-256（可计算时）；
- 未生成但原计划生成的文件及原因；
- 若 items 为空，原样写“本次未生成文件”。

绝对本机路径是 Owner 定位信息，只写入 `LOCAL_USER_ONLY` 回复或本地运行证据。外部钉钉消息、公开简报和公共仓库产物使用逻辑 artifact id 或脱敏相对名，不泄漏用户名、私有根或凭据路径。
