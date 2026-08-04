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
6. **「版权已过期」那条，年份必须真的 < `PD_PUBLISHED_BEFORE`**
   （= `THIS_YEAR - 95`；2026 年是 **1931**。★ 原先写死 1929，**两年前就该挪了**）
7. **机构署名不许标成个人一手**——`byline=institution` 而 `tier` 是 **P1 或 P2** → 报出，
   归到「归属不成立」，不要混进可得性统计。
   ★★ **2026-08-05 更正**：本条原先只写「`tier` 是 P1」，**而代码里拦的是 `("P1", "P2")`**。
   我照文档把 Carver 那四份机构署名的公报从 P1 降到 P2，**以为就清了，结果照样报出四条**。
   **文档比代码窄，读文档的人会照着改成一个仍然过不去的值。** 现已对齐到代码。

## ★★ 口径：**五条依据全部是美国法**

`§105` / `§303` 是 17 U.S.C.；`notice1909` 是 1909 年美国版权法的标记要求；
`pre1929`（键名）是美国版权到期——**实际分界随年份滚动**；`congressional` 是美国 GPO 出版物。

**若作品的原属国不是美国，本判据的结论可能与该国法不同。** 两个已实测的差别：

- **保护期**：中国著作权法是作者终身 **+50**（袁隆平卒 2021 → 2071），
  美国是终身 **+70**（→2091）。**两个数不同，而本判据只认后者。**
- **不受保护的对象**：中国《著作权法》第五条把**法律法规、国家机关的决议决定命令、时事新闻**
  排除在保护之外——**本判据的五条里没有对应项**。

**本判据不替非美国人物下结论**，只在输出里把这个口径说出来。属待裁定 ⑩。

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

# ★★★ 2026-08-05 修：**这条线原本写死成 1929，而它每年 1 月 1 日都会往前挪一格。**
#   美国 1978 年前已出版作品 = 出版年 + 95 年，次年元旦进入公有领域：
#       1928 年出版 → 2024-01-01 入 PD      1929 → 2025-01-01
#       **1930 → 2026-01-01（今天已 PD）**  1931 → 2027-01-01（尚未）
#   所以 THIS_YEAR=2026 时，正确的分界是「**1931 年以前出版**」，不是 1929。
#   写死 1929 意味着**每过一年就把两年份的合法材料错判成受版权保护**。
#   ★ 键名 `pre1929` **保留不改**——既有台账（如 Liebig「pre1929 依据 64/64」）用它引着；
#     改的是**年份判据**，不是标签。
PD_PUBLISHED_BEFORE = THIS_YEAR - 95      # 2026 → 1931

# ★ 分诊用：一个人不可能在识字之前发表作品。这里取 15 岁作下限——
#   **它只用于「要不要花时间去探这条依据」，不用于判某份材料是不是 PD。**
#   （袁隆平 1930 年生、分界 1931：要成立就得在 1 岁时出版，算术上排除，不是替他排除。）
MIN_PUBLISHING_AGE = 15

KINDS = {
    "sec105": "17 U.S.C. §105 联邦职务作品",
    "notice1909": "1909 年法：1978 年前出版且无版权标记",
    "pre1929": f"{PD_PUBLISHED_BEFORE} 年前出版，版权已过期（键名沿用 pre1929，年份随 THIS_YEAR 走）",
    "congressional": "国会记录/听证，GPO 印无标记",
    "unpublished_303": "17 U.S.C. §303 未刊作品：卒年 +70，且 2003-01-01 下限已过",
    # ★★ v0.0.0.95：与 build_source_ledger 的词汇表对齐。
    #   我在同一天先后写了两套取值表，`publicly-accessible` 与 `other` 台账认、本件不认
    #   ——新人物的台账若用了它们，本件会误报「不具名」。**两套词汇表就是漂移。**
    "publicly-accessible": "公开可读、无付费墙、未绕过访问控制 —— **这不是公有领域**",
    "other": "以上都不是，须在 rights_note 里写清",
}
# ★ 真正进入「公有领域」统计的只有这五条；后两条**不算 PD**。
TIERS = {"P1", "P2", "S1", "S2", "U"}   # 与 build_source_ledger.TIERS 同源
PD_KINDS = {"sec105", "notice1909", "pre1929", "congressional", "unpublished_303"}

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
            elif y >= PD_PUBLISHED_BEFORE:
                bad.append(f"{w}：**year={y} 不早于 {PD_PUBLISHED_BEFORE}**"
                           f"（{THIS_YEAR} 年的分界；出版年 +95 的次年元旦入 PD）")

        if kind == "publicly-accessible":
            # ★ 它不是公有领域，所以不核 PD 依据；核的是「取用方式合规」有没有写出来
            if not re.search(r"付费墙|paywall|公开|open|无需登录|未绕过|访问控制", ev, re.I):
                bad.append(f"{w}：`publicly-accessible` 的证据要写清**取用方式**"
                           f"（公开可读、无付费墙、未绕过访问控制），"
                           f"**而且它不是公有领域**——不要拿它去凑 PD 的数")

        if kind == "other" and not str(c.get("rights_note") or "").strip():
            bad.append(f"{w}：`other` 必须在 `rights_note` 里写清是什么")

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

        # ★★ 2026-08-05：**分档词表本件此前根本不校验。**
        #   我给 Carver 那四份机构署名的公报写了 `P3`——**P3 不是本项目的分档**
        #   （真词表 `build_source_ledger.TIERS = {P1,P2,S1,S2,U}`，
        #    全库台账实测出现 907 次，**P3 零次**）。
        #   而本件只问「是不是 P1/P2」，于是 `P3` 作为「不是 P1/P2」**静默通过**。
        #   ★ 又一次「空默认值吞掉不知道」：**一个不存在的值被读成了「合规」。**
        tier = c.get("tier")
        if tier is not None and tier not in TIERS:
            bad.append(f"{w}：分档 `{tier}` **不在词表里**——只许 {sorted(TIERS)}。"
                       f"（机构或同事署名的记 **S1**，他人所写的传记记 **S2**）")

        if c.get("byline") == "institution" and c.get("tier") in ("P1", "P2"):
            bad.append(f"{w}：★ **机构署名却标成个人一手（{c['tier']}）**——"
                       f"它是联邦出版物、可能是 PD，但不是他的散文。"
                       f"归「归属不成立」，不要混进可得性统计")
    return bad


def summarize(claims: list) -> dict:
    """→ 分依据计数。**「真公有领域」与「公开可分析」必须分开报**——

    这两件事结论完全不同，而全量实测里后者是主导（102 个交付包 7,629 条来源，
    明说公有领域的只有 7.7%）。**混在一起报，就等于把待裁定 ⑧ 的第 ① 问悄悄答了。**
    """
    by, sec105_own, words = {}, 0, 0
    for c in claims:
        by[c.get("kind")] = by.get(c.get("kind"), 0) + 1
        if c.get("kind") == "sec105" and c.get("byline") != "institution":
            sec105_own += 1
            words += int(c.get("words") or 0)
    pd_n = sum(n for k, n in by.items() if k in PD_KINDS)
    return {"★ 口径": ("**五条依据全部依据美国法**（17 U.S.C. §105/§303、1909 年法、"
                      "美国版权到期、GPO 国会出版物）。**若作品原属国不是美国，"
                      "结论可能与该国法不同**——例：中国是终身+50、美国是终身+70；"
                      "中国《著作权法》第五条排除的对象在本判据里没有对应项。属待裁定 ⑩"),
            "分依据": by,
            "**真公有领域**": pd_n,
            "**公开可分析（不是 PD）**": by.get("publicly-accessible", 0),
            "其它": by.get("other", 0),
            "**§105 且本人署名**": sec105_own, "其字数": words,
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


def feasible_grounds(born=None, died=None, us_federal=None, us_published_pre1978=None,
                     first_published_country=None):
    """★ **排期前的依据可行性分诊**：这个人身上，五条 PD 依据里哪几条**结构上还可能**？

    起因（2026-08-04）：七次可得性探测七次延后，每次 30–70 分钟。
    而其中几次，**依据的适用条件在开跑之前就已经排除了大部分路**——
    例：出生晚于 `PD_PUBLISHED_BEFORE` 的人，`pre1929` 不可能；非美国联邦雇员，`sec105` 不可能。

    **这不是猜，是依据本身的适用条件。** 分诊的用处是**把探测的射程缩小**，
    不是替探测下结论：**只要还剩一条可能，就仍然要探。**

    参数一律可以是 `None`（不知道）——**不知道就当「还可能」，不许替人排除。**
    """
    out = {}
    def mark(k, possible, why):
        out[k] = {"可能": possible, "理由": why}

    mark("pre1929",
         born is None or born + MIN_PUBLISHING_AGE < PD_PUBLISHED_BEFORE,
         (f"生于 {born}，要有 {PD_PUBLISHED_BEFORE} 年前的出版物就得在 "
          f"{PD_PUBLISHED_BEFORE - born} 岁以下发表——算术上排除")
         if (born and born + MIN_PUBLISHING_AGE >= PD_PUBLISHED_BEFORE)
         else ("生年未知——当作还可能" if born is None
               else f"生年早于 {PD_PUBLISHED_BEFORE - MIN_PUBLISHING_AGE}，可能有"))
    mark("sec105",
         us_federal is not False,
         "已知非美国联邦雇员" if us_federal is False
         else ("是否任过美国联邦职务未知——当作还可能" if us_federal is None else "任过美国联邦职务"))
    # ★★ URAA §104A：外国作品的「无版权标记」这个缺陷，**1996-01-01 已被自动治愈**。
    #   条文（袁隆平 #123 探测查实）：§104A(h)(6)(C)(i) 明文把「lack of proper notice」
    #   列为被恢复的缺陷；(h)(6)(D) 要求首次在 eligible country 出版且**未在 30 日内在美同步出版**；
    #   (h)(8) 定 source country；Berne/WTO 成员国恢复日 = **1996-01-01**。
    #   ★ 但**恢复只作用于「1996 年时在源国仍受保护」的作品**——
    #     Liebig（卒 1873，源国 1943 即过期）这类不受影响。**所以这里只提示，不否决。**
    _foreign = (first_published_country is not None
                and str(first_published_country).upper() not in ("US", "USA", "美国"))
    _why09 = ("已知无 1978 年前的美国出版物" if us_published_pre1978 is False
              else ("1978 年前有无美国出版物未知——当作还可能" if us_published_pre1978 is None
                    else "有 1978 年前的美国出版物"))
    if _foreign:
        _why09 += ("　★★ **首次出版国是 " + str(first_published_country) +
                   "，非美国** —— URAA §104A 把「无版权标记」列为**可恢复的缺陷**，"
                   "伯尔尼/WTO 成员国恢复日 1996-01-01。**若该作品 1996 年时在源国仍受保护，"
                   "这条缺陷已被自动治愈**，`notice1909` 基本不成立"
                   "（除非能证明 30 日内在美同步出版）。"
                   "★ 反之，若 1996 年时在源国**已过期**（如卒于 1873 的作者），恢复不适用，本提示不影响。")
    mark("notice1909", us_published_pre1978 is not False, _why09)
    mark("unpublished_303",
         died is None or died + 70 < THIS_YEAR,
         f"卒年 {died}+70 = {died+70}，未到 {THIS_YEAR}，仍在保护期" if (died and died + 70 >= THIS_YEAR)
         else ("卒年未知——当作还可能" if died is None else "卒年+70 已过"))
    mark("congressional", True, "**任何人都可能在美国国会作过证——这一条不能靠属性排除，只能查**")

    out["★ 口径"] = ("**五条依据全部依据美国法**——非美国人物的结论可能与其原属国法不同（待裁定 ⑩）")
    left = [k for k, v in out.items() if isinstance(v, dict) and v.get("可能")]
    out["**还可能的依据**"] = left
    out["**结论**"] = ("★ 五条全部排除——**但 `congressional` 永远不能靠属性排除**，此处必有 bug"
                     if not left else
                     f"探测射程可缩到 **{len(left)} 条**：{left}"
                     + ("　★ **只剩国会记录一条，做一次窄探测即可**" if left == ["congressional"] else ""))
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

    print("── ★★★ 反向对照 ⑥·补：**分界必须随 THIS_YEAR 滚动，不许写死 1929** ──")
    print(f"   THIS_YEAR={THIS_YEAR} → PD_PUBLISHED_BEFORE={PD_PUBLISHED_BEFORE}")
    chk(f"1930 年出版**是 PD**（2026-01-01 起）→ 不许报",
        not any("不早于" in x for x in check([{"work": "x", "kind": "pre1929",
                                              "year": 1930, "evidence": "扉页"}])))
    chk("1931 年出版**还不是 PD** → 必须报",
        any("不早于" in x for x in check([{"work": "x", "kind": "pre1929",
                                          "year": 1931, "evidence": "扉页"}])))
    chk(f"分界是算出来的（{THIS_YEAR}−95={PD_PUBLISHED_BEFORE}），不是字面量 1929",
        PD_PUBLISHED_BEFORE == THIS_YEAR - 95 and PD_PUBLISHED_BEFORE != 1929)
    chk("★ 分诊：1930 年生的人仍被排除 pre1929（要 1 岁出版）",
        "pre1929" not in feasible_grounds(born=1930, died=2021)["**还可能的依据**"])
    chk("★ 而 1900 年生的人不许被排除",
        "pre1929" in feasible_grounds(born=1900)["**还可能的依据**"])

    print("── 反向对照 ⑥：pre1929 的年份必须真的早于分界 ──")
    chk(f"year=1931 → 报出（分界 {PD_PUBLISHED_BEFORE}）",
        any(f"不早于 {PD_PUBLISHED_BEFORE}" in x for x in check([{"work": "x", "kind": "pre1929",
                                               "year": 1931, "evidence": "版权页"}])))

    print("── ★★★ 反向对照 ⑦·补：**分档不在词表里 → 必须报**（P3 曾静默通过） ──")
    chk("tier=P3 被报出",
        any("不在词表里" in x for x in check([{"work": "x", "kind": "pre1929", "year": 1900,
                                              "evidence": "扉页", "tier": "P3"}])))
    chk("★ 而 S1 / S2 是合法的，**不许误报**",
        not any("不在词表里" in x for x in check([
            {"work": "a", "kind": "pre1929", "year": 1900, "evidence": "扉页", "tier": "S1"},
            {"work": "b", "kind": "pre1929", "year": 1900, "evidence": "扉页", "tier": "S2"}])))
    chk("★ 没写 tier 的**不报**（本件不强制每条都有分档）",
        not any("不在词表里" in x for x in check([{"work": "c", "kind": "pre1929",
                                                  "year": 1900, "evidence": "扉页"}])))

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

    print("── ★★★ 反向对照 ⑫：与 build_source_ledger 的词汇表必须一致（v0.0.0.95）──")
    import importlib.util as _iu, pathlib as _pl
    _b = _pl.Path(__file__).resolve().parent / "build_source_ledger.py"
    if _b.is_file():
        _s = _iu.spec_from_file_location("_bsl", _b); _m = _iu.module_from_spec(_s); _s.loader.exec_module(_m)
        chk(f"两套取值表一致（各 {len(KINDS)} 条）", set(KINDS) == set(_m.RIGHTS_GROUNDS))
    else:
        chk("build_source_ledger.py 不在——**词汇表一致性未核（不是通过）**", False)

    print("── ★★ 反向对照 ⑬：`publicly-accessible` **不算进公有领域** ──")
    s = summarize([{"kind": "pre1929"}, {"kind": "publicly-accessible"},
                   {"kind": "publicly-accessible"}, {"kind": "other"}])
    chk(f"真 PD {s['**真公有领域**']}、公开可分析 {s['**公开可分析（不是 PD）**']}、其它 {s['其它']}",
        s["**真公有领域**"] == 1 and s["**公开可分析（不是 PD）**"] == 2 and s["其它"] == 1)
    chk("publicly-accessible 的证据不写取用方式 → 报出",
        any("取用方式" in x for x in check([{"work": "x", "kind": "publicly-accessible",
                                            "evidence": "网上有"}])))
    chk("写了取用方式 → 不报",
        not check([{"work": "x", "kind": "publicly-accessible",
                    "evidence": "作者官网公开可读，无付费墙，未绕过访问控制"}]))
    chk("other 无 rights_note → 报出",
        any("rights_note" in x for x in check([{"work": "x", "kind": "other", "evidence": "馆方授权"}])))

    print("── ★★ 反向对照 ⑭：依据可行性分诊（v0.0.0.96）──")
    y = feasible_grounds(born=1930, died=2021, us_federal=False, us_published_pre1978=False)
    chk(f"袁隆平那类（1930 生／2021 卒／非美联邦／无 1978 前美国出版）→ 只剩 {y['**还可能的依据**']}",
        y["**还可能的依据**"] == ["congressional"])
    b = feasible_grounds(born=1821, died=1910)
    chk(f"Blackwell 那类（1821–1910，其余未知）→ {len(b['**还可能的依据**'])} 条仍可能",
        set(b["**还可能的依据**"]) == {"pre1929", "sec105", "notice1909", "unpublished_303", "congressional"})
    print("── ★★★ 反向对照 ⑮：**不知道就当还可能，不许替人排除** ──")
    u = feasible_grounds()
    chk(f"全不知道 → 五条全留（实得 {len(u['**还可能的依据**'])} 条）",
        len(u["**还可能的依据**"]) == 5)
    chk("★ `congressional` **永远不能靠属性排除**",
        feasible_grounds(born=2020, died=2021, us_federal=False,
                         us_published_pre1978=False)["**还可能的依据**"] == ["congressional"])

    print("── ★★ 反向对照 ⑯：口径必须出现在**每一次**输出里（v0.0.0.97）──")
    for label, cl in (("有主张时", [{"kind": "pre1929", "year": 1900, "evidence": "x"}]),
                      ("空表时", [])):
        s = summarize(cl)
        chk(f"{label}都带口径说明", "★ 口径" in s and "美国法" in s["★ 口径"])

    print("── ★★ 反向对照 ⑰：URAA 提示（v0.0.0.101）──")
    cn = feasible_grounds(born=1930, died=2021, first_published_country="CN")
    chk("外国首次出版 → notice1909 带 URAA 提示",
        "URAA" in cn["notice1909"]["理由"])
    chk("★ 但**不否决**（仍标「可能」）——恢复只作用于 1996 年时源国仍受保护的作品",
        cn["notice1909"]["可能"] is True)
    us = feasible_grounds(born=1900, died=1980, first_published_country="US")
    chk("首次出版国是美国 → 不带 URAA 提示", "URAA" not in us["notice1909"]["理由"])
    un = feasible_grounds(born=1803, died=1873)
    chk("不知道首次出版国 → 不带提示（**不许替人推断**）",
        "URAA" not in un["notice1909"]["理由"])

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
