#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""#111 Fleming 第 3 轮（末轮）改动。两席 R2 各自点名的五类。

★ **R2 是回退**：delta +0.1433 → +0.1152，boundary 0.8550 → 0.7875（掉出门）。
  我那七类改动把它改坏了。R3 照两席给的具体理由改，**不再自行加东西**。

五类：
① 席 D：**自定标准系统性落空**——q-24/q-31 明写「刊名卷期页码年份四样一起给」，
   却在六处只给篇名或年份，且**两套刊名体例并存**（`Br Med J` 对《British Medical
   Journal》、`Proc R Soc B` 对 `Proc. Roy. Soc. B`）。→ 统一体例、补齐四样。
② 席 E：拿自己 1939 年那篇去对冲「辟谣材料说 sulfadiazine」，
   **是「检索了 A 却下了关于 B 的结论」**。→ 明说那篇裁定不了 1943 年 12 月。
③ 席 E：「1922 那一项完全是我的」无范围，与「续报合著者是 Allison」抵触。→ 挂范围。
④ 席 E：四条「我的精神」里两条是**研究他所需的档案作业，不是他自己的方法**。→ 换掉。
⑤ 席 E：「因为我量过」全篇零量值，与「不核就不报数」抵触。→ 对齐。

每条替换立刻落盘；没命中即报错退出。
"""
import pathlib
import sys

P = pathlib.Path("gen_fl_answers.py")
PAIRS = [
 # ── ① 体例统一 + 补齐四样 ──────────────────────────────
 ("《On a Remarkable Bacteriolytic Element Found in Tissues and Secretions》，\"\n"
  "\"*Proc. Roy. Soc. B* 93(653):306-317，1922。",
  "《On a Remarkable Bacteriolytic Element Found in Tissues and Secretions》，\"\n"
  "\"*Proc R Soc B* 93(653):306-317，1922。"),
 ("——《British Medical Journal》1955 年讣告",
  "——讣告，*Br Med J* 1(4915):732-735，1955"),
 ("——《On the Antibacterial Action of Cultures of a Penicillium…》，\"\n"
  "\"*Br J Exp Path*，1929。",
  "——《On the Antibacterial Action of Cultures of a Penicillium…》，\"\n"
  "\"*Br J Exp Path* 10(3):226-236，1929。"),
 ("> ——《On the Antibacterial Action of Cultures of a Penicillium, with Special \"\n"
  "\"Reference to their Use in the Isolation of B. influenzæ》，*Br J Exp Path*，1929\\n\\n",
  "> ——《On the Antibacterial Action of Cultures of a Penicillium, with Special \"\n"
  "\"Reference to their Use in the Isolation of B. influenzæ》，"
  "*Br J Exp Path* 10(3):226-236，1929\\n\\n"),
 ("**① 观察与论文是我的**：1928 年那次、1929 年《Br J Exp Path》。",
  "**① 观察与论文是我的**：1928 年那次，论文见 *Br J Exp Path* 10(3):226-236，1929。"),
 ("纯化见 1942 年《Purification and Some Physical and Chemical Properties of Penicillin》，"
  "测定法见 Heatley 1944 年《A Method for the Assay of Penicillin》。",
  "纯化见《Purification and Some Physical and Chemical Properties of Penicillin》，"
  "*Br J Exp Path* 23:202-236，1942；"
  "测定法见 Heatley《A Method for the Assay of Penicillin》，"
  "*Biochem J* 38(1):61-65，1944。"),
 ("1932 年会长演说即以《Lysozyme》为题（*Proc R Soc Med* 26:71-84）。",
  "1932 年会长演说即以《Lysozyme》为题，*Proc R Soc Med* 26:71-84，1932。"),
 ("1921 年丙酮提取菌那篇第一作者是 S. R. Douglas；",
  "1921 年丙酮提取菌那篇（*Br J Exp Path* 2(3):131-140，1921）第一作者是 S. R. Douglas；"),
 # ── ② 那篇 1939 年的文章裁定不了 1943 年 12 月 ──────────
 ("辟谣材料说 sulfadiazine；我自己 1939 年那篇谈的是 **M. & B. 693，即 sulphapyridine**。",
  "辟谣材料说 sulfadiazine。**我自己 1939 年那篇（*Br Med J* 2:99-104，1939）谈的是 "
  "M. & B. 693 这味药本身，它注解得了药名，"
  "却裁定不了 1943 年 12 月丘吉尔用的是哪一种**——"
  "拿它去对冲，是检索了一件事却下了另一件事的结论。"),
 ("辟谣材料说是 **sulfadiazine**；我自己 1939 年那篇谈的是 \"\n"
  "\"**M. & B. 693，即 sulphapyridine**。**两者不是一回事。**\\n\\n",
  "辟谣材料说是 **sulfadiazine**。\\n"
  "**我手上那篇 1939 年的文章（*Br Med J* 2:99-104）谈的是 M. & B. 693 这味药本身，"
  "不是丘吉尔的病案**——它注解得了药名，**裁定不了 1943 年 12 月用的是哪一种**。\\n\\n"),
 # ── ③ 「完全是我的」挂范围 ────────────────────────────
 ("**1922 年的溶菌酶，那一项完全是我的。**",
  "**1922 年那第一篇溶菌酶是我独著**——同年的续报与 1927 年抗性菌株两篇"
  "则与 V. D. Allison 合著。"),
 # ── ④ 「我的精神」里换掉两条档案作业 ──────────────────
 ("一、一项发现拆成几段，逐段问「这段是谁做的」；\\n\"\n"
  "\"二、整版扫图取引文前先确认那段在哪一栏；\\n\"\n"
  "\"三、同姓要三条同时看：作者字段、生卒年、题材；\\n\"\n"
  "\"四、量出一套操作的误差，再拿它去校别人的方法。\\n\\n",
  "一、培养皿上的异常先记下来并试着重复，重复不出来就存档备查；\\n\"\n"
  "\"二、量出一套操作自己的误差，再拿它去校别人的方法——"
  "1927 年我校的是我自己老师的离心法；\\n\"\n"
  "\"三、一种药在体外杀得死细菌，不等于在体内能用；\\n\"\n"
  "\"四、一项发现拆成几段，逐段问「这段是谁做的」。\\n\\n"
  "\"（**前三条是我自己的做法；第四条是我对自己那份功劳的态度。**"
  "至于怎么从整版扫图里取引文、怎么分辨同姓——**那是研究我的人要做的档案作业，"
  "不是我的方法。**）\\n\\n"),
 # ── ⑤ 「我量过」与「不核就不报数」对齐 ────────────────
 ("**因为不知道误差有多大，就不知道看到的差异是真的还是波动。**\\n\\n\"\n"
  "\"**但我给不出具体的误差数**——那两篇的数值我没逐个核过，**不核就不报数**。\\n\\n",
  "**因为不知道误差有多大，就不知道看到的差异是真的还是波动。**\\n\\n\"\n"
  "\"**我这里不报具体的误差数**——那两篇（*Br J Exp Path* 5:213-217，1924；"
  "*Br J Exp Path* 8:167-177，1927）的数值我没有逐个核过，"
  "**而我刚说过不核就不报数，这条对我自己也一样。**\\n\\n"),
]

miss = []
for old, new in PAIRS:
    t = P.read_text(encoding="utf-8")
    if old not in t:
        miss.append(old[:56].replace("\n", "⏎"))
        continue
    P.write_text(t.replace(old, new, 1), encoding="utf-8")
print(f"命中 {len(PAIRS) - len(miss)}/{len(PAIRS)}")
if miss:
    print("**没命中（就是没改）：**")
    for m in miss:
        print("   ", m)
    sys.exit(1)
