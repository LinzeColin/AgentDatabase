# Memory Atlas v1.2.1 S08-P1-T3 ChatGPT Export Human Auth Review

## 结论

`S08-P1-T3` 本地实现与验收通过。ChatGPT official export connector 现在只识别四种明确挑战：登录、2FA、CAPTCHA 和账号确认；遇到挑战时保持 `request_click_count=0`、持久化 `FAILED_NEEDS_HUMAN_AUTH` 并停止。认证本身始终由人完成，代码不填写字段、不读取 credential/cookie/storage、不点击认证控件，也不调用 private API。

人工完成后只能通过 `atlasctl chatgpt-export-auth --resume` 显式恢复，并同时提供确认标志、匹配 revision、bounded event id 和 SHA-256 evidence。若挑战发生在 `REQUESTED`，恢复目标固定为 `FAILED_RETRYABLE`，必须重新发出一次显式 request 命令；不会自动重试。其他合法状态恢复到认证前状态。

本 Task 没有运行真实 ChatGPT 浏览器流程、没有完成真实认证、没有提交生产导出请求。仓库基线保持 `IDLE / revision 0 / request null`。通知发现、下载、raw archive 和 push 仍属于 `S08-P2/P3`。

## 交付范围

- Contract：`config/data_sources/chatgpt_export_human_auth.json`
- Model parameters：`机器治理/参数与公式/chatgpt_export_human_auth.v1_2_1_s08_p1_t3.json`
- Runtime：`scripts/memory_atlas_cli/chatgpt_export_human_auth.py`
- Shared state integration：`scripts/memory_atlas_cli/chatgpt_export_state.py`
- Visible challenge detection：`apps/memory-atlas/scripts/chatgpt_export_request_connector.cjs`
- CLI：`atlasctl chatgpt-export-auth --inspect|--pause|--resume`
- Regression：`tests/test_memory_atlas_chatgpt_export_human_auth.py` 与 connector Playwright fixture
- Machine evidence：`机器治理/证据与日志/chatgpt_export_human_auth/chatgpt_export_human_auth.v1_2_1_s08_p1_t3.json`

## 状态与安全合同

Connector 只接受 exact visible headings 或 OpenAI official auth URL 分类，不读取页面正文或账号身份。只有四个固定错误码且 click count 为 0 时，stateful request 才进入 `FAILED_NEEDS_HUMAN_AUTH`；未知错误仍进入普通 retryable，已点击或不确定结果继续保持 `REQUESTED` pending。

通用 T2 `apply_export_transition` 继续以 `human_auth_resume_deferred` 拒绝 human-auth 恢复。T3 专用 resume 会验证最后一次 pause 的 provenance 和挑战枚举。显式恢复缺 confirmation、revision 冲突、无效 event/evidence、非法 pause history、并发锁或多余 mode 参数都 fail closed 且不写 state。

操作命令：

```bash
python3 -B scripts/atlasctl.py chatgpt-export-auth --inspect
python3 -B scripts/atlasctl.py chatgpt-export-auth --resume \
  --confirm-human-auth-complete \
  --expected-revision <revision> \
  --event-id <event-id> \
  --evidence-sha256 <sha256>
```

不得把 password、OTP、CAPTCHA answer、email、cookie、token、账号确认内容或页面正文放入参数、state、日志或 evidence。人工未确认完成时保持 `FAILED_NEEDS_HUMAN_AUTH`；不得使用通用 transition、删除 state 或自动重试绕过该边界。

## 验证状态

- Test-first：T3 模块与 challenge detector 不存在时分别以 Python ImportError 和 JavaScript TypeError 失败；实现后 T1/T2/T3 相关回归 `26/26 PASS`。
- Browser fixture：10 个页面场景 PASS，其中四种认证挑战均在任何 normal UI click 前停止；另有四个 official auth URL 分类 PASS。Source guard 未发现 credential/storage/private API、field fill/type 或 input value 读取。
- CLI/profile/test-value/runtime/governance focused regression `70/70 PASS`；script migration `20/20 PASS`。
- 精确 sync unit tests `237/237 PASS`（46.559 秒）。
- `validate:fast 6/6 PASS`（30.848 秒）；`validate:sync 10/10 PASS`（201.924 秒），credential scan 138.566 秒；均报告 `raw_mutation=false`、`remote_push=false`、`shell=false`。
- `chatgpt-export-auth --inspect` 返回 `IDLE / revision 0 / INSPECTED_NO_CHANGES`，基线 state 文件 SHA-256 保持 `da9b7f188ad0da9cb3dd482748b2d44ddfc65c4fc340b1214ad21d0a36b78aa3`。

## 未完成与回滚

`S08-P1` 在本 Task 后完成，但 `S08` Stage 仍未完成。下一 Task 只能是 `S08-P2-T1`，实现并配置只读通知 connector；本轮没有进入该范围。

回滚使用本 Task 的本地 `git revert`。如果未来真实状态已进入 `FAILED_NEEDS_HUMAN_AUTH`，回滚代码时必须保留最后可验证状态和 evidence，等待人工处理；不得删除状态后重复请求。本轮没有 fetch、push、deploy、branch、PR、merge、rebase 或广域清理。
