# Memory Atlas v1.2.1 S08-P1-T2 ChatGPT Export State Review

## 结论

`S08-P1-T2` 本地实现与验收通过。`atlasctl request-chatgpt-export` 现在先以原子写入持久化 `REQUESTED` reservation，再调用 T1 visible-UI connector；状态处于 `REQUESTED`、`WAITING_FOR_EXPORT` 或 `LINK_READY` 时，后续请求在 connector 前被拒绝，防止 pending 期间重复提交。

本 Task 没有提交真实 ChatGPT Data Export 请求，也没有调用浏览器。仓库基线保持 `IDLE / revision 0 / request null`。`FAILED_NEEDS_HUMAN_AUTH` 可被记录，但登录、2FA、CAPTCHA 或账号确认后的恢复仍由 `S08-P1-T3` 实现，不能把本 Task 写成 P1 或 Stage 8 完成。

## 交付范围

- Contract：`config/data_sources/chatgpt_export_state.json`
- Model parameters：`机器治理/参数与公式/chatgpt_export_state.v1_2_1_s08_p1_t2.json`
- Durable baseline：`data/sync_state/chatgpt.json`
- State runtime：`scripts/memory_atlas_cli/chatgpt_export_state.py`
- CLI integration：`atlasctl chatgpt-export-state` 与 stateful `request-chatgpt-export`
- Regression：`tests/test_memory_atlas_chatgpt_export_state.py`
- Machine evidence：`机器治理/证据与日志/chatgpt_export_state/chatgpt_export_state.v1_2_1_s08_p1_t2.json`

## 状态合同

正常链路为 `IDLE → REQUESTED → WAITING_FOR_EXPORT → LINK_READY → DOWNLOADED → ARCHIVED → PARSED → VALIDATED → COMMITTED → PUSHED`，并保留 `FAILED_NEEDS_HUMAN_AUTH` 与 `FAILED_RETRYABLE`。每次迁移要求 bounded event id、reason code、SHA-256 evidence、UTC time 和匹配 revision；同一 event 的业务字段一致时幂等，不一致时 fail closed。

真实请求必须同时提供 `--apply --confirm-request`。进程锁覆盖 state check、reservation、connector 和 finalize；reservation 在 connector 前通过 temp file、file fsync、atomic replace 和 directory fsync 持久化。零点击失败可显式重试；已点击或结果不确定时保持 `REQUESTED` pending，不能自动重试。

Connector 输出只接受 T1 的精确 success/failure 字段集合、schema、task、acceptance、mode/action、布尔安全边界、hash 与退出码配对。多余 account/page 字段、格式漂移或退出码矛盾会被替换为受控 `connector_output_invalid`，原始内容不进入 state 或最终输出。

## 操作与停止条件

只读检查：

```bash
python3 -B scripts/atlasctl.py chatgpt-export-state --inspect
```

外部步骤完成后，operator 可使用 `chatgpt-export-state --apply` 并同时提供 `--to-state`、`--expected-revision`、`--event-id`、`--reason-code` 和 `--evidence-sha256`。状态损坏、symlink、超限、revision 冲突、重复 event 冲突、并发锁、非法迁移或 human-auth resume 一律停止且不写入。

不得手工删除 pending state 后重发请求，不得把 cookie、token、password、email、通知正文或下载链接写入状态。`FAILED_NEEDS_HUMAN_AUTH` 出现后必须等待 T3 的人工认证合同；通知、下载、归档和 push 属于 S08-P2/P3。

## 验证状态

- Test-first：新增三项回归分别暴露 connector 多余字段、非法 history 跳转和跨时间事件重放缺口，修复后 dedicated `10/10 PASS`。
- 相关 modular CLI、runtime、validator profile、test-value、T1 connector 与 T2 state 回归 `63/63 PASS`；精确 sync 单测 `229/229 PASS`。
- `chatgpt-export-state --inspect` 返回 `IDLE / revision 0 / INSPECTED_NO_CHANGES`；缺少 `--confirm-request` 的 apply 在 connector 前以 `request_click_count=0` fail closed，state SHA-256 前后均为 `da9b7f188ad0da9cb3dd482748b2d44ddfc65c4fc340b1214ad21d0a36b78aa3`。
- `validate:fast 6/6 PASS`（29.715 秒）；`validate:sync 10/10 PASS`（180.430 秒），其中 credential scan 128.848 秒；两者均记录 `raw_mutation=false`、`remote_push=false`、`shell=false`。

## 未完成与回滚

`S08-P1-T3` 仍需实现 human-auth pause/resume；S08-P2/P3 仍需实现通知发现、链接验证、下载、raw archive 与最终受控 push。本轮没有 fetch、push、deploy、branch、PR、merge、rebase 或广域清理。

回滚使用本 Task 的本地 `git revert`。如外部请求未来已发生，回滚代码时必须保留最后可验证 pending state 与外部证据，不得删除 state 后重复请求。本 run 完成后停止在 `S08-P1-T3` 前。
