#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**这台仪器分得出 +0.03 吗？** ——用两侧逐字未动的题量它自己的噪声。

## 为什么有这件

Mendel #125 第 2 轮真 delta **+0.0278**，quick 门 **+0.0300**，
差 **0.0022**。我差一点就把这句写成「只差 0.0022」。

**去核之后：那一轮有 7 题两侧文本逐字未动**——同样两席、同样冻结指令、
同样载荷，**它们的 delta 本该完全不变**。实测却动了：

```
known             −0.0300 → −0.1800   （**−0.1500**）
token-efficiency  +0.1500 → +0.2950   （**+0.1450**）
...
逐题两轮差的 sd = 0.0928  →  16 题均值的 SE ≈ **0.0164**
```

**quick 门 +0.03 只有 1.83 个 SE。**
「差 0.0022 没过」这句话没有意义——**分不出「过了」和「等于零」。**

## 它做什么，不做什么

- **做**：找出**两轮之间两侧文本逐字未动**的题，用它们的 delta 变动
  估计单题噪声，推出总 delta 的 SE，并把三档门换算成 SE 的倍数。
- **不做**：**不判产物过没过门**。它判的是**「这个判断本身可不可信」**。
  ★ 也**不改门**——门是多少是待裁定的事，本件只把不确定度摆出来。
- **不做**：不在只有一轮、或没有一题逐字未动时给结论——那时它说
  **「未核」**，不说「通过」。

## 射程边界（**必须一起读**）

- 两轮只能给**一个**差值样本／题，**两点定不了方差**；这是下限意义上的估计。
- 逐字未动的题往往只有几题，**sd 自身的不确定度很大**
  （n=7 时 sd 的 95% 区间约 [0.6, 2.2]×）。本件会把这个区间一起报出来。
- 假定逐字未动的题与改写过的题**同分布**、题与题**独立**——**都未验证**。
- **★ 三轮取最好会抬高假过率**，本件会在轮数 ≥3 时提醒，但不计算它。
"""
import argparse
import json
import math
import pathlib
import statistics
import sys

# 与 common.py 的 PROFILE_THRESHOLDS 对齐；此处只用于**换算成 SE 倍数**，不做判定。
GATES = {"quick": 0.03, "standard": 0.05, "deep": 0.07}
# n → 卡方分位推出的 sd 置信区间倍数（0.025 / 0.975），只列常用的小 n。
_SD_CI = {2: (0.45, 31.9), 3: (0.52, 6.29), 4: (0.57, 3.73), 5: (0.60, 2.87),
          6: (0.62, 2.45), 7: (0.64, 2.20), 8: (0.66, 2.04), 9: (0.68, 1.92),
          10: (0.69, 1.83), 12: (0.71, 1.69), 16: (0.74, 1.55), 20: (0.76, 1.46)}


def _sd_ci(n: int) -> tuple:
    if n in _SD_CI:
        return _SD_CI[n]
    keys = sorted(_SD_CI)
    return _SD_CI[min(keys, key=lambda k: abs(k - n))]


def load_round(d: pathlib.Path) -> dict:
    """读一轮：载荷、key、各席打分。缺哪样就返回 None。"""
    pay = next(iter(sorted(d.glob("*_blind_payload.json"))), None)
    key = next(iter(sorted(d.glob("*_blind_key.json"))), None)
    judges = sorted(p for p in d.glob("*_judge_*.json"))
    if not (pay and key and judges):
        return {}
    items = {i["case_id"]: i for i in json.loads(pay.read_text(encoding="utf-8"))}
    return {"name": d.name, "items": items,
            "key": json.loads(key.read_text(encoding="utf-8")),
            "judges": {p.name: json.loads(p.read_text(encoding="utf-8")) for p in judges}}


def normalize(a_raw: float, b_raw: float) -> tuple:
    """量纲归一：任一侧 > 1.0 即判为 0–10 制。**与 assemble_judge_results.normalize 同口径。**

    ★★ 本件第一版**没有这一步**，于是对 0–10 制的人物把 SE 报大了十倍：
      koch/lister/pasteur/virchow/nightingale/osler 六人都是 0–10 制
      （实测 rk_judge_D.json 最小 6.00 最大 9.30），只有 Mendel 是 0–1 制。
      我拿「SE≈0.05」去和 Mendel 的 0.0164 比，**差点得出「Mendel 是低异常」的反结论**。
      这正是 `eval-artifacts-have-five-schemas` 记过的那个坑，**而我在自己的判据里又踩了一次**。
    """
    if a_raw > 1.0 or b_raw > 1.0:
        return a_raw / 10.0, b_raw / 10.0
    return a_raw, b_raw


def case_delta(rd: dict, q: str):
    """一题在这一轮的 delta（候选 − 基线），跨席取均值。取不到返回 None。"""
    k = rd["key"].get(q)
    if not k:
        return None
    cand = "A" if k.get("A") == "candidate" else "B"
    base = "B" if cand == "A" else "A"
    vals = []
    for scores in rd["judges"].values():
        row = scores.get(q)
        if isinstance(row, (list, tuple)) and len(row) >= 2:
            row = {"A": row[0], "B": row[1]}
        if isinstance(row, dict) and cand in row and base in row:
            try:
                a, b = normalize(float(row["A"]), float(row["B"]))
            except (TypeError, ValueError):
                return None
            vals.append((a - b) if cand == "A" else (b - a))
    return statistics.mean(vals) if vals else None


def resolution(round_dirs: list) -> dict:
    rounds = [r for r in (load_round(pathlib.Path(d)) for d in round_dirs) if r]
    if len(rounds) < 2:
        return {"状态": "**未核（不是通过）**：可用的轮次不足两轮"}

    frozen, drifts = [], []
    a, b = rounds[-2], rounds[-1]
    for q in sorted(set(a["items"]) & set(b["items"])):
        ia, ib = a["items"][q], b["items"][q]
        if ia.get("A") != ib.get("A") or ia.get("B") != ib.get("B"):
            continue
        if a["key"].get(q) != b["key"].get(q):          # A/B 映射变了，不可比
            continue
        da, db = case_delta(a, q), case_delta(b, q)
        if da is None or db is None:
            continue
        frozen.append(q)
        drifts.append(db - da)

    n_cases = len(set(a["items"]) & set(b["items"]))
    out = {"比的两轮": [a["name"], b["name"]], "两轮共有的题数": n_cases,
           "**两侧逐字未动的题数**": len(frozen), "逐题两轮差": [round(x, 4) for x in drifts]}
    if len(drifts) < 2:
        out["状态"] = ("**未核（不是通过）**：两侧逐字未动的题不足两道，量不出噪声。"
                       "★ 这不表示噪声小，只表示没量。")
        return out

    sd = statistics.stdev(drifts)
    se_case = sd / math.sqrt(2)                 # 两轮之差的方差 = 2×单轮方差
    se_mean = se_case / math.sqrt(n_cases) if n_cases else float("nan")
    lo, hi = _sd_ci(len(drifts))
    out["逐题两轮差的 sd"] = round(sd, 4)
    out["单题噪声 SE"] = round(se_case, 4)
    out["**总 delta 的 SE**"] = round(se_mean, 4)
    out["★ SE 自身的区间"] = f"约 [{se_mean*lo:.4f}, {se_mean*hi:.4f}]（n={len(drifts)}，sd 不确定度很大）"
    out["三档门相当于几个 SE"] = {
        g: (f"{v/se_mean:.2f} SE" + ("　**← 分不出**" if v < 2 * se_mean else ""))
        for g, v in GATES.items()} if se_mean > 0 else {}
    out["★ 口径"] = "**本件不判产物过没过门**，只判「那个判断可不可信」；也不改门。"
    out["★ 射程"] = ("两点定不了方差，这是下限估计；假定逐字未动的题与改写过的题同分布、"
                     "题与题独立——**均未验证**。")
    if len(rounds) >= 3:
        out["★★ 提醒"] = (f"已有 {len(rounds)} 轮。**多轮取最好会抬高假过率**——"
                          f"门若只有约 {GATES['quick']/se_mean:.1f} 个 SE，跑三轮取其一"
                          f"的实际过门概率远高于名义值。")
    return out


def verdict_line(delta: float, se: float) -> list:
    """把一个已经算出来的 delta 摆进它的不确定度里。**不判过没过。**"""
    lines = [f"  观测 delta = {delta:+.4f}　SE ≈ {se:.4f}　→ 约 {abs(delta)/se:.2f} 个 SE",
             f"  95% 区间约 [{delta-1.96*se:+.4f}, {delta+1.96*se:+.4f}]"]
    for g, v in GATES.items():
        inside = delta - 1.96 * se <= v <= delta + 1.96 * se
        if inside:
            lines.append(f"  ★ {g} 门 {v:+.4f} **落在区间内 → 过没过，这台仪器分不出来**")
    if delta - 1.96 * se <= 0 <= delta + 1.96 * se:
        lines.append("  ★ 0 也落在区间内 → **也不能说它比基线好**")
    return lines


def self_test() -> int:
    ok = True

    def chk(msg, cond):
        nonlocal ok
        ok = ok and bool(cond)
        print(("  ✓ " if cond else "  ✗ ") + msg)

    import tempfile

    def mk(root, name, items, scores_by_seat, key=None):
        d = root / name
        d.mkdir(parents=True, exist_ok=True)
        (d / "x_blind_payload.json").write_text(json.dumps(items, ensure_ascii=False),
                                                encoding="utf-8")
        key = key or {i["case_id"]: {"A": "candidate", "B": "baseline",
                                     "case_id": i["case_id"]} for i in items}
        (d / "x_blind_key.json").write_text(json.dumps(key, ensure_ascii=False), encoding="utf-8")
        for seat, sc in scores_by_seat.items():
            (d / f"x_judge_{seat}.json").write_text(json.dumps(sc, ensure_ascii=False),
                                                    encoding="utf-8")
        return d

    with tempfile.TemporaryDirectory() as t:
        root = pathlib.Path(t)
        items = [{"case_id": f"q-{i:02d}", "question": "q", "A": f"a{i}", "B": f"b{i}"}
                 for i in range(1, 9)]

        print("── ★★ 反向对照①：两轮打分**完全一样** → sd=0，且不许说「通过」 ──")
        sc = {f"q-{i:02d}": {"A": 0.8, "B": 0.7} for i in range(1, 9)}
        r1 = mk(root, "r1", items, {"D": sc}); r2 = mk(root, "r2", items, {"D": sc})
        out = resolution([r1, r2])
        chk(f"sd={out.get('逐题两轮差的 sd')}", out.get("逐题两轮差的 sd") == 0.0)
        chk("★ 输出里没有『通过』字样", "通过" not in json.dumps(out, ensure_ascii=False)
            or "不是通过" in json.dumps(out, ensure_ascii=False))

        print("── ★★ 反向对照②：两侧文本**全改过** → 说「未核」，不说噪声小 ──")
        items2 = [{"case_id": f"q-{i:02d}", "question": "q", "A": f"AA{i}", "B": f"BB{i}"}
                  for i in range(1, 9)]
        r3 = mk(root, "r3", items2, {"D": sc})
        out2 = resolution([r1, r3])
        chk(f"{out2.get('状态','')[:30]}", "未核" in str(out2.get("状态", "")))
        chk("★ 明说『不表示噪声小』", "不表示噪声小" in str(out2.get("状态", "")))

        print("── ★★ 反向对照③：**只有一轮** → 未核 ──")
        chk(f"{resolution([r1]).get('状态','')[:24]}", "未核" in str(resolution([r1]).get("状态", "")))

        print("── ★★ 反向对照④：噪声大到盖过 quick 门 → **必须标『分不出』** ──")
        sc2 = {f"q-{i:02d}": {"A": 0.8 + (0.3 if i % 2 else -0.3), "B": 0.7}
               for i in range(1, 9)}
        r4 = mk(root, "r4", items, {"D": sc2})
        out4 = resolution([r1, r4])
        chk(f"quick → {out4['三档门相当于几个 SE']['quick']}",
            "分不出" in out4["三档门相当于几个 SE"]["quick"])

        print("── ★ 反向对照⑤：**A/B 映射变了的题不许拿来当「未动」** ──")
        badkey = {i["case_id"]: {"A": "baseline", "B": "candidate", "case_id": i["case_id"]}
                  for i in items}
        r5 = mk(root, "r5", items, {"D": sc}, key=badkey)
        chk(f"逐字未动数 = {resolution([r1, r5])['**两侧逐字未动的题数**']}",
            resolution([r1, r5])["**两侧逐字未动的题数**"] == 0)

        print("── ★ 反向对照⑥：轮数 ≥3 时**必须提醒多轮取最好** ──")
        chk("提醒在", "抬高假过率" in str(resolution([r1, r4, r2]).get("★★ 提醒", "")))

        print("── ★★★ 反向对照⑦：**0–10 制与 0–1 制必须给出同一个 SE** ──")
        #   本件第一版漏了量纲归一，对 0–10 制的人把 SE 报大十倍，
        #   差点据此得出「Mendel 是低异常」的反结论。
        sc01 = {f"q-{i:02d}": {"A": 0.8 + (0.05 if i % 3 else -0.05), "B": 0.7}
                for i in range(1, 9)}
        sc10 = {k: {"A": round(v["A"] * 10, 4), "B": round(v["B"] * 10, 4)}
                for k, v in sc01.items()}
        base = mk(root, "n0", items, {"D": sc})
        a01 = resolution([base, mk(root, "n1", items, {"D": sc01})])["**总 delta 的 SE**"]
        a10 = resolution([base, mk(root, "n2", items, {"D": sc10})])["**总 delta 的 SE**"]
        chk(f"0–1 制 SE={a01}　0–10 制 SE={a10}　**必须相等**", abs(a01 - a10) < 1e-9)

        print("── ★ 反向对照⑧：**列表式 [分, 分] 的打分也要读得进来** ──")
        scl = {f"q-{i:02d}": [sc01[f"q-{i:02d}"]["A"], sc01[f"q-{i:02d}"]["B"]]
               for i in range(1, 9)}
        al = resolution([base, mk(root, "n3", items, {"D": scl})])["**总 delta 的 SE**"]
        chk(f"列表式 SE={al}（与字典式相等）", abs(al - a01) < 1e-9)

        print("── ★ 反向对照⑨：verdict_line 只摆区间，**不下过/不过的结论** ──")
        ln = " ".join(verdict_line(0.0278, 0.0164))
        chk("含『分不出来』", "分不出来" in ln)
        chk("★ 不含『✅ 过』这类判定", "✅" not in ln)

    print("\n" + ("✓ 自测全过" if ok else "✗ 自测未过"))
    return 0 if ok else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--round-dir", action="append", default=[],
                    help="轮次目录，按时间顺序给两次以上")
    ap.add_argument("--delta", type=float, help="已算出的真 delta，给了就把它摆进区间里")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if len(a.round_dir) < 2:
        ap.error("要么 --self-test，要么给至少两个 --round-dir")
    info = resolution(a.round_dir)
    print(json.dumps(info, ensure_ascii=False, indent=2))
    se = info.get("**总 delta 的 SE**")
    if a.delta is not None and se:
        print("\n── 把观测值摆进它的不确定度里（**不判过没过**）──")
        print("\n".join(verdict_line(a.delta, se)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
