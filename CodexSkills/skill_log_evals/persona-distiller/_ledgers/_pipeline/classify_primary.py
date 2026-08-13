#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一手／二手分类 —— 定 `一手占比` 那一项。阶段 2 的第二件。

用法：
    python3 classify_primary.py --raw <raw 目录> --surname <目标姓> [--surname 别拼法]…

**核心难点（不是模板能解决的）：**
`Life of George Washington` **是 Marshall 写的 ⇒ 一手**；
`Life of Lincoln`          **是别人写他的 ⇒ 二手**。
同一个「Life of」模式，两个方向。所以本工具的判法是
**「二手标记词 + 目标姓名」同时出现才判二手**，只有标记词不算。

**三个桶，`需人判` 不许默认成一手**
（[[empty-default-swallows-unknown]]：`[]`／`0 个` 都会被读成「没问题」；
 最坏一次静默丢掉的两席恰好同质，delta 从 −0.16 变 +0.25）。

★ 教训来源：Liebig #124 有 9 份「与他有关但不是他写的」混进一手，
  占比从 0.7419 掉到 0.5192，而门**只做分档字段的算术，不问分档对不对**
  （[[related-to-him-is-not-written-by-him]]）。

★ 退出码：0=跑完；2=参数错；3=没有可分类的文件。
"""
import argparse
import json
import pathlib
import re
import sys

# 「**别人在写他**」的标记词。★ 必须与目标姓名同现才算数。
# ★★ `biograph` 写成裸串会匹配 `autobiography` —— 子串包含，
#   与 `lister`⊂`callister`、`A.L.S`⊂德语 `als` 同型
#   （[[regex-must-clear-the-corpus-language]]）。实测后果：
#   Bismarck《思考与回忆》3 份、Fröbel 自传 6 份、Jefferson 文集 6 份，
#   **共 15 份自著被判成「别人写他的」**，Jefferson 一手占比 0.9655 被压到 0.7586。
#   ⇒ 这里用负向后顾断言 `(?<!auto)biograph`。
ABOUT = [
    r"life of", r"lives of", r"(?<!auto)biograph", r"anecdotes? of",
    r"a study of", r"sketch(es)? of", r"eulog", r"tribute to",
    r"and his (time|work|life|educational)", r"his life and", r"the man ",
    r"stories of", r"wit and wisdom",
    r"leben (des|von)", r"erinnerungen an",
    r"vita di", r"la vie de",
]

# ★★★ 2026-08-13 Michelangelo #185 新增：**画册／图版集**。
# 起因：他一轮里查出 **10 份**「不是他写的」被判成一手，其中 9 份是同一形态——
# **关于艺术家的画册，IA 的 creator 首位就是那位艺术家**，于是位次、姓名同现全都判不出来。
#   · Fisher 的 5 本蚀刻摹本册（`ETCHED BY JOSEPH FISHER` ＋ 出版者 `INTRODUCTION`）
#   · Knapp《reproduced in one hundred and sixty-nine illustrations》（第三人称叙事）
#   · 《Sixty outlines from the principal works of…》（图版说明目录）
#   · 《Michelangelo as a painter》（Masters in Art 丛书）
#   · 《Oeuvres complètes …et choix de Baccio Bandinelli et de Daniel de Volterre》（版画集）
#
# ★★ **归「需人判」，不直接判二手。** 理由：`Opere`／`Oeuvres complètes` 这类题名
# 既可能是画册也可能是他的文集，**判据分不出来，人读一眼正文就分得出**。
# 直接判二手会误伤真文集（Machiavelli 的《Opere》就是他的著作）。
# [[empty-default-swallows-unknown]]：说不准的要进独立的一档，不许并进任何一边。
PLATE_ALBUM = [
    r"etched fac[- ]?similes?", r"facsimiles of original studies",
    r"\boutlines from\b", r"reproduced in .{0,20}illustrations",
    r"\bin \d+ (illustrations|abbildungen|plates)\b", r"des meisters werke",
    r"\bas a painter\b", r"\bas a sculptor\b",
    r"\bplates?\b.{0,20}\bafter\b", r"\bafter the original (studies|drawings)\b",
]
# 「**他自己在回忆**」的标记词 —— 这些词单看像「写他」，实为自述体。
# ★ 判法：SELF_NARRATIVE ＋ 目标是第一作者 ⇒ **一手**，不进 ABOUT。
SELF_NARRATIVE = [
    r"autobiograph", r"reminiscence", r"memoirs?\b", r"confessions",
    r"erinnerungen", r"gedanken und", r"selbstbiographie",
]
# 「是他自己的话」的标记词（只作辅助证据，不单独定案）
BYSELF = [
    r"works", r"writings", r"letters", r"correspondence", r"speeches", r"addresses",
    r"autobiograph", r"complete works", r"select(ed)? works", r"papers",
    r"s[äa]mtliche", r"schriften", r"reden", r"briefe", r"briefwechsel", r"gedanken",
    r"opere", r"lettere", r"scritti", r"discorsi",
    r"[oœ]uvres", r"correspondance", r"confessions", r"discours",
]


def as_text(v) -> str:
    """★ IA 的 creator／title **可能是 list**（多值字段）。
    直接 .lower() 会 AttributeError；而更坏的写法是 `str(v)`——那会把
    `['A','B']` 变成带方括号的串，位置判断随之错位。这里显式按 `; ` 连。"""
    if isinstance(v, list):
        return "; ".join(str(x) for x in v)
    return str(v or "")


def classify(title, creator, surnames: list) -> tuple:
    t = as_text(title).lower()
    c = as_text(creator).lower()
    sn = [s.lower() for s in surnames]
    has_name_in_title = any(s in t for s in sn)
    about_hit = next((p for p in ABOUT if re.search(p, t)), "")
    self_narr = next((p for p in SELF_NARRATIVE if re.search(p, t)), "")
    self_hit = next((p for p in BYSELF if re.search(p, t)), "")
    # 目标在 creator 里的位置：第一位 → 多半是著者；靠后 → 多半是编者/传主/藏书主
    parts = [p.strip() for p in c.split(";") if p.strip()]
    pos = next((i for i, p in enumerate(parts) if any(s in p for s in sn)), -1)

    # ⓪ 自述体 + 目标是第一作者 ⇒ 一手。**必须排在 ① 之前**：
    #    《Bismarck, the man and the statesman; being the reflections and
    #     reminiscences of Otto, Prince von Bismarck》题名里既有他的姓名、
    #    又有 reminiscence，按 ① 会判成二手，而它是他本人的回忆录。
    if self_narr and pos == 0:
        return "一手", f"题名含自述体标记「{self_narr}」且目标为第一作者"
    # ①b ★ 画册／图版集 ⇒ **需人判**（不直接判二手，见 PLATE_ALBUM 的注释）
    plate = next((q for q in PLATE_ALBUM if re.search(q, t)), "")
    if plate:
        return "需人判", f"题名像**画册/图版集**（命中「{plate}」）——关于艺术家的画册，creator 首位常就是他本人，位次与姓名同现都判不出来。**去读一眼正文再定**"
    # ① 标记词 + 目标姓名同现 ⇒ 二手（这是唯一的强判据）
    if about_hit and has_name_in_title:
        return "二手", f"题名含「{about_hit}」且含目标姓名"
    # ② 目标不在 creator 里 ⇒ 二手
    if pos < 0:
        return "二手", "目标不在 creator 字段里"
    # ②b **角色是藏书主而不是作者** ⇒ 二手。
    #    IA 的 creator 段带角色限定词（`former owner`／`ed`／`tr`／`comp`／`author`）。
    #    这正是 Lincoln #174 探源切出的第二种污染（藏书票／传主），
    #    实测 Jefferson 有一份 Courtilz de Sandras 的书把他记成 `former owner`。
    #    ★ **位次判不出这个**——他可能排第 1 位而角色仍是藏书主。
    seg = parts[pos]
    if "former owner" in seg or "bookplate" in seg:
        return "二手", "creator 里目标的角色是 **former owner（藏书主）**，不是作者"
    # ③ 目标是第一作者 + 自著标记词 ⇒ 一手
    if pos == 0 and self_hit:
        return "一手", f"目标为第一作者，题名含「{self_hit}」"
    # ④ 目标是第一作者、题名无任何标记 ⇒ 一手（作品本名，如《Orbis pictus》）
    if pos == 0 and not about_hit:
        return "一手", "目标为第一作者，题名无「写他」的标记"
    # ⑤ 其余一律进「需人判」——**不许默认成一手**
    return "需人判", (f"creator 第 {pos + 1} 位"
                      + (f"；题名含「{about_hit}」但**不含目标姓名**" if about_hit else "")
                      + ("；无自著标记" if not self_hit else ""))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    ap.add_argument("--surname", action="append", required=True)
    a = ap.parse_args()
    raw = pathlib.Path(a.raw)
    mf = raw / "_fetch-manifest.json"
    if not mf.exists():
        print(f"{mf} 不在", file=sys.stderr)
        return 2
    recs = [r for r in json.loads(mf.read_text(encoding="utf-8"))["记录"]
            if r["status"] == "已取回"]
    if not recs:
        print("**没有可分类的文件** —— 不是「全是一手」", file=sys.stderr)
        return 3

    # ★ 人对「需人判」的裁定写在 raw/_primary-decisions.json：{identifier: "一手"|"二手"}
    #   **这是「需人判」唯一的出口**——没有它，这一档就会在下游被当成默认值吞掉
    #   （[[empty-default-swallows-unknown]]）。裁定必须写理由，格式 {"档":…, "理由":…}。
    dec_p = raw / "_primary-decisions.json"
    dec = json.loads(dec_p.read_text(encoding="utf-8")) if dec_p.exists() else {}
    # ★ `_rules`：**按人物写的规则**，用于同一部书的几十个扫描件——
    #   逐个列 identifier 会漏掉下一轮新抓的（Marshall 第 2 轮多了 40 份《华盛顿传》）。
    #   规则必须同时约束**题名**与**creator 首位**，不许只匹配题名。
    rules = dec.pop("_rules", [])

    def by_rule(rec):
        ti = as_text(rec.get("ia_title")).lower()
        cr = as_text(rec.get("ia_creator"))
        head = cr.split(";")[0]
        for r in rules:
            if r["当题名含"].lower() in ti and r["且creator首位含"] in head:
                return r["档"], "【人裁·规则】" + r["理由"]
        return None

    # ★★★ 2026-08-13：**裁定的 key 对不上任何记录 ⇒ 直接报错，不许静默忽略。**
    #   起因：我给 Fisher 那本摹本册写裁定时，identifier 是**照题名编的**
    #   （`eightyfouretched00fishgoog`），真值是 `eightyfouretche00raphgoog`。
    #   工具照旧跑完、照旧印「需人判 0」，**那条裁定一个字也没生效**，
    #   而我是靠「改动 2 条而我写了 3 条」这个对不上的数才发现的。
    #   ⇒ 一条不生效的裁定 = [[a-checker-nothing-calls-is-not-a-checker]] 的人工版。
    known = {r["identifier"] for r in recs}
    ghost = sorted(set(dec) - known)
    if ghost:
        print("✗ **裁定文件里有 %d 个 identifier 在本轮语料里不存在**——"
              "本次未分类（不是通过）：" % len(ghost), file=sys.stderr)
        for g in ghost:
            near = [k for k in known if k[:14] == g[:14]]
            print("    %s%s" % (g, ("　← 是不是想写 %s ？" % near[0]) if near else ""),
                  file=sys.stderr)
        return 4

    out, tally = [], {"一手": 0, "二手": 0, "需人判": 0}
    for r in recs:
        k, why = classify(r.get("ia_title", ""), r.get("ia_creator", ""), a.surname)
        # ★★ 2026-08-13：裁定对**任何** identifier 优先，不再只在「需人判」时生效。
        #   原来只有 `k == "需人判"` 才看裁定文件 ⇒ **人读了正文发现那是别人写的，也推翻不了工具**。
        #   Michelangelo #185 实测三例：
        #     · `artistmerchanta00bottgoog` 是 Charles Edwards Lester 1845 年的书，
        #       工具按 creator 里有他的名字判成一手；而那段第一人称说的是
        #       「一尊我接了 **300 美元**的胸像」——**他不用美元计价**，说话的是书里写的美国雕塑家。
        #     · Joseph Fisher 的两本 *Etched Fac-similes*，正文自印
        #       "ETCHED AND PUBLISHED BY JOSEPH FISHER" ＋ "A CATALOGUE OF EIGHTY-FOUR PRINTS"，
        #       是**照他的素描刻的复制品加目录**，不是他的文字。
        #   ⇒ 与 [[related-to-him-is-not-written-by-him]] 同型；
        #     而「人的判断没有回写到工具读的那份数据里」是本项目反复出现的形态。
        if r["identifier"] in dec:
            d = dec[r["identifier"]]
            # ★★ 2026-08-13：原来是 `d["理由"]` 直取，字段名写错就**抛栈**。
            #   Churchill #189 我写成了 `依据`，屏幕上只有一段 KeyError traceback，
            #   没有一个字说「字段名不对、应当叫什么」。
            #   [[error-message-points-at-an-exit-that-isnt-there]] 的近亲：
            #   **报错要指出怎么改，而不是把内部键名的 KeyError 甩给人看。**
            if "档" not in d:
                print(f"✗ 裁定 `{ident}` 缺 **`档`** 字段（应为「一手」/「二手」/「需人判」）",
                      file=sys.stderr)
                return 4
            _why = d.get("理由") or d.get("依据") or d.get("说明")
            if not _why:
                print(f"✗ 裁定 `{ident}` 缺**理由**字段。"
                      f"本工具认 `理由`（也接受 `依据`／`说明`）；实得字段：{sorted(d)}",
                      file=sys.stderr)
                return 4
            k, why = d["档"], "【人裁】" + _why
        elif k == "需人判":
            hit = by_rule(r)
            if hit:
                k, why = hit
        tally[k] += 1
        out.append({"identifier": r["identifier"], "档": k, "依据": why,
                    "title": as_text(r.get("ia_title"))[:80],
                    "creator": as_text(r.get("ia_creator"))[:80], "words": r.get("words", 0)})

    n = len(recs)
    print(f"{raw}｜{n} 份 → 一手 {tally['一手']}／二手 {tally['二手']}／**需人判 {tally['需人判']}**")
    lo = tally["一手"] / n
    hi = (tally["一手"] + tally["需人判"]) / n
    print(f"  一手占比：**下界 {lo:.4f}**（需人判全算二手）～ 上界 {hi:.4f}（需人判全算一手）")
    print(f"  ★ 门要用哪个数，取决于把「需人判」判成什么——**这一步不能跳过**")
    for k in ("二手", "需人判"):
        rows = [o for o in out if o["档"] == k]
        if rows:
            print(f"\n  【{k}】{len(rows)} 份：")
            for o in sorted(rows, key=lambda z: -z["words"]):
                print(f"    {o['identifier'][:42]:<44}{o['words']:>8,}  {o['title'][:52]}")
                print(f"      ↳ {o['依据']}｜creator: {o['creator'][:70]}")
    (raw / "_primary.json").write_text(json.dumps(
        {"总数": n, "计数": tally, "一手占比下界": round(lo, 4), "一手占比上界": round(hi, 4),
         "★口径": "需人判**不默认成一手**；门取哪个数须先把需人判判完", "明细": out},
        ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
