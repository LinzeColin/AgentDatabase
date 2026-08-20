#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""taxonomy.py —— 把「来源」拆成 harness / provider / model 三层。

Owner 的原话：「dws 只是一个 cli 工具不是 LLM，openchatcut 也只是工具」。
所以这里必须把**工具**和**LLM harness**分开 —— 混在一起算 token，
工具那几场会永远显示 0 用量，看起来像「有数据但很少」，其实是「根本不该有」。

三层的意思：
  harness   你操作的那个应用（Claude Code / Codex App / Kimi Code GUI / ChatGPT / DSH）
  provider  谁在服务这个模型（Anthropic / OpenAI / DeepSeek / SCNet / Moonshot）
  model     具体型号
"""
from __future__ import annotations

import re

# 来源 → harness。kind=llm 的才产生 token；tool 的不产生，单独列。
HARNESS = {
    "claude-code":    {"label": "Claude Code", "kind": "llm", "vendor": "Anthropic", "note": "CLI 与桌面端会话"},
    "claude-desktop": {"label": "Claude Code（桌面元数据）", "kind": "llm", "vendor": "Anthropic",
                       "note": "只有会话元数据，正文在 claude-code 里，不重复计会话"},
    "codex":          {"label": "Codex App", "kind": "llm", "vendor": "OpenAI", "note": "本机 rollout 记录"},
    "kimi-code":      {"label": "Kimi Code GUI", "kind": "llm", "vendor": "Moonshot",
                       "note": "可接多家模型，实际用到 DeepSeek 与 SCNet"},
    "chatgpt":        {"label": "ChatGPT", "kind": "llm", "vendor": "OpenAI",
                       "note": "仓内历史导出，不含 token 用量字段"},
    "dsh":            {"label": "DeepSeek Harness (DSH)", "kind": "llm", "vendor": "DeepSeek / SCNet",
                       "note": "会话是多帧 zstd；1937 场里 1929 场是 subagent 扇出，已标为机器"},
    "dws":            {"label": "钉钉 CLI（dws）", "kind": "tool", "vendor": "—",
                       "note": "钉钉客户端命令行，不是 LLM，不产生 token"},
    "openchatcut":    {"label": "OpenChatCut", "kind": "tool", "vendor": "—",
                       "note": "剪辑工具，不是 LLM，不产生 token"},
}

# 模型名 → provider。按前缀判，顺序即优先级。
PROVIDER_RULES = [
    (re.compile(r"^scnet/", re.I),                    "SCNet（中国超算）"),
    (re.compile(r"^deepseek-official/", re.I),        "DeepSeek"),
    (re.compile(r"^deepseek/|^deepseek-", re.I),      "DeepSeek"),
    (re.compile(r"^moonshot/|^kimi-", re.I),          "Moonshot"),
    (re.compile(r"^claude", re.I),                    "Anthropic"),
    (re.compile(r"^(gpt|o[13-9]|chatgpt|codex)", re.I), "OpenAI"),
    (re.compile(r"^(glm|qwen|minimax)", re.I),        "其他国内厂商"),
]

# 不是真模型名的占位符。计进模型分布会凭空造出一个不存在的「模型」。
PLACEHOLDER_MODELS = {"__secondary__", "<synthetic>", "", "unknown"}

# provider_hint 的原样值 → 展示名
HINT_MAP = {"deepseek-official": "DeepSeek", "openai": "OpenAI", "anthropic": "Anthropic",
            "scnet": "SCNet（中国超算）", "moonshot": "Moonshot"}


def provider_of(model: str, hint: str = "") -> str:
    if not model or model in PLACEHOLDER_MODELS:
        return HINT_MAP.get(hint.lower(), hint.title()) if hint else "未记录"
    for pat, name in PROVIDER_RULES:
        if pat.search(model):
            return name
    if hint:
        return HINT_MAP.get(hint.lower(), hint.title())
    return "未归类"


def model_family(model: str) -> str:
    """把 claude-opus-5[1m] / scnet/deepseek-v4-flash-0731 归到型号族。"""
    if not model or model in PLACEHOLDER_MODELS:
        return "未记录"
    m = model.split("/")[-1]
    m = re.sub(r"\[[^\]]*\]$", "", m)            # 去掉 [1m] 这类后缀
    m = re.sub(r"-\d{6,}$", "", m)               # 去掉 -0731 / -20251001 这类日期
    return m


def harness_of(source: str) -> dict:
    return HARNESS.get(source, {"label": source, "kind": "llm", "vendor": "未知", "note": ""})


def is_llm(source: str) -> bool:
    return harness_of(source)["kind"] == "llm"


def summarize(sessions: list) -> dict:
    """按 harness / provider / model 三层汇总 token 与会话。"""
    from collections import Counter, defaultdict

    def blank():
        return {"sessions": 0, "measured": 0, "input_excl": 0, "cached": 0,
                "cache_write": 0, "output": 0, "turns": 0, "tools": 0}

    def fold(b, s, weight=1):
        b["sessions"] += weight
        ci, cc, co = s.get("tok_in", 0), s.get("tok_cache_r", 0), s.get("tok_out", 0)
        if ci or cc or co:
            b["measured"] += weight
        b["input_excl"] += ci * weight
        b["cached"] += cc * weight
        b["cache_write"] += s.get("tok_cache_w", 0) * weight
        b["output"] += co * weight
        b["turns"] += s.get("turns", 0) * weight
        b["tools"] += s.get("tools", 0) * weight

    def close(b):
        raw = b["input_excl"] + b["cached"]
        b["input_total"] = raw
        # 分母为 0 写 None 而不是 0：没有用量 ≠ 命中率是 0%
        b["hit_rate"] = (b["cached"] / raw) if raw else None
        return b

    by_h, by_p, by_m = defaultdict(blank), defaultdict(blank), defaultdict(blank)
    pair = defaultdict(blank)                    # provider × model
    hm = defaultdict(Counter)                    # harness → 用到哪些模型

    for s in sessions:
        src = s["source"]
        h = harness_of(src)
        fold(by_h[src], s)
        mods = [m for m in (s.get("models") or []) if m not in PLACEHOLDER_MODELS]
        if not mods:
            prov = provider_of("", s.get("provider_hint", "")) if h["kind"] == "llm" else "—"
            fold(by_p[prov], s)
            fold(by_m["未记录"], s)
            fold(pair[(prov, "未记录")], s)
            hm[src]["未记录"] += 1
            continue
        # 一场会话可能换过模型。**按模型数均分**而不是每个都记全量，
        # 否则总量会被放大成模型个数倍 —— 这是最容易做出的假数据。
        w = 1.0 / len(mods)
        for mo in mods:
            fam = model_family(mo)
            prov = provider_of(mo, s.get("provider_hint", ""))
            fold(by_p[prov], s, w)
            fold(by_m[fam], s, w)
            fold(pair[(prov, fam)], s, w)
            hm[src][fam] += 1

    def rows(d, key):
        out = []
        for k, v in d.items():
            r = dict(close(v))
            r[key] = k
            r["sessions"] = round(r["sessions"], 1)
            r["measured"] = round(r["measured"], 1)
            out.append(r)
        return sorted(out, key=lambda r: -r["input_total"])

    harness_rows = []
    for src, v in by_h.items():
        h = harness_of(src)
        r = dict(close(v))
        r.update(source=src, label=h["label"], kind=h["kind"], vendor=h["vendor"], note=h["note"],
                 models=[k for k, _ in hm[src].most_common(6)])
        harness_rows.append(r)
    harness_rows.sort(key=lambda r: (r["kind"] != "llm", -r["input_total"]))

    return {
        "note": "harness = 你操作的应用；provider = 谁在服务模型；model = 具体型号。"
                "标 tool 的不是 LLM，不产生 token，单独列出而不是混进分母。",
        "harness": harness_rows,
        "provider": rows(by_p, "provider"),
        "model": rows(by_m, "model"),
        "provider_model": sorted(
            [dict(close(v), provider=k[0], model=k[1], sessions=round(v["sessions"], 1)) for k, v in pair.items()],
            key=lambda r: -r["input_total"])[:40],
        "tools_not_llm": [r for r in harness_rows if r["kind"] == "tool"],
    }
