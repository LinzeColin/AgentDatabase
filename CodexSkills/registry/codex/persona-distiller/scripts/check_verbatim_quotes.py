#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""逐字引文核查（文档层 + 用例层）—— `check_quote_integrity.py` 的姊妹件。

`check_quote_integrity.py` 只扫 `evidence/claims.jsonl`。
而**渲染文档、身份分面、评测用例里的引文一样会伪造**，此前没有常规检查，
每个人物都在临时写脚本——Robertson #97 临时写的那版还把判据的维度选错了两次。

## 判据：引号内**没有汉字**才当逐字英文引文核

先后错过两版，记在这里免得再错：

1. 「含 ≥4 个连续拉丁字母」→ 把「Tiger 由他与 Thorpe McKenzie 共同创立」
   这种中文强调句误判为英文引文（专名里有拉丁字母）。
2. 「拉丁字符占比 ≥60%」→ **仍然误判**，因为专名把一个短中文句撑到了 73%。

**一段逐字英文引文里不会出现汉字。** 这才是干净的维度。
（RUNBOOK 第六十种附记：判据连续误报两次以上，停止调参数，换维度。）

用法：
    python3 check_verbatim_quotes.py --workspace <target> --cache <corpus dir> \
        [--extra judge_payload_x.json ...]
"""
import argparse, json, pathlib, re, sys

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

CJK = re.compile(r"[\u4e00-\u9fff]")
QUOTE = re.compile(r"\u300c([^\u300d]{16,})\u300d")
LAT = re.compile(r"[A-Za-z]{4}")
NORM = re.compile(r"[^a-z0-9]+")


# ★★★ v0.0.0.150：省略号是**合法的引文形态**，不是编造。
#   `the Committee ... has had the inestimable advantage` —— 中间那一段是**作者主动略去的**，
#   拿它去语料里找连续串当然找不到。**按整串比会把正当的节引报成编造引文。**
ELLIPSIS = re.compile(r"\.\.\.+|…|\[[^\]]{0,12}\]")
# ★★ markdown 记号不是引文的一部分。实测 Carver `primarily **between**`、
#   Lister `**his guidance and advice**` 都因此报未命中——**那是我自己加的着重号**。
MARKUP = re.compile(r"\*+|_{2,}|`|<[^>]{1,12}>")
# ★ `<sup>r</sup>` 这类 HTML 标签也不是引文的一部分（Pasteur 的 `M. le D<sup>r</sup>`）。


def norm(s: str) -> str:
    return NORM.sub("", MARKUP.sub("", s).lower())


def norm_parts(s: str) -> list:
    """→ 按省略号切开后的各段（已归一化，丢掉太短的碎片）。

    ★ 判据变成：**每一段都要能在语料里找到**。
    这比「整串必须连续出现」宽，但**比不查严**——
    编造的句子不会恰好每一段都在语料里。
    """
    return [x for x in (norm(p) for p in ELLIPSIS.split(s)) if len(x) >= 12]


def _hit(q: str, corpus: str) -> bool:
    """→ 这条引文算不算「能在语料里找到」。

    整串命中最好；命中不了就按省略号切开，**每一段都要在**。
    切完没有够长的段（例如整条几乎都是省略号），**按未命中处理**——宁可报，不可漏。
    """
    if norm(q) in corpus:
        return True
    parts = norm_parts(q)
    return bool(parts) and all(p in corpus for p in parts)


def verbatim(q: str) -> bool:
    """逐字英文引文 = 引号内无汉字，且确实含英文词。"""
    return not CJK.search(q) and bool(LAT.search(q))


_PAGENO = re.compile(r"^[\divxlcdm]{1,6}([/\-][\divxlcdm]{1,6})?$")


def strip_page_furniture(text: str):
    """去掉**版口**：反复出现的页眉行与独立页码行。→ (去掉之后的文本, 去掉了哪些)

    ★ 为什么需要它：Sorby #133 的一条引文横跨了两页——

        …identical with the cavities in the crystals in artificial furnace
        SO R BY- — STRUCTURE OF CRYSTALS*        ← 页眉
        4/9                                       ← 页码
        slags, their very nature proves the igneous origin…

    候选把它接了起来、丢掉页眉，**那正是引跨页句子的正确做法**；
    而判据按连续串比对，当场报「未命中」。**引文是真的，判据看不懂版口。**

    ★★ 判法**不用硬编码刊名**（今天已经在 `check_quote_locator` 上栽过一次）：
      · 独立页码行：纯数字或罗马数字，可带 `4/9`、`12-13` 这种；
      · 页眉：**在同一份文件里反复出现 ≥3 次的短行**——
        一行在一份文档里出现三次以上且不长，它就是版口，与它写了什么无关。

    ★★★ 它**只作为第二次尝试**：第一遍用原样语料比，比不上才用它重试，
      而且命中要单独报成「跨版口」。**绝不把它掺进第一道**——
      掺进去就等于永久放宽，那时一条伪造引文只要跨过一个页眉就能蒙混。
    """
    lines = text.split("\n")
    keyed = [(l, re.sub(r"\s+", "", l.strip().lower())) for l in lines]
    from collections import Counter
    cnt = Counter(k for _, k in keyed if k)

    def isolated(i):
        """前后都是空行——版口总是被空白围着。"""
        prev = keyed[i - 1][1] if i > 0 else ""
        nxt = keyed[i + 1][1] if i + 1 < len(keyed) else ""
        return not prev and not nxt

    def shouty(s):
        """短、且大写字母占多数——页眉的形状。

        ★ 频次规则**挡不住页眉**：同一个页眉被 OCR 打成
          `SO R BY- — STRUCTURE OF CRYSTALS*`、`SORBY.—STRUCTURE…` 等等，
          每种拼法各出现一两次，**没有一种够 3 次**。
          实测就是这一条让第一版没修好 Sorby 那句。
        """
        t = s.strip()
        letters = [c for c in t if c.isalpha()]
        if not (0 < len(t) <= 60) or len(letters) < 4:
            return False
        return sum(c.isupper() for c in letters) / len(letters) >= 0.6

    out, removed = [], []
    for i, (line, k) in enumerate(keyed):
        if not k:
            out.append(line)
            continue
        if (_PAGENO.match(k)
                or (cnt[k] >= 3 and len(k) <= 60)
                or (shouty(line) and isolated(i))):
            removed.append(line.strip())
            continue
        out.append(line)
    return "\n".join(out), removed


def collect(ws: pathlib.Path, extra: list, *, only_verbatim: bool = True) -> list:
    """→ [(来源, 引文)]。默认只留**逐字英文**引文（`verbatim`）。

    ★ `only_verbatim=False` 用来回答「0 条」的成因：产物里到底有没有长引文。
      默认值保持 True —— 外部调用方 `quality_check.py:734` 的行为一个字不变。
      ★ 我第一版直接调 `collect()` 去数「全部长引文」，忘了**过滤就在这个函数里**，
        于是永远拿到 0，两条支路合并成一条。自测当场判红。
        [[a-gates-scan-set-is-smaller-than-reality]]
    """
    out = []
    for f in sorted(list(ws.glob("*.md")) + list(ws.glob("identity-facets/*.md"))
                    + list(ws.glob("references/research/*.md"))):
        for q in QUOTE.findall(corpus_body(f.read_text(encoding="utf-8"))):
            if verbatim(q) or not only_verbatim:
                out.append((f.name, q))
    for p in extra:
        try:
            data = json.loads(pathlib.Path(p).read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        # ★★ 两种形状都要认。原先只认「每条是 dict、里头有 candidate/rubric/prompt」
        #   的**派发格式**；而 `evals/candidate_answers.json` 是扁平的
        #   `{case_id: 答案文本}`——`r.get("candidate")` 取不到，**一条不报，看着像干净**。
        #   实测 Sorby #133：那份答案里有 **18 条**「」框住的英文引文，本件报 **0**。
        #   这正是「空默认值吞掉『不知道』」——0 被读成没问题。
        #   ★ 后果不轻：**评委读的是答案，delta 也是从答案算的**，
        #     而答案里的引文此前只有候选自己「我逐条比对过」的自述在背书。
        if isinstance(data, dict) and all(isinstance(v, str) for v in data.values()):
            for cid, text in data.items():                    # 扁平：case_id → 答案
                for q in QUOTE.findall(text):
                    if verbatim(q):
                        out.append((f"{pathlib.Path(p).name}:{cid}", q))
            continue
        rows = data if isinstance(data, list) else [data]
        for r in rows:
            if not isinstance(r, dict):
                continue
            for key in ("candidate", "rubric", "prompt"):
                for q in QUOTE.findall(str(r.get(key, ""))):
                    if verbatim(q):
                        out.append((f"{pathlib.Path(p).name}:{r.get('case_id', key)}", q))
    return out


# ── 负对照（v0.0.0.13 补）──────────────────────────────────────────────
# 本件是**硬门**，却一直没有负对照——`check_checkers.py` 首跑就把它点了出来。
# RUNBOOK 第十八种：**没有负对照的检查器，其「全绿」不构成任何证据。**
#
# ★ 负对照必须包含**它历史上真实错过的那两版误判形态**（见文件头判据一节），
#   而不只是我此刻想得到的形态。上一版（元检查器）刚因为「样本没覆盖真实形态」
#   而误判了 6 件检查器，同样的错不该在下一件上再犯一次。
SELFTEST_CORPUS = (
    "I have always believed that the best investments are the ones you "
    "understand deeply. Tiger was founded with eight million dollars.\n")
SELFTEST_DOC = """# 自测文档

他说：「I have always believed that the best investments are the ones you understand deeply.」

改了一个词的伪造引文：「I have never believed that the best investments are the ones you understand deeply.」

整句杜撰：「This sentence was never spoken by anyone anywhere in the corpus.」

中文强调句（含拉丁专名，**不是**英文引文）：「Tiger 由他与 Thorpe McKenzie 共同创立」

拉丁占比很高的短中文句（**仍然不是**英文引文）：「Alpha 与 Beta 的 Sharpe ratio 都不算高」
"""


def self_test() -> int:
    import tempfile
    bad_cases = []
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        ws, cache = root / "ws", root / "cache"
        ws.mkdir(); cache.mkdir()
        (ws / "persona.md").write_text(SELFTEST_DOC, encoding="utf-8")
        (cache / "corpus.txt").write_text(SELFTEST_CORPUS, encoding="utf-8")

        corpus = norm((cache / "corpus.txt").read_text(encoding="utf-8"))
        found = collect(ws, [])
        texts = [q for _, q in found]
        missed = [q for q in texts if not _hit(q, corpus)]

        # ★★★ 版口那一层**必须单独测**：上面这段只走 `corpus`，
        #   而放宽发生在 `corpus2`。不单独测，等于「改了的那条路从没被负对照走过」。
        _page_corpus = (
            "essential characters,\n"
            "they are identical with the cavities in the crystals in artificial furnace\n"
            "\n\nSO R BY- — STRUCTURE OF CRYSTALS*\n\n4/9\n\n"
            "slags, their very nature proves the igneous origin of the minerals\n")
        _c1 = norm(_page_corpus)
        _c2 = norm(strip_page_furniture(_page_corpus)[0])
        _true = ("they are identical with the cavities in the crystals in "
                 "artificial furnace slags, their very nature proves")
        _fake = ("they are identical with the cavities in the crystals in "
                 "artificial furnace slags, which I measured at once")
        page_checks = [
            ("跨版口的真引文：第一道比不上", not _hit(_true, _c1)),
            ("跨版口的真引文：去版口后能比上", _hit(_true, _c2)),
            # ↓ 这一条是整层的守门人
            ("**伪造引文去版口后仍然比不上**", not _hit(_fake, _c2)),
            ("去掉的确实是页眉与页码",
             any("STRUCTURE OF CRYSTALS" in x
                 for x in strip_page_furniture(_page_corpus)[1])
             and "4/9" in strip_page_furniture(_page_corpus)[1]),
        ]

        checks = page_checks + [
            ("真引文被认出且命中语料",
             any(q.startswith("I have always believed") for q in texts)
             and all(norm(q) in corpus for q in texts if q.startswith("I have always"))),
            ("改一个词的伪造引文被抓",
             any(q.startswith("I have never believed") for q in missed)),
            ("整句杜撰被抓",
             any(q.startswith("This sentence was never") for q in missed)),
            # ↓ 两条误判形态：这才是它真正栽过的地方
            ("中文强调句未被当成英文引文（专名含拉丁字母）",
             not any("共同创立" in q for q in texts)),
            ("拉丁占比高的短中文句未被当成英文引文",
             not any("都不算高" in q for q in texts)),
            ("逐字英文引文恰好 3 条", len(texts) == 3),
            ("未命中恰好 2 条", len(missed) == 2),
        ]
    # ── ★★★ 2026-08-17：零扫描面不许印肯定句（正反各一）──
    #   comenius #182 实测：0 条逐字英文引文，本判据照印「✓ 全部可在语料中找到」。
    #   ★ 断言必须打在**子进程真正印出来的那几行**上：印字逻辑在 `main()` 里，
    #     只断言 `collect()` 返回 0 条／1 条是测不到分支的 —— 把守卫删掉照样绿。
    #     （第一版我就是那么写的，变异对照当场拆穿。）
    #     [[a-checker-nothing-calls-is-not-a-checker]]
    import subprocess as _sp, sys as _sys, tempfile as _tf
    _self = str(pathlib.Path(__file__).resolve())

    def _run(md: str, corpus: str) -> str:
        with _tf.TemporaryDirectory() as _td:
            _r = pathlib.Path(_td); _ws = _r / "ws"; _c = _r / "c"
            _ws.mkdir(); _c.mkdir()
            (_ws / "persona.md").write_text(md, encoding="utf-8")
            (_c / "corpus.txt").write_text(corpus, encoding="utf-8")
            return _sp.run([_sys.executable, _self, "--workspace", str(_ws),
                            "--cache", str(_c)],
                           capture_output=True, text=True).stdout

    # 正：只有中文引文 ⇒ 逐字英文引文 0 条 ⇒ 必须说「未核」，且**不许**出现肯定句
    _out0 = _run("他说「这是一句足够长的中文引文用来占位」。\n", "nothing relevant here\n")
    checks.append(("★ 0 条可核 → 印「未核，不是通过」",
                   "未核，不是通过" in _out0))
    checks.append(("★ 0 条可核 → **不许**印「都可在语料中找到」",
                   "都可在语料中找到" not in _out0))
    # ★★★ 「0 条」的两种成因必须分得开（这一对断言分别钉住两条支路）
    _out_cn = _run("他说「这是一句足够长的中文引文用来占位」。\n", "irrelevant\n")
    checks.append(("★★★ 0 条但**有中文长引文** → 说清「有 N 条、全含汉字、一条也没核过」",
                   "全部含汉字" in _out_cn and "一条也没核过" in _out_cn))
    _out_none = _run("这一段里根本没有任何长引文。\n", "irrelevant\n")
    checks.append(("★★★ 0 条且**连中文引文也没有** → 说「一条长引文都没有」，不许说成含汉字",
                   "一条长引文都没有" in _out_none and "全部含汉字" not in _out_none))

    # 反：有 1 条真引文且命中 ⇒ 照旧印肯定句，且**不许**说未核
    _out1 = _run("他写道「a real sentence here for testing」。\n",
                 "He wrote a real sentence here for testing today.\n")
    checks.append(("★★ 反对照：1 条且命中 → 照旧印「都可在语料中找到」",
                   "都可在语料中找到" in _out1))
    checks.append(("★★ 反对照：1 条且命中 → **不许**说未核",
                   "未核" not in _out1))

    for label, ok in checks:
        print(f"  {'✓' if ok else '✗'} {label}")
        if not ok:
            bad_cases.append(label)
    if bad_cases:
        print("\n负对照未过：")
        for b in bad_cases:
            print(f"  · {b}")
        return 2
    # ★ 分解只写大类，**不写会漂的手抄数字**：08-17 加 4 条时那串「3+2+2+4」
    #   与 len(checks)=15 已经对不上（手抄计数必漂）。[[self-reported-numbers-must-be-computed]]
    print(f"\n负对照通过（**{len(checks)} 项**：正例 / 伪造引文 / 误判形态 / 版口跨页 / 零扫描面）")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    # ★ 不再 required —— 负对照必须能**独立跑**。
    #   `--self-test` 却要求 `--workspace/--cache`，等于负对照依赖它本该独立于的数据；
    #   `check_checkers.py` 把这种形态单列为 NOT-STANDALONE，因为它实际上从没被跑过。
    ap.add_argument("--workspace", type=pathlib.Path)
    ap.add_argument("--cache", nargs="+", type=pathlib.Path)
    ap.add_argument("--extra", nargs="*", default=[])
    ap.add_argument("--self-test", action="store_true", help="只跑内置双向负对照")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.workspace or not a.cache:
        ap.error("需要 --workspace 与 --cache（或只给 --self-test）")
    raw_texts = [corpus_body(p.read_text(encoding="utf-8", errors="replace"))
                 for d in a.cache for p in d.rglob("*.txt")]
    corpus = "\n".join(norm(t) for t in raw_texts)
    # ★ 第二道语料：把**版口**（页眉／页码）去掉之后再归一化。
    #   只在第一道未命中时才拿它重试，且**必须报出来是靠它才命中的**。
    corpus2 = "\n".join(norm(strip_page_furniture(t)[0]) for t in raw_texts)

    qs = collect(a.workspace, a.extra)
    bad, crossed = [], []
    for w, q in qs:
        if _hit(q, corpus):
            continue
        if _hit(q, corpus2):
            crossed.append((w, q))       # 引文本身是真的，只是横跨了版口
        else:
            bad.append((w, q))
    print(f"逐字英文引文 {len(qs)} 条（判据：引号内无汉字），"
          f"未命中 {len(bad)}，**跨版口命中 {len(crossed)}**")
    for w, q in bad:
        print(f"   \u2717 {w}: {q[:100]}")
    for w, q in crossed:
        print(f"   ⚠ 跨版口（引文为真，中间隔着页眉/页码）: {w}: {q[:70]}")
    if not qs:
        # ★★ **零扫描面不许印肯定句。** 2026-08-17 拿 comenius #182 实跑：
        #   它 `raw/` 下只有六份 `_ids*.txt`（记账文件，不是语料），
        #   逐字英文引文 **0 条**，而本判据照印「✓ 全部可在语料中找到」并 rc=0。
        #   「全部都找得到」在空集上恒真 —— **那不是通过，是没核**。
        #   同型先例：`check_rights_basis` 交叉喂测时也这么假绿过（同日已修）。
        #   ★ 只改措辞、**不改退出码** —— 让它变红是收紧判定，属决定不属清理。
        #   [[zero-hit-gates-must-prove-they-can-hit]]
        #
        # ★★★ 而「0 条」有**两种完全不同的成因**，必须分开说，否则读者会一律
        #   读成「这个人没引用过」。全库 54 个实测：19 个走这条路，其中
        #   **10 个产物里其实有长引文（合计 49 条）**，只是**全是中文** ——
        #   `verbatim()` 的定义是「引号内无汉字且含英文词」，中文引文**根本不在
        #   本门射程内**（它们是译文，对不上原文语料也属正常）。
        #   最极端的 Grotius：18 条中文引文，本门此前照印「✓ 全部可在语料中找到」。
        #   [[a-gates-scan-set-is-smaller-than-reality]]
        all_q = [q for _, q in collect(a.workspace, a.extra, only_verbatim=False)]
        print("   ⚠ **一条逐字英文引文都没扫到 —— 本次未核，不是通过。**")
        if all_q:
            print("     成因：产物里有 **%d** 条长引文，但**全部含汉字** ⇒ 不在本门射程内"
                  "（本门只核逐字**英文**引文）。**这 %d 条本判据一条也没核过。**"
                  % (len(all_q), len(all_q)))
        else:
            print("     成因：产物里**一条长引文都没有**（连中文的也没有）。")
        print("     （另需确认：语料目录传对了没有 —— `--cache` 指向的是不是真的正文。）")
    elif not bad and not crossed:
        print("   \u2713 全部 **%d** 条逐字英文引文都可在语料中找到" % len(qs))
    elif not bad:
        print("   \u2713 没有对不上的；上面那些是原文横跨页面，**不是引错**")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
