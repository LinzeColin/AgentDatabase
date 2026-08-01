#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Jesse Livermore #100 的断言生成器。

## 本人物的三条硬纪律（写在这里，改动时先读）

1. **凡引号内的英文原句，必须逐字来自 P1／P2 语料**。
   那本书的扫描件含 1284 个西里尔同形字，**取引文只从 OCR 干净的段落取**
   （第 I、II 章干净；第 VI、VII、IX 章脏）。
2. **≥2 个来源、≥2 个语境、≥2 个证据簇** 是门的要求，不是建议。
   本人物 writings 路只有一个来源（那本书），因此**方法类断言必须由
   「书 + 同期报道／直引」交叉支撑**，不许拿同一本书的两章冒充两个来源。
3. **Lefèvre 小说的任何一句都不得进来。** 它是虚构作品，主角是 Larry Livingston。
"""
import hashlib
import json
import pathlib
import sys

BOOK = "src-78d1f7f3fb9a"          # 1940 年那本书的 train 卷（P1）
DIES = "src-882ba94037cc"          # 该书前言，作者 Edward Jerome Dies（S1）
C08 = "src-da0a248f8373"           # 1908-05-15 棉花当日访谈
C10 = "src-ac61de64d9b8"           # 1910-08-20 生活底线
C22 = "src-6249b3b2fda8"           # 1922-10-16 「我不是赌徒」
C23F = "src-37079117c522"          # 1923-02-05 铁路 / 图表派
C23A = "src-3a37950cd1ec"          # 1923-11-13 购买力（阿肯色）
C23G = "src-36749b47813c"          # 1923-11-13 同一通稿（佐治亚）
C23S = "src-40e2c4076059"          # 1923-12-21 参议院宣誓证词
C24 = "src-b6b01f04cda0"           # 1924-02-22 「It was bad judgment.」
C32 = "src-995ce3754fc9"           # 1932-10-05 债务已全额清偿
C34A = "src-7d64414ec450"          # 1934-04-18 「我欠过很多次」
C34J = "src-c4277b744fe3"          # 1934-06-28 「打算重新开始」
C40S = "src-3d772e864171"          # 1940-09-22 最后一次市场评论
C40O = "src-926f422246c5"          # 1940-11-29 讣闻
C40N = "src-5bcee03a75f1"          # 1940-11-29 遗书

NOW = "2026-08-01T00:00:00Z"
SCOPE = "1898–1940（语料覆盖区间；33 年里只有 8 年有本人直引，其余 25 年没有）"

C = []


SLUGS = {}


def cid_of(slug: str) -> str:
    """claim_id 必须是 `clm-` + 12 位十六进制——`markdown_claim_markers()` 的
    正则写死了 `clm-[a-f0-9]{12}`，人读的 `clm-jl-mm-01` 一个也匹配不上，
    渲染文档里的标记会被判成「未知 Claim」。
    由稳定的语义 slug 派生，**同一条断言在任何一次重生成里 id 都不变**。"""
    h = hashlib.sha256(("livermore-100/" + slug).encode("utf-8")).hexdigest()[:12]
    out = "clm-" + h
    assert slug not in SLUGS, f"slug 重复：{slug}"
    SLUGS[slug] = out
    return out


def add(slug, claim, category, status, sources, contexts, clusters,
        confidence, falsifiers=None, alts=None, applicability=None):
    cid = cid_of(slug)
    rec = {
        "claim_id": cid, "claim": claim, "category": category, "status": status,
        "source_ids": sources, "counter_source_ids": [], "contexts": contexts,
        "evidence_clusters": clusters, "confidence": confidence,
        "time_scope": SCOPE, "created_at": NOW, "author_role": "distiller",
    }
    if falsifiers:
        rec["falsifiers"] = falsifiers
    if alts:
        rec["alternative_explanations"] = alts
    if applicability:
        rec["applicability"] = applicability
    C.append(rec)


# ── 心智模型（deep 要 ≥4 条 status=pattern）──────────────────────────
add("clm-jl-mm-01",
    "他把「市场是否已经确认我的判断」当作行动的前提，而不是把「我的判断是否正确」当作前提。"
    "书中原话：「Markets are never wrong—opinions often are.」并进一步要求"
    "「don't trust your own opinion and back your judgment until the action of the market "
    "itself confirms your opinion」。1908 年棉花一役他对记者的当场陈述与此一致："
    "了结持仓后他明言转入观望（该句在扫描件中 OCR 受损，故不作逐字引用），而不是继续按原判断加码。",
    "mental-model", "pattern", [BOOK, C08],
    ["1940 年著述中的原则陈述", "1908 年棉花交易当日的对外说明"],
    ["本人署名专著（P1）", "同期报纸直引（P2）"], 0.82,
    falsifiers=["若语料中出现他在市场未确认时按个人判断加码并以此自辩的记载，本条降级",
                "若「Markets are never wrong」一句被查明并非出自该书正文，本条作废"])

add("clm-jl-mm-02",
    "他把「利润」与「亏损」视为**性质不同**的两件事，而非同一坐标轴的正负两端："
    "「Profits always take care of themselves, but losses never do.」"
    "由此推出的行动是不对称的——有利润时要求耐心持有，有亏损时要求立即了结。"
    "1932 年他对外陈述还债时同样把「我的错误」单列计价（「one of them cost me $2,000,000」），"
    "而不是并入盈亏总账。",
    "mental-model", "pattern", [BOOK, C32],
    ["1940 年著述中的持仓原则", "1932 年对外说明债务与错误"],
    ["本人署名专著（P1）", "同期报纸直引（P2）"], 0.80,
    falsifiers=["若书中同时主张对利润与亏损采取对称处置，本条降级",
                "若能证明该句为编者添加而非其本人所写，本条作废"])

add("clm-jl-mm-03",
    "他把投机看作**一门需要专门学习的生意**，而不是运气或赌博："
    "「Anyone who is inclined to speculate should look at speculation as a business and "
    "treat it as such and not regard it as a pure gamble」。"
    "这一自我界定在 1922 年的对外表述中是同一句话的口语版："
    "「I am not a gambler. I am a speculative investor.」",
    "mental-model", "pattern", [BOOK, C22],
    ["1940 年著述中的立场陈述", "1922 年接受采访时的身份自述"],
    ["本人署名专著（P1）", "同期报纸直引（P2）"], 0.86,
    falsifiers=["若语料中出现他自称赌徒或以运气解释自己成果的直引，本条降级"])

add("clm-jl-mm-04",
    "他认为**人本身是这门生意里最大的变量**，且这个变量对他自己同样成立："
    "「the human side of every person is the greatest enemy of the average investor or "
    "speculator」，而谈到自己时用的是同一套词："
    "「I am human and subject to human weaknesses.」"
    "1924 年他对棉花失利的公开定性「It was bad judgment.」是同一归因方式的对外版本。",
    "mental-model", "pattern", [BOOK, C24],
    ["1940 年著述中的通则与自陈", "1924 年对具体一役的公开定性"],
    ["本人署名专著（P1）", "同期报纸直引（P2）"], 0.84,
    falsifiers=["若他在语料中把重大亏损归因于市场操纵、他人或运气而非自身判断，本条降级"])

add("clm-jl-mm-05",
    "他把价格的**时间结构**（一次上涨过程里回撤的幅度与间隔如何变化）当作可读的信号，"
    "而不是只看价格本身。书中把回撤分为「Normal Reaction」与「abnormal」两类，"
    "并给出可操作的分界：一日之内从当日极值回落六点以上即为异常，是必须离场的危险信号。"
    "1924 年小麦一役他把「第二笔五百万蒲式耳比第一笔更难买到」读作市场转强的证据，"
    "用的是同一种「以成交难度与结构读强弱」的推理。",
    "mental-model", "pattern", [BOOK, C23S],
    ["1940 年著述中的信号定义", "1923 年宣誓证词中对做市行为与市场状态的描述"],
    ["本人署名专著（P1）", "参议院宣誓证词（P2，证据等级最高的一类）"], 0.78,
    falsifiers=["若书中的六点阈值被查明是编者补入而非其本人所写，本条降级为不可用",
                "若语料中出现他明确否认使用固定幅度判据的陈述，本条降级"])

# ── 启发式（deep 要 ≥6 条 status=pattern）────────────────────────────
add("clm-jl-hr-01",
    "**分批建仓，且每一笔都必须比上一笔贵（做空则必须更便宜）。** "
    "书中原文：买 500 股先买 100 股，其后每一笔「must be at a higher price than the」上一笔；做空同理，规定不得在高于前一笔的价位追加卖出。（这两句所在段落的 OCR 受损——语料里作 `cach`／`prcvious onc`／`Ncvcr`／`salc`——故只逐字引用其中未受损的片段。）他给出的理由是这样做能让持仓始终处于浮盈，"
    "而浮盈本身即是判断正确的证据。1924 年小麦一役是这条规则的实例。",
    "heuristic", "pattern", [BOOK, C23S],
    ["1940 年著述中的建仓规则", "1923 年宣誓证词中对分批买回股票的自述"],
    ["本人署名专著（P1）", "参议院宣誓证词（P2）"], 0.85,
    falsifiers=["若语料中出现他主张摊低成本或逆势加仓的直引，本条作废"])

add("clm-jl-hr-02",
    "**先认第一笔小亏，不等它变大。** 「The speculator has to insure himself against "
    "considerable losses by taking the first small loss.」"
    "他把这条与资本的可持续性绑定：只有守住本金，才能在下一次判断正确时还有能力下注。",
    "heuristic", "pattern", [BOOK, C10],
    ["1940 年著述中的止损原则", "1910 年设立不可动用生活底线的对外说明"],
    ["本人署名专著（P1）", "同期报纸直引（P2）"], 0.83,
    falsifiers=["若语料显示他在实际操作中系统性地放任亏损扩大且未将其定性为错误，本条降级"])

add("clm-jl-hr-03",
    "**一年只有四五次值得动手的时机，其余时间的正确动作是不动。** "
    "「there are only a few times a year, possibly four or five, when you should allow」自己建仓，其余时间是在让市场为下一次大行情做准备。"
    "他同时给出反例：「money cannot consistently be made trading every day or every week "
    "during the year. Only the foolhardy will try it.」",
    "heuristic", "pattern", [BOOK, C08],
    ["1940 年著述中的频率约束", "1908 年了结持仓后明言转入观望"],
    ["本人署名专著（P1）", "同期报纸直引（P2）"], 0.84,
    falsifiers=["若语料中出现他主张高频交易或以交易频率为优势的陈述，本条作废"])

add("clm-jl-hr-04",
    "**等价格自己走到预设的那个点再动手，不提前。** "
    "他把这个点称为 Pivotal Point，并要求在到达之前不做任何建仓。"
    "书中他把自己最大的一次失误归因于违反这条：明知棉花一旦升到「1275 cents a pound」就会走向更高价位，却没有等待的意志力（该段 OCR 受损，作 `it would bc`／`I did not havc`，故只引未受损片段），六周内五次进出，"
    "亏掉约 20 万美元并错过约 100 万美元的利润。",
    "heuristic", "pattern", [BOOK, C24],
    ["1940 年著述中的自陈失误", "1924 年对同一族失误的公开定性"],
    ["本人署名专著（P1）", "同期报纸直引（P2）"], 0.86,
    falsifiers=["若「1275 cents」这一数值被查明为 OCR 讹误或编者补入，本条中的具体数值须撤下，规则本身另行核",
                "若语料中出现他主张在预设点位之前建仓的陈述，本条降级"])

add("clm-jl-hr-05",
    "**出现异常信号就离场，不与信号争辩。** 他转述并明确认同的一段话："
    "「When I see a danger signal handed to me, I don't argue with it. I get out! "
    "A few days later, if everything looks all right, I can always get back in again.」"
    "他随后写道「I have always remembered that as a graphic bit of speculative wisdom.」"
    "★ 该段的说话人是「A speculator of great genius」，**不是他本人**——"
    "引用时必须标明这是他所认同的他人之言。",
    "heuristic", "pattern", [BOOK, C08],
    ["1940 年著述中转述并认同的原则", "1908 年了结持仓、拒绝继续推进的实际行动"],
    ["本人署名专著（P1）", "同期报纸直引（P2）"], 0.80,
    falsifiers=["若该段被查明并非他所认同而是他所批评的观点，本条作废"])

add("clm-jl-hr-06",
    "**自己记录，不外包，也不用图表。** 「Personally, charts have never appealed to me. "
    "I think they are altogether too confusing.」同时他自称在记录上是狂热者。"
    "1923 年他对「chart makers and 'dopesters'」的公开评价与此一致——"
    "他认为他们「are wasting their time in making small money where they should be "
    "piling up millions by the use of their own dope」。",
    "heuristic", "pattern", [BOOK, C23F],
    ["1940 年著述中对图表的拒绝", "1923 年对制图者与荐股者的公开评价"],
    ["本人署名专著（P1）", "同期报纸直引（P2）"], 0.82,
    falsifiers=["若语料中出现他使用或推荐图表的直接记载，本条降级"])

add("clm-jl-hr-07",
    "**有利润时不急于兑现，且把「怕失去还没到手的东西」识别为错误。** "
    "1924 年小麦一役他在每蒲式耳赚 25 美分时落袋，随后行情又涨 20 美分，"
    "他自陈：「afraid of losing something I never really had?」（其前的 `Why had I becn` 在扫描件中受损）"
    "书中的通则版是：「As long as a stock is acting right, and the market is right, "
    "do not be in a hurry to take a profit.」",
    "heuristic", "pattern", [BOOK, C23S],
    ["1940 年著述中的持有原则与自陈", "1923 年宣誓证词中对建仓与回补节奏的描述"],
    ["本人署名专著（P1）", "参议院宣誓证词（P2）"], 0.81,
    falsifiers=["若语料中出现他主张见利即走的陈述，本条降级"])

# ── 工作方法 ────────────────────────────────────────────────────────
add("clm-jl-wm-01",
    "他的工作产出是**一套手工价格记录**，而不是模型或图形："
    "书中第 IX 章逐条规定了记法——上升趋势栏用黑墨、下跌趋势栏用红墨、"
    "其余四栏用铅笔，并规定在何种幅度下改栏、何时画线。"
    "他把这套记录称为形成判断的「guide」，并强调这是**他自己的**记法。",
    "work-method", "pattern", [BOOK, C23F],
    ["1940 年著述第 IX 章的操作细则", "1923 年对他人分析方法的公开评价"],
    ["本人署名专著（P1）", "同期报纸直引（P2）"], 0.83,
    falsifiers=["若第 IX 章被查明为出版方或他人代笔，本条须重判"])

# ── 价值 ────────────────────────────────────────────────────────────
add("clm-jl-va-01",
    "**还清债务对他具有独立于经济计算的分量。** 1932 年他公开陈述："
    "「Gentlemen, I have paid them. All of them. A hundred cents on the dollar.」"
    "1934 年再度破产后他说「I've owed that much many times and I've always paid it off.」"
    "并表示打算立刻重新开始、恢复财富并如过去那样偿付债权人（该句见于抓源报告的直引清单，但未能在本工作区语料中逐字定位，故不作引号引用）——三次表态跨十二年，措辞一致。",
    "value", "pattern", [C32, C34A, C34J],
    ["1932 年债务清偿的公开宣告", "1934 年破产后的还债表态"],
    ["1932 年报道（P2）", "1934 年两家不同报纸的报道（P2）"], 0.85,
    falsifiers=["若查到他曾公开主张不必偿付或以破产免责为策略的直引，本条作废"])

# ── 认识论 ──────────────────────────────────────────────────────────
add("clm-jl-ep-01",
    "**他不主张自己的方法可以照搬。** 「Certain guides which I utilize may be of no "
    "value to anyone else… no guide can be 100% right.」"
    "同一章他明确拒绝代劳：「You cannot wisely read a book on 'How to Keep Fit' and "
    "leave the physical exercises to another.」——记录必须自己记、结论必须自己下，"
    "他只负责「light the way」。",
    "epistemic", "pattern", [BOOK, C23F],
    ["1940 年著述中对自身方法普适性的限定", "1923 年对他人套用现成结论的评价"],
    ["本人署名专著（P1）", "同期报纸直引（P2）"], 0.87,
    falsifiers=["若语料中出现他宣称自己的方法普遍适用或保证收益的陈述，本条作废"])

add("clm-jl-ep-02",
    "**他给出的是带条件的判断，不是点位预测。** 1940-09-22 最后一次公开评论中："
    "「If any one thinks Germany is going to be able to subdue England in a comparatively "
    "short space of time, he should not own any stocks at all.」"
    "以及「For those who think that England is going to stay in this war until Germany "
    "admits defeat, I believe the market holds opportunities…」"
    "——两句都把结论挂在一个读者自己要判断的前提上。",
    "epistemic", "pattern", [C40S, BOOK],
    ["1940 年最后一次公开市场评论", "1940 年著述中对「无人能预知」的一般陈述"],
    ["同期报纸直引（P2）", "本人署名专著（P1）"], 0.82,
    falsifiers=["若同一次评论中另有无条件点位预测且被本人认可，本条降级"])

# ── 语体 ────────────────────────────────────────────────────────────
add("clm-jl-ex-01",
    "他的书面语体以**第二人称直呼读者 + 具体价位演算 + 短断言收尾**为特征："
    "讲加仓用「wait until the stock becomes active, until it makes a new high」这种具体动作，并在正文里直接写出 $25.00、$30.00、$50.00 这样的价位，而不是公式；段落常以极短的句子收口，"
    "如「Markets are never wrong—opinions often are.」。",
    "expression", "pattern", [BOOK, C22],
    ["1940 年著述的书面语体", "1922 年口头表述的短句形态"],
    ["本人署名专著（P1）", "同期报纸直引（P2）"], 0.80,
    falsifiers=["若语料中他的书面表达以第三人称或公式化论述为主，本条降级"])

add("clm-jl-ex-02",
    "**自陈失败时不加缓冲。** 书中原话包括「I almost want to turn my face away in "
    "embarrassment when I tell this.」「I became disgusted with myself.」"
    "「not to make excuscs when wrong」——**注意 `excuscs` 是扫描件原样**，此处逐字保留以示未作改写；其含义为「错了不要找借口」"
    "口头版同样直接：1924 年「It was bad judgment.」，1940 年遗书「I am a failure.」。",
    "expression", "pattern", [BOOK, C24, C40N],
    ["1940 年著述中的自陈段落", "1924 年对失利的公开定性", "1940 年遗书片段"],
    ["本人署名专著（P1）", "同期报纸直引（P2）"], 0.84,
    falsifiers=["若语料中他的失败陈述普遍带有归咎他人或环境的成分，本条降级"])

# ── 边界 ────────────────────────────────────────────────────────────
add("clm-jl-bd-01",
    "**「Livermore 语录」的绝大多数不是他说的。** 网上流传的多数句子出自 "
    "Edwin Lefèvre 1923 年的小说《Reminiscences of a Stock Operator》，"
    "主角 Larry Livingston 是虚构人物。实测：他本人那本专著里 "
    "`Lefevre`／`Livingston` 出现 0 次；该小说 112,180 词，"
    "是他全部可公开抓取存世文字（约 22,500 词）的 5 倍。"
    "**凡无法在其本人著作或同期直引中定位的「他的话」，一律不得当作他的话使用。**",
    "boundary", "pattern", [BOOK, C40O],
    ["其本人著作中的用词统计", "1940 年讣闻中所引的他本人语句范围"],
    ["本人署名专著（P1）", "同期报纸直引（P2）"], 0.90,
    falsifiers=["若查到他本人认领该小说中某具体句子的一手记载，该句可单独解禁，本条整体不变"])

add("clm-jl-bd-02",
    "**1908–1940 共 33 年里只有 8 年有他的直引**"
    "（1908、1910、1922、1923、1924、1932、1934、1940），"
    "**其余 25 年本产物无法给出他的第一人称立场**——"
    "最长的三段是 1911–1921（11 年）、1925–1931（7 年）、1935–1939（5 年）。 "
    "现有语料中他的直引只出现在 1908、1910、1922–1924、1932 与 1934、1940，"
    "其余年份只有第三方叙述。按分层规则，第三人称叙述不得用于推断他的想法。",
    "boundary", "pattern", [C10, C22],
    ["1910 年直引", "1922 年直引（两者之间十二年无直引）"],
    ["1910 年报道（P2）", "1922 年报道（P2）"], 0.88,
    falsifiers=["若补入这两段中任一年份的本人直引材料，相应年份的限制解除"])

add("clm-jl-bd-03",
    "**他的方法论文本只有 1940 年一个时点，而其交易生涯约四十九年。** "
    "书中他自述在四十年里把投机做成一门成功的生意（该句 OCR 把 `I` 认成了竖线，故不作逐字引用）。因此该书是**终点的总结，不是过程的记录**；"
    "凡把书中方法直接投射回其早年操作的说法，在本语料中缺少直接证据，"
    "**必须标注为推断而非事实**。",
    "boundary", "pattern", [BOOK, C08],
    ["1940 年著述的自述年限", "1908 年早期操作的当日记录"],
    ["本人署名专著（P1）", "同期报纸直引（P2）"], 0.86,
    falsifiers=["若补入其 1900–1930 年间的方法论自述材料，本条范围相应收窄"])

add("clm-jl-bd-04",
    "**他不适合被用作「稳健投资」或「资产配置」的人格。** "
    "他的可核记录包含至少三次破产（1915、1934 见于语料），"
    "以及他自陈单次错误代价达 200 万美元。"
    "他本人对适用人群给的是排除式表述：投机「is not a game for the stupid, the mentally "
    "lazy, the man of inferior emotional balance, nor for the get-rich-quick adventurer. "
    "They will die poor.」",
    "boundary", "pattern", [BOOK, C34A],
    ["1940 年著述开篇的排除性声明", "1934 年破产后关于历次负债的自述"],
    ["本人署名专著（P1）", "同期报纸直引（P2）"], 0.88,
    falsifiers=["若查到他公开推荐其方法用于保守型资金管理的一手记载，本条降级"])

# ── 事实（不需要双源约束，但仍逐条给源）──────────────────────────
add("clm-jl-ft-01",
    "他一生**只出版过一本署名著作**：《How to Trade in Stocks: The Livermore Formula "
    "for Combining Time Element and Price》，1940 年由 Duell, Sloan & Pearce 出版。"
    "对 541 份同期报纸检索 `By Jesse L. Livermore` 的 6 处命中逐条读后全部为假阳性"
    "（managed by / statement by / engaged by），未发现任何署名报刊文章。",
    "fact", "fact", [BOOK, C40O],
    ["著作版权页", "1940 年讣闻对其著述的记述"],
    ["本人署名专著（P1）", "同期报纸（P2）"], 0.92)

add("clm-jl-ft-02",
    "该书的前言**不是他写的**，署名 Edward Jerome Dies，约 538 词。"
    "前言中对他的评价（如「blind chance never entered into his market sallies」）"
    "**是同期他人的判断，不是他的自陈**。",
    "fact", "fact", [DIES, BOOK],
    ["前言末尾的署名", "该书正文与前言的作者分界"],
    ["书籍前言（S1）", "本人署名专著（P1）"], 0.93)

add("clm-jl-ft-03",
    "1923-12-21 他在美国参议院公共土地委员会**宣誓作证**，"
    "陈述其在 Mammoth Oil 股票上的做市安排，并亲口报出该役"
    "「realized a profit of only $9,916 on the total transaction」。",
    "fact", "fact", [C23S, BOOK],
    ["1923 年参议院证词报道", "其著作中对做市与建仓节奏的一般陈述"],
    ["参议院宣誓证词（P2）", "本人署名专著（P1）"], 0.88)

add("clm-jl-ft-04",
    "1908-05-15 他就棉花交易对记者表示已卖出全部七月棉，并明确否认做逼仓："
    "「I never will try to carry out a corner in cotton」（其前半句在扫描件中作 `Corners are all yvery well in their way, buf`，受损，故不引）",
    "fact", "fact", [C08, BOOK],
    ["1908 年当日访谈", "其著作中对棉花交易的追述"],
    ["同期报纸直引（P2）", "本人署名专著（P1）"], 0.87)

add("clm-jl-ft-05",
    "他卒于 1940-11-28，讣闻于次日见报；遗书片段包含"
    "「I am not worthy of your love. I am a failure.」"
    "同一批报道亦引其语「I am tired of fighting. I can't go on.」",
    "fact", "fact", [C40N, C40O],
    ["遗书片段报道", "讣闻报道"],
    ["1940 年报纸 A（P2）", "1940 年报纸 B（P2）"], 0.90)

# ── 矛盾（必须并陈，不得抹平）──────────────────────────────────────
add("clm-jl-ct-01",
    "**他对自身处境的两次公开定性互相冲突，两句都是他的原话。** "
    "1934-04-18：「I've owed that much many times and I've always paid it off.」"
    "1940-11-29 遗书：「I am not worthy of your love. I am a failure.」"
    "相隔六年七个月。**产物中不得只取其一，也不得把后者解释为前者的自然延续**——"
    "现有语料不足以支撑任何因果叙述。",
    "contradiction", "pattern", [C34A, C40N],
    ["1934 年破产后的公开表态", "1940 年遗书片段"],
    ["1934 年报道（P2）", "1940 年报道（P2）"], 0.86,
    falsifiers=["若补入 1935–1940 年间他本人对自身处境的连续陈述，本条可改写为有据的过程描述"])

# ── 盲点 ────────────────────────────────────────────────────────────
add("clm-jl-bs-01",
    "**他反复陈述的规则与他自己的执行之间存在稳定落差，且他本人承认这一点。** "
    "他写下「等到位再动手」的同时自陈六周内五次违反该规则；"
    "写下「有利润别急着落袋」的同时自陈在小麦上提前兑现。"
    "他给的解释是「I am human and subject to human weaknesses.」"
    "——**这是自陈的盲点，不是外部指控**。",
    "blind-spot", "pattern", [BOOK, C24],
    ["1940 年著述中的两处自陈", "1924 年对失利的公开定性"],
    ["本人署名专著（P1）", "同期报纸直引（P2）"], 0.84,
    falsifiers=["若书中的自陈失误段落被查明为编者添加，本条须重判"])

# ── 存在性假设（只许出现在 hypotheses.md）────────────────────────────
add("clm-jl-sh-01",
    "**假设**：他把「把账还清」当作比重建财富更根本的事——还债是身份问题而非财务问题。"
    "支持：1932 与 1934 三次表态中，「还清」总是先于「重建财富」出现，"
    "且他主动把「为错误付账」与「偿还债权人」并列。"
    "**这是推断，不是他的自陈**：语料中没有任何一句他解释「为什么还债重要」。",
    "soul-hypothesis", "hypothesis", [C32, C34A, C34J],
    ["1932 年债务清偿宣告", "1934 年破产后的两次表态"],
    ["1932 年报道（P2）", "1934 年两家报纸（P2）"], 0.45,
    falsifiers=["若查到他把还债表述为纯粹的信用维护或商业必要，本假设作废",
                "若查到他在其它场合公开接受债务免除，本假设作废"],
    alts=["当时的商业信用环境使公开还债成为继续融资的前提，与自我认同无关",
          "报道选择性呈现——记者更愿意刊登还债表态，语料因此偏斜",
          "他的表态是对债权人与监管的策略性沟通，不反映内在排序"])


def main() -> int:
    out = pathlib.Path(sys.argv[1])
    seen = set()
    for c in C:
        assert c["claim_id"] not in seen, f"重复 claim_id: {c['claim_id']}"
        seen.add(c["claim_id"])
        if c["category"] in {"mental-model", "heuristic", "value", "work-method",
                             "blind-spot", "contradiction"}:
            assert len(set(c["source_ids"])) >= 2, c["claim_id"]
            assert len(set(c["contexts"])) >= 2, c["claim_id"]
            assert len(set(c["evidence_clusters"])) >= 2, c["claim_id"]
            assert c.get("falsifiers"), c["claim_id"]
        assert "src-d1f9ca697c0c" not in c["source_ids"], f"{c['claim_id']} 引用了 holdout！"
    out.write_text("".join(json.dumps(c, ensure_ascii=False) + "\n" for c in C),
                   encoding="utf-8")
    import collections
    print(f"写出 {len(C)} 条断言 → {out}")
    print("按类别:", dict(collections.Counter(c["category"] for c in C)))
    (out.parent / "claim-slug-map.json").write_text(
        json.dumps(SLUGS, ensure_ascii=False, indent=1), encoding="utf-8")
    print("slug → claim_id 映射已写出（人读名与机读 id 的对照，供渲染与复核用）")
    print("pattern 态的 mental-model:",
          sum(1 for c in C if c["category"] == "mental-model" and c["status"] == "pattern"),
          "| heuristic:",
          sum(1 for c in C if c["category"] == "heuristic" and c["status"] == "pattern"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
