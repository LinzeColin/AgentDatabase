#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build.py —— 把会话记录聚合成页面直接读的 atlas.json。

纯标准库，不调用任何模型。所有结论都是**从数据算出来的**，不是生成的：
算不出来就写「不确定」，不写「没问题」。

产出:
  <web>/data/atlas.json           总表：天/周/主题/项目/切片/洞察
  <web>/data/day/YYYY-MM-DD.json  某一天的明细（日记用，按需加载）

用法: python3 build.py --sessions <extract 的 out 目录> --out <web 目录>
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract import TOPICS, SKIPPED  # noqa: E402  词表是唯一真源，不在这里复制一份

SLICES = [3, 7, 15, 30, 45, 60, 90, 180]

# 一场会话最多按几小时计入「活跃小时」。跨夜挂着的会话 start→end 能有 100 小时，
# 全算进去等于凭空造出没发生过的工作量。超过这个数就只认起止两端，中间不认。
ACTIVE_CAP_H = 4

# 主题占比低于这个数就不挂上去，最多挂 3 个。
TOPIC_MIN_SHARE = 0.12
TOPIC_MAX = 3

# 主题上层归并：Owner 的原话是「三个月了，依旧不能用它创造经济价值」。
# 这一层就是为了回答那句话 —— 时间到底落在「造东西」「交出去」还是「换到钱」。
LADDER = {
    "建设": ["修bug", "重构简化", "测试验收", "数据", "自动化", "治理规范", "文档", "前端界面"],
    "交付": ["部署上线", "办公文书", "业务方案"],
    "换钱": ["赚钱", "找工作"],
    "学习": ["学习"],
}
KW_TOPIC = {w: t for t, ws in TOPICS.items() for w in ws}


def utc(s: str):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def load(sessdir: Path) -> list:
    out = []
    for f in sorted(glob.glob(str(sessdir / "*.sessions.jsonl"))):
        for line in open(f, encoding="utf-8"):
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("start"):
                out.append(r)
    out.sort(key=lambda r: r["start"])
    return out


def keyword_weights(sessions: list) -> dict:
    """按语料稀有度给关键词打权重（IDF）。

    「方案」「客户」「数据」这种词几乎每场对话都出现，不降权的话一个主题能吞掉
    六成会话（实测 业务方案 1055/1752）。手工调词表是调不完的 ——
    出现在超过一半会话里的词权重直接归零，让它不再决定任何事。
    """
    human = [s for s in sessions if s.get("kind") == "human"]
    n = max(1, len(human))
    df = Counter()
    for s in human:
        for w in (s.get("kw") or {}):
            df[w] += 1
    w = {}
    for kw, d in df.items():
        share = d / n
        w[kw] = 0.0 if share > 0.5 else math.log(n / (1 + d))
    return w


def assign_topics(sess: dict, weights: dict) -> tuple:
    """返回 (主题列表, 各主题权重)。一次关键词都没命中就是真的未分类。"""
    score = defaultdict(float)
    for kw, cnt in (sess.get("kw") or {}).items():
        t = KW_TOPIC.get(kw)
        if not t:
            continue
        # log(1+次数) 而不是次数本身：一场长会话里「测试」出现 100 次，
        # 不代表它比只提过 3 次「委外单」的那场更是在做测试。
        score[t] += math.log1p(cnt) * weights.get(kw, 0.0)
    score = {k: v for k, v in score.items() if v > 0}
    if not score:
        return [], {}
    total = sum(score.values())
    ranked = sorted(score.items(), key=lambda kv: (-kv[1], kv[0]))
    keep = [k for k, v in ranked if v / total >= TOPIC_MIN_SHARE][:TOPIC_MAX]
    if not keep:
        keep = [ranked[0][0]]
    return keep, {k: round(score[k] / total, 3) for k in keep}


def hour_buckets(s: dict) -> list:
    """这场会话覆盖了哪些「日期+小时」格子。用于活跃小时与日历热力。"""
    a, b = utc(s["start"]), utc(s.get("end") or s["start"])
    if not a:
        return []
    if not b or b < a:
        b = a
    span_h = (b - a).total_seconds() / 3600.0
    if span_h > ACTIVE_CAP_H:
        # 跨度过长 = 中间大概率是挂着的，只认起止两端，不脑补中间
        return sorted({(a.date().isoformat(), a.hour), (b.date().isoformat(), b.hour)})
    out, cur = set(), a.replace(minute=0, second=0, microsecond=0)
    while cur <= b:
        out.add((cur.date().isoformat(), cur.hour))
        cur += timedelta(hours=1)
    return sorted(out)


def iso_week(d: str) -> str:
    y, m, dd = (int(x) for x in d.split("-"))
    iy, iw, _ = datetime(y, m, dd).isocalendar()
    return f"{iy}-W{iw:02d}"


def blank_bucket() -> dict:
    return {"n": 0, "human": 0, "auto": 0, "fanout": 0, "turns": 0, "tools": 0, "errors": 0,
            "tok_in": 0, "tok_out": 0, "tok_cache_r": 0,
            "topics": Counter(), "sources": Counter(), "projects": Counter(), "hours": set()}


def fold(b: dict, s: dict, buckets: list) -> None:
    b["n"] += 1
    b["human" if s["kind"] == "human" else "auto"] += 1
    if s["kind"] == "fanout":
        b["fanout"] += 1
    for k in ("turns", "tools", "errors", "tok_in", "tok_out", "tok_cache_r"):
        b[k] += s.get(k, 0)
    b["sources"][s["source"]] += 1
    if s.get("project"):
        b["projects"][s["project"]] += 1
    if s["kind"] == "human":
        for t in s["topics"]:
            b["topics"][t] += 1
    b["hours"].update(h for _, h in buckets)


def finish(b: dict) -> dict:
    o = {k: v for k, v in b.items() if k not in ("topics", "sources", "projects", "hours")}
    o["topics"] = dict(b["topics"])
    o["sources"] = dict(b["sources"])
    o["projects"] = dict(b["projects"].most_common(8))
    o["active_hours"] = len(b["hours"])
    o["hours"] = sorted(b["hours"])
    return o


# 同一来源、同一小时内启动多少场就算扇出。人手动开不出这个密度 ——
# 实测 2026-08-17 有 518 场在同一个小时里起，是一个给工业照片打标的 agent 扇出。
# 不标出来，那一天会显示成「你亲自开口 752 场」。
FANOUT_PER_HOUR = 15


def mark_fanout(sessions: list) -> int:
    buckets = defaultdict(list)
    for s in sessions:
        buckets[(s["source"], s["start"][:13])].append(s)
    n = 0
    for (src, hour), rows in buckets.items():
        if len(rows) < FANOUT_PER_HOUR:
            continue
        for r in rows:
            r["kind"] = "fanout"
            r["fanout"] = f"{hour.replace('T', ' ')}:00 起 {len(rows)} 场"
            n += 1
    return n


def build(sessions: list, out: Path) -> dict:
    fanout_n = mark_fanout(sessions)
    weights = keyword_weights(sessions)
    for s in sessions:
        s["topics"], s["topic_share"] = assign_topics(s, weights)
        s["day"] = s["start"][:10]
        s["buckets"] = hour_buckets(s)
        a, b = utc(s["start"]), utc(s.get("end") or s["start"])
        s["span_min"] = int(max(0, (b - a).total_seconds() / 60)) if a and b else 0

    days, weeks = defaultdict(blank_bucket), defaultdict(blank_bucket)
    projects = defaultdict(lambda: {"n": 0, "human": 0, "turns": 0, "tok_in": 0, "tok_out": 0,
                                    "first": "", "last": "", "topics": Counter(), "hours": set(),
                                    "sources": Counter()})
    for s in sessions:
        fold(days[s["day"]], s, s["buckets"])
        fold(weeks[iso_week(s["day"])], s, s["buckets"])
        p = projects[s.get("project") or "未标注"]
        p["n"] += 1
        p["human"] += 1 if s["kind"] == "human" else 0
        p["turns"] += s.get("turns", 0)
        p["tok_in"] += s.get("tok_in", 0)
        p["tok_out"] += s.get("tok_out", 0)
        p["sources"][s["source"]] += 1
        p["first"] = min(p["first"] or s["day"], s["day"])
        p["last"] = max(p["last"], s["day"])
        p["hours"].update(s["buckets"])
        if s["kind"] == "human":
            for t in s["topics"]:
                p["topics"][t] += 1

    day_rows = [dict(finish(v), d=k) for k, v in sorted(days.items())]
    week_rows = [dict(finish(v), w=k) for k, v in sorted(weeks.items())]
    proj_rows = []
    for name, p in projects.items():
        proj_rows.append({
            "name": name, "n": p["n"], "human": p["human"], "turns": p["turns"],
            "tok_in": p["tok_in"], "tok_out": p["tok_out"],
            "first": p["first"], "last": p["last"],
            "active_hours": len(p["hours"]),
            "topics": dict(p["topics"].most_common(5)),
            "sources": dict(p["sources"]),
            "shipped": bool(p["topics"].get("部署上线")),
        })
    proj_rows.sort(key=lambda r: -r["active_hours"])

    compact = [{
        "id": s["id"], "s": s["source"], "t": s["start"], "e": s.get("end") or s["start"],
        "d": s["day"], "p": s.get("project") or "", "k": s["kind"], "b": s.get("batch") or "",
        "u": s.get("turns", 0), "m": s.get("msgs", 0), "o": s.get("tools", 0),
        "ti": s.get("tok_in", 0), "to": s.get("tok_out", 0), "tc": s.get("tok_cache_r", 0),
        "tp": s["topics"], "h": s["span_min"], "n": (s.get("title") or "")[:90],
    } for s in sessions]

    atlas = {
        "meta": meta_block(sessions, day_rows, fanout_n),
        "topic_names": list(TOPICS),
        "ladder": LADDER,
        "days": day_rows,
        "weeks": week_rows,
        "projects": proj_rows,
        "sessions": compact,
        "slices": slices_block(sessions, day_rows),
        "trend": trend_block(week_rows),
        "insights": insights_block(sessions, day_rows, week_rows, proj_rows),
        "keyword_weights": {k: round(v, 3) for k, v in sorted(weights.items(), key=lambda kv: -kv[1])[:60]},
    }

    dd = out / "day"
    dd.mkdir(parents=True, exist_ok=True)
    for old in dd.glob("*.json"):
        old.unlink()
    by_day = defaultdict(list)
    for s in sessions:
        by_day[s["day"]].append(s)
    for day, rows in by_day.items():
        rows.sort(key=lambda r: r["start"])
        (dd / f"{day}.json").write_text(json.dumps({
            "day": day,
            "sessions": [{
                "id": r["id"], "source": r["source"], "start": r["start"], "end": r.get("end", ""),
                "project": r.get("project", ""), "kind": r["kind"], "batch": r.get("batch", ""),
                "title": r.get("title", ""), "topics": r["topics"], "turns": r.get("turns", 0),
                "tools": r.get("tools", 0), "tok_in": r.get("tok_in", 0), "tok_out": r.get("tok_out", 0),
                "models": r.get("models", []), "span_min": r["span_min"],
                "prompts": r.get("prompts", []),
            } for r in rows],
        }, ensure_ascii=False), encoding="utf-8")
    return atlas


def meta_block(sessions: list, days: list, fanout_n: int = 0) -> dict:
    human = [s for s in sessions if s["kind"] == "human"]
    auto = [s for s in sessions if s["kind"] != "human"]
    batches = Counter(s["batch"] for s in auto if s.get("batch"))
    src = Counter(s["source"] for s in sessions)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "sessions_total": len(sessions),
        "sessions_human": len(human),
        "sessions_auto": len(auto),
        "sessions_fanout": fanout_n,
        "fanout_hours": [{"when": k, "n": v} for k, v in
                         Counter(s.get("fanout", "") for s in sessions if s.get("fanout")).most_common(8)],
        "unclassified": sum(1 for s in human if not s["topics"]),
        "days_active": len(days),
        "first_day": days[0]["d"] if days else "",
        "last_day": days[-1]["d"] if days else "",
        "sources": dict(src),
        # 被判成机器刷的那部分必须单独列出来。合同 §2.3：被丢掉的东西不参与
        # 任何总量校验，所以总量永远对 —— 这里把它摆在最前面，不藏进分母里。
        "auto_batches": [{"prompt": k, "n": v} for k, v in batches.most_common(10)],
        "skipped_sources": SKIPPED,
        "method": {
            "topics": "关键词命中 × 语料稀有度(IDF)，出现在半数以上会话的词权重归零",
            "active_hours": f"有动静的整点格子数（去重）。**不等于工作时长** —— 同一小时内开十场会话也只算一格；跨度超过 {ACTIVE_CAP_H} 小时的会话只认起止两端，中间不脑补。",
            "kind": f"auto = 无用户发言 / 单轮机器指令 / 同一段提示词重复 5 次以上；"
                    f"fanout = 同一来源同一小时内起了 {FANOUT_PER_HOUR} 场以上（agent 扇出，不是你在对话）",
            "model_calls": "0（全部为确定性统计，运行期不调用任何模型）",
        },
    }


def slices_block(sessions: list, days: list) -> dict:
    if not days:
        return {}
    last = datetime.fromisoformat(days[-1]["d"])
    out = {}
    for n in SLICES + [0]:
        cut = (last - timedelta(days=n - 1)).date().isoformat() if n else "0000-00-00"
        sel = [s for s in sessions if s["day"] >= cut]
        hum = [s for s in sel if s["kind"] == "human"]
        tp = Counter()
        for s in hum:
            for t in s["topics"]:
                tp[t] += 1
        ld = Counter()
        for s in hum:
            for t in s["topics"]:
                for lname, ts in LADDER.items():
                    if t in ts:
                        ld[lname] += 1
        pr = Counter(s.get("project") or "未标注" for s in hum)
        hrs = set()
        for s in sel:
            hrs.update(s["buckets"])
        out[str(n)] = {
            "label": f"最近 {n} 天" if n else "全历史",
            "days": n,
            "from": cut if n else (days[0]["d"] if days else ""),
            "sessions": len(sel), "human": len(hum), "auto": len(sel) - len(hum),
            "days_active": len({s["day"] for s in sel}),
            "active_hours": len(hrs),
            "turns": sum(s.get("turns", 0) for s in sel),
            "tok_in": sum(s.get("tok_in", 0) for s in sel),
            "tok_out": sum(s.get("tok_out", 0) for s in sel),
            "topics": dict(tp.most_common()),
            "ladder": dict(ld),
            "projects": dict(pr.most_common(10)),
            "unclassified": sum(1 for s in hum if not s["topics"]),
        }
    return out


def trend_block(weeks: list) -> dict:
    """每周主题占比。给「像 economic index 那样」的堆叠面积图用。"""
    rows = []
    for w in weeks:
        tot = sum(w["topics"].values())
        rows.append({"w": w["w"], "n": w["n"], "human": w["human"], "active_hours": w["active_hours"],
                     "share": {k: round(v / tot, 4) for k, v in w["topics"].items()} if tot else {},
                     "count": w["topics"]})
    return {"weeks": rows}


def insights_block(sessions, days, weeks, projects) -> list:
    """全部由上面的数据直接算出。任何算不出来的都写「不确定」，不写「没问题」。"""
    out = []
    hum = [s for s in sessions if s["kind"] == "human"]

    ld = Counter()
    for s in hum:
        for t in s["topics"]:
            for lname, ts in LADDER.items():
                if t in ts:
                    ld[lname] += 1
    build_n, ship_n, money_n = ld.get("建设", 0), ld.get("交付", 0), ld.get("换钱", 0)
    if money_n:
        out.append({"k": "投入产出比", "v": f"{build_n // max(1, money_n)} : {ship_n // max(1, money_n)} : 1",
                    "d": f"建设 {build_n} 次 ／ 交付 {ship_n} 次 ／ 谈到钱 {money_n} 次。"
                         f"每谈一次钱，先做了 {build_n // max(1, money_n)} 次建设。",
                    "t": "warn" if build_n > money_n * 10 else "ok"})
    else:
        out.append({"k": "投入产出比", "v": "不确定",
                    "d": f"{len(hum)} 场真人会话里，一次都没有命中「赚钱」类关键词。"
                         f"不是比例难看，是这一栏没有数据。", "t": "warn"})

    if days:
        busiest = max(days, key=lambda d: d["active_hours"])
        out.append({"k": "最忙的一天", "v": busiest["d"],
                    "d": f"这一天有 {busiest['n']} 场会话（你亲自开口 {busiest['human']} 场），"
                         f"分布在 {busiest['active_hours']} 个不同的整点里。"
                         f"这是「有动静的钟点数」，不是你连续干了这么久。", "t": "ok"})
        streak = best = 0
        prev = None
        for d in days:
            cur = datetime.fromisoformat(d["d"]).date()
            streak = streak + 1 if prev and (cur - prev).days == 1 else 1
            best = max(best, streak)
            prev = cur
        out.append({"k": "最长连续天数", "v": f"{best} 天",
                    "d": f"有记录的 {len(days)} 天里，最长一次连着做了 {best} 天。", "t": "ok"})

    sunk = [p for p in projects if p["active_hours"] >= 4 and not p["shipped"]]
    sunk.sort(key=lambda p: -p["active_hours"])
    if sunk:
        top = sunk[:5]
        out.append({"k": "投入了但没上线", "v": f"{len(sunk)} 个项目",
                    "d": "花了时间、但一次都没出现过「部署上线」类话题：" +
                         "、".join(f"{p['name']}（{p['active_hours']}h）" for p in top),
                    "t": "warn"})

    once = [p for p in projects if p["n"] == 1]
    if once:
        out.append({"k": "只碰过一次", "v": f"{len(once)} 个项目",
                    "d": "开了一次就再没回去过。要么是试完就丢，要么是被更急的事挤掉了。", "t": "info"})

    hourc = Counter()
    for s in sessions:
        for _, h in s["buckets"]:
            hourc[h] += 1
    if hourc:
        peak = hourc.most_common(1)[0]
        # 记录是 UTC，Owner 在悉尼（UTC+10/11）。只做固定 +10，不猜夏令时。
        out.append({"k": "最常动手的时段", "v": f"{(peak[0] + 10) % 24:02d}:00 前后",
                    "d": f"这个整点出现过 {peak[1]} 次（按悉尼时间固定 +10 换算，未处理夏令时）。", "t": "info"})

    if len(weeks) >= 3:
        a, b = weeks[-2], weeks[-1]
        delta = b["active_hours"] - a["active_hours"]
        out.append({"k": "本周对比上周", "v": f"{delta:+d} 小时",
                    "d": f"{a['w']} 活跃 {a['active_hours']}h → {b['w']} 活跃 {b['active_hours']}h。"
                         f"（最后一周可能还没过完）", "t": "info"})

    auto_n = sum(1 for s in sessions if s["kind"] == "auto")
    fan_n = sum(1 for s in sessions if s["kind"] == "fanout")
    if auto_n or fan_n:
        out.append({"k": "不是你开口的", "v": f"{auto_n + fan_n} 场 / {len(sessions)} 场",
                    "d": f"批处理／单轮机器指令 {auto_n} 场，agent 密集扇出 {fan_n} 场，"
                         f"合计 {(auto_n + fan_n) * 100 // max(1, len(sessions))}%。"
                         f"上面所有「真人」口径都已经把它们剔掉了 —— 剔掉的数量就摆在这里。", "t": "info"})

    unc = sum(1 for s in hum if not s["topics"])
    if unc:
        out.append({"k": "认不出主题的", "v": f"{unc} 场",
                    "d": f"一个关键词都没命中，如实标成未分类，没有硬塞进任何一类。", "t": "info"})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sessions", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    sess = load(Path(args.sessions))
    if not sess:
        print("没有会话可聚合", file=sys.stderr)
        return 1
    out = Path(args.out)
    (out / "atlas").mkdir(parents=True, exist_ok=True)
    atlas = build(sess, out / "atlas")
    p = out / "atlas" / "atlas.json"
    p.write_text(json.dumps(atlas, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    m = atlas["meta"]
    print(f"会话 {m['sessions_total']}（真人 {m['sessions_human']} / 机器 {m['sessions_auto']}）"
          f"  活跃 {m['days_active']} 天  {m['first_day']} → {m['last_day']}")
    print(f"atlas.json {p.stat().st_size / 1024:.0f}KB   日明细 {len(list((out / 'atlas' / 'day').glob('*.json')))} 个")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
