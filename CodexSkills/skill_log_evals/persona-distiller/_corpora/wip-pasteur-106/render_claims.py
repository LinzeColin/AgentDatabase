#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把断言渲染进核心产物，并留下 `<!-- claim:clm-xxx -->` 标记。

**这一步不是为了消 orphan 警告**——是产物本身该有的：
断言层写了 33 条，若它们不出现在任何一份对外文档里，那 33 条就只活在账本里。
`claim.orphan` 判的正是这件事。
"""
import json, pathlib, collections

WS = pathlib.Path("workspaces/louis-pasteur")
C = [json.loads(l) for l in (WS / "evidence/claims.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]

# 类别 → 落到哪份文档（**按内容归属，不按凑数**）
DEST = {"fact": "facts.md", "work-method": "work.md", "heuristic": "decision-policy.md",
        "mental-model": "cognitive-os.md", "boundary": "boundaries.md",
        "blind-spot": "capabilities.md", "contradiction": "divergence-map.md",
        "value": "strategy.md", "epistemic": "strategy.md"}
TITLE = {"facts.md": "## 断言层（逐条可回语料）",
         "work.md": "## 可复用的做法（有步骤且有判据）",
         "decision-policy.md": "## 经验判据",
         "cognitive-os.md": "## 认知模型",
         "boundaries.md": "## 边界断言",
         "capabilities.md": "## 盲区",
         "divergence-map.md": "## 自相冲突之处（不遮）",
         "strategy.md": "## 价值与认识论口径"}

by = collections.defaultdict(list)
for c in C:
    d = DEST.get(c["category"])
    if d:
        by[d].append(c)

for fn, items in by.items():
    p = WS / fn
    t = p.read_text(encoding="utf-8") if p.exists() else f"# {fn[:-3]}\n"
    t = t.split("\n<!-- ↓ 断言渲染区")[0].rstrip()
    lines = [t, "", "", "<!-- ↓ 断言渲染区（由 render_claims.py 生成，勿手改） -->", "",
             TITLE.get(fn, "## 断言")]
    for c in sorted(items, key=lambda x: x["claim_id"]):
        lines.append("")
        lines.append(f"<!-- claim:{c['claim_id']} -->")
        lines.append(c["claim"])
        if c.get("falsifiers"):
            lines.append(f"\n> **何时作废**：{c['falsifiers'][0]}")
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  {fn:22} 渲染 {len(items):2} 条，{len(p.read_text(encoding='utf-8'))} 字节")

print(f"共 {sum(len(v) for v in by.values())} / {len(C)} 条落进核心产物")
