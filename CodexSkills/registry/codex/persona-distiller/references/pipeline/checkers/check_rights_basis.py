#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**说它是公有领域，依据是什么？**——聚合器的 `license` 字段不算依据。

## 为什么有这件

#116 Jean Watson 探测里撞到一条**已发生、可复现**的误判：

    DOI 10.1111/j.1365-2702.2005.01256.x
      （Watson 独著，Journal of Clinical Nursing 2005 Guest Editorial）

    Unpaywall  → best_oa_location.license = "public-domain"
    Crossref   → license = "http://onlinelibrary.wiley.com/termsAndConditions#vor"

**同一个 DOI，聚合器说公有领域，出版方条款说 Wiley 标准条款。**
作者 1940 年生**且在世**——这篇怎么可能是公有领域。

**照抄聚合器的 `license` 字段 = 把受保护作品当公有领域入库。**
而本项目的头号铁律就是只取公有领域。

## 产物侧实测（2026-08-04，十一个工作区）

`rights` 字段的全部取值：

    872 条  public-domain                                    （9 人）
    196 条  public-web                                       （Godin，在世）
     55 条  publicly-accessible-for-analysis; redistribution-not-assumed（Steinhardt，在世）

**两位在世作者都没有被标成公有领域——这一侧做得是对的。**
八位历史人物标 `public-domain` 也各自站得住（Jenner 卒 1823 … Osler 卒 1919）。

**但 872 条里，一条都没有记录「依据是什么」。**
`rights` 记的是**结论**，不是**依据**。

## ★ 为什么「结论对」还不够

**公有领域是一个随时间与法域变化的结论。** 最贴近的例子就在本名册里：

> **Fleming 卒于 1955 年。** 在「终身 + 70 年」的法域里，
> 他的作品是 **2025 年 1 月 1 日**才进入公有领域的。
> **同样一句 `public-domain`，2024 年写就是错的。**

一个只记结论、不记依据的字段，**事后无法复核**：
分不出「按卒年推定」「查了出版方页面」还是「照抄了 Unpaywall」。

## 判据

对每条声称公有领域的源：

| 依据 | 判 |
|---|---|
| 出版方页面 / Crossref 原始记录 / 版权局（CCE、CPRS） / 卒年规则 | **过** |
| **写着 Unpaywall／OpenAlex／CORE／BASE／Semantic Scholar 等聚合器** | **报——这是那条误判的形状** |
| **什么都没写** | **报「有结论无依据」——与上一条分开** |
| 不声称公有领域 | **不判**（在世作者标 `public-web` 是对的，不许误伤） |

## 它判不了什么

- **判不了结论本身对不对。** 它只看依据在不在、依据能不能作数。
  **今天那 872 条大概率结论都是对的**——本件报的是「依据不在产物里」，
  **不是「这些判断错了」**。
- **判不了法域。** 「终身+70」与「发表+95」结论可能不同；本件不替你选法域，
  但**依据里写明了法域的**，将来复核时才有得核。
- **它不设门**，只写 metrics。真正的把关在抓源侧：**只取公有领域**。
"""
import argparse
import collections
import json
import pathlib
import re
import sys

# 声称「公有领域」的取值（大小写与标点不敏感）
PD_VALUES = {"public-domain", "public domain", "publicdomain", "pd", "cc0"}

# ★★ 2026-08-04 适配性修正。**第一版只认得「结论」那一种写法，于是把更好的写法跳过了。**
#   实测：#117 Barton 的 `rights` 写的是**依据**——`卒年 1912，终身+70 已过`；
#   而 #111 Fleming 写的是**结论**——`public-domain`。
#   第一版 `is_pd()` 只匹配裸结论，于是 Barton 208 条全被判成「不声称公有领域，不判」，
#   **判据反而奖励了信息量更少的那种写法。**
#   （这正是「为解决新问题打补丁、导致旧的不适配」的反面例子：
#   　判据只认它出生时见过的形状，形状一变就白装。）
PD_ASSERTIONS = re.compile(
    r"公有领域|public\s*[-_]?\s*domain|\bcc0\b|(?<![a-z])pd(?![a-z])"
    r"|终身\s*\+?\s*70|卒年[^，。;；]{0,20}已过|保护期[^，。;；]{0,10}已过", re.I)

# ★ 聚合器：它们的 `license` 字段是**转述**，不是权利声明
#
# ★★ 2026-08-04 去掉三个会撞的 token：`\bcore\b`、`\bbase\b`、`\bs2\b`。
#   实测 #117 Barton **73 条假阳，全部来自 `\bs2\b`**——
#   命中的是**本流水线自己的分档名 S2**（我给第三方源写的
#   「S1 为同时代记述，**S2** 为后世研究与传记」）。
#   `core` 与 `base` 更糟，是普通英文词。
#
#   **宁可漏掉 CORE 与 BASE 这两家，也不能把「S2 分档」报成「照抄了聚合器」**——
#   一条假的「依据不作数」会让人回去重查一份本来没问题的源，
#   而判据分不出 `CORE`（聚合器）与 `core`（普通词）。**分不出的就不判。**
AGGREGATORS = re.compile(
    r"unpaywall|openalex|semantic\s*scholar|dimensions\.ai"
    r"|scilit|lens\.org|europe\s*pmc", re.I)

# 能作数的依据
AUTHORITATIVE = re.compile(
    r"crossref|出版方|publisher|版权局|copyright\s*office|\bcce\b|\bcprs\b"
    r"|renewal|续展|卒年|death|逝世|殁|public\s*domain\s*day|扉页|title\s*page"
    r"|colophon|terms\s*and\s*conditions|©|\(c\)", re.I)

# 依据可能写在这些字段里
BASIS_FIELDS = ("rights_basis", "rights_source", "license_source",
                "rights_note", "attribution")


def is_pd(value):
    """两种写法都要认：**裸结论**（`public-domain`）与**带依据的断言**（`卒年 1912，终身+70 已过`）。

    **不许把「不声称公有领域」的也认进来**——`public-web`（Godin，在世）、
    `publicly-accessible-for-analysis; redistribution-not-assumed`（Steinhardt，在世）
    都含 `public` 但都**没有**声称公有领域，一律不判。
    """
    if not value:
        return False
    s = str(value).strip()
    if s.lower().rstrip(".") in PD_VALUES:
        return True
    return bool(PD_ASSERTIONS.search(s))


def basis_of(record):
    """→ 依据文本（把可能承载依据的字段拼起来）。

    ★ `rights` **自己也可能就是依据**（`卒年 1912，终身+70 已过`）——
      第一版只看 `rights_basis`／`attribution` 等旁字段，
      于是「依据写在 rights 里」这种写法被判成「有结论无依据」。
    """
    parts = []
    rights = record.get("rights")
    if rights and str(rights).strip().lower().rstrip(".") not in PD_VALUES:
        # 裸结论不算依据；写成句子的才算。
        parts.append(str(rights))
    for f in BASIS_FIELDS:
        v = record.get(f)
        if v:
            parts.append(str(v))
    return " ".join(parts).strip()


def audit(records):
    """→ (聚合器依据的, 无依据的, 有据可查的, 不声称PD的)。"""
    by_agg, no_basis, ok, not_pd = [], [], [], []
    for r in records:
        sid = r.get("source_id") or r.get("id") or r.get("local_path") or "?"
        if not is_pd(r.get("rights")):
            not_pd.append(sid)
            continue
        b = basis_of(r)
        if not b:
            no_basis.append(sid)
        elif AGGREGATORS.search(b):
            # ★ 聚合器优先判：**即使同一段里也提到了 Crossref**，
            #   只要依据里出现聚合器就必须报——那正是误判发生的地方。
            by_agg.append((sid, b[:90]))
        elif AUTHORITATIVE.search(b):
            ok.append(sid)
        else:
            no_basis.append(sid)
    return by_agg, no_basis, ok, not_pd


# ══════════════════ 自测 ══════════════════

def selftest() -> int:
    fails = []

    def chk(label, cond):
        print(("  ✓ " if cond else "  ✗ ") + label)
        if not cond:
            fails.append(label)

    print("── ★★ 正向：**聚合器依据必须报**（Watson #116 那条真实误判的形状）──")
    agg, nb, ok, npd = audit([{
        "source_id": "s1", "rights": "public-domain",
        "rights_basis": "Unpaywall best_oa_location.license = public-domain"}])
    print(f"    → 聚合器依据 {len(agg)} 条")
    chk("Unpaywall 作依据 → 报", len(agg) == 1 and agg[0][0] == "s1")

    print("── ★★ 反向对照 ①：**结论碰巧对，依据仍然不作数** ──")
    agg, nb, ok, npd = audit([{
        "source_id": "s2", "rights": "public-domain",       # 1823 年卒的人，结论确实对
        "rights_basis": "OpenAlex 说 license 是 public-domain"}])
    chk("哪怕这一篇真的是 PD，写 OpenAlex 作依据也要报", len(agg) == 1 and not ok)

    print("── ★★ 反向对照 ②：**「无依据」与「聚合器依据」必须分开** ──")
    agg, nb, ok, npd = audit([{"source_id": "s3", "rights": "public-domain"}])
    print(f"    → 聚合器 {len(agg)}　无依据 {len(nb)}")
    chk("什么都没写 → 记「无依据」，不记「聚合器」", not agg and nb == ["s3"])

    print("── ★★ 反向对照 ③：**不声称 PD 的一律不判**（在世作者不许误伤）──")
    agg, nb, ok, npd = audit([
        {"source_id": "godin", "rights": "public-web"},                       # 在世
        {"source_id": "stein", "rights": "publicly-accessible-for-analysis; "
                                         "redistribution-not-assumed"},       # 在世
    ])
    print(f"    → 不判 {len(npd)} 条，报 {len(agg)+len(nb)} 条")
    chk("Godin／Steinhardt 那两种取值 → 完全不判", len(npd) == 2 and not agg and not nb)

    print("── ★ 反向对照 ④：能作数的依据要放行 ──")
    agg, nb, ok, npd = audit([
        {"source_id": "a", "rights": "public-domain", "rights_basis": "卒年 1910，终身+70 已过"},
        {"source_id": "b", "rights": "public-domain",
         "rights_basis": "Crossref license 字段为空，出版方扉页印 1898"},
        {"source_id": "c", "rights": "public-domain",
         "rights_basis": "CCE 全库 grep 未见续展登记，1928 年出版"},
    ])
    print(f"    → 有据可查 {len(ok)} 条")
    chk("卒年／Crossref＋出版方／版权局 三种依据都放行", len(ok) == 3 and not agg and not nb)

    print("── ★ 反向对照 ⑤：**聚合器优先**——同段里提到 Crossref 也仍要报 ──")
    agg, nb, ok, npd = audit([{
        "source_id": "d", "rights": "public-domain",
        "rights_basis": "Unpaywall 说 public-domain，Crossref 没细看"}])
    chk("既提聚合器又提 Crossref → 仍报（误判正是这么发生的）", len(agg) == 1 and not ok)

    print("── 反向对照 ⑥：大小写／句点不影响判定 ──")
    agg, nb, ok, npd = audit([{"source_id": "e", "rights": "Public-Domain.",
                               "rights_basis": "卒年 1823"}])
    chk("`Public-Domain.` 与 `public-domain` 同等对待", len(ok) == 1)

    print("── ★ 反向对照 ⑦：**依据写了但不知所云，算无依据** ──")
    agg, nb, ok, npd = audit([{"source_id": "f", "rights": "public-domain",
                               "rights_basis": "应该没问题"}])
    chk("「应该没问题」不算依据", nb == ["f"] and not ok)

    print("── ★★★ 反向对照 ⑨：**两种写法都要认**（适配性——第一版只认得一种）──")
    # #117 Barton 的真实形状：`rights` 里写的是**依据**，不是裸结论
    agg, nb, ok, npd = audit([{"source_id": "barton", "rights": "卒年 1912，终身+70 已过"}])
    print(f"    `卒年 1912，终身+70 已过` → 有据 {len(ok)}／无据 {len(nb)}／不判 {len(npd)}")
    chk("**依据写在 rights 里**也要算「声称公有领域」且「有据可查」",
        len(ok) == 1 and not npd and not nb)
    # #111 Fleming 的真实形状：裸结论
    agg, nb, ok, npd = audit([{"source_id": "fleming", "rights": "public-domain"}])
    chk("裸结论仍判「有结论无依据」（不许因为放宽而放过它）", nb == ["fleming"])

    print("── ★★ 反向对照 ⑩：**含 public 但不声称 PD 的，仍然一律不判** ──")
    agg, nb, ok, npd = audit([
        {"source_id": "godin", "rights": "public-web"},
        {"source_id": "stein", "rights": "publicly-accessible-for-analysis; "
                                        "redistribution-not-assumed"},
    ])
    print(f"    → 不判 {len(npd)} 条")
    chk("`public-web` 与 `publicly-accessible…` 都含 public，**都不许被认成 PD**",
        len(npd) == 2 and not ok and not nb and not agg)

    print("── ★★★ 反向对照 ⑪：**分档名 S2 不许被当成聚合器**（73 条真实假阳）──")
    agg, nb, ok, npd = audit([{
        "source_id": "barton-s2", "rights": "卒年 1912，终身+70 已过",
        "attribution": "**第三方材料，不计为其所著。** S1 为同时代记述（1860–1915），"
                       "S2 为后世研究与传记。"}])
    print(f"    含「S2 为后世研究」→ 聚合器 {len(agg)}／有据 {len(ok)}")
    chk("`S2` 是本流水线的分档名，**不许命中聚合器**", not agg and len(ok) == 1)

    print("── ★★ 反向对照 ⑫：**真的聚合器仍要抓出来** ──")
    agg, nb, ok, npd = audit([{
        "source_id": "x", "rights": "public-domain",
        "rights_basis": "Unpaywall best_oa_location.license = public-domain"}])
    chk("Unpaywall 仍报（放宽不许把真的也放过）", len(agg) == 1)

    print("── ★★ 反向对照 ⑧：**今天那 872 条的真实形状**（只有结论，没有依据字段）──")
    agg, nb, ok, npd = audit([{"source_id": f"s{i}", "rights": "public-domain"}
                              for i in range(872)])
    print(f"    → 无依据 {len(nb)} 条，聚合器 0 条")
    chk("872 条全部记为「有结论无依据」，**不是「判断错了」**",
        len(nb) == 872 and not agg)

    print(f"\n{'✓ 自测全过' if not fails else f'✗ **{len(fails)} 项未过**'}")
    return 0 if not fails else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ledger", type=pathlib.Path, help="evidence/source-ledger.jsonl")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return selftest()
    if not a.ledger:
        ap.error("要么 --self-test，要么给 --ledger")
    if not a.ledger.is_file():
        print(f"✗ **{a.ledger} 不在——本次未检查（不是通过）**")
        return 3

    records = [json.loads(l) for l in a.ledger.read_text(encoding="utf-8").splitlines()
               if l.strip()]
    if not records:
        print("✗ **账本是空的——本次未检查（不是通过）**")
        return 3

    agg, nb, ok, npd = audit(records)
    print(f"源 **{len(records)}** 条　声称公有领域 **{len(agg)+len(nb)+len(ok)}** 条"
          f"　不声称 {len(npd)} 条（不判）\n")
    print(f"  有据可查　　　　{len(ok):>4}")
    print(f"  **有结论无依据**　{len(nb):>4}")
    print(f"  **依据是聚合器**　{len(agg):>4}")

    if agg:
        print("\n✗ **依据取自聚合器——那不是权利声明，是转述**：")
        for sid, b in agg[:10]:
            print(f"    {sid}：{b}")
        print("\n  实测过的误判：Unpaywall 对 `10.1111/j.1365-2702.2005.01256.x`"
              " 返回 `license = public-domain`，\n"
              "  而同一 DOI 的 Crossref 写的是 Wiley 标准条款，**作者在世**。\n"
              "  **版权判据只能取自出版方页面、Crossref 原始记录或版权局记录。**")
        return 1

    if nb:
        print(f"\n！ **{len(nb)} 条只有结论、没有依据。**")
        print("  **这不是说这些判断错了**——今天名册上八位历史人物的结论都站得住。\n"
              "  但公有领域是**随时间与法域变化**的结论：Fleming 卒于 1955，\n"
              "  在「终身+70」法域里是 **2025 年**才进入公有领域的——\n"
              "  **同样一句 `public-domain`，2024 年写就是错的。**\n"
              "  只记结论不记依据，事后分不出是按卒年推定、查了出版方，还是照抄了聚合器。")
        return 1

    # ★★ **零扫描面不许印肯定句。** 2026-08-17 交叉喂测：把一份无关 JSON 当账本
    #   传进来，本判据**照样印「✓ 每一条公有领域声明都带得住的依据」并 rc=0** ——
    #   而它一条声明都没读到。「每一条都成立」在空集上恒真，那不是通过。
    #   [[zero-hit-gates-must-prove-they-can-hit]]｜[[a-rights-check-said-zero-red-after-reading-nothing]]
    claimed = len(agg) + len(nb) + len(ok)
    if not claimed:
        print("\n  ⚠ **账本里一条公有领域声明都没读到 —— 本次未核，不是通过。**")
        print("    （扫描面为空时「每一条都成立」恒真；先确认传对了账本文件。）")
        return 0
    print("\n  ✓ 全部 **%d** 条公有领域声明都带得住依据" % claimed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
