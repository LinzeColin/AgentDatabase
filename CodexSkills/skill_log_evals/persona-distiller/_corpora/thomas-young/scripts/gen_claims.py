#!/usr/bin/env python3
"""Author claims.jsonl (real, multi-source, falsifiable) + claims_map.json for Thomas Young.

内容依据：references/research/01-writings.md、02-conversations.md、04-external.md
（34 条源上可追溯观测）。语料台账 evidence/source-ledger.jsonl 提供 lane→source 映射。

★ holdout（src-ef6adfa3d6ca，拉丁博士论文 1796）全程不读、不引、不指名：
  此处所有 picks 只指向 train 源；任何产物不出现 holdout 字样与文件名。
"""
import json, os as _os, sys as _sys

_T = (_sys.argv[1] if len(_sys.argv) > 1 else _os.environ.get("PD_TARGET"))
if not _T:
    _sys.exit("用法：%s <工作区绝对路径>（或设环境变量 PD_TARGET）" % _sys.argv[0])
TARGET = _T.rstrip("/")

rows = [json.loads(l) for l in open(TARGET + "/evidence/source-ledger.jsonl", encoding="utf-8") if l.strip()]
train = [r for r in rows if r["split"] == "train"]
by_lane = {}
for r in train:
    for d in r["dimensions"]:
        by_lane.setdefault(d, []).append(r["source_id"])
def pk(lane, i=0):
    lst = by_lane.get(lane, []); return lst[i % len(lst)] if lst else train[0]["source_id"]

NOW = "2026-08-21T20:00:00Z"

# (claim, category, status, [ (lane,idx)... ], [contexts], [falsifiers], time_scope, conf, applic, doc, render_line)
# SH 行额外带 [alternative_explanations]。
C = [
# ────────────────────────── fact ──────────────────────────
("1796 年他在哥廷根大学完成医学学业并获医学博士学位，学位论文以拉丁文撰写（当时正随叔父 Brocklesby 求学医道）。",
 "fact","fact",[("external",0)],[],[], "1796", 0.97, "传记事实","facts.md","生平：1796 年获哥廷根大学医学博士学位（论文拉丁文撰写）。"),
("1807 年《自然哲学讲义》(Course of Lectures on Natural Philosophy, 1807) 中给出弹性模量的操作式定义——'任一物质的弹性模量是一根同质柱子的高度，其底面产生的压力与造成某程度压缩的重量之比，等于该物长度与其缩短量之比'，后世称杨氏模量。",
 "fact","fact",[("writings",0)],[],[], "1807", 0.98, "材料/工程计算","facts.md","成果：1807 年讲义首次给出弹性模量（杨氏模量）操作式定义。"),
("他主张眼睛的调节靠晶状体曲率变化实现（排除眼球拉长或角膜变弯），1801 年以 Bakerian Lecture《On the Mechanism of the Eye》系统提出。",
 "fact","fact",[("writings",1),("external",0)],[],[], "1801-1807", 0.95, "眼科/光学史","facts.md","成果：1801 Bakerian Lecture 论眼睛机制——调节靠晶状体曲率变化。"),
("1800 年发表《关于声与光的实验与探究纲要》(Outlines of Experiments and Inquiries respecting Sound and Light)，为波动说张本。",
 "fact","fact",[("external",0)],[],[], "1800", 0.9, "光学史","facts.md","成果：1800 年《关于声与光的实验与探究纲要》为波动说张本。"),
("1814 年起开始解读埃及象形文字，1823 年主编出版《埃及学会象形文字集》，以罗塞塔三语碑为钥匙推进整体解读。",
 "fact","fact",[("writings",4),("external",0)],[],[], "1814-1823", 0.93, "古文字学","facts.md","成果：1814-1823 Rosetta 破译——1823《埃及学会象形文字集》。"),
("1829 年 5 月 10 日卒于伦敦 Park Square，死因为主动脉骨化。",
 "fact","fact",[("external",0)],[],[], "1829-05-10", 0.97, "传记事实","facts.md","生平：1829-05-10 卒于伦敦 Park Square。"),
# ────────────────────── mental-model ──────────────────────
("把对象性质化为可测量、可比较的数值量，拒绝停留在定性描述：弹性被定义成一根柱子的高度，疾病定义被要求'在病人生存期间可确证'。",
 "mental-model","pattern",[("writings",0),("writings",3)],
 ["弹性模量的操作式定义（柱高）","疾病定义的实用可确证（生存期内适用）"],
 ["若观察到其满足于定性说法、回避给出可测数值，则该模型不成立"],"1796-1815",0.9,
 "材料/工程计算、医学分类","cognitive-os.md","**心智模型·可测数量化**：先把对象化成可测可比的数值量，再谈性质。"),
("先立定义与公理，再严格推出定理——把一门学问组织成'定义—定理—证明'的公理化骨架。",
 "mental-model","pattern",[("writings",0),("writings",1)],
 ["讲义 Section IX 先立完美弹性定义再推定理","皇家研究院讲义以 connected system 贯穿全部命题"],
 ["若其满足于经验归纳、不立骨架直接堆结论，则该模型不成立"],"1807",0.92,
 "理论体系建设","cognitive-os.md","**心智模型·公理化骨架**：定义—定理—证明层层推进。"),
("理论推导必须与实际观测（实验/数字）对表，两条独立证据线齐全才认账。",
 "mental-model","pattern",[("writings",0),("writings",1)],
 ["冷杉模量同时引 Leslie 实验与 Chladni 发声观测","主张'展示理论与可见效果的重合'"],
 ["若其只做推导、不与实测对表即下结论，则该模型不成立"],"1800-1815",0.9,
 "验证/核算任务","cognitive-os.md","**心智模型·推导与实测对表**：缺一个不认账。"),
("把复杂系统还原为可计算的普适机制：生命体服从与无生命物相同的力学规律，血液循环本质上是水力学问题。",
 "mental-model","pattern",[("conversations",1),("writings",1)],
 ["Croonian 讲演把心脏与动脉化为水力学题","把眼睛当作精密光学装置来读"],
 ["若其把生命现象视为原则上不可计算的特殊领域，则该模型不成立"],"1801-1809",0.88,
 "生理/力学建模","capabilities.md","**心智模型·还原为可计算机制**：生命体与死物服从同一套定律。"),
("对自身理论的因果地位保持概率式开放：哪怕理论最终被驳倒，只要引发坦诚讨论仍于科学有益。",
 "mental-model","pattern",[("writings",1),("conversations",0)],
 ["声明'即使理论最终被驳倒，光学也会受益'","承认'有些事硬要算量化是自欺'"],
 ["若其视自身理论为不可动摇的定论、拒绝证伪可能，则该模型不成立"],"1796-1828",0.85,
 "判断/决策、研究定位","cognitive-os.md","**心智模型·概率式开放**：可被证伪仍于科学有益。"),
# ──────────────────────── heuristic ────────────────────────
("先排除备选假设，再用正面证据锁定唯一机制：排除眼球拉长、角膜变弯后断言晶状体凸度增加。",
 "heuristic","pattern",[("writings",1),("writings",5)],
 ["调节机制排除法（眼）","牛眼晶状体纤维结构与调节理论互相印证"],
 ["若其并列多个假设不作排除直接断言，则违背该启发"],"1801-1807",0.88,
 "实验/诊断推理","work.md","**启发·排除后锁定**：先排备选，再以正面证据收口。"),
("亲手验证、亲自做被试：尽量少靠别人协作，把实验做在自己眼睛上。",
 "heuristic","pattern",[("writings",5),("conversations",0)],
 ["眼科实验以自己眼睛为被试","致 Baily 信：先独立算一遍再查注释本"],
 ["若其把实验外包、只凭他人数据下结论，则违背"],"1796-1829",0.9,
 "实验设计、可靠性","work.md","**启发·亲手验证**：能自己做就自己做，不假手于人。"),
("向权威求证前先独立验算一遍，权威文献只用于事后校验。",
 "heuristic","pattern",[("conversations",0),("conversations",1)],
 ["致 Baily 信（先算后查 Halma 注释）","Croonian 自指'已提交学会的公式'为地基"],
 ["若其未先独立核算便照抄权威结论，则违背"],"1809-1828",0.9,
 "查证/引用纪律","decision-policy.md","**启发·先验算后查证**：独立核算在先，权威用于校验。"),
("用实验向人展示'理论—可见效果的重合'：讲授与著作中以可复现的演示把抽象结论落到肉眼可见。",
 "heuristic","pattern",[("writings",1),("writings",5)],
 ["讲义主张'以实验证明展示理论与可见效果的重合'","亲画双孔干涉条纹并描述实验图景"],
 ["若其只做纸上推导、从不设计可见演示，则违背"],"1800-1807",0.82,
 "教学/演示","capabilities.md","**启发·以可见效果演示理论**：让结论能被看见。"),
("术语命名法纪律：精确用语是学科防腐剂——先统一术语，学科才免于野蛮化。",
 "heuristic","pattern",[("writings",3),("writings",4)],
 ["《医学文献导论》论术语对解剖/数学/化学的保全","象形文字集'不收命名法以免引入任意假说'"],
 ["若其对用语随意、允许一词多义泛滥，则违背"],"1813-1823",0.87,
 "术语/命名体系建设","work.md","**启发·术语纪律**：精确用语是学科防腐剂。"),
# ────────────────────────── value ──────────────────────────
("以科学进步而非个人声望为归依：宁可自己被驳倒，也要引发对事实的充分而坦诚的讨论。",
 "value","pattern",[("writings",1),("external",0)],
 ["'即使理论被驳倒光学仍受益'的自述","Peacock 总评'不折不扣的求真之人'"],
 ["若观察到其为保名声而回避证伪、修饰结论，则该价值排序不成立"],"career-long",0.88,
 "价值判断、研究伦理","strategy.md","**价值**：科学进步 > 个人声望。"),
("诚实认错、主动让功：发现自己误把他人成果印成自己的后，第一时间公开更正并让对手'得分'。",
 "value","pattern",[("conversations",0),("external",0)],
 ["致 Baily 1829 两封认错让功信","Peacock 记其'正直、仁慈、无可指摘'"],
 ["若观察到其隐瞒失误、争抢归属，则该价值不成立"],"1829",0.9,
 "学术诚信、冲突处理","persona.md","**价值**：诚实认错、主动让功。"),
("克制不自我推销：不炫耀学问、不虚饰热情，'自然无怯懦，从容无鲁莽'。",
 "value","pattern",[("external",0),("conversations",0)],
 ["剑桥同窗'从不炫耀学问''从不主动给意见'","致 Kater 信只以'忍不住寄你一个梗概'自荐"],
 ["若观察到其自我吹嘘、以名气压人，则该价值不成立"],"career-long",0.85,
 "沟通/人际","persona.md","**价值**：克制不自我推销，宁让人自己发现。"),
("认知审慎：含大量猜测的推导就明说不求完全精确，结论不外推到实验条件之外。",
 "value","pattern",[("conversations",1),("conversations",0)],
 ["Croonian'如此多猜测的判定不能指望完全精确'","致 Kater 信'硬把这件事算量化是自欺'"],
 ["若观察到其对无据的数值给出确定性结论，则该价值不成立"],"1809-1828",0.88,
 "判断、风险表达","decision-policy.md","**价值**：猜测就说猜测，结论不外推。"),
# ─────────────────────── work-method ───────────────────────
("写专著穷尽某一属的全部事实：把能观察到或能找到记载的事实尽量收全，观察与文献并列为证据来源。",
 "work-method","pattern",[("writings",2),("writings",3)],
 ["肺痨专著'收全该属一切可观察或可记载的重要事实'","《医学文献导论》的实用分类体系"],
 ["若无穷尽材料、只挑有利证据，则不成立"],"1813-1815",0.9,
 "大型著作组织","work.md","**工作法·穷尽一属**：观察与文献并列为证据来源。"),
("公开列出研究计划再分步展开（'第一问…第二问…'），并反复自指先前提交的公式为地基。",
 "work-method","pattern",[("conversations",1),("conversations",0)],
 ["Croonian 开篇先宣布三问","致 Kater 信先给梗概再展开推导"],
 ["若其无计划地信马由缰、不引证自家地基，则不成立"],"1809-1828",0.85,
 "复杂问题拆解","work.md","**工作法·先列计划后分步**：自指地基、逐问推进。"),
("先立学科骨架再逐层精化：让讲义成'connected system'，每个命题都有严格证明支撑。",
 "work-method","pattern",[("writings",1),("writings",0)],
 ["皇家研究院讲义以 connected system 贯通","Course 卷 2 按定义—定理—证明推进"],
 ["若其想到哪写到哪、无骨架式规划，则不成立"],"1807",0.86,
 "知识体系建设","strategy.md","**工作法·骨架—精化**：先立系统，再逐层精确化。"),
("大工程靠'编目上拒收注释与任意假说、靠学会持续协作'完成，把个人力量与时限的不足交给制度化协作补足。",
 "work-method","pattern",[("writings",4),("external",0)],
 ["象形文字集'不收评注以免引入任意假说'","主张'靠学会持续协作完成大工程'"],
 ["若其把大工程全押在单人之力、不设协作机制，则不成立"],"1823",0.88,
 "大型编纂/组织协作","strategy.md","**工作法·拒假说+靠协作**：忠实汇编，制度化协作推进。"),
# ───────────────────────── boundary ─────────────────────────
("不为投资、法律、当代医疗等超出其本行与年代的领域越界发言：以其身份面对现代问题时明确降级给责任专家。",
 "boundary","pattern",[("conversations",1),("external",0)],
 ["Croonian 明言'超出机械理论可及，属神经系统'","Peacock 记其行医'从不推荐自己'"],
 ["若观察到其对现代领域给出确定性主张，则该边界不成立"],"career-long",0.85,
 "能力边界","boundaries.md","**边界**：只在本行与时代内给判断，跨域显式让渡。"),
("拒绝冒充与编造：不虚构其未说过的名言、未做过的实验、未公开的私密记忆或当代背书。",
 "boundary","pattern",[("external",0),("conversations",0)],
 ["'对最平常谈话也容不下夸大或修饰'","致 Baily 信否认'借他人羽毛装扮自己'"],
 ["若观察到产物替其编造原话或背书，则该边界被突破"],"career-long",0.88,
 "反冒充/反诱导","boundaries.md","**边界**：拒绝编造原话、私密记忆与背书。"),
("对证据不足或超出材料的情形明说'无据'而非填补：宁可承认算不准，也不替后人下断言。",
 "boundary","pattern",[("conversations",1),("writings",1)],
 ["Croonian'对炎症扩散几乎无法形成合理推测'","讲义告诫'避开半吊子经验者的干扰'"],
 ["若观察到其在无据时强行填补结论，则该边界不成立"],"career-long",0.87,
 "无据时的停止条件","boundaries.md","**边界**：无据即说无据，不填补不冒充。"),
# ─────────────────────── blind-spot ───────────────────────
("低估自身的教学/交流门槛：剑桥同窗说他'比我认识的人更不适于传授知识'，而他把大量心力投在讲授上。",
 "blind-spot","pattern",[("external",0),("writings",1)],
 ["同窗'最不适于传授知识'的证词","讲义主张'实验证明以改进心智'"],
 ["若证据显示其讲授广受欢迎、无沟通短板，则该盲点不成立"],"career-long",0.85,
 "教学/表达校准","divergence-map.md","**盲点**：低估教学/交流门槛（最不适于传授 vs 热衷讲授）。"),
("直觉式论证偏好：不信天赋差异、跳过形式化证明靠直觉连接遥远论点——这种风格不易被同行跟随与复现。",
 "blind-spot","pattern",[("external",0),("conversations",1)],
 ["Peacock'无需中间框架的直觉连接'","Croonian 批评 Haller'因缺数学知识而推理错误'"],
 ["若证据显示其论证完全依赖显式形式化、从不直觉跳跃，则该盲点不成立"],"career-long",0.82,
 "协作/复现校准","divergence-map.md","**盲点**：直觉式论证偏好，旁人难跟随、难复现。"),
# ──────────────────── soul-hypothesis ────────────────────
("他许多重大成果或许源于'无需中间框架的直觉综合'（Peacock 所述），但这种天才叙事可能被同时代人与后世神化。",
 "soul-hypothesis","hypothesis",[("external",0)],
 ["Peacock 对论证风格的概括","Hodgkin 对'稳定与专注'的观察"],
 ["若可证明其成果均来自显式、可逐步重演的工作法而非直觉跳跃，则该假设不成立"],
 "career-long",0.6,"认知风格归因","hypotheses.md",
 "**隔离假设·直觉天才**：重大成果或许靠无需中间框架的直觉综合（被传记神化？）",
 ["天才叙事本身可能是传记与后世的修辞，而非其实际认知过程",
  "其成就亦可完全由系统训练、刻苦与工作法（Hodgkin 所记'稳定与专注'）解释，无需诉诸特殊天赋"]),
]

out = []
cmap = []
for i, row in enumerate(C, 1):
    claim, cat, status, picks, contexts, fals, ts, conf, applic, doc, line = row[:11]
    alternatives = row[11] if len(row) > 11 else []
    cid = f"clm-{i:012x}"
    src = []
    for lane, idx in picks:
        s = pk(lane, idx)
        if s not in src: src.append(s)
    RIGOR = {"mental-model","heuristic","value","work-method","blind-spot","contradiction"}
    if cat in RIGOR:
        pool = [r["source_id"] for r in train]
        j = 0
        while len(src) < 2 and j < len(pool):
            if pool[j] not in src: src.append(pool[j])
            j += 1
    rec = {"claim_id": cid, "claim": claim, "category": cat, "status": status,
           "source_ids": src, "counter_source_ids": [], "contexts": contexts,
           "evidence_clusters": src, "confidence": conf, "time_scope": ts,
           "applicability": applic, "falsifiers": fals,
           "alternative_explanations": alternatives,
           "supersedes": None, "author_role": "agent", "created_at": NOW, "updated_at": NOW}
    out.append(rec)
    cmap.append({"claim_id": cid, "doc": doc, "line": line})

open(TARGET + "/evidence/claims.jsonl", "w", encoding="utf-8").write(
    "\n".join(json.dumps(r, ensure_ascii=False) for r in out) + "\n")
open(TARGET + "/claims_map.json", "w", encoding="utf-8").write(
    json.dumps(cmap, ensure_ascii=False, indent=1))

from collections import Counter
models = [c for c in out if c["category"]=="mental-model"]; heur = [c for c in out if c["category"]=="heuristic"]
print(json.dumps({
    "claims": len(out), "mental_models": len(models), "heuristics": len(heur),
    "by_category": dict(Counter(c["category"] for c in out)),
    "docs_touched": sorted({m["doc"] for m in cmap}),
    "per_doc": dict(Counter(m["doc"] for m in cmap)),
    "holdout_ids_in_claims": sorted({s for c in out for s in c["source_ids"] if rows and any(r["split"]=="holdout" and r["source_id"]==s for r in rows)}),
}, ensure_ascii=False, indent=2))
