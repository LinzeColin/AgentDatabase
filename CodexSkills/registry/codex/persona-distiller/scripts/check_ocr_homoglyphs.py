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

**为什么加「完全由同形字构成」这个限定**：真正的俄语词几乎必然含有
至少一个**没有拉丁长相**的字母（б г д ж з и й л п ф ц ч ш щ ъ ы ь э ю я）。
`привет` 里的 `и` 就不是同形字，因此**真俄语不会被误判**。
而 `РКЕҒАСЕ` 七个字母全在同形字表里——**那不是俄语词，是被替换掉的英文词**。

判据的方向是「窄到不误伤」，代价是漏掉那些恰好全由同形字构成的真外文词
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
    return {
        "mixed": mixed,
        "all_homoglyph": all_homo,
        "counts": {
            "words": len(words),
            "latin_chars": latin,
            "non_latin_chars": non_latin,
            "mixed_words": len(mixed),
            "all_homoglyph_words": len(all_homo),
        },
    }


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
            text = path.read_text(encoding="utf-8", errors="replace")
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


def check_quotes(paths: list[pathlib.Path]) -> list[str]:
    problems = []
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            problems.append(f"{path}: 读不到：{exc}")
            continue
        for quote in extract_quotes(text):
            result = scan_text(quote)
            bad = result["all_homoglyph"] + result["mixed"]
            if bad:
                shown = "、".join(f"{w!r}→{restore(w)!r}" for w in bad[:4])
                problems.append(
                    f"{path}: 引文含 OCR 同形字 {shown}——"
                    f"读者拿这句去原件里搜是搜不到的｜{quote[:60]}…")
    return problems


# --------------------------------------------------------------------------
# 负对照。没有负对照的检查器，其「全绿」不构成任何证据（RUNBOOK 第十八种）。
# --------------------------------------------------------------------------
def self_test() -> int:
    failures: list[str] = []

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

    # 反向对照：拉丁不占多数时 B 判据必须失效（否则整篇俄文会被全量误杀）。
    r = scan_text("тор рот сор мот кот" * 5 + " ok")
    if r["all_homoglyph"]:
        failures.append("反向对照失败：非拉丁为主的文档不该套用 B 判据")

    for f in failures:
        print(f"✗ {f}")
    if failures:
        print(f"负对照未通过：{len(failures)} 项")
        return 1
    print("负对照通过：干净英文/真俄语/中文三条正对照 0 报，"
          "词内混文种、全同形字词、引文层三类坏样本全部抓出，"
          "且非拉丁为主的文档不套用 B 判据")
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
        if p.is_dir():
            files.extend(sorted(q for q in p.rglob("*")
                                if q.is_file() and q.suffix in
                                {".txt", ".md", ".py", ".json", ".jsonl"}))
        elif p.is_file():
            files.append(p)
        else:
            print(f"用法错误：{p} 不存在", file=sys.stderr)
            return 3

    quote_problems = check_quotes(files) if args.mode in {"quotes", "both"} else []
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

    if not quote_problems:
        print("✓ 引文层干净：没有引文含冒充拉丁字母的西里尔／希腊字符")
        return 0
    print(f"\n✗ 引文层 {len(quote_problems)} 条含同形字：\n")
    for p in quote_problems:
        print(f"  - {p}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
