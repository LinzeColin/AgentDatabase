#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_keywords_dont_pull_unowned_domains.py —— **一个词把「没人拥有的域」拉了进来**

## 它怎么来的（2026-08-17）

一天里在同一个词表上抓到两个真缺陷，两次都是手工发现的：

* `设计`/`design` 是**通用动词**，却是 `creative-design` 的裸关键词 ⇒
  一道零售扩张题里艺术设计师/客户营销师 `domain_match` **1.000**，
  真正对口的创业经营师只有 0.500；
* `仓库` 在词表里指 **git repo**，而中文里它也是 **warehouse** ⇒
  `warehouse-automation-roi`（相关族里**没有软件开发师**）被判成软件题，
  域从 2 变 3、人人被稀释；该题正是基准里最差的几道之一（−11.5%）。

**两次都是我一条条读出来的。** 本件把那个判别式写下来。

## 判别式

基准题自带 ground truth（`relevant` 相关族）。于是：

    题被判出的域 D_i
    该题所有相关族拥有的域并集 OWNED = ∪ CATEGORY_DOMAINS[fam]
    若 D_i ∉ OWNED ⇒ **这个域没有任何相关族拥有它** ⇒ 可疑

`domain_match = |族的域 ∩ 题的域| / |题的域|` —— 多一个没人拥有的域，
**分母变大而分子不变**，所有正确的人一起被稀释。

## ★ 必须用 `infer_domains`，不能用原始 `_signal_hits`

我第一版扫描用的是原始命中，于是把**已经修好的** `设计` 又报了一遍
（它现在是弱信号，命中但不认领域）。**判「有没有病」要看最终判定，
不看中间信号。** [[checker-blindspot-read-as-defect]]

## 已知的、量不出来的一条

`clinical-triage`（相关族：医疗护理师）判出 `['healthcare', 'operations-product']`，
`流程` 多拉了 operations-product ⇒ 医疗护理师从 1.0 掉到 0.5。
**但名册里医疗护理师 0 人**，这题注定命中 0 ——
改不改都量不出来。本件把它印出来但**不当红**：那是名册的洞。
[[a-red-that-can-never-turn-green-is-not-a-signal]]

退出码：0＝没有可疑命中（或只剩量不出来的那类）；1＝有可疑；4＝读不到基准题或分类表（未量）。
"""
import argparse
import importlib.util
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[4]
GROUP_SCRIPTS = REPO / "CodexSkills/registry/codex/persona-distiller-group/scripts"
BENCH = HERE / "measure_routing_discrimination.py"
# 名册里 0 人的族 —— 这些题注定命中 0，可疑与否量不出来，只印不拦。
UNMEASURABLE_NOTE = "名册里该族 0 人 ⇒ 这题注定命中 0，改不改都量不出来"


# ★★★ `general-decision` 是**「一个关键词都没撞上」的兜底标记**，
#   不是某个词拉进来的域 —— 它出现代表**无信号**，而路由自己已在披露兜底率。
#   我第一版没排除它，于是把 `supplier-single-source`（兜底题）报成
#   「有词拉进了没人拥有的域」。**缺信号与错信号是两件事，不许混。**
#   [[empty-default-swallows-unknown]]
NO_SIGNAL = "general-decision"


def suspicious(domains, relevant, category_domains):
    """→ 被判出、却**没有任何相关族拥有**的域。纯函数。

    ★ 排除 `general-decision`：它是无信号兜底，不是「某个词拉错了域」。
    """
    owned = set()
    for fam in relevant or []:
        owned |= set(category_domains.get(fam, ()))
    if not owned:
        return []                      # 相关族一个都认不出 ⇒ 判不了，交给调用方记未量
    return [d for d in domains if d not in owned and d != NO_SIGNAL]


def self_test() -> int:
    bad, tot = [], [0]

    def chk(lbl, ok):
        tot[0] += 1
        print(("  ✓ " if ok else "  ✗ ") + lbl)
        if not ok:
            bad.append(lbl)

    CD = {"软件开发师": {"software-ai", "research-education"},
          "建造采购师": {"engineering-industry", "operations-product"}}
    chk("★ 判出的域都被相关族拥有 ⇒ 无可疑",
        suspicious(["software-ai"], ["软件开发师"], CD) == [])
    chk("★★★ **多出一个没人拥有的域 ⇒ 报出来**（`仓库` 那一次的形状）",
        suspicious(["engineering-industry", "software-ai"], ["建造采购师"], CD) == ["software-ai"])
    chk("★★ 相关族认不出（空 owned）⇒ 返回空，交给调用方记未量，不许当成「没问题」",
        suspicious(["software-ai"], ["查无此族"], CD) == [])
    chk("★ 相关族为空同上", suspicious(["software-ai"], [], CD) == [])
    chk("★★ 多个可疑要全部报出",
        suspicious(["a", "b", "software-ai"], ["软件开发师"], CD) == ["a", "b"])
    chk("★★★ **`general-decision` 不算可疑** —— 它是无信号兜底，不是词拉错了域"
        "（第一版没排除，把兜底题 supplier-single-source 报成了缺陷）",
        suspicious(["general-decision"], ["软件开发师"], CD) == [])
    chk("★★ 兜底标记与真可疑同时出现时，只报真可疑",
        suspicious(["general-decision", "healthcare"], ["软件开发师"], CD) == ["healthcare"])
    print("\n自测 %d 项，不符 %d 项" % (tot[0], len(bad)))
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", "--selftest", dest="selftest", action="store_true")
    if ap.parse_args().selftest:
        return self_test()

    if not BENCH.is_file() or not GROUP_SCRIPTS.is_dir():
        print("★ **未量，不是通过**（rc=4）—— 读不到基准题或 group scripts：\n     %s\n     %s"
              % (BENCH, GROUP_SCRIPTS))
        return 4
    sys.path.insert(0, str(GROUP_SCRIPTS))
    try:
        spec = importlib.util.spec_from_file_location("_bench", BENCH)
        bench = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bench)
        # ★ 用最终判定，不用原始命中 —— 第一版用了 `_signal_hits`，把已修好的
        #   `设计` 又报了一遍（它现在是弱信号：命中但不认领域）。
        from compile_task_graph import infer_domains
        from route_team_moe import CATEGORY_DOMAINS
        import json
        idx = json.loads((GROUP_SCRIPTS.parent / "team-index.json")
                         .read_text(encoding="utf-8"))
        staffed = {p.get("registration_category") for p in idx.get("products", [])}
    except Exception as exc:                                   # noqa: BLE001
        print("★ **未量，不是通过**（rc=4）—— 读入失败：%r" % exc)
        return 4

    tasks = getattr(bench, "TASKS", None)
    if not tasks:
        print("★ **未量，不是通过**（rc=4）—— 基准题是空的")
        return 4

    hard, soft, unknown = [], [], []
    for t in tasks:
        rel = t.get("relevant") or []
        sus = suspicious(infer_domains(t["task"]), rel, CATEGORY_DOMAINS)
        if not rel or not any(f in CATEGORY_DOMAINS for f in rel):
            unknown.append(t["id"]); continue
        if not sus:
            continue
        # 相关族在名册里 0 人 ⇒ 量不出来，只印不拦
        (soft if not any(f in staffed for f in rel) else hard).append((t["id"], sus, rel))

    print("扫描面：基准题 **%d** 道｜身份族 %d 个｜名册里有人的族 %d 个"
          % (len(tasks), len(CATEGORY_DOMAINS), len(staffed & set(CATEGORY_DOMAINS))))
    if unknown:
        print("★ **相关族认不出、本次未判**：%d 道（%s）" % (len(unknown), "、".join(unknown[:4])))
    for tid, sus, rel in soft:
        print("  ⚠ %-24s 多拉了 %s ——（%s；相关族 %s）"
              % (tid, "、".join(sus), UNMEASURABLE_NOTE, "、".join(rel)))
    if hard:
        print("\n✗ **有词把「没人拥有的域」拉了进来**：%d 道" % len(hard))
        for tid, sus, rel in hard:
            print("     %-24s 多拉 %-24s 相关族：%s" % (tid, "、".join(sus), "、".join(rel)))
        print("\n  ★ 处置：找出是哪个词（逐词跑 `_signal_hits`），确认它在这 24 道题里"
              "**只服务这一道**、且去掉后真软件/真本域题不受影响，再改。"
              "**没有实测误路由就不要改词表**。")
        return 1
    print("\n✓ 可行动的可疑命中 **0** 道（另有 %d 道属「名册 0 人、量不出来」，只印不拦）"
          % len(soft))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
