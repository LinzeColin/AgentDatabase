#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""【脚手架】29–31 条断言的生成器。每人复制一份，只改 S（源 ID 表）与 C（断言元组表）。

## 生成时断言（全部来自实战教训，不要删）

1. **引号内不得含省略号**（RUNBOOK 第二十九种）。
   Maeda 车道初稿有 4 条是 `「片段A... 片段B」`——两片都真，缝起来的那句他没写过。
   需要跳内容就结束引号、用自己的话过渡、再开新引号。
2. **category 必须在 ledger.py 的白名单内**（第 v0.0.0.8 轮实战）。
   只查「mental-model ≥6」这类下限是查了一半——下限可以全绿而每一条 category 都非法。
3. **每条 ≥2 源、≥2 情境**，source_ids 不得重复。
4. **status 是「命题的种类」，不是「我的把握有多大」**（Robertson #97 实战）。
   合法值 `fact | pattern | hypothesis`（`unknown/superseded` 本模板不产出）：
   - `fact` —— 一个具体的、可单点核实的命题（某年某数、他说过某句）
   - `pattern` —— 跨多个场合观察到的**规律**
   - `hypothesis` —— **soul-hypothesis 类别强制用这个**，且必须带 alternative_explanations
   把握大小写在 `confidence`（0..1）里。我曾把四条跨年份的规律标成 `fact`，
   本意是「证据很硬」，结果**门直接判为不合格**——见下一条。
5. **门数的是「category ∧ status == 'pattern'」，不是数 category。**
   `quality_check.py:185` 的口径是
   `category in {'mental-model'} and status == 'pattern'`，阈值 `min_models: 4`。
   本模板旧版只断言 `Counter(category)['mental-model'] >= 6`，
   于是 Robertson #97 出现：**模板全绿（6 条），门报 `mental models 2 < 4`。**
   前几位人物没暴露，纯粹因为他们的 mental-model 恰好多数标了 pattern。
   **下限断言必须与门同口径，否则它保证的是另一件事。**
6. **soul-hypothesis 只许出现在 `hypotheses.md`。** 门有 `claim.hypothesis-escaped`，
   在 persona.md 里锚一次就会失败。

## 写断言时的五条纪律

1. **不做没数过的枚举**：计数一律给分子/分母，不写「只有」「多数」。
2. **不替他补理由**：只给了做法而没给理由的，如实写「他没给理由」（第十七种）。
   Salatin 一轮我给他补过一个「听起来合理」的理由，事后证明是我编的。
3. **归属分层**：他转述他人的材料，里面的主张**不属于他**。
   Maeda 一轮的 `Learnings from Neon` 那套 JTBD 工具设计法是 Neon 的，不是他的。
   归因错误比措辞错误严重得多。
4. **自述 ≠ 事实**：语料若无第三方材料，他讲的经历一律标「他自述」，status 不得给 fact。
5. **过度断言必查**：凡带「从不 / 唯一 / 没有一句」的，逐条去语料找反例。
   Maeda 一轮三条这类断言全部被反例证伪（「无任职起止」「操作文档没有一句为什么」
   「HOW 是唯一可控」）。**有分母有判据的就是事实断言，必须核。**
"""
import collections, json, pathlib, sys
from datetime import datetime, timezone

NOW = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
OUT = pathlib.Path(__file__).resolve().parent.parent / "evidence/claims.jsonl"  # ← 改

CATEGORIES = ("fact", "mental-model", "heuristic", "value", "epistemic", "expression",
              "lineage", "blind-spot", "contradiction", "work-method", "boundary",
              "soul-hypothesis")            # 抄自 scripts/ledger.py，不要凭记忆写

S = {
    "HIST": "src-dc603260fff5",        # The History and Progress of Metallurgical Science (1923)
    "CHEMIST": "src-9d9f22cec4f5",     # The Work and Position of the Metallurgical Chemist (1922)
    "METALLURGY": "src-f94b66599392",  # Metallurgy and Its Influence on Modern Progress (1925)
    "SHORTER": "src-63800b6e6147",     # A Shorter Working Day (1892, 与 H. de B. Gibbins 合著)
    "MAGNETIC": "src-b558bfde4e73",    # The Magnetic Mechanical Analysis of Manganese Steel (1920)
    "CORROSION": "src-db7d79db2c67",   # The Corrosion of Iron and Steel (1922)
    "WARD": "src-abb82d8164df",        # Elijah Ward of New York (1877, 冶金企业家传记)
    "MANGANESE": "src-24261c5726ef",   # Hadfield's Manganese Steel (1888, Joseph D. Weeks 转述)
}

# (category, 适用标签, 断言正文, [源别名], [情境≥2], [证伪条件], status, confidence, 时间范围)
#   soul-hypothesis 多给一项：末尾追加 [替代解释…]（门强制要求，见文件头第 6 条）
C = [
    # ── fact：可单点核实的具体命题（锰钢、Faraday、腐蚀损失、1888 论文）──
    ("fact", "水韧化",
     "锰钢经水淬（水韧化）后强度与延性同时大幅提升：第三方转述记录 14% 锰试棒抗拉强度由 36 吨/平方英寸升至 67 吨、延伸率由 1.56% 升至 44.44% 且未断裂，并把该过程命名为「water-toughening」；他在 1925 年著作中自述这是他的发现，称锰钢被水淬「韧化」而非如碳钢般「硬化」。",
     ["MANGANESE", "METALLURGY"],
     ["在 1888 年第三方转述 Weeks 对锰钢论文的摘录中", "在 1925 年《Metallurgy and Its Influence》论锰钢水淬热处理处"],
     "若语料中水韧化前后的强度/延伸率数字与 36→67 吨、1.56%→44.44% 不符，或水淬被描述为硬化而非韧化，本条作废。",
     "fact", 0.9, "1882–1925"),
    ("fact", "非磁性",
     "锰钢含锰较高时几乎无磁：第三方转述记录约 8% 锰时体材已不被磁铁吸引、20% 锰时能举 30 磅铁的铁磁铁只吸起几毫克细屑，并把普通铁的磁性记作 100,000 而锰钢为 20；他在 1925 年著作中亦称锰钢磁导率「exceedingly low, practically unity」。",
     ["MANGANESE", "METALLURGY"],
     ["在 1888 年第三方转述论锰钢电学性质处", "在 1925 年著作论合金钢与电气工程处"],
     "若语料把锰钢描述为磁性材料或磁导率接近铁，本条作废。",
     "fact", 0.9, "1888–1925"),
    ("fact", "耐磨高强",
     "锰钢以耐磨与高强著称：第三方转述记录 14% 锰试棒在双齿轮 18 英寸钻床下钻一个半英寸直径、四分之三英寸深的孔耗时一小时以上，而同样时间在低碳钢上可钻十五到二十个同尺寸孔；他在 1925 年著作中称「1 ton of manganese steel will do the work of about 10 tons of ordinary iron or steel」。",
     ["MANGANESE", "METALLURGY"],
     ["在 1888 年第三方转述的硬度测试记录中", "在 1925 年著作论合金钢节约铁料处"],
     "若语料显示锰钢易加工、寿命不比普通钢长，本条作废。",
     "fact", 0.9, "1888–1925"),
    ("fact", "1888论文",
     "他自述 1888 年在土木工程师学会（Institution of Civil Engineers）宣读首篇锰钢论文，此后已向国内外科学与技术学会提交 139 篇论文；1925 年著作亦称锰钢论文在 1888 年 2 月宣读与讨论，是合金钢系统研究的开端。",
     ["HIST", "METALLURGY"],
     ["在 1923 年致辞开场自述论文数量处", "在 1925 年著作论锰钢发现历史处"],
     "若语料显示锰钢论文并非 1888 年由他在土木工程师学会宣读，本条作废。",
     "fact", 0.85, "1888–1923"),
    ("fact", "腐蚀损失",
     "他在 1922 年皇家学会腐蚀论文中估算每年因腐蚀而报废的铁与钢超过 4000 万吨、合计年损失可能超过 5 亿英镑；1925 年著作的图表亦显示 1921 年因腐蚀报废的铁钢量几乎等于当年估算的生铁产量。",
     ["CORROSION", "METALLURGY"],
     ["在 1922 年《The Corrosion of Iron and Steel》引言中", "在 1925 年著作论铁料节约与腐蚀浪费处"],
     "若语料没有 4000 万吨或 5 亿英镑的估算，或未把腐蚀报废量与产量并列，本条作废。",
     "fact", 0.9, "1921–1925"),
    ("fact", "法拉第合金",
     "他在 1925 年著作中记述 Faraday 1821 年即从事钢合金研究，并称其为「probably the greatest experimental philosopher」；1923 年致辞亦称 Faraday 的早年记录显示其「master mind」也曾被铁合金方向吸引。",
     ["METALLURGY", "HIST"],
     ["在 1925 年著作的 Faraday 传记段落中", "在 1923 年致辞论 Percy 与 Faraday 处"],
     "若语料没有 Faraday 从事铁或钢合金实验的记述，本条作废。",
     "fact", 0.9, "1821–1925"),

    # ── mental-model（status 一律 pattern，与门同口径 ≥6）──
    ("mental-model", "反常数据",
     "他反复把「本应失败或反常」的数据当作新材料的线索：Terre Noire 公司因 2.5% 锰即脆而停止系列并错误地以为再加锰只会更糟，而他恰恰通过研究更高锰含量的合金发现物理性能发生根本变化；第三方转述也把「锰增 4% 引起强度与延性同时大升」列为需要特别注意的反常事实。",
     ["METALLURGY", "MANGANESE"],
     ["在 1925 年著作述 Terre Noire 史与「新纪元」处", "在 1888 年第三方转述论 12-14% 锰最优区间处"],
     "若语料显示他因循守旧、拒绝突破前人的锰含量界限，本条作废。",
     "pattern", 0.8, "1882–1925"),
    ("mental-model", "材料决定工程",
     "他持「材料性质决定工程进步」的心智模型：认为工程科学只进步到可用材料性质所允许的程度，材料改进后工程实践随即跟进；1923 年致辞的整体框架正是冶金科学及其对现代工程的影响。",
     ["METALLURGY", "HIST"],
     ["在 1925 年著作论合金钢重要性开篇", "在 1923 年致辞「冶金→现代工程」的框架中"],
     "若语料显示他认为工程需求独立于材料、材料进步只是附带，本条作废。",
     "pattern", 0.75, "1923–1925"),
    ("mental-model", "科学实用并重",
     "他给自己的研究预设「既科学又实用」的双重标准：腐蚀论文开篇即称希望结果「从科学和实用两个角度」增进知识；合金钢重要性论述也同时强调新物理性质与实际工程价值。",
     ["CORROSION", "METALLURGY"],
     ["在 1922 年腐蚀论文引言中", "在 1925 年著作论合金钢价值处"],
     "若语料显示他只追求纯科学或纯商业之一端，本条作废。",
     "pattern", 0.8, "1922–1925"),
    ("mental-model", "档案记录",
     "他把「记录与档案」当作知识积累的基础：既收藏约三百册自 1400 年以来的冶金古籍并列出主要作者谱系，又把 1882 年以来的化验与实验笔记本视为可回查的资产。",
     ["METALLURGY", "CHEMIST"],
     ["在 1925 年著作述冶金藏书与作者谱系处", "在 1922 年演讲回查实验室笔记本处"],
     "若语料显示他不收藏文献、也不保存实验记录，本条作废。",
     "pattern", 0.8, "1882–1925"),
    ("mental-model", "磁性表征",
     "他相信通过磁性行为能读出材料内部状态：1920 年磁力-机械分析的目标是从锰钢的磁性行为解释其机械性能，并沿 Joule 与 Villari 这对互逆效应建立「磁-机分析」方法；更早的第三方转述也记录 Ewing 用磁测表征锰钢磁导率近似恒定。",
     ["MAGNETIC", "MANGANESE"],
     ["在 1920 年磁力-机械分析论文的方法与结论中", "在 1888 年第三方转述对 Ewing 磁测实验的记录中"],
     "若语料显示他否认磁性测量与机械性能的关联，本条作废。",
     "pattern", 0.8, "1888–1920"),
    ("mental-model", "冶金史谱系",
     "他把冶金史理解为一条由先贤累积的谱系并将自己放进其中：1923 年致辞称 Percy 与 Faraday 的早期研究「已成熟为对全世界的巨大益处」、他因在同一方向工作而感到「不小的满足与鼓舞」；1925 年著作则把 Agricola、Dud Dudley、Percy、Bessemer 等列为谱系节点。",
     ["HIST", "METALLURGY"],
     ["在 1923 年致辞论 Percy/Faraday 处", "在 1925 年著作的冶金史谱系列表中"],
     "若语料显示他把自己视为冶金传统的局外人或断代者，本条作废。",
     "pattern", 0.85, "1923–1925"),

    # ── heuristic（status 一律 pattern，与门同口径 ≥8）──
    ("heuristic", "对照实验",
     "他设计实验时重视「只变一个变量」的对照：1920 年选取同一化学成分、仅热处理不同的两根锰钢棒对比磁性与机械性能；第三方转述也记录了同成分试棒在不同冷却水温（72°F 与 202°F）下的强度延性对比，并把差异归因于冷却快慢而非成分。",
     ["MAGNETIC", "MANGANESE"],
     ["在 1920 年磁力-机械分析的材料与方法中", "在 1888 年第三方转述的水淬温度对比实验中"],
     "若语料显示他在对照实验中同时改变多个变量，本条作废。",
     "pattern", 0.8, "1888–1920"),
    ("heuristic", "量级估算",
     "他习惯先用全球量级估算把问题量化，再落成产业主张：腐蚀论文用每年超过 4000 万吨报废与超 5 亿英镑损失来论证「应鼓励发展耐腐蚀合金钢」；1925 年著作也用世界生铁产量与腐蚀报废量的并列来说明问题的规模。",
     ["CORROSION", "METALLURGY"],
     ["在 1922 年腐蚀论文引言与结论中", "在 1925 年著作论铁料节约与图 2 处"],
     "若语料显示他从不做量级估算、只谈具体个案，本条作废。",
     "pattern", 0.75, "1922–1925"),
    ("heuristic", "权威背书",
     "他为确立锰钢的历史地位而援引权威与实物证据：1925 年著作汇编「世界上许多一流冶金学家」的评价（Osmond、Pourcel、Stead 等），把水韧化发现与碳钢淬火的发现等量齐观；1922 年演讲则当众展示 Bessemer 1897 年写给他的亲笔信。",
     ["METALLURGY", "CHEMIST"],
     ["在 1925 年著作汇编冶金学家评价处", "在 1922 年演讲展示 Bessemer 信件处"],
     "若语料显示他从不引用他人评价、只凭自家数据，本条作废。",
     "pattern", 0.8, "1897–1925"),
    ("heuristic", "自家工厂实验",
     "他主张并用自家企业做实验来验证主张：缩短工时论著用 Hadfield's Steel Foundry 450-500 名工人的实测数据论证工时缩短不损产量；1925 年著作也提到他正与其公司合作进行多项高温合金研究。",
     ["SHORTER", "METALLURGY"],
     ["在 1892 年《A Shorter Working Day》第七章哈氏铸钢厂实测中", "在 1925 年著作论高温合金研究处"],
     "若语料显示他只用外部数据、从不以自己的工厂为试验场，本条作废。",
     "pattern", 0.8, "1892–1925"),
    ("heuristic", "文献先例",
     "他研究前先读历史文献与先例来定位工作：1923 年致辞称他最早的冶金学研究来自 Percy 的著作，并被 Percy 著作与 Terre Noire 公司 1878 年巴黎展品资料所激励；1925 年著作也记录他年轻时把 Terre Noire 公司四十页小册子全文译出。",
     ["HIST", "METALLURGY"],
     ["在 1923 年致辞论 Percy 著作影响处", "在 1925 年著作述「新纪元」的 Terre Noire 翻译处"],
     "若语料显示他的研究不参考任何前人著作，本条作废。",
     "pattern", 0.8, "1878–1925"),
    ("heuristic", "经济账",
     "他习惯用成本与效益账说服人：缩短工时论著的核心论据是「减少工时实际上并未增加生产成本」且工人守时率上升；合金钢论述则用「1 吨锰钢抵 10 吨普通钢」说明节约换件与停机成本。",
     ["SHORTER", "METALLURGY"],
     ["在 1892 年《A Shorter Working Day》的实测结果总结中", "在 1925 年著作论合金钢节约铁料处"],
     "若语料显示他论证从不涉及成本或经济性，本条作废。",
     "pattern", 0.8, "1892–1925"),
    ("heuristic", "激励后辈",
     "他惯于用成就与示范激励后辈：1925 年著作称「过去的成就应鼓励年轻人再作努力」，并以自己在合金钢研究上「先知」般的预判作示范；1922 年演讲则主张帝国各阶层公民都应有听化学物理讲座、看演示的机会。",
     ["METALLURGY", "CHEMIST"],
     ["在 1925 年著作论合金钢未来处", "在 1922 年演讲论科学普及处"],
     "若语料显示他对后辈保守、不鼓励科普，本条作废。",
     "pattern", 0.75, "1922–1925"),
    ("heuristic", "诚实弃权",
     "当机制解释不明时他如实说「不清楚」而不编造理由：第三方转述的锰钢水韧化讨论直言「The cause of this is very obscure」；腐蚀论文也承认铜改善耐蚀的机制「at present little understood and difficult to investigate」并称正在继续研究。",
     ["MANGANESE", "CORROSION"],
     ["在 1888 年第三方转述论水韧化机制处", "在 1922 年腐蚀论文论铜作用机制处"],
     "若语料显示他在机制不明时给出确凿解释，本条作废。",
     "pattern", 0.85, "1888–1922"),

    # ── value ──
    ("value", "爱国",
     "他珍视并自豪于英国的工业与帝国传统：1923 年致辞称帝国的经历必须永远铭记，本国制造与工业中心在一战中「nobly did their utmost」；1925 年著作强调英国工作者「not been idle」。",
     ["HIST", "METALLURGY"],
     ["在 1923 年致辞「战时工作」段落中", "在 1925 年著作论英国冶金贡献处"],
     "若语料显示他对英国工业传统无自豪感，本条作废。",
     "pattern", 0.85, "1923–1925"),
    ("value", "分析诚实",
     "他把化学分析的绝对精确与诚实视为职业底线：1922 年演讲称「figures 不可做假、精确必须至高无上」，并自豪地说数以十万计的分析结果中从未见过一份不诚实的；1920 年磁测论文也强调实验操作上避免感应误差的必要。",
     ["CHEMIST", "MAGNETIC"],
     ["在 1922 年冶金化学家演讲论分析纪律处", "在 1920 年磁力-机械分析论实验装置设计处"],
     "若语料显示他允许凑数或对不精确数据无所谓，本条作废。",
     "pattern", 0.85, "1920–1922"),

    # ── epistemic ──
    ("epistemic", "证实与推测",
     "他在表述中注意区分「已证实」与「推测」：第三方转述记录他把 12-14% 锰最优区间的机制解释明确标为「This is only surmise」；腐蚀论文对含铜钢在海水等长期暴露下的效益也说是否会被抹平甚至反转「尚不确定」。",
     ["MANGANESE", "CORROSION"],
     ["在 1888 年第三方转述论锰钢结晶机制处", "在 1922 年腐蚀论文论海水暴露与谨慎结论处"],
     "若语料显示他把推测当作定论陈述，本条作废。",
     "pattern", 0.8, "1888–1922"),

    # ── expression ──
    ("expression", "致辞体",
     "他的书面语言是正式、庄重的维多利亚-爱德华时代致辞体：频繁致谢与谦辞（「beg you to pardon my shortcomings」）、多用敬称与历史引文（Milton、Gladstone 等），并以「满足与鼓舞」一类情感措辞表达对先贤与同侪的敬意。",
     ["HIST", "CHEMIST"],
     ["在 1923 年致辞的开场与结尾中", "在 1922 年演讲的开场与致谢中"],
     "若语料显示他的语言简洁口语、无敬语无引文，本条作废。",
     "pattern", 0.7, "1922–1923"),

    # ── lineage ──
    ("lineage", "智识先辈",
     "他把 Percy 与 Faraday 视为自己研究方向的智识先辈：1923 年致辞称 Percy 是「我们时代著名冶金学家之一」、他最早的冶金研究来自 Percy 的著作，并把 Faraday 与 Percy 的早期研究并列为激励他的「两位伟人」。",
     ["HIST", "METALLURGY"],
     ["在 1923 年致辞的 Percy 传记段落中", "在 1925 年著作的冶金史谱系中"],
     "若语料显示他把 Percy 或 Faraday 视作无关紧要者，本条作废。",
     "pattern", 0.85, "1923–1925"),

    # ── blind-spot ──
    ("blind-spot", "发明归属",
     "他对锰钢发明归属的叙述有自我辩护的痕迹：他自己反复强调 1882 年 9 月 7 日实验笔记本的原始条目与「22 岁青年的预言」，而 1888 年第三方转述 Weeks 却明确称锰钢是「其父的发明」、他只是「大力完善」者——两条叙事并存，而他的文本从未正面回应父发明说。",
     ["METALLURGY", "MANGANESE"],
     ["在 1925 年著作引实验笔记本条目处", "在 1888 年第三方转述 Weeks 的开篇定性处"],
     "若语料显示他主动承认并归功于父亲的发明，本条作废。",
     "pattern", 0.75, "1888–1925"),
    ("blind-spot", "循环确证",
     "他引用「世界一流冶金学家的评价」来确证锰钢地位时，部分评价本身以他的论文为基础（第三方转述明确说「经他允许，我们从其论文中大段引用」），存在把自我陈述当独立确证的循环风险。",
     ["MANGANESE", "METALLURGY"],
     ["在 1888 年第三方转述的引用说明中", "在 1925 年著作汇编冶金学家评价处"],
     "若语料显示他所引评价完全独立于他的论文与陈述，本条作废。",
     "pattern", 0.6, "1888–1925"),

    # ── contradiction ──
    ("contradiction", "精确与估算",
     "他的主张存在「绝对精确」理想与「工程估算」现实之间的张力：1922 年演讲宣称分析「figures 不可做假、精确必须至高无上」，同年腐蚀论文却用「careful estimates appear to show」这样宽泛的估算给出 4000 万吨与 5 亿英镑的腐蚀损失数字。",
     ["CHEMIST", "CORROSION"],
     ["在 1922 年冶金化学家演讲论分析纪律处", "在 1922 年腐蚀论文的损失估算处"],
     "若语料显示腐蚀损失数字同样来自精确测量而非估算，本条作废。",
     "pattern", 0.65, "1922"),

    # ── work-method ──
    ("work-method", "实验笔记",
     "他系统保存实验与化验记录：1922 年自述化验与实验笔记可追溯至 1882 年且至今无误，1925 年著作则直接引用 1882 年 9 月 7 日实验笔记本的原始条目来支撑锰钢发明叙事。",
     ["CHEMIST", "METALLURGY"],
     ["在 1922 年演讲回查笔记本处", "在 1925 年著作引笔记本条目处"],
     "若语料显示他无记录习惯或记录不可追溯，本条作废。",
     "pattern", 0.85, "1882–1925"),

    # ── boundary ──
    ("boundary", "身份边界",
     "他明确划定自己的专业边界：1925 年著作称作为冶金学家「不属于他的职责范围」去长篇讨论电气工程进展，只在合金钢对电气应用的意义上发言；1922 年演讲也承认一门致辞无法覆盖所有科学分支。",
     ["METALLURGY", "CHEMIST"],
     ["在 1925 年著作论合金钢与电气工程处", "在 1922 年演讲开场论覆盖范围处"],
     "若语料显示他声称自己是电学或电气工程权威，本条作废。",
     "pattern", 0.8, "1922–1925"),

    # ── soul-hypothesis（唯一允许 status=hypothesis 的条目）──
    ("soul-hypothesis", "灵魂假设",
     "驱动他一生工作的深层动机，最可能是作为「第二代工业家-科学家」的自我完成：他把自己理解为承接 Percy 与 Faraday 的冶金谱系、并为它补上英国工业实际应用一章的接力者——既要用锰钢与合金钢证明自己配得上父亲建立的钢铁事业，又要用冶金史写作在历史上留下自己的位置。",
     ["HIST", "METALLURGY"],
     ["在 1923 年致辞的 Percy/Faraday 谱系段落中", "在 1925 年著作的锰钢发明叙事中"],
     "若语料显示他完全出于商业利益或纯好奇、没有任何谱系与传承意识，本条作废。",
     "hypothesis", 0.6, "1882–1925",
     ["替代解释一：主要是商业与产业竞争驱动，科学史与爱国表述只是对外公关的外衣。",
      "替代解释二：主要是纯粹科学好奇心驱动，工业家身份只是其外部载体。",
      "替代解释三：主要是自我确证驱动——要摆脱「父亲发明、他完善」的标签，证明自己是原创者。"]),
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
    #    数 category 会在门报错的同一份数据上显示全绿——Robertson #97 实测 6 vs 2。
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
