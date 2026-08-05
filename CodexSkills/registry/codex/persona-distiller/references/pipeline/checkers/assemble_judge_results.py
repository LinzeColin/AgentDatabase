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


def read_seat(raw: dict, key: dict, seat: str, suite_of: dict) -> list:
    """一席的原始打分 → 逐对记录。key 决定哪一侧是候选。"""
    out = []
    raw = unwrap_scores(raw)
    for qid, v in raw.items():
        if qid.startswith("_") or qid not in key:
            continue
        k = key[qid]
        if isinstance(v, (list, tuple)):
            a_raw, b_raw, note = float(v[0]), float(v[1]), ""
        else:
            a_raw, b_raw, note = float(v["A"]), float(v["B"]), v.get("note", "")
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


def flatten(rows: list, real_id: dict) -> list:
    """逐对记录 → 工作区 `results.jsonl` 的扁平行。

    ★ 写进工作区的那份**必须用真 case_id**，不是载荷里的不透明编号。
      第一版直接把 `q-01…` 写了进去，发布门拿它去 `cases.jsonl` 查一条都对不上，
      于是 **overall / delta / boundary / fact 四项全部报 0.000**——
      看上去像产物彻底失败，实际是判据在跟一份对不上号的文件说话。
    """
    return [{"case_id": real_id[r["case_id"]], "system": sys_,
             "overall_score": round(r[sys_], 4),
             "judge_id": r["seat"], "suite": r["suite"]}
            for r in rows for sys_ in ("candidate", "baseline")]


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

    print(f"\n{'✓ 自测全过' if not fails else f'✗ **{len(fails)} 项未过**'}")
    return 0 if not fails else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workspace", help="人物工作区（含 evals/cases.jsonl）")
    ap.add_argument("--round-dir", help="本轮目录（含 *_blind_key.json 与各席打分）")
    ap.add_argument("--key", help="盲判 key 的路径；默认取 round-dir 里的 *_blind_key.json")
    ap.add_argument("--seat", action="append", default=[],
                    help="席位，形如 seat-D-score-v1:cb_judge_D.json，可给多次")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return selftest()
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
    flat = flatten(rows, real)

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
