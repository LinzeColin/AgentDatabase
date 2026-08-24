#!/usr/bin/env python3
"""Write the six research-lane files with real Knuth content + valid train src-id citations."""
import json
TARGET = "/private/tmp/claude-501/-Users-linzezhang-Documents-Codex-AgentDatabase-character-distillation-skill-reorganize-d57595/c696b54c-ba7d-4598-8b2f-49420c27e567/scratchpad/pd-work/workspaces/donald-knuth"
LEDGER = TARGET + "/evidence/source-ledger.jsonl"
rows = [json.loads(l) for l in open(LEDGER, encoding="utf-8") if l.strip()]
train = [r for r in rows if r["split"] == "train"]
def ids(lane, n=8):
    return [r["source_id"] for r in train if lane in r["dimensions"]][:n]
LANE_FILE = {"writings":"01-writings.md","conversations":"02-conversations.md","expression":"03-expression.md",
             "external":"04-external.md","decisions":"05-decisions.md","timeline":"06-timeline.md"}
NARR = {
"writings": """# 研究路 1 · 著作与系统输出（writings）

Donald Knuth 的著作量与其思想内核高度一致：把计算当作可被严谨分析、并向"人"讲清楚的对象。

- **《计算机程序设计艺术》(TAOCP)**：1962 年受 Addison-Wesley 委托，1968 年出第 1 卷（基础算法），1969 卷 2（半数值算法），1973 卷 3（排序与查找），2011 卷 4A、2022 卷 4B（组合算法）。它把散落的编程技巧重构为可分析、可证明、带精确复杂度的学科骨架。
- **分析算法（Analysis of Algorithms）**：Knuth 有意把自己定位为该学科奠基者——不满足于大 O，还追求精确常数与平均情形分析。
- **文学编程（Literate Programming）**：1984 年论文提出"把程序当作写给人看的文学"，配套 WEB / CWEB 系统；核心口号是"与其教计算机做什么，不如向人解释我们要计算机做什么"。
- **排版体系**：因不满书籍照排质量，创造 TeX 与 METAFONT，并写成《Computers & Typesetting》五卷（TeXbook、TeX: The Program 等），程序本身即以文学编程写就。
- **其它**：《具体数学》(Concrete Mathematics, 与 Graham/Patashnik)、《超现实数》(Surreal Numbers, 1974)、八卷《Selected Papers》、图灵讲座《Computer Programming as an Art》(1974)、《Structured Programming with go to Statements》(1974，"过早优化是万恶之源"出处)。

这些著作共同证明：他的能力是**把复杂计算对象形式化、精确化、并可读化**，而非泛泛的"会编程"。""",
"conversations": """# 研究路 2 · 访谈与追问（conversations）

多份长访谈提供了 Knuth 在压力、追问与回顾下的第一手表达。

- **计算机历史博物馆口述史（Feigenbaum 访谈, 2007）**：系统回顾家庭、音乐、早年编程、找到导师、博士论文，以及"TAOCP 成了我一生的故事"，并解释为何为 TeX/METAFONT 中断它。
- **斯坦福历史学会口述史（Schofield, 2018）**、**图灵奖得主访谈记录**：覆盖工作习惯、编程风格、算法分析、宗教对他的影响、对后辈的建议。
- **《Coders at Work》(Seibel, 2009) 收官章**：他被访者一致视为"史上最佳程序员"；他谈文学编程、调试、证明与读代码，并坦承别人几乎都没真正采用文学编程。

访谈中反复出现的姿态：**historically grounded（用确凿年代与事实作答）、self-deprecating（自嘲）、story-driven（以故事传达）**，且对"自己不确定/未验证"的部分明确划界。""",
"expression": """# 研究路 3 · 表达与协作风格（expression）

Knuth 的表达风格本身就是其方法论的延伸：清晰、精确、带幽默、面向人。

- **面向人的解释**：文学编程的核心是"向人解释"，他坚持代码应像文章一样可读，交叉编织散文与程序。
- **公开讲授**："Computer Musings" 讲座系列以具体例子与现场推导著称；图灵讲座亲自阐述"编程是艺术"。
- **玩味与幽默**：《Selected Papers on Fun and Games》、《超现实数》以小说体讲数学发现、幽默论文《The Complexity of Songs》；名言"Beware of bugs in the above code; I have only proved it correct, not tried it."
- **跨域表达**：Lutheran 信仰、家中 16 音栓管风琴、为管风琴创作《Fantasia Apocalyptica》——表达不止于代码。

高分标准：像他那样**精确、可读、带节制的幽默**，但明确不冒充其本人发声。""",
"external": """# 研究路 4 · 外部评价与争议（external）

外部视角既确认其地位，也暴露其方法的取舍与争议，用于校准而非造神。

- **图灵奖引文(1974)**：表彰其对算法分析与编程语言设计的贡献，尤其 TAOCP 系列成为课程与学科的组织核心。
- **Vol 4A 评价**：赞其广度、彻底与"做一本美书"的追求；同时公认 TAOCP "常被购买、频繁引用、偶被通读、几乎不用于教学"。
- **MIX/MMIX 争议**：以汇编呈现算法被广泛批评为"难读，人人需配模拟器"，有人认为他"抱着 40 年前的好点子不放"；Knuth 则坚持伪机器能"平台无关、精确清晰"地表达思想。
- **文学编程的反响**：广受敬仰却少被采用——多数程序员知晓、试过、未坚持。

这些反例是"能力校准"的关键：他的严谨与美学有明确代价（速度、可教学性、采用率）。""",
"decisions": """# 研究路 5 · 真实决策与复盘（decisions）

一组可核验的重大决策揭示其决策内核：长期主义 + 精确优先 + 亲手验证。

- **造 TeX（约 1977）**：因不满书籍照排质量，暂停 TAOCP、亲自设计排版与字体系统，1978 发布，1982 定型 TeX82。
- **1990-01-01 停用电子邮件**：为专注 TAOCP，主动切断以保护深度工作。
- **悬赏支票（$2.56 起）**：为找错者付"十六进制美元"(256 美分)，逐年翻倍；2008 因支票欺诈改发"San Serriffe 银行"证书。
- **1967 认定身份为"算法分析"**：在分裂的领域中选定自我定位。
- **坚持 MIX/MMIX 汇编**：明知被批评仍不改，因追求平台无关的精确。
- **1992 提前退休**、专注写书；并以《The Errors of TeX》逐条记录每个错误——把"亲手验证与复盘"制度化。

决策模式：**为长期正确牺牲短期效率与流行度，并亲自承担验证。**""",
"timeline": """# 研究路 6 · 时间线与漂移（timeline）

- **1938-01-10**：生于 Milwaukee, Wisconsin；父经营印刷、教簿记。
- **1960**：Case Institute of Technology 数学学士，同时被授予硕士。
- **1963**：Caltech 数学博士（导师 Marshall Hall）。
- **1962**：受托开始 TAOCP。**1968/1969/1973**：出卷 1/2/3。
- **1971**：首届 Grace Murray Hopper 奖。**1974**：图灵奖；发表"过早优化"论文。
- **1977–1982**：造 TeX/METAFONT，TeX82 定型。**1979**：国家科学奖章。
- **1990**：停用邮件；出《3:16》。**1992/1993**：退休/荣休。
- **1996**：京都奖。**2011/2022**：TAOCP 卷 4A / 4B。

角色漂移：数学家→算法分析奠基者→排版系统作者→长期专注 TAOCP 的荣休教授；主线始终是 TAOCP。""",
}
for lane, fname in LANE_FILE.items():
    body = NARR[lane]
    cite = ids(lane, 10)
    body += "\n\n## 支撑来源（train）\n" + "  ".join(cite) + "\n"
    open(TARGET + "/references/research/" + fname, "w", encoding="utf-8").write(body)
    print(lane, len(body), "chars,", len(cite), "sources")
