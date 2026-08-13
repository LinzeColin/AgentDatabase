#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""声口密度 —— 阶段 2 的第三件，也是**最会被门放过去的那一项**。

用法：
    python3 measure_voice.py --raw <raw 目录> [--samples 8]

**为什么它必须单独量：**
门数的是**来源**，不是**声口**（[[gates-count-sources-not-voice]]）——
Coffin #130 三道门全过、研究门 16→0，而 17 万字里他说的实质的话**只有 8 句**。
同类死法还有 Sellers #154、Bain #136。**排期前不量这一项，就会白做一整轮。**

**两个已经踩过的坑，写死在实现里：**

① **量错语域**（[[measured-voice-in-the-wrong-register]]）：
   拿合著技术论文的第一人称密度判「有没有声口」，而 `I` 的 40 处
   **几乎全是化学式**里的元素符号。
   ⇒ 本工具**先打印命中原句再报率**（[[read-the-hits-before-reporting-the-rate]]），
     且英文的 `I` 单列一栏，**不与 my/me/myself 合并计数**——
     `I` 是罗马数字、姓名缩写、OCR 噪声的重灾区，另外三个词不是。

② **译本不是他的声口**：Fröbel 的英译本、Machiavelli 的英译本量到的是**译者**的文风。
   ⇒ 本工具按语种分栏，并把 creator 里带 `tr`／`translat` 的标出来。
     **Machiavelli 的 `00-抓源前必读` 已写死：声口只能用意大利原文量。**

★ 本工具**不给通过/不通过**——密度多少算够，取决于人物与语域，
  由人看分布与原句判。给一个阈值反而会造出「纸面上过了」的门。

★ 退出码：0=跑完；2=参数错；3=没有可量的文件。
"""
import argparse
import json
import pathlib
import random
import re
import sys

# ★★★ 2026-08-13 新增：**多人对话体检测**（Brandeis #172 实测）。
# 起因：他的语料里有一卷 28.2 万词的国会听证记录，第一人称 16.8/千词——**看着声口最好**，
# 而抽样一读，「`Mr. Catchings. My point would be that the Carnegie Steel …`」**根本不是他说的**。
# 实测把 31 份分成两类：
#   多人对话体 4 份（听证/庭审）：第一人称 8.41/千词，**说话人标记 10.8–13.8/千词**
#   单一作者文本 27 份：第一人称中位 1.21/千词，**说话人标记 0.02–0.09/千词**
# ⇒ 两类差**两个数量级**，用「说话人标记密度」分得开。
# ★ **只报不拦，而且不判方向**：命中只说明「这一份里不止一个人说话」，
#   **不等于「这些第一人称不是他」** —— 全库实测三种含义完全不同：
#     Lincoln  #174  29/66（43.9%）：辩论与演说集，**他本人正是其中一位说话人** ⇒ 逐句归属，不排除
#     Plato    #186  20/52（38.5%）：对话录，**那个「我」是他笔下的人物** ⇒ 不能当他的声口
#     Brandeis #172   4/31（12.9%）：国会听证，**他是众多证人之一** ⇒ 逐句归属
#   ⇒ 本件只负责**指出这一份要逐句判说话人**，免得「第一人称密度高」被整份读成「他的声口好」。
#   ★★ 我第一版把提示写成「这些份里的第一人称大量不是他说的」——**那对 Lincoln 是错的**，已改。
#   [[measured-voice-in-the-wrong-register]]：量声口先问「这是谁的语域」。
SPEAKER_TAG = re.compile(
    r"\b(?:Mr|Mrs|Ms|Dr|Senator|Representative|Commissioner|Chairman|The\s+CHAIRMAN|"
    r"Q|A)\.\s+[A-Z][A-Za-z]+\.|\b(?:SOC|Socrates|ΣΩ)\.")
MULTI_SPEAKER_PER_K = 0.5   # 说话人标记 ≥0.5/千词 ⇒ 判为多人对话体（实测两类差两个数量级）


# ★★ 译者标记：**必须按词边界匹配**。
#   2026-08-13 实测：原来写的是 `"tr" in creator.lower()`，
#   于是 `Henry G. Gilbert Nursery and Seed Trade Catalog Collection` 里的 **`Trade`**
#   把 Burbank #183 的 **22 份英文种苗目录全标成了「疑似译本」**——全假。
#   同 [[regex-must-clear-the-corpus-language]]（`A.L.S` 撞德语 `als`、`lister` ⊂ `callister`）。
#   ⇒ 收窄成词元：`tr.` / `trans.` / `translat*` / `traduit` / `übers*` / `übersetzt` / `traduzione`。
#   ★ 正对照：Fröbel #181 与 Machiavelli #177 的英译本仍须被标出来（改完两边都跑过）。
TRANSLATOR_RE = re.compile(
    r"(?<![A-Za-z])(tr|trans)\.(?![A-Za-z])"          # `tr.` / `trans.`
    r"|translat"                                       # translator / translated / translation
    r"|traduit|traduzione|traducci|tradutor"           # 法/意/西/葡
    r"|[üu]bers(?:etz|\.)"                            # übersetzt / übers.
    r"|vertaal|[оО]перевод",
    re.I)

# 每种语言：(不含歧义的第一人称词, 有歧义的单独列)
MARKERS = {
    "en": (r"\b(my|me|myself|mine)\b", r"(?<![A-Za-z])I(?![A-Za-z])"),
    "de": (r"\b(mein|meine|meinem|meinen|meiner|mir|mich)\b", r"\bich\b"),
    "fr": (r"\b(mon|ma|mes|moi|mien)\b", r"\bje\b"),
    "it": (r"\b(mio|mia|miei|mie|me)\b", r"\bio\b"),
    "la": (r"\b(meus|mea|meum|mihi|meo|meam)\b", r"\bego\b"),
    "cs": (r"\b(můj|moje|mého|mně|mne)\b", r"\bjá\b"),
}
# ★★★ **主语脱落语言里，第一人称代词密度量不出声口。**
#   意大利语／拉丁语／捷克语／西班牙语的第一人称主要靠**动词词尾**，代词常常省。
#   实测（2026-08-12）：
#     Machiavelli 意大利文 30 份，代词中位 **0.56**/千词 —— 看着像「没声口」；
#     换成第一人称动词，最高那份 **13.04**/千词，原句「io voglio…」「io non ti credo…」
#     ⇒ **他声口充沛，是量具错了。**
#     Comenius 拉丁文 9 份，代词 0.79、动词 **0.44** —— 两把尺子都低，**是真的低**。
#   ⇒ 跨语种**不能直接比代词密度**；主语脱落语言必须同时看动词。
#   同 [[measured-voice-in-the-wrong-register]]（那次是拿合著论文的 `I` 当声口，
#   40 处几乎全是化学式）。
PRO_DROP = {"it", "la", "cs"}
VERBS_1SG = {
    "it": r"\b(credo|dico|voglio|penso|posso|debbo|giudico|scrivo|parlo|so|ho|sono)\b",
    "la": r"\b(dico|credo|volo|possum|scribo|puto|video|opinor|censeo|sum|arbitror)\b",
    "cs": r"\b(myslím|říkám|chci|mohu|vím|jsem|píši)\b",
    "en": r"\b(i think|i say|i believe|i shall|i have|i am|i was|i would)\b",
    "de": r"\b(glaube ich|sage ich|ich glaube|ich sage|ich habe|ich bin|ich will)\b",
    "fr": r"\b(je crois|je dis|je veux|je pense|j'ai|je suis)\b",
}
WS = re.compile(r"\s+")
# ★★ **折行断字必须先接回去，否则量到的不是第一人称。**
#   实测（Marshall #173，2026-08-12）随机抽 10 条命中，**10 条全是断字**：
#     me- morable → 匹配 `me`      me- dium  → 匹配 `me`
#     ar- my      → 匹配 `my`      ene* my   → 匹配 `my`
#   传记那 53 份的 1.70/千词里有相当一部分是这种噪声。
#   同 [[fixtures-cleaner-than-the-real-thing]]：**自造夹具里没有折行，真语料里到处是。**
DEHYPH_NL = re.compile(r"(\w)[-\u2010\u2011]\s*\n\s*([a-z])")
DEHYPH_SP = re.compile(r"(\w)[-\u2010\u2011]\s+([a-z])")


def dehyphenate(text: str) -> str:
    """把 OCR 折行断开的词接回去。**只接「连字符 + 小写续行」**——
    大写续行多半是真的复合词或专名，不动。"""
    text = DEHYPH_NL.sub(r"\1\2", text)
    return DEHYPH_SP.sub(r"\1\2", text)


def guess_lang(text: str) -> str:
    """粗判语种：按高频虚词计票。**只用于分栏，不用于任何判定。**"""
    t = text[:200000].lower()
    votes = {
        "en": len(re.findall(r"\b(the|and|of|that|which)\b", t)),
        "de": len(re.findall(r"\b(der|die|und|nicht|eine)\b", t)),
        "fr": len(re.findall(r"\b(les|des|que|dans|pour)\b", t)),
        "it": len(re.findall(r"\b(che|della|nella|questo|sono)\b", t)),
        "la": len(re.findall(r"\b(quod|autem|enim|atque|sunt)\b", t)),
        "cs": len(re.findall(r"\b(jest|jako|které|ale|nebo)\b", t)),
    }
    return max(votes, key=votes.get) if max(votes.values()) > 30 else "?"


NATIVE = None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    ap.add_argument("--native-lang", default=None,
                    help="人物写作的母语（en/de/fr/it/…）。给了它就按语种判译本——"
                         "**这是唯一高召回的判法**，元数据大多不写 translated")
    ap.add_argument("--samples", type=int, default=8)
    ap.add_argument("--seed", type=int, default=20260812)
    a = ap.parse_args()
    global NATIVE
    NATIVE = (a.native_lang or '').lower() or None
    raw = pathlib.Path(a.raw)
    mf = raw / "_fetch-manifest.json"
    if not mf.exists():
        print(f"{mf} 不在", file=sys.stderr)
        return 2
    recs = [r for r in json.loads(mf.read_text(encoding="utf-8"))["记录"]
            if r["status"] == "已取回"]
    prim_p = raw / "_primary.json"
    prim = {}
    if prim_p.exists():
        prim = {o["identifier"]: o["档"] for o in json.loads(prim_p.read_text(encoding="utf-8"))["明细"]}
    if not recs:
        print("没有可量的文件", file=sys.stderr)
        return 3

    rng = random.Random(a.seed)
    rows, by_lang, all_hits = [], {}, []
    for r in recs:
        p = raw / r["file"]
        if not p.exists():
            continue
        # ★ 只量**一手**——二手里的第一人称是别人的声口，混进来这个数就没意义了
        if prim.get(r["identifier"]) == "二手":
            continue
        rawtext = p.read_text(encoding="utf-8", errors="replace")
        text = dehyphenate(rawtext)
        n = len(text.split())
        if n < 500:
            continue
        lang = guess_lang(text)
        clean, amb = MARKERS.get(lang, MARKERS["en"])
        c = len(re.findall(clean, text, re.I))
        b = len(re.findall(amb, text, 0 if lang == "en" else re.I))
        # ★ 动词这把尺子**只对主语脱落语有意义**。对英/德/法算出来的 0.00
        #   不是「没有第一人称动词」，是**这把尺子在这儿不适用**——
        #   照样印 0.00 就是又一次「空默认值被读成没问题」
        #   （[[empty-default-swallows-unknown]]）。⇒ 不适用时记 None，显示 `—`。
        vb = (len(re.findall(VERBS_1SG[lang], text, re.I))
              if lang in PRO_DROP else None)
        meta_tr = bool(TRANSLATOR_RE.search(str(r.get("ia_creator", "")))
                       or TRANSLATOR_RE.search(str(r.get("ia_title", ""))))
        # ★★ 语种判法优先：文件语种 ≠ 人物母语 ⇒ 译本。元数据只作补充。
        lang_tr = bool(NATIVE and lang not in ("?", NATIVE))
        tr = lang_tr or meta_tr
        rows.append({"id": r["identifier"], "lang": lang, "words": n,
                     "无歧义每千词": round(c / n * 1000, 2),
                     "有歧义每千词": round(b / n * 1000, 2),
                     # ★ 主语脱落语言里**这一栏才是主信号**
                     "第一人称动词每千词": (round(vb / n * 1000, 2) if vb is not None else None),
                     "主语脱落语": lang in PRO_DROP, "疑似译本": tr,
                     "说话人标记每千词": round(len(SPEAKER_TAG.findall(text)) / n * 1000, 2)})
        by_lang.setdefault(lang, []).append(c / n * 1000)
        for m in re.finditer(clean, text, re.I):
            s = max(0, m.start() - 70)
            all_hits.append((r["identifier"], WS.sub(" ", text[s:m.end() + 70]).strip()))

    if not rows:
        print("**一份都没量到** —— 不是「没有声口」，是没有 ≥500 词的一手文件", file=sys.stderr)
        return 3

    print(f"{raw}｜量了 {len(rows)} 份一手（≥500 词）")
    print(f"{'语种':<6}{'份':>4}{'中位·无歧义/千词':>18}{'最低':>8}{'最高':>8}")
    for lg, vals in sorted(by_lang.items(), key=lambda kv: -len(kv[1])):
        vals.sort()
        med = vals[len(vals) // 2]
        print(f"{lg:<6}{len(vals):>4}{med:>18.2f}{vals[0]:>8.2f}{vals[-1]:>8.2f}")
    pd_rows = [x for x in rows if x["主语脱落语"]]
    if pd_rows:
        vv = sorted(x["第一人称动词每千词"] for x in pd_rows)
        pv = sorted(x["无歧义每千词"] for x in pd_rows)
        print(f"★ **主语脱落语 {len(pd_rows)} 份**：代词中位 {pv[len(pv) // 2]:.2f}"
              f"，而**第一人称动词中位 {vv[len(vv) // 2]:.2f}**/千词"
              f" —— 这两个数差很多时，**低的那个是量具错，不是没声口**")
    # ★ 多人对话体：只报不拦
    multi = [x for x in rows if x.get("说话人标记每千词", 0) >= MULTI_SPEAKER_PER_K]
    if multi:
        print(f"\n★★ **多人对话体 {len(multi)}／{len(rows)} 份**（说话人标记 ≥{MULTI_SPEAKER_PER_K}/千词）"
              f" —— 这些份里的第一人称**必须逐句判说话人**，不能整份当成他的声口：")
        for x in sorted(multi, key=lambda z: -z["说话人标记每千词"])[:6]:
            print(f"     {x['id'][:34]:<34} 说话人标记 {x['说话人标记每千词']:5.2f}/千词")
        solo = [x for x in rows if x.get("说话人标记每千词", 0) < MULTI_SPEAKER_PER_K]
        if solo:
            sv = sorted(x["无歧义每千词"] for x in solo)
            print(f"     ⇒ **去掉这些之后**，单一作者文本 {len(solo)} 份的无歧义第一人称"
                  f"中位 **{sv[len(sv) // 2]:.2f}**/千词")
    tr_n = sum(1 for x in rows if x["疑似译本"])
    print(f"疑似译本 {tr_n}／{len(rows)} 份 —— **译本量到的是译者的文风，不是他的声口**")
    print("  口径：" + ("语种 ≠ %s（高召回）＋ 元数据标记" % NATIVE if NATIVE else
          "**只按元数据标记（低召回）**——IA 大多不写 translated，"
          "要判准请给 `--native-lang`"))

    print(f"\n★ **先读命中，再看率**（随机 {a.samples} 条，种子 {a.seed}）：")
    for ident, s in rng.sample(all_hits, min(a.samples, len(all_hits))):
        print(f"  [{ident[:28]:<28}] …{s[:110]}…")

    (raw / "_voice.json").write_text(json.dumps({
        "量了": len(rows), "按语种中位": {k: round(sorted(v)[len(v) // 2], 2) for k, v in by_lang.items()},
        "疑似译本": tr_n,
        "★口径": "只量一手；无歧义词与有歧义词分列；**本工具不给通过/不通过**",
        "明细": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
