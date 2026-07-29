# Teleiosis v0.0.0.2 升级边界

## 保留

- `teleiosis` runtime slug；
- 永久 Genesis hash `14ab08b9053db4ca87140e59a49f1de8105a718a87ec2d55590c6487c1a77086`；
- v0.0.0.1 的全部脚本、Schema、安装、事务、恢复、回滚和 139 项原生回归；
- main-only、无 PR/临时分支的目标仓规则。

## 新增

- `scripts/teleiosis_cycle.py` 与 `scripts/wbi_cycle/`；
- `scripts/wbi_market.py` 与 `scripts/wbi_market/`；
- `assets/market/templates/`；
- `references/INTEGRATED_MARKET_CYCLE.md`；
- `references/MARKET_EVIDENCE_CONTROL.md`；
- `references/market/`；
- `tests/test_teleiosis_v2_cycle.py`、`test_teleiosis_v2_assurance.py`、`test_teleiosis_v2_cluster_stats.py`、`test_teleiosis_v2_market_evidence.py`、`test_teleiosis_v2_quality.py`。

## 替换

- `SKILL.md`、`README.md`、`CHANGELOG.md`、`VERSION` 升级为统一 v0.0.0.2。

## 禁止

- 删除或覆盖目标仓中未包含在 overlay 的现有文件；
- 单独安装旧 `skill-market-lab`；
- 修改 Genesis 内容或重签 hash；
- 用 taskpack 的局部 50 项测试替代目标仓原生完整 `self-test`；
- 发现 Semantic Delta 时用旧完整树覆盖更新后的 main。
