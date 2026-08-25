#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pricing.py —— 价格加权 token（BIE, base-input-equivalent）。

为什么不直接用美元：单价会变。历史数据必须用当时的价重算，
不能用今天的价重算历史 —— 那会把一次调价读成一次用量变化。
BIE 是无量纲的倍数，跨时间可比；美元留给「当期账单」那一栏。

    BIE = in×1.0 + cache_read×r + cache_write×w + out×o

倍数按 provider 取，不许拿一家的倍数去算另一家。
表里没有的 provider 一律返回 None（未定价），绝不静默按 0 或按 Anthropic 算 ——
静默补 0 正是 v0.5.x 那一批假数字的共同形态。

■ 已知的失效条件（调用方必须原样透出，不许只报一个总数）
  1. 跨 provider 加总不成立。各家的 r 差一个数量级（0.1 ~ 0.25），
     加起来的那个数不对应任何真实账单。
  2. Gemini 显式缓存装不进这个公式 —— 它按「租金 × 小时」计费，与 token 量正交。
     所以表里没有 gemini，将来要加得先改公式，不是加一行倍数。
  3. 跨 tokenizer 版本不可比。Claude 4.7+ 换过 tokenizer，同样文本多约 30% token；
     BIE 跨版本比较会把 tokenizer 变更读成用量增长。
  4. 本机只有三个来源真的量到了 token（claude-code / codex / kimi-code）。
     其余来源不是「成本为 0」，是没量到，必须记进 unpriced。
"""
from __future__ import annotations

# 每个来源属于哪家。不在这张表里的来源 = 未定价，不猜。
SOURCE_PROVIDER = {
    "claude-code":    "anthropic",
    "claude-desktop": "anthropic",
    "codex":          "openai",
    "chatgpt":        "openai",
    "kimi-code":      "moonshot",
    "workbuddy":      None,      # 用量在 traces 里、没有 sessionId，摊不到会话上
    "dsh":            "deepseek",
    # dws 是审计日志，不是模型会话 —— 故意不给 provider。
}

# 倍数相对「基础输入单价」。confidence 是给页面看的，不是装饰：
#   verified —— 官方定价页长期稳定，且本项目的量绝大部分落在这里
#   approx   —— 形状可信，具体档位可能随模型/时间漂移，页面必须标出来
PRICES = {
    "anthropic": {
        "in": 1.0, "cache_read": 0.10, "cache_write": 1.25, "out": 5.0,
        "confidence": "verified", "fetched": "2026-08-20",
        "note": "Sonnet 3/15、Opus 15/75、Haiku 1/5 —— 输出恒为输入的 5 倍；"
                "缓存读 0.1×、5 分钟缓存写 1.25×，三档模型一致",
    },
    "openai": {
        "in": 1.0, "cache_read": 0.10, "cache_write": 0.0, "out": 8.0,
        "confidence": "approx", "fetched": "2026-08-20",
        "note": "按 GPT-5 档（1.25 / 0.125 / 10）折算；OpenAI 不单收缓存写费用。"
                "codex 实际用的是哪个具体型号本机日志里没记，所以标 approx",
    },
    "moonshot": {
        "in": 1.0, "cache_read": 0.25, "cache_write": 0.0, "out": 4.0,
        "confidence": "approx", "fetched": "2026-08-20",
        "note": "按 Kimi K2 档折算。缓存命中折扣比 Anthropic 浅得多（0.25 而不是 0.1）"
                "—— 这正是「不许跨家套用倍数」的原因",
    },
    # DeepSeek —— 倍数**从本机的真实账本反推出来的**，不是抄单价页。
    # ~/.dsh/storages/token-billing-ledger.json 每一步都带 cost + 四类 token，
    # 解一个最小二乘就得到相对倍数。这是这张表里唯一有本机账单背书的一行。
    "deepseek": {
        "in": 1.0, "cache_read": 0.25, "cache_write": 0.0, "out": 4.0,
        "confidence": "ledger", "fetched": "2026-08-17",
        "note": ("由本机 token-billing-ledger.json 的 580 条非估算计费步骤最小二乘反推："
                 "v4-pro ¥4.0e-6/输入、¥1.0e-6/缓存读、¥1.6e-5/输出；v4-flash 恰好是它的一半。"
                 "两个型号解出同一组相对倍数（缓存读 0.25、输出 4.00）。"
                 "★ 注意缓存读是 0.25 不是 Anthropic 的 0.10 —— 这正是「不许跨家套用倍数」的实证。"
                 "★ 那本账是滚动的，只覆盖 1 场 1 天（¥133.90）—— 倍数可信，用量不是全历史"),
    },
    # SCNet（中国超算）—— 本机是 Token Plan 套餐制，**按量单价不适用**。
    # 硬给一个倍数会让页面显示出一个根本不存在的「按量成本」。
    "scnet": {
        "in": 1.0, "cache_read": 0.10, "cache_write": 0.0, "out": 1.0,
        "confidence": "plan", "fetched": "2026-08-21",
        "note": ("套餐制（Token Plan），按量单价不适用 —— 倍数只用来做内部占比，"
                 "绝不能读成钱。而且 Token Plan 明令禁止 API 脚本化/批量调用，"
                 "扇出走这条线是合规问题不只是成本问题"),
    },
}

FIELDS = (("tok_in", "in"), ("tok_cache_r", "cache_read"),
          ("tok_cache_w", "cache_write"), ("tok_out", "out"))


def provider_of(source: str | None) -> str | None:
    return SOURCE_PROVIDER.get(source or "")


def priced_providers() -> list:
    """页面上「按哪几家的价算的」那一行。"""
    return [{"provider": p, "confidence": v["confidence"], "fetched": v["fetched"],
             "note": v["note"], "mult": {k: v[k] for k in ("in", "cache_read", "cache_write", "out")}}
            for p, v in sorted(PRICES.items())]


def bie(s: dict) -> float | None:
    """一场会话的价格加权 token。未定价返回 None —— 不是 0。

    区别是硬的：0 是一个断言（「这场没花钱」），None 是「没量到 / 不知道价」。
    把 None 当 0 加进总量，总量就永远显得是对的。
    """
    p = PRICES.get(provider_of(s.get("source")))
    if not p:
        return None
    raw = sum((s.get(f) or 0) for f, _ in FIELDS)
    if raw <= 0:
        return None                      # 一个 token 都没量到，不是成本为 0
    return round(sum((s.get(f) or 0) * p[m] for f, m in FIELDS), 2)


def raw_tokens(s: dict) -> int:
    return sum((s.get(f) or 0) for f, _ in FIELDS)


def _real_money(sessions: list) -> dict:
    """**真实账单**，不是折算。本机只有 DSH 记了这个（cost + currency + estimated）。

    为什么单独成一栏：BIE 是无量纲倍数，回答「哪一块最贵」；
    这一栏是真钱，回答「到底花了多少」。把两者并成一个数，
    读的人会以为整个站上的量都有账单背书 —— 实际上只有极小一块有。
    """
    rows = [s for s in sessions if s.get("cost_cny")]
    if not rows:
        return {"state": "没做", "why": "没有任何来源记了真实账单金额。"}
    tot = round(sum(s["cost_cny"] for s in rows), 2)
    est = sum(s.get("cost_estimated_steps", 0) for s in rows)
    steps = sum(s.get("billing_steps", 0) for s in rows)
    days = sorted({(s.get("start") or "")[:10] for s in rows if s.get("start")})
    return {
        "state": "通",
        "currency": "CNY",
        "total": tot,
        "sessions": len(rows),
        "billing_steps": steps,
        "estimated_steps": est,
        "days": days,
        "coverage_note": (f"只有 {len(rows)} 场 / {len(days)} 天有真实账单 —— "
                          f"来自 DSH 的滚动账本，它只保留最近一场。"
                          f"这不是你的全部花费，是唯一一块能拿出账单的。"),
        "why_others_missing": "其余 harness 的本机日志里只有 token 数，没有金额。",
    }


def summarize(sessions: list) -> dict:
    """给页面的成本口径块。覆盖率是一级指标，不是脚注。

    同时给两个覆盖率，因为它们差 20 倍，只报一个都会误导：
      by_volume —— 按 token 条数（旧口径只占 0.6%，看着像没漏）
      by_cost   —— 按价格加权（旧口径占 12.3%，这才是钱的口径）
    """
    tot = old = 0.0
    raw_all = raw_old = 0
    per_provider = {}
    # 两种情况必须分开。混在一起会让「dsh 根本没有价目表」和
    # 「这场 claude-code 会话没量到 token」看起来是同一件事 —— 而它们的解法完全不同：
    # 前者要去查单价，后者要去查为什么日志里没有用量。
    no_price = {"sessions": 0, "sources": {}}
    no_usage = {"sessions": 0, "sources": {}}
    by_field = {m: 0 for _, m in FIELDS}

    for s in sessions:
        prov = provider_of(s.get("source"))
        p = PRICES.get(prov)
        raw = raw_tokens(s)
        if not p or raw <= 0:
            src = s.get("source") or "未标注"
            bucket = no_price if not p else no_usage
            bucket["sessions"] += 1
            bucket["sources"][src] = bucket["sources"].get(src, 0) + 1
            continue
        v = sum((s.get(f) or 0) * p[m] for f, m in FIELDS)
        # 旧口径：只算 in+out，且不加权 —— 原样重现，好给对照
        o = (s.get("tok_in") or 0) * p["in"] + (s.get("tok_out") or 0) * p["out"]
        tot += v; old += o
        raw_all += raw
        raw_old += (s.get("tok_in") or 0) + (s.get("tok_out") or 0)
        for f, m in FIELDS:
            by_field[m] += (s.get(f) or 0) * p[m]
        d = per_provider.setdefault(prov, {"sessions": 0, "bie": 0.0, "raw": 0})
        d["sessions"] += 1; d["bie"] += v; d["raw"] += raw

    for d in per_provider.values():
        d["bie"] = round(d["bie"])

    return {
        "metric": "BIE 价格加权 token（base-input-equivalent，无量纲）",
        "formula": "in×1.0 + cache_read×r + cache_write×w + out×o，倍数按 provider 取",
        "bie_total": round(tot),
        "bie_old_scope": round(old),
        "coverage_by_cost": round(tot and old / tot, 4) or None,
        "coverage_by_volume": round(raw_all and raw_old / raw_all, 4) or None,
        "by_field": {k: round(v) for k, v in by_field.items()},
        "by_provider": per_provider,
        "no_price": dict(no_price, why="这些来源没有价目表 —— 要么本机查不到当期单价，要么它根本不是模型会话。"),
        "no_usage": dict(no_usage, why="这些来源有价目表，但日志里一个 token 都没记 —— 是「没量到」，不是「没花钱」。"),
        "prices": priced_providers(),
        "real_money": _real_money(sessions),
        "caveats": [
            "跨 provider 加总不成立：各家缓存折扣差一个数量级（0.10 ~ 0.25）。",
            "跨 tokenizer 版本不可比：换过 tokenizer 的模型，同样文本 token 数不同。",
            "「没有价目表」和「没量到 token」是两件事，分开列：前者要去查单价，后者要去查日志。",
            "两者都不等于「成本为 0」。",
        ],
    }
