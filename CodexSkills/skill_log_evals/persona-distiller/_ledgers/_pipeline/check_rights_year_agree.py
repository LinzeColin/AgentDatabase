#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_rights_year_agree.py —— **`rights` 主张 PD，台账里的年份接不接得住**

## 为什么有这件

2026-08-13 建 Dewey #190 台账时，`emit_source_ledger` 写出了这一行：

    source_id     src-a0ada4409351
    published_at  "2003"
    rights        "pre1931"
    rights_basis  "公有领域 = 出版于 ≤1930（分界 1931）；出版年 2003（题名页年份取最大）"

**同一行里，依据说 ≤1930，取值写 2003。** 台账**自己驳倒自己**，而
从抓源到建台账没有任何一件判据看这两个字段是否互相印证——
`scan_copyright.py` 只扫正文里的版权声明，看不到台账字段。

真相是那份是 Project Gutenberg 的电子本，1971/1996/…/2003 全来自 PG 页眉
（"Readable ... Since 1971"、版权声明）；底本《民主与教育》1916 年出版、确在公有领域。
**结论没错，凭据错了** —— 而错的凭据就这样躺在交付物里。
[[catalog-says-one-person-bytes-are-another]] 的同型：**著录字段本身是坏的。**

## 判什么（★ **四档分开数**，口径写在输出里）

| 档 | 形态 | 判定 |
|---|---|---|
| **①a 自相矛盾** | 按年份主张 PD，而年份**按今天的分界也够不着** | ✗ **红**（rc=1） |
| **①b 分界陈旧** | 年份接不住 rights 里写的旧分界，**而按今天的分界确在 PD** | ⚠ 计数报出，重建台账即好 |
| **② 无本地凭据** | rights 按年份主张 PD，而 published_at **没有四位年份** | ⚠ 计数报出，`--strict` 才算红 |
| **③ 出射程** | rights 写明了**非年份依据**（§303／§105／捐献声明／公元前著作…） | 只计数，**不判** |

★ 分四档的理由：处置各不相同。②「凭据在 IA 元数据里只是没落进台账」，
①b「分界每年元旦前移，旧台账的 rights 字符串陈旧」——**权利上都没问题**；
只有 ①a 是权利主张真的站不住。混成一个数字就没法处置了。
★ ①b 是 2026-08-13 跑起来才发现的：**我原本把它和 ①a 混在一档**，
  差点把已入库的 Carver #127 报成「权利主张站不住」——而 1929 ≤ 1930，它确在 PD。
[[counts-need-their-cutoff-stated]]

★ 本件**不**判「这份到底是不是公有领域」——那要看原书。
   它只问一件：**台账写下的两个字段，能不能互相印证。**

## 用法

    python3 check_rights_year_agree.py                    # 全库
    python3 check_rights_year_agree.py --ledger <台账.jsonl>
    python3 check_rights_year_agree.py --strict           # ② 也算红
    python3 check_rights_year_agree.py --self-test

退出码：0＝没有自相矛盾；1＝有；4＝一个台账都没找到（**未判，不是通过**）
"""
import argparse
import datetime
import glob
import json
import os
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
CORPORA = HERE.parent.parent / "_corpora"

THIS_YEAR = datetime.date.today().year
PD_CUTOFF = THIS_YEAR - 95            # 2026 → 1931（与 emit_source_ledger.py 同式）
LATEST_PD_YEAR = PD_CUTOFF - 1        # 可用最晚出版年

# ① rights 取值「按年份主张 PD」的两种写法（全库实测只有这两种）
#    · `pre1931` / `pre-1931`
#    · 散文里含 `pre-1929 publication` 这类「按出版年」的措辞
BY_YEAR_CODE = re.compile(r"^pre-?(\d{4})$", re.I)
BY_YEAR_PROSE = re.compile(r"pre-?(\d{4})\s+publication", re.I)

# ③ 写明了**非年份**依据的标记词——命中即出射程
#    ★ 逐条取自全库实测出现过的 rights 散文，不是我想象的
NON_YEAR_BASIS = re.compile(
    r"§\s*30[35]|17\s*U\.?S\.?C\.?\s*§\s*30[35]|"        # 未出版稿／联邦职务作品
    r"dedicated to the public|捐献|"                       # 权利人捐献声明
    r"公元前|未声明底本年份|"                                # 古代著作
    r"卒于\s*\d{4}\s*年前",                                 # 按作者卒年
    re.I)

YEAR4 = re.compile(r"(1[0-9]{3}|20[0-9]{2})")


def classify(rights, published_at):
    """→ ("ok"|"矛盾"|"无据"|"出射程"|"非PD", 说明)。**纯函数，自测不碰磁盘。**"""
    rt = str(rights or "").strip()
    if not rt:
        return "非PD", "rights 为空——本件不判（缺字段是另一件的事）"

    code = BY_YEAR_CODE.match(rt)
    prose = BY_YEAR_PROSE.search(rt)
    if not (code or prose):
        if NON_YEAR_BASIS.search(rt):
            return "出射程", "写明了非年份依据"
        # 裸 `public-domain` 之类：没说按什么主张 ⇒ 本件够不着，另记一档
        if re.search(r"public[-\s]?domain|公有领域", rt, re.I):
            return "出射程", "★ 只写了「公有领域」而未声明依据——**本件够不着**，需另立一件"
        return "非PD", "rights 不是 PD 主张"

    claimed = int((code or prose).group(1))          # 主张里写的分界年
    m = YEAR4.search(str(published_at or ""))
    if not m:
        return "无据", f"rights 按年份主张 PD（pre{claimed}），而 published_at={published_at!r} 里没有四位年份"
    y = int(m.group(1))
    if y < claimed:
        return "ok", f"出版年 {y} < {claimed}"
    # ★★ 到这儿是「主张接不住」。**两种成因，处置完全不同，必须切开**：
    #    · 今天的分界也够不着 ⇒ 真矛盾（权利上就站不住）
    #    · 只是主张里那个分界陈旧（分界每年元旦前移）⇒ **这份今天确在 PD**，
    #      坏的只是 rights 字符串，重建台账即可。[[pd-cutoff-rolls-every-january]]
    if y >= PD_CUTOFF:
        return "矛盾", (f"rights=pre{claimed} 而出版年 {y} ≥ {claimed}；"
                        f"**按今天的分界 {PD_CUTOFF} 也够不着** —— 权利主张站不住")
    return "陈旧", (f"rights=pre{claimed} 而出版年 {y} ≥ {claimed}，"
                    f"**但 {y} ≤ {LATEST_PD_YEAR}，按今天的分界 {PD_CUTOFF} 确在公有领域**；"
                    f"坏的是 rights 字符串（建台账时分界还是 {claimed}），重建台账即可")


def ledgers(one=None):
    if one:
        return [one] if os.path.isfile(one) else []
    return sorted(glob.glob(str(CORPORA / "wip-*" / "workspaces" / "*" /
                                "evidence" / "source-ledger.jsonl")))


def scan(paths):
    buckets = {"矛盾": [], "陈旧": [], "无据": [], "出射程": 0, "ok": 0, "非PD": 0}
    rows = 0
    for p in paths:
        who = os.path.basename(os.path.dirname(os.path.dirname(p)))
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except ValueError:
                continue
            rows += 1
            k, why = classify(r.get("rights"), r.get("published_at"))
            if k in ("矛盾", "陈旧", "无据"):
                buckets[k].append({"人": who, "source_id": r.get("source_id"),
                                   "title": (r.get("title") or "")[:52],
                                   "published_at": r.get("published_at"), "为什么": why})
            else:
                buckets[k] += 1
    return rows, buckets


def self_test() -> int:
    """★ 正例逐字取自 2026-08-13 真实撞到的 Dewey 那一行与 Burbank 三行。"""
    cases = [
        # (rights, published_at, 该判成什么, 这一条从哪来)
        ("pre1931", "2003", "矛盾", "★ Dewey src-a0ada4409351（PG 页眉年份）"),
        ("pre1931", "", "无据", "★ Burbank src-aab594edb7c1（published_at 空串）"),
        ("pre1931", "1916", "ok", "正常：出版年在分界之前"),
        ("pre1931", "1930", "ok", "★ 压线：1930 < 1931 必须放行"),
        ("pre1931", "1931", "矛盾", "★ 压线反向：1931 不小于 1931 必须报"),
        ("pre1929", "1929", "陈旧", "★ Carver src-2e3cf8be2189：接不住旧分界 1929，而 1929 ≤ 1930 今天确在 PD"),
        ("pre1929", "1930", "陈旧", "★ 同上边界：1930 正好是今天可用的最晚出版年"),
        ("pre1929", "1931", "矛盾", "★ 旧分界 + 今天也够不着 ⇒ 仍是真矛盾"),
        ("public-domain (pre-1929 publication; US 17 USC)", None, "无据",
         "★ Liebig：散文里按年份主张，而没有 published_at"),
        ("公有领域；依 17 U.S.C. §303，作者卒于 1955 年前者已进入 PD", "未系年", "出射程",
         "★ Blackwell：写明非年份依据 ⇒ 本件不判"),
        ("public-domain（原作公元前 1 世纪；本转写页未声明底本年份）", None, "出射程",
         "★ Cicero：古代著作"),
        ("public-domain", None, "出射程",
         "★ Semmelweis：裸主张，本件够不着（另立一件）"),
        ("in-copyright", "1966", "非PD", "不是 PD 主张 ⇒ 不判"),
        ("", "1916", "非PD", "rights 为空 ⇒ 不判"),
    ]
    bad = 0
    for rt, pa, want, src in cases:
        got, why = classify(rt, pa)
        ok = got == want
        bad += 0 if ok else 1
        print(f"  {'✓' if ok else '✗'} {want:5s} ← rights={rt[:38]!r} published_at={pa!r}")
        print(f"       {src}")
        if not ok:
            print(f"       ✗ 实得 {got}：{why}")
    # ★ 反向：分界随年份滚动，别写死
    ok_roll = PD_CUTOFF == THIS_YEAR - 95 and LATEST_PD_YEAR == PD_CUTOFF - 1
    bad += 0 if ok_roll else 1
    print(f"  {'✓' if ok_roll else '✗'} 分界随年份滚动：{THIS_YEAR} − 95 = {PD_CUTOFF}"
          f"（可用最晚出版年 {LATEST_PD_YEAR}）")
    # ★ 「几例来自实测」现算，不手写 [[self-reported-numbers-must-be-computed]]
    real = sum(1 for _, _, _, s in cases if re.search(r"src-[0-9a-f]{8,}|Liebig|Blackwell|Cicero|Semmelweis", s))
    print(f"\n{'✓ 全过' if bad == 0 else f'✗ {bad} 项不符'}"
          f"（{len(cases)} 例，其中 **{real} 例**逐字取自全库实测的 rights 取值，"
          f"其余 {len(cases)-real} 例是边界/反向构造）")
    return 0 if bad == 0 else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ledger")
    ap.add_argument("--strict", action="store_true", help="② 无本地凭据也算红")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()

    paths = ledgers(a.ledger)
    if not paths:
        print("★★ **未判，不是通过**：一个 source-ledger.jsonl 都没找到"
              f"（找的是 {CORPORA}/wip-*/workspaces/*/evidence/）")
        return 4

    rows, b = scan(paths)
    if a.json:
        print(json.dumps({"台账数": len(paths), "行数": rows,
                          "矛盾": b["矛盾"], "分界陈旧": b["陈旧"], "无据": b["无据"],
                          "出射程": b["出射程"], "通过": b["ok"], "非PD主张": b["非PD"]},
                         ensure_ascii=False, indent=1))
        return 1 if (b["矛盾"] or (a.strict and b["无据"])) else 0

    print(f"扫了 {len(paths)} 个台账 / {rows} 行　（分界 {PD_CUTOFF} = {THIS_YEAR} − 95，"
          f"可用最晚出版年 {LATEST_PD_YEAR}）\n")
    print(f"  ①a **自相矛盾**　{len(b['矛盾']):4d} 条　按今天的分界 {PD_CUTOFF} 也够不着——权利主张站不住")
    print(f"  ①b 分界陈旧　　　{len(b['陈旧']):4d} 条　接不住 rights 里的旧分界，**而今天确在 PD**")
    print(f"  ②  无本地凭据　　{len(b['无据']):4d} 条　按年份主张，而台账里没有四位年份")
    print(f"  ③  出射程　　　　{b['出射程']:4d} 条　写明了非年份依据 / 裸主张")
    print(f"     互相印证　　 {b['ok']:4d} 条　　　非 PD 主张 {b['非PD']} 条")

    if b["矛盾"]:
        print("\n✗ **①a 自相矛盾**（按今天的分界也够不着——权利主张站不住）：")
        for x in b["矛盾"]:
            print(f"  · {x['人']}／{x['source_id']}　published_at={x['published_at']!r}")
            print(f"      {x['title']}")
            print(f"      {x['为什么']}")
    if b["陈旧"]:
        print(f"\n⚠ **①b 分界陈旧** {len(b['陈旧'])} 条——**权利上没问题**，"
              f"重建台账就会写成 pre{PD_CUTOFF}：")
        for x in b["陈旧"]:
            print(f"  · {x['人']}／{x['source_id']}　published_at={x['published_at']!r}　{x['title']}")
    if b["无据"]:
        print(f"\n⚠ **② 无本地凭据** {len(b['无据'])} 条"
              f"{'（--strict 已开，计入红）' if a.strict else '（默认不算红）'}：")
        seen = {}
        for x in b["无据"]:
            seen.setdefault(x["人"], []).append(x["source_id"])
        for who, ids in seen.items():
            print(f"  · {who}　{len(ids)} 条　例 {ids[0]}")
    if not b["矛盾"]:
        print("\n✓ 没有自相矛盾的行")

    print("\n★ 射程：只比**台账自己写下的** rights 与 published_at 两个字段是否互相印证。"
          "\n  它**不**判「这份到底是不是公有领域」——那要看原书。"
          "\n  ③ 里的裸 `public-domain`（没写依据）本件够不着，是另一件的事。")
    return 1 if (b["矛盾"] or (a.strict and b["无据"])) else 0


if __name__ == "__main__":
    raise SystemExit(main())
