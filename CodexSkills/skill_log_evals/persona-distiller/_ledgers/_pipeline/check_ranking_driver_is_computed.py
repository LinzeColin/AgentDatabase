#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_ranking_driver_is_computed.py —— **`ranking_driver` 曾是二值标志冒充度量**

## 抓到它的那一次（2026-08-17）

`self_check.py`（README 教的第一条验证命令）rc=1，追下去有两条路由测试红：
一道纯软件工程题的前 14 名里，**农场主 Joel Salatin 排第 6**，
而 Martin Fowler / Barbara Liskov / Simon Willison 一个都没进（他们**没被排除**，
只是排在后面）。逐项拆开 Salatin 那 0.2049 分：

    task_similarity  0.000 × 0.24 = 0      ← 与题目相关
    scenario_match   0.000 × 0.10 = 0      ← 与题目相关
    capability_match 0.000 × 0.14 = 0      ← 与题目相关
    user_value_match 0.000 × 0.07 = 0      ← 与题目相关
    ────────────────────────────────  四项占总权重 0.55，他全是 0
    evidence         1.000 × 0.05 = 0.0500 （24.4%）  σ=0，人人相同
    domain_match     0.333 × 0.15 = 0.0500 （24.4%）  前 6 名全是 0.333
    currentness      0.750 × 0.06 = 0.0450 （22.0%）  只因为他是现代人
    boundary         1.000 × 0.04 = 0.0400 （19.5%）  σ=0，人人相同
    packet_similarity0.132 × 0.15 = 0.0199 （ 9.7%）

**90.3% 来自与题目无关的项**，其中两项 σ=0 —— 对名次贡献**精确为零**，
只是给每个合格者白送 0.09 分的地板。[[weight-is-not-the-driver-weight-times-sigma-is]]

## 而 observability 当时说的是什么

    "ranking_driver": ("domain_match" if domain_signal_candidates else "currentness …")

一个**二值标志**：只要有任一候选 `domain_match > 0`，就宣称 domain_match 在驱动排序。
实测那道题 **67/83 候选都「有 domain 信号」**（对 81% 的人为真，谈不上区分），
而现算 weight×σ 的第一名是 **task_similarity（27.4%）**，domain_match 只有 25.3%。
[[a-gate-that-says-independent-may-not-be]]｜[[a-comment-claiming-a-guard-is-not-a-guard]]

## 已改（只动披露，**没动排序**）

`route_team_moe.py`：权重表提到模块级单一真源；`ranking_driver` 改为
`ranking_drivers(ranked)[0]`（现算 weight×σ，σ 取**全部合格候选**而非入选那几个），
并新增 `ranking_components`（逐项 weight/σ/share）与
`selected_with_zero_task_relevance`（四项相关信号全 0 却入选的人）。

## 本件判什么

1. `ranking_driver` **必须等于** `ranking_components` 里 weight×σ 最大的那一项；
2. σ=0 的分项 share 必须是 0（否则「贡献精确为零」这句话就没落地）；
3. shares 之和 ≈ 1；
4. `selected_with_zero_task_relevance` **必须存在**（缺字段＝倒退回旧披露）。

★ 第 4 条**只查字段在不在，不拿它的长度当红线** —— 名单非空是**排序**的问题，
  而排序怎么改是产品决定。拿它当门会造出一道我这边永远变不绿的红。
  [[a-red-that-can-never-turn-green-is-not-a-signal]]｜[[no-blocking-on-gate-shortfall]]
  它的**数目照印**，不许藏。

退出码：0＝披露自洽；1＝披露与自己的数据打架；4＝跑不动路由（未量）。
"""
import argparse
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[4]
GROUP = REPO / "CodexSkills/registry/codex/persona-distiller-group"
TASK = ("Design a software engineering review covering TDD, refactoring, evolutionary "
        "architecture, Python SQLite CLI, coding-agent prompt injection, AI/ML evaluation "
        "monitoring feedback loops, distributed systems API type design and technical teaching")


def verdict(obs: dict):
    """→ (问题列表, 事实字典)。**纯函数**，不跑子进程，便于自测。"""
    bad, facts = [], {}
    comps = obs.get("ranking_components") or []
    if not comps:
        return ["`ranking_components` 缺席 —— 无法判定 ranking_driver 是算的还是断言的"], facts
    top = max(comps, key=lambda c: c["weight_x_sigma"])
    facts["top"] = top["component"]
    facts["driver"] = obs.get("ranking_driver")
    if obs.get("ranking_driver") != top["component"]:
        bad.append("`ranking_driver`=%r，而 weight×σ 最大的是 %r"
                   % (obs.get("ranking_driver"), top["component"]))
    for c in comps:
        if c["sigma"] == 0 and c["share"] != 0:
            bad.append("%s 的 σ=0，share 却是 %s（σ=0 的分项对名次贡献精确为零）"
                       % (c["component"], c["share"]))
    tot = sum(c["share"] for c in comps)
    facts["share_sum"] = round(tot, 4)
    if comps and abs(tot - 1.0) > 0.01:
        bad.append("shares 之和 = %.4f，不是 1" % tot)
    if "selected_with_zero_task_relevance" not in obs:
        bad.append("缺 `selected_with_zero_task_relevance` —— 倒退回了旧披露")
    facts["zero_relevance"] = obs.get("selected_with_zero_task_relevance")

    # ★★★ 「这把尺子看得见几个人」——2026-08-17 实测英文题只有 30%。
    #   用 **A + B == 全集** 对补集：reachable + blind 必须正好等于合格候选数，
    #   否则「30%」这个数就没有分母。[[a-gates-scan-set-is-smaller-than-reality]]
    reach, blind = obs.get("task_relevance_reachable"), obs.get("task_relevance_blind")
    if reach is None or blind is None:
        bad.append("缺 `task_relevance_reachable`/`task_relevance_blind` —— "
                   "「这把尺子对多少人恒为 0」这件事又变回不可见")
    else:
        facts["reachable"], facts["blind"] = reach, blind
        elig = obs.get("eligible_candidates")
        if elig is not None and reach + blind != elig:
            bad.append("reachable(%s) + blind(%s) = %s ≠ eligible_candidates(%s)"
                       % (reach, blind, reach + blind, elig))
    return bad, facts


def self_test() -> int:
    bad, tot = [], [0]

    def chk(lbl, ok):
        tot[0] += 1
        print(("  ✓ " if ok else "  ✗ ") + lbl)
        if not ok:
            bad.append(lbl)

    good = {"ranking_driver": "task_similarity",
            "selected_with_zero_task_relevance": [],
            "eligible_candidates": 83, "task_relevance_reachable": 25, "task_relevance_blind": 58,
            "ranking_components": [
                {"component": "task_similarity", "weight": .24, "sigma": .09, "weight_x_sigma": .0216, "share": .6},
                {"component": "domain_match", "weight": .15, "sigma": .06, "weight_x_sigma": .009, "share": .4},
                {"component": "evidence", "weight": .05, "sigma": 0.0, "weight_x_sigma": 0.0, "share": 0.0}]}
    chk("★ 自洽的披露 → 无问题", verdict(good)[0] == [])
    b = json.loads(json.dumps(good)); b["ranking_driver"] = "domain_match"
    chk("★★★ **driver 不是 weight×σ 最大的那项 → 报**（这正是抓到的那一次）",
        any("weight×σ 最大" in x for x in verdict(b)[0]))
    b = json.loads(json.dumps(good)); b["ranking_components"][2]["share"] = 0.1
    chk("★★ σ=0 却有 share → 报", any("σ=0" in x for x in verdict(b)[0]))
    b = json.loads(json.dumps(good)); b["ranking_components"][0]["share"] = 0.9
    chk("★★ shares 之和不为 1 → 报", any("之和" in x for x in verdict(b)[0]))
    b = json.loads(json.dumps(good)); b.pop("selected_with_zero_task_relevance")
    chk("★★★ 缺 `selected_with_zero_task_relevance` → **报倒退**",
        any("倒退" in x for x in verdict(b)[0]))
    b = json.loads(json.dumps(good)); b["selected_with_zero_task_relevance"] = ["Joel Salatin"] * 5
    chk("★★★ **反对照：名单非空本身不算问题**（那是排序的事，不是披露的事）—— "
        "它只能被印出来，不能当红线", verdict(b)[0] == [])
    chk("★★ `ranking_components` 缺席 ⇒ 报「无法判定」，不是通过",
        verdict({"ranking_driver": "x"})[0] != [])
    b = json.loads(json.dumps(good)); b.pop("task_relevance_blind")
    chk("★★★ 缺 `task_relevance_blind` → **报**（「尺子对多少人恒为 0」不许再变回不可见）",
        any("恒为 0" in x for x in verdict(b)[0]))
    b = json.loads(json.dumps(good)); b["task_relevance_blind"] = 57
    chk("★★★ **A + B ≠ 全集 → 报**（25+57≠83；「30%」没有分母就不成立）",
        any("≠ eligible_candidates" in x for x in verdict(b)[0]))
    b = json.loads(json.dumps(good)); b["task_relevance_reachable"] = 83; b["task_relevance_blind"] = 0
    chk("★★ 反对照：**全都看得见（blind=0）本身不是问题**，只要加起来对得上",
        verdict(b)[0] == [])
    print("\n自测 %d 项，不符 %d 项" % (tot[0], len(bad)))
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", "--selftest", dest="selftest", action="store_true")
    if ap.parse_args().selftest:
        return self_test()

    rt = GROUP / "scripts/route_team.py"
    if not rt.is_file():
        print("★ **未量，不是通过**（rc=4）—— 找不到 %s" % rt)
        return 4
    r = subprocess.run([sys.executable, str(rt), "--task", TASK, "--size", "14"],
                       cwd=str(GROUP), capture_output=True, text=True)
    if r.returncode != 0 or not r.stdout.strip():
        print("★ **未量，不是通过**（rc=4）—— 路由跑不动：rc=%d" % r.returncode)
        for l in (r.stderr or "").strip().splitlines()[-3:]:
            print("     " + l[:120])
        return 4
    obs = json.loads(r.stdout)["routing_observability"]
    bad, facts = verdict(obs)
    print("扫描面：一道英文软件工程题｜合格候选 %s｜有 domain 信号 %s"
          % (obs.get("eligible_candidates"), obs.get("domain_signal_candidates")))
    print("ranking_driver = **%s**（weight×σ 最大的是 %s）｜shares 之和 %s"
          % (facts.get("driver"), facts.get("top"), facts.get("share_sum")))
    rc_, bl = facts.get("reachable"), facts.get("blind")
    if rc_ is not None:
        print("★★★ 这把尺子**看得见的人**：**%d / %d（%.0f%%）**｜"
              "四项相关信号恒为 0 的 **%d 人**" % (rc_, rc_ + bl, 100.0 * rc_ / max(1, rc_ + bl), bl))
        print("    （成因是卡片写法：自然中文 67 / 自然英文 26 / slug 式 9。"
              "英文题只有英文卡命中，中文题只有中文卡命中，slug 两边都不命中。）")
    z = facts.get("zero_relevance")
    print("★ 四项题目相关信号**全为 0 却入选**的：**%s 人** %s"
          % ("未量" if z is None else len(z), z if z else ""))
    print("  （这一项**只报不拦** —— 名单非空是排序的问题，怎么改是产品决定。）")
    for c in obs.get("ranking_components", []):
        print("   %-20s w=%.2f σ=%.4f w×σ=%.5f %5.1f%%"
              % (c["component"], c["weight"], c["sigma"], c["weight_x_sigma"], 100 * c["share"]))
    if bad:
        print("\n✗ **披露与它自己的数据打架**：")
        for b in bad:
            print("     " + b)
        return 1
    print("\n✓ `ranking_driver` 是**现算**的，且与 `ranking_components` 自洽。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
