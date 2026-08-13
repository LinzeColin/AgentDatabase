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
    python3 check_impossible_by_lifespan.py --scan-all      # 全库回扫（生年取自 _卒年.json）
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
import sys as _sys, pathlib as _pl
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent))
from workspace_roots import iter_workspaces  # noqa: E402

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


# ★★★ 「出版早于出生」是**事实**，不一定是**缺陷**。
# Jefferson #175 实测：台账里有一本 **1684** 年的书（他生于 1743，早 59 年），
# 而那一条**早就判对了**——`tier: S1`、`attribution: OTHER`、
# 归属依据写着 `creator 里目标的角色是 former owner`：
# **那是他藏书室里的书，不是他写的**。
# ⇒ 若不分开这两种，本件就会把「判据已经做对的事」报成缺陷
#   （[[checker-blindspot-read-as-defect]]：判据的盲区被我当成缺陷）。
SECONDARY_TIERS = {"S1", "S2", "secondary", "二手"}
NOT_AUTHOR_MARKS = ("other", "former owner", "藏书", "旧主", "collector")


def already_handled(rec: dict) -> str:
    """这一条是不是**已经被判成不是他写的**？→ 说明，或空串。"""
    if str(rec.get("tier") or "").strip() in SECONDARY_TIERS:
        blob = (str(rec.get("attribution") or "") + " " +
                str(rec.get("authorship_detail") or "") + " " +
                str(rec.get("author") or "")).lower()
        for m in NOT_AUTHOR_MARKS:
            if m in blob:
                return f"已判二手且归属标「{m}」"
        return "已判二手"
    return ""


def evaluate(rows, born: int):
    dated = [(r, y) for r in rows if (y := year_of(r)) is not None]
    early = [(r, y) for r, y in dated if y < born]
    real, noted = [], []
    for r, y in early:
        (noted if already_handled(r) else real).append((r, y))

    def fmt(pairs):
        return [{"年": y, "identifier": r.get("identifier") or r.get("source_id") or "?",
                 "creator": (r.get("creator") or r.get("author") or "")[:60],
                 "title": (r.get("title") or "")[:78],
                 "已有处置": already_handled(r)}
                for r, y in sorted(pairs, key=lambda x: x[1])]

    return {
        "条数": len(rows), "有年份": len(dated), "无年份": len(rows) - len(dated),
        "出生年": born,
        "出版年早于出生年": len(early),
        "**仍判成他的（真缺陷）**": len(real),
        "★ 已判二手/非作者（只是提示，不算缺陷）": len(noted),
        "逐条": fmt(real),
        "★ 逐条·已处置": fmt(noted),
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
    ok1 = r["**仍判成他的（真缺陷）**"] == 2
    bad += 0 if ok1 else 1
    print(f"  {'✓' if ok1 else '✗'} 反例：1856／1860 两条必须报出（实得 {r['**仍判成他的（真缺陷）**']}）")
    got = {x["identifier"] for x in r["逐条"]}
    ok2 = got == {"a", "b"}
    bad += 0 if ok2 else 1
    print(f"  {'✓' if ok2 else '✗'} 正例：1922 与**出生当年 1863** 都不许被报（实得报出 {sorted(got)}）")
    ok3 = r["无年份"] == 1
    bad += 0 if ok3 else 1
    print(f"  {'✓' if ok3 else '✗'} 无年份的单列为「无年份」，**不算通过**（实得 {r['无年份']}）")

    # ★★ Jefferson #175 那条真记录：早于出生 **59 年**，而**判据早就判对了**
    #   （tier S1 + former owner）⇒ 必须落进「已处置」，**不许报成缺陷**。
    jeff = [{"source_id": "src-96915834ac95", "published_at": "1684", "tier": "S1",
             "attribution": "OTHER",
             "author": "Courtilz de Sandras, Gatien, 1644-1712; Jefferson, Thomas, 1743-1826, former owner",
             "title": "Histoire des promesses illusoires depuis la Paix des Pirenees"}]
    rj = evaluate(jeff, 1743)
    ok5 = rj["**仍判成他的（真缺陷）**"] == 0 and rj["★ 已判二手/非作者（只是提示，不算缺陷）"] == 1
    bad += 0 if ok5 else 1
    print(f"  {'✓' if ok5 else '✗'} Jefferson 那本 1684 年的藏书：**已判二手 + former owner** ⇒ "
          f"只算提示不算缺陷（实得 真缺陷 {rj['**仍判成他的（真缺陷）**']}／已处置 "
          f"{rj['★ 已判二手/非作者（只是提示，不算缺陷）']}）")

    # ★ 反方向：把出生年改早，两条反例必须变绿——否则说明它报的不是「早于出生」
    r2 = evaluate(rows, 1800)
    ok4 = r2["**仍判成他的（真缺陷）**"] == 0
    bad += 0 if ok4 else 1
    print(f"  {'✓' if ok4 else '✗'} 把出生年改成 1800 之后必须一条都不报"
          f"（实得 {r2['**仍判成他的（真缺陷）**']}）——防止它其实是在报别的东西")
    print(f"\n{'✓ 正负对照全过' if bad == 0 else f'✗ {bad} 项不符'}（反例逐字取自 Ford #188 探源池）")
    return 0 if bad == 0 else 1


# ★ 全库回扫：生年取自 `_ledgers/_卒年.json`（204 人、每条带出处与置信度）。
#   没有调用方的判据不算做完 —— 这就是它的调用方。
BORN_FILE = pathlib.Path(__file__).resolve().parents[1] / "_卒年.json"
CORPORA = pathlib.Path(__file__).resolve().parents[2] / "_corpora"


def _norm(s: str) -> str:
    """归一姓名用于比对。★ **去掉单字母中间名**：工作区 slug 写 `walter-a-shewhart`，
    而生年表写 `Walter Shewhart` —— 第一版因此把他报成「对不上生年」，
    而那不是数据缺，是我的匹配太窄。"""
    import unicodedata
    s = unicodedata.normalize("NFKD", s.lower()).replace("-", " ")
    toks = [w for w in re.split(r"[^a-z]+", s) if w and len(w) > 1]
    return "".join(toks)


def scan_all():
    if not BORN_FILE.exists():
        print(f"★★ **未跑，不是通过**：读不到生年表 {BORN_FILE}")
        return 5
    born = json.loads(BORN_FILE.read_text(encoding="utf-8"))
    BY = {_norm(v["name"]): v for v in born.values() if isinstance(v, dict) and v.get("born")}
    # ★ 两种「判不了」必须分开报，它们的处置完全不同
    #   （[[empty-default-swallows-unknown]]：混成一句就都成了「未判」）：
    #     ① 生年表里**有这个人但 born 是 null** —— 生年本来就未知（Carver、Pacioli）
    #     ② 生年表里**根本没有这个人** —— 该补表
    real, noted, no_born, no_person, scanned = [], [], [], [], 0
    for led in sorted(_w / "evidence" / "source-ledger.jsonl"
                      for _w in iter_workspaces(CORPORA)
                      if (_w / "evidence" / "source-ledger.jsonl").is_file()):
        slug = led.parent.parent.name
        key = _norm(slug)
        cand = [v for k, v in BY.items() if k == key or key in k or k in key]
        if not cand:
            # 分辨「表里有人但没生年」与「表里根本没这个人」
            allp = {_norm(v["name"]): v for v in born.values() if isinstance(v, dict)}
            hit = [v for k, v in allp.items() if k == key or key in k or k in key]
            (no_born if hit else no_person).append(slug)
            continue
        rows = [json.loads(l) for l in led.read_text(encoding="utf-8").splitlines() if l.strip()]
        r = evaluate(rows, cand[0]["born"])
        scanned += 1
        if r["**仍判成他的（真缺陷）**"]:
            real.append((slug, cand[0]["born"], r))
        if r["★ 已判二手/非作者（只是提示，不算缺陷）"]:
            noted.append((slug, cand[0]["born"], r))
    print(f"扫过 {scanned} 个工作区｜"
          f"**生年未知 {len(no_born)} 个｜生年表里没有 {len(no_person)} 个**（都是未判，不是通过）")
    if real:
        print(f"\n✗ **{len(real)} 个工作区有「早于出生且仍判成他的」条目**：")
        for slug, b, r in real:
            print(f"  · {slug}（生 {b}）：{r['**仍判成他的（真缺陷）**']} 条")
            for x in r["逐条"][:4]:
                print(f"      {x['年']}  {x['title'][:62]}")
    else:
        print("\n✓ 没有「早于出生且仍判成他的」条目")
    if noted:
        print(f"\n★ 早于出生但**判据已经判对**的（不算缺陷，列出来让人看见）：{len(noted)} 个工作区")
        for slug, b, r in noted:
            for x in r["★ 逐条·已处置"][:2]:
                print(f"  · {slug}　{x['年']}　{x['title'][:52]}　[{x['已有处置']}]")
    if no_born:
        print(f"\n⚠ **生年本来就未知**（生年表里有这个人，`born` 是 null）：{no_born}")
        print("   ⇒ 这一类**补不了**，本件对它们永远判不了；不是缺陷，也不是通过。")
    if no_person:
        print(f"\n⚠ **生年表里没有这个人**：{no_person}")
        print("   ⇒ 这一类**补得了**：往 `_ledgers/_卒年.json` 加一条（要带出处）。")
    return 1 if real else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scan-all", action="store_true", help="全库回扫，生年取自 _卒年.json")
    ap.add_argument("--ledger")
    ap.add_argument("--tsv")
    ap.add_argument("--born", type=int)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.scan_all:
        return scan_all()
    if not (a.ledger or a.tsv) or a.born is None:
        print("要么 --self-test，要么给 --born 加上 --ledger 或 --tsv", file=sys.stderr)
        return 2
    rows = load(a.ledger, a.tsv)
    r = evaluate(rows, a.born)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=1))
    else:
        print(f"条数 {r['条数']}｜有年份 {r['有年份']}｜**无年份 {r['无年份']}**（那一批本件判不了）")
        if r["**仍判成他的（真缺陷）**"]:
            print(f"\n✗ **{r['**仍判成他的（真缺陷）**']} 条出版年早于他出生（{a.born}）、且仍判成他的——不可能是他**：")
            for x in r["逐条"]:
                print(f"  · {x['年']}  {x['identifier']}")
                print(f"      {x['creator']} ｜ {x['title']}")
        else:
            print(f"\n✓ 没有「早于 {a.born} 且仍判成他的」条目")
        if r["★ 已判二手/非作者（只是提示，不算缺陷）"]:
            print(f"\n★ 早于出生但**已判二手/非作者**的：{r['★ 已判二手/非作者（只是提示，不算缺陷）']} 条"
                  "（**不算缺陷**——判据已经做对了，这里只列出来让人看见）")
            for x in r["★ 逐条·已处置"]:
                print(f"  · {x['年']}  {x['title'][:62]}　[{x['已有处置']}]")
        print("\n★ 射程：**只管出生这一侧**。身后出版是常态（文集/遗稿/译本/重印），"
              "卒年那一侧不能用同样的力度判。无年份的那一批**未判，不是通过**。")
    if r["有年份"] == 0:
        return 5
    return 1 if r["**仍判成他的（真缺陷）**"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
