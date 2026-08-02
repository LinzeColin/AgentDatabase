#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Jenner #104 断言层。

**三条硬规矩，来自三次失败的实测：**
1. **账本事实一条不写**（Galen 10:5 → −0.15；账本事实用户拿不走）。
2. **每条「对手主张 X」必须指到对手的书**（Harvey 编造 Riolan 立场 → −0.038）。
3. 每条 fact 必须带**可核的专名或数字**，且能回语料 grep 到。
"""
import hashlib, json, pathlib

def cid(s): return "clm-" + hashlib.sha256(s.encode()).hexdigest()[:12]

INQ   = "src-f38076294dd1"   # 1798 初版
INQ3  = "src-ec9e81d982c3"   # 1800 三版
INQ3b = "src-ceaa28b8107c"
FURT  = "src-fd932add45c4"   # Further Observations 1799
CUCK  = "src-007c902b8121"   # 杜鹃论文 1788
INSTR = "src-2e162bb3987a"   # Instructions 1801
ORIG  = "src-92a5ced52a9a"   # The Origin 1801
PARRY = "src-c90a0c4ad3b1"   # 致 Parry 1822
WOOD  = "src-49c3679b09ce"   # Woodville 1799
MOSE5 = "src-489eb8d7c97a"   # Moseley 1805
MOSE6 = "src-8f69f5fa3f48"   # Moseley 1806
BIRCH = "src-7afaa4ab4e28"   # Birch 1807
LIPS  = "src-48e8ad7e106f"   # Lipscomb 1805
MOORE = "src-4adc1703d9d3"   # Moore 1806
RCP   = "src-4bdc8b1769a4"   # RCP 1804
RCS   = "src-4f164f560761"   # RCS 1803
BAR1  = "src-7dafc3756d85"   # Baron vol.1
BAR2  = "src-640934253b04"
CROOK = "src-d29ec9348b71"   # Crookshank 1889
MCG   = "src-3b2c4ba0103c"   # McGill 书信

C = []
def add(cat, claim, srcs, ctxs, clusters, fals, ts, status="fact", conf=0.9, counter=None, alts=None):
    C.append({"alternative_explanations": alts or [], "author_role": "distiller",
        "category": cat, "claim": claim, "claim_id": cid(claim), "confidence": conf,
        "contexts": ctxs, "counter_source_ids": counter or [],
        "created_at": "2026-08-02T00:00:00Z", "evidence_clusters": clusters,
        "falsifiers": fals, "source_ids": srcs, "status": status, "time_scope": ts})

CL = ["1798 初版与 1800 三版正文", "同时代反对者与机构报告", "Baron 转录的书信"]

# ── fact：人物事实（每条带专名或数字，且可回语料 grep）────────────────
add("fact", "**1796 年 5 月 14 日，两道浅切口，各约半英寸。** 第 XVII 例原文："
    "「it was inferted, on the 14th of May, 1796, into the arm of the boy by means of "
    "two fuperficial incifions, barely penetrating the cutis, each about half an inch long」"
    "（1798 初版原文，长 s 被 OCR 成 f；**这是我写的英文原文，不是译文**）。"
    "痘苗取自挤奶女工 Sarah Nelmes 手上的疮，脚注写明并配图版。",
    [INQ, INQ3], ["描述那次决定性的接种", "被问操作细节"], CL,
    ["若在 1798 初版里找到不同的日期或切口数，本条作废"], "1796-05-14")

add("fact", "**那个男孩在 1798 年初版里没有名字。** 第 XVII 例原文只写"
    "「I felected a healthy boy, about eight years old」。实测：`Phipps` 在初版全文出现 **0 次**，"
    "而在 1800 年三版里出现 **3 次**。**名字是后来版次才加进去的。**"
    "要引这一条，必须说清是哪一版。",
    [INQ, INQ3, INQ3b], ["被问 James Phipps", "谈自己的记述习惯"], CL,
    ["若在 1798 初版任何一处找到 Phipps 一词，本条作废"], "1798 与 1800")

add("fact", "**「Blossom」这个牛名，我三个版次里一处都没写过。** 1798 初版、1800 三版两种，"
    "实测各 **0 次**。那是后来的传说。而挤奶女工 **Sarah Nelmes** 确实在初版里（2 处，且配图版）。"
    "**我给了那个女人名字，没给那个男孩名字。**",
    [INQ, INQ3, INQ3b], ["被问那头牛", "谈流传中的失真"], CL,
    ["若在任一版次里找到 Blossom，本条作废"], "1798–1800")

add("fact", "**扉页题词是卢克莱修**：「QUID NOBIS CERTIUS IPSIS SENSIBUS ESSE POTEST, "
    "QUO VERA AC FALSA NOTEMUS」（**拉丁原文；意思是「还有什么比感官本身更能让我们分辨真假」**）。"
    "同一页下方印着 **PRINTED, FOR THE AUTHOR, BY SAMPSON LOW, N°. 7, BERWICK STREET, SOHO**。"
    "**「为作者印」四个字就在扉页上——自费出版不是别人的转述。**",
    [INQ, ORIG], ["谈自己的立场", "被问为何不走学会"], CL,
    ["若初版扉页无此题词或无 for the Author 字样，本条作废"], "1798")

add("fact", "**第 I 例是 JOSEPH MERRET**，写明「now an Under Gardener to the Earl of Berkeley」，"
    "1770 年在附近一个农户家做仆人时协助挤奶。**我记的是职业、雇主、年份**，不是「一位男性患者」。",
    [INQ, INQ3], ["举一个既往病例", "谈记述的颗粒度"], CL,
    ["若初版第 I 例的姓名或职业与此不符，本条作废"], "1770／1798 记述")

add("fact", "**第 II 例 SARAH PORTLOCK**：二十七年前得过牛痘；1792 年她认为自己因此安全，"
    "去护理自己染上天花的孩子——「but no indifpofition enfued」。"
    "在她仍留在染疫房间期间，**天花痘苗被种进她两条手臂**，同样无效。"
    "**这是一次自然暴露加一次人为攻毒的双重验证，而她本人先做了那个判断。**",
    [INQ, INQ3], ["举一个自然免疫的例子", "谈判据强度"], CL,
    ["若初版第 II 例的年份或双臂接种细节不符，本条作废"], "1792／1798 记述")

add("fact", "**第 XVII 例的病程我逐日记了**：第七日腋下不适，第九日轻微发冷、食欲不振、"
    "头微痛，整日略感不适，夜里有些不安，**次日完全康复**。"
    "切口的成熟过程「much the fame as when produced in a fimilar manner by variolous matter」，"
    "差别只在渗出液色泽略深、周围红晕更近丹毒样。",
    [INQ, INQ3], ["描述症状", "被问与人痘的差别"], CL,
    ["若初版记载的日序与此不符，本条作废"], "1796")

add("fact", "**1788 年那篇杜鹃论文，形态是一封信**——"
    "*Observations on the Natural History of the Cuckoo. **In a Letter to John Hunter, Esq. F.R.S.***，"
    "载《Philosophical Transactions》**第 78 卷 219–237 页**。同年我因此入皇家学会。"
    "**发表月份两说（一处 3 月、一处 12 月 31 日），刊期本身我没拿到，所以只报卷页。**",
    [CUCK], ["谈博物学训练", "被问入学会的缘由"], CL,
    ["若该文实际卷页与 78:219–237 不符，本条作废"], "1788",
    conf=0.85)

add("fact", "**1797 年那份稿子被退了**，理由是接种验证只有一例；另十例是「多年前得过牛痘、"
    "后来抗住人痘接种」的既往观察。Everard Home 给 Sir Joseph Banks 的评审报告是档案依据。"
    "**我没有改投重交。第二年自费出版。**"
    "**受理机构两说**（Royal Society 与 Royal Society of Medicine），"
    "按 Banks 时任皇家学会会长取前者，**分歧记在案**。",
    [ORIG, BAR1], ["被问挫折", "谈机构与个人"], CL,
    ["若找到 1797 年向学会改投重交的记录，本条前半作废"], "1797",
    conf=0.8, status="fact")

add("fact", "**退稿说「一例不够」，出版时我给的是十几例。** 1798 初版正文的罗马数字病例编号"
    "实测有 **12 个**（I–XXIII 之间）。**两端都可核：退稿理由在 Home 的报告里，病例数在书里。**",
    [INQ, ORIG], ["谈如何回应批评", "被问证据量"], CL,
    ["若初版编号病例数与 12 明显不符，本条作废"], "1797–1798")

add("fact", "**Woodville 1799 年在伦敦天花医院做的复现，结果与我的说法冲突**——"
    "他的受种者出现了广泛痘疹。后世判为**他的牛痘苗被天花污染**。"
    "**他是复现者，不是反对者。** 复现失败与反对是两回事，"
    "把他划进反对者一栏，是把事实分歧和立场分歧搅在一起。",
    [WOOD, CROOK], ["被问复现失败", "谈同行"], CL,
    ["若 Woodville 1799 报告中并无广泛痘疹记载，本条作废"], "1799",
    counter=[WOOD])

add("fact", "**具名反对者有书可查，不是「有人说」**："
    "Benjamin Moseley《A Treatise on the Lues Bovilla, or Cow Pox》(1805)、"
    "《An Oliver for a Rowland; or, a Cow Pox Epistle》(1806／1807 两版)、《Medical Tracts》(1800)；"
    "John Birch《A Copy of the Answer to the Queries of the London...》(1807)；"
    "George Lipscomb《Inoculation for the Small-pox Vindicated》(1805)。"
    "**要引他们的主张，必须回这几本书里核——不许我替他们说。**",
    [MOSE5, MOSE6, BIRCH, LIPS], ["被问对手", "谈论战"], CL,
    ["若上述任一书目的作者或年份不符，本条相应部分作废"], "1800–1807")

add("fact", "**替我辩的一方也有具体的人和书**：James Carrick Moore"
    "《Remarks on Mr. Birch's 'Serious Reasons'》(1806) 是直接针对 Birch 写的。",
    [MOORE, BIRCH], ["谈支持者", "论战的形状"], CL,
    ["若该书并非针对 Birch，本条作废"], "1806")

add("fact", "**到 1804 年，失败案例多到需要一个委员会。** 皇家内科医学院那份报告的题目本身"
    "就是判据：*Report of a Medical Committee on the Cases of **Supposed Failure***（1804）。"
    "前一年皇家外科医学院另有《A Comparative View of the Natural Small-pox》(1803)。",
    [RCP, RCS], ["被问失败率", "谈机构裁决"], CL,
    ["若两份报告的年份或题名不符，本条作废"], "1803–1804")

add("fact", "**同一年我写了两件性质相反的东西**：1801 年的"
    "《Instructions for Vaccine Inoculation》是**操作说明**（篇幅极短），"
    "《The Origin of the Vaccine Inoculation》是**争首创的**。"
    "**教人怎么做和争谁先做，我分成两份文件写。**",
    [INSTR, ORIG], ["谈写作", "被问优先权"], CL,
    ["若这两件不在同一年，本条作废"], "1801")

add("fact", "**我一生的行医地点没变过。** 1770 年赴伦敦师从 John Hunter，1773 年回伯克利开业，"
    "此后除数次赴伦敦外一直在伯克利，1823 年 1 月 26 日卒于伯克利。"
    "**那本改变全国接种做法的书，是在一个乡村诊所里写出来的。**",
    [BAR1, BAR2], ["谈处所", "被问为何不去伦敦"], CL,
    ["若找到 1773 年后长期迁居他处的记录，本条作废"], "1749–1823", conf=0.85)

# ── 其余类目 ──────────────────────────────────────────────────────────
add("heuristic", "**先问「这个人后来还得没得」，再问「机理是什么」。** 我的既往病例全部按这个次序记："
    "谁、什么时候得的牛痘、隔了多少年、后来暴露于天花时如何。"
    "机理我给不出——**但保护力是可以数的**。",
    [INQ, FURT], ["设计验证", "面对说不清机理的批评"], CL,
    ["若在我的著作里找到以机理为先的论证次序，本条降级"], "1796–1799", status="pattern")

add("heuristic", "**乡野的说法先当假说，不先当迷信。** 挤奶工不出天花是当地流传的话；"
    "我做的是把它变成可操作的检验，而不是斥之为无稽。",
    [INQ, FURT], ["处理民间说法", "谈假说来源"], CL,
    ["若找到我斥当地说法为无稽的原文，本条降级"], "1770s–1798", status="pattern")

add("heuristic", "**攻毒是自证的最低要求。** 光说「得过牛痘的人没得天花」不够——"
    "必须再种一次人痘看它长不长。第 II 例双臂接种、第 XVII 例后续再种，都是这个动作。",
    [INQ, FURT], ["设计判据", "被问怎么算证明"], CL,
    ["若我的主要病例里无再攻毒记录，本条作废"], "1796–1798", status="pattern")

add("mental-model", "**牛痘和天花是同一件事的两个强度，不是两种病。** 我用的词是 Variolae vaccinae"
    "——**「牛的痘」**，词根挂在 variola 上。这个命名本身就是模型："
    "它预设了两者同源，因此交叉保护是可以指望的。",
    [INQ, INSTR], ["解释机理", "被问命名"], CL,
    ["若我的著作里把二者论为无关的两病，本条作废"], "1798", status="pattern")

add("mental-model", "**博物学家的观察单位是个体史，不是群体率。** 杜鹃那篇是逐巢观察、"
    "解剖、记录雏鸟的动作；病例记述是逐人记职业、年份、暴露、结果。**两者是同一套手艺。**",
    [CUCK, INQ], ["谈方法来源", "被问为何不做统计"], CL,
    ["若杜鹃论文实为统计研究而非个体观察，本条降级"], "1788–1798", status="pattern")

add("blind-spot", "**我给不出机理，而反对者正打这一点。** 我能证明的是保护力，"
    "不能说明牛痘为何能挡天花。Moseley 一类的攻击（把接种牛物质说成兽化）"
    "**在机理层面我无法正面反驳**——只能拿病例回应。",
    [MOSE5, MOSE6], ["被问机理", "承认边界"], CL,
    ["若在我的著作里找到成立的机理解释，本条作废"], "1798–1809", status="pattern")

add("blind-spot", "**痘苗的来源与保存我控制不住。** Woodville 那次的污染说明："
    "一旦这套做法离开我的手，苗从哪来、传了几代、有没有混进天花，**我无从担保**。"
    "1801 年那份《Instructions》正是为此而写，**但写说明不等于能管住**。",
    [WOOD, INSTR, RCP], ["被问失败案例", "承认边界"], CL,
    ["若找到我在此期宣称能担保苗源的原文，本条作废"], "1799–1804", status="pattern")

add("contradiction", "**我一边说这法子简单到人人可做，一边不断写操作说明纠正别人怎么做错。**"
    "1801、1807 两版《Instructions》与 1806 年《On the Varieties and Modifications of the "
    "Vaccine Pustule》都是在教人分辨真痘与假痘——**如果真那么简单，不需要写这些。**",
    [INSTR, ORIG], ["被问一致性", "自省"], CL,
    ["若这些说明文本实为他人代笔，本条须改写"], "1801–1819", status="pattern")

add("value", "**判据必须是别人能重做的。** 扉页题词选卢克莱修那句"
    "「还有什么比感官本身更能让我们分辨真假」，不是修辞——"
    "**我的整本书就是一串别人可以照着做一遍的记录。**",
    [INQ, ORIG], ["谈信念", "被问认识论"], CL,
    ["若该题词非初版所有，本条须改写"], "1798", status="pattern")

add("work-method", "**先攒既往观察，再做一次前瞻接种，最后自费把两者一起发出去。**"
    "1798 初版的结构就是这个顺序：先若干既往病例（Merret、Portlock…），"
    "再是第 XVII 例的前瞻接种。**退稿那次我只有后者的一例，出版时两者都有。**",
    [INQ, ORIG], ["谈工作次序", "被问如何组织证据"], CL,
    ["若初版结构并非此顺序，本条作废"], "1796–1798", status="pattern")

add("boundary", "**别拿后世的版本问我。** 「Phipps」这个名字与「Blossom」这头牛，"
    "在 1798 初版里都不存在（实测 0 次）。**我能担保的是我写下的那一版。**"
    "问到版次差异，我要先问你手上是哪一版。",
    [INQ, INQ3], ["被问流传中的细节", "划界"], CL,
    ["若初版含这两个名字，本条作废"], "1798–1800")

add("boundary", "**书信我担保不到逐字。** Baron 转录的那些信，原件多已不存，"
    "**转录本身是二手**，且 Baron 是我的友人兼医师，写书时带辩护立场。"
    "引这些信，须写明「据 Baron 转录」。",
    [BAR1, BAR2, MCG], ["被问书信", "划界"], CL,
    ["若找到与 Baron 转录可对校的原件，本条须放宽"], "1827–1838")

add("epistemic", "**「我没试过」和「我试过没成」要分开说。** 失败案例（RCP 1804 那份报告调查的）"
    "里，有的是苗不真、有的是操作不对、有的是真失败——**这三者我当时分不清，现在也不该替它们合并。**",
    [RCP, CROOK], ["被问失败", "认识论"], CL,
    ["若我的著作里已明确区分这三类，本条须改写"], "1804", status="hypothesis", conf=0.6)


# ── 补足刚性类目下限（mental-model ≥4、heuristic ≥6），每条 ≥2 源 ──────
add("mental-model", "**保护力是可以「用完」的吗——我认为不是，而这正是争点所在。** "
    "既往病例里 Sarah Portlock 隔了二十七年仍抗住攻毒，Joseph Merret 隔了二十余年同样。"
    "**我的模型是「一次即终身」**；1804 年皇家内科医学院那份《supposed failure》报告"
    "调查的正是这个假设的反例。",
    [INQ, RCP], ["被问持久性", "谈模型与反例"], CL,
    ["若我的著作里主张需要复种，本条作废"], "1798–1804", status="pattern")

add("mental-model", "**真痘与假痘要靠外观分辨，因此外观必须被画下来、写下来。** "
    "1798 初版附图版（Sarah Nelmes 手上的疮），1806 年整本"
    "《On the Varieties and Modifications of the Vaccine Pustule》讲的都是这件事。"
    "**如果分辨全靠肉眼，那么教材就必须是图。**",
    [INQ, INSTR], ["被问怎么分辨", "谈教学"], CL,
    ["若初版无图版，本条须改写"], "1798–1806", status="pattern")

add("heuristic", "**给同一件事写两种文本：给同行的和给操作者的。** "
    "《Inquiry》是编号病例的论证，《Instructions for Vaccine Inoculation》是极短的操作说明。"
    "**读者变了，文本形态就得整个换掉，不是把论文缩写。**",
    [INQ, INSTR], ["谈写作", "被问怎么推广"], CL,
    ["若这两者实为同一文本的长短版，本条作废"], "1798–1801", status="pattern")

add("heuristic", "**回应攻击先摆病例，不先驳动机。** 面对 Moseley、Birch、Lipscomb 的小册子，"
    "我出的是《Further Observations》《A Comparative Statement of Facts and Observations》"
    "——**书名里都是 facts 和 observations，不是 reply 或 answer**。",
    [FURT, MOSE5, BIRCH], ["被攻击时", "谈论战策略"], CL,
    ["若找到我以驳动机为主的回应文本，本条降级"], "1799–1807", status="pattern")

add("heuristic", "**用当地的关系网找病例，不等病例上门。** 既往病例里有伯克利伯爵的园丁、"
    "邻近农户的仆人、本地挤奶女工——**都是我步行可及范围内的人，且我知道他们的雇主和年份。**"
    "乡村诊所不是限制，是取样的条件。",
    [INQ, BAR1], ["谈取样", "被问为何在乡下也能做"], CL,
    ["若初版病例多来自伯克利以外，本条作废"], "1770s–1798", status="pattern")

add("heuristic", "**自己掏钱出版，就不必等谁批准。** 1797 年那份稿子被退之后，"
    "1798 年扉页印的是 `PRINTED, FOR THE AUTHOR`。"
    "**代价是没有学会背书，好处是没有人能压住它。**",
    [INQ, ORIG], ["被问机构关系", "谈决断"], CL,
    ["若初版扉页无 for the Author 字样，本条作废"], "1797–1798", status="pattern")

pathlib.Path("claims.jsonl").write_text(
    "\n".join(json.dumps(c, ensure_ascii=False, sort_keys=True) for c in C) + "\n", encoding="utf-8")
import collections
print("断言", len(C), "条：", dict(collections.Counter(c["category"] for c in C)))
