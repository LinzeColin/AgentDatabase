# 白箱迭代Skill v0.0.0.3

**English brand:** Teleiosis
**安装身份:** `teleiosis`（唯一 Registry Skill）
**执行模式:** `FULL_NO_ROUTING`
**Candidate 语义:** `C` 是迭代对象本身的连续 Candidate revision，不是 SHA 检查点。

Teleiosis v0.0.0.3 将五个来源合并为一个可安装 Skill：v0.0.0.1 永久基线、Owner v0.0.0.2、已上线的市场证据 v0.0.0.2、Skill Market Lab、Product Reality Lab。S/P 以完整源代码和能力合同内置在 `modules/`；T 复用父 Skill 的唯一 canonical engine，不会被注册成第二、第三个 Skill；外部 `verifier` 仍保持独立裁决。

## 1. 三个内置子模块

| 符号 | 内置模块 | 责任 | 裁决边界 |
|---|---|---|---|
| `T` | Raw Teleiosis | Genesis、存在性挑战、同行与时效、Baseline/Candidate、评测、十视角、硬门、回滚、交付 | 唯一内部决策控制面 |
| `S` | Skill Market Lab | 五臂因果、六类压力、大数据、竞品、Shadow/Canary、真实任务/结果/代价/反馈 | 只供证，不 PROMOTE |
| `P` | Product Reality Lab | 产品数字孪生、八维覆盖、前后端/数据/性能/安全/故障/防呆、Field、缺陷收敛 | 只输出 Verifier 前状态 |

三个模块**不是路由选项**。每次正式调用都沿同一条路径重复轮跑完整能力表；不因任务分类或模型判断删减模块。每轮执行相邻模块交叉验证，每组复审 Candidate lineage、证据与回归影响，每次 Run 做最终反证复审，从机制上压低盲点、死角、单一评委偏差和伪完成。

## 2. 永久执行流程

```text
一轮：T1 -> C1 -> S1 -> C2 -> P1 -> C3
一组：连续三轮
一次 Run：连续三组 = 9 轮
```

一次完整 Run 共 27 个 T/S/P 阶段和 27 个 Candidate revisions。每个阶段都对当前 Candidate 读取完整 Capability Manifest；结果只能是 `EXECUTED / NOT_APPLICABLE_WITH_REASON / NOT_RUN / BLOCKED`。`NO_CHANGE` 仍要完成全量检查。

### C 的正确含义

```text
C0 --T--> C1 --S--> C2 --P--> C3
```

- C1/C2/C3 是迭代对象被相应模块诊断、实验和优化后的**实际文件树/工作副本**；
- 阶段允许形成真实修改，也允许经证据判断 `NO_CHANGE`；
- 每个 revision 保存 parent、精确 diff、测试、理由和回滚；
- 动态 fingerprint 只证明“当时看的是哪个内容”，不能预先锁死后续修改；
- 仓库 HEAD、`metadata/release.json`、README 或 overlay 的固定 SHA 永远不是应用前提。

## 3. 防呆与干净运行目录

正式 Run 只接受真实普通目录和普通文件，拒绝符号链接、路径嵌套、路径穿越、未知字段、超限输入和疑似凭证。Workspace 根目录只有：

```text
candidate/
.teleiosis/
RUN_STATE.json
RUN_STATUS.json
SUMMARY.md
NEXT_STAGE.json
RESULT.json
```

`NEXT_STAGE.json` 是下一阶段唯一输入模板；填完后直接执行 `next`，无需手工再创建杂乱文件。阶段提交采用事务写入；`NO_CHANGE`/`KEEP`/`REVERT` 都与实际 Candidate Delta 对账。机器模式只输出一个 JSON，错误不泄露凭证、不产生 traceback、usage 或缓存噪声；子进程采用定长尾缓冲、总输出硬上限和进程组清理。任务包 `--result-file` 只能原子写入包外普通路径，并使用 `0600` 权限。

任务包用户优先使用根目录 `START_HERE.py`：无参数只读检查，`install` 一键安装，`publish --yes` 才允许真实推送。

## 4. 直接验证

```bash
python3 scripts/wbi.py verify-self --strict
python3 scripts/wbi.py self-test --timeout 600
python3 scripts/teleiosis_run.py contract
```

`verify-self` 会从包内 Genesis lock 动态读取自身锚点并验证真实文件；仍可显式传入外部 hash 获得更强信任，但不再要求用户手抄固定 hash 才能使用。

## 5. 直接安装

从最终任务包根目录执行：

```bash
python3 install.py --skills-root /absolute/path/to/skills
```

安装器支持：

- 全新安装；
- 从 v0.0.0.1 / 任一 v0.0.0.2 语义升级；
- v0.0.0.3 幂等重复安装；
- 保留未知上游文件；
- 仓外备份、事务收据和精确回滚；
- 不以固定 repo/file/overlay SHA 阻塞普通上游漂移。

### 独立 Skill ZIP

最终任务包同时包含 `dist/Teleiosis-v0.0.0.3-skill.zip`。可由包内 `payload/teleiosis/scripts/wbi.py install` 直接安装；包内锚点自动发现，外部锚可选但不再是基础可用性的前置条件。

## 6. AgentDatabase main 推送

Codex 使用任务包的 `scripts/publish_main.py`。它每次从远端最新 `main` 建立临时 clone，在该 integration base 上执行语义 merge、测试和 Catalog 更新；推送前再次读取远端。如果 main 前进，丢弃临时 clone 并从最新 main 重试，最多三次。不会在 ahead/behind 的旧本地工作树上硬推，也不创建 branch/PR。

## 7. 第一次调用

```text
调用 Teleiosis v0.0.0.3，对 <目标 Skill> 在安装目录外建立只读 Baseline 和可回滚 Candidate。严格以 T1→C1→S1→C2→P1→C3 为一轮，三轮一组、三组一次 Run；T/S/P 全量非路由运行。C 是迭代对象本身的连续 revision，允许基于证据持续修改，不是固定 SHA 检查点。完成竞品、因果、大数据、六类压力、产品八维试炼、真实市场/Field 分级、交叉验证、复审、回滚和外部 Verifier 交接；模拟不得冒充真实市场。
```

## 8. 关键目录与版本边界

根目录 `VERSION`、`SKILL.md metadata.version` 和 `metadata/release.json` 是当前版本权威，统一为 `v0.0.0.3`。v0.0.0.1/v0.0.0.2 仅作为 Genesis、Amendment、测试命名和 `metadata/release.json.lineage` 中的来源谱系；所有可执行入口与内置模块版本统一为 v0.0.0.3。


- `modules/raw_teleiosis/`：T 的能力合同与来源描述；实现复用父 Skill，不保留重复旧源码；
- `modules/skill_market_lab/`：Skill Market Lab 完整内置源；
- `modules/product_reality_lab/`：Product Reality Lab 完整内置源；
- `scripts/wbi_core/`：Teleiosis 核心；
- `scripts/wbi_run/`：固定全量 Run 与 Candidate revision 控制；
- `references/FULL_RUN_CONTRACT.md`：执行合同；
- `delivery/INSTALL_AND_GITHUB.md`：安装与移动 main。

## 9. 证据边界

模拟、合成任务、LLM judge、压力流量和测试 Fixture 都是实验室证据。真实市场至少要求获授权的真实用户/独立验收者、真实任务、可观察结果或现实代价和可审计轨迹。没有这些证据时必须写 `NOT_CLAIMED`。P 最多输出 `READY_FOR_VERIFIER`，最终 PASS 只来自外部独立 Verifier。
