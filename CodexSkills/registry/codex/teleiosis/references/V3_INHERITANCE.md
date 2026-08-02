# v0.0.0.3 → v0.0.0.5 非降级继承

## 继承事实

`legacy/v0.0.0.3/` 保存 2026-08-03 从 Owner Registry 读取的 v3 SKILL、README 和 444 条 Manifest。三份文件都有固定 SHA-256，并由 `integrity.verify_v3_lineage` 强制检查。

| v3 语义 | v5 对应实现 | 验证 |
|---|---|---|
| T/S/P 全量非路由 | T/S/P 原能力表完整保留，并增加 A | capability manifest 与 36 阶段顺序测试 |
| 连续 Candidate | revision、parent、tree digest、evidence、rollback | workflow 回归 |
| 3 轮×3 组 | `T-C-S-C-P-C-A-C` 扩展序列 | contract/sequence 测试 |
| 动态 fingerprint | 不以固定 repository SHA 阻断普通漂移 | semantic reconcile 测试 |
| 移动 main | 七类 Stage 0 分类 | semantic.py |
| 证据与失败透明 | raw evidence、rejected、NO_CHANGE、BLOCKED | workflow/validation |
| 安装、升级、回滚 | staging→verify→atomic swap→receipt | installer 测试 |
| 外部 Verifier 正式 PASS | 内部 handoff 始终 NOT_ISSUED | verifier handoff 测试 |

## 来源边界

本包没有取得 v3 全部 444 个文件的字节，因此不写“逐字节合并”。v5 的可用性来自：经 130 项测试的 v4 可执行基座、v3 原始合同快照、v5 新增运行模块、旧能力回归和完整安装/封包验证。若未来取得完整 v3 源树，应在新 Candidate 中执行 Stage 0，而不是整树覆盖。
