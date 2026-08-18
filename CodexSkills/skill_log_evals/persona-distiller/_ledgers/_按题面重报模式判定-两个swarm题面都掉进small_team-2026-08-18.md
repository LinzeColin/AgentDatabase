# 按**题面**重报模式判定：**oracle 期望 swarm 的两个题面，都掉进 small_team**（2026-08-18）

## 为什么要按题面重报

72 条 = **12 个独立题面 × 6 变体**。「命中 25%」这种百分数**把同一题面数了 6 遍**。
按题面逐个列出来，信息量完全不同：

| # | 题面（截 40 字） | oracle 期望 | **实得（题面＋变体）** | |
|---:|---|---|---|:--:|
| 1 | 解释一个边界清晰的专业概念并给出一个可执行示例 | single_expert | small_team | |
| 2 | 诊断一个单一领域问题，列出假设、证据缺口、结论和改判条件 | single_expert | small_team | |
| 3 | 复审一个软件产品 PRD、用户流程、架构、风险与验收 | small_team | **deep_team** | |
| 4 | 对一个跨研究与工程主题做来源核验、方法比较、反证和落地建议 | small_team | **small_team** | ✓ |
| 5 | 处理涉及财务、法律、运营和技术的**高风险**决策 | deep_team | **deep_team** | ✓ |
| 6 | 设计跨服务、数据、权限、恢复和运维的软件架构并生成迁移任务包 | deep_team | small_team | |
| **7** | **对至少二十五个独立市场或技术分片并行研究**，去重后形成竞品矩阵 | **swarm** | **small_team** | |
| **8** | **批量分析三十个独立文件或对象**，产出结构化结果、异常表和统一摘要 | **swarm** | **small_team** | |
| 9 | 核验强当前性事实，将人物方法与当前事实通道分离后给出决策 | small_team | **small_team** | ✓ |
| 10 | 完成创意策略、反例、用户审阅和最终可发布制品 | small_team | **deep_team** | |
| 11 | 面对人物资料不足或超出能力边界的任务，正确拒绝外推 | single_expert | small_team | |
| 12 | 从部分失败、缺文件或中断状态恢复任务 | deep_team | **deep_team** | ✓ |

**按题面命中 4 / 12。**

## ★★★★ 最硬的一条：**oracle 里期望 swarm 的题面有 2 个，两个都掉进 small_team**

第 7 条题面里写着「**至少二十五个独立市场或技术分片并行研究**」，
第 8 条写着「**批量分析三十个独立文件或对象**」——
**任务包作者显然是照着 swarm 的定义写的**，而路由把两条都判成 `small_team`。

⇒ 加上此前两处，**「swarm 够不到」现在有四条独立证据**：

    ① 60 条名册标签：swarm **0 次**，`parallelizability` 最大 **0.275**
    ② 72 条 oracle：swarm **0 次**，最大 **0.665**（门 0.72）
    ③ 验收证据 `route-swarm.json` 那条**照着门写的**题面：也只有 **0.665**
    ④ **本条**：oracle 里**明写 swarm 意图的 2 个题面，双双落进 small_team**

**四条读数指向同一个上界 0.665 < 0.72。**「swarm 结构性不可达」不再是样本内的话。

## ★★ 顺带订正我昨天……不，两小时前写的一句

我在 v0.0.0.34 的 CHANGELOG 里写过「**变体不带任何信息**」。**要收窄**：

    换手率：12 条去变体 与 72 条全量 ⇒ 中位/区间**完全相同** ⇒ 那句**成立**
    模式判定：**12 个题面里有 5 个**，光题面与「题面＋变体尾巴」**档位不同**

        解释一个边界清晰的专业概念…        single_expert → **small_team**
        复审一个软件产品 PRD…             small_team    → **deep_team**
        处理涉及财务、法律…高风险决策        small_team    → **deep_team**
        核验强当前性事实…                 single_expert → **small_team**
        完成创意策略、反例、用户审阅…        small_team    → **deep_team**

**成因**：变体尾巴「变体 N：要求证据可追溯、控制面隔离、最终只交付一个一致成果。」约 25 字，
而 `complexity` 里有一项就是 `min(word_count,120)/170` —— **多 25 字就多 0.15 的 complexity**，
足以跨过 0.38 或 0.76。

⇒ **「变体不带信息」只对与长度无关的指标成立。** 模式判定**恰恰**由长度驱动
（真任务上唯一起作用的触发就是 `complexity`），所以对它变体**很有信息**——
**而那个信息是「题面变长了」，不是「任务变复杂了」。**
[[length-confound-in-blind-eval]]｜[[changing-the-sampling-unit-changes-the-ruler]]

## 可复算

```bash
cd CodexSkills/skill_log_evals/persona-distiller/_ledgers/_pipeline
python3 export_benchmark_tasks.py -o /tmp/b72.json
cd ../../../../registry/codex/persona-distiller-group
python3 - <<'PY'
import sys, json, pathlib, re
sys.path.insert(0,'scripts'); import compile_task_graph as C
VAR = re.compile(r"\s*变体\s*\d+\s*[：:].*$", re.S)
B = pathlib.Path("../../../skill_log_evals/persona-distiller/_ledgers/_pipeline/benchmarks")
per = {}
for n in ("development-48","regression-24"):
    for l in (B/(n+".jsonl")).read_text(encoding="utf-8").splitlines():
        if l.strip():
            r = json.loads(l); per.setdefault(VAR.sub("", r["task"]).strip(), set()).add(r["expected_mode"])
for i,(stem,exp) in enumerate(per.items(),1):
    print(i, sorted(exp), C.choose_mode(C.task_profile(stem))[0], stem[:34])
PY
```

[[samples-cannot-support-universal-claims]]｜[[length-confound-in-blind-eval]]｜[[a-red-that-can-never-turn-green-is-not-a-signal]]｜[[counts-need-their-cutoff-stated]]
