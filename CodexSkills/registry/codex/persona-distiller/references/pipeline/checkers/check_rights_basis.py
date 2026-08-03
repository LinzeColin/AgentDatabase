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

# ★ 聚合器：它们的 `license` 字段是**转述**，不是权利声明
AGGREGATORS = re.compile(
    r"unpaywall|openalex|\bcore\b|\bbase\b|semantic\s*scholar|\bs2\b|dimensions\.ai"
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
    if not value:
        return False
    return str(value).strip().lower().rstrip(".") in PD_VALUES


def basis_of(record):
    """→ 依据文本（把可能承载依据的字段拼起来）。"""
    parts = []
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

    print("\n  ✓ 每一条公有领域声明都带得住的依据")
    return 0


if __name__ == "__main__":
    sys.exit(main())
