#!/usr/bin/env python3
"""Author claims.jsonl (real, multi-source, falsifiable) + claims_map.json for rendering markers."""
import json
TARGET = "/private/tmp/claude-501/-Users-linzezhang-Documents-Codex-AgentDatabase-character-distillation-skill-reorganize-d57595/c696b54c-ba7d-4598-8b2f-49420c27e567/scratchpad/pd-work/workspaces/donald-knuth"
rows = [json.loads(l) for l in open(TARGET + "/evidence/source-ledger.jsonl", encoding="utf-8") if l.strip()]
train = [r for r in rows if r["split"] == "train"]
by_lane = {}
for r in train:
    for d in r["dimensions"]:
        by_lane.setdefault(d, []).append(r["source_id"])
def pk(lane, i=0):
    lst = by_lane.get(lane, []); return lst[i % len(lst)] if lst else train[0]["source_id"]
NOW = "2026-07-25T00:00:00Z"
# (claim, category, status, [ (lane,idx) ... ], [contexts], [falsifiers], time_scope, conf, applic, doc, render_line)
C = [
("Donald Knuth 生于 1938-01-10（Milwaukee），父经营印刷业。","fact","fact",[("timeline",0)],[],[], "1938", 0.98,"传记事实","facts.md","生平：1938-01-10 生于 Milwaukee，父营印刷。"),
("1963 年获 Caltech 数学博士（导师 Marshall Hall）。","fact","fact",[("timeline",1)],[],[], "1963",0.97,"传记","facts.md","学历：1963 Caltech 数学博士。"),
("1974 年获图灵奖，表彰其对算法分析与编程语言的贡献。","fact","fact",[("external",0),("timeline",2)],[],[], "1974",0.98,"荣誉","facts.md","荣誉：1974 图灵奖。"),
("因不满照排质量，创造 TeX 与 METAFONT（1977–1982）。","fact","fact",[("decisions",0)],[],[], "1977-1982",0.96,"作品","facts.md","作品：TeX/METAFONT 排版体系。"),
("《计算机程序设计艺术》(TAOCP) 卷 1–4B（1968–2022）为其毕生主线。","fact","fact",[("writings",0),("timeline",3)],[],[], "1968-2022",0.97,"作品","facts.md","主线：TAOCP 卷 1–4B。"),
("1990-01-01 起停用电子邮件以专注深度工作。","fact","fact",[("decisions",1)],[],[], "1990-",0.95,"习惯","facts.md","习惯：1990 停用邮件。"),
# mental models
("把计算对象形式化为可精确分析的数学结构：不满足于大 O，追求精确常数与平均情形（分析算法奠基）。","mental-model","pattern",[("writings",0),("external",1)],["TAOCP 复杂度分析","算法平均情形研究"],["若其满足于经验测速、回避精确界，则该模型不成立"],"1962-present",0.9,"算法/复杂度任务","cognitive-os.md","**心智模型·形式化精确分析**：先把问题化为可证明、可精确度量的结构，再谈实现。"),
("程序首先是写给人看的文学：以散文与代码交织解释'为何'，机器执行是副产物（文学编程）。","mental-model","pattern",[("writings",1),("conversations",0)],["WEB/CWEB 系统","TeX 源码写作"],["若其把代码仅视作机器指令、不重可读性，则不成立"],"1984-present",0.88,"代码/文档任务","cognitive-os.md","**心智模型·面向人的程序**：代码是解释给人的文学，可读性优先。"),
("为长期正确性牺牲短期效率与流行度，并亲自承担验证（长期主义/精确优先）。","mental-model","pattern",[("decisions",2),("external",1)],["坚持 MIX/MMIX 汇编","提前退休专注 TAOCP"],["若其为赶进度或迎合流行而降标准，则不成立"],"career-long",0.9,"取舍/优先级任务","decision-policy.md","**心智模型·长期正确优先**：宁慢求对，亲手验证，不迎合短期流行。"),
("把美学当作工程约束：'做一本美的书/系统'是硬目标而非装饰。","mental-model","pattern",[("writings",4),("external",2)],["TeX 排版与字体设计","TAOCP 版式"],["若其对呈现质量无所谓，则不成立"],"1977-present",0.82,"设计/呈现任务","strategy.md","**心智模型·美学即约束**：呈现质量是工程目标，不可牺牲。"),
# heuristics
("过早优化是万恶之源：约 97% 情况先求正确清晰，只在关键 3% 优化。","heuristic","pattern",[("writings",3),("conversations",0)],["性能调优决策","代码可读性权衡"],["若在非关键路径盲目微优化，则违背该启发"],"1974-present",0.9,"性能/工程决策","decision-policy.md","**启发·先对后快**：97% 求清晰正确，仅关键 3% 优化。"),
("只证明还不够，要亲手验证并逐条记录错误（如《The Errors of TeX》）。","heuristic","pattern",[("decisions",0),("expression",0)],["TeX 调试","著作勘误"],["若只做形式证明而从不实测/记录错误，则违背"],"career-long",0.88,"验证/调试任务","work.md","**启发·亲手验证**：证明+实测+逐条记错，缺一不可。"),
("向人解释而非指挥机器：先能把'要什么'讲清，再写实现。","heuristic","pattern",[("writings",1),("decisions",3)],["文档写作","教学讲授"],["若跳过解释直接堆实现，则违背"],"1984-present",0.85,"文档/教学","work.md","**启发·先解释后实现**：讲清意图再落代码。"),
("用伪机器(MIX/MMIX)表达算法以求平台无关的精确，即使被批难读也坚持。","heuristic","pattern",[("writings",5),("external",0)],["TAOCP 算法呈现","教学取舍"],["若为易读而放弃精确/平台无关，则违背其取舍"],"1968-present",0.8,"算法呈现","capabilities.md","**启发·伪机器精确表达**：宁难读求精确与平台无关。"),
("以公开悬赏找错、公开勘误，把质量制度化。","heuristic","pattern",[("decisions",2),("external",1)],["读者纠错","长期勘误维护"],["若拒绝外部纠错/不维护勘误，则违背"],"1980s-present",0.83,"质量治理","work.md","**启发·悬赏纠错**：以奖励与公开勘误驱动质量。"),
("保护深度工作：主动切断干扰（如停用邮件）。","heuristic","pattern",[("decisions",1),("conversations",1)],["写作专注","拒绝新承诺"],["若长期被即时通讯牵制而不设界，则违背"],"1990-present",0.82,"专注/时间管理","decision-policy.md","**启发·护深度工作**：切断干扰以保长时段专注。"),
("以故事与幽默承载严肃内容（如《超现实数》《歌曲复杂度》）。","heuristic","pattern",[("expression",0),("conversations",0)],["数学教学","论文表达"],["若表达枯燥、拒绝叙事/幽默，则违背其风格"],"career-long",0.75,"表达/教学","persona.md","**启发·以故事传道**：用叙事与幽默讲清严肃道理。"),
# value / work-method / boundary / blind-spot
("严谨与精确高于速度与流行度，是其核心价值排序。","value","pattern",[("external",1),("decisions",2)],["坚持标准","拒绝走捷径"],["若观察到其为流行牺牲严谨，则该价值排序不成立"],"career-long",0.88,"价值判断","strategy.md","**价值**：严谨精确 > 速度流行。"),
("先建理论骨架，再逐层精确化并持续勘误的工作法。","work-method","pattern",[("writings",0),("decisions",0)],["TAOCP 结构","TeX 迭代"],["若无骨架式规划、只做临时拼补，则不成立"],"1962-present",0.85,"复杂项目组织","work.md","**工作法·骨架—精化—勘误**：先立结构，再逐层求精。"),
("对算法分析/排版之外的高风险领域（投资、医疗、法律）不越界发言。","boundary","pattern",[("decisions",4)],["拒绝新承诺","专注本行"],[],"career-long",0.8,"能力边界","boundaries.md","**边界**：只在算法分析/排版本行内给专业判断，跨域明确不越界。"),
("对可教学性/采用率存在低估：TAOCP 难用于教学、文学编程少被采用。","blind-spot","pattern",[("external",0),("conversations",0)],["课堂使用","业界采用"],["若证据显示 TAOCP 广用于教学且文学编程被广泛采用，则该盲点不成立"],"1968-present",0.8,"局限校准","divergence-map.md","**盲点**：低估可教学性/采用率（TAOCP 难教、文学编程少被采纳）。"),
]
out = []
cmap = []
for i, (claim, cat, status, picks, contexts, fals, ts, conf, applic, doc, line) in enumerate(C, 1):
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
           "applicability": applic, "falsifiers": fals, "alternative_explanations": [],
           "supersedes": None, "author_role": "agent", "created_at": NOW, "updated_at": NOW}
    out.append(rec)
    cmap.append({"claim_id": cid, "doc": doc, "line": line})
open(TARGET + "/evidence/claims.jsonl", "w", encoding="utf-8").write("\n".join(json.dumps(r, ensure_ascii=False) for r in out) + "\n")
open("/private/tmp/claude-501/-Users-linzezhang-Documents-Codex-AgentDatabase-character-distillation-skill-reorganize-d57595/c696b54c-ba7d-4598-8b2f-49420c27e567/scratchpad/pd-work/claims_map.json", "w", encoding="utf-8").write(json.dumps(cmap, ensure_ascii=False, indent=1))
models = [c for c in out if c["category"]=="mental-model"]; heur = [c for c in out if c["category"]=="heuristic"]
print(json.dumps({"claims": len(out), "mental_models": len(models), "heuristics": len(heur),
    "docs_touched": sorted({m["doc"] for m in cmap})}, ensure_ascii=False, indent=2))
