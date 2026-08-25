from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve()
SCRIPTS = HERE.parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from audit_persona_fleet_for_team import build_admission  # noqa: E402
from build_execution_contract import build_contract  # noqa: E402
from build_team_dossier import build_dossier, route_persona_slugs  # noqa: E402
from compile_task_graph import compile_graph  # noqa: E402
from route_team_moe import build_route  # noqa: E402
from score_team_delta import score_result  # noqa: E402
from record_team_outcome import rebuild  # noqa: E402
from build_team_delta_card import build_card  # noqa: E402
from team_runtime_common import required_control_plane, write_json  # noqa: E402

CATEGORIES = [
    "软件开发师", "投资资本师", "材料建工师", "建造采购师",
    "创业经营师", "政治法律师", "思想教育师", "财务合规师",
    "农林牧渔师", "客户营销师", "艺术设计师", "医疗护理师",
]


def make_delivery(root: Path, category: str, slug: str, other_name: str | None = None) -> str:
    rel = Path(category) / slug / "versions" / "0.0.0.1" / f"{slug}-persona-distillation-delivery-v0.0.0.1.zip"
    target = root / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    claims = []
    for index, category_name in enumerate(("mental-model", "heuristic", "work-method", "blind-spot", "contradiction"), start=1):
        claims.append(json.dumps({
            "claim_id": f"{slug}-C{index:02d}",
            "category": category_name,
            "claim": f"{slug} uses evidence-first software AI research method {index}",
            "confidence": "high",
            "falsifiers": ["opposite evidence"],
            "time_scope": "stable",
            "source_ids": [f"SRC-{index}"],
        }, ensure_ascii=False))
    divergence = f"Documented divergence with {other_name}: use staged evidence instead of intuitive consensus." if other_name else "No named divergence in this fixture."
    inner_bytes = io.BytesIO()
    with zipfile.ZipFile(inner_bytes, "w", zipfile.ZIP_DEFLATED) as inner:
        inner.writestr("skill/evidence/claims.jsonl", "\n".join(claims) + "\n")
        inner.writestr("skill/boundaries.md", "- Do not invent current facts.\n- Do not exceed the documented capability scope.\n")
        inner.writestr("skill/divergence-map.md", divergence + "\n")
        inner.writestr("skill/decision-policy.md", "- Freeze assumptions before deciding.\n")
        inner.writestr("skill/work.md", "- Produce an evidence-linked artifact.\n")
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as outer:
        outer.writestr(f"delivery/runtime/{slug}-persona-skill-v0.0.0.1.zip", inner_bytes.getvalue())
    return str(rel)


def make_registry(root: Path, count: int = 45) -> None:
    products = []
    names = [f"Expert Person {index:02d}" for index in range(count)]
    counts = {category: 0 for category in CATEGORIES}
    for index in range(count):
        category = CATEGORIES[index % len(CATEGORIES)]
        counts[category] += 1
        slug = f"expert-person-{index:02d}"
        artifact = make_delivery(root, category, slug, names[(index + 1) % count] if index < 2 else None)
        products.append({
            "subject_uid": f"person-{index:04d}",
            "subject_slug": slug,
            "canonical_name": names[index],
            "registration_category": category,
            "identity_family_id": "software-engineer",
            "application_scenarios": ["软件 AI 研究 架构 竞品 benchmark", "evidence-first decision"],
            "key_capabilities": ["软件 AI 研究", "架构分析", "证据核验", "benchmark"],
            "user_value": ["Produces a better evidence-linked decision artifact"],
            "distillation_traits": ["Evidence before conclusion"],
            "hard_boundaries": ["No invented current facts"],
            "latest_artifact": artifact,
            "team_card": f"{category}/{slug}/team-card.json",
            "readiness": "ready",
            "subject_status": "living",
            "subject_active_through": 2026,
            "research_cutoff": "2026-08-01",
        })
    write_json(root / "team-index.json", {
        "generator_version": "v0.0.0.14",
        "category_counts": counts,
        "products": products,
    })


class CandidateAcceptanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        make_registry(self.root)
        write_json(self.root / "expert-fleet-admission.json", build_admission(self.root, require_artifacts=True))
        self.task = "使用软件 AI 研究和 benchmark 设计专家团队路由架构，完成竞品与证据分析。"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_four_modes_and_mandatory_controls(self) -> None:
        cases = [
            ("single_expert", 1),
            ("small_team", 5),
            ("small_team", 15),
            ("deep_team", 10),
            ("deep_team", 30),
            ("swarm", 25),
        ]
        expected_controls = {row["role_id"] for row in required_control_plane()}
        for mode, size in cases:
            with self.subTest(mode=mode, size=size):
                route = build_route(self.task, self.root, mode, size, "b")
                self.assertEqual(route["status"], "ready")
                self.assertEqual(route["mode"], mode)
                self.assertEqual(route["persona_expert_count"], size)
                self.assertFalse(route["solo_allowed"])
                self.assertTrue(all(row.get("subject_slug") for row in route["members"]))
                self.assertEqual({row["role_id"] for row in route["control_plane"]}, expected_controls)
                self.assertEqual(route["total_runtime_units"], size + len(expected_controls))

    def test_route_dossier_execution_contract_is_connected(self) -> None:
        route = build_route(self.task, self.root, "small_team", 7, "b")
        self.assertIn("members", route)
        self.assertIn("selected_roles", route)
        slugs = route_persona_slugs(route)
        self.assertEqual(len(slugs), 7)
        dossier = build_dossier(self.root, slugs, route)
        self.assertEqual(dossier["status"], "ready")
        self.assertEqual(dossier["loaded_persona_experts"], 7)
        self.assertTrue(all(member["payload_loaded"] for member in dossier["members"]))
        self.assertTrue(all(member["capsules"]["voice_capsule"]["enabled"] is False for member in dossier["members"]))
        contract = build_contract(route, dossier)
        self.assertEqual(contract["status"], "ready")
        roles = {unit["role"] for unit in contract["execution_units"]}
        for role in ("hypothesis-framer", "counterevidence-adversary", "independent-reviewer", "decision-judge", "synthesis-lead"):
            self.assertIn(role, roles)

    def test_c_requires_real_calibration_and_falls_back_to_b(self) -> None:
        route = build_route(self.task, self.root, "small_team", 5, "c", telemetry_path=self.root / "missing.json")
        self.assertEqual(route["strategy"], "B")
        self.assertIn("60 outcomes", route["strategy_fallback_reason"])

    def test_auto_never_returns_solo(self) -> None:
        graph = compile_graph("请用最适合的人物专家解释一个明确的软件架构问题。")
        self.assertIn(graph["mode"], {"single_expert", "small_team", "deep_team", "swarm"})
        self.assertNotEqual(graph["mode"], "solo")
        self.assertFalse(graph["persona_count_contract"]["solo_allowed"])

    def test_outcome_telemetry_can_unlock_c_only_with_evidence(self) -> None:
        slices = [
            "single-explanation", "single-diagnosis", "small-product", "small-research",
            "deep-high-risk", "deep-architecture", "swarm-search", "swarm-batch", "currentness",
        ]
        runs = []
        for index in range(60):
            runs.append({
                "task_slice": slices[index % len(slices)],
                "task_domains": ["software-ai"],
                "subject_slugs": ["expert-person-00"],
                "predicted_success": 0.9,
                "actual_success": 0.9,
                "overall_delta": 96.0,
            })
        telemetry = rebuild(runs)
        self.assertTrue(telemetry["eligible_for_c"])
        self.assertLessEqual(telemetry["expected_calibration_error"], 0.12)
        self.assertGreaterEqual(telemetry["task_slice_coverage"], 0.75)

    def test_delta_card_keeps_user_output_concise(self) -> None:
        card = build_card(
            {"mode": "single_expert", "persona_expert_count": 1, "task_graph": {"mode_reasons": ["bounded task"]}},
            {"work_completed": ["artifact"], "member_contributions": [{"subject_slug": "expert-person-00", "decision_influence": 1, "artifact_owned": True}], "next_action": "publish"},
            {"dimensions": {"overall_delta": 96}, "benefit_deltas": {"quality": 12}, "efficiency_deltas": {"latency": 4}, "status": "TARGET_METRICS_MET_EVIDENCE_INCOMPLETE"},
        )
        self.assertEqual(card["persona_expert_count"], 1)
        self.assertEqual(card["next_action"], "publish")
        self.assertNotIn("full_role_transcript", card)

    def test_95_and_75_scoring_contract(self) -> None:
        strong = score_result({
            "absolute": {"user_experience": 97, "moe": 97, "routing": 96, "functionality": 98, "quality": 97},
            "candidate": {
                "quality": 98, "task_completion": 99, "evidence_coverage": 98,
                "risk_reduction": 98, "time_saved": 95, "user_action_reduction": 98,
                "cost": 20, "latency": 20, "coordination_tax": 10, "correlated_error_risk": 5,
            },
            "baseline": {
                "quality": 70, "task_completion": 70, "evidence_coverage": 65,
                "risk_reduction": 60, "time_saved": 55, "user_action_reduction": 55,
                "cost": 50, "latency": 50, "coordination_tax": 40, "correlated_error_risk": 35,
            },
            "paired": {"win_rate": 99, "noninferiority_rate": 100, "catastrophic_error_free_rate": 100},
            "evidence": {"level": "L4", "external_verifier_passed": True, "production_blind_tasks": 20, "native_competitors_run": 2},
        })
        self.assertTrue(strong["target95_pass"])
        self.assertTrue(strong["floor75_pass"])
        self.assertEqual(strong["status"], "MARKET_LEADER_PASS")

        weak = score_result({
            "absolute": {"user_experience": 74, "moe": 90, "routing": 90, "functionality": 90, "quality": 90},
            "candidate": {key: 50 for key in ("quality", "task_completion", "evidence_coverage", "risk_reduction", "time_saved", "user_action_reduction", "cost", "latency", "coordination_tax", "correlated_error_risk")},
            "baseline": {key: 50 for key in ("quality", "task_completion", "evidence_coverage", "risk_reduction", "time_saved", "user_action_reduction", "cost", "latency", "coordination_tax", "correlated_error_risk")},
            "paired": {"win_rate": 50, "noninferiority_rate": 50, "catastrophic_error_free_rate": 90},
            "evidence": {"level": "L2"},
        })
        self.assertFalse(weak["floor75_pass"])
        self.assertEqual(weak["status"], "CANDIDATE_REJECTED_BELOW_FLOOR")


if __name__ == "__main__":
    unittest.main()
