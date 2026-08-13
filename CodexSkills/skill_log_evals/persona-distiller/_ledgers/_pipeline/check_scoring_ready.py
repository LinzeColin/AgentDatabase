#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_scoring_ready.py —— **等着判分的人，拿起来就能跑吗**

## 为什么有这件

阶段 5（判分）是本项目**唯一的停点**，而它**只能由人授权**（要两名互相独立的评委）。
授权来之前 agent 能做的只有一件：**把「拿起就能跑」这件事先证明掉**。

2026-08-13 现状：等着判分的有 **12 人**，而
`_第1批阶段5判分-开箱即跑清单-2026-08-13.md` 只覆盖其中 **8 人**——
Brandeis #172／Michelangelo #185／Dewey #190／Churchill #191 四人
**分辨力没算、压线没复核、风险没写**。
⇒ 授权来了才发现少四份预登记，那一刻再补就是**判完之后补口径**，
   而本项目的规矩是「装置先落纸，判完只补实测数」。

## 判什么（逐人）

| 项 | 判据 |
|---|---|
| 十份产物 | `persona.md` 等十份齐、且 `persona.md` 里有 `<!-- claim:` 标记 |
| 断言层 | `evidence/claims.jsonl` 非空 |
| 盲判用例 | `evals/cases.jsonl` ≥16 题、≥16 类 |
| **分辨力** | `se_mean = 0.0656/√n`，`2 SE` 与档位门比——**门是几个 SE** |
| 装置件 | 冻结基线 prompt、两席评委指令、载荷生成器**都在** |
| **预登记** | 那份开箱即跑清单里**点到这个人的名字了吗** |

★ `sd = 0.0928` 是**借来的**（Mendel #125 同装置实测），`se_case = sd/√2 = 0.0656`。
  两轮之差的方差是单轮的 2 倍，**漏掉这一步会把 SE 少算 40%**。
★ 本件**不判「该不该发」**，只判「装置齐不齐、判得出判不出」。

## 用法

    python3 check_scoring_ready.py
    python3 check_scoring_ready.py --self-test

退出码：0＝12 人全部就绪；1＝有人缺件或没预登记；4＝找不到工作区（**未判**）
"""
import argparse
import glob
import json
import math
import os
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
PD = HERE.parent.parent
CORPORA = PD / "_corpora"
PRELOG = PD / "_ledgers/_第1批阶段5判分-开箱即跑清单-2026-08-13.md"
DEFER = PD / "_ledgers/_延后名单.json"
RIG = {
    "冻结基线 prompt": HERE / "BASELINE-PROMPT-FROZEN-v1.md",
    "评委席 D": HERE / "judge_prompts/seat_D_score.md",
    "评委席 E": HERE / "judge_prompts/seat_E_strict.md",
}
PRODUCTS = ["persona.md", "facts.md", "work.md", "decision-policy.md", "strategy.md",
            "capabilities.md", "boundaries.md", "cognitive-os.md", "hypotheses.md",
            "divergence-map.md"]
SD_BORROWED = 0.0928                 # Mendel #125 同装置实测，**借来的**
SE_CASE = SD_BORROWED / math.sqrt(2)  # 两轮之差的方差 = 2×单轮方差
GATE = {"quick": 0.03, "standard": 0.05, "deep": 0.07}


def resolution(n_cases: int, profile: str):
    """→ (se_mean, 2SE, 门是几个 SE)。**纯函数**，自测不碰磁盘。"""
    if n_cases <= 0:
        return None, None, None
    se_mean = SE_CASE / math.sqrt(n_cases)
    return se_mean, 2 * se_mean, GATE.get(profile, GATE["quick"]) / se_mean


def profile_of(ws: pathlib.Path):
    """从台账现算档位——**不读任何写死的表**。"""
    led = ws / "evidence/source-ledger.jsonl"
    if not led.is_file():
        return None, 0, 0
    rows = [json.loads(l) for l in led.read_text(encoding="utf-8").splitlines() if l.strip()]
    tr = [r for r in rows if r.get("split") == "train"]
    lanes = len({d for r in tr for d in (r.get("dimensions") or [])})
    p1 = sum(1 for r in tr if r.get("tier") == "P1")
    n = len(tr)
    if n >= 45 and lanes >= 6 and n and p1 / n >= 0.65:
        return "deep", n, lanes
    if n >= 24 and lanes >= 6 and n and p1 / n >= 0.50:
        return "standard", n, lanes
    return "quick", n, lanes


def hollow_lanes(ws: pathlib.Path):
    """→ (空心道名单, 去掉后还剩几道, 门)；量不了就 None。

    ★ **复用** `check_lane_distinct_works.analyse`，**不在这里重写一遍度量**——
      临时脚本重实现判据的度量，两边口径必然分叉（已犯过）。
    """
    try:
        sys.path.insert(0, str(HERE))
        from check_lane_distinct_works import analyse, PROFILES
    except Exception:
        return None
    led, dj = ws / "evidence/source-ledger.jsonl", ws / "raw/_dedup.json"
    if not (led.is_file() and dj.is_file()):
        return None                        # **未检查，不是通过**
    tr = [json.loads(l) for l in led.read_text(encoding="utf-8").splitlines() if l.strip()]
    tr = [r for r in tr if r.get("split") == "train"]
    res = analyse(tr, json.loads(dj.read_text(encoding="utf-8")).get("重复簇") or [])
    prof, _, _ = profile_of(ws)
    gate = PROFILES[prof or "quick"]["min_lanes"]
    bad = [l for l, (n, w) in res.items() if n >= 2 and w == 1]
    left = len([l for l, (n, w) in res.items() if w >= 2 or n == 1])
    return (bad, left, gate)


def _deferred_names():
    """→ 归一后的延后/拒发人名集合。**已结案的人不该出现在待判队列里。**"""
    if not DEFER.is_file():
        return set()
    out = set()
    for it in json.loads(DEFER.read_text(encoding="utf-8")).get("deferred", []):
        for k in [it.get("name", "")] + list(it.get("aliases") or []):
            if k:
                out.add(re.sub(r"[^a-z]", "", k.lower()))
    return out


def scan():
    pre = PRELOG.read_text(encoding="utf-8") if PRELOG.is_file() else ""
    closed = _deferred_names()
    out = []
    for d in sorted(glob.glob(str(CORPORA / "wip-*" / "workspaces" / "*"))):
        ws = pathlib.Path(d)
        cases = ws / "evals/cases.jsonl"
        if not cases.is_file():
            continue
        rows = [json.loads(l) for l in cases.read_text(encoding="utf-8").splitlines() if l.strip()]
        if not rows:
            continue                       # 空用例 = 还没做到阶段 4，不在本件射程
        # ★★ 射程：**有用例 ≠ 等着判分**。第一版把 30 个有用例的工作区全算成
        #   「等着判分」，而其中 14 个**早就判过分**（已入库或记拒发），
        #   还有几个是**已结案不判**（装置不成立）。
        #   ⇒ 真集合 = 有用例 ＋ **没有判分结果** ＋ **不在延后名单里**。
        if [q for q in ws.glob("evals/**/results*.jsonl") if q.stat().st_size > 2]:
            continue                       # 已经判过分
        claims = ws / "evidence/claims.jsonl"
        n_claims = sum(1 for l in claims.read_text(encoding="utf-8").splitlines()
                       if l.strip()) if claims.is_file() else 0
        miss = [f for f in PRODUCTS if not (ws / f).is_file()]
        persona = ws / "persona.md"
        anchored = persona.is_file() and "<!-- claim:" in persona.read_text(encoding="utf-8")
        prof, n_src, lanes = profile_of(ws)
        hollow = hollow_lanes(ws)          # ★ 一部作品撑起的道（见 check_lane_distinct_works）
        suites = len({r.get("suite") for r in rows})
        se_mean, two_se, gate_se = resolution(len(rows), prof or "quick")
        slug = ws.name
        key = re.sub(r"[^a-z]", "", slug.lower())
        # ★★ **不许静默跳过。** 第二版按延后名单过滤时用的是 `continue`，
        #   于是 Churchill 从表里**整个消失**了——而他当天刚做完阶段 4，
        #   我差点据此以为「他不在待判队列」。**被判据吃掉的人，比报错的人危险。**
        #   ⇒ 已结案 **＋ 有完整产物** 本身就是一条要报的矛盾，不是过滤条件。
        closed_as = next((c for c in closed if len(c) > 5 and (key in c or c in key)), None)
        # 预登记：清单里点到名字了吗（按 slug 的姓氏段比，避免大小写/中间名差异）
        surname = slug.split("-")[-1]
        registered = bool(pre) and (surname.lower() in pre.lower())
        out.append({
            "工作区": slug, "档": prof, "train 源": n_src, "道": lanes,
            "断言": n_claims, "题数": len(rows), "类数": suites,
            "缺产物": miss, "claim 标记": anchored, "已结案": closed_as,
            "空心道": hollow, "se_mean": se_mean, "2SE": two_se, "门是几个SE": gate_se,
            "已预登记": registered,
        })
    return out


def self_test() -> int:
    ok = t = 0

    def chk(d, c):
        nonlocal ok, t
        t += 1
        ok += 1 if c else 0
        print(f"  {'✓' if c else '✗'} {d}")

    # ★ 逐字复算清单里那张表：32 题 quick ⇒ 2.59 SE；33 题 ⇒ 2.63
    se, two, g = resolution(32, "quick")
    chk(f"★ 32 题 quick：门应为 2.59 个 SE（实得 {g:.2f}）", abs(g - 2.59) < 0.02)
    chk(f"★ 32 题：2 SE 应为 0.0232（实得 {two:.4f}）", abs(two - 0.0232) < 0.0005)
    se33, _, g33 = resolution(33, "quick")
    chk(f"★ 33 题 quick：门应为 2.63 个 SE（实得 {g33:.2f}）", abs(g33 - 2.63) < 0.03)
    _, _, gd = resolution(32, "deep")
    chk(f"★ 32 题 deep：门应为 6.03 个 SE（实得 {gd:.2f}）", abs(gd - 6.03) < 0.03)
    # ★ 16 题的那个「门低于仪器噪声」旧读数也要复现得出来
    _, _, g16 = resolution(16, "quick")
    chk(f"★ 16 题 quick：应复现出补题之前的 1.83 个 SE（实得 {g16:.2f}）", abs(g16 - 1.83) < 0.03)
    # ★ se_case 必须除过 √2
    chk("★★ se_case 必须是 sd/√2 —— 漏掉这一步会把 SE 少算约 29%（门虚高 41%）",
        abs(SE_CASE - 0.0928 / math.sqrt(2)) < 1e-9)
    chk("0 题 ⇒ 不给数（不许当成 0 SE）", resolution(0, "quick") == (None, None, None))
    print(f"\n{'✓ 全过' if ok == t else f'✗ {t - ok}/{t} 项不符'}"
          "（前四条逐字复算 2026-08-13 那份开箱即跑清单里的表）")
    return 0 if ok == t else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()

    rows = scan()
    if not rows:
        print(f"★★ **未判，不是通过**：{CORPORA} 下没有带非空 evals/cases.jsonl 的工作区")
        return 4
    if a.json:
        print(json.dumps(rows, ensure_ascii=False, indent=1))

    print("★ 射程：有用例 ＋ **没有判分结果**。"
          "已结案的人**不过滤掉**，改成报矛盾——过滤会让人整个消失。\n")
    print(f"真正等着判分的 **{len(rows)} 人**　"
          f"（sd={SD_BORROWED} 借自 Mendel #125；se_case = sd/√2 = {SE_CASE:.4f}）\n")
    print(f"{'工作区':30s} {'档':9s} {'题':>4s} {'类':>3s} {'断言':>4s} "
          f"{'2SE':>7s} {'门是几个SE':>10s}  预登记  缺件")
    bad = []
    for r in rows:
        gaps = []
        if r["缺产物"]:
            gaps.append(f"缺 {len(r['缺产物'])} 份产物")
        if not r["claim 标记"]:
            gaps.append("persona.md 无 claim 标记")
        if r["题数"] < 16 or r["类数"] < 16:
            gaps.append(f"题/类不足（{r['题数']}/{r['类数']}）")
        if r["断言"] == 0:
            gaps.append("断言层为空")
        if not r["已预登记"]:
            gaps.append("**未预登记**")
        if r["已结案"]:
            gaps.append(f"★★ **矛盾：延后名单里已结案**（{r['已结案']}）而产物齐全")
        h = r["空心道"]
        if h is None:
            gaps.append("空心道**未检查**（无 raw/_dedup.json）")
        elif h[0] and h[1] < h[2]:
            gaps.append(f"★★ **空心道 {'/'.join(h[0])} 去掉后只剩 {h[1]} 道 < 门 {h[2]}**")
        elif h[0]:
            gaps.append(f"空心道 {'/'.join(h[0])}（去掉后 {h[1]} 道 ≥ 门 {h[2]}，不挡）")
        if gaps:
            bad.append((r["工作区"], gaps))
        print(f"{r['工作区']:30s} {str(r['档']):9s} {r['题数']:>4d} {r['类数']:>3d} "
              f"{r['断言']:>4d} {r['2SE']:>7.4f} {r['门是几个SE']:>10.2f}  "
              f"{'✓' if r['已预登记'] else '✗':^6s}  {'；'.join(gaps) if gaps else '—'}")

    print("\n装置件：")
    for k, p in RIG.items():
        print(f"  {'✓' if p.is_file() else '✗'} {k}　{p.relative_to(PD)}")
    rig_ok = all(p.is_file() for p in RIG.values())

    print(f"\n{'✗' if bad or not rig_ok else '✓'} "
          f"{'有 %d 人缺件或未预登记' % len(bad) if bad else '全部就绪'}"
          f"{'；装置件不全' if not rig_ok else ''}")
    if bad:
        print("\n★ 未预登记的意思：那份开箱即跑清单**没点到这个人的名字**——"
              "分辨力、压线复核、逐人风险都没写。"
              "\n  等授权到了再补，就成了**判完之后补口径**，"
              "而本项目的规矩是「装置先落纸，判完只补实测数」。")
    print("\n★ 射程：本件只判**装置齐不齐、判得出判不出**，"
          "**不判该不该发**，也不代替授权——判分要两名互相独立的评委，**只能由人起**。")
    return 1 if (bad or not rig_ok) else 0


if __name__ == "__main__":
    raise SystemExit(main())
