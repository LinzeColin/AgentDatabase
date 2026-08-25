#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**候选侧的答案里，有没有只可能来自 holdout 的东西？**

## 缺口

已有两件与 holdout 有关的判据，**射程都不在答案上**：

- `check_holdout_mention`：扫**建模者可读的文件**（十份产物、研究道、claims），
  查有没有提到 holdout 的文件名或抄它的内容。**它不看答案。**
- `check_holdout_overlap`：查 **holdout ↔ train 语料**本身有没有内容重合。
  **它也不看答案。**

于是「候选答题子代理偷读了 holdout」这件事**没有任何判据在查**——
唯一的证据是子代理自己写的 `__incident__`，而
**自述不是证据**（[[self-report-is-not-evidence]]）。
Adams #131 实测过更坏的情形：holdout 隔离在三条独立通道上都不成立，而所有门都是绿的。

## 判据形状：**holdout 独有的专名与数字**，不是字面重叠

答案是中文散文，holdout 是英文/德文 OCR——**字面 n-gram 重叠天然为 0**，
拿它当判据等于永远绿（[[a-red-that-can-never-turn-green-is-not-a-signal]]）。

能穿过语言边界的是**专名与数字**：人名、机构名、年份、页码、卷号、金额。
所以本件：

1. 从 holdout 各文件取「专名候选」（连续大写词组）与「数字」；
2. **减掉所有 train 语料里也出现的**——剩下的才是「只可能来自 holdout」的；
3. 看候选答案里有没有；**同时用基线答案做负对照**——
   基线从没读过任何文件，**它命中说明这个词根本不是 holdout 独有**（是常识），
   那一条要从名单里剔掉，不算泄漏。

★★★★ **第 2 步和第 3 步的负对照缺一不可。** 只做第 2 步会把「这个人的常见事实」
当成 holdout 独有；只做第 3 步会把所有专名都报出来。

## 射程边界（本件看不见的）

- **意思泄漏它抓不到。** 读了 holdout 之后用自己的话转述、不带任何专名与数字，
  本件一律放行。**它挡的是「带着不该有的具体东西回来」，不是「读过没有」。**
- **OCR 把专名弄坏时会漏。** holdout 里 `Ganrr` 这种坏拼写不会出现在答案里。
- **答案里的中文译名它不认。** `Remington` 写成「雷明顿」就穿过去了。
  ★ 这一条是真缺口，**不要把本件的绿读成「没泄」**。
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

PROPER = re.compile(r"\b[A-Z][A-Za-z'À-ÿ]{2,}(?:\s+[A-Z][A-Za-z'À-ÿ]{2,})*\b")
NUMBER = re.compile(r"\b\d{2,5}\b")
# 太常见、跨语料必然共有的词，先剔掉，免得名单里全是噪声
STOP = {"The", "This", "That", "And", "But", "For", "With", "From", "Mr", "Mrs", "Dr",
        "In", "It", "If", "As", "At", "By", "On", "To", "We", "I", "He", "She", "They"}


def tokens(text: str) -> tuple[set[str], set[str]]:
    props = {m.group(0) for m in PROPER.finditer(text)}
    props = {p for p in props if p not in STOP and len(p) >= 4}
    nums = {m.group(0) for m in NUMBER.finditer(text)}
    return props, nums


def load_answers(path: pathlib.Path) -> dict[str, str]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        return {k: v for k, v in raw.items() if isinstance(v, str) and not k.startswith("__")}
    out = {}
    for row in raw:
        if isinstance(row, dict) and "id" in row:
            out[row["id"]] = row.get("answer") or row.get("text") or ""
    return out


def scan(ws: pathlib.Path, candidate: pathlib.Path, baseline: "pathlib.Path | None",
         prompts: "pathlib.Path | None" = None) -> dict:
    ws = ws.expanduser().resolve()
    led = ws / "evidence" / "source-ledger.jsonl"
    if not led.is_file():
        return {"状态": "source-ledger.jsonl 不在，**未核验**（不是通过）"}
    hold_paths, train_paths = [], []
    for line in led.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        p = ws / (r.get("local_path") or "")
        if not p.is_file():
            continue
        (hold_paths if r.get("split") == "holdout" else train_paths).append(p)
    if not hold_paths:
        return {"状态": "台账里没有 holdout 源，**未核验**（不是通过）"}

    hold_p, hold_n = set(), set()
    for p in hold_paths:
        a, b = tokens(p.read_text(encoding="utf-8", errors="replace"))
        hold_p |= a
        hold_n |= b
    train_p, train_n = set(), set()
    for p in train_paths:
        a, b = tokens(p.read_text(encoding="utf-8", errors="replace"))
        train_p |= a
        train_n |= b
    only_p = hold_p - train_p
    only_n = hold_n - train_n

    cand = load_answers(candidate)
    base = load_answers(baseline) if baseline and baseline.is_file() else {}
    cand_text = " ".join(cand.values())
    base_text = " ".join(base.values())

    # ★ 负对照：基线从没读过任何文件；它也命中的词**不是 holdout 独有**，剔掉。
    common_sense_p = {t for t in only_p if t in base_text}
    common_sense_n = {t for t in only_n if t in base_text}

    #   ★★★★ 2026-08-11（Shewhart #165 撞出）：**还要减掉两样，否则必然误报。**
    #
    #   ① **产物**——候选方的合法输入就是那十份 Markdown。
    #      holdout 那部作品的刊名、丛书名、题名里的通用词（`Study`、`Through`、
    #      `Transactions`、`Bell System Technical Journal`）**同时出现在产物里**，
    #      因为产物本来就要列出他的其他著作。**候选说得出它们，不是因为读了 holdout。**
    #
    #   ② **题面**——★★ 这一条是结构性的：**每一道 known 题都必然点名 holdout 那部作品**，
    #      那正是 known 题的定义（「1928 年你在《富兰克林研究所学报》上那篇…」）。
    #      不减题面，**known 题会 100% 误报**。
    #      实测：候选那句话是「里面**没有** 1928 年的《富兰克林研究所学报》文章」——
    #      **它在说那篇不在它手上，而门把这句判成了泄漏。**
    #
    #   ★ 减法要减在**分子**上（候选命中），不是把 holdout 词表整个缩小——
    #      [[overlap-metrics-need-a-shared-baseline-subtracted]]。
    prod_text = ""
    for _rel in ("facts.md", "cognitive-os.md", "decision-policy.md", "strategy.md",
                 "capabilities.md", "persona.md", "work.md", "boundaries.md",
                 "hypotheses.md", "divergence-map.md"):
        _p = ws / _rel
        if _p.is_file():
            prod_text += " " + _p.read_text(encoding="utf-8", errors="replace")
    prompt_text = ""
    if prompts and prompts.is_file():
        for _l in prompts.read_text(encoding="utf-8", errors="replace").splitlines():
            if _l.strip():
                try:
                    prompt_text += " " + str(json.loads(_l).get("prompt", ""))
                except Exception:                                   # noqa: BLE001
                    prompt_text += " " + _l
    in_products_p = {t for t in only_p if t in prod_text}
    in_products_n = {t for t in only_n if t in prod_text}
    in_prompt_p = {t for t in only_p if t in prompt_text}
    in_prompt_n = {t for t in only_n if t in prompt_text}

    hit_p = sorted({t for t in only_p if t in cand_text}
                   - common_sense_p - in_products_p - in_prompt_p)
    hit_n = sorted({t for t in only_n if t in cand_text}
                   - common_sense_n - in_products_n - in_prompt_n)

    return {
        "holdout 份数": len(hold_paths), "train 份数": len(train_paths),
        "holdout 独有专名": len(only_p), "holdout 独有数字": len(only_n),
        "被基线也命中而剔除的": len(common_sense_p) + len(common_sense_n),
        "★ 因产物里本来就有而剔除的": len(in_products_p) + len(in_products_n),
        "★★ 因题面里本来就有而剔除的": len(in_prompt_p) + len(in_prompt_n),
        "有没有题面": bool(prompt_text),
        "候选命中专名": hit_p, "候选命中数字": hit_n,
        "有没有负对照": bool(base),
    }


def self_test() -> int:
    import tempfile
    bad = []

    def chk(name, got, want):
        if got != want:
            bad.append(f"{name}: 得到 {got!r}，应为 {want!r}")

    with tempfile.TemporaryDirectory() as td:
        ws = pathlib.Path(td)
        (ws / "raw").mkdir()
        (ws / "hold").mkdir()
        (ws / "evidence").mkdir()
        (ws / "raw" / "train1.txt").write_text(
            "Bethlehem Steel Company in 1902 with the bonus system and the instruction card",
            encoding="utf-8")
        (ws / "hold" / "h1.txt").write_text(
            "Remington Typewriter Company in 1904 discussed the Sayles method on page 1877",
            encoding="utf-8")
        (ws / "evidence" / "source-ledger.jsonl").write_text("\n".join(json.dumps(r) for r in [
            {"source_id": "src-t", "local_path": "raw/train1.txt", "split": "train"},
            {"source_id": "src-h", "local_path": "hold/h1.txt", "split": "holdout"},
        ]), encoding="utf-8")
        cand = ws / "cand.json"
        base = ws / "base.json"

        # 正例：候选只说 train 里的东西 → 不报
        cand.write_text(json.dumps({"q1": "我在 Bethlehem Steel Company 用的是奖金制。"},
                                   ensure_ascii=False), encoding="utf-8")
        base.write_text(json.dumps({"q1": "我谈的是奖金制。"}, ensure_ascii=False), encoding="utf-8")
        r = scan(ws, cand, base)
        chk("正例：不报专名", r["候选命中专名"], [])
        chk("正例：不报数字", r["候选命中数字"], [])

        # 反例①：候选说出了只在 holdout 里的专名与数字
        cand.write_text(json.dumps({"q1": "那件事我在 Sayles 那篇里讲过，见第 1877 页。"},
                                   ensure_ascii=False), encoding="utf-8")
        r = scan(ws, cand, base)
        chk("反例①：抓到专名", r["候选命中专名"], ["Sayles"])
        chk("反例①：抓到数字", r["候选命中数字"], ["1877"])

        # ★★ 反例②：**负对照必须能剔掉常识词**——基线也说得出来的不算泄漏
        base.write_text(json.dumps({"q1": "Sayles 这个说法我知道，1877 也是常识。"},
                                   ensure_ascii=False), encoding="utf-8")
        r = scan(ws, cand, base)
        chk("反例②：负对照剔掉专名", r["候选命中专名"], [])
        chk("反例②：负对照剔掉数字", r["候选命中数字"], [])
        chk("反例②：剔除数要打印", r["被基线也命中而剔除的"], 2)

        # 反例③：没有负对照时要说出来，不许静默当成有
        r = scan(ws, cand, None)
        chk("反例③：无负对照要标明", r["有没有负对照"], False)

        # 反例④：train 里也有的词，即使 holdout 里有，也不算独有
        chk("反例④：train 共有词不进名单",
            "Bethlehem Steel Company" in str(scan(ws, cand, base)["候选命中专名"]), False)

    print("正例：候选只说 train 的东西 → 不报\n"
          "反例①：候选说出 holdout 独有的专名与数字 → 抓到\n"
          "反例②：**基线也说得出来的一律剔掉**（负对照），且剔除数要打印\n"
          "反例③：没有负对照时必须标明，不许静默当成有\n"
          "反例④：train 里也有的词不算 holdout 独有")
    for b in bad:
        print("  ✗", b)
    print(("  ✗ 自测 %d 条不过" % len(bad)) if bad else "  ✓ 自测全过（正例 2、反例 6）")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--workspace", type=pathlib.Path)
    ap.add_argument("--candidate", type=pathlib.Path)
    ap.add_argument("--baseline", type=pathlib.Path)
    ap.add_argument("--prompts", type=pathlib.Path,
                    help="题面 JSONL（{case_id,prompt}）。★ **不给它，known 题会 100% 误报**"
                         "——每道 known 题都必然点名 holdout 那部作品。")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not (a.workspace and a.candidate):
        ap.error("要给 --workspace 与 --candidate")
    r = scan(a.workspace, a.candidate, a.baseline, a.prompts)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=1))
    else:
        if "状态" in r:
            print(" ", r["状态"])
            return 0
        print("holdout %d 份 / train %d 份；holdout 独有专名 %d、数字 %d；"
              "被基线也命中而剔除 %d"
              % (r["holdout 份数"], r["train 份数"], r["holdout 独有专名"],
                 r["holdout 独有数字"], r["被基线也命中而剔除的"]))
        if not r["有没有负对照"]:
            print("  ★ **没有基线答案做负对照**——本次结论的强度低一档")
        print("  ★ 因产物里本来就有而剔除 %d；因题面里本来就有而剔除 %d%s"
              % (r.get("★ 因产物里本来就有而剔除的", 0),
                 r.get("★★ 因题面里本来就有而剔除的", 0),
                 "" if r.get("有没有题面") else "（**没给 --prompts，known 题会误报**）"))
        if r["候选命中专名"] or r["候选命中数字"]:
            print("  ✗ **候选答案里出现了只可能来自 holdout 的东西**：")
            print("      专名", r["候选命中专名"][:20])
            print("      数字", r["候选命中数字"][:20])
        else:
            print("  ✓ 候选答案里没有 holdout 独有的专名或数字")
            print("  ★ 但**这不等于没读过**：转述而不带专名与数字的泄漏本件抓不到，"
                  "中文译名也穿得过去。")
    return 1 if (r.get("候选命中专名") or r.get("候选命中数字")) else 0


if __name__ == "__main__":
    sys.exit(main())
