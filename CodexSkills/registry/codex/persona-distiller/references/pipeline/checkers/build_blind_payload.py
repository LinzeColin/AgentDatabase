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
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
LEAK_CHECKER = HERE / "check_answer_surface_leak.py"


def assign(cases: dict, cand: dict, base: dict) -> tuple:
    """→ (payload, key)。A/B 由 `sha256(case_id) % 2` 决定，**与内容无关、可复现**。"""
    payload, key = [], {}
    for i, cid in enumerate(sorted(cases), 1):
        if cid not in cand or cid not in base:
            raise SystemExit(f"✗ **缺答案：{cid}**——不是「这题跳过」，是载荷不完整")
        flip = int(hashlib.sha256(cid.encode()).hexdigest(), 16) % 2
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

    print(f"\n{'✓ 自测全过' if not fails else f'✗ **{len(fails)} 项未过**'}")
    return 0 if not fails else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workspace", type=pathlib.Path, help="人物工作区（含 evals/cases.jsonl）")
    ap.add_argument("--round-dir", type=pathlib.Path, help="本轮落盘目录")
    ap.add_argument("--candidate", help="{case_id: 候选答案} 的 JSON")
    ap.add_argument("--baseline", help="{case_id: 基线答案} 的 JSON")
    ap.add_argument("--prefix", default="blind", help="落盘文件名前缀")
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

    a.round_dir.mkdir(parents=True, exist_ok=True)
    (a.round_dir / f"{a.prefix}_blind_payload.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
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
    r1 = a.round_dir.parent / "round1" / f"{a.prefix}_blind_key.json"
    if a.round_dir.name != "round1" and r1.is_file():
        if json.loads(r1.read_text(encoding="utf-8")) != key:
            print("✗ **A/B 映射与第 1 轮不一致——中止（轮次之间不可比）**"); return 3
        print("A/B 映射与第 1 轮逐条一致 ✅")

    r = length_report(cases, cand, base)
    print(f"{r['n']} 对；A 侧是候选的题数 "
          f"{sum(1 for v in key.values() if v['A'] == 'candidate')}")
    print(f"★ **候选均长 {r['cand']:.0f}，基线均长 {r['base']:.0f}"
          f"——候选比基线长 {r['ratio_pct']:+.0f}%**")
    print("  （A/B 两侧的均长差**不是**该看的数：候选被均分到两侧，"
          "两侧接近是分配方式的产物）")
    print("★ 题号已改为不透明编号 q-01…（套组归属只在 key 里）")

    # ★★ 生成即判：泄题必须拦在派发评委之前
    if a.skip_leak_check:
        print("\n⚠ **跳过了表面特征泄题门**——"
              "Barton #117 三轮判分正是因为这道门没在派发前跑而全部作废")
        return 0
    print("\n── 表面特征泄题门（**派发之前必须过**）──")
    p = subprocess.run([sys.executable, str(LEAK_CHECKER),
                        "--candidate", str(cand_path), "--baseline", str(base_path)],
                       capture_output=True, text=True)
    print(p.stdout.rstrip())
    if p.returncode != 0:
        print("\n✗ **这份载荷不许派发评委。** 判出来的 delta 不能当作盲判结果引用——"
              "重写答案，不要改门。")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
