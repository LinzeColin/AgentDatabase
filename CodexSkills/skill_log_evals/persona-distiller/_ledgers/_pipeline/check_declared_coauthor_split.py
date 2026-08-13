#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_declared_coauthor_split.py —— **书自己在序言里写明「哪部分是谁写的」**

## 为什么有这件

2026-08-13 Dewey #190 阶段 3 取引文之前，打开《Ethics》(1908) 的序言，逐字读到：

> As to the respective shares of the work for which the authors are severally
> responsible, … **Part I. has been written by Mr. Tufts, Part II. by Mr. Dewey,
> and in Part III., Chapters XX. and XXI. are by Mr. Dewey, Chapters XXII.-XXVI.
> by Mr. Tufts.**

按这段声明逐段量：三份《Ethics》各 21 万词，**Tufts 占 50.7%**
（Part I 29.1% ＋ Part III 第 XXII–XXVI 章 21.6%），Dewey 只占 45.0%。
而台账把整册记成 `tier=P1`「他的」——**三份合计约 32.6 万词挂错了人。**

★ 这不是「著录字段有两个名字」那件事。全库 **376 行** `tier=P1` 而 `author` 有多位，
  绝大多数是**编者/译者**（`Lincoln, Abraham; Perry, Bliss, ed`、
  `Kant; Hartenstein`）——那种情况下主体确实是作者。
  真正致命的信号是**正文自己声明了分工**：一部合著书里，整整几部分是别人写的。
  [[creator-field-is-not-authorship]]、[[related-to-him-is-not-written-by-him]]

## 判什么

在每份语料的**前 10% 或前 15 万字符**（序言区）里找这类声明：

    Part I. has been written by Mr. Tufts
    Chapters XX. and XXI. are by Mr. Dewey
    the chapters on X are by Professor Y

命中且**归属人里出现主体以外的名字** ⇒ ✗ 红（rc=1）：这份语料里有明确不是他写的部分。

★ 本件**只报「书自己说了什么」**，不去判某一段到底是谁写的——
   那要靠分部边界，边界定位不到时**说未判，不许猜**。
   能定位到就顺带把词数占比算出来（Dewey 那三份就是这样量到 50.7% 的）。

★ 反过来也**不许**把「没找到声明」当成「没有合著」——
   没声明只是没证据，本件对它不置一词。[[negative-capability-claims-need-evidence-too]]

## 用法

    python3 check_declared_coauthor_split.py --workspace <工作区> --subject Dewey
    python3 check_declared_coauthor_split.py --scan _corpora
    python3 check_declared_coauthor_split.py --self-test

退出码：0＝没有「划归他人」的声明；1＝有；4＝读不到语料（**未判**）
"""
import argparse
import glob
import json
import os
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
CORPORA = HERE.parent.parent / "_corpora"

# 序言区：前 10%，但至少 20000、至多 150000 字符
def _front(text: str) -> str:
    return text[:max(20000, min(150000, len(text) // 10))]


# 「哪几部分 由 谁 写」——单元词 + 归属动词 + 人名
UNIT = r"(?:Parts?|Chapters?|Books?|Sections?|Appendix|Appendices)"
ROMAN = r"[IVXLCivxlc]+\.?"
# ★ 人名用**具名组**：`units` 是 (?P<units>…) 占了第 1 组，
#   写 `m.group(1)` 取到的是单元号（自测当场抓到：who 全成了 "I."／"XX. and XXI."）。
NAME = r"(?:Mr\.|Mrs\.|Miss|Dr\.|Prof(?:essor)?\.?|Sir)?\s*(?P<who>[A-Z][A-Za-z]{2,}(?:\s+[A-Z][A-Za-z]{2,})?)"
DECL = re.compile(
    rf"{UNIT}\s+(?P<units>{ROMAN}(?:\s*(?:,|and|to|-|–)\s*{ROMAN})*)\s*"
    rf"(?:has been|have been|is|are|was|were)?\s*(?:written\s+)?by\s+{NAME}",
    re.I)

# 「分工」这个话题本身的标记词——命中才认为这是一段分工声明，
# ★ 只靠上面的正则会把「Chapter X by Mr. Smith」这种**引用别人的书**也捞进来。
TOPIC = re.compile(
    r"respective shares|severally responsible|has been written by|"
    r"were written by|is by|are by|joint work|collaborat",
    re.I)


def declarations(text: str):
    """→ [(声明原句, 归属人)]。**纯函数**，只看序言区。"""
    front = _front(text)
    out = []
    for m in DECL.finditer(front):
        a = max(0, m.start() - 260)
        ctx = " ".join(front[a:m.end() + 60].split())
        if not TOPIC.search(ctx):
            continue                       # 不是分工声明，多半是在引用别人的书
        out.append((ctx[-300:], m.group("who").strip()))
    return out


def foreign(decls, subject: str):
    """→ 归属人里**不是主体**的那些（去重，保序）。"""
    sub = subject.lower()
    seen, out = set(), []
    for _, who in decls:
        w = who.lower()
        if sub in w or w in sub or w.split()[-1] == sub.split()[-1]:
            continue
        if w not in seen:
            seen.add(w)
            out.append(who)
    return out


def self_test() -> int:
    ok = t = 0

    def chk(d, c):
        nonlocal ok, t
        t += 1
        ok += 1 if c else 0
        print(f"  {'✓' if c else '✗'} {d}")

    # ★ 逐字取自《Ethics》(1908) src-dc899c319809 的序言
    real = ("As to the respective shares of the work for which the authors are "
            "severally responsible, while each has contributed suggestions and "
            "criticisms to the work of the other in sufficient degree to make the "
            "book throughout a joint work, Part I. has been written by Mr. Tufts, "
            "Part II. by Mr. Dewey, and in Part III., Chapters XX. and XXI. are by "
            "Mr. Dewey, Chapters XXII.-XXVI. by Mr. Tufts.")
    d = declarations(real)
    chk("★ 真例：《Ethics》序言那段必须被认出来", len(d) >= 1)
    chk("★ 真例：归属人里必须出现 Tufts（主体是 Dewey）",
        "tufts" in " ".join(x[1] for x in d).lower())
    chk("★ 真例：以 Dewey 为主体时，报出来的「他人」是 Tufts 而不是 Dewey",
        [w.lower() for w in foreign(d, "Dewey")] == ["tufts"])
    chk("★ 反向：以 Tufts 为主体时，报出来的是 Dewey",
        "dewey" in [w.lower() for w in foreign(d, "Tufts")])

    # ★ 负例①：引用别人的书，**不是**分工声明
    cite = ("For a fuller account see Chapter IV by Mr. Smith in the volume "
            "edited by the Society, and compare the bibliography below.")
    chk("★ 负例：正文里「Chapter IV by Mr. Smith」（引别人的书）不许报",
        not declarations(cite))

    # ★ 负例②：独著的序言
    solo = ("In preparing this book I have had the assistance of many friends, "
            "to whom my thanks are due. The whole of the work is my own.")
    chk("负例：独著序言不许报", not declarations(solo))

    # ★ 只看序言区：同样的句子放到正文很后面，不许报
    tail = "x " * 200000 + real
    chk("★ 只看序言区（前 10%／上限 15 万字符）——同句落在正文深处不许报",
        not declarations(tail))

    print(f"\n{'✓ 全过' if ok == t else f'✗ {t - ok}/{t} 项不符'}"
          "（真例逐字取自《Ethics》(1908) 的序言）")
    return 0 if ok == t else 1


def scan_ws(ws: pathlib.Path, subject: str):
    led = ws / "evidence/source-ledger.jsonl"
    if not led.is_file():
        return None
    hits = []
    for line in led.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        p = ws / (r.get("local_path") or "")
        if not p.is_file():
            continue
        d = declarations(p.read_text(encoding="utf-8", errors="replace"))
        if not d:
            continue
        fo = foreign(d, subject)
        if fo:
            hits.append({"source_id": r.get("source_id"), "tier": r.get("tier"),
                         "split": r.get("split"), "title": (r.get("title") or "")[:52],
                         "归给他人": fo, "声明原句": d[0][0][-220:]})
    return hits


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace")
    ap.add_argument("--subject", help="主体姓氏（如 Dewey）；缺省时从工作区目录名取最后一段")
    ap.add_argument("--scan", help="扫 _corpora 下全部工作区")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()

    targets = []
    if a.scan:
        for d in sorted(glob.glob(os.path.join(a.scan, "wip-*", "workspaces", "*"))):
            if os.path.isdir(d):
                targets.append(pathlib.Path(d))
    elif a.workspace:
        targets.append(pathlib.Path(a.workspace))
    else:
        print("★★ **未判**：要给 --workspace 或 --scan")
        return 4

    total, bad, nolead = 0, [], 0
    for ws in targets:
        subj = a.subject or ws.name.split("-")[-1]
        h = scan_ws(ws, subj)
        if h is None:
            nolead += 1
            continue
        total += 1
        for x in h:
            x["工作区"] = ws.name
            x["主体"] = subj
            bad.append(x)

    print(f"扫了 {total} 个有台账的工作区"
          f"{f'（另有 {nolead} 个没有台账，**未判**）' if nolead else ''}\n")
    if bad:
        print(f"✗ **{len(bad)} 份语料在序言里声明了分工，且有部分明确归给他人**：")
        for x in bad:
            print(f"  · {x['工作区']}／{x['source_id']}　tier={x['tier']} split={x['split']}")
            print(f"      {x['title']}")
            print(f"      归给：{'、'.join(x['归给他人'])}（主体 {x['主体']}）")
            print(f"      声明：…{x['声明原句']}")
    else:
        print("✓ 没有「书自己声明某部分归他人」的语料")
    print("\n★ 射程：只报**书自己说了什么**。没找到声明**不等于**没有合著"
          "——那只是没证据，本件对它不置一词。"
          "\n★ 分部边界能定位时才算词数占比；定位不到就说未判，**不许猜**。")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
