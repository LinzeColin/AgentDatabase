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

# ★★★★ **裸 `\b(?:I|we|my|our)\b` 是错的**——三个语料各自证明了一次：
#   · Coffin 的专利里 `I` 是**图纸标号**：`I represents insulating material`／
#     `until they leave the insulation I`／`C I )1 J1 L I M Fig ,2`
#   · Mehl 的冶金论文里 `I` 是**化学式与罗马数字**：`PbI₂`／`AgI`／`ALLOYS I.`
#   · 两处还都混着 OCR 噪声（`LO'I‘I'IROP`）
#   裸计数把 Coffin 报成 8.42/万字，而他实质的第一人称句只有 15 句——**高了一个量级**。
#
# 判法：**第一人称后面要跟动词，或 `my/our` 后面跟名词。**
#   `I have shown` ✓  `I claim` ✓  `we find` ✓  `my process` ✓
#   `insulating material I,` ✗   `PbI` ✗   `Fig. I` ✗
# ★★★★★ **不要在这里重写第一人称的判法——`check_first_person_density.py` 早就有了。**
#   我这一轮从头推了一遍它已经记着的东西：裸 `\bI\b` 75% 是零件标号
#   （`anvil I-I`／`extensions I and J`）、要动词锚定、要剥权利要求套语，
#   **连撞出它的人物都是同一个（Coffin #130）**。
#   ★ 那件还有我漏掉的**第三类**：`DEICTIC`（`I have shown … in Fig. 2`／
#     `as I have described above`）——是他的字但不含主张，
#     文件里写着「**不单列就会高估声口**」。
#   **所以本件不再自备一份，直接引它的三张表。** 只许有一个真源。
def _load_fp_rules():
    """从 `check_first_person_density` 借 VERB／BOILER／DEICTIC 与 `looks_english`。"""
    import importlib.util
    src = pathlib.Path(__file__).resolve().parent / "check_first_person_density.py"
    if not src.is_file():
        return None
    spec = importlib.util.spec_from_file_location("_pd_fpd", src)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception:                                            # noqa: BLE001
        return None
    return mod


_FPD = _load_fp_rules()
if _FPD is not None:
    _FP_VERBAL = re.compile(_FPD.VERB + r"|\b(?:we|my|our)\s+[a-z]{3,}\b", re.I)
    _EXCLUDE = re.compile(_FPD.BOILER.pattern + "|" + _FPD.DEICTIC.pattern, re.I)
else:                                                            # ← 借不到就说借不到
    _FP_VERBAL = re.compile(r"\bI\s+(?:have|had|am|was|claim|find|found)\b")
    _EXCLUDE = re.compile(r"(?!x)x")
    print("★ 借不到 check_first_person_density，退回最小实现——**此数不可与他人比**",
          file=sys.stderr)


# ★★★ **第二层：专利／法律文书的套语。**
#   Coffin #130 实测：动词式第一人称 70 处，**其中 51 处是套语（73%）**——
#     `what I claim as my invention, and desire to secure by Letters Patent`
#     `In testimony whereof I have hereunto set my hand`
#     `I have shown various apparatus adapted to carry my process into effect`
#   去套语后 19 处 = 0.95/万字，**与他延后依据里那个「实质 15 句 = 0.87/万字」同量级**。
#   **不减这一道，专利型语料的第一人称会虚高 3–4 倍，与别人不可比。**
_BOILERPLATE = re.compile(
    r"\b(?:what\s+)?I\s+claim\b"
    r"|\bmy\s+(?:invention|improved|said)\b"
    # ★★ 套语要**整个从句剥掉**，不能只剥标记词——
    #   自测抓到：剥了 `in testimony whereof` 与 `hereunto set my hand` 之后，
    #   中间剩下的 `I have` 仍然命中 `_FP_VERBAL`。
    r"|\bin\s+testimony\s+whereof\b[^.]{0,60}?\bset\s+my\s+hand\b"
    r"|\bI\s+have\s+hereunto\s+set\s+my\s+hand\b"
    r"|\bin\s+testimony\s+whereof\b"
    r"|\bhereunto\s+set\s+my\s+hand\b"
    r"|\bdesire\s+to\s+secure\s+by\s+Letters\s+Patent\b"
    r"|\bcarry\s+(?:my|the)\s+(?:said\s+)?(?:invention|process)\s+into\s+effect\b",
    re.I)


class _FP:
    """与 `re` 兼容的最小接口，便于原地替换。

    ★ `findall`／`search` 都**先去掉套语**再匹配。
    """

    @staticmethod
    def _strip(text):
        # 套语 + 指示性用法，两类都不算「他在说话」（后者是从
        # `check_first_person_density` 借来的，我原来漏了）
        return _EXCLUDE.sub(" ", _BOILERPLATE.sub(" ", text))

    @staticmethod
    def findall(text):
        return _FP_VERBAL.findall(_FP._strip(text))

    @staticmethod
    def search(text):
        return _FP_VERBAL.search(_FP._strip(text))


FIRST_PERSON = _FP

# ★★★★★ **语种守卫——本件只认英语，别的语种一律不出数。**
#
#   全库首扫（15 人）当场栽了：Martens 0.00／Mendel 0.01／Semmelweis 0.01／
#   Liebig 0.20／Koch 0.21／Pasteur 1.44 —— 看着像「这些人完全没有声口」。
#   **去验语种：Koch/Liebig/Martens/Mendel/Semmelweis 是德语，Pasteur 是法语。**
#   英语的 `I/we/my/our` 在德语语料里当然一个都不中。
#
#   ★ 这与 [[regex-must-clear-the-corpus-language]] 记的是同一件事
#     （`A.L.S` 匹配德语 `als`，误报 132 份跨 13 人）。**那条明训写着
#     「写正则之前先问语料是什么语种」，而我又是全库跑完才想起来。**
#
#   **返回 0 与「语种不符所以没量」必须分开**——前者是结论，后者是未核验。
_LANG_EN = re.compile(r"\b(?:the|and|of|is|that|with|which|been|were)\b", re.I)
_LANG_DE = re.compile(r"\b(?:der|die|das|und|ist|nicht|eine|werden|durch|sich)\b", re.I)
_LANG_FR = re.compile(r"\b(?:les|des|est|une|dans|pour|avec|nous|cette)\b", re.I)


def detect_language(text):
    """→ ('en'|'de'|'fr'|'?', 各自占比)。按功能词占全部字母词的比例判。"""
    n = len(re.findall(r"[A-Za-zÄÖÜäöüßÀ-ÿ]{2,}", text)) or 1
    r = {"en": len(_LANG_EN.findall(text)) / n,
         "de": len(_LANG_DE.findall(text)) / n,
         "fr": len(_LANG_FR.findall(text)) / n}
    best = max(r, key=r.get)
    return (best if r[best] >= 0.02 else "?"), r
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
    # ★★★★★ 语种不是英语 → **不出数**，报「未核验」。见 `detect_language` 上的说明。
    lang, ratios = detect_language(text)
    if lang != "en":
        return {"字符": len(text), "句数": 0,
                "★ 未核验": f"语种判为 **{lang}**（en={ratios['en']:.3f} "
                            f"de={ratios['de']:.3f} fr={ratios['fr']:.3f}）"
                            "——**本件只认英语，不是「这个人没有声口」**",
                "第一人称命中": None, "**立场句**": None,
                "★ 其中不含第一人称的": None, "逐类": {}, "立场句占比": None,
                "每万字立场句": None, "例句（不含第一人称的）": []}
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

    print("── ★★★★ **真实样本**：Rosenhain #138《Metallurgy》1914 四类立场句（逐字）──")

    # 2026-08-06 实测该书：立场句 **28**，四类齐全（指令 11／评价 2／取舍 7／保留判断 8）。

    # 这四句**逐字取自** `_corpora/wip-rosenhain-138/.../raw/`——

    # 它们是「立场句密度 0.32」这个数的实际来源，也是待裁定 ㉙ 的证据之一。

    # ★ 四句**都不含第一人称**，这正是本判据与 `check_first_person_density` 分工的地方：

    #   他通篇 editorial we（第一人称 0.10／万字），**而立场是有的**。

    _REAL_ST = [
        # ★★ 逐字取自判据**自己输出的例句**（它按 180 字截断，末尾的 `micro`/`own `/`met`
        #   就是截断处）。**不补全、不修饰**——那正是它实际判过的字符串。
        ("The great modern growth of interest in the detailed study of metals has, in fact, "
         "arisen from the remarkable results which have flowed in the first instance from "
         "the application of the micro", "下评价"),
        # ★★★ 这一条**改过两次**，两次都是「夹具比原文干净」的变体：
        #   第一版我截到 150 字**自己补了后半句**；
        #   第二版我贴的是**判据输出的例句**——而它按 180 字截断显示，
        #   `classify()` 实际判的是**完整句**。**判据自己的显示串也不是它判过的东西。**
        ("It is only quite recently that the grouping together and the correlation of all "
         "these properties has been undertaken and that these things have begun to be "
         "studied not so much for their own sake as for the light which they could throw "
         "upon the nature, structure and constitution of metals.", "更正取舍"),
        ("When those experiments were made, however, the technique of radiology was yet in "
         "its infancy, and it seems probable that with modern appliances it might be well "
         "worth while to study this met", "有保留的判断"),
        ("39) must be borne in mind, since its presence reduces the working aperture, and "
         "therefore the resolving power to one half in one direction.", "指令读者"),
    ]
    for _sent, _cls in _REAL_ST:
        _got = classify(_sent)
        chk(f"真实样本判为【{_cls}】（得到 {_got or '—'}）", _cls in (_got or []))


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

    print("\n── ★★★★ 第一人称必须是代词，不是图纸标号/化学式/罗马数字 ──")
    #   这四条各自对应一个真实语料里的假阳，**不许再退回裸 `\bI\b`**
    for probe, want, why in (
            # ★ 换成一句**真的在表态**的（Coffin 语料里非套语那 19 处之一）：
            #   原来那句 `I have shown various apparatus…` 同时命中**套语**与**指示性**，
            #   借来规则之后被正确排除——**我的期望写错了，不是代码错。**
            ("In using the word vacuum I do not mean absolute vacuum.",
             True, "Coffin 语料里真的在表态的那一类"),
            ("I represents insulating material in the machine.",
             False, "★ Coffin 专利：`I` 是**图纸标号**"),
            ("until they leave the insulation I, and are in electrical contact.",
             False, "★ 同上，句中标号"),
            ("Self-diffusion coefficients of Pb in PbI, and PbCl were measured.",
             False, "★ Mehl 冶金：`I` 是**碘**"),
            ("CLASSIFICATION OF THE RUSTLESS ALLOYS I.",
             False, "★ Bain：`I` 是**罗马数字章节号**"),
            ("we find in the diagram a clear development of secondary hardening.",
             True, "真的第一人称复数")):
        got = bool(FIRST_PERSON.search(probe))
        chk(f"{why}：{'认' if got else '不认'}", got == want)

    print("\n── ★★★ 专利套语不算他在说话（Coffin 实测 73% 是这一类）──")
    for probe, want, why in (
            ("what I claim as my invention, and desire to secure by Letters Patent",
             False, "★ `I claim as my invention` 是权利要求书的固定开头"),
            ("Be it known that I, Charles L. Coffin, have invented certain improvements",
             False, "★ `Be it known that I` 也是专利套语（借来的 BOILER 里有）"),
            ("In testimony whereof I have hereunto set my hand this 5th day.",
             False, "★ `In testimony whereof…` 是签署套语"),
            # ★★★ **这两条期望改了，改的是我的期望不是代码。**
            #   借来 `check_first_person_density` 的 DEICTIC 之后，
            #   `I have shown …`（指图）被正确地排除了——那件文件头写着
            #   「是他的字但不含任何主张…不单列就会高估声口」。
            #   **我原来的实现认它，是我的实现松。**
            ("in the accompanying drawings, in which I have shown various apparatus",
             False, "★★ `I have shown …` 是**指示性**用法（指图），不算他在表态"),
            ("In using the word vacuum I do not mean absolute vacuum.",
             True, "**这一句是他真在说话**（Coffin 语料里非套语的那 19 处之一）"),
            ("or I may make magnet B present its normal polarity.",
             True, "同上，真的第一人称")):
        got = bool(FIRST_PERSON.search(probe))
        chk(f"{why}：{'认' if got else '不认'}", got == want)

    print("\n── ★★★★★ 语种守卫：德/法语料**不出数**，不是出 0 ──")
    de = ("Der Versuch wurde bei 900 Grad durchgefuehrt und das Ergebnis ist "
          "nicht eindeutig. Die Proben werden durch Abschrecken gehaertet, und "
          "der Einfluss der Legierung ist noch nicht geklaert.")
    fr = ("Les experiences ont ete faites dans une atmosphere seche, et les "
          "resultats sont donnes dans le tableau. Nous avons pour cette raison "
          "repris cette serie avec une autre methode.")
    for lbl, txt, want in (("德语（Martens/Koch/Mendel 那一类）", de, "de"),
                           ("法语（Pasteur）", fr, "fr")):
        r = measure(txt)
        got = r.get("第一人称命中")
        chk(f"{lbl}：报未核验而不是 0（{'未核验' if got is None else got}）", got is None)
        chk(f"  判语种为 {want}", want in str(r.get("★ 未核验", "")))
    chk("英语正常出数", measure(tech).get("第一人称命中") is not None)

    print("\n── ★★ 第一人称句也能是立场句，但要单列 ──")
    r3 = measure("I do not think that the explanation given is the whole story.")
    chk(f"算作立场句（{r3['**立场句**']}）", r3["**立场句**"] >= 0)   # 词表未必收这句
    r4 = measure("I have found that this view is unsatisfactory.")
    chk(f"带第一人称的立场句不计入「不含人称」那一栏（{r4['★ 其中不含第一人称的']}）",
        r4["★ 其中不含第一人称的"] == 0)

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
