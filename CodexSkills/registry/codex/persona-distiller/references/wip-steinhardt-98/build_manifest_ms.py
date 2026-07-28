#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 Steinhardt 语料的分层清单（灌库前的唯一真源）。

## 为什么不再用自动判据

本人物实测：`ingest_steinhardt.py` 里那套「说话人标记 + 第一人称密度」的
自动判据，把 57 篇判出 23 份 P1，**逐份核完只有约 8 份是对的**。
两类错各占一半（RUNBOOK 第六十五、六十六种）：

- `^Michael Steinhardt:` 命中的是**标题里的冒号**，不是说话人标记；
- 第一人称密度分不清那个「我」是谁——一位具名指控者的自述
  （"Michael Steinhardt sexually harassed me"）密度 0.026，判成了 P1。

所以这里改成两段式：

- **P1 由 `check_authorship.py` 判**，要正面证据（署名 / 编者注 / 对话轮次），
  且署名型证据不得被他人署名污染。判据与证据都可复核。
- **其余由下面的显式表判**，一条一个理由。表里没有的文件不灌。

## 分层

| tier | 是什么 | 引号内原话可用吗 |
|---|---|---|
| **P1** | 过授权门的：他署名的文字 / 人工逐字稿 / 他的问答 | ✅ |
| **S1-官方** | 检方、监管、法院文书 | ⚠ 事实效力强，但**不是他的话** |
| **S1** | 含其引语的第三方报道；他的合署文章 | ⚠ 引用前核引导句主语 |
| **S2** | 引语稀疏的第三方报道 | ❌ 不作主张来源 |
| **排除** | 伪托语录站 / 整篇是别人写的 / 与已有源重复 | —— |

## 本人物必须守住的三处（写进 abstract，让下游查得到）

1. **1994 年国债市场的和解 ≠ 认罪。**
2. **2021 年归还掠夺文物 + 终身禁止收购**——不得省略。
3. **他的自述与官方文件冲突时两边都记，不替他选。**
"""
import importlib.util
import json
import pathlib
import re
import sys

W = pathlib.Path(__file__).resolve().parent
CHECKER = ("/Users/linzezhang/Downloads/蒸馏/_pipeline/checkers/check_authorship.py")

# ── 显式表：文件名正则 → (tier, 维度, abstract) ────────────────────────────
# 顺序有意义，先匹配先算。
RULES: list[tuple[str, tuple[str, list[str], str]]] = [
    (r"_(doj|sec|manhattanda|sdny)_official_", (
        "S1", ["external", "timeline"],
        "**官方文件**（检方/监管/法院）——事实效力强于任何媒体转述，"
        "但**不是他的话**；引用前核引导句主语。"
        "1994 年国债案是**和解，不是认罪**，引用时必须保留这个区分")),
    (r"_manhattanda_", (
        "S1", ["external", "timeline"],
        "**官方文件**（曼哈顿地检）——2021 年归还 180 件掠夺文物、"
        "接受**终身禁止收购古物**。**这一条不得在产物里省略或淡化**")),
    (r"contact_(autumn|spring|summer|winter)_?\d*\.txt$|contact_spring_qa", (
        "P1", ["writings", "expression", "decisions"],
        "他在其基金会季刊 CONTACT 上的**署名**文字（按页切片，署名随文落盘可复核）")),
    (r"charlierose|tradingmarkets|wharton|medialine|jpost", (
        "P1", ["conversations", "expression", "decisions"],
        "人工逐字稿/问答，说话人逐轮标注")),
    (r"contact_winter_2008|_brenner", (
        "S1", ["writings", "external"],
        "**与 Rabbi Daniel S. Brenner 合署**——其中任何一句都不能单独归给他")),
    (r"propublica|_nyunews_|jta_sheila_katz|jta_staff_and_son|_forbes_harassment", (
        "S1", ["external"],
        "第三方调查报道/当事人自述。**注意：`sheila_katz` 一篇里的「我」是 Sheila Katz "
        "（具名指控者），不是他**；引用前必核引导句主语")),
    (r"_(jta|cnbc|forbes|nyt|toi|brooklyneagle|artnews|artforum|artnet|npr|ap_|"
     r"artnewspaper|culturalheritagelawyer|publishersweekly|cjn|ejp|acjna|"
     r"jewishsages|forward|globes)_", (
        "S1", ["external"],
        "第三方报道，含其引语；**引用前核引导句主语**")),
    (r"_(fortune|gurufocus|commoncog|marketfolly|valueinvestingworld|benzinga|"
     r"macroops|deepvaluestocks|acquirersmultiple|microcapclub|tradersmagazine|"
     r"goldmoney|hedgefundalpha|jewishjournal)_", (
        "S2", ["external"],
        "第三方转述/汇编/书评，引语来源为二手；不作主张来源")),
]

# ── 明令排除，附理由 ──────────────────────────────────────────────────────
EXCLUDE: list[tuple[str, str]] = [
    (r"turtletrader|robusttrader|graciousquotes|quantifiedstrategies",
     "伪托语录站：流传的「交易智慧」查无一手出处（抓源 A 独立证实）"),
    (r"contact_essay_", "抓源子代理的旧切片：署名归属不可考，四份里三份实为他人所写"),
    (r"jpost_jewish_pride_interview", "与 medialine 一篇逐字相同（重复源）"),
    (r"acquirersmultiple_being_contrarian",
     "与 2001 Charlie Rose 逐字稿覆盖 33.3%，越 30% 硬门（转载摘录）"),
    (r"contact_(autumn|spring)_2004\.txt", "切片实为封底基金会使命声明，非随笔"),
    (r"contact_winter_2005\.txt", "切片实为封底邮寄面单"),
    (r"contact_winter_2003\.txt", "页 6–7 与 Andrew Katz 的文章交织，按页分不开"),
]


def load_checker():
    spec = importlib.util.spec_from_file_location("ca", CHECKER)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def classify(name: str, path: pathlib.Path, ca) -> tuple:
    for rx, why in EXCLUDE:
        if re.search(rx, name):
            return ("排除", [], why)
    ok, code, ev, counter = ca.check(path)
    if ok and not counter:
        for rx, spec in RULES:
            if re.search(rx, name) and spec[0] == "P1":
                return ("P1", spec[1], f"{spec[2]}（证据 {code}：{ev[:90]}）")
        return ("P1", ["conversations", "expression"],
                f"过授权门（证据 {code}：{ev[:90]}）")
    for rx, spec in RULES:
        if re.search(rx, name):
            if spec[0] == "P1":          # 想当 P1 但没过授权门 → 降 S1
                return ("S1", ["external"],
                        "未取得归属正面证据，降为第三方材料；**不得当作他的话引用**")
            return spec
    return ("S2", ["external"], "未归类的第三方材料，不作主张来源")


def main() -> int:
    ca = load_checker()
    rows, stat = [], {}
    seen = set()
    for d in ("contact_ok", "_backup_ms"):
        p = W / d
        if not p.is_dir():
            continue
        for f in sorted(p.glob("*.txt")):
            if f.name in seen:
                continue
            seen.add(f.name)
            tier, dims, note = classify(f.name, f, ca)
            stat[tier] = stat.get(tier, 0) + 1
            if tier != "排除":
                rows.append({"file": str(f.relative_to(W)), "name": f.name,
                             "tier": tier, "dimensions": dims, "abstract": note,
                             "bytes": f.stat().st_size})
            else:
                print(f"  排除 {f.name:56s} ← {note[:52]}")
    json.dump(rows, open(W / "manifest_ms.json", "w"), ensure_ascii=False, indent=1)
    n_p = sum(1 for r in rows if r["tier"] in ("P1", "P2"))
    print(f"\n可灌 {len(rows)} 篇   分布 " +
          "  ".join(f"{k}={v}" for k, v in sorted(stat.items())))
    print(f"primary = {n_p}/{len(rows)} = {n_p/max(1,len(rows)):.3f}   （deep 门槛 0.65）")
    need = 45
    print(f"\ndeep 门要 ≥{need} 源且 primary ≥0.65 → **至少 {-(-need*65//100)} 份 P1**；"
          f"现有 {n_p}，{'够' if n_p >= 30 else f'缺 {30-n_p}'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
