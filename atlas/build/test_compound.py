#!/usr/bin/env python3
"""compound.py 的负控。跑法：python3 atlas/build/test_compound.py

这里测的不是「能不能跑通」，是**能不能挡住不该通过的东西**：
一个事件声称自己已经产生经济影响，但拿不出证据 —— 系统必须把它压回去，
而不是照单全收。这条规则如果只写在文档里、不由代码执行，它就等于不存在。
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compound  # noqa: E402

FAILED: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    print(("  ✓ " if cond else "  ✗ ") + name + (f"  —— {detail}" if detail and not cond else ""))
    if not cond:
        FAILED.append(name)


def ev(**kw) -> dict:
    base = {
        "schema_version": compound.SCHEMA,
        "event_id": "t-001",
        "generated_at": "2026-08-20T00:00:00Z",
        "producer": {"kind": "chatgpt_schedule", "name": "成果复利转化器"},
    }
    base.update(kw)
    return base


def write(d: Path, name: str, obj) -> None:
    (d / name).write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        D = Path(td)

        # ── 1. 形状校验：坏 JSON / 错 schema / 缺 event_id 都要被拒收且**说出来** ──
        print("\n【形状校验】")
        (D / "bad.json").write_text("{ 这不是 json", encoding="utf-8")
        write(D, "wrongschema.json", {"schema_version": "something.else.v9", "event_id": "x"})
        write(D, "noid.json", {"schema_version": compound.SCHEMA})
        write(D, "ok.json", ev(candidates=[{"candidate_id": "c1", "problem": "占位",
                                            "stage": "CAPTURED"}]))
        events, rejected = compound.read_events([D])
        check("坏 JSON / 错 schema / 缺 id 三个都被拒收", len(rejected) == 3, f"实际 {len(rejected)}")
        check("拒收记录带原因", all(r.get("why") for r in rejected))
        check("合格的那一个读进来了", len(events) == 1 and events[0]["event_id"] == "t-001")

        # ── 2. 核心负控：没有证据就不许升级 ──
        print("\n【不许自动升级 —— 这一节是整个模块存在的理由】")
        for name, cand, paths, allowed in [
            ("声称 ECONOMIC_IMPACT 但零证据 → 压到 CAPTURED",
             {"candidate_id": "a", "problem": "空口经济影响", "stage": "ECONOMIC_IMPACT"},
             [], "CAPTURED"),
            ("声称 ADOPTED 但只有一条证据 → 压到 QUALIFIED",
             {"candidate_id": "b", "problem": "空口采用", "stage": "ADOPTED",
              "evidence": ["只有一条"]},
             [], "QUALIFIED"),
            ("有采用证据 → 可以到 ADOPTED",
             {"candidate_id": "c", "problem": "真被用了", "stage": "ADOPTED",
              "evidence": ["e1", "e2"], "adoption_evidence": ["第二个任务用了它"]},
             [], "ADOPTED"),
            ("金额只是 ESTIMATED → 最高 OUTCOME，不许 ECONOMIC_IMPACT",
             {"candidate_id": "d", "problem": "估的钱", "stage": "ECONOMIC_IMPACT",
              "evidence": ["e1", "e2"], "adoption_evidence": ["用了"]},
             [{"candidate_id": "d", "path": "cost_reduction", "value_status": "ESTIMATED"}],
             "OUTCOME"),
            ("金额 OBSERVED → 允许 ECONOMIC_IMPACT",
             {"candidate_id": "e", "problem": "真省下来了", "stage": "ECONOMIC_IMPACT",
              "evidence": ["e1", "e2"], "adoption_evidence": ["用了"]},
             [{"candidate_id": "e", "path": "cost_reduction", "value_status": "OBSERVED",
               "evidence": ["token 日均从 x 降到 y"]}],
             "ECONOMIC_IMPACT"),
        ]:
            rows, clamps = compound.project_candidates(
                [ev(event_id=cand["candidate_id"], candidates=[cand], economic_paths=paths)])
            got = rows[0]["stage"] if rows else "(空)"
            check(name, got == allowed, f"得到 {got}，应为 {allowed}")

        # 压回去这件事必须留痕，否则页面上看不出「它本来声称更高」
        rows, clamps = compound.project_candidates(
            [ev(candidates=[{"candidate_id": "z", "problem": "空口", "stage": "ECONOMIC_IMPACT"}])])
        check("压回去的动作有记录（可审计）", len(clamps) == 1 and clamps[0]["claimed"] == "ECONOMIC_IMPACT")

        # HOLD / REJECT 是旁路，不受证据上限约束 —— 允许「这周不晋级」
        rows, _ = compound.project_candidates(
            [ev(candidates=[{"candidate_id": "h", "problem": "先放着", "stage": "HOLD"}])])
        check("HOLD 不被压回主链", rows[0]["stage"] == "HOLD")

        # ── 3. 金额未知就是未知，绝不填 0 ──
        print("\n【金额未知 ≠ 0】")
        rows, _ = compound.project_candidates([ev(
            candidates=[{"candidate_id": "m", "problem": "没金额", "stage": "CAPTURED"}],
            economic_paths=[{"candidate_id": "m", "path": "direct_revenue",
                             "value_status": "UNKNOWN", "amount": None}])])
        roll = compound.economic_rollup(rows)
        amounts = [r["amount"] for p in roll["paths"] for r in p["rows"]]
        check("未知金额保持 None，没有被填成 0", amounts == [None], f"实际 {amounts}")
        check("没有可核金额时 money_state 是「没做」", roll["money_state"] == "没做")

        # ── 4. 失败桥：只有根因已证实且有守卫的，才算形成防复发资产 ──
        print("\n【失败桥不许普通报错冒充复利】")
        br = compound.failure_bridge([
            {"root_cause_state": "PROVEN", "guard": "回归测试 x"},
            {"root_cause_state": "PROVEN", "guard": ""},
            {"root_cause_state": "HYPOTHESIS", "guard": "有守卫但根因没证实"},
            {"root_cause_state": "UNKNOWN", "guard": ""},
        ])
        check("4 条里只有 1 条算形成资产", br["guarded"] == 1, f"实际 {br['guarded']}")
        check("根因已证实的是 2 条", br["proven"] == 2)

        # ── 5. 空输入：必须是「没做/说不准」，不能是「通」，更不能是一堆 0 冒充结果 ──
        print("\n【没有事件时不许假装有结果】")
        empty = compound.build([D / "不存在"], {}, [], {}, {})
        check("空输入状态不是「通」", empty["state"] != "通", empty["state"])
        check("空输入 champion 是 None 而不是占位对象", empty["champion"] is None)
        check("空输入漏斗全 0 且如实标注", all(v == 0 for v in empty["funnel"].values()))
        check("空输入带 not_measured 清单", len(empty["not_measured"]) >= 3)

        # ── 6. 去重：同一条候选在多个事件里出现只算一条，证据取并集 ──
        print("\n【去重与证据合并】")
        rows, _ = compound.project_candidates([
            ev(event_id="e1", generated_at="2026-08-01T00:00:00Z",
               candidates=[{"candidate_id": "k", "problem": "同一件事",
                            "stage": "CAPTURED", "evidence": ["证据甲"]}]),
            ev(event_id="e2", generated_at="2026-08-08T00:00:00Z",
               candidates=[{"candidate_id": "k", "problem": "同一件事",
                            "stage": "QUALIFIED", "evidence": ["证据乙"]}]),
        ])
        check("同一候选合并成一条", len(rows) == 1, f"实际 {len(rows)}")
        check("证据取并集", set(rows[0]["evidence"]) == {"证据甲", "证据乙"})
        check("状态变化留了轨迹（漏斗要显示变化不只是累计）", len(rows[0]["moves"]) == 2)

    print("\n" + ("全部通过" if not FAILED else f"✗ {len(FAILED)} 条没过：" + "；".join(FAILED)))
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
