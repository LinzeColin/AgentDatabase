# 白箱迭代Skill v0.0.0.2

**English brand:** Teleiosis  
**Functional name:** White-Box Iteration Skill

白箱迭代Skill用于完善其他 Skill，也以同等或更严格的证据标准完善自身。v0.0.0.2 把原 Market Lab 的因果实验、六类压力、大数据、真实任务与市场反馈内嵌为无独立晋级权的证据内核，并继续保留 Darwin 的实验棘轮、Luban 的产品成熟化门、冻结评测、双白箱、独立终审、确定性打包、原子安装和回滚。

永久 Genesis 只约束真实性、安全、双白箱、责任、回滚和有限运行；版本、架构、模型、供应商、候选策略、预算、评分、发布 profile 和实现均可演化。详细规则按需位于 `references/`、`schemas/`、`scripts/` 和 `templates/`，不把整份 Genesis 重复塞进每次模型上下文。

## v0.0.0.2 唯一宏循环

```text
raw Teleiosis ×3 → 修改已批准对象
market evidence ×3 → 修改已批准对象
raw Teleiosis ×3 → 修改已批准对象
market evidence ×3 → 修改已批准对象
raw Teleiosis ×3 → 修改已批准对象
```

每个 `×3` 必须连续完成诊断、对抗实验、裁决稳定三轮。第三轮先绑定 staged Candidate 的目录树 SHA-256，后续修改节点只把同一哈希原子提交为下一正式 Candidate；任何提交后再改内容、跳段或交错都会使账本 FAIL。

```bash
python3 scripts/teleiosis_cycle.py --help
python3 scripts/wbi_market.py --help
```

市场 Gate 不是单独读取平均分：先运行 `quality-audit`，再把其 digest 与 `SUMMARY.json` 一同交给 `gate`。任何缺失的质量审计、Holdout 污染、样本比例异常、环境不一致、功效不足、评委未校准、过期市场事件或孤立反馈都会阻断证据就绪结论。

Market 内核只输出 `EVIDENCE_READY_FOR_TELEIOSIS / KEEP_BASELINE / REVERT / REHEAT_REQUIRED / BLOCKED`，正式 `PROMOTE` 始终由 Teleiosis 的冻结 Gate 决定。独立 `skill-market-lab` 已标记为 `SUPERSEDED`，不得与 v0.0.0.2 并行安装。

## 快速验证

日常激活只执行快速完整性检查：

```bash
python3 scripts/wbi.py verify-self --strict \
  --expected-genesis-hash 14ab08b9053db4ca87140e59a49f1de8105a718a87ec2d55590c6487c1a77086
```

源码、Gate、Schema、脚本、测试或依赖改变后，以及正式封包前，再运行一次完整回归：

```bash
python3 scripts/wbi.py self-test --timeout 600
```

## 正式安装

```bash
SKILLS_ROOT="/absolute/runtime-specific/skills-root"
ARCHIVE_SHA256="<copy from SHA256SUMS.txt>"
python3 scripts/wbi.py install \
  /absolute/path/White-Box-Iteration-Skill-Teleiosis-v0.0.0.2-final.zip \
  --skills-root "$SKILLS_ROOT" \
  --profile optimizer \
  --verification-level release \
  --result-file /absolute/external/path/install-result.json \
  --expected-genesis-hash 14ab08b9053db4ca87140e59a49f1de8105a718a87ec2d55590c6487c1a77086 \
  --expected-archive-sha256 "$ARCHIVE_SHA256"
python3 scripts/wbi.py install-status \
  --skills-root "$SKILLS_ROOT" --verify-installed --profile optimizer \
  --expected-genesis-hash 14ab08b9053db4ca87140e59a49f1de8105a718a87ec2d55590c6487c1a77086
```

升级加 `--replace`，安装器会保留旧版并返回 rollback pointer。release/deep 安装先核对外部 SHA-256 信任锚，再把输入 ZIP 冻结到私有快照并核对源文件稳定性；内部锁和事务目录拒绝链接。`release` 使用严格结构、Genesis 校验和非递归 smoke；完整回归已在正式封包时运行。只有需要在切换前再次运行整套回归时才显式使用 `deep`。调用中断时通过 `install-status` 查看持久事务，证据不完整再运行 `recover-install`，不要猜测成功。完整说明见 `delivery/INSTALL.md`。

## 首次调用

```text
调用 Teleiosis v0.0.0.2，对 <目标Skill路径> 冻结只读 Baseline；严格执行 T1×3→C1→M1×3→C2→T2×3→C3→M2×3→C4→T3×3→C5。运行真实同行、五臂因果、六类压力、大数据、市场 L0–L7、十视角、独立复审、确定性打包与回滚；Market 只供证，不得自行 PROMOTE。
```

## 关键命令

```bash
python3 scripts/wbi.py --help
python3 scripts/teleiosis_cycle.py --help
python3 scripts/wbi_market.py --help
python3 scripts/wbi.py init-run --help
python3 scripts/wbi.py competitors --help
python3 scripts/wbi.py freshness-scan --help
python3 scripts/wbi.py seal-eval --help
python3 scripts/wbi.py review-plan --help
python3 scripts/wbi.py gate --help
python3 scripts/wbi.py package --help
python3 scripts/wbi.py install --help
python3 scripts/wbi.py install-status --help
python3 scripts/wbi.py recover-install --help
```

正式 2×6 复审必须在 `init-run` 时通过 `--review-attestation-contract` 冻结外部可信 runtime adapter。安装目录内的自写 JSON、角色模拟或重复上下文不能证明独立性。

所有运行事实写在安装目录外的 workspace；sealed holdout、私密运行数据、凭证和第三方动态执行环境不进入安装包。正式运行显式传入用户任务时区对应的 `--valid-as-of YYYY-MM-DD`。

## v0.0.0.2 质量与因果硬门

市场实证内核在汇总前强制执行 holdout 污染、assignment、SRM、跨臂暴露、环境一致性、事前 power plan、可选 judge 校准、市场时间和引用完整性，并用 evidence chain 绑定全部制品。详见 `references/market/QUALITY_AND_CAUSALITY.md`。
