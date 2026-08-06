#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**声口不在人称里——量「立场句」，不只量第一人称。**

## 撞出它的那一段（Mehl #137，2026-08-06）

1936 年 Institute of Metals Division 具名荣誉讲演，开篇第一段：

> `IN examining the progress of metallurgical science, the critic must remember
> that most of our present knowledge of metals and alloys has been accumulated
> through the needs of industry and commerce rather than through the desire and
> efforts of a large body of scientists… The progress of metallurgy, scientifically
> speaking, has been irregular, and little given to the exhaustive exploitation
> of important scientific fields.`

**第一人称：0。** 而它命令读者怎么看（`the critic must remember`）、
对整个学科下评价（`has been irregular`）、把功劳从科学家挪给工业需求
（`rather than through the desire and efforts of…`）——**通篇是立场。**

**按第一人称密度算这段是 0；按「这是不是他在说话」算，这段满是他。**

## 为什么这件事要紧

**两条延后建在第一人称密度上**：

| 人物 | 依据 |
|---|---|
| C. L. Coffin #130 | 17 万字里实质第一人称 15 句（0.87/万字） |
| Edgar Bain #136 | 105 K 字符第一人称约 11 处 |

若那把尺量的是**代词**而不是**声口**，这两条都要重看（已记 ㉙ 待用户裁定）。
**本件不改任何处置**——它只把「立场句」这个量算出来，让判断有数可依。

## 判法：四类立场动作，各自独立计数

1. **指令读者**：`the critic must remember` / `it must be borne in mind` / `one should note`
2. **对领域或工作下评价**：`has been irregular` / `unsatisfactory` / `remarkable` / `unfortunate`
3. **更正与取舍**：`contrary to` / `it is a mistake to` / `far from satisfactory` /
   `not so much … as` / **`preferable to X rather than Y`**（只收带方法论口吻的这一种）
   ★ **裸 `rather than` 已删**——见下「首跑结果」，它在技术散文里是普通事实对比。
4. **有保留的判断**：`there can be little doubt` / `it seems clear` / `it is doubtful whether`

★★★ **不数被动式的「据观察」**——`it has been found that` 是转述不是立场。
★★ **不数普通比较级**——`higher than` 不是取舍。

## ★★★★ 首跑结果：**它没能解决 ㉙**——数太小、差距太窄

写它的动机是「第一人称密度可能量错了」。落地之后拿五个样本跑：

| 样本 | 字符 | 立场句 | 不含第一人称 | 每万字 |
|---|---|---|---|---|
| Bain 1928 独著 | 44,163 | 1 | 1 | 0.23 |
| Bain 1929 合著 | 10,413 | 0 | 0 | 0.0 |
| Bain 1930 合著正文 | 50,438 | 1 | 1 | 0.20 |
| Mehl 1939 合著正文 | 40,160 | 0 | 0 | 0.0 |
| **Mehl 1936 独著讲演** | 184,630 | **8** | 6 | **0.43** |

**差距只有 1.9 倍，绝对数是 8 句对 1 句。** 这个量级下不了任何处置结论。

★★ **收紧之前它报的是 5.4 倍**——那是假的：`rather than` 一条规则贡献了大半，
而它在技术散文里是**普通的事实对比**
（`Th atoms reach the surface of W in spurts rather than at a uniform rate`）。
**去读命中才发现 8 条例句里 5–6 条是假阳。**

### 所以本件的正确定位

- 它**不是**「声口」的度量，是**立场句的下限计数**；
- **它没有推翻也没有坐实第一人称那把尺**；
- 我读出来的那个分别（Mehl 讲演开篇通篇是判断、Bain 四件里读不到评价句）
  **是定性的，本件复现不了它**。

★★★ **不要拿本件的数去改任何处置。** ㉙ 仍然要人裁。

## 诚实边界（写在最前面，因为它决定这个数能不能用）

- **这是词表判据。** 本项目已经栽过：出戏门第一版词表把「谈语料」误判成出戏
  （见 `check_persona_frame_break.py`）。**词表能给出下限，给不出真值。**
- **不区分作者**：整份扫会把讨论段里别人的立场算进来。
  调用方**必须**先切出目标本人的段落（Bain 1930 那件 74% 是讨论段）。
- **只报不拦。**
"""

import argparse
import json
import pathlib
import re
import sys

# ── 四类立场动作。每条都能在原文里指出实例，不是想出来的。
DIRECTIVE = (
    # ★ 主动与被动都要收：`I must emphasize` 与 `it must be emphasized`。
    #   第一版只写了被动分词（`emphasi[sz]ed`），**主动式一条都不中**——自测抓到的。
    r"\b(?:must|should)\s+(?:be\s+)?(?:remember(?:ed)?|borne\s+in\s+mind|note[ds]?|"
    r"emphasi[sz]e[ds]?|recogni[sz]e[ds]?|conclude|admit)\b",
    r"\bone\s+(?:must|should|cannot)\b",
    r"\bit\s+(?:must|should)\s+be\s+(?:remembered|noted|emphasi[sz]ed|recogni[sz]ed)\b",
)
EVALUATIVE = (
    r"\b(?:has|have|had)\s+been\s+(?:irregular|unsatisfactory|disappointing|"
    r"remarkable|noteworthy|inadequate|unfortunate)\b",
    # ★★ `inadequate`／`striking` 单独出现时多半在描述**物**不是在评价**工作**：
    #   `even though its energy is inadequate`（描述能量）
    #   `The striking photograph presented several years ago by Dr.`（描述照片）
    #   —— 首跑各贡献 1 条假阳。**要求它修饰工作/领域/证据这类词。**
    r"\b(?:unsatisfactory|disappointing|inadequate|unfortunate|regrettable|admirable|"
    r"remarkable|crude)\s+(?:and\s+\w+\s+)?(?:work|study|treatment|evidence|"
    r"explanation|theory|data|results?|state\s+of|situation|literature)\b",
    r"\b(?:the|this|that|his|such)\s+(?:work|study|treatment|evidence|explanation|"
    r"theory|data|results?|literature|view|opinion|approach|position|account|"
    r"hypothesis|state\s+of\s+\w+)\s+(?:is|are|was|were|has\s+been|have\s+been)\s+"
    r"(?:unsatisfactory|disappointing|inadequate|unfortunate|crude|admirable|remarkable)\b",
    r"\blittle\s+given\s+to\b",
)
CORRECTIVE = (
    # ★★★ **`rather than` 单独一条已删。** 全库首跑当场证明它是噪声源：
    #   Mehl 1936 讲演 10 条「更正取舍」里，`rather than` 贡献的假阳有
    #     `Th atoms reach the surface of W in spurts rather than at a uniform rate`
    #     `takes place in the ratio given in the compound Mg2Si rather than according to…`
    #     `, rather than a unique constant.`
    #   ——**全是普通的事实对比，不是取舍立场。**
    #   还有 `This seems rather contradictory to…`：`rather` 是副词，
    #   被 `rather\s+than` 的宽松写法误伤。
    #   ★ 只保留**带方法论口吻**的那一种：`preferable to X rather than Y`
    #     （`it seems preferable to gather good experimental data rather than to
    #       hypothesize at great length` —— 这一条是真立场）。
    r"\b(?:preferable|better|wiser|more\s+profitable)\s+to\b[^.]{0,80}?\brather\s+than\b",
    r"\bcontrary\s+to\b",
    r"\bit\s+is\s+a\s+mistake\s+to\b",
    r"\bfar\s+from\s+(?:being|complete|satisfactory)\b",
    r"\bnot\s+so\s+much\s+.{0,40}?\bas\b",
)
HEDGED = (
    r"\bthere\s+(?:can\s+be|is)\s+little\s+doubt\b",
    r"\bit\s+seems?\s+(?:clear|probable|likely|doubtful)\b",
    r"\bit\s+is\s+doubtful\s+whether\b",
    r"\bin\s+the\s+writer'?s\s+(?:opinion|view|judgment)\b",
)
CLASSES = (("指令读者", DIRECTIVE), ("下评价", EVALUATIVE),
           ("更正取舍", CORRECTIVE), ("有保留的判断", HEDGED))

# ★★★ 明确**不算**立场的：转述式被动。写成负对照，防止把它加回来。
NOT_STANCE = (
    r"\bit\s+(?:has\s+been|was|is)\s+found\s+that\b",
    r"\bit\s+(?:has\s+been|was|is)\s+observed\s+that\b",
    r"\bit\s+(?:has\s+been|was|is)\s+shown\s+that\b",
)

FIRST_PERSON = re.compile(r"\b(?:I|we|my|our)\b")
_SENT = re.compile(r"[^.!?]{15,400}[.!?]")


def sentences(text):
    return [" ".join(m.group(0).split()) for m in _SENT.finditer(text)]


def classify(sent):
    """→ 命中的立场类别（可多类）。"""
    hit = []
    for name, pats in CLASSES:
        if any(re.search(p, sent, re.I) for p in pats):
            hit.append(name)
    return hit


def measure(text):
    ss = sentences(text)
    per_class = {name: 0 for name, _ in CLASSES}
    stance, stance_no_fp, examples = 0, 0, []
    for s in ss:
        c = classify(s)
        if not c:
            continue
        stance += 1
        for name in c:
            per_class[name] += 1
        if not FIRST_PERSON.search(s):
            stance_no_fp += 1          # ★ 这一栏是本件的要点
            if len(examples) < 8:
                examples.append({"类": c, "句": s[:190]})
    fp = len(FIRST_PERSON.findall(text))
    n = len(ss) or 1
    return {
        "字符": len(text), "句数": len(ss),
        "第一人称命中": fp,
        "**立场句**": stance,
        "★ 其中不含第一人称的": stance_no_fp,
        "逐类": per_class,
        "立场句占比": round(stance / n, 4),
        "每万字立场句": round(stance / max(1, len(text)) * 10000, 2),
        "例句（不含第一人称的）": examples,
    }


def self_test():
    bad = []

    def chk(lbl, ok):
        print(("  ✓ " if ok else "  ✗ ") + lbl)
        if not ok:
            bad.append(lbl)

    print("── ★★★ 正例：Mehl 1936 讲演开篇（第一人称 0，而通篇立场）──")
    mehl = ("IN examining the progress of metallurgical science, the critic must "
            "remember that most of our present knowledge of metals and alloys has "
            "been accumulated through the needs of industry and commerce rather than "
            "through the desire and efforts of a large body of scientists interested "
            "primarily in developing a science of metals. The progress of metallurgy, "
            "scientifically speaking, has been irregular, and little given to the "
            "exhaustive exploitation of important scientific fields.")
    r = measure(mehl)
    chk(f"认出立场句 {r['**立场句**']} 句（要 ≥2）", r["**立场句**"] >= 2)
    chk(f"其中不含第一人称的 {r['★ 其中不含第一人称的']} 句（要 ≥1）",
        r["★ 其中不含第一人称的"] >= 1)
    chk(f"指令读者 {r['逐类']['指令读者']}≥1", r["逐类"]["指令读者"] >= 1)
    chk(f"下评价 {r['逐类']['下评价']}≥1", r["逐类"]["下评价"] >= 1)
    # ★★★ **这一条从 ≥1 改成 ==0，并且是诚实的降级不是放水。**
    #   Mehl 开篇那句 `accumulated through the needs of industry and commerce
    #   rather than through the desire and efforts of a large body of scientists`
    #   **确实是立场**（把功劳从科学家挪给工业需求）。
    #   但它与下面这些**纯事实对比**的表面形态完全一样：
    #     `Th atoms reach the surface of W in spurts rather than at a uniform rate`
    #     `takes place in the ratio given in the compound Mg2Si rather than …`
    #   **词表分不开这两者。** 与其留一条 30% 精度的规则去虚报，
    #   不如**如实记下这一类抓不到**——本件因此是**下限**，不是真值。
    chk(f"更正取舍 {r['逐类']['更正取舍']}==0（★ 这一类词表分不开，已如实降级）",
        r["逐类"]["更正取舍"] == 0)

    print("\n── ★★★ 反例：纯转述的技术散文，一句都不许算立场 ──")
    tech = ("The specimens were heated to 900 C. and quenched in brine. It has been "
            "found that the rate of transformation increases with temperature. The "
            "diffusion coefficient was measured by the method of Matano. Values are "
            "given in Table 3. It was observed that the grain size decreased.")
    r2 = measure(tech)
    chk(f"技术散文立场句 {r2['**立场句**']}（要 0）", r2["**立场句**"] == 0)

    print("\n── ★★ 转述式被动**明确不算**（防止有人把它加回来）──")
    for p in NOT_STANCE:
        s = re.sub(r"\\b|\(\?:|\)|\\s\+", " ", p)
        probe = "It has been found that the alloy is stable."
        chk(f"`it has been found that…` 不算立场", not classify(probe))
        break
    chk("`it was shown that…` 不算立场",
        not classify("It was shown that the phase is metastable."))

    print("\n── ★ 反例：普通比较级不是取舍 ──")
    chk("`higher than` 不算",
        not classify("The value is higher than that reported by Smith."))

    print("\n── ★★ 第一人称句也能是立场句，但要单列 ──")
    r3 = measure("I must emphasize that this view is unsatisfactory.")
    chk(f"算作立场句（{r3['**立场句**']}）", r3["**立场句**"] >= 1)
    chk(f"但不计入「不含第一人称」那一栏（{r3['★ 其中不含第一人称的']}）",
        r3["★ 其中不含第一人称的"] == 0)

    if bad:
        print("\n未过：")
        for b in bad:
            print("  · " + b)
        return 2
    print("\n✓ 自测全过（5 正 + 4 反 + 2 条分栏）")
    return 0


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", nargs="?", help="要量的文本（**调用方须先切出目标本人的段落**）")
    ap.add_argument("--from-line", type=int, default=0)
    ap.add_argument("--to-line", type=int, default=0)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.file:
        ap.error("要么 --self-test，要么给文件")
    p = pathlib.Path(a.file)
    if not p.is_file():
        print(f"✗ {p} 不在——**未核验（不是通过）**", file=sys.stderr)
        return 2
    lines = p.read_text(encoding="utf-8", errors="replace").split("\n")
    if a.to_line:
        lines = lines[a.from_line:a.to_line]
    print(json.dumps(measure("\n".join(lines)), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
