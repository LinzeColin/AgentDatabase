#!/usr/bin/env python3
"""compound.py —— 成果复利投影：把「做过什么」推进到「变成了什么、被谁用了、离钱多远」。

## 这一层为什么存在

Memory Atlas 到 v0.4.x 已经能回答「时间去哪了」。它答不了的是下一个问题：
**这些时间最后沉淀成了什么？被第二个任务复用了吗？离经济结果还有几步？**

## 两个平面，一条事实链

    A 确定性信号面（每天/归档触发，零模型）
      repeats / pain / expensive-no-outcome / GitHub 交付信号
                    ↓
    B 语义事件面（ChatGPT 定时任务 或 任务结束时的 agent closeout）
      memory_atlas.compounding_event.v1
                    ↓
    C 复利投影（本文件）
      CAPTURED → QUALIFIED → EXPERIMENT → ADOPTED → OUTCOME → ECONOMIC_IMPACT
                                                    ↘ HOLD / REJECT

**本文件不调用任何模型。** 语义判断由 B 面产出，这里只做形状校验、合并、去重、状态投影。
Atlas 的日常流水线保持零 token、零 agent —— 这是全局红线，不因为这个功能破例。

## 三条不许越过的线

1. **「做完了」不等于「被采用」。** 文件写完、commit、部署成功，都只是 OUTCOME 之前的事。
2. **没有采用证据就不许升到 ADOPTED；没有经济证据就不许升到 ECONOMIC_IMPACT。**
   事件里写了更高的 stage 也要压回来，并把「压过」这件事记下来，可审计。
3. **金额未知就是未知。** 不允许自动填 0 —— 0 是一个断言，未知不是。
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = "memory_atlas.compounding_event.v1"

# 漏斗。HOLD / REJECT 是旁路，不在主链上 —— 允许「这周不晋级」是这套设计的一部分，
# 逼着每周造一个 Skill 才是把它做坏的方式。
STAGES = ["CAPTURED", "QUALIFIED", "EXPERIMENT", "ADOPTED", "OUTCOME", "ECONOMIC_IMPACT"]
SIDE = ["HOLD", "REJECT"]
RANK = {s: i for i, s in enumerate(STAGES)}

# 经济路径。每一条都要能指到可核的证据；没有现金结果的保留领先指标，不伪造金额。
PATHS = {
    "direct_revenue": "直接收入",
    "sales_lead": "销售线索",
    "cost_reduction": "成本下降",
    "failure_avoidance": "少踩一次坑",
    "reusable_asset": "资产被复用",
    "decision_impact": "改变了决策",
    "leading_indicator": "离钱更近的领先指标",
}
VALUE_STATUS = ["UNKNOWN", "ESTIMATED", "OBSERVED", "VERIFIED"]

NOT_MEASURED = [
    {"item": "真实金额", "why": "本机没有账单/发票/收款记录的接入口。有金额的事件会照原样显示，"
                              "没有的一律标未知 —— 自动填 0 等于断言「没赚到」，那是另一回事。"},
    {"item": "跨人采用", "why": "单人工作区，「被第二个人采用」这条路径天然为空。"
                                "这里只能观测「被第二个任务/项目复用」。"},
    {"item": "反事实", "why": "「不做这件事会损失多少」需要对照组。单人单时间线拿不到，"
                              "所以成本下降只报可观测的降幅，不报避免的损失。"},
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _norm(t: str) -> str:
    """候选去重用的归一化键。同一个问题换个说法不该算两条。"""
    t = re.sub(r"\s+", "", (t or "").lower())
    t = re.sub(r"[，。！？、,.!?；;：:（）()\[\]「」【】]", "", t)
    return t[:48]


# ──────────────────────────────────────────────────────────────
# 一、读语义事件
# ──────────────────────────────────────────────────────────────

def read_events(dirs: list[Path]) -> tuple[list, list]:
    """读入所有 compounding event。形状不对的**不丢弃也不假装读到了**，单独列出来。

    返回 (合格事件, 拒收记录)。拒收记录会一路带到页面上 ——
    「读到了几个、拒了几个、为什么拒」比「静默跳过」有用得多。
    """
    ok, rejected = [], []
    for d in dirs:
        if not d.exists():
            continue
        for f in sorted(d.glob("*.json")):
            try:
                ev = json.loads(f.read_text(encoding="utf-8"))
            except Exception as e:                      # noqa: BLE001 坏文件不该拖垮整轮
                rejected.append({"file": f.name, "why": f"不是合法 JSON：{type(e).__name__}"})
                continue
            if ev.get("schema_version") != SCHEMA:
                rejected.append({"file": f.name,
                                 "why": f"schema 是「{ev.get('schema_version')}」，不是 {SCHEMA}"})
                continue
            if not ev.get("event_id"):
                rejected.append({"file": f.name, "why": "没有 event_id，无法去重"})
                continue
            ev["_file"] = f.name
            ok.append(ev)
    # 同一个 event_id 只留最新的一份
    by_id = {}
    for ev in sorted(ok, key=lambda e: e.get("generated_at") or ""):
        by_id[ev["event_id"]] = ev
    return list(by_id.values()), rejected


# ──────────────────────────────────────────────────────────────
# 二、确定性信号 → 沉淀债务
#    这一段完全不依赖语义事件。没有任何 event 的时候，它自己就成立。
# ──────────────────────────────────────────────────────────────

def derive_debt(lessons: dict, projects: list, delivery: dict, tokens: dict) -> list:
    """沉淀债务：做了很多但还没变成结果的地方。

    这比「又找到一个新 Skill」重要 —— 新 Skill 是增量，债务是漏水的地方。
    每一条都必须能指回具体证据，不能是感想。
    """
    debt = []

    # ① 问了很多次但还没固化：同一个问题被反复问，说明上一次的答案没留下来
    for r in (lessons.get("repeats") or [])[:8]:
        if r.get("n", 0) < 3:
            continue
        debt.append({
            "kind": "repeat_no_asset",
            "kind_label": "问了很多次，还没固化",
            "title": (r.get("text") or "")[:60],
            "size": r["n"],
            "size_label": f"{r['n']} 遍",
            "why": f"横跨 {r.get('days', 0)} 天还在问同一件事。答案没有留在任何一个 agent 找得到的地方。",
            "evidence": [f"{r.get('first', '?')} → {r.get('last', '?')}",
                         "、".join((r.get("projects") or [])[:3]) or "未标项目"],
            "next": "把结论写进对应仓的 AGENTS.md，下一轮蒸馏会带进简报。",
        })

    # ② 烧得很贵但没有可观测产出：token 花了，git 上什么都没留下
    dl_days = {d["d"]: d for d in (delivery.get("days") or [])}
    heavy = []
    for row in (tokens.get("by_day") or []):
        d = dl_days.get(row.get("d"))
        if not d or d.get("commits", 0) > 0:
            continue
        heavy.append((row.get("input_total", 0), row.get("d"), d.get("sessions", 0)))
    heavy.sort(reverse=True)
    for tot, day, sess in heavy[:5]:
        if tot <= 0:
            continue
        debt.append({
            "kind": "expensive_no_outcome",
            "kind_label": "烧得很贵，没有可观测产出",
            "title": f"{day} 读进 {tot:,} token，当天 0 提交",
            "size": tot,
            "size_label": f"{sess} 场",
            "why": "这不等于白干 —— 那天可能在读、在想、在做不进 git 的事。"
                   "但它是「有投入没留痕」最直接的候选，值得回头看一眼当天到底做了什么。",
            "evidence": [f"当天 {sess} 场会话", "GitHub 当天 0 提交"],
            "next": "打开那一天的记录，判断：是真的没产出，还是产出没进 git。",
        })

    # ③ 报错最密的项目还没有防复发资产
    for p in (lessons.get("pain") or [])[:4]:
        if p.get("per", 0) < 1.0:
            continue
        debt.append({
            "kind": "failed_recurred_no_guard",
            "kind_label": "反复出错，还没有守卫",
            "title": f"{p.get('name')} 每场平均 {p.get('per', 0):.1f} 次报错",
            "size": round(p.get("per", 0) * 10),
            "size_label": f"{p.get('sessions', 0)} 场",
            "why": "不是这个项目 bug 多，是它最消耗你。反复出现的同一类失败没有沉下来变成守卫，"
                   "下一个 agent 会原样再踩一遍。",
            "evidence": [f"{p.get('sessions', 0)} 场会话"],
            "next": "挑一条复发次数最高的，写成回归测试或 pre-commit 守卫。",
        })

    # ④ 谈过上线但没有第二次复用：资产造出来了，没人第二次用
    for p in projects:
        if not p.get("shipped"):
            continue
        if p.get("human", 0) >= 3 and p.get("active_hours", 0) <= 6:
            debt.append({
                "kind": "deployed_no_adoption",
                "kind_label": "上过线，没有第二次复用",
                "title": p.get("name", ""),
                "size": p.get("human", 0),
                "size_label": f"{p.get('human')} 场",
                "why": "谈过部署上线，但此后几乎没再被碰过。造出来的东西没有第二个任务用它，"
                       "就还停在 EXPERIMENT，不是 ADOPTED。",
                "evidence": [f"{p.get('first', '')} → {p.get('last', '')}",
                             f"活跃 {p.get('active_hours', 0)} 个钟点"],
                "next": "要么找一个能复用它的任务，要么明确 REJECT 掉，别挂着。",
            })
    # 每类最多留两条，避免同一类刷屏
    seen = Counter()
    out = []
    for d in sorted(debt, key=lambda x: -x["size"]):
        if seen[d["kind"]] >= 2:
            continue
        seen[d["kind"]] += 1
        out.append(d)
    return out


# ──────────────────────────────────────────────────────────────
# 三、状态投影：只降不升
# ──────────────────────────────────────────────────────────────

def _evidence_ceiling(cand: dict, paths: list) -> tuple[str, str]:
    """这条候选靠现有证据最高能到哪一档。返回 (上限, 理由)。

    事件里写 ECONOMIC_IMPACT 不代表就是 ECONOMIC_IMPACT ——
    「不为了漂亮指标制造 adoption/economic impact」这条纪律必须由代码执行，不能靠自觉。
    """
    has_econ = any(p.get("value_status") in ("OBSERVED", "VERIFIED") for p in paths)
    if has_econ:
        return "ECONOMIC_IMPACT", ""
    has_outcome = bool(cand.get("outcome_evidence")) or any(
        p.get("value_status") == "ESTIMATED" for p in paths)
    if has_outcome:
        return "OUTCOME", "没有 OBSERVED/VERIFIED 的经济证据"
    if cand.get("adoption_evidence"):
        return "ADOPTED", "没有可观测结果证据"
    if len(cand.get("evidence") or []) >= 2:
        return "EXPERIMENT", "没有第二个任务真实使用它的证据"
    if cand.get("evidence"):
        return "QUALIFIED", "证据只有一条，还不足以开实验"
    return "CAPTURED", "还没有任何证据"


def project_candidates(events: list) -> tuple[list, list]:
    """把所有事件里的候选合并成一张表，并按证据把 stage 压到上限之内。"""
    merged: dict[str, dict] = {}
    econ_by_cand: dict[str, list] = defaultdict(list)

    for ev in events:
        for p in (ev.get("economic_paths") or []):
            cid = p.get("candidate_id") or ""
            econ_by_cand[cid].append(p)

    for ev in events:
        src = (ev.get("producer") or {}).get("kind") or "unknown"
        when = ev.get("generated_at") or ""
        for c in (ev.get("candidates") or []):
            key = c.get("candidate_id") or _norm(c.get("problem", ""))
            if not key:
                continue
            cur = merged.get(key)
            if cur is None:
                cur = dict(c)
                cur["candidate_id"] = key
                cur["_seen"] = []
                merged[key] = cur
            else:
                # 同一条候选在多个事件里出现：证据取并集，其余字段以最新为准
                cur["evidence"] = list(dict.fromkeys(
                    (cur.get("evidence") or []) + (c.get("evidence") or [])))
                for k, v in c.items():
                    if k != "evidence" and v:
                        cur[k] = v
            cur["_seen"].append({"at": when, "by": src, "stage": c.get("stage") or "CAPTURED"})

    rows, clamps = [], []
    for key, c in merged.items():
        paths = econ_by_cand.get(key, [])
        claimed = (c.get("stage") or "CAPTURED").upper()
        if claimed in SIDE:
            stage = claimed
        else:
            ceiling, why = _evidence_ceiling(c, paths)
            if RANK.get(claimed, 0) > RANK.get(ceiling, 0):
                clamps.append({"candidate": (c.get("problem") or key)[:50],
                               "claimed": claimed, "allowed": ceiling, "why": why})
                stage = ceiling
            else:
                stage = claimed
        moves = sorted(c.get("_seen") or [], key=lambda x: x["at"])
        rows.append({
            "id": key,
            "type": c.get("type") or "other",
            "problem": c.get("problem") or "",
            "stage": stage,
            "claimed_stage": claimed,
            "evidence": c.get("evidence") or [],
            "recurrence": c.get("recurrence") or "",
            "cost_of_not_fixing": c.get("cost_of_not_fixing") or "",
            "reuse_scope": c.get("reuse_scope") or "",
            "maintenance_cost": c.get("maintenance_cost") or "",
            "paths": paths,
            "first_seen": moves[0]["at"] if moves else "",
            "last_seen": moves[-1]["at"] if moves else "",
            "moves": moves,
        })
    rows.sort(key=lambda r: (-RANK.get(r["stage"], -1), r["problem"]))
    return rows, clamps


def pick_champion(events: list, cands: list) -> dict | None:
    """本周最值得转化的一件事。默认只有一个 —— 允许 NO_PROMOTION。"""
    promos = []
    for ev in events:
        for p in (ev.get("promotions") or []):
            promos.append((ev.get("generated_at") or "", p))
    promos.sort(key=lambda x: x[0], reverse=True)
    primary = next((p for _, p in promos if (p.get("role") or "").upper() == "PRIMARY"), None)
    if not primary:
        return None
    cid = primary.get("candidate_id") or ""
    c = next((x for x in cands if x["id"] == cid), None)
    return {
        "candidate_id": cid,
        "problem": (c or {}).get("problem") or primary.get("why_now") or "",
        "stage": (c or {}).get("stage") or "CAPTURED",
        "why_now": primary.get("why_now") or "",
        "experiment": primary.get("minimum_experiment") or "",
        "success": primary.get("success_criteria") or [],
        "stop": primary.get("stop_or_rollback") or [],
        "next_7d": primary.get("next_7d_action") or "",
        "target_30d": primary.get("target_30d_outcome") or "",
        "evidence": (c or {}).get("evidence") or [],
    }


def closeout_digest(events: list) -> dict:
    """最近的 closeout 变化。只留新教训、别再犯、未了事项 —— 不放完整聊天。"""
    missions, lessons, unresolved, failures = [], [], [], []
    for ev in sorted(events, key=lambda e: e.get("generated_at") or "", reverse=True):
        for m in (ev.get("missions") or []):
            missions.append({
                "id": m.get("mission_id") or "",
                "project": m.get("project") or "",
                "objective": (m.get("objective") or "")[:120],
                "outcome": (m.get("actual_outcome") or "")[:160],
                "state": m.get("completion_state") or "UNKNOWN",
                "at": ev.get("generated_at") or "",
            })
            for u in (m.get("unresolved_obligations") or []):
                unresolved.append({"project": m.get("project") or "", "what": str(u)[:120]})
        for l in (ev.get("lessons") or []):
            lessons.append({"lesson": (l.get("lesson") or "")[:140],
                            "scope": l.get("scope") or "tentative",
                            "do_not_repeat": (l.get("do_not_repeat") or "")[:140]})
        for f in (ev.get("failure_inputs") or []):
            failures.append({
                "id": f.get("failure_id") or "",
                "project": f.get("project") or "",
                "symptom": (f.get("symptom") or "")[:120],
                "root_cause_state": f.get("root_cause_state") or "UNKNOWN",
                "do_not_repeat": (f.get("do_not_repeat") or "")[:140],
                "guard": f.get("regression_asset_candidate") or "",
            })
    return {
        "missions": missions[:12], "missions_total": len(missions),
        "lessons": lessons[:12], "unresolved": unresolved[:12],
        "failures": failures[:12],
    }


def failure_bridge(fails: list) -> dict:
    """接到既有 failure-compound：只有真关闭且已有可复用守卫的，才算「形成了防复发资产」。
    普通报错不许冒充复利。"""
    proven = [f for f in fails if f.get("root_cause_state") == "PROVEN"]
    guarded = [f for f in proven if f.get("guard")]
    return {
        "total": len(fails),
        "proven": len(proven),
        "guarded": len(guarded),
        "rows": guarded[:8],
        "note": "只有「根因已证实」且「已有可复用守卫」的失败才算形成防复发资产。"
                "剩下的还在 HYPOTHESIS/UNKNOWN，不计入复利。",
    }


def economic_rollup(cands: list) -> dict:
    """价值实现。按路径分开列，金额未知就是未知 —— 不自动填 0。"""
    by_path = defaultdict(lambda: {"n": 0, "status": Counter(), "rows": []})
    money = []
    for c in cands:
        for p in c.get("paths") or []:
            k = p.get("path") or "leading_indicator"
            b = by_path[k]
            b["n"] += 1
            b["status"][p.get("value_status") or "UNKNOWN"] += 1
            b["rows"].append({
                "candidate": c["problem"][:60],
                "status": p.get("value_status") or "UNKNOWN",
                "amount": p.get("amount"),
                "currency": p.get("currency"),
                "evidence": p.get("evidence") or [],
                "leading_indicator": p.get("leading_indicator") or "",
            })
            if p.get("amount") is not None:
                money.append(p)
    return {
        "paths": [{"path": k, "label": PATHS.get(k, k), "n": v["n"],
                   "status": dict(v["status"]), "rows": v["rows"][:5]}
                  for k, v in sorted(by_path.items(), key=lambda kv: -kv[1]["n"])],
        "money_rows": len(money),
        "money_state": "通" if money else "没做",
        "note": "金额未知就显示未知。自动填 0 是一个断言（「没赚到」），"
                "而现在的真实状态是「没有可核的金额数据入口」—— 两件事不能混。",
    }


# ──────────────────────────────────────────────────────────────
# 四、装配
# ──────────────────────────────────────────────────────────────

def build(event_dirs: list[Path], lessons: dict, projects: list,
          delivery: dict, tokens: dict) -> dict:
    events, rejected = read_events(event_dirs)
    cands, clamps = project_candidates(events)
    champ = pick_champion(events, cands)
    digest = closeout_digest(events)
    debt = derive_debt(lessons or {}, projects or [], delivery or {}, tokens or {})

    funnel = Counter(c["stage"] for c in cands)
    moves = []
    for c in cands:
        seq = c.get("moves") or []
        for i in range(1, len(seq)):
            if seq[i]["stage"] != seq[i - 1]["stage"]:
                moves.append({"candidate": c["problem"][:50], "at": seq[i]["at"],
                              "from": seq[i - 1]["stage"], "to": seq[i]["stage"]})
    moves.sort(key=lambda m: m["at"], reverse=True)

    # 状态语只有四个词。没有语义事件时是「没做」，不是「通」也不是 0。
    if events:
        state = "通"
        why = ""
    elif debt:
        state = "说不准"
        why = ("还没有收到任何语义事件（closeout / 成果复利转化器）。"
               "下面这些是从本机记录确定性派生出来的债务信号 —— "
               "它们能告诉你哪里在漏，但给不出根因和验收结论。")
    else:
        state = "没做"
        why = "既没有语义事件，也没有派生出债务信号。"

    return {
        "state": state,
        "why": why,
        "generated_at": _now(),
        "schema": SCHEMA,
        "sources": {
            "events": len(events),
            "event_ids": [e.get("event_id") for e in events][:20],
            "rejected": rejected,
            "producers": dict(Counter((e.get("producer") or {}).get("kind") or "unknown"
                                      for e in events)),
        },
        "funnel": {s: funnel.get(s, 0) for s in STAGES},
        "funnel_side": {s: funnel.get(s, 0) for s in SIDE},
        "funnel_moves": moves[:12],
        "champion": champ,
        "champion_note": ("默认只推一个。允许 NO_PROMOTION —— "
                          "逼着每周造一个新 Skill 是把这套东西做坏的方式。"),
        "candidates": cands[:40],
        "clamps": clamps,
        "clamp_note": ("事件里声称的 stage 高于证据能支撑的上限时，这里会把它压回来并记一笔。"
                       "「做完了」不等于「被采用」，「部署成功」不等于「有经济影响」。"),
        "debt": debt,
        "debt_note": ("这是比「又找到一个新 Skill」更重要的队列：新 Skill 是增量，"
                      "债务是漏水的地方。每条都指得回具体证据。"),
        "economic": economic_rollup(cands),
        "closeout": digest,
        "failure_bridge": failure_bridge(digest["failures"]),
        "not_measured": NOT_MEASURED,
        "stages": STAGES,
        "stage_labels": {
            "CAPTURED": "发现候选", "QUALIFIED": "证据够了", "EXPERIMENT": "正在试",
            "ADOPTED": "被第二个任务用了", "OUTCOME": "对结果有可观测影响",
            "ECONOMIC_IMPACT": "有经济结果", "HOLD": "暂停", "REJECT": "淘汰",
        },
        "note": ("语义判断来自 ChatGPT 定时任务与 agent 归档产出的事件；"
                 "本层只做形状校验、合并、去重与状态投影，运行期不调用任何模型。"),
    }
