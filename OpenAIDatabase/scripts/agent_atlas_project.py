#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""agent_atlas_project.py —— 把会话事件投影进 MemoryAtlas 的可视化数据

MemoryAtlas 前端读 data/derived/visualization/memory_atlas.json，
契约是 nodes / edges / timeline / metrics / data_sources。
本脚本把每日沉淀出来的会话事件按同一契约**增补**进去 ——
增补不是覆盖：原有 156 个节点 / 720 条边一个不动，只加 agent 会话这一层。

为什么要投影而不是让 Owner 去读 markdown：
他要的是「让我清楚地认识到我对 AI 的使用」，而 MemoryAtlas 是他已有的
可视化入口。产出了却不在他会打开的地方，等于没产出 ——
本仓的 AGENT_CONTEXT.md 就是这么废掉的。

隐私：投影只放**聚合与标签**，不放原话。node label 用「来源·主题」，
不用会话 title（那是 Owner 的原话，且本仓是 PUBLIC）。

零 agent 零 token：纯统计与坐标计算，运行期不调模型。

用法:
  python3 agent_atlas_project.py --events <目录> --atlas <memory_atlas.json> [--dry-run]
退出码: 0=成功  1=失败
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

LAYER = "agent_sessions"
PALETTE = {"claude-code": "#c78bff", "codex": "#8fd3ff", "kimi-code": "#ffd08f",
           "chatgpt-archive": "#8fffc4", "codex-archive": "#9fb8ff",
           "dws": "#ff9fb8", "openchatcut": "#c4c4c4"}


def load_events(d: Path) -> list:
    rows = []
    for f in sorted(d.glob("*.events.jsonl")):
        for line in f.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except ValueError:
                    continue
    return rows


def project(events: list) -> dict:
    """产出增补块。坐标用确定性布局 —— 同样输入必须给同样位置，
    否则每天重生成都会让图乱跳，Owner 会以为数据变了。"""
    by_source = Counter(e["source_id"] for e in events)
    by_topic = Counter(t for e in events for t in e.get("topics", []))
    src_topic = defaultdict(Counter)
    for e in events:
        for t in e.get("topics", []):
            src_topic[e["source_id"]][t] += 1

    nodes, edges = [], []
    # 来源节点：环形排布，半径按会话量
    srcs = sorted(by_source)
    for i, s in enumerate(srcs):
        ang = 2 * math.pi * i / max(len(srcs), 1)
        nodes.append({
            # kind 必须用前端认识的类型，否则节点在 JSON 里但图上看不见 ——
            # 2026-08-20 实测：用自造的 agent_source 时，UI 的计数仍是 156，
            # 我的 16 个节点一个都没渲染出来。「在数据里」不等于「看得到」。
            "id": f"agentsrc:{s}", "kind": "theme", "theme_id": f"agent-{s}",
            "label": f"AI 工具·{s}（{by_source[s]} 会话）",
            "layer": LAYER,
            "visual": {"brightness": 0.9, "color": PALETTE.get(s, "#bbbbbb"),
                       "position": {"x": round(50 + 34 * math.cos(ang), 4),
                                    "y": round(50 + 34 * math.sin(ang), 4), "z": 0},
                       "size": round(1 + math.log10(by_source[s] + 1), 3)},
            "metrics": {"sessions": by_source[s]},
        })
    # 主题节点：内环
    tps = [t for t, _ in by_topic.most_common()]
    for i, t in enumerate(tps):
        ang = 2 * math.pi * i / max(len(tps), 1)
        nodes.append({
            "id": f"agenttopic:{t}", "kind": "theme", "theme_id": f"agent-topic-{t}",
            "label": f"我在做·{t}（{by_topic[t]} 会话）",
            "layer": LAYER,
            "visual": {"brightness": 0.75, "color": "#ffffff",
                       "position": {"x": round(50 + 16 * math.cos(ang), 4),
                                    "y": round(50 + 16 * math.sin(ang), 4), "z": 0},
                       "size": round(0.6 + math.log10(by_topic[t] + 1) * 0.6, 3)},
            "metrics": {"sessions": by_topic[t]},
        })
    # 边：来源 -> 主题，权重是共现次数
    for s, tc in src_topic.items():
        for t, c in tc.items():
            edges.append({"id": f"edge:agent:{s}:{t}", "kind": "agent_uses_topic",
                          "source": f"agentsrc:{s}", "target": f"agenttopic:{t}",
                          "layer": LAYER, "weight": c})

    # 时间线：按天聚合，不放原话
    byday = Counter(str(e.get("occurred_at", ""))[:10] for e in events)
    byday.pop("", None)
    timeline = [{"category": "agent_activity", "date": d,
                 "importance": "高" if n >= 100 else ("中" if n >= 20 else "低"),
                 "label": f"{n} 个会话", "memory_id": "", "memory_tier": "一般",
                 "layer": LAYER}
                for d, n in sorted(byday.items())]

    days = sorted(byday)
    return {
        "nodes": nodes, "edges": edges, "timeline": timeline,
        "data_source": {
            "id": LAYER, "label": "本机 Agent 会话", "platform": "local_agents",
            "status": "active", "ingestion_status": "active_real_local_redacted_summary",
            "description": "本机各 agent 会话的脱敏派生摘要（只含聚合，不含原话）。",
            "node_count": len(nodes), "activity_count": len(events),
            "latest_date": days[-1] if days else "", "record_types": ["agent_session_summary"],
        },
        "metric": {"id": "agent_sessions_total", "label": "Agent 会话总数",
                   "value": len(events), "unit": "个"},
    }


def merge(atlas: dict, block: dict) -> dict:
    """增补：先摘掉上一轮本层的产物再放新的，保证幂等且不误伤原有数据。"""
    atlas["nodes"] = [n for n in atlas.get("nodes", []) if n.get("layer") != LAYER] + block["nodes"]
    atlas["edges"] = [e for e in atlas.get("edges", []) if e.get("layer") != LAYER] + block["edges"]
    atlas["timeline"] = [t for t in atlas.get("timeline", []) if t.get("layer") != LAYER] + block["timeline"]
    atlas["data_sources"] = [d for d in atlas.get("data_sources", [])
                             if d.get("id") != LAYER] + [block["data_source"]]
    atlas["metrics"] = [m for m in atlas.get("metrics", [])
                        if m.get("id") != block["metric"]["id"]] + [block["metric"]]
    # overview 是**预计算**的计数，UI 直接读它 —— 只加 nodes 不更新这里，
    # 界面上的数字纹丝不动，看起来像「没生效」。
    # 2026-08-20 实测踩过：节点确实进了 JSON，UI 仍显示旧的 156/720。
    ov = atlas.setdefault("overview", {})
    ov["node_count"] = len(atlas["nodes"])
    ov["edge_count"] = len(atlas["edges"])
    ov["theme_node_count"] = sum(1 for n in atlas["nodes"] if n.get("kind") == "theme")
    ov["conversation_count"] = ov.get("conversation_count", 0)
    ov["agent_session_count"] = block["metric"]["value"]

    layers = atlas.setdefault("visual_layers", [])
    if isinstance(layers, list) and LAYER not in [
            (l.get("id") if isinstance(l, dict) else l) for l in layers]:
        layers.append({"id": LAYER, "label": "本机 Agent 会话", "default_visible": True})
    return atlas


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--events", required=True)
    ap.add_argument("--atlas", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    events = load_events(Path(args.events))
    if not events:
        print("FAIL: 无事件")
        return 1
    ap_path = Path(args.atlas)
    if not ap_path.is_file():
        print(f"FAIL: 找不到 {ap_path}")
        return 1
    atlas = json.loads(ap_path.read_text(encoding="utf-8"))
    before = (len(atlas.get("nodes", [])), len(atlas.get("edges", [])))
    block = project(events)
    atlas = merge(atlas, block)
    after = (len(atlas["nodes"]), len(atlas["edges"]))
    if not args.dry_run:
        ap_path.write_text(json.dumps(atlas, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps({"state": "PASS", "events": len(events),
                      "nodes": f"{before[0]} -> {after[0]}",
                      "edges": f"{before[1]} -> {after[1]}",
                      "timeline_days": len(block["timeline"]),
                      "dry_run": args.dry_run}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
