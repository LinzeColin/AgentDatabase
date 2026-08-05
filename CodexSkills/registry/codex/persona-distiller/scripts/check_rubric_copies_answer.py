#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**rubric 里预先写好了答案的原字符串**——那时评委量的是字符串对齐，不是能力。

## 它是 RUNBOOK 第五十四种的判据（此前一直停在散文态）

第五十四种「rubric 是照着答案倒写的」记于 Robertson #97：
两席评委各自独立指出 rubric 多处规定了答案的措辞，而 candidate 每次精确命中同一措辞——
「**这套评测检验的是同一语料库的召回，不是推理质量**」。

**记了，但没落成判据。于是它又回来了两次：**

| 人物 | 拿着 rubric 打出的 delta | 评委自己说的话 |
|---|---|---|
| Carver #127（**已入库**） | +0.3791（16/16） | —— |
| Thomson #129 | +0.4516（16/16 三轮不变） | 席 D：「rubric 把原字符串、卷次、连 `are`/`1`/`meth- ods` 三处 OCR 讹字都预先写了出来……**我无法区分某一侧是真检索到的，还是照着 rubric 复述的**」 |

同一批答案换成**无 rubric** 再判：Thomson **−0.0859**、Carver **−0.2019**。
**摆动 0.6038 / 0.5810。**

## 它量什么

对每道题，找 **rubric 与候选答案共有的长字符串**（默认 ≥24 字符，跳过纯空白与标点）。
共有的越长、越多，这道题的分就越是在量「字符串对不对得上」。

## ★ 它不判对错，只报形状

- **`fact-preservation` 那类本来就要求逐字复现**——那里出现共有长串是**设计使然**。
  但**含义不变**：那道题的分**仍然只证明字符串对齐**。本件照报，并在输出里注明。
- **不拦。** 要不要改 rubric 取决于人物与用例，判据不替人做主。
"""
import argparse
import json
import pathlib
import re
import sys

MIN_RUN = 24                      # 共有子串的最短「权重」，不是字符数
# ★★ 中日韩字符按 2 计权：`上碳硬则弧脚有稳的落点，下碳软则烧损跟得上` 只有 21 个字符，
#   却比 21 个拉丁字符（约三个英文单词）承载多得多。
#   自测反向对照③当场抓到：**按字符数算，这条中文抄袭被漏掉了。**
_CJK = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]")


def weight(s: str) -> int:
    return len(s) + len(_CJK.findall(s))
SOURCING_SUITES = ("fact-preservation", "token-efficiency", "anonymous-fidelity")
_WS = re.compile(r"\s+")


def _norm(s: str) -> str:
    return _WS.sub(" ", str(s)).strip()


def _suite(case_id: str) -> str:
    s = re.sub(r"^[a-z]{2,4}-", "", str(case_id))
    return re.sub(r"-\d+$", "", s)


def shared_runs(a: str, b: str, min_run: int = MIN_RUN) -> list:
    """→ a 与 b 共有的、长度 ≥ min_run 的子串（去重、只留最长的那些）。

    ★ 用逐字符的动态规划会在几万字上很慢；这里走「**以 a 的每个位置起，
      用 b 的集合做最长匹配**」的朴素法，但**先用 min_run 长度的窗口做哈希筛**，
      整体线性偏上，够用。**不写两侧可变长的正则**（第六十八种、第七十三种的教训）。
    """
    a, b = _norm(a), _norm(b)
    # 种子窗口按**字符**取，长度取「能凑够 min_run 权重」的最小值：
    #   纯 CJK 时 12 字即可，纯拉丁时要 24 字。
    win = max(6, min_run // 2 if _CJK.search(b) else min_run)
    if len(a) < win or len(b) < win:
        return []
    seeds = {b[i:i + win] for i in range(len(b) - win + 1)}
    out, i = [], 0
    while i <= len(a) - win:
        w = a[i:i + win]
        if w not in seeds:
            i += 1
            continue
        # 命中种子后往右尽量延长
        j = i + win
        while j < len(a) and a[i:j + 1] in b:
            j += 1
        seg = a[i:j]
        if weight(seg.strip(" ，。、；：,.;:()（）「」\"'")) >= min_run:
            out.append(seg)
        i = j - win + 1 if j - win + 1 > i else i + 1
    # 去掉被别的段包住的
    out.sort(key=len, reverse=True)
    kept = []
    for s in out:
        if not any(s in k for k in kept):
            kept.append(s)
    return kept


def check(rubrics: dict, answers: dict, min_run: int = MIN_RUN) -> dict:
    per, total_chars = {}, 0
    for cid, ru in sorted(rubrics.items()):
        ans = answers.get(cid)
        if not ans or not ru:
            continue
        runs = shared_runs(ru, ans, min_run)
        if runs:
            n = sum(len(x) for x in runs)
            total_chars += n
            per[cid] = {
                "共有长串数": len(runs),
                "共有字符数": n,
                "占答案的比例": round(n / max(len(_norm(ans)), 1), 3),
                "最长的三段": [x[:110] for x in runs[:3]],
                "套组": _suite(cid),
                "★": ("**问出处的套组，共有长串是设计使然**——"
                      "但那道题的分**仍然只证明字符串对齐**。"
                      if _suite(cid) in SOURCING_SUITES else ""),
            }
    n_case = len(rubrics)
    out = {
        "题数": n_case,
        "**rubric 抄了答案原文的题**": len(per),
        "占比": f"{len(per) / max(n_case,1):.0%}",
        "共有字符合计": total_chars,
        "逐题": per,
        "★ 口径": ("**只报不拦。** 共有长串越多，这道题的分越是在量「字符串对不对得上」"
                   "而不是能力。要不要改 rubric 取决于人物与用例。"),
        "★★ 参照": ("Thomson #129 与 Carver #127 都被评委当场指出过这件事；"
                     "同一批答案换成无 rubric 再判，delta 分别掉到 −0.0859 与 −0.2019，"
                     "**摆动 0.6038 / 0.5810**。"),
    }
    return out


def self_test() -> int:
    ok = True

    def chk(m, c):
        nonlocal ok
        ok = ok and bool(c)
        print(("  ✓ " if c else "  ✗ ") + m)

    print("── ★★★ 正向：Thomson #129 的真实形态（rubric 把引文原串写进去了）──")
    ru = ("**评分标准**：须引出「On my own account, having had considerable」"
          "并说明 `are` 是 `arc` 的 OCR 讹字；须给坐标 vol. vii (1890)。")
    an = ("原话是：「On my own account, having had considerable」，"
          "`are` 是 `arc` 的 OCR 讹字，我照原样引。出处：vol. vii（1890）。")
    r = check({"et-fact-preservation-01": ru}, {"et-fact-preservation-01": an})
    chk(f"抓到 1 题：{r['**rubric 抄了答案原文的题**']}", r["**rubric 抄了答案原文的题**"] == 1)
    d = r["逐题"]["et-fact-preservation-01"]
    chk(f"共有串含那句引文：{d['最长的三段'][0][:40]}",
        "On my own account" in " ".join(d["最长的三段"]))
    chk(f"标出这是问出处的套组：{bool(d['★'])}", bool(d["★"]))

    print("\n── ★★★ 反向对照①：**rubric 只描述要求、不写答案原串 → 不许报** ──")
    ru2 = "**评分标准**：须指出这段话出自哪一年的哪一场讨论，并说明如何处理 OCR 讹字。"
    an2 = ("原话是：「On my own account, having had considerable」，"
           "出自 1890 年 AIEE 讨论 Marks 那篇碳棒论文。")
    r = check({"et-fact-preservation-01": ru2}, {"et-fact-preservation-01": an2})
    chk(f"没报：{r['**rubric 抄了答案原文的题**']}", r["**rubric 抄了答案原文的题**"] == 0)

    print("\n── ★★ 反向对照②：**短的共用词组不算**（否则「评分标准」四个字就报） ──")
    r = check({"x-voice-01": "评分标准：须给出可照做的步骤。"},
              {"x-voice-01": "评分标准这三个字在答案里也出现，但它不构成抄袭。须给出可照做的步骤。"})
    chk(f"短语不报：{r['**rubric 抄了答案原文的题**']}", r["**rubric 抄了答案原文的题**"] == 0)

    print("\n── ★★ 反向对照③：非出处套组抄了原串，**不给豁免标记** ──")
    ru3 = "**评分标准**：须答「下软上硬」并说明上碳硬则弧脚有稳的落点，下碳软则烧损跟得上。"
    an3 = "两条路。一条在碳棒上：下软上硬。上碳硬则弧脚有稳的落点，下碳软则烧损跟得上。"
    r = check({"et-voice-01": ru3}, {"et-voice-01": an3})
    chk(f"抓到：{r['**rubric 抄了答案原文的题**']}", r["**rubric 抄了答案原文的题**"] == 1)
    chk("不给出处豁免标记", not r["逐题"]["et-voice-01"]["★"])

    print("\n── ★ 反向对照④：答案缺失时不许报（**没有答案就不是抄**） ──")
    r = check({"a-1": "x" * 60}, {})
    chk(f"没报：{r['**rubric 抄了答案原文的题**']}", r["**rubric 抄了答案原文的题**"] == 0)

    print("\n" + ("✓ 自测全过" if ok else "✗ 自测未过"))
    return 0 if ok else 2


def _load(path: str, want_rubric: bool) -> dict:
    d = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    if isinstance(d, list):
        key = "rubric" if want_rubric else ("candidate" if any("candidate" in x for x in d) else "A")
        return {x.get("case_id", str(i)): (x.get(key) or "") for i, x in enumerate(d)}
    return {k: (v.get("rubric") if want_rubric and isinstance(v, dict) else
                v if isinstance(v, str) else (v.get("candidate") or "")) or ""
            for k, v in d.items()}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rubrics", help="case_id → rubric 的 JSON，或 dispatch_*.json")
    ap.add_argument("--answers", help="case_id → 候选答案的 JSON")
    ap.add_argument("--min-run", type=int, default=MIN_RUN)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not (a.rubrics and a.answers):
        ap.error("要么 --self-test，要么同时给 --rubrics 与 --answers")
    r = check(_load(a.rubrics, True), _load(a.answers, False), a.min_run)
    print(json.dumps(r, ensure_ascii=False, indent=2))
    return 0                       # **只报不拦**


if __name__ == "__main__":
    sys.exit(main())
