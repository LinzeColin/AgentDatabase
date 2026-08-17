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
| **能不能被门检查** | `meta.json` ＋ **`SKILL.md`** 都在（`ensure_target()` 的硬要求） |
| **预登记** | 那份开箱即跑清单里**点到这个人的名字了吗** |

★ `sd = 0.0928` 是**借来的**（Mendel #125 同装置实测），`se_case = sd/√2 = 0.0656`。
  两轮之差的方差是单轮的 2 倍，**漏掉这一步会把 SE 少算 40%**。
★ 本件**不判「该不该发」**，只判「装置齐不齐、判得出判不出」。

★★★ **本件不覆盖合成门。** 2026-08-13 我拿它放行了三个人
（Brandeis／Michelangelo／Dewey），而真跑 `quality_check --phase synthesis`
是 **22／46／36 条硬错**。**「产物齐」不等于「过门」。**
其中两人当时连门都没开机——缺 `SKILL.md`，`ensure_target()` 直接拒检、
只报一条 `target.invalid`（长得像小毛病，实际后面 46 条全被挡住）。
⇒ 本件现在查 `SKILL.md`，**并在报告末尾印出必须另跑的命令**。

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
import sys as _sys, pathlib as _pl
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent))
from workspace_roots import iter_workspaces  # noqa: E402

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
    """→ (逐人的行, 分桶计数)。

    ★★ 2026-08-14 补分桶：本件原来只印「真正等着判分的 N 人」，
      **不印被跳过的那些**。三条 `continue` 各吃掉一批：没有 cases 文件的、
      cases 空的、已经判过分的。于是「17 人」看不出是从多少里筛出来的，
      而「做到阶段 3 没做阶段 4」那一批**一个字都不出现**。
      [[a-continue-hid-the-worst-case]]、[[filters-make-rows-vanish]]
    """
    pre = PRELOG.read_text(encoding="utf-8") if PRELOG.is_file() else ""
    closed = _deferred_names()
    out = []
    tally = {"扫到的工作区": 0, "没有 cases 文件": 0, "cases 是空的": 0,
             "已经判过分": 0, "留下的": 0, "★ 有 claims 却没有 cases": []}
    for d in [str(_w) for _w in iter_workspaces(CORPORA)]:
        ws = pathlib.Path(d)
        tally["扫到的工作区"] += 1
        cases = ws / "evals/cases.jsonl"
        _cl = ws / "evidence/claims.jsonl"
        _nc = sum(1 for l in _cl.read_text(encoding="utf-8").splitlines()
                  if l.strip()) if _cl.is_file() else 0
        if not cases.is_file():
            tally["没有 cases 文件"] += 1
            if _nc:                        # ★ 做到阶段 3、没做阶段 4 —— 原先整个看不见
                tally["★ 有 claims 却没有 cases"].append(f"{ws.name}({_nc})")
            continue
        rows = [json.loads(l) for l in cases.read_text(encoding="utf-8").splitlines() if l.strip()]
        if not rows:
            tally["cases 是空的"] += 1
            continue                       # 空用例 = 还没做到阶段 4，不在本件射程
        # ★★ 射程：**有用例 ≠ 等着判分**。第一版把 30 个有用例的工作区全算成
        #   「等着判分」，而其中 14 个**早就判过分**（已入库或记拒发），
        #   还有几个是**已结案不判**（装置不成立）。
        #   ⇒ 真集合 = 有用例 ＋ **没有判分结果** ＋ **不在延后名单里**。
        if [q for q in ws.glob("evals/**/results*.jsonl") if q.stat().st_size > 2]:
            tally["已经判过分"] += 1
            continue                       # 已经判过分
        claims = ws / "evidence/claims.jsonl"
        n_claims = sum(1 for l in claims.read_text(encoding="utf-8").splitlines()
                       if l.strip()) if claims.is_file() else 0
        miss = [f for f in PRODUCTS if not (ws / f).is_file()]
        # ★★ `quality_check.ensure_target()` 的硬要求：两个都在，否则**整个工作区拒检**
        no_target = [f for f in ("meta.json", "SKILL.md") if not (ws / f).is_file()]
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
            "★ 路径": str(ws),
            "断言": n_claims, "题数": len(rows), "类数": suites,
            "缺产物": miss, "claim 标记": anchored, "已结案": closed_as,
            "门开不了": no_target,
            "空心道": hollow, "se_mean": se_mean, "2SE": two_se, "门是几个SE": gate_se,
            "已预登记": registered,
        })
    tally["留下的"] = len(out)
    return out, tally


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

    # ── ★★★ 2026-08-17：「判完之后还查得了吗」这一档，正反各一 ──
    #   ★ 它必须**只报不判**：走独立通道，不进 `bad`、不改退出码。
    #     第一版直接 `gaps.append(...)`，实测**9 个人只因这一条就新进「缺件」名单**
    #     （✗ 8 人 → 17 人），而我在注释里写着「只报信息」——**那句话当场是假的**。
    import tempfile as _tf
    with _tf.TemporaryDirectory() as _td:
        _r = pathlib.Path(_td)

        def _mk(name, with_rig):
            d = _r / name / "evals"
            d.mkdir(parents=True)
            (d / "cases.jsonl").write_text('{"suite":"s"}\n', encoding="utf-8")
            if with_rig:
                (d / "baseline.v1.json").write_text("{}", encoding="utf-8")
                (d / "judge_payload.v1.json").write_text("{}", encoding="utf-8")
            return _r / name

        def _miss(ws):
            e = pathlib.Path(ws) / "evals"
            out = []
            if not (e / "baseline.v1.json").is_file():
                out.append("baseline.v1.json")
            if not list(e.glob("judge_payload*.json")):
                out.append("judge_payload*.json")
            return out

        _a, _b = _mk("has-rig", True), _mk("no-rig", False)
        chk("★ 有成对载荷 → 不报", _miss(_a) == [])
        chk("★★ 缺成对载荷 → 两件都点名",
            _miss(_b) == ["baseline.v1.json", "judge_payload*.json"])
        # 反对照：只缺一件时**只点那一件**，不许一律报两件
        (_b / "evals" / "baseline.v1.json").write_text("{}", encoding="utf-8")
        chk("★★ 只缺 payload 时只点 payload", _miss(_b) == ["judge_payload*.json"])
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

    rows, tally = scan()
    if not rows:
        print(f"★★ **未判，不是通过**：{CORPORA} 下没有带非空 evals/cases.jsonl 的工作区")
        return 4
    if a.json:
        print(json.dumps(rows, ensure_ascii=False, indent=1))

    print("★ 射程：有用例 ＋ **没有判分结果**。"
          "已结案的人**不过滤掉**，改成报矛盾——过滤会让人整个消失。")
    # ★★ 分母：三条 continue 各吃掉一批，不印出来就看不出「17」是从多少里筛的
    print(f"★★ **分母**：扫到工作区 **{tally['扫到的工作区']}** ＝ "
          f"没有 cases 文件 {tally['没有 cases 文件']} ＋ cases 是空的 {tally['cases 是空的']} ＋ "
          f"**已经判过分 {tally['已经判过分']}** ＋ 留下的 {tally['留下的']}")
    _s3 = tally["★ 有 claims 却没有 cases"]
    if _s3:
        print(f"   ★ 其中 **{len(_s3)} 个做到阶段 3、没做阶段 4**（有 claims 无用例）—— "
              f"**本件射程之外，不是通过**：{'、'.join(_s3)}")
    print()
    print(f"真正等着判分的 **{len(rows)} 人**　"
          f"（sd={SD_BORROWED} 借自 Mendel #125；se_case = sd/√2 = {SE_CASE:.4f}）\n")
    print(f"{'工作区':30s} {'档':9s} {'题':>4s} {'类':>3s} {'断言':>4s} "
          f"{'2SE':>7s} {'门是几个SE':>10s}  预登记  缺件")
    bad = []
    no_rig = []          # ★ 判完之后无法复查盲判的人（**只报，不进 bad**）
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
        if r["门开不了"]:
            gaps.append(f"★★ **缺 {'／'.join(r['门开不了'])} ⇒ 合成门拒检整个工作区**"
                        "（只会报一条 target.invalid）")
        if r["已结案"]:
            gaps.append(f"★★ **矛盾：延后名单里已结案**（{r['已结案']}）而产物齐全")
        h = r["空心道"]
        if h is None:
            gaps.append("空心道**未检查**（无 raw/_dedup.json）")
        elif h[0] and h[1] < h[2]:
            gaps.append(f"★★ **空心道 {'/'.join(h[0])} 去掉后只剩 {h[1]} 道 < 门 {h[2]}**")
        elif h[0]:
            gaps.append(f"空心道 {'/'.join(h[0])}（去掉后 {h[1]} 道 ≥ 门 {h[2]}，不挡）")
        # ★★★ 2026-08-17 新增：**判完之后，这次盲判还查得了吗**
        #   `check_answer_surface_leak.py` 要成对载荷（`evals/baseline.v1.json`
        #   ＋ `evals/judge_payload*.json`）才跑得动。缺了它，判完就**永远**答不出
        #   「这次盲判到底盲不盲」——不是「盲判坏了」，是**没有留下能复查的东西**。
        #   全库实测（2026-08-17）：22 个工作区有评测数据却缺载荷，
        #   其中 **8 个已经判过分**（godin／jenner／koch／lister／pasteur／
        #   rosenhain／steinhardt／virchow），他们的 delta 建立在一次无法复查的盲判上。
        #   ⇒ **在判分之前说出来**，别等判完再发现。
        #   ★ 本条**只报信息，不改任何门的判定** —— 它不进 `bad`，只挂在那一行上。
        #   [[zero-hit-gates-must-prove-they-can-hit]]
        # ★ 用**这一行自己的**路径，不用外层循环泄漏下来的 `ws`——
        #   第一版就是那么写的，于是每一行都在查同一个工作区，命中 0。
        _ev = pathlib.Path(r["★ 路径"]) / "evals"
        _miss_rig = []
        if not (_ev / "baseline.v1.json").is_file():
            _miss_rig.append("baseline.v1.json")
        if not list(_ev.glob("judge_payload*.json")):
            _miss_rig.append("judge_payload*.json")
        if _miss_rig:
            # ★★★ **走独立通道，不进 `gaps`。**
            #   第一版直接 `gaps.append(...)`，而 `if gaps: bad.append(...)` ——
            #   实测**9 个人只因这一条就新进「缺件」名单**（✗ 8 人 → 17 人）。
            #   我在注释里写着「只报信息，不改任何门的判定」，**那句话当场就是假的**。
            #   让门对 9 个人变严是**决定**，不是清理；本件只负责说出来。
            no_rig.append((r["工作区"], "／".join(_miss_rig)))
        if gaps:
            bad.append((r["工作区"], gaps))
        print(f"{r['工作区']:30s} {str(r['档']):9s} {r['题数']:>4d} {r['类数']:>3d} "
              f"{r['断言']:>4d} {r['2SE']:>7.4f} {r['门是几个SE']:>10.2f}  "
              f"{'✓' if r['已预登记'] else '✗':^6s}  {'；'.join(gaps) if gaps else '—'}")

    if no_rig:
        print("\n★ **判完之后无法复查这次盲判是否真盲**（缺成对载荷，泄题门跑不动）"
              "　**%d 人**：" % len(no_rig))
        for _n, _w in no_rig:
            print("    · %-30s 缺 %s" % (_n, _w))
        print("  ★ 本节**不改判定**——不进「缺件」计数，也不影响退出码。")
        print("  ★ 为什么要现在说：全库实测 22 个工作区有评测数据却缺载荷，"
              "其中 **8 个已经判过分**，他们的 delta 建立在一次无法复查的盲判上。"
              "**判分之前留下载荷，成本近似为零；判完再补，做不到。**")

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
    print("\n★★★ **本件不覆盖合成门**——它是判分的**前一道**，必须逐人另跑（每人几分钟）：")
    print("      python3 CodexSkills/registry/codex/persona-distiller/scripts/quality_check.py \\")
    print("        <工作区> --phase synthesis          # 要 \"passed\": true 且 errors 为空")
    print("  2026-08-13 实测：第 1 批八人全过；而只按本件放行的三人是 **22／46／36 条硬错**。")
    print("\n★ 射程：本件只判**装置齐不齐、判得出判不出**，"
          "**不判该不该发**，也不代替授权——判分要两名互相独立的评委，**只能由人起**。")
    return 1 if (bad or not rig_ok) else 0


if __name__ == "__main__":
    raise SystemExit(main())
