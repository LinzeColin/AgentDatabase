# Product Reality Lab

集成版本：`v0.0.0.3`（来源谱系：`product-reality-lab-v0.0.0.1`）

这是一个位于开发与 `verifier` 之间的现实发现 Skill。它将竞品/开源研究、产品表面与状态建模、前后端/数据/性能/安全/故障实验、防呆审计、真实用户灰度和缺陷收敛统一为一套机器可读证据协议。

## 核心边界

- 不签发 PASS。
- 不把模型作为唯一 Oracle。
- 不把模拟用户当真实市场反馈。
- 不在无授权目标执行主动扫描、压力或混沌。
- 不复制无来源、许可证不兼容或受保护的竞品内容。

## CLI

```bash
python3 scripts/prl.py selftest
python3 scripts/prl.py init --workspace /tmp/prl-run --subject-name demo --subject-ref abc123 --owner run-owner
python3 scripts/prl.py index-evidence --workspace /tmp/prl-run --evidence-class SYNTHETIC --tool playwright
python3 scripts/prl.py sync-coverage --workspace /tmp/prl-run --auto-cover-evidenced
python3 scripts/prl.py validate --workspace /tmp/prl-run
python3 scripts/prl.py score --workspace /tmp/prl-run
python3 scripts/prl.py handoff --workspace /tmp/prl-run
```

`sync-coverage` 会从 Surface、State、Transition、Role、Data、Fault、Oracle 和 Evidence 目录自动建立逐项清单，并反算 total/covered/waived；手工把计数改成 100% 无法绕过校验。`field_validation_complete` 同样由带 `FIELD_OBSERVED` 证据的已完成实验反推，不能手填为真。

详细机制见 `SKILL.md` 与 `references/`。
