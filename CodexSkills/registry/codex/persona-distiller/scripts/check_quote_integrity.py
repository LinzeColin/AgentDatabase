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
"""
import argparse, glob, json, pathlib, re, sys

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
    r"|\u2039\s*\*{0,2}([A-Za-zÀ-ÿ][^\u203a]{18,300})\u203a")

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
    print(f"语料 {len(texts)} 份（已投影为字母数字串）")
    if not texts:
        # ★ 0 份语料时**不许往下判**：那样每条引文都会被报成「未命中」，
        #   把「没核成」印成「核出了问题」。退出码 2 与「查出未命中」的 1 区分开。
        print("⚠️  一份语料都没读到，本次检查结果不可信"
              "——确认 --cache 指到含 .txt 的目录（本流水线在 <工作区>/raw/ 下）")
        return 3


    def scan(label: str, unit_id: str, text: str, acc):
        for m in Q.finditer(text):
            acc["quotes"] += 1
            for seg in SPLIT.split(_q(m)):
                if len(proj(seg)) < MIN:
                    continue
                acc["segs"] += 1
                hit = find(seg, texts, folded)
                if hit == "longs":
                    acc["longs"].append((unit_id, re.sub(r"\s+", " ", seg).strip()[:100]))
                elif not hit:
                    acc["bad"].append((f"{label}/{unit_id}", re.sub(r"\s+", " ", seg).strip()[:100]))

    acc = {"quotes": 0, "segs": 0, "bad": [], "longs": []}

    if a.claims:
        for line in a.claims.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                scan("断言", r["claim_id"], r["claim"], acc)

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

    if not a.claims and not a.answers:
        print("  ⚠ 既没给 --claims 也没给 --answers，**什么都没核**（不是通过）")

    print(f"引文 {acc['quotes']} 条，切分后核验片段 {acc['segs']} 个，"
          f"未命中 {len(acc['bad'])} 个，长 s 还原后才命中 {len(acc['longs'])} 个")
    for cid, s in acc["longs"]:
        print(f"  · 长 s 还原后命中 {cid}: 「{s[:70]}」")
    for cid, s in acc["bad"]:
        print(f"  ⚠ {cid}: 「{s}」")
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
