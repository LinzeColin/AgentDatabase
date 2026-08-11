#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**一段文字出现在他的语料里，不等于那段是他写的。**

## 撞出它的那一次（Koch #107，2026-08-11）

要给 41 条压在同一对源上的断言找独立第二簇，我按关键词密度排了候选榜，
**三次都排错，每次都是去读原文才推翻的**：

| 候选 | 看着像什么 | 实际是什么 |
|---|---|---|
| `arbeitenausdemka1886unse`（机构汇编，289 次命中，**榜首**） | 他的方法讲得最密 | **别人在讨论他**——14 处 `von Koch` 全是第三人称 |
| `DeutscheMedizinischeWochenschrift…`（期刊整卷，记 P1） | 一手源 | 整卷里既有他的篇也有别人的篇 |
| **`Gesammelte Werke` 第二卷（他自己的文集，P1）** | **同一作者，最干净** | **收着讨论记录，含他人发言** |

第三条最要紧：前两条从 `tier` 还看得出苗头（机构汇编记 S1），
而**他自己的文集是 P1，`tier` 帮不了你**。

## 它做什么

给定一份源与若干检索词，把每一处命中**分成三类**：

- `his`      —— 没有反证，按他的正文算
- `about`    —— 段内有**第三人称称谓**（`Geheimrat Koch` / `Herr Koch` / `von Koch`）
- `reported` —— 段内有**转述框架**（`Was ich … vernommen habe` / `wie Herr X sagte`）

**它不判「这段能不能撑那条断言」**——那要读。它只把**明显不是他的**先滤掉，
把逐段核的量降下来。

## 它不做什么

- **不给「他的正文」盖章。** `his` 只表示「没找到反证」，不表示已核实。
- **不替代 `check_authorship`**：那件判的是**整份源归不归他**，
  本件判的是**一份源里的某一段**。两件的射程不重叠。

用法：
    python3 check_passage_is_his_voice.py --file <src.txt> --surname Koch --term Reinkultur
    python3 check_passage_is_his_voice.py --self-test
"""
import argparse
import re
import sys
import pathlib

#: 第三人称称谓：头衔／敬称 + 姓，或 `von <姓>`（「由某某描述的」）。
#: ★ 只用**姓**构造，因为语料里的名往往被 OCR 打坏（Koch 那批里 `Robert` 极少完整）。
_APPELL = (r"(?:Geheimrat|Geheimrath|Geheimen?\s+Regierungsra[thd]|Herr|Herrn|Prof(?:essor)?\.?|"
           r"Dr\.|Direktor|Kollege)\s+(?:[A-ZÄÖÜ][a-zäöüß]+\s+){0,2}%s\b")
#: `von <姓>` 只有在**后面接分词或名词**时才是「由他所…的」，
#: 单独的 `von Koch` 也可能是署名行的一部分，所以两种形态都收，由调用方看样例定夺。
_BY = r"\bvon\s+(?:Dr\.\s*)?%s\b"
#: 转述框架：说话人不是他。
_REPORTED = (r"(?:Was\s+ich\s+[^.]{0,60}?vernommen|wie\s+(?:Herr|Prof|Dr)\.?\s+\w+\s+(?:sagte|bemerkte|"
             r"ausführte)|nach\s+den\s+Ausführungen\s+(?:des\s+)?(?:Herrn|Prof))")

WINDOW = 260          # 命中点前后各取多少字符当「段」

#: ★★★★★ 2026-08-11：**只看窗口的判法在真语料上失效**。
#:   本件第一版只在命中点前后 260 字符里找反证，自测 6/6 全过——
#:   而拿 `arbeitenausdemka1886unse`（我手工核过：整卷是别人在讨论他）去跑，
#:   它报 **his 66 / about 0**：那 14 处 `von Koch` 散在 190 万字符里，
#:   **一处都不在检索词的窗口内**。
#:   自测之所以全绿，是因为**我的夹具把反证放在了检索词旁边，而真语料不是那样**
#:   （[[fixtures-cleaner-than-the-real-thing]]）。
#:   → 补一个**文档级**信号：整份源里第三人称称谓的密度。
#:     「整卷是别人在写他」与「他自己的文集」在这个数上分得开，在窗口上分不开。
DOC_APPELL_WARN = 1.0     # 每万词；超过这个数就提醒「这份源多半在谈他，不是他在写」


def doc_level(text: str, surname: str):
    """整份源的第三人称称谓密度（每万词）——**窗口判法看不见的那一层**。"""
    flat = re.sub(r"\s+", " ", re.sub(r"-\s*\n\s*", "", text))
    n = len(re.findall(r"\w+", flat)) or 1
    hits = (len(re.findall(_APPELL % re.escape(surname), flat))
            + len(re.findall(_BY % re.escape(surname), flat)))
    return hits, round(hits * 1e4 / n, 2)


def classify(text: str, surname: str, term: str, window: int = WINDOW):
    """→ [(类别, 上下文), …]，类别 ∈ {his, about, reported}。"""
    flat = re.sub(r"-\s*\n\s*", "", text)
    flat = re.sub(r"\s+", " ", flat)
    appell = re.compile(_APPELL % re.escape(surname))
    by = re.compile(_BY % re.escape(surname))
    rep = re.compile(_REPORTED)
    out = []
    for m in re.finditer(re.escape(term), flat):
        a, b = max(0, m.start() - window), min(len(flat), m.end() + window)
        seg = flat[a:b]
        if rep.search(seg):
            kind = "reported"
        elif appell.search(seg) or by.search(seg):
            kind = "about"
        else:
            kind = "his"
        out.append((kind, seg))
    return out


# ---- 自测夹具：**逐字取自 Koch #107 的真语料**，不是我编的干净句子 ----
#   [[fixtures-cleaner-than-the-real-thing]]：夹具比原文干净就等于没测。
_FX_ABOUT = ("Die Augen waren geschlossen und die Augenlider verklebt, wie dies bei der "
             "von Koch!) beschriebenen Stäbchensepticämie der Mäuse stets beobachtet wird. "
             "Im weiteren Verlaufe der Krankheit frassen die Thiere nicht mehr. Reinkultur")
_FX_REPORTED = ("Was ich gestern von Geheimrat Koch als eine Art Konzession vernommen habe, "
                "ist, daß man doch einen gewissen Dauerzustand der Bazillen annehmen müsse. "
                "Er hat allerlei Plattenkulturen angestellt.")
_FX_HIS = ("Die genaue Beobachtung der Bazillen in ihren Reinkulturen führte dann zur "
           "Auffindung von einigen sehr charakteristischen Eigenschaften bezüglich ihrer "
           "Form und ihres Wachstums in Nährgelatine, wodurch sie mit Sicherheit von "
           "anderen Bazillen zu unterscheiden sind.")


def self_test() -> int:
    bad = []

    def chk(label, ok):
        print(("  ✓ " if ok else "  ✗ ") + label)
        if not ok:
            bad.append(label)

    r = classify(_FX_ABOUT, "Koch", "Reinkultur")
    chk("① `von Koch beschriebenen` → about（%s）" % (r[0][0] if r else "无命中"),
        len(r) == 1 and r[0][0] == "about")

    r = classify(_FX_REPORTED, "Koch", "Plattenkultur")
    chk("② `Was ich … von Geheimrat Koch … vernommen habe` → reported（%s）"
        % (r[0][0] if r else "无命中"), len(r) == 1 and r[0][0] == "reported")

    r = classify(_FX_HIS, "Koch", "Reinkultur")
    chk("③ 他自己的正文 → his（%s）" % (r[0][0] if r else "无命中"),
        len(r) == 1 and r[0][0] == "his")

    # ④ ★ 过校正守卫：**只要段内提到姓就判 about** 是坏修法——
    #    他自己的文章里也会写自己的姓（署名、自引）。这一条钉死不许那么干。
    _self_cite = ("Wie ich in meiner Arbeit über die Ätiologie der Milzbrandkrankheit "
                  "gezeigt habe, lassen sich die Bazillen in Reinkultur züchten. "
                  "Koch, Wollstein.")
    r = classify(_self_cite, "Koch", "Reinkultur")
    chk("④ 段内有裸姓但无称谓／转述 → 仍是 his（%s）" % (r[0][0] if r else "无命中"),
        len(r) == 1 and r[0][0] == "his")

    # ⑤ 转述优先于称谓：两者同时出现时算 reported（说话人不是他，更强的反证）
    r = classify(_FX_REPORTED, "Koch", "Bazillen")
    chk("⑤ 称谓与转述同现 → reported 优先（%s）" % (r[0][0] if r else "无命中"),
        r and r[0][0] == "reported")

    # ⑥ 窗口边界：命中点离反证超过窗口就不算——**避免把整卷染成 about**
    far = "Herr Koch sprach. " + ("x" * 900) + " Reinkultur"
    r = classify(far, "Koch", "Reinkultur", window=200)
    chk("⑥ 反证在窗口外 → his（%s）" % (r[0][0] if r else "无命中"),
        len(r) == 1 and r[0][0] == "his")

    # ⑦ ★★★ 文档级：**反证离检索词很远时，窗口判法必然漏，而文档级必须逮到**。
    #    这一条是拿真事故构造的：`arbeitenausdemka1886unse` 190 万字符里
    #    14 处 `von Koch`，一处都不在检索词窗口内 → 窗口判法报 his 66 / about 0。
    far_doc = ("Reinkultur " + ("Fuellwort " * 400)
               + "wie dies bei der von Koch beschriebenen Stäbchensepticämie beobachtet wird. "
               + ("Fuellwort " * 400))
    r = classify(far_doc, "Koch", "Reinkultur")
    _, dens = doc_level(far_doc, "Koch")
    chk("⑦ 反证在窗口外：窗口判 his（%s）而**文档级密度 %.2f 必须 >0**"
        % (r[0][0] if r else "无", dens), r and r[0][0] == "his" and dens > 0)

    print("\n自测 %d/7 通过" % (7 - len(bad)), file=sys.stderr)
    return 1 if bad else 0


def main() -> int:
    if "--self-test" in sys.argv[1:]:
        return self_test()
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--file", required=True)
    ap.add_argument("--surname", required=True)
    ap.add_argument("--term", action="append", required=True)
    ap.add_argument("--window", type=int, default=WINDOW)
    ap.add_argument("--show", type=int, default=2, help="每类打印几条上下文")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    text = pathlib.Path(a.file).read_text(encoding="utf-8", errors="replace")
    hits, dens = doc_level(text, a.surname)
    flag = "★★ 这份源多半在**谈他**，不是他在写" if dens >= DOC_APPELL_WARN else "（低）"
    print("══ 文档级：第三人称称谓 %d 处，**%.2f／万词** %s" % (hits, dens, flag))
    print("   ★ 这一层窗口判法看不见——反证可能散在全文任何地方。\n")
    for term in a.term:
        rows = classify(text, a.surname, term, a.window)
        n = len(rows)
        c = {k: sum(1 for x, _ in rows if x == k) for k in ("his", "about", "reported")}
        print("── %s：命中 %d｜his %d｜about %d｜reported %d"
              % (term, n, c["his"], c["about"], c["reported"]))
        for kind in ("about", "reported"):
            for _, seg in [r for r in rows if r[0] == kind][:a.show]:
                print("     [%s] …%s…" % (kind, seg[:150]))
    print("\n★ `his` 只表示**没找到反证**，不表示已核实——补第二簇之前仍要读那一段。",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
