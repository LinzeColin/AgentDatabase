#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**答案的表面特征不许成为指认候选侧的信号。**

## 为什么有这道判据

盲判的前提是评委看不出哪一侧是候选。**只要存在一条「不读内容就能用」的规则，
而它在多数题上都指对，这份盲判就不盲**——评委不必理解答案，套规则就能猜中。

本判据检两类通道，**判据相同、只是特征不同**：

- **长度**（v0.0.0.51 起）：候选是不是题题都更长（或都更短）
- **格式**（★ 2026-08-04 新增）：候选是不是题题都带粗体/反引号/项目符号/标题行，
  而基线是裸散文

两类都用同一个量：**「某条单一表面规则能指对多少题」**。

## 两次实测，两次都是 32/32

| | 通道 | 实测 | 谁发现的 |
|---|---|---|---|
| Lister #108 R3 | 长度 | 候选 +144%，**32/32 全部更长** | 席 D |
| **Barton #117 R3** | **格式** | 候选 32/32 带标记（均 10.2 个），**基线 0/32** | **席 E** |

Barton 那轮长度是干净的（均长比 0.89、更短 23/32=72%，两条都在界内），
判据打印「✓ 长度指不出哪一侧是哪个系统」——**那句话就长度而言没错，
但它让人以为盲判成立，而实际上一条正则 `\\*\\*|`` ` 把 32 题全分开了。**

**回查了四个留有载荷的人物，合计 116/128 = 91% 的题可被这条正则指认**
（Barton 32/32、Nightingale 30/32、Fleming 28/32、Osler 26/32）。
**不是某个人物的失误，是这条判据一直漏了一整类通道。**
成因很朴素：候选答案由本流水线写成 Markdown，基线由裸模型写成散文。

## 判据

对每条通道算**「定向可利用率」**＝ `max(只有候选具备的题数, 只有基线具备的题数) / 共有题数`
——即固定规则「带此特征的那侧是候选」能稳赢的比例。

- **每条通道的定向可利用率 ≤ 75%**（等价于该规则至少四分之一的题会指错）
- 长度另有总量约束：**均长比 ∈ [0.77, 1.30]**、**候选更短占比 ∈ [25%, 75%]**

阈值与长度那条同源：`shorter_frac ∈ [25%, 75%]` 本就是在说
「这条启发式必须有四分之一以上会错」。**新通道沿用同一条判据，不是新标准。**

## 它判不了什么

- **它不判「候选是不是靠表面特征赢的」**。全过也可能是篇幅或排版在起作用——
  它只保证**没有哪一条单一表面规则指得准**，不保证这些特征不影响分数。
  后者要靠等长同体裁基线，那会改变对照的定义，**是人的决定**。
- **它只认得列出来的那几条通道。** 席 E 是靠人读出来的格式通道；
  **下一条通道大概率也得靠人先看见**。判据全绿只说明「已知通道都堵上了」。
- **中英混排下「字数」按字符算**，一个汉字与一个字母同权。
  同一人物内部前后一致即可比，**跨人物比这个数没有意义**。
"""
import argparse
import json
import pathlib
import re
import sys

MAX_AGG = 1.30
MIN_AGG = 1 / MAX_AGG          # ★ 对称下界 ≈0.77
MIN_SHORTER = 0.25
MAX_SHORTER = 1 - MIN_SHORTER  # ★ 对称上界 0.75

# 格式通道的上限与 MAX_SHORTER 同源：单一规则至少四分之一的题要指错
MAX_EXPLOIT = 0.75

# ★ 每条通道是一个「不读内容就能用」的表面特征。
#   `粗体/反引号` 是席 E 在 Barton #117 实际用来分组的那条；
#   `空行分段` 与 `破折号` 是随后逐通道实测找出来的——**它们不是补齐凑数**：
#     空行分段  Barton **81%（超门）**、Nightingale 50%（方向还相反）
#     破折号    Osler 56% / Fleming 56% / Nightingale 59%，**三人同向偏候选**
CHANNELS = {
    "粗体/反引号": re.compile(r"\*\*|`"),
    "项目符号":   re.compile(r"^\s*(?:[-*+•]|\d+[.)、])\s+", re.M),
    "标题行":     re.compile(r"^\s*#{1,6}\s+", re.M),
    "空行分段":   re.compile(r"\n\s*\n"),
    "破折号":     re.compile(r"——"),
}

# ★★ 直角引号「」**故意不列为通道**，这是量过之后的决定，不是遗漏。
#   四人实测可利用率 16% / 19% / 31% / 31%，**都远在门下**——两侧都在用。
#   而 `check_verbatim_quotes` / `check_quote_locator` 正是靠 `「…」`
#   认出「这里有一条逐字引文」的。**若为了「更不像 Markdown」把引号也去掉，
#   等于把三道引文判据一起弄瞎**，它们会因为找不到引文而静默通过。
#
# ★★★ 2026-08-05 更正射程（Carver #127）：上面那句「两侧都在用」**在本人物身上不成立**。
#   实测 **候选 15/16、基线 2/16 → 可利用 81%**，远超门，与此前四人（16/19/31/31%）
#   完全不同量级。根因不难懂：**候选之所以带引号，是因为它在引语料；
#   基线没有语料可引。** 这不是格式习惯的差别，是**有没有根据**的差别。
#
#   所以本件**照旧不把「」列为拦截通道**（删引号会弄瞎引文判据，那个代价更大），
#   但**必须把这个数报出来**——沉默会让「✓ 已知通道都堵上了」被读成「盲判是干净的」。
#   ★ 它是**只报不拦**：改法只能是「让基线也有根据可引」或「接受并记为残余泄题」，
#     **绝不是把候选的引号删掉**。
QUOTE_MARK = re.compile(r"「[^」]{4,}」|\u201c[^\u201d]{4,}\u201d")
#   **逐字引文继续用「」，这是判据之间已经核过的相容点。**


def measure(cand: dict, base: dict) -> dict:
    """→ {共有题数, 总体均长比, 候选更短的题数, 更短占比, 逐题最大比, 各通道定向可利用率}。"""
    keys = [k for k in cand if k in base]
    if not keys:
        return {}
    tc = sum(len(cand[k]) for k in keys)
    tb = sum(len(base[k]) for k in keys)
    shorter = sum(1 for k in keys if len(cand[k]) < len(base[k]))
    ratios = sorted(((len(cand[k]) / max(len(base[k]), 1), k) for k in keys), reverse=True)

    surface = {}
    for name, rx in CHANNELS.items():
        c_only = sum(1 for k in keys if rx.search(cand[k]) and not rx.search(base[k]))
        b_only = sum(1 for k in keys if rx.search(base[k]) and not rx.search(cand[k]))
        surface[name] = {
            "cand_only": c_only, "base_only": b_only,
            "exploit": max(c_only, b_only) / len(keys),
            "side": "候选" if c_only >= b_only else "基线",
            "cand_n": sum(1 for k in keys if rx.search(cand[k])),
            "base_n": sum(1 for k in keys if rx.search(base[k])),
        }

    qc = sum(1 for k in keys if QUOTE_MARK.search(cand[k]))
    qb = sum(1 for k in keys if QUOTE_MARK.search(base[k]))
    q_only_c = sum(1 for k in keys if QUOTE_MARK.search(cand[k]) and not QUOTE_MARK.search(base[k]))
    q_only_b = sum(1 for k in keys if QUOTE_MARK.search(base[k]) and not QUOTE_MARK.search(cand[k]))
    quote_mark = {"cand_n": qc, "base_n": qb,
                  "exploit": max(q_only_c, q_only_b) / len(keys),
                  "side": "候选" if q_only_c >= q_only_b else "基线"}

    return {"n": len(keys), "agg": tc / max(tb, 1), "quote_mark": quote_mark,
            "shorter": shorter, "shorter_frac": shorter / len(keys),
            "worst": ratios[0], "cand_chars": tc, "base_chars": tb,
            "surface": surface}


def verdict(m: dict) -> list:
    """→ 未过的条目列表；空表示都过。

    ★★ 2026-08-04 加入格式通道。此前只检长度，
    而**「表面特征指不指得出哪一侧」从来不只有长度一条**。
    Barton #117 第 3 轮长度两条都过，格式却 32/32 全分开——
    **判据打了绿灯，盲判其实已经破了。**

    ★★ 2026-08-04 早些时候改为**双向**。此前只防「候选更长」一个方向：
    `agg` 只有上界、`shorter_frac` 只有下界。
    #117 Barton 实测：均长比 **0.67**、候选更短 **31/32 = 97%**，
    两条都过、并打印「✓ 长度指不出哪一侧是哪个系统」——**那句话是错的**，
    97% 一边倒和 97% 倒向另一边一样能指认。
    """
    bad = []
    if m["agg"] > MAX_AGG:
        bad.append(f"**总体均长比 {m['agg']:.2f} > {MAX_AGG}**——整体靠篇幅取胜")
    elif m["agg"] < MIN_AGG:
        bad.append(f"**总体均长比 {m['agg']:.2f} < {MIN_AGG:.2f}**"
                   "——候选整体过短，长度同样会变成指认信号（**反方向的同一个问题**）")
    if m["shorter_frac"] < MIN_SHORTER:
        bad.append(f"**候选更短的题只有 {m['shorter']}/{m['n']} = "
                   f"{m['shorter_frac']:.0%}，要 ≥{MIN_SHORTER:.0%}**"
                   "——长度会变成指认候选的信号")
    elif m["shorter_frac"] > MAX_SHORTER:
        bad.append(f"**候选更短的题多达 {m['shorter']}/{m['n']} = "
                   f"{m['shorter_frac']:.0%}，要 ≤{MAX_SHORTER:.0%}**"
                   "——一边倒同样能指认，只是倒的方向反了")

    for name, s in m.get("surface", {}).items():
        if s["exploit"] > MAX_EXPLOIT:
            bad.append(f"**「{name}」能指认 {max(s['cand_only'], s['base_only'])}/{m['n']} = "
                       f"{s['exploit']:.0%} 的题（要 ≤{MAX_EXPLOIT:.0%}）**"
                       f"——「带此特征的是{s['side']}」这条规则不读内容就能稳赢"
                       f"（候选 {s['cand_n']}/{m['n']} 带，基线 {s['base_n']}/{m['n']} 带）")
    return bad


# ══════════════════ 自测 ══════════════════
# 夹具是**实测数据的形状**，不是编的：
#   Lister #108 R3：候选 +144%，32/32 全长（席 D：长度是完美泄题信号）
#   Osler  #110 R3：均长比 1.30，14/32 更短（两席均报「长度指不出哪一侧」）
#   Barton #117 R3：格式 32/0（席 E：一行正则 32 题干净分开）

def _mk(n: int, ratio: float, shorter: int) -> tuple:
    """造一对答案：总体比约为 ratio，其中 shorter 道候选更短。**两侧都不带格式标记。**"""
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


def _mark(pairs: tuple, cand_marked: int, base_marked: int) -> tuple:
    """给一对答案加格式标记：候选前 cand_marked 道带、基线前 base_marked 道带。"""
    cand, base = pairs
    ks = sorted(cand)
    for i, k in enumerate(ks):
        if i < cand_marked:
            cand[k] = "**" + cand[k] + "**"
        if i < base_marked:
            base[k] = "**" + base[k] + "**"
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

    print("── ★★ 正向：**Barton #117 的真实格式形状（候选 32 带、基线 0 带）→ 必须报** ──")
    #   这一组**长度全部合格**（0.89 / 23 更短 = 72%），改前一条都不报，
    #   还打印「✓ 长度指不出哪一侧是哪个系统」——**盲判其实已经破了**。
    cand, base = _mark(_mk(32, 0.89, 23), 32, 0)
    m = measure(cand, base)
    bad = verdict(m)
    chk(f"长度两条仍过（{m['agg']:.2f} / {m['shorter_frac']:.0%}）"
        f"但格式可利用 {m['surface']['粗体/反引号']['exploit']:.0%} → **报出且只报格式那一条**",
        len(bad) == 1 and "粗体/反引号" in bad[0])

    print("── ★ 正向：Fleming #111 的形状（候选 32 带、基线 4 带）→ 88% 仍要报 ──")
    cand, base = _mark(_mk(32, 1.00, 16), 32, 4)
    m = measure(cand, base)
    chk("28/32 = 88% > 75% → 报出（**基线也带一点也救不了**）",
        any("粗体/反引号" in b for b in verdict(m)))

    print("── ★★ 反向对照 ⓪：**Barton #117 早先的长度形状（0.67，31/32 更短）→ 必须报** ──")
    #   改前这一组两条都过，还打印「✓ 长度指不出哪一侧」——**那句话是错的**。
    m = {"n": 32, "agg": 0.67, "shorter": 31, "shorter_frac": 31 / 32,
         "worst": 1.07, "cand_chars": 6093, "base_chars": 9081, "surface": {}}
    b = verdict(m)
    chk("候选整体过短 + 一边倒 → **两条都要报**（此前一条都不报）", len(b) == 2)

    print("── 反向对照 ①：Osler #110 第 3 轮的形状（1.30，14/32 更短）→ 不许报 ──")
    cand, base = _mk(32, 1.30, 14)
    m = measure(cand, base)
    chk(f"均长比 {m['agg']:.2f} ≤ {MAX_AGG} 且更短 {m['shorter']}/32 = "
        f"{m['shorter_frac']:.0%} ≥ {MIN_SHORTER:.0%}、两侧均无格式标记 → 一条不报",
        not verdict(m))

    print("── 反向对照 ②：候选偏短但**没到一边倒**，不许报（判的是泄题，不是长短）──")
    #   ★ 本条原为「均长比 0.70、更短 28/32 → 一条不报」。
    #     **那个前提在 2026-08-04 被 Barton #117 推翻**：0.70 加 28/32 正是一边倒，
    #     长度照样指得出哪一侧。旧夹具把「候选更短」当成天然无害，
    #     而判据要防的是**任一方向的一边倒**。
    cand, base = _mk(32, 0.85, 20)
    m2 = measure(cand, base)
    chk(f"均长比 {m2['agg']:.2f} ≥ {MIN_AGG:.2f} 且更短 {m2['shorter']}/32 = "
        f"{m2['shorter_frac']:.0%} ≤ {MAX_SHORTER:.0%} → 一条不报",
        not verdict(m2))

    print("── ★ 反向对照 ③：**两侧都带格式标记 → 不许报**（判的是可指认，不是排版本身）──")
    cand, base = _mark(_mk(32, 1.00, 16), 32, 32)
    m3 = measure(cand, base)
    chk(f"候选 32/32 带、基线 32/32 带 → 定向可利用 "
        f"{m3['surface']['粗体/反引号']['exploit']:.0%}，一条不报", not verdict(m3))

    print("── ★ 反向对照 ④：**格式一边倒但方向相反 → 同样要报**（对称）──")
    cand, base = _mark(_mk(32, 1.00, 16), 0, 32)
    m4 = measure(cand, base)
    s4 = m4["surface"]["粗体/反引号"]
    chk(f"基线 32 带、候选 0 带 → 报出且指明是「{s4['side']}」侧",
        any("粗体/反引号" in b for b in verdict(m4)) and s4["side"] == "基线")

    print("── ★ 反向对照 ⑤：恰好 75% 可利用 → 放行；78% → 报出 ──")
    cand, base = _mark(_mk(32, 1.00, 16), 24, 0)
    chk("24/32 = 75% 恰在门上 → 不报", not verdict(measure(cand, base)))
    cand, base = _mark(_mk(32, 1.00, 16), 25, 0)
    chk("25/32 = 78% > 75% → 报出",
        any("粗体/反引号" in b for b in verdict(measure(cand, base))))

    print("── 反向对照 ⑥：边界值——恰好等于长度门槛的一律放行 ──")
    m = {"n": 32, "agg": MAX_AGG, "shorter": 8, "shorter_frac": MIN_SHORTER,
         "worst": (1.0, "q"), "cand_chars": 0, "base_chars": 0, "surface": {}}
    chk(f"agg 恰为 {MAX_AGG}、更短占比恰为 {MIN_SHORTER:.0%} → 不报", not verdict(m))
    m2 = dict(m, agg=MAX_AGG + 0.01)
    chk("超出门槛 0.01 → 报出", len(verdict(m2)) == 1)
    m3 = dict(m, shorter=7, shorter_frac=7 / 32)
    chk(f"更短 7/32 = {7/32:.1%} < {MIN_SHORTER:.0%} → 报出", len(verdict(m3)) == 1)

    print("── 反向对照 ⑦：两侧题号对不上时不许沉默通过 ──")
    chk("无共有题号 → measure 返回空，由调用方按 exit 3 处理",
        measure({"a": "x"}, {"b": "y"}) == {})

    print("── 反向对照 ⑧：单题也要能算，不许除零 ──")
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
    print(f"表面特征（定向可利用率，门 ≤{MAX_EXPLOIT:.0%}）：")
    for name, s in m["surface"].items():
        flag = "  ← **可指认**" if s["exploit"] > MAX_EXPLOIT else ""
        print(f"  {name:<12} 候选 {s['cand_n']:>2}/{m['n']}　基线 {s['base_n']:>2}/{m['n']}"
              f"　可利用 {s['exploit']:.0%}{flag}")

    q = m.get("quote_mark")
    if q:
        hot = "  ← **超门，但本件不拦**" if q["exploit"] > MAX_EXPLOIT else ""
        print(f"  {'「」直角引号':<12} 候选 {q['cand_n']:>2}/{m['n']}　基线 {q['base_n']:>2}/{m['n']}"
              f"　可利用 {q['exploit']:.0%}（**只报不拦**）{hot}")
        if q["exploit"] > MAX_EXPLOIT:
            print("    ★ 候选带引号是因为**它在引语料**，基线没有语料可引——"
                  "这是「有没有根据」的差别，不是格式习惯的差别。")
            print("    ★★ 改法只有两条：让基线也有据可引，或**接受并记为残余泄题**。"
                  "**绝不是把候选的引号删掉**——那会同时弄瞎三道引文判据。")

    bad = verdict(m)
    if not bad:
        print("\n  ✓ 已检的表面特征都指不出哪一侧是哪个系统"
              "（**只说明已知通道堵上了，不代表没有别的通道**）")
        return 0
    for b in bad:
        print("✗ " + b)
    print("\n**表面特征不许成为泄题信号，超了就重写，不打警告了事。**")
    return 1


if __name__ == "__main__":
    sys.exit(main())
