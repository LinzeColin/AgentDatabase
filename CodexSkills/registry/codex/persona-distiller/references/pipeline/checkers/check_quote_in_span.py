#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**整版扫图里，引文有没有落在别人那一段。**

## 为什么有这道判据

`check_quote_integrity` 只问「这句在不在语料里」。
**整版扫图的语料里，「在」是不够的**——同一个 .txt 常常还装着同页别人的文章。

Fleming #111 实测：PMC 把旧 BMJ / Proc R Soc 按**整页**提供，
`penicillin-letter-1941` 那一份的下半版是**新西兰医院财政的另一篇**；
`freelance-science-1952` 同版还有 P. A. Gorer 的两篇书评。
从这些文件里取引文而不确认落在哪一段，
**会把别人的文字挂到本人物名下——而引文核查会说「在」。**

## 判据

读一份**作者边界清单**（`raw/_BOUNDARIES.json`），形如：

    {"penicillin-letter-1941": {"start_line": 68, "end_line": 196, ...}}

对每条逐字引文：若它出现在某个有边界记录的文件里，
就查它是否落在 `start_line..end_line` 之内。**落在外面即报。**

## 它判不了什么

- **没有边界记录的文件一概不判**——本判据不猜边界。
  清单要由读过原文的人写，且要留 `start_evidence` / `end_evidence` 供复核。
- 引文若在两份文件里都出现，只按第一份判。
"""
import argparse
import json
import pathlib
import re
import sys

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

Q = re.compile(
    r"[「\"“]\s*\*{0,2}([A-Za-zÀ-ÿ][^」\"”]{18,300})[」\"”]"
    r"|`\s*\*{0,2}([A-Za-zÀ-ÿ][^`]{18,400})`")
PROJ = re.compile(r"[^0-9A-Za-z]+")


def _p(s):
    return PROJ.sub("", s).lower()


def _q(m):
    for g in m.groups():
        if g:
            return g
    return ""


def collect_quotes(blobs):
    """→ [(来源标签, 引文)]。`blobs` 是 {标签: 文本}。"""
    out = []
    for tag, text in blobs.items():
        for m in Q.finditer(text or ""):
            s = _q(m)
            if len(_p(s)) >= 25:
                out.append((tag, s))
    return out


def locate(corpus_dir, name):
    """按**原文件名**递归找，不假设目录布局。

    ★ 接线负对照当场抓出来的：抓源目录是 `raw/<名>/<名>.txt`，
    而**工作区里是 `raw/src-<hash>/<原名>.txt`**。
    第一版写死 `cache/<名>/<名>.txt`，在工作区上一条也找不到，
    于是打印「其中 0 条出现在有边界记录的文件里」——**看起来像没问题。**
    """
    root = pathlib.Path(corpus_dir)
    direct = root / name / f"{name}.txt"
    if direct.is_file():
        return direct
    for f in root.rglob(f"{name}.txt"):
        return f
    return None


def check(quotes, spans, corpus_dir):
    """→ (查过的条数, [(来源, 文件, 引文)])——列出落在别人那一段里的。"""
    checked, bad = 0, []
    for tag, q in quotes:
        pq = _p(q)
        for name, b in spans.items():
            f = locate(corpus_dir, name)
            if not f:
                continue
            lines = corpus_body(f.read_text(encoding="utf-8", errors="replace")).split("\n")
            if pq not in _p("\n".join(lines)):
                continue
            checked += 1
            inside = _p("\n".join(lines[b["start_line"] - 1:b["end_line"]]))
            if pq not in inside:
                bad.append((tag, name, q[:90]))
            break
    return checked, bad


# ══════════════════ 自测 ══════════════════

def selftest() -> int:
    import tempfile
    fails = []

    def chk(label, cond):
        print(("  ✓ " if cond else "  ✗ ") + label)
        if not cond:
            fails.append(label)

    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        (root / "page").mkdir()
        # 一份整版扫图：前半是他的信，后半是别人的另一篇
        (root / "page" / "page.txt").write_text(
            "HEADER LINE\n"
            "I think, however, I can claim some merit in the discovery here.\n"
            "ALEXANDER FLEMING.\n"
            "NEW ZEALAND HOSPITAL FINANCE\n"
            "The subsidy is five shillings per bed for returned soldiers here.\n",
            encoding="utf-8")
        spans = {"page": {"start_line": 1, "end_line": 3}}

        print("── 正向：引文落在别人那一段 ──")
        n, bad = check([("答案/x", "The subsidy is five shillings per bed for returned soldiers")],
                       spans, root)
        chk(f"下半版的句子 → 报出（查过 {n} 条）", n == 1 and len(bad) == 1)

        print("── 反向对照 ①：引文落在他那一段，不许报 ──")
        n, bad = check([("答案/y", "I can claim some merit in the discovery here")], spans, root)
        chk("他那一段里的句子 → 不报", n == 1 and not bad)

        print("── 反向对照 ②：没有边界记录的文件一概不判 ──")
        n, bad = check([("答案/z", "The subsidy is five shillings per bed for returned soldiers")],
                       {}, root)
        chk("清单为空 → 查过 0 条、不报", n == 0 and not bad)

        print("── 反向对照 ③：语料里根本没有的句子不算越界 ──")
        n, bad = check([("答案/w", "This sentence does not appear anywhere in the corpus at all")],
                       spans, root)
        chk("语料里没有 → 不计入、不报（那是 check_quote_integrity 的活）",
            n == 0 and not bad)

        print("── 反向对照 ④：太短的引文不判（噪声太大）──")
        qs = collect_quotes({"a": "他说 `short one` 就完了。"})
        chk("投影后不足 25 字符 → 不收集", not qs)

        print("── 反向对照 ⑤：**工作区布局也要找得到**（接线负对照抓出来的）──")
        (root / "src-abc123def456").mkdir()
        (root / "src-abc123def456" / "page.txt").write_text(
            (root / "page" / "page.txt").read_text(encoding="utf-8"), encoding="utf-8")
        import shutil
        shutil.rmtree(root / "page")
        n2, bad2 = check([("答案/x", "The subsidy is five shillings per bed for returned soldiers")],
                         spans, root)
        chk("语料在 `src-<hash>/<原名>.txt` 下 → 仍找得到并报出", n2 == 1 and len(bad2) == 1)
        (root / "page").mkdir()
        (root / "page" / "page.txt").write_text(
            (root / "src-abc123def456" / "page.txt").read_text(encoding="utf-8"), encoding="utf-8")

        print("── 反向对照 ⑥：边界恰好含首尾行 ──")
        n, bad = check([("答案/v", "I think, however, I can claim some merit in the discovery")],
                       {"page": {"start_line": 2, "end_line": 2}}, root)
        chk("单行边界也要算对", n == 1 and not bad)

    print(f"\n{'✓ 自测全过' if not fails else f'✗ **{len(fails)} 项未过**'}")
    return 0 if not fails else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--answers", help="{case_id: 答案} 的 JSON")
    ap.add_argument("--claims", help="claims.jsonl")
    ap.add_argument("--boundaries", help="作者边界清单 JSON")
    ap.add_argument("--cache", help="语料目录（含 <名>/<名>.txt）")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return selftest()
    if not (a.boundaries and a.cache):
        ap.error("要么 --self-test，要么同时给 --boundaries 与 --cache")

    bp = pathlib.Path(a.boundaries)
    if not bp.is_file():
        print(f"✗ **{a.boundaries} 不在——本次未检查（不是通过）**")
        return 3
    spans = {k: v for k, v in json.loads(bp.read_text(encoding="utf-8")).items()
             if isinstance(v, dict) and v.get("start_line") and v.get("end_line")}
    if not spans:
        print(f"✗ **{a.boundaries} 里没有一条可用的边界记录——本次未检查（不是通过）**")
        return 3

    blobs = {}
    if a.answers:
        for k, v in json.loads(pathlib.Path(a.answers).read_text(encoding="utf-8")).items():
            blobs["答案/" + k] = v
    if a.claims:
        for line in pathlib.Path(a.claims).read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                blobs["断言/" + r["claim_id"]] = r.get("claim", "")
    if not blobs:
        print("✗ **答案与断言都没给——本次未检查（不是通过）**")
        return 3

    quotes = collect_quotes(blobs)
    checked, bad = check(quotes, spans, a.cache)
    print(f"逐字引文 {len(quotes)} 条；其中 {checked} 条出现在有边界记录的文件里")
    if not checked:
        print("  ⚠ **没有一条引文落在有边界记录的文件里**——"
              "本判据这一轮什么也没查到，不构成通过")
        return 0
    if bad:
        print(f"\n✗ **{len(bad)} 条引文落在别人那一段里**——"
              "整版扫图同页有别的文章，引它等于把别人的文字挂到本人物名下：")
        for tag, name, q in bad:
            print(f"    {tag}　@{name}\n        {q}")
        return 1
    print("  ✓ 每一条都落在本人物的那一段里")
    return 0


if __name__ == "__main__":
    sys.exit(main())
