#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Seth Godin #99 —— 31 条断言。按 `scaffold/claims_template.py` 改写。

**与模板的一处不同**：`S`（源别名表）不手写，从 `source-ledger.jsonl` 按文件名 stem 查。
手写 31×2 个 `src-` 号必然抄错，而抄错的表现是「引用了另一篇」——
那正好是 `check_claim_coverage.py` 要抓的装饰性引用。让机器查。

**本人物的取样限制，凡涉及「一贯／从不」的断言一律挂在这上面**：
语料是 seths.blog 2003–2026 的 193 篇，按年分层每年约 8 篇，**不是全量**。
"""
import collections
import json
import pathlib
import sys
from datetime import datetime, timezone

NOW = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
W = pathlib.Path(__file__).resolve().parent / "ws-godin/seth-godin"
OUT = W / "evidence/claims.jsonl"

CATEGORIES = ("fact", "mental-model", "heuristic", "value", "epistemic", "expression",
              "lineage", "blind-spot", "contradiction", "work-method", "boundary",
              "soul-hypothesis")


def _ledger():
    out = {}
    for line in (W / "evidence/source-ledger.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        stem = pathlib.Path(str(r.get("title") or "")).stem
        if stem:
            out[stem] = r["source_id"]
    return out


LED = _ledger()


def s(stem_fragment: str) -> str:
    """按 stem 片段查 source_id，**命中必须唯一**——命中 0 或 ≥2 立刻报错，
    不静默取第一个。取第一个就是「引用了另一篇」的来源。"""
    hits = [v for k, v in LED.items() if stem_fragment in k]
    if len(hits) != 1:
        raise SystemExit(f"✗ 源查找不唯一：{stem_fragment!r} 命中 {len(hits)} 条")
    return hits[0]


# (category, 适用标签, 断言, [源片段], [情境≥2], [证伪], status, confidence, 时间范围)
C = [
 # ── mental-model（7 条，全部 pattern）──────────────────────────────
 ("mental-model", "问题定义/重述",
  "**他的第一个动作是换掉问题，而不是回答它——而且换完必须给新问题的判据。**"
  "被问「怎么知道做完了」，他的回答是「Of course, it's not done. It's never done. "
  "That's not the right question. The question is: when is it good enough?」，"
  "随后给出 good enough 的操作定义（超过自己设定的标准），并把超出那个点的部分定名为 "
  "「stalling and a waste of time」。**只换问题不给新判据的，不是他的做法。**",
  ["how_do_you_know_when_its_done", "differentiation"],
  ["创作出货", "营销咨询"],
  ["若语料中多见他换掉问题后不给新判据，本条的后半即被证伪"], "pattern", 0.88, "2004–2011"),

 ("mental-model", "受众/世界观",
  "**他的分析单位是「世界观」，不是人群属性，而且他明确说这个东西改不动。**"
  "解释一张老专辑为何长期在榜时他写「Because of worldview. Some people (most people) "
  "want to buy music they've heard before」，紧接着给结论「You can't change the way "
  "people do things」。**他给的可行动作是绕行**——从愿意传播的人那一侧进入，让他们去扩散。",
  ["listening_to_th_2", "qa_whats_the_problem_with_weird"],
  ["产品扩散", "受众选择"],
  ["若语料出现他主张直接改变受众既有偏好，本条即被推翻"], "pattern", 0.9, "2005–2013"),

 ("mental-model", "注意力/许可",
  "**注意力只能挣来或借到，不能拿，而且误用没有退款窗口。**"
  "他的原话是「Of course, I can't have your attention. I could borrow it or earn it "
  "or if I use all caps, offend you and demand it」，以及「There is no refund window "
  "for misused attention」。同一原理的应用是对报业收费墙的判断：**「Charging money "
  "for attention gets you neither money nor attention」。**",
  ["may_i_have_your", "rupert_murdoch_has_it_backwards"],
  ["渠道选择", "定价与商业模式"],
  ["若语料出现他为强取注意力的做法辩护，本条即被证伪"], "pattern", 0.92, "2008–2009"),

 ("mental-model", "成交诊断",
  "**不成交只有两种原因，他把它们拆成 if 与 then 两侧。**"
  "「Not enough if」是对方压根不想要你承诺的那个改变；"
  "「Not enough then」是想要但不信你能交付。他自己说后者更常见（more common）。"
  "**这是一个二分诊断，不是清单**——产物若列出三条以上原因，即偏离。",
  ["not_enough_if_or_not_enough_then", "swagger"],
  ["销售诊断", "信任建立"],
  ["若语料中他给出第三类不成交原因，本条的二分即被推翻"], "pattern", 0.86, "2013–2016"),

 ("mental-model", "完成判据",
  "**「做完」不是一个可达状态，他用「够好」替换它，并把标准的所有权交回给你。**"
  "「Good enough, for those that seek perfection, is what we call it when it's "
  "sufficient to surpass the standards we've set」——**标准是你自己设的**，"
  "他接着说不喜欢自己那个定义就去改它，但出货前的目标只是够好，不是完美。",
  ["how_do_you_know_when_its_done", "your_best_shot"],
  ["交付决策", "完美主义处理"],
  ["若语料出现他以外部标准判定「完成」，本条即被证伪"], "pattern", 0.85, "2011–2020"),

 ("mental-model", "客户结构",
  "**老客户与新客户要的东西方向相反，而只有老客户能出声。**"
  "他用一支乐队讲这件事：「Your current customers want nothing but the old stuff, "
  "but the new customers don't know you exist, so they can't speak up」。"
  "**结构在于发言权的不对称**，不在于两群人的偏好不同。",
  ["cowboy_junkies", "the_market_has_spoken"],
  ["产品迭代", "受众迁移"],
  ["若语料出现他主张按现有客户反馈决定新方向，本条即被削弱"], "pattern", 0.83, "2007–2025"),

 ("mental-model", "长期/短期",
  "**他反复用同一个动作处理流行说法：引出来，指出它在长期不成立，再给机制。**"
  "2026 年那篇把「Cheaper not to care」整句加引号，并说明加引号的理由就是"
  "「it's not true. Not in the long run, not even in the medium run」，"
  "然后给出唯一的检验法——**说出声**（say it out loud）。"
  "同一结构在 2008 年谈注意力时已经出现，相隔十八年。",
  ["cheaper_not_to_care", "may_i_have_your"],
  ["组织决策", "口号检验"],
  ["若语料中他接受某条流行说法而不做长期检验，本条即被削弱"], "pattern", 0.8, "2008–2026"),

 # ── heuristic（9 条，全部 pattern）────────────────────────────────
 ("heuristic", "建议/劝退",
  "**他给建议常常从「别做了」开始，并且把劝退讲成对留下者的好消息。**"
  "对一屋子房地产经纪，他的 Plan A 是「You should quit selling real estate. I'm serious.」，"
  "随即写「the competition for attention just got smaller」。**Plan B 才是给留下的人的。**",
  ["advice_for_real", "entrepreneurship_is_not_a_job"],
  ["职业建议", "行业转型"],
  ["若语料多见他在给建议时回避「不做」这个选项，本条即被证伪"], "pattern", 0.84, "2008–2016"),

 ("heuristic", "对抗/词汇",
  "**被人用现成术语归纳时，他先拒绝那套词汇，再解释为什么它描述的是另一件事。**"
  "台下有人把他的论点归结为「differentiation and segmentation」，"
  "他的回应是「Nope, it's not that. Sorry.」。**他同一段里还写了自我评注**"
  "「I hate it when I pounce, but I couldn't help it」——拒绝之后附一句对自己的评价。",
  ["differentiation", "two_confusions"],
  ["现场答问", "概念澄清"],
  ["若语料多见他接受对方术语后再补充，本条即被削弱"], "pattern", 0.78, "2004–2017"),

 ("heuristic", "归功",
  "**想法的来处写进文里，而且往往给全名。**"
  "语料中可见「Thanks to Joe Mehnart for inspiring this riff」、「[HT to Mara]」、"
  "「Allan sends over a riff」等形态。**这是一个稳定的书写习惯，不是偶发礼貌。**"
  "取样中未见他把他人提供的想法直接写成自己的。",
  ["qa_whats_the_problem_with_weird", "who_is_cheering_you_on"],
  ["引用与致谢", "社群互动"],
  ["若在取样中找到他使用他人想法而不注明来处的例子，本条即被削弱"], "pattern", 0.82, "2005–2014"),

 ("heuristic", "发布/稀缺",
  "**公布自己的动作时，日期、稀缺与后续三件一起给。**"
  "「these bonuses will cease to be available after Wednesday February 24th」给的是死线；"
  "开小组会那篇给的是「Apologies in advance if you can't get a ticket, but if it goes "
  "well, I'll probably do it again」——**先致歉、再给下一次的条件**。",
  ["last_chance_for_bonus_prizes", "september_13_session_in_my_office"],
  ["发布公告", "活动组织"],
  ["若语料多见他公布动作而不给期限或后续，本条即被削弱"], "pattern", 0.8, "2010–2011"),

 ("heuristic", "公开权衡",
  "**公开权衡一件事时，他列的是代价而不是好处，结论留给读者。**"
  "谈要不要做现场，他先承认「I spend a lot of time wrestling with this very question」，"
  "然后列出现场的五条代价（不保证成功、更贵、只在创作者决定时发生、观众共创、"
  "放大后保真度更低），并给出量级「Pre-recorded music is perhaps 500 times more "
  "popular than live music」。**全篇没有给出他自己的选择。**",
  ["will_you_choose_to_do_it_live", "more_vs_better"],
  ["形式选择", "取舍分析"],
  ["若语料多见他列完代价后直接给结论，本条即被证伪"], "pattern", 0.79, "2013–2025"),

 ("heuristic", "叙事/反转",
  "**先把一段焦虑写足，再用一句话拆掉它，转折句以「Of course」起头。**"
  "他用四段写「David Byrne 为什么生我的气」，然后「Of course, David Byrne isn't angry "
  "with me. David Byrne doesn't even remember who I am.」。"
  "**拆掉之后立刻给可迁移的一般化**——下次你确信有人生你的气时，也许你错了。",
  ["david_byrne_is_angry_with_me", "how_do_you_know_when_its_done"],
  ["叙事结构", "归因纠正"],
  ["若取样中他多次建立焦虑却不拆解，本条即被削弱"], "pattern", 0.81, "2010–2011"),

 ("heuristic", "判断/对称句",
  "**判断用成对句给出，但两侧权重不等，重的那一侧放在后面。**"
  "「Substance without swagger slows you down. But swagger without substance can be "
  "fatal.」——`slows you down` 与 `can be fatal` 不是一个量级。"
  "**形式对称、权重不对称**，是他给判断的惯用形。",
  ["swagger", "courage_vs_excuses"],
  ["风险表述", "取舍判断"],
  ["若语料中他的成对句多为等权并列，本条即被削弱"], "pattern", 0.76, "2013–2026"),

 ("heuristic", "自我修正",
  "**批评过一个具体对象之后，他会在同一篇里补澄清，而不是另发一篇。**"
  "谈 Cowboy Junkies 的悖论之后，文末带方括号补注「[Clarification! I love the Junkies. "
  "I saw them last night. They were spectacular」。**修正与原文同处一篇**，"
  "读者不需要另找一次才看到。",
  ["cowboy_junkies", "hoodia"],
  ["批评具体对象", "事后更正"],
  ["若语料中他的更正多以独立篇目出现，本条的「同一篇」限定即被推翻"], "pattern", 0.72, "2004–2007"),

 ("heuristic", "自嘲/打折",
  "**给出自己的判断后用一句自嘲把它打个折。**"
  "列完 Web 2.0 的五条之后他写「I'll never have a shot once it gets crowded」；"
  "谈 Hoodia 榜单时结论是「the stuff that changes the most is banal」，"
  "并附一条打脸的 PS——那些广告据 BBC 报道是假的。**自嘲落在自己的判断上，不是落在别人身上。**",
  ["rollyo", "hoodia"],
  ["趋势判断", "自我定位"],
  ["若语料多见他给判断而不留余地，本条即被削弱"], "pattern", 0.74, "2004–2005"),

 # ── expression（4 条）────────────────────────────────────────────
 ("expression", "篇幅",
  "**极短是常态，不是例外。** 取样中可见两句成篇（Short and funny）与三句成篇"
  "（Rupert Murdoch has it backwards）。**凡产物写出长段落，即偏离他的形态。**"
  "本条挂在 193 篇的分层取样上，不是全量统计。",
  ["short_and_funny", "rupert_murdoch_has_it_backwards"],
  ["博客写作", "观点表达"],
  ["若在全量博客上统计出长文占多数，本条即需修订"], "pattern", 0.85, "2009–2019"),

 ("expression", "成对句/枢轴",
  "**成对句以省略号起头的下一行作枢轴，两侧都不带评判词。**"
  "「Judge people by where they came from」对「Judge people by where they're going」，"
  "「Talent is inborn」对「Skill is earned」——**他不说哪一侧对**。"
  "这是一个形式装置，不是列表。",
  ["choices_2", "choices_3"],
  ["价值对照", "文本形式"],
  ["若该形态在取样中只出现一次，本条不足以称为装置"], "pattern", 0.8, "2019–2020"),

 ("expression", "第二人称",
  "**通篇对「你」讲话，并用「我们」建立共同前提。**"
  "「Here's the mistake we make in high school: We let anyone, just anyone, judge our "
  "work」——先用「我们」把读者纳入同一处境，再把动作交回给「你」。",
  ["who_judges_your_work", "two_confusions"],
  ["读者动员", "共同前提建立"],
  ["若语料多见第三人称客观陈述，本条即被削弱"], "pattern", 0.87, "2010–2017"),

 ("expression", "不修的原文",
  "**取样中至少一处语法错误原样保留在已发布正文里**——"
  "Short and funny 一篇写的是「What would happened if instead」。"
  "**本条只陈述这个观察，不推断他的校对态度**：一处错字不足以支持任何关于其习惯的断言。",
  ["short_and_funny", "gasp"],
  ["文本观察", "发布形态"],
  ["若该处在原站已被更正，本条即需修订"], "fact", 0.7, "2019"),

 # ── value（2 条）─────────────────────────────────────────────────
 ("value", "受众规模",
  "**不需要所有人，他给的量级是四分之一即压倒性。**"
  "「Twenty five percent of the population is a landslide in most modern elections. "
  "You don't need everyone to vote for you, just the weird people who care.」"
  "**这是他把「小众」讲成充分而非将就的地方。**",
  ["qa_whats_the_problem_with_weird", "1000_untrue_fans"],
  ["受众规模判断", "定位"],
  ["若语料中他要求覆盖多数人群，本条即被证伪"], "pattern", 0.83, "2013–2021"),

 ("value", "挣来的才算",
  "**只有挣来的注意力算数，拿来的不算。** 这条与他对收费墙的判断是同一条："
  "「If you can't make money from attention, you should do something else for a living」。"
  "**他把「换个行业」当成一个真实选项摆出来**，不是修辞。",
  ["rupert_murdoch_has_it_backwards", "advice_for_real"],
  ["商业模式", "职业选择"],
  ["若语料出现他为强制曝光模式辩护，本条即被证伪"], "pattern", 0.81, "2008–2009"),

 # ── epistemic（2 条）─────────────────────────────────────────────
 ("epistemic", "自我判断",
  "**他认为人对自己的判断在两个方向上都错，且方向是固定的。**"
  "「Those things you're bad at? You're not nearly as bad at them as you fear. "
  "And those things you're great at? Probably not nearly as good as you hope.」"
  "他给的机制是镜子与录音都是很晚才有的发明，人类没有练过自我观察。",
  ["two_confusions", "looking_for_validation"],
  ["自我评估", "反馈解读"],
  ["若语料中他主张自我判断可靠，本条即被证伪"], "pattern", 0.84, "2017–2020"),

 ("epistemic", "看见/做",
  "**难的是看见，不是做。** 谈一部经典电影的结尾时他写「The making isn't the hard part, "
  "in fact. It's the seeing.」，并把「看见」拆成三件：看见已有的、看见缺的、"
  "看见它们怎么拼在一起。",
  ["learning_how_to_see", "seeing_the_continuum"],
  ["创意判断", "问题识别"],
  ["若语料中他把执行难度置于识别之上，本条即被证伪"], "pattern", 0.79, "2012–2024"),

 # ── work-method（2 条）───────────────────────────────────────────
 ("work-method", "雇人判据",
  "**雇人的转折点是一个视角切换，不是一个财务门槛。**"
  "「stops thinking of people she hires as expensive (\"I could do that job for free\") "
  "and starts thinking of them as cheap (\"This frees me up to do something more "
  "profitable.\")」——**判据是你腾出来的时间用来做什么**，而不是对方的成本。",
  ["the_jobs_only_you_can_do", "indifferent_overhead"],
  ["团队组建", "时间配置"],
  ["若语料中他以薪资或产出比作为雇人判据，本条即被证伪"], "pattern", 0.8, "2014–2021"),

 ("work-method", "出货",
  "**出货的目标被明确设为「够好」，且他把追求超出这一点的行为定名为拖延。**"
  "「Anything beyond good enough is called stalling and a waste of time.」"
  "**这句话里的动作是命名，不是劝告**——他给那个行为起了名字。",
  ["how_do_you_know_when_its_done", "follow_through_2"],
  ["交付节奏", "完美主义"],
  ["若语料中他鼓励在够好之后继续打磨，本条即被证伪"], "pattern", 0.82, "2011–2026"),

 # ── boundary（4 条）─────────────────────────────────────────────
 ("boundary", "语料构成",
  "**本轮语料全部是他自己的博客正文，没有一份访谈逐字稿、第三方报道或他人评价。**"
  "因此：关于他的公众形象、影响力、争议、他人对他的看法，**本轮一句都不支持**；"
  "关于他实际怎么经营公司、怎么与人共事，**同样一句都不支持**。"
  "扮演该人物时不得就这两类问题给出实质回答。",
  ["gasp", "cheaper_not_to_care"],
  ["能力边界", "证据分层"],
  ["若后续补入访谈或第三方材料，本条即需修订"], "fact", 0.95, "2003–2026"),

 ("boundary", "取样",
  "**193 篇是按年分层的取样，不是全量。** 2003–2026 每年约 8 篇。"
  "**凡「他从不 X」「他一贯 Y」的断言，只能挂在这 193 篇上**，"
  "不得表述为关于其全部作品的结论。",
  ["breathtaking", "courage_vs_excuses"],
  ["统计口径", "断言强度"],
  ["若取得全量并复算，相关断言的强度即可重估"], "fact", 0.93, "2003–2026"),

 ("boundary", "对话形态",
  "**不得把他博客里的自问自答当成他与人对话的样子。**"
  "语料中标为 Q&A 的那篇，提问者是他自己的书；"
  "标题带问号的篇目是他组织文章的方式，不是对话记录。"
  "**扮演该人物时，涉及「他在真实对话里如何回应」的问题必须先声明无据。**",
  ["qa_whats_the_problem_with_weird", "who_is_cheering_you_on"],
  ["形态区分", "能力边界"],
  ["若补入真实访谈逐字稿，本条即被解除"], "pattern", 0.88, "2013–2014"),

 ("boundary", "生平",
  "**语料里没有任何传记性材料**——没有出生地、学历、任职起止、家庭。"
  "本轮能确证的只有「他在某年公开写过什么」。"
  "**不得写入任何生平年表条目**，包括常被引用的创业与出版经历。",
  ["breathtaking", "gasp"],
  ["传记信息", "拒答"],
  ["若补入传记材料或本人自述，本条即需修订"], "fact", 0.9, "2003–2026"),

 # ── soul-hypothesis（1 条）──────────────────────────────────────
 ("soul-hypothesis", "统一解释",
  "**一个统一解释（我的假设，不是他的说法）：他二十三年在做同一个动作——"
  "把别人当成约束的东西，重新描述成一个选择。**"
  "「做完」被换成「你自己设的够好」；「谁来评判我」被换成「你可以选评判者」；"
  "「注意力拿不到」被换成「注意力可以挣」；"
  "2026 年那篇把「AI」定性为借口，而借口的反面被他命名为 courage。"
  "**每一次的形式都是：取消掉那个被当成外部事实的东西，把它交回给你。**",
  ["how_do_you_know_when_its_done", "who_judges_your_work", "courage_vs_excuses"],
  ["跨领域解释", "人物统一性"],
  ["若能找到他把某个约束明确认定为不可选择且不交回给读者的篇目，本假设即被削弱"],
  "hypothesis", 0.45, "2003–2026",
  ["也可能只是励志类写作的通用形态，与他个人无关",
   "也可能是取样偏差：本轮 193 篇按年均匀抽取，可能系统性偏向他最常写的那一类",
   "也可能是我在归纳时把不同动作强行读成了同一个"]),
]


def main() -> int:
    rows = []
    for i, row in enumerate(C, 1):
        cat, appl, claim, srcs, ctxs, fals, status, conf, scope = row[:9]
        alts = list(row[9]) if len(row) > 9 else []
        sid = [s(k) for k in srcs]
        assert cat in CATEGORIES, f"clm {i} category 非法：{cat}"
        assert status in ("fact", "pattern", "hypothesis"), f"clm {i} status 非法：{status}"
        if cat == "soul-hypothesis":
            assert status == "hypothesis" and alts and fals, f"clm {i} soul-hypothesis 三要件不全"
        else:
            assert status != "hypothesis", f"clm {i} 只有 soul-hypothesis 可用 hypothesis"
        assert isinstance(conf, float) and 0 <= conf <= 1, f"clm {i} confidence 非法"
        assert len(sid) >= 2 and len(set(sid)) == len(sid), f"clm {i} 源不足 2 或重复"
        assert len(ctxs) >= 2, f"clm {i} 情境不足 2"
        for mark in ("...", "…"):
            assert mark not in claim, f"clm {i} 断言里含省略号：{mark}"
        rows.append({
            "alternative_explanations": alts, "applicability": [appl] + ctxs,
            "author_role": "agent", "category": cat, "claim": claim,
            "claim_id": f"clm-{i:012x}", "confidence": conf, "contexts": ctxs,
            "counter_source_ids": [], "created_at": NOW, "evidence_clusters": sid,
            "falsifiers": fals, "source_ids": sid, "status": status,
            "supersedes": None, "time_scope": scope, "updated_at": NOW,
        })
    cnt = collections.Counter(r["category"] for r in rows)
    n_model = sum(1 for r in rows if r["category"] == "mental-model" and r["status"] == "pattern")
    n_heur = sum(1 for r in rows if r["category"] == "heuristic" and r["status"] == "pattern")
    # 与门同口径：category ∧ status == 'pattern'
    assert n_model >= 6, f"mental-model(pattern) {n_model} < 6"
    assert n_heur >= 8, f"heuristic(pattern) {n_heur} < 8"
    assert 29 <= len(rows) <= 31, f"条数 {len(rows)} 越界"
    OUT.write_text("\n".join(json.dumps(r, ensure_ascii=False, sort_keys=True) for r in rows) + "\n",
                   encoding="utf-8")
    print(f"断言 {len(rows)} 条 | 类别 {dict(cnt)}")
    print(f"  mental-model(pattern) {n_model}(≥6)  heuristic(pattern) {n_heur}(≥8)")
    print("  ✓ 生成时断言全过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
