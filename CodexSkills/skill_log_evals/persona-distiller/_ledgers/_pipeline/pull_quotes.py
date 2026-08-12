#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从语料里取**可复算定位**的逐字引文。研究道写作用。

用法：
    python3 pull_quotes.py --raw <raw>  --ledger <source-ledger.jsonl> \
        --lane writings --n 8 [--exclude-third-party] [--min-len 70] [--max-len 200]

## 为什么要有这件

「零编造引文」是本项目的硬约束，而手打引文有三种错法，全都发生过：
- 记忆里的句子与原文差几个词（[[self-reported-numbers-must-be-computed]]）
- **改了讹字再当逐字引文用**（[[verbatim-is-not-understood]]，一天两次）
- 引文对得上而**说话人不是他**（Marshall 的第一人称是华盛顿的；
  Lincoln 全集前置页是别人的悼词 → `front_matter_third_party`）

⇒ 本工具**只做机械摘取**：从文件里原样切出，附上可复算的定位，
  **判断「这句是不是他说的、值不值得引」仍然是人的事。**

★★ **实证这一点的一条**（2026-08-12，Lincoln #174 writings 道）：
   本工具取出

       `In 1848, when I first went on the bench, the circuit embraced
        fourteen counties, and Mr.`

   逐字无误、定位可复算、在一手 P1 文件里、含第一人称 ——**四道机械判据全过**。
   而**林肯一生没当过法官**：说这话的是巡回法庭的某位法官（回忆录被收进这册）。
   ⇒ **没有任何机械规则能挡住它。** 说话人这一关只能人读，
     或交给项目自己的 `check_lane_quotes_verbatim.py` / `quote_speaker` 那一层。

## 定位口径

`norm_offset` = **归一空白（`\\s+`→单空格）之后**的字符偏移。
★ 不用原始偏移：原始文本里词间是双空格＋换行，同一句在不同扫描件里偏移不同，
  而归一之后可复算——校验只需

    text = re.sub(r"\\s+", " ", open(path).read())
    assert text[norm_offset:norm_offset+len(quote)] == quote

本工具**自己先跑一遍这个断言**，不过的不输出（见 `--self-check` 恒开）。

★ 退出码：0=取到；2=参数错；3=一条都没取到（**不是「没有引文」，是筛太紧**）。
"""
import argparse
import json
import pathlib
import re
import sys

WS = re.compile(r"\s+")
# OCR 坏行的粗筛：非常见标点/字母的字符太多，或连续三个 1–2 字母「词」
BAD_CHARS = re.compile(r"[^A-Za-zÀ-ÿ0-9,.;:'\"()\-–— ]")
BAD_RUN = re.compile(r"\b[A-Za-z]{1,2}\b \b[A-Za-z]{1,2}\b \b[A-Za-z]{1,2}\b")
# ★ 读命中读出来的三种坏样本（每一种都真的被取到过一次）：
#   ① **悼词/他人文章的脚注**：`A Eulogy on Abraham Lincoln, delivered before the
#      Municipal Authorities of the City of Boston, June I, 1865.`
#      —— `front_matter_third_party` 只看头 8000 字符，**第三方可以在文件任何位置**。
#   ② **目录行**：`Sturtevant xi Early Speeches, Political Papers, and Legal Notes
#      (March i, 1832, to May 29, 1856) : "I Am Humble Abraham Lincoln.`
#   ③ **从词中间起头**：`s of the 24th of February last…`／`e evil spirit…`
#      —— 句子正则从 `.?!` 之后切，而缩写里的点会把切口落在词中。
ATTRIB = re.compile(r"(?i)\b(eulogy|delivered before|an address (by|on)|"
                    r"introduction by|edited by|translated by|memorial (address|volume)|"
                    r"tribute to|in memoriam|obituary)\b")
#   ★ 首版要求「**两个**罗马数字」才判目录，于是
#     `Sturtevant xi Early Speeches, … (March i, 1832, to May 29, 1856)` 漏网
#     ——`xi` 是两字符而 `i` 只有一字符。改为**出现任何一个 ≥2 字符的罗马数字**即判：
#     正经散文里句中几乎不会出现 `xi`／`vii`／`iv` 这种孤立记号。
TOC_LIKE = re.compile(r"(\b[ivxlcdm]{2,6}\b|"                            # 任一罗马数字
                      r"\.{3,}|"                                          # 目录引导点
                      r"(\d+\s*,\s*){3,})")                             # 一串数字


def dehyphenate(t: str) -> str:
    t = re.sub(r"(\w)[-‐‑]\s*\n\s*([a-z])", r"\1\2", t)
    return re.sub(r"(\w)[-‐‑]\s+([a-z])", r"\1\2", t)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--lane", required=True)
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--min-len", type=int, default=70)
    ap.add_argument("--max-len", type=int, default=200)
    ap.add_argument("--exclude-third-party", action="store_true")
    ap.add_argument("--first-person", action="store_true",
                    help="只要含第一人称的句子（英文 I/my/me）")
    a = ap.parse_args()

    raw = pathlib.Path(a.raw)
    recs = [json.loads(l) for l in pathlib.Path(a.ledger).read_text(encoding="utf-8").splitlines()
            if l.strip()]
    pool = [r for r in recs if a.lane in (r.get("dimensions") or [])
            and r.get("tier") in ("P1", "P2") and r.get("split") == "train"]
    if a.exclude_third_party:
        before = len(pool)
        pool = [r for r in pool if not r.get("front_matter_third_party")]
        print(f"排除前置页含第三方的：{before} → {len(pool)} 份", file=sys.stderr)
    if not pool:
        print("这一道没有可取的一手 train 源", file=sys.stderr)
        return 3

    out = []
    for r in sorted(pool, key=lambda x: str(x.get("published_at") or "")):
        f = raw / pathlib.Path(r["local_path"]).name
        if not f.exists():
            continue
        norm = WS.sub(" ", dehyphenate(f.read_text(encoding="utf-8", errors="replace")))
        for m in re.finditer(r"[^.?!]{%d,%d}[.?!]" % (a.min_len, a.max_len), norm):
            s = m.group(0).strip()
            if len(BAD_CHARS.findall(s)) > 1 or BAD_RUN.search(s):
                continue
            if not re.match(r"[\"\u201c]?[A-Z]", s):        # ③ 必须从大写字母起头
                continue
            if ATTRIB.search(s) or TOC_LIKE.search(s):       # ①② 悼词署名行／目录行
                continue
            if a.first_person and not re.search(r"\bI\b|\bmy\b|\bme\b", s):
                continue
            off = norm.find(s)
            if off < 0 or norm[off:off + len(s)] != s:      # ★ 自校验，不过不输出
                continue
            out.append({"source_id": r["source_id"], "published_at": r.get("published_at", ""),
                        "title": r.get("title", "")[:60], "norm_offset": off,
                        "len": len(s), "quote": s})
            break                                           # 每份只取一条，保多样性
    if not out:
        print("**一条都没取到** —— 不是「没有引文」，是筛太紧（长度/坏行/第一人称）",
              file=sys.stderr)
        return 3

    out = out[:a.n]
    print(json.dumps({"lane": a.lane, "取到": len(out),
                      "★ 定位口径": "norm_offset 是 `re.sub(r'\\\\s+',' ',dehyphenate(正文))` 之后的字符偏移；"
                                   "校验：text[norm_offset:norm_offset+len(quote)] == quote",
                      "★ 本工具不判断": "这句是不是他说的、值不值得引 —— **人来判**",
                      "引文": out}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
