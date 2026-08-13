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


def pairs(ho: dict, tr: dict):
    """→ [(holdout_id, train_id)]，**纯函数**（签名已经算好）。"""
    return [(h, t) for h, (hs, *_) in ho.items()
            for t, (ts, *_) in tr.items() if same_work(hs, ts)]


def self_test() -> int:
    ok = n = 0

    def chk(d, c):
        nonlocal ok, n
        n += 1
        ok += 1 if c else 0
        print(f"  {'✓' if c else '✗'} {d}")

    A = "the quick brown fox jumps over the lazy dog and then some more words here to make it long enough"
    B = A + " plus a tail that differs a bit at the end of the text"
    C = "completely unrelated sentence about numbers and machines with no shared phrasing whatsoever ok"
    ho = {"h1": (signature(A), "t", "1900", "en")}
    tr = {"t1": (signature(B), "t", "1900", "en"), "t2": (signature(C), "u", "1900", "en")}
    got = pairs(ho, tr)
    chk(f"★★ **正对照：同一部作品被配上**（实得 {got}）", got == [("h1", "t1")])
    chk("★★ **反例：不相干的文本不许配上**", ("h1", "t2") not in got)
    chk("★ 两边都空 ⇒ 0 对", pairs({}, {}) == [])
    chk("★★ **holdout 读不到正文时是 0 对 —— 调用方必须另计未量，不许当成干净**",
        pairs({}, tr) == [])
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
    print("\n★★ 这个数是**下界**：`same_work` 靠 n-gram，**跨语种恒为 0** —— "
          "原文在 train、译本在 holdout 时本件一声不吭。**「0 对」不等于「没有泄漏」。**")
    print("★ 报出来的每一对都要人读：要么重划 split，要么在判决书里写明这一对的存在。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
