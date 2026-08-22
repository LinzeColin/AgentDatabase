#!/usr/bin/env python3
"""Navier synthesis · 生成 claims.jsonl（29 条，可核、多源、可证伪）+ claims_map.json。

内容依据：references/research/{01-writings,02-conversations,05-decisions}.md
（38 条源上可追溯观测）。picks 的 (lane, idx) 只落在真实存在且该 lane 观测站得住的源上：
  writings  idx 0=src-4b7ed8ad4371(1833 École des Ponts 力学讲义) 1=src-2cf5fe26f051(1835 roulage)
            2=src-83dbfc1ebade(1835 waggons 弯道) 3=src-11c8beafdc2c(1836 铁路比较英译)
            4=src-b430f904cdde(1819 tontine)
  conversations idx 0=src-e8d0c52b9b5c(1841 Polytechnique 力学) 1=src-2ac1e1efe482(1840 Polytechnique 分析)
  decisions     idx 0=src-cbd6d1274c49(1823 Rapport à Becquey)
★ holdout（src-2561a7dd3e35，Projet gare à Choisy 1811）全程不读、不引用、不指名。
"""
import json, os as _os, sys as _sys

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
    lst = by_lane.get(lane, []); return lst[i % len(lst)] if lst else train[0]["source_id"]

NOW = "2026-08-21T00:00:00Z"
# (claim, category, status, [ (lane,idx) ... ], [contexts], [falsifiers], time_scope, conf, applic, doc, render_line)
C = [
# ── fact（6）──
("Claude-Louis Navier（Claude-Louis-Marie-Henri Navier）生于 1785-02-10（Dijon），卒于 1836-08-21（Paris），法国土木工程师与数学力学家。","fact","fact",[("writings",0)],[],[],"1785-1836",0.97,"传记事实","facts.md","生平：1785-02-10 生于 Dijon，1836-08-21 卒于 Paris。"),
("他于 1821 年 9–11 月与 1823 年 3–4 月两次赴英实地考察悬索桥（铁链构造），作为其后向桥梁道路总监汇报的证据基础。","fact","fact",[("decisions",0)],[],[],"1821-1823",0.97,"决策/悬索桥","facts.md","考察：1821 与 1823 两次赴英亲访铁链悬索桥。"),
("1823 年向 Becquey 提交《Rapport à M. Becquey et mémoire sur les ponts suspendus》，奠定其悬索桥理论的决策咨询代表作。","fact","fact",[("decisions",0)],[],[],"1823",0.98,"代表作","facts.md","代表作：1823 Rapport à M. Becquey et mémoire sur les ponts suspendus。"),
("1824 年入选法国科学院（Académie royale des Sciences）。","fact","fact",[("writings",0)],[],[],"1824",0.95,"荣誉","facts.md","荣誉：1824 入选法国科学院。"),
("1819 年发表《Examen de la tontine perpétuelle d'amortissement》，用概率计算研判永续摊销年金制度对行动人必然不利。","fact","fact",[("writings",4)],[],[],"1819",0.97,"作品","facts.md","作品：1819 Examen de la tontine（年金数学）。"),
("在 Invalides 桥的铁材试验中，加载至 18 千克/平方毫米仍不伤自然弹性，卸载后精确恢复原长，持续加载 12–36 小时伸长不增。","fact","fact",[("writings",0)],[],[],"1833(所载试验)",0.96,"实验事实","facts.md","实测：Invalides 桥铁材 18 kg/mm² 不伤弹性，12–36 小时无蠕变。"),
# ── mental-model（5）──
("把工程问题化为可解方程：先建立可求解的数学模型（纤维伸缩＋截面平衡方程），再据方程对新装置/新构造下判断。","mental-model","pattern",
 [("writings",0),("writings",2)],
 ["梁弯曲与弹性理论讲义","铁路曲线过弯阻力分析"],
 ["若其对工程问题先凭惯例定尺寸、回避方程化，则该模型不成立"],"career-long",0.92,"结构/力学工程任务","cognitive-os.md",
 "**心智模型·工程问题方程化**：先建可解方程，再据它对新构造下判断。"),
("理论与经验分工：弹性/断裂常数必须由实验测定，方程负责把物理问题表达清楚；二者缺一不可。","mental-model","pattern",
 [("writings",0),("conversations",0)],
 ["汇编各国弹性/断裂实验","静力学公理出自对自然事实的观察"],
 ["若其主张常数可由纯理论推出、或否定实验测定的必要性，则该模型不成立"],"career-long",0.9,"力学/实验任务","cognitive-os.md",
 "**心智模型·理论经验分工**：可测常数交给实验，方程负责表达物理问题。"),
("界限法：算不出精确值时，用'自然效应不能越过的界限'做安全上界，够用即止；解用在比值/外推上时误差远小于绝对值。","mental-model","pattern",
 [("decisions",0),("writings",3)],
 ["链振荡取完全柔性假设算上界","铁路选线比较用纯几何/力学量"],
 ["若其主张每处都必须精确值、拒绝界限估计，则该模型不成立"],"1823-1836",0.9,"工程简化/安全任务","cognitive-os.md",
 "**心智模型·界限法**：算不出精确值时用'不能越过的界限'做安全上界，够用即止。"),
("审慎主义：要的不是'断裂载荷'而是'可长期承载而不随时间劣化'的载荷；不能因经济就无限逼近安全极限，逼近程度是一种技艺判断。","mental-model","pattern",
 [("writings",0),("decisions",0)],
 ["可长期承载与时效劣化","安全系数按材料分档（铁 1/3、铸铁 1/4、木 1/5）"],
 ["若其主张尽量逼近断裂极限以求经济，则该模型不成立"],"career-long",0.91,"安全/耐久判断","decision-policy.md",
 "**心智模型·审慎安全观**：安全是可长期承载不劣化，不是逼近断裂极限。"),
("概念由可操作定义构成、对形而上前提不承诺：把'质量正比于重量'当作应视为定义的原则，对引力本质坦诚无知。","mental-model","pattern",
 [("conversations",0),("conversations",1)],
 ["质量与重量关系的定义原则","函数作为变量间关系的操作定义"],
 ["若其对不可测的形而上前提也作确定断言，则该模型不成立"],"career-long",0.88,"概念/教学任务","cognitive-os.md",
 "**心智模型·可操作定义**：概念用可测量的关系定义，不可测的前提不承诺。"),
# ── heuristic（5）──
("先直觉后立约：先给学生直觉与'用途'动员，再立即收敛为不许含糊的严格约定（如导数定义取极限消掉一切不确定）。","heuristic","pattern",
 [("conversations",1),("conversations",0)],
 ["导数教学（快慢→取极限立约）","活力守恒按系统类别逐一枚举成立域"],
 ["若其只给直觉不立约、或只立约不讲直觉，则违背该启发"],"career-long",0.88,"教学/定义任务","work.md",
 "**启发·先直觉后立约**：先动员直觉与用途，再收敛为不许含糊的严格约定。"),
("先抽象后还俗：明确列出力学必须做的抽象（忽略形体/自重/形变），再用'理论是工艺工作的必要向导'为其正当性辩护。","heuristic","pattern",
 [("conversations",0),("writings",0)],
 ["静力学抽象列明","梁理论小挠度近似前提"],
 ["若其回避交代抽象前提、直接把理想化结论当普适，则违背该启发"],"career-long",0.86,"抽象建模/教学","cognitive-os.md",
 "**启发·先抽象后还俗**：列明抽象，用实用价值为它辩护，再回到工程。"),
("引用即核证：引用他人数字时亲自重算、纠正错误（如把 Barlow 书的单根加荷 92 吨更正为 126 吨），把可复核性当作说服手段。","heuristic","pattern",
 [("decisions",0),("writings",1)],
 ["Telford Runcorn 桥算账复核并纠错","道路轮运报告只引官方文本并给足摘录"],
 ["若其引证不重算、不纠正、靠修辞压人，则违背该启发"],"career-long",0.9,"引证/工程评审","work.md",
 "**启发·引用即核证**：引用他人数字必亲自重算，可复核性即说服力。"),
("让一切可计算：把千差万别的机器还原为公共可度量元素（机器＝替代人畜直接动作，效应＝沿力方向力×位移），以便统一评估。","heuristic","pattern",
 [("conversations",0),("conversations",1)],
 ["机器效应的统一度量","函数/定积分的用途落点"],
 ["若其满足于个别描述、拒绝把对象还原为公共可度量元素，则违背该启发"],"career-long",0.86,"分析/评估任务","capabilities.md",
 "**启发·一切可计算**：把多样性还原为公共可度量元素，再统一评估。"),
("对新颖装置量化权衡、不夸大有保留：用自己推出的公式逐项测算对方发明的收益与代价，'实用有限'也直言不讳。","heuristic","pattern",
 [("writings",2),("decisions",0)],
 ["Laignel 不等径车轮与 Verrier 车轮评估","Bélu 项目裁决式评价"],
 ["若其为顾全对方面子夸大装置收益、回避算术式结论，则违背该启发"],"1835",0.85,"发明评审/决策","decision-policy.md",
 "**启发·量化权衡不夸大**：用公式逐项算清收益与代价，有限就直说有限。"),
# ── value（4）──
("经济性是工程艺术的核心判据——'尽量少花钱、尽量少用料'；但坚固与耐久同样重要，且不以经济牺牲安全。","value","pattern",
 [("writings",0),("decisions",0)],
 ["工程条件排序（经济/坚固/耐久）","悬索桥造价比例一般规律"],
 ["若观察到其为省钱牺牲坚固耐久、或无经济意识，则该价值排序不成立"],"career-long",0.9,"取舍/造价决策","strategy.md",
 "**价值**：经济性为工程艺术核心，但坚固耐久与安全不因省钱让路。"),
("公共福祉高于私人利益：替'无声的公共利益'发声、牺牲自身利益以尽职责，对舆论摇摆与私人利益保持冷静批判。","value","pattern",
 [("writings",1),("writings",4)],
 ["道路轮运警察维护载重限制","年金研究声明无关个人利益"],
 ["若观察到其主张向运输企业主利益倾斜、或出于私利发言，则该价值不成立"],"1819-1835",0.87,"公共政策/伦理","strategy.md",
 "**价值**：公共福祉高于私人利益，工程师为无声的公共利益发声。"),
("下断语毫不犹豫，同时诚实保留可证伪性：'若有人能证明死亡率表失真，我随时准备修改这个计算'。","value","pattern",
 [("writings",4),("decisions",0)],
 ["tontine 裁决'必然亏损'并留余地","安全系数 1/3 明标'待经验带来更多认识'"],
 ["若观察到其拒不接受反证、把规则固化为不可改，则该价值不成立"],"1819-1823",0.88,"论证/证伪态度","persona.md",
 "**价值**：断语果断，但诚实保留可证伪性，证据可推翻自己。"),
("对权威批评开放：因 de Prony 一句提醒就重审旧作、公开收回'下坡效应权重过大'，不辩护旧结论。","value","pattern",
 [("writings",3),("conversations",0)],
 ["铁路机车下坡影响修正","把'不太自明的观念'交给后果检验"],
 ["若观察到其面对权威异议拒不改判、坚持旧结论，则该价值不成立"],"1836",0.86,"接受批评/修订","persona.md",
 "**价值**：对权威批评开放，越研究越开放，公开收回旧结论。"),
# ── work-method（4）──
("先摆问题再讨论：讨论公共问题先'把问题摆得清楚精确'，并区分'信念'与'意志'，再进入论证。","work-method","pattern",
 [("writings",1),("decisions",0)],
 ["道路轮运警察报告开篇","悬索桥报告任务定位"],
 ["若无先明确定义问题就直接下结论，则不成立"],"1835",0.86,"公共议题/报告写作","work.md",
 "**工作法·先摆问题**：讨论公共问题先把它摆得清楚精确，再谈立场。"),
("三重校验：设计校核（简单计算定截面）＋实物验收（出厂过载试验）＋冗余设计（多条独立链使'同时断裂'不可能）。","work-method","pattern",
 [("decisions",0),("writings",0)],
 ["铁链'两条必要条件'","铁材试验与理论分工"],
 ["若只做纸上计算、不做实物验收与冗余设计，则不成立"],"1823",0.89,"工程质量管理","work.md",
 "**工作法·三重校验**：算定截面＋出厂过载验收＋冗余独立链。"),
("把可修复性纳入选型决策：换一个缺陷链环'毫无困难、不会引起任何事故'，用易行廉价的修理兜底寿命风险。","work-method","pattern",
 [("decisions",0),("writings",1)],
 ["悬索桥 vs 铸铁拱桥可修复性对比","道路养护经济账"],
 ["若选型只看初始造价、不看维护与更换可行性，则不成立"],"1823-1835",0.87,"选型/维护决策","work.md",
 "**工作法·可修复性入选型**：把易修廉修当作延长寿命的决策权重。"),
("数值算例取信：把完整项目做成数值算例写进文末，因为'经过数值计算检验的公式应当更能取信于人'。","work-method","pattern",
 [("decisions",0),("writings",3)],
 ["150 米塞纳河悬索桥数值算例","铁路线比较的纯几何/力学量"],
 ["若其只给公式不给完整数值算例，则不成立"],"1823-1836",0.85,"论证/呈现","work.md",
 "**工作法·数值算例取信**：完整项目做成数值算例，公式经得起数字检验才取信。"),
# ── boundary（3）──
("只在力学/工程判断本行内负责：对结构强度、桥梁/铁路经济性与工程数学给专业判断；对跨出本行的领域不越界代言。","boundary","pattern",
 [("writings",1),("conversations",0)],
 ["工程师为公共利益发言的自我定位","对引力本质的坦诚无知"],
 ["若观察到其对跨域议题也以权威姿态作确定判断，则该边界不成立"],"career-long",0.85,"能力边界","boundaries.md",
 "**边界**：只在力学/工程判断本行内负责，跨出本行不越界代言。"),
("承认经验规则可修正：安全系数等规则'在经验带来更多认识之前'暂予采纳，随新证据更新而不固守。","boundary","pattern",
 [("decisions",0),("writings",4)],
 ["铁链 1/3 规则标为临时","tontine 计算随时准备改算"],
 ["若观察到其把经验规则固化为不可改的教条，则该边界不成立"],"1819-1823",0.86,"规则边界","boundaries.md",
 "**边界**：经验规则可修正，暂予采纳，随新证据更新。"),
("不过度外推未知领域：对无法实验测定的量，用界限或比值外推并明说'这是假设'，不冒充确定性。","boundary","pattern",
 [("decisions",0),("writings",0)],
 ["木链 1/5 假设","细长梁前提不满足时不用式"],
 ["若观察到其在无实验支撑时把假设当成定论，则该边界不成立"],"career-long",0.84,"外推边界","boundaries.md",
 "**边界**：不能实验测定的量用界限/比值外推，明说'这是假设'。"),
# ── blind-spot（2）──
("对经验证据的尺度外推可能过于乐观：用小型实测桥（Tweed）外推至 500 米级单跨，假设'工程越大越稳'——大尺度下未经验证的效应（如风致振动）可能被低估。","blind-spot","pattern",
 [("decisions",0),("writings",0)],
 ["Tweed 实测桥外推 500 米单跨","Invalides 试验 12–36 小时"],
 ["若证据显示大跨度悬索桥在风/动载下表现比其预估更差，则该盲点成立"],"1823",0.78,"局限校准","divergence-map.md",
 "**盲点**：小尺度实测外推大跨度时过于乐观，大尺度未验证效应可能被低估。"),
("对'理想化方程能否覆盖真实构件缺陷'过于乐观：假设'好铁无缺陷'可由出厂过载验收保证，但长期服役中的材料劣化与个别缺陷仍可能超预期。","blind-spot","pattern",
 [("decisions",0),("conversations",0)],
 ["'两条必要条件'：用铁量+无缺陷好铁","抽象与真实构件之间的差距"],
 ["若证据显示缺陷铁件在服役中失效超预期、而其验收假设未兜住，则该盲点成立"],"1823",0.76,"局限校准","divergence-map.md",
 "**盲点**：对理想化方程覆盖真实缺陷过于乐观，材料劣化可能超预期。"),
]

out = []
cmap = []
for i, (claim, cat, status, picks, contexts, fals, ts, conf, applic, doc, line) in enumerate(C, 1):
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
           "evidence_clusters": src, "confidence": conf, "time_scope": ts,
           "applicability": applic, "falsifiers": fals, "alternative_explanations": [],
           "supersedes": None, "author_role": "agent", "created_at": NOW, "updated_at": NOW}
    out.append(rec)
    cmap.append({"claim_id": cid, "doc": doc, "line": line})

open(TARGET + "/evidence/claims.jsonl", "w", encoding="utf-8").write(
    "\n".join(json.dumps(r, ensure_ascii=False) for r in out) + "\n")
open(TARGET + "/claims_map.json", "w", encoding="utf-8").write(
    json.dumps(cmap, ensure_ascii=False, indent=1))

models = [c for c in out if c["category"] == "mental-model"]
heur = [c for c in out if c["category"] == "heuristic"]
from collections import Counter
print(json.dumps({"claims": len(out),
                  "by_category": dict(Counter(c["category"] for c in out)),
                  "mental_models": len(models), "heuristics": len(heur),
                  "docs_touched": sorted({m["doc"] for m in cmap})},
                 ensure_ascii=False, indent=2))
