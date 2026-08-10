#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""引文真实性核验 —— 把断言里的每一句英文原文拿去语料里逐字找。

## 这个脚本第一版是错的，错法值得写下来（RUNBOOK ⑮ 的第四个实例）

第一版直接拿 `「...」` 里的整段去匹配，报出 8 条「未命中」。全是误报，三个原因：

1. **撇号**：`I'm prone to...` 被我的字符类从 `m` 截断，拿 `m prone to...` 去找当然找不到。
2. **省略号是我自己的省略标记**：`「A… B」` 里的 A 与 B 在原文中**并不相邻**，
   当成一整句去找必然落空。**必须按 `…`／`...` 切开，分段各自核。**
3. **引文里嵌了 markdown 粗体**：`「...**My intuition for what's easy**...」`，
   `**` 是我加的强调，不在原文里。

**8 条全是我的工具坏了，不是引文假。** 差一步就报出「产物里有 8 条伪造引文」——
**误报的检查比没有检查更糟**，因为它会触发一轮根本不需要的订正，
而那轮订正很可能把真引文改坏。

## 现在的做法

- 按 `…` / `...` 切段，每段单独核，短于 12 字符的段跳过（太短匹配无意义）
- 剥掉 markdown `**` `*` `_`
- 撇号／引号统一（`'` `'` `'` → `'`，`"` `"` → `"`）
- 词间用 `\\s*` 连接（语料是 HTML 转文本，词间常有多余空格——`double- ESC` 就是这么漏的）
- 大小写不敏感

**未命中仍不等于伪造**，只等于「换这几种方式都没找到」，须人工看一眼再定。

## v0.0.0.58：**反引号形态，以及「0 条却印绿勾」**

Fleming #111 的候选答案里逐字引文我全用了 Markdown 反引号。
本判据原本只认 `「」`／`""`／`«»`／`„“`／`‹›` 五种，**一条也匹配不上**，
于是打印：

    引文 0 条，切分后核验片段 0 个，未命中 0 个
      ✓ 全部可在语料中找到

**十七条逐字引文一条都没核过，而报告是绿的。**
`check_quote_locator` 早有「一条都没扫到 → exit 3」这道兜底，本件一直没有。

两处都补：引号形态加反引号；**扫到 0 条时 exit 3，不许印绿勾**。

补完当场抓到一处真问题：`fl-planning-fidelity-02` 引的讣告原文是
`The oM.Bchoice of the school was fortuitous`——**`oM.B` 是版面杂字窜进了词中间**，
而我写引文时把它抹掉了。**那正是「改了 OCR 错字再当逐字引文用」。**
改法是从 `choice` 起引并写明前面粘着什么，**不是把杂字删掉当没看见**。
"""
import argparse, glob, json, pathlib, re, sys

#: ★ 剥掉抓源方写的出处表头再量——**表头是出处说明，不是他的话**。
#:   全库只有 Adams（144 份）与 Coffin（36 份）有这种表头，
#:   实测占全文**聚合 17.2% / 11.7%**，**逐份中位 39.1% / 16.1%**。
#: ★★ 接上之后**逐个量过前后差**，只写量到的：
#:   · `check_lane_quotes_verbatim` @ Coffin：核过 1 → 0，
#:     报出 `Coffin, Charles L., Detroit, Mich.` **对不上**——
#:     那句「逐字引文」只存在于**我自己写的表头里**。这是 Barton 事故的引文版，实锤一条。
#:   · ★★★★ `check_ocr_language_death` @ Coffin：不剥时「**每一份都在下限之上**」，
#:     剥掉表头后报出 **2 份虚词占比 0.101（下限 0.15）**——
#:     **我那段干净的英文表头把 OCR 烂掉的文件托过了及格线。**
#:     同一件在 Adams 上是「可判份数 94 → 60」：34 份**只因表头的词数才够得上判**。
#:   · `check_first_person_density`：正文字符 −0.6%，密度 1.68 → **1.69**——
#:     **几乎没变**。我一度在这里写「第一人称密度被表头拉偏」，**那句没有实测支撑，已删**。
#:   · 其余多数判据前后一致。**接线是按「表头不是他的话」这条原则做的，不是因为每个都变了。**
import sys as _sys, pathlib as _pl
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent))
from common import corpus_body  # noqa: E402

SPLIT = re.compile(r"…|\.\.\.")
NONWORD = re.compile(r"[^0-9A-Za-z]+")
MIN = 20        # 投影后的最小长度；再短就不足以判定
LONGS = re.compile(r"[fs]")

# v0.0.0.37：引号形态原本只认「」与 " —— **法文 «» 一律扫不到。**
# Pasteur #106 实测：答案里 11 条外语引文，只有 4 条被看见，**7 条法文 «» 从未被扫过**（64%）。
# 与 v0.0.0.26（非西方姓名形态）、v0.0.0.35（射程停在断言层）同一族：
# **判据的覆盖面比数据窄，而它照样报绿。**
# 一并加德文 „…"、单书名号‹›、英文弯引号，并允许引号后紧跟 markdown 粗体与重音字母。
Q = re.compile(
    r"[「\"\u201c]\s*\*{0,2}([A-Za-zÀ-ÿ\u0370-\u03ff][^」\"\u201d]{18,300})[」\"\u201d]"
    r"|\u00ab\s*\*{0,2}([A-Za-zÀ-ÿ\u0370-\u03ff][^\u00bb]{18,400})\u00bb"
    r"|\u201e\s*\*{0,2}([A-Za-zÀ-ÿ][^\u201c\u201d]{18,300})[\u201c\u201d]"
    r"|\u2039\s*\*{0,2}([A-Za-zÀ-ÿ][^\u203a]{18,300})\u203a"
    # ★ v0.0.0.58：**反引号也是引文形态。**
    #   Fleming #111 实测：他这一轮的逐字引文我全用了 Markdown 反引号，
    #   四种引号一条都不匹配——判据报「引文 0 条」，**却仍印了「✓ 全部可在语料中找到」**。
    #   十六条逐字引文一条都没核过，而报告是绿的。
    r"|`\s*\*{0,2}([A-Za-zÀ-ÿ\u0370-\u03ff][^`]{18,400})`")

def _q(m):
    """取第一个非空捕获组——四种引号形态共用一个 finditer。"""
    for g in m.groups():
        if g:
            return g
    return ""



def proj(s: str) -> str:
    """投影成只保留字母数字的小写串——标点／空白／markdown／引号形态全部抹平。"""
    return NONWORD.sub("", s).lower()


def fold_s(s: str) -> str:
    """把 f 与 s 折叠成同一符号。**只允许这一种字形差**，不是通用模糊匹配。

    1800 年前的印本用长 s（ſ），OCR 普遍认成 f：`inferted`／`fuperficial incifions`／`Efq`。
    本项目允许引用时把它还原成 s 并注明，所以核验时必须容这一种差；
    **但也只容这一种**——OCR 的其它噪声（`DoHors`←Doctors、`WOQDVILLE`←WOODVILLE）
    折叠后仍然对不上，照样报出来。那正是本门要抓的：**把 OCR 错字顺手改正了再当逐字引文用。**
    """
    return LONGS.sub("§", s)


def find(seg: str, projected, folded=None) -> str:
    """返回 'exact' / 'longs' / '' —— 空串表示未命中。"""
    q = proj(seg)
    if len(q) < MIN:
        return "exact"                   # 太短，不作判据
    if any(q in t for t in projected):
        return "exact"
    if folded is not None and any(fold_s(q) in t for t in folded):
        return "longs"
    return ""


# 负对照样本：四类伪造，覆盖从整句编造到「真句只改一个词」（**构造夹具**）
SELF_TEST = [
    ("整句伪造", "I have always believed that writing tests before code is the single most important discipline"),
    ("真句改数字", "SD currently has 456 dependencies which weren't core in Perl 5.8.5"),
    ("真句改主语", "My colleague is prone to just tuning out a bit and thinking it's probably fine"),
    ("真句只改一词", "This reduces context bloat for the reviewer and gets it to look at again"),
]

# ★ 真实夹具：全部取自 #104 Edward Jenner 第 3 轮的实际答案与实际语料，一字未改。
# 前两条必须放行（长 s 还原是明写的允许），第三条必须抓出（改的是 OCR 错字，不是长 s）。
REAL_LONGS_OK = ("长 s 还原—须放行",
                 "it was inserted, on the 14th of May, 1796, into the arm of the boy "
                 "by means of two superficial incisions")
REAL_VERBATIM_OK = ("逐字命中—须放行",
                    "It was not with Sir Joseph, but with Home ; he took the paper. "
                    "It was shewn to the Council, and returned to me")
# ★ v0.0.0.37 真实夹具：取自 Pasteur #106 的实际答案，用法文书名号 «» 包裹。
#   扩形态之前，这一条**根本不会被扫到**（判据只认「」与 "），
#   Pasteur 答案里 11 条外语引文有 7 条属这种情形——**64% 从未被核过，而判据照样报绿。**
REAL_FRENCH_GUILLEMET = ("法文 «» 引号—须被扫到并命中",
    "\u00abSur vingt chiens trait\u00e9s, je n'aurais pu r\u00e9pondre d'en rendre r\u00e9fractaires \u00e0 la rage plus de quinze ou seize.\u00bb")
REAL_OCR_FIXED = ("改了 OCR 错字—须抓出",
                  "To Doctors JENNER and WOODVILLE")   # 语料作 "To DoHors JENNER and WOQDVILLE"

# ★ v0.0.0.38：自测**自带夹具语料**，不再借用调用方传进来的 --cache。
#
# 此前自测直接拿 main() 装好的那份语料判，于是：
#   · 只有跑 Jenner 时才过；跑别人时前两条真实夹具必然「误杀」，
#     自测报「本检查器已失效」——而检查器本身好好的。
#   · 元检查器普查因此把它记作「负对照不可独立验证」。
#   · v0.0.0.38 把「自测未过」接成了硬错，若不修，除 Jenner 外**每个人都会被挡**。
#
# 下面三段是从 Jenner #104 真实语料里**逐字符取出的原样**（含其 OCR 讹形），
# 文件名附在各段后面，可回查。**这是自测夹具，不是任何人的语料。**
_FIX_LONGS = (   # src-ec9e81d982c3/inquiryintocause00jenn.normalized.txt
    "it  was  inferted,  on  the  14th\nof  May,  1796,  into  the  arm  of  the  boy  "
    "by  means  of  two\nfuperficial  incifions")
_FIX_VERBATIM = (  # src-d29ec9348b71/b21463475_0001.normalized.txt
    "It  was  not  with  Sir  Joseph,  but  with  Home  ;  he  took\nthe  paper.  "
    "It  was  shewn  to  the  Council,  and  returned  to  me")
_FIX_OCR = (  # src-6d5211d60581/b22006345.txt —— 原样含讹形，**不得改正**
    "To  DoHors  JENNER  and  WOQDVILLE")
_FIX_FRENCH = (  # Pasteur #106 语料原样
    "Sur vingt chiens traités, je n'aurais pu répondre d'en rendre "
    "réfractaires à la rage plus de quinze ou seize.")


def fixture_corpus() -> tuple[list, list]:
    """自测专用夹具语料 → (投影, 长 s 折叠)。与真实语料同一套装载后处理。"""
    texts, folded = [], []
    for raw in (_FIX_LONGS, _FIX_VERBATIM, _FIX_OCR, _FIX_FRENCH):
        p = proj(raw)
        texts.append(p)
        folded.append(fold_s(p))
    return texts, folded


def load_corpus(cache_dirs) -> tuple[list, list]:
    """cache 目录 → (投影正文, 长 s 折叠后正文)。

    ★ v0.0.0.38 抽成函数，为的是**让装载这一步也能被负对照**。
    此前它内联在 main() 里，自测只能拿到「已经装好的语料」，
    于是「一份都没装到」这个失败模式，自测在结构上就看不见。
    """
    texts, folded = [], []
    for d in cache_dirs:
        # `{d}/*.txt` 不递归；本流水线语料在 `raw/<source_id>/<file>.txt`，深一层。
        for f in glob.glob(f"{d}/**/*.txt", recursive=True):
            p = proj(pathlib.Path(f).read_text(encoding="utf-8", errors="replace"))
            texts.append(p)
            folded.append(fold_s(p))
    return texts, folded


def self_test(projected=None, folded=None) -> int:
    """负对照 + 真实夹具 + 反向对照。任何一条不合即判本检查器失效。

    ★ v0.0.0.38：改用**自带夹具语料**，不再吃调用方的 --cache。
    自测判的是「这件检查器还灵不灵」，那就不能取决于此刻在跑谁的语料。
    参数保留但忽略，只为不破坏既有调用签名。
    """
    projected, folded = fixture_corpus()
    missed = 0
    print("\n══ 负对照（伪造引文必须全部抓到）══")
    for label, q in SELF_TEST:
        caught = not find(q, projected, folded)
        print(f"  {'✓ 抓到' if caught else '✗ 漏掉'}  {label}: 「{q[:62]}…」")
        missed += not caught

    print("\n══ 真实夹具（Jenner #104 实际数据，一字未改）══")
    for label, q in (REAL_LONGS_OK, REAL_VERBATIM_OK):
        hit = find(q, projected, folded)
        ok = bool(hit)
        print(f"  {'✓' if ok else '✗ 误杀'}  {label}（{hit or '未命中'}）: 「{q[:58]}…」")
        missed += not ok
    hit = find(REAL_OCR_FIXED[1], projected, folded)
    print(f"  {'✓ 抓到' if not hit else '✗ 漏掉'}  {REAL_OCR_FIXED[0]}: 「{REAL_OCR_FIXED[1]}」")
    missed += bool(hit)

    # v0.0.0.37：法文引号必须被 Q 认出来（形态覆盖），而不只是内容能匹配
    m = Q.search(REAL_FRENCH_GUILLEMET[1])
    seen = bool(m and _q(m))
    print(f"  {'✓' if seen else '✗ 扫不到'}  {REAL_FRENCH_GUILLEMET[0]}：Q 正则{'认出' if seen else '**没认出**'}法文 «» 形态")
    missed += not seen

    print("\n══ 反向对照 ══")
    # ① 抽掉语料：真实引文必须转红——证明放行来自语料，不是来自匹配太松
    a = find(REAL_VERBATIM_OK[1], [], [])
    print(f"  {'✓' if not a else '✗'} 抽掉语料后，逐字命中的那条转为未命中")
    missed += bool(a)
    # ② 关掉长 s 折叠：长 s 样本必须转红——证明放行来自这条明写的允许本身
    b = find(REAL_LONGS_OK[1], projected, None)
    print(f"  {'✓' if not b else '✗'} 关掉长 s 折叠后，长 s 样本转为未命中")
    missed += bool(b)

    # ④ v0.0.0.130：**标识符过滤**的双向对照。
    #    接 --docs 之后，研究文档里的判据名/字段名/来源号会被反引号一并扫进来，
    #    而它们永远不在语料里——不过滤就是每人几条长期误报，
    #    **而误报的代价是作者学会忽略这道门。**
    #    过滤太狠同样危险：德文长复合词一旦被当成标识符跳过，伪造就查不出来了。
    print("\n══ 标识符对照（v0.0.0.130）══")
    _ID = re.compile(r"^[A-Za-z_][A-Za-z0-9]*(?:[._\-/][A-Za-z0-9_]+)+$")
    for s in ("research.invalid-source", "check_quote_integrity", "src-20044a8564a5",
              "evals/cases.jsonl", "quality_check.py", "min_baseline_delta"):
        k = bool(_ID.match(s))
        print(f"  {'✓ 跳过' if k else '✗ **没跳**'}  标识符 {s}")
        missed += not k
    for s in ("Milzbrandbakterien", "The recent war has taught us that",
              "proportionate to the length of time", "Read by title and published"):
        k = bool(_ID.match(s))
        print(f"  {'✓ 照核' if not k else '✗ **误跳**'}  引文 {s}")
        missed += bool(k)

    # ③ v0.0.0.38：**装载这一步**的对照。
    #    此前全部对照都建立在「语料已经装好」之上，于是「一份都没装到」
    #    这个失败模式在结构上就测不到——而它恰恰会把每条引文都报成未命中，
    #    看起来与「查出一片伪造引文」完全一样。
    print("\n══ 装载对照（v0.0.0.38）══")
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        nest = root / "raw" / "src-deadbeef"
        nest.mkdir(parents=True)
        (nest / "a.txt").write_text(
            "antiseptic principle in the practice of surgery", encoding="utf-8")
        t_n, f_n = load_corpus([str(root / "raw")])
        print(f"  {'✓' if len(t_n) == 1 else '✗'} 嵌套布局 raw/<src>/x.txt 读到 "
              f"{len(t_n)} 份（流水线自己产出的布局）")
        missed += len(t_n) != 1

        flat = root / "flat"; flat.mkdir()
        (flat / "b.txt").write_text("carbolic acid", encoding="utf-8")
        t_f, _ = load_corpus([str(flat)])
        print(f"  {'✓' if len(t_f) == 1 else '✗'} 平铺布局仍读到 1 份（反向对照）")
        missed += len(t_f) != 1

        empty = root / "empty"; empty.mkdir()
        t_e, _ = load_corpus([str(empty)])
        print(f"  {'✓' if not t_e else '✗'} 空目录读到 0 份，不凭空命中（反向对照）")
        missed += bool(t_e)

    print("\n  ✓ 负对照通过" if not missed else f"\n  ✗ {missed} 条不合——本检查器已失效，不得依赖其结论")
    return missed


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--claims", type=pathlib.Path,
                    help="断言层 claims.jsonl")
    ap.add_argument("--answers", type=pathlib.Path, nargs="*", default=[],
                    help="**答案层**：候选答案 JSON（id→文本）或盲判载荷（[{case_id,A,B}]）。"
                         "断言层绿不代表答案层绿——被判、被发布的是答案层。")
    # ★ v0.0.0.38：`--cache` 由 required=True 改为按需必填。
    #   自测现在自带夹具语料，**必须能独立跑起来**——
    #   元检查器普查此前把本件记作「负对照不可独立验证」，根因就在这一行。
    # ★ v0.0.0.130：**研究文档层**。此前本件只认 --claims / --answers，
    #   于是 `references/research/*.md` 里的逐字引文**从来没有被任何判据核过**——
    #   而研究文档正是断言的来源。Carver #127 实测：6 份研究文档 78 条引文，
    #   我手工声称「58/58 逐字核过」，一上工具就查出一条把 OCR 讹字 `iSyy.`
    #   写成了 `1899.`（**改了 OCR 错字再当逐字引文用**，正是本件文件头点名的那一类）。
    #   手工核不是核。
    ap.add_argument("--docs", type=pathlib.Path, nargs="*", default=[],
                    help="**研究文档层**：references/research/*.md 等 Markdown")
    ap.add_argument("--cache", nargs="+", default=[])
    ap.add_argument("--self-test", action="store_true",
                    help="跑负对照（自带夹具语料，可不带 --cache 独立运行）")
    a = ap.parse_args()

    # 只跑自测：不碰任何人的语料，退出码 0=灵 / 2=已失效
    if a.self_test and not a.cache:
        return 2 if self_test() else 0
    if not a.cache:
        ap.error("--cache 必填（除非只跑 --self-test）")

    # ★ v0.0.0.38：装载走 load_corpus()，与自测**同一份代码**——
    #   否则对照测的是另一条路径，绿了也不构成证据。
    #   该函数把 `{d}/*.txt` 改成了递归：本流水线语料在 `raw/<source_id>/<file>.txt`，
    #   非递归写法对着工作区或 raw/ 永远读到 0 份，于是每条引文都「找不到」，
    #   门报出一片**假红**。check_claim_coverage.py 同一天撞出同一个坑。
    texts, folded = load_corpus(a.cache)
    # ★★★★ 2026-08-11：退出码 **3 与 4 是两件事**，此前挤在同一个 3 里。
    #   3 = **一份语料都没读到**（回连/路径的问题）
    #   4 = 语料读到了，但**一条引文都没扫到**（答案/断言里就没有引文）
    #   调用方 `quality_check` 原本把 3 一律印成「一份语料都没读到」——
    #   2026-08-11 我据此在夹具上查了好几步语料路径，而真相是「语料 8 份读到了、引文 0 条」。
    #   **同一个码表达两种原因，报错就会把人送到错的地方。**
    print(f"语料 {len(texts)} 份（已投影为字母数字串）")
    if not texts:
        # ★ 0 份语料时**不许往下判**：那样每条引文都会被报成「未命中」，
        #   把「没核成」印成「核出了问题」。退出码 2 与「查出未命中」的 1 区分开。
        print("⚠️  一份语料都没读到，本次检查结果不可信"
              "——确认 --cache 指到含 .txt 的目录（本流水线在 <工作区>/raw/ 下）")
        return 3


    # ★ v0.0.0.130：**反引号里不全是引文。** 研究文档用反引号同时包两种东西：
    #   语料原文，和**代码标识符**（判据名 `research.invalid-source`、字段名
    #   `check_quote_integrity`、来源号 `src-20044a8564a5`、文件名 `_ids.txt`）。
    #   后者永远不会出现在语料里，于是每份研究文档都会带着几条**必然未命中**——
    #   接进门之后就是长期误报，而误报的代价是作者学会忽略这道门。
    #   口径：**无空白 + 由 . _ - / 连接的字母数字段**判为标识符，跳过。
    #   ★ 只跳这一种形状——德文长复合词（`Milzbrandbakterien`）没有分隔符，照核不误。
    IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9]*(?:[._\-/][A-Za-z0-9_]+)+$")

    def scan(label: str, unit_id: str, text: str, acc):
        for m in Q.finditer(text):
            acc["quotes"] += 1
            for seg in SPLIT.split(_q(m)):
                if len(proj(seg)) < MIN:
                    continue
                if IDENT.match(seg.strip()):
                    acc["idents"] += 1        # 标识符不是引文，**只计数不判**
                    continue
                acc["segs"] += 1
                hit = find(seg, texts, folded)
                if hit == "longs":
                    acc["longs"].append((unit_id, re.sub(r"\s+", " ", seg).strip()[:100]))
                elif not hit:
                    acc["bad"].append((f"{label}/{unit_id}", re.sub(r"\s+", " ", seg).strip()[:100]))

    acc = {"quotes": 0, "segs": 0, "bad": [], "longs": [], "idents": 0}

    if a.claims:
        for line in a.claims.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                scan("断言", r["claim_id"], r["claim"], acc)

    # ★ v0.0.0.137：**围栏代码块不是引文。** ```bash … ``` 里是命令，
    #   不是在声称「语料里有这句」。Thomson #129 实测：README/SKILL 模板里的
    #   `python3 install.py`、`runtime_router.py plan --task …` 四条被报成「未命中」——
    #   与此前 `research.invalid-source` 那类同源：**判据把「反引号包着的」一律当引文**。
    #   标识符过滤只挡得住单个词，挡不住多词命令行。
    _FENCE = re.compile(r"^```.*?^```", re.M | re.S)
    for path in a.docs:
        scan("研究", path.name, _FENCE.sub("", corpus_body(path.read_text(encoding="utf-8"))), acc)

    for path in a.answers:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):           # 盲判载荷
            for row in data:
                for side in ("A", "B"):
                    if isinstance(row.get(side), str):
                        scan("答案", f"{row.get('case_id')}:{side}", row[side], acc)
        elif isinstance(data, dict):         # id → 文本
            for k, v in data.items():
                if isinstance(v, str) and not k.startswith("_"):
                    scan("答案", k, v, acc)

    if not a.claims and not a.answers and not a.docs:
        print("  ⚠ --claims / --answers / --docs 一个都没给，**什么都没核**（不是通过）")

    print(f"引文 {acc['quotes']} 条，切分后核验片段 {acc['segs']} 个，"
          f"未命中 {len(acc['bad'])} 个，长 s 还原后才命中 {len(acc['longs'])} 个"
          + (f"，跳过标识符 {acc['idents']} 个（判据名/字段名/来源号，不是引文）"
             if acc["idents"] else ""))
    for cid, s in acc["longs"]:
        print(f"  · 长 s 还原后命中 {cid}: 「{s[:70]}」")
    for cid, s in acc["bad"]:
        print(f"  ⚠ {cid}: 「{s}」")
    # ★ v0.0.0.58：**扫到 0 条时不许印绿勾。**
    #   「没扫到」与「查过没问题」必须能分开——
    #   `check_quote_locator` 早就有这道兜底，本件一直没有。
    if not acc["quotes"]:
        print("✗ **一条引文都没扫到——本次未检查（不是通过）**；"
              "确认答案里的引文用的是本判据认得的形态"
              "（「」／\"\"／«»／„“／‹›／反引号）")
        return 4          # ★ 与「语料读不到」(3) **分开**：见下方说明
    print("  ✓ 全部可在语料中找到" if not acc["bad"]
          else "\n  ⚠ 未命中不等于伪造——须人工看一眼原文再定（见文件头）。"
               "\n    但**「改了 OCR 错字再当逐字引文用」也会落在这里**，那一类是真问题。")
    # ★ v0.0.0.38：退出码分三种，此前三种情形都返回 2，调用方无从分辨，
    #   于是它退回去做串匹配（`'未命中 0 个' not in out`）——
    #   而这个代码库自己在 check_claim_coverage 的接线处写过
    #   「★ 判据用**退出码**，不用输出串」。在一处立的规矩，在另一处没执行。
    #   0=干净　1=查出未命中（真发现）　2=自测未过　3=语料读不到（结论不可信）
    if a.self_test and self_test(texts, folded):
        return 2
    return 1 if acc["bad"] else 0


if __name__ == "__main__":
    sys.exit(main())
