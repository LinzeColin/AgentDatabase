#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**长度不许成为指认候选侧的信号。**

## 为什么有这道判据

盲判的前提是评委看不出哪一侧是候选。**如果候选每一题都比基线长，长度就是完美的泄题信号**
——评委不必读内容，数字数就能猜中，而且会猜中 32 次。

Lister #108 第 3 轮实测：候选比基线长 **+144%**，
**64 题里候选没有一道不比基线长**。席 D 在 `_overall` 里直接写：
「长的一侧在 32/32 全部命中同一个系统」。那一轮 delta +0.1292——
**这个数有多少是内容挣的、多少是长度送的，数据内部没有对照可以回答。**

## 判据（两条，缺一不可）

- **总体均长比 ≤ 1.30**——防整体靠篇幅取胜
- **候选更短的题 ≥ 25%**——只要有相当一部分题候选更短，
  「长的那侧是候选」这条启发式就会**错**四分之一以上，评委用不了它

**旧规则「逐题 ≤1.5 倍」实测防不住**：Lister R3 三十二题里 12 题本就 ≤1.5，
而候选仍 32/32 都更长。**新规则严于旧规则，不是放宽。**

## 它判不了什么

- **它不判「候选是不是靠篇幅赢的」**。两条都过，仍可能是篇幅在起作用——
  它只保证**长度指不出哪一侧是哪个系统**，不保证长度不影响分数。
  后者要靠等长基线，那会改变对照的定义，**是人的决定**。
- **中英混排下「字数」按字符算**，一个汉字与一个字母同权。
  同一人物内部前后一致即可比，**跨人物比这个数没有意义**。
"""
import argparse
import json
import pathlib
import sys

MAX_AGG = 1.30
MIN_SHORTER = 0.25


def measure(cand: dict, base: dict) -> dict:
    """→ {共有题数, 总体均长比, 候选更短的题数, 更短占比, 逐题最大比}。"""
    keys = [k for k in cand if k in base]
    if not keys:
        return {}
    tc = sum(len(cand[k]) for k in keys)
    tb = sum(len(base[k]) for k in keys)
    shorter = sum(1 for k in keys if len(cand[k]) < len(base[k]))
    ratios = sorted(((len(cand[k]) / max(len(base[k]), 1), k) for k in keys), reverse=True)
    return {"n": len(keys), "agg": tc / max(tb, 1),
            "shorter": shorter, "shorter_frac": shorter / len(keys),
            "worst": ratios[0], "cand_chars": tc, "base_chars": tb}


def verdict(m: dict) -> list:
    """→ 未过的条目列表；空表示两条都过。"""
    bad = []
    if m["agg"] > MAX_AGG:
        bad.append(f"**总体均长比 {m['agg']:.2f} > {MAX_AGG}**——整体靠篇幅取胜")
    if m["shorter_frac"] < MIN_SHORTER:
        bad.append(f"**候选更短的题只有 {m['shorter']}/{m['n']} = "
                   f"{m['shorter_frac']:.0%}，要 ≥{MIN_SHORTER:.0%}**"
                   "——长度会变成指认候选的信号")
    return bad


# ══════════════════ 自测 ══════════════════
# 夹具是**实测数据的形状**，不是编的：
#   Lister #108 R3：候选 +144%，32/32 全长（席 D：长度是完美泄题信号）
#   Osler  #110 R3：均长比 1.30，14/32 更短（两席均报「长度指不出哪一侧」）

def _mk(n: int, ratio: float, shorter: int) -> tuple:
    """造一对答案：总体比约为 ratio，其中 shorter 道候选更短。"""
    base = {f"q-{i:02d}": "基" * 100 for i in range(n)}
    cand = {}
    for i in range(n):
        k = f"q-{i:02d}"
        cand[k] = "候" * (60 if i < shorter else 100)
    # 用非更短的那些题把总量调到目标
    long_keys = [f"q-{i:02d}" for i in range(shorter, n)]
    need = int(ratio * 100 * n) - 60 * shorter
    per = max(101, need // max(len(long_keys), 1))
    for k in long_keys:
        cand[k] = "候" * per
    return cand, base


def selftest() -> int:
    fails = []

    def chk(label, cond):
        print(("  ✓ " if cond else "  ✗ ") + label)
        if not cond:
            fails.append(label)

    print("── 正向：Lister #108 第 3 轮的形状（+144%，32/32 全长）──")
    cand, base = _mk(32, 2.44, 0)
    m = measure(cand, base)
    bad = verdict(m)
    chk(f"均长比 {m['agg']:.2f}、更短 {m['shorter']}/32 → 两条都未过（实报 {len(bad)} 条）",
        len(bad) == 2)

    print("── 正向：只超总量、更短的题够数 ──")
    cand, base = _mk(32, 1.60, 12)
    bad = verdict(measure(cand, base))
    chk("均长比超、更短占比够 → 只报总量那一条",
        len(bad) == 1 and "均长比" in bad[0])

    print("── 正向：总量合格但候选题题更长 ──")
    # 这正是旧规则防不住的形态：整体不夸张，但没有一道候选更短
    cand, base = _mk(32, 1.20, 0)
    bad = verdict(measure(cand, base))
    chk("均长比 1.20 过、更短 0/32 → 仍报出（**旧规则在这里会放行**）",
        len(bad) == 1 and "更短" in bad[0])

    print("── 反向对照 ①：Osler #110 第 3 轮的形状（1.30，14/32 更短）→ 不许报 ──")
    cand, base = _mk(32, 1.30, 14)
    m = measure(cand, base)
    chk(f"均长比 {m['agg']:.2f} ≤ {MAX_AGG} 且更短 {m['shorter']}/32 = "
        f"{m['shorter_frac']:.0%} ≥ {MIN_SHORTER:.0%} → 一条不报",
        not verdict(m))

    print("── 反向对照 ②：候选整体更短也不许报（判的是泄题，不是长短）──")
    cand, base = _mk(32, 0.70, 28)
    chk("均长比 0.70、更短 28/32 → 一条不报", not verdict(measure(cand, base)))

    print("── 反向对照 ③：边界值——恰好等于门槛的一律放行 ──")
    m = {"n": 32, "agg": MAX_AGG, "shorter": 8, "shorter_frac": MIN_SHORTER,
         "worst": (1.0, "q"), "cand_chars": 0, "base_chars": 0}
    chk(f"agg 恰为 {MAX_AGG}、更短占比恰为 {MIN_SHORTER:.0%} → 不报", not verdict(m))
    m2 = dict(m, agg=MAX_AGG + 0.01)
    chk("超出门槛 0.01 → 报出", len(verdict(m2)) == 1)
    m3 = dict(m, shorter=7, shorter_frac=7 / 32)
    chk(f"更短 7/32 = {7/32:.1%} < {MIN_SHORTER:.0%} → 报出", len(verdict(m3)) == 1)

    print("── 反向对照 ④：两侧题号对不上时不许沉默通过 ──")
    chk("无共有题号 → measure 返回空，由调用方按 exit 3 处理",
        measure({"a": "x"}, {"b": "y"}) == {})

    print("── 反向对照 ⑤：单题也要能算，不许除零 ──")
    m5 = measure({"q": "候候候"}, {"q": "基"})
    chk(f"单题 3:1 → agg {m5['agg']:.1f}，更短 0/1", m5["n"] == 1 and m5["agg"] == 3.0)

    print(f"\n{'✓ 自测全过' if not fails else f'✗ **{len(fails)} 项未过**'}")
    return 0 if not fails else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--candidate", help="{case_id: 答案} 的 JSON")
    ap.add_argument("--baseline", help="{case_id: 答案} 的 JSON")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return selftest()
    if not (a.candidate and a.baseline):
        ap.error("要么 --self-test，要么同时给 --candidate 与 --baseline")

    cand = json.loads(pathlib.Path(a.candidate).read_text(encoding="utf-8"))
    base = json.loads(pathlib.Path(a.baseline).read_text(encoding="utf-8"))
    m = measure(cand, base)
    if not m:
        print("✗ **两侧没有共有的题号——结果不可信，不是「没问题」**")
        return 3

    print(f"共有题 {m['n']} 道；候选 {m['cand_chars']} 字，基线 {m['base_chars']} 字")
    print(f"**总体均长比 {m['agg']:.2f}**（门 ≤{MAX_AGG}）　"
          f"**候选更短 {m['shorter']}/{m['n']} = {m['shorter_frac']:.0%}**"
          f"（门 ≥{MIN_SHORTER:.0%}）")
    print(f"逐题最长的一道：{m['worst'][1]} 比基线 {m['worst'][0]:.2f} 倍")

    bad = verdict(m)
    if not bad:
        print("\n  ✓ 长度指不出哪一侧是哪个系统")
        return 0
    for b in bad:
        print("✗ " + b)
    print("\n**长度不许成为泄题信号，超了就重写，不打警告了事。**")
    return 1


if __name__ == "__main__":
    sys.exit(main())
