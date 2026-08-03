#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**说「我量过」的地方，有没有量出来的数。**

## 为什么有这道判据

席 E 在八个人物身上反复扣同一处分。原话（Fleming #111 第 3 轮 q-30）：

> 「因为我量过，不是因为不喜欢」这句最承重，**全文却没有任何测得的数**。

这是一类可数的缺陷，不是文风问题：
**答案借用了实测的权威，却没有交出实测的内容。**
读者拿不到数，就无从判断这个「量过」是真做过还是修辞。

评委每人只能点出一两处（他们要在 32 题里通读），
**判据能把范围数出来**——这是第四次把席位批评落成判据。

## 判据

在**同一段**里：出现实测声明（`我量过` / `我数过` / `我算过` / `实测` / `测得` …），
就必须出现一个**可读的数**（阿拉伯数字，或带量词的中文数字）。
两者都在同段 → 放行；只有声明没有数 → 报出。

## ★ 不许把「诚实的弃权」也报出来

Fleming 第 3 轮里有这么一句：

> 「那两篇的数值**我没逐个核过，不核就不报数**。」

席 E 专门表扬了它（「自缚的规矩」）。
**这一句里有实测词、没有数，但它恰恰是对的**——
它声明的是「我没量」，不是「我量过」。

判据若把它一起报出来，等于把产物往**不诚实的方向**推：
作者为了让判据变绿，会去掉这句弃权、或者随便补一个数。
**反向对照 ④⑤ 专守这一条。**

## 它判不了什么

- **不查那个数对不对**。数对不对是 `check_self_reported_counts` 与人工的活。
  这一件只问「有没有」。
- 段落之外的数不算。读者的检索单位是段落——
  数在三段之外，等于没给。
"""
import argparse
import json
import pathlib
import re
import sys

# 实测声明：借用了「我做过测量／计数」这一权威的说法
CLAIM = re.compile(
    r"我(?:亲自)?(?:量|数|测|算|核|统计|比较|对照)过"
    r"|我(?:量|数|测|算)了"
    r"|实测"
    r"|测得"
    r"|量出"
    r"|数出"
    r"|我(?:的)?(?:测量|统计|计数)(?:结果|显示|表明)")

# **弃权式**：声明的是「我没量」。有实测词、没有数，但它是对的。
ABSTAIN = re.compile(
    r"没(?:有)?(?:逐个|逐条|逐份|一一)?(?:核|量|数|测|算)过"
    r"|未(?:曾)?(?:核|量|数|测|算)过"
    r"|不核(?:就)?不报数"
    r"|没核(?:就)?不报数"
    r"|(?:我)?拿不出(?:这个)?数"
    r"|(?:这个)?数(?:我)?给不出"
    r"|无从(?:核|量|数)")

# 可读的数：阿拉伯数字，或带量词的中文数字
NUMBER = re.compile(
    r"\d"
    r"|[一二三四五六七八九十百千万零两]+\s*"
    r"(?:次|条|份|页|个|人|年|月|日|篇|倍|成|分|处|例|件|种|张|台|米|克|升|度|％|%)")


def paragraphs(text: str):
    """按空行切段——读者的实际检索单位。"""
    for para in re.split(r"\n\s*\n", text or ""):
        if para.strip():
            yield para


def scan(unit_id: str, text: str, acc):
    for para in paragraphs(text):
        # ★ 弃权要**独立成立**，不能挂在「先匹配到实测声明」之下。
        #   自测反向对照 ④ 当场抓出来的：`我没逐个核过` 里的「我」后面跟的是「没」，
        #   `CLAIM` 本来就不匹配，于是弃权一次都数不到——
        #   报告会显示「诚实弃权 0 处」，**而产物里明明有一处，且是席 E 专门表扬的那一处。**
        if ABSTAIN.search(para):
            acc["abstain"] += 1          # 诚实的弃权，单独计数，**不算问题**
            continue
        m = CLAIM.search(para)
        if not m:
            continue
        acc["total"] += 1
        if NUMBER.search(para):
            acc["ok"] += 1
        else:
            acc["bad"].append((unit_id, m.group(0), para.strip()[:110]))


# ══════════════════ 自测 ══════════════════

def selftest() -> int:
    fails = []

    def chk(label, cond):
        print(("  ✓ " if cond else "  ✗ ") + label)
        if not cond:
            fails.append(label)

    def run(text):
        acc = {"total": 0, "ok": 0, "bad": [], "abstain": 0}
        scan("x", text, acc)
        return acc

    print("── 正向：Fleming #111 q-30 的真实形状 ──")
    a = run("**是实证不是意见之争。**\n\n"
            "我反对往伤口里灌防腐剂，**因为我量过**，不是因为不喜欢。")
    chk("有「我量过」、段里没有数 → 报出", len(a["bad"]) == 1 and a["total"] == 1)

    print("── 反向对照 ①：给了数的不许报 ──")
    b = run("我反对往伤口里灌防腐剂，**因为我量过**——"
            "石炭酸在伤口渗出液里 20 分钟后杀菌力降到原来的三成。")
    chk("同段里有「20 分钟」「三成」→ 放行", not b["bad"] and b["ok"] == 1)

    print("── 反向对照 ②：光有数、没有实测声明 → 不计入 ──")
    c = run("那篇论文是 1929 年发的，卷期是 10(3):226-236。")
    chk("没有实测声明 → total=0，不报", c["total"] == 0 and not c["bad"])

    print("── ★ 反向对照 ③：**数在另一段不算**（读者按段检索）──")
    d = run("**因为我量过。**\n\n另起一段才写：降到原来的三成。")
    chk("数落在另一段 → 仍报出", len(d["bad"]) == 1)

    print("── ★★ 反向对照 ④：**诚实的弃权不许报**（席 E 专门表扬过的那一句）──")
    # 判据若把它报出来，作者为了变绿会去掉弃权、或随便补个数——**把产物推向不诚实。**
    e = run("那两篇的数值**我没逐个核过，不核就不报数**。")
    chk("「没逐个核过、不核就不报数」→ 不报，单独计入弃权",
        not e["bad"] and e["abstain"] == 1 and e["total"] == 0)

    print("── ★★ 反向对照 ⑤：弃权的其它说法也要认 ──")
    for s in ("这个数我给不出，手上没有原始记录。",
              "我未曾核过那一批，所以拿不出数。",
              "无从核，我不报。"):
        f = run(s)
        chk(f"「{s[:12]}…」→ 不报", not f["bad"])

    print("── 反向对照 ⑥：一段里既有实测声明又有弃权 → 按弃权算 ──")
    g = run("**我量过一部分**，但**剩下那些我没核过，不核就不报数。**")
    chk("同段兼有 → 归弃权，不报", not g["bad"] and g["abstain"] == 1)

    print("── 反向对照 ⑦：中文数字要带量词才算数 ──")
    h = run("**我量过**，结论很一致。")
    chk("「一致」里的「一」不是数 → 仍报出", len(h["bad"]) == 1)
    i = run("**我量过**，一共三次，结论一致。")
    chk("「三次」带量词 → 放行", not i["bad"])

    print("── 反向对照 ⑧：整篇没有实测声明 → total=0，调用方须报「未检查」──")
    j = run("青霉素的分离纯化是牛津做的，不是我。")
    chk("total=0（不构成通过）", j["total"] == 0)

    print(f"\n{'✓ 自测全过' if not fails else f'✗ **{len(fails)} 项未过**'}")
    return 0 if not fails else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--answers", type=pathlib.Path, nargs="*", default=[],
                    help="候选答案 JSON（id→文本）或盲判载荷（[{case_id,A,B}]）")
    ap.add_argument("--claims", type=pathlib.Path, help="断言层 claims.jsonl")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return selftest()
    if not (a.answers or a.claims):
        ap.error("--answers 或 --claims 至少给一个（除非只跑 --self-test）")

    acc = {"total": 0, "ok": 0, "bad": [], "abstain": 0}

    if a.claims:
        for line in a.claims.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                scan(f"断言/{r['claim_id']}", r.get("claim", ""), acc)

    for path in a.answers:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):                    # 盲判载荷
            for row in data:
                for side in ("A", "B"):
                    if side in row:
                        scan(f"{row.get('case_id', '?')}/{side}", row[side], acc)
        else:
            for k, v in data.items():
                scan(f"答案/{k}", v, acc)

    print(f"实测声明 {acc['total']} 处，同段带数 {acc['ok']} 处，"
          f"**光说不给数 {len(acc['bad'])} 处**；另有诚实弃权 {acc['abstain']} 处（不计问题）")

    if not acc["total"] and not acc["abstain"]:
        print("  ⚠ **一处实测声明都没扫到——本次未检查（不是通过）**")
        return 0

    if acc["bad"]:
        print(f"\n✗ **{len(acc['bad'])} 处借了实测的权威却没交出实测的内容**——"
              "读者拿不到数，就无从判断这个「量过」是真做过还是修辞：")
        for uid, kw, snip in acc["bad"]:
            print(f"    {uid}　「{kw}」\n        {snip}")
        print("\n  **两条出路：把数补上，或者改成弃权式（「没核过，不核就不报数」）。**"
              "\n  后者不会被本判据报出——**弃权是诚实的，不是缺陷。**")
        return 1

    print("  ✓ 每一处实测声明都在同段给了数")
    return 0


if __name__ == "__main__":
    sys.exit(main())
