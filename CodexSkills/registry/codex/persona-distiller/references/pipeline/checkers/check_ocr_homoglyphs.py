#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**同形字门**：查 OCR 扫描件里的「看起来是英文、其实是西里尔字母」。

## 触发本检查器的实例

Jesse Livermore #100 是本项目第一个**只有扫描件**的人物（1877–1940）。
他唯一的亲笔著作《How to Trade in Stocks》(1940) 只有 OCR 文本可得。
实测这份 12.5 万字的英文语料里含 **1405 个西里尔字符**：

| 语料里的样子 | 实际是 | 说明 |
|---|---|---|
| `HOW ТО TRADE` | `HOW TO TRADE` | `Т`=U+0422，`О`=U+041E |
| `РКЕҒАСЕ` | `PREFACE` | **七个字母全是西里尔同形字** |
| `ТО МІМА`（题献页） | `TO MIMA` | 同上 |

## 为什么现有的门一个都拦不住

- `check_verbatim_quotes.py` 拿引文去语料里比对——**我从语料里复制一段带同形字的话，
  它会说「找到了」**。逐字引文检查回答的是「语料里有没有这句」，
  不是「这句里的字符是不是真的」。
- `check_quote_integrity.py` 查的是引文有没有被截断改写，同样不看字符集。
- `check_authorship.py` 更是反过来被它咬了一口：这本书的署名页 OCR 成
  `BY / JESSE 1. LIVERMORE`（`L.` 变成 `1.`），**正版署名反而认不出来**。

于是：**门全绿，而产物里那句「他的原话」含有他绝不可能写出的西里尔字母。**
交付出去的引文是不可引用的——读者拿它去原书里搜，一个字也搜不到。

## 判据（两条，都是语言无关的）

### A. 单词内混用文种 —— 恒为错

一个词里同时出现拉丁字母与西里尔／希腊字母。**任何语言里都不成立**，
没有假阳性可言。

### B. 少数派文种里的「全同形字词」 —— OCR 替换

文档以拉丁字母为主时，若出现一个**完全由同形字构成**的西里尔词，判为 OCR 替换。

**为什么加「完全由同形字构成」这个限定**：长的俄语词多半含有
至少一个**没有拉丁长相**的字母（б г д ж з и й л п ф ц ч ш щ ъ ы ь э ю я）。
`привет` 里的 `и` 就不是同形字。
而 `РКЕҒАСЕ` 七个字母全在同形字表里——**那不是俄语词，是被替换掉的英文词**。

### ★★★★ 2026-08-07 更正：这里原先写着「**真俄语不会被误判**」，**是错的**

拿归档里的真语料一验就翻了：Benardos #128 的来源台账 `raw/_ids.txt`
（拉丁 59.7% / 西里尔 40.3%）被报出 **117 个 `all_homoglyph`，逐个读下来全是真俄语词**——
`соавтором`／`Текст`／`сварке`／`Реостат`／`оснастка`／`реестру`，以及改革前的 `отъ`、`имъ`。

**原来那句推理只对长词成立**，而俄语文本里占多数的恰恰是
`на не с о в к у то от а` 这类**整词全由同形字构成的虚词**。
一个俄语人物的语料（Benardos #128、Slavyanov #115）**必然大面积中招**。

**没有修，只是把射程写对了。** 试过一个判别式并**当场否掉**：
「文档里非同形字西里尔的占比」——Benardos 真俄语 **35.0%**，
而 Barton #117 那份**真 OCR 垃圾**（`Кей Cross Headquarters` = Red Cross、
`Мау` = May、`ШасафБаноп` = 糊掉的 Clara Barton）也有 **26.7%**。
**两者分不开，该判别式不成立。**

所以本判据在 B 这一路上的真实射程是：
**「这份文档里有西里尔字符」——它分不清那是 OCR 替换还是真的外文。**
语料层只报不拦，这个假阳不会挡任何人；但**读报告的人必须知道**，
否则会把 117 条噪声当成 117 处 OCR 损伤。

判据的方向仍是「窄到不误伤」，代价是漏掉那些恰好全由同形字构成的真外文词
（如 `ТОРС`）。**宁可漏，不可误杀**——误杀会让人去关掉这个门。

## 两级严重度（**引文里出现是错，语料里出现只是报**）

| 位置 | 处置 | 理由 |
|---|---|---|
| 断言／文档／用例里的**引文** | **error**，退出码 1 | 引文必须可被读者拿去原件里核对；含同形字就核不到 |
| **语料文件**本身 | **report**，不影响退出码 | 扫描件的 OCR 质量不是执行者能修的。它的用处是**逼你避开脏段落取引文**，并把「这份源是 OCR 件」记进账 |

★ 这个分级是有意的。把语料也判成 error 只会导致「为了过门而不用扫描件」，
而扫描件常常是历史人物**唯一**的一手件。
**门要拦的是把脏字符交付出去，不是拦你使用扫描件。**

退出码：0 = 引文层干净；1 = 引文含同形字；3 = 用法错误。
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import tempfile
import unicodedata

#: ★ 剥掉抓源方写的出处表头再量——**表头是出处说明，不是他的话**。
#:   全库只有 Adams（144 份）与 Coffin（36 份）有这种表头，
#:   实测占全文**聚合 17.2% / 11.7%**，**逐份中位 39.1% / 16.1%**。
#: ★★ 接上之后**逐个量过前后差**，只写量到的：
#:   · `check_lane_quotes_verbatim` @ Coffin：核过 1 → 0，
#:     报出 `Coffin, Charles L., Detroit, Mich.` **对不上**——
#:     那句「逐字引文」只存在于**我自己写的表头里**。这是 Barton 事故的引文版，实锤一条。
#:   · ★★★★ `check_ocr_language_death` @ Coffin：不剥时「**每一份都在下限之上**」，
#:     剥掉表头后报出 **2 份虚词占比 0.101（下限 0.15）**——
#:     **我那段干净的英文表头把 OCR 烂掉的文件托过了及格线。**
#:     同一件在 Adams 上是「可判份数 94 → 60」：34 份**只因表头的词数才够得上判**。
#:   · `check_first_person_density`：正文字符 −0.6%，密度 1.68 → **1.69**——
#:     **几乎没变**。我一度在这里写「第一人称密度被表头拉偏」，**那句没有实测支撑，已删**。
#:   · 其余多数判据前后一致。**接线是按「表头不是他的话」这条原则做的，不是因为每个都变了。**
import sys as _sys, pathlib as _pl
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent))
from common import corpus_body  # noqa: E402

# 与拉丁字母同形的西里尔／希腊字母 → 它们冒充的拉丁字母。
# 只收**字形上真的会混**的那些；拿不准的一律不收（宁可漏，不可误杀）。
HOMOGLYPHS = {
    # 西里尔大写
    "А": "A", "В": "B", "Е": "E", "К": "K", "М": "M", "Н": "H", "О": "O",
    "Р": "P", "С": "C", "Т": "T", "У": "Y", "Х": "X", "І": "I", "Ј": "J",
    "Ѕ": "S", "Ғ": "F", "Ԛ": "Q", "Ԝ": "W", "Ь": "b", "Ӏ": "I",
    # 西里尔小写
    "а": "a", "в": "B", "е": "e", "к": "k", "м": "m", "н": "H", "о": "o",
    "р": "p", "с": "c", "т": "t", "у": "y", "х": "x", "і": "i", "ј": "j",
    "ѕ": "s", "ԁ": "d", "һ": "h", "ӏ": "l", "ԛ": "q", "ԝ": "w",
    # 希腊
    "Α": "A", "Β": "B", "Ε": "E", "Ζ": "Z", "Η": "H", "Ι": "I", "Κ": "K",
    "Μ": "M", "Ν": "N", "Ο": "O", "Ρ": "P", "Τ": "T", "Υ": "Y", "Χ": "X",
    "ο": "o", "ρ": "p", "ν": "v",
}

WORD_RE = re.compile(r"[^\W\d_]+", re.UNICODE)


def _script(ch: str) -> str:
    """粗分文种。只区分本判据需要的三类，其余归 other。"""
    try:
        name = unicodedata.name(ch)
    except ValueError:
        return "other"
    if name.startswith("LATIN"):
        return "latin"
    if name.startswith("CYRILLIC"):
        return "cyrillic"
    if name.startswith("GREEK"):
        return "greek"
    return "other"


def scan_text(text: str) -> dict:
    """→ {'mixed': [...], 'all_homoglyph': [...], 'counts': {...}}"""
    mixed: list[str] = []
    all_homo: list[str] = []
    script_totals = {"latin": 0, "cyrillic": 0, "greek": 0, "other": 0}

    words = WORD_RE.findall(text)
    for word in words:
        scripts = {_script(ch) for ch in word}
        for ch in word:
            script_totals[_script(ch)] += 1
        real = scripts - {"other"}
        # A. 词内混用文种
        if len(real) > 1:
            mixed.append(word)
            continue
        # B. 少数派文种的全同形字词（是否少数派由调用方按文档统计决定）
        if real and real != {"latin"} and all(ch in HOMOGLYPHS for ch in word):
            all_homo.append(word)

    latin = script_totals["latin"]
    non_latin = script_totals["cyrillic"] + script_totals["greek"]
    # 拉丁不占多数时，B 判据不成立（文档本身可能就是俄文／希腊文）
    if latin <= non_latin:
        all_homo = []
    # ★ 2026-08-07 新增的这一项**只用于给读报告的人提示，不参与任何判定**：
    #   「没有拉丁长相」的非拉丁字母有多少。真外文里它必然大量出现。
    #   ⚠ 它**分不开**真外文与 OCR 垃圾——Benardos 真俄语 35.0%，
    #     Barton 那份真 OCR 垃圾也有 26.7%。当初想拿它做判别式，实测否掉了。
    genuine = sum(1 for ch in text
                  if _script(ch) in ("cyrillic", "greek") and ch not in HOMOGLYPHS)
    return {
        "mixed": mixed,
        "all_homoglyph": all_homo,
        "counts": {
            "words": len(words),
            "latin_chars": latin,
            "non_latin_chars": non_latin,
            "mixed_words": len(mixed),
            "all_homoglyph_words": len(all_homo),
            "genuine_nonlatin_chars": genuine,
        },
    }


def _has_genuine_nonlatin(rep: dict, floor: float = 0.15) -> bool:
    """这份语料里「没有拉丁长相」的非拉丁字母够不够多（提示用，**不是判定**）。

    ⚠ **它不能用来判断是真外文还是 OCR 垃圾。** 两个实测值：
    Benardos #128 真俄语 **35.0%**，Barton #117 真 OCR 垃圾 **26.7%**——
    重叠，分不开。它只回答「这份东西里有没有成规模的真外文字母」，
    据此提醒读报告的人：**这一栏得人去读**。
    """
    c = rep.get("counts", {})
    nl = c.get("non_latin_chars", 0)
    if not nl:
        return False
    return c.get("genuine_nonlatin_chars", 0) / nl >= floor


def restore(word: str) -> str:
    """把同形字换成它**长得像**的那个拉丁字母。仅用于报告里显示。

    ⚠ **这不是「还原成原文」，绝不可拿它去修引文。**

    实例（本检查器自测时撞到，assertion 写错的是我）：语料里的 `РКЕҒАСЕ`
    原文是 `PREFACE`，而本函数输出 `PKEFACE`——因为第二个字符是
    `CYRILLIC CAPITAL LETTER KA`（长得像 `K`），**OCR 把原文的 `R` 认成了 `K`，
    并且用西里尔字母写了出来**。也就是说这一处错了两层：认错字母 + 用错文种。

    **同形字表只能揭示「这里出过 OCR 错」，不能告诉你原文是什么。**
    原文只能回原件去看。拿本函数的输出当「修好的引文」交付，就是编造。
    """
    return "".join(HOMOGLYPHS.get(ch, ch) for ch in word)


# --------------------------------------------------------------------------
# 引文抽取：只看**引号里**的内容，那才是要交付给读者去核对的东西。
# --------------------------------------------------------------------------
QUOTE_RE = re.compile(
    r"[“”\"]([^“”\"\n]{8,400})[“”\"]"      # 直双引号与弯双引号
    r"|「([^」\n]{4,400})」"                # 中文直角引号
    , re.UNICODE)


def extract_quotes(text: str) -> list[str]:
    out = []
    for m in QUOTE_RE.finditer(text):
        span = m.group(1) or m.group(2) or ""
        if span.strip():
            out.append(span.strip())
    return out


def check_corpus(paths: list[pathlib.Path]) -> list[dict]:
    reports = []
    for path in paths:
        try:
            text = corpus_body(path.read_text(encoding="utf-8", errors="replace"))
        except OSError as exc:
            reports.append({"file": str(path), "error": str(exc)})
            continue
        result = scan_text(text)
        if result["counts"]["mixed_words"] or result["counts"]["all_homoglyph_words"]:
            reports.append({
                "file": str(path),
                "counts": result["counts"],
                "samples": [
                    {"as_scanned": w, "reads_as": restore(w)}
                    for w in (result["all_homoglyph"] + result["mixed"])[:8]
                ],
            })
    return reports


def check_quotes_counted(paths):
    """→ (problems, 读到的文件数, 扫到的引文条数)。

    ★ 分母必须能取到。原来只返回 `problems`，于是 `if not quote_problems:`
      对**两种**情形印同一句「✓ 引文层干净」：
        ① 有引文、且一条都不含同形字   → 真通过
        ② **一条引文都没扫到**         → 什么也没查
      2026-08-14 用空但合法的输入实测坐实为假绿。
      [[zero-hit-gates-must-prove-they-can-hit]]
    """
    problems, n_files, n_quotes = [], 0, 0
    for path in paths:
        try:
            text = corpus_body(path.read_text(encoding="utf-8", errors="replace"))
        except OSError as exc:
            problems.append(f"{path}: 读不到：{exc}")
            continue
        n_files += 1
        for quote in extract_quotes(text):
            n_quotes += 1
            result = scan_text(quote)
            bad = result["all_homoglyph"] + result["mixed"]
            if bad:
                shown = "、".join(f"{w!r}→{restore(w)!r}" for w in bad[:4])
                problems.append(
                    f"{path}: 引文含 OCR 同形字 {shown}——"
                    f"读者拿这句去原件里搜是搜不到的｜{quote[:60]}…")
    return problems, n_files, n_quotes


def check_quotes(paths: list[pathlib.Path]) -> list[str]:
    """只要 problems 的老口径（既有调用方照用）。要分母请用 `check_quotes_counted`。"""
    return check_quotes_counted(paths)[0]


# --------------------------------------------------------------------------
# 负对照。没有负对照的检查器，其「全绿」不构成任何证据（RUNBOOK 第十八种）。
# --------------------------------------------------------------------------
def self_test() -> int:
    failures: list[str] = []

    # ══ ★★★★ 逐字真实样本：**同一个判定，两种截然不同的原因**（2026-08-07）══
    #   两串都是从 `skill_log_evals` 归档里 `repr()` 出来的**原文**，一个字没动。
    #
    #   ① Benardos #128 的来源台账 `raw/_ids.txt`——**真俄语**。
    #      全文 5160 个西里尔字符里 1806 个（35.0%）是**没有拉丁长相**的字母
    #      （и л д б ж э я ъ…），是货真价实的俄文注释。
    #      **判据在整份文件上报出 117 个 `all_homoglyph`，逐个读下来全是真词**：
    #      соавтором／Текст／сварке／Реостат／оснастка／реестру／改革前的 отъ、имъ。
    #      ★ 这**证伪了本文件文档头原先那句「真俄语不会被误判」**——
    #        那句推理对 `привет` 这种长词成立，而俄语里占多数的是
    #        `на не с о в к у то от` 这类**全由同形字构成的虚词**。
    #
    #   ② Barton #117 的 `rc-peace-war-1912.txt`——**真 OCR 垃圾**（同一判定，真阳）。
    #      `Кей Cross Headquarters` 是 Red Cross、`Мау` 是 May、
    #      `ШасафБаноп` 是糊掉的 Clara Barton。这里报得对。
    #
    #   ★★★ **关键在于：本判据分不开这两者。**
    #     我曾想用「文档里有没有非同形字西里尔」去区分——
    #     **量了一下就被否掉**：Benardos 35.0%，而 Barton 那份 OCR 垃圾也有 26.7%。
    #     该判别式不成立，**没有落地**。这条留在这里是为了让下一个人别再走一遍。
    print("\n── ★★★★ 逐字真实样本：真俄语 vs 真 OCR 垃圾（判据分不开）──")
    _ru_real = 'us-patent-363320-1887-elektrogefest\thttps://patentimages.storage.googleapis.com/74/6f/2a/17ed495adeac02/US363320.pdf\tN. de Benardos & S. Olszewski, «Process of and Apparatus for Working Metals by the Direct Application of the Electric Current», United States Letters Patent No. 363,320\t1887\tprinted leaf: «Patented May 17, 1887»; «Application filed December 3, 1885. Serial No. 184,847»; 4 sheets of drawings + specification, 7 PDF pages\ten\tP1\tCO-AUTHORED\tlane=writings. ELECTRODE=carbon. Основополагающий документ «Электрогефеста» и единственный из шести с соавтором — Stanisław Olszewski, поэтому CO-AUTHORED, а не HIS-OWN. Текст от первого лица; «The conductor preferably consists of a stick or cylindrical rod of carbon». Все три следующих патента ссылаются именно на него. RIGHTS=pre1929'
    _ocr_real = 'lara Barton, taken about 1585 allstar ну, етсин r8 De шр opp. 17 \nThe First Red Cross Warehouse, ане DC A si, sais то а DT \nШасафБаноп staken about, 15848 4 55,22 зу чил». ЗЇ. пим МИА аз. 113 \nатир Бет а AGB 630700 6 015 605 оо ооо а бо 143 \nКей Cross Headquarters ........ БОҚТАП К Ма: о он ИЙ \n[ойоебозп, Ра  реғюгене оошот 2222222 2: 155 '
    _r1 = scan_text(_ru_real)
    _r2 = scan_text(_ocr_real)
    print(f"  ① Benardos 真俄语行：all_homoglyph={_r1['all_homoglyph']}")
    print(f"  ② Barton 真 OCR 垃圾：all_homoglyph={_r2['all_homoglyph'][:8]}")
    if len(_r1["all_homoglyph"]) != 8:
        failures.append(f"真俄语样本行为变了：期望 8 个，实得 {len(_r1['all_homoglyph'])}")
    if "соавтором" not in _r1["all_homoglyph"]:
        failures.append("真俄语样本：`соавтором` 不再被报——**这是假阳，但行为变了要有人知道**")
    if len(_r2["all_homoglyph"]) != 13:
        failures.append(f"真 OCR 垃圾样本行为变了：期望 13 个，实得 {len(_r2['all_homoglyph'])}")
    if not _r2["all_homoglyph"]:
        failures.append("★ 真 OCR 垃圾一个都不报了——**真阳丢了**，比假阳严重")
    print(f"  ✓ 两侧都按现行口径复现（真俄语 8 假阳／真 OCR 13 真阳）")

    # 正对照一：干净英文，一条都不许报。
    clean = ("The speculator's chief enemies are always boring from within. "
             "It is inseparable from human nature to hope and to fear.")
    r = scan_text(clean)
    if r["counts"]["mixed_words"] or r["counts"]["all_homoglyph_words"]:
        failures.append(f"正对照·干净英文被误报：{r}")

    # 正对照二：真俄语不许被判成 OCR 替换（含非同形字 и/л/д 等）。
    russian = "привет мир большой словарь для людей"
    r = scan_text(russian)
    if r["all_homoglyph"]:
        failures.append(f"正对照·真俄语被误杀：{r['all_homoglyph']}")

    # 正对照三：中文不受影响。
    r = scan_text("他把亏损归给自己而不是市场。")
    if r["counts"]["mixed_words"] or r["counts"]["all_homoglyph_words"]:
        failures.append(f"正对照·中文被误报：{r}")

    # 负对照 A：词内混文种。
    r = scan_text("HOW TO TRАDE IN STOCKS")          # A 是西里尔
    if not r["mixed"]:
        failures.append("负对照 A 未抓出：词内混用拉丁与西里尔")

    # 负对照 B：全同形字词（本例取自真实语料）。
    r = scan_text("HOW ТО TRADE IN STOCKS РКЕҒАСЕ")   # ТО 与 РКЕҒАСЕ 全西里尔
    if len(r["all_homoglyph"]) < 2:
        failures.append(f"负对照 B 未抓出：全同形字词，实得 {r['all_homoglyph']}")
    # ★ 这一条断言我第一次写成了「应还原为 PREFACE」，自测当场把我抓了出来。
    #   语料里那个词的原文确实是 PREFACE，但本函数只能给出 PKEFACE——
    #   因为 OCR 把 `R` 认成了 `K` **并且**用西里尔字母写了出来，错了两层。
    #   保留这条断言正是为了钉死「restore 不是还原、不可拿去修引文」。
    if restore("РКЕҒАСЕ") != "PKEFACE":
        failures.append(f"restore 行为变了：РКЕҒАСЕ → {restore('РКЕҒАСЕ')!r}，"
                        f"应为 'PKEFACE'（它显示的是字形，不是原文）")

    # 负对照 C：引文层必须报错。
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)
        dirty = tmp / "claims.py"
        dirty.write_text('q = "It was never my thinking that made ТНЕ big money"\n',
                         encoding="utf-8")
        if not check_quotes([dirty]):
            failures.append("负对照 C 未抓出：引文里的同形字")
        ok = tmp / "clean.py"
        ok.write_text('q = "It was never my thinking that made the big money"\n',
                      encoding="utf-8")
        if check_quotes([ok]):
            failures.append("正对照·干净引文被误报")
        # 反向：中文引文（「」）里的干净内容不许报
        zh = tmp / "zh.md"
        zh.write_text("他写道「投机者最大的敌人来自内部」。\n", encoding="utf-8")
        if check_quotes([zh]):
            failures.append("正对照·中文直角引号内的干净内容被误报")

        # ★★ 负对照 D：**分母**。一条引文都没扫到时不许打成绿。
        #   2026-08-14 实测坐实的假绿就在这里 —— `quote_problems` 为空，
        #   而「没得查」与「查过且干净」印同一句话。
        none = tmp / "noquote.txt"
        none.write_text("no quotes here at all, just prose.\n", encoding="utf-8")
        _p, _f, n_none = check_quotes_counted([none])
        if n_none != 0 or _p:
            failures.append(f"负对照 D：无引文文件应得 0 条引文/0 问题，实得 {n_none}/{len(_p)}")
        _p2, _f2, n_clean = check_quotes_counted([ok])
        if n_clean < 1:
            failures.append(f"负对照 D：干净引文文件应扫出 ≥1 条，实得 {n_clean}")
        if n_none == n_clean:
            failures.append("负对照 D：**有引文与没引文的分母一样**——分母没起作用")

    # 反向对照：拉丁不占多数时 B 判据必须失效（否则整篇俄文会被全量误杀）。
    r = scan_text("тор рот сор мот кот" * 5 + " ok")
    if r["all_homoglyph"]:
        failures.append("反向对照失败：非拉丁为主的文档不该套用 B 判据")

    # ══════════════════════════════════════════════════════════════
    # ㉕ `check_corpus()` / `_has_genuine_nonlatin()`
    #    —— 2026-08-12 之前这两个从没被自测进入过
    # ══════════════════════════════════════════════════════════════
    #
    # 上面各条打的是 `scan_text()`（**一段文本里有没有同形字**）与
    # `check_quotes()`（引文层）。而 `check_corpus()` 是语料层的入口：
    # 它决定**哪些文件被读、读到的是文件的哪一段、什么样的结果算「有问题」**。
    # `check_selftest_reach` 把本件列在「验了配料、没验判决」名单上——它是对的。
    print("\n══ ㉕ check_corpus() 本体（tempdir 上跑真流程）══")
    _CLEAN = "HOW TO TRADE IN STOCKS. The tape tells the truth about the market."
    # ★ 逐字真实样本：Livermore #100 的 OCR 把 `PREFACE` 扫成七个西里尔同形字。
    _ALLH = "THE РКЕҒАСЕ of this book explains how the tape tells the truth."
    # 词内混文种：末尾 `E` 是 CYRILLIC CAPITAL IE（U+0415）。
    _MIX = "HOW TO TRADЕ IN STOCKS, said the man about the market and the tape."

    def _corp(files: dict, extra=()):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            for name, body in files.items():
                (d / name).write_text(body, encoding="utf-8")
            paths = [d / n for n in files] + [d / x for x in extra]
            for x in extra:
                (d / x).mkdir(exist_ok=True)
            return check_corpus(paths)

    rep = _corp({"clean.txt": _CLEAN})
    ok = rep == []
    print(f"  {'✓' if ok else '✗'} ㉕a 干净英文语料 → 0 份报告（{len(rep)}）")
    failures += [] if ok else ["㉕a 干净语料被误报"]

    rep = _corp({"a.txt": _ALLH})
    ok = (len(rep) == 1 and rep[0]["counts"]["all_homoglyph_words"] == 1
          and rep[0]["samples"][0]["as_scanned"] == "РКЕҒАСЕ")
    print(f"  {'✓' if ok else '✗'} ㉕b 全同形字词 `РКЕҒАСЕ` → 报出，并给出 as_scanned")
    failures += [] if ok else ["㉕b 全同形字词未报"]

    # ★★ `restore()` 只说明「这里出过 OCR 错」，**不是原文**：
    #    这一处 reads_as 是 `PKEFACE`，而原书写的是 `PREFACE`——
    #    OCR 认错了字母（R→K）**又**用错了文种。拿它当「修好的引文」交付就是编造。
    ok = rep and rep[0]["samples"][0]["reads_as"] == "PKEFACE"
    print(f"  {'✓' if ok else '✗'} ㉕b′ `reads_as` 是 **PKEFACE 不是 PREFACE**"
          f"——同形字表揭示不了原文，不许拿它修引文")
    failures += [] if ok else ["㉕b′ restore() 的射程说明失效"]

    rep = _corp({"m.txt": _MIX})
    ok = len(rep) == 1 and rep[0]["counts"]["mixed_words"] == 1
    print(f"  {'✓' if ok else '✗'} ㉕c 词内混文种 `TRADЕ` → 报出（A 判据，恒为错）")
    failures += [] if ok else ["㉕c 词内混文种未报"]

    # ㉕d 射程：多份文件都要扫到，不是只扫第一份或最后一份。
    rep = _corp({"a.txt": _ALLH, "b.txt": _MIX, "c.txt": _CLEAN})
    names = sorted(pathlib.Path(r["file"]).name for r in rep)
    ok = names == ["a.txt", "b.txt"]
    print(f"  {'✓' if ok else '✗'} ㉕d 射程：三份里恰好报出有问题的两份（{names}）")
    failures += [] if ok else ["㉕d 射程"]

    # ㉕e **读不了的文件不许静默消失**——它要带 error 出现在报告里。
    rep = _corp({"a.txt": _ALLH}, extra=("adir",))
    errs = [r for r in rep if "error" in r]
    ok = len(errs) == 1 and len(rep) == 2
    print(f"  {'✓' if ok else '✗'} ㉕e 读不了的路径 → 带 error 进报告（不是静默跳过）")
    failures += [] if ok else ["㉕e 读失败可见性"]

    # ㉕f ★ 射程声明（**不是缺陷**）：出处表头由 `corpus_body` 剥掉，
    #    表头里的同形字**按设计不查**——表头是抓源方写的，不是他的话。
    #    两种表头格式都要剥（`SOURCE: …\n====` 与开头连续的 `#` 行）。
    for tag, hdr in (("SOURCE 式", "SOURCE: РКЕҒАСЕ scan\n" + "=" * 24 + "\n"),
                     ("# 式", "# source: РКЕҒАСЕ scan\n# url: http://x\n")):
        rep = _corp({"h.txt": hdr + _CLEAN})
        ok = rep == []
        print(f"  {'✓' if ok else '✗'} ㉕f 射程：{tag}出处表头里的同形字**按设计不查**（表头非他的话）")
        failures += [] if ok else [f"㉕f 表头射程（{tag}）"]

    # ㉕g `_has_genuine_nonlatin` 是**提示**不是判定——两个实测值证明它分不开。
    #    Benardos #128 真俄语 35.0%／Barton #117 真 OCR 垃圾 26.7%，同在门 0.15 之上。
    _ru = {"counts": {"non_latin_chars": 1000, "genuine_nonlatin_chars": 350}}
    _junk = {"counts": {"non_latin_chars": 1000, "genuine_nonlatin_chars": 267}}
    _none = {"counts": {"non_latin_chars": 0, "genuine_nonlatin_chars": 0}}
    ok = (_has_genuine_nonlatin(_ru) and _has_genuine_nonlatin(_junk)
          and not _has_genuine_nonlatin(_none))
    print(f"  {'✓' if ok else '✗'} ㉕g `_has_genuine_nonlatin`：真俄语 35.0% 与 OCR 垃圾 26.7% "
          f"**双双为真** ⇒ 它分不开，只能当提示（无非拉丁时为假）")
    failures += [] if ok else ["㉕g 提示项的射程"]

    for f in failures:
        print(f"✗ {f}")
    if failures:
        print(f"负对照未通过：{len(failures)} 项")
        return 1
    print("负对照通过：干净英文/真俄语/中文三条正对照 0 报，"
          "词内混文种、全同形字词、引文层三类坏样本全部抓出，"
          "非拉丁为主的文档不套用 B 判据；"
          "另 check_corpus 本体九条（含读失败可见性与两种表头射程）")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="同形字门：OCR 扫描件里冒充拉丁字母的西里尔／希腊字符")
    ap.add_argument("paths", nargs="*", type=pathlib.Path,
                    help="要查的文件；目录会被递归展开")
    ap.add_argument("--mode", choices=["quotes", "corpus", "both"], default="both",
                    help="quotes=只查引文（error）；corpus=只查语料（report）")
    ap.add_argument("--self-test", action="store_true", help="跑负对照，不读真实树")
    ap.add_argument("--json", action="store_true", help="机读输出")
    args = ap.parse_args()

    if args.self_test:
        return self_test()
    if not args.paths:
        print("用法错误：需要至少一个路径（或用 --self-test）", file=sys.stderr)
        return 3

    files: list[pathlib.Path] = []
    for p in args.paths:
        # ★ 2026-08-12：`is_dir()` 对**病态路径**不是返回 False，而是抛 OSError
        #   （实测 Errno 63「File name too long」——起因是我在 zsh 里对未加引号的
        #   变量指望它按换行分词，**zsh 不做分词**，整串路径变成了一个参数）。
        #   本件本来就有一条干净的「用法错误：… 不存在」出口，
        #   不该在它前面掉进 traceback。**崩了也不是「查过了」。**
        try:
            is_dir, is_file = p.is_dir(), p.is_file()
        except OSError as exc:
            print(f"用法错误：{str(p)[:120]}… 取不到状态（{exc}）", file=sys.stderr)
            return 3
        if is_dir:
            files.extend(sorted(q for q in p.rglob("*")
                                if q.is_file() and q.suffix in
                                {".txt", ".md", ".py", ".json", ".jsonl"}))
        elif is_file:
            files.append(p)
        else:
            print(f"用法错误：{p} 不存在", file=sys.stderr)
            return 3

    if args.mode in {"quotes", "both"}:
        quote_problems, n_qfiles, n_quotes = check_quotes_counted(files)
    else:
        quote_problems, n_qfiles, n_quotes = [], 0, 0
    corpus_reports = check_corpus(files) if args.mode in {"corpus", "both"} else []

    if args.json:
        print(json.dumps({"quote_problems": quote_problems,
                          "corpus_reports": corpus_reports},
                         ensure_ascii=False, indent=2))
        return 1 if quote_problems else 0

    if corpus_reports:
        print(f"· 语料层（只报不拦）：{len(corpus_reports)} 份文件含同形字")
        for rep in corpus_reports[:10]:
            if "error" in rep:
                print(f"  - {rep['file']}：{rep['error']}")
                continue
            c = rep["counts"]
            print(f"  - {pathlib.Path(rep['file']).name}："
                  f"非拉丁字符 {c['non_latin_chars']} 个／"
                  f"全同形字词 {c['all_homoglyph_words']} 个／"
                  f"混文种词 {c['mixed_words']} 个")
            for s in rep["samples"][:3]:
                print(f"      {s['as_scanned']!r} 其实是 {s['reads_as']!r}")
        if len(corpus_reports) > 10:
            print(f"  …另有 {len(corpus_reports) - 10} 份")
        print("  ↑ 这些是 OCR 件。**取引文时避开这些位置**，并把「本源是扫描件」记进账。")
        # ★★★★ 2026-08-07：**「全同形字词」这一栏在含真外文的语料上几乎全是假阳。**
        #   Benardos #128 的 `raw/_ids.txt` 实测 117 条，逐个读下来全是真俄语
        #   （соавтором／Текст／сварке／Реостат）。判据**分不开**真外文与 OCR 替换：
        #   试过用「非同形字西里尔占比」区分，Benardos 35.0% 而真 OCR 垃圾也有 26.7%。
        #   不打这行字，读的人会把 117 条噪声当成 117 处 OCR 损伤。
        _foreign = [r for r in corpus_reports
                    if "error" not in r and r["counts"]["all_homoglyph_words"]
                    and _has_genuine_nonlatin(r)]
        if _foreign:
            # ★ 措辞在这里改过一次：初稿写的是「这几份多半是真外文，不是 OCR 损伤」，
            #   拿 Barton #117 那份**真 OCR 垃圾**一跑，它也被打上同一句话——**说反了**。
            #   本标记两个方向都不下结论，它只说「这一栏不能当计数读」。
            print(f"  ★★ **其中 {len(_foreign)} 份含大量「没有拉丁长相」的非拉丁字母**"
                  f"（и л д б ж э я ъ 之类）——"
                  f"**这几份的「全同形字词」一栏不能当 OCR 损伤的计数读**：")
            for r in _foreign[:5]:
                c = r["counts"]
                print(f"       {pathlib.Path(r['file']).name}："
                      f"全同形字词 {c['all_homoglyph_words']} 个，"
                      f"非同形字非拉丁 {c.get('genuine_nonlatin_chars', '?')} 个"
                      f"（占非拉丁 {c.get('genuine_nonlatin_chars', 0) / max(c['non_latin_chars'], 1):.1%}）")
            print("       ★ **判据分不开真外文与 OCR 垃圾**，两个方向都会错：")
            print("         · Benardos #128 `_ids.txt` 非同形字占 35.0%，"
                  "117 条**全是真俄语**（соавтором／Текст／Реостат）→ 假阳")
            print("         · Barton #117 `rc-peace-war-1912.txt` 占 26.7%，"
                  "2923 条**全是真 OCR 垃圾**（Кей Cross = Red Cross）→ 真阳")
            print("         两个区间重叠，**曾想拿这个占比做判别式，实测否掉了**。"
                  "**这一栏要人去读原文。**")

    # ★★ 分母印出来。原来只有一句「✓ 引文层干净」，而 quote_problems 为空
    #   有**两种**情形：①有引文、一条都不含同形字 → 真通过；
    #   ②**一条引文都没扫到** → 什么也没查。两种印同一句话就是假绿。
    #   写法照抄 `check_quote_in_span`。[[zero-hit-gates-must-prove-they-can-hit]]
    print("引文层：读到 %d 个文件，扫出 %d 条引文" % (n_qfiles, n_quotes))
    if not n_quotes:
        print("  ⚠ **一条引文都没扫到**（%d 个候选文件里 %d 个读得到）——"
              "本判据这一轮什么也没查到，不构成通过" % (len(files), n_qfiles))
        return 0
    if not quote_problems:
        print("✓ 引文层干净：这 %d 条引文都不含冒充拉丁字母的西里尔／希腊字符" % n_quotes)
        return 0
    print(f"\n✗ 引文层 {len(quote_problems)} 条含同形字：\n")
    for p in quote_problems:
        print(f"  - {p}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
