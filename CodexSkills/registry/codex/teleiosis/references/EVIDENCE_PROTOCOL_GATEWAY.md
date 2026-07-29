# Evidence Protocol Gateway

## 目标

EasyDarwin 的核心启发是协议分层：同一视频流可以经不同协议分发，但每个协议的边界清晰。Teleiosis 的证据也必须协议化，否则 GitHub README、ZIP、运行状态、LLM 评语和验收 verdict 会混成不可审计叙事。

## 默认协议

| protocol_id | 可证明 | 不可证明 |
|---|---|---|
| `github-source` | commit、文件、license、目录结构 | runtime outcome、formal review |
| `local-zip` | 收到的 artifact bytes、SHA-256 | 源码 provenance、业务效果 |
| `runtime-status` | 某时刻服务/命令返回 | 用户结果、长期稳定 |
| `provider-receipt` | 调用身份、usage、外部 run id | verdict |
| `verifier-evidence` | 对唯一 Subject 的验收裁决 | 其他版本/分支 |
| `persona-route` | 角色覆盖和观点生成 | 外部独立性 |

## 规则

每个 positive claim 必须声明所依赖的 protocol；协议不支持的 claim 只能是 `UNKNOWN` 或 `NOT_PROVEN`。