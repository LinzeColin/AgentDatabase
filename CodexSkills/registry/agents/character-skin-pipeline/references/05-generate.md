# 出图：API、Batch、断点续跑

## 渠道选型（实测，2026-08）

| 渠道 | 单张 4K | 612 张 | 备注 |
|---|---|---|---|
| **OpenAI API + Batch** | **$0.057** | **~$50** | 首选 |
| OpenAI API 实时 | $0.114 | ~$70 | 要盯结果时用 |
| MiniMax Hub Pro 转售 | 8.34 元 | **15,300 元 / 10.9 个月** | 同一个模型，贵 41 倍 |
| mmx CLI (image-01) | — | — | 质量已证否 |
| ComfyUI 本地 | 免费 | — | 构图合格率实测 15.5%，证否 |

**MiniMax 自己没有任何图像模型**：Hub 里 10 个图像模型全是转售
（`openai` / `midjourney` / `seedream` / `kling` / `nano_banana`），
自家只有 H3(视频)、M3(文本)、Speech/Music(音频)。所以找不到「MiniMax 图像 API
充值入口」是因为它不存在。Hub 里的「Design Image 2」配置写着 `model_name: gpt-image-2`。

查证命令（Hub 桌面端跑着时）：
```bash
curl -s http://127.0.0.1:8001/api/models | python3 -m json.tool | grep -A2 backend
```

## 接口细节

`POST /v1/images/edits`，multipart 或 JSON。

**JSON 模式下参数叫 `images`，是对象数组**：
```json
{"model":"gpt-image-2","prompt":"…","size":"3840x2160",
 "images":[{"image_url":"data:image/jpeg;base64,…"}]}
```
不是 multipart 的 `image`，不是字符串数组，不是 Responses 风格的
`{"type":"input_image", …}`——**三种我都试错过，第二种让 165 张一次性全废**。

**尺寸上限：长边 3840。** 超了返回
`Invalid size. The longest edge must be less than or equal to 3840.`

## Batch

- `POST /v1/files` (purpose=batch) → `POST /v1/batches` (endpoint=`/v1/images/edits`, 24h)
- 输入文件按体积分块，**每块控制在 90MB 以内**（每条约 0.45MB，含 base64 锚图）
- **结果文件是 GB 级 JSONL，必须分块流式落盘**：
  ```python
  while True:
      chunk = response.read(4 * 1024 * 1024)
      if not chunk: break
      handle.write(chunk)
  ```
  一次性 `read()` 会在 ssl 层抛 `OverflowError: signed integer is greater than maximum`，
  **把守护进程直接打死**——而那时 606 张图其实早已生成完毕，只是取不回来。

## 断点续跑

台账（`batch_run.py` 的 `progress.json`）每个单元记：
`task / side / anchor / prompt / expected / attempt / status / metrics / fails / accepted_file`。

状态机：`pending → in_batch → accepted | retry | blocked`。
`retry` 达到 `max_attempts`（默认 3）转 `blocked`。

**重试必须把上一次的失败条款拼进 prompt**：
```
CORRECTIONS REQUIRED (previous attempt failed these): <gate 给的「下次：…」子句>
```
不带修正条件的重试只是再掷一次骰子。曾观察到一次过度修正把暗版亮度从 0.43
推到 0.56，冲出band的另一侧——所以修正条款要给**目标值**不是方向。

## 守护

守夜脚本读日志判活即可，**别用模型轮询**。两条：
- **每轮都写日志**，不要只在「进展变化」时写——165 张集体失败时进展一直是 0，
  一行都没记，看起来像进程死了。
- 异常退出用**退出码区分原因**，让上层知道该做什么（0 完成 / 2 宿主没了 / 3 停摆 / 4 报错）。
