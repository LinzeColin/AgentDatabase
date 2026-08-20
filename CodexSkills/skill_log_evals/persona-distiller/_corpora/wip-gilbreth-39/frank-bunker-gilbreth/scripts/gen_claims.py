#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""【脚手架】29–31 条断言的生成器。每人复制一份，只改 S（源 ID 表）与 C（断言元组表）。

## 生成时断言（全部来自实战教训，不要删）

1. **引号内不得含省略号**（RUNBOOK 第二十九种）。
   需要跳内容就结束引号、用自己的话过渡、再开新引号。
2. **category 必须在 ledger.py 的白名单内**。
3. **每条 ≥2 源、≥2 情境**，source_ids 不得重复。
4. **status 是「命题的种类」**：`fact | pattern | hypothesis`。
5. **门数的是「category ∧ status == 'pattern'」**：mental-model ≥6、heuristic ≥8。
6. **soul-hypothesis 只许出现在 `hypotheses.md`。**

## 写断言时的五条纪律

1. **不做没数过的枚举**：计数一律给分子/分母，不写「只有」「多数」。
2. **不替他补理由**：只给了做法而没给理由的，如实写「他没给理由」。
3. **归属分层**：他转述他人的材料，里面的主张**不属于他**。
4. **自述 ≠ 事实**：语料若无第三方材料，他讲的经历一律标「他自述」，status 不得给 fact。
5. **过度断言必查**：凡带「从不 / 唯一 / 没有一句」的，逐条去语料找反例。

本份语料要点（Gilbreth 专用）：
- 「therbligs」一词在 PROCESS（1921）里以 OCR 断词 `ther- bligs` 出现，
  与「one best way」的记录/持续改进绑定；数量与逆序拼写是外部常识，语料未给，
  故断言只写「细分单元名为 therbligs」，不写「18 个」。
- 疲劳分类前后不一致：MOTION（1911）三因 vs FATIGUE（1916）两分类——写成 contradiction。
- Primer 引用的泰勒定义是**泰勒的主张**，Gilbreth 是转述者/普及者——归 lineage 并注明归属。
- Field System 的无账簿会计由第三方 John P. Slack 记述——注明「第三方记述」。
"""
import collections, json, pathlib, sys
from datetime import datetime, timezone

NOW = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
OUT = pathlib.Path(__file__).resolve().parent.parent / "evidence/claims.jsonl"  # ← 改

CATEGORIES = ("fact", "mental-model", "heuristic", "value", "epistemic", "expression",
              "lineage", "blind-spot", "contradiction", "work-method", "boundary",
              "soul-hypothesis")            # 抄自 scripts/ledger.py，不要凭记忆写

S = {
    "MOTION": "src-d229be6683e5",   # Motion Study: A Method for Increasing the Efficiency of the Workman (1911)
    "FATIGUE": "src-39dfef403efb",  # Fatigue Study: The Elimination of Humanity's Greatest Unnecessary Waste (1916, 与 Lillian 合著)
    "PRIMER": "src-51659308714b",   # Primer of Scientific Management (1912)
    "BRICK": "src-a105f1d59a92",    # Bricklaying System (1909)
    "FIELD": "src-512232eb4755",    # Field System (1908, 建筑现场管理系统)
    "APPLIED": "src-b84ad47069dd",  # Applied Motion Study (1917, 合著)
    "PROCESS": "src-4613a3b8b48f",  # Process Charts (1921, ASME 论文, 合著)
    "MEASURE": "src-2019536f67f7",  # Measurement of the Human Factor in Industry (1917, 合著)
    "PILES": "src-84fb8b78b859",    # The Making and Driving of Corrugated Concrete Piles (1906, 工程报告)
    "PSYCH": "src-8ae7cf6e0575",    # The Psychology of Management (1914, Lillian 独著)
    "HANDI": "src-6d9c3e11ab6d",    # Motion Study for the Handicapped (1920, **HOLDOUT — 严禁作断言来源**)
}

# (category, 适用标签, 断言正文, [源别名], [情境≥2], [证伪条件], status, confidence, 时间范围)
#   soul-hypothesis 多给一项：末尾追加 [替代解释…]（门强制要求，见文件头第 6 条）
C = [
    # ── fact：体系定义与命名 ──────────────────────────────────────────
    ("fact", "动作研究目标与三阶段",
     "《Motion Study》（1911）把动作研究的目标定为「The aim of motion study is to find and perpetuate the scheme of perfection」，"
     "并提出三阶段：先发现并归类最佳实践、再推出法则、最后应用法则去标准化实践（既可增产也可减工时）。",
     ["MOTION", "PSYCH"], ["建立动作研究学科框架", "向工程师与公众定义方法目标"],
     "语料出现他否定该目标或把目标改为单纯增产的表述。", "fact", 0.9, "1911 前后"),
    ("fact", "therbligs 命名",
     "《Process Charts》（1921）把动作周期里的各个细分单元称为 therbligs（「the individual subdivisions of the cycle of motions, or therbligs, as they are called」），"
     "并主张用它们把 one best way 记录下来以供持续累积改进。语料未给出单元数量，也未解释名称来源。",
     ["PROCESS", "APPLIED"], ["定义基本动作单元术语", "记录 one best way 的持续改进"],
     "语料表明 therbligs 一词非他所用，或与动作细分单元无关。", "fact", 0.85, "1917-1921"),
    ("fact", "micro-motion 与 cyclegraph",
     "《Applied Motion Study》（1917）记述他发明的 micro-motion 方法——用摄影机、可记录时刻的时钟与分格背景记录动作（「The micro-motion method of making motion studies consists of recording motions by means of a motion picture camera」），"
     "又用「attaching a small electric light to the hand」的 cyclegraph 记录动作轨迹，并靠「putting an interrupter in the light circuit」得到带时间标记的 chronocyclegraph。",
     ["APPLIED", "PSYCH"], ["发明测量动作轨迹的装置", "在心理与教学层面论证其价值"],
     "语料把这些装置归于他人，或否认其记录用途。", "fact", 0.9, "1917 前后"),
    ("fact", "砌砖用最少动作",
     "《Bricklaying System》（1909）断言「It is a fact beyond dispute that the fastest bricklayers, and generally the best bricklayers, are those who use the fewest motions, and not those who are naturally the quickest motioned」。",
     ["BRICK", "MOTION"], ["砌砖标准化", "论证动作研究的节约潜力"],
     "语料出现最快的砌砖工反而用最多动作的记载。", "fact", 0.9, "1909-1911"),
    ("fact", "砌砖系统创新",
     "《Bricklaying System》（1909）展示他通过 packet system 与可顶升脚手架改造砌砖：动作图列出十八个操作（「it is not probable that any one first class bricklayer would use all of the eighteen operations as shown on this chart」），"
     "并有「Jacking Up the Scaffold While the Men Are Working on it」的可调高度脚手架。",
     ["BRICK", "MOTION"], ["砌砖工序标准化", "脚手架与材料布置创新"],
     "语料无 packet system、十八操作或顶升脚手架的记载。", "fact", 0.9, "1909-1911"),
    ("fact", "疲劳研究定位",
     "《Fatigue Study》（1916）副标题即「The Elimination of Humanity's Greatest Unnecessary Waste」，并断言「No organization can continue to be of first quality whose workers are over-fatigued」。",
     ["FATIGUE", "MOTION"], ["定义疲劳研究的使命", "论证工人过度疲劳的组织代价"],
     "语料把疲劳研究定位为别的目标（如单纯增产）。", "fact", 0.9, "1916"),
    ("lineage", "Primer 通俗化泰勒",
     "《Primer of Scientific Management》（1912）开篇引用 Taylor 的定义（「The principal object of management should be to secure the maximum prosperity for the employer coupled with the maximum prosperity for each employee」「Scientific Management has for its very foundation the firm conviction that the true interests of the two are one and the same」）并加以通俗化——"
     "这些主张属 Taylor 本人，Gilbreth 是转述者与普及者，不是原创者。",
     ["PRIMER", "PSYCH"], ["向初学者普及科学管理", "承接泰勒的科学管理谱系"],
     "语料表明这些定义是 Gilbreth 原创或未注明泰勒。", "fact", 0.9, "1912"),
    ("fact", "Field System 无账簿会计",
     "第三方 John P. Slack 记述 Gilbreth 的现场系统采用无账簿会计——「It provides for no cash book, journal nor ledger, but in their place substitutes what is in fact a systematic set of memoranda」，"
     "并称业主每周六可见截至周四的结构总成本。这是第三方对其系统的记述，不是自述。",
     ["FIELD", "MEASURE"], ["多工地远程成本管理", "让非制作者也能读懂的记录系统"],
     "语料表明该系统仍使用常规账簿。", "fact", 0.85, "1908"),
    ("fact", "Process Chart 定义",
     "《Process Charts》（1921）定义「The process chart is a device for visualizing a process as a means of improving it」，"
     "并要求在改动任何细分之前「the entire process must be presented in such form that it can be visualized all at once before any changes are made in any of its subdivisions」。",
     ["PROCESS", "MEASURE"], ["流程可视化方法", "改动前先审视全局"],
     "语料否认 process chart 的可视化目的。", "fact", 0.9, "1921"),
    ("fact", "测量人的价值",
     "《Measurement of the Human Factor》（1917）断言「Measurement on machines that are obsolete is of little value」「Measurement of human beings is valuable forever」，"
     "并说「definite and permanent advance is made in any kind of work, whether with materials or men, until use is made of measurement」。",
     ["MEASURE", "FATIGUE"], ["论证测量人的持久价值", "把测量列为工业进步前提"],
     "语料出现「测量人不重要」的相反表述。", "fact", 0.9, "1917"),
    # ── mental-model：跨场合的规律 ────────────────────────────────────
    ("mental-model", "疲劳研究属废除浪费",
     "他把疲劳研究与动作研究视为同一件事的两半——「Fatigue study is related to motion study in that both are branches of waste elimination」；"
     "不必要动作→不必要疲劳→浪费的因果链贯穿其体系。",
     ["FATIGUE", "MOTION"], ["衔接动作研究与疲劳研究", "把浪费作为统一的分析视角"],
     "语料把疲劳研究与清除浪费拆成无关的两件事。", "pattern", 0.85, "1916-1917"),
    ("mental-model", "one best way 动态",
     "他认为最佳方法不是一次定死的，而是要靠记录与持续累积改进逐步逼近：process chart「is not only the first step in visualizing the one best way to do work, but is useful in every stage of deriving it」，"
     "动作细节则「recorded for constant and cumulative improvement」。",
     ["PROCESS", "MOTION"], ["定义 one best way 的动态性", "流程图表作为逐步推导工具"],
     "语料表明 one best way 一旦确定就不可再改。", "pattern", 0.85, "1921"),
    ("mental-model", "把工人放在中心",
     "他把工人放在分析与设计活动的中心（「The moment one begins to make man, the worker, the centre of activity」），"
     "并接受 Lillian 在 PSYCH 里记下的个体观——「recognition of the individual, not only as an economic unit but also as a personality」。",
     ["FATIGUE", "PSYCH"], ["设计疲劳研究框架", "从心理学视角定义个体"],
     "语料把工人当纯工具或纯成本项。", "pattern", 0.85, "1914-1916"),
    ("mental-model", "变量分类框架",
     "他把影响产出的一切因素系统归类为变量——工人、环境/设备/工具、动作三大类，逐一单独考虑（MOTION 的三组变量表；PSYCH 记 motion study 为把工作拆成最基本细分单元）。",
     ["MOTION", "PSYCH"], ["建立动作分析框架", "把复杂产出问题拆成可测量变量"],
     "语料没有变量分类，或把各因素当作不可分解的整体。", "pattern", 0.85, "1911-1914"),
    ("mental-model", "不必要动作是最大浪费",
     "他反复断言浪费里最大的一类是不必要、方向错误、无效的动作——「There is no waste of any kind in the world that equals the waste from needless, ill-directed, and ineffective motions」（MOTION 与 APPLIED 均出现）。",
     ["MOTION", "APPLIED"], ["论证动作研究优先级", "把浪费概念统一到动作"],
     "语料出现「最大浪费是别的（如材料浪费）」的表述。", "pattern", 0.9, "1911-1917"),
    ("mental-model", "动作研究超越车间",
     "他把动作研究看作不限于工厂的通用方法，推广到办公室、学校、商店、家庭、农场（「they are not for the trades only; they are for the offices, the schools, the colleges, the stores, the households, and the farms」），"
     "并已与合作者研究手术中的基本动作与音乐家的肌肉活动。",
     ["MOTION", "APPLIED"], ["把方法推广到非车间领域", "与外科医生等外部合作"],
     "语料把动作研究限定为工厂专用。", "pattern", 0.85, "1911-1917"),
    ("mental-model", "反对把人当机器",
     "他正面反驳科学管理会「把人变成机器」的指责（「Does it not make machines out of men」），用训练有素的拳手、击剑手、高尔夫球员类比标准化的价值；"
     "Lillian 也在 PSYCH 中记下「Contrary to a widespread belief that Scientific Management kills individuality」。",
     ["PRIMER", "PSYCH"], ["回应外界对科学管理的批评", "辩护标准化与个体性相容"],
     "语料表明他认为标准化就该抹平个体差异。", "pattern", 0.85, "1912-1914"),
    # ── heuristic：可迁移的操作规律 ───────────────────────────────────
    ("heuristic", "先测量再下结论",
     "他强调先测量并「abide by the results」：不测量就无法可靠复现、预测与控制未来条件（MEASURE），因为「Measurement of human beings is valuable forever」。",
     ["MEASURE", "FATIGUE"], ["研究人类因素", "反对凭印象下结论"],
     "语料出现「凭经验即可」的反例。", "pattern", 0.9, "1917"),
    ("heuristic", "用标准化单元重构",
     "他认为真正的进步不是靠「消除」旧动作，而是靠把操作重新建构为标准单元——「the only real progress comes through a reconstruction of the operation, building it up of standardized units, or elements」。",
     ["MOTION", "PSYCH"], ["从现有方法走向标准方法", "把动作拆解后重组"],
     "语料说纯消除即可取得真正进步。", "pattern", 0.9, "1911-1914"),
    ("heuristic", "工人无法自行优化",
     "他断言工人无法凭自己按动作研究法则安排最经济的做法——「the worker cannot, by himself, arrange to do his work in the most economical manner in accordance with the laws of motion study」，"
     "因此需要专家研究与标准化。",
     ["MOTION", "PRIMER"], ["论证专家研究必要性", "说明标准为何由研究部门定"],
     "语料声称工人天然知道最优做法。", "pattern", 0.85, "1911-1912"),
    ("heuristic", "记录要能被他人使用",
     "他要求测量记录的形式要能让没做过这些测量的人直接用（MEASURE「records of measurement are in such form」，「that skill and experience may thus be transferred」）；"
     "Field System 的无账簿备忘录让业主也能一目了然。",
     ["MEASURE", "FIELD"], ["跨人复用测量结果", "多工地远程管理"],
     "语料主张记录只给测量者本人用。", "pattern", 0.85, "1908-1917"),
    ("heuristic", "用可视化辅助教学",
     "他主张用看得见的记录帮助教学与掌握：cyclegraph 的发明动机之一就是帮助不善视觉想象的工人掌握动作经济性（APPLIED），process chart 把流程可视化（PROCESS），工人「learn to think in elementary motions」。",
     ["APPLIED", "PROCESS"], ["把抽象动作变成可见轨迹", "用图表教工人与管理者"],
     "语料表明记录只用于归档而非教学。", "pattern", 0.85, "1917-1921"),
    ("heuristic", "先写标准再谈执行",
     "他主张标准即使暂时没有执行机制也要先写成文字——「Standards in writing should be made, even if there is not the managerial mechanism necessary to enforce and maintain them」，因为写下的标准会加速执行机制到来。",
     ["PROCESS", "PRIMER"], ["推动标准化落地", "长期累积改进"],
     "语料主张没有执行机制就不必写标准。", "pattern", 0.9, "1921"),
    ("heuristic", "调查先于行动",
     "他主张在动手之前先记录现状：疲劳研究以调查（survey）为起点（FATIGUE「A survey is an attempt to record existing conditions」），流程改进则以可视化整条流程为前置条件（PROCESS）。",
     ["FATIGUE", "PROCESS"], ["疲劳研究的第一步", "流程改进前审视全局"],
     "语料主张直接改而不先记录现状。", "pattern", 0.85, "1916-1921"),
    ("heuristic", "按个体特点分派工作",
     "他主张测量人类因素并据此把人放到合适的工作上（MEASURE 以 war cripple 与 industrial cripple 为例，说明教所有残障者同一种工作的错误），"
     "并把「It is the measurement that has resulted in better placement, and in assigning each individual to that type of work for which he will become best fitted」作为测量的好处。",
     ["MEASURE", "FATIGUE"], ["残障者就业问题", "按个体能力配岗"],
     "语料主张所有人做同一种标准工作。", "pattern", 0.85, "1917"),
    # ── value / work-method / contradiction / blind-spot / boundary ──
    ("value", "工人应得公平对待",
     "他认为工人只有在确信会得到公平对待时才会诚心配合（FATIGUE「they know that they are getting a square deal」），"
     "并强调疲劳研究「is not a new scheme for taking advantage of them」——方法与工人利益应一致。",
     ["FATIGUE", "PSYCH"], ["工人福利立场", "回应工人对科学管理的怀疑"],
     "语料主张可以靠欺骗或施压工人取得配合。", "pattern", 0.85, "1914-1916"),
    ("work-method", "工程决策量化+理由",
     "他在工程决策中给出可核验的量化设计并逐条说明理由：波纹混凝土桩以波纹「Increasing the surface for skin friction」并作射水出口（PILES），"
     "又以混凝土桩替代木桩省成本省时间（「With the concrete piles it was possible not only to save this cost, but also to save so much time that the rent available would come near to covering the cost of the piles」）。",
     ["PILES", "FIELD"], ["桩基方案比选", "材料替代的经济性论证"],
     "语料表明桩基选择纯凭惯例、无量化理由。", "pattern", 0.85, "1906-1908"),
    ("contradiction", "疲劳分类前后不一",
     "他对疲劳的分类在语料中前后不一致：《Motion Study》（1911）说「Fatigue is due to three causes」，"
     "包括带到工地的疲劳、因多余动作与环境条件造成的不必要疲劳、因产出造成的必要疲劳；"
     "而《Fatigue Study》（1916）说「There are two classes of fatigue」，只分不必要与必要两类——分类随体系演化而变化。",
     ["MOTION", "FATIGUE"], ["术语演化的文本证据", "动作研究与疲劳研究衔接"],
     "语料中两书分类完全一致。", "pattern", 0.9, "1911-1916"),
    ("blind-spot", "疲劳毒素理论过时",
     "他采纳了当时医学的「疲劳毒素」说（MOTION「The toxin of fatigue is the phrase the physicians have given us」，「Fatigue is due to a secretion in the blood」），"
     "把疲劳归因于血液中的毒素——这套生理机制解释在今天已被更精细的疲劳科学取代，属于他那个时代科学视野的边界。",
     ["MOTION", "FATIGUE"], ["依赖当时医学理论", "作为时代科学边界的案例"],
     "语料表明他否弃了疲劳毒素理论。", "pattern", 0.85, "1911-1916"),
    ("boundary", "不能替代天才与一流技工",
     "他承认动作研究不能取代一流技工或天才的价值（APPLIED「There will be those who will say that no such theory, methods, or devices can ever supplant the need and usefulness of the first-class mechanic or the genius in the trades」，"
     "并答「With this we humbly agree」），但可把两位天才的方法拆成基本单元、各取最优重组。",
     ["APPLIED", "PRIMER"], ["为方法划定射程", "承认人高于方法"],
     "语料声称方法可以完全取代人才。", "pattern", 0.9, "1917"),
    # ── soul-hypothesis（只许出现在 hypotheses.md）───────────────────
    ("soul-hypothesis", "科学方法万能论的乐观信仰",
     "（假设）他把「测量＋标准化＋消除浪费」当作一种可以改善一切人与事的普遍事业，并抱乐观信念：对工人是公平对待、对残障者是重新分派合适工作、对家庭与学校等一切活动都能用动作研究改善——这构成其人格底色。",
     ["FATIGUE", "MOTION"], ["对工人、残障者与各行业的普遍适用主张", "把方法使命化"],
     "语料显示他对科学方法的普遍适用持怀疑或悲观态度。", "hypothesis", 0.55, "1911-1917",
     ["① 可能是进步主义时代「效率崇拜」的普遍风气，不是他个人特有信念",
      "② 可能是作为效率顾问的公开宣传话术，与其私下判断有别",
      "③ 乐观与福利基调可能主要来自 Lillian 的心理学视角，而非他本人的工程师气质"]),
]


def main() -> int:
    rows = []
    for i, row in enumerate(C, 1):
        cat, appl, claim, srcs, ctxs, fals, status, conf, scope = row[:9]
        alts = list(row[9]) if len(row) > 9 else []
        sid = [S[k] for k in srcs]
        assert cat in CATEGORIES, f"clm {i} category 非法：{cat}"
        assert status in ("fact", "pattern", "hypothesis"), f"clm {i} status 非法：{status}"
        # ★ 门的硬规则，不是风格建议：ledger.py:76 与 quality_check.py:214
        if cat == "soul-hypothesis":
            assert status == "hypothesis", f"clm {i} soul-hypothesis 的 status 必须是 hypothesis"
            assert alts, f"clm {i} soul-hypothesis 必须给 alternative_explanations"
            assert fals, f"clm {i} soul-hypothesis 必须给 falsifiers"
        else:
            assert status != "hypothesis", f"clm {i} 只有 soul-hypothesis 可用 hypothesis"
        assert isinstance(conf, float) and 0 <= conf <= 1, f"clm {i} confidence 非法"
        assert len(sid) >= 2 and len(set(sid)) == len(sid), f"clm {i} 源不足 2 或重复"
        assert len(ctxs) >= 2, f"clm {i} 情境不足 2"
        for mark in ("...", "…"):
            assert mark not in claim, f"clm {i} 引号内含省略号：{mark}"
        rows.append({
            "alternative_explanations": alts, "applicability": [appl] + ctxs,
            "author_role": "agent", "category": cat, "claim": claim,
            "claim_id": f"clm-{i:012x}", "confidence": conf, "contexts": ctxs,
            "counter_source_ids": [], "created_at": NOW, "evidence_clusters": sid,
            "falsifiers": fals, "source_ids": sid, "status": status,
            "supersedes": None, "time_scope": scope, "updated_at": NOW,
        })
    # ★★ 与门同口径：category ∧ status == 'pattern'。**不要退回去数 category。**
    cnt = collections.Counter(r["category"] for r in rows)
    n_model = sum(1 for r in rows if r["category"] == "mental-model" and r["status"] == "pattern")
    n_heur = sum(1 for r in rows if r["category"] == "heuristic" and r["status"] == "pattern")
    assert n_model >= 6, (f"mental-model(pattern) {n_model} < 6"
                          f"  ← category 计数是 {cnt['mental-model']}，**门不看这个**")
    assert n_heur >= 8, (f"heuristic(pattern) {n_heur} < 8"
                         f"  ← category 计数是 {cnt['heuristic']}，**门不看这个**")
    assert 29 <= len(rows) <= 31, f"条数 {len(rows)} 越界"
    OUT.write_text("\n".join(json.dumps(r, ensure_ascii=False, sort_keys=True) for r in rows) + "\n",
                   encoding="utf-8")
    print(f"断言 {len(rows)} 条 | 类别 {dict(cnt)}")
    print(f"  mental-model {cnt['mental-model']}(≥6) heuristic {cnt['heuristic']}(≥8)")
    print("  ✓ 生成时断言全过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
