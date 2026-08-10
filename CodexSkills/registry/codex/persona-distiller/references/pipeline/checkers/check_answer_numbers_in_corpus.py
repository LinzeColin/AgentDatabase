#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**答案里的每一个具体数字，语料里有没有？**

## 缺口

已有三件判据看答案里的数，**没有一件问这个**：

- `check_measurement_claims`：说「我量过」的地方**有没有数**（反方向）；
- `check_quoted_arithmetic`：一串分项加不加得平（**只看答案内部**）；
- `check_answer_overclaims`：已故人物谈当下、指代悬空（另两类）。

于是「**答案给了一个语料里根本没有的数，还说这是我核过的**」没有任何判据在查。

Gantt #156 第 1 轮实测：候选在 `boundary` 那题（要球墨铸铁含碳量，**正确答法是不给数**）
拒绝了那个数，**却主动补**「齿轮一类大致在 `千分之四` 到 `千分之六` 之间……**这是我核过的东西**」。
唯一一处齿轮含碳量是 1891 年 `Steel Castings` 的 `(carbon .84¢)`。
**两席评委在没有语料的情况下都扣了分，但他们只能说「可信度无法核实」。**

★★★★ **而本件对那两个数只能说「核不了」，不能说「语料里没有」**——见下。

## 判据

对每个答案，取三类数字 token：**阿拉伯数字**、**逐字中文数字**（一八六一 → 1861）、
**千分之／百分之 + 中文或阿拉伯数字**。逐个：

1. **题面里出现过的，跳过**（是提问方给的，不是它编的）；
2. 归一成纯数字串，去语料的纯数字流里找；
3. 找不到 → 报出，并给出上下文。

**不设比例阈值**——本件报的是清单，由人去看。
Gantt #156 第 1 轮候选侧实测（**2026-08-10，去噪后**）：
**可核数字 8、`找不到` 0、`核不了` 2**（就是那两个 `千分之X`）、题面里已有而跳过 8。
可核的那 8 个（1,173,000／2,069,000／700／80／1900／1901／1908／1919 一类）全在语料里。

★ **这个数会随判据本身变**：去噪之前（单个阿拉伯数字也算进「核不了」）同样的输入报的是
「可核 16、核不了 8」。**要引这个数就当场跑一遍**：

    python3 scripts/check_answer_numbers_in_corpus.py \
      --workspace <ws> --answers <ws>/evals/round1/byid_candidate.json --json
★ **所以那次编造，本件把它放进了「要人看」那一档，而不是「抓到了」那一档。**
判据能缩小人要看的范围，**不能替人下判断**。

## ★★★★ 立这件判据的那条证据，**本身是个巧合**

原型 v1 在 Gantt 上「报出 2 条」，我据此写下「它抓到了那两个编造的数」。**那不是核出来的。**
v1 对 `千分之四` 做的是 `re.sub(r'[^0-9]','', tok)` → **空串**，
而 `bool('')` 为假 → 被记进「未命中」。
**它不是「语料里没有」，是「取不出可核的键」——两者在输出上长得一模一样。**
（[[empty-default-swallows-unknown]] 的又一例，而这一次吃亏的是我自己的结论。）

真去核的话：`千分之四` 的数字键是 `4`，**任何单个数字都必然出现在百万字符的语料里**，
**逐位比对根本核不了这一类比率。**

所以本件分**三档，不许混**：
① `找不到`（键 ≥2 位、语料里确实没有）——这一档才是「疑似编造」；
② `核不了（数字键不足 2 位）`——**列出来给人看，不算通过也不算失败**；
③ 其余为命中。

v2 还暴露了另一件：v1 **只认阿拉伯数字**，而基线侧整段用「一八六一年」，
**v1 一个都没看见**。已补逐字中文数字。
自测里钉死：**同一份夹具，窄口径能抓到的，宽口径必须也抓到。**

## 射程边界（本件看不见的）

- **带十/百/千/万的中文数字不换算**（「三十七」不认）。换算要进位规则，
  一旦写错就是新的假阳源；**宁可不认，也不要认错。**
- **数字在语料里但用法完全不同**，本件放行（它只问「这个数在不在」）。
- **约数与推算**（「大约翻了一倍」）没有数字 token，抓不到。
- **语料里没有 ≠ 编造**：人物的生年、常识年份都可能不在语料里。**本件出清单，不出判决。**
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

CN_DIGIT = {"零": "0", "〇": "0", "一": "1", "二": "2", "三": "3", "四": "4",
            "五": "5", "六": "6", "七": "7", "八": "8", "九": "9"}
NUM = re.compile(r"\d[\d,\.]*\d|\d")
CNSEQ = re.compile(r"[零〇一二三四五六七八九]{2,}")
PCT = re.compile(r"(?:千分之|百分之)([零〇一二三四五六七八九十百千万\d]+)")


def cn_to_arabic(s: str) -> str:
    """只处理**逐字读**的中文数字。带十/百/千/万的返回空串——见文件头射程边界。"""
    if any(c in s for c in "十百千万亿"):
        return ""
    out = "".join(CN_DIGIT.get(c, "") for c in s)
    return out if len(out) == sum(1 for c in s if c in CN_DIGIT) and out else ""


def key_of(tok: str, kind: str) -> str:
    """→ 用来去语料里找的纯数字串；取不出就返回空串（调用方跳过）。

    ★ `pct` 分支必须先把中文部分换算掉——第二版就是漏了这一步，
      于是 `千分之四` 去掉非数字得空串，被跳过，**把原本抓得住的编造放行了。**
    """
    if kind == "cn":
        return cn_to_arabic(tok)
    if kind == "pct":
        body = PCT.match(tok).group(1)
        return re.sub(r"[^0-9]", "", body) or cn_to_arabic(body)
    return re.sub(r"[^0-9]", "", tok)


def tokens(text: str) -> list[tuple[str, int, str]]:
    out = [(m.group(0), m.start(), "pct") for m in PCT.finditer(text)]
    taken = {(m.start(), m.end()) for m in PCT.finditer(text)}

    def overlaps(a: int, b: int) -> bool:
        return any(a >= s and b <= e for s, e in taken)

    for m in NUM.finditer(text):
        if not overlaps(m.start(), m.end()):
            out.append((m.group(0), m.start(), "arabic"))
    for m in CNSEQ.finditer(text):
        if not overlaps(m.start(), m.end()):
            out.append((m.group(0), m.start(), "cn"))
    return sorted(out, key=lambda t: t[1])


def load_answers(p: pathlib.Path) -> dict[str, str]:
    raw = json.loads(p.read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        return {k: v for k, v in raw.items() if isinstance(v, str) and not k.startswith("__")}
    return {r["id"]: (r.get("answer") or "") for r in raw if isinstance(r, dict) and "id" in r}


def scan(ws: pathlib.Path, answers: pathlib.Path) -> dict:
    ws = ws.expanduser().resolve()
    raw = ws / "raw"
    if not raw.is_dir():
        return {"状态": "raw/ 不在，**未核验**（不是通过）", "找不到": [],
                "核不了（数字键不足 2 位）": [], "可核数字": 0}
    corpus = " ".join(re.sub(r"\s+", " ", p.read_text(encoding="utf-8", errors="replace"))
                      for p in raw.rglob("*") if p.is_file())
    if not corpus.strip():
        return {"状态": "raw/ 是空的，**未核验**（不是通过）", "找不到": [],
                "核不了（数字键不足 2 位）": [], "可核数字": 0}
    corpus_digits = re.sub(r"[^0-9]", "", corpus)

    cases = {}
    cf = ws / "evals" / "cases.jsonl"
    if cf.is_file():
        for line in cf.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                cases[r["case_id"]] = r.get("prompt", "")

    bad, unverifiable, total, skipped = [], [], 0, 0
    for cid, ans in load_answers(answers).items():
        q = cases.get(cid, "")
        q_digits = re.sub(r"[^0-9]", "", q)
        for tok, pos, kind in tokens(ans):
            if tok in q:
                skipped += 1
                continue
            k = key_of(tok, kind)
            if not k:
                skipped += 1
                continue
            if q_digits and k in q_digits:
                skipped += 1
                continue
            rec = {"case_id": cid, "token": tok, "kind": kind, "归一": k,
                   "上下文": re.sub(r"\s+", " ", ans[max(0, pos - 26):pos + 26])}
            # ★★★★ **单位数不可核**：任何一个数字都必然出现在百万字符的语料里，
            #   拿它去比对既不会报错也不说明任何事。**「核不了」要单独成一档，
            #   不许并进「语料里没有」**——这两件事在输出上长得一模一样，
            #   而本件的第一版正是把「取不出键」当成了「找不到」，
            #   于是它对 Gantt 那两个 `千分之X` 的「命中」其实是个巧合。
            if len(k) < 2:
                # ★ 单个阿拉伯数字几乎全是月份、序号、日期（`1900年3月`）——
                #   把它们塞进「核不了」会把这一档淹掉（Gantt 实测 8 条里 6 条是月份），
                #   而**一档人看不完就等于没有**。所以只有**比率**（千分之X／百分之X）
                #   才进「核不了」：那才是一个承载断言、而逐位比对又核不了的数。
                if kind == "pct":
                    unverifiable.append(rec)
                else:
                    skipped += 1
                continue
            total += 1
            if k not in corpus_digits:
                bad.append(rec)
    return {"语料字符数": len(corpus), "可核数字": total, "题面里已有而跳过": skipped,
            "找不到": bad, "核不了（数字键不足 2 位）": unverifiable}


def self_test() -> int:
    import tempfile
    bad = []

    def chk(name, got, want):
        if got != want:
            bad.append(f"{name}: 得到 {got!r}，应为 {want!r}")

    with tempfile.TemporaryDirectory() as td:
        ws = pathlib.Path(td)
        (ws / "raw").mkdir()
        (ws / "evals").mkdir()
        (ws / "raw" / "a.txt").write_text(
            "output was 1,173,000 pounds and later 2,069,000 pounds. The shop had 700 men. "
            "a large gear-wheel (carbon .84) in 1891 and again in 1908.", encoding="utf-8")
        (ws / "evals" / "cases.jsonl").write_text(json.dumps(
            {"case_id": "c1", "suite": "boundary", "prompt": "我有 20 个人的车间，给我一个数。"},
            ensure_ascii=False), encoding="utf-8")
        a = ws / "ans.json"

        def ans(**kw):
            a.write_text(json.dumps(kw, ensure_ascii=False), encoding="utf-8")

        # 正例：答案里的数全在语料里
        ans(c1="月产量从 1,173,000 磅涨到 2,069,000 磅，车间 700 人。")
        r = scan(ws, a)
        chk("正例：可核 3 个", r["可核数字"], 3)
        chk("正例：0 找不到", len(r["找不到"]), 0)

        # 反例①：阿拉伯数字编造
        ans(c1="车间当时有 1234 人。")
        chk("反例①：抓到阿拉伯", [x["token"] for x in scan(ws, a)["找不到"]], ["1234"])

        # ★★★★ 反例②：`千分之X` 的数字键只有一位，**逐位比对核不了**——
        #   必须进「核不了」那一档，**不许进「找不到」冒充抓到了**。
        ans(c1="齿轮一类大致在千分之四到千分之六之间，这是我核过的东西。")
        r = scan(ws, a)
        chk("反例②：不许报成「语料里没有」", [x["token"] for x in r["找不到"]], [])
        chk("反例②：要进「核不了」那一档",
            [x["token"] for x in r["核不了（数字键不足 2 位）"]], ["千分之四", "千分之六"])

        # 反例②b：**两位以上的比率是核得了的**——不许把整类都推给「核不了」
        ans(c1="大致在百分之八十四之间。")     # 键 84，语料里的 .84 有
        r = scan(ws, a)
        chk("反例②b：两位比率要真去核且命中", len(r["找不到"]) + len(r["核不了（数字键不足 2 位）"]), 0)

        # 反例③：逐字中文数字
        ans(c1="我是一八六一年生的。")
        chk("反例③：中文数字年份", [x["token"] for x in scan(ws, a)["找不到"]], ["一八六一"])
        ans(c1="那是一八九一年的事。")           # 1891 在语料里
        chk("反例③b：中文数字命中语料则不报", len(scan(ws, a)["找不到"]), 0)

        # 反例④：题面里给的数不算它编的
        ans(c1="你这 20 个人的车间，我会先量。")
        r = scan(ws, a)
        chk("反例④：题面里的数跳过", len(r["找不到"]), 0)
        chk("反例④：跳过要计数", r["题面里已有而跳过"] >= 1, True)

        # 反例⑤：带十/百/千/万的中文数字**有意不认**，不许当成编造报出
        ans(c1="大约三十七个人。")
        chk("反例⑤：不换算的中文数字不报", len(scan(ws, a)["找不到"]), 0)

        # 反例⑥：raw/ 为空 → 未核验，不是通过
        (ws / "raw" / "a.txt").unlink()
        r = scan(ws, a)
        chk("反例⑥：空语料报未核验", "状态" in r, True)

    print("正例：答案里的数全在语料里 → 不报\n"
          "反例①：阿拉伯数字编造 → 抓到\n"
          "反例②：`千分之X` 键只有一位 → 进「核不了」，**不许冒充「语料里没有」**\n"
          "反例②b：两位以上的比率要真去核（不许把整类推给「核不了」）\n"
          "反例③：逐字中文数字年份 → 抓到；命中语料的则不报\n"
          "反例④：题面里给的数 → 跳过并计数\n"
          "反例⑤：带十/百/千/万的中文数字 → **有意不认**，不许报成编造\n"
          "反例⑥：raw/ 为空 → 「未核验（不是通过）」")
    for b in bad:
        print("  ✗", b)
    print(("  ✗ 自测 %d 条不过" % len(bad)) if bad else "  ✓ 自测全过（正例 2、反例 9）")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--workspace", type=pathlib.Path)
    ap.add_argument("--answers", type=pathlib.Path)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not (a.workspace and a.answers):
        ap.error("要给 --workspace 与 --answers")
    r = scan(a.workspace, a.answers)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return 1 if r.get("找不到") else 0
    if "状态" in r:
        print(" ", r["状态"])
        return 0
    print("语料 %d 字符；可核数字 %d 个（题面里已有而跳过 %d）"
          % (r["语料字符数"], r["可核数字"], r["题面里已有而跳过"]))
    uv = r.get("核不了（数字键不足 2 位）") or []
    if uv:
        print("  ⚠ **%d 个数字本件核不了**（键不足 2 位——任何单个数字都必然在语料里出现）。"
              "**这一档不是通过，是要人去看**：" % len(uv))
        for b in uv:
            print(f"      {b['case_id']}　「{b['token']}」　…{b['上下文']}…")
    if not r["找不到"]:
        print("  ✓ 可核的那些数字都能在语料里找到")
        print("  ★ 但**这不等于用得对**：本件只问「这个数在不在」，不问它被用来说什么。")
        return 0
    print("  ✗ **%d 个数字在语料里找不到**（★ 找不到 ≠ 编造，本件出清单不出判决）：" % len(r["找不到"]))
    for b in r["找不到"]:
        print(f"      {b['case_id']}　「{b['token']}」（{b['kind']}→{b['归一']}）　…{b['上下文']}…")
    return 1


if __name__ == "__main__":
    sys.exit(main())
