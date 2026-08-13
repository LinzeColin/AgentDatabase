#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_inflected_byline_candidates.py —— **署名就在扉页上，只是变了格**

## 抓到它的那一次

2026-08-14，Comenius 有 **48 份**被归属核验判成「查无署名证据」。
本项目当时的结论是「这 48 行两头都空：既没有正文署名，也没有替代权威」。
我去打开读了一遍前 4000 字，**21 份（44%）扉页上明明写着他的名字**：

    JOH. AMOS COMENII ORBIS SENSUALIUM PICTUS               ← 拉丁属格 -ii
    a Joanne Amos **Comenio** ine composita                 ← 拉丁夺格 -o
    JANA AMOSA **KOMENSKÉHO** DIDAKTIKA                     ← 捷克属格 -ého
    Spisy Jana Amosa **Komenského**                         ← 同上

**`check_authorship.py` 找的是「Comenius」这个主格形**，
而拉丁书的扉页几乎从不用主格：`Comenii`（属格）、`Comenio`（夺格）才是常态。
⇒ 那 48 份里至少 21 份**不是没有署名，是署名换了个词尾**。

★ 这跟 [[filename-matching-is-brittle]] 是同一件事的语言版：
  **精确匹配一个词形，等于假设全世界只用主格。**

## 本件只做一件事：**把候选交出来，不改任何东西**

对每个「运行时查无署名证据」的一手源，在正文**前 `HEAD` 字**里找目标姓名的
**屈折变体**（拉丁 `-i/-ii/-o/-um/-us`、捷克/斯拉夫 `-ého/-a/-ovi`、
德语 `-s`、意语/西语 `-i`），命中就连上下文印出来。

## ★★ 它**不能**替你下结论，三条实测理由

1. `Spisy Jana Amosa Komenského` 的同一页上还有 **`Jan Kvačala`（编者）** ——
   名字在扉页上不等于这本书是他写的；
2. `Časoměrné překlady žalmův Jana Amosa Komenského, **pak Jana Blahoslava**…`
   是**多人合集**，他只占其中一部分；
3. `The Project Gutenberg EBook of The Orbis Pictus, **by John Amos Comenius**`
   命中的是 **Gutenberg 的样板行**，不是扉页。[[digitizer-boilerplate-matches-your-keyword]]

⇒ 每一条都要打开读，确认是**扉页署名**再按 `A-byline` 逐字照录进台账。

## 它有意不改 `check_authorship.py`

那是**已冻结的判分输入**（㊵）：改它会让全库已判过的工作区改变裁定。
本件是独立的一件，报告制、rc 恒 0。

## 用法

    python3 check_inflected_byline_candidates.py <工作区> [--verdicts <auth 输出>]
    python3 check_inflected_byline_candidates.py --self-test
"""
import argparse
import json
import pathlib
import re
import sys

HEAD = 4000          # 只看正文前这么多字（扉页区）
MIN_STEM = 4         # 姓氏词干至少这么长才拿去匹配，免得 `Ford` 之类误爆


def stems(full_name: str):
    """人名 → 拿去做屈折匹配的词干集合。**纯函数**。

    只取长度 ≥ MIN_STEM 的词，且**去掉常见的教名**——
    `John`／`Jan`／`Johann` 在拉丁扉页上到处都是，用它匹配等于全命中。
    """
    drop = {"john", "jan", "johann", "joh", "jean", "juan", "giovanni", "amos",
            "amosa", "amose", "van", "von", "de", "da", "di", "der", "the"}
    out = set()
    for w in re.split(r"[^\wÀ-ž]+", full_name or ""):
        if len(w) >= MIN_STEM and w.lower() not in drop:
            out.add(w)
    return out


def inflected(stem: str) -> re.Pattern:
    """一个词干 → 认得屈折词尾的正则。

    ★★ 两次剥词尾，缺一个自测就红：
      · 拉丁：`Comenius` 要剥掉 `ius` 才接得上 `Comenii`／`Comenio`；
      · 斯拉夫：`Komenský` 要剥掉末尾那个 `ý` 才接得上 `Komenského`
        —— 我第一版只剥了拉丁那一种，自测里捷克那条当场判红。
    """
    bases = {stem}
    a = re.sub(r"(ius|us|s)$", "", stem, flags=re.I)
    if len(a) >= 3:
        bases.add(a)
    b = re.sub(r"[ýyaeiouáéíóú]$", "", a, flags=re.I)
    if len(b) >= 3:
        bases.add(b)
    tail = (r"(?:ius|us|um|orum|is|io|ii|i|o|a|e|y|ý|ého|eho|ému|emu|ým|ym|"
            r"ovi|ov|ova|em|en|s)?")
    alt = "|".join(re.escape(x) for x in sorted(bases, key=len, reverse=True))
    return re.compile(rf"\b(?:{alt}){tail}\b", re.I)


def find(text: str, name: str, head: int = HEAD, aliases=()):
    """→ [(命中的词, 上下文)]，只在前 head 字里找。

    ★★ `aliases` 不是锦上添花，是**必需**：同一个人在另一种语言里是**另一个姓**。
      Comenius（拉丁）＝ **Komenský**（捷克），而 `meta.json` 里只有一个形。
      我手工 grep 时把两个都写了，得 21/48；判据只用 meta 的那个形，得 16/48 ——
      **同一件事两个数，差的是词表**。[[counts-need-their-cutoff-stated]]
    """
    seg = text[:head]
    out = []
    all_stems = set(stems(name))
    for a in aliases:
        all_stems |= stems(a)
    for st in sorted(all_stems):
        rx = inflected(st)
        for m in rx.finditer(seg):
            ctx = re.sub(r"\s+", " ", seg[max(0, m.start() - 70):m.end() + 70])
            out.append((m.group(), ctx))
    return out


def self_test() -> int:
    ok = t = 0

    def chk(d, c):
        nonlocal ok, t
        t += 1
        ok += 1 if c else 0
        print(f"  {'✓' if c else '✗'} {d}")

    N = "John Amos Comenius"
    chk(f"★ 词干去掉教名与 Amos（实得 {sorted(stems(N))}）", sorted(stems(N)) == ["Comenius"])
    # ★★ 正对照：四种真实扉页写法
    for s, why in [("JOH. AMOS COMENII ORBIS SENSUALIUM PICTUS", "拉丁属格 -ii"),
                   ("a Joanne Amos Comenio ine composita", "拉丁夺格 -o"),
                   ("Des Johann Amos Comenius Entwurf", "主格（原来就认得）")]:
        chk(f"★★ **正对照（{why}）**：「{s[:38]}」", bool(find(s, N)))
    chk("★★ **捷克属格 `Komenského`**（另一个词干）",
        bool(find("JANA AMOSA KOMENSKÉHO DIDAKTIKA", "Jan Amos Komenský")))
    # ★★ 反例：不许把别的名字算成他的
    chk("★★ **反例：`Blahoslava` 不许命中 Komenský**",
        not find("pak Jana Blahoslava, Matouše", "Jan Amos Komenský"))
    chk("★★ **反例：只出现在 4000 字之后的不算**",
        not find("x" * 5000 + " COMENII ", N))
    chk("★ 反例：教名单独出现不算（`Johannis` 不该命中）", not find("Johannis Lasitii", N))
    print(f"\n{'✓ 全过' if ok == t else f'✗ {t - ok}/{t} 项不符'}")
    return 0 if ok == t else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("workspace", nargs="?")
    ap.add_argument("--verdicts", help="check_authorship 的输出（只看它判 ✗ 的那些）")
    ap.add_argument("--alias", action="append", default=[],
                    help="他在别的语言里的姓（可重复）。**同一个人在拉丁文/捷克文里是两个姓** "
                         "——Comenius vs Komenský；不给的话那一半永远搜不到")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.workspace:
        ap.error("要 <工作区>")
    ws = pathlib.Path(a.workspace)
    meta = json.loads((ws / "meta.json").read_text(encoding="utf-8"))
    name = meta.get("name") or ws.name.replace("-", " ")

    only = None
    if a.verdicts:
        only, cur = set(), None
        for line in pathlib.Path(a.verdicts).read_text(encoding="utf-8").splitlines():
            m = re.match(r"=== (\S+) \(\d+ 份\) ===", line)
            if m:
                cur = m.group(1)
                continue
            m = re.match(r"\s*✗ (\S+\.txt)", line)
            if m and cur == ws.name:
                only.add(m.group(1))

    rows, scanned = [], 0
    for line in (ws / "evidence/source-ledger.jsonl").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if (r.get("split") != "train" or r.get("attribution") != "HIS-OWN"
                or r.get("tier") not in ("P1", "P2")):
            continue
        p = ws / str(r.get("local_path") or "")
        if not p.is_file():
            continue
        if only is not None and p.name not in only:
            continue
        scanned += 1
        hits = find(p.read_text(encoding="utf-8", errors="replace"), name, aliases=a.alias)
        if hits:
            rows.append((len(hits), r["source_id"], str(r.get("title") or "")[:46], hits[0][1][:130]))

    rows.sort(reverse=True)
    scope = "运行时判 ✗ 的" if only is not None else "全部一手"
    _st = set(stems(name))
    for _a in a.alias:
        _st |= stems(_a)
    if not a.alias:
        print("★ **没给 `--alias`**：只按 `meta.json` 里那一个姓搜。"
              "同一个人在别的语言里可能是另一个姓（Comenius vs Komenský），**那一半搜不到**。")
    print(f"★★ **分母**：{ws.name}｜姓名词干 {sorted(_st)}｜"
          f"扫了{scope} **{scanned}** 份（只看正文前 {HEAD} 字）")
    print(f"⇒ **扉页区出现姓名屈折变体的：{len(rows)} 份"
          f"（{len(rows)/scanned:.0%}）** —— 这些是**候选，不是结论**\n" if scanned else "")
    for c, sid, ti, ctx in rows:
        print(f"  {c:2d} 次  {sid}  {ti}\n        …{ctx}…")
    print("\n★★ **每一条都要打开读**，确认是**扉页署名**再按 `A-byline` 逐字照录进台账。"
          "\n   实测三种误报：编者名同页（`Jan Kvačala`）／多人合集（`pak Jana Blahoslava`）／"
          "**数字化样板行**（`The Project Gutenberg EBook of …, by …`）。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
