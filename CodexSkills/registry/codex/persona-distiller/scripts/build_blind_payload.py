#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""盲判载荷生成 → 不透明编号 + 两侧落进工作区 + **当场跑表面特征泄题门**。

**每人共用这一份，不许再各写各的。**

## 为什么收成共享件

此前每人一份 `build_XX_blind.py`，虽然文件头自称「母版」，
但**工作区路径是写死的**（`workspaces/clara-barton/clara-barton/evals/cases.jsonl`）——
复制出去改漏一处就是静默错。同一个失误类已经在
`assemble_XX_results.py` 上炸过一次（同一处除以 10 做了两遍，
三轮 delta 全差一个数量级）。

## 它替哪几条已知缺陷把关

**① `case_id` 不许把期望行为写在题号上。**
`jl-refusal-stop-01` / `jl-style-decoy-02` 这类题号**直接告诉评委这题该拒答**。
两席在 Lister #108 三轮里共报四次：

> 席 D：「`case_id` 已把期望行为写进名字…**这份盲判并不盲。**」
> 席 E：「`refusal-stop`／`style-decoy`／`token-efficiency` 直接写在 id 里，
>        **两侧都在照名字表演。**」

发给评委的一律是 `q-01`…，套组归属只留在 key 里。

**② 报候选/基线的均长比，不报 A/B 侧的差。**
候选被 `sha256 % 2` 均分到两侧，**A/B 均长必然接近——那是分配方式的产物**，
不是「两个系统长度对等」。Lister 三轮：A/B 侧差 5.5%/0.8%/8.7%，
而真实的候选比基线长 **73%/109%/144%**。

**③ 两侧一起落进工作区。**
`evals/` 里一度只有候选侧，基线只存在于人物工作目录——
**判据造好了、接线好了，却没有数据可判**，只能报「未核（不是通过）」。

**④ ★ 生成即判：当场跑 `check_answer_surface_leak`。**
Barton #117 的格式泄题（一条正则分开 32/32）是**第 3 轮判完之后**
才由席 E 说出来的——三轮判分全部作废在这上面。
**泄题必须拦在派发评委之前，不是拦在判完之后。**
本件默认在落盘后直接跑那道门，未过就**退出 1 且不建议派发**。

## 用法

    python3 build_blind_payload.py --workspace <target> --round-dir round1 \\
        --candidate cb_candidate.json --baseline cb_baseline.json [--prefix cb]
    python3 build_blind_payload.py --self-test
"""
import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
LEAK_CHECKER = HERE / "check_answer_surface_leak.py"
LOC_CHECKER = HERE / "check_quote_locator.py"   # ★ v0.0.0.89：坐标也在生成时把


RUBRIC_MARKERS = ("## 逐题 rubric", "## 逐题评分标准")
_CID_RE = re.compile(r"^[a-z]{2,4}(?:-[a-z]+)+-\d+$")


def extract_rubrics(text: str, cases: list):
    """从冻结指令里抽出逐题 rubric。**抽不到就返回 None，绝不退回整份文件。**

    ## ★ 这个函数是补一个真实的漏

    原来一行：`text.split("## 逐题 rubric", 1)[-1]`。
    Adams #131 的小标题写的是 **`## 逐题评分标准`**（写 v2 rubric 时改的名），
    `split` 没命中 —— 而 **`[-1]` 在没命中时返回的是整份文件**。
    于是整段前言被当成一条 rubric 喂给了判据，多出一个键 **`'#'`**。

    ★★ **它没有报错，报的是「0/17」。** 17 = 16 题 + 1 个假题。
    分母多了 1 而没有任何一处说话——**这正是「判据绿了但指错了文件」的第 11 次。**

    三道防线，缺一不可：
    1. 认多个小标题（两种写法都是真实存在的）；
    2. **一个都不命中 → 返回 None 让调用方中止**，不许静默用整份文件；
    3. 键必须长得像 case_id，且**必须真的在本次的题目集合里**——
       前言那种块连第 3 关都过不了。
    """
    body = None
    for m in RUBRIC_MARKERS:
        if m in text:
            body = text.split(m, 1)[1]
            break
    if body is None:
        return None
    want, out = set(cases), {}
    for blk in re.split(r"\n### ", body):
        blk = blk.strip()
        if not blk:
            continue
        cid = blk.split("\u3000")[0].split()[0].strip()
        if cid in want or _CID_RE.match(cid):
            out[cid] = "### " + blk
    return out or None


def _balanced_flips(cids: list) -> dict:
    """→ {case_id: flip}，**恰好一半 0 一半 1**，仍然只依赖 case_id、可复现。

    按 sha256 排序取前一半为 0。与逐题取模的区别只在**边际分布**：
    取模是 16 次独立抛硬币，本函数是**不放回地发 8 黑 8 白**。
    """
    order = sorted(cids, key=lambda c: hashlib.sha256(c.encode()).hexdigest())
    half = len(order) // 2
    return {c: (0 if i < half else 1) for i, c in enumerate(order)}


def assign(cases: dict, cand: dict, base: dict, balanced: bool = False) -> tuple:
    """→ (payload, key)。A/B 只由 case_id 决定，**与内容无关、可复现**。

    `balanced=False`（默认，历史行为）：`sha256(case_id) % 2`，**16 次独立抛硬币**。
    `balanced=True`：强制 8/8。

    ## ★ 为什么会有这个参数——Adams #131 抽到 14/16

    实测：仓里三个前缀 `ca`/`et`/`gwc` 分别是 **14/16**、8/16、9/16。
    拿 2000 个合成前缀验哈希本身：**均值 8.059**、偏离 ≥4 的占 **7.55%**
    （16 次公平抛硬币的理论值 7.68%）——**哈希是公平的，Adams 只是手气差。**

    ★★ 但「公平」不等于「够用」：**每 13 个人物就有 1 个会落到 ≥12/16**，
    600 人算下来约 46 次。那时**位置与系统高度相关**，
    评委任何一点位置偏好（比如偏爱先读到的那一侧）都会**直接灌进 delta**。
    这与已记的「长度混杂」是同一类混杂，只是通道从篇幅换成了位次。

    ★★★ **默认没有改成 True**：改了会让已派发轮次的 A/B 变号，
    与「各轮之间 A/B 必须逐条一致」直接冲突。**Adams #131 用的仍是取模。**
    是否从下一个人物起改默认——**待用户裁定（⑱）**。
    """
    flips = _balanced_flips(sorted(cases)) if balanced else None
    payload, key = [], {}
    # ★★★★ 2026-08-11：**发题的顺序原先是按 case_id 字母序，那本身就是套组线索。**
    #
    #   原写 `enumerate(sorted(cases), 1)`，于是每个人物、每一轮都恒有：
    #       q-01 = anonymous-fidelity｜q-02 = boundary｜…｜q-16 = voice
    #   评委只要知道那 16 个套组名（它们是标准的、每个人物都一样），
    #   **就能从位次反推出这一题在测什么**。
    #
    #   ★ 抓到它的是 Grotius #168 第 2 轮的席 K，它在观察报告里写：
    #     「派发说题号是 8 位十六进制，载荷里实际是 q-01…q-16 顺序编号，
    #       且同类题相邻——**顺序本身携带信息**」。
    #   本件的文件头一直写着「发给评委的一律是 q-01…，套组归属只留在 key 里」——
    #   **那句话只对了一半：编号不带信息了，顺序还带着。**
    #
    #   改成按 cid 的哈希排：仍然确定、可复现，但**与套组名的字母序不相关**。
    #   ★ A/B 翻转仍由 `sha256(cid) % 2` 驱动，**不受本次改动影响**——
    #     「各轮之间 A/B 必须逐条一致」那条不变量保住了。
    order = sorted(cases, key=lambda c: hashlib.sha256(("order|" + c).encode()).hexdigest())
    for i, cid in enumerate(order, 1):
        if cid not in cand or cid not in base:
            raise SystemExit(f"✗ **缺答案：{cid}**——不是「这题跳过」，是载荷不完整")
        flip = flips[cid] if flips is not None else \
            int(hashlib.sha256(cid.encode()).hexdigest(), 16) % 2
        a, b = (cand[cid], base[cid]) if flip == 0 else (base[cid], cand[cid])
        opaque = f"q-{i:02d}"
        key[opaque] = {"A": "candidate" if flip == 0 else "baseline",
                       "B": "baseline" if flip == 0 else "candidate",
                       "case_id": cid}
        payload.append({"case_id": opaque, "question": cases[cid], "A": a, "B": b})
    return payload, key


def length_report(cases: dict, cand: dict, base: dict) -> dict:
    """→ 候选/基线的均长与比值。**A/B 侧的差不在这里，因为那不是该看的数。**"""
    n = len(cases)
    lc = sum(len(cand[c]) for c in cases) / n
    lb = sum(len(base[c]) for c in cases) / n
    return {"n": n, "cand": lc, "base": lb, "ratio_pct": (lc - lb) / max(lb, 1) * 100}


# ══════════════════ 自测 ══════════════════

def selftest() -> int:
    fails = []

    def chk(label, cond):
        print(("  ✓ " if cond else "  ✗ ") + label)
        if not cond:
            fails.append(label)

    cases = {f"xx-refusal-stop-{i:02d}": f"题面 {i}" for i in range(1, 9)}
    cand = {c: "候选答案" * 10 for c in cases}
    base = {c: "基线答案" * 10 for c in cases}

    print("── 正向：题号必须是不透明编号，套组不许出现在发给评委的那份里 ──")
    payload, key = assign(cases, cand, base)
    chk(f"载荷题号形如 {payload[0]['case_id']}（**不是 xx-refusal-stop-01**）",
        all(p["case_id"].startswith("q-") for p in payload))
    blob = json.dumps(payload, ensure_ascii=False)
    chk("载荷里搜不到 refusal-stop 这类会泄期望行为的串", "refusal-stop" not in blob)
    chk("而 key 里留着真 case_id（回查用）",
        all(v["case_id"] in cases for v in key.values()))

    print("── 正向：A/B 分配可复现，同一 case_id 每次都落同一侧 ──")
    _, key2 = assign(cases, cand, base)
    chk("两次生成的 key 逐条相同", key == key2)

    print("── ★★ 位次平衡：balanced=True 必须恰好一半一半，且仍然可复现 ──")
    #   反向对照：先证明**默认那条路真的会一边倒**，否则这个自测什么也没证明。
    skew = {f"ca-{s}-01": "题面" for s in
            ("anonymous-fidelity", "boundary", "capability-calibration", "contrast",
             "fact-preservation", "identity-routing", "known", "long-horizon",
             "planning-fidelity", "refusal-stop", "style-decoy", "task-completion",
             "token-efficiency", "tool-use", "trajectory", "voice")}
    sc = {c: "候选" for c in skew}
    sb = {c: "基线" for c in skew}
    _, k_mod = assign(skew, sc, sb)
    n_mod = sum(1 for v in k_mod.values() if v["A"] == "candidate")
    chk(f"默认（取模）在 Adams 真实题号上确实一边倒：{n_mod}/16", n_mod == 14)
    _, k_bal = assign(skew, sc, sb, balanced=True)
    n_bal = sum(1 for v in k_bal.values() if v["A"] == "candidate")
    chk(f"balanced=True 变成 {n_bal}/16", n_bal == 8)
    _, k_bal2 = assign(skew, sc, sb, balanced=True)
    chk("balanced 也可复现（两次逐条相同）", k_bal == k_bal2)
    chk("★ 两条路给出的 A/B **确实不同**（所以不许中途改默认）", k_mod != k_bal)

    print("── ★★ 抽 rubric：小标题不认识时**必须返回 None**，不许退回整份文件 ──")
    real = ["ca-known-01", "ca-voice-01"]
    doc = ("# 冻结评委指令 v1\n\n前言：不许把「本库没收录」当成正确答案。\n\n"
           "## 逐题评分标准\n\n### ca-known-01\u3000[known]\n\n须说明拿不出该篇。\n\n"
           "### ca-voice-01\u3000[voice]\n\n须先认没讲清。\n")
    r = extract_rubrics(doc, real)
    chk(f"认得 `## 逐题评分标准`，抽出 {len(r or {})} 条", r is not None and len(r) == 2)
    chk("**前言没有混进来**（没有 `#` 这种假题）", r is not None and "#" not in r)
    r2 = extract_rubrics(doc.replace("## 逐题评分标准", "## 逐题 rubric"), real)
    chk("`## 逐题 rubric` 这种老写法也认得", r2 is not None and len(r2) == 2)
    chk("★ 两种写法抽出来的内容一样", (r or {}).keys() == (r2 or {}).keys())
    bad = extract_rubrics(doc.replace("## 逐题评分标准", "## 打分细则"), real)
    chk("★★ 小标题不认识 → **返回 None**（旧代码这里会把整份文件当 rubric）", bad is None)

    print("── 反向对照 ①：缺一条答案 → 必须退出，不许静默少一题 ──")
    short = {k: v for k, v in cand.items() if k != sorted(cases)[0]}
    try:
        assign(cases, short, base); ok = False
    except SystemExit as e:
        ok = "缺答案" in str(e)
    chk("候选少一题 → SystemExit（**不是「这题跳过」**）", ok)

    print("── ★ 反向对照 ②：长度报的是候选/基线，不是 A/B 侧 ──")
    #   造一组「候选整体长一倍」的：A/B 侧均长会接近，而候选/基线比必须是 +100%
    long_cand = {c: "候选答案" * 20 for c in cases}
    r = length_report(cases, long_cand, base)
    chk(f"候选比基线长 {r['ratio_pct']:+.0f}%（**A/B 侧差在这里根本没被算**）",
        abs(r["ratio_pct"] - 100) < 1)
    pl, ky = assign(cases, long_cand, base)
    a_len = sum(len(p["A"]) for p in pl) / len(pl)
    b_len = sum(len(p["B"]) for p in pl) / len(pl)
    chk(f"同一组数据的 A/B 两侧均长 {a_len:.0f} vs {b_len:.0f}"
        f"——**接近，且这正是它不该被当成「长度对等」的原因**",
        abs(a_len - b_len) / max(b_len, 1) < 0.35)

    print("── 反向对照 ③：泄题门必须存在，缺了不许当成通过 ──")
    chk(f"{LEAK_CHECKER.name} 在", LEAK_CHECKER.is_file())
    chk(f"{LOC_CHECKER.name} 在", LOC_CHECKER.is_file())
    # ★ 反向对照：两道生成时判据必须都在——少一道就等于那一道从没跑过
    chk("四道生成时判据都在（少一道 = 那道从没跑过）",
        LEAK_CHECKER.is_file() and LOC_CHECKER.is_file()
        and (HERE / "check_answer_holdout_leak.py").is_file()
        and (HERE / "check_answer_numbers_in_corpus.py").is_file())

    print("\n── ★★ 发题顺序不许携带套组信息（2026-08-11，席 K 抓到）──")
    SUITES = ["known", "boundary", "voice", "trajectory", "contrast", "fact-preservation",
              "style-decoy", "task-completion", "planning-fidelity", "tool-use",
              "capability-calibration", "refusal-stop", "long-horizon", "identity-routing",
              "anonymous-fidelity", "token-efficiency"]
    _cases = {f"hg-{s}-01": f"题面：{s}" for s in SUITES}
    _cand = {k: "候选文" for k in _cases}
    _base = {k: "基线文" for k in _cases}
    _pay, _key = assign(_cases, _cand, _base)

    seq = [_key[f"q-{i:02d}"]["case_id"] for i in range(1, 17)]
    alpha = sorted(_cases)
    chk("发题顺序**不等于** case_id 字母序（字母序＝套组名顺序，恒定可反推）",
        seq != alpha)

    # ★ 反对照①：仍须确定可复现——同样的输入两次必须给出同样的顺序
    _pay2, _key2 = assign(_cases, _cand, _base)
    chk("**反对照**：同输入两次 → 顺序完全相同（确定、可复现）",
        [_key2[f"q-{i:02d}"]["case_id"] for i in range(1, 17)] == seq)

    # ★ 反对照②：16 题一个不多一个不少，且 q-01…q-16 与 case_id 一一对应
    chk("**反对照**：16 题齐、无重复、与 case_id 一一对应",
        len(seq) == 16 and len(set(seq)) == 16 and set(seq) == set(_cases))

    # ★ 反对照③：**A/B 翻转不受排序改动影响**——那条不变量是「各轮之间逐条一致」
    import hashlib as _h
    ok_flip = all(
        _key[f"q-{i:02d}"]["A"] == ("candidate"
                                    if int(_h.sha256(seq[i - 1].encode()).hexdigest(), 16) % 2 == 0
                                    else "baseline")
        for i in range(1, 17))
    chk("**反对照**：A/B 翻转仍由 `sha256(cid)%2` 决定，排序改动没碰它", ok_flip)

    print(f"\n{'✓ 自测全过' if not fails else f'✗ **{len(fails)} 项未过**'}")
    return 0 if not fails else 2


def locator_gate(cand_path) -> int:
    """引文坐标在**生成时**把关。→ 0 过 / 1 拦。

    ★★ 它**不受 `--skip-leak-check` 影响**——那个旗标按名字只该跳过表面泄题门。
    第一版我把这段接在泄题门之后，而 `--skip-leak-check` 是 `return 0` 早退，
    **实跑才发现这道门永远跑不到**。只看代码不算。

    实测 12 人：长逐字引文 198 条，**缺坐标 66 条（33%）**——
    判据一直在报 ⚠、席 E 也点名过同一批题（「未在本题标出 CR 卷次」
    「图注标『出自全集』而无卷页」），**而它从没被当成缺陷修过**：
    因为它是 ⚠ 不是 error，没有人回头看清单。

    ★ 装在这里而不是把发布门的 ⚠ 改成 error——后者会改动已判过的人的门。
    **这一道只拦新载荷。**

    ★★ 它**不需要语料**：`check_quote_locator` 只看答案里引文附近有没有坐标，
    从不读 raw/。我第一版加了个 `--corpus` 前置条件，于是没给语料时它打印
    「未核（不是通过）」却**返回 0（通过）**——**印的话和做的事相反**。
    条件已删，这道门无条件跑。
    """
    print("\n── 引文坐标门（**派发之前必须过**）──")
    if not LOC_CHECKER.is_file():
        print("⚠ check_quote_locator.py 不在，**引文坐标未核（不是通过）**")
        return 0
    q = subprocess.run([sys.executable, str(LOC_CHECKER), "--answers", str(cand_path)],
                       capture_output=True, text=True)
    print(q.stdout.rstrip())
    # ★★★★ 2026-08-07：**退出码 3 是「没有引文可查」，1 才是「有引文而缺坐标」。**
    #   本门原先写 `if q.returncode != 0`，把两者混成一个，于是打印出两句互相矛盾的话：
    #       「一条长逐字引文都没扫到——**本次未检查（不是通过）**」
    #       「✗ **不许派发：有逐字引文找不到坐标。**」
    #   **两句不可能同时为真。**
    #   ★ 后果是这道门对「答案里没有长逐字引文」的人物**永远变不绿**——
    #     [[a-red-that-can-never-turn-green-is-not-a-signal]]。
    #   ★★ 而 Whitworth #152 之所以撞上，是**我自己两条规矩打架**：
    #     为堵格式泄题通道，我要求两侧「禁反引号、英文引语转写成中文」，
    #     于是长逐字引文一条也没有了。
    #   修法：**只拦 rc==1（有引文而缺坐标）**；rc==3 报「未检查（不是通过）」并放行，
    #   **但要把这句话打得足够响**，不许被读成「通过」。
    if q.returncode == 3:
        print("\n⚠⚠ **本轮答案里没有长逐字引文，因此这道门没有可查的东西——**")
        print("   **这是「未检查」，不是「通过」。** 载荷放行，但这一轮的引文可回查性**没有被验证过**。")
        print("   ★ 若这是格式规矩造成的（例如禁反引号／要求英文引语转写成中文），"
              "那是有意的取舍：**堵住了格式泄题通道，代价是失去了引文坐标这一层的检查**。"
              "两件事都要写进协议记录。")
        return 0
    if q.returncode != 0:
        print("\n✗ **这份载荷不许派发评委：有逐字引文找不到坐标。**")
        print("  坐标 = 卷/期/页/篇名/图注编号，写在同一段里。")
        print("  「详见那篇论文」不算坐标；「出自全集」不算坐标。")
        print("  ★ 补坐标是**有实质**的改动（读者从此能回查），"
              "与「为过长度门加几个字」性质相反。")
        print("  ★★ 同一段话可能有手稿版与印本版两个措辞（Blackwell #118 实例）"
              "——不带坐标，读者无从知道引的是哪一版。")
        return 1
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workspace", type=pathlib.Path, help="人物工作区（含 evals/cases.jsonl）")
    ap.add_argument("--round-dir", type=pathlib.Path, help="本轮落盘目录")
    ap.add_argument("--candidate", help="{case_id: 候选答案} 的 JSON")
    ap.add_argument("--baseline", help="{case_id: 基线答案} 的 JSON")
    ap.add_argument("--prefix", default="blind", help="落盘文件名前缀")
    ap.add_argument("--baseline-source", default="self-authored-strawman",
                    help="基线来源，透传给泄题门。★ bare-model-run 免长度两条的**拦**"
                         "（仍照报），其余照旧硬拦——见待裁定 ⑭")
    ap.add_argument("--skip-leak-check", action="store_true",
                    help="★ 只在判据本身出问题时用；跳过就等于把泄题拖到判完之后才发现")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return selftest()
    if not (a.workspace and a.round_dir and a.candidate and a.baseline):
        ap.error("要么 --self-test，要么给齐 --workspace/--round-dir/--candidate/--baseline")

    ev = a.workspace / "evals"
    if not ev.is_dir():
        print(f"✗ **{ev} 不在——工作区路径给错了，没落盘**"); return 3
    cases = {}
    for line in (ev / "cases.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line); cases[r["case_id"]] = r["prompt"]

    cand = json.loads(pathlib.Path(a.candidate).read_text(encoding="utf-8"))
    base = json.loads(pathlib.Path(a.baseline).read_text(encoding="utf-8"))
    payload, key = assign(cases, cand, base)

    # ★★★ `--round-dir round2` 这种**裸相对名**必须落在工作区里，不是当前目录。
    #   实测代价：在技能目录下跑，它把载荷与**盲判 key** 写进了
    #   `registry/codex/persona-distiller/round2/`——**已发布的产品目录**，并被我提交进 git。
    #   两位评委各自独立报了这件事（一位在约定位置找不到载荷，自己重新生成了一份）。
    if not a.round_dir.is_absolute() and len(a.round_dir.parts) == 1:
        a.round_dir = a.workspace / "evals" / a.round_dir
        print(f"★ --round-dir 是裸名，已解析到工作区内：{a.round_dir}")
    a.round_dir.mkdir(parents=True, exist_ok=True)
    _payload_path = a.round_dir / f"{a.prefix}_blind_payload.json"
    _payload_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")

    # ★★ v0.0.0.117：**冻结指令要求按某个字段打分，而载荷里没有那个字段。**
    #   Mendel #125 第 1 轮**派发之后**才发现：两席都写「给 `candidate` 和 `baseline`
    #   各打一个分」，而载荷里是 `A`／`B`；席 D 另有五处提到 `rubric`，载荷里根本没有。
    #   **派发之后就改不得了**：改指令＝中途换尺子，补载荷＝两席看到不同的东西。
    #   ★ **只报不拦**——「该不该有 rubric」是待裁定 ④，一个不能自行选的口子。
    #     本处只保证：这个不一致**不会再到派发之后才被看见**。
    # ★★ v0.0.0.119：**有几道题，rubric 明说克制才对——而评委看不到 rubric。**
    #   Mendel #125 实测：`gm-known-01` 的 rubric 写「答『不确定／记不得』**可接受**」，
    #   候选照做，**得 −0.1800**；`gm-boundary-01` 写「**顺着答下去即为失败**」，
    #   基线顺着答了，**赢 0.18**。两份冻结 rubric 判候选对、基线错，评委两者都看不到。
    #   ★ **只报不拦，且绝不把这些题剔出去**——去掉不利子集再报数就是为凑数放宽判据。
    # ★★★ v0.0.0.122：**引文真伪，必须在派发之前核——因为评委核不了。**
    #   `check_quote_integrity` 早就支持 `--answers`，**但全项目没有一处这样调用它**。
    #   Mendel #125 补跑：6 条德文引文，**1 条未命中**——
    #   `Einleitende Bemerkungen`，而语料里印的是 OCR 讹字 `Hinleitende Bemerkungen`。
    #   **我把 OCR 错字改正后当逐字引文用了**，正是该件文件头点名的那一类。
    #   两席都没抓到（席 D 反而给了那一题全场最高的 0.93）——**评委没有语料，核不了。**
    _qi = pathlib.Path(__file__).resolve().parent / "check_quote_integrity.py"
    _src = pathlib.Path(a.workspace) / "references" / "sources"
    if _qi.is_file() and a.candidate and _src.is_dir():
        print("\n── 引文真伪：拿答案里的原文去语料里逐字找（**只报不拦**）──")
        _rq = subprocess.run([sys.executable, str(_qi), "--answers", a.candidate,
                              "--cache", str(_src)], capture_output=True, text=True)
        for _ln in _rq.stdout.splitlines():
            if any(k in _ln for k in ("引文", "未命中", "⚠", "语料")):
                print("  " + _ln.strip())
        print("  ★ 未命中不等于伪造，但**「改了 OCR 错字再当逐字引文用」也落在这里**——"
              "那一类是真问题，且评委查不出来。")

    # ★★ v0.0.0.121：**每修一处引入一处，连续两轮四个实例**（见 _fix-introduces-new-defect.md）。
    #   R2 修 contrast 引入「至今未见数字化本」；R3 修 task-completion 引入「同一卷」而全篇无卷次。
    #   修完之后**没有任何一步去验改的那一处自己站不站得住**，要等下一轮评委再抓。
    _oc = pathlib.Path(__file__).resolve().parent / "check_answer_overclaims.py"
    if _oc.is_file() and a.candidate and pathlib.Path(a.candidate).is_file():
        print("\n── 候选答案的两类过度断言（**只报不拦**）──")
        _ro = subprocess.run([sys.executable, str(_oc), "--answers", a.candidate],
                             capture_output=True, text=True)
        try:
            _io = json.loads(_ro.stdout)
            _no = _io.get("**报出**", 0)
            if _no:
                for _h in _io.get("逐条", []):
                    print(f"  ⚠ {_h['case_id']}　{_h['类']}（{_h['触发词']}）")
                    print(f"      {_h['句']}")
            else:
                print("  ✓ 已故人物谈当下／指代悬空　各 0 处")
            print("  ★ 本件判不了：「原文写的」后面的断言是否真在引文里、译文是否比原文宽")
        except Exception as _eo:                                 # noqa: BLE001
            print(f"  ⚠ 输出无法解析，**未核（不是通过）**：{_eo}")

    _here0 = pathlib.Path(__file__).resolve().parent
    _rw = _here0 / "check_restraint_without_remainder.py"
    _cases = pathlib.Path(a.workspace) / "evals" / "cases.jsonl"
    if _rw.is_file() and _cases.is_file():
        print("\n── rubric 要求克制、而评委看不到 rubric（**只报不拦**）──")
        _r0 = subprocess.run([sys.executable, str(_rw), "--cases", str(_cases)],
                             capture_output=True, text=True)
        try:
            _i0 = json.loads(_r0.stdout)
            _n0 = _i0.get("**rubric 把克制指定为正确行为的题**", 0)
            print(f"  {_n0} / {_i0.get('题数')} 题的 rubric 把克制指定为正确行为")
            for _h in _i0.get("逐题（按实测 delta 升序）", []):
                print(f"      {_h['套组']}")
            if _n0:
                print("      ★ 评委按题面判「谁更合题」，**克制在这些题上天然吃亏**。"
                      "这是待裁定 ④，本件不替它选。")
        except Exception as _e0:                                 # noqa: BLE001
            print(f"  ⚠ 输出无法解析，**未核（不是通过）**：{_e0}")

    _here = pathlib.Path(__file__).resolve().parent
    _jm = _here / "check_judge_prompt_matches_payload.py"
    _pdir = _here.parent / "references" / "pipeline" / "judge_prompts"
    _prompts = sorted(_pdir.glob("seat_*.md")) if _pdir.is_dir() else []
    if _jm.is_file() and _prompts:
        print("\n── 评委指令 vs 载荷字段（**只报不拦**）──")
        _argv = [sys.executable, str(_jm), "--payload", str(_payload_path)]
        for _pp in _prompts:
            _argv += ["--prompt", str(_pp)]
        _r = subprocess.run(_argv, capture_output=True, text=True)
        try:
            _info = json.loads(_r.stdout)
            _n = _info.get("**对不上的字段数**", 0)
            if _n:
                print(f"  ⚠⚠ **指令引到而载荷里没有的字段：{_n} 处**")
                for _row in _info.get("逐席", []):
                    if _row.get("**载荷里没有的**"):
                        print(f"      {_row['指令']}：{_row['**载荷里没有的**']}")
                print("      ★ 评委拿不到这些字段，只能按题面自拟判据。"
                      "**派发前知道，比派发后才发现强。**")
            else:
                print("  ✓ 指令引到的字段，载荷里都有")
        except Exception as _exc:                                # noqa: BLE001
            print(f"  ⚠ 输出无法解析，**未核（不是通过）**：{_exc}")
    (a.round_dir / f"{a.prefix}_blind_key.json").write_text(
        json.dumps(key, ensure_ascii=False, indent=1), encoding="utf-8")

    # ★ 两侧一起落进工作区——**门看不见的东西，等于没做。**
    cand_path = ev / "judge_payload.v1.json"
    base_path = ev / "baseline.v1.json"
    cand_path.write_text(json.dumps({c: cand[c] for c in cases}, ensure_ascii=False, indent=1),
                         encoding="utf-8")
    base_path.write_text(json.dumps({c: base[c] for c in cases}, ensure_ascii=False, indent=1),
                         encoding="utf-8")
    print(f"★ 候选与基线两侧已落进 {ev}/——发布门现在看得见它们")

    # 轮次之间 A/B 映射必须一致，否则各轮不可比
    # ★★★★ 2026-08-07 修：原先写 `f"{a.prefix}_blind_key.json"`，**用本轮的前缀去上一轮找**。
    #   而前缀按轮次变（`--prefix whitworth-152-round2`），第 1 轮的 key 叫
    #   `whitworth-152-round1_blind_key.json`——**名字永远对不上，这道门永远变不绿**。
    #   ★ 它给出的诊断还是错的：印「多半是 --round-dir 落在了工作区之外」，
    #     而 round_dir 明明就在工作区里（上一行刚打印过解析后的绝对路径）。
    #     **一个永远红、且把人指向错误病因的门，比没有这道门更贵。**
    #     [[a-red-that-can-never-turn-green-is-not-a-signal]]
    #   按形状找，不按前缀找——同一条纪律见 `find_seat_file`。
    _r1_dir = a.round_dir.parent / "round1"
    _r1_hits = sorted(_r1_dir.glob("*_blind_key.json"))
    r1 = _r1_hits[0] if _r1_hits else _r1_dir / f"{a.prefix}_blind_key.json"
    # ★★ 找不到第 1 轮的 key 时**不许沉默跳过**：
    #   `is_file()` 假就整条检查一句话不说地没跑，
    #   而沉默的跳过会被读成通过（见 [[empty-default-swallows-unknown]]）。
    if a.round_dir.name != "round1" and not r1.is_file():
        print(f"✗ **{_r1_dir} 里没有 *_blind_key.json**")
        print("  轮次之间 A/B 映射是否一致**未核**——这不是通过。")
        print("  第 1 轮的 key 不在应在的地方；**中止**（不是「跳过这道检查」）。")
        return 5
    if a.round_dir.name != "round1" and r1.is_file():
        if json.loads(r1.read_text(encoding="utf-8")) != key:
            print("✗ **A/B 映射与第 1 轮不一致——中止（轮次之间不可比）**"); return 3
        print("A/B 映射与第 1 轮逐条一致 ✅")
        # ★★ 把这个设计的**代价**一起说出来——上面那句注释只写了收益。
        #   ★ 翻转率**由判据算**，不是我写死的一句话：
        #     check_blind_rounds_independent 此前从未被任何代码调用过。
        rk = HERE / "check_blind_rounds_independent.py"
        if rk.is_file():
            q = subprocess.run([sys.executable, str(rk), "--keys", str(r1),
                                str(a.round_dir / f"{a.prefix}_blind_key.json")],
                               capture_output=True, text=True)
            for line in (q.stdout or "").splitlines():
                if line.strip():
                    print("  " + line.strip())
        else:
            print("  ⚠ check_blind_rounds_independent.py 不在，**翻转率未核（不是通过）**")
        print("    两席已实测能靠格式/长度认出候选侧（Barton 100%，四人合计 91%），"
              "**第 1 轮认出的边在后两轮原样有效**——")
        print("    所以「三轮 delta 逐轮向零」这类跨轮趋势"
              "**不宜当三个独立样本读**。（权衡不是缺陷，待裁定 ⑦）")

    r = length_report(cases, cand, base)
    print(f"{r['n']} 对；A 侧是候选的题数 "
          f"{sum(1 for v in key.values() if v['A'] == 'candidate')}")
    print(f"★ **候选均长 {r['cand']:.0f}，基线均长 {r['base']:.0f}"
          f"——候选比基线长 {r['ratio_pct']:+.0f}%**")
    print("  （A/B 两侧的均长差**不是**该看的数：候选被均分到两侧，"
          "两侧接近是分配方式的产物）")
    print("★ 题号已改为不透明编号 q-01…（套组归属只在 key 里）")

    # ★★★ 出戏门（**派发之前只报不拦**）——Thomson #129 的教训
    #   那一轮判出 +0.4516（16/16 三轮不变），而事后回扫发现
    #   **10/16 道 rubric 把「本库没收录 X」这类资料层状态指定为正确答案**，
    #   与同一份指令第 3 条「扣局部出戏」直接冲突——**判据在惩罚守住人物、奖励破框**。
    #   回扫 Carver #127 同样是 6/16 = 38%：**不是个例，是这套 rubric 写法的通病。**
    #   ★ 这道门若当时就在，Thomson 那 10 条**在派发第 1 轮之前**就会被看见。
    #   **只报不拦**：出不出戏要不要改，取决于人物与用例，判据不替人做主。
    frame_checker = HERE / "check_persona_frame_break.py"
    if frame_checker.exists():
        print("\n── 出戏门（**只报不拦**；rubric 与产物一起查）──")
        argv = [sys.executable, str(frame_checker), str(cand_path)]
        # 逐题 rubric 在人物自己的冻结指令里（`judge_prompts/v1.md` 的 `### <case_id>` 段）
        rubrics = {}
        v1 = a.workspace / "judge_prompts" / "v1.md"
        if v1.is_file():
            rubrics = extract_rubrics(v1.read_text(encoding="utf-8"), sorted(cases))
            if rubrics is None:
                print("✗ **抽不出逐题 rubric——中止。**\n"
                      f"   {v1} 里找不到已知的小标题（{'／'.join(RUBRIC_MARKERS)}），\n"
                      "   **且不许退回「拿整份文件当 rubric」**——那样判据查的是别的东西。")
                return 4
        rub_json = a.round_dir / "_rubrics_for_frame_check.json"
        if rubrics:
            rub_json.write_text(json.dumps(rubrics, ensure_ascii=False), encoding="utf-8")
            argv += ["--rubrics", str(rub_json)]
            # ★★★ 再写一份**按载荷编号**索引的，给喂判据的席位用。
            #   起因：席 E 在 Sorby #133 第 3 轮自己报上来——
            #   「载荷的 case_id 顺序与 v1.md 的逐题标准排列不一致，
            #     **我先按题面文字把每题对回它那条标准再打分**」。
            #   载荷用不透明编号 `q-01…` 且**按 case_id 字母序排**，而 v1.md 按套组顺序写；
            #   评委手上没有揭盲键，只能**照题面文字手工做这个 join**。
            #   ★ 手工 join 一旦错位，那一席的分就是拿错标准打的，**而且不会报错**。
            #     席 E 发现了并自己纠正；同轮席 D 一个字没提——**我无从知道它有没有错位。**
            #   ★★ 写出这份**不泄任何东西**：它只说「q-07 对应哪条标准」，
            #     而 A/B 哪侧是候选仍然只在 `*_blind_key.json` 里。
            by_qid = {q: rubrics.get(v.get("case_id"), "")
                      for q, v in (key or {}).items()}
            if any(by_qid.values()):
                (a.round_dir / "rubrics_by_qid.json").write_text(
                    json.dumps(by_qid, ensure_ascii=False, indent=1), encoding="utf-8")
                print("  ✓ 已按载荷编号另写一份 `rubrics_by_qid.json`——"
                      "**喂判据的席位直接用它，不要再手工对题面**")
        else:
            print("  ⚠ 没找到 `judge_prompts/v1.md` 的逐题 rubric——**只查了产物，没查判据**")
        fp = subprocess.run(argv, capture_output=True, text=True)
        try:
            fr = json.loads(fp.stdout)
            if fr.get("模式") == "analytic":
                print("  本判据不适用（第三人称分析型产物）")
            else:
                na, nr = len(fr.get("产物出戏", {})), len(fr.get("判据要求出戏", {}))
                print(f"  产物出戏 {na} 题；**判据把资料层答案指定为正确 {nr} 题**")
                if nr:
                    print("  ★★★ **根因在判据不在产物**——只改产物下一轮还会长回来。"
                          "参照：Thomson #129 = 10/16、Carver #127 = 6/16。")
                    print(f"  判据出问题的题：{sorted(fr['判据要求出戏'])[:8]}")
                if na:
                    print(f"  产物出戏的题：{sorted(fr['产物出戏'])[:8]}")
        except Exception:                                        # noqa: BLE001
            print("  ⚠ 出戏门输出解析失败，**未核**（不是通过）")

    # ★★★ rubric 抄答案门（**只报不拦**）——RUNBOOK 第五十四种的判据
    #   Robertson #97 两席评委独立指出「rubric 规定了答案的措辞」，**记了但没落成判据**，
    #   于是它又回来两次：Carver #127（已入库）7/16 = 44%、Thomson #129 8/16 = 50%。
    #   共有长串越多，这道题的分越是在量「字符串对不对得上」而不是能力。
    copy_checker = HERE / "check_rubric_copies_answer.py"
    if copy_checker.exists() and rubrics:
        print("\n── rubric 抄答案门（**只报不拦**）──")
        # ★★ 两侧都传：中译/压缩层要拿**基线侧**当趋同下限
        #   （写判据时基线还不存在，抄它在物理上不可能）。
        cp = subprocess.run([sys.executable, str(copy_checker),
                             "--rubrics", str(rub_json), "--answers", str(cand_path),
                             "--answers-b", str(base_path)],
                            capture_output=True, text=True)
        try:
            cr = json.loads(cp.stdout)
            n = cr["**rubric 抄了答案原文的题**"]
            print(f"  {n}/{cr['题数']}（{cr['占比']}）题的 rubric 里有答案的**英文原字符串**；"
                  f"共有 {cr['共有字符合计']} 字")
            cz = cr.get("★★★ **中译/压缩层（冻结指令要求，原先完全没查）**") or {}
            if cz:
                print(f"  ★★★ **中译/压缩层：{cz['越线题数']}/{cr['题数']}（{cz['占比']}）**"
                      "——冻结指令写着「中译与压缩也算抄」，上面那一层只比英文，对它们全盲")
                for cid, sides in list(cz.get("逐题", {}).items())[:4]:
                    for side, d in sides.items():
                        if d.get("越线"):
                            q = d.get("**判据引号内被答案照抄的短语**") or []
                            tag = f"引号回声 {[x['短语'] for x in q]}" if q else f"串 {d['中文连续串'][:2]}"
                            print(f"    · {cid} [{side}] {tag}")
            if n:
                worst = sorted(cr["逐题"].items(),
                               key=lambda kv: -kv[1]["占答案的比例"])[:3]
                for cid, d in worst:
                    print(f"    · {cid}  占该答案 {d['占答案的比例']:.0%}  "
                          f"{d['最长的三段'][0][:56]}")
                print("  ★★ 参照：Carver #127 = 7/16、Thomson #129 = 8/16。"
                      "**这几题的分要按「字符串对齐」读，不是能力。**")
        except Exception:                                        # noqa: BLE001
            print("  ⚠ 输出解析失败，**未核**（不是通过）")

    # ★★ 生成即判：泄题必须拦在派发评委之前
    if locator_gate(cand_path):                  # ★ 在早退之前——它不该被 skip 掉
        return 1
    if a.skip_leak_check:
        print("\n⚠ **跳过了表面特征泄题门**——"
              "Barton #117 三轮判分正是因为这道门没在派发前跑而全部作废")
        return 0
    # ── 位次混杂（**只报不拦**，同「长度混杂」一类，待裁定 ⑱）──
    # ★ 此前没有任何一处报过这个数：Adams #131 的 14/16 是我用肉眼看出来的，
    #   不是门告诉我的。**判据不说话，就等于不存在。**
    n_a = sum(1 for v in key.values() if v["A"] == "candidate")
    n = len(key)
    lead = max(n_a, n - n_a)
    print(f"\n── 位次混杂（**只报不拦**）──\n"
          f"A 侧是候选 {n_a}/{n}，一边倒的那侧占 {lead}/{n} = {lead/max(n,1):.0%}")
    if lead / max(n, 1) >= 0.75:
        print(f"  ⚠ **位次与系统相关度 {lead/max(n,1):.0%}**——"
              f"评委若对「先读到的那一侧」有任何偏好，**会直接灌进 delta**。\n"
              f"    ★ 这不是编造出来的风险：同一类混杂已在长度上实测过（裁定 ⑭）。\n"
              f"    ★★ 报数时必须带上这句话：**这一轮的 delta 有位次混杂。**\n"
              f"    修法是 `assign(..., balanced=True)` 强制 8/8；"
              f"**本轮没有改**——改了会让已派发轮次的 A/B 变号。")
    else:
        print("  ✓ 位次没有一边倒（<75%）")

    print("\n── 表面特征泄题门（**派发之前必须过**）──")
    p = subprocess.run([sys.executable, str(LEAK_CHECKER),
                        "--candidate", str(cand_path), "--baseline", str(base_path),
                        "--baseline-source", a.baseline_source],
                       capture_output=True, text=True)
    print(p.stdout.rstrip())
    # ★★★★ 2026-08-07：`capture_output=True` **把 stderr 一起吞了**。
    #   实测形态：我给 `--baseline-source` 传了散文，而它是四选一的枚举，
    #   argparse 把「invalid choice」写进 stderr、退出码 2 ——
    #   于是这道门印出的是**一个空的小节**，紧接着一句
    #   「✗ 不许派发。**重写答案，不要改门。**」
    #   **答案一个字都没问题，问题在我的命令行参数。**
    #   照那句话去做的人会去重写一批好答案，而真因一个字都看不到。
    #   [[empty-default-swallows-unknown]]：空输出被读成「门跑了且失败了」。
    if (p.stderr or "").strip():
        print("  ── 判据的 stderr（**以前这一段是被吞掉的**）──")
        for _l in p.stderr.rstrip().splitlines():
            print("  │ " + _l)
    if p.returncode != 0:
        if not (p.stdout or "").strip():
            # 门自己一句话没说 ≠ 门判了不合格
            print("\n✗ **这道门没有产出任何判读就失败了**（退出码 "
                  f"{p.returncode}）——**先看上面的 stderr，多半是调用方式不对，"
                  "不是答案有问题。** 在排除这一点之前，不要动答案。")
            return 1
        print("\n✗ **这份载荷不许派发评委。** 判出来的 delta 不能当作盲判结果引用——"
              "重写答案，不要改门。")
        return 1

    # ── holdout 泄漏门（v0.0.0.90）────────────────────────────────────────
    # ★★★★ 此前**没有任何判据看过答案与 holdout 的关系**：
    #   `check_holdout_mention` 扫的是建模者可读文件，`check_holdout_overlap` 比的是
    #   holdout ↔ train 语料，**两件都不看答案**。
    #   于是「候选答题子代理偷读了 holdout」唯一的证据是它自己写的 `__incident__`——
    #   而自述不是证据（[[self-report-is-not-evidence]]）。
    #   ★ 它**用基线答案做负对照**：基线从没读过任何文件，
    #     基线也说得出来的词不算 holdout 独有。
    # ── 答案里的数字回核（v0.0.0.91，**只报不拦**）────────────────────────
    #   Gantt #156 第 1 轮：候选在「不该给数」的那题主动补了 `千分之四`–`千分之六`
    #   并说「这是我核过的东西」，而全语料里没有这个数。
    #   ★ 本件**不拦**：`找不到` 可能是合理的（人物生年、常识年份），
    #     `核不了` 更只是「要人看」。**它缩小人要看的范围，不替人下判断。**
    nc = HERE / "check_answer_numbers_in_corpus.py"
    print("\n── 答案里的数字回核（**只报不拦**）──")
    if not nc.is_file():
        print("⚠ check_answer_numbers_in_corpus.py 不在，**答案数字未核（不是通过）**")
    else:
        n = subprocess.run([sys.executable, str(nc), "--workspace", str(a.workspace),
                            "--answers", str(cand_path)], capture_output=True, text=True)
        print((n.stdout or "").rstrip())
        if (n.stderr or "").strip():
            for _l in n.stderr.rstrip().splitlines():
                print("  │ " + _l)

    hl = HERE / "check_answer_holdout_leak.py"
    print("\n── holdout 泄漏门（专名与数字，带基线负对照）──")
    if not hl.is_file():
        print("⚠ check_answer_holdout_leak.py 不在，**holdout 泄漏未核（不是通过）**")
    else:
        #   ★★★★ 2026-08-11（Shewhart #165）：**必须把题面也传进去，否则 known 题 100% 误报。**
        #     每一道 known 题都必然点名 holdout 那部作品——那正是 known 题的定义
        #     （「1928 年你在《富兰克林研究所学报》上那篇…」）。
        #     实测：候选答的是「里面**没有** 1928 年的《富兰克林研究所学报》文章」，
        #     **它在说那篇不在它手上，而门把这句判成了泄漏**，并拦下了整份载荷。
        #     同批误报的还有 `Bell System Technical Journal`／`Study`／`Through`／
        #     `Transactions`——那些**在产物里本来就有**（判据侧已加产物排除集）。
        _prompts = a.workspace / "evals" / "cases.jsonl"
        _hl_argv = [sys.executable, str(hl), "--workspace", str(a.workspace),
                    "--candidate", str(cand_path), "--baseline", str(base_path)]
        if _prompts.is_file():
            _hl_argv += ["--prompts", str(_prompts)]
        h = subprocess.run(_hl_argv, capture_output=True, text=True)
        print((h.stdout or "").rstrip())
        if (h.stderr or "").strip():
            for _l in h.stderr.rstrip().splitlines():
                print("  │ " + _l)
        if h.returncode != 0:
            if not (h.stdout or "").strip():
                print("\n✗ **这道门没有产出任何判读就失败了**（退出码 "
                      f"{h.returncode}）——**先看上面的 stderr**，多半是调用方式不对。")
            else:
                print("\n✗ **候选答案里有只可能来自 holdout 的东西，这份载荷不许派发。**")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
