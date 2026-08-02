#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**引文层门**：这句外语，是他写的原文，还是译者写的？

## 三个人物、六轮盲判，同一条错反复出现

| 人物 | 形态 | 谁抓到的 |
|---|---|---|
| Livermore #100 | 把 Dies 写的前言当他的自陈 | 席 E |
| Vesalius #102 | 「hunc **suum** primum juvenilem conatum」写成「我自己称它」——`suum` 是第三人称 | 席 E |
| Harvey #103 | 「the greatest crucifying to **him** that ever **he** had」写成「我对 Aubrey 说过」 | 席 E |
| Harvey #103 | 「I confess, I say, nay, I even pointedly assert」被我说成「三个动词一层比一层硬，是我有意堆的」——**他写的是拉丁文，那个英文阶梯是译者的手笔** | 席 E |

**最后一次尤其要紧**：我不但把译文当原话，还**分析了译者的修辞并说那是我的匠心**。

## 而人工修不干净——这是本门存在的直接理由

Harvey 第 3 轮我做的正是「把这个错一次改到位」。改完之后席 E 复核：

> 一个系统在 `hv-token-02` 里立下规矩「**英译的字句是译者的**」，
> 然后在 `fact-01`、`plan-01`、`traj-01`、`task-02` **四处照样零标注地引英译**；
> 更差的是**标注贴反了**——`voice-02` 把「意思是我的」贴在**批评者的话**上，
> `tool-02` 的标注处**根本没有引文**。

**立了规矩、亲手改了两轮、仍有四处漏网 + 两处贴错。**
这正是 RUNBOOK 第四十一种：**发现停在散文态，就等于没发现。**

## 判据三条

对每一段候选答案：

1. **有外语引文而无引文层标注 → 判错。**
   外语引文 = 引号内连续 ≥3 个拉丁字母词或 ≥3 个希腊词。
   标注 = 文中出现「原文／拉丁／希腊／译文／英译／转译／译者」等层次词。
2. **标注贴在非本人话语上 → 判错。**
   若标注紧邻的那段引文，其前后 40 字内出现他人主语（对手名、「他们说」、「记我的话」…），
   而标注写的是「意思是我的」一类归己表述，判为**贴反**。
3. **标注处并无引文 → 判错。**（空标注，比不标更坏：它制造了核过的假象。）

## 射程（必须一起说）

- **它数的是形态，不判真伪。** 一段标了「译文」的伪造引文照样过。
  **它挡的是「忘了标」与「标反了」，不挡「编的」。**
- **第 2 条只在标注与他人主语同段出现时触发**——跨段的贴反它看不见。
- 编造对手立场（Harvey 那次最严重的错）**本门完全挡不住**，
  那要靠「每条『对手主张 X』必须指到对手的书与页」，是另一件事。**不要拿本门当那件事的替代。**

退出码：0 = 通过；1 = 有问题；3 = 用法错误。
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

# 引号内 ≥3 个连续拉丁词，或 ≥3 个希腊词
# ★ 单字母词必须允许：负对照第一次跑就抓出了这个——
#   `「**a** fact which I have myself ascertained…」`、
#   `「**I** confess, I say, nay…」` 都以单字母词起首，
#   而我第一版写的是 `[A-Za-z]{2,}`，两条真实样本一条都匹配不上。
#   **判据自己的负对照抓出了判据自己的正则。**
FOREIGN = re.compile(
    r"[「\"“''][\s*_]*[A-Za-zÀ-ɏ]+(?:[\s,;.\-—*_]+[A-Za-zÀ-ɏ]+){2,}"
    r"|[「\"“''][\s*_]*[Ͱ-Ͽ]+(?:[\s,;.\-—*_]+[Ͱ-Ͽ]+){2,}")
# ★ `[\s*_]` 不是洁癖：真实数据里我写的是 `「**I confess, I say, nay…」`，
#   markdown 粗体符卡在引号与首词之间，**引文就在标注旁边却被判成「空标注」**。
# 引文层标注词（判「全文有没有标注」用）
LAYER = re.compile(r"原文|拉丁|希腊|译文|英译|转译|译者|逐字核|回原本|原本核")
# ★★ 出处式标注 —— 第二、三条只查这个，不查上面的词表。
#   真实数据里「把我的书从英文译成**拉丁**文」「回**拉丁**原本核」都只是**叙述**，
#   我第一版拿词表当标注判据，把这些全判成了「空标注」。
#   **词表是词汇，不是标注。** 标注是「（英文出自 Willis 1847 英译，字句是译者的）」这种出处式写法。
CREDIT = re.compile(
    r"[（(][^）)]{0,60}?(?:原文|拉丁|希腊|译文|英译|转译|译者)[^）)]{0,60}[）)]"
    r"|字句是译者的|是\*{0,2}(?:译文|英译)\*{0,2}(?:——|—|，|。)")
# 归己表述
MINE = re.compile(r"意思是我的|是我(?:的话|说的|写的|有意)|我的原话|我自己(?:称|写|说)")
# ★ 他人主语 —— 必须是「**别人在说话**」，不是「别人的名字出现了」。
#   第一版我写成裸名字表（Willis|Aubrey|…），结果把
#   `（英文出自 **Willis** 1847 英译，字句是译者的，意思是我的）` 判成了贴反——
#   **Willis 在那里是译本出处，不是说话的人。**
#   这与本门要挡的错是同一形态：**把出处当成了话主。判据自己贴反了一次。**
OTHERS_SPEECH = re.compile(
    r"他们(?:说|称|讥|骂|写)|记我的话|转述|编者(?:说|称|写|加)|对手(?:说|称|写)|批评者(?:说|称|写)"
    r"|(?:Aubrey|Willis|Sylvius|Hofmann|Riolan|Primrose|Falloppio|Dies)\s*(?:说|称|写道|记(?!我))")
# 译本出处（出现即说明这一处的外文名是「译本来源」而非「话主」）
TRANSLATOR_CREDIT = re.compile(r"出自[^，。）]{0,24}(?:英译|译本|译文|转译)|字句是译者的")


def check_text(text: str) -> list[str]:
    problems = []
    quotes = list(FOREIGN.finditer(text))
    has_layer = bool(LAYER.search(text))

    if quotes and not has_layer:
        problems.append(
            f"有 {len(quotes)} 处外语引文而**全文无引文层标注**"
            f"（首处：{quotes[0].group(0)[:44]}…）——**读者无从知道那是原文还是译文**")

    for m in CREDIT.finditer(text):
        w = text[max(0, m.start() - 120): m.end() + 120]
        # ③ 标注处并无引文
        if not FOREIGN.search(w):
            problems.append(
                f"**空标注**：{m.group(0)[:26]}… 附近 120 字内没有任何外语引文"
                f"——**比不标更坏，它制造了核过的假象**")
        # ② 标注贴在他人话语上（译本出处不算话主）
        elif MINE.search(w) and OTHERS_SPEECH.search(w) and not TRANSLATOR_CREDIT.search(w):
            problems.append(
                f"**标注贴反**：{m.group(0)[:26]}… 处同时出现归己表述与他人主语"
                f"——检查这段引文到底是谁说的")
    return problems


# ── 负对照 ────────────────────────────────────────────────────────────
# ★ 真实样本：下面四条全部取自本项目实际写出的答案（2026-08-02 三个人物）。
REAL_UNFLAGGED = ('他明确写过「a fact which I have myself ascertained in the case of the sheep」，'
                  '那句「我自己量的」是有意加的。')          # Harvey，零标注
REAL_THIRD_PERSON = ('我对 Aubrey 说过那是「the greatest crucifying to him that ever he had '
                     'in all his life」。')                  # Harvey，第三人称当自述
REAL_FLAGGED_OK = ('我在书里写得比你问得更重（英文出自 Willis 1847 **英译**，字句是译者的，'
                   '意思是我的）：「I confess, I say, nay, I even pointedly assert, that I '
                   'have never found any visible anastomoses.」')
# 规则 ② 的夹具 —— **这条是构造的，如实标出**：
#   真实那一处（Harvey `voice-02`）引的是**中文**，够不着规则 ②，只触发规则 ③。
#   为了让规则 ② 不落空，把同一句里的批评者原话换成实际存在的英译措辞。
#   **它是构造样本，不冒充真实产出。**
CONSTRUCTED_MISATTACHED = ('他们说我是「fond of vivisection for the sake of vain glory」'
                           '（英译，意思是我的）——')
REAL_HOLLOW = ('他们说这是「爱做活体解剖以博虚名」（英文出自 Willis 1847 英译，字句是译者的，'
               '**意思是我的**）——')                        # 标注贴在批评者话上且无引文


# ★ 真实误报夹具：下面两句是本门第一版在真实数据上**误杀**的原文，钉在这里防回归。
REAL_NARRATIVE = ('而 Aubrey 有一条书目类陈述被驳倒过：他说 George Ent 把我的书从英文译成拉丁文。')
REAL_INSTRUCTION = ('要引逐字原话，**回拉丁原本核**；若你手上是 1653 年那个匿名英译，'
                    '那连我审定都没经过。')


def self_test() -> int:
    fails = []

    # ★ 真实误报 1：「译成拉丁文」是叙述，不是标注 → 不许报空标注
    if any("空标注" in x for x in check_text(REAL_NARRATIVE)):
        fails.append("真实误报 1 未修：把叙述里的「拉丁」当成了标注")
    # ★ 真实误报 2：「回拉丁原本核」是给读者的指示，不是标注 → 不许报空标注
    if any("空标注" in x for x in check_text(REAL_INSTRUCTION)):
        fails.append("真实误报 2 未修：把指示里的「拉丁／英译」当成了标注")

    # ★ 真实样本 1：零标注的英语引文 → 必须抓出
    p = check_text(REAL_UNFLAGGED)
    if not any("无引文层标注" in x for x in p):
        fails.append("真实样本 1 未抓出：Harvey 实写的零标注英译引文")

    # ★ 真实样本 2：第三人称引文且零标注 → 必须抓出（形态上同 1）
    p = check_text(REAL_THIRD_PERSON)
    if not p:
        fails.append("真实样本 2 未抓出：第三人称引文当自述且零标注")

    # ★ 真实样本 3：标注齐全且引文在旁 → **不许误杀**
    p = check_text(REAL_FLAGGED_OK)
    if p:
        fails.append(f"真实样本 3 被误杀：标注齐全的引用却报 {p}")

    # ★ 真实样本 4：标注贴在批评者话上、且标注处无外语引文 → 必须抓出
    p = check_text(REAL_HOLLOW)
    if not any("空标注" in x or "贴反" in x for x in p):
        fails.append("真实样本 4 未抓出：空标注 / 贴反")

    # 规则 ②（构造夹具）：标注贴在批评者的英译话语上 → 必须报贴反
    p = check_text(CONSTRUCTED_MISATTACHED)
    if not any("贴反" in x for x in p):
        fails.append(f"规则②未触发：归己表述贴在他人话语上却未报（实得 {p}）")

    # ★ 规则 ② 的反面：译本出处里的人名**不是**话主，不许触发
    if any("贴反" in x for x in check_text(REAL_FLAGGED_OK)):
        fails.append("译本出处被当成话主——判据自己犯了它要挡的那种贴反")

    # 正对照：纯中文无引文 → 0 报
    if check_text("我不给这个。语料里没有可核的记载，去查婚姻登记原件。"):
        fails.append("正对照被误杀：无外语引文的纯中文答案")

    # 正对照：引文只有两个词（不构成引文层问题）
    if check_text("他称之为「hoc Paradoxum」。"):
        fails.append("正对照被误杀：短于三词的外语片段不该触发")

    # 负对照：多处引文、只标了一处 → 仍算有标注（本门只查有无，不查逐条）
    #   **这是有意留的缺口，写在这里让它可见**：逐条配对需要句法分析，本门不做。
    t = ('（英译）他写「one two three four」，又写「five six seven eight」。')
    if check_text(t):
        fails.append("边界失败：全文有标注时不应逐条报")

    # 反向对照：把 LAYER 清空，真实样本 3 必须转红——证明抓/放靠的是标注判据本身
    global LAYER
    saved = LAYER
    try:
        LAYER = re.compile(r"___不可能出现___")
        blind = check_text(REAL_FLAGGED_OK)
    finally:
        LAYER = saved
    if not blind:
        fails.append("反向对照失败：清空标注词表后，已标注样本仍未报——说明放行的不是标注判据")

    for f in fails:
        print(f"✗ {f}")
    if fails:
        print(f"负对照未通过：{len(fails)} 项")
        return 1
    print("负对照通过：**四条真实样本各自判对**（零标注英译、第三人称当自述、"
          "标注齐全未误杀、空标注+贴反被抓出）；规则②另用**一条构造夹具**"
          "（真实那处引的是中文，够不着规则②）；**译本出处里的人名不被当成话主**；"
          "纯中文与两词片段未误杀；全文有标注时不逐条报（有意留的缺口）；"
          "**清空标注词表后已标注样本转红**（证明放行靠的是标注判据本身）")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="引文层门：外语引文必须标明是原文还是译文")
    ap.add_argument("paths", nargs="*", type=pathlib.Path)
    ap.add_argument("--field", default="candidate")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return self_test()
    if not a.paths:
        print("用法错误：需要至少一个 JSON 路径（或 --self-test）", file=sys.stderr)
        return 3

    bad = []
    for p in a.paths:
        if not p.is_file():
            print(f"用法错误：{p} 不存在", file=sys.stderr)
            return 3
        data = json.loads(p.read_text(encoding="utf-8"))
        rows = data if isinstance(data, list) else [{"case_id": k, a.field: v} for k, v in data.items()]
        for r in rows:
            if not isinstance(r, dict) or a.field not in r:
                continue
            for x in check_text(str(r[a.field])):
                bad.append((r.get("case_id") or "?", x))

    if a.json:
        print(json.dumps([{"case": c, "problem": x} for c, x in bad], ensure_ascii=False, indent=1))
        return 1 if bad else 0
    if not bad:
        print("✓ 引文层清楚：每一处外语引文都标明了是原文还是译文")
        return 0
    print(f"\n✗ 引文层 {len(bad)} 处问题：\n")
    for c, x in bad:
        print(f"  - {c}　{x}")
    print("\n  ↑ **三个人物、六轮盲判，这条错反复出现，人工改两轮都改不干净。**"
          "\n  最坏的一次：我把译者的英文修辞分析成了「我有意堆的」——**他写的是拉丁文**。")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
