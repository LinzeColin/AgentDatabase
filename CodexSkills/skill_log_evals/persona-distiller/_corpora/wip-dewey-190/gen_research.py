#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按已核偏移**从语料原样抽出**引文，生成 Dewey #190 的六条研究道。

★ 引文一律由本脚本定位并断言，**不手抄**——手抄偏移的教训见踩坑库。
★ 每条断言三件事：① 在该源里逐字存在；② 唯一；③ 落在「核定属他」的区间里。
"""
import json, pathlib, sys

W = pathlib.Path(__file__).resolve().parent / "workspaces" / "john-dewey"
ROWS = {json.loads(l)["source_id"]: json.loads(l)
        for l in (W / "evidence/source-ledger.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
_CACHE = {}


def text(sid):
    if sid not in _CACHE:
        _CACHE[sid] = (W / ROWS[sid]["local_path"]).read_text(encoding="utf-8", errors="replace")
    return _CACHE[sid]


def Q(sid, start, end):
    """抽 [start,end) 并断言逐字唯一、且落在核定属他的区间里。"""
    t = text(sid)
    raw = t[start:end]
    assert t.count(raw) == 1, f"{sid}@{start} 不唯一"
    c = ROWS[sid].get("coauthor_declared")
    if c:
        ok = any(a <= start and end <= b for a, b in c["他自己写的（字符区间）"])
        assert ok, f"{sid}@{start} 落在**不是他写的**区间里"
    return " ".join(raw.split())


def head(sid):
    r = ROWS[sid]
    return f"`{sid}`（{r.get('published_at')}，《{(r.get('title') or '').strip()}》）"


# (源, 起, 止, 小标题, 判据)
WRITINGS = [
 ("src-0ca65cad1b2c", 7299, 7466, "他先把「我要你看的是哪一件」单独说一句，再展开",
  "整句的主干是「It is to this … that I especially ask your attention」——\n"
  "**先划定注意力的落点，再补充那件事是什么**。他不是先讲内容再总结，\n"
  "而是把「请你看这里」做成一个独立动作。"),
 ("src-e35552b6cd32", 3928, 4090, "定义靠**排除**推进：先说不算什么",
  "「the term is restricted by **excluding** whatever is directly presented」——\n"
  "他给「思维」下定义的办法是一层层减：先把直接看到、听到、闻到、尝到的排除出去。\n"
  "判据：**减法先于加法**，被排除的那一项每次都写明。"),
 ("src-90d864c14aae", 12521, 12651, "用一个具体书名去驳一个抽象定义",
  "谈「生活」这个词的射程时，他不举抽象反例，而是搬出**《林肯传》**：\n"
  "翻开它不会期待看到一篇生理学论文。判据：**抽象争议一律换成一个人人手里都有的实物**。"),
 ("src-d2ba66e8dd88", 13563, 13645, "从「什么在顶回来」定义对象",
  "「we are acutely aware of what **resists** us」——他定义「对象」不靠属性，\n"
  "靠**它在你试图控制时顶回来的那一下**。判据：概念用「遇到阻力的经验」来锚，不用本质。"),
 ("src-e35552b6cd32", 615, 800, "书的立场在开篇就说成一句可反驳的断言",
  "「This book represents the conviction that …」——他把整本书压缩成一句**可以被反对**的主张，\n"
  "而不是一段主题描述。判据：**开篇给的是立场，不是范围**。"),
 ("src-0ca65cad1b2c", 8592, 8668, "先声明自己不打算做什么",
  "「I make no apology for not dwelling at length upon …」——\n"
  "在展开之前**先把自己不会做的事说清楚**，且不为此致歉。\n"
  "判据：射程是主动划的，不是被追问出来的。"),
]

CONVERSATIONS = [
 ("src-7a97b0ef28fd", 11427, 11640, "写信时先报自己的惊讶程度，再给理由",
  "「I can't get over my astonishment at …」——**情绪在前、事实在后**，\n"
  "与他著作里「先立论后举证」的次序正好相反。判据：私信里他允许自己先说反应。"),
 ("src-7a97b0ef28fd", 13539, 13650, "细节精确到工具",
  "吃的是「a regular Japanese lunch」，而他补了一句**用筷子吃的**。\n"
  "判据：**记录里带着可核对的具体动作**，不停在「体验很好」这一层。"),
 ("src-7a97b0ef28fd", 18130, 18225, "用可数的量描述一天",
  "「we have only had four Japanese callers and two American ones」——\n"
  "「今天比较清静」这句判断后面**跟着数字**。判据：主观形容词后面接可数事实。"),
]

EXPRESSION = [
 ("src-9fdb7da7d9d3", 7150, 7305, "让步之后才下强断言",
  "「in spite of the deficiencies we so freely deplore, no country has at any time accomplished more」——\n"
  "**先承认对方常说的缺点，再给一个更强的正面判断**。判据：让步不是修辞缓冲，是把对手的论据先收进自己这边。"),
 ("src-9fdb7da7d9d3", 8086, 8180, "给「怎样才算数」定条件",
  "谈公共意见时他不停在赞成或反对，而是补一句**成立的条件**：\n"
  "要经过 deliberate inquiry and discussion 才算 intelligently formed。\n"
  "判据：**评价一件事之前先说它合格的条件**。"),
 ("src-bc5eed8386ff", 3565, 3670, "把「做不到」说成一句平直的事实",
  "「It is not practicable to attempt to assemble all …」——\n"
  "会长致辞里，他对做不到的事**不铺垫、不道歉**，一句话结掉再转向可行的部分。"),
]

EMPTY = {
 "04-external": ("External accounts",
   "**本道 0 份（train split）。**\n\n"
   "阶段 2 的分道实测：39 份语料全部落在 writings／conversations／expression 三道，\n"
   "`external`（他人写他的记述）一份都没有——抓源用的是 `creator:\"Dewey, John\"`，\n"
   "**按定义只会捞到署他名的东西**。\n\n"
   "★ 这不是「没有这类材料」，是**这一轮没有去取**。要补就得换检索式\n"
   "（按题名检索写他的传记/评论），那属于新一轮抓源，不在本轮射程内。"),
 "05-decisions": ("Decisions and judgments",
   "**本道 0 份（train split）。**\n\n"
   "他是哲学家与教育学者，不是法官或行政首长；本轮语料里没有\n"
   "「他做判断并留下正式记录」那一类文件（判决、裁定、官方报告）。\n\n"
   "★ 与 04 不同，这一条**大概率是真的没有**，而不是没去取——\n"
   "但本轮**没有为此专门检索过**，所以只能说「本轮语料里没有」。"),
 "06-timeline": ("Timeline",
   "**本道 0 份（train split）。**\n\n"
   "**这一面我说不出。** 不是「他没有」，是本工作区手边取不到可用的材料；\n"
   "被问到与此有关的事，就直说说不出，**不要推测**。\n\n"
   "★ 这一条有明确的解锁条件：**随年份滚动**。分界每年元旦前移一年，\n"
   "他 1930 年后的作品会逐年进入公有领域。"),
}


def render(title, items, lane_note=""):
    out = [f"# {title}", "", "## Scope and assigned sources", "",
           "（本节由 `emit_lane_scope.py` 机械填入，不要手改）", "",
           "## Source-linked observations", ""]
    if lane_note:
        out += [lane_note, ""]
    for i, (sid, a, b, h, why) in enumerate(items, 1):
        out += [f"### O-{i} · {h}", "", f"{head(sid)}：", "",
                f"> `{Q(sid, a, b)}`", "", why, ""]
    return "\n".join(out) + "\n"


def main():
    R = W / "references/research"
    R.mkdir(parents=True, exist_ok=True)
    (R / "01-writings.md").write_text(render("Writings and systematic works", WRITINGS), encoding="utf-8")
    (R / "02-conversations.md").write_text(render(
        "Conversations and correspondence", CONVERSATIONS,
        "★★ **本道唯一的源是与妻子 Alice 共同署名的书信集**，书里没有逐封署名。\n"
        "台账 `coauthor_declared` 里按「写信人怎么称呼配偶」切了 112 段：\n"
        "**John 10,063 词（19.6%）／Alice 5,792 词（11.3%）／归属不了 35,535 词（69.1%）**。\n"
        "下面每条引文都由 `gen_research.py` 断言**落在 John 那 19.6% 里**；\n"
        "未判的 69.1% 一个字都没用。"), encoding="utf-8")
    (R / "03-expression.md").write_text(render("Expression and public voice", EXPRESSION), encoding="utf-8")
    for name, (title, body) in EMPTY.items():
        (R / f"{name}.md").write_text(
            f"# {title}\n\n## Scope and assigned sources\n\n"
            f"（本节由 `emit_lane_scope.py` 机械填入，不要手改）\n\n"
            f"## Source-linked observations\n\n{body}\n", encoding="utf-8")
    n = len(WRITINGS) + len(CONVERSATIONS) + len(EXPRESSION)
    print(f"✓ 六道写好；观察 {n} 条，引文全部由脚本从语料原样抽出并断言唯一")
    print(f"   writings {len(WRITINGS)}｜conversations {len(CONVERSATIONS)}｜expression {len(EXPRESSION)}"
          f"｜external/decisions/timeline 各 0（无材料，理由写在道里）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
