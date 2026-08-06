#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**门数的是「有几份来源」，不是「有几句他的话」**——语料够门，声口不够。

## 撞出它的那一次（Coffin #130，2026-08-05，**在写断言之前**）

三道 quick 门**全过**：

| 项 | 实测 | 门 | |
|---|---|---|---|
| 来源数 | 18 | ≥8 | ✓ |
| 道数 | 3 | ≥3 | ✓ |
| 一手占比 | 15/18 = 83.3% | ≥0.40 | ✓ |

**而整份语料（172,138 字符）里，他自己说的实质的话只有 15 句**（0.87/万字）。
★ 我第一版报的是「8 句」——**那是本件早期正则漏数的结果**，见下「为什么裸数会骗人」末段。

因为那 18 份里 14 份是**专利说明书**——文体决定了它几乎全是第三人称的装置描述
加权利要求样板。**每多抓一件专利，来源数 +1，而他的话几乎 +0。**
实测：最长的两份（32k / 35k 字符）**各只有 1 句**实质第一人称。

抓源方为此把 `conversations` 一道找遍了（AIEE vols 4/6/7/8、ASME vol 10、
1918–1921 三部书、1913 年 NYPL 书目），**没有一份是他开口说话的**。
（AIEE 里的每一个「Coffin」都是 `CoFFIN, CHAs. A.`——汤姆森—休斯顿的副总裁兼司库，**另一个人**。）

## ★★★ 为什么裸数「I」会骗人（75% 是噪音）

第一版我量出 118 处第一人称，密度 7.2/万字，**差点当成「够用」写进风险单**。
去看样本才发现：**OCR 把零件标号读成了 `I`**——
`anvil I-I`、`extensions I and J`、`I serving to force the ends together`。

| | 数 |
|---|---|
| 裸 `\\bI\\b` | 118 |
| **其中零件标号等噪音** | **89（75%）** |
| 动词锚定（`I have`／`I find`／`I prefer`…） | 16 |
| 其中权利要求套语 | 6 |
| **实质** | **8** |

→ 本判据**只数动词锚定的、且不是套语的**。裸数一律不报。

## 它报什么

按源报实质第一人称句数与密度（每万字），并给出**逐句原文**——
**不给数就下结论是不许的，所以它必须能出示那几句。**

## ★★ 全库普查实测（2026-08-05，10 个有语料的工作区）

**只在体裁与语言都可比时才有意义。** 清楚是英文、且构成相近的几个：

| 工作区 | 源 | 正文字符 | 实质句 | 密度 |
|---|---|---|---|---|
| **wip-coffin-130** | 18 | 172,138 | 15 | **0.87** ⚠ |
| wip-carver-127 | 38 | 1,172,699 | 225 | 1.92 |
| wip-thomson-129 | 53 | 918,922 | 391 | **4.25** |
| wip-blackwell-118 | 89 | 8,094,123 | 3,882 | 4.80 |
| wip-lister-108 | 60 | 22,109,350 | 11,296 | 5.11 |

**Coffin 比同族的 Thomson 薄 5 倍**——两人同为焊接、同时代、同为英文，
差别就在 Thomson 有学会讨论记录而 Coffin 只有专利。**这一栏正是为此而设。**

### ★★★ 两条不可信，不许当结论用

- **非英文一律不给数**：Mendel #125（德文，15,789,533 字符）曾报「实质 0 句」、
  Pasteur #106、Semmelweis #105 同理。**那不是声口薄，是判据不认识那门语言。**已加语言护栏。
- **混语语料的判定不可靠**：Koch #107（120 源 / 2 亿字符 / 0.07）与 Liebig #124（0.47）
  仍被判为英文并打上「薄」，而两人都是德语人物、语料里多半掺着英译与英文二手件。
  本件的语言判定**只抽前 6 份各 2 万字**，抽到英文就整份算英文。
  **→ 这两条的「薄」不作数。** 要作数得逐份判语言，本件还没做。

## ★ 它不做什么

- **不拦。** 密度低不等于做不成：分析型产物、第三人称产物本来就不靠第一人称
  （见 `check_persona_frame_break` 的 `analytic` 模式）。**它只把数摆出来。**
- **不判「够不够」。** 够不够取决于要出哪些用例——
  `voice`／`trajectory`／`contrast` 要他谈自己，`known`／`tool-use` 只要他讲做法。
"""
import argparse
import json
import pathlib
import re
import sys

# 只认动词锚定的第一人称——裸 `I` 在 OCR 语料里 75% 是零件标号
VERB = (r"\bI (?:have|had|am|was|claim|find|found|prefer|may|make|made|use|used|do|did|"
        r"desire|employ|shown|show|believe|consider|know|knew|think|thought|wish|intend)\b")
# ★★★ **不许写 `[^.]{0,110}…[^.]{0,110}\.`**——两侧都是可变长否定字符类，
#   在几十万字的语料上会灾难性回溯。实测：Thomson #129 的 1,030,112 字符**直接跑不完**
#   （2 分钟超时），而本件已经接进研究门——**那等于把门挂死**。
#   （与 RUNBOOK 第六十八种同一种病：可变长字符类相邻。）
#   改法：**只用正则找动词锚点，上下文用字符串切片取**，全程线性。
_ANCHOR = re.compile(VERB)
# 专利/论文的套语——是他的字，但**不是他的话**
BOILER = re.compile(r"(What I claim|I claim as my invention|desire to secure by Letters Patent|"
                    r"Be it known that I|I, the undersigned)", re.I)
# ★★ **指示性**第一人称——是他的字，但不含任何主张：
#   `I have shown the conductor ... in Fig. 2`（指图）、
#   `In testimony whereof I have hereunto set my hand`（签署套语）、
#   `as I have described above`（回指本文）。
#   抓源方独立复量时把这类单列（~23 里约 10 句），**不单列就会高估声口**。
DEICTIC = re.compile(
    r"(In testimony whereof|hereunto set my hand|"
    r"I have (?:shown|illustrated|described|indicated|represented|designated)\b|"
    r"as I have (?:said|stated|shown|described)\b|"
    r"I have (?:not )?(?:herein|above|hereinbefore))", re.I)
HDR = "=" * 40          # 抓源方写的表头与正文的分隔线


def body_of(text: str) -> str:
    """剥掉抓源方自己写的表头——**表头里的字不是文献的字**。"""
    return text.split(HDR, 1)[-1] if HDR in text else text


def scan_text(text: str) -> dict:
    b = re.sub(r"\s+", " ", body_of(text))
    raw = len(re.findall(r"\bI\b", b))
    subs, deictic = [], []
    for m in _ANCHOR.finditer(b):
        a = b.rfind(".", 0, m.start())          # 上一个句点之后
        z = b.find(".", m.end())                # 下一个句点
        seg = b[(a + 1 if a >= 0 else 0):(z + 1 if z >= 0 else len(b))].strip()
        if len(seg) > 320:                      # 句子过长多半是没断开的 OCR 块，截一下
            seg = seg[:320]
        if BOILER.search(seg):
            continue
        (deictic if DEICTIC.search(seg) else subs).append(seg)
    # ★ 套语独立数，**不依赖 SENT 先匹配上**——
    #   `Be it known that I, CHARLES L. COFFIN, of Detroit, have invented…`
    #   的动词离 `I` 太远，SENT 根本不匹配，若挂在 SENT 下面就永远数不到它。
    #   （自测反向对照②当场抓到：期望 ≥2 而只得 1。）
    boil = len(BOILER.findall(b))
    return {"chars": len(b), "raw_I": raw, "boilerplate": boil,
            "deictic": deictic, "substantive": subs}


# ★★★ **本件只会量英文。** 全语料普查时实测：Mendel #125（德文）在 15,789,533 字符里
#   报「实质 0 句」，Koch #107（德文）2 亿字符报 0.07/万字——**那不是声口薄，是判据不认识那门语言**。
#   德文的 `ich habe`、法文的 `j'ai`、俄文的 `я`，本件一个都不认。
#   → 非英文语料一律报**不适用**，不给数。**给了数就会被人当成薄。**
_EN = re.compile(r"\b(the|and|of|that|which|with|from|this|is|are|was|were)\b", re.I)


def looks_english(text: str) -> bool:
    """粗判是不是英文——每万字至少 60 个常见英文虚词。**只用来决定报不报数。**"""
    n = len(text) or 1
    return len(_EN.findall(text)) / n * 10000 >= 60


def scan(root: pathlib.Path) -> dict:
    files = sorted(p for p in root.rglob("*.txt") if p.name != "_ids.txt")
    per, tot_c, tot_raw, tot_b, tot_d, allsub = [], 0, 0, 0, 0, []
    for f in files:
        r = scan_text(f.read_text(encoding="utf-8", errors="replace"))
        tot_c += r["chars"]
        tot_raw += r["raw_I"]
        tot_b += r["boilerplate"]
        tot_d += len(r["deictic"])
        allsub += [(f.parent.name, s) for s in r["substantive"]]
        per.append({"源": f.parent.name, "字符": r["chars"],
                    "裸I": r["raw_I"], "实质": len(r["substantive"])})
    n = len(allsub)
    sample = ""
    for f in files[:6]:
        sample += body_of(f.read_text(encoding="utf-8", errors="replace"))[:20000]
    if sample and not looks_english(sample):
        return {"语料": str(root), "源数": len(files), "正文字符": tot_c,
                "**本判据不适用**": "**这份语料不是英文。** 本件只认英文的第一人称动词锚点"
                                     "（`I have`／`I find`／`I prefer`…），"
                                     "德文 `ich habe`、法文 `j'ai`、俄文 `я` **一个都不认**。\n"
                                     "★ 实测：Mendel #125（德文）15,789,533 字符报「实质 0 句」、"
                                     "Koch #107（德文）2 亿字符报 0.07/万字——**那不是声口薄，"
                                     "是判据不认识那门语言。给了数就会被人当成薄。**",
                "**实质第一人称句**": None, "**密度（每万字）**": None}
    out = {
        "语料": str(root),
        "源数": len(files),
        "正文字符": tot_c,
        "裸 I 命中": tot_raw,
        "★ 其中噪音（零件标号等，近似）": f"{max(0, tot_raw - n - tot_b)}"
                                    f"（{max(0, tot_raw - n - tot_b) / max(tot_raw,1):.0%}）"
                                    "——OCR 把 `anvil I-I`／`extensions I and J` 读成第一人称",
        "套语（是他的字，不是他的话）": tot_b,
        "指示性（指图/签署/回指，不含主张）": tot_d,
        "**实质第一人称句**": n,
        "**密度（每万字）**": round(n / max(tot_c, 1) * 10000, 2),
        "逐句原文": [f"[{w}] {s[:150]}" for w, s in allsub[:40]],
        "逐源": sorted(per, key=lambda x: -x["实质"])[:12],
        "★ 口径": ("**只报不拦。** 密度低不等于做不成——分析型／第三人称产物本来就不靠第一人称。"
                   "够不够取决于要出哪些用例：`voice`/`trajectory`/`contrast` 要他谈自己，"
                   "`known`/`tool-use` 只要他讲做法。"),
    }
    if n and tot_c:
        out["★★ 参照"] = ("Coffin #130 实测 **8 句 / 0.5 每万字**——三道 quick 门全过，"
                          "而他自己说的实质的话只有 8 句。**门数的是来源，不是声口。**")
    return out


def self_test() -> int:
    ok = True

    def chk(m, c):
        nonlocal ok
        ok = ok and bool(c)
        print(("  ✓ " if c else "  ✗ ") + m)

    print("── ★★★ 正向：Coffin #130 那 8 句里的三句必须认出来 ──")
    r = scan_text('Of course in using the word "vacuum" I do not mean absolute vacuum, '
                  "but that which is ordinarily obtained by the use of an air-pump. "
                  "but I prefer chloridation roasting. "
                  "The construction and use of leaching vats are so well known that "
                  "I have not deemed it necessary to illustrate them.")
    chk(f"三句全中：{len(r['substantive'])}", len(r["substantive"]) == 3)

    print("\n── ★★★ 反向对照①：**OCR 把零件标号读成 I，一句都不许算** ──")
    r = scan_text("R represents an upright arm on base C, carrying an anvil I-I, "
                  "insulated from arm P. M and N are tapped through the extensions I and J. "
                  "I serving to force the ends of the hoop together to form the weld.")
    chk(f"裸 I 命中 {r['raw_I']} 处而实质 {len(r['substantive'])} 句",
        r["raw_I"] >= 3 and len(r["substantive"]) == 0)

    print("\n── ★★ 反向对照②：权利要求套语是他的字，**不是他的话** ──")
    r = scan_text("What I claim as my invention, and desire to secure by Letters Patent, is—1. "
                  "Be it known that I, CHARLES L. COFFIN, of Detroit, have invented certain new "
                  "and useful Improvements.")
    chk(f"套语 {r['boilerplate']} 句、实质 {len(r['substantive'])} 句",
        r["boilerplate"] >= 2 and len(r["substantive"]) == 0)

    print("\n── ★★ 反向对照③：**抓源方写的表头不算语料** ──")
    head = ("SOURCE: US Patent 428,459\nINVENTOR: Charles L. Coffin, of Detroit\n"
            "NOTE: I have reproduced the OCR verbatim and I prefer not to correct it.\n"
            + "=" * 40 + "\nUNITED STATES PATENT OFFICE.")
    r = scan_text(head)
    chk(f"表头里的两句第一人称被剥掉：实质 {len(r['substantive'])}", len(r["substantive"]) == 0)

    print("\n── ★ 反向对照④：正常第一人称叙述要数得出来 ──")
    r = scan_text("I have tried that with considerable success. I find the arc steadier. "
                  "I prefer a soft under carbon.")
    chk(f"三句：{len(r['substantive'])}", len(r["substantive"]) == 3)

    print("\n── ★★★ 反向对照⑤：**非英文语料一律报不适用，不许给数** ──")
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        d = pathlib.Path(td) / "src-de"
        d.mkdir(parents=True)
        (d / "a.txt").write_text(
            "Es ist mir gelungen, die Versuche mit Erbsen so anzustellen, dass ich habe "
            "beobachten koennen, wie sich die Merkmale in den folgenden Generationen "
            "verhalten. Ich habe dabei stets dieselbe Sorte verwendet. " * 20,
            encoding="utf-8")
        r = scan(pathlib.Path(td))
        chk(f"判为不适用：{'**本判据不适用**' in r}", "**本判据不适用**" in r)
        chk(f"不给数：{r.get('**实质第一人称句**')}", r.get("**实质第一人称句**") is None)

    print("\n── ★ 反向对照⑥：英文语料照常给数 ──")
    with tempfile.TemporaryDirectory() as td:
        d = pathlib.Path(td) / "src-en"
        d.mkdir(parents=True)
        (d / "a.txt").write_text(
            "The apparatus which is shown in the drawing is of the kind that was used "
            "with the current from the machine. I prefer a soft under carbon. " * 20,
            encoding="utf-8")
        r = scan(pathlib.Path(td))
        chk(f"给了数：实质 {r.get('**实质第一人称句**')} 句", isinstance(r.get("**实质第一人称句**"), int))

    print("\n" + ("✓ 自测全过" if ok else "✗ 自测未过"))
    print("\n══ ★★★★ **真实样本**：Rosenhain #138 语料逐字（含真实的跨行与断字）══")
    # 今天最要紧的一处更正全建在本判据上：探测报「第一人称 4.01」，实测 **0.10**——
    # 那个 4.01 是 `we/our/us` 的密度。**下面三段把这个区分钉死。**
    # 逐字取自 `_corpora/wip-rosenhain-138/.../raw/`，**连换行与 `try¬ ing` 的断字一起**。
    import tempfile as _tf4, os as _os4, pathlib as _pl4
    _REAL_FP = [
        # ★ editorial we —— **不该算第一人称**。这一句正是探测把 4.01 当成第一人称的来源。
        ("Perhaps this purely scientific aspect of our subject may with \n"
         "advantage be dealt with first. While the greatest practical \n"
         "importance obviously attaches to a deeper knowledge of metals",
         0, "editorial we（Metallurgy 1914）——**不算第一人称**"),
        # ★★ 真第一人称 —— 该算。三句都出自 1902 年那封 Nature 来信（全语料唯一密集处）
        ("desire to see a more efficient use made of our coal-supply, I yet \n"
         "think that he has drawn far too gloomy a picture of the future, \n"
         "and I wish to draw attention to a consideration",
         1, "`I yet think`（1902 Nature 来信）——**跨行**，该算"),
        ("I should like to add that what I have said in this letter does \n"
         "not at all lessen the urgency of Prof. Perry's plea",
         1, "`I should like to add`——该算"),
    ]
    for _txt, _min, _why in _REAL_FP:
        _r4 = scan_text(_txt)
        _sub = _r4.get("substantive")          # ★ 它是**句子列表**，不是计数
        _n = len(_sub) if isinstance(_sub, (list, tuple)) else int(_sub or 0)
        chk(f"{_why}（实质句 {_n}，要 {'≥1' if _min else '=0'}）",
            (_n >= 1) if _min else (_n == 0))

    return 0 if ok else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("corpus", nargs="?", help="语料目录（递归找 *.txt）")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.corpus:
        ap.error("要么 --self-test，要么给语料目录")
    p = pathlib.Path(a.corpus)
    if not p.is_dir():
        print(json.dumps({"状态": f"**未核（不是通过）**：{p} 不是目录"}, ensure_ascii=False))
        return 3
    print(json.dumps(scan(p), ensure_ascii=False, indent=2))
    return 0                      # **只报不拦**


if __name__ == "__main__":
    sys.exit(main())
