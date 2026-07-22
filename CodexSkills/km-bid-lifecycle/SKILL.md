---
name: km-bid-lifecycle
description: 通过DingTalk Workspace CLI只读同步“商务报价群”投标台账和Excel附件，自动追踪资格/候选/中标/流标/重招结果、竞争对手、报价和周期性项目。命令运行时动态探测；无结果保持待定。
---

# KM Bid Lifecycle

## 每次运行前后硬契约

- `INPUT_SUFFICIENCY_PREFLIGHT`：直接调用时也必须先按 `../km-bid-scout/references/input_preflight_and_output_locator.md` 检查本 Skill 的 required 输入；缺失即 `BLOCKED`，不得静默省略，只有 Owner 逐字段、逐 run 显式授权的可豁免项才能降级。
- `OUTPUT_LOCATOR`：最终回复必须列出创建/更新/复用文件的绝对路径；没有文件时明确写“本次未生成文件”并给 output root。

## 触发

`DINGTALK_SYNC`、`OUTCOME_WATCH`、团队台账对账或结果追踪。

## DWS前置

先检查 `command -v dws`、`dws version`、`dws --help`、目标命令的 `dws schema` 和 `dws auth status`。本机 2026-07-17 安装基线为官方 open edition `v1.0.52`，但版本必须每次重查，不把该快照当永久事实。再验证企业管理员对数据范围的授权，并由 Owner 绑定精确 profile、enterprise 和 conversation id；同名不自动选。Help 决定可接受 flags，Schema 决定 Agent 契约；未登录、授权不足、冲突或 hash 漂移时停止真实读取。不要把旧命令永久写死。

`DWS_CONFIRMATION_METADATA_NOT_AUTHORIZATION`：DWS Schema 的 `confirmation` 只描述 CLI 交互元数据，不是 Owner、企业管理员或本 run 的外部写授权。任何目标工具只要 `effect` 为 `write` 或 `destructive`，在本 Skill 的只读运行中都必须停止；即使 Schema 写 `confirmation=not_required` 也不得执行。2026-07-18 的 `chat` 快照中 43 个写入/破坏性工具有 42 个为该值，因此不能依赖该字段实现本项目安全门。

## 群同步

1. 解析并绑定唯一“商务报价群”私有conversation id；
2. 事件流+watermark补偿扫描；
3. 下载新Excel附件，按message/file hash版本化；
4. 工作表、表头、隐藏列和公式自发现；
5. 同时保存公式与显示值；公式不替代官方结果；
6. 以项目编号/标包/官方URL优先对账，模糊匹配歧义不自动合并；
7. 归一化已投/未投/待投/撤回和未投原因。

## 结果追踪

用项目编号、标包、标题、采购人、代理和官方平台寻找资格、候选、最终、合同、终止、流标、二次公告和结果变更。无结果→OUTCOME_PENDING；候选第一→CANDIDATE_WINNER，不等于FINAL_WIN。

## 扩展价值

提取竞争对手、排名、报价、重复中标；识别周期性项目、下一窗口和可能的中标总包专业分包机会。预测必须与当前正式标分开。

## 默认只读

不发送群消息、不改在线表、不报名、不支付、不用CA。本 Skill 当前只读契约不因一般性 Owner 授权自动变为可写；如未来确需写操作，必须进入独立任务包、独立 Run Contract、精确对象与内容确认、dry-run、企业权限和回滚门，且不得复用本 Skill 的只读 PASS。

## 输出

`BidLedgerRowVersion[]`、`BidSubmission[]`、`OutcomeNotice[]`、`CompetitorResult[]`、`RecurrenceSignal[]`、`DiscoveryLeadTime`。

输出契约版本 `0.4.1`；用 `python3 scripts/validate_output.py OUTPUT.json` 检查。不符合 `assets/output.schema.json` 的输出不交给下游。
