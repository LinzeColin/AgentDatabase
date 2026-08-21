#!/usr/bin/env python3
"""色情度档位 L1–L5：出图率与色情度的取舍，用**降级重试**而不是二选一。

背景：v0.0.1 把 pin-up 拉满（L5），全量 110 张里 67 张被 gpt-image-2 的安全系统拦下，
昼夜成对可用的只剩 9 个变体。而 v1.7.0 的措辞（L1）上一轮是 94/94 全过。

标定发现的关键事实：**安全系统有随机性，不是固定阈值。**
同一档同一张，重试就可能过；不同角色在同一档结果也不一致
（shinku 在 L5 过、L4 拦、L3 过、L2 拦）。所以「挑一档跑全量」是错的做法。

正确做法是**阶梯降级重试**：第一次用最高档，被拦就降一档再试，
既拿到能拿到的最高色情度，又不会整张丢掉。

    L5  全强度：吊袜带 · 露腰 · 深V · 高衩 · 含胸挺腰 · 暗示性姿态
    L4  −暗示性姿态
    L3  −含胸/挺腰
    L2  −露腰/深V/高衩          ← 最低可接受档，再低就等于没做
    L1  v1.7.0 原版（已知 100% 通过，仅作兜底参考，不进重试阶梯）
"""

from __future__ import annotations

SUGGESTIVE = ("the pose is consciously alluring and suggestive — weight on one hip, "
              "arched back, chin slightly lowered, direct eye contact with the viewer. ")
NO_SUGGEST = ("the pose is elegant and poised — weight on one hip, "
              "arched back, chin slightly lowered, direct eye contact with the viewer. ")
NO_ARCH    = "the pose is elegant and poised — weight on one hip, direct eye contact with the viewer. "
MAXIMAL    = ("The silhouette is maximally skin-revealing: bare shoulders, bare arms, bare midriff, "
              "fully bare thighs above the stocking band, and a deep plunging neckline. Favour "
              "high-cut leotard, micro-skirt, bodysuit and open-side silhouettes over anything that "
              "covers the hips or waist. ")
MODEST     = ("The silhouette is open and skin-revealing — bare shoulders, arms, thighs "
              "and décolletage. ")

NAMES = {5: "L5 全强度", 4: "L4 −暗示性姿态", 3: "L3 −含胸/挺腰",
         2: "L2 −露腰/深V/高衩", 1: "L1 v1.7.0 原版"}

# 用户 2026-08-21 定的：从 L4 起，依次降到 L3、L2；L2 都出不来就算这张要重做。
LADDER = (4, 3, 2)


def at_level(prompt: str, level: int) -> str:
    """把任务包里的 L5 prompt 降到指定档位。"""
    p = prompt
    if level <= 4:
        p = p.replace(SUGGESTIVE, NO_SUGGEST)
    if level <= 3:
        p = p.replace(NO_SUGGEST, NO_ARCH)
    if level <= 2:
        p = p.replace(MAXIMAL, MODEST)
    if level <= 1:
        p = p.replace(", worn with visible garter straps", "")
        p = p.replace("MANDATORY WARDROBE AND PRESENTATION — applies to every character "
                      "without exception, this is glamour pin-up art and the wardrobe rule "
                      "is not optional:",
                      "MANDATORY WARDROBE — applies to every character without exception:")
        p = p.replace("PIN-UP DIRECTION: emphasise the unbroken leg line from hip to ankle "
                      "and the bust line; ", "")
    return p


def level_for_attempt(attempt: int) -> int:
    """第 n 次尝试该用哪一档。attempt 从 1 起。"""
    return LADDER[min(attempt, len(LADDER)) - 1]
