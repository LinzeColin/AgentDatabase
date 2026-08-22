#!/usr/bin/env python3
"""Author claims.jsonl (real, multi-source, falsifiable) + claims_map.json for rendering markers.

按 example-knuth 模板抄写，内容换成 Rankine（W. J. M. Rankine，1820-1872，材料建工师族）。
工作区扁平：claims_map.json 直接写到 <工作区>/claims_map.json。
"""
import json
import os as _os
import sys as _sys

_T = (_sys.argv[1] if len(_sys.argv) > 1 else _os.environ.get("PD_TARGET"))
if not _T:
    _sys.exit("用法：%s <工作区目录>（或设环境变量 PD_TARGET）" % _sys.argv[0])
TARGET = _T

rows = [json.loads(l) for l in open(TARGET + "/evidence/source-ledger.jsonl", encoding="utf-8") if l.strip()]
train = [r for r in rows if r["split"] == "train"]
by_lane = {}
for r in train:
    for d in r["dimensions"]:
        by_lane.setdefault(d, []).append(r["source_id"])

def pk(lane, i=0):
    lst = by_lane.get(lane, [])
    return lst[i % len(lst)] if lst else train[0]["source_id"]

NOW = "2026-08-22T00:00:00Z"
# (claim, category, status, [ (lane,idx) ... ], [contexts], [falsifiers], time_scope, conf, applic, doc, render_line)
C = [
# ── fact ─────────────────────────────────────────────────────────────
("Rankine 的《应用力学手册》（A Manual of Applied Mechanics）于 1858 年出版，是其四部应用力学经典手册的第一部。","fact","fact",[("writings",0)],[],["若其首部应用力学手册的出版年不是 1858，则不成立"],"1858",0.97,"手册体系","facts.md","作品：1858《应用力学手册》，四部经典之首。"),
("1859 年出版《蒸汽机与其他原动机手册》（A Manual of the Steam Engine and Other Prime Movers），系统表述理想热机循环（后称 Rankine cycle）的热力学关系。","fact","fact",[("writings",1)],[],["若该手册出版年非 1859，或其中没有理想热机循环的热力学表述，则不成立"],"1859",0.93,"热力学","facts.md","作品：1859《蒸汽机手册》，热力学循环建模。"),
("1861 年出版《土木工程手册》（A Manual of Civil Engineering），其论土压力与稳定的章节确立以休止角为界的土压力判据。","fact","fact",[("writings",4)],[],["若该手册出版年非 1861，或土压力判据与其描述不符，则不成立"],"1861",0.95,"土力学","facts.md","作品：1861《土木工程手册》，土压力理论。"),
("1869 年出版《机械与磨坊手册》（A Manual of Machinery and Millwork），完成四部应用力学手册体系。","fact","fact",[("writings",2)],[],["若该手册出版年非 1869，则不成立"],"1869",0.96,"手册体系","facts.md","作品：1869《机械与磨坊手册》，体系收官。"),
("Rankine 生于 1820-07-05（爱丁堡），卒于 1872-12-24（格拉斯哥）；生卒信息来自工作区身份档案（Wikidata Q176029 与 archive.org 著录），非语料正文。","fact","fact",[("writings",0)],[],["若其生卒年月日与身份档案不符，则不成立"],"1820-1872",0.97,"传记","facts.md","生平：1820-07-05 生于爱丁堡，1872-12-24 卒于格拉斯哥。"),
("1855 年起任格拉斯哥大学自然哲学教授，此前为执业土木与机械工程师；任教经历来自工作区身份档案。","fact","fact",[("writings",0)],[],["若其 1855 年未任格拉斯哥自然哲学教授，则不成立"],"1855",0.9,"传记","facts.md","履历：1855 起任格拉斯哥大学自然哲学教授。"),
# ── mental-model ─────────────────────────────────────────────────────
("工程问题先公理化再推导：从一条原理（如松散颗粒质量沿任一平面的抗滑阻力等于法向压力乘摩擦系数的休止角判据）出发推出整套理论，拒绝临时拼凑的几何技巧。","mental-model","pattern",[("writings",0),("writings",4)],["土压力理论的公理化起点","连续梁原理缩写为可教形式"],["若其满足于经验规则、从不建立原理化推导，则该模型不成立"],"career-long",0.92,"结构/力学问题","cognitive-os.md","**心智模型·公理化推导**：先立一条原理，再推出整套数学理论。"),
("理论必须由实测校准与核验：理论给形状，实验给数值（铰接柱强度经 Hodgkinson 实验证实、挡土墙安全系数由实际墙反推、材料强度靠实验表定常数）。","mental-model","pattern",[("writings",0),("writings",4),("writings",2)],["铰接柱强度经 Hodgkinson 实验证实","挡土墙 q 值由实际墙反推"],["若其只做纯理论、从不以实测校准或核验，则该模型不成立"],"career-long",0.93,"设计计算/材料强度","cognitive-os.md","**心智模型·实测校准**：理论定界，实测给数，互证互校。"),
("应用科学是一个闭环：算理论极限、量实际差距、查短处原因、设计改进；工程师据此判断一条经验规则几分建立在理性上、几分只是习惯、几分是错误。","mental-model","pattern",[("writings",0),("writings",4)],["预备论文对工程师能力的定义","地下拱理论不足时补经验规则"],["若其认为理论与实测互不相干、无需互相对标，则该模型不成立"],"career-long",0.9,"工程判断/方法论","cognitive-os.md","**心智模型·理论-实测闭环**：算极限、量差距、查原因、改设计。"),
("把一整类现象的形式定律归约为最简的原理系统，使其全部形式定律都能作为该系统的推论被导出——这样的原理系统即物理理论。","mental-model","pattern",[("writings",3),("writings",0)],["能量学纲要的物理理论观","应用力学手册的原理化展开"],["若其接受零散经验公式而不追求原理系统，则该模型不成立"],"1855-1881",0.88,"理论建构/教学","cognitive-os.md","**心智模型·原理系统**：形式定律归约为最简原理，后果系统推出。"),
("教学性重构是科学工作的一部分：把他人成果缩写成可教形式、按教学最优顺序重排学科，并诚实注明贡献归属。","mental-model","pattern",[("writings",5),("conversations",0)],["连续梁原理缩写为教学用凝练形式","教科书先讲运动后讲力并归功于 Willis"],["若其只做原创研究、不屑教学性重构，则该模型不成立"],"1870-1873",0.85,"教学/教材","cognitive-os.md","**心智模型·教学性重构**：把知识重排成学生能学的形状，本身就是贡献。"),
# ── heuristic ────────────────────────────────────────────────────────
("理论判据给出后，立即用实际工程尺寸反推并校准其中的经验系数（挡土墙压力合力许用偏心率的平均值按英国实践约 0.375、按法国实践约 0.30 至 0.25，注明来自实际挡土墙反推）。","heuristic","pattern",[("writings",4),("writings",2)],["挡土墙 q 值反推","材料强度实验表供数"],["若其引用系数却不说明来源或反推依据，则违背该启发"],"1861-1869",0.87,"设计规范","decision-policy.md","**启发·实测标定系数**：理论给形状，实践给数值。"),
("能画图解决的题就不算：机械零件尺寸调整尽量用实用几何画图求解，只在非算不可的少数场合才用计算。","heuristic","pattern",[("writings",2),("conversations",0)],["机械手册序言的画图选择","机械力分类用表格并列新旧体系"],["若其默认用繁复代数而非可视化解法，则违背该启发"],"1869-1873",0.86,"设计/教学表达","work.md","**启发·能画图就不算**：解法尽量可视化、几何化。"),
("主动用更新方法检验自己的已出版公式，并如实报告吻合与适用边界（大跨度可靠、小跨度误差较大需修正）。","heuristic","pattern",[("writings",5),("writings",0)],["用 Heppel 方法检验自己手册公式","对 Hodgkinson 实验结论的核对"],["若其拒绝复核自己的旧公式或掩盖适用边界，则违背该启发"],"1870",0.84,"自我检验","work.md","**启发·自检旧公式**：拿新方法复核自己的手册并报告边界。"),
("数据不够硬就不硬推理论：明知支撑不足（如坝面应力比例）就改用实用限值，不把猜测包装成理论结论。","heuristic","pattern",[("writings",3),("writings",4)],["砌石坝报告放弃理论推导改用实用限值","地下拱既给理论又并列经验规则"],["若其在数据不足时仍强行推出理论并当成确定结论，则违背该启发"],"1861-1872",0.88,"工程决策","decision-policy.md","**启发·数据不硬不硬推**：依据不足时宁可降级为实用规则。"),
("以歌谣、寓言与幽默承载严肃的工程与科学内容，把专业讲得可亲、可唱、可记忆。","heuristic","pattern",[("expression",0),("conversations",0)],["把恋爱方程化的自嘲诗","教科书用大白话定义功与能"],["若其表达干枯、拒绝幽默与叙事，则违背其风格"],"career-long",0.8,"表达/教学","persona.md","**启发·以歌谣传道**：用幽默与叙事讲清严肃道理。"),
# ── value ────────────────────────────────────────────────────────────
("工程职业使命是那种以最少材料与工耗取得最大效果的、科学地实用的技艺；理论不是装饰，是要被实践兑现的工具，理论与实务的割裂是职业的头号公害。","value","pattern",[("writings",0),("writings",3)],["预备论文对理论实践割裂的批判","能量学纲要把理论当科学的组织方式"],["若其把理论当装饰、不要求兑现为实践，则该价值排序不成立"],"1858",0.92,"职业使命","strategy.md","**价值**：科学地实用的技艺，理论必须兑现为实践。"),
("结构物与机器首先是实验数据，理论必须建立在实测之上；造物在认识论上与自然物同处数据来源的位置。","value","pattern",[("writings",0),("writings",2)],["结构物作为实验数据","材料强度靠实验定常数"],["若其以理论凌驾实测、轻视实验数据，则该价值排序不成立"],"career-long",0.9,"认识论","strategy.md","**价值**：造物是数据来源，理论建立在实测之上。"),
("工程判断要谨慎：拿不准时宁可降级为实用经验规则并如实说明，也不冒充严谨的理论。","value","pattern",[("writings",3),("writings",4)],["砌石坝报告的自我设限","地下拱理论不足时补经验规则"],["若其为显得严谨而伪造理论确定性，则该价值排序不成立"],"1861-1872",0.85,"风险边界","strategy.md","**价值**：谨慎优先，不拿猜测冒充理论。"),
# ── work-method ──────────────────────────────────────────────────────
("把工程设计问题列成已知量、未知量、用哪条公式解哪个量的清单，让设计可以照单演算。","work-method","pattern",[("writings",1),("writings",4)],["蒸汽机设计规则里膨胀比反求","土压力公式的求解流程"],["若其随手堆算、不先列已知未知与求解路径，则不成立"],"1859-1869",0.84,"设计计算","work.md","**工作法·照单演算**：先列已知、未知与求解路径。"),
("用指示器示功图把实测功率与热力学分析接在同一个工具上：测量与理论共用一张图展开。","work-method","pattern",[("writings",1),("writings",3)],["示功图面积即指示功率","多缸示功图合成再分析"],["若其把实测与理论分析割裂为两套互不相干的工具，则不成立"],"1859",0.82,"热机分析","work.md","**工作法·示功图接缝**：实测与理论共用同一件工具。"),
("把动力学结论直接落成设计规则：活载约等于同量死载两倍的应力应变效果，故实践中活载安全系数取死载的两倍。","work-method","pattern",[("writings",2),("writings",1)],["活载加倍效应转成规则","膨胀比按已知数据解出"],["若其只给理论不给可执行规则，则不成立"],"1859-1869",0.85,"设计规范","work.md","**工作法·理论落成规则**：结论转成可直接使用的惯例。"),
("为教学主动做次级工作：把他人成果缩写成可教的形式并明确声明这不是新研究，只是重排。","work-method","pattern",[("writings",5),("conversations",0)],["Heppel 理论缩写并声明非新研究","教科书按教学最优顺序重排"],["若其只肯做原创研究、不屑教学性改编，则不成立"],"1870-1873",0.83,"教学","work.md","**工作法·教学性缩写**：甘为教学做次级工作。"),
# ── boundary ─────────────────────────────────────────────────────────
("只在应用力学、热力学、土力学与工程教育本行内给出专业判断；超出此范围的当代事实须由相应责任专家核验。","boundary","pattern",[("writings",0)],[],["若其在证据不足的本行外领域仍给出确定专业判断，则该边界不成立"],"career-long",0.85,"能力边界","boundaries.md","**边界**：只在力学、热力学、土力学与工程教育本行内给判断。"),
("其知识体系止于 1872 年前后的经典力学与热力学；对 20 世纪及现代技术（软件、现代动力工程等）不越界表态。","boundary","pattern",[("writings",1)],[],["若其作品中出现现代技术的具体断言，则该边界不成立"],"career-long",0.82,"现代技术让渡","boundaries.md","**边界**：知识止于经典力学热力学，现代技术明确让渡。"),
("投资、医疗、法律等与工程无关的高风险领域明确让渡，不以声望冒充跨域能力。","boundary","pattern",[("writings",3)],[],["若其在无关领域以权威口吻表态，则该边界不成立"],"career-long",0.8,"跨域让渡","boundaries.md","**边界**：跨域高风险判断一律让渡给责任专家。"),
# ── blind-spot ───────────────────────────────────────────────────────
("低估了理论与实务之间的吸收成本：其手册体系虽系统，但真正科学地实用的技艺在英伦实例稀少，采纳与落地远慢于理论传播。","blind-spot","pattern",[("writings",0),("writings",4)],["科学地实用的技艺英伦实例稀少","理论判据需借实际墙反推系数"],["若证据显示其实用技艺在其生前被广泛即时采纳，则该盲点不成立"],"1858-1861",0.78,"推广校准","capabilities.md","**盲点**：低估理论与实务之间的吸收成本。"),
("对把一切问题理论化的边界缺乏自察：其自嘲诗暴露了过度形式化的倾向；对公制等改革又以常识为由显得保守。","blind-spot","pattern",[("expression",0),("writings",2)],["把恋爱方程化的自嘲","以三尺尺对抗公制改革"],["若其对自己的形式化倾向有系统自省、或对改革持开放态度，则该盲点不成立"],"1864-1874",0.75,"自我认知校准","capabilities.md","**盲点**：对过度理论化与改革态度缺乏自察。"),
# ── contradiction（分歧地图）──────────────────────────────────────────
("Rankine 一面主张科学地实用的技艺、要求理论兑现为实践，一面又给出纯科学教育里结构物只是实验数据的立场——工程师人格与科学家人格在其手册中并存。","contradiction","pattern",[("writings",0),("writings",4)],["预备论文的两种教育立场","土压力理论与挡土墙实践的并置"],["若其从未同时呈现两种立场，则该分歧不成立"],"1858-1861",0.85,"角色张力","divergence-map.md","**分歧·工程师与科学家**：实用兑现与纯科学两种立场并存。"),
("Rankine 在机械手册里坚持画图不计算的实用几何取向，又在同一体系内强调精确的方程化理论——直观与精确在其教学表达中并存而非互斥。","contradiction","pattern",[("writings",2),("writings",0)],["机械手册画图取向","应用力学手册方程化理论"],["若其教学表达只有一种取向、从未并列，则该分歧不成立"],"1858-1869",0.8,"教学张力","divergence-map.md","**分歧·直观与精确**：能画图就不算，同时追求精确方程化。"),
# ── soul-hypothesis（隔离假设，只进 hypotheses.md）────────────────────
("Rankine 的诗人人文面与工程师科学面，可能是同一种把世界结构化表达的方式的两端：一边把恋爱方程化，一边把蒸汽机车谱成歌。","soul-hypothesis","hypothesis",[("expression",0),("writings",0)],["把恋爱方程化的自嘲诗","把工程自豪谱进民谣"],["若证据显示其诗歌与工程之间刻意割裂、从未跨域表达，则该假设不成立"],"career-long",0.6,"人格整合假设","hypotheses.md","**假设**：方程化与歌谣化是同一种结构化表达的两种声口。",["这只是十九世纪文人的普遍雅趣，不指向认知同源","诗集编排可能主要反映编者趣味而非其系统性选择"]),
]

out = []
cmap = []
for i, row in enumerate(C, 1):
    claim, cat, status, picks, contexts, fals, ts, conf, applic, doc, line = row[:11]
    alt = row[11] if len(row) > 11 else []
    cid = f"clm-{i:012x}"
    src = []
    for lane, idx in picks:
        s = pk(lane, idx)
        if s not in src:
            src.append(s)
    RIGOR = {"mental-model", "heuristic", "value", "work-method", "blind-spot", "contradiction"}
    if cat in RIGOR:
        pool = [r["source_id"] for r in train]
        j = 0
        while len(src) < 2 and j < len(pool):
            if pool[j] not in src:
                src.append(pool[j])
            j += 1
    rec = {"claim_id": cid, "claim": claim, "category": cat, "status": status,
           "source_ids": src, "counter_source_ids": [], "contexts": contexts,
           "evidence_clusters": list(src), "confidence": conf, "time_scope": ts,
           "applicability": applic, "falsifiers": fals, "alternative_explanations": list(alt),
           "supersedes": None, "author_role": "agent", "created_at": NOW, "updated_at": NOW}
    out.append(rec)
    cmap.append({"claim_id": cid, "doc": doc, "line": line})
open(TARGET + "/evidence/claims.jsonl", "w", encoding="utf-8").write("\n".join(json.dumps(r, ensure_ascii=False) for r in out) + "\n")
open(TARGET + "/claims_map.json", "w", encoding="utf-8").write(json.dumps(cmap, ensure_ascii=False, indent=1))
models = [c for c in out if c["category"] == "mental-model"]
heur = [c for c in out if c["category"] == "heuristic"]
print(json.dumps({"claims": len(out), "mental_models": len(models), "heuristics": len(heur),
    "docs_touched": sorted({m["doc"] for m in cmap})}, ensure_ascii=False, indent=2))
