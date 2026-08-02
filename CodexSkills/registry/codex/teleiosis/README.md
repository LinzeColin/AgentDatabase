# Teleiosis v0.0.0.5｜真实可用完整包

此版本不是把 v0.0.0.4 再发一次，也不是只增加文档。它以已通过 130 项测试的 v4 可执行基座为起点，补回 v3 非降级继承证据，并增加可直接运行的 Stage 0、Taskpack、三次 Skill Audit、复审硬门、8192 条回归语料、一键 Doctor 与冻结 Verifier handoff。

## 直接使用

```bash
python3 START_HERE.py doctor
python3 START_HERE.py install
```

默认安装到 `~/.codex/skills/teleiosis/`。项目级安装：

```bash
python3 START_HERE.py install --project
```

Windows 双击 `INSTALL.bat`；macOS 双击 `INSTALL.command`。失败时只输出一个结构化 JSON，不打印噪声或 traceback。

## 你实际得到什么

| 能力 | 用户可见结果 |
|---|---|
| T/S/P/A 四引擎 | 同一个 Candidate 连续迭代，不把市场、产品、竞技拆成互不相干的 Skill |
| v3 非降级 | v3 的三引擎语义、移动 main、证据和回滚继续有效 |
| Stage 0 | 面对最新仓库不会用旧整树覆盖新实现 |
| 三次 Skill Audit | Baseline、整改、冻结三次真实差量复审，不能重复凑次数 |
| Taskpack | 需求、任务、测试、Oracle、证据和制品一一追踪 |
| 8192 条回归 | 四引擎与六分区离线回归可重放，不用小样本冒充“大数据” |
| Doctor | 一条命令检查包、治理、复审、回归和 Fresh Builder |
| 事务安装 | 新装、幂等升级、保留未知非冲突文件、备份和回滚 |
| Verifier handoff | 冻结精确 Subject 给外部验收，内部不能自签 PASS |

## 诚实边界

v5 保存了 v3 的原始 SKILL、README 和 444 条 Manifest，但没有伪称获取 v3 全部文件字节。人物专家 dossier、目标仓写入、原生竞品 L3、真实市场 L4 和正式独立 Verifier 当前未运行，状态被明确封锁在对应证据等级。

## 常用命令

```bash
python3 scripts/teleiosis.py check
python3 scripts/teleiosis.py self-test
python3 scripts/teleiosis.py taskpack validate
python3 scripts/teleiosis.py skill-audit
python3 scripts/teleiosis.py review
python3 scripts/teleiosis.py regression
python3 scripts/teleiosis.py contract
python3 scripts/validate_release.py --output-dir /outside/teleiosis-v5-validation --runs 3
```
