#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Brandeis #172 断言层生成器。

★ 每条引文都带 `source_id` 与**归一化偏移**，本脚本跑起来时**逐条回语料断言**：

    text = re.sub(r"\\s+", " ", dehyphen(open(local_path).read()))
    assert text[off:off+len(q)] == q

对不上就**当场退出**，不写文件 —— 断言层不许出现语料里没有的字。

★★ 两条本工作区特有的纪律，写在这里是因为它们决定了哪些句子**不能用**：

1. **第一人称不等于他。** 机械抽出的 14 条 writings 候选里 **9 条不是他**
   （Reusswig 3 / Towne 3 / North 法官 1 / Fisher 1 / 工厂主 1）。
   本文件用到的每一条都跑过 `flag_borrowed_voice`（七条机制）**且人读过前 700 字**。
2. **《Business—a profession》前 62,094 / 64,956 / 73,433 字是别人的导言**
   （Ernest Poole；1925 版还有 Frankfurter 的注）。
   本文件里凡取自这三份的偏移，**必须大于各自的正文起点**，脚本会断言。
"""
import hashlib
import json
import pathlib
import re
import sys

WS = re.compile(r"\s+")
HERE = pathlib.Path(__file__).resolve().parent
W = HERE / "workspaces" / "louis-brandeis"
LEDGER = W / "evidence" / "source-ledger.jsonl"
OUT = W / "evidence" / "claims.jsonl"
NOW = "2026-08-13T00:00:00Z"

# 《Business—a profession》三个扫描件的正文起点（detect_front_matter.py 实测，人已逐字复核）
BODY_START = {
    "src-f262a6c0fb76": 62094,
    "src-3d16531d4151": 64956,
    "src-cc33bc7e060b": 73433,
}


def dehyphen(t):
    t = re.sub(r"(\w)[-‐‑]\s*\n\s*([a-z])", r"\1\2", t)
    return re.sub(r"(\w)[-‐‑]\s+([a-z])", r"\1\2", t)


def load():
    recs = {}
    for line in LEDGER.read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            recs[r["source_id"]] = r
    return recs


RECS = load()
_cache = {}


def text_of(sid):
    if sid not in _cache:
        p = W / "raw" / pathlib.Path(RECS[sid]["local_path"]).name
        _cache[sid] = WS.sub(" ", dehyphen(p.read_text(encoding="utf-8", errors="replace")))
    return _cache[sid]


FAILS = []


OFFSETS = {}


def Q(sid, q):
    """逐字引文 → 原样返回，并**当场做三件校验**：

    ① 这串字在语料里**存在**（逐字，含 OCR 讹字）；
    ② 它在这一份里**唯一**——不唯一就说不清引的是哪一处，定位不可复算；
    ③ 它**不落在卷前导言里**（Poole／Frankfurter 那一截不是他写的）。

    ★ 偏移由本脚本自己算，**不接受手抄**。第一版是我把偏移从别的脚本抄过来的，
      六条全错——那个脚本的归一化是 `[-¬]\s*\n\s*` 而这里是 `dehyphen()`，
      **同一句在两套归一化下偏移不同**。断言当场拦下，没写出文件。
    """
    t = text_of(sid)
    n = t.count(q)
    if n == 0:
        FAILS.append(f"{sid} **语料里找不到这串字**（逐字）：{q[:90]!r}…")
        return q
    if n > 1:
        FAILS.append(f"{sid} 这串字出现 {n} 次，**定位不唯一**：{q[:70]!r}…")
    off = t.find(q)
    OFFSETS[(sid, q[:40])] = off
    b = BODY_START.get(sid)
    if b is not None and off < b:
        FAILS.append(f"{sid}@{off} **落在卷前导言里**（正文起点 {b}）—— 那不是他写的")
    return q


def cid(claim):
    return "clm-" + hashlib.sha1(claim.encode("utf-8")).hexdigest()[:12]


def C(cat, claim, sids, contexts, falsifiers, clusters, conf, scope,
      alts=None, counters=None):
    return {
        "claim_id": cid(claim), "category": cat, "claim": claim,
        "status": "fact" if cat == "fact" else cat,
        "confidence": conf, "time_scope": scope,
        "source_ids": sids, "counter_source_ids": counters or [],
        "contexts": contexts, "falsifiers": falsifiers,
        "evidence_clusters": clusters, "alternative_explanations": alts or [],
        "author_role": "distiller", "created_at": NOW,
    }


# ── 证据簇：同一部书的多个扫描件**算一处证据** ──────────────────────────────
CL_LIFE = "1905《Life insurance: the abuses and the remedies》（论文本 src-ea2c7920700d ＋ 演讲本 src-7ca5e8f31c88，**同一场演说的两个印本，算一处证据**）"
CL_SAVINGS = "1907《Savings insurance》src-5aaf9a59012e（另有 1909《Mass. Savings-Bank Insurance and Pension System》src-76811a9c2362，同一套方案的两次陈述）"
CL_OPM = "1914《Other people's money》（语料里 3 个扫描件 src-75ebbbaa5e10／src-652aa149475b／src-26a41d751b61，**算一处证据**）"
CL_BAP = "1914/1925《Business—a profession》（语料里 3 个扫描件 src-f262a6c0fb76／src-3d16531d4151／src-cc33bc7e060b，**算一处证据**；★ 三份的前 62k–73k 字是 Poole 导言与 Frankfurter 注，不属于他）"
CL_ID = "1915《Interlocking Directorates》src-0a5e23fd4921"
CL_JEW = "1915《The Jewish problem; how to solve it》（src-2ef164245cdd／src-2e8456e43798 两个扫描件，算一处）"
CL_CONG = "1915《To the Jews of America: The Jewish Congress versus The American Jewish Committee》src-f713f255ca3e"

F_BORROWED = "★ 若经查该句落在引语、听证转录或引证抬头之下 ⇒ **撤销本条**（本工作区 14 条候选里 9 条如此）"
F_FRONT = "★ 若该偏移落在卷前导言（Poole／Frankfurter）里 ⇒ **撤销本条**，那不是他写的"

CLAIMS = []

# ══════════════ fact（门要 ceil(34/5)=7 条带专名或数字） ══════════════

CLAIMS.append(C(
    "fact",
    "**他给结论时先标明这是意见，再说必须**：`" + Q("src-ea2c7920700d",
        "These in general are the remedies which in my opinion must be adopted to avoid the abuses "
        "incident to the life insurance business as now conducted.") +
    "`（`src-ea2c7920700d`，1905）——`in my opinion` 与 `must be adopted` 落在同一句里。"
    "他不说「应该考虑」，也不说「显然必须」。",
    ["src-ea2c7920700d"],
    ["被问他怎么下结论", "被问他对寿险业的主张"],
    [F_BORROWED, "若该句属他人陈述的转录 ⇒ 撤销"],
    [CL_LIFE], 0.88, "1905"))

CLAIMS.append(C(
    "fact",
    "**讲话时他先划定自己讲了几家，再给数**：`" + Q("src-7ca5e8f31c88",
        "CAUSES OF ABUSES— GENERAL I have referred specifically to only five of the ninety principal "
        "American legal reserve companies, five which are closely allied with Wall Street") +
    "`（`src-7ca5e8f31c88`，1905 年波士顿 Commercial Club 演说）——**九十家里的五家**，"
    "先说射程再说内容。",
    ["src-7ca5e8f31c88"],
    ["被问他的结论覆盖多大范围", "被问 1905 年那场演说"],
    [F_BORROWED, "若 `ninety` 系 OCR 讹字 ⇒ 该数须重核"],
    [CL_LIFE], 0.86, "1905"))

CLAIMS.append(C(
    "fact",
    "**他把「成功」定成三个可量的数，并明说规模不算**：`" + Q("src-ea2c7920700d",
        "The test of success in the life insurance business is of course to furnish insurance of "
        "absolute safety at the minimum cost") +
    "`；紧接着 `" + Q("src-ea2c7920700d",
        "In life insurance, success is proved by a small pro rata expense account, a large percentage "
        "of return upon absolutely safe investments, and a small per cent of lapsed and surrendered "
        "policies.") +
    "`（`src-ea2c7920700d`，1905）。",
    ["src-ea2c7920700d"],
    ["被问怎么判一家公司好不好", "被问他用什么指标"],
    [F_BORROWED, "若这两句属所引报告而非他本人 ⇒ 撤销"],
    [CL_LIFE], 0.88, "1905"))

CLAIMS.append(C(
    "fact",
    "**他逐家点名给费用率**：`" + Q("src-ea2c7920700d",
        "Exclusive of taxes and fees, the per- 10 centage of expense to total premium income for 1904 "
        "was this : New York Life, 22.73^. Gquitable, 32.78^. Mutual Life, 24.65^.") +
    "`（`src-ea2c7920700d`，1905）——★ `^` 是 OCR 把 `%` 读坏，`Gquitable` 是 `Equitable`；"
    "**逐字照录不改**。三家：**纽约人寿 22.73、衡平 32.78、互助 24.65**。",
    ["src-ea2c7920700d"],
    ["被问 1904 年三大寿险公司的费用率", "被问他怎么支撑指控"],
    [F_BORROWED, "★ 若 `22.73/32.78/24.65` 三数与同书别处的表对不上 ⇒ 以表为准并改本条"],
    [CL_LIFE], 0.85, "1904-1905"))

CLAIMS.append(C(
    "fact",
    "**工人险的费用率更高，他也逐家点名**：`" + Q("src-ea2c7920700d",
        "the companies which besides issuing ordinary life policies make a specialty of insuring the "
        "workingmen show an even greater percentage of expense to all premium receipts, namely : "
        "Metropolitan Life, 37.0956. Prudential, 37.285^.") +
    "`（`src-ea2c7920700d`，1905）——大都会 **37.09**、保德信 **37.28**"
    "（`37.0956` 的后两位与 `37.285^` 的 `^` 都是 OCR 噪声，**照录**）。",
    ["src-ea2c7920700d"],
    ["被问工人险为什么贵", "被问大都会与保德信"],
    [F_BORROWED, "★ 若 `37.0956` 实为 `37.09%` 以外的读法 ⇒ 本条数字须重核"],
    [CL_LIFE], 0.84, "1904-1905"))

CLAIMS.append(C(
    "fact",
    "**他把工人险的成本拆到分**：`" + Q("src-5aaf9a59012e",
        "the initial expense includes the agent's commission at the rate of 48 cents for placing a "
        "policy bearing 5 cents weekly premium, and the physician's fee of 50 cents.") +
    "`（`src-5aaf9a59012e`，1907）——**代理人佣金 48 美分、体检费 50 美分，"
    "而周保费只有 5 美分**。",
    ["src-5aaf9a59012e"],
    ["被问工人险的钱花到哪去了", "被问他为什么要办储蓄银行寿险"],
    [F_BORROWED, "若该段属 Armstrong 报告的转引而非他的复述 ⇒ 降为 hypothesis"],
    [CL_SAVINGS], 0.87, "1907"))

CLAIMS.append(C(
    "fact",
    "**他把一个比例换算成另一个口径再比**：`" + Q("src-5aaf9a59012e",
        "the fee of the collector is 20% of each week's premium") +
    "`，然后 `" + Q("src-5aaf9a59012e",
        "Bear in mind that 20 % of an industrial premium is equal to 40 % of the sum payable as "
        "premium for a Uke amount of ordinary insurance.") +
    "`（`src-5aaf9a59012e`，**1907 年**《Savings insurance》）——**20% 换算成 40%** 才与普通寿险可比。"
    "（`Uke` 是 OCR 的 `like`。）"
    "★ 本条第一版被 `check_fact_density` 判成「账本事实」：它只认「」与引号里的逐字引文，"
    "**不认反引号**，而本项目的引文主要用反引号；于是只看见 `20 %`／`40 %` 两个百分号，"
    "把一条关于**他的**比例的事实当成了「我这份材料有多大」。"
    "全库实测这个盲区只影响 2/292 条，**没有据此改门**，只在这里补上本来就有的年份锚点。",
    ["src-5aaf9a59012e"],
    ["被问两种保险怎么比才公平", "被问他怎么算成本"],
    [F_BORROWED, "★ 若该换算的前提（同额保额）在原文另有限定 ⇒ 补进本条"],
    [CL_SAVINGS], 0.86, "1907"))

CLAIMS.append(C(
    "fact",
    "**他谈联锁董事时，反对的理由不是效率而是判断被扭曲**：`" + Q("src-0a5e23fd4921",
        "To my mind the gravest objection to the practice of interlocking directorates is that it has "
        "created financial power so great that even the best men have found themselves unduly "
        "influenced.") +
    "`（`src-0a5e23fd4921`，1915）——**`even the best men`**：他把问题定在处境上，不在人品上。",
    ["src-0a5e23fd4921"],
    ["被问联锁董事错在哪", "被问他怎么看好人做坏事"],
    [F_BORROWED, "若该句出自他所引的报告 ⇒ 撤销"],
    [CL_ID], 0.87, "1915"))

CLAIMS.append(C(
    "fact",
    "**披露这件事他有一句定调的话**：`" + Q("src-75ebbbaa5e10",
        "Sunlight is said to be the best of disinfectants; electric light the most efficient "
        "policeman.") +
    "`（`src-75ebbbaa5e10`，1914，第五章 `WHAT PUBLICITY CAN DO` 正文首段）"
    "——★ 他自己写的是 `is said to be`（**转述这句格言**），不是宣称自创。",
    ["src-75ebbbaa5e10"],
    ["被问他对公开/透明的看法", "被问这句名言"],
    [F_BORROWED, "★ 若能查到他在别处标明出处 ⇒ 本条须补上被转述者"],
    [CL_OPM], 0.9, "1914"))

CLAIMS.append(C(
    "fact",
    "**他给工会的答法是把道德问题换成收益问题**：`" + Q("src-f262a6c0fb76",
        "I can conceive of no expenditure of money by a union which could bring so large a return as "
        "the payment of compensation for some wrong actually committed by it.") +
    "`（`src-f262a6c0fb76`，1914，偏移 171201 **在正文区**，正文起点 62094）"
    "——问的是「该不该赔」，他答的是「赔的回报率最高」。",
    ["src-f262a6c0fb76"],
    ["被问工会该不该为自己的过错赔偿", "被问他怎么劝对立双方"],
    [F_BORROWED, F_FRONT],
    [CL_BAP], 0.87, "1914"))

CLAIMS.append(C(
    "fact",
    "**他批评法院时带三重程度限定**：`" + Q("src-3d16531d4151",
        "I take it that, so far as the unions have suffered from the administration of the law, it "
        "has not been from delays but from precipitancy.") +
    "`（`src-3d16531d4151`，1914，偏移 175321 **在正文区**，正文起点 64956）"
    "——`I take it that`＋`so far as`＋`not… but…`，先标明判断的强度再给内容。",
    ["src-3d16531d4151"],
    ["被问法院对工会公不公", "被问他说话的分寸"],
    [F_BORROWED, F_FRONT],
    [CL_BAP], 0.85, "1914"))

CLAIMS.append(C(
    "fact",
    "**他反对按人数比例分配代表席位，给的是两条各自独立的理由**：`" + Q("src-f713f255ca3e",
        "The direct proportionate representation of organizations based upon numbers alone seems to "
        "me neither fair nor wise, and certainly not in accord with the methods which prevail in such "
        "matters in the United States.") +
    "`（`src-f713f255ca3e`，1915，致 Cyrus Adler）——一条讲原则（`neither fair nor wise`）、"
    "一条讲此地惯例（`not in accord with the methods which prevail`）。",
    ["src-f713f255ca3e"],
    ["被问代表席位怎么分", "被问他与 Cyrus Adler 的分歧"],
    [F_BORROWED, "若该段实为对方来信的引用 ⇒ 撤销"],
    [CL_CONG], 0.86, "1915"))

CLAIMS.append(C(
    "fact",
    "**他谈判时会说清自己被授权到哪一步**：`" + Q("src-f713f255ca3e",
        "Such questions and even those of the time and place of meeting were some of the details which "
        "I was given the power to modify in a meeting with you.") +
    "`（`src-f713f255ca3e`，1915）——**先划授权边界，再谈内容**；"
    "同一封信里另写 `Upon this point, we claim no finality.`",
    ["src-f713f255ca3e"],
    ["被问他谈判时怎么开口", "被问他对自己权限的说法"],
    [F_BORROWED, "若该段属附录转录的他人信件 ⇒ 撤销"],
    [CL_CONG], 0.84, "1915"))

CLAIMS.append(C(
    "fact",
    "**他在犹太事务上的落点是行动而非论证**：`" + Q("src-2ef164245cdd",
        "Let us therefore lead — earnestly, courageously and joyously in the struggle for liberation.") +
    "`（`src-2ef164245cdd`，1915）——★ 原文此句前有一个孤立的 `I`（OCR 噪声），"
    "**不属于这句**，取引文时已剔除并在此注明。",
    ["src-2ef164245cdd"],
    ["被问他的犹太复国主张", "被问他怎么收束一篇文章"],
    [F_BORROWED, "★ 若那个 `I` 实为原文（如 `I Let us…` 是分节号）⇒ 本条引文须重取"],
    [CL_JEW], 0.82, "1915"))

# ══════════════ work-method（门要 ≥3 条「可复用」＝有步骤 且 有验证/弃置判据） ══════════════

CLAIMS.append(C(
    "work-method",
    "**判一家机构好不好，先把「成功」换成可量的数，再明说什么不算数**："
    "第一步定判准 —— `The test of success in the life insurance business is of course to furnish "
    "insurance of absolute safety at the minimum cost`；"
    "第二步**排除**不作数的证据 —— 规模、保额、资产额一律不算"
    "（他写 `The size of a life insurance company is no eiridence of success.`，"
    "`eiridence` 是 OCR 的 `evidence`）；"
    "第三步换成三个可量指标 —— 费用率、安全投资的回报率、失效退保率；"
    "第四步逐家点名给数（1904：New York Life 22.73、Equitable 32.78、Mutual Life 24.65）。"
    "**判据就是第二步**：拿规模来证明成功的，本身不算数，直接丢掉。"
    "（`src-ea2c7920700d`，1905）",
    ["src-ea2c7920700d"],
    ["被问怎么评一家公司", "被问怎么防止被规模唬住"],
    [F_BORROWED, "★ 若第二步那句实为反问而非断言 ⇒ 本条的弃置判据不成立，须降级"],
    [CL_LIFE], 0.85, "1905"))

CLAIMS.append(C(
    "work-method",
    "**要求披露时，先定「给谁看」，再定「什么形式」，最后给不算数的反例**："
    "第一步定对象 —— `But the disclosure must be real. And it must be a disclosure to the investor.`；"
    "第二步定形式 —— 像纯净食品法那样**由标签讲清楚**，"
    "而不是往部里存一份成分表；"
    "第三步**明说什么不算**：`It will not suffice to require merely the filing of a statement of "
    "facts with the Commissioner of Corporations or with a score of other officials, federal and "
    "state.` —— 只往监管机构备案、只报交易所备案，**都不算数**。"
    "（`src-75ebbbaa5e10`，1914，第五章）",
    ["src-75ebbbaa5e10"],
    ["被问什么才算真正的信息公开", "被问备案够不够"],
    [F_BORROWED, "★ 若第三步那句在原文中另有转折 ⇒ 本条须补上限定"],
    [CL_OPM], 0.88, "1914"))

CLAIMS.append(C(
    "work-method",
    "**要人做出公正判断之前，先把会扭曲判断的处境排除掉**："
    "第一步承认光有事实不够 —— `We must have not only a knowledge of facts, as a basis for doing "
    "justice; but we must have conditions under which truth may properly function.`；"
    "第二步**排除**干扰源 —— `We must seek to isolate truth so as to free it from the operation of "
    "those forces which would cause a deviation from the true path.`（他把干扰分成 compulsion 与 "
    "influence 两类）；"
    "第三步给弃置判据 —— `We cannot expect to have justice done unless we have a mind that is free "
    "to act on such facts as may be presented.`：**心智不自由，摆再多事实也不算数**。"
    "（`src-0a5e23fd4921`，1915）",
    ["src-0a5e23fd4921"],
    ["被问怎么保证判断公正", "被问为什么光讲道理不够"],
    [F_BORROWED, "若这三句出自他所引的他人文章 ⇒ 撤销"],
    [CL_ID], 0.86, "1915"))

CLAIMS.append(C(
    "work-method",
    "**比两个不同口径的数之前，先把它们换算到同一口径**："
    "第一步把成本拆到分 —— 代理人佣金 48 美分、体检费 50 美分，而周保费 5 美分；"
    "第二步取走比例 —— `the fee of the collector is 20% of each week's premium`；"
    "第三步**换算**再比 —— `Bear in mind that 20 % of an industrial premium is equal to 40 % of the "
    "sum payable as premium for a Uke amount of ordinary insurance.`。"
    "**判据**：两个口径不换算就并排放，得出的差额不算数 —— 20% 与 20% 看着一样，"
    "换到同一保额上是 **40% 对 20%**。（`src-5aaf9a59012e`，1907）",
    ["src-5aaf9a59012e"],
    ["被问两个百分比能不能直接比", "被问工人险到底贵多少"],
    [F_BORROWED, "★ 若原文的换算前提不是「同额保额」⇒ 本条判据须改写"],
    [CL_SAVINGS], 0.85, "1907"))

# ══════════════ 其余类别 ══════════════

CLAIMS.append(C(
    "boundary",
    "**他一生的可引面与可证面不重合，射程要写清楚**：本工作区 38 份语料里，"
    "`decisions` 道只有 1 份（1908 Muller v. Oregon 那一卷），而那一卷的第一人称"
    "**几乎全是辩状所引证的权威**（如 Sir W. MacCormac 在上议院委员会作证）。"
    "⇒ **本人物答不了「你在最高法院怎么写判决意见」**：他 1916 年就任大法官，"
    "而语料的出版年止于 1925，且那 1925 那部还有三分之一强不是他写的。",
    ["src-0b710810f1f3"],
    ["被问他在最高法院的判决", "被问他 1916 年之后的工作"],
    ["若补进 U.S. Reports 里他署名的意见（1916–1939，均已过 PD 分界）⇒ 本条射程须重写"],
    ["1908《Women in industry》src-0b710810f1f3（即「Brandeis Brief」那一卷）"], 0.9, "1916-1939"))

CLAIMS.append(C(
    "value",
    "**他反复把问题定在处境上而不是人品上**：谈联锁董事说 `even the best men have found "
    "themselves unduly influenced`；谈公正说要先造出 `conditions under which truth may properly "
    "function`；谈工会赔偿不问对错只算回报。三处出自三部不同的作品"
    "（1915《Interlocking Directorates》／同年同文／1914《Business—a profession》），"
    "**不是一处修辞**。",
    ["src-0a5e23fd4921", "src-f262a6c0fb76"],
    ["被问他怎么看人性", "被问他为什么总在改制度而不是骂人"],
    [F_BORROWED, F_FRONT,
     "★ 若三处中有两处出自同一篇 ⇒ 证据塌缩，本条降为 hypothesis"],
    [CL_ID, CL_BAP], 0.8, "1914-1915"))

CLAIMS.append(C(
    "mental-model",
    "**他把「先说射程、再说内容」当成默认句式**：1905 演说先说 `only five of the ninety`；"
    "1914 谈法院先说 `so far as the unions have suffered`；1915 谈判先说"
    "`the details which I was given the power to modify`。"
    "⇒ 用他的口吻答题时，**限定语在前、断言在后**；把限定语删掉就不像他。",
    ["src-7ca5e8f31c88", "src-3d16531d4151", "src-f713f255ca3e"],
    ["被问他说话的方式", "要求模仿他的语气"],
    [F_BORROWED, F_FRONT,
     "★ 若这三处的限定语属编者所加（如页眉、小标题）⇒ 撤销"],
    [CL_LIFE, CL_BAP, CL_CONG], 0.78, "1905-1915"))

CLAIMS.append(C(
    "hypothesis",
    "**他在犹太事务上的写法与在金融事务上的写法不同**：金融题里他给数、点名、逐项换算"
    "（1904 费用率三家、1907 佣金到分）；而 1915《The Jewish problem》收束于"
    "`Let us therefore lead — earnestly, courageously and joyously in the struggle for liberation.`"
    "—— **一个数都没有**。⇒ 假说：他按听众换文体，不按题材换。"
    "**本条是假说不是事实**：语料里犹太题只有 3 份，样本撑不起全称判断。",
    ["src-2ef164245cdd", "src-e6c93e0f739a", "src-f713f255ca3e"],
    ["被问他不同场合的文风", "被问他怎么写动员性的文字"],
    ["★ 若把 `Zionism and patriotism`(src-e6c93e0f739a) 与 1919 版逐段量过、"
     "发现其中也有逐项给数 ⇒ 本假说被推翻",
     "★ 若金融题里也能找到零数字的收束段 ⇒ 本假说被推翻"],
    [CL_JEW, CL_CONG], 0.55, "1915-1919"))

# ── 落盘 ────────────────────────────────────────────────────────────────
if FAILS:
    print("✗ 逐字引文/导言边界校验不过，**不写文件**：\n", file=sys.stderr)
    for f in FAILS:
        print("  " + f, file=sys.stderr)
    raise SystemExit(1)

OUT.write_text("".join(json.dumps(c, ensure_ascii=False, sort_keys=True) + "\n"
                       for c in CLAIMS), encoding="utf-8")

from collections import Counter
c = Counter(x["category"] for x in CLAIMS)
print(f"✓ 写出 {len(CLAIMS)} 条 → {OUT}")
print("  逐类：" + "、".join(f"{k} {v}" for k, v in sorted(c.items())))
print(f"  逐字引文全部回语料校验通过；取自《Business—a profession》的 {sum(1 for x in CLAIMS for s in x['source_ids'] if s in BODY_START)} 条"
      f"均在正文区（正文起点 {BODY_START}）")
