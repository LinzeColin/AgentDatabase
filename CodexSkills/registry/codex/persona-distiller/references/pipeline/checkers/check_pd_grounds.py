#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""公有领域依据核验 —— **把「它是公有领域」拆成「凭哪一条」并要求证据**。

## 为什么有这道判据

#119 DeBakey 的探测暴露了一处我自己会犯的混淆：

> 三卷 GPO 政府出版物**确实是公有领域**，但依据是
> 「1978 年前出版、无版权标记」（1909 年法），**不是 §105 联邦职务作品**
> ——作者脚注实录 `Formerly Colonel, MC, AUS`，写作时他已是平民教授。

两者结论相同（都是 PD），**依据完全不同，射程也完全不同**：

- §105 的射程是「这个人在联邦任内写的东西」——**可以外推到他同期的其他作品**
- 1909 年法的射程是「这一份印本上没有版权标记」——**一份一份地判，不可外推**

把后者当成前者，就会得出「他有 §105 的口子、可以按 deep 排期」这种错结论。
**实际口径是 0。**

## 它检查什么

调用方给一张**依据表**，每条主张一个 PD 依据，本件核：

1. **依据必须具名**——`kind` 只许四条之一，写「公有领域」而不写凭哪一条 → 报出
2. **每条依据必须带证据**——`evidence` 为空 → 报出（不写证据等于没有证据）
3. **§105 必须有在职证据**——证据里出现 `formerly` / 前任 / 卸任 / 退役 → **报出**
   （这正是 DeBakey 那三卷的实况）
4. **§105 不许拿「政府出版/GPO」当依据**——那是 1909 年法那条的证据，不是 §105 的
5. **1909 年法那条必须报核验强度**——扫本 OCR 是强，HTML 转录是弱，未标注 → 报出
6. **1929 年前出版那条，年份必须真的 < 1929**
7. **机构署名不许标成个人一手**——`byline=institution` 而 `tier` 是 P1 → 报出，
   归到「归属不成立」，不要混进可得性统计

## 它不做什么

- **不判某份东西是不是公有领域。** 那是调用方（和法律）的判断。
  本件只核**主张的形式是否完整、证据是否与所主张的依据同类**。
- **不上网核验。** 它读不到原文，不知道扉页背面有没有 ©。
  所以第 5 条只能要求**如实标注核验强度**，不能替你去看。
- **不判可得性。** 「取不到」与「取到了但不是 PD」是两回事，别混。
"""
import argparse
import json
import pathlib
import re
import sys

THIS_YEAR = 2026   # ★ 常量，不用 date.today()：判据的结论要可复现，不许随日子变

KINDS = {
    "sec105": "17 U.S.C. §105 联邦职务作品",
    "notice1909": "1909 年法：1978 年前出版且无版权标记",
    "pre1929": "1929 年前出版，版权已过期",
    "congressional": "国会记录/听证，GPO 印无标记",
    "unpublished_303": "17 U.S.C. §303 未刊作品：卒年 +70，且 2003-01-01 下限已过",
}

# ★ 见到这些词，「在职」这个前提就不成立 —— DeBakey 三卷的实况
EX_OFFICE = re.compile(r"formerly|ex-|retired|前任|卸任|退役|离任|脱离军职|已是平民", re.I)
# ★ 「政府出版/GPO」是 1909 那条的证据，拿它当 §105 的依据是本判据的头号目标
GPO_ONLY = re.compile(r"GPO|Government Printing|政府出版|官方出版|superintendent of documents", re.I)
# §105 真正需要的：写明当时在任该联邦职务
IN_OFFICE = re.compile(r"in office|serving as|现任|时任|任内|在职|chief,|director,|administrator", re.I)

# ★ §303 那条：1978 年前完成且从未出版的，版权到卒年+70 止，但下限是 2003-01-01
S303_FLOOR = 2003
UNPUBLISHED = re.compile(r"unpublished|manuscript|\bmss?\b|未刊|手稿|日记|信札|档案", re.I)

STRENGTH = {"scan-ocr", "page-image", "html-transcript", "metadata-only"}
WEAK = {"html-transcript", "metadata-only"}


def check(claims: list) -> list:
    """→ 问题列表；空表示每条主张的形式都完整。**不代表它们真是公有领域。**"""
    bad = []
    for i, c in enumerate(claims):
        w = f"第 {i+1} 条（{c.get('work') or '无题名'}）"
        kind = c.get("kind")
        if kind not in KINDS:
            bad.append(f"{w}：依据 `{kind}` 不具名——只许 {sorted(KINDS)}；"
                       f"**只写「公有领域」不算依据**")
            continue
        ev = str(c.get("evidence") or "").strip()
        if not ev:
            bad.append(f"{w}：{kind} **没有证据**——不写证据等于没有证据")
            continue

        if kind == "sec105":
            if EX_OFFICE.search(ev):
                bad.append(f"{w}：**§105 不成立**——证据里出现离任表述"
                           f"（`{EX_OFFICE.search(ev).group(0)}`）。"
                           f"作品写于任外则不是职务作品；它可能仍是 PD，但依据是别条")
            elif not IN_OFFICE.search(ev):
                bad.append(f"{w}：§105 的证据里**没有在职表述**"
                           f"（署名/脚注/前言须写明当时任该联邦职务且在职务范围内）")
            if GPO_ONLY.search(ev) and not IN_OFFICE.search(ev):
                bad.append(f"{w}：★ **拿「政府出版/GPO」当 §105 的依据**——"
                           f"那是 1909 年法那条的证据。两者结论都是 PD，"
                           f"但 §105 可外推到同期作品，1909 那条只判这一份印本")

        if kind == "notice1909":
            s = c.get("verify_strength")
            if s not in STRENGTH:
                bad.append(f"{w}：1909 那条**未标核验强度**（须为 {sorted(STRENGTH)}）"
                           f"——「某站 HTML 里没看到 ©」与「扫本 OCR grep 得 0 命中」不是一回事")
            elif s in WEAK and not c.get("weak_acknowledged"):
                bad.append(f"{w}：核验强度是 `{s}`（弱），须显式标 `weak_acknowledged`"
                           f"——扉页背面是版权标记的常规位置，转录站可能根本没转")
            y = c.get("year")
            if isinstance(y, int) and y >= 1978:
                bad.append(f"{w}：1909 年法只管 1978 年前出版的，而 year={y}")

        if kind == "pre1929":
            y = c.get("year")
            if not isinstance(y, int):
                bad.append(f"{w}：pre1929 必须给出版年份")
            elif y >= 1929:
                bad.append(f"{w}：**year={y} 不早于 1929**")

        if kind == "unpublished_303":
            dy = c.get("death_year")
            if not isinstance(dy, int):
                bad.append(f"{w}：§303 那条**必须给卒年**——它算的是卒年+70，没有卒年就没有期限")
            elif dy + 70 >= THIS_YEAR:
                bad.append(f"{w}：**仍在保护期**——卒年 {dy} +70 = {dy+70}，未到 {THIS_YEAR}")
            elif THIS_YEAR < S303_FLOOR:
                bad.append(f"{w}：§303 的 {S303_FLOOR}-01-01 下限尚未到")
            if not UNPUBLISHED.search(ev):
                bad.append(f"{w}：§303 只管**从未出版**的——证据里没有未刊/手稿/档案的表述。"
                           f"若它其实出版过，依据应是 1909 年法或 1929 年前那条")

        if c.get("byline") == "institution" and c.get("tier") in ("P1", "P2"):
            bad.append(f"{w}：★ **机构署名却标成个人一手（{c['tier']}）**——"
                       f"它是联邦出版物、可能是 PD，但不是他的散文。"
                       f"归「归属不成立」，不要混进可得性统计")
    return bad


def summarize(claims: list) -> dict:
    """→ 分依据计数，并**单列 §105 且本人署名的那一档**（排期口径就看这个数）。"""
    by, sec105_own, words = {}, 0, 0
    for c in claims:
        by[c.get("kind")] = by.get(c.get("kind"), 0) + 1
        if c.get("kind") == "sec105" and c.get("byline") != "institution":
            sec105_own += 1
            words += int(c.get("words") or 0)
    return {"分依据": by, "**§105 且本人署名**": sec105_own, "其字数": words,
            "总条数": len(claims)}


def coverage(claims: list, source_ids) -> dict:
    """★ **分母**：台账里这些来源，有几份写了公有领域依据？**按标识符比集合，不比份数。**

    第一版拿「依据条数 vs 工作区目录数」相减，真数据一跑报出 **覆盖率 104%**
    ——分子来自台账 95 条、分母来自工作区 89 个目录，**两组数不在同一个标识符空间**。
    这是我的默认失误形态：拿到两组数就相减，没先问它们是不是同一个空间里的。

    所以本函数**只接受标识符集合**，并且：
    - 少的那些**逐个列出来**（不是只报一个差值）
    - **主张里出现台账没有的 id → 单独报**，因为那说明两边根本不是一套东西
    - 覆盖率永远 ≤100%（分子是交集，不是主张条数）
    """
    src = set(source_ids)
    claimed = {c.get("source_id") for c in claims if c.get("kind") in KINDS}
    claimed.discard(None)
    hit, missing, alien = claimed & src, src - claimed, claimed - src
    out = {"台账来源份数": len(src), "写了依据的": len(hit),
           "**没写依据的**": len(missing),
           "覆盖率": f"{len(hit)/len(src):.0%}" if src else "**无来源，分母未知**"}
    if missing:
        out["没写依据的是"] = sorted(missing)[:10]
    if alien:
        out["★★ 主张指向台账里没有的来源"] = (
            f"{len(alien)} 个 → {sorted(alien)[:6]}"
            f"　**这说明两边不是同一套标识符，覆盖率不可信**")
    return out


# ══════════════════ 自测 ══════════════════

def selftest() -> int:
    fails = []

    def chk(label, cond):
        print(("  ✓ " if cond else "  ✗ ") + label)
        if not cond:
            fails.append(label)

    print("── 正向：一条形式完整的 §105 主张不报 ──")
    ok105 = {"work": "OTSG 通报", "kind": "sec105", "year": 1944, "tier": "P1",
             "evidence": "前言实录 Chief, General Surgery Branch, Office of The Surgeon General"}
    chk("在职表述齐 → 不报", not check([ok105]))

    print("── ★★ 反向对照 ①：DeBakey 实例——署名写 Formerly，§105 不成立 ──")
    p = check([dict(ok105, evidence="脚注：Professor, Baylor. Formerly Colonel, MC, AUS.")])
    chk("报出「§105 不成立」", any("§105 不成立" in x for x in p))

    print("── ★★ 反向对照 ②：拿「GPO 出版」当 §105 的依据 → 报出 ──")
    p = check([dict(ok105, evidence="由 GPO 印行，正文无版权标记")])
    chk("报出「拿政府出版当 §105」", any("当 §105 的依据" in x for x in p))
    chk("同时报出「没有在职表述」", any("没有在职表述" in x for x in p))

    print("── ★ 反向对照 ③：只写「公有领域」不写凭哪一条 → 报出 ──")
    chk("kind=public-domain 报出",
        any("不具名" in x for x in check([{"work": "x", "kind": "public-domain",
                                          "evidence": "馆方标 PD"}])))

    print("── ★ 反向对照 ④：有依据但没有证据 → 报出 ──")
    chk("evidence 为空 → 报出",
        any("没有证据" in x for x in check([{"work": "x", "kind": "pre1929", "evidence": " "}])))

    print("── ★ 反向对照 ⑤：1909 那条不标核验强度 / 标了弱但不承认 ──")
    n09 = {"work": "Cold Injury", "kind": "notice1909", "year": 1958, "evidence": "正文无 ©"}
    chk("未标强度 → 报出", any("未标核验强度" in x for x in check([n09])))
    chk("弱强度未承认 → 报出",
        any("须显式标" in x for x in check([dict(n09, verify_strength="html-transcript")])))
    chk("弱强度已承认 → **不报**",
        not check([dict(n09, verify_strength="html-transcript", weak_acknowledged=True)]))
    chk("扫本 OCR → 不报", not check([dict(n09, verify_strength="scan-ocr")]))

    print("── 反向对照 ⑥：pre1929 的年份必须真的早于 1929 ──")
    chk("year=1931 → 报出",
        any("不早于 1929" in x for x in check([{"work": "x", "kind": "pre1929",
                                               "year": 1931, "evidence": "版权页"}])))

    print("── ★★ 反向对照 ⑦：机构署名却标成个人一手 → 报出（归属不成立）──")
    p = check([{"work": "总统委员会报告", "kind": "congressional", "byline": "institution",
                "tier": "P1", "evidence": "GPO 印，28 名委员集体署名"}])
    chk("报出「机构署名却标成个人一手」", any("机构署名" in x for x in p))
    chk("同一条改标 P2 仍报（P1/P2 都算一手）",
        any("机构署名" in x for x in check([{"work": "x", "kind": "congressional",
                                            "byline": "institution", "tier": "P2",
                                            "evidence": "集体署名"}])))
    chk("同一条改标 S1 → **不报**",
        not check([{"work": "x", "kind": "congressional", "byline": "institution",
                    "tier": "S1", "evidence": "集体署名"}]))

    print("── ★ 反向对照 ⑧：排期口径只数「§105 且本人署名」的那一档 ──")
    s = summarize([ok105,
                   {"kind": "sec105", "byline": "institution", "words": 9999},
                   {"kind": "notice1909", "words": 5000}])
    chk(f"三条里 §105 本人署名 {s['**§105 且本人署名**']} 条（机构署名那条不计）",
        s["**§105 且本人署名**"] == 1)

    print("── ★★ 反向对照 ⑨：§303 未刊作品那条 ──")
    u = {"work": "日记 mss962", "kind": "unpublished_303", "death_year": 1910,
         "evidence": "LoC 手稿部 mss962，从未出版"}
    chk("卒 1910 + 手稿表述 → 不报", not check([u]))
    chk("**没给卒年 → 报出**",
        any("必须给卒年" in x for x in check([{k: v for k, v in u.items() if k != "death_year"}])))
    chk("卒年 1990（+70=2060）→ 报「仍在保护期」",
        any("仍在保护期" in x for x in check([dict(u, death_year=1990)])))
    chk("证据里没有未刊/手稿表述 → 报出",
        any("从未出版" in x for x in check([dict(u, evidence="1902 年由 Longmans 出版")])))

    print("── ★★ 反向对照 ⑩：分母按标识符比集合，且逐个列出缺的 ──")
    ids = {f"s{i}" for i in range(95)}
    cov = coverage([dict(u, source_id=f"s{i}") for i in range(45)], ids)
    chk(f"95 份里写了依据 {cov['写了依据的']}、**没写 {cov['**没写依据的**']}**、"
        f"覆盖 {cov['覆盖率']}",
        cov["**没写依据的**"] == 50 and cov["覆盖率"] == "47%")
    chk("缺的**逐个列出来**，不是只报差值", len(cov.get("没写依据的是", [])) == 10)
    chk("一份来源都没有时不除零", "无来源" in coverage([], set())["覆盖率"])

    print("── ★★★ 反向对照 ⑪：真数据上出过的 104%——两边不是同一套标识符 ──")
    cov = coverage([dict(u, source_id=f"x{i}") for i in range(95)], {f"s{i}" for i in range(89)})
    chk(f"覆盖率 {cov['覆盖率']}，**不可能超过 100%**", cov["覆盖率"] == "0%")
    chk("并且**明说主张指向台账里没有的来源**", "★★ 主张指向台账里没有的来源" in cov)

    print("── ★ 反向对照 ⑪：空表不报错，也不许被读成「通过」──")
    chk("空表返回空问题列表", check([]) == [])
    chk("而 summarize 明说总条数 0", summarize([])["总条数"] == 0)

    print(f"\n{'✓ 自测全过' if not fails else f'✗ **{len(fails)} 项未过**'}")
    return 0 if not fails else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--claims", help="依据表 JSON 数组")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return selftest()
    if not a.claims:
        print("✗ **什么都没核**——既没给 --claims 也没给 --self-test。这不是通过。")
        return 2

    claims = json.loads(pathlib.Path(a.claims).read_text(encoding="utf-8"))
    problems = check(claims)
    s = summarize(claims)
    print(f"核过 {s['总条数']} 条主张")
    for k, v in s.items():
        print(f"  {k}: {v}")
    if problems:
        print(f"\n✗ **{len(problems)} 处**：")
        for p in problems:
            print(f"  · {p}")
        return 1
    print("\n✓ 每条主张的形式都完整。"
          "★ 这**不代表**它们真是公有领域——本件核的是主张形式，不是法律结论。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
