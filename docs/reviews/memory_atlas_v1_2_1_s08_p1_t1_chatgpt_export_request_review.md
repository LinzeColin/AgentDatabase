# Memory Atlas v1.2.1 S08-P1-T1 ChatGPT Export Request Connector Review

## 结论

`S08-P1-T1` 本地实现与验收通过。新增 `atlasctl request-chatgpt-export`，通过显式 loopback CDP 端点连接用户已经运行且已登录的 Chrome，在一个 task-owned 临时标签页中只操作 ChatGPT 官方可见 UI。代码不读取 browser profile、cookies、storage state、password、token 或账号身份，也不调用未公开 API。

本 Task 没有提交真实生产导出请求。真实登录态 smoke 只走到官方 `Confirm export` 确认框后点击 `Cancel`，用于验证当前可见 UI 和 selector 合同；`S08-P1-T2` 的 durable state、pending 去重与恢复尚未实现，不能把本 Task 写成完整自动导出流程完成。

## 交付范围

- Contract：`config/data_sources/chatgpt_export_request.json`
- Model parameters：`机器治理/参数与公式/chatgpt_export_request.v1_2_1_s08_p1_t1.json`
- Browser connector：`apps/memory-atlas/scripts/chatgpt_export_request_connector.cjs`
- CLI wrapper：`scripts/memory_atlas_cli/chatgpt_export_request.py`
- `atlasctl` command：`request-chatgpt-export`
- Regression：`tests/test_memory_atlas_chatgpt_export_request.py` 与 `tests/chatgpt_export_request_connector.test.cjs`
- Machine evidence：`机器治理/证据与日志/chatgpt_export_request/chatgpt_export_request.v1_2_1_s08_p1_t1.json`

## 执行合同

只读检查：

```bash
python3 -B scripts/atlasctl.py request-chatgpt-export \
  --dry-run \
  --cdp-endpoint http://127.0.0.1:9222
```

真实请求必须由 operator 同时提供 `--apply --confirm-request`。少任一 flag 都在启动 browser process 前 fail closed。Connector 只接受无 user-info、path、query 或 fragment 的数字 loopback `http://127.0.0.1:<port>` 或 `http://[::1]:<port>`，不接受 hostname、远程 debugging service 或含 credential 的 endpoint。

## 可见 UI 与隔离

- Connector 新建并最终关闭一个 task-owned tab，不选择或关闭用户现有 ChatGPT tabs。
- 当前观察路径：`Open profile menu → Settings → Data controls → Export data → Request data export - are you sure?`。
- 每一步必须是唯一且可见的 accessibility locator；缺失、重复、origin 漂移或不可见均停止，不猜 selector、不自动重试。
- Inspect 模式进入确认框后必须点击 `Cancel`，request click count 为 0。
- Apply 模式最多点击一次 `Confirm export`；服务器接受、pending 去重和可恢复状态不在 T1 冒充完成。
- 子进程机器输出限制为 16 KiB 且只允许固定 JSON 字段，不保留 account、页面正文、browser diagnostics 或 endpoint。
- 若 Confirm click 已尝试但结果或 tab cleanup 不确定，失败输出必须保留 `request_click_count=1`，不能把可能已发生的外部副作用写成零。

## 验证状态

- Test-first：生产模块不存在时 dedicated test 按预期 ImportError。
- Dedicated Python + browser fixture：8/8 PASS；fixture 覆盖 6 个浏览器场景，inspect 0 次 request click、request 1 次 click，missing/ambiguous profile 和 wrong origin 均 fail closed；包装层额外验证精确 mode/action 配对，并在 apply 子进程超时时以 1 次点击上限记录不确定副作用。
- `atlasctl --apply` 缺少 `--confirm-request` 在 browser process 前返回 `explicit_request_confirmation_required`；不可用 loopback endpoint 返回 `browser_connection_failed`，均为 exit 2。
- 真实 Chrome 登录态只读 smoke 到达官方确认框并取消；未读取凭证、未提交请求、未修改 profile。
- 相关 modular CLI、runtime 与 connector 回归 30/30 PASS；focused 治理回归 77/77 PASS。
- `validate:fast` 6/6 PASS（21.893 秒）；最终完整 `validate:sync` 10/10 PASS（178.901 秒）：sync unit 219/219、public-raw layout、三来源 dry-run、Codex archive/state/derived、raw append-only 与 129.327 秒 credential scan 全部通过；profile 记录 `raw_mutation=false`、`remote_push=false`、`shell=false`。

## 未完成与回滚

`S08-P1-T2` 仍需实现 `REQUESTED → WAITING_FOR_EXPORT → ...` durable state、pending 去重与恢复；`S08-P1-T3` 仍需实现 login/2FA/CAPTCHA 的 human-auth pause/resume。本 Task 不下载 ZIP、不归档 raw、不触发 Git remote 或部署。

回滚使用本 Task 的本地 `git revert`，不删除或修改用户 browser profile、cookies、账号设置或已产生的外部请求证据。本轮完成后停止在 `S08-P1-T2` 前。
