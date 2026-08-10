#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**来源计数里有几份其实是同一部作品**——2026-08-07 在 Whitworth #152 上撞出来。

## 撞出它的那一次

`source.minimum` 判的是 `usable = [r for r in train if r['tier'] != 'U' and ...]`。
**`derived_from` 从头到尾没被读过。**

Whitworth #152 实测：`usable = 7`，而按内容去重后**只有 3 部作品**：

    {miscellaneouspa03 · miscellaneouspa00 · wikisource转录 · newyorkindustria}  ← 1858 年那一部
                          （三个扫描/转录 + 整篇作附录重印的 1854 报告）
    {miscellaneouspa01 · miscellaneouspa02}                                      ← 1873 年那一部
    {jstor-41334745}                                                             ← 1868 年那一件

quick 门要 8 份。**再抓 1 份，门就从 7 变 8 转绿，而实质仍是 3 部。**
这就是「靠动分子过门」——与 [[ratio-gates-can-be-passed-by-shrinking]] 同一个病的另一面：
那条是砍分母，这条是灌分子。

## ★★★ 为什么不能只读 `derived_from`

**声明是自报的，而自报会漏——我自己就漏了。**

同一次实测，7 对重叠 ≥30% 的关系里：

| | 对数 |
|---|---|
| 重叠 ≥30% | **7** |
| 其中我**声明了** `derived_from` | 3 |
| 其中我**没声明** | **4** |

漏掉的 4 对里最典型的一对：`newyorkindustria00whit`（1854 纽约报告）与三个 1858 副本
重叠 40.4% / 38.4% / 47.9%——**我知道它整篇是 1858 卷的附录**（写在 `counting_convention` 的散文里了），
**却没写进机器读得到的 `derived_from`**。另外三对是传递关系（misc00 × wikisource 70.9%：
两者都 derived_from misc03，彼此却没连边）。

★ 所以本件**同时**做两件事，缺一不可：
1. 读 `derived_from` 的声明
2. **不信声明，直接比内容**——8 词片重叠，以短的一侧为分母（与
   `check_claim_source_independence` 同一把尺，那件做的是断言层，**来源层此前没人做**）

这正是 [[a-gate-that-says-independent-may-not-be]] 那个形状：
**一道自称查独立性的门，如果只读被查方的自我声明，它查的是诚意不是事实。**

## 门槛是量出来的，不是拍的

Whitworth #152 全部 21 对的实测分布：

    重份对：0.3843 … 0.7562   （7 对）
    独立对：0.0000 … 0.0241   （14 对）
    ────────────────────────
    **中间空了 16 倍**，0.30 坐在缺口正中。

★ 最硬的负对照也在这批里：`miscellaneouspa03`（1858 杂稿）×`miscellaneouspa01`（1873 Guns and Steel）
= **0.0241**——**同一个人、同一家出版社（Longman）、同一个书名系列**，
而它们是两部不同的作品，**判据必须不合并**。

## 它判不了什么（射程必须一起说）

- **它只比 8 词片，不懂语义。** 同一个论点被作者在两部书里用不同的话说两遍，本件看不出来。
- **它对非英文语料的分词是 `[a-z0-9]+`**，中日韩会退化成一个空集合 → 重叠恒为 0。
  中文语料的来源去重**本件管不到**，别把它的 ✓ 读成「已核」。
- **它不判「该不该合并」，只报「长得一样」。** 一部书的两个版次（有实质修订）
  会被它判成同一部；是不是该当两处证据，由人按 `counting_convention` 写清楚。
- **★ 对长 s 讹坏的源，它的读数不作数**（v0.0.0.131 加）。
  8 词的连续正确串扛不住逐词 92%–98% 的讹变，读到的低值**分不清
  「确实不同源」与「同源但字形认不出来」**。哪些源属此类由
  `check_longs_corruption.py` 判；**本件对它们的沉默不构成「互相独立」的证据。**

  ★★ 但**不要把这条读成「本件坏了」**——我差点就是这么读的。
  全库 245 对已声明同源实测：n=8 中位 **0.6709**，低于门的只有 **1.6%**，
  十分位 0.376 仍在门之上。**判据整体是好的**，失去分辨力的只是上面那一类源。
  实测见 `_ledgers/_判重分辨力全库实测-2026-08-11.md`。

- **★ `derived_from` 的语义是多义的**，别拿本件的输出反推「声明该不该有」：
  同一字段被用来表达「同作品不同版本」（重叠高）、
  **「同一部出版物的不同卷」（重叠接近 0，而且合理）**、
  「整体与被单独刊行的一章」（以短的一侧为分母时高）三种关系。
  全库读得最低的三对全是第二类（DJBP 1853 vol1/2/3 两两），**低是对的**。

## 输出

- `usable`：与 `quality_check` 同口径的可用来源数
- `distinct_works`：按 ≥threshold 的连通分量算出的独立作品数
- `inflation`：`usable / distinct_works`
- `**未声明的重复对**`：重叠够高而 `derived_from` 两边都没连边的——**这是本件的头条**

退出码：0 = 没有未声明的重复对；1 = 有；3 = 用法错误。
**只报不拦**由调用方决定（`quality_check` 接的是 warning 不是 error，见那边注释）。
"""
from __future__ import annotations

import argparse
import itertools
import json
import pathlib

#: ★ 剥掉抓源方写的出处表头再量——**表头是给人看的出处说明，不是他的话**。
#:   Adams 实测表头占全文中位 39.1%，两两 2556 对里 1764 对因此越线。
import sys as _sys
_sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from common import corpus_body  # noqa: E402
import re
import sys

SHINGLE_N = 8
DEFAULT_THRESHOLD = 0.30
_WORD = re.compile(r"[a-z0-9]+")


def shingles(text: str, n: int = SHINGLE_N) -> set:
    """→ 文本的 n 词片集合。**只认拉丁字母与数字**，射程见文件头。"""
    w = _WORD.findall(text.lower())
    if len(w) < n:
        return set()
    return {" ".join(w[i:i + n]) for i in range(len(w) - n + 1)}


def containment(a: set, b: set) -> float:
    """→ 两集合的重叠率，**以短的一侧为分母**。

    ★ 用包含度而不是 Jaccard：一份 8 KB 的节选与一份 300 KB 的全本，
    Jaccard 会被长度差压到接近 0，而节选**确实完全落在全本里**。
    Whitworth #152 的 `jstor` 只有 5.5% 是他的，正是这种形态。
    """
    if not a or not b:
        return 0.0
    return len(a & b) / min(len(a), len(b))


def components(ids: list, pairs: list) -> list:
    """→ 按 pairs 给出的边求连通分量（并查集）。"""
    parent = {i: i for i in ids}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b, *_ in pairs:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    groups = {}
    for i in ids:
        groups.setdefault(find(i), []).append(i)
    return sorted(groups.values(), key=len, reverse=True)


BOILERPLATE_DF = 0.85     # 出现在这么高比例的来源里 → 判为样板，两侧一起扣掉
BOILERPLATE_MIN_N = 5     # 少于这么多份时不做扣除（否则真的三份重份会被当样板抹掉）


def boilerplate(sh: dict, df_floor: float = BOILERPLATE_DF,
                min_n: int = BOILERPLATE_MIN_N) -> set:
    """→ 出现在 ≥df_floor 比例来源里的词片（**样板**）。

    ★★★★ 这一步是 2026-08-07 被自己的假阳打出来的。

    第一版没有它，全库回扫报 **Adams #131 虚高 6.9×、1587 对未声明重复**。
    去读命中：他那 69 份语料**每份只有 2–4 KB**，而每份开头都带同一段
    **本流水线自己写的表头**——

        SOURCE: Discussion remarks by Comfort A. Adams on "SYNCHRONOUS MACHINES"…
        IN:     Transactions of the American Institute of Electrical Engineers…
        URL:    https://archive.org/details/…
        FILE:   …
        （外加一整段 OCR 约定说明：「OCR reproduced verbatim and uncorrected
          including its mistakes」「printed is Comfort A Adams or C A Adams…」）

    共有词片抽样出来全是这段话。**判据量到的是我自己的模板，不是来源。**
    与 [[i-create-the-leak-channels-myself]]、
    [[overlap-metrics-need-a-shared-baseline-subtracted]] 同一条：
    **重合类判据必须先减掉三方共有的东西，而且分子分母两边一起减。**

    门槛是量出来的：

        Adams #131（69 份）  DF=100% 的词片 **47** 个，DF≈90% 的 **175** 个 → 共 222
                            而每份只有 420–613 个词片，**样板就是那 225 个共有片**
        Whitworth #152（7 份）**DF ≥90% 的词片：0 个**（最高 70%，19 个）

    两者不重叠，0.85 坐在中间。

    ★ `min_n`：份数太少时不扣。5 份里的 5 份重份 DF=100%，那不是样板，是真重复。
    """
    n = len(sh)
    if n < min_n:
        return set()
    df = {}
    for s in sh.values():
        for g in s:
            df[g] = df.get(g, 0) + 1
    need = df_floor * n
    return {g for g, c in df.items() if c >= need}


def analyse(records: list, texts: dict, threshold: float = DEFAULT_THRESHOLD) -> dict:
    """records 是 usable 的台账行；texts 是 {source_id: 正文}。"""
    ids = [r["source_id"] for r in records]
    name = {r["source_id"]: r.get("original_name") or r["source_id"] for r in records}
    declared = {r["source_id"]: set(r.get("derived_from") or []) for r in records}
    sh = {sid: shingles(texts.get(sid, "")) for sid in ids}

    boiler = boilerplate(sh)
    net = {sid: (s - boiler) for sid, s in sh.items()}

    # ★★ 「已声明」按**声明的连通分量**算，不是只看直接边（2026-08-07 修）。
    #   第一版只判 `b in derived_from[a] or a in derived_from[b]`。
    #   而 `derived_from` 的自然写法是**全组都指向一个基准件**：
    #     misc00 → misc03、wikisource → misc03
    #   于是 misc00 × wikisource **没有直接边**，被报成「未声明」——
    #   而声明者其实已经把话说完了。
    #   ★ 这不是放宽：只有**声明**连得上的才免报，内容连得上但声明连不上的照报。
    #   ★ 键用**组内最小 source_id**，不用 `id(grp)`：后者是对象地址，
    #     列表被回收后地址会被复用，两个不相干的组可能拿到同一个键。
    _decl_edges = [(sid, d) for sid, ds in declared.items() for d in ds if d in declared]
    _decl_group = {}
    for grp in components(list(declared), _decl_edges):
        key = min(grp)
        for sid in grp:
            _decl_group[sid] = key

    empty = [name[s] for s in ids if not sh[s]]
    # ★ 扣掉样板之后变空的，与「本来就空」要分开——前者说明**这份文件几乎全是样板**
    all_boiler = [name[s] for s in ids if sh[s] and not net[s]]
    dup_pairs, undeclared, boiler_only = [], [], []
    for a, b in itertools.combinations(ids, 2):
        ov_raw = containment(sh[a], sh[b])
        ov = containment(net[a], net[b])
        if ov_raw >= threshold > ov:
            # 只在**没扣样板**时越线 → 那一对的「重复」是样板撑出来的
            boiler_only.append({"甲": name[a], "乙": name[b],
                                "扣样板前": round(ov_raw, 4), "扣样板后": round(ov, 4)})
        if ov < threshold:
            continue
        #   单件自成一组时键就是它自己，两个单件的键必然不同 → 不会误判成已声明。
        is_declared = (b in declared[a]) or (a in declared[b]) or (
            _decl_group.get(a, a) == _decl_group.get(b, b))
        row = {"甲": name[a], "乙": name[b], "重叠": round(ov, 4),
               "扣样板前": round(ov_raw, 4), "已声明 derived_from": is_declared}
        dup_pairs.append((a, b, ov, is_declared))
        if not is_declared:
            undeclared.append(row)

    comps = components(ids, dup_pairs)
    distinct = len(comps)
    out = {
        "usable": len(ids),
        "distinct_works": distinct,
        "inflation": round(len(ids) / distinct, 3) if distinct else None,
        "threshold": threshold,
        "**未声明的重复对**": undeclared,
        "已声明的重复对数": sum(1 for *_x, d in dup_pairs if d),
        "作品分组": [[name[s] for s in g] for g in comps],
        "样板词片数": len(boiler),
        "★ 只因样板才越线的对数（已扣除，不计入重复）": len(boiler_only),
    }
    if boiler_only:
        out["★ 只因样板才越线的（抽样）"] = boiler_only[:5]
    if boiler:
        out["★ 样板抽样"] = sorted(boiler)[:4]
    if all_boiler:
        # ★ 这不是「没重复」，是**这几份文件扣掉流水线自己的表头之后什么都不剩**
        out["★★ 扣掉样板后为空的（文件几乎全是表头）"] = all_boiler
    if empty:
        # ★ 空集合不是「没有重复」，是「本件对这几份看不见」。
        #   `[]`／`0` 会被读成通过——[[empty-default-swallows-unknown]]。
        out["★ 本件看不见的（分词后不足 8 词，多为中日韩或纯噪声）"] = empty
    return out


def load(target: pathlib.Path) -> tuple:
    led = target / "evidence/source-ledger.jsonl"
    if not led.is_file():
        raise FileNotFoundError(f"找不到台账：{led}")
    rows = [json.loads(l) for l in led.read_text(encoding="utf-8").splitlines() if l.strip()]
    usable = [r for r in rows
              if r.get("split") == "train"
              and r.get("tier") != "U"
              and r.get("extraction_status") != "failed"]
    texts = {}
    for r in usable:
        d = target / "references/sources" / r["source_id"]
        f = next(iter(sorted(d.glob("*.txt"))), None) if d.is_dir() else None
        texts[r["source_id"]] = (corpus_body(f.read_text(encoding="utf-8", errors="replace"))
                                 if f else "")
    return usable, texts


def self_test() -> int:
    ok = True

    def chk(msg, cond):
        nonlocal ok
        ok = ok and bool(cond)
        print(("  ✓ " if cond else "  ✗ ") + msg)

    print("\n══ ★★★★ 逐字真实样本：Whitworth #152 的 21 对实测 ══")
    #   下面这张表是 2026-08-07 在真语料上跑出来的**实测值**，不是构造的。
    #   ★ 之所以要真值：合成夹具会把「重份」写得比真实的更像、把「独立」写得比真实的更不像，
    #     而本件的全部价值就在于**那条缝在哪**。
    REAL = {  # (甲, 乙): 实测重叠
        ("misc03-1858", "misc00-1858"): 0.5528,
        ("misc03-1858", "wikisource-1858"): 0.7556,
        ("misc03-1858", "ny1854"): 0.4043,
        ("misc00-1858", "wikisource-1858"): 0.7093,
        ("misc00-1858", "ny1854"): 0.3843,
        ("wikisource-1858", "ny1854"): 0.4786,
        ("misc01-1873", "misc02-1873"): 0.7562,
        # ★★ 最硬的负对照：**同一个人、同一家出版社（Longman）、同一个书名系列**
        ("misc03-1858", "misc01-1873"): 0.0241,
        ("misc03-1858", "misc02-1873"): 0.0154,
        ("misc00-1858", "misc01-1873"): 0.0239,
        ("misc00-1858", "misc02-1873"): 0.0151,
        ("wikisource-1858", "misc01-1873"): 0.0013,
        ("wikisource-1858", "misc02-1873"): 0.0014,
        ("misc03-1858", "jstor1868"): 0.0000,
        ("misc00-1858", "jstor1868"): 0.0000,
        ("wikisource-1858", "jstor1868"): 0.0000,
        ("misc01-1873", "ny1854"): 0.0000,
        ("misc01-1873", "jstor1868"): 0.0000,
        ("misc02-1873", "ny1854"): 0.0000,
        ("misc02-1873", "jstor1868"): 0.0000,
        ("ny1854", "jstor1868"): 0.0000,
    }
    dup = sorted(v for v in REAL.values() if v >= DEFAULT_THRESHOLD)
    ind = sorted(v for v in REAL.values() if v < DEFAULT_THRESHOLD)
    chk(f"21 对齐全（{len(REAL)} 对）", len(REAL) == 21)
    chk(f"重份 {len(dup)} 对，落在 {dup[0]:.4f}–{dup[-1]:.4f}", len(dup) == 7 and dup[0] >= 0.38)
    chk(f"独立 {len(ind)} 对，落在 {ind[0]:.4f}–{ind[-1]:.4f}", len(ind) == 14 and ind[-1] <= 0.025)
    gap = dup[0] / ind[-1] if ind[-1] else float("inf")
    chk(f"**两群之间空了 {gap:.1f} 倍**，门槛 {DEFAULT_THRESHOLD} 坐在缺口里", gap >= 10)
    chk("★ 最硬负对照：1858 杂稿 × 1873 Guns and Steel = 0.0241"
        "（同人同社同系列，**不许合并**）", REAL[("misc03-1858", "misc01-1873")] < DEFAULT_THRESHOLD)

    print("\n── 连通分量：7 份 → 3 部作品 ──")
    ids = ["misc03-1858", "misc00-1858", "wikisource-1858", "ny1854",
           "misc01-1873", "misc02-1873", "jstor1868"]
    pairs = [(a, b, v, False) for (a, b), v in REAL.items() if v >= DEFAULT_THRESHOLD]
    comps = components(ids, pairs)
    chk(f"分成 {len(comps)} 组：{[sorted(g) for g in comps]}", len(comps) == 3)
    chk("1858 那组含 4 份（三个副本 + 作附录重印的 1854 报告）",
        any(len(g) == 4 and "ny1854" in g for g in comps))
    chk("1873 那组含 2 份", any(len(g) == 2 for g in comps))
    chk("jstor 独自一组", any(g == ["jstor1868"] for g in comps))

    print("\n── ★★★ 声明会漏：只读 derived_from 的判据抓不到 4 对 ──")
    #   实测：7 对重叠 ≥30%，而**我自己只声明了 3 对**。
    #   漏的那 4 对包括我明知道的那一对（1854 报告是 1858 卷的附录，写进了散文没写进字段）。
    DECLARED = {("misc03-1858", "misc00-1858"), ("misc03-1858", "wikisource-1858"),
                ("misc01-1873", "misc02-1873")}
    dup_pairs = {(a, b) for (a, b), v in REAL.items() if v >= DEFAULT_THRESHOLD}
    missed = dup_pairs - DECLARED
    chk(f"未声明 {len(missed)} 对：{sorted(missed)}", len(missed) == 4)
    chk("★ 其中含「1854 报告 × 1858 卷」——**声明者知道却没写进字段**",
        ("misc03-1858", "ny1854") in missed)

    print("\n══ ★★★★ 逐字真实样本②：Adams #131——**判据量到的是我自己的模板** ══")
    #   全库回扫（25 个归档工作区）的第一版结果里，Adams #131 报
    #   **虚高 6.9×、1587 对未声明重复**——全库最严重的一个。
    #   ★ 去读命中才发现：他那 69 份语料**每份只有 2–4 KB**，
    #     而每份开头都带同一段**本流水线自己写的表头**（SOURCE:/IN:/URL:/FILE: +
    #     一整段 OCR 约定说明）。共有词片抽样出来全是那段话。
    #   ★★ **报率之前先读命中**——这一条今天在两件事上各救了我一次。
    A = {"raw_inflation": 6.9, "raw_undeclared": 1587,
         "net_inflation": 1.327, "net_undeclared": 18,
         "boiler_shingles": 222, "boiler_only_pairs": 1569,
         "pair_raw": 0.536, "pair_net": 0.015}
    chk(f"扣样板后虚高 {A['raw_inflation']}× → **{A['net_inflation']}×**",
        A["net_inflation"] < 1.5 < A["raw_inflation"])
    chk(f"未声明对 {A['raw_undeclared']} → **{A['net_undeclared']}**",
        A["net_undeclared"] < A["raw_undeclared"] / 50)
    chk(f"**{A['boiler_only_pairs']} 对是样板撑出来的**"
        f"（如 0001-conv-1907 × 0003-conv-1908：{A['pair_raw']:.1%} → {A['pair_net']:.1%}）",
        A["pair_raw"] >= DEFAULT_THRESHOLD > A["pair_net"])
    chk(f"样板词片 {A['boiler_shingles']} 个（DF=100% 的 47 + DF≈90% 的 175）",
        A["boiler_shingles"] == 222)
    print("  ★ 而同一次改动下 **Whitworth #152 一点没动**：样板词片 0 个，"
          "7→3 部、4 对未声明照旧——**真阳没被这次减法误伤**。")
    chk("门槛 0.85 坐在两者之间（Adams DF≥90% 有 222 片，Whitworth 0 片）",
        BOILERPLATE_DF == 0.85)
    chk(f"份数 <{BOILERPLATE_MIN_N} 时不做扣除（5 份里 5 份重份不是样板）",
        boilerplate({f"s{i}": {"a b c d e f g h"} for i in range(4)}) == set())
    chk("份数够时才扣",
        boilerplate({f"s{i}": {"a b c d e f g h"} for i in range(6)}) != set())

    print("\n── ★★ 「已声明」按连通分量算，不是只看直接边 ──")
    #   `derived_from` 的自然写法是全组都指向一个基准件：misc00→misc03、wikisource→misc03。
    #   于是 misc00 × wikisource **没有直接边**——第一版把它报成「未声明」，
    #   而声明者其实已经把话说完了。★ 这不是放宽：内容连得上而声明连不上的照报。
    _t = "the true plane is obtained by mutual grinding of three surfaces in turn " * 40
    _recs = [{"source_id": "src-aaaaaaaaaaaa", "original_name": "base.txt"},
             {"source_id": "src-bbbbbbbbbbbb", "original_name": "scanB.txt",
              "derived_from": ["src-aaaaaaaaaaaa"]},
             {"source_id": "src-cccccccccccc", "original_name": "scanC.txt",
              "derived_from": ["src-aaaaaaaaaaaa"]}]
    _tx = {"src-aaaaaaaaaaaa": _t, "src-bbbbbbbbbbbb": _t, "src-cccccccccccc": _t}
    _r = analyse(_recs, _tx)
    chk(f"B 与 C 都只指向 A，B×C 不再报未声明：{len(_r['**未声明的重复对**'])} 对",
        not _r["**未声明的重复对**"] and _r["distinct_works"] == 1)
    # ★ 负对照：**只有 B 声明了 A，C 谁也没声明** → C 与 A、C 与 B 都该报
    _recs2 = [dict(_recs[0]), dict(_recs[1]),
              {"source_id": "src-cccccccccccc", "original_name": "scanC.txt"}]
    _r2 = analyse(_recs2, _tx)
    chk(f"C 没声明时照报：{len(_r2['**未声明的重复对**'])} 对（应为 2）",
        len(_r2["**未声明的重复对**"]) == 2)

    print("\n── 反向对照：两份毫无关系的文本不许报 ──")
    a = shingles("the true plane is obtained by the mutual grinding of three surfaces " * 20)
    b = shingles("choice and chance an elementary treatise on permutations " * 20)
    chk(f"重叠 {containment(a, b):.4f} < 门槛", containment(a, b) < DEFAULT_THRESHOLD)

    print("\n── 反向对照：短到分不出词片时，报「看不见」而不是「没重复」 ──")
    r = analyse([{"source_id": "s1", "original_name": "tiny.txt"},
                 {"source_id": "s2", "original_name": "tiny2.txt"}],
                {"s1": "too short", "s2": "also short"})
    chk(f"看不见的被单列出来：{r.get('★ 本件看不见的（分词后不足 8 词，多为中日韩或纯噪声）')}",
        len(r.get("★ 本件看不见的（分词后不足 8 词，多为中日韩或纯噪声）") or []) == 2)
    chk("**且没有报成 0 个重复对就完事**",
        r["distinct_works"] == 2 and not r["**未声明的重复对**"])

    print("\n── 反向对照：同一份自己跟自己不算一对 ──")
    t = "the uniform system of screw threads proposed to the institution " * 30
    r = analyse([{"source_id": "s1", "original_name": "a.txt"}], {"s1": t})
    chk(f"单份 → 1 部作品、0 对：{r['distinct_works']}, {len(r['**未声明的重复对**'])}",
        r["distinct_works"] == 1 and not r["**未声明的重复对**"])

    print("\n" + ("✓ 自测全过" if ok else "✗ 自测未过"))
    return 0 if ok else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("target", nargs="?", help="工作区目录")
    ap.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true", help="只跑负对照，不读真实树")
    a = ap.parse_args()

    if a.self_test:
        return self_test()
    if not a.target:
        print("✗ 需要工作区目录（或只给 --self-test）", file=sys.stderr)
        return 3
    try:
        usable, texts = load(pathlib.Path(a.target))
    except (FileNotFoundError, OSError) as exc:
        print(f"✗ {exc}", file=sys.stderr)
        return 3

    r = analyse(usable, texts, a.threshold)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        print(f"可用来源 {r['usable']} 份 → **按内容去重后 {r['distinct_works']} 部作品**"
              f"（虚高 {r['inflation']}×，门槛 {r['threshold']}）")
        for g in r["作品分组"]:
            head = g[0]
            rest = "".join(f"\n        ＋ {x}" for x in g[1:])
            print(f"  · {head}{rest}")
        if r["**未声明的重复对**"]:
            print(f"\n★★ **重叠够高而 `derived_from` 两边都没连边的 "
                  f"{len(r['**未声明的重复对**'])} 对**——这些是台账上看不出来的：")
            for p in r["**未声明的重复对**"]:
                print(f"    {p['重叠']:>6.1%}  {p['甲']}  ×  {p['乙']}")
            print("  ★ 处置：要么补 `derived_from`，要么在 `attribution_basis.counting_convention` "
                  "里写清为什么它们该当两处证据。**别只在散文里写——那是我这次犯的错。**")
        else:
            print("\n✓ 没有未声明的重复对")
        if r.get("★ 本件看不见的（分词后不足 8 词，多为中日韩或纯噪声）"):
            print(f"\n⚠ **本件看不见的 "
                  f"{len(r['★ 本件看不见的（分词后不足 8 词，多为中日韩或纯噪声）'])} 份**"
                  f"（分词后不足 8 词；中日韩语料本件一律看不见）——**不是「已核干净」**：")
            for n in r["★ 本件看不见的（分词后不足 8 词，多为中日韩或纯噪声）"]:
                print(f"    {n}")
    return 1 if r["**未声明的重复对**"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
