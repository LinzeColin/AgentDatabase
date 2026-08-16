#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""路由到底有没有分辨力 —— **对着随机抽人比一次**。

为什么要有这份文件
------------------
2026-08-15 Owner 的评价：「路由、覆盖、记录、自优化迭代、有效激活调用、命中率
**都没有实质性收益和效果**」。任务包自己的验收是 PASS 的 —— 它验的是
「链路跑得通」，不是「选对了人」。**两件不同的事。**

实测触发：给「小团队项目管理 SaaS 该按人头月付还是按项目计费」跑真实入口，
`small_team` 选出 9 人，里面有**焊接裂纹与失效机理**专家、**压力设备与管道**
专家、两个**编程语言设计者**。而分数带是：

    入选 9 人 base_score  0.1375 – 0.2060（σ=0.0228）
    排除 61 人 base_score  0.0000 – 0.1989
    ⇒ **入选最低 < 排除最高，两个区间重叠**

## 这份判据回答的那一个问题

**路由选出的队伍，含相关身份族的比例，比「从同一个可选池里按同样人数随机抽」
高多少？** 高不了就是没有分辨力 —— 无论链路多完整。

## 它怎么不作弊

★ **相关族是按任务文本预先标的，与路由器用的字段无关**（路由器用
  `application_scenarios`／`key_capabilities`／`base_score`；本件只用
  `registration_category`）。不拿路由器自己的信号当答案。
★ **随机基线从真实可选池抽，带着池子本身的族偏斜**（软件开发师 34、
  投资资本师 21、材料建工师 15……）。拿均匀分布当 null 会把偏斜算成本事。
  [[negative-control-must-not-share-the-assumption]]
★ **正对照**：内置一个「答案明显」的任务（写 Python API 的可读性），
  若连它都不比随机高，那是本件的尺子坏了，不是产品坏了。
★ 随机基线用**固定种子**，可复算。

## 它答不了什么（必须一起念）

1. 它**不判最终答案对不对** —— 那要盲测，要两个互相独立的会话。
   本件只量路由这一层。[[bibliographic-proxy-instead-of-the-measurement]]
2. 族相关性是**我标的**。标签逐条写在 TASKS 里，可以被推翻；
   推翻它就推翻本件的结论。[[self-report-is-not-evidence]]
3. 「随机抽也差不多」**不等于人物无用** —— 只等于**这一层的选择没有增益**。

用法
----
    python3 measure_routing_discrimination.py --self-test
    python3 measure_routing_discrimination.py --registry-root <group 目录>
    python3 measure_routing_discrimination.py --registry-root <...> --trials 500
"""
import argparse
import json
import pathlib
import random
import statistics
import subprocess
import sys

# ── 任务集：`relevant` 是**按任务文本标的**，与路由器用的字段无关 ──────────
#   每条都写清「为什么这几族相关」，让它可以被逐条反驳。
TASKS = [
    {
        "id": "pricing-saas",
        "task": "我们要给一款面向小团队的项目管理 SaaS 定价，"
                "现在有按人头月付和按项目数计费两种方案，选哪个？",
        "relevant": ["创业经营师", "客户营销师", "财务合规师", "投资资本师"],
        "why": "定价 = 商业模式（创业经营）＋ 获客与包装（客户营销）＋ "
               "收入确认与合规（财务合规）＋ 单位经济与回报（投资资本）。",
    },
    {
        "id": "api-readability",
        "task": "我们的 Python SDK 有 40 个公开函数，命名和参数顺序很不一致，"
                "要怎么重新设计才让人一看就会用？",
        "relevant": ["软件开发师", "艺术设计师"],
        "why": "★ **正对照**：API 可读性设计是软件开发师的正题；"
               "「让人一看就会用」把设计师也拉进来。这一条若不比随机高，"
               "是尺子坏了。",
    },
    {
        "id": "steel-weld-failure",
        "task": "一批压力容器的焊缝在服役 8 个月后出现裂纹，"
                "要判断是材料、工艺还是设计的问题，怎么查？",
        "relevant": ["材料建工师", "建造采购师"],
        "why": "焊缝失效机理与压力设备评价，正是材料建工与建造采购的正题。",
    },
    {
        "id": "clinical-triage",
        "task": "县医院急诊分诊流程要重做，怎么在护士人手不足的情况下"
                "既不漏掉重症又不让轻症等太久？",
        "relevant": ["医疗护理师"],
        "why": "★ 这一条**注定命中 0** —— 名册里医疗护理师是 0 人。"
               "留着它是为了让「族缺口」在数字上现形，不是为了凑分。",
    },
    {
        "id": "land-lease-dispute",
        "task": "一块租了 20 年的农地，出租方现在要提前收回，"
                "合同里没写提前解约条款，我们该怎么谈？",
        "relevant": ["政治法律师", "农林牧渔师"],
        "why": "合同争议与谈判（政治法律）＋ 农地经营实务（农林牧渔）。",
    },
    {
        "id": "factory-layout",
        "task": "新车间要排产线，工位怎么摆能让在制品最少、换型最快？",
        "relevant": ["建造采购师", "创业经营师", "材料建工师"],
        "why": "厂房与工位布置（建造采购）＋ 生产组织（创业经营）＋ 工艺约束（材料建工）。",
    },
]

DEFAULT_TRIALS = 400
SEED = 20260815


def run_router(registry_root, task, mode="auto"):
    """→ (选中成员的 registration_category 列表, 可选池大小, route-plan)。"""
    script = pathlib.Path(registry_root) / "scripts" / "route_team_moe.py"
    out = subprocess.run(
        [sys.executable, str(script), "--task", task,
         "--mode", mode, "--registry-root", str(registry_root)],
        capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError("route_team_moe 失败 rc=%d：%s" % (out.returncode, out.stderr[:300]))
    plan = json.loads(out.stdout[out.stdout.find("{"):])
    cats = [m.get("registration_category") for m in plan.get("members", [])]
    obs = plan.get("routing_observability") or {}
    return cats, obs.get("eligible_candidates"), plan


def eligible_pool_categories(registry_root):
    """真实可选池的族分布 —— 随机基线必须**带着池子的偏斜**抽。"""
    admission = pathlib.Path(registry_root) / "expert-fleet-admission.json"
    d = json.loads(admission.read_text(encoding="utf-8"))
    rows = d if isinstance(d, list) else None
    if rows is None:
        for v in d.values():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                rows = v
                break
    rows = rows or []
    ok = [r for r in rows if str(r.get("admission")) == "eligible"]
    return [r.get("registration_category") for r in ok]


def hit_rate(cats, relevant):
    if not cats:
        return 0.0
    return sum(1 for c in cats if c in relevant) / len(cats)


def random_baseline(pool, k, relevant, trials, rng):
    """从**真实可选池**抽 k 人（不放回），重复 trials 次。"""
    if len(pool) < k:
        return None, None
    xs = []
    for _ in range(trials):
        xs.append(hit_rate(rng.sample(pool, k), relevant))
    return statistics.mean(xs), statistics.pstdev(xs)


def selftest():
    bad = []
    rng = random.Random(SEED)
    pool = ["A"] * 30 + ["B"] * 30 + ["C"] * 40

    # ① 全命中 / 全不命中 / 一半
    for cats, rel, want in [(["A", "A"], ["A"], 1.0), (["B", "C"], ["A"], 0.0),
                            (["A", "B"], ["A"], 0.5), ([], ["A"], 0.0)]:
        got = hit_rate(cats, rel)
        if abs(got - want) > 1e-9:
            bad.append("hit_rate(%s,%s) 期望 %.2f 得 %.2f" % (cats, rel, want, got))

    # ② 随机基线要贴近池子里该族的占比 —— 抽 10 人、A 占 30% ⇒ 均值≈0.30
    mean, _ = random_baseline(pool, 10, ["A"], 2000, rng)
    if not (0.27 <= mean <= 0.33):
        bad.append("随机基线偏了：抽 10 人 A 命中率均值 %.4f，池中 A 占 0.30" % mean)

    # ③ ★ 负对照：**基线必须带池子的偏斜**。若拿均匀分布当 null，
    #    抽 C（占 40%）会被算成 1/3 而不是 0.40 —— 那样偏斜会被记成本事。
    meanC, _ = random_baseline(pool, 10, ["C"], 2000, rng)
    if not (0.37 <= meanC <= 0.43):
        bad.append("★ 基线没带偏斜：C 占 0.40 而基线给 %.4f" % meanC)
    if abs(meanC - mean) < 0.05:
        bad.append("★ 基线对不同占比的族给了几乎一样的数 —— 它没在看池子")

    # ④ 池子比队伍还小时明说不可算，不许悄悄返回 0
    m, _ = random_baseline(["A"] * 3, 5, ["A"], 10, rng)
    if m is not None:
        bad.append("池子(3) < 队伍(5) 时应返回 None，实得 %r" % m)

    for b in bad:
        print("  ✗ " + b)
    n = 4 + 3 + 1
    print("自测 %d/%d" % (n - len(bad), n))
    return 1 if bad else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--registry-root")
    ap.add_argument("--trials", type=int, default=DEFAULT_TRIALS)
    ap.add_argument("--self-test", "--selftest", dest="selftest", action="store_true")
    ap.add_argument("--json", dest="as_json", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.registry_root:
        ap.error("要 --registry-root（persona-distiller-group 目录），或只跑 --self-test")

    root = pathlib.Path(a.registry_root).resolve()
    pool = eligible_pool_categories(root)
    rng = random.Random(SEED)
    print("可选池 %d 人；随机基线 %d 次（seed=%d，**从真实池按其族偏斜抽**）\n"
          % (len(pool), a.trials, SEED))

    rows = []
    for t in TASKS:
        cats, n_elig, plan = run_router(root, t["task"])
        routed = hit_rate(cats, t["relevant"])
        base, sd = random_baseline(pool, len(cats), t["relevant"], a.trials, rng)
        rows.append({
            "id": t["id"], "team_size": len(cats),
            "routed_hit": routed, "random_hit": base, "random_sd": sd,
            "delta": None if base is None else routed - base,
            "mode": plan.get("mode"), "strategy": plan.get("strategy"),
            "relevant": t["relevant"], "picked": cats,
            "_breakdowns": [m["score_breakdown"] for m in plan.get("members", [])
                            if isinstance(m.get("score_breakdown"), dict)],
        })

    print("%-20s %5s  %8s  %8s  %9s  %s" % ("任务", "人数", "路由命中", "随机命中", "差值", "模式/策略"))
    for r in rows:
        d = r["delta"]
        print("%-20s %5d  %7.1f%%  %7.1f%%  %+8.1f%%  %s/%s"
              % (r["id"], r["team_size"], 100 * r["routed_hit"], 100 * r["random_hit"],
                 100 * d, r["mode"], r["strategy"]))

    deltas = [r["delta"] for r in rows if r["delta"] is not None]
    mean_d = statistics.mean(deltas)
    wins = sum(1 for d in deltas if d > 0)
    print("\n  %d 个任务：路由高于随机 **%d** 个、低于 %d 个、平均差值 %+.1f 个百分点"
          % (len(deltas), wins, sum(1 for d in deltas if d < 0), 100 * mean_d))

    # ★★ **报均值必须连它离零几个 SE 一起报。** 本项目已栽过：
    #   +0.0291 被当成正收益，实际门落在它的不确定区间里；
    #   +0.00265 离零 0.48 SE，要 18 轮才判得出。
    #   [[a-reading-exactly-at-the-threshold-is-load-bearing]]｜[[gate-below-instrument-noise]]
    if len(deltas) >= 2:
        sd = statistics.stdev(deltas)
        se = sd / (len(deltas) ** 0.5)
        n_se = abs(mean_d) / se if se else float("inf")
        print("     σ %.1f pp｜SE %.1f pp｜**离零 %.2f SE** ⇒ %s"
              % (100 * sd, 100 * se, n_se,
                 "判不出与零的差别（<2 SE）—— **不许写成「有收益」**" if n_se < 2
                 else "离零 ≥2 SE"))
        need = int((2 * sd / abs(mean_d)) ** 2) + 1 if mean_d else None
        if need and n_se < 2:
            print("     要让这个效应量达到 2 SE，任务集需要约 **%d 个任务**（现有 %d 个）"
                  % (need, len(deltas)))

    # ★ 分层看：相关族在池子里**稀有**时路由才显出信号
    rare = [r for r in rows if r["random_hit"] is not None and 0 < r["random_hit"] < 0.15]
    common = [r for r in rows if r["random_hit"] is not None and r["random_hit"] >= 0.15]
    if rare and common:
        print("\n  ★★ 分层（按相关族在池中的稀有度）：")
        print("     随机基线 <15%%（相关族稀有）%d 个 → 平均 **%+.1f pp**：%s"
              % (len(rare), 100 * statistics.mean(r["delta"] for r in rare),
                 "、".join(r["id"] for r in rare)))
        print("     随机基线 ≥15%%（相关族常见）%d 个 → 平均 **%+.1f pp**：%s"
              % (len(common), 100 * statistics.mean(r["delta"] for r in common),
                 "、".join(r["id"] for r in common)))
        print("     ⇒ 相关族越常见，路由越接近（甚至低于）随机抽。")

    pos = next(r for r in rows if r["id"] == "api-readability")
    print("  ★ 正对照（api-readability，答案明显）：路由 %.1f%% vs 随机 %.1f%% ⇒ %s"
          % (100 * pos["routed_hit"], 100 * pos["random_hit"],
             "尺子是活的" if pos["delta"] > 0 else "**连正对照都不高 —— 先查本件，别急着判产品**"))

    zero = next(r for r in rows if r["id"] == "clinical-triage")
    print("  ★ 族缺口（clinical-triage）：路由 %.1f%% —— 名册里医疗护理师 **0 人**，"
          "这一条注定命中 0，是名册的洞不是路由的错" % (100 * zero["routed_hit"]))

    # ★★★ 分项诊断：**哪一项在真正分辨人**。
    #   路由≈随机不是玄学，去看打分的分项就知道 —— 若唯一有极差的那一项
    #   与任务无关（比如「人物年代新旧」），那它排的就是年代不是本事。
    flat = {}
    n_bd = 0
    for r in rows:
        for m in r.get("_breakdowns", []):
            n_bd += 1

            def walk(d, prefix=""):
                for k, v in d.items():
                    if isinstance(v, dict):
                        walk(v, prefix + k + ".")
                    elif isinstance(v, (int, float)):
                        flat.setdefault(prefix + k, []).append(v)
            walk(m)
    if flat:
        print("\n  ★★★ 打分分项的分辨力（样本：%d 个入选席位 / %d 个任务；"
              "**排除者不带 score_breakdown，取不到**）" % (n_bd, len(rows)))
        print("     %-32s %8s %8s" % ("分项", "极差", "σ"))
        dead = []
        for k, vs in sorted(flat.items(), key=lambda kv: -(max(kv[1]) - min(kv[1]))):
            rng_ = max(vs) - min(vs)
            print("     %-32s %8.4f %8.4f" % (k, rng_, statistics.pstdev(vs)))
            if rng_ == 0:
                dead.append(k)
        top = max(flat.items(), key=lambda kv: max(kv[1]) - min(kv[1]))
        print("     ⇒ 分辨力最大的是 **%s**（极差 %.4f）" % (top[0], max(top[1]) - min(top[1])))
        if dead:
            print("     ⇒ **对所有候选恒定、一点分辨力都没有的分项：%s**" % "、".join(dead))

    if a.as_json:
        print("\n" + json.dumps({"seed": SEED, "trials": a.trials,
                                 "pool_size": len(pool), "rows": rows},
                                ensure_ascii=False, indent=1))
    # 只报数，不设阈值 —— 阈值要 Owner 定。永远 rc=0。
    return 0


if __name__ == "__main__":
    sys.exit(main())
