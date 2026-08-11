#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把断言渲染进核心产物，并留下 `<!-- claim:clm-xxx -->` 标记。

**这一步不是为了消 `claim.orphan` 警告**——是产物本身该有的：
断言层写了 N 条，若它们不出现在任何一份对外文档里，那 N 条就只活在账本里。
`claim.orphan` 判的正是这件事。

## 它此前只是某一轮的临时脚本

原件躺在 `_corpora/wip-pasteur-106/render_claims.py`，工作区路径**写死在源码里**，
`scripts/` 里没有、任何调用点也不认识它——于是后面每个人物都得重抄一遍。
[[tool-existed-and-i-did-it-by-hand]]。本件是把它提升成正式工具时的版本。

## ★★★ 提升时修掉的一个缺陷：未映射的类别被**静默丢掉**

原件写的是：

    d = DEST.get(c["category"])
    if d:
        by[d].append(c)

`ledger.py` 的受控词表有 12 个类别，而原件的 `DEST` 只列了 9 个——
`expression`／`lineage`／`soul-hypothesis` 三类**一条也落不进产物，且不报错**。
末行那句「共 N / M 条落进核心产物」是唯一的痕迹，而 N<M 很容易被读成「有些本来就不该落」。
[[empty-default-swallows-unknown]]：`[]`／`0 个文件` 都会被读成「没问题」。

现在：**没有映射就报错并非零退出**，不许悄悄少渲染。
"""
import argparse
import collections
import json
import pathlib
import sys

# 类别 → 落到哪份文档（**按内容归属，不按凑数**）。
# 键必须覆盖 `scripts/ledger.py:CLAIM_CATEGORIES` 的全部 12 个。
DEST = {
    "fact": "facts.md",
    "work-method": "work.md",
    "heuristic": "decision-policy.md",
    "mental-model": "cognitive-os.md",
    "boundary": "boundaries.md",
    "blind-spot": "capabilities.md",
    "contradiction": "divergence-map.md",
    "value": "strategy.md",
    "epistemic": "strategy.md",
    "expression": "persona.md",
    "lineage": "facts.md",
    "soul-hypothesis": "hypotheses.md",
}
TITLE = {
    "facts.md": "## 断言层（逐条可回语料）",
    "work.md": "## 可复用的做法（有步骤且有判据）",
    "decision-policy.md": "## 经验判据",
    "cognitive-os.md": "## 认知模型",
    "boundaries.md": "## 边界断言",
    "capabilities.md": "## 盲区",
    "divergence-map.md": "## 自相冲突之处（不遮）",
    "strategy.md": "## 价值与认识论口径",
    "persona.md": "## 声音与表达（可核到语料）",
    "hypotheses.md": "## 假设（未证实）",
}
MARK = "\n<!-- ↓ 断言渲染区"


def render(ws: pathlib.Path, write: bool = True) -> tuple:
    """→ (每份文档渲染了几条, 未映射的类别)。**未映射一律回报，不静默丢。**"""
    claims = [json.loads(l) for l in
              (ws / "evidence/claims.jsonl").read_text(encoding="utf-8").splitlines()
              if l.strip()]
    by = collections.defaultdict(list)
    unmapped = collections.Counter()
    for c in claims:
        dest = DEST.get(c.get("category"))
        if dest is None:
            unmapped[c.get("category")] += 1
            continue
        by[dest].append(c)
    counts = {}
    for fn, items in sorted(by.items()):
        path = ws / fn
        text = path.read_text(encoding="utf-8") if path.exists() else "# %s\n" % fn[:-3]
        text = text.split(MARK)[0].rstrip()
        lines = [text, "", "",
                 "<!-- ↓ 断言渲染区（由 render_claims.py 生成，勿手改） -->", "",
                 TITLE.get(fn, "## 断言")]
        for c in sorted(items, key=lambda x: x["claim_id"]):
            lines.append("")
            lines.append("<!-- claim:%s -->" % c["claim_id"])
            lines.append(c["claim"])
            if c.get("falsifiers"):
                lines.append("\n> **何时作废**：%s" % c["falsifiers"][0])
        if write:
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        counts[fn] = len(items)
    return counts, unmapped


def self_test() -> int:
    """正反自测。反对照两条：未映射必须报出来；重复渲染必须幂等。"""
    import tempfile
    fails = []

    def chk(label, got, want):
        print("  %s %s%s" % ("✓" if got == want else "✗", label,
                             "" if got == want else "  得 %r 应为 %r" % (got, want)))
        if got != want:
            fails.append(label)

    # ★ 正对照：受控词表里的 12 个类别**必须全部有落点**。
    #   这一条是这次提升的起因——原件只有 9 个，另 3 个静默消失。
    import re as _re
    here = pathlib.Path(__file__).resolve().parent
    ledger = (here / "ledger.py").read_text(encoding="utf-8")
    # ★★★ 必须跨行解析：`CLAIM_CATEGORIES` 是多行元组。
    #   第一版只取了起始那一行，解析出 **0 个类别**，于是
    #   「12 个类别全部有落点」这条**恒真**——空集合让判据自动通过。
    #   [[empty-default-swallows-unknown]]。所以下面先断言「解析到的不能是空的」。
    _m = _re.search(r"CLAIM_CATEGORIES\s*=\s*\((.*?)\)", ledger, _re.S)
    cats = _re.findall(r"['\"]([a-z-]+)['\"]", _m.group(1)) if _m else []
    chk("①a 受控词表解析得到的类别数 > 0（空集合会让 ①b 恒真）", len(cats) > 0, True)
    chk("①b 受控词表 %d 个类别全部有落点" % len(cats),
        sorted(set(cats) - set(DEST)), [])

    with tempfile.TemporaryDirectory() as d:
        ws = pathlib.Path(d)
        (ws / "evidence").mkdir()
        rows = [{"claim_id": "clm-aaaaaaaaaaaa", "category": "fact", "claim": "甲",
                 "falsifiers": ["若甲不成立"]},
                {"claim_id": "clm-bbbbbbbbbbbb", "category": "expression", "claim": "乙"},
                {"claim_id": "clm-cccccccccccc", "category": "不存在的类别", "claim": "丙"}]
        (ws / "evidence/claims.jsonl").write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")
        counts, unmapped = render(ws)
        chk("② fact 落进 facts.md", counts.get("facts.md"), 1)
        # ★★ 反对照：`expression` 落进 persona.md——原件会把它丢掉且不报错
        chk("③ expression 落进 persona.md", counts.get("persona.md"), 1)
        # ★★★ 反对照：未映射的类别**必须被报出来**，不许静默丢
        chk("④ 未映射类别被报出", dict(unmapped), {"不存在的类别": 1})
        first = (ws / "facts.md").read_text(encoding="utf-8")
        render(ws)
        chk("⑤ 重复渲染幂等", (ws / "facts.md").read_text(encoding="utf-8"), first)
        chk("⑥ 标记写进正文", "<!-- claim:clm-aaaaaaaaaaaa -->" in first, True)
        chk("⑦ 作废条件带出来", "**何时作废**" in first, True)
    print("自测 %d 项，失败 %d" % (8, len(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("workspace", nargs="?", type=pathlib.Path)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        sys.exit(self_test())
    if not a.workspace:
        print(__doc__)
        sys.exit(2)
    counts, unmapped = render(a.workspace)
    for fn, n in sorted(counts.items()):
        print("  %-22s 渲染 %2d 条" % (fn, n))
    print("共 %d 条落进核心产物" % sum(counts.values()))
    if unmapped:
        print("✗ **有类别没有落点，这些断言一条也没进产物**：%s"
              % dict(unmapped))
        print("  → 补 `DEST` 的映射，**不要当成「本来就不该落」**。")
        sys.exit(1)
    sys.exit(0)
