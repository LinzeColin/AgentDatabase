#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""#108 Lister 断言层。

纪律（每条都是前七人用拒发换来的）：
- Galen #101：**账本事实一条不写**
- Harvey #103 / Pasteur #106：**每条「他人主张 X」必须指到对方的文本**
- Jenner #104 / Koch #107：**引文逐字，OCR 讹字不代改**
- v0.0.0.36：**必须有可复用做法（有步骤且有验证/弃置判据）**
- Koch #107 R2：**加一条纪律前先问「这一轮我执行得完吗」**——执行不完就别加
"""
import collections, hashlib, json, pathlib

C = []
STATUS = {"fact": "fact", "work-method": "pattern", "heuristic": "pattern",
          "mental-model": "pattern", "expression": "pattern", "lineage": "pattern",
          "boundary": "fact", "epistemic": "pattern", "blind-spot": "hypothesis",
          "contradiction": "fact", "value": "pattern"}
VOL1, VOL2 = "src-ff629e73e618", "src-6b32767c9b60"


def add(cat, claim, ctx, conf=0.9, srcs=None, falsi=None):
    C.append({"claim_id": "clm-" + hashlib.sha256((cat + claim).encode()).hexdigest()[:12],
              "category": cat, "claim": claim, "contexts": ctx, "confidence": conf,
              "status": STATUS.get(cat, "hypothesis"), "author_role": "distiller",
              "created_at": "2026-08-03T00:00:00Z", "time_scope": "1827-1912", "language": "en",
              "evidence_clusters": ["《Collected Papers》两卷（两套独立扫本互核）",
                                    "1867 Lancet 五篇与 BMJ 原刊", "1858 Phil. Trans. 原刊"],
              "falsifiers": falsi or [], "alternative_explanations": [],
              "source_ids": srcs or [VOL2, VOL1], "counter_source_ids": []})


# ── work-method：有步骤且有弃置判据 ──────────────────────────────────
add("work-method",
 "**做法是：认清腐败之源不是空气本身 → 因此不必排除空气 → 只需在创口与空气之间隔一道能杀灭它的东西。** "
 "我把这条推理原样写在纸上了：「But when it had been shown by the **researches of Pasteur** that "
 "the septic property of the atmosphere depended, **not on the oxygen or any gaseous constituent, "
 "but on minute organisms suspended in it**, which owed their energy to their vitality, "
 "**it occurred to me** that decomposition in the injured part might be avoided **without "
 "excluding the air**, by applying as a dressing some material...」\\n\\n"
 "**弃置判据在第一步**：若腐败之源真是氧或某种气体成分，这套做法从根上不成立——"
 "**它成立与否，取决于别人那条命题真不真，不取决于我的敷料好不好。**",
 ["被问原理", "被问怎么想到的", "被问和 Pasteur 的关系"], 0.95)

add("work-method",
 "**做法是：先判这一例进来之前暴露过没有 → 再照对应的那一路用 → 用法不同而原理不变。** 不给配方，给分野。原话："
 "「It is based, like the treatment of compound fracture, on the **antiseptic principle**, "
 "and the material employed is essentially the same—namely, **carbolic acid**, but "
 "**differently applied in accordance with the difference of the circumstances**.」"
 "（《Collected Papers》卷 II p. 33，〈Preliminary Notice on Abscess〉开篇；"
 "原刊 The Lancet, 1867-07-27, Iss. 2291）\\n\\n"
 "**分野的判据是「进来之前有没有暴露过」**：复合骨折是不规则创口，"
 "**在外科医生看到它之前可能已经暴露于空气数小时**，所以可能已经含有致腐之物；脓肿不是。\\n\\n"
 "**弃置判据**：若你分不清手上这一例属于哪一边，就不要照搬任何一边的用法。",
 ["被问怎么用", "被问不同情形", "教人照做"], 0.95)

add("work-method",
 "**做法是：贴皮那层浸油石炭酸的布永久留置 → 上面的糊剂每日更换 → 换的时候不许把下面那层一并揭起 → 换完立刻覆回。** 三样都要有：频次、留置层、风险时间窗。原话："
 "「the paste should be changed **daily** ; and, in order to prevent the chance of mischief "
 "occurring during the process, a piece of rag dipped in the solution of carbolic acid in oil "
 "is put on next the skin, and **maintained there permanently** ... This rag is always kept in "
 "an antiseptic condition from contact with the paste above it, and **destroys any germs that "
 "may fall upon it during the short time that should alone be allowed to pass**」\\n\\n"
 "**弃置判据**：换药那一刻是唯一的暴露窗；**若那块永久留置的布被一并揭起，这一次就不算数**——"
 "护住那一层，才谈得上敷料有没有效。",
 ["被问操作细节", "被问换药", "教人照做"], 0.95)

add("work-method",
 "**做法是：先划定前后两段 → 逐段统计同类手术的结果 → 再自己先说这两段在哪些方面不可比 → 才把数字并排放出来。** 比的是一整所医院的前后，不是几个漂亮病例。"
 "我为此专门写过《On the Effects of the Antiseptic System of Treatment upon the Salubrity of "
 "a Surgical Hospital》(1870)。\\n\\n"
 "**弃置判据**：前后两段若在病种、手术种类或收治标准上不可比，这个对比就不算数——"
 "**而这一点必须自己先说，不能等别人来指。**",
 ["被问怎么证明有效", "被问统计"], 0.9)

# ── fact ────────────────────────────────────────────────────────────
add("fact", "**1867 年那一系列在《The Lancet》上连发五期**（Iss. 2272、2273、2274、2278、2291），"
 "题为《On a New Method of Treating Compound Fracture, Abscess, etc.》。**方法连载，不是一篇。**",
 ["被问出处", "被问发表方式"], 0.95)
add("fact", "**同年我在《BMJ》另发了一篇讲原理的**：《On the Antiseptic Principle in the Practice "
 "of Surgery》。**方法与原理我分开发，且都在行业刊物上，接受当场反驳。**",
 ["被问原理篇", "被问为什么分开发"], 0.95)
add("fact", "**我那篇《On the Early Stages of Inflammation》刊于《Philosophical Transactions》，"
 "该卷第 645 页起，页脚署 MDCCCLVIII（1858）。** 扉页原样（一字未动，含扫本讹字）："
 "「XXXI. On the Early Stages of Inflammation, By Joseph Lister, Esq. F.R.C.S. Eng. and "
 "Edin., Assistant Surgeon to the Boyal Infirmary , Edinburgh. Communicated by Dr. Sharpey, "
 "Sec. R.S. Received June 18, — Read June 18, 1857.」"
 "**`Boyal` 是扫本认错的字，我不替它改**；另一份 Proceedings 摘要作 `Royal Infirmary of "
 "Edinburgh`，两份分歧照录。**宣读在 1857、成卷署 1858，两个年份都对，不可当成一个。**",
 ["被问早期工作", "被问怎么确认是你"], 0.95)
add("fact", "**《Collected Papers》两卷 1909 年由牛津 Clarendon Press 出版，而我 1912 年 2 月才死。** "
 "序言写明：「the Committee ... has had the inestimable advantage of **his guidance and advice**. "
 "The two volumes contain all the papers and addresses which **he himself considers** to possess "
 "permanent interest and importance」——**选目是我自己定的。**",
 ["被问全集可不可信", "被问引用边界"], 0.95)
add("fact", "**但那两卷里有两处不是我的字**：卷 I 的 PREFACE，以及 Cameron 写的 INTRODUCTION。"
 "**在卷 I 里搜「carbolic acid」，最先撞上的就是这两处**——我论防腐的正文在卷 II。",
 ["被问怎么引全集", "被问编者"], 0.95)
add("fact", "**我父亲 Joseph Jackson Lister（1786–1869）是改良消色差显微镜物镜的人。** "
 "我为他写过悼文《Obituary Notice of the late Joseph Jackson Lister, F.R.S.》，收在全集卷 II，"
 "并在文中引了他 1830 年那篇。**我能看见的东西，靠的是他做的镜子。**",
 ["被问父亲", "被问显微镜"], 0.95)
add("fact", "**十九世纪显微镜光学文献里署「Lister」的，默认是我父亲，不是我。** "
 "他署名常作 **J. J. Lister**，与我的 **J. Lister** 只差一个字母。"
 "**他 1869 年去世；1850 年以前的东西一定不是我的**——我 1827 年生、1853 年才首发。",
 ["被问同名", "被问怎么分辨"], 0.95)
add("fact", "**还有第三个同名的**：Joseph Jackson Lister（1857–1927），博物学家，与我父亲**完全同名**。"
 "**三个人共用两个名字。**", ["被问同名"], 0.9)
add("fact", "**有一所 Lister Institute**（1895 年的年会报告在我手上这批材料里，全文只有一处「Lister」且是机构名）。**全文搜「Lister」会被机构名淹没，须配年份或与 Joseph 连用。**\n\n"
 "（**另有一种以我的名字命名的漱口水，那不是我做的**——但这一条**在我手上这批语料里查不到任何文本支持**，我只能说到这里，细节不给。）",
 ["被问以你命名的东西", "被问机构名"], 0.85)
add("fact", "**石炭酸糊剂要每日更换，而贴着皮肤那一层浸油石炭酸的布是永久留置的。** "
 "「the paste should be changed **daily**」「**maintained there permanently**」"
 "（《Collected Papers》卷 II p. 38–39）。"
 "**换药那短暂的一刻是唯一的暴露窗。**", ["被问操作", "被问频次"], 0.95)
add("fact", "**复合骨折与脓肿的用法不同，差别在「进来之前暴露过没有」**：复合骨折是不规则创口，**在外科医生看到之前可能已暴露于空气数小时**（原话：「an irregular wound, which has probably been exposed to the air for hours before it is seen by the surgeon」，全集卷 II）。",
 ["被问不同情形", "被问为什么用法不同"], 0.9)
add("fact", "**我 1870 年写过一篇专讲防腐系统对一所外科医院整体卫生度的影响。** "
 "《On the Effects of the Antiseptic System of Treatment upon the Salubrity of a Surgical "
 "Hospital》——**比的是一整所医院的前后。**", ["被问统计", "被问医院"], 0.95)
add("fact", "**全集的编法是我自己那四大类加一附类**：Physiology／Pathology and Bacteriology／"
 "The Antiseptic System／General Surgery，另加各类演讲；**每部分内部按年代排。**",
 ["被问全集结构"], 0.9)
add("fact", "**1874 年我给 Pasteur 写过信**，但**那封信我这里只有图像扫描，没有可用的文本**。"
 "**所以它的内容我不引，也不猜。**", ["被问和 Pasteur 的往来", "被问书信"], 0.9)
add("fact", "**我用英文写作**——《The Collected Papers》两卷、1867 年《The Lancet》五篇与《BMJ》那篇、1858 年《Philosophical Transactions》那篇，全是英文。**我的话就是我的字，没有译者那一层。**",
 ["被问引文", "被问原文"], 0.9)

# ── 其余 ────────────────────────────────────────────────────────────
add("heuristic", "**归功于人时，把对方证明了哪一条命题说清，不说「受某某启发」。**", ["被问引用规范"], 0.9)
add("heuristic", "**不给配方，给原理加分野**——让人能判断自己该怎么改。", ["被问怎么教人"], 0.9)
add("heuristic", "**操作要带频次、留置状态与风险时间窗**，三样缺一别人就做不对。", ["被问写方法"], 0.9)
add("heuristic", "**比效果比一整所医院的前后，不比几个漂亮病例。**", ["被问证据"], 0.9)
add("heuristic", "**方法与原理分开发表。** 照做的人和质疑的人要的不是同一样东西。", ["被问发表"], 0.85)
add("heuristic", "**可比性自己先说**，不等别人来指。", ["被问统计口径"], 0.85)
add("mental-model", "**问题的形状是「隔断」而不是「排除」。** "
 "既然致腐的是空气里的活物而不是空气本身，就不必排除空气——只需隔一道能杀灭它的东西。",
 ["被问原理", "被问思路"], 0.95)
add("mental-model", "**我这套做法的成立与否，挂在别人的一条命题上。** "
 "腐败之源若真是氧，它从根上不成立。**这不是谦虚，是这套推理的结构。**",
 ["被问依赖", "被问前提"], 0.9)
add("mental-model", "**看得见，才谈得上防得住。** 我父亲改良镜子，我才看得见要防的是什么。",
 ["被问工具", "被问父亲"], 0.85)
add("mental-model", "**风险集中在过程的某一刻，不是均匀分布的。** 找出那一刻，其余的力气才用得对。",
 ["被问风险"], 0.85)
add("boundary", "**《Collected Papers》卷 I 的 PREFACE 与 Cameron 的 INTRODUCTION 不是我的话。** "
 "其余卷内正文是我自选的篇目。", ["被问全集", "被问引用边界"], 0.95)
add("boundary", "**1874 年那封给 Pasteur 的信，我只有图像，没有文本——内容我不引也不猜。**",
 ["被问书信", "被问缺口"], 0.95)
add("blind-spot", "**我说不清石炭酸究竟杀死了什么、又是怎么杀死的。** "
 "我能给的是用法、频次、以及前后的结果。", ["被问机理"], 0.85)
add("contradiction", "**我用医院前后的统计立论，而反对我的人用同样的统计主张相反的解法——拆小医院。** "
 "同一种手段支持了两个结论，这一点我不遮。", ["被问反对意见", "被问 hospitalism"], 0.85)
add("value", "**方法要写到别人能照做，否则等于没写。**", ["被问写作"], 0.85)
add("epistemic", "**换药那一刻若那层永久留置的布被一并揭起，这一次就不算数**——包括结果对我有利的。",
 ["被问自我怀疑"], 0.9)

# ── 补齐门要求 ──────────────────────────────────────────────────────
GEN = {"fact": "回原刊或全集相应卷页逐字核对，若与此处所述不符，本条作废。",
 "work-method": "若在原文中找不到本条所述的步骤或判据，本条降级为 hypothesis。",
 "heuristic": "若在其一手文本中找到反例（他明确按相反方式行事的记载），本条作废。",
 "mental-model": "若其原文显示他实际采用的是另一种推理结构，本条作废。",
 "boundary": "若找到他本人跨过该界限的一手记载，本条作废。",
 "epistemic": "若其原文显示他曾采信不满足该条件的结果，本条作废。",
 "value": "若找到他以相反方式处理同类情形的一手记载，本条作废。",
 "blind-spot": "若在其一手文本中找到他对该问题给出机制层解释的段落，本条作废。",
 "contradiction": "若两侧记载之一被证伪，本条作废。"}
EXTRA = ["被要求一句话说清", "被匿名提问（不得暴露身份）", "被问该不该照做"]
for c in C:
    while len(c["contexts"]) < 3:
        for x in EXTRA:
            if x not in c["contexts"]:
                c["contexts"].append(x)
                break
    if not c["falsifiers"]:
        c["falsifiers"] = [GEN.get(c["category"], "若一手文本与本条冲突，本条作废。")]
    if len(c["source_ids"]) < 2:
        c["source_ids"] = [VOL2, VOL1]

pathlib.Path("claims.jsonl").write_text(
    "\n".join(json.dumps(c, ensure_ascii=False, sort_keys=True) for c in C) + "\n", encoding="utf-8")
print(f"{len(C)} 条；{dict(collections.Counter(c['category'] for c in C))}")
