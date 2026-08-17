#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_attribution_tier_consistency.py —— **同一行里 `attribution` 与 `tier` 打架**

## 抓到它的那一次

2026-08-14，给 Brandeis #172 补 heuristic。六组候选**全部落空**，
去量语料构成才看见：他 `attribution=HIS-OWN` 那个池子里，
**32.0% 的词（358,987）`tier` 是 `S1`**。那两份是同一部

    1916《The case for the shorter work day … Bunting v. Oregon》
    creator: Frankfurter, Felix; Oregon, defendant; **Brandeis**; Bunting; Goldmark

**他排第 3 / 共 5**，而这是 Frankfurter 与 Goldmark 汇编的**法庭辩护状**。
台账把它同时标成 `HIS-OWN`（他的话）与 `S1`（二手），**两个字段互相否定**。

后果不是难看：我按 `attribution` 过滤去找「他自己说过的话」，
于是把 35.9 万词**别人汇编的材料**当成了他的声口 —— 六组候选里
「引 Gilbreth 的证词」「辩护状的目录行」「讲真的阳光与照明」全从这里来。

## 本件判什么

台账每一行，`attribution` 与 `tier` 必须指向同一件事：

| attribution | tier 允许 | 不允许 |
|---|---|---|
| `HIS-OWN`（他的话） | `P1`／`P2` | **`S1`／`S2`／`U`** |
| `OTHER`（别人的话） | `S1`／`S2`／`U` | **`P1`／`P2`** |

★ 它**不判哪一个字段是对的** —— 那要读书名页、看 creator 位次，是人的事。
  它只说「这两个字段在这一行上不能同时成立」。

## 它判不了什么（**必须一起念**）

0. ★★★ **`attribution` 有两代 schema，本件只判得了其中一半。**
   2026-08-14 实测：**25 个工作区是枚举**（`HIS-OWN`／`OTHER`，1,613 行），
   **28 个是散文**（那一栏写的是归属**理由**，如「整卷扫图，已切边界：她署名的报告在
   第 250–729 行……」，1,568 行 = **49.3%**）。
   `clash()` 拿字符串比 `HIS-OWN`／`OTHER`，对散文那一半**恒返回 None**——
   于是它们**一条也不会被报出来**，而屏幕上看不出区别。
   ⇒ 本件现在把两代的行数**分开印**；「N 行打架」这个数**只覆盖枚举那一半**。
   [[eval-artifacts-have-five-schemas]]。

1. **两个字段一致 ≠ 两个都对。** 一行标 `OTHER`＋`S1` 完全自洽，
   而它可能其实是他写的。本件对那种情况**一言不发**。
2. 它**不改台账**。存量按㊵冻结；本件是给**新人物**用的
   （㊸ 立的原则：新人物的流程该改就改）。

## 用法

    python3 check_attribution_tier_consistency.py
    python3 check_attribution_tier_consistency.py --self-test

退出码：0＝没有互相打架的行；2＝有（**逐行印出来，含 creator 位次**）
"""
import argparse
import glob
import json
import pathlib
import sys as _sys, pathlib as _pl
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent))
from workspace_roots import iter_workspaces  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
PD = HERE.parent.parent
CORPORA = PD / "_corpora"

PRIMARY = {"P1", "P2"}
SECONDARY = {"S1", "S2", "U"}

# ★★★ 2026-08-14：`clash()` 原来只认 `HIS-OWN`／`OTHER` 两个值，而
#   `build_source_ledger.py:61` 声明的合法值是**五个**：
#       HIS-OWN / CO-AUTHORED / THIRD-PARTY / ATTRIBUTION-UNCLEAR / OTHER-INVENTOR
#   **`OTHER` 根本不在 builder 的词表里**（数据里却有 108 行），
#   而 builder 声明的 `THIRD-PARTY`(4)／`CO-AUTHORED`(5)／`ATTRIBUTION-UNCLEAR`(1)
#   **我一条都没在判**——其中 `THIRD-PARTY` ＋ P1 正是本件要抓的那一种。
#   ⇒ 两套词表**取并集**，并把「他的话」与「不是他的话」分清。
OWN_VALUES = {"HIS-OWN"}
NOT_OWN_VALUES = {"OTHER", "THIRD-PARTY", "OTHER-INVENTOR"}
# CO-AUTHORED／ATTRIBUTION-UNCLEAR 是**中间态**：合著与存疑都可能配任一 tier，
# 本件对它们**不下判断**（下判断要读书名页，是人的事），但会单独计数印出来。
AMBIGUOUS_VALUES = {"CO-AUTHORED", "ATTRIBUTION-UNCLEAR"}


def clash(attribution, tier):
    """一行的两个字段是不是互相否定。→ 说明字符串或 None。**纯函数**。"""
    if attribution in OWN_VALUES and tier in SECONDARY:
        return f"标着「他的话」却记二手（tier={tier}）"
    if attribution in NOT_OWN_VALUES and tier in PRIMARY:
        return f"标着「不是他的话」（{attribution}）却记一手（tier={tier}）"
    return None


def creator_position(author: str, surname: str):
    """→ (他排第几, 共几位)。creator 栏是 `;` 分隔的。判不出来给 (None, n)。"""
    parts = [x.strip() for x in (author or "").split(";") if x.strip()]
    for i, a in enumerate(parts):
        if surname and surname.lower() in a.lower():
            return i + 1, len(parts)
    return None, len(parts)


def self_test() -> int:
    ok = t = 0

    def chk(d, c):
        nonlocal ok, t
        t += 1
        ok += 1 if c else 0
        print(f"  {'✓' if c else '✗'} {d}")

    chk("★ HIS-OWN ＋ S1 → 打架（Brandeis 那两份就是这个）",
        clash("HIS-OWN", "S1") is not None)
    chk("★ HIS-OWN ＋ U → 打架", clash("HIS-OWN", "U") is not None)
    chk("★ OTHER ＋ P1 → 打架（反方向）", clash("OTHER", "P1") is not None)
    chk("★★★ **THIRD-PARTY ＋ P1 → 打架** —— builder 声明的合法值，我原来一条都没判",
        clash("THIRD-PARTY", "P1") is not None)
    chk("★★ OTHER-INVENTOR ＋ P2 → 打架（同上，builder 词表里的）",
        clash("OTHER-INVENTOR", "P2") is not None)
    chk("★★ 反例：**CO-AUTHORED 是中间态，不下判断**（合著配任一 tier 都讲得通）",
        clash("CO-AUTHORED", "P1") is None and clash("CO-AUTHORED", "S1") is None)
    chk("★★ 反例：ATTRIBUTION-UNCLEAR 同样不下判断", clash("ATTRIBUTION-UNCLEAR", "P1") is None)
    chk("★ THIRD-PARTY ＋ S1 → 不报（这本来就是自洽的）", clash("THIRD-PARTY", "S1") is None)
    chk("★ 反例：HIS-OWN ＋ P1 → 不报", clash("HIS-OWN", "P1") is None)
    chk("★ 反例：OTHER ＋ S1 → 不报", clash("OTHER", "S1") is None)
    chk("★★ 反例：两个字段一致**不代表两个都对** —— OTHER＋S1 自洽，"
        "而它可能其实是他写的；本件对这种情况一言不发",
        clash("OTHER", "S1") is None)
    _ENUM={"HIS-OWN","OTHER","UNKNOWN",None,""}
    _is_prose=lambda a: isinstance(a,str) and a not in _ENUM and len(a)>24
    chk("★★★ **散文型 attribution 认得出来**（老台账把归属理由写在这一栏）",
        _is_prose("**整卷扫图，已切边界**：她署名的报告在第 250–729 行，末行 CLARA BARTON。"))
    chk("★ 反例：枚举值不算散文", not _is_prose("HIS-OWN") and not _is_prose("OTHER"))
    chk("★ 反例：短字符串不算散文（免得把手滑写的短标记当成理由）", not _is_prose("his own"))
    chk("★★ 散文型走 clash() 恒 None —— **本件对它一言不发，这正是要印出来的射程**",
        clash("**整卷扫图，已切边界**：她署名的报告在第 250–729 行……", "S1") is None)
    chk("★ 反例：字段缺失不许当成打架", clash(None, None) is None and clash("HIS-OWN", None) is None)
    p, n = creator_position(
        "Frankfurter, Felix; Oregon, defendant; Brandeis, Louis Dembitz; Bunting; Goldmark",
        "Brandeis")
    chk(f"★ creator 位次：Brandeis 排第 {p}/{n}（实测那份就是 3/5）", (p, n) == (3, 5))
    p2, n2 = creator_position("Dewey, John", "Brandeis")
    chk(f"★ 反例：名字不在 creator 里 → 位次 None（实得 {p2}）", p2 is None)
    # ── ★★★ 2026-08-17：「HIS-OWN 靠什么撑着」这一档的正反对照 ──
    #   实测：全库 14 行打架，**14/14 的署名证据是 `['ia-creator-field']`**。
    #   ★ 反对照要有：**有别的署名证据的行，不许被套用这条结论**（否则等于放宽）。
    _only_cf = lambda ev: list(ev) == ["ia-creator-field"]
    chk("★★★ 只有 `ia-creator-field` → 归入「证据只有 creator 栏」",
        _only_cf(["ia-creator-field"]))
    chk("★★★ 反对照：还有 `A-byline` → **不归入**（这行仍要人读书名页）",
        not _only_cf(["ia-creator-field", "A-byline"]))
    chk("★★★ 反对照：单独一条 `A-byline` → **不归入**",
        not _only_cf(["A-byline"]))
    chk("★★★ 反对照：**一条证据都没有** → 也**不归入**（那是另一类：无证据）",
        not _only_cf([]))
    # ★★ 真实数据兜底：这一档在全库上的实测值必须能现算出来，且**不许为 0**
    #   （为 0 说明我把字段名读错了，而不是「问题没了」）。
    try:
        import subprocess as _sp, sys as _sys
        _o = _sp.run([_sys.executable, str(pathlib.Path(__file__).resolve())],
                     capture_output=True, text=True).stdout
        # ★ 断言要打在**那个数**上，不是打在标签上 —— 标签在计数为 0 时照样印。
        #   变异对照当场拆穿：把字段名改成不存在的 `evidence`，计数变 0 而标签还在，
        #   旧写法照样绿。[[read-the-hits-before-reporting-the-rate]]
        #
        # ★★★ 而这条断言**不许钉死「14/14」** —— 我上一步就把那 14 行改掉了，
        #   钉死的数会被我自己的下一次交付当场证伪。写成**判别式**：
        #     有打架的行 ⇒ 那个数必须解析得出、且 creator-only 那档要能数出来；
        #     一行都没有 ⇒ 本档不该出现，**那是通过，不是缺陷**。
        #   [[claims-my-own-next-delivery-falsifies]]
        import re as _re
        # ★ 正则按**源码里的格式串**写，别照记忆猜：那句是
        #   f"...互相否定的：**{N} 行**，分布在 **{M}** 个工作区" —— `行` 在粗体**里面**。
        _clash = _re.search(r"互相否定的：\*\*(\d+) 行\*\*", _o)
        _tot = int(_clash.group(1)) if _clash else None
        _m = _re.search(r"其中 \*\*(\d+)/(\d+)\*\* 行的 `attribution=HIS-OWN`", _o)
        if _tot == 0:
            chk("★★★ 真跑一次：全库 **0 行打架** ⇒ 本档不出现（这是通过，不是缺陷）",
                _m is None and "✓ 没有互相否定的行" in _o)
        else:
            _n, _d = (int(_m.group(1)), int(_m.group(2))) if _m else (None, None)
            chk(f"★★★ 真跑一次：有 {_tot} 行打架 ⇒ 这一档必须数得出来"
                f"（实得 {_n}/{_d}；读错字段名会让它变 0 而标签还在）",
                _n is not None and _d == _tot)
    except Exception as _e:                                       # noqa: BLE001
        chk(f"★★★ 真跑一次**未判**（跑不起来：{_e}）", False)

    print(f"\n{'✓ 全过' if ok == t else f'✗ {t - ok}/{t} 项不符'}")
    return 0 if ok == t else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()

    total = 0
    enum_rows = prose_rows = 0
    enum_ws = prose_ws = 0
    hits = []
    ENUM = {"HIS-OWN", "OTHER", "UNKNOWN", None, ""}
    judged = [0, 0, 0]   # [能判, 中间态, 缺失/不认识]
    for d in [str(_w) for _w in iter_workspaces(CORPORA)]:
        ws = pathlib.Path(d)
        led = ws / "evidence/source-ledger.jsonl"
        if not led.is_file():
            continue
        meta = ws / "meta.json"
        surname = ""
        if meta.is_file():
            try:
                surname = (json.loads(meta.read_text(encoding="utf-8")).get("name") or "").split()[-1]
            except (ValueError, IndexError):
                pass
        bad = []
        _prose = 0
        for line in led.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            total += 1
            _a = r.get("attribution")
            if isinstance(_a, str) and _a not in ENUM and len(_a) > 24:
                _prose += 1          # ★ 散文型：本件对它一言不发
            elif _a in OWN_VALUES or _a in NOT_OWN_VALUES:
                judged[0] += 1       # ★ 真正能判的
            elif _a in AMBIGUOUS_VALUES:
                judged[1] += 1       # 中间态：认得出但有意不判
            else:
                judged[2] += 1       # 缺失／不认识
            why = clash(_a, r.get("tier"))
            if why:
                pos, n = creator_position(r.get("author"), surname)
                # ★★★ 2026-08-17：把**这条 HIS-OWN 是靠什么撑起来的**一并带出来。
                #   全库 14 行打架，**14 行的署名证据全是 `['ia-creator-field']`**（现算）。
                #   而本项目已实测「**creator 栏有名字 ≠ 他写的**」——五种污染源，
                #   Michelangelo 那一族正是「画册把艺术家挂成 creator」（实测 23%）。
                #   ⇒ 这不是「要人去读书名页」，是**本仓早已定过的一类**。
                #   [[creator-field-is-not-authorship]]｜[[art-books-list-the-artist-as-creator]]
                _ev = list(r.get("authorship_evidence") or r.get("evidence_kinds") or [])
                bad.append((r.get("source_id"), r.get("split"), why, pos, n,
                            (r.get("title") or "")[:38], _ev))
        if _prose:
            prose_ws += 1
            prose_rows += _prose
        else:
            enum_ws += 1
        if bad:
            hits.append((ws.name, bad))

    print(f"★★ **`attribution` 两代 schema**：枚举型 {enum_ws} 个工作区｜"
          f"**散文型 {prose_ws} 个（{prose_rows} 行，占 {100*prose_rows/total:.1f}%）** —— "
          f"散文那一半 `clash()` 恒返回 None，**下面这个数只覆盖枚举那一半**")
    print(f"★★ **本件真正判得了多少行**：能判 **{judged[0]}**（{100*judged[0]/total:.1f}%）"
          f"｜中间态有意不判 {judged[1]}（CO-AUTHORED／ATTRIBUTION-UNCLEAR）"
          f"｜散文型 {prose_rows}｜缺失或不认识 {judged[2]}")
    print(f"   ⇒ 下面那个「N 行打架」的**分母是 {judged[0]}，不是 {total}**。"
          f"「只有 N 行」**不等于**「全库只有 N 个问题」。")
    print(f"全库台账 **{total}** 行；`attribution` 与 `tier` 互相否定的："
          f"**{sum(len(b) for _, b in hits)} 行**，分布在 **{len(hits)}** 个工作区")
    # ★★★ 打架的行里，**HIS-OWN 只靠 `ia-creator-field` 撑着**的单独数出来。
    _all_bad = [row for _, b in hits for row in b]
    _only_cf = [row for row in _all_bad if row[6] == ["ia-creator-field"]]
    if _all_bad:
        print(f"★★★ 其中 **{len(_only_cf)}/{len(_all_bad)}** 行的 `attribution=HIS-OWN` "
              f"**只有 `ia-creator-field` 一条证据**。")
        print("   本仓已实测：**creator 栏有名字 ≠ 他写的**（五种污染源：同名者／藏书票／"
              "书信方向／编者层／托名伪作；画册把艺术家挂成 creator 实测 23%）。")
        print("   ⇒ 这些行**该改的是 `attribution`，不是 `tier`** —— `tier_reason` 那一侧"
              "写着具体理由（无出版年、名言图导出、facsimile 画册），是有依据的一侧。")
        if len(_only_cf) < len(_all_bad):
            print(f"   ★ 另 **{len(_all_bad) - len(_only_cf)}** 行有别的署名证据，"
                  f"**那几行仍要人读书名页**——不适用上面这条。")
    print("★ 本件**不替你改字段**，也不判 tier 那一侧对不对；"
          "只把「两个不能同时成立」和「HIS-OWN 靠什么撑着」摆出来。\n")
    for name, bad in hits:
        print(f"❌ {name}（{len(bad)} 行）")
        for sid, sp, why, pos, n, ti, ev in bad:
            where = f"creator 里他排第 {pos}/{n}" if pos else (f"creator 共 {n} 位，**没有他**" if n else "无 creator")
            tag = "**证据只有 creator 栏**" if ev == ["ia-creator-field"] else (
                  "**无任何署名证据**" if not ev else "证据：%s" % "／".join(ev))
            print(f"     {sid} split={sp} —— {why}；{where}；{tag}　《{ti}》")
    if not hits:
        print("✓ 没有互相否定的行")
    return 2 if hits else 0


if __name__ == "__main__":
    raise SystemExit(main())
