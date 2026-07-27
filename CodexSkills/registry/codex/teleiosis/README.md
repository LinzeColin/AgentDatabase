# 白箱迭代Skill v0.0.0.1

**English brand:** Teleiosis  
**Functional name:** White-Box Iteration Skill

白箱迭代Skill用于完善其他 Skill，也以同等或更严格的证据标准完善自身。它把 Darwin 的实验棘轮、Luban 的五道产品成熟化门、真实同行研究、冻结评测、开放候选搜索、双白箱、独立终审、确定性打包、原子安装和回滚整合为一个短内核控制面。

永久 Genesis 只约束真实性、安全、双白箱、责任、回滚和有限运行；版本、架构、模型、供应商、候选策略、预算、评分、发布 profile 和实现均可演化。详细规则按需位于 `references/`、`schemas/`、`scripts/` 和 `templates/`，不把整份 Genesis 重复塞进每次模型上下文。

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
  /absolute/path/White-Box-Iteration-Skill-Teleiosis-v0.0.0.1-final.zip \
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
调用白箱迭代Skill，对 <目标Skill路径> 运行完整白箱完善：冻结只读 Baseline，只改外部 Candidate；先挑战是否值得存在，完成时效研究、至少五个真实同行、生态位、真实产物和冻结评测；执行十个系统视角、真实结果比较、独立复审、确定性打包与可回滚安装。不可用能力必须 BLOCKED，不得伪造 PASS。
```

## 关键命令

```bash
python3 scripts/wbi.py --help
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
