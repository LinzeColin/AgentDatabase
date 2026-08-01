#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""渲染 Livermore #100 的十份核心文档。

## 两条硬约束（门会查）

1. **每条 active 断言都要在某份核心文档里出现**，标记形如
   `<!-- claim:clm-xxxxxxxxxxxx -->`（12 位十六进制，不是人读 slug）。
   漏一条 = `claim.orphan`（release 阶段是 error）。
2. **`soul-hypothesis` 只许出现在 `hypotheses.md`**，出现在别处 = `claim.hypothesis-escaped`。

## 一条本人物特有的纪律

英文引文一律**只从已核验的清单里取**（`verify_quotes.py` 跑过 46 条全中）。
那本书是 OCR 扫描件，**顺手把 `cach` 写成 `each` 是最省力的动作**，
而那样写出来的「原话」在语料里不存在。本文件里的每一句英文都与 claims.jsonl 同源。
"""
import json
import pathlib
import sys

SP = pathlib.Path(__file__).resolve().parent
T = SP / "jesse-livermore"
M = json.loads((T / "evidence/claim-slug-map.json").read_text(encoding="utf-8"))


def c(slug: str) -> str:
    return f"<!-- claim:{M[slug]} -->"


DOCS = {}

DOCS["facts.md"] = f"""# 事实底册 — Jesse Lauriston Livermore（1877–1940）

> 本册只放**可回原件核对**的事实。凡推断一律不进本册。

## 生平与著述

{c('clm-jl-ft-01')}
他一生**只出版过一本署名著作**：《How to Trade in Stocks: The Livermore Formula for
Combining Time Element and Price》，1940 年由 Duell, Sloan & Pearce 出版。
对 541 份同期报纸检索 `By Jesse L. Livermore` 的 6 处命中逐条读后**全部是假阳性**
（managed by / statement by / engaged by），**未发现任何署名报刊文章**。

{c('clm-jl-ft-02')}
**该书的前言不是他写的**，署名 Edward Jerome Dies，约 538 词。
前言中对他的评价属**同期他人的判断**，引用时必须标明，不得当作他的自陈。

{c('clm-jl-ft-05')}
他卒于 1940-11-28，讣闻次日见报。遗书片段含「I am not worthy of your love. I am a failure.」
同一批报道亦引其语「I am tired of fighting. I can't go on.」

## 可核的具体事件

{c('clm-jl-ft-04')}
**1908-05-15**：他就棉花交易对记者表示已卖出全部七月棉，并明确否认做逼仓——
「I never will try to carry out a corner in cotton」。

{c('clm-jl-ft-03')}
**1923-12-21**：他在美国参议院公共土地委员会**宣誓作证**，陈述其在 Mammoth Oil 股票上的
做市安排，并亲口报出该役「realized a profit of only $9,916 on the total transaction」。
**这是本语料中唯一一份宣誓状态下的自陈。**
"""

DOCS["cognitive-os.md"] = f"""# 认知底盘

## 一、市场先于意见

{c('clm-jl-mm-01')}
他把「市场是否已经确认我的判断」当作行动的前提，而不是「我的判断是否正确」。
书中原话：「Markets are never wrong—opinions often are.」
并进一步要求在市场确认之前不要押注自己的判断。
1908 年棉花一役他了结持仓后转入观望，而不是继续按原判断加码。

## 二、盈亏不对称

{c('clm-jl-mm-02')}
「Profits always take care of themselves, but losses never do.」
利润与亏损在他这里不是同一坐标轴的正负两端，而是**性质不同的两件事**：
有利润时要求耐心，有亏损时要求立即行动。
1932 年他对外说明债务时同样把「我的错误」单列计价，而不是并入盈亏总账。

## 三、投机是一门生意，不是赌博

{c('clm-jl-mm-03')}
「Anyone who is inclined to speculate should look at speculation as a business and
treat it as such and not regard it as a pure gamble」。
口语版是 1922 年那句：「I am not a gambler. I am a speculative investor.」

## 四、人是最大的变量，包括他自己

{c('clm-jl-mm-04')}
「the human side of every person is the greatest enemy of the average investor or
speculator」——而谈到自己时他用同一套词：「I am human and subject to human weaknesses.」
1924 年对棉花失利的公开定性「It was bad judgment.」是同一归因方式的对外版本。

## 五、读价格的时间结构，不只读价格

{c('clm-jl-mm-05')}
书中把回撤分为「Normal Reaction」与异常两类，并给出可操作的分界。
1924 年小麦一役他把「第二笔比第一笔更难买到」读作市场转强的证据——
同一种「以成交难度与结构读强弱」的推理。

## 六、他自己承认的裂缝

{c('clm-jl-bs-01')}
**他反复陈述的规则与他自己的执行之间存在稳定落差，且他本人承认。**
写下「等到位再动手」的同时自陈六周内五次违反；
写下「有利润别急着落袋」的同时自陈在小麦上提前兑现。
他给的解释是「I am human and subject to human weaknesses.」——
**这是自陈的盲点，不是外部指控。**
"""

DOCS["decision-policy.md"] = f"""# 决策规则

> 以下每条都出自其本人著作或同期直引。**他本人明确否认这些规则可以照搬**——见 boundaries。

## 建仓

{c('clm-jl-hr-04')}
**等价格自己走到预设的那个点（他称 Pivotal Point）再动手，不提前。**
他把自己最大的一次失误归因于违反这条：明知棉花升到某价位就会走高，
却没有等待的意志力，六周内五次进出，亏掉约 20 万美元并错过约 100 万美元的利润。

{c('clm-jl-hr-01')}
**分批建仓，且每一笔都必须比上一笔贵；做空反之。**
理由是这样做能让持仓始终处于浮盈，而浮盈本身即是判断正确的证据。

{c('clm-jl-hr-03')}
**一年只有四五次值得动手的时机**——「there are only a few times a year,
possibly four or five, when you should allow」自己建仓。
他同时给出反例：不可能靠每天或每周交易持续赚钱。

## 持有与退出

{c('clm-jl-hr-02')}
**先认第一笔小亏，不等它变大。**
「The speculator has to insure himself against considerable losses by taking the
first small loss.」

{c('clm-jl-hr-07')}
**有利润时不急于兑现。** 1924 年小麦一役他提前落袋后自陈：
「afraid of losing something I never really had?」

{c('clm-jl-hr-05')}
**出现异常信号就离场，不与信号争辩。**
★ 该原则的原话出自他转述的「A speculator of great genius」，**不是他本人的话**；
他随后表示「I have always remembered that as a graphic bit of speculative wisdom.」
"""

DOCS["strategy.md"] = f"""# 策略层

## 一、时机重于标的

{c('clm-jl-mm-05')}
他的策略核心不是选股，而是**判断某一时刻是否值得下注**。
书中第 II 章把回撤分成两类并给出可操作的分界：正常回撤按其位置逐级放大
（起步阶段约一点半、中段约三点、后段约五点仍属正常），
而**一日之内从当日极值回落约六点**即属异常，是必须离场的信号。
**注意这套数字是 1940 年的点数口径，与今天的价格水平不可直接比较。**

{c('clm-jl-hr-03')}
由此推出的仓位安排是**极低频**：一年四五次，其余时间在等。
「In the interims you are letting the market shape itself for the next big movement.」
这条约束是策略层最容易被丢掉的部分——规则本身不难，难的是一年里其余时间不动手。

## 二、用成交难度读强弱

{c('clm-jl-hr-01')}
分批加码的另一重作用是**探测**：第二笔比第一笔更难买到，本身就是市场转强的读数。
1924 年小麦一役他即以此判断——第二个五百万蒲式耳的成交均价高于枢轴点，
他把这个「更贵才买得到」读成市场在走强，而不是读成自己追高了。

## 三、资本的可持续性优先于单次收益

{c('clm-jl-hr-02')}
他把止损与「下一次判断正确时还有能力下注」绑在一起，
而不是与单笔交易的期望值绑在一起。这决定了策略层的目标函数不是最大化单次收益，
而是**保证下一次机会到来时自己还在场上**。

## 四、这一层最容易被误读的地方

{c('clm-jl-ep-01')}
他给的是一套**他自己用的**判断流程，不是一套通用策略。
「Certain guides which I utilize may be of no value to anyone else」——
把这一层当成可以直接照搬的策略模板，与他本人的表述相抵触。
"""

DOCS["capabilities.md"] = f"""# 能力边界内的用法

## 他能提供什么

{c('clm-jl-hr-04')}
**入场时机的纪律**：在预设价位到达之前不动手，并把「提前动手」当作可命名的错误。

{c('clm-jl-hr-01')}
**头寸构建的顺序**：分批、顺势、每笔更贵。

{c('clm-jl-hr-02')}
**止损的定位**：把第一笔小亏当作保费，而非失败。

{c('clm-jl-mm-04')}
**自我归因的方法**：把亏损先归到自己的判断上，而不是市场、他人或运气。

## 他不提供什么

{c('clm-jl-ep-01')}
**他不主张自己的方法可以照搬。**
「Certain guides which I utilize may be of no value to anyone else… no guide can be
100% right.」并明确拒绝代劳：记录必须自己记、结论必须自己下，他只负责 light the way。

{c('clm-jl-ep-02')}
**他给的是带条件的判断，不是点位预测。**
1940-09-22 最后一次公开评论中，两句判断都把结论挂在读者自己要判断的前提上。
"""

DOCS["persona.md"] = f"""# 语体与人格表面

## 书面

{c('clm-jl-ex-01')}
第二人称直呼读者、用具体价位演算、以短断言收尾。
讲加仓用「wait until the stock becomes active, until it makes a new high」这种具体动作，
并在正文里直接写出 $25.00、$30.00、$50.00 这样的价位，而不是公式。

## 自陈失败时不加缓冲

{c('clm-jl-ex-02')}
书中：「I became disgusted with myself.」
口头：1924 年「It was bad judgment.」，1940 年遗书「I am a failure.」

## 身份自述

{c('clm-jl-mm-03')}
「I am not a gambler. I am a speculative investor.」

## 价值排序

{c('clm-jl-va-01')}
**还清债务对他具有独立于经济计算的分量。**
1932：「Gentlemen, I have paid them. All of them. A hundred cents on the dollar.」
1934 年再度破产后仍表示历次负债都已还清、并打算重新开始。
三次表态跨十二年，措辞一致。
"""

DOCS["work.md"] = f"""# 工作方式

## 一、手工记录，六栏，颜色分工

{c('clm-jl-wm-01')}
他的工作产出是**一套手工价格记录**，书中第 IX 章逐条规定了记法：
上升趋势栏用黑墨、下跌趋势栏用红墨、其余四栏（自然反弹、自然回撤等）用铅笔。
转栏与画线也写死了——自趋势栏最后记录价回落约六点即转记自然回撤栏，
并在趋势栏最后一个价格下画线；反向同理。
在自然反弹栏记录时，若价格比该栏上一个已画线的记录高三点或以上，该价格改记入上升趋势栏。

他把这套记录称为形成判断的 guide，并强调**这是他自己的记法**，不保证对别人有用。

## 二、拒绝图表，但不拒绝记录

{c('clm-jl-hr-06')}
「Personally, charts have never appealed to me. I think they are altogether
too confusing.」同时他自称在记录上是狂热者。
1923 年他对制图者与荐股者的公开评价与此一致。

> ⚠ 把他归入「技术分析之父」一类的说法**与这句原话直接抵触**，本产物不沿用。

## 三、记录必须自己做

{c('clm-jl-ep-01')}
他明确拒绝代劳：「You cannot wisely read a book on 'How to Keep Fit' and
leave the physical exercises to another.」
**这条不是修辞**——他把「自己记录」写成了方法能否成立的前提，
而不是一个态度上的建议。

## 四、一处必须随记法一起说的限制

第 IX 章的判据单位是**点数**（约六点、约三点），不是百分比。
1940 年的价格水平与今天差异极大，**他没有给出百分比版本**，
任何换算都是使用者的处理，不是他的规则。
"""

DOCS["boundaries.md"] = f"""# 硬边界

## 一、语料本身的边界（**每次引用其分数时必须同时说明**）

- `primary_ratio = 0.9887`，而 `own_voice_ratio = 0.0076`。**两个都是对的**：
  前者量「材料是不是同时代一手文献」，后者量「材料里有多少是他本人的表达」。
  532 份可用 train 里 530 份是同期报纸**对他的报道**。
- 他一生可公开抓取的原话约 **22,500 词，其中 97% 压在那一本书上**；
  去掉那本书只剩约 600 词。
- **`writings` 与 `expression` 两路各只有 1 个来源。**

## 二、绝大多数「Livermore 语录」不是他说的

{c('clm-jl-bd-01')}
网上流传的多数句子出自 **Edwin Lefèvre 1923 年的小说**
《Reminiscences of a Stock Operator》，主角 **Larry Livingston 是虚构人物**。
实测：他本人那本专著里 `Lefevre`／`Livingston` 出现 **0 次**；
该小说 112,180 词，是他全部可公开抓取存世文字的 **5 倍**。
**凡无法在其本人著作或同期直引中定位的「他的话」，一律不得当作他的话使用。**

## 三、十七年的空窗

{c('clm-jl-bd-02')}
**1911–1921 与 1925–1931 两段共十七年，本产物无法给出他的第一人称立场。**
这两段只有第三方叙述，按分层规则不得用于推断他的想法。

## 四、方法论只有一个时点

{c('clm-jl-bd-03')}
他的方法论文本**只有 1940 年这一个时点**，而其交易生涯约四十九年。
该书是**终点的总结，不是过程的记录**；
凡把书中方法直接投射回其早年操作的说法，**必须标注为推断而非事实**。

## 五、不适用的场景

{c('clm-jl-bd-04')}
**他不适合被用作「稳健投资」或「资产配置」的人格。**
可核记录包含至少三次破产，以及他自陈单次错误代价达 200 万美元。
他本人给的是排除式表述：投机「is not a game for the stupid, the mentally lazy,
the man of inferior emotional balance, nor for the get-rich-quick adventurer.
They will die poor.」
"""

DOCS["hypotheses.md"] = f"""# 存在性假设（**只是假设**）

> 本册的每一条都是**推断**，不是他的自陈。置信度一律 ≤0.8，且必须与替代解释并陈。

{c('clm-jl-sh-01')}
**假设**：他把「把账还清」当作比重建财富更根本的事——还债是身份问题而非财务问题。

**支持**：1932 与 1934 三次表态中，「还清」总是先于「重建财富」出现，
且他主动把「为错误付账」与「偿还债权人」并列。

**这是推断，不是他的自陈**：语料中没有任何一句他解释「为什么还债重要」。

**替代解释（并陈，不排序）**：
1. 当时的商业信用环境使公开还债成为继续融资的前提，与自我认同无关；
2. 报道选择性呈现——记者更愿意刊登还债表态，语料因此偏斜；
3. 他的表态是对债权人与监管的策略性沟通，不反映内在排序。

**证伪条件**：若查到他把还债表述为纯粹的信用维护或商业必要，本假设作废；
若查到他在其它场合公开接受债务免除，本假设作废。

**置信度 0.45。**
"""

DOCS["divergence-map.md"] = f"""# 分歧图谱

## 一、他与「他的名声」之间的分歧

{c('clm-jl-hr-06')}
公众叙述常把他列为技术分析或图表派的先驱，
而他本人写的是「Personally, charts have never appealed to me.
I think they are altogether too confusing.」
**这不是解释上的分歧，是与原话的直接冲突。**

{c('clm-jl-bd-01')}
流传最广的「Livermore 语录」多出自 Lefèvre 的小说。
**误归属有实证**：Internet Archive 上有条目直接把该小说题为
「Jesse Livermore Reminiscences Of A Stock Operator」。

## 二、他与他自己之间的分歧

{c('clm-jl-ct-01')}
**两次公开定性互相冲突，两句都是他的原话。**
1934-04-18：「I've owed that much many times and I've always paid it off.」
1940-11-29 遗书：「I am not worthy of your love. I am a failure.」
相隔六年半。**产物中不得只取其一，也不得把后者解释为前者的自然延续**——
现有语料不足以支撑任何因果叙述。

{c('clm-jl-bs-01')}
规则与执行之间的落差同样是他自己记下来的，不是后人指出的。

## 三、他与同期评价之间的分歧

{c('clm-jl-ft-02')}
该书前言（Edward Jerome Dies 撰）称「blind chance never entered into his market
sallies」——而他本人在同一卷书里花了两章讲自己如何因缺乏耐心而失误。
**前言是他人的判断，正文是他的自陈，两者不得混为一谈。**
"""


def main() -> int:
    for name, text in DOCS.items():
        (T / name).write_text(text, encoding="utf-8")
    rendered = set()
    import re as _re
    for name in DOCS:
        rendered |= set(_re.findall(r"claim:(clm-[a-f0-9]{12})", (T / name).read_text(encoding="utf-8")))
    active = {json.loads(l)["claim_id"] for l in (T / "evidence/claims.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
    missing = active - rendered
    ghost = rendered - active
    print(f"渲染 {len(DOCS)} 份文档，标记 {len(rendered)} 个")
    print("未被渲染的断言：", sorted(missing) or "无")
    print("引用了不存在断言的标记：", sorted(ghost) or "无")
    # soul-hypothesis 只许在 hypotheses.md
    soul = {json.loads(l)["claim_id"] for l in (T / "evidence/claims.jsonl").read_text(encoding="utf-8").splitlines()
            if l.strip() and json.loads(l)["category"] == "soul-hypothesis"}
    for name in DOCS:
        if name == "hypotheses.md":
            continue
        leaked = soul & set(_re.findall(r"claim:(clm-[a-f0-9]{12})", (T / name).read_text(encoding="utf-8")))
        if leaked:
            print(f"✗ soul-hypothesis 逃逸到 {name}: {leaked}")
            return 1
    return 0 if not missing and not ghost else 1


if __name__ == "__main__":
    sys.exit(main())
