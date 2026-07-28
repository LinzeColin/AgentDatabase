#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""【脚手架】29–31 条断言的生成器。每人复制一份，只改 S（源 ID 表）与 C（断言元组表）。

## 生成时断言（全部来自实战教训，不要删）

1. **引号内不得含省略号**（RUNBOOK 第二十九种）。
   Maeda 车道初稿有 4 条是 `「片段A... 片段B」`——两片都真，缝起来的那句他没写过。
   需要跳内容就结束引号、用自己的话过渡、再开新引号。
2. **category 必须在 ledger.py 的白名单内**（第 v0.0.0.8 轮实战）。
   只查「mental-model ≥6」这类下限是查了一半——下限可以全绿而每一条 category 都非法。
3. **每条 ≥2 源、≥2 情境**，source_ids 不得重复。
4. **status 是「命题的种类」，不是「我的把握有多大」**（Robertson #97 实战）。
   合法值 `fact | pattern | hypothesis`（`unknown/superseded` 本模板不产出）：
   - `fact` —— 一个具体的、可单点核实的命题（某年某数、他说过某句）
   - `pattern` —— 跨多个场合观察到的**规律**
   - `hypothesis` —— **soul-hypothesis 类别强制用这个**，且必须带 alternative_explanations
   把握大小写在 `confidence`（0..1）里。我曾把四条跨年份的规律标成 `fact`，
   本意是「证据很硬」，结果**门直接判为不合格**——见下一条。
5. **门数的是「category ∧ status == 'pattern'」，不是数 category。**
   `quality_check.py:185` 的口径是
   `category in {'mental-model'} and status == 'pattern'`，阈值 `min_models: 4`。
   本模板旧版只断言 `Counter(category)['mental-model'] >= 6`，
   于是 Robertson #97 出现：**模板全绿（6 条），门报 `mental models 2 < 4`。**
   前几位人物没暴露，纯粹因为他们的 mental-model 恰好多数标了 pattern。
   **下限断言必须与门同口径，否则它保证的是另一件事。**
6. **soul-hypothesis 只许出现在 `hypotheses.md`。** 门有 `claim.hypothesis-escaped`，
   在 persona.md 里锚一次就会失败。

## 写断言时的五条纪律

1. **不做没数过的枚举**：计数一律给分子/分母，不写「只有」「多数」。
2. **不替他补理由**：只给了做法而没给理由的，如实写「他没给理由」（第十七种）。
   Salatin 一轮我给他补过一个「听起来合理」的理由，事后证明是我编的。
3. **归属分层**：他转述他人的材料，里面的主张**不属于他**。
   Maeda 一轮的 `Learnings from Neon` 那套 JTBD 工具设计法是 Neon 的，不是他的。
   归因错误比措辞错误严重得多。
4. **自述 ≠ 事实**：语料若无第三方材料，他讲的经历一律标「他自述」，status 不得给 fact。
5. **过度断言必查**：凡带「从不 / 唯一 / 没有一句」的，逐条去语料找反例。
   Maeda 一轮三条这类断言全部被反例证伪（「无任职起止」「操作文档没有一句为什么」
   「HOW 是唯一可控」）。**有分母有判据的就是事实断言，必须核。**
"""
import collections, json, pathlib, sys
from datetime import datetime, timezone

NOW = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
OUT = pathlib.Path(__file__).resolve().parent / "ws-XXXX/XXXX/evidence/claims.jsonl"  # ← 改

CATEGORIES = ("fact", "mental-model", "heuristic", "value", "epistemic", "expression",
              "lineage", "blind-spot", "contradiction", "work-method", "boundary",
              "soul-hypothesis")            # 抄自 scripts/ledger.py，不要凭记忆写

S = {}                                       # ← 每人填：别名 → src-xxxxxxxxxxxx

# (category, 适用标签, 断言正文, [源别名], [情境≥2], [证伪条件], status, confidence, 时间范围)
#   soul-hypothesis 多给一项：末尾追加 [替代解释…]（门强制要求，见文件头第 6 条）
C = []                                       # ← 每人填


def main() -> int:
    rows = []
    for i, row in enumerate(C, 1):
        cat, appl, claim, srcs, ctxs, fals, status, conf, scope = row[:9]
        alts = list(row[9]) if len(row) > 9 else []
        sid = [S[k] for k in srcs]
        assert cat in CATEGORIES, f"clm {i} category 非法：{cat}"
        assert status in ("fact", "pattern", "hypothesis"), f"clm {i} status 非法：{status}"
        # ★ 门的硬规则，不是风格建议：ledger.py:76 与 quality_check.py:214
        if cat == "soul-hypothesis":
            assert status == "hypothesis", f"clm {i} soul-hypothesis 的 status 必须是 hypothesis"
            assert alts, f"clm {i} soul-hypothesis 必须给 alternative_explanations"
            assert fals, f"clm {i} soul-hypothesis 必须给 falsifiers"
        else:
            assert status != "hypothesis", f"clm {i} 只有 soul-hypothesis 可用 hypothesis"
        assert isinstance(conf, float) and 0 <= conf <= 1, f"clm {i} confidence 非法"
        assert len(sid) >= 2 and len(set(sid)) == len(sid), f"clm {i} 源不足 2 或重复"
        assert len(ctxs) >= 2, f"clm {i} 情境不足 2"
        for mark in ("...", "…"):
            assert mark not in claim, f"clm {i} 引号内含省略号：{mark}"
        rows.append({
            "alternative_explanations": alts, "applicability": [appl] + ctxs,
            "author_role": "agent", "category": cat, "claim": claim,
            "claim_id": f"clm-{i:012x}", "confidence": conf, "contexts": ctxs,
            "counter_source_ids": [], "created_at": NOW, "evidence_clusters": sid,
            "falsifiers": fals, "source_ids": sid, "status": status,
            "supersedes": None, "time_scope": scope, "updated_at": NOW,
        })
    # ★★ 与门同口径：category ∧ status == 'pattern'。**不要退回去数 category。**
    #    数 category 会在门报错的同一份数据上显示全绿——Robertson #97 实测 6 vs 2。
    cnt = collections.Counter(r["category"] for r in rows)
    n_model = sum(1 for r in rows if r["category"] == "mental-model" and r["status"] == "pattern")
    n_heur = sum(1 for r in rows if r["category"] == "heuristic" and r["status"] == "pattern")
    assert n_model >= 6, (f"mental-model(pattern) {n_model} < 6"
                          f"  ← category 计数是 {cnt['mental-model']}，**门不看这个**")
    assert n_heur >= 8, (f"heuristic(pattern) {n_heur} < 8"
                         f"  ← category 计数是 {cnt['heuristic']}，**门不看这个**")
    assert 29 <= len(rows) <= 31, f"条数 {len(rows)} 越界"
    OUT.write_text("\n".join(json.dumps(r, ensure_ascii=False, sort_keys=True) for r in rows) + "\n",
                   encoding="utf-8")
    print(f"断言 {len(rows)} 条 | 类别 {dict(cnt)}")
    print(f"  mental-model {cnt['mental-model']}(≥6) heuristic {cnt['heuristic']}(≥8)")
    print("  ✓ 生成时断言全过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
