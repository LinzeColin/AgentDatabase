#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""recall.py —— 提问那一刻，把已经踩过的坑摆到眼前。

**现状的失效点**【实测 2026-08-20】：现在注入的只是一个 `gh api` 地址，不是内容。
本次会话实测转化率就是 **0** —— 调研 agent 全程没执行那条命令，
是翻文件系统才偶然读到 brief。给地址等于没给。

所以改成：`UserPromptSubmit` 钩子 + 本地字面索引，命中就把**内容**注进去。

■ 为什么不需要模型
  BM25 是算术不是推理。而且沉淀内容几乎全是路径、命令、错误码、仓名 ——
  **精确标识符上字面匹配本来就优于语义 embedding**。
  钩子的 context 成本官方原话是「Zero, unless the hook returns output」，
  触发是「Always fires on its event」——不依赖模型判断要不要读。

■ 三条必须守住的失败形态
  1. 语料里从没出现过的问题 → **0 注入**。什么都命中 = 假绿。
  2. 索引文件不存在 → **静默成功**，绝不阻断提问。
  3. 注入体积封顶（≤3 条、每条 ≤2 行）。

■ 不要拿「省了多少 token」当指标
  【第三方】cached input 占 token 的 96.46%、占成本的 63.91%，模型输出只占 0.38%。
  针对注入体积的优化映射到总成本上不足 1%。
  **注入的价值来自少返工一次，不来自省下几百 token。**

零依赖，只用标准库。运行期不调用任何模型。
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path

MAX_HITS = 3
MAX_LINES_PER_HIT = 2
# 命中门槛**随索引规模走**，不是一个绝对数。
# BM25 的分数正比于 idf，而 idf 正比于 log(文档数) —— 一个在 84 条索引上
# 调好的绝对阈值（4.0），换到 3 条的索引上会把**所有**命中都毙掉。
# 0.9×log(1+n)：n=84 时约 4.0（保住已验过的那档表现），n=3 时约 1.25。
SCORE_FACTOR = 0.9
MIN_TERMS = 2            # 至少两个**有区分度**的词元同时命中，孤证不注
K1, B = 1.5, 0.75

# 虚词。索引只有几十条时 BM25 的 IDF 压不住它们：
# 实测「What is the capital of Burkina Faso」靠 the/is/of 命中了 3 条，
# 而那三条跟布基纳法索毫无关系。这是「什么都命中」的典型形态。
STOP = {
    "the", "and", "for", "you", "your", "are", "was", "were", "this", "that", "with",
    "from", "into", "have", "has", "not", "but", "all", "any", "can", "will", "would",
    "should", "what", "when", "where", "which", "who", "how", "why", "its", "his", "her",
    "our", "their", "them", "they", "then", "than", "there", "here", "about", "over",
    "一个", "一下", "这个", "那个", "什么", "怎么", "可以", "需要", "已经", "现在",
    "帮我", "我们", "他们", "还是", "如果", "因为", "所以", "但是", "然后", "这样",
}

_ASCII = re.compile(r"[A-Za-z_][A-Za-z0-9_.\-/]{2,}")
# 标识符：一眼就知道是专名的词元（长 ASCII、带斜杠/下划线/点）。
# 这类词元**天然有区分度**，不该被 idf 地板挡掉 —— 地板是按文档占比算的，
# 而 `OpenAIDatabase` 在那个仓的 AGENTS.md 里到处都是，占比高但仍然是专名。
# 实测：不给这条豁免，「OpenAIDatabase 的 data 目录能删吗」命中 0 条。
_IDENT = re.compile(r"^[a-z_][a-z0-9_.\-/]{7,}$|[/_.]")
_CJK = re.compile(r"[一-鿿]+")
_NUMCODE = re.compile(r"\b(?:[A-Z]{2,}-?\d{2,}|\d{3,})\b")


def tokens(text: str) -> list:
    """字面词元。**不做词干、不做同义、不做向量** —— 要的就是「一模一样」。

    中文切 2 字和 3 字滑窗：中文没有空格，只按整段取会一个都对不上；
    切到 1 字则满屏都是命中。2~3 字是实测下来唯一能同时避开这两头的粒度。
    """
    t = text or ""
    out = [m.group(0).lower() for m in _ASCII.finditer(t)]
    out += [m.group(0) for m in _NUMCODE.finditer(t)]
    for seg in _CJK.findall(t):
        for n in (2, 3):
            for i in range(len(seg) - n + 1):
                out.append(seg[i:i + n])
    return [x for x in out if x not in STOP]


class Index:
    """一个小到可以整个读进内存的字面索引。本机实测索引 < 1MB。"""

    def __init__(self, rows: list):
        self.rows = rows
        self.docs = [Counter(r.get("terms") or []) for r in rows]
        self.len = [sum(d.values()) or 1 for d in self.docs]
        self.avg = sum(self.len) / max(1, len(self.len))
        df = Counter()
        for d in self.docs:
            df.update(d.keys())
        n = max(1, len(self.docs))
        self.idf = {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}
        self.df = df
        # 区分度闸：**按文档频次算，不按 idf 值算**。
        # 第一版拿一个从 n 推出来的 idf 阈值去比，结果在小索引上把**所有**词元
        # 都毙掉了（n=3 时任何词元的 df/n 都 ≥1/3）—— 三条测试全灭才发现。
        # 下限 3 是给小索引留的底：只有三条文档时，「频次高」不构成「没区分度」。
        self.df_max = max(3, n * 0.25)
        self.score_floor = SCORE_FACTOR * math.log(1 + n)

    @classmethod
    def load(cls, path) -> "Index | None":
        """读不到就返回 None。**调用方必须容忍 None** —— 索引缺席不是错误。"""
        try:
            p = Path(path)
            rows = [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
        except (OSError, ValueError):
            return None
        return cls(rows) if rows else None

    def search(self, query: str, k: int = MAX_HITS) -> list:
        q = tokens(query)
        if not q:
            return []
        qc = Counter(q)
        scored = []
        for i, d in enumerate(self.docs):
            sc = 0.0
            hit_terms = 0
            for t, qf in qc.items():
                f = d.get(t, 0)
                if not f:
                    continue
                idf = self.idf.get(t, 0.0)
                if self.df.get(t, 0) > self.df_max and not _IDENT.search(t):
                    continue        # 太常见、又不是专名的词元，不算证据
                hit_terms += 1
                sc += idf * (f * (K1 + 1)) / (f + K1 * (1 - B + B * self.len[i] / self.avg))
            # 分数够 **且** 有区分度的词元够。只卡分数的话，
            # 一堆低区分度词元累加也能翻过门槛 —— 那正是假命中的来源。
            if sc >= self.score_floor and hit_terms >= MIN_TERMS:
                scored.append((sc, i))
        scored.sort(key=lambda x: -x[0])
        return [dict(self.rows[i], _score=round(s, 2)) for s, i in scored[:k]]


def render(hits: list) -> str:
    """注入文本。**只给指针，不写摘要** —— 压缩改写会牺牲「精确复述当时的东西」。"""
    if not hits:
        return ""
    out = ["以下是这台机器上已经踩过的坑，按字面命中，不是模型判断的："]
    for h in hits:
        line = (h.get("line") or "").strip()
        if not line:
            continue
        out.append(f"- {line}"[:220])
        ptr = [p for p in (h.get("pointers") or []) if p][:MAX_LINES_PER_HIT - 1]
        for p in ptr:
            out.append(f"  → {p}"[:220])
    return "\n".join(out) if len(out) > 1 else ""


def recall(prompt: str, index_path) -> str:
    idx = Index.load(index_path)
    if idx is None:
        return ""                    # 索引缺席 = 静默成功，绝不阻断提问
    return render(idx.search(prompt))
