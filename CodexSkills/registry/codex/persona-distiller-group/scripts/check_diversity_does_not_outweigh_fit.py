#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**多样性权重把「对口的人」换掉了多少？**

## 抓到它的那一次（2026-08-18）

`test_new_software_deliveries_are_available_to_routing` 红着，缺 Simon Willison。
追下去不是路由坏了、也不是缺人 —— 是 `marginal_select()` **重罚同族**。
一道英文软件工程评审题 size=14，产物自报的 `base_score` vs `marginal_score`：

     1 Kent Beck        软件开发师  0.3616 → **0.3548**
     2 Harry Bhadeshia  材料建工师  0.3076 → 0.2738
     5 **Joel Salatin   农林牧渔师  0.2299 → 0.2470**   ← **反涨 7%**（唯一的农林牧渔师）
    10 Chip Huyen       软件开发师  **0.3549**（全场第 2 高）→ **0.1872**（**掉 47%**）

**第 2–9 名每族各一人；第 10 名才回到第二个软件开发师。**
⇒ **一道软件工程评审题，14 人里只有 3 个软件开发师，第 5 位是农场主。**

## 临界点是**从源码算出来的**，不是估的

`route_team_moe.marginal_select()`：

    value = 0.76*base + diversity_bonus - 0.30*max_redundancy - repeat_penalty
      diversity_bonus = 0.08  当该族**首次**被选中，否则 0
      repeat_penalty  = min(0.12, 该族已选人数 * 0.025)

⇒ 同族第 2 人相对一个**新族**候选的净劣势 = 0.08 + 0.025 = **0.105**，
  折算到 base 上需领先 **0.105 / 0.76 = 0.1382**。

    实测对得上：Chip Huyen − Joel Salatin = 0.3549 − 0.2299 = **0.1250 < 0.1382**
                ⇒ Salatin 胜出（他第 5、Huyen 第 10）——**与实跑一致**。

    同族第 3 人需领先 0.1711｜第 5 人 0.2368｜penalty 封顶后最大 0.2632

## ★★★ **默认样本低估了这个问题** —— 两份样本一起报（★ 订正见下）

|  | 样本 | 换手率 |
|---|---|---:|
| 默认 | 名册标签 8 条（名词短语，33 字） | **中位 36%**（29–43%） |
| **`--tasks`** | **72 道 oracle 全量**（12 个题面 × 6 变体） | **中位 57%（43–79%）** |
| 同上·去变体 | **12 个独立题面** | **中位 57%（43–79%）** ← 与全量**完全相同**，变体不带信息 |

**在更像真实提问的那份样本上，按对口度排前列的人有近六成被换掉。**
⇒ 本件默认那个 36% **不是上界，是下界**。报它必须连样本一起报。

★★ **我先前在这里写的是「中位 61%（57–64%）」——那是 `--limit 8` 取「前 8 条」得到的，
  而 oracle 文件**按题面聚集排列**，**前 8 条只覆盖 2 个题面**。
  中位数只小动了 4 个点，但**区间从 57–64% 变成 43–79%** ——
  **那个窄区间看着像「稳定」，其实只是 2 个题面 × 4 个变体。**
  [[uniqueness-counted-on-a-thin-sample-is-manufactured]]｜[[samples-cannot-support-universal-claims]]

★ 两份都不是真实用户提问（一份产物自写的标签、一份任务包作者写的 oracle）——
  **真实提问的分布仍然没有量过。**

## 它量的是**换手率**，不是「好不好」

「多样性该不该压过对口度」是**设计取舍**，判据说了不算。本件只报一个可证伪的数：

> **按 `base_score` 排的前 K 名里，有几个没能进最终 K 人名单。**

两个分数都**由产物自己印出来**（`selected_roles[].base_score` / `.marginal_score`），
本件不重算打分 —— **不造第二把尺子**。
[[i-built-a-second-ruler-while-the-authoritative-one-sat-in-scripts]]

## ★★★ 非退化守卫：**公式变了，上面那些临界点就作废**

本件印的 0.1382/0.1711/… 全部依赖那四个常数。若有人改了它们而本件照印，
就是拿**过期的推导**去解释**现在的行为**。所以开跑先核那一段源码的形状，
对不上 ⇒ **rc=4 未量，不是通过**。
[[a-stale-reason-does-not-void-the-conclusion]]｜[[checkers-must-key-on-a-closed-set-not-on-wording]]

另两道：**选中人数 < 3 判未量**（两三个人谈不上多样性）；
**一条样本都跑不出判未量**。

退出码：0＝换手率未超基线；1＝比基线更严重；4＝公式形状变了/取不到样本（未量）。
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
ROUTER = HERE / "route_team_moe.py"

#: `marginal_select` 里那四个常数的**形状**。改了就说明推导要重做。
FORMULA_SHAPE = (
    r"value\s*=\s*0\.76\s*\*\s*item\[.base_score.\]\s*\+\s*diversity_bonus"
    r"\s*-\s*0\.30\s*\*\s*max_redundancy\s*-\s*repeat_penalty")
BONUS_SHAPE = r"diversity_bonus\s*=\s*0\.08\s+if\s+categories\[category\]\s*==\s*0\s+else\s+0\.0"
PENALTY_SHAPE = r"repeat_penalty\s*=\s*min\(0\.12,\s*categories\[category\]\s*\*\s*0\.025\)"

BASE_WEIGHT, BONUS, STEP, CAP = 0.76, 0.08, 0.025, 0.12

#: 回归地板：前 K 名被换掉的比例**超过**它才判红。
#: ★ **首跑实测中位 0.36**（8 条名册标签、mode=deep_team、size=14；范围 0.29–0.43），
#:   地板就设在实测值上 —— 设成 0.50 那样的圆整数会让它**很久红不了**，那不是信号。
#:   本指标**确定性**（同题同码同结果），没有跑间噪声，中位数可复现。
#:   [[zero-hit-gates-must-prove-they-can-hit]]
BASELINE_CHURN = 0.36
BASELINE_LIMIT = 8         # ★ 基线是在这个样本量上测的；换了就不适用
MIN_TEAM = 3               # 非退化：选中 <3 人谈不上多样性


def formula_intact() -> tuple[bool, list[str]]:
    """源码里那四个常数的形状还对得上吗。→ `(是否对得上, 对不上的项)`。"""
    try:
        src = ROUTER.read_text(encoding="utf-8")
    except OSError:
        return False, ["读不到 route_team_moe.py"]
    bad = []
    for name, pat in (("value 公式", FORMULA_SHAPE),
                      ("diversity_bonus", BONUS_SHAPE),
                      ("repeat_penalty", PENALTY_SHAPE)):
        if not re.search(pat, src):
            bad.append(name)
    return (not bad), bad


def tipping_point(nth_of_family: int) -> float:
    """同族第 `nth`（≥2）人要胜过一个**新族**候选，`base_score` 需领先多少。"""
    penalty = min(CAP, (nth_of_family - 1) * STEP)
    return (BONUS + penalty) / BASE_WEIGHT


def load_external(path: str, limit: int) -> tuple[list[str], str]:
    """外部任务集（每行一条，或 JSON 数组）。★ 留这个插座是因为**默认样本低估了问题**。"""
    tp = pathlib.Path(path)
    if not tp.is_file():
        return [], "任务集文件不在：%s" % tp
    raw = tp.read_text(encoding="utf-8")
    try:
        tasks = [str(x) for x in json.loads(raw) if str(x).strip()]
    except ValueError:
        tasks = [ln.strip() for ln in raw.splitlines()
                 if ln.strip() and not ln.lstrip().startswith("#")]
    return tasks[:limit], "外部任务集 `%s`" % tp.name



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
          % (n_stem, n, "" if n_stem == n else "（同一题面的多个变体**不带额外信息**）"))
    if n_stem < 5:
        print("  ★★ **独立题面只有 %d 个 —— 下面的比例与区间都撑不起结论**；"
              "取样时请覆盖到更多题面。" % n_stem)

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


def route(task: str, size: int, mode: str = "deep_team") -> list[dict] | None:
    # ★ **必须显式给 `--mode`**：名册标签多是名词短语，`--mode auto` 会推成
    #   `single_expert`，此时再给 `--size 14` 直接 ValueError ⇒ 一条都跑不出来。
    #   首版没给 `--mode`，实跑 **0/8**，判据如实报了 **rc=4 未量**（没有假绿）。
    #   [[zero-hit-gates-must-prove-they-can-hit]]
    r = subprocess.run(
        [sys.executable, str(HERE / "route_team_moe.py"), "--task", task,
         "--mode", mode, "--size", str(size)],
        capture_output=True, text=True)
    if r.returncode != 0 or not r.stdout.strip():
        return None
    try:
        plan = json.loads(r.stdout[r.stdout.find("{"):])
    except ValueError:
        return None
    return [x for x in (plan.get("selected_roles") or [])
            if x.get("role_type") == "persona-solver"]


def top_k_by_base(task: str, k: int, mode: str) -> list[str] | None:
    """全体合格候选里，按 `base_score` 排的前 K 是谁。

    ★★★ **第一版这里是错的**：我只拿路由**选中的那 K 个人**去比位次，
      而选中集合与「前 K」是同一批人时，membership 差恒为 0，
      于是我退而比**位次**，得出中位 89% —— **那量的是排序抖动，不是换手**。
      要问「谁被换掉了」，必须有**全体候选**的 base 排名，而产物只印选中的人。
      ⇒ 这里**调产品自己的 `score_candidate`** 现算全体候选（**不是另写一套打分**）。
      [[measure-a-change-at-the-layer-it-acts-on]]｜[[i-built-a-second-ruler-while-the-authoritative-one-sat-in-scripts]]
    """
    sys.path.insert(0, str(HERE))
    try:
        import route_team_moe as M
        from compile_task_graph import compile_graph
    except Exception:                                   # noqa: BLE001
        return None
    idx = ROOT / "team-index.json"
    if not idx.is_file():
        return None
    cards = json.loads(idx.read_text(encoding="utf-8")).get("products") or []
    adm, tel = M.load_admission(ROOT), M.load_telemetry(None)
    try:
        graph = compile_graph(task, mode, k)
    except Exception:                                   # noqa: BLE001
        return None
    rows = []
    for c in cards:
        score, _br, why = M.score_candidate(c, graph, "B", tel, adm)
        if why:
            continue
        rows.append((float(score), c.get("canonical_name")))
    if not rows:
        return None
    rows.sort(key=lambda r: -r[0])
    return [n for _s, n in rows[:k]]


def churn_of(solvers: list[dict], top_k: list[str]) -> tuple[float, dict, list[str]]:
    """→ `(换手率, 族分布, 被换掉的人)`。

    换手率 = **按 base 排前 K 里、没能进最终名单的人数 / K**。
    ★ 这是**成员**之差，不是位次之差。
    """
    k = len(top_k)
    chosen = {r.get("canonical_name") for r in solvers}
    dropped = [n for n in top_k if n not in chosen]
    cats: dict = {}
    for r in solvers:
        c = str(r.get("registration_category"))
        cats[c] = cats.get(c, 0) + 1
    return (len(dropped) / k if k else 0.0), cats, dropped


def self_test() -> int:
    ok = True

    def chk(name, cond):
        nonlocal ok
        ok = ok and bool(cond)
        print("  %s %s" % ("✓" if cond else "**✗**", name))

    print("自测：")
    intact, bad = formula_intact()
    chk("① 源码里那四个常数的形状还对得上（对不上则本件的推导作废）%s"
        % ("" if intact else "：%s" % bad), intact)

    chk("② 同族第 2 人的临界点 = (0.08+0.025)/0.76 = %.4f" % tipping_point(2),
        abs(tipping_point(2) - 0.105 / 0.76) < 1e-12)
    chk("③ 临界点随同族人数**单调不减**",
        tipping_point(2) < tipping_point(3) < tipping_point(5) <= tipping_point(9))
    chk("④ penalty 封顶后不再涨（第 6 人与第 9 人相同）",
        abs(tipping_point(6) - tipping_point(9)) < 1e-12)

    # ★★★ 正对照：实测那一对必须落在临界点的**正确一侧**
    chk("⑤ ★ 正对照：Huyen−Salatin base 差 0.1250 **小于** 临界点 %.4f ⇒ Salatin 该胜出"
        % tipping_point(2), (0.3549 - 0.2299) < tipping_point(2))

    # ★ 负对照：领先足够多的同族人应当胜出
    chk("⑥ ★ 负对照：若同族第 2 人领先 0.20（> %.4f），临界点不该再挡住他"
        % tipping_point(2), 0.20 > tipping_point(2))

    # churn：正/负对照
    team = [{"canonical_name": "A", "registration_category": "x"},
            {"canonical_name": "B", "registration_category": "y"}]
    c1, cats1, drop1 = churn_of(team, ["A", "B"])
    chk("⑦ ★ 正对照：前 K 全部入选 ⇒ 换手率 **0**", c1 == 0.0 and drop1 == [])
    c2, _, drop2 = churn_of(team, ["A", "C"])
    chk("⑧ ★ 负对照：前 K 里的 C 被换掉 ⇒ 换手率 **0.5**，且点得出是谁",
        abs(c2 - 0.5) < 1e-9 and drop2 == ["C"])
    c3, _, _ = churn_of(team, ["C", "D"])
    chk("⑧b ★★ 负对照：前 K 全被换掉 ⇒ **1.0**（本件必须够得到上界）", c3 == 1.0)
    chk("⑨ 族分布数得对", cats1 == {"x": 1, "y": 1})
    chk("⑩ 空的前 K 不炸（判 0，由 main 另行判未量）", churn_of([], [])[0] == 0.0)
    chk("⑪ 基线在 (0,1) 内 —— 0 会让它恒红、1 会让它恒绿",
        0 < BASELINE_CHURN < 1.0 and BASELINE_LIMIT > 0 and MIN_TEAM >= 3)


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
    ap.add_argument("--limit", type=int, default=BASELINE_LIMIT)
    ap.add_argument("--size", type=int, default=14)
    ap.add_argument("--mode", default="deep_team",
                    help="必须显式给 —— auto 会把名词短语标签推成 single_expert")
    ap.add_argument("--baseline-churn", type=float, default=BASELINE_CHURN)
    ap.add_argument("--tasks", default=None, metavar="文件",
                    help="改用外部任务集。★ 默认样本（名册标签）**低估了问题**："
                         "72 道 TaskPack oracle 上换手率中位 **61%%**，名册标签只有 36%%")
    ap.add_argument("--self-test", "--selftest", dest="selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return self_test()

    print("# 多样性权重把「对口的人」换掉了多少\n")
    intact, bad = formula_intact()
    if not intact:
        print("★ **未量，不是通过**（rc=4）—— `marginal_select` 的公式形状变了：%s" % bad)
        print("  本件印的所有临界点都是**从那四个常数推出来的**，形状一变就作废。")
        print("  ⇒ 先重做推导，再改这里的 `FORMULA_SHAPE`／常数，**不要直接放行**。")
        return 4

    print("`marginal_select()` 的公式（源码形状已核）：")
    print("    value = %.2f*base + diversity_bonus - 0.30*max_redundancy - repeat_penalty" % BASE_WEIGHT)
    print("      首次见到某族 bonus **+%.2f**｜第 n 个同族 penalty **min(%.2f, (n-1)*%.3f)**"
          % (BONUS, CAP, STEP))
    print("  ⇒ **同族第 n 人要胜过一个新族候选，`base_score` 需领先：**")
    for n in (2, 3, 5, 9):
        print("       第 %d 人  **%.4f**%s" % (n, tipping_point(n),
                                              "（penalty 已封顶）" if n >= 6 else ""))

    if (a.limit != BASELINE_LIMIT or a.tasks) and a.baseline_churn == BASELINE_CHURN:
        print("\n★ **未量，不是通过**（rc=4）—— 基线 %.2f 是在**默认样本、--limit %d** 上测的，"
              "本次%s%s。"
              % (BASELINE_CHURN, BASELINE_LIMIT,
                 ("换了任务集 `%s`" % a.tasks) if a.tasks else "",
                 ("、" if a.tasks else "") + ("用了 --limit %d" % a.limit)
                 if a.limit != BASELINE_LIMIT else ""))
        print("  ⇒ 显式给 `--baseline-churn <0..1>`，或去掉 `--limit`／`--tasks`。")
        return 4

    tasks, src = (load_external(a.tasks, a.limit) if a.tasks else sample_tasks(a.limit))
    print("\n样本：**%d** 条，来自%s｜mode=%s size=%d" % (len(tasks), src, a.mode, a.size))
    print_stem_note(tasks)
    print("  ★★ **射程**：这是**名册标签**不是用户提问；同一天实测换一份样本读数会翻。")
    if not tasks:
        print("\n★ **未量，不是通过**（rc=4）—— 一条样本都取不到")
        return 4

    churns, rows, failed = [], [], 0
    for t in tasks:
        solvers = route(t, a.size, a.mode)
        if not solvers or len(solvers) < MIN_TEAM:
            failed += 1
            continue
        tk = top_k_by_base(t, len(solvers), a.mode)
        if not tk:
            failed += 1
            continue
        c, cats, dropped = churn_of(solvers, tk)
        churns.append(c)
        rows.append((t, len(solvers), c, cats, dropped))

    print("\n跑通 **%d** 条｜跳过/失败 %d 条（选中 <%d 人或路由失败）"
          % (len(churns), failed, MIN_TEAM))
    if not churns:
        print("★ **未量，不是通过**（rc=4）—— 一条也没跑出够 %d 人的队伍" % MIN_TEAM)
        return 4

    med = statistics.median(churns)
    print("**换手率**（按 base 排的前 K 里**没能进最终名单**的人 / K）："
          "中位 **%.0f%%**｜最小 %.0f%%｜最大 %.0f%%"
          % (100 * med, 100 * min(churns), 100 * max(churns)))
    worst = max(rows, key=lambda r: r[2])
    print("\n最严重的一条（换手 %.0f%%）：「%s」" % (100 * worst[2], worst[0][:34]))
    print("  族分布：%s" % worst[3])
    print("  被换掉的（base 前 K 却没进名单）：%s" % ("、".join(str(x) for x in worst[4][:6]) or "无"))
    top_fam = max(worst[3].items(), key=lambda kv: kv[1]) if worst[3] else ("—", 0)
    print("  ⇒ **%d 人的队伍分散在 %d 个族**，最多的一族只有 **%d** 人。"
          % (worst[1], len(worst[3]), top_fam[1]))

    print("\n★ 「多样性该不该压过对口度」是**设计取舍**，本件不判对错 ——"
          "它只把这个数摆到台面上。")
    print("  要改只有调那四个常数（＝改路由，撞「门、席位一概不动」），**要 Owner 定**（#123 ⑩）。")

    if med > a.baseline_churn:
        print("\n✗ **比基线更严重**（rc=1）—— 中位换手 %.0f%% > 基线 %.0f%%。"
              % (100 * med, 100 * a.baseline_churn))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
