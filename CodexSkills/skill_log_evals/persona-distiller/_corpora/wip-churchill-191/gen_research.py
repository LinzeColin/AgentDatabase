#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Churchill #191 六条研究道：引文由脚本按偏移**从语料原样抽出**并断言。

★ 每条断言两件事：① 在该源里逐字存在 ② 唯一。
★★ 另一道纪律：候选一律先过 `flag_borrowed_voice.judge()`，判成借用声口的不用。
   两处硬约定（都是逐份读过原文之后定的）：
   · **《Lord Randolph Churchill》(1906) 整份不取引文**——那是他写他父亲的传记，
     满篇是转引的书信与校友回忆，且引语用**单引号**，判定器只认双引号，挡不住。
   · **《Savrola》(1900) 整份不取引文**——那是小说，里面的第一人称是虚构人物。
"""
import importlib.util
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
W = HERE / "workspaces" / "winston-churchill"
_spec = importlib.util.spec_from_file_location(
    "fbv", HERE.parent.parent / "_ledgers/_pipeline/flag_borrowed_voice.py")
fbv = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(fbv)

ROWS = {json.loads(l)["source_id"]: json.loads(l)
        for l in (W / "evidence/source-ledger.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
BANNED_SOURCES = {"src-c53e1c37f040", "src-0af00d0f0365", "src-cd511a154ee0"}
_T = {}


def norm(sid):
    if sid not in _T:
        _T[sid] = fbv.dehyphen((W / ROWS[sid]["local_path"]).read_text(encoding="utf-8", errors="replace"))
    return _T[sid]


def Q(sid, a, b):
    assert sid not in BANNED_SOURCES, f"{sid} 在禁取名单里"
    t = norm(sid)
    raw = t[a:b]
    assert t.count(raw) == 1, f"{sid}@{a} 不唯一"
    assert not fbv.judge(t, a, raw), f"{sid}@{a} 被判成**借用声口**"
    return " ".join(raw.split())


def head(sid):
    r = ROWS[sid]
    return f"`{sid}`（{r.get('published_at')}，《{(r.get('title') or '').strip()}》）"


WRITINGS = [
 ("src-925ef102d33e", 91424, 91580, "把「宗教狂热」这个现成解释先否掉，再给自己的",
  "「It is, I believe, an historical fact that the revolt of a great population has "
  "**never** been caused solely or even mainly by religious enthusiasm」——\n"
  "他不是补充一个新因素，而是**先把当时最流行的那个解释整条划掉**。\n"
  "判据：`I believe` 与 `an historical fact` 落在同一句里——**标明这是我的判断，同时把它当事实主张下**。"),
 ("src-934c9771e8e3", 16187, 16290, "用一句反讽收掉一场争论",
  "谈接种争议时他不站队，最后一句是：**若他们能发明一种防子弹的接种法，我马上去打**。\n"
  "判据：**争论以一个具体到荒谬的条件收尾**，而不是以结论收尾。"),
 ("src-615074b71a84", 33964, 34140, "把选择写成一句「负担不起」",
  "「we could not afford to remain 'in splendid isolation'」——\n"
  "他讲外交转向时不谈是非，谈**负担得起负担不起**。\n"
  "判据：战略判断用**成本语言**下，而且引号里那个现成说法**是被他拿来否掉的**。"),
 ("src-925ef102d33e", 40980, 41043, "手段与目的分两半说",
  "「It is the means by which we fight ; the end at which we aim.」——\n"
  "一句话拆成对仗的两半，**手段一半、目的一半**。判据：他给定义时爱用这种两半式。"),
]

TIMELINE = [
 ("src-0db9f607011e", 14406, 14490, "写童年时先立一个人物，再说自己其实没见过",
  "「'Little Ella', though **I never saw her**, became a feature in my early life.」——\n"
  "他先让这个人物在叙述里成立，**紧接着自己拆掉它的实在性**。\n"
  "判据：回忆里他会主动标出「这一段我并没亲见」。"),
 ("src-0db9f607011e", 14482, 14620, "细节精确到「她喜欢吃什么」",
  "紧接上一句，他列的是**她爱吃什么、怎么祷告、哪些地方淘气哪些地方乖**。\n"
  "判据：一个他明说没见过的人，**记忆里留下的却是可枚举的具体条目**。"),
]

EXTERNAL = [
 ("src-4603171fd82d", 34210, 34400, "同时代记录里，他被当作「政府代表」而不是演说家",
  "1908 年那场自由贸易大会的会议记录把他写成 **the President of the Board of Trade, "
  "and the representative of His Majesty's Government**。\n"
  "判据：**别人记录他时给的是职务**，而他自己写东西时几乎不提职务。"),
 ("src-4603171fd82d", 1059056, 1059240, "同一场会上有人当面说他的部门与他本人不一致",
  "会议记录里有人说：他的部门在推进保护主义的论证，**而他本人是个彻底的自由贸易者**。\n"
  "判据：这是**第三方留下的、与他自述不一致的一条**——external 道的价值正在于此。"),
]

EMPTY = {
 "02-conversations": ("Conversations and correspondence",
   "**本道 0 份（train split）。**\n\n"
   "本轮抓源用的是 IA 的 creator 检索式（按他的姓名），捞到的是署他名的著作；\n"
   "书信集、议会问答记录这一类**这一轮没有去取**。\n\n"
   "★ 这不是「没有这类材料」——他的书信与议会发言留存极多，\n"
   "而其中大部分的**编纂本出版于 1930 年之后**，落在公有领域分界之外。\n"
   "要补就得先分清哪些编纂本本身已进入公有领域，属新一轮抓源。"),
 "03-expression": ("Expression and public voice",
   "**本道 0 份（train split）。**\n\n"
   "★ 语料里确有一份演说汇编（《Great speeches of the war》，1915），\n"
   "但它被判成 **external／二手**：那是**别人编的汇编**，不是他自己出的讲辞集。\n"
   "⇒ 「他的公开讲话」这一面，本轮**只能隔着第三方编者看**。"),
 "05-decisions": ("Decisions and judgments",
   "**本道 0 份（train split）。**\n\n"
   "他 1908–1929 年间历任商务大臣、内政大臣、海军大臣、财政大臣，\n"
   "**公务文件极多**——但那些是政府档案，不在本轮 IA 抓源的射程里，\n"
   "且其中相当部分受官方档案规则约束。\n"
   "★ 这一条是「有而没去取」，**不是「没有」**。"),
}


def render(title, items, note=""):
    out = [f"# {title}", "", "## Scope and assigned sources", "",
           "（本节由 `emit_lane_scope.py` 机械填入，不要手改）", "",
           "## Source-linked observations", ""]
    if note:
        out += [note, ""]
    for i, (sid, a, b, h, why) in enumerate(items, 1):
        out += [f"### O-{i} · {h}", "", f"{head(sid)}：", "", f"> `{Q(sid, a, b)}`", "", why, ""]
    return "\n".join(out) + "\n"


def main():
    R = W / "references/research"
    R.mkdir(parents=True, exist_ok=True)
    note = ("★★ **两份源整份不取引文**（逐份读过原文之后定的）：\n"
            "`src-c53e1c37f040`《Lord Randolph Churchill》(1906) 是他写**他父亲**的传记，\n"
            "满篇转引书信与校友回忆，且引语用**单引号**——借用声口判定器只认双引号，挡不住；\n"
            "`src-0af00d0f0365`／`src-cd511a154ee0`《Savrola》(1900) 是**小说**，"
            "里面的第一人称是虚构人物。")
    (R / "01-writings.md").write_text(render("Writings and systematic works", WRITINGS, note), encoding="utf-8")
    (R / "06-timeline.md").write_text(render("Timeline", TIMELINE), encoding="utf-8")
    (R / "04-external.md").write_text(render("External accounts", EXTERNAL), encoding="utf-8")
    for name, (title, body) in EMPTY.items():
        (R / f"{name}.md").write_text(
            f"# {title}\n\n## Scope and assigned sources\n\n"
            f"（本节由 `emit_lane_scope.py` 机械填入，不要手改）\n\n"
            f"## Source-linked observations\n\n{body}\n", encoding="utf-8")
    n = len(WRITINGS) + len(TIMELINE) + len(EXTERNAL)
    print(f"✓ 六道写好；观察 {n} 条（writings {len(WRITINGS)}／timeline {len(TIMELINE)}／"
          f"external {len(EXTERNAL)}；conversations/expression/decisions 各 0，理由写在道里）")
    print("   每条引文都过了：逐字存在 ＋ 唯一 ＋ **不被判成借用声口**")
    return 0


if __name__ == "__main__":
    sys.exit(main())
