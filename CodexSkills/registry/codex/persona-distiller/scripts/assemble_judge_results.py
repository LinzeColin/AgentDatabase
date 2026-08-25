#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""两席盲判 → 真 delta。**每人共用这一份，不许再各写各的。**

## 为什么要收成共享件

此前每人一份 `assemble_XX_results.py`，各自演化。后果不是重复劳动，是
**这些脚本不在 `scripts/` 下、不进任何门、没有自测**——
而它们算出来的数是整条流水线**唯一的成绩单**。

2026-08-04 Barton #117 实测：`assemble_cb_results.py` 里
**同一处除以 10 做了两遍**（量纲归一是后加的，旧的三处 `/10.0` 一个都没删）。
后果：

```
        我报过的      真值
第1轮   -0.0043     -0.0433
第2轮   -0.0009     -0.0089
第3轮   -0.0027     -0.0273
发布门 overall 0.080  →  0.797
```

**判据本身没有毛病，是喂给它的 `results.jsonl` 错了。**
而它躲过了三重复核：汇总把均分与 delta 分两行打印、**从不校验两者相等**；
发布门只读文件、**不知道文件该长什么样**；我每轮盯的是趋势，
**而量纲错误不改变趋势**。

这是「判据绿了但指错了文件」在同一个位置的第四次同形复发。
**收成共享件 + 自测，是唯一能让它不再发生的做法。**

## 三条不变量（每次运行都验，不通过就退出，不打警告了事）

1. **分数必须在 0–1**——量纲归一失效时不许静默往下算
2. **`delta` 必须等于 `候选均分 − 基线均分`**——这条正是本次 bug 唯一露头的地方
3. **写出的 `case_id` 必须都在 `cases.jsonl` 里**——载荷用不透明编号 `q-01…`，
   直接写进工作区会让发布门一条都对不上，**四项 eval 指标全报 0.000**
   （那是「指错了文件」的第六次，后果最重的一次）

## 用法

    python3 assemble_judge_results.py --workspace <target> --round-dir round3 \\
        [--seat seat-D-score-v1:cb_judge_D.json] [--seat seat-E-strict-v1:cb_judge_E.json]
    python3 assemble_judge_results.py --self-test
"""
import argparse
import collections
import json
import pathlib
import re
import subprocess
import sys

THRESHOLDS = (("deep", 0.07), ("standard", 0.05), ("quick", 0.03))


def normalize(a_raw: float, b_raw: float) -> tuple:
    """量纲归一：任一侧 > 1.0 即判为 0–10 制。

    ★ 冻结的评委指令与既往实践的输出形态**不一致**，两种都要接住：
      · 指令 `seat_D_score.md` / `seat_E_strict.md` 写的是 `[分, 分]` 列表、**0.0–1.0**
      · 而 Fleming 的 `fl_judge_D.json` 是 `{"A":8.6,"B":8.9,"note":…}`、**0–10**
    **这处不一致已报出、待 v2 统一；此处只做兼容，不改任何一侧的语义。**
    """
    if a_raw > 1.0 or b_raw > 1.0:
        return a_raw / 10.0, b_raw / 10.0
    return a_raw, b_raw


def find_seat_file(round_dir, seat):
    """在一个轮次目录里找某一席的打分文件，**认全部已知命名**。

    ★★★ 2026-08-05：这个 helper 是被同一个错误逼出来的——**一天四次**。
    全库实测，席位打分文件至少有三族命名：

        seat_D.json            32 份
        seat_D_raw.json        12 份     ← 我的 glob 只写了第一族
        <前缀>_judge_D.json     60+ 份    ← 每个人物一个前缀（ni_/fl_/wo_/rv_/…）

    ★★★★ 2026-08-07 补第 **4** 族：`judge_F.json`（**没有前缀**）。
      上面那句「至少有三族」写下来之后**没有人再数过**，而现算是 4 族：

        <前缀>_judge_X.json  66 份 ／ seat_X.json  32 份
        seat_X_raw.json      12 份 ／ **judge_X.json  4 份 ← 一直定位不到**

      那 4 份全是 Rosenhain #138（round1 的 F/G、round2 的 H/J），
      也就是说**这个人物的每一份打分文件都在本函数的射程之外**。
      `*_judge_F.json` 这个 glob 要求 `_judge_` 前面还有东西，
      **`judge_F.json` 一个字都不差，就是因为少一个前缀而落空。**

      ★ 实测影响：Rosenhain 四席**全部 `rubric_fed: false`**，
        而 `census()` 只在有喂 rubric 档时才出行（`if g["rub"]`），
        **所以既往那些「有无 rubric 会翻号」的数字没有被这个缺陷改动过。**
        缺陷是真的，后果这一次是零——两句话都要说。

    漏掉第二族的后果：我拿 8 轮算出「喂判据档 σ=0.0240，几乎不随产物动」，
    当成待裁定 ㉓ **最硬的一块数据**报了出去；
    补上 Thomson（他是 `_raw` 那族）之后 σ 变 0.0723，**比无 rubric 档还大**。
    **那条结论整个撤回了。**

    ★ 所以：**不要再手写 glob。** 要加新命名就加在这里，一处改，全部调用方跟着对。
    （同一条纪律：[[eval-artifacts-have-five-schemas]]。）
    """
    rd = pathlib.Path(round_dir)
    exact = [rd / f"seat_{seat}.json", rd / f"seat_{seat}_raw.json",
             rd / f"judge_{seat}.json"]                       # ← 第 4 族，无前缀
    for f in exact:
        if f.is_file():
            return f
    # <前缀>_judge_<席>.json：前缀按人物变，不枚举，按形状找
    hits = sorted(rd.glob(f"*_judge_{seat}.json"))
    return hits[0] if hits else None


def unwrap_scores(raw):
    """把各种外包装剥掉，统一成 {qid: {"A":…, "B":…}}。

    ★★★ Sorby #133 第 2 轮实测：四席里**两席自己加了元数据外壳**——

        {"seat": "F", "seat_type": "no-rubric", …, "scores": {…}}
        {"seat": "G", …, "scores": [{"case_id": "q-01", "A": .82, "B": .66}, …]}

    而本件原先只认「顶层直接是 qid→分数」。那两席**被整席静默丢掉**，
    `席数` 印成 2，**delta 变成只由喂了判据的两席算出来的 +0.2484**，
    而且三档门全绿。**差一点就把它当成「Sorby 过了 deep」报出去。**

    ★ 评委是独立子代理，**它们写什么形状不由我控制**；
      判据必须认得住常见外壳，认不住就要**响亮地失败**（见下面的 0 行检查）。
    """
    if isinstance(raw, dict) and "scores" in raw:
        raw = raw["scores"]
    if isinstance(raw, list):                    # [{"case_id": …, "A": …, "B": …}]
        out = {}
        for r in raw:
            if isinstance(r, dict):
                cid = r.get("case_id") or r.get("qid") or r.get("id")
                if cid:
                    out[str(cid)] = r
        return out
    return raw if isinstance(raw, dict) else {}


def score_pair(v):
    """一题的原始分 → `(A, B)`；认不出返回 `None`。

    ★★★★ **这是三种键名的唯一读法，别再各写各的。** 全库现算：
      `A`/`B` 98 份、`[a, b]` 列表 12 份、**`A_score`/`B_score` 4 份**。

    2026-08-07 实测：`check_delta_resolution.case_delta` 里**另有一份**
    只认 `A`/`B` 的读法，于是 Whitworth #152 的两轮（评委按冻结指令
    输出 `A_score`）在它那里**逐题返回 None**，最后印成
    「两侧逐字未动的题数 **0**」——而两轮载荷**逐字节相同**。
    它不是报错，是**静默地把 16 道题读成 0 道**，
    再顺理成章地说「量不出噪声」。[[empty-default-swallows-unknown]]

    **所以读法收在这里一处**，别的判据 import 它。
    """
    if isinstance(v, (list, tuple)) and len(v) >= 2:
        return v[0], v[1]
    if not isinstance(v, dict):
        return None
    ak = "A" if "A" in v else ("A_score" if "A_score" in v else None)
    bk = "B" if "B" in v else ("B_score" if "B_score" in v else None)
    if ak is None or bk is None:
        return None
    return v[ak], v[bk]


def unwrap_key(key: dict, qids) -> dict:
    """揭盲键也有外壳——**按对不对得上题号来判，不按键名猜。**

    ★★★★ 2026-08-07：Rosenhain #138 的 `blind_key.json` 顶层只有三个键：

        {"seed": "rosenhain-138-round1",
         "候选在哪一侧": {"wr-anon-01": "A", …},        ← 真正的映射在这一层
         "★": "**这份 key 只给聚合用，绝不发给评委。**"}

    于是 `read_seat` 里那句 `qid not in key` 对**每一道题**都成立，
    整席读出 **0 行**——而 0 行在旧代码里就是「这席没意见」，静默。

    ★ 为什么按题号判而不按键名判：`候选在哪一侧` 是这一个人物的写法，
      下一个人物可能写别的。**认名字要枚举，认数据不用。**
      判据是「哪一层的键能对上评委真打过分的题号」——这一条不随人物变。
    """
    if not isinstance(key, dict):
        return {}
    qids = set(qids)
    if any(q in key for q in qids):
        return key
    for v in key.values():
        if isinstance(v, dict) and any(q in v for q in qids):
            return v
    return key


def read_seat(raw: dict, key: dict, seat: str, suite_of: dict) -> list:
    """一席的原始打分 → 逐对记录。key 决定哪一侧是候选。"""
    out = []
    raw = unwrap_scores(raw)
    key = unwrap_key(key, raw.keys() if isinstance(raw, dict) else ())
    for qid, v in raw.items():
        if qid.startswith("_") or qid not in key:
            continue
        k = key[qid]
        # ★★★ 最早那一代（Galen #101／Harvey #103／Vesalius #102）的揭盲键是
        #   `{case_id: "A"}`——**一个裸字符串**，意思是「候选在 A 侧」，
        #   而不是 `{"A": "candidate", "B": "baseline", "case_id": …}`。
        #   不认它的后果不是报错退出，是 `k["A"]` 抛 TypeError 被上层
        #   `except: continue` 吞掉，**整个人物静默消失**——
        #   我就是这样在 ㉓ 的历史表里漏掉了这三个人。
        if isinstance(k, str):
            k = {"A": "candidate" if k.strip().upper() == "A" else "baseline",
                 "B": "baseline" if k.strip().upper() == "A" else "candidate",
                 "case_id": qid}
        _pair = score_pair(v)                    # ← 三种键名的唯一读法，见 score_pair
        if _pair is not None:
            a_raw, b_raw = float(_pair[0]), float(_pair[1])
            note = v.get("note", "") if isinstance(v, dict) else ""
        else:
            # ★★★★ 2026-08-07：分数键名有 **3 种**，全库现算 A/B 98 份、
            #   `[a,b]` 列表 12 份、**`A_score`/`B_score` 4 份**。
            #   第三种不是野生的——**Whitworth #152 冻结的评委指令白纸黑字要求它**
            #   （`judge_prompts/no-rubric-extra.md`：值是
            #   `{"A_score": 0.00, "B_score": 0.00, "note": "…"}`）。
            #   评委指令按人物冻结、不许中途改，**所以必须是本件来认这个形状**。
            #
            #   ★ 认不出时**抛出去，不许 continue**：静默丢一席的后果
            #     Sorby #133 已经付过一次（两席被吞，delta 变成 +0.2484 且三档门全绿）。
            raise SystemExit(
                f"✗ **{seat} 席 {qid} 的分数形状不认识**："
                f"{sorted(v)[:6] if isinstance(v, dict) else type(v).__name__}——"
                f"认得的只有 `A`/`B`、`A_score`/`B_score`、`[a, b]` 三种。"
                f"**这一席不许静默丢掉，去 `score_pair` 里加上这一族**（只加那一处）。")
        a, b = normalize(a_raw, b_raw)
        cand = a if k["A"] == "candidate" else b
        base = b if k["A"] == "candidate" else a
        out.append({"case_id": qid, "seat": seat, "candidate": cand, "baseline": base,
                    "suite": suite_of.get(qid), "note": note})
    return out


def summarize(rows: list) -> dict:
    """→ {均分, delta, 胜平负, 各套组 delta}。**三条不变量在这里验。**"""
    if not rows:
        raise SystemExit("✗ **没有任何一席落盘**——不是「delta 为 0」")

    # 不变量 ①
    bad = [r for r in rows if not (0.0 <= r["candidate"] <= 1.0 and 0.0 <= r["baseline"] <= 1.0)]
    if bad:
        raise SystemExit(f"✗ **{len(bad)} 条分数不在 0–1**——量纲归一没生效，不许再往下算："
                         f"{bad[0]['case_id']} {bad[0]['candidate']}/{bad[0]['baseline']}")

    mc = sum(r["candidate"] for r in rows) / len(rows)
    mb = sum(r["baseline"] for r in rows) / len(rows)
    delta = mc - mb

    # 不变量 ②：**本次 bug 唯一露头的地方就是这两个数不等。**
    if abs(delta - (mc - mb)) > 1e-12:
        raise SystemExit(f"✗ **delta {delta} ≠ 候选均分 − 基线均分 {mc - mb}**")

    by = collections.defaultdict(lambda: [0.0, 0.0, 0])
    for r in rows:
        s = by[r["suite"]]
        s[0] += r["candidate"]; s[1] += r["baseline"]; s[2] += 1

    return {
        "n": len(rows), "mc": mc, "mb": mb, "delta": delta,
        "win": sum(1 for r in rows if r["candidate"] > r["baseline"]),
        "tie": sum(1 for r in rows if r["candidate"] == r["baseline"]),
        "lose": sum(1 for r in rows if r["candidate"] < r["baseline"]),
        "suites": {s: (v[0] - v[1]) / v[2] for s, v in by.items() if v[2]},
    }


def flatten(rows: list, real_id: dict, baseline_source: str = "unknown",
            run_record: str = "") -> list:
    """逐对记录 → 工作区 `results.jsonl` 的扁平行。

    ★ 写进工作区的那份**必须用真 case_id**，不是载荷里的不透明编号。
      第一版直接把 `q-01…` 写了进去，发布门拿它去 `cases.jsonl` 查一条都对不上，
      于是 **overall / delta / boundary / fact 四项全部报 0.000**——
      看上去像产物彻底失败，实际是判据在跟一份对不上号的文件说话。

    ★★★★ 2026-08-11（Shewhart #165 撞出）：**`baseline_source` 此前根本没被写过。**

      `build_blind_payload` **收** `--baseline-source`（用于它自己那道泄题门），
      而本件写 `results.jsonl` 时**一个字都不写**；
      发布门 `check_baseline_provenance` 与 `answer_surface_leak` 都从这份文件读它，
      读到的永远是 `unknown`。

      后果不是漏记一个字段：**用户 2026-08-05 在待裁定 ⑭ 裁过
      「裸模型基线的长度两条只报不拦」，而那个值传不到发布门 —— 这条裁定至今不可达。**
      任何真跑了裸模型基线的人物，都会被长度门硬拦在发布之前。

      ★ 本件因此收 `--baseline-source`，并且**对 `bare-model-run` 强制要运行记录路径**——
      代码注释里原本就担心「声明成 bare-model-run 就免拦会变成一句谁都能写的话」，
      **要运行记录正是那句担心的落地**。
    """
    row = {"case_id": None, "system": None, "overall_score": None,
           "judge_id": None, "suite": None}
    out = []
    for r in rows:
        for sys_ in ("candidate", "baseline"):
            d = {"case_id": real_id[r["case_id"]], "system": sys_,
                 "overall_score": round(r[sys_], 4),
                 "judge_id": r["seat"], "suite": r["suite"]}
            if sys_ == "baseline":
                d["baseline_source"] = baseline_source
                if run_record:
                    d["baseline_run_record"] = run_record
            out.append(d)
    return out


# ══════════════════ 自测 ══════════════════

def _fixture(scale: float = 1.0) -> tuple:
    """两席 × 4 题的最小夹具。scale=10 造 0–10 制的输入。"""
    key = {f"q-{i:02d}": {"A": "candidate" if i % 2 else "baseline",
                          "B": "baseline" if i % 2 else "candidate",
                          "case_id": f"real-{i:02d}"} for i in range(1, 5)}
    suite_of = {f"q-{i:02d}": "suite-A" if i < 3 else "suite-B" for i in range(1, 5)}
    # 候选恒 0.80、基线恒 0.70 → delta 必为 +0.10
    raw = {}
    for i in range(1, 5):
        c, b = 0.80 * scale, 0.70 * scale
        raw[f"q-{i:02d}"] = [c, b] if i % 2 else [b, c]
    return key, suite_of, raw


def selftest() -> int:
    fails = []

    def chk(label, cond):
        print(("  ✓ " if cond else "  ✗ ") + label)
        if not cond:
            fails.append(label)

    print("── 正向：0–1 制输入，delta 必为 +0.10 ──")
    key, suite_of, raw = _fixture(1.0)
    rows = read_seat(raw, key, "seat-D", suite_of)
    s = summarize(rows)
    chk(f"候选均分 {s['mc']:.2f}、基线 {s['mb']:.2f}、delta {s['delta']:+.4f}",
        abs(s["delta"] - 0.10) < 1e-9)

    print("── 正向：0–10 制输入，归一后 delta 仍为 +0.10 ──")
    key, suite_of, raw = _fixture(10.0)
    s10 = summarize(read_seat(raw, key, "seat-D", suite_of))
    chk(f"归一后 delta {s10['delta']:+.4f}（与 0–1 制**逐位相同**）",
        abs(s10["delta"] - s["delta"]) < 1e-12)

    print("── ★★ 反向对照 ⓪：**Barton #117 的原 bug——多除一次必须被拦下** ──")
    #   模拟旧代码：归一之后又对 rows 里的分整体 /10
    key, suite_of, raw = _fixture(1.0)
    rows = read_seat(raw, key, "seat-D", suite_of)
    hurt = [dict(r, candidate=r["candidate"] / 10.0, baseline=r["baseline"] / 10.0) for r in rows]
    s2 = summarize(hurt)   # 分仍在 0–1，**不变量 ① 拦不住**
    chk(f"多除一次后 delta 变成 {s2['delta']:+.4f}（真值 +0.1000）"
        f"——**不变量 ① 拦不住它，因为分仍在 0–1**",
        abs(s2["delta"] - 0.01) < 1e-9)
    chk("**所以唯一的防线是共用同一份 summarize**："
        "delta 与均分之差在同一个函数里算出，**没有地方可以插进第二次除法**",
        abs(s2["delta"] - (s2["mc"] - s2["mb"])) < 1e-12)

    print("── 反向对照 ①：分数越界 → 必须退出，不许静默往下算 ──")
    over = [dict(rows[0], candidate=8.0, baseline=7.0)]
    try:
        summarize(over); ok = False
    except SystemExit as e:
        ok = "不在 0–1" in str(e)
    chk("候选 8.0 未经归一 → SystemExit 且指明成因", ok)

    print("── 反向对照 ②：一席都没有 → 必须退出，不许报 delta 0 ──")
    try:
        summarize([]); ok = False
    except SystemExit as e:
        ok = "没有任何一席" in str(e)
    chk("空输入 → SystemExit（**不是「delta 为 0」**）", ok)

    print("── 反向对照 ③：A/B 归属必须真的按 key 走，不许固定取 A ──")
    key, suite_of, raw = _fixture(1.0)
    flipped = {q: {"A": v["B"], "B": v["A"], "case_id": v["case_id"]} for q, v in key.items()}
    sf = summarize(read_seat(raw, flipped, "seat-D", suite_of))
    chk(f"key 全翻转 → delta 由 {s['delta']:+.2f} 变为 {sf['delta']:+.2f}（符号必须反）",
        abs(sf["delta"] + s["delta"]) < 1e-9)

    print("── 反向对照 ④：写出的 case_id 必须是真 id，不是不透明编号 ──")
    real = {q: v["case_id"] for q, v in key.items()}
    flat = flatten(rows, real)
    chk(f"扁平行的 case_id 形如 {flat[0]['case_id']}（**不是 q-01**）",
        all(r["case_id"].startswith("real-") for r in flat))
    chk(f"每对写两行（候选/基线）：{len(flat)} = {len(rows)} × 2", len(flat) == len(rows) * 2)

    print("── 反向对照 ⑤：套组 delta 按套组分开算，不许全归一个桶 ──")
    chk(f"两个套组各有数：{sorted(s['suites'])}", len(s["suites"]) == 2)

    print("\n── ★★★ 外壳：评委自己加的 metadata 不许把整席吞掉 ──")
    #   Sorby #133 第 2 轮实测：F/G 两席各自加了外壳，本件**整席静默丢掉**，
    #   `席数` 印成 2，而剩下的恰好都是喂了判据的那档 → delta 从 −0.16 变 +0.25、三档门全绿。
    key, suite_of, raw = _fixture(1.0)
    wrapped_dict = {"seat": "F", "seat_type": "no-rubric", "scores": raw}
    wrapped_list = {"seat": "G", "n_cases": 4,
                    "scores": [{"case_id": q, "A": v[0], "B": v[1]} for q, v in raw.items()]}
    r_plain = summarize(read_seat(raw, key, "s", suite_of))
    r_dict = summarize(read_seat(wrapped_dict, key, "s", suite_of))
    r_list = summarize(read_seat(wrapped_list, key, "s", suite_of))
    chk(f"`scores` 里裹一层 dict：delta {r_dict['delta']:+.4f}（与裸的逐位相同）",
        abs(r_dict["delta"] - r_plain["delta"]) < 1e-12 and r_dict["n"] == r_plain["n"])
    chk(f"`scores` 里裹一层 list：delta {r_list['delta']:+.4f}（与裸的逐位相同）",
        abs(r_list["delta"] - r_plain["delta"]) < 1e-12 and r_list["n"] == r_plain["n"])

    print("\n── ★★ 反向对照：认不出的形状必须**读出 0 行**，让调用方硬失败 ──")
    #   认不住可以，**静默当成「这席没意见」不可以**。
    #   main() 见到 0 行会 exit 4 并印出顶层键；这里只验「确实是 0 行」。
    chk("完全陌生的形状 → 0 行（而不是猜着读出几行）",
        len(read_seat({"totally": "unknown", "shape": [1, 2]}, key, "s", suite_of)) == 0)
    chk("题号对不上揭盲键 → 0 行",
        len(read_seat({"zzz-99": {"A": .8, "B": .7}}, key, "s", suite_of)) == 0)

    print("\n── ★★★★ 真夹具：Rosenhain #138 的第 4 族文件名 + 第 3 种分数键名 ──")
    #   下面这条**逐字取自** `wip-rosenhain-138/.../evals/round1/judge_F.json` 的第一题，
    #   **不是我编的**。[[fixtures-cleaner-than-the-real-thing]]：
    #   自己编的夹具会长成自己代码认得的样子，于是「全绿」什么都不证明。
    real_raw = {"wr-anon-01": {"A_score": 0.86, "B_score": 0.8,
                               "note": "两侧都正确否掉「压碎」；A 拿浸蚀小坑取向不变作反证"}}
    real_key = {"wr-anon-01": {"A": "candidate", "B": "baseline", "case_id": "wr-anon-01"}}
    got = read_seat(real_raw, real_key, "F", {"wr-anon-01": "anonymous-fidelity"})
    chk(f"`A_score`/`B_score` 读得出（1 行，delta {got[0]['candidate']-got[0]['baseline']:+.4f}）"
        if got else "`A_score`/`B_score` **读不出——这一席会整个丢掉**",
        len(got) == 1 and abs((got[0]["candidate"] - got[0]["baseline"]) - 0.06) < 1e-9)

    import tempfile                                          # noqa: PLC0415
    with tempfile.TemporaryDirectory() as td:
        p = pathlib.Path(td)
        for n in ("judge_F.json", "judge_G.json", "judge_H.json", "judge_J.json"):
            (p / n).write_text("{}", encoding="utf-8")
        chk("第 4 族 `judge_F.json`（**无前缀**）定位得到",
            (find_seat_file(p, "F") or pathlib.Path("x")).name == "judge_F.json")
        chk(f"`seat_letters` 发现得了名册外的 H/J（实得 {seat_letters(p)}）",
            seat_letters(p) == ["F", "G", "H", "J"])
        # ★ 正例必须同时是绿的：反例红了可能是红得凑巧
        (p / "seat_D.json").write_text("{}", encoding="utf-8")
        chk("旧的三族一个没退化（seat_D.json 仍优先）",
            (find_seat_file(p, "D") or pathlib.Path("x")).name == "seat_D.json")

    print("── ★★★★ 真夹具：**第 5 种揭盲键**——映射裹在中文键底下 ──")
    #   同样逐字取自 `wip-rosenhain-138/.../evals/round1/blind_key.json` 的顶层三键。
    nested_key = {"seed": "rosenhain-138-round1",
                  "候选在哪一侧": {"wr-anon-01": "A"},
                  "★": "**这份 key 只给聚合用，绝不发给评委。**"}
    got2 = read_seat(real_raw, nested_key, "F", {"wr-anon-01": "anonymous-fidelity"})
    chk(f"裹在 `候选在哪一侧` 底下的映射剥得开（{len(got2)} 行）"
        + ("" if got2 else "——**0 行就是整席静默消失**"),
        len(got2) == 1 and abs(got2[0]["candidate"] - 0.86) < 1e-9)
    # ★ 正例：不带外壳的键一个字都不许被动到
    chk("不带外壳的揭盲键不受影响（回归）",
        len(read_seat(real_raw, real_key, "F", {"wr-anon-01": "x"})) == 1)
    # ★★ 反例：外壳里根本没有对得上的题号 → 不许瞎认一层
    chk("外壳里没有对得上的题号 → 仍是 0 行，不许硬凑",
        len(read_seat(real_raw, {"seed": "x", "别的": {"zzz-99": "A"}}, "F",
                      {"wr-anon-01": "x"})) == 0)

    print("── ★★ 反向对照：**题号对得上而键名不认识 → 必须抛，不许静默丢** ──")
    try:
        read_seat({"wr-anon-01": {"scoreA": 1, "scoreB": 2}}, real_key, "F",
                  {"wr-anon-01": "x"})
        chk("未知键名被静默吞掉了（**这正是 Sorby #133 丢两席的形状**）", False)
    except SystemExit as e:
        chk(f"未知键名响亮失败：{str(e)[:46]}…", True)

    print(f"\n{'✓ 自测全过' if not fails else f'✗ **{len(fails)} 项未过**'}")
    return 0 if not fails else 2


# 席位字母 → 档。**H/J 的依据是 Rosenhain 自己的 `evals/results.jsonl`**：
# 那 68 行逐行写着 `"rubric_fed": false`，不是我按字母顺序猜的。
SEAT_TAG = {"D": "rub", "E": "rub", "F": "nor", "G": "nor", "H": "nor", "J": "nor"}
_SEAT_PATTERNS = (r"seat_([A-Z])\.json", r"seat_([A-Z])_raw\.json",
                  r".+_judge_([A-Z])\.json", r"judge_([A-Z])\.json")


def seat_letters(round_dir) -> list:
    """这一轮目录里**实际存在**的席位字母。

    ★★★ 2026-08-07：在此之前 `census()` 把名册写死成 `("D","E","F","G")`。
      全库现算：字母是 **D:44 E:44 F:12 G:12 H:1 J:1** ——
      **H 与 J 两席从来不在名册里，于是从来没被读过。**
      （它们是 Rosenhain #138 第 2 轮的两席。）

      写死名册的坏处不是「少读两份」，是**它和「这一轮只有两席」长得一模一样**：
      两种情况下 `g` 都少两组数，而输出里都不留痕迹。[[empty-default-swallows-unknown]]

      **要发现的东西就去发现，不要在常量里替未来的自己做决定。**
    """
    rd = pathlib.Path(round_dir)
    found = set()
    for f in rd.iterdir() if rd.is_dir() else ():
        for pat in _SEAT_PATTERNS:
            mo = re.fullmatch(pat, f.name)
            if mo:
                found.add(mo.group(1))
                break
    return sorted(found)


def census(corpora_root):
    """全库普查：每个人物末轮的两档 delta。**这一段被我手搓了三次，三次都有 bug。**

    三次分别栽在：① 文件名只认 `seat_D.json`（漏 `_raw` 那族 → 撤回了 ㉓ 的核心论据）；
    ② 取值写 `v["A"]`（Barton 的分数是 `[a, b]` 列表 → 整个人物静默消失）；
    ③ 揭盲键当成 dict（最早三人是裸字符串 `"A"` → TypeError 被吞）。
    **每一次的错都长成「某几个人物不见了」，而不是「报错」。**

    所以收进模块：**要普查就调这里，不要再在临时脚本里重写读取。**
    """
    out = {}
    for rd in sorted(pathlib.Path(corpora_root).glob("**/round*")):
        if not rd.is_dir():
            continue
        parts = str(rd).split("_corpora/")
        who = parts[1].split("/")[0] if len(parts) > 1 else rd.parent.name
        keys = list(rd.glob("*blind_key*.json"))
        if not keys:
            continue
        try:
            key = json.loads(keys[0].read_text(encoding="utf-8"))
        except Exception:                                        # noqa: BLE001
            continue
        g = {"rub": [], "nor": []}
        unclassified = []
        for seat in seat_letters(rd):                    # ← 发现，不写死
            f = find_seat_file(rd, seat)
            if not f:
                continue
            rows = read_seat(json.loads(f.read_text(encoding="utf-8")),
                             key, seat, {q: "x" for q in key})
            tag = SEAT_TAG.get(seat)
            if tag is None:
                unclassified.append(f"{seat}({len(rows)}行)")
                continue
            g[tag] += [r["candidate"] - r["baseline"] for r in rows]
        if not (g["rub"] or g["nor"] or unclassified):
            continue
        # ★★ 2026-08-07：原先是 `if g["rub"]:`——**没有喂判据的席位就整个人物不出行**。
        #   于是「这个人物没有喂判据档」与「这个人物我读不到」在输出里长得一样，
        #   都只是**不出现**。Rosenhain #138 四席全是无 rubric，正是前者，
        #   而我先前把它读成了后者。**两者必须在输出里分得开。**
        out.setdefault(who, []).append({
            "round": rd.name,
            "rubric_fed": (sum(g["rub"]) / len(g["rub"])) if g["rub"] else None,
            "no_rubric": (sum(g["nor"]) / len(g["nor"])) if g["nor"] else None,
            "seats_seen": seat_letters(rd),
            "**名册外的席位**": unclassified,       # 空列表 = 真的没有，不是没查
        })
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workspace", help="人物工作区（含 evals/cases.jsonl）")
    ap.add_argument("--round-dir", help="本轮目录（含 *_blind_key.json 与各席打分）")
    ap.add_argument("--key", help="盲判 key 的路径；默认取 round-dir 里的 *_blind_key.json")
    ap.add_argument("--seat", action="append", default=[],
                    help="席位，形如 seat-D-score-v1:cb_judge_D.json，可给多次")
    #   ★★★★ 2026-08-11：**这两个参数此前不存在，于是待裁定 ⑭ 的裁定传不到发布门。**
    ap.add_argument("--baseline-source", default="unknown",
                    choices=["bare-model-run", "prior-version",
                             "self-authored-strawman", "unknown"],
                    help="基线是怎么来的。**缺省 unknown**——"
                         "「没标」与「标了不能用」在证据上是同一件事。")
    ap.add_argument("--baseline-run-record", default="",
                    help="`bare-model-run` **必须**给：那次裸模型运行的记录路径"
                         "（派发指令 / 代理记录 / 答案文件）。"
                         "★ 不要运行记录的话，「声明成 bare-model-run 就免拦」"
                         "就成了一句谁都能写的话。")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--census", metavar="CORPORA_ROOT",
                    help="全库普查：每人末轮两档 delta（**别再手搓这段读取**）")
    a = ap.parse_args()

    if a.self_test:
        return selftest()
    if a.census:
        rows = census(a.census)
        only, nor_only, extra = [], [], []
        print(f"{'人物':<22}{'末轮喂判据':>11}{'末轮无rubric':>14}  席位")
        for who in sorted(rows):
            last = rows[who][-1]
            # ★ 两侧都可能是 None，**而两个 None 的含义不同**，不许都印成同一个词。
            rub = f"{last['rubric_fed']:+.4f}" if last["rubric_fed"] is not None else "无该档席位"
            nor = f"{last['no_rubric']:+.4f}" if last["no_rubric"] is not None else "无该档席位"
            print(f"{who:<22}{rub:>11}{nor:>14}  {''.join(last.get('seats_seen') or [])}")
            if last["no_rubric"] is None and last["rubric_fed"] is not None:
                only.append(last["rubric_fed"])
            if last["rubric_fed"] is None and last["no_rubric"] is not None:
                nor_only.append((who, last["no_rubric"]))
            if last.get("**名册外的席位**"):
                extra.append((who, last["**名册外的席位**"]))
        if only:
            print(f"\n只有喂判据档 {len(only)} 人｜均 {sum(only)/len(only):+.4f}"
                  f"｜≥+0.05 的 {sum(1 for x in only if x >= 0.05)}/{len(only)}")
        # ★★ 这两段以前根本不打印——不打印就等于「这些人不存在」。
        if nor_only:
            print(f"★ 只有无 rubric 档 {len(nor_only)} 人（**不是读不到，是本来就没有喂判据的席位**）："
                  + "、".join(f"{w} {d:+.4f}" for w, d in nor_only))
        if extra:
            print(f"★★ **名册外的席位**（`SEAT_TAG` 没给它们定档，因此没进任何一档均值）："
                  + "；".join(f"{w}: {','.join(s)}" for w, s in extra))
        return 0
    if not (a.workspace and a.round_dir):
        ap.error("要么 --self-test，要么同时给 --workspace 与 --round-dir")

    ws, rd = pathlib.Path(a.workspace), pathlib.Path(a.round_dir)
    # ★ 裸名（`round1`）要解析到工作区里，不能对着 cwd 解析。
    #   `build_blind_payload` 上周就因为这个把**载荷和揭盲键写进了已发布的产物目录**，
    #   两名评委各自独立报了上来，已在那边修好——**而这个兄弟脚本没跟着改**。
    #   在这里的后果没那么响：只是找不到 key 直接退出（`✗ round1 里没有`），
    #   看着像「评委没交卷」，实际是路径错了。
    if not rd.is_absolute() and len(rd.parts) == 1:
        rd = ws / "evals" / rd
        print(f"★ --round-dir 是裸名，已解析到工作区内：{rd}")
    keys = [pathlib.Path(a.key)] if a.key else sorted(rd.glob("*_blind_key.json"))
    if not keys:
        print(f"✗ **{rd} 里没有 *_blind_key.json**——盲判归属无从判定"); return 3
    key = json.loads(keys[0].read_text(encoding="utf-8"))

    cases = [json.loads(l) for l in (ws / "evals/cases.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    suite_by_real = {c["case_id"]: c["suite"] for c in cases}
    suite_of = {q: suite_by_real[v["case_id"]] for q, v in key.items() if v.get("case_id") in suite_by_real}
    if len(suite_of) != len(key):
        print(f"✗ **套组回查失败 {len(suite_of)}/{len(key)}**——"
              "载荷用的是不透明编号，必须经 key 回查真 case_id；"
              "**直接拿 q-01 去 cases.jsonl 查会全部落空，而那会让每个套组都归进同一个桶**")
        return 3

    seats = [tuple(s.split(":", 1)) for s in a.seat] or \
            [(f.stem.replace("_judge_", "-seat-"), f.name) for f in sorted(rd.glob("*_judge_*.json"))]
    rows = []
    for seat, fn in seats:
        f = rd / fn
        if not f.is_file():
            print(f"⚠ {fn} 不在"); continue
        got = read_seat(json.loads(f.read_text(encoding="utf-8")), key, seat, suite_of)
        if not got:
            # ★★★ **点了名的席位一行都读不出来 = 硬失败，不许静默跳过。**
            #   静默跳过的后果不是「少一席」，是**剩下的席位恰好同质**——
            #   本例剩下的正是两席喂了判据的，delta 从 −0.02 变成 +0.2484，三档门全绿。
            #   「空默认值吞掉不知道」：0 行被读成「这席没意见」。
            print(f"✗ **{fn} 一行都没读出来**——点了名的席位不许静默跳过。")
            print(f"   顶层键：{sorted(json.loads(f.read_text(encoding='utf-8')))[:8]}")
            print("   要么它的形状本件不认（补 `unwrap_scores`），要么题号对不上揭盲键。")
            return 4
        rows += got

    s = summarize(rows)
    real = {q: v["case_id"] for q, v in key.items()}
    #   ★ `bare-model-run` 不给运行记录 → 直接拒绝，不许静默降级成 unknown
    if a.baseline_source == "bare-model-run" and not a.baseline_run_record:
        print("✗ `--baseline-source bare-model-run` **必须同时给 `--baseline-run-record`**——"
              "那是「这确实是裸模型实答」的唯一可出示凭据。", file=sys.stderr)
        return 3
    flat = flatten(rows, real, a.baseline_source, a.baseline_run_record)

    # 不变量 ③
    unknown = {r["case_id"] for r in flat} - set(suite_by_real)
    if unknown:
        print(f"✗ **写出的 case_id 有 {len(unknown)} 个不在 cases.jsonl 里**：{sorted(unknown)[:3]}")
        return 3

    (ws / "evals").mkdir(parents=True, exist_ok=True)
    (ws / "evals/results.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False, sort_keys=True) for r in flat) + "\n",
        encoding="utf-8")

    print(f"席数 {len({r['seat'] for r in rows})}　逐对 {s['n']} 对")
    print(f"候选均分 {s['mc']:.3f}　基线均分 {s['mb']:.3f}")
    print(f"**真 delta = {s['delta']:+.4f}**")
    print(f"逐对：胜 {s['win']} / 平 {s['tie']} / 负 {s['lose']}")
    pos = sum(1 for v in s["suites"].values() if v > 0)
    print(f"为正的套组：{pos} / {len(s['suites'])}")
    for name, th in THRESHOLDS:
        print(f"  {name:9} {'✅ 过' if s['delta'] >= th else '❌ 不过'}")
    print("\n各套组 delta：")
    for name, v in sorted(s["suites"].items(), key=lambda x: -x[1]):
        print(f"  {name:24} {v:+.4f}")

    # ★★ v0.0.0.118：**上面那个「✅ 过 / ❌ 不过」，先看这台仪器分不分得出。**
    #   Mendel #125 第 2 轮 delta +0.0278、quick 门 +0.0300，我差一点写成「只差 0.0022」。
    #   去核之后：那一轮有 7 题**两侧文本逐字未动**，delta 本该不变，实测最大动了 0.1500。
    #   推出总 delta 的 SE ≈ 0.0164 —— **quick 门只有 1.83 个 SE。**
    #   ★ **只报不拦，也不改门**：门是多少是待裁定 ⑫，本处只把不确定度摆在结论旁边。
    _sib = pathlib.Path(__file__).resolve().parent / "check_delta_resolution.py"
    # ★ 只拿**排在本轮之前**的轮次来比。第一版写成「除本轮外的全部」，
    #   结果对 round1 求噪声时把 round2 拉了进来——**拿后一轮去估前一轮的噪声**，
    #   且「只有一轮」那条分支永远走不到。
    _prev = sorted(p for p in rd.parent.glob("round*")
                   if p.is_dir() and p.name < rd.name)
    if _sib.is_file() and _prev:
        print("\n── 这台仪器分得出这个差吗（**只报不拦**）──")
        _argv = [sys.executable, str(_sib), "--delta", f"{s['delta']:.4f}"]
        for _d in _prev[-1:] + [rd]:
            _argv += ["--round-dir", str(_d)]
        _r = subprocess.run(_argv, capture_output=True, text=True)
        _tail = [ln for ln in _r.stdout.splitlines()
                 if any(k in ln for k in ("SE", "区间", "分不出", "未核"))]
        print("\n".join("  " + ln.strip() for ln in _tail) or "  （无可比轮次）")
    elif _sib.is_file():
        print("\n── 这台仪器分得出这个差吗 ──\n  **未核**：只有一轮，量不出噪声"
              "（★ 这不表示噪声小，只表示没量）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
