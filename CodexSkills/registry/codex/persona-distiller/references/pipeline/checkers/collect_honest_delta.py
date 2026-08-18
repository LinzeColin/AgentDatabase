#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**「诚实 delta」的唯一口径** —— 把三种形状、两条臂、两种量纲收成一张表。

## 为什么要它（2026-08-12 撞出来的）

待裁定 ㉛ 剩的半问是「门该不该按分辨力定」，需要历史 delta 的分布。
我按 `system` 字段算了一版，**当场作废**——两处对不上：

| 人物 | 台账记的 | 我算的 |
|---|---:|---:|
| Thomson #129 | **−0.0859** | **+0.1597** |
| Galen #101 | −0.1259 | −0.1456 |

去查才知道，`results.jsonl` 底下压着**三件互不相同的事**：

### ① 三种形状

| 形状 | 份数 | 长相 |
|---|---:|---|
| 长表 | 28 | 一行一个系统：`{case_id, judge_id, system, overall_score}` |
| 宽表 | 9 | 一行两个系统：`{case_id, seat, candidate, baseline}` |
| 空文件 | 1 | 0 行（benardos-128） |

### ② 两条臂 —— **不许合并**

长表的 `system` 有两种组合：`('baseline','candidate')` **26 份**、
`('bare_model','candidate')` **2 份**。
Thomson 就在后一档：台账那个 −0.0859 是 **vs 基线**，
按 `system` 算出的 +0.1597 是 **vs 裸模型**——
**两个数都对，回答的不是同一个问题。**

### ③ 两种量纲 —— ★★ **按实测最大值判，不按形状判**

同时有两种形状的 9 个人，逐个比：

    fleming/jenner/koch/lister/nightingale/osler/pasteur/virchow —— 宽表 = 长表 × **10.00**
    barton ——————————————————————————————————— 宽表 = 长表 × **1.00**

也就是说宽表**多数**是 0–10，**而 Barton 那份本来就是 0–1**。
**按「宽表就除以 10」写死会把 Barton 算错一个数量级。**
⇒ 本件按**该份文件里观测到的最大分**判：`> 1.5` 才归一化。
  （[[eval-artifacts-have-five-schemas]]：按一种命名去统计，一天错三次。）

## 它自带一道对照

9 个人同时有两种形状。**归一化之后两者必须相等**——
本件把它当成硬校验：对不上就报出来，而不是挑一个用。
实测 9/9 逐个吻合到小数点后四位。

## 它**不**做什么

- **不判「该不该发」**：只出数，门在 `quality_check`。
- **不合并两条臂**：`baseline` 与 `bare_model` 分开列。
- **不替污染读数下结论**：已知「看过 rubric 才写基线」的那批只标记，不剔除，
  剔不剔由读的人决定（`--exclude-tainted` 才剔）。

退出码：0 = 出表；1 = 有人物两种形状对不上；3 = 用法错误。
"""
from __future__ import annotations

import argparse
import json
import pathlib
import statistics
import sys

#: 已知污染：**看过 rubric 才写基线**，delta 被抬高。
#: 出处：`_待用户裁定.md` ㊵ 之外的独立记录 + [[implausibly-good-result-is-a-defect-report]]
#: （「delta +0.6553 比历史最大值大 18 倍；不是产品成了，是我看过 rubric 才写基线」）。
#: ★ 这是**名单**不是判据——加人要写清出处。
TAINTED = {
    "wip-godin": "看过 rubric 才写基线（+0.6473）",
    "wip-steinhardt-98": "看过 rubric 才写基线（+0.6525）",
    "wip-livermore-100": "看过 rubric 才写基线（+0.8013）",
}

#: ★★★★ 2026-08-18：**污染名单是按「人物」列的，而泄题是按「席位协议」发生的。**
#:
#:   Adams #131 自己的工作区里放着一页 `evals/DELTA-READ-ME-FIRST.md`，逐字写着：
#:     「记录的 delta 是 +0.2922。**那个数不能当『比裸模型强』的证据用**。」
#:     有 rubric（**冻结协议 D/E，发布门读的就是这个**）0.909/0.617 ⇒ **+0.2922**
#:     无 rubric（**同一批答案、同一 A/B、同一天**）      0.807/0.769 ⇒ **+0.0375**
#:     无 rubric 侧逐对只有 **胜 17 / 负 15** —— 接近抛硬币。
#:     席 D 点名 **8 题**、席 E 点名 **5 题**的评分标准**把答案抄了进去**
#:     （形态是中译与压缩，**字面比对的判据看不见，实测报 0/16**）。
#:
#:   而 **Adams 不在上面的 `TAINTED` 名单里** —— 名单只有 3 位。
#:   实测（同日）：全库 **24** 份非空 `evals/results.jsonl` 里，
#:   **席位恰好是 {seat-D-score-v1, seat-E-strict-v1} 的有 14 份**；
#:   这 14 份中 **`results.jsonl` 带 `rubric_fed` 字段的 0 份**，
#:   `evals/*.md` 里提到 rubric/泄题/污染字眼的**只有 3 份**（8 份的 README 只有 100 字）。
#:
#:   ⇒ **本工具报出的 delta，凡出自这两席的，都要连 Adams 那页一起读。**
#:     ★ 但**不能就此把 14 份全判成污染**：泄题是**每个人物自己的 rubric** 有没有抄进答案，
#:       **席位相同 ≠ rubric 相同**。这是**线索不是判定**。
#:     ★★ 要判得准，得给 `results.jsonl` 加 `rubric_fed` 字段（**产物格式变更，属决定**）。
#:   [[rubric-fed-judges-flip-the-sign]]｜[[implausibly-good-result-is-a-defect-report]]
RUBRIC_FED_SEATS = frozenset({"seat-D-score-v1", "seat-E-strict-v1"})
RUBRIC_FED_EVIDENCE = (
    "Adams #131 `evals/DELTA-READ-ME-FIRST.md`：同一批答案换掉 rubric 后 "
    "+0.2922 → +0.0375，逐对胜 17/负 15；席 D 点名 8 题、席 E 点名 5 题")

SCALE_HINT = 1.5   # 观测最大分 > 这个值 ⇒ 认为是 0–10 量纲，除以 10


def _norm(vals: list) -> tuple:
    """→ (归一化后的分数, 用的除数)。**按观测最大值判量纲。**"""
    if not vals:
        return [], 1.0
    div = 10.0 if max(vals) > SCALE_HINT else 1.0
    return [v / div for v in vals], div


def read_one(path: pathlib.Path) -> dict | None:
    """读一份 `results.jsonl` → 一条记录；读不出返回 None（**并说明为什么**）。"""
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return {"path": str(path), "错": f"读不了：{exc}"}
    rows = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except ValueError:
            continue
    if not rows:
        return {"path": str(path), "错": "0 行（空文件）—— **不是 delta=0**"}

    if "system" in rows[0]:
        arm = "bare_model" if any(str(d.get("system")) == "bare_model"
                                  for d in rows) else "baseline"
        cand = [d["overall_score"] for d in rows
                if str(d.get("system")) == "candidate" and "overall_score" in d]
        base = [d["overall_score"] for d in rows
                if str(d.get("system")) == arm and "overall_score" in d]
        seats = sorted({str(d.get("judge_id")) for d in rows if "judge_id" in d})
        shape = "长表"
    elif "candidate" in rows[0] and "baseline" in rows[0]:
        arm = "baseline"
        cand = [d["candidate"] for d in rows if isinstance(d.get("candidate"), (int, float))]
        base = [d["baseline"] for d in rows if isinstance(d.get("baseline"), (int, float))]
        seats = sorted({str(d.get("seat")) for d in rows if "seat" in d})
        shape = "宽表"
    else:
        return {"path": str(path), "错": f"形状不认识：键 {sorted(rows[0])[:6]}"}

    if not cand or not base:
        return {"path": str(path), "错": f"候选 {len(cand)} 条／对照 {len(base)} 条，算不出"}

    # ★★★★ **先读 `round` 与 `rubric_fed`——它们本来就在数据里。**
    #   2026-08-12 我先按席位去**猜**分组（D/E vs F/G），猜对了形状，
    #   而 Thomson 那份文件里白纸黑字有 `round` 与 `rubric_fed` 两个字段。
    #   按它们分组：`round3 / rubric_fed=False` → **−0.0859**，
    #   与台账记的诚实 delta **逐位吻合**；`rubric_fed=True` → +0.4084，正是那个不能用的数。
    #   ⇒ [[tool-existed-and-i-did-it-by-hand]] 的变体：**字段已经在了，我却去推**。
    #   现在的口径：**有 `rubric_fed` 就只取 False 的；有 `round` 就取最后一轮**；
    #   两者都没有时才退回席位分组（并把这件事标出来）。
    grouped, rule = {}, []
    if any("rubric_fed" in d for d in rows):
        rows = [d for d in rows if d.get("rubric_fed") is False]
        rule.append("只取 rubric_fed=False")
    if any("round" in d for d in rows):
        last = sorted({str(d.get("round")) for d in rows if "round" in d})[-1]
        rows = [d for d in rows if str(d.get("round")) == last]
        rule.append(f"只取最后一轮 {last}")
    if rule:
        # 用过滤后的行重算候选/对照
        if shape == "长表":
            cand = [d["overall_score"] for d in rows if str(d.get("system")) == "candidate"]
            base = [d["overall_score"] for d in rows if str(d.get("system")) == arm]
            seats = sorted({str(d.get("judge_id")) for d in rows if "judge_id" in d})
        else:
            cand = [d["candidate"] for d in rows if isinstance(d.get("candidate"), (int, float))]
            base = [d["baseline"] for d in rows if isinstance(d.get("baseline"), (int, float))]
            seats = sorted({str(d.get("seat")) for d in rows if "seat" in d})
        if not cand or not base:
            return {"path": str(path), "错": f"按「{' + '.join(rule)}」过滤后算不出"}

    # ★★★ 席位分组（**只在没有 round/rubric_fed 时才用**）：
    #   一份文件里可能压着两组互相矛盾的读数。
    #   Thomson #129 实测：席 D+E 是**有 rubric**（+0.4084），席 F+G 是**无 rubric**（−0.0859），
    #   而 4 席一起平均得 +0.1597 —— **一个既不是有 rubric 也不是无 rubric 的数**。
    #   台账白纸黑字写着「只有后者能用」。
    #   ⇒ 席数 > 2 时**必须分组报**，本件不替它选。
    #   （[[rubric-fed-judges-flip-the-sign]]：有无 rubric 会翻号，已在两个人物上复现。）
    per_seat = {}
    if len(seats) > 2 and not rule:
        key = "judge_id" if shape == "长表" else "seat"
        for sd in seats:
            sr = [d for d in rows if str(d.get(key)) == sd]
            if shape == "长表":
                sc = [d["overall_score"] for d in sr if str(d.get("system")) == "candidate"]
                sb = [d["overall_score"] for d in sr if str(d.get("system")) == arm]
            else:
                sc = [d["candidate"] for d in sr if isinstance(d.get("candidate"), (int, float))]
                sb = [d["baseline"] for d in sr if isinstance(d.get("baseline"), (int, float))]
            if sc and sb:
                dv = 10.0 if max(sc + sb) > SCALE_HINT else 1.0
                per_seat[sd] = round(statistics.mean([v / dv for v in sc])
                                     - statistics.mean([v / dv for v in sb]), 4)
    c, div = _norm(cand)
    b, _ = _norm(base + cand)          # ★ 两侧同一把尺子：合起来判量纲
    b = [v / div for v in base]
    rec = {"path": str(path), "形状": shape, "臂": arm, "席": seats,
           "案例": len(cand), "量纲除数": div,
           "口径": "、".join(rule) if rule else "全份（无 round／rubric_fed 字段）",
           "delta": round(statistics.mean(c) - statistics.mean(b), 4),
           # ★ 两条臂的**绝对分**（已归一到 0–1）。delta 是差，差看不出
           #   「候选变差」还是「对照本来就强」——那两件事的处置方向相反。
           "候选均": round(statistics.mean(c), 4),
           "对照均": round(statistics.mean(b), 4)}
    if per_seat:
        rec["★ 逐席"] = per_seat
        rec["★ 席数 > 2"] = ("**这份里可能压着两组不同条件的读数**（Thomson #129 实测："
                             "D/E 有 rubric、F/G 无 rubric，合并平均得到的数两边都不是）。"
                             "**合并值不可引用，去看逐席。**")
    return rec


def collect(root: pathlib.Path) -> dict:
    """扫全树 → `{人物: [记录…]}`。**同一内容的文件只算一次。**"""
    import hashlib
    out, seen = {}, set()
    for p in sorted(root.rglob("results.jsonl")):
        try:
            h = hashlib.sha256(p.read_bytes()).hexdigest()
        except OSError:
            h = str(p)
        who = next((q.name for q in p.parents if q.name.startswith("wip-")), p.parent.name)
        # ★★★ 2026-08-18：去重键从**内容哈希**改成 **(人物, 内容哈希)**。
        #   原来只按内容去重，本意是「同一人物的镜像副本只算一次」——**跨人物时就成了灾**：
        #   **所有空文件的 sha256 都是同一个**（`e3b0c442…`）。
        #   全库实测 **25 份 0 行的 `results.jsonl`**，原实现只报出第一个
        #   （`wip-benardos-128`），**另外 24 个人物整个不出现** ——
        #   读的人会以为它们「没有 results.jsonl」或「没什么可说的」，
        #   而实际上它们有一模一样的问题。**过滤让那一行整个消失。**
        # ★★ 不是取消去重：同一人物 + 同内容照样只算一次（镜像副本的本意保住）。
        #   [[filters-make-rows-vanish]]｜[[empty-default-swallows-unknown]]
        if (who, h) in seen:
            continue
        seen.add((who, h))
        rec = read_one(p)
        if rec:
            out.setdefault(who, []).append(rec)
    return out


def cross_check(recs: list) -> str:
    """同一人物的多份记录，**归一化后同臂的 delta 必须一致**。→ 不一致的说明，或 ""。"""
    by_arm = {}
    for r in recs:
        if "delta" not in r:
            continue
        by_arm.setdefault(r["臂"], []).append((r["形状"], r["delta"]))
    bad = []
    for arm, xs in by_arm.items():
        ds = {round(d, 4) for _, d in xs}
        if len(ds) > 1:
            bad.append(f"{arm}: " + "、".join(f"{s} {d:+.4f}" for s, d in xs))
    return "；".join(bad)


def self_test() -> int:
    import tempfile
    fails = []

    def chk(msg, cond):
        print(("  ✓ " if cond else "  ✗ ") + msg)
        if not cond:
            fails.append(msg)

    d = pathlib.Path(tempfile.mkdtemp())

    def w(name, rows):
        f = d / name
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
                     encoding="utf-8")
        return f

    print("══ 三种形状各读一遍 ══")
    # ① 长表（0–1），vs baseline
    lg = [{"case_id": f"c{i}", "judge_id": "F", "system": s, "overall_score": v}
          for i, (s, v) in enumerate([("candidate", 0.9), ("baseline", 0.8)] * 4)]
    r = read_one(w("a/results.jsonl", lg))
    chk(f"① 长表 vs baseline → 臂={r.get('臂')} delta={r.get('delta'):+.4f}（应 +0.1000，除数 1）",
        r.get("臂") == "baseline" and abs(r["delta"] - 0.1) < 1e-9 and r["量纲除数"] == 1.0)
    # ①a 两条臂的**绝对分**要在，且**方向不许反**（候选 0.9 高于对照 0.8）。
    #   只断言 delta 的话，把两个键写反也照样绿。
    chk(f"①a 绝对分 候选={r.get('候选均')} 对照={r.get('对照均')}（应 0.9 / 0.8，**不许写反**）",
        abs(r.get("候选均", -9) - 0.9) < 1e-9 and abs(r.get("对照均", -9) - 0.8) < 1e-9)
    chk("①b 候选均 − 对照均 == delta（同一把尺子，不是两处各算各的）",
        abs(r["候选均"] - r["对照均"] - r["delta"]) < 1e-9)

    # ② 长表 vs bare_model —— **不许当成 baseline**
    bm = [{"case_id": f"c{i}", "judge_id": "F", "system": s, "overall_score": v}
          for i, (s, v) in enumerate([("candidate", 0.9), ("bare_model", 0.5)] * 4)]
    r = read_one(w("b/results.jsonl", bm))
    chk(f"② 长表 vs **bare_model** → 臂={r.get('臂')}（**不许写成 baseline**）",
        r.get("臂") == "bare_model" and abs(r["delta"] - 0.4) < 1e-9)

    # ③ 宽表 0–10 —— 必须归一化
    wd = [{"case_id": f"c{i}", "seat": "seat-D", "candidate": 9.0, "baseline": 8.0}
          for i in range(4)]
    r = read_one(w("c/results.jsonl", wd))
    chk(f"③ 宽表 0–10 → 除数 {r.get('量纲除数')}、delta {r.get('delta'):+.4f}（应 +0.1000）",
        r["量纲除数"] == 10.0 and abs(r["delta"] - 0.1) < 1e-9)
    # ③a ★ 绝对分也必须**跟着归一**。delta 是差，差在两侧同乘 10 时看不出没归一；
    #   绝对分会——0–10 的原分直接漏出来就是 9.0 / 8.0。
    chk(f"③a 0–10 的绝对分要归一到 0–1：候选={r.get('候选均')} 对照={r.get('对照均')}（应 0.9 / 0.8）",
        abs(r["候选均"] - 0.9) < 1e-9 and abs(r["对照均"] - 0.8) < 1e-9)

    # ③′ ★★ 宽表**本来就是 0–1**（Barton 那份就是）——不许照除 10
    wd1 = [{"case_id": f"c{i}", "seat": "seat-D", "candidate": 0.9, "baseline": 0.8}
           for i in range(4)]
    r = read_one(w("d/results.jsonl", wd1))
    chk(f"③′ 宽表**已是 0–1** → 除数 {r.get('量纲除数')}（**按实测最大值判，不按形状判**）",
        r["量纲除数"] == 1.0 and abs(r["delta"] - 0.1) < 1e-9)

    print("══ 读不出来的，要说为什么 ══")
    r = read_one(w("e/results.jsonl", []))
    chk("④ 空文件 → 报「0 行（空文件）」，**不是 delta=0**",
        "错" in r and "空文件" in r["错"])
    r = read_one(w("f/results.jsonl", [{"case_id": "x", "foo": 1}]))
    chk("⑤ 形状不认识 → 报出它的键，不静默跳过", "错" in r and "形状不认识" in r["错"])
    r = read_one(w("g/results.jsonl",
                   [{"case_id": "x", "judge_id": "F", "system": "candidate",
                     "overall_score": 0.9}]))
    chk("⑥ 只有候选没有对照 → 报「算不出」", "错" in r and "算不出" in r["错"])

    print("══ ★★ 席位分组：一份文件里压着两组不同条件的读数 ══")
    # 复刻 Thomson #129 的形状：D/E 有 rubric（高）、F/G 无 rubric（低），
    # 合并平均得到的数**两边都不是**。
    mix = []
    for i in range(4):
        for sd, cv, bv in (("D", 0.95, 0.55), ("E", 0.95, 0.55),
                           ("F", 0.60, 0.68), ("G", 0.60, 0.68)):
            mix += [{"case_id": f"c{i}", "judge_id": sd, "system": "candidate",
                     "overall_score": cv},
                    {"case_id": f"c{i}", "judge_id": sd, "system": "baseline",
                     "overall_score": bv}]
    r = read_one(w("h/results.jsonl", mix))
    ps = r.get("★ 逐席", {})
    chk(f"⑩ 席数 4 → **逐席分开报**（{ps}）",
        set(ps) == {"D", "E", "F", "G"}
        and abs(ps["D"] - 0.40) < 1e-9 and abs(ps["F"] + 0.08) < 1e-9)
    chk("⑩′ 合并值被明确标为**不可引用**", "★ 席数 > 2" in r and "不可引用" in r["★ 席数 > 2"])
    chk(f"⑩″ 而合并值 {r['delta']:+.4f} 两边都不是（D/E {ps['D']:+.4f}、F/G {ps['F']:+.4f}）"
        f"——**这正是它必须分组的理由**",
        min(ps.values()) < r["delta"] < max(ps.values()))
    # 反向：2 席时**不分组**（否则每份都要人去读逐席，噪声淹掉信号）
    two = [{"case_id": f"c{i}", "judge_id": sd, "system": s, "overall_score": v}
           for i in range(4) for sd in ("F", "G")
           for s, v in (("candidate", 0.9), ("baseline", 0.8))]
    r2 = read_one(w("i/results.jsonl", two))
    chk("⑩‴ 反向：2 席 → **不分组**（只有 >2 席才可能压着两组条件）", "★ 逐席" not in r2)

    print("══ 交叉校验：同一人物两种形状必须一致 ══")
    ok = cross_check([{"臂": "baseline", "形状": "长表", "delta": 0.1},
                      {"臂": "baseline", "形状": "宽表", "delta": 0.1}])
    chk("⑦ 归一化后一致 → 不报", ok == "")
    bad = cross_check([{"臂": "baseline", "形状": "长表", "delta": 0.1},
                       {"臂": "baseline", "形状": "宽表", "delta": 1.0}])
    chk(f"⑦′ 归一化后仍差 10 倍 → **报出来**（{bad[:40]}…）", bool(bad))
    # ⑦″ 两条臂各自一致时，**不许因为两臂不同就报错**
    ok2 = cross_check([{"臂": "baseline", "形状": "长表", "delta": 0.1},
                       {"臂": "bare_model", "形状": "长表", "delta": 0.9}])
    chk("⑦″ 两条臂数不同 → **不报**（它们本来就不是一个量）", ok2 == "")

    print("══ 去重与污染标记 ══")
    same = [{"case_id": "c0", "judge_id": "F", "system": "candidate", "overall_score": 0.9},
            {"case_id": "c0", "judge_id": "F", "system": "baseline", "overall_score": 0.8}]
    w("wip-x-1/evals/results.jsonl", same)
    w("wip-x-1/round2/results.jsonl", same)     # 同内容副本
    got = collect(d / "wip-x-1")
    chk(f"⑧ 同内容的两份只算一次（得 {sum(len(v) for v in got.values())} 条）",
        sum(len(v) for v in got.values()) == 1)
    chk("⑨ 污染名单是**名单不是判据**：每条都带出处",
        all(isinstance(v, str) and v for v in TAINTED.values()))
    chk("⑩ ★ 席位线索是**闭集合**且非空（不靠措辞匹配）",
        isinstance(RUBRIC_FED_SEATS, frozenset) and len(RUBRIC_FED_SEATS) >= 2)
    chk("⑪ ★★ 席位线索与污染名单**不是同一件事**（前者按席、后者按人，不许互相顶替）",
        not (set(TAINTED) & RUBRIC_FED_SEATS) and bool(RUBRIC_FED_EVIDENCE.strip()))

    # ★★★ ⑫⑬ 2026-08-18：去重键曾经只有内容哈希 —— **所有空文件哈希相同**，
    #   于是全库 25 份 0 行的 `results.jsonl` 只报出第一个，**24 个人物整个消失**。
    #   这两条把那次反例钉死：跨人物不许互吞，同人物仍要去重。
    _t = pathlib.Path(tempfile.mkdtemp())
    for _who, _body in (("wip-x-1", ""), ("wip-y-2", ""),
                        ("wip-z-3", '{"seat":"seat-D-score-v1","case_id":"c",'
                                    '"suite":"s","candidate":0.8,"baseline":0.7}\n')):
        _d = _t / _who / "evals"
        _d.mkdir(parents=True)
        (_d / "results.jsonl").write_text(_body, encoding="utf-8")
    _g = collect(_t)
    chk("⑫ **两个人物各有一个空 `results.jsonl` ⇒ 两个都要出现**"
        "（去重键只有内容哈希时，第二个会被吞掉）",
        sorted(_g) == ["wip-x-1", "wip-y-2", "wip-z-3"])

    _t2 = pathlib.Path(tempfile.mkdtemp())
    _b = ('{"seat":"seat-D-score-v1","case_id":"c","suite":"s",'
          '"candidate":0.8,"baseline":0.7}\n')
    for _sub in ("evals", "references/evals"):
        _d = _t2 / "wip-w-4" / _sub
        _d.mkdir(parents=True)
        (_d / "results.jsonl").write_text(_b, encoding="utf-8")
    chk("⑬ **同一人物两处镜像副本、内容相同 ⇒ 仍然只算一次**（去重的本意要保住）",
        all(len(v) == 1 for v in collect(_t2).values()))

    print("\n" + ("✓ 自测全过" if not fails else f"✗ **{len(fails)} 条不合**"))
    return 0 if not fails else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("root", nargs="?", type=pathlib.Path,
                    help="语料根（含 wip-* 的那一层）")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--exclude-tainted", action="store_true",
                    help="剔掉已知「看过 rubric 才写基线」的读数（默认只标记）")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.root or not a.root.is_dir():
        print("用法错误：需要语料根目录（或 --self-test）", file=sys.stderr)
        return 3

    data = collect(a.root)
    bad_cross, out = {}, {}
    for who, recs in sorted(data.items()):
        msg = cross_check(recs)
        if msg:
            bad_cross[who] = msg
        best = {}
        for r in recs:
            if "delta" not in r:
                continue
            best.setdefault(r["臂"], r)
        if best:
            first = best[list(best)[0]]
            out[who] = {"臂": {k: v["delta"] for k, v in best.items()},
                        "口径": first.get("口径", ""),
                        "形状": sorted({r.get("形状") for r in recs if "形状" in r}),
                        "席": best[list(best)[0]]["席"],
                        "案例": best[list(best)[0]]["案例"]}
            if who in TAINTED:
                out[who]["★ 污染"] = TAINTED[who]
            # ★ 席位线索（**不是判定**）：这份读数出自那两席吗
            if set(out[who].get("席") or []) & RUBRIC_FED_SEATS:
                out[who]["★ 席位线索"] = "出自 %s" % "/".join(sorted(RUBRIC_FED_SEATS))
            if any("★ 逐席" in r for r in recs):
                ps = next(r["★ 逐席"] for r in recs if "★ 逐席" in r)
                out[who]["★ 合并值不可引用"] = ps
        errs = [r["错"] for r in recs if "错" in r]
        if errs:
            out.setdefault(who, {})["★ 读不出的份"] = errs

    if a.exclude_tainted:
        out = {k: v for k, v in out.items() if k not in TAINTED}

    if a.json:
        print(json.dumps({"人物": out, "**两种形状对不上**": bad_cross},
                         ensure_ascii=False, indent=1))
        return 1 if bad_cross else 0

    print(f"人物 {len(out)} 个｜口径：**按观测最大分判量纲（>{SCALE_HINT} 则 /10）、"
          f"两条臂分开列、同内容文件只算一次**\n")
    print(f"{'人物':<24}{'vs 基线':>10}{'vs 裸模型':>11}{'席':>4}{'案例':>5}  形状")
    for who, v in out.items():
        arms = v.get("臂", {})
        b = f"{arms['baseline']:+.4f}" if "baseline" in arms else "—"
        m = f"{arms['bare_model']:+.4f}" if "bare_model" in arms else "—"
        tag = "  ★污染" if "★ 污染" in v else ""
        if "★ 合并值不可引用" in v:
            tag += "  ★★**合并值不可引用**（>2 席且无 round/rubric_fed，去看逐席）"
        print(f"{who:<24}{b:>10}{m:>11}{len(v.get('席', [])):>4}{v.get('案例', 0):>5}  "
              f"{'/'.join(v.get('形状', []))}{tag}")
    if bad_cross:
        print(f"\n✗ **{len(bad_cross)} 个人物的两种形状归一化后仍对不上**：")
        for k, msg in bad_cross.items():
            print(f"   {k}: {msg}")
        return 1
    print("\n✓ 凡是同时有两种形状的人物，归一化之后**逐个吻合**")
    nz = [k for k, v in out.items() if "★ 合并值不可引用" in v]
    if nz:
        print(f"\n★★ **{len(nz)} 个人物的合并值不可引用**（>2 席且文件里没有 round/rubric_fed）：")
        for k in nz:
            print(f"   {k}：逐席 {out[k]['★ 合并值不可引用']}")
        print("   —— Thomson #129 实测：席分两组时合并平均得到的数**两边都不是**。")
    if not a.exclude_tainted and any("★ 污染" in v for v in out.values()):
        print("★ 带「污染」标记的是已知「看过 rubric 才写基线」的读数——"
              "**只标记不剔除**，要剔加 `--exclude-tainted`。")

    # ★★★★ 席位线索：**污染名单按人物列，而泄题按席位协议发生**
    cued = sorted(k for k, v in out.items() if "★ 席位线索" in v)
    unlisted = [k for k in cued if k not in TAINTED]
    if cued:
        print("\n★★ **席位线索（不是判定）**：**%d** 份读数出自 `%s`；"
              % (len(cued), "/".join(sorted(RUBRIC_FED_SEATS))))
        print("   其中**不在污染名单里**的 **%d** 份：%s"
              % (len(unlisted), "、".join(unlisted) or "无"))
        print("   依据：%s" % RUBRIC_FED_EVIDENCE)
        print("   ⇒ **凡出自这两席的 delta，都要连 Adams 那页 "
              "`evals/DELTA-READ-ME-FIRST.md` 一起读。**")
        print("   ★ 但**不能就此把它们全判成污染**：泄题是**每个人物自己的 rubric** "
              "有没有把答案抄进去，**席位相同 ≠ rubric 相同**。")
        # ★ **现算，不写死**：口径串里带「无 round／rubric_fed 字段」的就是没有该字段的那批。
        #   我第一版直接写「实测这 N 份一份都没有」——**那个数我没算过**，
        #   而且我手工只扫了 `evals/results.jsonl`（15 份），本工具的扫描面更宽。
        #   [[self-reported-numbers-must-be-computed]]
        no_field = sum(1 for k in cued if "rubric_fed" in str(out[k].get("口径", ""))
                       and "无" in str(out[k].get("口径", "")))
        print("   ★★ 要判得准得给 `results.jsonl` 加 `rubric_fed` 字段 —— "
              "这 %d 份里**明确记着「无 round／rubric_fed 字段」的有 %d 份**"
              "（**产物格式变更，属决定**）。" % (len(cued), no_field))
    return 0


if __name__ == "__main__":
    sys.exit(main())
