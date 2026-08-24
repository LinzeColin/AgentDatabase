# Operations Control Plane

## 为什么来自 EasyDarwin

EasyDarwin 的可借鉴点不是流媒体本身，而是把核心能力做成可运行产品：Web 管理、预览、协议输出、在线/离线监控、拉流转发、鉴权、部署目录和构建命令。Teleiosis 的 skill 交付也必须有同等“运行面”意识。

## Teleiosis 运维面

| 域 | 必要证据 |
|---|---|
| entrypoints | `verify-self`、`market-profile`、`optimize`、`run-status`、`explain-block`、`install-status` |
| configuration | release profile、review attestation contract、budget、valid_as_of |
| status | 八域状态，不压成一个总 PASS |
| recovery | resume、recover-install、rollback-install |
| protocol | GitHub、ZIP、runtime status、provider receipt、verifier evidence |
| deployment | deterministic package、expected archive hash、transaction receipt |

## 非目标

本轮不新增长期后台服务、Web UI 或真实云端状态面；只把运维证据合同补齐，避免给 Codex 增加部署工作量。