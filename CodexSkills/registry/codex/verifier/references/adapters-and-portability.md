# 工具适配器、归一化与跨平台可移植性

## 决策边界

Verifier 是裁决内核，不复制所有测试平台。外部工具只贡献可核验观察：

```text
capability discovery → authorized argv → raw result → hash verification → normalized claim → Verifier gate
```

**Adapter 不能直接写 verdict**、release approval 或 acceptance status；`normalize_adapter_result.py` 会递归拒绝这些字段。Adapter 输出的 `PASS` 只代表其声明范围内的观察，不自动升级最终结论。

## 六类统一契约

统一支持：`static_analysis`、`test_execution`、`release_observation`、`ai_evaluation`、`supply_chain`、`human_manual`。每类都必须记录：工具名/版本/来源、精确 Subject、argv、cwd、退出码/timeout、显式状态映射、原始证据路径/大小/SHA-256、逐 claim Oracle 与限制。

机器模板：

- `templates/ADAPTER_CONTRACT.json`
- `templates/ADAPTER_RESULT.json`

归一化：

```bash
python3 -B scripts/normalize_adapter_result.py input.json \
  --evidence-root <run-root> --output normalized.json --json
```

## Fail-closed 映射

- `warning|skipped|unstable|partial|incomplete|unknown|not_run` 不得映射为 PASS；
- timeout 不得 PASS；
- PASS 必须有至少一份已哈希原始证据；
- 每个 PASS claim 必须引用已登记证据；
- 任一非 PASS claim 不得被总体 PASS 掩盖；
- Adapter 的 argv 是数组，不拼接 shell 字符串；环境秘密只引用，不写入公开结果。

## 优先复用

项目原生 build/test/lint/typecheck、已锁定 CI、API contract/property、browser/mobile/desktop、mutation/security/load/resilience、AI eval/red-team、release analysis、policy-as-code、attestation/signing。新增工具要记录版本、许可、网络、缓存、供应链和费用，不能因知名度自动安装。

## 跨平台与 Offline

显式处理 POSIX/Windows 路径、大小写/Unicode、symlink/权限/锁、signal/exit code/编码/时区、x86_64/arm64/GPU/browser、只读 CI/Kubernetes 和网络受限环境。离线时不静默使用过期缓存；记录 cache key、来源和完整性。无法在目标平台复现时，结论只能覆盖实际环境。
