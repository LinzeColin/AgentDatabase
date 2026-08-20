#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sediment.py —— 给 **agent** 看的开发经验沉淀。

Owner 下午提的那条一直没交：
    「把所有本地 agent 对话上传到 private repo 并抽取提取沉淀经验，
      减少后续 agent 开发阻碍，降低 token 损耗」

这一份不是给人读的报告，是给**下一个接手的 agent** 读的简报：
它进某个项目之前，应该先知道什么，才不会把已经踩过的坑再踩一遍、
把已经问过十四次的问题再问一次。

全部由会话数据直接派生，**不调用任何模型**。产出两份：
  AGENT_BRIEF.md    人和 agent 都能读的简报
  agent_brief.json  机器读的同一份内容
两份都落在私有目录，绝不进公开仓 —— 里面有 Owner 的原话。
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPEAT_PREFIX = 26
REPEAT_MIN = 3


def load(sessdir: Path) -> list:
    out = []
    for f in sorted(sessdir.glob("*.sessions.jsonl")):
        for line in f.open(encoding="utf-8"):
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("start"):
                out.append(r)
    out.sort(key=lambda r: r["start"])
    return out


def topics_by_id(atlas_path: str) -> dict:
    """从 build.py 的产物里取「会话 id → 主题」。

    为什么不在这里自己判：主题分类要全语料的 IDF 权重，重算一遍等于开第二个分类器。
    两个分类器迟早给出两个答案，那时候没人知道该信哪个。
    """
    if not atlas_path:
        return {}
    p = Path(atlas_path)
    if not p.exists():
        return {}
    try:
        a = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return {s["id"]: (s.get("tp") or []) for s in (a.get("sessions") or []) if s.get("id")}


def build(sessions: list, topics: dict | None = None) -> dict:
    # 这里**故意把 agent 扇出也算进来**：扇出本身就是「该被固化却没固化」的对象。
    # 738 次同一句提示词烧掉 2.27 亿 token 正是扇出干的 —— 把它剔掉，
    # 这份简报就看不见最该修的那一件事。但标签必须说清楚，不能叫「真人会话」。
    hum = [s for s in sessions if s.get("prompts")]

    # 1) 被反复问的事 —— 每一条都是「本该固化却没固化」的证据
    groups = defaultdict(list)
    for s in hum:
        if s.get("prompts"):
            groups["".join(s["prompts"][0].split())[:REPEAT_PREFIX]].append(s)
    # 跨天复发 vs 单日批量：两种病，两种药，绝不能同名。
    # 实测：排第一的「738 次」全部发生在 2026-08-17 一天之内，是一批图片标注扇出。
    # 把它叫「被问过 738 次」会让读的人以为有人真的问了 738 遍。
    repeats, batches = [], []
    for _, rows in groups.items():
        if len(rows) < REPEAT_MIN:
            continue
        rows.sort(key=lambda r: r["start"])
        row = {
            "asked": len(rows),
            "days": len({r["start"][:10] for r in rows}),
            "first": rows[0]["start"][:10], "last": rows[-1]["start"][:10],
            "gist": rows[0]["prompts"][0][:180],
            "projects": [k for k, _ in Counter(r.get("project") or "—" for r in rows).most_common(3)],
            "tokens_spent": sum(r.get("tok_in", 0) + r.get("tok_cache_r", 0) for r in rows),
        }
        # 见 build.py 同一处：只看跨天不够，评委面板跑 4 天也能产 340 条一样的提示词。
        rate = row["asked"] / max(1, row["days"])
        if row["days"] >= 2 and rate <= 5:
            row["advice"] = "隔天又问，说明上一次的答案没留下来 —— 写进对应仓的 AGENTS.md"
            repeats.append(row)
        else:
            row["advice"] = "同一段提示词被重放 N 遍（平均每天 >5 遍）—— 该做成脚本/workflow，把提示词参数化"
            batches.append(row)
    repeats.sort(key=lambda r: -r["asked"])
    batches.sort(key=lambda r: -r["asked"])

    # 2) 每个项目的进入简报
    proj = defaultdict(lambda: {"n": 0, "turns": 0, "tools": Counter(), "topics": Counter(),
                                "errors": 0, "tok": 0, "models": Counter(),
                                "first": "", "last": "", "sources": Counter()})
    for s in hum:
        p = s.get("project") or "未标注"
        d = proj[p]
        d["n"] += 1
        d["turns"] += s.get("turns", 0)
        d["errors"] += s.get("errors", 0)
        d["tok"] += s.get("tok_in", 0) + s.get("tok_cache_r", 0)
        d["tools"].update(s.get("tool_names") or {})
        d["topics"].update(s.get("topics") or (topics or {}).get(s.get("id")) or [])
        d["sources"][s["source"]] += 1
        for m in (s.get("models") or []):
            d["models"][m] += 1
        day = s["start"][:10]
        d["first"] = min(d["first"] or day, day)
        d["last"] = max(d["last"], day)

    briefs = []
    for p, d in sorted(proj.items(), key=lambda kv: -kv[1]["n"]):
        if d["n"] < 3:
            continue
        briefs.append({
            "project": p, "sessions": d["n"], "turns": d["turns"],
            "span": f"{d['first']} → {d['last']}",
            "errors_per_session": round(d["errors"] / max(1, d["n"]), 1),
            "tokens": d["tok"],
            "tokens_per_session": int(d["tok"] / max(1, d["n"])),
            "top_topics": [k for k, _ in d["topics"].most_common(4)],
            "top_tools": [k for k, _ in d["tools"].most_common(6)],
            "harnesses": [k for k, _ in d["sources"].most_common(3)],
            "models": [k for k, _ in d["models"].most_common(3)],
        })

    # 3) 最贵的会话形态：每一「轮用户发言」平摊掉多少 token
    cost = []
    for s in hum:
        tok = s.get("tok_in", 0) + s.get("tok_cache_r", 0)
        if tok < 1_000_000:
            continue
        cost.append({
            "day": s["start"][:10], "project": s.get("project", ""),
            "title": (s.get("title") or "")[:90],
            "turns": s.get("turns", 0), "tools": s.get("tools", 0),
            "tokens": tok,
            "per_turn": int(tok / max(1, s.get("turns", 1))),
        })
    cost.sort(key=lambda r: -r["per_turn"])

    # 4) 报错最密集的地方 —— 下一个 agent 该提前防的
    pain = sorted(
        ({"project": p, "errors_per_session": round(d["errors"] / max(1, d["n"]), 1),
          "sessions": d["n"], "top_tools": [k for k, _ in d["tools"].most_common(4)]}
         for p, d in proj.items() if d["errors"] and d["n"] >= 3),
        key=lambda r: -r["errors_per_session"])[:12]

    tool_tot = Counter()
    for s in hum:
        tool_tot.update(s.get("tool_names") or {})

    return {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "audience": "接手本工作区的 agent",
        "purpose": "进项目之前先读这一份，别把踩过的坑再踩一遍、别把问过十四次的问题再问一次",
        "sessions_analysed": len(hum),
        "sessions_scope": "含 agent 扇出与批处理 —— 它们本身就是该被固化的对象",
        "repeats": repeats[:30],
        "batches": batches[:20],
        "project_briefs": briefs[:30],
        "expensive_sessions": cost[:20],
        "pain_points": pain,
        "tool_usage": [{"tool": k, "n": v} for k, v in tool_tot.most_common(25)],
        "method": "全部由会话记录直接派生，运行期不调用任何模型。"
                  "「问过几次」按每场会话第一句的前 26 个字判重；"
                  "**跨天复发**与**单日批量**分开列 —— 前者是答案没留下来，后者是活该做成脚本。",
    }


def to_markdown(b: dict) -> str:
    L = []
    A = L.append
    A("# AGENT BRIEF —— 接手前先读这一份\n")
    A(f"> 生成于 {b['generated_at']}　分析了 {b['sessions_analysed']} 场有提示词的会话。")
    A(f"> 口径：{b['sessions_scope']}")
    A(f"> {b['purpose']}\n")
    A(f"> {b['method']}\n")

    A("## 一、隔天又问过的事（先查这里，别再问一遍）\n")
    if b["repeats"]:
        A("| 问过 | 横跨 | 烧掉 token | 大意 | 涉及项目 |")
        A("|---:|---:|---:|---|---|")
        for r in b["repeats"][:15]:
            gist = r["gist"].replace("|", "／").replace("\n", " ")[:80]
            A(f"| {r['asked']} 次 | {r['days']} 天 | {r['tokens_spent']:,} | {gist} | {'、'.join(r['projects'])} |")
        A("\n每一行都是「上一次的答案没留下来」的证据 —— 结论该写进对应仓的 `AGENTS.md`。\n")
    else:
        A("目前没有跨天复发的提问。\n")

    A("## 一之二、被批量重放的提示词（该做成脚本，不是该记住）\n")
    A("> 这一节和上一节**是两种病**。上面那种是「忘了」，这种是「本来可以只写一次脚本」。")
    A("> 早前把两者混在一张表里，排第一的「被问过 738 次」其实全部发生在 2026-08-17 一天之内，")
    A("> 是一批图片标注扇出 —— 读的人会以为真有人问了 738 遍。\n")
    if b.get("batches"):
        A("| 投喂 | 起始 | 天数 | 烧掉 token | 大意 | 涉及项目 |")
        A("|---:|---|---:|---:|---|---|")
        for r in b["batches"][:12]:
            gist = r["gist"].replace("|", "／").replace("\n", " ")[:80]
            A(f"| {r['asked']} 遍 | {r['first']} | {r['days']} | {r['tokens_spent']:,} | {gist} | {'、'.join(r['projects'])} |")
        A("\n把提示词参数化写成脚本或 workflow，之后每一次都是净赚的时间。\n")
    else:
        A("目前没有单日批量投喂。\n")

    A("## 二、项目进入简报\n")
    for p in b["project_briefs"][:14]:
        A(f"### {p['project']}")
        A(f"- 会话 {p['sessions']} 场 · 你说话 {p['turns']} 次 · {p['span']}")
        A(f"- 每场平均提到 {p['errors_per_session']} 次报错　每场平均 {p['tokens_per_session']:,} token")
        A(f"- 常见话题：{'、'.join(p['top_topics']) or '—'}")
        A(f"- 常用工具：{'、'.join(p['top_tools']) or '—'}")
        A(f"- 用过的应用／模型：{'、'.join(p['harnesses'])}　{'、'.join(p['models']) or '未记录'}\n")

    A("## 三、最费钱的会话形态（每轮发言平摊的 token）\n")
    A("| 日期 | 项目 | 你说 | 工具 | 总 token | 每轮平摊 | 标题 |")
    A("|---|---|---:|---:|---:|---:|---|")
    for r in b["expensive_sessions"][:12]:
        A(f"| {r['day']} | {r['project'][:22]} | {r['turns']} | {r['tools']} | "
          f"{r['tokens']:,} | {r['per_turn']:,} | {r['title'][:44].replace('|', '／')} |")
    A("\n每轮平摊特别高的，通常是「一句话丢过去让它自己跑很久」。这不是坏事 —— "
      "但如果结果还要返工，那这一轮就是纯亏。\n")

    A("## 四、报错最密集的地方\n")
    A("| 项目 | 每场提到报错 | 会话 | 常用工具 |")
    A("|---|---:|---:|---|")
    for r in b["pain_points"]:
        A(f"| {r['project'][:30]} | {r['errors_per_session']} | {r['sessions']} | {'、'.join(r['top_tools'])} |")
    A("")

    A("## 五、工具使用分布\n")
    A("| 工具 | 调用次数 |")
    A("|---|---:|")
    for r in b["tool_usage"][:18]:
        A(f"| {r['tool']} | {r['n']:,} |")
    A("")
    return "\n".join(L) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sessions", required=True)
    ap.add_argument("--out", required=True, help="私有目录 —— 里面有 Owner 原话，绝不进公开仓")
    ap.add_argument("--web", default="", help="站点目录；给出则同时写一份到 <web>/brief/")
    ap.add_argument("--atlas", default="",
                    help="build.py 产出的 atlas.json；主题在那里判过一次，这里只读不重判 —— "
                         "自己再判一遍就是第二套口径，两边迟早对不上")
    args = ap.parse_args()
    sess = load(Path(args.sessions))
    if not sess:
        print("没有会话可分析", flush=True)
        return 1
    b = build(sess, topics_by_id(args.atlas))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    md = to_markdown(b)
    (out / "agent_brief.json").write_text(json.dumps(b, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "AGENT_BRIEF.md").write_text(md, encoding="utf-8")
    # 同时落到站点目录，让人能在 Access 后面直接打开
    if args.web:
        w = Path(args.web) / "brief"
        w.mkdir(parents=True, exist_ok=True)
        (w / "AGENT_BRIEF.md").write_text(md, encoding="utf-8")
        (w / "agent_brief.json").write_text(json.dumps(b, ensure_ascii=False), encoding="utf-8")
    print(f"AGENT_BRIEF: {len(b['repeats'])} 条跨天复发 · {len(b.get('batches') or [])} 条批量重放 · {len(b['project_briefs'])} 个项目简报 · "
          f"{len(b['pain_points'])} 个痛点 · {len(b['tool_usage'])} 种工具")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
