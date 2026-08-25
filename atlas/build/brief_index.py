#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""brief_index.py —— 离线派生 `brief_index.jsonl`，给 recall.py 用。

每行一条「下一次真的用得上」的东西：

    {"terms": [...], "line": "一句话", "pointers": [...],
     "first_seen": "...", "last_seen": "...", "n": 3, "kind": "repeat"}

四个来源，**全部确定性派生，一句都不是生成的**：
  repeat  跨天又问过的问题 + 上次落在哪（answer 的指针）
  batch   一天之内被投喂 N 遍的提示词 —— 这活该做成脚本
  agents  各仓 AGENTS.md 里「结论/为什么/代价」三段式的经验条
  pain    工具失败最密集的项目

■ 一条硬规矩：**line 必须是原话或原样统计，不许改写**
  Zep 在 LongMemEval 的 single-session-assistant 上比 full-context 低 14.2 个点，
  就是因为压缩改写牺牲了「精确复述当时的东西」。这里宁可长一点也不改写。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from recall import tokens  # noqa: E402

MAX_LINE = 180
# AGENTS.md 里的经验条。**两种形态都要认**：
#   ① 契约规定的三段式 `- **结论**：… / **为什么**：… / **代价**：…`
#   ② 现存文件里实际用的自由段落 —— 只挑「这是一条规矩」的句子，不整篇索引
# 只认 ① 的后果实测过：AgentDatabase 全仓 0 条命中，而「R2 存储类要用哪个」
# 这类真的踩过的坑就写在 ② 里。
AGENT_RULE = re.compile(r"^\s*-\s*\*\*结论\*\*[：:]\s*(.+)$")
AGENT_WHY = re.compile(r"^\s*\*\*为什么\*\*[：:]\s*(.+)$")
AGENT_COST = re.compile(r"^\s*\*\*代价\*\*[：:]\s*(.+)$")
# 规矩句的标记词。宽一点没关系 —— 检索端有区分度地板挡着，
# 索引里多几条没人命中的条目，成本是几 KB；漏掉一条真规矩，代价是再踩一次。
IMPERATIVE = re.compile(r"禁止|铁律|⛔|必须|不得|永不|一律|绝不|不许|只许|不要在|勿")
MIN_RULE_LEN = 12
MAX_RULE_LEN = 300


def _row(kind: str, line: str, pointers: list, extra: dict) -> dict:
    line = " ".join((line or "").split())[:MAX_LINE]
    ptr = [" ".join(str(p).split())[:150] for p in (pointers or []) if p][:3]
    # terms 同时吃 line 和 pointers —— 路径和命令是最值钱的字面锚点，
    # 只索引正文的话「那个脚本叫什么来着」这类问题永远命中不了。
    return dict(extra, kind=kind, line=line, pointers=ptr,
                terms=tokens(line + " " + " ".join(ptr)))


def from_atlas(atlas: dict) -> list:
    rows = []
    L = atlas.get("lessons") or {}

    for r in (L.get("repeats") or []):
        ptr = list(r.get("files") or []) + list(r.get("cmds") or [])
        line = f"「{r.get('text','')[:60]}」这个问题问过 {r.get('n')} 次、跨 {r.get('days')} 天"
        if not ptr:
            line += "，而且一个产物都没有 —— 上次的答案没被写下来"
        rows.append(_row("repeat", line, ptr, {
            "first_seen": r.get("first"), "last_seen": r.get("last"), "n": r.get("n", 0)}))

    for r in (L.get("batches") or [])[:15]:
        rows.append(_row("batch",
                         f"「{r.get('text','')[:60]}」一天之内被投喂 {r.get('n')} 次 —— 这活该做成脚本，不该手工重来",
                         [], {"first_seen": r.get("first"), "last_seen": r.get("last"),
                              "n": r.get("n", 0)}))

    for r in (L.get("pain") or [])[:12]:
        rows.append(_row("pain",
                         f"{r.get('name')} 这个项目每场会话平均 {r.get('per_tool')} 次工具失败"
                         f"（{r.get('sessions')} 场）—— 进去之前先想想哪一步最容易挂",
                         [], {"n": r.get("tool", 0)}))
    return rows


def from_agents_md(repo_root: Path) -> list:
    """各仓由人写的经验条（结论/为什么/代价三段式）。**机器蒸馏不出来的那一半。**

    收两处，缺一不可：
      · `**/dev-notes/*.md` —— 契约 2026-08-25 修订后的新落点
      · `**/AGENTS.md`      —— 修订前的存量，继续收，不然历史经验会静默消失

    为什么把经验挪出 AGENTS.md：旧契约让各仓的 AGENTS.md 被经验条撑爆
    （DouyinOps 实测 182 → 1037 行），开头的开工指令被埋掉。
    **改契约必须同时改这里** —— 只改契约的话，蒸馏器还在只 glob AGENTS.md，
    新经验一条都收不到，而 brief 照常生成、页面照常显示「数据截至」，没有任何一处会喊。
    """
    rows = []
    _srcs = sorted(set(repo_root.glob("**/dev-notes/*.md")) | set(repo_root.glob("**/AGENTS.md")))
    for p in _srcs:
        # 排除项按**仓内相对路径**判。用绝对路径判的话，
        # 在 worktree（本身就在 _scratch/ 底下）里跑，整个仓都会被跳过 ——
        # 实测就是这样：agents 类目一条都没有，只剩 rule。
        rel_str = str(p.relative_to(repo_root))
        if "node_modules" in rel_str or rel_str.startswith("_scratch/"):
            continue
        try:
            lines = p.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        rel = rel_str
        cur = None
        for ln in lines:
            # 形态②：自由段落里的规矩句
            plain = re.sub(r"[*`\[\]]", "", ln).strip()
            if (cur is None and IMPERATIVE.search(plain)
                    and MIN_RULE_LEN <= len(plain) <= MAX_RULE_LEN
                    and not plain.startswith("#")):
                rows.append(_row("agents", plain, [rel], {"src": rel}))
            m = AGENT_RULE.match(ln)
            if m:
                if cur:
                    rows.append(cur)
                cur = _row("agents", m.group(1), [rel], {"src": rel})
                continue
            if cur is None:
                continue
            w, c = AGENT_WHY.match(ln), AGENT_COST.match(ln)
            if w:
                cur["pointers"] = (cur["pointers"] + ["为什么：" + w.group(1)[:120]])[:3]
            elif c:
                cur["pointers"] = (cur["pointers"] + ["代价：" + c.group(1)[:120]])[:3]
            elif not ln.strip():
                rows.append(cur); cur = None
        if cur:
            rows.append(cur)
    # pointers 变过之后 terms 要跟着重算，否则「为什么/代价」那两行索引不到
    for r in rows:
        r["terms"] = tokens(r["line"] + " " + " ".join(r["pointers"]))
    return rows


# 本机全局契约。**它不进仓，只在本机索引** —— 但它装着代价最高的几条铁律
# （R2 零付费、主树只读、git gc 禁 --prune=now），而这些正是最该在提问那一刻
# 被摆出来的东西。不收它的后果实测过：「git gc 可以加 prune 吗」命中 0 条。
GLOBAL_RULES = [Path.home() / ".claude" / "CLAUDE.md",
                Path.home() / ".codex" / "AGENTS.md"]


def from_global_rules() -> list:
    rows = []
    for p in GLOBAL_RULES:
        if not p.is_file():
            continue
        try:
            lines = p.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for ln in lines:
            plain = re.sub(r"[*`\[\]]", "", ln).strip()
            if (IMPERATIVE.search(plain) and MIN_RULE_LEN <= len(plain) <= MAX_RULE_LEN
                    and not plain.startswith("#")):
                rows.append(_row("rule", plain, [f"~/{p.relative_to(Path.home())}"], {}))
    return rows


def build(atlas: dict, repo_root: Path | None) -> list:
    rows = from_atlas(atlas)
    if repo_root and repo_root.is_dir():
        rows += from_agents_md(repo_root)
    rows += from_global_rules()
    # 去重：同一句话不要出现两遍
    seen, out = set(), []
    for r in rows:
        k = r["line"]
        if k and k not in seen:
            seen.add(k)
            out.append(r)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--atlas", required=True, help="build.py 产出的 atlas.json")
    ap.add_argument("--repo", default="", help="仓根，用来收集 AGENTS.md 里的经验条")
    ap.add_argument("--out", required=True, help="brief_index.jsonl 落在哪")
    a = ap.parse_args()
    atlas = json.loads(Path(a.atlas).read_text(encoding="utf-8"))
    rows = build(atlas, Path(a.repo) if a.repo else None)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    kinds = {}
    for r in rows:
        kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
    print(f"索引 {len(rows)} 条  {kinds}  {out.stat().st_size / 1024:.0f}KB  →  {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
