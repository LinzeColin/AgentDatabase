#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**合同写着「人工关键词不得成为冠军路由的主要证据」—— 量一下它是不是。**

## 合同原文

`references/moe-routing-contract.md` 「A 层」一节最后一句：

> 「人工关键词不得成为冠军路由的主要证据。」

## ★★★ 先说清楚：**仓里已经有一件在量这个数了**，本件不是第二把尺子

`_ledgers/_pipeline/measure_routing_discrimination.py` **已经**现算 weight×σ、
**已经**把合同那句话逐字印在输出里（实测报 `domain_match` 占 **66.5%**）。
本件与它**共用同一个来源**（`route_team_moe.ranking_drivers`），不是独立第二读数。

那本件补的是什么：

| | 那件 | 本件 |
|---|---|---|
| 在哪 | `_ledgers/_pipeline/`（**开发台账树，不随包分发**） | **本包 `scripts/`**，用户装了就有 |
| 结论 | 报一个数 + 印合同原文 | **rc 判定 + 回归地板**（不许更依赖词表） |
| 指标 | 份额 | **「当第一驱动」的任务占比**（合同问的是名次） |
| 守卫 | — | 非退化（σ 全 0 会让份额退化成 0，**看着像合规**）＋ **基线绑定样本量** |

⇒ 规则本身此前**没有 rc 级执行点，且执行不到用户手上**。
[[a-rule-in-a-doc-has-no-enforcer]]｜[[i-built-a-second-ruler-while-the-authoritative-one-sat-in-scripts]]

## ★★ 因果也要说准：不是有人选了词表当冠军

那件工具的结论里写着一句本件必须照搬的话：

> 「合同想要的冠军证据是 **C 层结果遥测** —— 而遥测至今 **0 条**。
>  关键词之所以主导，是因为 **C 从来没有打开过**，不是有人选它当冠军。」

⇒ 本件报的是**违约的事实**，**不是**指认谁选错了。真正的出路是 C 层拿到 ≥60 条
  可归因结果（`route_team_moe.load_telemetry` 的门槛），那不是改词表能解决的。

## 量什么：`domain_match` 占**排序驱动**的份额

排序驱动不是权重，是 **weight × σ**（σ=0 的分项权重再大也不动名次）。
`route_team_moe.ranking_drivers()` 已经现算这张表，本件只是把它跑成一个可回归的数。

而 `domain_match` 的**任务那一侧**正是人工关键词表：

    infer_domains(task)  ←  DOMAIN_SIGNALS（手工维护的词表）
    domain_match = |CATEGORY_DOMAINS[候选人的族] ∩ 任务的域| / |任务的域|

（候选人那一侧是 `registration_category`，是策展字段，不是词表；**本件只就任务侧下判断**。）

## 首跑实测（2026-08-18 @v0.0.0.31）

单题（「为一个遗留微服务代码库设计测试策略与重构方案」，deep_team/14）：

    domain_match  weight 0.150｜σ 0.4925｜weight×σ 0.07388｜**share 64.6%**
    第二名 packet_similarity 9.8%｜task_similarity 9.5%｜capability_match 5.2%

默认样本（名册标签前 12 条）：

    **domain_match 当第一驱动的任务：8 / 12 = 67%**   ← 合同问的「主要证据」是这个
    份额：中位 **46.6%**｜最小 **0.0%**｜最大 59.5%

**在三分之二的任务上，冠军路由的主要证据就是那张人工词表。** 与合同那句话正面冲突。

### ★★★ 换第二份样本，这个数**涨到 92%**（★ 订正：我先前写 100%，那是只覆盖 3 个题面的读数）

|  | 样本 | 当第一驱动 | 份额中位 |
|---|---|---:|---:|
| 默认 | 名册标签 12 条（名词短语，33 字） | **8/12 = 67%** | 46.6% |
| **`--tasks`** | **72 道 TaskPack oracle 全量**（12 个题面 × 6 变体） | **66/72 = 92%** | — |
| 同上·去变体 | **12 个独立题面** | **11/12 = 92%** | — |

⇒ **默认样本低估了问题**：在更像真实提问的那份上，**12 个题面里 11 个的冠军驱动是那张人工词表**。

★★ **我先前在这里写的是「12/12 = 100%」——那是拿 `--limit 12` 取「前 12 条」得到的，
  而 oracle 文件**按题面聚集排列**（题面1×4、题面2×4…），**前 12 条只覆盖 3 个题面**。
  同一题面的 4 个变体当然一致 ⇒ 那个 100% 是**重复计数**堆出来的。
  全量 72 条（12 个题面）实测 **92%**。**方向不变，但「每一道都是」不成立。**
  [[samples-cannot-support-universal-claims]]｜[[uniqueness-counted-on-a-thin-sample-is-manufactured]]

  复现：`python3 _pipeline/export_benchmark_tasks.py -o /tmp/b72.json`
        `--tasks /tmp/b72.json --limit 72 --baseline-top-rate 1.0`

## 它是**回归地板**，不是会挡人的门

首跑就违约，而修它要么改词表、要么改权重 —— **都会移动每一道真实任务选出的人**，
属「门、席位一概不动」的范围，要 Owner 定（Task #123 ③）。
一道从建成起就红、且只能靠改产品行为才转绿的门不是信号。
所以：**rc=1 只在「当第一驱动的任务占比」比基线更高时**（＝更依赖词表了）。
★ 主指标是**名次**不是份额 —— 合同问的是「是不是**主要**证据」。
  份额随样本大幅漂（同一天三份样本：单题 64.6%、12 条名册标签中位 46.6%、台账记 65.1%），
  「谁排第一」稳得多。份额照印，只是不当地板。
[[a-red-that-can-never-turn-green-is-not-a-signal]]｜[[no-blocking-on-gate-shortfall]]

## ★★★ 非退化守卫（防共用零件）

本件读的 `ranking_drivers` 与被判对象同源。若打分坍成常数，**所有 σ=0**，
份额会退化成「谁都不是驱动」而看着像**合规**——违规与合规映射到同一读数。
所以硬下限：**至少两个分项 σ>0，且候选人数 ≥10**，达不到 ⇒ **rc=4 未量，不是通过**。
[[a-gate-must-not-share-a-part-with-what-it-guards]]｜[[weight-is-not-the-driver-weight-times-sigma-is]]

## 样本

默认用**产物自带的 `application_scenarios`**（不是我编的）。
若 `--tasks <文件>` 给了外部任务集则改用它，并关闭「标签不是用户提问」那句射程话。
★ 同一天实测：**两份样本会给出相反的图**（名册标签 vs 72 道 oracle），
  所以本件**永远连样本一起印**。

退出码：0＝当第一驱动的占比未超基线；1＝更依赖词表了；4＝非退化守卫没过 / 取不到样本（未量）。
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import statistics
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent

CONTRACT = ROOT / "references" / "moe-routing-contract.md"
CONTRACT_LINE = "人工关键词不得成为冠军路由的主要证据"

#: ★★★ **主指标是「当第一驱动的任务占比」，不是份额** —— 合同问的是
#: 「是不是**主要**证据」，那是个**名次**问题。份额随样本大幅漂
#: （同一天三份样本：单题 64.6%、12 条名册标签中位 46.6%、台账记 65.1%），
#: 而「谁排第一」稳得多。份额仍然照印，只是不当地板。
#: [[counts-need-their-cutoff-stated]]｜[[changing-the-sampling-unit-changes-the-ruler]]
#: 首跑实测 **8/12 = 0.67**（默认样本＝名册标签前 12 条）。地板就设在实测值上：
#: 设成 1.00 会让这道门**永远红不了**，那不是信号。★ 换 `--tasks` 就换了样本，
#: 地板也要跟着换 —— 用 `--baseline-top-rate` 显式给。
#: [[zero-hit-gates-must-prove-they-can-hit]]
BASELINE_TOP_RATE = 0.67
BASELINE_LIMIT = 12        # ★★★ 基线是**在这个样本量上**测的；换了样本量它就不适用
BASELINE_SHARE = 0.70      # 只印，不当地板
MIN_NONZERO_SIGMA = 2      # 非退化①：至少两个分项 σ>0
MIN_CANDIDATES = 10        # 非退化②：合格候选人数下限


def sample_tasks(limit: int) -> tuple[list[str], str]:
    idx = ROOT / "team-index.json"
    if not idx.is_file():
        return [], "team-index.json 不在"
    data = json.loads(idx.read_text(encoding="utf-8"))
    out = []
    for p in data.get("products", []):
        for sc in (p.get("application_scenarios") or [])[:1]:
            if isinstance(sc, str) and sc.strip():
                out.append(sc.strip())
    return out[:limit], "产物自带的 `application_scenarios`"


def observe(task: str, mode: str, size: int) -> dict | None:
    r = subprocess.run(
        [sys.executable, str(HERE / "route_team_moe.py"), "--task", task,
         "--mode", mode, "--size", str(size)],
        capture_output=True, text=True)
    if r.returncode != 0 or not r.stdout.strip():
        return None
    try:
        return json.loads(r.stdout[r.stdout.find("{"):])
    except ValueError:
        return None


def share_of(plan: dict, component: str = "domain_match"):
    """→ `(份额, σ>0 的分项数, 合格候选数, 是不是第一驱动)`；取不到就 `(None, 0, 0, None)`。

    ★ 「是不是第一驱动」按 **weight×σ 最大**判 —— 那正是 `ranking_drivers` 的排序依据，
      也正是合同那句「**主要**证据」问的东西。**份额是量，名次是它问的。**
    """
    ro = plan.get("routing_observability") or {}
    comps = ro.get("ranking_components") or []
    if not comps:
        return None, 0, 0, None
    nonzero = sum(1 for c in comps if float(c.get("sigma") or 0) > 0)
    elig = int(ro.get("eligible_candidates") or 0)
    hit = next((c for c in comps if c.get("component") == component), None)
    top = max(comps, key=lambda c: float(c.get("weight_x_sigma") or c.get("share") or 0))
    is_top = (top.get("component") == component) if nonzero else None
    return ((float(hit["share"]) if hit and hit.get("share") is not None else None),
            nonzero, elig, is_top)



#: ★★★★ 2026-08-18：**「取前 N 条」不等于「N 个不同的题」。**
#:   本件用 `--tasks` 读 72 道 oracle 时取了 `tasks[:limit]`，而那份文件
#:   **按题面聚集排列**（题面1×4、题面2×4…）⇒ 前 8 条只覆盖 **2** 个题面、
#:   前 12 条只覆盖 **3** 个。我因此报出过一个 **100%** 和一个**窄区间**，
#:   两者都是**同一题面的多个变体互相凑**出来的。
#:   ⇒ 凡按 `--tasks` 取样，**必须连「覆盖几个独立题面」一起印**。
#:   [[uniqueness-counted-on-a-thin-sample-is-manufactured]]｜[[samples-cannot-support-universal-claims]]
_VARIANT_TAIL = re.compile(r"\s*变体\s*\d+\s*[：:].*$", re.S)


def stem_coverage(tasks: list) -> tuple:
    """→ `(独立题面数, 样本数)`。去掉「 变体 N：…」尾巴后按题面去重。"""
    stems = {_VARIANT_TAIL.sub("", str(t)).strip() for t in tasks}
    return len(stems), len(tasks)


def print_stem_note(tasks: list) -> None:
    n_stem, n = stem_coverage(tasks)
    print("  ★ **覆盖 %d 个独立题面 / %d 条样本**%s"
          % (n_stem, n, "" if n_stem == n else "（同一题面的多个变体**对与长度无关的指标不带额外信息**；★ 对 `complexity` 这类**按字数算**的指标它们**会改结果**）"))
    if n_stem < 5:
        print("  ★★ **独立题面只有 %d 个 —— 下面的比例与区间都撑不起结论**；"
              "取样时请覆盖到更多题面。" % n_stem)

def contract_line_present() -> bool:
    if not CONTRACT.is_file():
        return False
    return CONTRACT_LINE in CONTRACT.read_text(encoding="utf-8")


def self_test() -> int:
    ok = True

    def chk(name, cond):
        nonlocal ok
        ok = ok and bool(cond)
        print("  %s %s" % ("✓" if cond else "**✗**", name))

    print("自测：")
    chk("① 合同里那句话还在（**它没了本件就无的放矢**）", contract_line_present())

    good = {"routing_observability": {
        "eligible_candidates": 50,
        "ranking_components": [
            {"component": "domain_match", "sigma": 0.49, "share": 0.646},
            {"component": "task_similarity", "sigma": 0.045, "share": 0.095},
            {"component": "evidence_strength", "sigma": 0.0, "share": 0.0}]}}
    s, nz, el, top = share_of(good)
    chk("② 正对照：读得出份额 0.646、σ>0 的分项 2 个、合格 50 人、**它是第一驱动**",
        abs(s - 0.646) < 1e-9 and nz == 2 and el == 50 and top is True)
    other = {"routing_observability": {"eligible_candidates": 50, "ranking_components": [
        {"component": "domain_match", "sigma": 0.01, "weight_x_sigma": 0.001, "share": 0.05},
        {"component": "task_similarity", "sigma": 0.5, "weight_x_sigma": 0.12, "share": 0.80}]}}
    chk("②b ★ 负对照：别人当第一驱动时要判 False（不能永远说 True）",
        share_of(other)[3] is False)

    # ★★★ 负对照①：**打分坍成常数** —— 所有 σ=0，份额看着像 0（＝「不是驱动」＝合规）
    dead = {"routing_observability": {
        "eligible_candidates": 50,
        "ranking_components": [
            {"component": "domain_match", "sigma": 0.0, "share": 0.0},
            {"component": "task_similarity", "sigma": 0.0, "share": 0.0}]}}
    s2, nz2, _, top2 = share_of(dead)
    chk("③ ★★★ 负对照：σ 全 0 时份额是 0（**看着像合规**），且第一驱动判 None 不判 False",
        s2 == 0.0 and top2 is None)
    chk("④ 而非退化守卫抓得住它（σ>0 的分项 %d < %d）" % (nz2, MIN_NONZERO_SIGMA),
        nz2 < MIN_NONZERO_SIGMA)

    # ★ 负对照②：候选太少 ⇒ σ 不可信
    thin = {"routing_observability": {
        "eligible_candidates": 3,
        "ranking_components": [
            {"component": "domain_match", "sigma": 0.4, "share": 0.9},
            {"component": "task_similarity", "sigma": 0.1, "share": 0.1}]}}
    _, nz3, el3, _t3 = share_of(thin)
    chk("⑤ ★ 负对照：合格只 3 人 ⇒ 由 main 判未量（%d < %d）" % (el3, MIN_CANDIDATES),
        el3 < MIN_CANDIDATES)

    # ★ 缺字段不炸
    s4, nz4, el4, t4 = share_of({"routing_observability": {}})
    chk("⑥ 缺 ranking_components 时返回 (None,0,0,None)，不抛异常",
        s4 is None and nz4 == 0 and el4 == 0 and t4 is None)

    chk("⑦ 两条基线都在 (0,1] 之内且不为 0（地板压到 0 等于把本件关掉）",
        0 < BASELINE_SHARE <= 1.0 and 0 < BASELINE_TOP_RATE <= 1.0)
    chk("⑧ ★★ 地板不是 1.00（设成 1.00 这道门永远红不了）", BASELINE_TOP_RATE < 1.0)
    chk("⑨ ★★★ 基线记着它自己的样本量（换了样本量不给新地板要判未量）",
        isinstance(BASELINE_LIMIT, int) and BASELINE_LIMIT > 0)


    # ── stem_coverage：正 + 负对照 ──
    chk("★ 正对照：全不同的题面 ⇒ 覆盖数 == 样本数",
        stem_coverage(["甲的问题。", "乙的问题。", "丙的问题。"]) == (3, 3))
    chk("★★ 负对照：同一题面的 4 个变体 ⇒ **覆盖数 1、样本数 4**（这正是我踩过的那一脚）",
        stem_coverage(["某题。 变体 1：要求证据可追溯。",
                       "某题。 变体 2：要求证据可追溯。",
                       "某题。 变体 3：要求证据可追溯。",
                       "某题。 变体 4：要求证据可追溯。"]) == (1, 4))
    chk("★ 负对照：不含「变体」的题面**一个字都不许动**",
        stem_coverage(["诊断一个单一领域问题，列出假设、证据缺口、结论和改判条件。"]) == (1, 1))

    print("自测：%s" % ("**全过**" if ok else "**有失败**"))
    return 0 if ok else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--limit", type=int, default=BASELINE_LIMIT,
                    help="跑多少条任务（默认 %d，＝基线的样本量）" % BASELINE_LIMIT)
    ap.add_argument("--mode", default="deep_team")
    ap.add_argument("--size", type=int, default=14)
    ap.add_argument("--tasks", default=None, metavar="文件",
                    help="改用外部任务集（每行一条，或 JSON 数组）")
    ap.add_argument("--baseline-top-rate", dest="baseline_top_rate",
                    type=float, default=BASELINE_TOP_RATE,
                    help="回归地板：当第一驱动的占比超过它才判红（默认 %.2f）" % BASELINE_TOP_RATE)
    ap.add_argument("--self-test", "--selftest", dest="selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return self_test()

    # ★★★ **基线只对它自己那份样本成立。** 换了样本量或换了任务集却不给新地板，
    #   判据会拿一个不适用的数去判 —— 那比不判更坏。判未量，并把出路印出来。
    #   （我自己刚踩了这一脚：调用方用 `--limit 8` 跑，8 条上是 6/8=75% > 0.67 ⇒ 误报回归。）
    #   [[counts-need-their-cutoff-stated]]｜[[error-message-points-at-an-exit-that-isnt-there]]
    explicit_floor = any(x.startswith("--baseline-top-rate") for x in (argv or sys.argv[1:]))
    if not explicit_floor and (a.limit != BASELINE_LIMIT or a.tasks):
        print("★ **未量，不是通过**（rc=4）—— 基线 %.2f 是在**默认样本、--limit %d** 上测的，"
              % (BASELINE_TOP_RATE, BASELINE_LIMIT))
        print("  而本次%s%s。"
              % ("换了任务集 `%s`" % a.tasks if a.tasks else "",
                 ("、" if a.tasks else "") + "用了 --limit %d" % a.limit
                 if a.limit != BASELINE_LIMIT else ""))
        print("  ⇒ **显式给一个地板**：`--baseline-top-rate <0..1>`；"
              "或去掉 `--limit`／`--tasks` 用默认样本。")
        return 4

    if a.tasks:
        tp = pathlib.Path(a.tasks)
        if not tp.is_file():
            print("★ **未量，不是通过**（rc=4）—— 任务集文件不在：%s" % tp)
            return 4
        raw = tp.read_text(encoding="utf-8")
        try:
            tasks = [str(x) for x in json.loads(raw) if str(x).strip()]
        except ValueError:
            tasks = [ln.strip() for ln in raw.splitlines()
                     if ln.strip() and not ln.lstrip().startswith("#")]
        tasks, src = tasks[:a.limit], "外部任务集 `%s`" % tp.name
    else:
        tasks, src = sample_tasks(a.limit)

    print("# 人工关键词是不是冠军路由的主要证据\n")
    print("合同（`references/moe-routing-contract.md` A 层）：**「%s」**" % CONTRACT_LINE)
    if not contract_line_present():
        print("★ **未量，不是通过**（rc=4）—— 合同里找不到这句话了，本件无的放矢。")
        return 4
    print("样本：**%d** 条，来自%s" % (len(tasks), src))
    print_stem_note(tasks)
    if not a.tasks:
        print("  ★★ **射程**：这是**名册标签**不是用户提问。同一天实测：换成 72 道 oracle "
              "任务集，`single_expert` 与无域信号两项的读数**与本样本相反**。"
              "**任何一个百分数都要连样本一起读。**")
    if not tasks:
        print("\n★ **未量，不是通过**（rc=4）—— 一条样本都取不到")
        return 4

    shares, nonzeros, eligs, tops, failed = [], [], [], [], 0
    for t in tasks:
        plan = observe(t, a.mode, a.size)
        if plan is None:
            failed += 1
            continue
        s, nz, el, is_top = share_of(plan)
        if s is None:
            failed += 1
            continue
        shares.append(s)
        nonzeros.append(nz)
        eligs.append(el)
        tops.append(bool(is_top))

    print("\n跑通 **%d** 条｜失败 %d 条" % (len(shares), failed))
    if not shares:
        print("★ **未量，不是通过**（rc=4）—— 一条也没读出 `ranking_components`")
        return 4

    min_nz = min(nonzeros)
    min_el = min(eligs)
    if min_nz < MIN_NONZERO_SIGMA or min_el < MIN_CANDIDATES:
        print("\n★ **未量，不是通过**（rc=4）—— 非退化守卫没过："
              "σ>0 的分项最少 **%d**（要 ≥%d）、合格候选最少 **%d**（要 ≥%d）。"
              % (min_nz, MIN_NONZERO_SIGMA, min_el, MIN_CANDIDATES))
        print("  ★ 这一档防的是**共用零件**：打分若坍成常数，份额会退化成 0，"
              "**看着像合规**，而那正是最坏的坏。")
        return 4

    top_rate = sum(tops) / len(tops)
    med = statistics.median(shares)
    print("**`domain_match` 当第一驱动的任务：%d / %d = %.0f%%**  ← 合同问的「主要证据」是这个"
          % (sum(tops), len(tops), 100 * top_rate))
    print("`domain_match` 占排序驱动（weight×σ）的份额："
          "**中位 %.1f%%**｜最小 %.1f%%｜最大 %.1f%%"
          % (100 * med, 100 * min(shares), 100 * max(shares)))
    print("  （合格候选中位 %d 人｜σ>0 的分项中位 %d 个）"
          % (statistics.median(eligs), statistics.median(nonzeros)))
    print("\n★ `domain_match` 的**任务那一侧**来自 `DOMAIN_SIGNALS` —— **手工维护的关键词表**。")
    print("★★ **因果**：合同想要的冠军证据是 **C 层结果遥测**，而遥测至今 **0 条**"
          "（C 要 ≥60 条可归因结果）。")
    print("   关键词之所以主导，是因为 **C 从来没有打开过** —— 不是有人选它当冠军。")
    print("  候选人那一侧是 `registration_category`（策展字段，不是词表）；本件只就任务侧下判断。")

    if top_rate > a.baseline_top_rate:
        print("\n✗ **比基线更依赖词表**（rc=1）—— 当第一驱动 %.0f%% > 基线 %.0f%%。"
              % (100 * top_rate, 100 * a.baseline_top_rate))
        return 1
    print("\n△ **与合同那句话正面冲突**：%d/%d 条任务上，冠军驱动就是那张人工词表"
          "（份额中位 %.1f%%）。未超基线 %.0f%% ⇒ rc=0。"
          % (sum(tops), len(tops), 100 * med, 100 * a.baseline_top_rate))
    print("  ★ 本件**不建议改词表或权重** —— 那会移动每一道真实任务选出的人，")
    print("    属「门、席位一概不动」，要 Owner 定（Task #123 ③）。")
    print("  ★★ 本件的产出是一句可证伪的话："
          "「**%d/%d 条任务的冠军驱动是人工词表**，份额中位 %.1f%%」。"
          % (sum(tops), len(tops), 100 * med))
    return 0


if __name__ == "__main__":
    sys.exit(main())
