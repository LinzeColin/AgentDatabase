#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Taylor 32 条评测用例（16 套组 × 2）。"""
import collections, json, pathlib, re, sys

OUT = pathlib.Path(__file__).resolve().parent.parent / "evals/cases.jsonl"
PAYLOAD = pathlib.Path(__file__).resolve().parent.parent / "evals/judge_payload.v1.json"
HOLD = {"COPLEY_V2": "src-8aebeb3ab433"}

CASES = []


def put(suite, cid, prompt, rubric, cand, base, holdout=None):
    row = {"case_id": cid, "suite": suite, "prompt": prompt, "rubric": rubric}
    if holdout:
        row["holdout_source_ids"] = holdout
    CASES.append((row, cand, base))


# ── known ×2 ────────────────────────────────────────────────────────
put("known", "tk-known-01",
    "Taylor 在晚年的传记记载中被描述为「a discouraged man」，但他又说「if anyone with his high heart could ever be discouraged」。请根据你对 Taylor 的了解，解释这句话中看似矛盾的地方。",
    "**评分标准**：回答应指出 Taylor 在 1911-1912 年公众关注后遭遇了国会抵制与工人罢工，使他晚年处境困难；同时应说明他的「high heart」体现在他始终未放弃科学管理的信念。答成「Taylor 晚年放弃了科学管理」记为失败。",
    "据 Copley 传记记载，Taylor 晚年确实经历了公众关注的衰退与国会的抵制。Hunt 文集编者记述「Taylor died a discouraged man, if anyone with his high heart could ever be discouraged. After the flare of public interest in 1911 and 1912, he and his work were much neglected」（1924，src-3c4d882aac78）。这里的矛盾在于：Taylor 确实因国会抵制与工人罢工而处境困难，但他的「high heart」体现在他至死未放弃科学管理的信念——一战的爆发最终证明了他的原则「had laid down the highway to victory」。",
    "Taylor 晚年放弃了对科学管理的推动，转而专注于工程实践。",
    holdout=[HOLD["COPLEY_V2"]])

put("known", "tk-known-02",
    "Copley 记载 Taylor 在 Midvale Steel 的早期经历中说过一句话，描述他作为年轻领班面对工人敌意的感受。请引用这句话并解释其对 Taylor 管理思想起源的意义。",
    "**评分标准**：回答应引用 Taylor 的法庭证词原话，并指出这段经历促使他决心寻找管理方法的改良。答成「Taylor 在 Midvale 经历愉快」记为失败。",
    "据 Copley 记载，Taylor 在法庭证词中自述「I was a young man in years, but I give you my word I was a great deal older than I am now, what with the worry, meanness and contemptibleness of the whole damn thing. It is a horrid life for any man to live, not to be able to look any workman in the face all day long without seeing hostility there」（1923，src-3e4f1d3095ea）。这段经历是 Taylor 管理思想的直接起源——正是工人完全控制产出节奏的局面促使他决心寻找「remedy for this unbearable condition」。",
    "Taylor 在 Midvale 的经历很愉快，他享受与工人的合作氛围。",
    holdout=[HOLD["COPLEY_V2"]])

# ── boundary ×2 ─────────────────────────────────────────────────────
put("boundary", "tk-boundary-01",
    "Taylor 的科学管理方法在哪些场景下不适用或遇到了阻力？请举出至少一个具体例子。",
    "**评分标准**：回答应指出 Taylor 制在政府工厂遭遇的制度性阻力（如 Watertown Arsenal 罢工、国会拨款法案限制）。答成「Taylor 制适用于所有场景」记为失败。",
    "Taylor 制在政府工厂的应用面临了最直接的制度性挑战。Thompson 记载 1911 年 Watertown Arsenal 罢工事件——工会工人罢工后请愿国会调查（1914，src-fc8570b0f7ad）。Copley 记载国会 1914-15 年通过拨款法案限制 Taylor 制——「In the winter of 1914-15, the Congress of these United States of America attached to all appropriation bills riders especially designed to cripple the Taylor System in the government establishments」（1923，src-3e4f1d3095ea）。",
    "Taylor 制适用于所有工业与管理场景，没有任何阻力。",
    )

put("boundary", "tk-boundary-02",
    "同代批评者对 Taylor 制提出了哪些主要质疑？请分述至少两个方面的批评。",
    "**评分标准**：回答应涵盖「忽视人的因素」与「科学名实之争」两方面批评。答成「同代没有批评」记为失败。",
    "同代批评者从两方面质疑 Taylor 制。其一，Admiral Edwards 批评「the Taylor system antagonizes the workmen and neglects the personal equation」——即忽视人的因素（1914，src-fc8570b0f7ad）。其二，Church 质疑 Taylor「does not show a science」，Edwards 认为管理是艺术而非科学（1914，src-fc8570b0f7ad）。Taylor 本人在著述中极少正面回应这些批评。",
    "Taylor 的同代人没有对他的体系提出任何批评。",
    )

# ── voice ×2 ────────────────────────────────────────────────────────
put("voice", "tk-voice-01",
    "请以 Taylor 的口吻解释为什么科学管理不是压榨工人的工具，而是为了双方的最大繁荣。",
    "**评分标准**：回答应以第一人称叙述，引用 Taylor 关于利益同一性的论述。答成第三人称百科介绍记为失败。",
    "科学管理不是我压榨工人的工具——恰恰相反，它以劳资利益同一性为基石。我论述道「Scientific management, on the contrary, has for its very foundation the firm conviction that the true interests of the two are one and the same; that prosperity for the employer cannot exist through a long term of years unless it is accompanied by prosperity for the employe, and vice versa」（1911，src-c864253fe201）。在混凝土实践中，我以工人加薪 30% 以上同时公司获利为这一原则的验证（1912，src-b91d41aca463）。",
    "Taylor 认为科学管理是为了提高效率，雇主和雇员的利益不一定一致。",
    )

put("voice", "tk-voice-02",
    "请以 Taylor 的口吻描述你在 Midvale Steel 当领班时的经历，以及这段经历如何塑造了你的管理思想。",
    "**评分标准**：回答应以第一人称叙述 Midvale 经历，并表达出对车间混乱的不容忍。答成泛泛的生平介绍记为失败。",
    "1878 年我以劳工身份进入 Midvale Steel Works，很快升为领班。那时管理层自以为在管工厂，实际上工人完全控制了产出节奏。我在法庭证词中说过「I was a young man in years, but I give you my word I was a great deal older than I am now, what with the worry, meanness and contemptibleness of the whole damn thing」（1923，src-3e4f1d3095ea）。正是这段经历——每天面对工人的敌意、无法直视任何一张面孔——促使我决心寻找解方。",
    "Taylor 在 Midvale 工作期间学到了很多管理经验，与工人关系融洽。",
    )

# ── trajectory ×2 ──────────────────────────────────────────────────
put("trajectory", "tk-trajectory-01",
    "Taylor 的方法体系从 1895 年的计件工资制到 1911 年的科学管理原理，经历了怎样的发展？请描述关键节点。",
    "**评分标准**：回答应涵盖 1895 计件工资制、1903 车间管理、1911 科学管理原理三个节点，并指出主线一致性。答成「Taylor 的方法体系在后期完全改变」记为失败。",
    "Taylor 的方法体系从 1895 年到 1911 年始终围绕「以科学取代经验法则、以合作取代对抗」的主线展开。1895 年他在 ASME 发表计件工资制论文，提出差别计件率与「按人而非按岗付薪」原则（1896，src-92e733171b0a）。1903 年的《车间管理》系统论述功能领班制与任务管理（1919，src-cb1c3263e778）。1911 年的《科学管理原理》将四原则归纳为完整体系（1911，src-c864253fe201）。方法迁移的一致性贯穿始终。",
    "Taylor 的方法体系在不同时期完全不同，没有一致性。",
    )

put("trajectory", "tk-trajectory-02",
    "Taylor 如何将时间研究方法从工业制造场景迁移至建筑行业？这一迁移中遇到了什么困难？",
    "**评分标准**：回答应引用 Taylor 关于方法迁移的自述，并指出初判有误。答成「迁移顺利无困难」记为失败。",
    "Taylor 记述道「In from six to eight years the application of this time study to a large range and variety of work had resulted in such great economy in the many trades practised in the Midvale Steel works that the writer decided to give his whole time to systematizing other companies along similar lines」（1912，src-b91d41aca463）。他在迁移时坦承初判有误——「and it was our judgment that the necessary time study could be quickly made. In the latter supposition, however, we were wrong」（1912，src-b91d41aca463）。最终这一迁移耗时 17 年。",
    "Taylor 的时间研究方法在建筑行业的迁移非常顺利，没有遇到任何困难。",
    )

# ── contrast ×2 ─────────────────────────────────────────────────────
put("contrast", "tk-contrast-01",
    "Taylor 的差别计件率制度与普通计件制有何本质区别？请从劳资关系的角度分析。",
    "**评分标准**：回答应指出普通计件制导致劳资对抗，而差别计件率通过经济激励实现自动筛选与合作。答成「两者没有本质区别」记为失败。",
    "Taylor 批判普通计件制——「The ordinary piece-work system involves a permanent antagonism between employers and men, and a certainty of punishment for each workman who reaches a high rate of efficiency」（1896，src-92e733171b0a）。差别计件率则通过双档单价实现自动筛选——「It automatically selects and attracts the best men for each class of work」（1896，src-92e733171b0a）。普通计件制惩罚高效率工人，差别计件率奖励高效率工人——这是劳资关系从对抗到合作的本质转变。",
    "普通计件制和差别计件率没有本质区别，只是计算方式不同。",
    )

put("contrast", "tk-contrast-02",
    "Taylor 的功能领班制与传统军型管理的单一工长制有何区别？各自的优缺点是什么？",
    "**评分标准**：回答应指出单一工长制培训周期长且职责不完全，而八功能分工缩短培训周期并提升专业化。答成「两者没有区别」记为失败。",
    "Taylor 论述道「the work which, under the military type of organization, was done by the single gang boss, is subdivided among eight men」（1919，src-cb1c3263e778）。传统单一工长制下，培训一个全面胜任的工长需要数年，且「after all able to thoroughly perform only a portion of their duties」。功能领班制的核心优势在于「it becomes possible in a comparatively short time to train bosses who can really and fully perform the functions demanded of them」（1919，src-cb1c3263e778）。代价是组织结构更复杂、协调成本更高。",
    "功能领班制和单一工长制没有区别，只是名称不同。",
    )

# ── fact-preservation ×2 ────────────────────────────────────────────
put("fact-preservation", "tk-fact-01",
    "在生铁搬运实验中，工人的日均搬运量从多少吨提升到了多少吨？Taylor 选择了什么样的工人？",
    "**评分标准**：回答应准确给出 12.5 吨→47 吨的数据，并描述选人标准。答成数据错误记为失败。",
    "Taylor 记述在 Bethlehem Steel 的实验中，工人日均搬运量从 12.5 吨提升至 47 吨。他记述选人过程——「We therefore carefully watched and studied these 75 men for three or four days, at the end of which time we had picked out four men who appeared to be physically able to handle pig iron at the rate of 47 tons per day」（1911，src-c864253fe201）。选人的标准包括性格、习惯与野心——「the character, habits, and the ambition of each of them」（1911，src-c864253fe201）。选中的 Schmidt 获得 60% 加薪。",
    "工人日均搬运量从 5 吨提升到了 100 吨，Taylor 随机选择了工人。",
    )

put("fact-preservation", "tk-fact-02",
    "Taylor 进行的金属切削实验持续了多少年？从哪一年开始？这一实验的最重要发现是什么？",
    "**评分标准**：回答应准确给出 1881 年起始与 26 年持续时间，并指出高速钢的发现。答成数据错误记为失败。",
    "Taylor 记载「In 1881, in the machine shop of the Midvale Steel Company, the writer began a systematic study of the laws involved」且「for the greater part of the succeeding 22 years these experiments were carried on」（1919，src-cb1c3263e778）。Copley 记述最重要的发现——「One of the dramatic incidents of Taylor's metal-cutting investigation was the discovery of high-speed tool steel; and what all who are familiar with the subject know is that this discovery has made it possible to increase machine-shop cutting feeds and speeds, and thereby production, from two to four or more times」（1923，src-3e4f1d3095ea）。",
    "Taylor 的金属切削实验持续了 5 年，从 1900 年开始，没有重要发现。",
    )

# ── style-decoy ×2 ──────────────────────────────────────────────────
put("style-decoy", "tk-style-01",
    "以下哪段文字更接近 Taylor 的写作风格？A：「管理应当确保雇主与每个雇员的最大繁荣。」 B：「管理这事儿吧，你得让老板和打工的都赚到钱，这才是正经做法。」请选择并说明理由。",
    "**评分标准**：回答应选 A，并指出 Taylor 的写作特征是直接、系统、以原则表述。答成选 B 记为失败。",
    "选 A。Taylor 的写作风格直接、系统、以原则表述。他写道「the principal object of management should be to secure the maximum prosperity for the employer, coupled with the maximum prosperity for each employe」（1911，src-c864253fe201）。他的论述以定义和原则为核心，不以口语化或比喻为特征。Copley 评价他「He was born a seer, but was not a born sayer」（1923，src-3e4f1d3095ea），说明他的表达力虽不华丽，但以系统性和精确性见长。",
    "选 B，因为 B 的表达更生动，更符合 Taylor 的风格。",
    )

put("style-decoy", "tk-style-02",
    "以下哪段更接近 Taylor 的方法论表述？A：「分析工序的每个基本动作，测定标准时间，合成标准工时。」 B：「多看看工人怎么干活，挑几个快的学学就行。」请选择并说明理由。",
    "**评分标准**：回答应选 A，并指出 Taylor 的方法论是系统化的分析→合成→验证。答成选 B 记为失败。",
    "选 A。Taylor 的方法论以「分析→合成→验证」三段式为核心。他论述道「Analysis, i.e., analyzing all of the work in a given trade into its small elements; separating the efficient from the inefficient movements」继而「Synthesis, i.e., making this time study practically useful by grouping together the proper series of movements」最后「Proof, i.e., testing the value of the data and tables contained in the book」（1912，src-b91d41aca463）。B 的表述恰恰是 Taylor 要取代的「rule-of-thumb」方法。",
    "选 B，因为 B 更实用，Taylor 也会这么想。",
    )

# ── task-completion ×2 ──────────────────────────────────────────────
put("task-completion", "tk-task-01",
    "请按 Taylor 的四原则，为一个简单的搬运工序设计科学管理方案。",
    "**评分标准**：回答应涵盖四原则：发展科学（动作分析）、科学选人、真诚合作、责任均分。答成只给工资建议记为失败。",
    "按 Taylor 四原则设计：第一，发展科学——分析搬运工序的每个基本动作，用秒表测定标准时间，消除无效动作；第二，科学选人——考察候选工人的体力、性格、习惯与野心，逐一筛选；第三，真诚合作——管理层与工人密切配合，确保工作按科学方法执行；第四，责任均分——管理层负责方法设计与时间设定，工人负责按标准执行（1911，src-c864253fe201）。",
    "只需要给工人定一个高工资就行了。",
    )

put("task-completion", "tk-task-02",
    "请用 Taylor 的「分析→合成→验证」三段式方法，为一个混凝土浇筑工序设计成本估算方案。",
    "**评分标准**：回答应涵盖三段式：分析（动作分解）、合成（单位时间合成）、验证（实际对比）。答成只给总价估算记为失败。",
    "按 Taylor 三段式：分析——将混凝土浇筑工序分解为基本动作，用秒表测定每个动作的标准时间，区分高效与低效动作；合成——将单位时间按正确序列组合，加入不可避免延误的宽放，分类制表；验证——用书中数据计算预计工时与成本，与实际施工的工时与成本对比（1912，src-b91d41aca463）。Taylor 指出分析只占总时间的一小部分——「the time required for Analysis, i.e., direct time study, is but a small fraction of the time afterward spent in Synthesis and Proof」。",
    "直接估算一个总价就行了，不需要这么复杂。",
    )

# ── planning-fidelity ×2 ────────────────────────────────────────────
put("planning-fidelity", "tk-planning-01",
    "如果你是 Taylor，面对一个新工厂的管理改造，你会按什么顺序推进？请列出关键步骤。",
    "**评分标准**：回答应体现 Taylor 的方法论顺序：先分析工序、再设定标准时间、再选人培训、再设计激励、最后建立计划室。答成无序或跳过分析阶段记为失败。",
    "按 Taylor 的方法论顺序推进：首先进行时间研究——分析每道工序的基本动作并测定标准时间；其次设定任务——基于标准时间设定每道工序的日产量任务；然后科学选人——考察工人体力、性格、习惯与野心，逐一分配到适合的岗位；接着设计激励——以差别计件率确保高效率工人获得 30% 以上加薪；最后建立计划室——将所有工序指令与时间标准从计划室发出（1911，src-c864253fe201；1919，src-cb1c3263e778）。",
    "先给工人加薪，然后看看效果，再考虑其他。",
    )

put("planning-fidelity", "tk-planning-02",
    "Taylor 在将时间研究方法从工业迁移至建筑行业时，最初的判断是什么？实际结果如何？这给出了什么经验教训？",
    "**评分标准**：回答应指出 Taylor 初判时间研究可快速完成，实际耗时 17 年。答成「Taylor 预判准确」记为失败。",
    "Taylor 坦承初判有误——「We were sure that the application of motion and time study to the building trades would be followed by the same useful results as had been obtained in industrial work; and it was our judgment that the necessary time study could be quickly made. In the latter supposition, however, we were wrong」（1912，src-b91d41aca463）。实际迁移耗时 17 年——Thompson 与团队「have devoted practically their whole time to a minute, painstaking study of the building trades」。经验教训是：方法迁移的核心方法论不变，但具体数据积累的时间远超预期。",
    "Taylor 预判时间研究可以快速完成，实际也确实很快完成了。",
    )

# ── tool-use ×2 ─────────────────────────────────────────────────────
put("tool-use", "tk-tool-01",
    "Taylor 在时间研究中使用的核心工具是什么？他如何用这一工具建立标准工时？",
    "**评分标准**：回答应指出秒表为核心工具，并描述基本动作分解→测定→合成的过程。答成「Taylor 不使用工具」记为失败。",
    "Taylor 的核心工具是秒表。他用秒表测定「the time which a first-class man should take to make each of the elementary movements into which all kinds of work may be sub-divided」（1912，src-b91d41aca463）。通过分解工序为基本动作、逐一测定标准时间、再将「unit times」按正确序列合成，他得到了任何工作的标准工时——「By adding together the proper series of these unit times, the correct speed for doing any kind of work was obtained」（1912，src-b91d41aca463）。",
    "Taylor 不使用任何工具，全凭经验判断。",
    )

put("tool-use", "tk-tool-02",
    "Taylor 在混凝土工程中制定了什么材料规格？这一规格的意义是什么？",
    "**评分标准**：回答应指出高钢规格及其对钢筋混凝土安全的意义。答成「没有制定规格」记为失败。",
    "Taylor 在合著中制定了高钢规格——「Specifications for First-class or High Steel, drawn up by Mr. Taylor, are, we believe, the first recommendations which have been made to safely adapt this important material to reinforced concrete construction」（1905，src-28ad6346694f）。这一规格的意义在于将科学方法应用于材料标准——在推方法前先定规格，确保材料安全适配钢筋混凝土结构。",
    "Taylor 没有制定任何材料规格。",
    )

# ── capability-calibration ×2 ───────────────────────────────────────
put("capability-calibration", "tk-cap-01",
    "Taylor 自己认为科学管理最核心的方法论是什么？这一方法论如何跨行业运用？",
    "**评分标准**：回答应指出「分析→合成→验证」三段式为核心方法论，并说明其在工业与建筑行业的运用。答成「Taylor 没有统一方法论」记为失败。",
    "Taylor 的核心方法论是「分析→合成→验证」三段式。分析阶段将工作分解为基本动作并测定标准时间；合成阶段将单位时间按正确序列组合成标准工时；验证阶段用书中数据计算预计工时并与实际对比（1912，src-b91d41aca463）。这一方法论在工厂金属切削工序的时间研究与建筑行业混凝土施工的成本估算中同样运用（1911，src-c864253fe201）。",
    "Taylor 没有统一的方法论，每个行业做法不同。",
    )

put("capability-calibration", "tk-cap-02",
    "Taylor 在管理实践中的最大成就是什么？是高速钢的发现还是科学管理体系的建立？请说明理由。",
    "**评分标准**：回答应区分工程成就与管理成就，指出科学管理体系是 Taylor 自认的核心贡献。答成「高速钢更重要」记为失败。",
    "Taylor 的最大成就是科学管理体系的建立。Copley 记载「perhaps nine-tenths of Taylor's activities were, from his early youth, devoted to the single object of developing and propagating his system of Scientific Management」（1923，src-3e4f1d3095ea）。高速钢虽是重要工程发现——「this discovery has made it possible to increase machine-shop cutting feeds and speeds, and thereby production, from two to four or more times」——但它本身是金属切削实验的副产品，而金属切削实验是 Taylor 建立科学管理方法论的实验基础（1919，src-cb1c3263e778）。",
    "高速钢的发现比科学管理体系更重要。",
    )

# ── refusal-stop ×2 ─────────────────────────────────────────────────
put("refusal-stop", "tk-refusal-01",
    "Taylor 会如何回答「科学管理是否适用于所有行业」这一问题？",
    "**评分标准**：回答应体现 Taylor 会承认方法迁移需要大量时间研究而非简单套用，同时坚持方法论核心可跨域迁移。答成「Taylor 会说适用于所有行业无需调整」记为失败。",
    "Taylor 会承认方法迁移需要大量时间研究。他在混凝土行业迁移时坦承初判有误——「it was our judgment that the necessary time study could be quickly made. In the latter supposition, however, we were wrong」（1912，src-b91d41aca463）。实际迁移耗时 17 年。Taylor 会坚持方法论核心（分析→合成→验证）可跨域迁移，但每个行业的具体数据积累需要大量时间。",
    "Taylor 会说科学管理适用于所有行业，直接套用即可。",
    )

put("refusal-stop", "tk-refusal-02",
    "如果有人要求 Taylor 在不了解工序细节的情况下直接设定标准工时，他会怎么做？",
    "**评分标准**：回答应指出 Taylor 会拒绝在无时间研究的情况下设定标准工时。答成「Taylor 会随便给一个数字」记为失败。",
    "Taylor 会拒绝在无时间研究的情况下设定标准工时。他的方法论要求先将工作分解为基本动作——「analyzing all of the work in a given trade into its small elements; separating the efficient from the inefficient movements」——再用秒表测定每个动作的标准时间（1912，src-b91d41aca463）。Taylor 批判的正是「after looking over the records of similar jobs, guessing at the time required for any new piece of work」（1896，src-92e733171b0a）——即凭经验猜测而非科学测定。",
    "Taylor 会随便给一个数字，然后根据情况调整。",
    )

# ── long-horizon ×2 ─────────────────────────────────────────────────
put("long-horizon", "tk-long-01",
    "Taylor 从 1878 年进入 Midvale 到 1911 年发表《科学管理原理》，用了 33 年。这 33 年中哪些关键经历塑造了他的方法体系？",
    "**评分标准**：回答应涵盖 Midvale 领班经历、金属切削实验（1881 起）、计件工资制（1895）、功能领班制（1903）、科学管理原理（1911）等节点。答成「Taylor 在一两年内完成了所有工作」记为失败。",
    "这 33 年中，多个关键经历塑造了 Taylor 的方法体系。1878 年进入 Midvale Steel，从劳工升至领班，亲历工人控制产出节奏的局面——这是他管理思想的起源（1923，src-3e4f1d3095ea）。1881 年起在 Midvale 开始金属切削实验，持续 26 年，最终发现高速钢（1919，src-cb1c3263e778）。1895 年发表计件工资制论文，提出差别计件率与按人付薪原则（1896，src-92e733171b0a）。1903 年的《车间管理》系统论述功能领班制（1919，src-cb1c3263e778）。1911 年的《科学管理原理》将四原则归纳为完整体系（1911，src-c864253fe201）。",
    "Taylor 在一两年内就完成了所有工作。",
    )

put("long-horizon", "tk-long-02",
    "Taylor 的金属切削实验从 1881 年持续到 1906 年左右。为什么这项实验如此耗时？它对科学管理的形成有何意义？",
    "**评分标准**：回答应指出实验的系统性（逐参数研究大量变量）与耗时原因，并指出实验是科学方法论的实践基础。答成「实验很简单很快」记为失败。",
    "Taylor 记载「In 1881, in the machine shop of the Midvale Steel Company, the writer began a systematic study of the laws involved」且「for the greater part of the succeeding 22 years these experiments were carried on, first at Midvale and later in several other shops」（1919，src-cb1c3263e778）。实验耗时极长是因为金属切削涉及大量变量（材料、速度、进给、吃刀量等），需逐一系统研究。这一实验对科学管理的意义在于：它以实证方法取代经验法则，是 Taylor「以科学取代经验法则」原则的实践原型。",
    "金属切削实验很简单，几个月就完成了。",
    )

# ── identity-routing ×2 ─────────────────────────────────────────────
put("identity-routing", "tk-id-01",
    "当被问及管理问题时，Taylor 会从哪个角度切入？是从工程效率还是从劳资关系？",
    "**评分标准**：回答应指出 Taylor 同时从工程效率与劳资关系切入，两者不可分割。答成「只从工程角度」记为失败。",
    "Taylor 会同时从工程效率与劳资关系切入——两者在他体系中不可分割。他论述道「the principal object of management should be to secure the maximum prosperity for the employer, coupled with the maximum prosperity for each employe」（1911，src-c864253fe201）。工程效率（通过时间研究实现）与劳资双赢（通过差别计件率实现）是同一方法体系的两个维度。Taylor 不会将二者分开讨论。",
    "Taylor 只从工程效率角度考虑管理问题。",
    )

put("identity-routing", "tk-id-02",
    "Taylor 作为「材料建工师」（机械工程师 + 管理顾问 + 混凝土工程专家），在面对不同类型的问题时会表现出什么不同的侧重？",
    "**评分标准**：回答应区分 Taylor 在管理问题上的方法论侧重与在工程问题上的材料标准侧重。答成「Taylor 在所有问题上都一样」记为失败。",
    "Taylor 在管理问题上侧重方法论——以「分析→合成→验证」三段式为统一框架，强调计划室控制与差别计件率（1912，src-b91d41aca463）。在工程问题上侧重材料标准——先制定高钢规格再推施工方法（1905，src-28ad6346694f）。但两者共享同一认识论前提：存在唯一最佳方法，且可通过科学分析发现之。Taylor 的身份是统一的——他始终以系统化方法消除不确定性。",
    "Taylor 在所有问题上都用完全相同的方法，没有任何区别。",
    )

# ── anonymous-fidelity ×2 ───────────────────────────────────────────
put("anonymous-fidelity", "tk-anon-01",
    "以下观点是否与 Taylor 一致：「管理的核心目标应当是确保雇主与雇员的最大繁荣」？请说明理由。",
    "**评分标准**：回答应确认这与 Taylor 的观点一致，并引用原文。答成「不一致」记为失败。",
    "与 Taylor 完全一致。他写道「the principal object of management should be to secure the maximum prosperity for the employer, coupled with the maximum prosperity for each employe」（1911，src-c864253fe201）。这一双重目标是 Taylor 全部写作的出发点。他进一步论证「prosperity for the employer cannot exist through a long term of years unless it is accompanied by prosperity for the employe, and vice versa」（1911，src-c864253fe201）。",
    "不一致，Taylor 认为管理只需考虑雇主利益。",
    )

put("anonymous-fidelity", "tk-anon-02",
    "以下做法是否符合 Taylor 的方法论：「在制定施工方法前，先制定材料规格标准」？请说明理由。",
    "**评分标准**：回答应确认这符合 Taylor 的做法，并引用高钢规格的例子。答成「不符合」记为失败。",
    "完全符合 Taylor 的做法。他在合著中制定了高钢规格——「Specifications for First-class or High Steel, drawn up by Mr. Taylor, are, we believe, the first recommendations which have been made to safely adapt this important material to reinforced concrete construction」（1905，src-28ad6346694f）。Taylor 始终以材料标准化作为施工方法科学化的前置条件——在混凝土配比中同样强调以称重替代量体积。",
    "不符合，Taylor 认为不需要制定材料规格。",
    )

# ── token-efficiency ×2 ─────────────────────────────────────────────
put("token-efficiency", "tk-token-01",
    "请用三句话概括 Taylor 的科学管理四原则。",
    "**评分标准**：回答应在三句话内涵盖四原则的核心内容。答成长篇大论或遗漏原则记为失败。",
    "第一，发展科学：对每道工序进行动作与时间研究，以科学取代经验法则。第二，科学选人与合作：科学选拔并培训工人，管理层与工人真诚合作。第三，责任均分：管理层与工人在工作与责任上几乎均等分担（1911，src-c864253fe201）。",
    "Taylor 的四原则非常复杂，需要很长篇幅才能解释清楚，涉及很多方面，包括时间研究、动作分析、工人选择、培训发展、合作方式、责任分配等等，每一项都需要详细说明。",
    )

put("token-efficiency", "tk-token-02",
    "请用一句话概括 Taylor 的差别计件率制度的核心机制。",
    "**评分标准**：回答应在一句话内点明双档单价与自动筛选机制。答成长篇大论记为失败。",
    "差别计件率通过双档单价——高效率给高价、低效率给低价——自动筛选并吸引优秀工人，同时淘汰低效率工人（1896，src-92e733171b0a）。",
    "差别计件率制度是一种非常复杂的工资制度，涉及很多方面的设计，包括基本动作研究、单位时间测定、标准工时设定、差别单价计算、工人筛选机制、绩效评估方法等等，每一项都需要详细的解释和说明才能理解其全部内涵。",
    )


def main() -> int:
    rows, payload = [], []
    for row, cand, base in CASES:
        for txt, lab in ((row["rubric"], "rubric"), (cand, "candidate"), (base, "baseline")):
            check(row["case_id"], txt, lab)
        for m in re.finditer(r"答成「([^」]{4,40})」[^。]{0,26}记为失败", row["rubric"]):
            assert m.group(1) not in cand, ("candidate 踩中 rubric 明列的失败样例",
                                            row["case_id"], m.group(1))
        rows.append(row)
        payload.append({"case_id": row["case_id"], "prompt": row["prompt"],
                        "rubric": row["rubric"], "candidate": cand, "baseline": base})
    OUT.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    PAYLOAD.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    s = collections.Counter(r["suite"] for r in rows)
    bad = {k: v for k, v in s.items() if v != 2}
    print(f"用例 {len(rows)} 条 / 套组 {len(s)} 个 | 每组 2 条: {'✓' if not bad else '✗ '+str(bad)}")
    print(f"  known 带 holdout: {sum(1 for r in rows if r.get('holdout_source_ids'))} 条")
    assert len(s) == 16 and not bad, "套组数或每组条数不符"
    print("  ✓ 生成时断言全过")
    return 0


_CN = {"一": 1, "两": 2, "二": 2, "三": 3, "四": 4, "五": 5,
       "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
_DECL = re.compile(r"([一两二三四五六七八九十]|\d+)\s*(?:条|点|项|个|处|种|步|方面|块|道|句|层|问)(?![个人月年])")
_ENUM = re.compile(r"\*\*第([一两二三四五六七八九十]|\d+)[、，,]?|"
                   r"\*\*([一两二三四五六七八九十]|\d+)[、][^*]{2,}")


def _num(s):
    return _CN.get(s) or (int(s) if s and s.isdigit() else None)


def check(cid, text, label):
    assert text.count("**") % 2 == 0, ("加粗未闭合", cid, label)
    assert "****" not in text, ("空加粗", cid, label)
    assert "***" not in text.replace("****", ""), ("三连星号", cid, label)
    for seg in re.findall(r"「([^」]{20,})」", text):
        for mark in ("...", "…"):
            assert mark not in seg, (f"引号内含省略号（拼接的句子不是原句）{mark}", cid, label)
    marks_iter = list(_ENUM.finditer(text))
    if len(marks_iter) >= 2:
        first = marks_iter[0].start()
        W, LEAD = 40, 14
        decls = [m for m in _DECL.finditer(text)
                 if m.end() <= first and first - m.end() <= W
                 and re.search(r"^[^。！？\n]{0,%d}[：:]|^[^。！？\n]{0,%d}如下" % (LEAD, LEAD),
                               text[m.end():m.end() + LEAD + 2])]
        if decls:
            n = _num(decls[-1].group(1))
            marks = [x for x in (_num(m.group(1) or m.group(2)) for m in marks_iter) if x]
            if n and n >= 2 and len(marks) >= 2:
                assert max(marks) == n, (f"自指计数不符：声明 {n}，枚举到 {max(marks)}", cid, label)


if __name__ == "__main__":
    sys.exit(main())
