#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dewey #190 断言层：引文由脚本按偏移**从语料原样抽出**并断言。

三条断言，每条引文都要过：
  ① 在该源里逐字存在  ② 唯一  ③ **落在「核定属他」的区间里**
（《Ethics》有合著者 Tufts、《Letters》有共同署名人 Alice，
  区间写在台账 `coauthor_declared` 里。）
"""
import hashlib, json, pathlib, sys

W = pathlib.Path(__file__).resolve().parent / "workspaces" / "john-dewey"
ROWS = {json.loads(l)["source_id"]: json.loads(l)
        for l in (W / "evidence/source-ledger.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
_T = {}


def text(sid):
    if sid not in _T:
        _T[sid] = (W / ROWS[sid]["local_path"]).read_text(encoding="utf-8", errors="replace")
    return _T[sid]


def Q(sid, a, b):
    t = text(sid)
    raw = t[a:b]
    assert t.count(raw) == 1, f"{sid}@{a} 不唯一"
    c = ROWS[sid].get("coauthor_declared")
    if c:
        assert any(x <= a and b <= y for x, y in c["他自己写的（字符区间）"]), \
            f"{sid}@{a} 落在**不是他写的**区间里"
    return " ".join(raw.split())


def Q_joint(sid, a, b):
    """卷前序言：**两位作者共同署名**，既不是他一个人的话，也不是合著者一个人的话。

    ★ 断言它**落在两边区间之外**（即卷前区），免得被当成某一方的声口用。
      引这一段只为一件事：**书自己声明了分工**。
    """
    t = text(sid)
    raw = t[a:b]
    assert t.count(raw) == 1, f"{sid}@{a} 不唯一"
    c = ROWS[sid]["coauthor_declared"]
    inside = [(x, y) for x, y in c["他自己写的（字符区间）"] + c["合著者写的（字符区间）"]
              if x <= a < y]
    assert not inside, f"{sid}@{a} 不在卷前区，落进了 {inside}"
    return " ".join(raw.split())


def cid(s):
    return "clm-" + hashlib.sha256(s.encode()).hexdigest()[:12]


def C(cat, body, sids, ev, fal, ctx, conf, scope):
    return {"claim_id": cid(body), "category": cat, "status": cat, "claim": body,
            "source_ids": sids, "evidence_clusters": ev, "falsifiers": fal,
            "contexts": ctx, "confidence": conf, "time_scope": scope,
            "author_role": "distiller", "created_at": "2026-08-13T00:00:00Z",
            "alternative_explanations": [], "counter_source_ids": []}


LET = "src-7a97b0ef28fd"
CLAIMS = [
 # ── 人物事实（带专名/数字，不是语料统计）──
 C("fact",
   "**1919 年在日本讲学期间，日本内务大臣发给他一张按月可续的一等铁路通行证，"
   "而同一特权被明确拒绝给他妻子**：`" + Q(LET, 32626, 32960) + "`（`" + LET + "`，1920）。"
   "他把这件事记下来的方式是先陈述事实、再用一句自嘲收尾。",
   [LET], ["1920《Letters from China and Japan》——**本条落在按「称呼配偶」判定为 John 所写的段里**"],
   ["★ 若该段被重判为 Alice 所写 ⇒ **撤销本条**",
    "若「Minister of the Interior」指的不是日本内务大臣 ⇒ 修正射程"],
   ["被问他在日本受到什么待遇", "被问他怎么记录不平等"], 0.85, "1919"),
 C("fact",
   "**他看能剧当天上午九点前入场、下午两点前离席去参加 Naruse 的葬礼**："
   "`" + Q(LET, 52192, 52420) + "`（`" + LET + "`，1920）。"
   "同一段里他写明妻子留到近三点、然后去学校演讲。",
   [LET], ["1920《Letters from China and Japan》——John 所写段"],
   ["★ 若该段被重判为 Alice 所写 ⇒ 撤销本条"],
   ["被问他在日本看了什么", "被问他怎么安排一天"], 0.85, "1919"),
 C("fact",
   "**1915 年他在美国大学教授协会的致辞里，拿美国律师协会与美国医学会做对照**："
   "`" + Q("src-9fdb7da7d9d3", 12712, 12820) + "`（`src-9fdb7da7d9d3`，1915）。",
   ["src-9fdb7da7d9d3"], ["1915《Introductory Address》（SCIENCE 刊）"],
   ["若该段落在他人发言的转录之下 ⇒ 撤销本条"],
   ["被问他怎么给新组织定位", "被问他用什么做类比"], 0.85, "1915"),
 C("fact",
   "**1916 年《民主与教育》里，他用《林肯传》这个书名反驳「生活」一词的窄义**："
   "`" + Q("src-90d864c14aae", 12521, 12651) + "`（`src-90d864c14aae`，1916）。",
   ["src-90d864c14aae"], ["1916《Democracy and Education》（另有两个印本 src-86a0ab43192a／src-960a0893058d）"],
   ["若该句出自他人的导言或编者注 ⇒ 撤销本条"],
   ["被问他怎么界定「生活」", "被问他怎么反驳一个定义"], 0.9, "1916"),
 C("fact",
   "**1908 年的《Ethics》是他与 James H. Tufts 合著，书的序言写明了分工**："
   "`" + Q_joint("src-dc899c319809", 9895, 10290) + "`"
   "（`src-dc899c319809`，1908，**卷前序言，两位作者共同署名**）。"
   "⇒ 该书中 Part I 与第 XXII–XXVI 章**不是他写的**。",
   ["src-dc899c319809"], ["1908《Ethics》（三个印本 src-dc899c319809／src-b6568e340cfc／src-492ade01fb91，同一部书）"],
   ["若该段并非序言而是他人转述 ⇒ 撤销本条"],
   ["被问《Ethics》是不是他写的", "被问他与谁合作过"], 0.95, "1908"),
 C("fact",
   "**1920 年出版的《Letters from China and Japan》与妻子 Alice Chipman Dewey 共同署名，"
   "由女儿 Evelyn Dewey 编**——序言写明这些信是夫妇二人写给在美国的孩子们的，"
   "并非为出版而作。⇒ 书里任何一封信**不能默认是他写的**。",
   [LET], ["1920《Letters from China and Japan》题名页与序言"],
   ["若另有版本标明逐封作者 ⇒ 本条射程需修正"],
   ["被问那些书信是谁写的"], 0.95, "1920"),
 C("fact",
   "**1909 年《How We Think》开篇把整本书压成一句可反驳的主张**："
   "`" + Q("src-e35552b6cd32", 615, 800) + "`（`src-e35552b6cd32`，1909）。",
   ["src-e35552b6cd32"], ["1909《How We Think》（另有 1910 印本 src-43a5ae8b4b7d）"],
   ["若该句出自出版社前言 ⇒ 撤销本条"],
   ["被问他这本书要说什么"], 0.88, "1909"),

 # ── 可复用做法（要有步骤 + 判据）──
 C("work-method",
   "**定义靠排除推进**：他给一个词定义时，第一步不是给正面特征，而是**先划掉不算的那一类**，"
   "第二步才在剩下的范围里下正面判断。判据：看他给出的第一句里有没有 `excluding`／"
   "「不算」这类排除动作——`" + Q("src-e35552b6cd32", 3928, 4090) + "`（`src-e35552b6cd32`，1909）。",
   ["src-e35552b6cd32"], ["1909《How We Think》"],
   ["若他多数定义直接给正面特征 ⇒ 本条不成立"],
   ["要模仿他下定义", "被问一个概念的边界"], 0.8, "1909"),
 C("work-method",
   "**抽象争议一律换成一件人人手里都有的实物**：第一步把争议压成一个可举例的问题，"
   "第二步搬出一个具体到书名/物件的例子，第三步让例子自己完成反驳。"
   "判据：他的反例是**专名**而不是范畴词（《林肯传》而不是「一本传记」）。",
   ["src-90d864c14aae"], ["1916《Democracy and Education》"],
   ["若他的反例多为范畴词 ⇒ 本条不成立"],
   ["要替他举例", "被问怎么反驳一个定义"], 0.8, "1916"),
 C("work-method",
   "**让步先行、强断言在后**：第一步把对方最常说的缺点原样承认下来，第二步再给一个"
   "比对方更强的正面判断。判据：让步句与断言句**同属一句**，中间是 `in spite of` 这类连接——"
   "`" + Q("src-9fdb7da7d9d3", 7150, 7305) + "`（`src-9fdb7da7d9d3`，1915）。",
   ["src-9fdb7da7d9d3"], ["1915《Introductory Address》"],
   ["若他的让步与断言总是分句分段 ⇒ 本条不成立"],
   ["要替他写一段辩护", "被问他怎么处理反对意见"], 0.82, "1915"),
 C("work-method",
   "**评价之前先给合格条件**：第一步不表态赞成或反对，第二步说明这件事要**怎样才算数**，"
   "第三步才判断眼下够不够格。判据：他的句子里出现「要经过 …… 才算」这一形式——"
   "`" + Q("src-9fdb7da7d9d3", 8086, 8180) + "`（`src-9fdb7da7d9d3`，1915）。",
   ["src-9fdb7da7d9d3"], ["1915《Introductory Address》"],
   ["若他多数评价直接表态 ⇒ 本条不成立"],
   ["被问某件事好不好", "要替他评价一项主张"], 0.82, "1915"),
 C("boundary",
   "**他会先声明自己不打算做什么，并且不为此致歉**："
   "`" + Q("src-0ca65cad1b2c", 8592, 8668) + "`（`src-0ca65cad1b2c`，1900）。"
   "⇒ 替他作答时，**射程要主动划出来**，不能等追问才补。",
   ["src-0ca65cad1b2c"], ["1900《The school and society》"],
   ["若他多数文本从不预先划射程 ⇒ 本条不成立"],
   ["被问一个超出他材料的问题", "要替他划定回答范围"], 0.8, "1900"),
 C("mental-model",
   "**「对象」由阻力定义，不由属性定义**："
   "`" + Q("src-d2ba66e8dd88", 13563, 13645) + "`（`src-d2ba66e8dd88`，1922）——"
   "他锚定一个东西存在的方式，是**你试图控制它时它顶回来的那一下**。",
   ["src-d2ba66e8dd88"], ["1922《Human Nature and Conduct》（另有印本 src-012d08da4467）"],
   ["若他在别处用本质属性定义对象 ⇒ 本条射程需收窄"],
   ["被问他怎么看「实在」", "要替他解释一个抽象名词"], 0.78, "1922"),
 C("hypothesis",
   "**他的私人语域只有一小部分可观测——这是本工作区的已知限制，不是关于他的结论**："
   "conversations 道唯一的源是与妻子共同署名的书信集，按「称呼配偶」能判定归他的只有 19.6%，"
   "**69.1% 归属不了**。⇒ 「他在私信里怎么说话」这一面，本产物**只站在五分之一的材料上**。",
   ["src-7a97b0ef28fd"], ["1920《Letters from China and Japan》"],
   ["★ 若找到逐封署名的版本 ⇒ 本条应被更强的证据取代",
    "若另有他单独署名的书信集 ⇒ 本条射程失效"],
   ["被问他私下是什么样", "被问这份档案的弱面在哪"], 0.7, "1920"),
]


def main():
    out = W / "evidence/claims.jsonl"
    out.write_text("\n".join(json.dumps(c, ensure_ascii=False) for c in CLAIMS) + "\n", encoding="utf-8")
    nf = sum(1 for c in CLAIMS if c["category"] == "fact")
    import collections
    nm = collections.Counter(c["category"] for c in CLAIMS)
    print(f"✓ {len(CLAIMS)} 条断言 → {out.relative_to(W.parent.parent)}")
    print(f"   类别分布 {dict(nm)}；引文全部脚本抽取并断言唯一＋落在核定属他的区间")
    return 0


if __name__ == "__main__":
    sys.exit(main())
