#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_pd_claim_has_a_year.py —— **没有出版年就不许断言公有领域**

## 抓到它的那一次

2026-08-14，顺着「归属查无证据」的 96 行往下读，撞见 Leonardo 工作区里这一行：

    title              Leonardo Da Vinci (Quote) - Nothing Strenghtens Authority So Much As Silence.
    tier               P1        attribution  HIS-OWN
    published_at       （空）
    published_at_basis **取不到**
    rights             pre1931
    rights_basis       公有领域 = 出版于 ≤1930（分界 1931 = 2026 − 95）；出版年 **未取到**（**取不到**）

**同一行里，`rights_basis` 一边说「出版于 ≤1930」，一边承认年份没取到。**
正文 130 字符／18 词，末行是 `Www.Etoile.App` —— 一个名言壁纸应用的导出物，
根本不是 1930 年前的出版物。

本项目的硬规矩是「**只取公有领域（出版年 ≤1930，`PD_CUTOFF` 随年份滚动）**」。
这一行**在没有年份的情况下满足了那条规矩** —— 判据从来没问过「年份到底有没有」。

## 判什么

`published_at` 里**没有任何四位年份**、而 `rights` 以 `pre` 开头
或 `rights_basis` 里写着「公有领域」／「PD 依据」的行 ⇒ **✗ 红**。

★ 这道门**可以是硬门**：全库实测已经是 **0 行**（撤回三行之后），
  而且规矩本身是绝对的——**没有年份就是判不了 PD，不是「大概可以」**。
  不像那些天生要靠人读的检查，这一条不会变成
  [[a-red-that-can-never-turn-green-is-not-a-signal]]。

## 撤回的三行（**标 U 不是删**）

| 工作区 | source_id | 为什么 |
|---|---|---|
| leonardo-da-vinci | `src-a481f69dbb90` | 名言壁纸应用的导出物，18 词 |
| luther-burbank | `src-aab594edb7c1` | 正文前 6000 字无年份，OCR 碎化 |
| luther-burbank | `src-85ef70c92ca3` | 同上 |

★ Burbank 卒于 1926、这些是他自家苗圃的目录，「多半在 1930 前」——
**那是常识，不是证据**。本项目的 PD 判据要逐条给年份出处，所以宁可标 U。
同一工作区另有带年份的《The Burbank seed book》（1907／1909），不受影响。

## 用法

    python3 check_pd_claim_has_a_year.py
    python3 check_pd_claim_has_a_year.py --self-test

退出码：0＝没有这样的行；1＝**有**（逐行印出来）；4＝找不到任何台账（未判）
"""
import argparse
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from workspace_roots import iter_workspaces  # noqa: E402

CORPORA = HERE.parent.parent / "_corpora"
YEAR = re.compile(r"\b(1[0-9]{3}|20[0-2]\d)\b")


def claims_pd(rights, rights_basis) -> bool:
    """这一行是不是在断言公有领域。**纯函数**。"""
    r, b = str(rights or ""), str(rights_basis or "")
    return r.startswith("pre") or "公有领域" in b or "PD 依据" in b


def has_year(published_at) -> bool:
    """`published_at` 里有没有四位年份。**空字符串、None、「取不到」都算没有**。"""
    return bool(YEAR.search(str(published_at or "")))


def bad(row) -> bool:
    """断言了 PD 却没有年份 ⇒ True。"""
    return claims_pd(row.get("rights"), row.get("rights_basis")) and not has_year(
        row.get("published_at"))


def self_test() -> int:
    ok = t = 0

    def chk(d, c):
        nonlocal ok, t
        t += 1
        ok += 1 if c else 0
        print(f"  {'✓' if c else '✗'} {d}")

    # ★★ 正对照：真实那一行（照录）
    real = {"published_at": "", "rights": "pre1931",
            "rights_basis": "公有领域 = 出版于 ≤1930（分界 1931 = 2026 − 95）；出版年 **未取到**（**取不到**）"}
    chk("★★ **正对照：Leonardo 那一行被判红**（rights=pre1931 而 published_at 为空）", bad(real))
    # ★★ 负对照三种，都不许红
    chk("★★ 反例：有年份 ＋ 断言 PD ⇒ 不红",
        not bad({"published_at": "1907", "rights": "pre1931", "rights_basis": "公有领域 …"}))
    chk("★★ 反例：**没年份但也没断言 PD** ⇒ 不红（撤回之后就是这个样子）",
        not bad({"published_at": "", "rights": "未定——无出版年，PD 判不了",
                 "rights_basis": "**PD 未判定**：published_at 为空"}))
    chk("★ 反例：卒年式的 rights（`卒年 1912，终身+70 已过`）不按 pre 开头，"
        "且 rights_basis 不含 PD 字样 ⇒ 不红",
        not bad({"published_at": "", "rights": "卒年 1912，终身+70 已过", "rights_basis": ""}))
    # ★ 年份识别
    chk("★ `published_at` 写「**取不到**」算没有年份", not has_year("**取不到**"))
    chk("★ `published_at` 写 `1885-03` 算有年份", has_year("1885-03"))
    chk("★ None 算没有年份，不报错", not has_year(None))
    # ★ PD 断言的三种写法都认得
    chk("★ `rights=pre1929` 也算断言 PD", claims_pd("pre1929", ""))
    chk("★ `rights_basis` 里写「PD 依据」也算", claims_pd("", "PD 依据 = 该印本出版年 1770"))
    chk("★ 两个都空 ⇒ 不算断言", not claims_pd("", ""))
    print(f"\n{'✓ 全过' if ok == t else f'✗ {t - ok}/{t} 项不符'}")
    return 0 if ok == t else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    if ap.parse_args().self_test:
        return self_test()

    tot, pd_rows, hits, seen_ws = 0, 0, [], 0
    for ws in iter_workspaces(CORPORA):
        led = ws / "evidence/source-ledger.jsonl"
        if not led.is_file():
            continue
        seen_ws += 1
        for line in led.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            tot += 1
            if claims_pd(r.get("rights"), r.get("rights_basis")):
                pd_rows += 1
            if bad(r):
                hits.append((ws.name, r["source_id"], r.get("tier"), r.get("split"),
                             str(r.get("published_at_basis") or "")[:22],
                             str(r.get("title") or "")[:56]))
    if not tot:
        print("★ **未判** —— 一份台账都没读到")
        return 4

    print(f"★★ **分母**：{seen_ws} 个工作区、台账 {tot:,} 行 → "
          f"其中**断言了公有领域的 {pd_rows:,} 行**（只有这些才可能违反本条）")
    print(f"⇒ 断言了 PD **却没有出版年**的：**{len(hits)} 行**")
    for n, sid, tier, sp, basis, ti in hits:
        print(f"  ✗ {n} / {sid}  tier={tier} split={sp} 年份依据「{basis}」\n     {ti}")
    if hits:
        print("\n★ 处置：**要么补上年份并写明出处**（扉页照录 ／ IA date 字段 ＋ 互证），"
              "**要么把 rights 改成「未定」并标 tier=U**。"
              "\n★★ **不许臆断**：「作者卒于 19xx，多半在 1930 前」是常识不是证据。")
        return 1
    print("  ✅ 一行也没有")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
