#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_impossible_by_lifespan.py —— **出版年早于他出生 ⇒ 不可能是他**

## 为什么有这件

Henry Ford #188 探源，`creator:"Ford, Henry"` 的池子里**至少五个人**：

    Ford, Henry Jones (1851–1925)     历史学家，PD 内 96 条（70.6%）
    Ford, Henry, 1863-1947            ★ 工业家本人，10 条（7.4%）
    Ford, Henry Justice (1860–1941)   安德鲁·朗童话集的插画家
    Ford, Henry A.（编县志的）        《History of Hamilton County, Ohio》1881
    Worthington Chauncey Ford         第五个

**年代筛不掉他们**：这几位卒年都在 1925–1941，作品同期、同样在公有领域。
逐个枚举同名者能删掉大部分，但**枚举永远不全**——删到只剩 22 条时，
里面还有 1856《Observations on the fevers of the west coast of Africa》
与 1860《The history of Putnam and Marshall counties》。

★★ 而这两条根本不需要认识是谁：**它们出版时他还没出生。**

## 判什么

给定人物的**出生年**，报出 `published_at < birth_year` 的每一条。
这条规则**对每个人都成立**，不依赖认不认识那些同名者，
所以它是枚举式排除之外的**另一道**，不是替代。

★ **不判「晚于卒年」**：身后出版是常态（文集、遗稿、译本、重印），
  卒年那一侧不能用同样的力度判。本件只管出生这一侧——
  [[counts-need-their-cutoff-stated]]：说清楚只管哪一侧。

★★ 边界留一岁：`published_at < birth_year` 才报，等于出生年不报
  （编目年份常有一年的误差）。

## 用法

    python3 check_impossible_by_lifespan.py --ledger <source-ledger.jsonl> --born 1863
    python3 check_impossible_by_lifespan.py --tsv <探源.tsv> --born 1863     # 抓源之前就能用
    python3 check_impossible_by_lifespan.py --self-test

退出码：0＝没有不可能项；1＝有；2＝参数不对；5＝没有年份可判（**未判，不是通过**）
"""
import argparse
import csv
import io
import json
import pathlib
import re
import sys

YEAR = re.compile(r"(1[0-9]\d\d|20\d\d)")


def year_of(rec: dict):
    for k in ("published_at", "pub_year", "year", "date", "publicdate"):
        v = rec.get(k)
        if v in (None, ""):
            continue
        m = YEAR.search(str(v))
        if m:
            return int(m.group(1))
    return None


def load(ledger=None, tsv=None):
    if ledger:
        return [json.loads(l) for l in pathlib.Path(ledger).read_text(encoding="utf-8").splitlines() if l.strip()]
    lines = [l for l in pathlib.Path(tsv).read_text(encoding="utf-8").splitlines(True) if not l.startswith("#")]
    return list(csv.DictReader(io.StringIO("".join(lines)), delimiter="\t"))


def evaluate(rows, born: int):
    dated = [(r, y) for r in rows if (y := year_of(r)) is not None]
    bad = [(r, y) for r, y in dated if y < born]
    return {
        "条数": len(rows), "有年份": len(dated), "无年份": len(rows) - len(dated),
        "出生年": born,
        "**出版年早于出生年**": len(bad),
        "逐条": [{"年": y, "identifier": r.get("identifier") or r.get("source_id") or "?",
                  "creator": (r.get("creator") or "")[:60],
                  "title": (r.get("title") or "")[:78]} for r, y in sorted(bad, key=lambda x: x[1])],
    }


def self_test() -> int:
    """正反对照。★ 反例必须是**真的**：逐字取自 Ford #188 的探源池。"""
    rows = [
        {"identifier": "a", "year": "1856", "creator": "Ford, Henry",
         "title": "Observations on the fevers of the west coast of Africa"},
        {"identifier": "b", "year": "1860", "creator": "Ford, Henry A., comp",
         "title": "The history of Putnam and Marshall counties"},
        {"identifier": "c", "year": "1922", "creator": "Ford, Henry, 1863-1947",
         "title": "My life and work"},
        {"identifier": "d", "year": "1863", "creator": "Ford, Henry",
         "title": "边界：出生当年，**不报**"},
        {"identifier": "e", "creator": "Ford, Henry", "title": "没有年份，不该被算成通过"},
    ]
    r = evaluate(rows, 1863)
    bad = 0
    ok1 = r["**出版年早于出生年**"] == 2
    bad += 0 if ok1 else 1
    print(f"  {'✓' if ok1 else '✗'} 反例：1856／1860 两条必须报出（实得 {r['**出版年早于出生年**']}）")
    got = {x["identifier"] for x in r["逐条"]}
    ok2 = got == {"a", "b"}
    bad += 0 if ok2 else 1
    print(f"  {'✓' if ok2 else '✗'} 正例：1922 与**出生当年 1863** 都不许被报（实得报出 {sorted(got)}）")
    ok3 = r["无年份"] == 1
    bad += 0 if ok3 else 1
    print(f"  {'✓' if ok3 else '✗'} 无年份的单列为「无年份」，**不算通过**（实得 {r['无年份']}）")

    # ★ 反方向：把出生年改早，两条反例必须变绿——否则说明它报的不是「早于出生」
    r2 = evaluate(rows, 1800)
    ok4 = r2["**出版年早于出生年**"] == 0
    bad += 0 if ok4 else 1
    print(f"  {'✓' if ok4 else '✗'} 把出生年改成 1800 之后必须一条都不报"
          f"（实得 {r2['**出版年早于出生年**']}）——防止它其实是在报别的东西")
    print(f"\n{'✓ 正负对照全过' if bad == 0 else f'✗ {bad} 项不符'}（反例逐字取自 Ford #188 探源池）")
    return 0 if bad == 0 else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ledger")
    ap.add_argument("--tsv")
    ap.add_argument("--born", type=int)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not (a.ledger or a.tsv) or a.born is None:
        print("要么 --self-test，要么给 --born 加上 --ledger 或 --tsv", file=sys.stderr)
        return 2
    rows = load(a.ledger, a.tsv)
    r = evaluate(rows, a.born)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=1))
    else:
        print(f"条数 {r['条数']}｜有年份 {r['有年份']}｜**无年份 {r['无年份']}**（那一批本件判不了）")
        if r["**出版年早于出生年**"]:
            print(f"\n✗ **{r['**出版年早于出生年**']} 条出版年早于他出生（{a.born}）——不可能是他**：")
            for x in r["逐条"]:
                print(f"  · {x['年']}  {x['identifier']}")
                print(f"      {x['creator']} ｜ {x['title']}")
        else:
            print(f"\n✓ 没有出版年早于 {a.born} 的条目")
        print("\n★ 射程：**只管出生这一侧**。身后出版是常态（文集/遗稿/译本/重印），"
              "卒年那一侧不能用同样的力度判。无年份的那一批**未判，不是通过**。")
    if r["有年份"] == 0:
        return 5
    return 1 if r["**出版年早于出生年**"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
