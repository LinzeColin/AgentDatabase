#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**值得开工名单**：在抓源之前，把 50 个 pending 排一遍序。

## 它只用「开工前就知道的东西」

| 轴 | 开工前算得出来吗 | 依据 |
|---|---|---|
| **出版年 / PD** | **能** | `_卒年.json`（204 人，带 Wikidata 出处） |
| **分族历史出货率** | **能** | registry 实际产物数 ÷（产物 + 延后） |
| 声口 own_voice | **不能** | 要抓完源才有数 |
| 一手源占比 | **不能** | 同上 |
| min_lanes 道数 | **不能** | 同上 |

★ **后三项不是被忽略，是开工前取不到。**
  它们是**抓源后的第一个检查点**——量出来不达标就当场结案，
  不要走到合成再发现（Sellers #154 是开工前量的，省下了整轮；
  Coffin #130 是走到判分才发现声口不够）。

## PD 判法

本项目分界：出版于 ≤ `THIS_YEAR − 95`（2026 年是 1931，随年份滚动）。

- **卒年 ≤ 1930** → 他不可能在分界之后出版，**全部作品必然在界内**。绿。
- **卒年 1931 及以后** → 晚期作品可能越界，**要逐作品定位出版年**。黄。
- **在世 / 卒年不详** → 红（在世无到期日）／先补年份（不用下载，查 Wikidata）。

## 分族出货率的用法与射程

出货率 = registry 里该族产物数 ÷（该族产物数 + 该族延后数）。

★ **它是历史频率，不是这个人的概率。** 低出货率族里照样有能出货的人
（材料建工师 11 连延后之后仍有 Carver 那样的高 delta 人物在别的族）。
它只用来在「PD 同为绿灯」的人之间排先后，**不用来否决任何人**。

用法：`python3 worth_starting.py [--top N]`
"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
LED = HERE.parent
ROOT = LED.parent.parent.parent            # …/CodexSkills
REG = ROOT / "registry/codex/persona-distiller-group"
PD_CUTOFF = 1930                           # 出版于 ≤ 这一年必在公有领域（2026 口径）


def load_years() -> dict:
    p = LED / "_卒年.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}


def load_deferred() -> list:
    p = LED / "_延后名单.json"
    if not p.is_file():
        return []
    d = json.loads(p.read_text(encoding="utf-8"))
    return d.get("deferred", []) if isinstance(d, dict) else d


def load_pending() -> list:
    """问 `next_person.py`，**不自己重算队列**。"""
    out = subprocess.run([sys.executable, str(HERE / "next_person.py"), "--show", "999"],
                         capture_output=True, text=True)
    if out.returncode != 0:
        raise SystemExit(f"next_person.py 失败 rc={out.returncode}：{out.stderr[:300]}")
    return json.loads(out.stdout).get("upcoming", [])


def family_rates(deferred: list) -> dict:
    """`{族: (产物数, 延后数, 出货率)}`。产物数按 registry 实际目录数。"""
    shipped = {}
    if REG.is_dir():
        for fam in REG.iterdir():
            if fam.is_dir():
                shipped[fam.name] = sum(1 for x in fam.iterdir() if x.is_dir())
    defer = {}
    for r in deferred:
        fam = r.get("family_zh") or "?"
        defer[fam] = defer.get(fam, 0) + 1
    out = {}
    for fam in set(shipped) | set(defer):
        s, d = shipped.get(fam, 0), defer.get(fam, 0)
        out[fam] = (s, d, s / (s + d) if (s + d) else 0.0)
    return out


def classify(person: dict, years: dict) -> tuple:
    """→ `(灯, 理由)`。灯 ∈ 绿／黄／红／补年份。

    ★★ 2026-08-12 首跑就抓到自己一个缺陷：Solon／Confucius／Plato 被判成
      **「卒年缺；在世则无到期日」**——而他们分别卒于公元前 6/5/4 世纪。
      根因：`_卒年.json` 对**精度低于年**的 Wikidata 日期按规则留空
      （`0428-00-00 BC(十年精度)` → `died: null`），而我只看 `died` 这一个字段，
      于是「日期精度不够」被读成了「可能还活着」。
      **`source` 串里白纸黑字有 ` BC`**——要读那一栏，而不是拿空值当答案。
      ⇒ [[empty-default-swallows-unknown]] 的又一例：`null` 被读成了一个断言。
    """
    rec = years.get(person["name"].strip().lower())
    if rec is None:
        return "补年份", "卒年表里没有他——查 Wikidata 即可，**不用下载任何文件**"
    if rec.get("alive") is True:
        return "红", "**在世**（记录里 `alive: true`）——无到期日，本项目不做"
    died = rec.get("died")
    if died is None:
        # 日期精度低于年 → 留空。**公元前的人不是「不详」。**
        if " BC" in str(rec.get("source", "")):
            return "绿", "卒年因精度低于年而留空，但 `source` 是 **BC 纪年**，**必在界内**"
        return "补年份", f"卒年留空且来源无 BC 纪年（born={rec.get('born')}）——先补年份"
    if died <= PD_CUTOFF:
        return "绿", f"卒于 {died} ≤ {PD_CUTOFF}，**全部作品必在界内**"
    return "黄", f"卒于 {died} > {PD_CUTOFF}，晚期作品可能越界，要逐作品定位出版年"


def attribution_flag(rec) -> str:
    """**归属必查**：PD 绿灯盖不住「这些字是不是他写的」。

    首跑把 **Socrates 排进了本批第 6 位**——而传世的全是别人的转录。
    这正是 ㉚（Maudslay「不留文本的人」）与延后类别「归属不成立」要问的事，
    **PD 那一轴对它完全无感**。

    ★ 本件**不替任何人下归属结论**（那要看一手源，属于零编造的射程）。
      它只做一件机械的事：把风险集中的那一档标出来——
      **卒于公元 500 年以前**的人，传世文本多经后人编纂／转录，
      开工前必须先答一句「他自己写的东西存世吗」，答不了就不开工。
    """
    if not rec:
        return ""
    died = rec.get("died")
    if (isinstance(died, int) and died < 500) or " BC" in str(rec.get("source", "")):
        return "**归属必查**"
    return ""


def main(argv) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=10)
    a = ap.parse_args(argv)

    years, deferred = load_years(), load_deferred()
    pending, rates = load_pending(), family_rates(load_deferred())
    if not pending:
        print("**pending 为 0——未核验，不是「都做完了」**")
        return 2

    rows = []
    for p in pending:
        light, why = classify(p, years)
        rec = years.get(p["name"].strip().lower())
        s, d, rate = rates.get(p["family_zh"], (0, 0, 0.0))
        rows.append({**p, "灯": light, "理由": why, "归属": attribution_flag(rec),
                     "族出货": f"{s}/{s+d}", "族出货率": rate})

    order = {"绿": 0, "黄": 1, "补年份": 2, "红": 3}
    # ★ 带「归属必查」的排在同灯位的后面——**不是否决，是让它别占本批名额**，
    #   因为那一句话答不出来的话，整轮都白做（Socrates 一个字没留下）。
    rows.sort(key=lambda r: (order[r["灯"]], bool(r["归属"]),
                             -r["族出货率"], r["priority"], r["order"]))

    print(f"# 值得开工名单（pending {len(rows)} 人）\n")
    print("| # | 人 | 族 | 灯 | 归属 | 族出货 | 依据 |")
    print("|---:|---|---|:--:|:--:|---:|---|")
    for i, r in enumerate(rows, 1):
        mark = " **←本批**" if i <= a.top else ""
        print(f"| {i} | {r['name']}{mark} | {r['family_zh']} | {r['灯']} "
              f"| {r['归属']} | {r['族出货']} | {r['理由']} |")
    n = {k: sum(1 for r in rows if r["灯"] == k) for k in order}
    print(f"\n绿 {n['绿']}｜黄 {n['黄']}｜补年份 {n['补年份']}｜红 {n['红']}"
          f"｜其中带**归属必查** {sum(1 for r in rows if r['归属'])} 人")
    print("\n★ 声口／一手源占比／min_lanes **开工前取不到**，"
          "它们是抓源后的第一个检查点，不达标当场结案。")
    # ★★★ 2026-08-18：上面那句对**非英文语料的人物不成立**，必须连射程一起印 ——
    #   否则读的人会以为三项都会给出读数，而声口那一项**结构性给不出**。
    #   实测（Eiffel #142 法文 374,811 字符）：`check_first_person_density` 报
    #   「可读占比 0%／**本判据不适用**」，读数是 **null 不是 0**（判据是对的，没有假绿）。
    #   全库射程：有语种字段的工作区 49 个，**英文占比 <50% 的 19 个（39%）**
    #   —— de/la/fr/it/grc，且多位已出货（Pasteur #106／Koch #107／Virchow #109…），
    #   即他们**是在没有声口读数的情况下走完全程的**。
    #   ★ 本处**只加披露，不改任何阈值、不改任何判定** —— 与「未核 ≠ 通过」同类。
    #   台账：`_声口检查点对四成人物结构性不可用-2026-08-18.md`
    print("★★ **射程**：上面三项里的**声口**，判据只认英文第一人称锚点"
          "（`I have`／`I find`…），德文 `ich habe`、法文 `j'ai`、俄文 `я` 都不认。")
    print("   全库有语种字段的 49 个工作区里，**英文占比 <50% 的有 19 个（39%）**——"
          "对他们，声口那一档只能记「**未量**」，")
    print("   **既不是「够」也不是「不够」**。抓源后别把 `null` 读成 0。"
          "（判据本身没错：它返回 null 而不是 0。）")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
