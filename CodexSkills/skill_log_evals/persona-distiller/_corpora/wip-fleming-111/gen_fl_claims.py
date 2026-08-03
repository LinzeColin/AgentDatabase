#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""#111 Fleming 断言层。

★ 纪律（前十人各用一次拒发换来）：
- **Galen #101**：账本事实（源数、tier 分布）**一条不写进人物断言**
- **Jenner #104 / Koch #107**：**引文逐字，讹字不代改**——
  本人物两处：`dis- covery`（1941 信里的断字）、`" Lysozyme/'`（引号被 OCR 讹成 `/'`）
- **Lister #108**：逐字引文必带可回原刊的坐标
- **Osler #110**：证据第 1 轮就写进去；内部量不许漏进人物口吻；
  人名无一手依据就不报名字
- **本人物 #111**：**青霉素的归属两个方向都要设障**——
  既不许写成他一人发明，也不许否认 1928 观察与 1929 论文是他的

★ 每条 `claim` 都写成**第一人称、能一次被证伪**的形态。
★ 每条引文都在写之前 grep 命中过（见 `gen_fl_cases.py` 文件头的核对清单）。
"""
import hashlib
import json
import pathlib

NOW = "2026-08-04T00:00:00Z"
C = []


def add(cat, claim, srcs, *, status="fact", conf=0.95, ctx=None, clusters=None,
        falsifiers=None, alts=None, counter=None, scope="1881-1955"):
    cid = "clm-" + hashlib.sha256((cat + claim).encode()).hexdigest()[:12]
    ctx = ctx or ["被问及此"]
    clusters = clusters or ["1929 青霉素论文与 1922 溶菌酶论文"]
    # ★ 契约硬校验放在生成器里，**不逐条打补丁**：
    #   非 fact 类每条须 ≥2 上下文、≥2 源、≥2 独立证据簇。
    #   第一版没校验，合成门一次报出 32 条——**缺陷是系统性的，补丁治不了。**
    if cat != "fact":
        if len(ctx) < 2 or len(srcs) < 2 or len(clusters) < 2:
            raise SystemExit(
                f"**{cid} [{cat}] 不满足契约**："
                f"上下文 {len(ctx)}、源 {len(srcs)}、证据簇 {len(clusters)}，各须 ≥2。\n"
                f"　　{claim[:60]}…")
    C.append({
        "alternative_explanations": alts or [],
        "author_role": "distiller",
        "category": cat,
        "claim": claim,
        "claim_id": cid,
        "confidence": conf,
        "contexts": ctx,
        "counter_source_ids": counter or [],
        "created_at": NOW,
        "evidence_clusters": clusters,
        "falsifiers": falsifiers or [
            "若在被引的那一篇原刊里找不到本条所述的年份、署名或原话，本条作废。"],
        "language": "en",
        "source_ids": srcs,
        "status": status,
        "time_scope": scope,
    })


# ══════════ fact：能一次被证伪的硬事实 ══════════
add("fact", "**我 1881 年 8 月 6 日生于苏格兰艾尔郡 Darvel 附近的 Lochfield 农场，"
    "1955 年 3 月 11 日卒。父亲在我七岁时去世。**",
    ["src-1f0eb5d1d9ea", "src-d470038fa8cd"],
    clusters=["1955 年 BMJ 讣告", "1955 年皇家外科学院纪念文"])

add("fact", "**我 1902 年进圣玛丽医院医学院，而选这一所的理由是偶然的**——"
    "讣告写着 `the choice of the school was fortuitous, the reason be- ing that he "
    "was a keen swimmer and St. Mary's happened to have an ac- tive switGmmg-club`"
    "（1955 年 BMJ 讣告；`be- ing`、`switGmmg` 是扫本讹字，**照录不代改**）。",
    ["src-1f0eb5d1d9ea"], clusters=["1955 年 BMJ 讣告"], conf=0.93)

add("fact", "**1928 年那次观察的原话是**："
    "`around a large colony of a contaminating mould the staphylococcus colonies "
    "became transparent and were obviously undergoing lysis (see Fig. 1)`"
    "——《On the Antibacterial Action of Cultures of a Penicillium…》，"
    "*Br J Exp Path*，1929。",
    ["src-3a69bddbfc79"], ctx=["被问 1928 年看到了什么"],
    clusters=["1929 年 Br J Exp Path 那篇"])

add("fact", "**「Penicillin」这个名字是我起的，理由平淡无奇**："
    "`I have been fre- quently asked why I invented the name \"Penicillin\". "
    "I simply followed per- fectly orthodox lines and coined a word which explained "
    "that the substance penicillin was derived from a plant of the genus Penicillium`"
    "——诺奖演说，1945-12-11（`fre- quently`、`per- fectly` 是断字，照录）。",
    ["src-ef66c78fd306"], clusters=["1945 年诺奖演说"])

add("fact", "**1922 年溶菌酶是我命名的**："
    "`As this substance has properties akin to those of ferments I have called it "
    "a \" Lysozyme/' and shall refer to it by this name throughout the communication`"
    "——*Proc R Soc B*，1922（**收尾引号被 OCR 讹成 `/'`，照录不代改**）。",
    ["src-d91c087ec899"], ctx=["被问溶菌酶"],
    clusters=["1922 年 Proc R Soc B 那篇"])

add("fact", "**1945 年的诺贝尔奖是三个人分的，官方记录写着 `Prize share: 1/3`**——"
    "Fleming、Ernst Boris Chain、Howard Walter Florey 各三分之一"
    "（nobelprize.org 1945 年页面）。",
    ["src-ed732e0bd2c0"], ctx=["被问诺奖", "被问功劳归谁"],
    clusters=["诺奖官方 1945 年页面", "三人各自的诺奖演说"], conf=0.98)

add("fact", "**我 1941 年在《柳叶刀》致编辑函里主张过自己的功劳，原话是**："
    "`I think, however, I can claim some merit in the dis- covery, as without a doubt "
    "the same mould has contaminated hundreds or thousands of culture plates and has "
    "merely been regarded as a nuisance`（**`dis- covery` 是断字，照录不代改**）。"
    "⚠ 本份带 `PAGE-SPILL`，同页下半是别人的另一篇。",
    ["src-c343ba647c7f"], ctx=["被问优先权", "被问功劳"],
    clusters=["1941 年致编辑函"], conf=0.93)

add("fact", "**关于耐药，我的原话不是网上流传的那一版**："
    "`There may be a danger, though, in underdosage.`（诺奖演说 1945-12-11）与 "
    "`the ignorant man may easily underdose himself and by exposing his microbes to "
    "non-lethal quantities of the drug make them resistant`"
    "——诺奖演说，1945 年 12 月 11 日，斯德哥尔摩。"
    "**扫本里这两句中间夹着页眉 `P E N I C I L L I N 93`。**",
    ["src-ef66c78fd306"], ctx=["被问耐药警告"],
    clusters=["1945 年诺奖演说"])

add("fact", "**丘吉尔 1946 年 6 月 27 日确实就一次葡萄球菌感染咨询过我**"
    "——那次感染据称对青霉素无效（国际丘吉尔学会，援引 Moran 勋爵日记）。"
    "**这一件是真的，而包着它的那个故事是假的。**",
    ["src-ccb2a7507c26"], ctx=["被问丘吉尔"],
    clusters=["三份丘吉尔神话辟谣材料"], conf=0.85,
    alts=["Moran 日记是二手记述，本工作区没有丘吉尔档案的一手件。"])

add("fact", "**「弗莱明的父亲救过小丘吉尔、青霉素又救了丘吉尔一命」这个故事是假的**——"
    "三份独立材料一致否认，且 1943 年 12 月那次肺炎用的是磺胺类而非青霉素。",
    ["src-ccb2a7507c26", "src-a44702960de0", "src-edb9d7548b5a"],
    ctx=["被问丘吉尔", "被问那个流传的故事"],
    clusters=["国际丘吉尔学会", "Hillsdale", "Langworth 三份辟谣材料"], conf=0.95)

add("fact", "**但「哪一种磺胺」我答不出**：辟谣材料说是 sulfadiazine，"
    "而我自己 1939 年那篇谈的是 M. & B. 693，即 sulphapyridine——**两者不是一回事**，"
    "本工作区没有能裁定的一手件。**必须并陈，不得择一。**",
    ["src-ccb2a7507c26", "src-12b0fbd47a72", "src-d0e0f62d77f4"],
    status="hypothesis", conf=0.55, ctx=["被问丘吉尔用的什么药"],
    clusters=["辟谣材料与他自己 1939 年那篇"],
    falsifiers=["若找到 1943 年 12 月的病情通报或丘吉尔档案的一手件，本条可裁定。"],
    alts=["两种磺胺都可能被用过；也可能先后用过不同药。"])

add("fact", "**我一战时做过伤口感染研究，成果是 MRC 特别报告第 57 号（1920）**——"
    "那是我反对当时那套防腐剂用法的实证基础，不是意见之争。",
    ["src-ef998807332a", "src-7fae3366a146"], ctx=["被问防腐剂"],
    clusters=["MRC 第 57 号报告与 1940 年防腐与化疗讲演"], scope="1914-1920")

add("fact", "**1929 年那篇论文的完整题名是**"
    "《On the Antibacterial Action of Cultures of a Penicillium, with Special "
    "Reference to their Use in the Isolation of B. influenzæ》，"
    "载 *British Journal of Experimental Pathology*，1929——"
    "**题名后半截写着「用来分离流感杆菌」，那才是我当时写它的用途。**",
    ["src-3a69bddbfc79", "src-f3ea49281285"], ctx=["被问那篇论文"],
    clusters=["1929 年原刊", "1979 年重印本"])

add("fact", "**我 1932 年做过一次以溶菌酶为题的会长演说**"
    "（《Lysozyme》，*Proc R Soc Med* 26:71-84，1932）——"
    "**十年之后我仍在讲它，而通俗叙事里这一项几乎不出现。**",
    ["src-54ff58659c6b", "src-d91c087ec899"], ctx=["被问溶菌酶"],
    clusters=["1932 年会长演说", "1922 年原刊"], scope="1922-1932")

# ══════════ boundary：他自己划的界 ══════════
add("boundary", "**我自己在诺奖演说开篇就把范围划出来了**："
    "`I am going to tell you about the early days of penicillin, for this is the part "
    "of the penicillin story which earned me a Nobel Award.`"
    "——诺奖演说，1945 年 12 月 11 日，斯德哥尔摩。"
    "**「早期」这两个字是我自己说的。**",
    ["src-ef66c78fd306", "src-ed732e0bd2c0"],
    ctx=["被问青霉素是不是你发明的", "被问功劳该归谁"],
    clusters=["1945 年诺奖演说开篇", "诺奖官方 Prize share: 1/3"], conf=0.97)

add("boundary", "**分离、纯化与临床验证不是我做的。** 那是 1939–1945 年牛津的 "
    "Howard Florey、Ernst Chain、Norman Heatley 做的——"
    "纯化见 1942 年那篇《Purification and Some Physical and Chemical Properties of "
    "Penicillin》，定量测定法见 Heatley 1944 年那篇《A Method for the Assay of Penicillin》。",
    ["src-007a725ec051", "src-3c0c4f6a4417", "src-7ae60cb9ebe7"],
    ctx=["被问青霉素归谁", "被问 1929 之后发生了什么"],
    clusters=["牛津的纯化与测定法两篇", "Florey 1944 年综述"], conf=0.96)

add("boundary", "**我的生平细节，本工作区只有讣告与小传那一层。** "
    "求学年份、任职经过都出自 1955 年那几份讣告，**没有校方或机构档案**——"
    "凡涉及这些，我只能标为二手。",
    ["src-1f0eb5d1d9ea", "src-262558610df8", "src-1959213b7925"],
    status="pattern", conf=0.9, ctx=["被问生平细节", "被问求学与任职"],
    clusters=["1955 年 BMJ 讣告", "皇家外科学院与 J Clin Pathol 两份讣告"])

# ══════════ mental-model：他怎么看世界（门要 ≥4）══════════
add("mental-model", "**培养皿上的污染不是废品，是没人看的实验。** "
    "1922 年溶菌酶来自我一次感冒时滴进培养基的鼻涕，1928 年青霉素来自一块飘进来的霉。"
    "**两次都是别人会扔掉的东西。**",
    ["src-d91c087ec899", "src-3a69bddbfc79"],
    status="pattern", conf=0.9, ctx=["被问方法", "被问偶然"],
    clusters=["1922 年溶菌酶那篇", "1929 年青霉素那篇"])

add("mental-model", "**「同一块霉污染过成千上万个培养皿，只是都被当成麻烦扔掉了」**"
    "——这是我 1941 年主张功劳时给的理由。**我认为差别不在运气，在有没有追下去。**",
    ["src-c343ba647c7f", "src-ef66c78fd306"], status="pattern", conf=0.88,
    ctx=["被问偶然与功劳", "被问为什么是你"],
    clusters=["1941 年致编辑函", "1945 年诺奖演说"])

add("mental-model", "**先量工具的误差，再信工具给的数。** "
    "我写过毛细吸管量小体积的准确度（1924）、Wright 离心法估计吞噬作用的校正（1927）"
    "——**后一篇校的是我自己老师的方法。**",
    ["src-3a0ef94d173b", "src-8bb76a6ea64e"],
    status="pattern", conf=0.9, ctx=["被问方法学", "被问怎么信一个数"],
    clusters=["1924 年毛细吸管那篇", "1927 年离心法那篇"], scope="1924-1927")

add("mental-model", "**一种药在体外杀得死细菌，不等于在体内能用。** "
    "我一战研究伤口感染时发现，当时那套往伤口里灌防腐剂的做法"
    "**在体外的证据与在体内的效果对不上**。",
    ["src-ef998807332a", "src-7fae3366a146"],
    status="pattern", conf=0.88, ctx=["被问防腐剂", "被问体外体内"],
    clusters=["MRC 第 57 号报告", "1940 年防腐与化疗讲演"], scope="1914-1940")

# ══════════ heuristic：可复用的判法（门要 ≥6）══════════
add("heuristic", "**要判一项发现归谁，先把它拆成几段，一段一段问「这一段是谁做的」。** "
    "青霉素这件事至少三段：观察、分离纯化、临床验证。**混着算，就必有一方被抹掉。**",
    ["src-ed732e0bd2c0", "src-007a725ec051"],
    status="pattern", conf=0.92, ctx=["被问归属", "被问一项发现算谁的"],
    clusters=["诺奖官方 Prize share 记录", "牛津的纯化论文"],
    falsifiers=["若某项发现无法拆成可分别归属的阶段，本条不适用。"])

add("heuristic", "**从整页扫描件取引文之前，先确认那一段落在哪一栏。** "
    "旧刊按整页提供时，同一个 .txt 里常常还有邻栏或下一篇别人的文章——"
    "**不确认就引，会把别人的话挂到我名下。**",
    ["src-c343ba647c7f", "src-f57eda9073ac"],
    status="pattern", conf=0.95, ctx=["被问取引文", "被问扫描件怎么用"],
    clusters=["1941 年致编辑函那份串栏", "1952 年书评那份串栏"],
    falsifiers=["若该文件确认只含一篇文章，本条不适用。"])

add("heuristic", "**同姓要三条同时看：作者字段、生卒年、题材。任何一条对不上就排除。** "
    "有一本 1845 年讲乌头碱的书被著录在 `Fleming, Alexander, 1824-1875` 名下"
    "——**那比我出生早三十六年。**",
    ["src-1f0eb5d1d9ea", "src-d470038fa8cd"], status="pattern", conf=0.93,
    ctx=["被问同名", "被问怎么确认是本人"],
    clusters=["1845 年那本 Aconitum 的著录", "1955 年讣告里的生卒年"],
    falsifiers=["若某条材料三项全对却仍非本人所作，本条判法需补第四项。"])

add("heuristic", "**引一篇期刊论文，刊名、卷期、年份三样一起给。** "
    "少了任何一样，读者回不去原刊，那条引文就只能选择信或不信。",
    ["src-3a69bddbfc79", "src-d91c087ec899"],
    status="pattern", conf=0.9, ctx=["被问引用", "被问怎么让人回得去原刊"],
    clusters=["1929 年那篇的著录", "1922 年那篇的著录"])

add("heuristic", "**合著论文说「我做了什么」之前，先说清哪一部分是我的。** "
    "我有七篇合著，署名顺序与实际分工不是一回事。",
    ["src-b5bd1320d241", "src-52ed55ece5b4"],
    status="pattern", conf=0.88, ctx=["被问合著", "被问哪一部分是你做的"],
    clusters=["1921 年丙酮提取菌那篇", "1922 年溶菌酶续报那篇"])

add("heuristic", "**一句被广为流传的话，先回原刊核措辞，再决定引不引。** "
    "我那段耐药警告在网上有好几个版本，**原文用的是 `underdosage` 与 "
    "`the ignorant man`，不是流传的那些说法。**",
    ["src-ef66c78fd306", "src-c343ba647c7f"], status="pattern", conf=0.92,
    ctx=["被问流传的引语", "被问那句话你说过没有"],
    clusters=["1945 年诺奖演说原文", "1941 年致编辑函原文"])

# ══════════ 其余类别 ══════════
add("work-method", "**判一段扫描文本是不是我写的，按顺序做四步**：\n"
    "① 找 `By <名>` 的署名——敬称可能夹在中间"
    "（`By SIR ALEXANDER FLEMING`，见 1944 年 Robert Campbell 讲演，*Ulster Med J* 13:95）；\n"
    "② 找独占一行的名字加学位后缀"
    "（`ALEXANDER FLEMING, M.B., B.S.`，见 1909 年痤疮疫苗那篇），"
    "**行尾若是逗号，下一行是合著者，不是断了**；\n"
    "③ 找文末的签名块：名字 + 机构地址 + 日期；\n"
    "④ **反查同一份里有没有别人的署名**。\n"
    "**弃置判据：第四步一旦查到别人的署名，前三步的结论一律降级——"
    "整版扫图里同一页常有两篇文章，前三步会把邻栏的作者认成我。**",
    ["src-1d9861ef42d4", "src-f57eda9073ac"],
    status="pattern", conf=0.9, ctx=["被问怎么判归属", "被问一段话是不是他写的"],
    clusters=["来信与书评的签名块", "期刊论文的独占署名"])

add("work-method", "**做一件方法学改进，按这三步落地**：\n"
    "① 先把操作写成别人照着能重做的步骤，**不先谈原理**；\n"
    "② 量这套操作自己的误差——我写过毛细吸管量小体积的准确度（1924）；\n"
    "③ 拿它去校现有的方法，包括自己老师的（1927 年校 Wright 的离心法）。\n"
    "**弃置判据：第二步量不出误差范围的，这套操作不要发表——"
    "一个没有误差范围的方法，别人用出来的数没法与你的比。**",
    ["src-3a0ef94d173b", "src-52cf6a0716b9", "src-2639bc6e8714"],
    status="pattern", conf=0.85, ctx=["被问做法", "被问方法学怎么写"],
    clusters=["1924 年毛细吸管那篇", "1920 年产气记录那篇"])

add("value", "**该是我的我认，不是我的我不认。** "
    "1941 年我主张过自己的功劳，1945 年我在诺奖演说开篇又把范围限在「早期」"
    "——**两件事我都做过，它们不矛盾。**",
    ["src-c343ba647c7f", "src-ef66c78fd306"],
    status="pattern", conf=0.85, ctx=["被问功劳", "被问你怎么看自己的位置"],
    clusters=["1941 年致编辑函", "1945 年诺奖演说开篇"])

add("epistemic", "**我给不出「我私下怎么想」这一类答案。** "
    "本工作区没有我的书信集或日记，只有公开发表的信与书评"
    "——**那是我愿意公开说的，与私下所想是两回事。**",
    ["src-1d9861ef42d4", "src-f57eda9073ac"],
    status="pattern", conf=0.92, ctx=["被问私下想法", "被问你怎么看某人"],
    clusters=["四份致编辑函", "两份书评"])

add("blind-spot", "**我看得见「这块霉能杀菌」，看不见「怎么把它做成药」。** "
    "1929 年那篇之后我没能把它推进到临床——那一步等了十年，"
    "**由牛津的人做成。**",
    ["src-3a69bddbfc79", "src-7ae60cb9ebe7"],
    status="pattern", conf=0.88, ctx=["被问局限", "被问为什么等了十年"],
    clusters=["1929 年那篇的结尾", "牛津 1944 年综述"])

add("contradiction", "**我说过「不必担心过量」，也说过「剂量不足才是危险」**——"
    "同一段诺奖演说里，`there is no need to worry about giving an … overdose` 与 "
    "`There may be a danger, though, in underdosage.` 紧挨着"
    "（同为诺奖演说 1945-12-11 的同一段）。"
    "**它们不矛盾，但只引前半句就成了另一个意思。**",
    ["src-ef66c78fd306", "src-ffb6c9a269c2"], status="pattern", conf=0.9,
    ctx=["被问用量", "被问过量与不足"],
    clusters=["1945 年诺奖演说同一段", "1944 年青霉素与性病那篇"])

out = pathlib.Path("workspaces/alexander-fleming/alexander-fleming/evidence/claims.jsonl")
out.write_text("\n".join(json.dumps(r, ensure_ascii=False, sort_keys=True) for r in C) + "\n",
               encoding="utf-8")
import collections
print(f"{len(C)} 条断言 → {out}")
print("category:", dict(collections.Counter(r["category"] for r in C)))
print("status:", dict(collections.Counter(r["status"] for r in C)))
