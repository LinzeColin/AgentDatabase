#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""metrics.py —— token／缓存、经济指数、耦合网络三个派生块。

纯标准库，运行期不调用任何模型。每个指标都写明口径，算不出来就标「不确定」。
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

# Owner 在悉尼。固定 +10，不猜夏令时 —— 猜错比差一小时更糟。
TZ_OFFSET_H = 10

# 参照 Owner 给的 codex_cache_hit_report 口径，逐字对齐：
#   缓存命中率 = cached_input_tokens / input_tokens，按 input token 加权
#   其中 input_tokens **含**缓存命中部分
# 本仓 extract 存的是「不含缓存」的 tok_in，所以这里要加回去再算，
# 否则同一份数据会算出两个不同的命中率。
CACHE_METRIC = "cached / (input_excl_cache + cached)，按 token 加权；input 口径含缓存，与参照报告一致"

SLICE_BUCKETS = [(0, 6, "00:00–05:59"), (6, 12, "06:00–11:59"),
                 (12, 18, "12:00–17:59"), (18, 24, "18:00–23:59")]


def local_dt(iso: str) -> datetime | None:
    if not iso:
        return None
    try:
        d = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except ValueError:
        return None
    return d.astimezone(timezone.utc) + timedelta(hours=TZ_OFFSET_H)


def _blank() -> dict:
    return {"sessions": 0, "measured": 0, "input_excl": 0, "cached": 0,
            "cache_write": 0, "output": 0}


def _fold(b: dict, s: dict) -> None:
    b["sessions"] += 1
    ci, cc = s.get("tok_in", 0), s.get("tok_cache_r", 0)
    if ci or cc or s.get("tok_out", 0):
        b["measured"] += 1
    b["input_excl"] += ci
    b["cached"] += cc
    b["cache_write"] += s.get("tok_cache_w", 0)
    b["output"] += s.get("tok_out", 0)


def _close(b: dict) -> dict:
    raw_in = b["input_excl"] + b["cached"]
    b["input_total"] = raw_in
    # 分母为 0 时写 None 而不是 0：没有用量不等于命中率是 0%。
    # 「算不出」和「0」在看板上长得一样，但意思完全相反。
    b["hit_rate"] = (b["cached"] / raw_in) if raw_in else None
    b["unmeasured"] = b["sessions"] - b["measured"]
    return b


def token_block(sessions: list) -> dict:
    """按天／周／时段／来源／会话五种切法给 token 与缓存。"""
    by_day, by_week, by_slice, by_source, by_kind = (defaultdict(_blank) for _ in range(5))
    per_session = []
    for s in sessions:
        d = local_dt(s.get("start", ""))
        if not d:
            continue
        day = d.date().isoformat()
        iy, iw, _ = d.isocalendar()
        _fold(by_day[day], s)
        _fold(by_week[f"{iy}-W{iw:02d}"], s)
        _fold(by_source[s["source"]], s)
        _fold(by_kind[s.get("kind", "human")], s)
        for lo, hi, label in SLICE_BUCKETS:
            if lo <= d.hour < hi:
                _fold(by_slice[label], s)
                break
        raw_in = s.get("tok_in", 0) + s.get("tok_cache_r", 0)
        if raw_in or s.get("tok_out", 0):
            per_session.append({
                "id": s["id"], "day": day, "at": d.strftime("%Y-%m-%d %H:%M"),
                "hour": d.hour, "src": s["source"], "kind": s.get("kind", "human"),
                "project": s.get("project", ""), "title": (s.get("title") or "")[:70],
                "turns": s.get("turns", 0), "tools": s.get("tools", 0),
                "input_total": raw_in, "cached": s.get("tok_cache_r", 0),
                "cache_write": s.get("tok_cache_w", 0), "output": s.get("tok_out", 0),
                "hit": round(s.get("tok_cache_r", 0) / raw_in, 6) if raw_in else None,
                "models": s.get("models", [])[:2],
            })
    per_session.sort(key=lambda r: -r["input_total"])

    total = _blank()
    for s in sessions:
        _fold(total, s)
    _close(total)

    return {
        "metric": CACHE_METRIC,
        "timezone": f"Australia/Sydney (UTC+{TZ_OFFSET_H}，未处理夏令时)",
        "total": total,
        "by_day": [dict(_close(v), d=k) for k, v in sorted(by_day.items())],
        "by_week": [dict(_close(v), w=k) for k, v in sorted(by_week.items())],
        "by_slice": [dict(_close(by_slice[lbl]), slice=lbl)
                     for _, _, lbl in SLICE_BUCKETS if lbl in by_slice],
        "by_source": [dict(_close(v), s=k) for k, v in
                      sorted(by_source.items(), key=lambda kv: -kv[1]["input_excl"])],
        "by_kind": [dict(_close(v), k=k) for k, v in by_kind.items()],
        "sessions": per_session[:900],
        "sessions_total": len(per_session),
        # 有多少场根本没有用量记录，必须自己站出来说，不能只在分母里消失
        "no_usage": sum(1 for s in sessions
                        if not (s.get("tok_in") or s.get("tok_cache_r") or s.get("tok_out"))),
    }


# —— 经济指数 ——
# 对标 Anthropic Economic Index 的三个核心问法，换成 Owner 自己的数据能回答的形式：
#   1. 自动化 vs 协作   —— 一次指令让机器干完 vs 来回打磨
#   2. 任务份额随时间   —— 注意力结构怎么迁移的
#   3. 集中度           —— 精力是摊开的还是压在少数几件事上
AUTOMATION_TOOLS_MIN = 8


def _mode(s: dict) -> str:
    """把一场会话分成自动化／协作／单问。判据是行为，不是主题。"""
    turns, tools = s.get("turns", 0), s.get("tools", 0)
    if turns <= 1 and tools >= AUTOMATION_TOOLS_MIN:
        return "自动化"      # 一句话丢过去，机器自己干了一长串
    if turns >= 5:
        return "协作"        # 来回打磨
    if turns <= 1:
        return "单问"        # 问一句拿一个答案
    return "轻协作"


def _hhi(counts: dict) -> float | None:
    """赫芬达尔指数：0 = 完全摊开，1 = 全压在一件事上。"""
    total = sum(counts.values())
    if not total:
        return None
    return round(sum((v / total) ** 2 for v in counts.values()), 4)


def economics_block(sessions: list, ladder: dict) -> dict:
    hum = [s for s in sessions if s.get("kind") == "human"]
    modes = Counter(_mode(s) for s in hum)

    weeks = defaultdict(lambda: {"modes": Counter(), "topics": Counter(),
                                 "projects": Counter(), "n": 0,
                                 "tools": 0, "turns": 0})
    for s in hum:
        d = local_dt(s.get("start", ""))
        if not d:
            continue
        iy, iw, _ = d.isocalendar()
        w = weeks[f"{iy}-W{iw:02d}"]
        w["n"] += 1
        w["modes"][_mode(s)] += 1
        w["tools"] += s.get("tools", 0)
        w["turns"] += s.get("turns", 0)
        for t in s.get("topics", []):
            w["topics"][t] += 1
        if s.get("project"):
            w["projects"][s["project"]] += 1

    week_rows = []
    for k in sorted(weeks):
        w = weeks[k]
        tot_t = sum(w["topics"].values()) or 1
        week_rows.append({
            "w": k, "n": w["n"],
            "modes": dict(w["modes"]),
            "share": {t: round(v / tot_t, 4) for t, v in w["topics"].items()},
            "hhi_topic": _hhi(w["topics"]), "hhi_project": _hhi(w["projects"]),
            "tools_per_turn": round(w["tools"] / w["turns"], 2) if w["turns"] else None,
        })

    ladder_total = sum(ladder.values()) or 1
    return {
        "definition": {
            "自动化": f"你只说了 ≤1 次、机器却调用了 ≥{AUTOMATION_TOOLS_MIN} 次工具 —— 一句话丢过去它自己干完",
            "协作": "你说了 ≥5 次 —— 来回打磨出来的",
            "轻协作": "2~4 次往返",
            "单问": "问一句拿一个答案，机器几乎没动工具",
            "集中度": "赫芬达尔指数 HHI，0 = 精力完全摊开，1 = 全压在一件事上",
            "每轮工具数": "工具调用次数 ÷ 你说话次数，衡量一句话能撬动多少活",
        },
        "modes": dict(modes),
        "mode_share": {k: round(v / max(1, len(hum)), 4) for k, v in modes.items()},
        "weeks": week_rows,
        "ladder_share": {k: round(v / ladder_total, 4) for k, v in ladder.items()},
        "hhi_topic_all": _hhi(Counter(t for s in hum for t in s.get("topics", []))),
        "hhi_project_all": _hhi(Counter(s.get("project") or "未标注" for s in hum)),
    }


# —— 耦合网络 ——
# 宇宙那一屏之前只是把点撒开，看不出任何关系。这里把「同一场会话里共同出现」
# 变成边：项目↔主题、主题↔主题、来源↔项目。有边才谈得上耦合。
def coupling_block(sessions: list, min_weight: int = 2) -> dict:
    hum = [s for s in sessions if s.get("kind") == "human"]
    nodes: dict[str, dict] = {}
    edges: Counter = Counter()

    def node(nid: str, kind: str, label: str) -> None:
        n = nodes.setdefault(nid, {"id": nid, "kind": kind, "label": label, "w": 0})
        n["w"] += 1

    for s in hum:
        proj = s.get("project") or ""
        tops = s.get("topics", [])
        src = s["source"]
        node(f"src:{src}", "source", src)
        if proj:
            node(f"proj:{proj}", "project", proj)
            edges[(f"src:{src}", f"proj:{proj}")] += 1
        for t in tops:
            node(f"topic:{t}", "topic", t)
            if proj:
                edges[(f"proj:{proj}", f"topic:{t}")] += 1
        for i, a in enumerate(tops):
            for b in tops[i + 1:]:
                key = tuple(sorted((f"topic:{a}", f"topic:{b}")))
                edges[key] += 1

    keep = [{"a": a, "b": b, "w": w} for (a, b), w in edges.items() if w >= min_weight]
    keep.sort(key=lambda e: -e["w"])
    keep = keep[:900]
    used = {e["a"] for e in keep} | {e["b"] for e in keep}
    return {
        "nodes": [n for n in nodes.values() if n["id"] in used],
        "edges": keep,
        "note": f"边 = 同一场会话里共同出现的次数，≥{min_weight} 次才画。"
                f"只统计你亲自开口的会话。",
        "dropped_edges": len(edges) - len(keep),
    }


# —— 交付对照 ——
# 会话记录只能证明你**在做**，GitHub 才能证明你**做出来了**。
# 两条曲线放在一起，「建设 : 交付」那个比例才不是自说自话。
def delivery_block(sessions: list, gh: dict) -> dict:
    if not gh or gh.get("state") == "不确定":
        return {"state": "不确定",
                "why": (gh or {}).get("why", "没有 GitHub 数据"),
                "days": [], "projects": [], "totals": {}}

    hum = [s for s in sessions if s.get("kind") == "human"]
    sess_by_day = Counter()
    turns_by_day = Counter()
    for s in hum:
        d = local_dt(s.get("start", ""))
        if d:
            sess_by_day[d.date().isoformat()] += 1
            turns_by_day[d.date().isoformat()] += s.get("turns", 0)

    gh_by_day = {r["d"]: r for r in gh.get("days", [])}
    all_days = sorted(set(sess_by_day) | set(gh_by_day))
    rows = []
    for d in all_days:
        g = gh_by_day.get(d, {})
        rows.append({
            "d": d,
            "sessions": sess_by_day.get(d, 0),
            "turns": turns_by_day.get(d, 0),
            "commits": g.get("commits", 0),
            "prs": g.get("prs", 0),
            "merged": g.get("merged", 0),
            "releases": g.get("releases", 0),
            "repos": g.get("repos", {}),
        })

    talked = [r for r in rows if r["sessions"] > 0]
    shipped = [r for r in rows if r["commits"] > 0]
    both = [r for r in rows if r["sessions"] > 0 and r["commits"] > 0]
    talk_only = [r for r in rows if r["sessions"] > 0 and r["commits"] == 0]
    ship_only = [r for r in rows if r["sessions"] == 0 and r["commits"] > 0]

    tot_s = sum(r["sessions"] for r in rows)
    tot_c = sum(r["commits"] for r in rows)

    # 项目层：会话里提到的项目名 vs 仓名，能对上的才算
    repo_names = {r["repo"] for r in gh.get("repos", [])}
    repo_commits = {r["repo"]: r["commits"] for r in gh.get("repos", [])}
    proj_sessions = Counter(s.get("project") or "未标注" for s in hum)
    matched, unmatched = [], []
    for p, n in proj_sessions.most_common(40):
        hit = next((r for r in repo_names if r.lower() == p.lower()
                    or p.lower().startswith(r.lower()) or r.lower().startswith(p.lower())), None)
        if hit:
            matched.append({"project": p, "repo": hit, "sessions": n,
                            "commits": repo_commits.get(hit, 0),
                            "per_session": round(repo_commits.get(hit, 0) / max(1, n), 2)})
        elif n >= 3:
            unmatched.append({"project": p, "sessions": n})
    matched.sort(key=lambda r: -r["sessions"])

    return {
        "state": "通",
        "days": rows,
        "projects": matched,
        "unmatched_projects": unmatched[:20],
        "totals": {
            "days_talked": len(talked),
            "days_shipped": len(shipped),
            "days_both": len(both),
            "days_talk_only": len(talk_only),
            "days_ship_only": len(ship_only),
            "sessions": tot_s,
            "commits": tot_c,
            "commits_per_session": round(tot_c / max(1, tot_s), 3),
            "overlap_rate": round(len(both) / max(1, len(talked)), 4),
        },
        "note": "「只聊没交付」＝那天有会话但没有一条属于你的提交。"
                "不代表白干（可能在读、在想、在做仓外的事），但它是那条比例最直观的证据。"
                "项目名与仓名对不上的单独列出，不硬凑。",
    }
