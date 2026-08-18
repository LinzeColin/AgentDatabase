#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**同一件事用中文问和用英文问，路由判成同一个域吗？**

## 为什么这道判据非有不可

`domain_match` 是**决定谁进候选池**的那一项，不是排序的一项。实测（2026-08-18，
`route_team_moe.score_candidate`，strategy=B，accept_threshold 0.17）：

    英文软件题：合格 91 人 —— 其中 **83 人**是靠 `domain_match` 抬过 0.17 的
                                  task_similarity 只抬了 **3** 人、scenario 1 人、capability **0** 人
    中文同一题：合格 58 人 —— domain_match 34、packet_similarity 24

⇒ **四项文本相关分几乎不参与「谁能进池子」**，进池子的事实上由 `infer_domains()` 一个函数定。
  那它把同一件事判错域，后面所有分数都是在错的池子里排序 —— **而没有任何判据在看它。**

## 与已有两件的分工 —— **本件不是第二把尺子**

`tests/test_domain_classifier_language.py` 与 `tests/test_generic_verbs_do_not_claim_a_domain.py`
早就在管这个函数，而且管得很细（`ci` 不许在 "de**ci**de" 里发火；`设计`/`design`/`仓库`
三个词已逐个处置）。**它们断的都是「这道题的正确域是 X」——绝对标准，要人一题一题定。**

本件断的是**关系**：同一内容的两个语言版本必须落进同一组域。不需要标准答案，
所以能覆盖前两件写不到的题。★ 下面 `诊断`/`评审` 两条**不是新缺陷类**，
是 `设计`/`design` 那一类的**第 3、第 4 个实例** —— 那份测试文件里写着
「只降这两个，且都是**实测误发过的**；不凭感觉扩名单」，本件供的正是那个「实测」。
[[i-built-a-second-ruler-while-the-authoritative-one-sat-in-scripts]]

## 它查的是**关系**，不是绝对标准

夹具里的题是**我写的**（[[fixtures-are-clean-because-i-wrote-them]]），所以本件
**不敢**断言「这道题的正确域是 X」—— 那要人来定。它只断言一件不需要标准答案的事：

> **同一段内容的中译本与英文本，必须落进同一组域。**

谁对谁错都行，但**不能因为换了语言就换域**。这条关系断言不受「题是我编的」影响。

## ★★★ 共用零件的防线：非退化负对照

本件调用的 `infer_domains` **正是被判对象**（[[a-gate-must-not-share-a-part-with-what-it-guards]]）。
一个恒返回 `[]`（或恒返回同一个域）的坏实现会让**平价率满分**——违规与合规映射到同一读数。
所以下限守卫是硬的：

    非退化门：必须有 ≥3 对**两侧都**推断出非 `general-decision` 的域，且全库
              推断出的不同域 ≥3 种。达不到 ⇒ **rc=4 未量，不是通过。**

## 它**不是**一道会变红挡人的门

首跑就是 **3/6 不平价**（见下）。一道从建成起就红、且要改代码才能变绿的门不是信号
（[[a-red-that-can-never-turn-green-is-not-a-signal]]）。所以本件是**回归地板**：

    rc=0  平价数 ≥ 基线（默认 3）
    rc=1  平价数 **掉到基线以下** —— 这才是回归
    rc=4  非退化门没过 / 装不进 compile_task_graph（未量）

基线用 `--baseline N` 覆盖。**修好一对就把基线抬一档**，否则修了也没锁住。

## 首跑实测（2026-08-18，基线由此而来）

| 同一内容 | 英文 → | 中文 → | |
|---|---|---|:--:|
| 遗留微服务代码库的测试与重构 | `software-ai,operations-product` | `software-ai` | ✗ |
| 诊断分布式系统线上故障并写复盘 | **`general-decision`**（一个信号都不命中） | **`healthcare`** | ✗ |
| 40 公顷再生农场轮作 | `agriculture` | `agriculture` | ✓ |
| 与难缠供应商谈供货合同 | `legal-policy` | `legal-policy` | ✓ |
| 医院灭菌流程安全论证评审 | `healthcare` | `healthcare,operations-product,software-ai` | ✗ |
| 小众 B2B 产品上市方案 | `operations-product` | `operations-product` | ✓ |

**两侧各有一种错法，方向相反：**

* **中文过火** —— `诊断` 是 `healthcare` 的**裸关键词**，于是「诊断分布式系统的线上故障」
  整题被判成医疗；`评审` 是 `software-ai` 的裸关键词，于是「评审医院灭菌流程」也带上软件。
  这与文件里**已经写明**的 `设计`/`design` 是**同一类缺陷**，而 `WEAK_SIGNALS`
  这个装置就在 `compile_task_graph.py` 里 —— 这两个词只是没进去。
* **英文欠火** —— `Diagnose a production outage in a distributed system and write the
  postmortem` **一个信号都不命中**，退回 `general-decision`。

★ **本件只报，不改词表。** 往 `WEAK_SIGNALS` 里加词会改变**每一道真实任务**选出的人，
  属「门、席位一概不动」的范围，要 Owner 定（Task #129 选项 E）。

用法：

    python3 check_domain_inference_language_parity.py            # 报平价数
    python3 check_domain_inference_language_parity.py --verbose  # 连命中的信号一起印
    python3 check_domain_inference_language_parity.py --self-test
"""
from __future__ import annotations

import argparse
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent

# ★ 中文一列是英文一列的**直译**，内容相同。判的是「换语言会不会换域」，
#   不判「这道题的正确域是什么」——后者要人定，本件不碰。
PAIRS: tuple[tuple[str, str], ...] = (
    ("Design a test strategy and refactoring plan for a legacy microservice codebase",
     "为一个遗留微服务代码库设计测试策略与重构方案"),
    ("Diagnose a production outage in a distributed system and write the postmortem",
     "诊断分布式系统的线上故障并写复盘报告"),
    ("Plan a crop rotation for a 40-hectare regenerative farm",
     "为一个 40 公顷的再生农场规划轮作"),
    ("Negotiate a supply contract with a difficult vendor",
     "与一个难缠的供应商谈供货合同"),
    ("Review the safety case for a new hospital sterilization protocol",
     "评审一份新的医院灭菌流程的安全论证"),
    ("Draft a go-to-market plan for a niche B2B product",
     "为一个小众 B2B 产品起草上市方案"),
)

BASELINE = 3          # 2026-08-18 实测：6 对里 3 对平价
MIN_BOTH_SIDED = 3    # 非退化门①：两侧都推出真域的对数
MIN_DISTINCT = 3      # 非退化门②：全库推断出的不同域种数


def _load():
    """→ `(infer_domains, DOMAIN_SIGNALS, _signal_hits)`，装不进就 `None`。"""
    sys.path.insert(0, str(HERE))
    try:
        from compile_task_graph import (  # noqa: PLC0415
            DOMAIN_SIGNALS, _signal_hits, infer_domains)
    except Exception:                      # noqa: BLE001 —— 装不进 ⇒ 未量，不是通过
        return None
    return infer_domains, DOMAIN_SIGNALS, _signal_hits


def measure(infer, pairs=PAIRS) -> dict:
    rows, both_sided, seen = [], 0, set()
    for en, zh in pairs:
        de, dz = list(infer(en)), list(infer(zh))
        same = set(de) == set(dz)
        real_en = [d for d in de if d != "general-decision"]
        real_zh = [d for d in dz if d != "general-decision"]
        if real_en and real_zh:
            both_sided += 1
        seen.update(de)
        seen.update(dz)
        rows.append({"en": en, "zh": zh, "domains_en": de, "domains_zh": dz, "same": same})
    return {"rows": rows,
            "parity": sum(1 for r in rows if r["same"]),
            "total": len(rows),
            "both_sided": both_sided,
            "distinct_domains": len(seen)}


def divergence_leads(infer, signals, hits) -> list[tuple]:
    """**线索，不是判定**：只看**平价失败**的那几对，列出「只在一侧出现的域」是被哪些词拉进来的。

    ★ 第一版的判法是「某域被唯一一个信号独自拉进来」——**两头都错**：
      8 条线索里 7 条是 `crop`／`农场`／`contract`／`hospital`／`product` 这类
      **本来就该命中的正经关键词**，真正要看的 `诊断` 埋在里面
      （[[a-signal-that-both-overfires-and-underfires]]）。
      改成 key 在**平价失败**上——那正是本件量的东西，不是我对某个词的看法。
    """
    out = []
    for en, zh in PAIRS:
        de, dz = set(infer(en)), set(infer(zh))
        if de == dz:
            continue
        for task, only in ((zh, dz - de), (en, de - dz)):
            low = task.casefold()
            for dom in sorted(only):
                if dom == "general-decision":
                    out.append((task, dom, "（一个信号都不命中，退回兜底）"))
                    continue
                fired = [s for s in signals.get(dom, ()) if hits(s, low)]
                out.append((task, dom, "、".join(fired) or "（查不到命中词）"))
    return out


def self_test() -> int:
    ok = True

    def chk(name, cond):
        nonlocal ok
        ok = ok and bool(cond)
        print("  %s %s" % ("✓" if cond else "**✗**", name))

    print("自测：")
    # ① 正对照：真实实现下，平价数落在 [0, 6]，且非退化门过得了
    loaded = _load()
    chk("① compile_task_graph 装得进（装不进本件只能判未量）", loaded is not None)
    if loaded:
        infer, sigs, hits = loaded
        m = measure(infer)
        chk("② 平价数在 0..6 之间", 0 <= m["parity"] <= m["total"])
        chk("③ 非退化门①：两侧都推出真域的 ≥%d 对（实得 %d）"
            % (MIN_BOTH_SIDED, m["both_sided"]), m["both_sided"] >= MIN_BOTH_SIDED)
        chk("④ 非退化门②：不同域 ≥%d 种（实得 %d）"
            % (MIN_DISTINCT, m["distinct_domains"]), m["distinct_domains"] >= MIN_DISTINCT)
        chk("⑤ 农业那一对确实平价（**首跑锚点**，它变了说明词表动过）",
            any(r["same"] and r["domains_en"] == ["agriculture"] for r in m["rows"]))

    # ② ★★★ 负对照：**恒返回 [] 的坏实现平价率满分** —— 非退化门必须把它打掉
    degenerate = lambda _t: []                                   # noqa: E731
    md = measure(degenerate)
    chk("⑥ 坏实现（恒空）平价数确实满分 —— 说明单看平价数会被骗", md["parity"] == md["total"])
    chk("⑦ 而非退化门①拦住了它（两侧都推出真域 0 对）", md["both_sided"] == 0)

    # ③ 负对照：恒返回同一个域的坏实现，也满分，也必须被打掉
    onedom = lambda _t: ["healthcare"]                           # noqa: E731
    m1 = measure(onedom)
    chk("⑧ 坏实现（恒 healthcare）平价数也满分", m1["parity"] == m1["total"])
    chk("⑨ 而非退化门②拦住了它（不同域仅 %d 种）" % m1["distinct_domains"],
        m1["distinct_domains"] < MIN_DISTINCT)

    # ④ 正对照：一个「换语言也不换域」的完美实现要判平价满分且非退化门全过
    perfect = lambda t: ["agriculture"] if "farm" in t or "农场" in t else (  # noqa: E731
        ["healthcare"] if "hospital" in t or "医院" in t else ["legal-policy"])
    mp = measure(perfect)
    chk("⑩ 完美实现平价满分", mp["parity"] == mp["total"])
    chk("⑪ 且非退化门全过（真域 %d 对 / %d 种）" % (mp["both_sided"], mp["distinct_domains"]),
        mp["both_sided"] >= MIN_BOTH_SIDED and mp["distinct_domains"] >= MIN_DISTINCT)

    print("自测：%s" % ("**全过**" if ok else "**有失败**"))
    return 0 if ok else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--baseline", type=int, default=BASELINE,
                    help="回归地板：平价数掉到它以下才判红（默认 %d）" % BASELINE)
    ap.add_argument("--verbose", action="store_true", help="连命中的信号词一起印")
    ap.add_argument("--self-test", "--selftest", dest="selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return self_test()

    loaded = _load()
    if loaded is None:
        print("★ **未量，不是通过**（rc=4）—— 装不进 `compile_task_graph`")
        return 4
    infer, sigs, hits = loaded
    m = measure(infer)

    print("# 域推断的中英平价（**同一内容、两种语言，域必须一样**）\n")
    print("| 同一内容 | 英文 → | 中文 → | |")
    print("|---|---|---|:--:|")
    for r in m["rows"]:
        print("| %s | `%s` | `%s` | %s |"
              % (r["zh"][:20],
                 ",".join(r["domains_en"]) or "（空）",
                 ",".join(r["domains_zh"]) or "（空）",
                 "✓" if r["same"] else "**✗**"))
    print("\n**平价 %d/%d**｜两侧都推出真域 %d 对｜不同域 %d 种"
          % (m["parity"], m["total"], m["both_sided"], m["distinct_domains"]))

    if m["both_sided"] < MIN_BOTH_SIDED or m["distinct_domains"] < MIN_DISTINCT:
        print("\n★ **未量，不是通过**（rc=4）—— 非退化门没过："
              "两侧真域 %d 对（要 ≥%d）、不同域 %d 种（要 ≥%d）。"
              % (m["both_sided"], MIN_BOTH_SIDED, m["distinct_domains"], MIN_DISTINCT))
        print("   ★ 这一档是防**共用零件**的：`infer_domains` 若退化成恒空/恒单域，"
              "平价率会满分，而那正是最坏的坏。")
        return 4

    leads = divergence_leads(infer, sigs, hits)
    if leads:
        print("\n★ **线索（不是判定）**：平价失败的那几对里，**只在一侧出现的域**是被这些词拉进来的 ——")
        for task, dom, sig in leads:
            print("    「%s」 多出 `%s`  ← %s" % (task[:30], dom, sig))
        print("   「这个词该不该单独拉一个域」由人判，本件不据此判红。"
              "已知同类先例：`设计`/`design` 已因同样理由进了 `WEAK_SIGNALS`。")

    if a.verbose:
        print("\n逐题命中的信号：")
        for en, zh in PAIRS:
            for task in (en, zh):
                low = task.casefold()
                fired = [(d, [s for s in ss if hits(s, low)])
                         for d, ss in sigs.items()]
                fired = [(d, f) for d, f in fired if f]
                print("  「%s」" % task[:44])
                for d, f in fired:
                    print("      %-20s ← %s" % (d, "、".join(f)))

    if m["parity"] < a.baseline:
        print("\n★ **回归**（rc=1）—— 平价 %d < 基线 %d。**换语言换了域的对数变多了。**"
              % (m["parity"], a.baseline))
        return 1
    if m["parity"] > a.baseline:
        print("\n★ 平价 %d **高于**基线 %d —— 修好了就把 `BASELINE` 抬到 %d，否则锁不住。"
              % (m["parity"], a.baseline, m["parity"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
