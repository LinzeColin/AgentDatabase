#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**合议票数门**：团队宣称的票数，不得超过它实际点名的人数。

## 席 B 抓到的那一处（2026-08-02 三臂盲判）

> 它用「三个人一致」「三票否决」赋予自己一种**从未展示的合议权威**——
> **t1 只摆了两路却称三票。**

回看 `ans_team.json` 的 t1 原文，实情比席 B 说的还差一格：

```
**趋势那一路的读法：** …
**估值那一路的读法：** …
**先说三个人一致的那一条，可以直接执行：现在不加仓。**
一个是因为价格没有突破，两个是因为估值变贵了。**三票否决。**
```

**只摆了两路，宣称三票，而且全文一个成员名都没出现。**
读者无从知道第三票是谁投的、投的什么——**「三人团队」四个字在这里是修辞，不是事实。**

这不是文风问题。团队臂相对裸模型 **−0.0219**、相对单人物 **+0.0825**，
唯一能解释团队层价值的就是「多个不同视角」；
**而一份不点名的合议宣称，恰好把这个唯一的卖点变成了不可核验的断言。**

## 判据

1. 在答案里找**合议宣称**：数词 + 票／人／位 + 一致／否决／同意／反对／都认为……
2. 在答案里找**实际点名的成员**：给定名册中，有几个人的名字真的出现在正文里。
3. **宣称数 > 点名数 → 判错。**

少说不算错（点名 3 人只宣称「两人认为」是诚实的收敛）；**多说才算错。**

### 为什么门槛是「点名」而不是「分了几段」

分段可以任意切。**只有名字能对上名册**——它是唯一可核验的锚。
本门因此顺带强制了 v0.0.0.11 遗留的那条：**团队产出必须逐条署名。**

## 这个判据的射程（必须一起说）

- 它数的是**名字有没有出现**，不是**这个人是否真的持这个观点**。
  把三个名字撒进正文就能骗过它。**它挡的是「凭空宣称票数」，不是「冒名代言」。**
- 中文数词只识别到「十」以内的常用写法；团队规模 5–20 里 11–20 的中文写法
  （十一、十二…）已覆盖，**再往上不认**——超出团队规模上限，不在射程内。
- 「一致」若不带数词（如「大家一致认为」），**本门不判**——没有可比的数。
  这条缺口是有意留的：堵它需要判定「大家」指几个人，那是语义不是句式。

退出码：0 = 通过；1 = 有超额宣称；3 = 用法错误。
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

CN_NUM = {"一": 1, "两": 2, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6,
          "七": 7, "八": 8, "九": 9, "十": 10,
          "十一": 11, "十二": 12, "十三": 13, "十四": 14, "十五": 15,
          "十六": 16, "十七": 17, "十八": 18, "十九": 19, "二十": 20}
_NUM_ALT = "|".join(sorted(CN_NUM, key=len, reverse=True))

# 合议宣称：数词 + （票|人|位|个人） + 合议动词。动词必须在数词后 12 字内。
CONSENSUS = re.compile(
    rf"(?P<n>{_NUM_ALT}|\d{{1,2}})\s*(?:票|人|位|个人)"
    rf"[^\n。；]{{0,12}}?(?:一致|否决|同意|反对|赞成|都认为|全票|通过)")
# 反向语序：「一致否决 —— 三票」这类
CONSENSUS_REV = re.compile(
    rf"(?:一致|否决|全票|都认为)[^\n。；]{{0,8}}?(?P<n>{_NUM_ALT}|\d{{1,2}})\s*(?:票|人|位)")


def _to_int(tok: str) -> int:
    return CN_NUM.get(tok, int(tok) if tok.isdigit() else 0)


def claimed_counts(text: str) -> list[tuple[int, str]]:
    out = []
    for rx in (CONSENSUS, CONSENSUS_REV):
        for m in rx.finditer(text):
            n = _to_int(m.group("n"))
            if n:
                out.append((n, m.group(0)))
    return out


def named_members(text: str, members: list[str]) -> list[str]:
    """名册中有几个人的名字真的出现在正文里。中英文名都按整串匹配。"""
    hit = []
    for name in members:
        name = str(name).strip()
        if not name:
            continue
        # 英文名允许只匹配姓氏（正文里常只称姓）；中文名整串匹配。
        tokens = [name] + ([name.split()[-1]] if re.search(r"[A-Za-z]", name) and " " in name else [])
        if any(t and t.lower() in text.lower() for t in tokens):
            hit.append(name)
    return hit


def check(text: str, members: list[str]) -> dict:
    claims = claimed_counts(text)
    named = named_members(text, members)
    worst = max((c for c, _ in claims), default=0)
    return {
        "roster_size": len(members),
        "claimed_max": worst,
        "claims": [f"{n}｜{s}" for n, s in claims][:6],
        "named": named,
        "named_count": len(named),
        "overclaim": bool(claims) and worst > len(named),
    }


# ── 负对照 ────────────────────────────────────────────────────────────
T1_EXCERPT = (
    "**趋势那一路的读法：**三个月 60% 之后横盘两周、量缩。\n"
    "**估值那一路的读法：**横盘和缩量不是信息。\n"
    "**先说三个人一致的那一条，可以直接执行：现在不加仓。**"
    "一个是因为价格没有突破，两个是因为估值变贵了。三票否决。")
MEMBERS3 = ["Jesse Livermore", "Benjamin Graham", "Philip Fisher"]


def self_test() -> int:
    fails = []

    # ★ 负对照 1（真实样本）：t1 原文——宣称三票，一个名字都没出现
    r = check(T1_EXCERPT, MEMBERS3)
    if not r["overclaim"]:
        fails.append(f"负对照 1 未抓出：t1 真实样本（宣称 {r['claimed_max']}，点名 {r['named_count']}）")
    if r["named_count"] != 0:
        fails.append(f"负对照 1 计数错：t1 全文无成员名，却数出 {r['named_count']}")

    # 负对照 2：点名 2 人却宣称三票
    t = "Livermore 说不加，Graham 说减。三人一致否决加仓。"
    if not check(t, MEMBERS3)["overclaim"]:
        fails.append("负对照 2 未抓出：点名 2 人宣称 3 票")

    # 负对照 3：阿拉伯数字写法
    if not check("Livermore 认为不加。3 票否决。", MEMBERS3)["overclaim"]:
        fails.append("负对照 3 未抓出：阿拉伯数字票数")

    # 正对照 1：点名 3 人宣称三票 → 放行
    t = "Livermore 说不加；Graham 说减；Fisher 说守。三票否决加仓。"
    if check(t, MEMBERS3)["overclaim"]:
        fails.append("正对照 1 被误杀：点名 3 人宣称 3 票")

    # 正对照 2：完全不作合议宣称 → 放行（哪怕一个名字都没有）
    if check("现在不加仓，因为价格没有突破。", MEMBERS3)["overclaim"]:
        fails.append("正对照 2 被误杀：没有任何合议宣称")

    # 正对照 3：少说不算错——点名 3 人只宣称两人
    t = "Livermore、Graham、Fisher 都看过。其中两人反对加仓。"
    if check(t, MEMBERS3)["overclaim"]:
        fails.append("正对照 3 被误杀：点名 3 人只宣称 2 人（诚实的收敛）")

    # 边界：英文正文里只称姓 → 应能对上名册
    t = "Livermore is against it; Graham is against it; Fisher agrees. 三票否决。"
    if check(t, MEMBERS3)["overclaim"]:
        fails.append("边界失败：英文正文只称姓时未能对上名册")

    # 边界：「大家一致认为」无数词 → 本门不判（射程外，明确不误杀）
    if check("大家一致认为不该加仓。", MEMBERS3)["overclaim"]:
        fails.append("边界失败：无数词的「一致」被判成超额宣称")

    # ★ 反向对照：把数词识别拿掉，真实样本必须不再被抓出——证明抓到它的是判据本身
    saved = dict(CN_NUM)
    try:
        CN_NUM.clear()
        blind = check(T1_EXCERPT, MEMBERS3)
    finally:
        CN_NUM.update(saved)
    if blind["overclaim"]:
        fails.append("反向对照失败：清空数词表后仍报错，说明抓到它的不是数词判据")

    for f in fails:
        print(f"✗ {f}")
    if fails:
        print(f"负对照未通过：{len(fails)} 项")
        return 1
    print("负对照通过：**t1 真实样本被抓出（宣称三票、点名 0 人）**；点名 2 宣称 3、"
          "阿拉伯数字两类坏样本全抓出；点名足数、无合议宣称、少说三类正对照未误杀；"
          "英文只称姓能对上名册；无数词的「一致」不误判；"
          "**清空数词表后真实样本不再报错**（证明抓到它的是判据本身）")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="合议票数门：宣称的票数不得超过实际点名的人数")
    ap.add_argument("path", nargs="?", type=pathlib.Path, help="团队答案 JSON（{任务: 文本} 或数组）")
    ap.add_argument("--members", nargs="*", default=[], help="本次路由的名册人名")
    ap.add_argument("--members-file", type=pathlib.Path, help="从 JSON 读名册（数组或 {members:[...]}）")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return self_test()
    if not a.path:
        print("用法错误：需要团队答案 JSON 路径（或 --self-test）", file=sys.stderr)
        return 3

    members = list(a.members)
    if a.members_file and a.members_file.is_file():
        raw = json.loads(a.members_file.read_text(encoding="utf-8"))
        rows = raw if isinstance(raw, list) else raw.get("members", [])
        members += [r if isinstance(r, str) else str(r.get("canonical_name") or "") for r in rows]
    if not members:
        print("用法错误：需要 --members 或 --members-file（**没有名册就无从核对点名**）",
              file=sys.stderr)
        return 3

    data = json.loads(a.path.read_text(encoding="utf-8"))
    items = data.items() if isinstance(data, dict) else enumerate(data)
    bad = []
    for key, text in items:
        r = check(str(text), members)
        if r["overclaim"]:
            bad.append((key, r))

    if a.json:
        print(json.dumps([{"task": k, **r} for k, r in bad], ensure_ascii=False, indent=1))
        return 1 if bad else 0
    if not bad:
        print("✓ 无超额合议宣称：每一处票数都不超过实际点名的人数")
        return 0
    print(f"\n✗ 超额合议宣称 {len(bad)} 处：\n")
    for k, r in bad:
        print(f"  - {k}　宣称 {r['claimed_max']} 票／人，实际点名 {r['named_count']} 人"
              f"{'（' + '、'.join(r['named']) + '）' if r['named'] else '（**一个都没有**）'}")
        for c in r["claims"][:2]:
            print(f"      原文：{c}")
    print("\n  ↑ **合议是团队层唯一的卖点，不点名的合议宣称把它变成了不可核验的断言。**")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
