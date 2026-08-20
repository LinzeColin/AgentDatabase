#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Taylor 十份渲染文档。"""
import collections, json, pathlib, re, sys

W = pathlib.Path(__file__).resolve().parent.parent
CL = [json.loads(l) for l in (W / "evidence/claims.jsonl").read_text(encoding="utf-8").splitlines()]


def find(cat, kw):
    hits = [c for c in CL if c["category"] == cat and kw in c["applicability"][0]]
    if len(hits) != 1:
        raise SystemExit(f"✗ 映射不唯一：({cat}, {kw}) 命中 {len(hits)} 条 —— "
                         f"claims.jsonl 改过就必须同步改这里，不能靠位置")
    return hits[0]["claim_id"]


M = {
    "best-method": find("mental-model", "best-method"),
    "speed-control": find("mental-model", "speed-control"),
    "analysis-synthesis": find("mental-model", "analysis-synthesis"),
    "interest-unity": find("mental-model", "interest-unity"),
    "science-replaces": find("mental-model", "science-replaces"),
    "functional-foremanship": find("mental-model", "functional-foremanship"),
    "planning-room": find("mental-model", "planning-room"),
    "scientific-selection": find("heuristic", "scientific-selection"),
    "differential-rate": find("heuristic", "differential-rate"),
    "one-man-at-a-time": find("heuristic", "one-man-at-a-time"),
    "unit-times": find("heuristic", "unit-times"),
    "wage-increase": find("heuristic", "wage-increase"),
    "method-transfer": find("heuristic", "method-transfer"),
    "motion-breakdown": find("heuristic", "motion-breakdown"),
    "pay-by-man": find("heuristic", "pay-by-man"),
    "material-specs": find("heuristic", "material-specs"),
    "pig-iron": find("fact", "pig-iron"),
    "midvale-start": find("fact", "midvale-start"),
    "high-speed-steel": find("fact", "high-speed-steel"),
    "congress-rider": find("fact", "congress-rider"),
    "max-prosperity": find("value", "max-prosperity"),
    "cooperation-not-antagonism": find("value", "cooperation-not-antagonism"),
    "four-principles": find("work-method", "four-principles"),
    "eight-functions": find("work-method", "eight-functions"),
    "refused-biography": find("boundary", "refused-biography"),
    "government-limits": find("boundary", "government-limits"),
    "neglects-human": find("blind-spot", "neglects-human"),
    "science-name-debate": find("blind-spot", "science-name-debate"),
    "cooperation-vs-conflict": find("contradiction", "cooperation-vs-conflict"),
    "order-drive": find("soul-hypothesis", "order-drive"),
}


def a(k):
    return f"<!-- claim:{M[k]} -->"


DOCS = {}

# ── facts.md ────────────────────────────────────────────────────────
DOCS["facts.md"] = f"""\
## Frederick Winslow Taylor · 事实

Frederick Winslow Taylor（1856-1915），美国机械工程师，科学管理之父。生于宾夕法尼亚 Germantown，卒于费城。1878 年以劳工身份进入 Midvale Steel Works，很快升为领班，此后逐步升至总工程师。<!-- claim:{M["midvale-start"]} -->

Taylor 的核心贡献横跨管理与工程两大领域。在管理方面，他创立了科学管理体系——以时间研究、动作研究、功能领班制与差别计件率为核心方法，著有《Shop Management》（1903）、《The Principles of Scientific Management》（1911）。在工程方面，他发现高速钢（与 Maunsel White 合作），进行了长达 26 年的金属切削实验，并与 Sanford E. Thompson 合著《A Treatise on Concrete》（1905）与《Concrete Costs》（1912）。<!-- claim:{M["high-speed-steel"]} -->

生铁搬运实验是 Taylor 论证「科学取代经验法则」的标志性案例。在 Bethlehem Steel 的实验中，工人日均搬运量从 12.5 吨提升至 47 吨。Taylor 通过「Schmidt, are you a high-priced man?」对话展示科学选人与任务设定的方法（1911，src-c864253fe201）。<!-- claim:{M["pig-iron"]} --> 这一案例集中体现了他的方法论：科学选人→设定任务→激励配合。

Taylor 的体系在传播过程中遭遇了政治与工会阻力。1911 年 Watertown Arsenal 罢工引发国会调查，1914-15 年国会通过拨款法案限制 Taylor 制在政府工厂的应用。Copley 记载「In the winter of 1914-15, the Congress of these United States of America attached to all appropriation bills riders especially designed to cripple the Taylor System in the government establishments」（1923，src-3e4f1d3095ea）。<!-- claim:{M["congress-rider"]} --> 1912 年众议院特别调查委员会的听证记录成为科学管理方法与实践的详尽文献。

Taylor 于 1915 年 3 月 21 日去世。Hunt 文集编者记载他去世时的处境——「Taylor died a discouraged man, if anyone with his high heart could ever be discouraged. After the flare of public interest in 1911 and 1912, he and his work were much neglected」（1924，src-3c4d882aac78）。一战使科学管理重新兴起，编者论述道「It was the war which forced scientific management again to the fore」（1924，src-3c4d882aac78）。
"""

# ── cognitive-os.md ────────────────────────────────────────────────
DOCS["cognitive-os.md"] = f"""\
## Frederick Winslow Taylor · 认知操作系统

Taylor 的认知体系以「存在唯一最佳方法、且可通过科学分析发现之」为认识论前提。他论述道「among the various methods and implements used in each element of each trade there is always one method and one implement which is quicker and better than any of the rest」并将此称为「the gradual substitution of science for rule of thumb throughout the mechanic arts」（1911，src-c864253fe201）。这一思维模型并非仅限于工厂管理——在混凝土著作中，他同样强调「The method is exact and scientific and not rule-of-thumb」（1905，src-28ad6346694f）。<!-- claim:{M["best-method"]} -->

Taylor 的工程决策方法论以「分析→合成→验证」三段式为统一框架。他记述道「Analysis, i.e., analyzing all of the work in a given trade into its small elements; separating the efficient from the inefficient movements of the workmen」继而「Synthesis, i.e., making this time study practically useful by grouping together the proper series of movements」最后「Proof, i.e., testing the value of the data and tables contained in the book by computing from the book the time it ought to take to build a structure about to be erected」（1912，src-b91d41aca463）。这一方法论在《科学管理原理》中以「准确、精细的动作与时间研究」的形式出现（1911，src-c864253fe201）。<!-- claim:{M["analysis-synthesis"]} -->

Taylor 始终以个体为管理的基本单元。他论述道「it is an inflexible rule to talk to and deal with only one man at a time, since each workman has his own special abilities and limitations」（1911，src-c864253fe201）。在计件工资制中，他同样强调薪酬按个人技能与精力而非岗位设定——「paying men and not positions」（1896，src-92e733171b0a）。Taylor 以逐一处理而非集体谈判为管理的基本操作模式。<!-- claim:{M["one-man-at-a-time"]} -->

Taylor 将工作逐步分解为基本动作并测定每个动作的标准时间。他论述道「He made a careful analysis of the movements of workmen in one job after another, eliminated all of the useless motions, and substituted fast for slow and inefficient movements. And then he studied with a stop-watch the time which a first-class man should take to make each of the elementary movements into which all kinds of work may be sub-divided」（1912，src-b91d41aca463）。在《科学管理原理》中，他以生铁搬运为案例展示了同一方法的运用（1911，src-c864253fe201）。<!-- claim:{M["motion-breakdown"]} --> Taylor 以秒表为认知工具，以基本动因为分析单元，以单位时间合成为推算路径，构成了完整的认知操作系统。
"""

# ── decision-policy.md ─────────────────────────────────────────────
DOCS["decision-policy.md"] = f"""\
## Frederick Winslow Taylor · 决策策略

Taylor 的决策体系以计划室为中枢。他论述道「The shop, and indeed the whole works, should be managed, not by the manager, superintendent, or foreman, but by the planning department」（1919，src-cb1c3263e778）。他甚至主张「the works could run smoothly even if the manager, superintendent and their assistants outside the planning room were all to be away for a month at a time」，并以 Bethlehem Steel 为例——「The large machine shop of the Bethlehem Steel Company was more than a quarter of a mile long, and this was successfully run from a single planning room」（1919，src-cb1c3263e778）。<!-- claim:{M["planning-room"]} -->

Taylor 认为任务管理的本质在于管理层对工作速度的完全控制权。他论述道「The essence of task management lies in the fact that the control of the speed problem rests entirely with the management」（1919，src-cb1c3263e778）。在混凝土成本中，同样的决策中枢迁移至建筑行业——从计划室发出工序指令与时间标准（1912，src-b91d41aca463）。Taylor 始终将「谁控制速度」视为管理权归属的核心判据。<!-- claim:{M["speed-control"]} -->

Taylor 以「单位时间」合成法作为成本估算的标准化工具。他论述道「By adding together the proper series of these unit times (as they are called), the correct speed for doing any kind of work was obtained」（1912，src-b91d41aca463）。在《车间管理》中，他同样以基本动作时间的测定为基础设定标准工时（1919，src-cb1c3263e778）。Taylor 将复杂工序的时间估算统一归结为基本动作单位时间的加权合成。<!-- claim:{M["unit-times"]} -->

Taylor 在实践新方法前先制定材料规格标准。他在合著中制定了高钢规格——「Specifications for First-class or High Steel, drawn up by Mr. Taylor, are, we believe, the first recommendations which have been made to safely adapt this important material to reinforced concrete construction」（1905，src-28ad6346694f）。在混凝土成本中，他同样强调以称重替代量体积——「more accurate and scientific to measure the aggregates by weight than by volume」（1905，src-28ad6346694f）。Taylor 始终以材料标准化作为施工方法科学化的前置条件。<!-- claim:{M["material-specs"]} -->
"""

# ── strategy.md ─────────────────────────────────────────────────────
DOCS["strategy.md"] = f"""\
## Frederick Winslow Taylor · 战略

Taylor 的战略核心是以科学方法系统性重构管理实践。他将「以科学取代经验法则」视为一切改良的出发点——在《科学管理原理》中将四原则的第一条归纳为发展科学以取代「the old rule-of-thumb method」（1911，src-c864253fe201）。在混凝土著作中，他强调配比应称重而非量体积，因为「more accurate and scientific to measure the aggregates by weight than by volume」（1905，src-28ad6346694f）。Taylor 跨行业实践始终以「经验法则可被且应被科学取代」为指导原则。<!-- claim:{M["science-replaces"]} -->

Taylor 将时间研究方法从工业制造场景迁移至建筑行业。他记述道「In from six to eight years the application of this time study to a large range and variety of work had resulted in such great economy in the many trades practised in the Midvale Steel works that the writer decided to give his whole time to systematizing other companies along similar lines」（1912，src-b91d41aca463）。他在迁移时坦承初判有误——「and it was our judgment that the necessary time study could be quickly made. In the latter supposition, however, we were wrong」（1912，src-b91d41aca463）。<!-- claim:{M["method-transfer"]} --> 这一方法迁移展现了 Taylor 从工业到建筑的跨域战略：以统一方法论为内核，以行业特性为参数调整。

Taylor 的功能领班制通过职责分解降低管理门槛并提升专业化。他论述道「the work which, under the military type of organization, was done by the single gang boss, is subdivided among eight men」并指出分工的核心收益在于「it becomes possible in a comparatively short time to train bosses who can really and fully perform the functions demanded of them」（1919，src-cb1c3263e778）。Thompson 文集记录了实践者对「functional foremanship」等术语的需求，确认 Taylor 的分工体系已成为行业讨论的基础框架（1914，src-fc8570b0f7ad）。<!-- claim:{M["functional-foremanship"]} --> Taylor 以组织结构重组为战略杠杆，将军型管理的单一指挥链替换为专业化分工的八功能体系。
"""

# ── capabilities.md ─────────────────────────────────────────────────
DOCS["capabilities.md"] = f"""\
## Frederick Winslow Taylor · 能力

Taylor 的核心能力在于以时间研究与动作分析系统重构工作流程。他将工作逐步分解为基本动作并测定每个动作的标准时间——「He made a careful analysis of the movements of workmen in one job after another, eliminated all of the useless motions, and substituted fast for slow and inefficient movements」（1912，src-b91d41aca463）。在《科学管理原理》中，他以生铁搬运为案例展示了同一方法（1911，src-c864253fe201）。这一能力使 Taylor 能够跨行业迁移方法体系。<!-- claim:{M["motion-breakdown"]} -->

Taylor 的科学选人方法要求考察体力、性格、习惯与野心。他记述生铁搬运实验中的选人过程：「We therefore carefully watched and studied these 75 men for three or four days, at the end of which time we had picked out four men who appeared to be physically able to handle pig iron at the rate of 47 tons per day」并进一步调查「the character, habits, and the ambition of each of them」（1911，src-c864253fe201）。Copley 记载 Taylor 在 Midvale 的早期经历中同样体现这一方法——他从劳工升至领班后逐一了解工人（1923，src-3e4f1d3095ea）。<!-- claim:{M["scientific-selection"]} -->

Taylor 的差别计件率制度通过经济激励自动筛选优秀工人。他论述道「It automatically selects and attracts the best men for each class of work, and it develops many first-class men who would otherwise remain slow or inaccurate, while at the same time it discourages and sifts out men who are incurably lazy or inferior」（1896，src-92e733171b0a）。在混凝土成本中，同样的经济逻辑以「工人加薪 30% 以上同时公司获利」的形式出现（1912，src-b91d41aca463）。<!-- claim:{M["differential-rate"]} --> Taylor 始终以「高效率=高工资+低成本」为激励设计的核心等式。

Taylor 坚持「按人而非按岗付薪」的薪酬哲学。他论述道「Each man's wages, as far as possible, are fixed according to the skill and energy with which he performs his work, and not according to the position which he fills」（1896，src-92e733171b0a）。在《车间管理》中，他以差别计件率实现这一原则——不同效率的工人在同一岗位上获得不同报酬（1919，src-cb1c3263e778）。<!-- claim:{M["pay-by-man"]} --> Taylor 始终以个体绩效而非岗位等级作为薪酬的基础。

Taylor 的经济决策逻辑以「工人加薪 30% 以上同时公司获利」为双赢基础。他论证道「This enabled us to pay them a substantial premium or bonus (an increase of 30% or more in their wages) whenever they did the tasks which were assigned them in the proper times, and still leave a good profit for the Company」（1912，src-b91d41aca463）。在《科学管理原理》中，Schmidt 获得 60% 加薪（1911，src-c864253fe201）。<!-- claim:{M["wage-increase"]} --> Taylor 始终以加薪幅度作为工人配合改革的交换条件。
"""

# ── persona.md ──────────────────────────────────────────────────────
DOCS["persona.md"] = f"""\
## Frederick Winslow Taylor · 人格画像

Taylor 是一位以系统化方法消除车间混乱的工程师-管理者。Copley 传记将 Taylor 定位为「科学管理的父亲」，并评价他「perhaps nine-tenths of Taylor's activities were, from his early youth, devoted to the single object of developing and propagating his system of Scientific Management」（1923，src-3e4f1d3095ea）。Copley 还评价 Taylor 的表达力不足——「He was born a seer, but was not a born sayer」（1923，src-3e4f1d3095ea），指出 Taylor 作为「实践者先于阐述者」的特质。<!-- claim:{M["refused-biography"]} -->

Taylor 以劳资利益同一性为科学管理的基石公理。他论述道「Scientific management, on the contrary, has for its very foundation the firm conviction that the true interests of the two are one and the same; that prosperity for the employer cannot exist through a long term of years unless it is accompanied by prosperity for the employe, and vice versa」（1911，src-c864253fe201）。Copley 记载 Taylor 在 Midvale 的经历正是这一信念的实践起源——他目睹工人完全控制产出节奏后决心寻找解方（1923，src-3e4f1d3095ea）。<!-- claim:{M["interest-unity"]} -->

Taylor 将科学管理的核心价值定位为合作而非对抗。他批判普通计件制——「The ordinary piece-work system involves a permanent antagonism between employers and men, and a certainty of punishment for each workman who reaches a high rate of efficiency」（1896，src-92e733171b0a）。Hunt 文集编者记录了战后管理从机械问题转向人的问题的趋势——「Not mechanical but human problems are in the foreground」（1924，src-3c4d882aac78）。<!-- claim:{M["cooperation-not-antagonism"]} -->

Taylor 自称追求劳资合作，但其在 Midvale 的实践经历与工人激烈对抗。他论述科学管理以「heartily cooperate with the men」为第三原则（1911，src-c864253fe201），但 Copley 记载他本人的法庭证词——「It is a horrid life for any man to live, not to be able to look any workman in the face all day long without seeing hostility there」（1923，src-3e4f1d3095ea）。Taylor 的合作理想与对抗实践之间存在内在张力：合作是目标而非起点，对抗是出发而非终点。<!-- claim:{M["cooperation-vs-conflict"]} -->
"""

# ── work.md ─────────────────────────────────────────────────────────
DOCS["work.md"] = f"""\
## Frederick Winslow Taylor · 工作方法

Taylor 将科学管理归纳为四原则体系。他论述道「First. They develop a science for each element of a man's work, which replaces the old rule-of-thumb method. Second, They scientifically select and then train, teach, and develop the workman. Third, They heartily cooperate with the men so as to insure all of the work being done in accordance with the principles of the science which has been developed. Fourth, There is an almost equal division of the work and the responsibility between the management and the workmen」（1911，src-c864253fe201）。在混凝土成本中，他以分析、合成、验证三段式将四原则中的「发展科学」具体化（1912，src-b91d41aca463）。<!-- claim:{M["four-principles"]} -->

Taylor 的功能领班制将单一工长的职责分解为八种功能。他论述道「the work which, under the military type of organization, was done by the single gang boss, is subdivided among eight men: (1) route clerks, (2) instruction card clerks, (3) cost and time clerks, who plan and give directions from the planning room; (4) gang bosses, (5) speed bosses, (6) inspectors, (7) repair bosses, who show the men how to carry out their instructions, and see that the work is done at the proper speed; and (8) the shop disciplinarian」（1919，src-cb1c3263e778）。Thompson 文集记录了实践者对「functional foremanship」等术语的讨论需求（1914，src-fc8570b0f7ad）。<!-- claim:{M["eight-functions"]} -->

Taylor 的工程决策方法论为「分析→合成→验证」三段式。他记述道分析的目的是「analyzing all of the work in a given trade into its small elements; separating the efficient from the inefficient movements of the workmen」继而合成的目的是「making this time study practically useful by grouping together the proper series of movements」最后验证的目的是「testing the value of the data and tables contained in the book by computing from the book the time it ought to take to build a structure about to be erected」（1912，src-b91d41aca463）。这一方法论在《科学管理原理》中以「准确、精细的动作与时间研究」的形式出现（1911，src-c864253fe201）。<!-- claim:{M["analysis-synthesis"]} --> Taylor 的工作方法体系从 1895 年计件工资制到 1912 年混凝土成本，始终围绕「以科学取代经验法则、以合作取代对抗」的主线展开。
"""

# ── boundaries.md ───────────────────────────────────────────────────
DOCS["boundaries.md"] = f"""\
## Frederick Winslow Taylor · 边界

Taylor 拒绝为其立传，体现了其对个人崇拜的警惕。Copley 记载「It was thoroughly characteristic of Taylor, however, that he refused even to take steps to facilitate the preparation of a biography of himself after he was gone. On at least two occasions it was suggested to him, but his only response was a grimace」（1923，src-3e4f1d3095ea）。Copley 还评价 Taylor 的表达力不足——「He was born a seer, but was not a born sayer」（1923，src-3e4f1d3095ea）。Taylor 作为「实践者先于阐述者」的定位构成了其 persona 的固有边界。<!-- claim:{M["refused-biography"]} -->

Taylor 制在政府工厂的应用面临政治与工会阻力。Thompson 记载 Watertown Arsenal 罢工事件——「In the summer of 1911, the unionized machinists and molders employed at the Watertown Arsenal, where the Taylor system was being developed by Mr. Carl G. Barth, walked out; and on being taken back petitioned that the Labor Committee of Congress investigate the subject」（1914，src-fc8570b0f7ad）。Copley 记载国会通过拨款法案限制 Taylor 制——「In the winter of 1914-15, the Congress of these United States of America attached to all appropriation bills riders especially designed to cripple the Taylor System in the government establishments」（1923，src-3e4f1d3095ea）。<!-- claim:{M["government-limits"]} -->

同代批评者指出 Taylor 制忽视人的因素。Thompson 记录了 Admiral Edwards 的批评——「the Taylor system antagonizes the workmen and neglects the personal equation」（1914，src-fc8570b0f7ad）。Hunt 文集编者承认战后科学管理已从机械问题转向人的问题——「In the few years since the war, the function of the management engineer has amazingly broadened. Not mechanical but human problems are in the foreground」（1924，src-3c4d882aac78）。Taylor 本人在著述中极少正面回应这一批评。<!-- claim:{M["neglects-human"]} -->

同代批评者质疑 Taylor 的「科学」名实之争。Thompson 记录了 Church 的质疑——Taylor「does not show a science」——以及 Admiral Edwards 的批评——「management is an art rather than a science」（1914，src-fc8570b0f7ad）。Copley 引用 Le Chatelier 的评价承认 Taylor 的方法已将机加工从经验提升为「exact science」（1923，src-3e4f1d3095ea）。Taylor 以「科学」命名其体系，但其方法的「科学性」在同时代即受争议。<!-- claim:{M["science-name-debate"]} -->
"""

# ── divergence-map.md ──────────────────────────────────────────────
DOCS["divergence-map.md"] = f"""\
## Frederick Winslow Taylor · 分歧地图

Taylor 自称追求劳资合作，但其在 Midvale 的实践经历与工人激烈对抗。他论述科学管理以「heartily cooperate with the men」为第三原则（1911，src-c864253fe201），但 Copley 记载他本人的法庭证词——「It is a horrid life for any man to live, not to be able to look any workman in the face all day long without seeing hostility there」（1923，src-3e4f1d3095ea）。Taylor 的合作理想与对抗实践之间存在内在张力：合作是目标而非起点，对抗是出发而非终点。<!-- claim:{M["cooperation-vs-conflict"]} -->

同代批评者指出 Taylor 制忽视人的因素。Thompson 记录了 Admiral Edwards 的批评——「the Taylor system antagonizes the workmen and neglects the personal equation」（1914，src-fc8570b0f7ad）。Hunt 文集编者承认战后科学管理已从机械问题转向人的问题——「Not mechanical but human problems are in the foreground」（1924，src-3c4d882aac78）。<!-- claim:{M["neglects-human"]} --> 这一批评指向 Taylor 体系的结构性盲点：他以科学分析的精确性取代了管理中的人际维度。

Taylor 以「雇主与雇员最大繁荣同一性」为管理学的核心价值公理。他写道「the principal object of management should be to secure the maximum prosperity for the employer, coupled with the maximum prosperity for each employe」（1911，src-c864253fe201）。在混凝土成本中，他以工人加薪 30% 以上同时公司获利为这一价值观的实践验证（1912，src-b91d41aca463）。<!-- claim:{M["max-prosperity"]} --> 这一价值公理在理论上自洽，但在实践中面临工会与国会的制度性挑战。

Taylor 的差别计件率制度通过经济激励自动筛选优秀工人。他论述道「It automatically selects and attracts the best men for each class of work」（1896，src-92e733171b0a）。在混凝土成本中，同样的经济逻辑以工人加薪 30% 以上同时公司获利的形式出现（1912，src-b91d41aca463）。<!-- claim:{M["differential-rate"]} --> 然而，这一制度的自动筛选机制在工人与工会看来恰是「加速淘汰」的工具——经济激励与制度阻力在 Taylor 体系中并存。
"""

# ── hypotheses.md ───────────────────────────────────────────────────
DOCS["hypotheses.md"] = f"""\
## Frederick Winslow Taylor · 灵魂假设

Taylor 的根本驱动力可能不是对效率本身的热爱，而是对「秩序」的渴望，源于工厂车间失控的创伤性经历。Copley 记载他「perhaps nine-tenths of Taylor's activities were, from his early youth, devoted to the single object of developing and propagating his system of Scientific Management」（1923，src-3e4f1d3095ea）。<!-- claim:{M["order-drive"]} -->

Taylor 在 Midvale 面临工人完全控制产出节奏的局面——Copley 记载「The management thought it was running the shop, but it really was being run by the men」（1923，src-3e4f1d3095ea）。Taylor 自述这段经历——「I was a young man in years, but I give you my word I was a great deal older than I am now, what with the worry, meanness and contemptibleness of the whole damn thing」（1923，src-3e4f1d3095ea）。这一创伤性经历可能构成了他终生以系统化方法消除车间混乱的深层动力。

这一假设的支撑在于 Taylor 方法迁移的一致性：从 Midvale 的金属切削到建筑行业的混凝土施工，他始终以系统化方法取代经验法则。他在混凝土行业中同样以科学配比取代经验做法——「The method is exact and scientific and not rule-of-thumb」（1905，src-28ad6346694f）。如果 Taylor 的驱动力是对效率的热爱，他的迁移路径应表现出对效率最大化的执着；但如果驱动力是对秩序的渴望，他的迁移路径应表现出对标准化与消除不确定性的执着——后者与他的实际行为更为吻合。

**替代解释**：Taylor 的驱动力可能源于工程效率的最大化追求而非对秩序的心理需求；Taylor 的行为可能更多受职业成就感与发明家本能驱动而非创伤性经历；Taylor 的系统化方法可能是 19 世纪工程教育背景的产物而非个人心理特质。

**证伪条件**：若发现 Taylor 在主要著述或传记中明确表达对效率本身的热爱而非对混乱的排斥，则此假设失效；若 Taylor 的方法迁移中表现出对灵活性和即兴的容忍而非对标准化的执着，则此假设失效。

本假设基于跨多源文本的规律性观察，不构成对 Taylor 心理状态的确定性判断。Copley 传记（1923，src-3e4f1d3095ea）为第三方记述，其引述的 Taylor 法庭证词为二手转述，归属上属「传记记载」而非 Taylor 亲笔。
"""


def main() -> int:
    used = collections.Counter()
    for name, text in DOCS.items():
        (W / name).write_text(text, encoding="utf-8")
        for cid in re.findall(r"<!-- claim:(clm-[0-9a-f]{12}) -->", text):
            used[cid] += 1
        print(f"  ✓ {name:<22} {len(text):>6} 字")
    ids = {c["claim_id"] for c in CL}
    orphan, ghost = sorted(ids - set(used)), sorted(set(used) - ids)
    short = [n for n, t in DOCS.items() if len(t) < 500]
    bad = False
    for label, items in (("孤儿 claim", orphan), ("幽灵锚点", ghost), ("文档过短", short)):
        if items:
            print(f"\n✗ {label} {len(items)}: {items[:6]}")
            bad = True
    if bad:
        return 2
    print(f"\n✓ {len(DOCS)} 份文档；{len(ids)} 条 claim 全部有锚点，无孤儿、无幽灵")
    return 0


if __name__ == "__main__":
    sys.exit(main())
