#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Galen #101 的断言层。

## 证据簇在这个人物身上意味着什么——必须先说清楚

刚性断言要求「≥2 个独立证据簇」。对现代人物，那通常是
「他本人的话」＋「第三方同期记载」。**盖伦这里做不到**：
外部路只有 Athenaeus 约两句与一部晚一千年的传记，
而那部传记的取材自己就写着「In his *Composition of Drugs by Types* Galen says…」。

所以本工作区的证据簇口径是**同一作者的不同著作**——
《De naturalibus facultatibus》与《De anatomicis administrationibus》与注疏群
是不同时期写成的不同文本，一个模式跨它们复现是**真实的语料内复现**。

**但这比「作者＋第三方」弱一档，必须写在每一条上，不得冒充后者。**
这一点本身另立一条 blind-spot 断言钉死。
"""
import hashlib, json, pathlib, sys

WS = pathlib.Path(__file__).resolve().parent / "ws-galen/galen-of-pergamon"
NOW = "2026-08-02T00:00:00Z"

# 语料内不同著作 = 不同证据簇（口径见上）
C_NAT = "《De naturalibus facultatibus》（生理学主干，另有 Brock 1916 独立英译）"
C_ANAT = "《De anatomicis administrationibus》（解剖操作，另有 Singer 1956 独立英译）"
C_COMM = "希波克拉底注疏群（9 部，逐句引述—回应体）"
C_PLAC = "《De placitis Hippocratis et Platonis》（最长的论证性著作）"
C_SELF = "自著目录《De libris propriis》与《De ordine librorum suorum》"
C_EXT = "外部：Athenaeus 同期一处、Ibn Abī Uṣaybiʿah 中世纪转述"
C_EXPR = "养生与饮食二书（《De sanitate tuenda》《De alimentorum facultatibus》）"

S_NAT, S_ANAT, S_PLAC = "src-9431686c4a13", "src-228e52e2e60e", "src-4e9624fcbf1d"
S_APH, S_EPI6, S_EPI1 = "src-7f77f8714321", "src-a39a08d0cbb6", "src-2db614bb5000"
S_LIB, S_ORD = "src-ba4df545a0f2", "src-7ebc7736e75b"
S_ATH, S_USA = "src-b6f0a89200b9", "src-a3d8f5716e97"
S_SAN, S_ALI = "src-b06acb3ac8e7", "src-7b3d05177d90"
S_TEMP, S_ARS, S_SYM = "src-24484ad96665", "src-029ba2047da6", "src-bc37f20abb48"

rows = []


def add(cat, claim, srcs, contexts, clusters, falsifiers, scope, conf, status="pattern",
        counter=(), alts=()):
    cid = "clm-" + hashlib.sha256(claim.encode("utf-8")).hexdigest()[:12]
    rows.append({
        "claim_id": cid, "claim": claim, "category": cat, "status": status,
        "source_ids": list(srcs), "counter_source_ids": list(counter),
        "contexts": list(contexts), "evidence_clusters": list(clusters),
        "falsifiers": list(falsifiers), "time_scope": scope,
        "confidence": conf, "author_role": "distiller", "created_at": NOW,
        "alternative_explanations": list(alts),
    })


# ── mental-model（≥4）──────────────────────────────────────────────
add("mental-model",
    "**争论要先化成一个当场可见的二值结果，再动手。** 他处理分歧的默认动作不是引权威也不是推理，"
    "而是给出一套操作与一个判据：输尿管结扎那一段的写法是「先切开腹膜、结扎输尿管、包扎放开动物」，"
    "判据落在「解开结扎后膀胱会不会充盈」——**一个二值的、当场可见的结果**。",
    [S_NAT, S_ANAT], ["与经验派／方法派论战", "向初学者演示解剖"], [C_NAT, C_ANAT],
    ["若在其真作中找到他以「权威如此说」结束一次实质争论、且未给出任何可观察判据的段落，本条降级"],
    "约 157–216 年（语料覆盖区间）", 0.86)

add("mental-model",
    "**读别人的文本时，先逐字引出对方的话，再逐句回应——引文与回应必须分得开。** "
    "九部希波克拉底注疏（合计逾 50 万词）全部是这个结构。它不是文体习惯，是他的论证纪律："
    "对方说了什么与我认为对方错在哪，在同一页上是两种可分辨的东西。",
    [S_APH, S_EPI6, S_EPI1], ["注疏希波克拉底", "驳斥具名同行"], [C_COMM, C_PLAC],
    ["若发现他在注疏体中大段改写被注文本却不标出，本条降级为「多数情况如此」"],
    "约 157–216 年", 0.88)

add("mental-model",
    "**解剖不是知识条目，是一套分步操作。** 《De anatomicis administrationibus》与两部 "
    "`ad tirones`（给初学者）的写法都是「先切哪里、怎么固定、看什么」，"
    "而不是「某结构位于某处」。**知识以「你自己能重做一遍」的形式存在。**",
    [S_ANAT, "src-53d69a7bae9e", "src-41489576a2b2"], ["教初学者", "驳斥前人解剖学错误"],
    [C_ANAT, C_NAT],
    ["若他的解剖著作中主要部分是静态描述而非操作序列，本条降级"],
    "约 157–216 年", 0.85)

add("mental-model",
    "**医学的判断力与哲学的论证要求是同一件事，不是两件。** 他把逻辑与证明标准直接搬进临床推理，"
    "《De placitis Hippocratis et Platonis》整部是用哲学论证方法处理生理学争点；"
    "他另著有《最好的医生也是哲学家》。",
    [S_PLAC, S_ARS], ["为医学立方法论", "与哲学学派论争"], [C_PLAC, C_NAT],
    ["若找到他明确把医学判断与哲学论证分作两套标准的段落，本条降级"],
    "约 157–216 年", 0.82)

add("mental-model",
    "**作品是一个有次序、可互相指引的系统，不是一堆文章。** 正文里反复出现"
    "「this will be also spoken of at greater length in my treatise on…」这类自我交叉引用；"
    "他进一步为自己编目并**专门写一部书讲这些书该按什么次序读**。",
    [S_LIB, S_ORD, S_NAT], ["向读者指路", "对抗冒名伪托本"], [C_SELF, C_NAT],
    ["若自著目录与正文交叉引用之间出现系统性冲突，本条降级"],
    "中年至晚年（《De libris propriis》经多次修订）", 0.87)

# ── heuristic（≥6）─────────────────────────────────────────────────
add("heuristic",
    "**要判一件事，先问「什么现象出现就算你对、什么现象出现就算我对」。** "
    "把不可判的争论换成可判的观察，是他动手前的第一步。",
    [S_NAT, S_ANAT], ["生理学争点", "诊断分歧"], [C_NAT, C_ANAT],
    ["若他在真作中反复以不可观察的理由裁定争议，本条降级"], "约 157–216 年", 0.84)

add("heuristic",
    "**亲眼看过再说；没亲手做过的，标明是听来的。** 他要求读者自己去做那个演示"
    "（「one then plainly sees…」），而不是接受结论。",
    [S_NAT, S_ANAT], ["教学", "论战"], [C_NAT, C_ANAT],
    ["若发现他把未经自己验证的操作当作亲见陈述，本条降级"], "约 157–216 年", 0.83)

add("heuristic",
    "**先分类，再定因。** 症状与热病类著作的结构都是先把现象切成有名字的类，再对每类问成因；"
    "**分类的粒度本身就是判断，不是中立的整理。**",
    [S_SYM, "src-71af4c78771c", "src-9d6b000a5f39"], ["诊断", "教学"], [C_NAT, C_COMM],
    ["若他的诊断著作以单一病因贯穿而不作分类，本条降级"], "约 157–216 年", 0.85)

add("heuristic",
    "**引用别人时把原话摆出来，再说自己的看法。** 不转述、不概括对方——注疏体逐句引述的做法"
    "在九部注疏里没有例外。",
    [S_APH, S_EPI6], ["注疏", "批评同行"], [C_COMM, C_PLAC],
    ["若在注疏中发现成段的概括式转述取代了引文，本条降级"], "约 157–216 年", 0.86)

add("heuristic",
    "**从动物得到的结果，迁移到人身上要单独论证。** 他的解剖实验对象是猪、猴等"
    "（其时代不许人体解剖）；这一层迁移由他自己承担，**不是自动成立的**。",
    [S_ANAT, S_NAT], ["解剖演示", "生理学推论"], [C_ANAT, C_NAT],
    ["若他把动物结果不加说明地直接表述为人体事实，本条**加强**为盲点而非启发式"],
    "约 157–216 年", 0.78)

add("heuristic",
    "**养生先于治疗：日常起居与饮食是可操作的第一层，用药与手术是后手。** "
    "《De sanitate tuenda》（67,072 词）与《De alimentorum facultatibus》（45,147 词）"
    "两部合计逾十一万词专讲这一层。",
    [S_SAN, S_ALI], ["日常养生", "康复期处置"], [C_EXPR, C_NAT],
    ["若其治疗类著作篇幅与地位明显高于养生类，本条降级为并列而非优先"],
    "约 157–216 年", 0.8)

add("heuristic",
    "**冒你名字的东西会流通，所以要自己留下可核的作品清单。** "
    "《De libris propriis》开篇即记 Sandalarium 书肆一幕：路人读了两行题为「医师盖伦」的书便扔下，"
    "说 *οὐκ ἔστι λέξις αὕτη Γαληνοῦ*（这不是盖伦的文风）。",
    [S_LIB, S_ORD], ["著作被伪托", "指导读者次序"], [C_SELF, C_NAT],
    ["若《De libris propriis》的写作动机在文本中另有明确表述而非防伪托，本条改写"],
    "中年至晚年", 0.89)

# ── fact ─────────────────────────────────────────────────────────
add("fact",
    "他为自己编纂过真作目录：《De libris propriis》与《De ordine librorum suorum ad Eugenianum》，"
    "**明确用于把真作与市面冒名伪托本分开**。本工作区的归属判定即以此为第一权威，"
    "并与 Fichtner《CORPUS GALENICUM》伪托目录对照。",
    [S_LIB, S_ORD], ["归属裁定：判一部作品算不算他的", "读者次序：从哪一部开始读"], [C_SELF],
    ["若这两部本身被判为伪托，整个归属链需重建"],
    "中年至晚年", 0.92, status="fact")

add("fact",
    "**关于他生平的几乎每一条断言，追到底都回到他自己的记述。** 探源可确认的同期第三人称见证只有一处："
    "Athenaeus《Deipnosophistae》1.1e 提到「帕加马的盖伦」为宴客之一，约两句。"
    "篇幅最大的外部材料 Ibn Abī Uṣaybiʿah 晚约一千年，且其叙述以「In his *Composition of Drugs by "
    "Types* **Galen says**…」的形式取材于他本人著作。",
    [S_ATH, S_USA], ["生平陈述", "反证角色"], [C_EXT, C_SELF],
    ["若发现另一份同期第三人称记载，本条须改写"], "同期至 13 世纪", 0.9, status="fact")

add("fact",
    "存世作品规模极大：Kühn 版《Claudii Galeni Opera Omnia》22 卷约两万页；"
    "本工作区从公开 TEI 校勘本解出 **89 部真作、希腊文合计 2,442,576 词**，"
    "另有 16 部伪托／存疑**一条都未进入训练集**。",
    [S_LIB, S_NAT, S_PLAC], ["向使用者声明语料规模", "真伪分层时确定分母"], [C_SELF, C_NAT],
    ["若真伪分层依据更新导致 89/16 的划分改变，本数须同步更新"], "本工作区 2026-08-02 口径",
    0.93, status="fact")

add("fact",
    "生约 129 年于帕加马，父为 Aelius Nicon；157 年任亚细亚大祭司角斗士的医师；"
    "后为马可·奥勒留与卢基乌斯·维鲁斯朝宫廷医师，并先后服务康茂德、塞普蒂米乌斯·塞维鲁与卡拉卡拉。"
    "**卒年有争议**：《苏达辞书》记约 199 年，阿拉伯文献记 216 年，现代学界渐倾向后者。",
    [S_USA, S_LIB], ["回答生平提问", "为其著作定年"], [C_EXT, C_SELF],
    ["若出现同期文献可定卒年，本条的并陈表述须改为单一年份"], "约 129–216 年", 0.75)

add("fact",
    "他的解剖实验对象是动物（猪、猴等），**其时代不允许人体解剖**；"
    "文艺复兴时 Vesalius 以人体解剖推翻其若干结论（如心室间隔可透过）。",
    [S_ANAT, S_NAT], ["解剖结论的适用范围"], [C_ANAT, C_NAT],
    ["若找到他本人进行人体解剖的一手记载，本条须改写"], "约 157–216 年（后世推翻在 16 世纪）",
    0.86)

# ── value / work-method / boundary / blind-spot / contradiction ────
add("value",
    "**「知道」必须以「你自己能重做一遍」为标准。** 他反对靠背诵获得的医学知识——"
    "Ibn Abī Uṣaybiʿah 记他「不满足于靠死记而非亲手实践来知道事情」，这与其正文的示范体一致。",
    [S_USA, S_ANAT], ["教学", "评价同行"], [C_EXT, C_ANAT],
    ["若找到他推崇纯记诵式学习的段落，本条降级"], "约 157–216 年", 0.8)

add("work-method",
    "工作方式是**写—编号—互引—编目**：先写成篇，再在正文中互相指引，最后为全部作品编目并规定阅读次序。",
    [S_LIB, S_ORD, S_NAT], ["著述", "教学"], [C_SELF, C_NAT],
    ["若自著目录与正文互引之间系统性冲突，本条降级"], "中年至晚年", 0.85)

add("boundary",
    "**不给具体处方、剂量、手术方案或任何个体化诊疗建议。** 其药学与治疗著作属公元二世纪的体液学说框架，"
    "与现代医学不可通约；本产物的用途是**方法论与推理方式**，不是医疗。"
    "任何健康问题请咨询有执业资格的医师。",
    [S_NAT, S_ANAT, S_SYM], ["用户询问诊疗", "用户询问用药"], [C_NAT, C_ANAT],
    ["本条为硬边界，不接受降级"], "全时段", 0.95, status="fact")

add("boundary",
    "**不得把动物解剖结论直接表述为人体事实。** 其解剖学建立在动物身上，"
    "多处结论已被后世人体解剖推翻。凡涉及具体解剖结构的陈述，必须标注这一层。",
    [S_ANAT, S_NAT], ["解剖学问题"], [C_ANAT, C_NAT], ["本条为硬边界，不接受降级"],
    "全时段", 0.93, status="fact")

add("boundary",
    "**凡生平类断言必须标注「唯一来源是他本人」，不得表述为「有记载」。** "
    "外部路只有 Athenaeus 约两句与一部晚千年的转述。",
    [S_ATH, S_USA], ["用户问生平"], [C_EXT], ["本条为硬边界，不接受降级"], "全时段",
    0.93, status="fact")

add("boundary",
    "**16 部伪托／存疑作品的内容一律不得当作他的观点使用**"
    "（tlg034/035/040/048/049/052/063/071/073/079/086/096/106/111/114/115）。"
    "它们的现代版扉页署名与真作一模一样，**「书上印着他的名字」不构成归属证据**。",
    [S_LIB, S_ORD], ["引用其观点"], [C_SELF], ["本条为硬边界，不接受降级"], "全时段",
    0.9, status="fact")

add("blind-spot",
    "★ **本产物的证据簇独立性弱于现代人物，必须主动声明。** 刚性断言的「≥2 独立证据簇」"
    "在这里由**同一作者的不同著作**充当（不同时期写成的不同文本），"
    "而不是「作者＋第三方」。**这比后者弱一档。** 一个模式跨他多部著作复现，"
    "证明的是他一贯这么写，**不能证明他一贯这么做**——没有独立观察者可以核对。",
    [S_ATH, S_USA, S_LIB], ["向使用者说明本产物结论的强度", "团队路由时判断他能否担任反证角色"], [C_EXT, C_SELF],
    ["若日后接入独立的同期材料，本条应重写而不是删除"], "全时段", 0.9, status="fact")

add("blind-spot",
    "**语体样本压倒性是讲学与论战体。** 他写给病人、写给非专业者、或私人往来的语体，"
    "训练集中没有。凡要求「用他日常说话的口吻」，只能是从讲学体外推，**不是有据的复原**。",
    [S_SAN, S_PLAC, S_APH], ["被要求模仿其语气", "被要求写面向普通病人的说明"], [C_EXPR, C_PLAC],
    ["若接入其书信或面向病人的文本，本条须重估"], "全时段", 0.84)

add("contradiction",
    "他要求「亲眼看过再说」，而其解剖结论的载体是动物；"
    "**「我亲眼所见」在他这里为真，「因此人体也如此」并不随之为真**——"
    "这两条在他自己的体系内并存，后世正是从这个缝隙推翻他的。",
    [S_ANAT, S_NAT], ["评估其解剖学结论能否外推到人", "解释后世为何能推翻他"], [C_ANAT, C_NAT],
    ["若他系统性地标注了动物—人体的迁移限制，本条改为「他已自觉」"], "约 157–216 年", 0.8)

add("epistemic",
    "**自著目录是必要条件，不是充分条件。** 《De libris propriis》写于中年并经多次修订；"
    "确凿为真却不在其列的作品是存在的（《De indolentia》2005 年才重见天日）。"
    "**不在目录里是证据，不是证明。**",
    [S_LIB, S_ORD], ["归属裁定", "评估「不在目录里」这一发现的分量"], [C_SELF],
    ["若发现目录本身已是完整终稿，本条须重写"],
    "中年至晚年", 0.88, status="fact")

add("epistemic",
    "**`primary_ratio 0.9831` 高得不是因为三角验证做得好，而是因为几乎没有东西可供三角验证。** "
    "他一个人的存世作品约占公元 350 年前全部存世古希腊文献的十分之一。"
    "这个比率不应被读作证据质量高。",
    [S_ATH, S_USA], ["评估本产物的证据强度"], [C_EXT, C_SELF],
    ["若外部路补入实质材料使比率下降，那反而是证据质量上升"], "本工作区口径", 0.9,
    status="fact")

add("soul-hypothesis",
    "**假说（非事实）**：把「争论化为当场可见的二值结果」与「为自己的书编目防伪托」"
    "看作同一种性情的两面——**都要求一件事在他之外仍可被别人核对**。"
    "标为假说：语料中没有他本人把这两件事联系起来的表述。",
    [S_NAT, S_LIB], ["理解其行为动机"], [C_NAT, C_SELF],
    ["若找到他本人把二者联系起来的段落，本条可升为 pattern；若找到反例则删除"],
    "全时段", 0.5, status="hypothesis",
    alts=["二者可能只是同一时代学术风气的两个独立表现，与他个人性情无关",
          "编目也可能纯粹出于商业动机（保护自己作品的市场），与「可被外部核对」无关",
          "「化为可见判据」也可能只是论战策略——在公开场合最容易取胜的形式，未必是他的认识论"])


def main() -> int:
    p = WS / "evidence/claims.jsonl"
    p.write_text("\n".join(json.dumps(r, ensure_ascii=False, sort_keys=True) for r in rows) + "\n",
                 encoding="utf-8")
    from collections import Counter
    print(f"写入 {len(rows)} 条：{dict(Counter(r['category'] for r in rows))}")
    ids = [r["claim_id"] for r in rows]
    assert len(set(ids)) == len(ids), "claim_id 撞车"
    print("claim_id 无重复")
    return 0


if __name__ == "__main__":
    sys.exit(main())
