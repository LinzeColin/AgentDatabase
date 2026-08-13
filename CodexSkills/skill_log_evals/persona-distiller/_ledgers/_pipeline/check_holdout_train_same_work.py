#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_holdout_train_same_work.py —— **密封集里那部书，train 里也有一份**

## 为什么要有这件

holdout 是密封集：题从它出，而人物档案是从 train 蒸出来的。
**同一部作品同时在两边**，就意味着答案本来就在被测者的材料里 ——
这时候量到的 delta 不是「声口／方法」，是**背下来的内容**。

2026-08-14 对第 1 批**正等着判分**的八个人逐对量了一遍，实测**两对**：

| 人 | holdout | train |
|---|---|---|
| niccolo-machiavelli | `A true copy of a letter written by … 1691` | `Machiavel's vindication of himself… 1691` |
| jean-jacques-rousseau | `Extrait du Projet de paix perpétuelle…` 1761 | **同名同年，另一份** |

Machiavelli 那一对尤其说明问题：**两个编目题名完全不同，是同一份 1691 年的小册子**
—— 按题名去查是查不出来的，只有拿正文比才看得见。

## ★★★ 先说清：**权威不是本件**

`registry/.../scripts/check_holdout_overlap.py` **早就在，而且是硬门**：

    覆盖率 = |holdout 的 shingle ∩ train 的| / |**holdout** 的|    （n=8）
    ≥0.30 ✗ 硬失败｜0.10–0.30 ⚠ 需人工核｜<0.10 ✓

**它的分母是 holdout，本件的 `same_work` 分母是并集或较短的一侧** ——
所以两把尺子会给出不同答案。**划 split 有效性以它为准，不是以本件为准。**

我第一版没先搜仓就造了本件，结果两个方向都报错：
把覆盖率 **0.0780** 的 Machiavelli 说成「同一部作品」（它按权威判据是**绿的**），
又把覆盖率 **0.6896–0.7418** 的 Nightingale 只写成「2/32 题受影响」（她按权威判据
**是硬失败，而且已判分入库**）。[[i-built-a-second-ruler-while-the-authoritative-one-sat-in-scripts]]

⇒ **本件的定位**：补权威那把够不着的一格 ——
「覆盖率低于 0.10、但两份确实是同一部作品」（体量相近时 Jaccard 比覆盖率敏感）。
**报出来的先拿 `check_holdout_overlap` 复核一遍再说话。**

## ★★ 它判得了什么、判不了什么（**射程要先说**）

- **同语种：可靠。** 用的是全库同一把尺子（`same_work`：Jaccard ≥0.05 或包含率 ≥0.25），
  实测同一部作品 0.2155–0.4254、不同作品 ≤0.0018，中间是空的。
- **跨语种：判不了，恒为 0。** 原文与译文的 n-gram 重叠是 **0.0000**
  —— 法文 `Émile` 在 train、德译 `Aemil` 在 holdout，本件**一声不吭**。
  这不是本件的缺陷，是这把尺子的物理极限。[[cross-language-holdout-leak-is-invisible]]
- 因此本件报的数是**下界**：真实的重合只会更多。**「0 对」不等于「没有泄漏」。**

★ 按题名去猜跨语种的那一半会**大量误报**：实测 Pestalozzi 的
`Lienhard und Gertrud` 1790 两边都有、Fröbel 的 `The education of man` 两边都有，
而正文比下来**都不是同一份文本**（多卷本的不同卷、不同印本的不同 OCR）。
⇒ 题名同不等于文本同，**本件只认正文**。

## 用法

    python3 check_holdout_train_same_work.py --batch1     # 第 1 批八人（约 80 秒）
    python3 check_holdout_train_same_work.py --all        # 全库（慢，十几分钟）
    python3 check_holdout_train_same_work.py <工作区>
    python3 check_holdout_train_same_work.py --self-test

退出码恒 0：**报出来的要人读**（同一份文本两边都有 ⇒ 要么重划、要么在判决书里写明）。
"""
import argparse
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from check_claim_evidence_independence import guess_lang, same_work  # noqa: E402
from find_second_evidence import norm  # noqa: E402
from measure_distinct_works import signature  # noqa: E402
from workspace_roots import iter_workspaces  # noqa: E402

CORPORA = HERE.parent.parent / "_corpora"
BATCH1 = ["lincoln-174", "jefferson-175", "bismarck-176", "machiavelli-177",
          "rousseau-178", "kant-179", "pestalozzi-180", "frobel-181"]

# ★★ 较短一侧至少这么多 shingle，否则不算命中。
#   第一版没有这条，全库报 **218 对** —— 其中 Adams 一个人占 120 对。
#   打开读：他的 holdout 2,277 词 vs train **394 词**，包含率 0.6182 却只共有 **34 个 shingle**
#   —— 是 AIEE 会议录的**版面样板**（刊头 ＋ 作者栏）撑起来的，不是同一篇文章。
#   命中对里「较短一侧 shingle 数」的中位数：Adams **74**，而真命中的
#   Machiavelli 957、Rousseau 1,464、Nightingale 5,597。**门放 200，余量 4.8 倍。**
#   加上这条之后 218 → 92 对、11 个工作区。[[read-the-hits-before-reporting-the-rate]]
MIN_SHINGLE = 200


def load_split(ws: pathlib.Path, split: str):
    """→ {source_id: (签名, 题名, 年, 语种)}。**读不到正文的不进来**，由调用方计未量。"""
    led = ws / "evidence/source-ledger.jsonl"
    out = {}
    if not led.is_file():
        return out
    for line in led.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("split") != split:
            continue
        p = ws / str(r.get("local_path") or "")
        if not p.is_file():
            continue
        t = norm(p.read_text(encoding="utf-8", errors="replace"))
        out[r["source_id"]] = (signature(t), str(r.get("title") or "")[:56],
                               str(r.get("published_at") or "")[:4], guess_lang(t))
    return out


def pairs(ho: dict, tr: dict, min_sh: int = MIN_SHINGLE):
    """→ [(holdout_id, train_id)]，**纯函数**（签名已经算好）。

    ★ `min_sh`：较短一侧的 shingle 数下限。低于它的一律不算命中 ——
      短文件靠版面样板就能把包含率顶到 0.6 以上（实测 34 个共有 shingle）。
    """
    return [(h, t) for h, (hs, *_) in ho.items()
            for t, (ts, *_) in tr.items()
            if min(len(hs), len(ts)) >= min_sh and same_work(hs, ts)]


def self_test() -> int:
    ok = n = 0

    def chk(d, c):
        nonlocal ok, n
        n += 1
        ok += 1 if c else 0
        print(f"  {'✓' if c else '✗'} {d}")

    # ★★ 夹具必须**够长**：门是「较短一侧 ≥200 shingle」，用我随手编的一句话做正对照
    #   会被门拦掉——第一版正是如此，正对照当场判红。[[fixtures-cleaner-than-the-real-thing]]
    #   这里造 4,000 个互不相同的词，签名规模与真实一手源同量级。
    A = " ".join(f"w{i}x{i*7%1013}" for i in range(4000))
    B = A + " " + " ".join(f"tail{i}" for i in range(300))      # 同一部作品的另一印本
    C = " ".join(f"z{i}q{i*3%997}" for i in range(4000))        # 完全不同的作品
    SHORT = "the quick brown fox jumps over the lazy dog and then some more words here ok"
    ho = {"h1": (signature(A), "t", "1900", "en")}
    tr = {"t1": (signature(B), "t", "1900", "en"), "t2": (signature(C), "u", "1900", "en")}
    got = pairs(ho, tr)
    chk(f"★★ **正对照：同一部作品被配上**（实得 {got}）", got == [("h1", "t1")])
    chk("★★ **反例：不相干的文本不许配上**", ("h1", "t2") not in got)
    chk("★ 两边都空 ⇒ 0 对", pairs({}, {}) == [])
    chk("★★ **holdout 读不到正文时是 0 对 —— 调用方必须另计未量，不许当成干净**",
        pairs({}, tr) == [])
    # ★★ 短文件反例：签名很小的两份，即使 same_work 说是，也不许算命中
    tiny_h = {"h9": (signature(SHORT), "t", "1900", "en")}
    tiny_t = {"t9": (signature(SHORT + " and a little more"), "t", "1900", "en")}
    chk(f"★★ **反例：较短一侧只有 {len(signature(SHORT))} 个 shingle（< {MIN_SHINGLE}）⇒ 不算命中**"
        "　——Adams 那 120 对就是这么来的", pairs(tiny_h, tiny_t) == [])
    chk("★ 把门降到 1 时同一对又出现（证明是**门**在起作用，不是这两份本来就不像）",
        pairs(tiny_h, tiny_t, min_sh=1) == [("h9", "t9")])
    print(f"\n{'✓ 全过' if ok == n else f'✗ {n - ok}/{n} 项不符'}")
    return 0 if ok == n else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("workspace", nargs="?")
    ap.add_argument("--batch1", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()

    if a.workspace:
        wss = [pathlib.Path(a.workspace)]
    elif a.batch1:
        wss = [next(CORPORA.glob(f"wip-{w}/workspaces/*")) for w in BATCH1]
    elif a.all:
        wss = list(iter_workspaces(CORPORA))
    else:
        ap.error("要 <工作区> ／ --batch1 ／ --all ／ --self-test")

    total, measured, no_ho, no_text = 0, 0, [], []
    for ws in wss:
        ho, tr = load_split(ws, "holdout"), load_split(ws, "train")
        if not ho:
            (no_ho if not (ws / "evidence/source-ledger.jsonl").is_file() else no_text).append(ws.name)
            continue
        measured += 1
        hits = pairs(ho, tr)
        total += len(hits)
        langs = sorted({v[3] for v in list(ho.values()) + list(tr.values()) if v[3] != "?"})
        mark = "❗" if hits else "·"
        print(f"{mark} {ws.name:26s} holdout 读到 {len(ho):3d}／train 读到 {len(tr):3d}"
              f"｜语种 {langs}｜**同作品 {len(hits)} 对**")
        for h, t in hits:
            print(f"     ❗ holdout [{ho[h][2]} {ho[h][3]}] {ho[h][1]}")
            print(f"        ↔ train  [{tr[t][2]} {tr[t][3]}] {tr[t][1]}")

    print(f"\n★★ **分母**：给了 {len(wss)} 个工作区 → **真量到 {measured} 个**"
          f"｜holdout 读不到正文/没有 holdout 的 {len(no_text) + len(no_ho)} 个（**未量，不是干净**）")
    if no_text:
        print(f"     未量：{', '.join(no_text)}")
    print(f"⇒ **同一部作品同时在 holdout 与 train 的：{total} 对**")
    print(f"★ 前提：**较短一侧 ≥{MIN_SHINGLE} 个 shingle** 才算命中 —— "
          f"不加这条，短文件的版面样板会把包含率顶上去（**全库实测 218 → 92 对**，"
          f"其中 Adams 一个人 120 对全是这么来的）")
    print("\n★★ 这个数是**下界**：`same_work` 靠 n-gram，**跨语种恒为 0** —— "
          "原文在 train、译本在 holdout 时本件一声不吭。**「0 对」不等于「没有泄漏」。**")
    print("★ 报出来的每一对都要人读：要么重划 split，要么在判决书里写明这一对的存在。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
