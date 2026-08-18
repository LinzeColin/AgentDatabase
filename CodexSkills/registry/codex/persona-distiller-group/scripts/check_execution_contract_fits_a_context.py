#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""宿主要把执行合同装进上下文 —— **deep_team 那份是 776 KB**。

## 事实（2026-08-18 实测 @v0.0.0.40，整条链现跑，读的是**盘上字节**）

    档位            人数   route-plan   dossier    contract
    single_expert    1 人      30 KB       83 KB      38 KB
    small_team       9 人     111 KB      531 KB     233 KB
    deep_team       28 人     273 KB   **1796 KB**  **776 KB**

合同 **98% 是 `execution_units`**（每位专家一段），所以它**随人数近似线性长**。

★★ 把它和档位阶梯并排读：**32 个无意义词就能拿到 deep_team**
（见 `check_mode_ladder_reachable.py` 与 `check_team_size_ladder_has_no_hole.py`）
⇒ **一个稍微长一点的请求，就能产出宿主装不下的合同。**

★ token 数**不是量出来的**：字节是实测，token 要除以一个我选的除数。
  本件**印区间不印单值**（4.0 / 2.5 / 1.5 字节每 token 三档），
  并明说除数是选的。[[counts-need-their-cutoff-stated]]

★★★ 本件**不判「太大了」**（多大算大取决于宿主，不是这个包能定的），
  只判「**每位专家占的字节不许比基线更胖**」—— 那是这个包自己控制得了的。
  [[a-red-that-can-never-turn-green-is-not-a-signal]]

用法：

    python3 check_execution_contract_fits_a_context.py
    python3 check_execution_contract_fits_a_context.py --baseline-kb-per-expert 1   # 看它红不红得了
    python3 check_execution_contract_fits_a_context.py --self-test
"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent

# ── 基线（2026-08-18 实测）──────────────────────────────────────────────
BASELINE_KB_PER_EXPERT = 29.0     # deep_team：776 KB ÷ 28 人 ≈ 27.7；留一点余量
MIN_MODES = 2                     # 至少要跑出两个不同人数，否则「随人数长」无从谈起
DIVISORS = (4.0, 2.5, 1.5)        # 字节/token 的三档粗估 —— **是选的，不是量的**

CASES = (
    ("修复登录接口的空指针崩溃并补回归测试。", "短请求"),
    ("为一个遗留微服务代码库设计测试策略与重构方案", "中等请求"),
    ("处理涉及财务、法律、运营和技术的高风险决策，输出场景推演、权衡矩阵、"
     "可执行方案与不可逾越的边界，并对每条结论标注证据强度与失效条件", "长请求"),
)


def run_chain(task: str, out: pathlib.Path) -> dict | None:
    """route → dossier → contract。→ {mode, experts, rp, do, ct}（字节），失败返回 None。"""
    rp, do, ct = out / "rp.json", out / "do.json", out / "ct.json"
    r = subprocess.run([sys.executable, str(HERE / "route_team_moe.py"),
                        "--task", task, "--output", str(rp)],
                       capture_output=True, text=True)
    if r.returncode != 0 or not rp.is_file():
        return None
    try:
        info = json.loads(r.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return None
    for cmd in ([sys.executable, str(HERE / "build_team_dossier.py"),
                 "--route-plan", str(rp), "--output", str(do)],
                [sys.executable, str(HERE / "build_execution_contract.py"),
                 "--route-plan", str(rp), "--dossier", str(do), "--output", str(ct)]):
        if subprocess.run(cmd, capture_output=True, text=True).returncode != 0:
            return None
    if not ct.is_file():
        return None
    # ★ `execution_units` 占多少 —— **现算**，不写死。
    #   我第一版写死「98%」，那是在 small_team 上量的；deep_team 实测是 **99.4%**。
    #   [[self-reported-numbers-must-be-computed]]
    share = None
    try:
        doc = json.loads(ct.read_text(encoding="utf-8"))
        whole = len(json.dumps(doc, ensure_ascii=False).encode())
        eu = len(json.dumps(doc.get("execution_units"), ensure_ascii=False).encode())
        share = 100.0 * eu / max(1, whole)
    except (ValueError, OSError):
        share = None
    return {"mode": info.get("mode"), "experts": int(info.get("persona_expert_count") or 0),
            "rp": rp.stat().st_size, "do": do.stat().st_size, "ct": ct.stat().st_size,
            "eu_share": share}


def measure() -> list[dict]:
    rows = []
    with tempfile.TemporaryDirectory() as td:
        for i, (task, label) in enumerate(CASES):
            out = pathlib.Path(td) / str(i)
            out.mkdir()
            row = run_chain(task, out)
            if row:
                row["label"] = label
                rows.append(row)
    return rows


def token_range(nbytes: int) -> list[tuple[float, float]]:
    """→ [(除数, K token), …]。**除数是选的** —— 调用方必须把这句话一起印出去。"""
    return [(d, nbytes / d / 1000) for d in DIVISORS]


def self_test() -> int:
    ok = True

    def chk(name, cond):
        nonlocal ok
        print("   %s %s" % ("✓" if cond else "✗", name))
        ok = ok and bool(cond)

    rows = measure()
    chk("① 整条链跑得通（route→dossier→contract），成功 %d/%d 例" % (len(rows), len(CASES)),
        len(rows) == len(CASES))
    sizes = {r["experts"] for r in rows}
    chk("②★探针没死：至少跑出 %d 种人数（现测 %s）" % (MIN_MODES, sorted(sizes)),
        len(sizes) >= MIN_MODES)
    chk("③ 合同非空：最小的那份也 > 1 KB（现测 %.0f KB）"
        % (min(r["ct"] for r in rows) / 1024), min(r["ct"] for r in rows) > 1024)

    big = max(rows, key=lambda r: r["experts"])
    small = min(rows, key=lambda r: r["experts"])
    chk("④★★ 合同**随人数长**：%d 人那份(%.0fKB) 必须大于 %d 人那份(%.0fKB)"
        % (big["experts"], big["ct"] / 1024, small["experts"], small["ct"] / 1024),
        big["ct"] > small["ct"] and big["experts"] > small["experts"])

    # ★★★ 反例：token 区间必须**现算**，不许写死（我第一版把区间写死过，和实算差了 13 K）
    tr = token_range(big["ct"])
    lo, hi = min(k for _, k in tr), max(k for _, k in tr)
    chk("⑤★★★ token 区间现算（%.0f–%.0f K）且随字节变 —— 换个字节数必须换个区间"
        % (lo, hi), abs(token_range(big["ct"] * 2)[0][1] - tr[0][1] * 2) < 1e-6)
    chk("⑥ 每档除数都印得出来（%s）" % (DIVISORS,), len(DIVISORS) >= 2)
    chk("⑦ 地板可达：0 < BASELINE_KB_PER_EXPERT", BASELINE_KB_PER_EXPERT > 0)
    shares = [r.get("eu_share") for r in rows if r.get("eu_share") is not None]
    chk("⑧★★ `execution_units` 占比是**现算的**且各档不同（现测 %s）"
        % ["%.1f%%" % x for x in shares],
        len(shares) == len(rows) and len({round(x, 1) for x in shares}) > 1)
    print("   —— self-test %s ——" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="执行合同的体量：每位专家占多少字节")
    ap.add_argument("--baseline-kb-per-expert", type=float, default=None)
    ap.add_argument("--self-test", "--selftest", dest="selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return self_test()

    floor = BASELINE_KB_PER_EXPERT if a.baseline_kb_per_expert is None else a.baseline_kb_per_expert
    rows = measure()
    if len(rows) < len(CASES):
        print("★ **未量，不是通过**（rc=4）—— 整条链只跑通 %d/%d 例" % (len(rows), len(CASES)))
        return 4
    if len({r["experts"] for r in rows}) < MIN_MODES:
        print("★ **未量，不是通过**（rc=4）—— 只跑出一种人数，「随人数长」无从谈起")
        return 4

    print("整条链现跑（读的是**盘上字节**，不是重新序列化的数）：\n")
    print("  %-8s %-14s %5s %11s %10s %10s" % ("请求", "档位", "人数", "route-plan", "dossier", "contract"))
    for r in rows:
        print("  %-8s %-14s %4d 人 %8.0f KB %8.0f KB %8.0f KB"
              % (r["label"], r["mode"], r["experts"], r["rp"] / 1024, r["do"] / 1024, r["ct"] / 1024))

    big = max(rows, key=lambda r: r["experts"])
    per = big["ct"] / 1024 / max(1, big["experts"])
    print("\n最大那份：**%s / %d 人 / 合同 %.0f KB** ⇒ **每位专家约 %.1f KB**"
          % (big["mode"], big["experts"], big["ct"] / 1024, per))
    _sh = big.get("eu_share")
    print("  合同里 `execution_units` 占 **%s**（每位专家一段）⇒ 它随人数近似线性长。"
          % ("%.1f%%" % _sh if _sh is not None else "**未算出**"))
    print("  token 数**不是量出来的** —— 字节是实测，除数是我选的：")
    for d, k in token_range(big["ct"]):
        print("     ÷ %.1f 字节/token ⇒ ≈ **%.0f K token**" % (d, k))
    tr = [k for _, k in token_range(big["ct"])]
    print("  ⇒ 区间 **%.0f–%.0f K token**。别只报一个数。" % (min(tr), max(tr)))
    print("\n  ★★ 与档位阶梯并排读：**32 个无意义词就能拿到 deep_team**")
    print("     ⇒ 一个稍长的请求就能产出宿主可能装不下的合同。")
    print("     （多大算大取决于宿主，**本件不判那个** —— 见下面判的是什么。）")

    print()
    if per > floor:
        print("✗ **每位专家占的字节变胖了**：%.1f KB > 地板 %.1f KB" % (per, floor))
        return 1
    print("✓ 未超基线：每人 %.1f KB ≤ %.1f KB（**不代表装得下** —— 那取决于宿主）"
          % (per, floor))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
