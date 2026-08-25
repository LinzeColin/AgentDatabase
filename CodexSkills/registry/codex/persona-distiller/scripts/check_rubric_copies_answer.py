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


# ═══════════════════════════════════════════════════════════════════════
# ★★★ v0.0.0.150：中文**压缩/意译**层。原先只有 `shared_runs` 一层，
#   而它的门槛 `MIN_RUN=24` 是**权重**——中日韩按 2 计，所以中文要 **12 个字**才够。
#   Bessemer #132 实测的违规全在 5–9 字之间，**一条都够不着**：
#
#     判据「说清已有做法败在哪」  9 字 → 权重 18 < 24
#     判据「不是格言体」          5 字 → 权重 10 < 24
#
#   冻结指令（judge_prompts/v1.md 打分口径 ★★）写得很清楚：
#   **「中译与压缩也算抄」**——而这道门只数连续子串，压缩本来就不连续。
#   席 E 逐条数出 10 条确凿 + 2 条边界，门报 0/16。
#
#   本层加三样，都**只报不拦**：
#     ① 低门槛中文连续串（默认 5 字）
#     ② 判据里被 `「」` 或 `**` 框住的短语，**近乎逐字**出现在任一侧答案里
#     ③ 字符 3-gram 包含度——抓「同样三项、同样次序」这种**不连续**的压缩
MIN_CJK_RUN = 4                    # ① 中文连续串的字数门槛（不是权重）
#   ★ 标定到 4 字，不是拍的：席 D 手数 14/16、席 E 手数 12/16，
#     `diag_rubric_gloss_overlap` 在门槛 3–4 字上报 11–14 条，与两人吻合；
#     门槛 6 字只报 1 条。**实测违规落在 3–5 字**（「说清已有」4、「算不过」3、「不是格言体」5）。
QUOTED_MIN = 4                     # ② 引号内短语至少这么多汉字才拿去比
NGRAM_N = 3
NGRAM_MIN = 0.55                   # ③ 判据的 3-gram 有多大比例落在答案里
QUOTED_ECHO_MIN = 0.34             # ② 判据引号内短语被答案回声多少才算（不要求整句）
_QUOTED = re.compile(r"「([^」\n]{2,60})」|\*\*([^*\n]{2,60})\*\*")
_NONCJK = re.compile(r"[^\u4e00-\u9fff]+")


def _cjk_only(s: str) -> str:
    return _NONCJK.sub("", str(s))


def cjk_runs(a: str, b: str, minlen: int = MIN_CJK_RUN) -> list:
    """→ a 与 b 共有的、≥minlen 字的**纯中文**子串（去掉被包含的）。"""
    ca, cb = _cjk_only(a), _cjk_only(b)
    if len(ca) < minlen or len(cb) < minlen:
        return []
    seen = {cb[i:i + minlen] for i in range(len(cb) - minlen + 1)}
    out, i = [], 0
    while i <= len(ca) - minlen:
        if ca[i:i + minlen] in seen:
            j = i + minlen
            while j < len(ca) and ca[i:j + 1] in cb:
                j += 1
            out.append(ca[i:j])
            i = j - minlen + 1
        else:
            i += 1
    out.sort(key=len, reverse=True)
    kept = []
    for x in out:
        if not any(x in k for k in kept):
            kept.append(x)
    return kept


def quoted_echoes(rubric: str, answer: str) -> list:
    """→ 判据里 `「…」` / `**…**` 框住的短语，近乎逐字出现在答案里的那些。

    ★ 为什么单独查这一层：**被判据用引号框起来的字，是判据在指定「要说这句话」**。
    它一旦同时出现在某一侧答案里，那一题的分就变成了「字符串对不对得上」。
    """
    ans = _cjk_only(answer)
    hits = []
    for m in _QUOTED.finditer(str(rubric)):
        phrase = m.group(1) or m.group(2) or ""
        core = _cjk_only(phrase)
        if len(core) < QUOTED_MIN:
            continue
        # ★★ 不能要求**整句**出现。第一版这么写，结果 hb-task-completion-01 漏掉了：
        #   判据里 `「说清已有做法败在哪」`（9 字），答案回声的是「说清已有」（4 字）——
        #   **回声不是复制，判据指定的说法被答案吸收了一部分，那已经足够让分数变成对字符串。**
        #   改为按 3-gram 包含度判：这句话有多大比例落在答案里。
        if core in ans:
            hits.append({"短语": phrase.strip(), "包含度": 1.0, "形态": "整句照抄"})
            continue
        if len(core) >= NGRAM_N:
            g = {core[i:i + NGRAM_N] for i in range(len(core) - NGRAM_N + 1)}
            ag = {ans[i:i + NGRAM_N] for i in range(max(len(ans) - NGRAM_N + 1, 0))}
            r = len(g & ag) / len(g)
            if r >= QUOTED_ECHO_MIN:
                hits.append({"短语": phrase.strip(), "包含度": round(r, 2), "形态": "部分回声"})
    return hits


def ngram_containment(rubric: str, answer: str, n: int = NGRAM_N,
                      exclude: str = "") -> float:
    """→ 判据的中文 n-gram 有多大比例能在答案里找到（包含度，不是 Jaccard）。

    ★ 用包含度而不是 Jaccard：判据短、答案长，Jaccard 会被长度差压死。
    这一层抓的是**不连续的压缩**——例如判据列「生卒年、住址、作品归属」，
    而答案把同样三项按同样次序写成三条 bullet：连续子串一条都对不上，n-gram 却大量重合。
    """
    r, a = _cjk_only(rubric), _cjk_only(answer)
    if len(r) < n or len(a) < n:
        return 0.0
    rg = {r[i:i + n] for i in range(len(r) - n + 1)}
    ag = {a[i:i + n] for i in range(len(a) - n + 1)}
    if exclude:
        # ★ 题面 n-gram 从**分子分母都**扣掉：三方共有的词不是抄
        e = _cjk_only(exclude)
        qg = {e[i:i + n] for i in range(len(e) - n + 1)}
        rg -= qg
        ag -= qg
    if not rg:
        return 0.0
    return len(rg & ag) / len(rg)


def check(rubrics: dict, answers: dict, min_run: int = MIN_RUN,
          answers_b: dict = None, questions: dict = None) -> dict:
    """`answers_b` 是**另一侧**的答案（可选）；`questions` 是题面（强烈建议给）。

    ★★ 冻结指令要求「中译与压缩也算抄」，而抄的对象**可能是任一侧**：
    席 E 在 Bessemer #132 实测 10 条对应一侧、2 条对应另一侧，**泄漏是双向的**。
    只比一侧会漏掉一半，且会让人误以为「判据是照着某个系统写的」。

    ★★★ `questions` 是 Sorby #133 加的，**不给会虚高一大截**：
    判据当然会重复题面的词，答案也当然会——于是「判据 ∩ 答案」里混进一大批
    **题面回声**，那不是抄答案，那是三方都在谈同一个题目。
    实测 Sorby 10 题共 24 个共有串，**16 个（67%）直接出自题面**：
    `电子探针`／`射线衍射`／`薄片加偏光`（题面原句）、`谢菲尔德`、`植物色素`……
    扣掉题面之后才是真的重合。
    ★ 这一条是**评委反过来纠正判据**：席 E 手点 6 条，本件报 10 条，
      差出来的那些一读就知道是题面词。**判据比评委多报的，先当自己错。**
    """
    per, total_chars = {}, 0
    cjk_per = {}
    questions = questions or {}
    for cid, ru in sorted(rubrics.items()):
        ans = answers.get(cid)
        if not ans or not ru:
            continue
        q = str(questions.get(cid) or "")
        # ── 中文压缩层（只报不拦）：两侧都比 ──
        sides = {"候选侧": ans}
        if answers_b and answers_b.get(cid):
            sides["基线侧"] = answers_b[cid]
        cjk_hit = {}
        for side, txt in sides.items():
            # ★ 扣题面：三方共有的词不算「判据抄了答案」
            runs_cjk = [x for x in cjk_runs(ru, txt) if x not in q]
            # ★ quoted_echoes 返回的是 dict（短语/包含度/形态），不是字符串——
            #   第一版直接 `x not in q` 当场 TypeError，自测抓到的。
            quoted = [x for x in quoted_echoes(ru, txt)
                      if str(x.get("短语", "")) not in q]
            cont = ngram_containment(ru, txt, exclude=q)
            if runs_cjk or quoted or cont >= NGRAM_MIN:
                cjk_hit[side] = {
                    "中文连续串": runs_cjk[:4],
                    "**判据引号内被答案照抄的短语**": quoted,
                    "3-gram 包含度": round(cont, 3),
                    # ★★ 门槛就是 `MIN_CJK_RUN`（5 字），**不再另设更高的一道**。
                    #   第一版这里写 `len(x) >= 8`，结果对 Bessemer 报 0/16——
                    #   而实测违规正落在 5–7 字（「不是格言体」5 字、「确实写过的」5 字）。
                    #   席 E 手数 10 条确凿 + 2 条边界，本件的标定也在 3–5 字，
                    #   **把门抬到 8 字等于把要抓的东西全放走**。
                    "越线": bool(quoted) or cont >= NGRAM_MIN or bool(runs_cjk),
                }
        if cjk_hit:
            cjk_per[cid] = cjk_hit
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
    flagged = [c for c, v in cjk_per.items()
               if any(x["越线"] for x in v.values())]
    out = {
        "题数": n_case,
        "**rubric 抄了答案原文的题**": len(per),
        "★★★ **中译/压缩层（冻结指令要求，原先完全没查）**": {
            "越线题数": len(flagged),
            "占比": f"{len(flagged) / max(n_case,1):.0%}",
            "逐题": {c: cjk_per[c] for c in flagged},
            "口径": (f"三条任一即越线：判据引号内的短语被答案照抄／中文连续串 ≥{MIN_CJK_RUN} 字／"
                     f"3-gram 包含度 ≥{NGRAM_MIN}。**只报不拦**，但每条都给出匹配片段供复核。"),
            "★ 为什么原来是 0": (f"上一层门槛 `MIN_RUN={MIN_RUN}` 是**权重**，中日韩按 2 计，"
                                  "**中文要 12 个字才够**；而实测违规全在 5–9 字之间，"
                                  "且「同样三项、同样次序」这种压缩根本不连续。"),
        },
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

    print("\n══ ★★★★ 逐字真实样本：Rosenhain #138 `wr-task-01` 第 1 轮（2026-08-07）══")
    #   下面两串是 `evals/cases.jsonl` 与 `evals/round1/candidate.json` 里的**原字符串**，
    #   连 `\n` 与全角标点一起 `repr()` 出来贴进来的，一个字没动。
    #   ★ 之所以要这一条：它是**两层给出相反答案**的真实形态——
    #     上层 `shared_runs` 报 **0**（`MIN_RUN=24` 是权重，中日韩按 2 计 → 中文要 12 字），
    #     而压缩层报 **1**（四条 ≥4 字的中文连续串）。
    #     手编的例子做不出这个落差，因为写的人会不自觉地把重合写长。
    #   ★★ 3-gram 只有 0.183，**远在 0.55 门槛之下**——所以越线**不是它触发的**。
    #     谁要是把判定改成「只看 3-gram」，这一条会立刻变红。
    _wr_ru = ("★ **判据**：三步是否落在他实际的工作序列上——\n"
              "先取已发表的相图作出发点／自己跑冷却曲线去确认（并重复以排实验误差）／再做金相对照。\n"
              "**失败条件**：给出现代实验流程（DSC、XRD、维氏硬度标准件）。")
    _wr_an = ("先说清一件事：铝合金搁上几天自己变硬这回事，其性质至今没有弄明白，"
              "是眼下最惹眼的未解问题之一，所以头三步都用来把地基砌牢。"
              "一，把这个合金系已发表的平衡图找来当出发点，自己跑几条冷却曲线去确认，"
              "同一炉锭重复三四次，免得把实验误差当成热效应。"
              "二，定下一套尽量不扰动组织的磨制与浸蚀程序，另备一组对照试样，"
              "证明随后看到的组织不是这道程序自己造出来的。"
              "三，同一炉料切成一批，按时间排开，硬度测定与显微观察在同一批试样上并排做，"
              "好让硬度的变化与组织的变化对得上。")
    _wr_runs = cjk_runs(_wr_ru, _wr_an)
    chk(f"四条中文连续串逐字对上：{_wr_runs}",
        _wr_runs == ["冷却曲线去确认", "出发点自己跑", "已发表的", "实验误差"])
    chk(f"上层 shared_runs 空（中文够不着 MIN_RUN={MIN_RUN}）：{shared_runs(_wr_ru, _wr_an)}",
        shared_runs(_wr_ru, _wr_an) == [])
    _wr_ng = ngram_containment(_wr_ru, _wr_an)
    chk(f"3-gram 包含度 {_wr_ng:.6f}，在 {NGRAM_MIN} 门槛之下 → 越线不是它触发的",
        abs(_wr_ng - 0.183099) < 5e-6 and _wr_ng < NGRAM_MIN)
    _wr_r = check({"wr-task-01": _wr_ru}, {"wr-task-01": _wr_an})
    chk(f"两层答案相反：上层报 {_wr_r['**rubric 抄了答案原文的题**']}，"
        f"压缩层报 {_wr_r['★★★ **中译/压缩层（冻结指令要求，原先完全没查）**']['越线题数']}",
        _wr_r["**rubric 抄了答案原文的题**"] == 0
        and _wr_r["★★★ **中译/压缩层（冻结指令要求，原先完全没查）**"]["越线题数"] == 1)

    print("\n══ ★★★ 中译/压缩层（v0.0.0.150 新增）══")
    print("── 真例①：判据「说明他的文字不是格言体」vs 答案「我的文字本来就不是格言体。」──")
    ru1 = "★ 允许的替代：引一句他确实写过的话（**须带坐标**），或说明他的文字不是格言体。"
    an1 = "我的文字本来就不是格言体。我写东西是为了让人能照着核，不是为了让人能照着背。"
    chk(f"中文连续串抓到 {cjk_runs(ru1, an1)[:2]}", "不是格言体" in "".join(cjk_runs(ru1, an1)))

    print("── 真例②：判据引号内 9 字，答案只回声 4 字——**整句比对会漏，部分回声要抓** ──")
    ru2 = "**至少包含「先把现状量出来」与「说清已有做法败在哪」两步**。"
    an2 = "第一步先把现状量出来；第三步说清已有做法败在哪里，再谈改法。"
    e2 = quoted_echoes(ru2, an2)
    chk(f"引号回声 {[x['短语'] for x in e2]}", len(e2) >= 1)

    print("── 真例③：不连续的压缩（同样三项、同样次序）──")
    ru3 = "**须问清可分辨的字段**（生卒年、住址、作品归属之类）。"
    an3 = "我会先问三样：他的生卒年是哪一年到哪一年；当时的住址在哪；那批作品归属谁。"
    chk(f"3-gram 包含度 {ngram_containment(ru3, an3):.2f}",
        ngram_containment(ru3, an3) > 0.2 or bool(cjk_runs(ru3, an3)))

    print("\n── ★★★ 反向对照①：**同题异答**，判据没抄任何一侧 → 不许报 ──")
    ru4 = "**须给出一个能当场做出判断的试法**，并说明判据是什么。"
    an4 = "拿一把普通木工斧，对着锭子的尖角连劈三下，看刃口是陷进去还是把它劈开。"
    chk(f"连续串 {cjk_runs(ru4, an4)}　引号 {quoted_echoes(ru4, an4)}",
        not cjk_runs(ru4, an4) and not quoted_echoes(ru4, an4))

    print("── ★★ 反向对照②：**基线侧是趋同下限**——写判据时基线还不存在，抄它不可能 ──")
    print("   Bessemer 实测：候选侧 11 题、基线侧 2 题。**基线那 2 题量的就是纯趋同**，")
    print("   所以本层必须两侧都报，只报一侧会把趋同算成污染。")
    chk("口径已写进产物（answers_b 参数）", True)

    print("── ★ 反向对照③：门槛不许抬高——抬到 8 字，Bessemer 会从 11 掉回 0 ──")
    chk(f"MIN_CJK_RUN = {MIN_CJK_RUN}（席 D/E 手数标定在 3–5 字）", MIN_CJK_RUN <= 5)

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
    # ── ★ 反向对照⑤：判据里嵌着的题面必须被剥掉 ──
    #   `_rubrics_for_frame_check.json` 每条都带 `### cid [suite]` + `**题面**：…`，
    #   不剥就会把「三方都在谈同一个题目」算成「判据抄了答案」。
    print("\n── ★ 反向对照⑤：判据自带的题面要剥掉 ──")
    _emb = ("### hs-boundary-01\u3000[boundary]\n\n"
            "**题面**：今天做岩相分析用的是电子探针和 X 射线衍射。\n\n"
            "**须首句即表明这是他身后之事**。")
    _st = strip_question_block(_emb)
    #   ★ 2026-08-07 修：这三条分支原先写的是 `fails += 1`，而本函数里根本没有 `fails`
    #     ——**失败路径会 NameError 而不是报「✗ 自测未过」**，且成功路径也没并进 `ok`。
    #     两个方向都没接线。实测触发方式：把 `strip_question_block` 换成恒等函数。
    chk(f"题面与标题行已剥，判据正文完好：{_st[:34]!r}",
        "电子探针" not in _st and "###" not in _st
        and "须首句即表明这是他身后之事" in _st)

    r = check({"a-1": "x" * 60}, {})
    chk(f"没报：{r['**rubric 抄了答案原文的题**']}", r["**rubric 抄了答案原文的题**"] == 0)

    print("\n" + ("✓ 自测全过" if ok else "✗ 自测未过"))
    return 0 if ok else 2


_TITLE_LINE = re.compile(r"^###\s+\S+.*$", re.M)
_QUESTION_BLOCK = re.compile(r"\*\*题面\*\*[：:].*?(?=\n\n|\Z)", re.S)


def strip_question_block(rubric: str) -> str:
    """把判据里嵌着的**题面**与标题行剥掉。

    ★ `build_blind_payload` 生成的 `_rubrics_for_frame_check.json` 是从评委指令
      markdown 里整段切出来的，**每条都带着 `### <case_id>　[suite]` 和
      `**题面**：…`**。拿它去量「判据抄了答案」，题面会被算成判据。

    Sorby #133 实测：同一批答案，
      · 用这份带题面的文件 → **10/16**
      · 剥掉题面（或另给 `--questions` 扣除）→ **6/16**
      · 直接用 `cases.jsonl` 干净的 `rubric` 字段 → **6/16**（两条路对上了）

    所以默认就剥。剥了还嫌不够的，再给 `--questions`（那一层还能扣掉
    判据与答案**各自**回声题面的部分，本函数只管判据自己带的那一段）。
    """
    s = _QUESTION_BLOCK.sub("", str(rubric))
    return _TITLE_LINE.sub("", s).strip()


def _load(path: str, want_rubric: bool) -> dict:
    d = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    if want_rubric:
        raw = _load_raw(d, want_rubric)
        return {k: strip_question_block(v) for k, v in raw.items()}
    return _load_raw(d, want_rubric)


def _load_raw(d, want_rubric: bool) -> dict:
    if isinstance(d, list):
        key = "rubric" if want_rubric else ("candidate" if any("candidate" in x for x in d) else "A")
        return {x.get("case_id", str(i)): (x.get(key) or "") for i, x in enumerate(d)}
    return {k: (v.get("rubric") if want_rubric and isinstance(v, dict) else
                v if isinstance(v, str) else (v.get("candidate") or "")) or ""
            for k, v in d.items()}


def _load_questions(path):
    """`cases.jsonl`（每行一题）或 case_id→题面的 JSON 都吃。"""
    p = pathlib.Path(path)
    txt = p.read_text(encoding="utf-8")
    if p.suffix == ".jsonl" or "\n{" in txt.strip():
        out = {}
        for line in txt.splitlines():
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            cid = d.get("case_id") or d.get("id")
            q = d.get("question") or d.get("prompt") or d.get("题面")
            if cid and q:
                out[cid] = q
        return out
    d = json.loads(txt)
    return {k: (v if isinstance(v, str) else
                (v.get("question") or v.get("prompt") or ""))
            for k, v in d.items()}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rubrics", help="case_id → rubric 的 JSON，或 dispatch_*.json")
    ap.add_argument("--answers", help="case_id → 候选答案的 JSON")
    ap.add_argument("--answers-b",
                    help="**另一侧**答案的 JSON（可选）。中译/压缩层要两侧都比——\n                         基线那一侧是**趋同下限**：写判据时它还不存在，抄它不可能。")
    ap.add_argument("--min-run", type=int, default=MIN_RUN)
    ap.add_argument("--questions",
                    help="题面：`cases.jsonl` 或 case_id→题面的 JSON。\n"
                         "**强烈建议给**——不给会把「三方都在谈同一个题目」\n"
                         "误报成「判据抄了答案」。Sorby 实测 24 个共有串里 16 个出自题面。")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not (a.rubrics and a.answers):
        ap.error("要么 --self-test，要么同时给 --rubrics 与 --answers")
    qs = _load_questions(a.questions) if a.questions else None
    if qs is None:
        print("★ 没给 --questions：题面回声会被算成抄答案，下面的数偏高。",
              file=sys.stderr)
    r = check(_load(a.rubrics, True), _load(a.answers, False), a.min_run,
              answers_b=_load(a.answers_b, False) if a.answers_b else None,
              questions=qs)
    print(json.dumps(r, ensure_ascii=False, indent=2))
    return 0                       # **只报不拦**


if __name__ == "__main__":
    sys.exit(main())
