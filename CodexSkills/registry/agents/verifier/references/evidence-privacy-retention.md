# 证据隐私、最小化、保留与销毁

## 原则

证据应足以支持裁决，但不应复制全部生产数据、凭据或无关个人信息。完整性与最小化同时成立。

## 数据分级

- `public`：可公开资料；
- `internal`：项目内部，无敏感个人数据；
- `confidential`：商业、客户、未发布信息；
- `restricted`：凭据、支付、健康、生物特征、密钥、受监管数据。

restricted 默认不得进入普通 evidence ZIP。只记录安全存储引用、哈希、访问控制和验证结论。

## 收集前

在 `EVIDENCE_POLICY.json` 记录：目的、允许类型、禁止类型、private evidence root、redaction 方法、retention_days、Owner、销毁动作、外部共享边界。

## 收集与脱敏

- 使用 synthetic/masked 数据优先。
- 日志仅截取与断言相关窗口，并保留原始文件哈希/安全引用。
- token、password、private key、cookie、Authorization header、连接串、个人邮箱/电话等由 `evidence_guard.py` 扫描。
- 自动脱敏只是启发式，报告 `possible_false_positive/possible_false_negative`；高风险数据需人工/策略复审。
- 不修改原始证据；生成单独 sanitized copy，并保留 source→sanitized 映射和各自哈希。

## 封存

- 公开/普通证据进入 sealed run；restricted 证据留在受控 private root，仅在 index 中引用。
- ZIP 前检查归档路径、symlink、缓存、临时文件和秘密扫描结果。
- Hash-only 不等于可信来源；需要时外部签名/时间戳/provenance。

## 保留与销毁

每类证据有明确到期日期，而不只写天数。到期动作：删除、匿名化、归档或重新授权。销毁记录包含対象、时间、执行者、方法和验证结果；无法验证删除时标记 UNKNOWN。

## 正向裁决门

发现未处理 high-confidence secret/private key，或 restricted 数据进入普通 ZIP，属于阻断。仅有低置信 PII 命中可进入人工复审，不自动 FAIL 产品。

## Safe-copy default

`evidence_guard.py redact-copy` only copies bounded text it can inspect and redact. Binary or oversized content is rejected by default; `--allow-uninspected-copy` is an explicit exception and never means the file is privacy-safe. Keep the original in the private evidence root and attach a separate reviewer decision before external sharing.
