#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**整版扫图里，引文有没有落在别人那一段。**

## 为什么有这道判据

`check_quote_integrity` 只问「这句在不在语料里」。
**整版扫图的语料里，「在」是不够的**——同一个 .txt 常常还装着同页别人的文章。

Fleming #111 实测：PMC 把旧 BMJ / Proc R Soc 按**整页**提供，
`penicillin-letter-1941` 那一份的下半版是**新西兰医院财政的另一篇**；
`freelance-science-1952` 同版还有 P. A. Gorer 的两篇书评。
从这些文件里取引文而不确认落在哪一段，
**会把别人的文字挂到本人物名下——而引文核查会说「在」。**

## 判据

读一份**作者边界清单**（`raw/_BOUNDARIES.json`）。**全库有两种写法，两种都认**：

    扁平（fleming / nightingale / slavyanov）
        {"penicillin-letter-1941": {"start_line": 68, "end_line": 196, ...}}
    区间数组（barton-117）—— 他的文字被别人的插段切成几块时只能这么写
        {"rc-in-cuba-1898": {"hers": [[171, 838]], "not_hers": [[840, 922]], ...}}

对每条逐字引文：若它出现在某个有边界记录的文件里，就查它是否落在**任何一段**之内。
**落在外面即报。**

★ 2026-08-18 之前只认第一种 ⇒ **Barton 那 8 条一条也读不到**，
  整份返回 rc=3「未检查」。守卫是对的（没报成通过），但**为 Barton 事故建的判据
  读不了 Barton 自己的记录**。现在两种都认，且**认不出的形状会印出来**，不静默丢弃。

## 它判不了什么

- **没有边界记录的文件一概不判**——本判据不猜边界。
  清单要由读过原文的人写，且要留 `start_evidence` / `end_evidence` 供复核。
- 引文若在两份文件里都出现，只按第一份判。
"""
import argparse
import json
import pathlib
import re
import sys

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

Q = re.compile(
    r"[「\"“]\s*\*{0,2}([A-Za-zÀ-ÿ][^」\"”]{18,300})[」\"”]"
    r"|`\s*\*{0,2}([A-Za-zÀ-ÿ][^`]{18,400})`")
PROJ = re.compile(r"[^0-9A-Za-z]+")


def _p(s):
    return PROJ.sub("", s).lower()


def _q(m):
    for g in m.groups():
        if g:
            return g
    return ""


def collect_quotes(blobs):
    """→ [(来源标签, 引文)]。`blobs` 是 {标签: 文本}。"""
    out = []
    for tag, text in blobs.items():
        for m in Q.finditer(text or ""):
            s = _q(m)
            if len(_p(s)) >= 25:
                out.append((tag, s))
    return out


def locate(corpus_dir, name):
    """按**原文件名**递归找，不假设目录布局。

    ★ 接线负对照当场抓出来的：抓源目录是 `raw/<名>/<名>.txt`，
    而**工作区里是 `raw/src-<hash>/<原名>.txt`**。
    第一版写死 `cache/<名>/<名>.txt`，在工作区上一条也找不到，
    于是打印「其中 0 条出现在有边界记录的文件里」——**看起来像没问题。**
    """
    root = pathlib.Path(corpus_dir)
    direct = root / name / f"{name}.txt"
    if direct.is_file():
        return direct
    for f in root.rglob(f"{name}.txt"):
        return f
    return None


def ranges_of(b):
    """→ 这条边界记录里「**属于他**」的行区间列表 `[(起, 止), …]`（1 起，闭区间）。

    ★★★ 2026-08-18：**全库有两种 schema，此前只认一种。**

        扁平（fleming / nightingale / slavyanov）：{"start_line": 68, "end_line": 196}
        区间数组（barton-117）：              {"hers": [[171, 838]], "not_hers": [[840, 922]]}

    第二种**更强**：他的文字被别人的插段切成几块时，单段 `start..end` 表达不了，
    而 `not_hers` 还能明写「这几行确定是别人的」。
    此前 `main()` 只收「同时有 start_line 与 end_line」的条目 ⇒
    **Barton 那 8 条一条也读不到**，判据对他整个返回 rc=3「未检查」。
    ★ 那**不是假绿**（守卫写对了），是**覆盖缺口** —— 而这件判据的开头写着
    它就是「Barton 事故的引文版」。**为某人建的判据，读不了那个人的记录。**
    [[eval-artifacts-have-five-schemas]]｜[[checkers-assume-a-shape-the-product-outgrows]]

    纯函数，不碰磁盘。认不出的形状返回 `[]`（由调用方判「未检查」，不当通过）。
    """
    return verdict_of(b)[1]


def verdict_of(b):
    """→ (判定, 区间列表)。判定三取一，**不是两取一**：

        "ranges"     有可用区间 ⇒ 查引文落不落在里面
        "none_his"   `hers: []` **明写的空** ⇒ 这份文件里**没有一行是他的**
                     ⇒ 落在这份文件里的引文**一律越界**（这是最强的信号，不是「没信息」）
        "unknown"    形状认不出、或明标「切不出边界」 ⇒ **未检查，不当通过**

    ★★★ 2026-08-18 我第一版把 `hers: []` 和「认不出」混成一档，双双跳过 ——
      **等于把最强的信号读成了没有信息**。Barton 那 3 条实况：

        heroines-of-service-1917       hers: []  why: 「群传…**没有一行是她的话**」
        women-in-american-history-1919 hers: []  why: 「群传，全章是别人写她」
        history-red-cross-1883         hers: []  mixed: [[1, 999999]]
                                       why: 「目次 OCR 破碎…**不给行号**」

      前两条是 `none_his`（任何引文落进去都该报）；第三条有 `mixed` ⇒ 边界确实切不出，
      是真的 `unknown`。**「明写的空」与「没写」必须分开。**
      [[empty-default-swallows-unknown]]｜[[negative-capability-claims-need-evidence-too]]
    """
    if not isinstance(b, dict):
        return "unknown", []
    out, saw_key = [], False
    for key in ("hers", "his", "theirs", "mine"):        # 同义键，全库实测只有 `hers`
        v = b.get(key)
        if isinstance(v, list):
            saw_key = True
            for pair in v:
                if (isinstance(pair, (list, tuple)) and len(pair) == 2
                        and all(isinstance(x, int) for x in pair) and pair[0] <= pair[1]):
                    out.append((pair[0], pair[1]))
    if out:
        return "ranges", out
    if isinstance(b.get("start_line"), int) and isinstance(b.get("end_line"), int) \
            and b["start_line"] <= b["end_line"]:
        return "ranges", [(b["start_line"], b["end_line"])]
    # ★ `mixed` 明说「他的和别人的混着、切不出边界」⇒ 真未知，不许当成 none_his
    if saw_key and not b.get("mixed"):
        return "none_his", []
    return "unknown", []


def check(quotes, spans, corpus_dir):
    """→ (查过的条数, [(来源, 文件, 引文)])——列出落在别人那一段里的。"""
    checked, bad = 0, []
    for tag, q in quotes:
        pq = _p(q)
        for name, b in spans.items():
            kind, rs = verdict_of(b)
            if kind == "unknown":
                continue
            f = locate(corpus_dir, name)
            if not f:
                continue
            lines = corpus_body(f.read_text(encoding="utf-8", errors="replace")).split("\n")
            if pq not in _p("\n".join(lines)):
                continue
            checked += 1
            # ★ `none_his`：这份文件里没有一行是他的 ⇒ 落进来就是越界，**不必再看区间**
            # ★ 多段：落进**任何一段**都算在内（他的文字被别人的插段切开时的正解）
            inside = (kind == "ranges"
                      and any(pq in _p("\n".join(lines[s - 1:e])) for s, e in rs))
            if not inside:
                bad.append((tag, name, q[:90]))
            break
    return checked, bad


# ══════════════════ 自测 ══════════════════

def selftest() -> int:
    import tempfile
    fails = []

    # ★★★ 2026-08-18 新增：两种 schema 都要认（纯函数，先于文件测试跑）
    def _chk0(lbl, cond):
        print(("  ✓ " if cond else "  ✗ ") + lbl)
        if not cond:
            fails.append(lbl)
    _chk0("★★★ 正例：扁平 `{start_line, end_line}` ⇒ 认出 1 段",
          ranges_of({"start_line": 68, "end_line": 196}) == [(68, 196)])
    _chk0("★★★ 正例：**Barton 的形状** `{hers: [[171,838]]}` ⇒ 认出 1 段（逐字取自 wip-barton-117）",
          ranges_of({"hers": [[171, 838]], "not_hers": [[840, 922]],
                     "evidence_start": "The Red Cross in Cuba"}) == [(171, 838)])
    _chk0("★★ 正例：多段 `hers` 全部收（他的文字被别人的插段切开时的正解）",
          ranges_of({"hers": [[10, 20], [40, 55]]}) == [(10, 20), (40, 55)])
    _chk0("★★★ 负例：`not_hers` **不算他的**（收错方向就把别人的话判成他的）",
          ranges_of({"not_hers": [[840, 922]]}) == [])
    _chk0("★★ 负例：两种都没有 ⇒ 返回空，由调用方判「未检查」，**不当通过**",
          ranges_of({"caveat": "x"}) == [] and ranges_of({}) == [] and ranges_of(None) == [])
    _chk0("★ 负例：区间写反 / 不是整数 ⇒ 不收（宁可未检查，不要错段）",
          ranges_of({"hers": [[900, 100]]}) == []
          and ranges_of({"hers": [["a", "b"]]}) == []
          and ranges_of({"start_line": 9, "end_line": 3}) == [])
    _chk0("★★ `hers` 存在时**优先于**扁平字段（更细的那个说了算）",
          ranges_of({"hers": [[5, 6]], "start_line": 1, "end_line": 100}) == [(5, 6)])
    # ★★★ 三态：`hers: []`（明写的空）≠ 没写。逐字取自 wip-barton-117。
    _chk0("★★★★ `hers: []` + why「没有一行是她的话」⇒ **none_his**，不是 unknown",
          verdict_of({"hers": [], "about_her": [[1918, 2696]],
                      "why": "群传，她只占一章；★ 全章是别人写她，**没有一行是她的话**。"})
          == ("none_his", []))
    _chk0("★★★ `hers: []` **且有 `mixed`**（明标切不出边界）⇒ **unknown**，不许当 none_his",
          verdict_of({"hers": [], "mixed": [[1, 999999]],
                      "why": "目次 OCR 破碎，页码读不准，所以**不给行号**"})[0] == "unknown")
    _chk0("★★ 连 `hers` 键都没有 ⇒ unknown（没写 ≠ 明写的空）",
          verdict_of({"caveat": "x"})[0] == "unknown")
    _chk0("★ 有区间 ⇒ ranges", verdict_of({"hers": [[1, 2]]})[0] == "ranges")

    def chk(label, cond):
        print(("  ✓ " if cond else "  ✗ ") + label)
        if not cond:
            fails.append(label)

    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        (root / "page").mkdir()
        # 一份整版扫图：前半是他的信，后半是别人的另一篇
        (root / "page" / "page.txt").write_text(
            "HEADER LINE\n"
            "I think, however, I can claim some merit in the discovery here.\n"
            "ALEXANDER FLEMING.\n"
            "NEW ZEALAND HOSPITAL FINANCE\n"
            "The subsidy is five shillings per bed for returned soldiers here.\n",
            encoding="utf-8")
        spans = {"page": {"start_line": 1, "end_line": 3}}

        print("── 正向：引文落在别人那一段 ──")
        n, bad = check([("答案/x", "The subsidy is five shillings per bed for returned soldiers")],
                       spans, root)
        chk(f"下半版的句子 → 报出（查过 {n} 条）", n == 1 and len(bad) == 1)

        print("── 反向对照 ①：引文落在他那一段，不许报 ──")
        n, bad = check([("答案/y", "I can claim some merit in the discovery here")], spans, root)
        chk("他那一段里的句子 → 不报", n == 1 and not bad)

        print("── 反向对照 ②：没有边界记录的文件一概不判 ──")
        n, bad = check([("答案/z", "The subsidy is five shillings per bed for returned soldiers")],
                       {}, root)
        chk("清单为空 → 查过 0 条、不报", n == 0 and not bad)

        print("── 反向对照 ③：语料里根本没有的句子不算越界 ──")
        n, bad = check([("答案/w", "This sentence does not appear anywhere in the corpus at all")],
                       spans, root)
        chk("语料里没有 → 不计入、不报（那是 check_quote_integrity 的活）",
            n == 0 and not bad)

        print("── 反向对照 ④：太短的引文不判（噪声太大）──")
        qs = collect_quotes({"a": "他说 `short one` 就完了。"})
        chk("投影后不足 25 字符 → 不收集", not qs)

        print("── 反向对照 ⑤：**工作区布局也要找得到**（接线负对照抓出来的）──")
        (root / "src-abc123def456").mkdir()
        (root / "src-abc123def456" / "page.txt").write_text(
            (root / "page" / "page.txt").read_text(encoding="utf-8"), encoding="utf-8")
        import shutil
        shutil.rmtree(root / "page")
        n2, bad2 = check([("答案/x", "The subsidy is five shillings per bed for returned soldiers")],
                         spans, root)
        chk("语料在 `src-<hash>/<原名>.txt` 下 → 仍找得到并报出", n2 == 1 and len(bad2) == 1)
        (root / "page").mkdir()
        (root / "page" / "page.txt").write_text(
            (root / "src-abc123def456" / "page.txt").read_text(encoding="utf-8"), encoding="utf-8")

        print("── 反向对照 ⑥：边界恰好含首尾行 ──")
        n, bad = check([("答案/v", "I think, however, I can claim some merit in the discovery")],
                       {"page": {"start_line": 2, "end_line": 2}}, root)
        chk("单行边界也要算对", n == 1 and not bad)

    print(f"\n{'✓ 自测全过' if not fails else f'✗ **{len(fails)} 项未过**'}")
    return 0 if not fails else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--answers", help="{case_id: 答案} 的 JSON")
    ap.add_argument("--claims", help="claims.jsonl")
    ap.add_argument("--boundaries", help="作者边界清单 JSON")
    ap.add_argument("--cache", help="语料目录（含 <名>/<名>.txt）")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return selftest()
    if not (a.boundaries and a.cache):
        ap.error("要么 --self-test，要么同时给 --boundaries 与 --cache")

    bp = pathlib.Path(a.boundaries)
    if not bp.is_file():
        print(f"✗ **{a.boundaries} 不在——本次未检查（不是通过）**")
        return 3
    raw_spans = json.loads(bp.read_text(encoding="utf-8"))
    ent = {k: v for k, v in raw_spans.items() if isinstance(v, dict) and not k.startswith("_")}
    kinds = {k: verdict_of(v)[0] for k, v in ent.items()}
    spans = {k: v for k, v in ent.items() if kinds[k] != "unknown"}
    unknown = [k for k, kk in kinds.items() if kk == "unknown"]
    none_his = [k for k, kk in kinds.items() if kk == "none_his"]
    # ★ 三态都印出来 —— 「认不出」以前是**静默丢弃**，正是它让 Barton 那份整份变 rc=3。
    print("边界记录 %d 条：有区间 **%d**｜**「整份都不是他的」%d**｜**认不出 %d**"
          % (len(ent), len(ent) - len(unknown) - len(none_his), len(none_his), len(unknown)))
    if none_his:
        print("  ★ 「整份都不是他的」（`hers: []` 明写的空）：%s" % "、".join(none_his[:5]))
        print("    ⇒ 引文只要落进这些文件就**一律越界** —— 这是最强的信号，不是「没信息」。")
    if unknown:
        print("  ★ 认不出 / 明标「切不出边界」的：%s" % "、".join(unknown[:5]))
        print("    ⇒ **不当作通过**。支持的写法：`{start_line, end_line}` 或 `{hers: [[起,止],…]}`；"
              "带 `mixed` 的表示边界确实切不出。")
    if not spans:
        print(f"✗ **{a.boundaries} 里没有一条可用的边界记录——本次未检查（不是通过）**")
        return 3

    blobs = {}
    if a.answers:
        for k, v in json.loads(pathlib.Path(a.answers).read_text(encoding="utf-8")).items():
            blobs["答案/" + k] = v
    if a.claims:
        for line in pathlib.Path(a.claims).read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                blobs["断言/" + r["claim_id"]] = r.get("claim", "")
    if not blobs:
        print("✗ **答案与断言都没给——本次未检查（不是通过）**")
        return 3

    quotes = collect_quotes(blobs)
    checked, bad = check(quotes, spans, a.cache)
    print(f"逐字引文 {len(quotes)} 条；其中 {checked} 条出现在有边界记录的文件里")
    if not checked:
        print("  ⚠ **没有一条引文落在有边界记录的文件里**——"
              "本判据这一轮什么也没查到，不构成通过")
        return 0
    if bad:
        print(f"\n✗ **{len(bad)} 条引文落在别人那一段里**——"
              "整版扫图同页有别的文章，引它等于把别人的文字挂到本人物名下：")
        for tag, name, q in bad:
            print(f"    {tag}　@{name}\n        {q}")
        return 1
    print("  ✓ 每一条都落在本人物的那一段里")
    return 0


if __name__ == "__main__":
    sys.exit(main())
