#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""memory_atlas_daily.py —— 每日沉淀总驱动（codex auto 只需跑这一条）

设计约束（Owner 2026-08-19 明确）：
    「整个流程全部都是无人工值守，唯一依赖 agent 只有 codex auto 每日增量上传，
      不论是软件运行使用还是分析提取全部都是软件自己的能力，0 agent 依赖
      0 token 消耗。这是一个每日沉淀的 memory atlas，不是一次性的任务。」

所以：
- 全程纯 Python，**运行期不调任何模型**，无 token 消耗
- 增量：只重算 mtime/size 变化的会话文件，不重扫 4.3GB
- fail-open 逐步骤：某一步挂了不拖垮其余步骤，但最终退出码如实反映
- 幂等：同一天重复跑结果一致，不产生重复事件（按 record_id 覆盖）

流水线：
    1 抽取   各来源会话 -> canonical 事件（增量）
    2 分析   9 档时间切片 + 主题趋势 + 收入阶梯
    3 视图   日记 / 日历 / 时间线
    4 沉淀   给 agent 的教训（带预算上限与出处）

用法:
  python3 memory_atlas_daily.py --repo-root <仓根> [--full]
退出码: 0=全部成功  1=有步骤失败（详见 JSON receipt）
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS = Path("OpenAIDatabase/scripts")
EVENTS = Path("OpenAIDatabase/data/derived/agent_sessions")
VIEWS = Path("OpenAIDatabase/人类可读/memory-atlas")
LESSONS = Path("OpenAIDatabase/data/derived/agent_context/LESSONS.md")
# 公开面：只放脱敏聚合，不含任何原话与路径。
# 本仓是 PUBLIC，而事件的 title 就是 Owner 当时说的原话 —— 合同禁止入库。
PUBLIC = Path("OpenAIDatabase/data/derived/agent_context/PUBLIC_SUMMARY.md")
# MemoryAtlas 前端读的可视化数据 —— 产出了却不在 Owner 会打开的地方，等于没产出。
ATLAS = Path("OpenAIDatabase/data/derived/visualization/memory_atlas.json")
ANALYSIS = Path("OpenAIDatabase/人类可读/memory-atlas/我在用AI做什么.md")


def run(root: Path, args: list, label: str) -> dict:
    t0 = time.time()
    try:
        r = subprocess.run([sys.executable, "-B", *args], cwd=root,
                           capture_output=True, text=True, timeout=3600)
        ok = r.returncode == 0
        tail = (r.stdout or r.stderr).strip().splitlines()[-1:] or [""]
        return {"step": label, "state": "PASS" if ok else "FAIL",
                "seconds": round(time.time() - t0, 1), "detail": tail[0][:200]}
    except (OSError, subprocess.SubprocessError) as exc:
        return {"step": label, "state": "FAIL",
                "seconds": round(time.time() - t0, 1), "detail": f"{type(exc).__name__}: {exc}"[:200]}


def write_weekly(events_dir: Path, out_dir: Path) -> dict:
    """按 ISO 周切片。Owner 2026-08-19 明确：打包切片最大为每周，不许按月/季。
    粒度越粗，出事时能回到的最近一个完好点就越远。"""
    from collections import defaultdict as _dd
    buckets = _dd(list)
    for f in sorted(events_dir.glob("*.events.jsonl")):
        for line in f.read_text(encoding="utf-8", errors="ignore").splitlines():
            if not line.strip():
                continue
            try:
                e = json.loads(line)
                d = datetime.fromisoformat(str(e["occurred_at"])[:10])
            except (ValueError, KeyError):
                continue
            y, w, _ = d.isocalendar()
            buckets[f"{y}-W{w:02d}"].append(line)
    out_dir.mkdir(parents=True, exist_ok=True)
    written = {}
    for wk, lines in sorted(buckets.items()):
        t = out_dir / f"{wk}.events.jsonl"
        body = "\n".join(lines) + "\n"
        if not t.is_file() or t.read_text(encoding="utf-8") != body:
            t.write_text(body, encoding="utf-8")     # 幂等：内容没变就不重写
        written[wk] = len(lines)
    return {"weeks": len(written), "granularity": "iso_week",
            "max_granularity_policy": "weekly_or_finer_only", "counts": written}


def write_public_summary(root: Path) -> None:
    """公开仓唯一允许的产物：纯计数与占比，零原话、零路径。

    为什么单独做一份而不是「把 LESSONS 脱敏一下」：
    脱敏是尽力而为，聚合是结构上就不含个人内容 —— 后者才敢放进 PUBLIC 仓。
    """
    from collections import Counter as _C
    ev = root / EVENTS
    topics, sources, days = _C(), _C(), set()
    total = 0
    for f in sorted(ev.glob("*.events.jsonl")):
        for line in f.read_text(encoding="utf-8", errors="ignore").splitlines():
            if not line.strip():
                continue
            try:
                e = json.loads(line)
            except ValueError:
                continue
            total += 1
            days.add(str(e.get("occurred_at", ""))[:10])
            sources[e.get("source_id", "?")] += 1
            for t in e.get("topics", []):
                topics[t] += 1
    lines = ["<!-- 由 memory_atlas_daily.py 生成。只含聚合计数，无原话无路径。 -->",
             "", "# Agent 使用聚合（公开面）", "",
             f"会话 **{total}** 个，活跃 **{len(days)}** 天。", "",
             "| 主题 | 会话数 | 占比 |", "|---|---|---|"]
    for t, c in topics.most_common():
        lines.append(f"| {t} | {c} | {c * 100 // max(total, 1)}% |")
    lines += ["", "| 来源 | 会话数 |", "|---|---|"]
    for s_, c in sources.most_common():
        lines.append(f"| {s_} | {c} |")
    lines += ["", "> 明细（含原话与路径）不入公开仓 —— 见 `.gitignore` 与",
              "> `config/data_sources/source_registry.json` 的 privacy_contract。", ""]
    (root / PUBLIC).parent.mkdir(parents=True, exist_ok=True)
    (root / PUBLIC).write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--full", action="store_true", help="全量重算（默认增量）")
    ap.add_argument("--weekly-archive", metavar="DIR",
                    help="按 ISO 周切片归档事件（Owner 定：打包切片最大为每周，不许更粗）")
    args = ap.parse_args()
    root = Path(args.repo_root).resolve()
    if not (root / SCRIPTS / "agent_session_extract.py").is_file():
        print(json.dumps({"state": "FAILED", "reason": "not_a_valid_repo_root",
                          "root": str(root)}, ensure_ascii=False))
        return 1

    (root / EVENTS).mkdir(parents=True, exist_ok=True)
    (root / VIEWS).mkdir(parents=True, exist_ok=True)

    inc = [] if args.full else ["--incremental"]
    steps = [
        (["--source", "all", "--out", str(EVENTS), *inc], "1_extract",
         SCRIPTS / "agent_session_extract.py"),
        (["--events", str(EVENTS), "--out", str(ANALYSIS)], "2_analysis",
         SCRIPTS / "agent_usage_analysis.py"),
        (["--events", str(EVENTS), "--out", str(VIEWS)], "3_views",
         SCRIPTS / "agent_journal_build.py"),
        (["--events", str(EVENTS), "--out", str(LESSONS)], "4_lessons",
         SCRIPTS / "agent_lessons_build.py"),
        (["--events", str(EVENTS), "--atlas", str(ATLAS)], "5_atlas",
         SCRIPTS / "agent_atlas_project.py"),
    ]
    results = [run(root, [str(script), *a], label) for a, label, script in steps]

    weekly = None
    if args.weekly_archive:
        weekly = write_weekly(root / EVENTS, Path(args.weekly_archive))

    write_public_summary(root)

    ev_files = sorted((root / EVENTS).glob("*.events.jsonl"))
    events = sum(sum(1 for line in f.read_text(encoding="utf-8", errors="ignore").splitlines()
                     if line.strip()) for f in ev_files)
    out_bytes = sum(f.stat().st_size for f in ev_files)
    failed = [r for r in results if r["state"] != "PASS"]
    receipt = {
        "schema_version": "memory_atlas.daily_sediment.v1",
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "mode": "full" if args.full else "incremental",
        "state": "SUCCEEDED" if not failed else "FAILED",
        "agent_dependency": "none_runtime_pure_script",
        "token_cost": 0,
        "sources": len(ev_files),
        "events_total": events,
        "events_bytes": out_bytes,
        "steps": results,
        "weekly_archive": weekly,
    }
    print(json.dumps(receipt, ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
