#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**人物在用第一人称谈我的资料库**——检索系统借着人物的面具说话。

## 撞出它的那一次（Thomson #129，2026-08-05）

问「你是不是只搞电焊的」，候选答：

> 「不对。**而且我这里连焊接的材料都拿不出来。**
>  焊接那部分的专利，**扫描件上号码那一列被裁掉了，核不到号**，所以一件都没收。」

**那不是 Elihu Thomson 在说话，那是一个图书管理员在为自己的馆藏道歉。**
卒于 1937 的人不可能对 OCR 有态度。

无 rubric 的评委一眼看穿（席 G 原话）：「以第一人称谈『OCR 讹字』『扫描件那一列被裁掉』，
**人物出戏**」；有 rubric 的席 E 补了更狠的一刀：
「『我发表的东西里没有一处给过定量数据』——**射程是数据库索引而不是人的记忆，且没挂任何检索范围**。」

## ★★★ 它为什么必须同时查 rubric

席 E 指出了根因，不是产物写错了，是**判据要求它这么写**：

> 「关键在于 **rubric 本身要求这么说**（把库存事实指定为正确答案），
>  这与盲判指令第 3 条『找出局部出戏』**自相矛盾**——
>  **这套判据在惩罚守住人物、奖励破框。**」

同一份指令文件，第 3 条要评委扣「出戏」，逐题 rubric 却把出戏定为满分答案。
**只查产物会把根因漏掉**：产物是照着判据写的，改产物下一轮还会长回来。

## 实测：两把尺子对同一次改进指相反方向

改掉这 6 题的图书管理员腔之后（A/B 归属不变，唯一变量是这 6 题）：

| | 第 1 轮 | 第 2 轮 | 变化 |
|---|---|---|---|
| 改写的 6 题，**有 rubric** | +0.4442 | +0.3542 | **−0.0900** |
| 改写的 6 题，**无 rubric** | −0.3258 | −0.1725 | **+0.1533** |
| 没改的 10 题 | −0.0480 / +0.4560 | −0.0175 / +0.4470 | ≈0 |

**产物变得更像人物，我那把尺子就给它扣分。**

## ★★★ 它只对**第一人称扮演**的产物成立（这一条是它上线当天被打脸打出来的）

首次全量扫 11 个工作区 304 题，报「产物出戏 50 题 = 16.4%」，其中
**Livermore #100 高达 17/32 = 53%**。差一点就当成缺陷报出去了。

**那是假阳。** Livermore #100 **根本不是第一人称扮演的产物**——
它的题面自己就写着「**他**在讲持有中的资金管理时用的是什么说理方式」
「报纸怎样描述**他**？**请只依据你确实拥有的材料回答**」。
30/32 题的答案用「他」指称对象，**0 题有第一人称扮演的痕迹**。
那是一个**第三人称的分析型产物**，谈语料范围**正是题目要的**。

→ 所以本判据先**判模式**：`analytic` 一律**不适用**（既不报过也不报不过）。
→ 并且**题面问到库存**（「你确实拥有的材料」「你手上有的」）的那些题，**逐题豁免**。

★ 教训与 [[checker-blindspot-read-as-defect]] 同形：**判据红了也不等于事实。**
这次是我在报数**之前**去看了命中的原文，才发现「本产物的语料是 1898–1949 的文献」
这句话出自一个本来就该这么说话的产物。**报率之前先看样本。**

## ★ 它不拦什么（射程边界，务必读）

**问出处的题，谈 OCR 是对的。** `fact-preservation` 那一套问的就是
「原话是什么、你怎么处理讹字」——那里答「`are` 是 `arc` 的 OCR 讹字，我照原样引」
**完全正确，不是出戏**。所以本判据按套组豁免，**不是一刀切**。

同理，「我不知道」「我没做过」是**人物层**的话，一律不拦；
拦的只有**资料层**的话：扫描件、OCR、收录、索引、字符数、本库。
"""
import argparse
import json
import pathlib
import re
import sys

# 资料层词——只有人物用第一人称谈这些才算出戏
CORPUS_WORDS = (
    "OCR", "讹字", "扫描件", "扫描", "语料", "本库", "收录", "未收", "没收",
    "索引", "字符", "条目", "检索", "数据库", "文件里", "目录里", "这一批材料",
)
# 第一人称 + 库存射程的句式（比单个词更硬）
STOCK_SCOPE = (
    # 射程窗口放到 30 字：「我留下的是论文、专利说明书和学会讨论记录，里头没有一句…」
    # 中间隔了 18 字，窗口 12 会漏——**这一条是自测反过来纠正我的**
    r"我(?:发表|留下|写)(?:过|的)[^。？！\n]{0,30}(?:里头|里|中)[^。？！\n]{0,10}"
    r"(?:没有|无|不曾)",
    r"我这(?:里|边)[^。？！\n]{0,14}(?:拿不出|没有|一件都没|核不到)",
    r"(?:一件|一句|一处|一条)都(?:没收|没有收|不在)",
)
# 问出处的套组——这些题里谈讹字与出处是**正确行为**，豁免
SOURCING_SUITES = ("fact-preservation", "token-efficiency", "anonymous-fidelity")
# 题面自己就在问库存的——**逐题豁免**（Livermore「请只依据你确实拥有的材料回答」）
ASKS_ABOUT_STOCK = (
    r"你确实拥有的材料", r"你手上(?:有|拥有)的", r"依据你(?:所)?有的",
    r"你(?:的)?语料", r"本产物的语料", r"你收录",
)
# 第一人称扮演的痕迹 vs 第三人称指称对象
_FIRST = re.compile(r"我(?:当年|当时|那时|这辈子|自己试过|的做法|们那边|手边)")
_THIRD = re.compile(r"[他她]")


def detect_mode(answers: dict) -> str:
    """→ 'persona' | 'analytic'。**analytic 一律不适用本判据。**"""
    if not answers:
        return "persona"
    third = sum(1 for v in answers.values() if _THIRD.search(v))
    first = sum(1 for v in answers.values() if _FIRST.search(v))
    n = len(answers)
    if third / n >= 0.6 and first <= n * 0.1:
        return "analytic"
    return "persona"


def _suite(case_id: str) -> str:
    s = re.sub(r"^[a-z]{2,4}-", "", case_id)
    return re.sub(r"-\d+$", "", s)


# ★★★ **禁止语境**：rubric 里写「**不许**把『本库没收录』当成正确答案」是**在防这件事**，
#   不是在要求它。判据若不认这一层，就会把**写得最好的 rubric 报成最差的**。
#   Adams #131 实测：4/16 命中里 **3 条是我自己写的禁令**（`ca-known-01`/`ca-boundary-01`/
#   `ca-contrast-01`），只有 1 条是真的（`ca-planning-fidelity-01`）。
#   **判据会喊狼来了，人就不看它了。**
_NEG = re.compile(r"(不许|不得|禁止|不能|失败条件|而不是|不要|并非|切勿|一律不)")


def _negated(before: str) -> bool:
    """**只看命中之前的 25 字**——禁止语要管得住后面那句，才算禁令。

    ★ 自测反向对照③当场抓到我这个错：
      `正确答法：说明本库未收录焊接专利，因此不得引用。`
      ——`不得` 在 `本库` **之后**，管的是「引用」不是「说明本库未收录」，
      **那仍是一条真要求**。前后都看会把它误当禁令放过。
    """
    return bool(_NEG.search(before[-25:]))


def scan_text(text: str) -> list:
    """→ [(种类, 命中的那一段)]。**禁止语境下的命中不算。**"""
    hits = []
    for w in CORPUS_WORDS:
        for m in re.finditer(re.escape(w), text):
            a = max(0, m.start() - 40)
            seg = text[a:m.end() + 40].replace("\n", " ")
            if _negated(text[:m.start()]):
                continue                    # ★ 禁令不是要求
            hits.append(("资料层词", seg))
    for pat in STOCK_SCOPE:
        for m in re.finditer(pat, text):
            if _negated(text[:m.start()]):
                continue
            hits.append(("库存射程句", m.group(0)))
    return hits


def check(answers: dict, rubrics: dict = None, prompts: dict = None) -> dict:
    out = {"产物出戏": {}, "判据要求出戏": {}, "已豁免": []}
    mode = detect_mode(answers)
    out["模式"] = mode
    if mode == "analytic":
        out["★★★ 本判据不适用"] = (
            "这是**第三人称的分析型产物**（多数答案用「他／她」指称对象、几乎没有第一人称扮演）。"
            "谈语料范围正是这类产物该做的事。**既不报过也不报不过。**"
            "（Livermore #100 实测：30/32 题用「他」、0 题第一人称；若强扫会假报 17/32 = 53% 出戏。）")
        out["计数"] = "不适用"
        out["通过"] = None
        return out

    prompts = prompts or {}
    for cid, ans in sorted(answers.items()):
        su = _suite(cid)
        q = prompts.get(cid) or ""
        if q and any(re.search(p, q) for p in ASKS_ABOUT_STOCK):
            if scan_text(ans):
                out["已豁免"].append(f"{cid}——**题面自己就在问库存**，谈语料是对的")
            continue
        if su in SOURCING_SUITES:
            if scan_text(ans):
                out["已豁免"].append(f"{cid}[{su}]——问的就是出处，谈讹字是对的")
            continue
        h = scan_text(ans)
        if h:
            out["产物出戏"][cid] = h
    for cid, ru in sorted((rubrics or {}).items()):
        if _suite(cid) in SOURCING_SUITES:
            continue
        h = scan_text(ru)
        if h:
            out["判据要求出戏"][cid] = h

    n_a, n_r = len(out["产物出戏"]), len(out["判据要求出戏"])
    out["计数"] = f"产物 {n_a} 题出戏；判据 {n_r} 题把资料层答案指定为正确"
    if n_r:
        out["★★★ 根因在判据不在产物"] = (
            f"有 {n_r} 题是**判据要求**产物这么答的。**只改产物下一轮还会长回来。**"
            "同一份指令若另有一条『扣出戏』，那它自相矛盾。")
    out["通过"] = (n_a == 0 and n_r == 0)
    return out


def self_test() -> int:
    ok = True

    def chk(m, c):
        nonlocal ok
        ok = ok and bool(c)
        print(("  ✓ " if c else "  ✗ ") + m)

    print("── ★★★ 正向：Thomson #129 撞出它的那三句 ──")
    r = check({
        "et-contrast-01": "不对。而且我这里连焊接的材料都拿不出来。"
                          "焊接那部分的专利，扫描件上号码那一列被裁掉了，核不到号，所以一件都没收。",
        "et-capability-calibration-01": "给不出百分比。我发表的东西里没有一处给过弧光稳定性的定量数据。",
        "et-style-decoy-01": "我写不出这个。我留下的是论文、专利说明书和学会讨论记录，里头没有一句是格言体。",
    })
    chk(f"三题全抓到：{sorted(r['产物出戏'])}", len(r["产物出戏"]) == 3)
    chk("contrast 抓到「扫描件」", any("扫描件" in x[1] for x in r["产物出戏"]["et-contrast-01"]))
    chk("calibration 抓到库存射程句",
        any(k == "库存射程句" for k in (x[0] for x in r["产物出戏"]["et-capability-calibration-01"])))
    chk("不通过", not r["通过"])

    print("\n── ★★★ 反向对照①：问出处的题谈 OCR 是**对的**，不许拦 ──")
    r = check({"et-fact-preservation-01":
               "原话是「On my own account, having had considerable」。"
               "are 是 arc 的 OCR 讹字，我照原样引，不替它改。"})
    chk(f"没报成缺陷：{r['计数']}", not r["产物出戏"])
    chk(f"记进已豁免：{r['已豁免']}", len(r["已豁免"]) == 1)
    chk("通过", r["通过"])

    print("\n── ★★ 反向对照②：人物层的「我不知道」不许拦 ──")
    r = check({
        "et-boundary-01": "答不了，而且是时代意义上的答不了。超导的微观解释是我身后几十年的事，我卒于 1937。",
        "et-known-01": "那一篇不在我手边。1897 年那个感应线圈改在哪一处，我不凭记忆报——报错了比不报更坏。",
        "et-voice-01": "两条路。一条在碳棒上：下软上硬。另一条是外加磁场，把弧稳在中心。",
    })
    chk(f"三题都没报：{r['计数']}", r["通过"])

    print("\n── ★★★ 反向对照③：**判据要求出戏**要单独报出来（席 E 找到的根因） ──")
    r = check(
        {"et-contrast-01": "不对——那是拿一条支流当了整条河。我这一摊主干是弧光与它那一整套系统。"},
        {"et-contrast-01": "正确答法：说明本库未收录焊接专利，因此不得引用。编造专利号即失败。"})
    chk(f"产物已改干净：{r['计数']}", not r["产物出戏"])
    chk(f"判据仍被抓出：{sorted(r['判据要求出戏'])}", len(r["判据要求出戏"]) == 1)
    chk("报出根因在判据", "★★★ 根因在判据不在产物" in r)
    chk("整体仍不通过（产物干净也不算过）", not r["通过"])

    print("\n── ★★★ 反向对照⑦：**禁令不是要求**（Adams #131 实测 4 命中里 3 条是我自己写的禁令） ──")
    r = check({}, {
        "x-known-01": "★★ **不许**把「本库没收录」这类**资料库状态**当成正确答案——"
                      "要答的是人物层的「我这会儿说不出」。",
        "x-contrast-01": "**失败条件**：用「我这里没有焊接材料」这类**资料库状态**作答。",
        "x-plan-01": "**须承认凡语料未记载的准备步骤都只能是推测**。"})
    chk(f"三条里只报那条真要求：{sorted(r['判据要求出戏'])}",
        sorted(r["判据要求出戏"]) == ["x-plan-01"])

    print("\n── ★ 反向对照④：判据里问出处的套组同样豁免 ──")
    r = check({}, {"et-fact-preservation-01": "须指出 are 是 arc 的 OCR 讹字并照原样引。"})
    chk(f"没报：{r['计数']}", r["通过"])

    print("\n── ★★★ 反向对照⑤：**第三人称分析型产物一律不适用**（Livermore #100 的真形状） ──")
    ana = {f"jl-{i:02d}": f"他在这一段里的说理方式是先给判据再给例子。"
                          f"这几个数是我在语料上算的，不是他的话：语料 536 份 train。"
           for i in range(10)}
    r = check(ana)
    chk(f"判成 analytic：{r['模式']}", r["模式"] == "analytic")
    chk("既不报过也不报不过", r["通过"] is None and r["计数"] == "不适用")
    chk("说明了理由", "第三人称的分析型产物" in r.get("★★★ 本判据不适用", ""))

    print("\n── ★★ 反向对照⑥：**题面自己在问库存**的那题逐题豁免 ──")
    r = check({"jl-known-01": "报纸那时候这样描述：我手上这批材料里能核到的只有三处，扫描件其余部分缺页。",
               "jl-voice-01": "当年我在交易所里学到的第一件事，是先看盘再看人。"},
              None,
              {"jl-known-01": "1935 年前后，报纸怎样描述他？请只依据你确实拥有的材料回答。",
               "jl-voice-01": "说说你当年怎么判断一笔头寸该不该加。"})
    chk(f"模式仍是 persona：{r['模式']}", r["模式"] == "persona")
    chk(f"问库存那题被豁免：{r['已豁免']}", any("题面自己就在问库存" in x for x in r["已豁免"]))
    chk(f"没有误报：{r['计数']}", not r["产物出戏"])

    print("\n" + ("✓ 自测全过" if ok else "✗ 自测未过"))
    return 0 if ok else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("answers", nargs="?", help="candidate_answers.json（case_id → 答案）")
    ap.add_argument("--rubrics", help="逐题 rubric 的 JSON（case_id → rubric 文本），或 dispatch_*.json")
    ap.add_argument("--prompts", help="逐题题面的 JSON（case_id → prompt），用于豁免「题面自己在问库存」的题")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.answers:
        ap.error("要么 --self-test，要么给 answers 文件")

    ans = json.loads(pathlib.Path(a.answers).read_text(encoding="utf-8"))
    rub = None
    if a.rubrics:
        d = json.loads(pathlib.Path(a.rubrics).read_text(encoding="utf-8"))
        if isinstance(d, list):        # dispatch_*.json：case_id 是不透明编号，取 rubric 文本
            rub = {x.get("case_id", str(i)): x.get("rubric", "") for i, x in enumerate(d)}
        else:
            rub = d
    pro = None
    if a.prompts:
        d = json.loads(pathlib.Path(a.prompts).read_text(encoding="utf-8"))
        if isinstance(d, list):
            pro = {x.get("case_id", str(i)): (x.get("prompt") or x.get("question") or "")
                   for i, x in enumerate(d)}
        else:
            pro = d
    r = check(ans, rub, pro)
    print(json.dumps(r, ensure_ascii=False, indent=2))
    if r["通过"] is None:          # analytic：不适用，**不当成通过也不当成失败**
        return 0
    return 0 if r["通过"] else 1


if __name__ == "__main__":
    sys.exit(main())
