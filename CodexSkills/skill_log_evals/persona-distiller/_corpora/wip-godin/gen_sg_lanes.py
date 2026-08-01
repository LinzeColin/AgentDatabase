#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Seth Godin #99 —— 六条研究泳道。

**取样声明（必须留在产物里）**：本轮语料是 seths.blog 2003–2026 的 **193 篇**，
按年分层、每年约 8 篇。**博客总量远大于此，这是分层取样不是全量**——
凡说「他从不 X」「他一贯 Y」的地方，都只能挂在这 193 篇上。

**结构性短板**：语料**全部是他自己的博客**。没有访谈逐字稿、没有第三方报道、
没有他人对他的评价。因此：
- `conversations` 泳道只能由「他在博客里对读者说话／答问」构成，不是真对话；
- `external` 泳道是「他谈论外部人事」，不是「外部人事谈论他」；
- **关于他实际怎么经营公司、怎么与人共事，本轮语料一句都不支持。**
"""
import pathlib
import re

W = pathlib.Path(__file__).resolve().parent / "ws-godin/seth-godin"
R = W / "references/research"
R.mkdir(parents=True, exist_ok=True)

LANES = {}

LANES["01-writings.md"] = """# 泳道一 · 著述（writings）

**样本**：133 篇（193 篇中的多数）。全部为 seths.blog 正文，单作者署名。

## 反复出现的第一动作：不回答问题，先换掉问题

`sg_2011_how_do_you_know_when_its_done`：

> Of course, it's not done. It's never done.
> That's not the right question.
> The question is: when is it good enough?

这不是修辞。他随后给了「good enough」的操作定义——
「sufficient to surpass the standards we've set」，并把超出这个点的部分
定名为 `stalling and a waste of time`。**换问题之后必须给新问题的判据**，
这一步在他的文章里几乎总是出现。

`sg_2004_differentiation` 是同一动作的对抗版：台下有人把他的论点归结为
「differentiation and segmentation」，他的回应是 `"Nope, it's not that. Sorry."`——
先拒绝对方的词汇，再解释为什么那两个词描述的是另一件事。
他还在同一段里写 `I hate it when I pounce, but I couldn't help it`。

## 世界观（worldview）是他的分析单位，不是人群属性

`sg_2005_listening_to_th_2` 解释一张老专辑为什么长期在榜：

> Because of worldview. Some people (most people) want to buy music
> they've heard before.

紧接着给出结论句：**`You can't change the way people do things.`**
他给的可行动作是绕行——`enter a population with your idea via an easier route
and let the people who want to spread your` 想法的人去扩散。

## 注意力是必须挣来的，不能拿

`sg_2008_may_i_have_your`：

> Of course, I can't have your attention. I could borrow it or earn it
> or if I use all caps, offend you and demand it.

以及 **`There is no refund window for misused attention`**。
`sg_2009_rupert_murdoch_has_it_backwards` 是同一原理的应用：
`If you can't make money from attention, you should do something else for a living.
Charging money for attention gets you neither money nor attention.`

## 建议常常从「别做了」开始

`sg_2008_advice_for_real`（对一屋子房地产经纪讲话）：

> Plan A: You should quit selling real estate.
> I'm serious.

而且他把「劝退」讲成对留下者的好消息——
`the competition for attention just got smaller`。Plan B 才是给留下的人的。

## 时间跨度上的一致性

2026 年的 `sg_2026_courage_vs_excuses` 仍是同一结构：
把 `AI` 定性为 `a simple, brand-new, all-purpose excuse`，
再给出对立项 `Courage` 的定义（`commitment to take risks and work hard
to make something better than most people think it needs to be`）。
**二十三年间，「先换问题、再给判据」这个动作没有变过。**
"""

LANES["02-conversations.md"] = """# 泳道二 · 对话（conversations）

**样本**：9 篇。**这是本人物最薄的一条泳道，且薄得有结构性原因。**

## 必须先说清楚这条泳道是什么

语料里**没有一份访谈逐字稿、没有一份对话记录**。
所谓 `conversations` 全部是**他在博客里对读者说话或自问自答**的形态。
把它们当成「他与人交谈时的样子」是越界——
**本轮语料不支持任何关于他实际对话方式的断言。**

## 自问自答体

`sg_2013_qa_whats_the_problem_with_weird` 是唯一明确标注为 Q&A 的一篇，
但提问者是他自己的书（`Our series continues with We Are All Weird`）。
里面有一处可用的量化表述：

> Twenty five percent of the population is a landslide in most modern elections.
> You don't need everyone to vote for you, just the weird people who care.

## 对读者的第二人称直呼

`sg_2010_who_judges_your_work` 全篇是对「你」讲话，
并把高中经验作为共同前提：`Here's the mistake we make in high school:
We let anyone, just anyone, judge our work (and by extension, judge us.)`

结论落在一个可选择的动作上——
`The ability to choose who judges your work` 被称作关键的构件。

## 提问式标题作为组织方式

`sg_2014_who_is_cheering_you_on`、`sg_2011_how_do_you_know_when_its_done`、
`sg_2016_not_enough_if_or_not_enough_then` —— 标题即问题，正文即他自己的回答。
**这是他组织文章的方式，不是他与人对话的方式。** 这一区分必须保留。
"""

LANES["03-expression.md"] = """# 泳道三 · 表达（expression）

**样本**：13 篇，但表达特征在全部 193 篇里都可观察。

## 极短

`sg_2019_short_and_funny` 全文两句：

> If we only forward the easy, short and funny things we read online,
> why are we surprised that our inbox is filled with nothing we'll remember tomorrow?
> What would happened if instead, we shared the most complex, useful and
> thoughtful things we discovered instead?

（原文 `What would happened` 的语法错误照录，未订正。）
`sg_2009_rupert_murdoch_has_it_backwards` 全文三句。
**短到这个程度是常态，不是例外**——凡产物写出长段落，即偏离。

## 成对句 + `…` 作枢轴

`sg_2019_choices_2` 通篇是这个形态：

> Judge people by where they came from
> … Judge people by where they're going
> Choices come with responsibility
> … People can't be trusted to make good choices

**两侧都不带评判词**，他不说哪一侧对。这是一个形式装置，不是列表。

## 先建立焦虑，再一句话拆掉

`sg_2010_david_byrne_is_angry_with_me` 用四段写「他为什么生我的气」，
然后：

> Of course, David Byrne isn't angry with me. David Byrne doesn't even
> remember who I am.

**转折句用 `Of course,` 起头**，把前面整段重新定义为读者（和作者）的自作多情。
`sg_2011_how_do_you_know_when_its_done` 用的是同一个词起头。

## 对称判断句

`sg_2013_swagger`：

> Substance without swagger slows you down.
> But swagger without substance can be fatal.

两侧不是并列，**后一侧更重**。这个「对称形式 + 不对称权重」是他给判断的惯用形。

## 归功的习惯

`Thanks to Joe Mehnart for inspiring this riff`（2013）、
`[HT to Mara]`（2014）、`Dave's new site`（2005）、
`Allan sends over a riff`（2006）。
**他把想法的来处写在文里**，而且往往是全名。
"""

LANES["04-external.md"] = """# 泳道四 · 外部（external）

**样本**：14 篇。**注意方向：这是「他谈论外部人事」，不是「外部人事谈论他」。**

语料里**没有任何第三方对他的报道、评价或反驳**。
因此关于他的公众形象、影响力、争议，本轮一句都不支持。

## 拿具体的人和公司当案例，且指名道姓

- `sg_2009_rupert_murdoch_has_it_backwards`：直接以人名为题下判断
  （`You don't charge the search engines to send people to articles on your site, you pay them`）
- `sg_2007_cowboy_junkies`：用一支乐队讲「老客户与新客户要的东西相反」
  ——`Your current customers want nothing but the old stuff, but the new
  customers don't know you exist, so they can't speak up.`
- `sg_2010_david_byrne_is_angry_with_me`：用一次真实的擦肩而过讲归因错误
- `sg_2008_may_i_have_your`：点名 Chris Anderson 的新书并称之为 `brilliant`

## 他会为批评过的对象补一条澄清

`sg_2007_cowboy_junkies` 文末带方括号补注：

> [Clarification! I love the Junkies. I saw them last night. They were spectacular…

**这是同一篇里的自我修正**，不是另发一篇。产物若把他写成只下判断不回头的人，即偏离。

## 对「新东西」的判断带自嘲

`sg_2005_rollyo` 给了一份 Web 2.0 的五条清单，随即：

> Tip: to be #1 … it helps to go first! I'll never have a shot once it gets crowded.

`sg_2004_hoodia` 的结论是 **`the stuff that changes the most is banal`**，
并附一条打脸的 PS：`according to the BBC, all those Hoodia ads you see online are frauds`。
"""

LANES["05-decisions.md"] = """# 泳道五 · 决策（decisions）

**样本**：11 篇。这条泳道记的是**他在博客上公开做过的动作**，
不是他的商业决策——**语料不包含任何公司内部决策的记录**。

## 他把自己的发布行为写进博客，并给截止日

`sg_2010_last_chance_for_bonus_prizes`：
`these bonuses will cease to be available after Wednesday February 24th.`
`sg_2011_september_13_session_in_my_office`：
`By request, I'm offering a small group session in my office on the 13th of September.`
并附 `Apologies in advance if you can't get a ticket, but if it goes well,
I'll probably do it again.`

**动作 + 具体日期 + 明确的稀缺说明**，三件同时给。

## 免费与付费的处理

`sg_2012_some_reading_without_charge_worth_way_more_tha` 整篇是一份免费资源清单，
标题自带定价论断（`worth way more than it costs`）。
`sg_2015_online_courses` 实际内容是劝捐（Room to Read、Compassion Collective），
并说明 `your donation will be matched dollar for dollar`。

## 对「要不要做现场」的公开权衡

`sg_2013_will_you_choose_to_do_it_live` 是本泳道里最完整的一次公开推理：
他先说 `I spend a lot of time wrestling with this very question`，
然后列出现场的五条代价（不保证成功、更贵、只在创作者决定时发生、
观众参与共创、放大后的保真度更低），再给出量级
`Pre-recorded music is perhaps 500 times more popular than live music`。

**他公开列出的是代价，不是好处**——结论留给读者。
"""

LANES["06-timeline.md"] = """# 泳道六 · 时间线（timeline）

**样本**：13 篇。本泳道只能建立**「他在某年公开写过什么」**，
不能建立他的生平年表——**语料里没有任何传记性材料**。

## 可确证的时间跨度

- 最早：`sg_2003_gasp`、`sg_2003_breathtaking`（2003 年 9 月 / 8 月）
- 最晚：`sg_2026_courage_vs_excuses`（2026 年）、`sg_2026_cheaper_not_to_care`（2026 年 3 月 22 日）
- **跨度 23 年，每年均有正文**（取样每年约 8 篇）

## 关注对象随年份移动，方法不移动

| 时期 | 他写的对象 |
|---|---|
| 2003–2006 | 网站、Web 2.0、iPod 配件、Yahoo! Buzz 榜 |
| 2007–2010 | 唱片业、报业收费墙、注意力经济、房地产经纪 |
| 2011–2015 | 出货与「good enough」、现场 vs 录制、patron 模式的过时 |
| 2016–2020 | if/then 承诺、自我判断的不可靠、选择的成对呈现 |
| 2021–2026 | 状态定价、AI 作为借口、`cheaper not to care` 的长期不成立 |

**这张表是我按取样篇目归纳的，不是他给的分期。**

## 一条可核的时间断言

`sg_2026_cheaper_not_to_care`（2026-03-22）与
`sg_2008_may_i_have_your`（2008）相隔十八年，
而两篇的结构完全一致：**引一句流行说法 → 指出它在长期不成立 → 给出机制**。
2026 那篇甚至把引号本身当成论据：
`It's in quotation marks for a reason: it's not true.`
"""


def source_ids():
    """文件名 → src-xxxxxxxxxxxx。泳道必须引 source_id，不能只写文件名——
    文件名会改，source_id 是账本里的稳定键。"""
    import json
    out = {}
    for line in (W / "evidence/source-ledger.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        title = str(r.get("title") or "")
        if title:
            out[pathlib.Path(title).stem] = r["source_id"]
    return out


def annotate(text: str, ids: dict) -> str:
    """把正文里出现的 `sg_xxx` 文件名后面补上 `[src-xxx]`。
    查不到的**原样留着并在末尾列出**——静默丢掉引用等于制造装饰性引用。"""
    missing = set()

    def sub(m):
        stem = m.group(0)
        sid = ids.get(stem)
        if not sid:
            missing.add(stem)
            return stem
        return f"{stem} [{sid}]"

    out = re.sub(r"sg_\d{4}_[a-z0-9_]+", sub, text)
    if missing:
        out += "\n\n> ⚠ 以下篇目在账本里查不到 source_id，未挂引用：" + "、".join(sorted(missing)) + "\n"
    return out


def main() -> int:
    ids = source_ids()
    for name, text in LANES.items():
        (R / name).write_text(annotate(text, ids), encoding="utf-8")
        print(f"  ✓ {name:<22} {len(text):>5} 字")
    print(f"\n✓ {len(LANES)} 条泳道写入 {R}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
