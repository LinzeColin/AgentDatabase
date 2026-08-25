#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import champion_core as core


def suite(value: float, *, hard: bool = False, elapsed: float = 0.05, chars: int = 120, tasks: int = 2) -> dict:
    rows = []
    for index in range(8):
        rows.append(
            {
                "case_id": f"c-{index}",
                "task_id": f"t-{index % tasks}",
                "score": value,
                "hard_fail": hard,
                "dimensions": {
                    "correctness": value,
                    "coverage": value,
                    "executability": value,
                    "security": 0.0 if hard else value,
                    "efficiency": value,
                    "oracle": value,
                },
                "elapsed_seconds": elapsed,
                "candidate_chars": chars,
                "output_chars": chars,
            }
        )
    return {
        "mean": value,
        "worst": value,
        "variance": 0.0,
        "hard_failure_count": len(rows) if hard else 0,
        "per_task": {f"t-{index}": value for index in range(tasks)},
        "results": rows,
    }


def bundles(value: float, **kwargs) -> dict:
    return {
        "final": suite(value, **kwargs),
        "regression": suite(value, **kwargs),
        "redteam": suite(value, **kwargs),
    }


class ChampionCoreTests(unittest.TestCase):
    def test_strict_champion_passes_only_when_all_dimensions_lead(self) -> None:
        champion = bundles(0.96, elapsed=0.01, chars=70)
        peers = {name: bundles(0.75, elapsed=0.10, chars=180) for name in core.CAPABILITY_PRIORS if name != "prompt_compiler"}
        result = core.strict_champion_gate(
            champion_name="prompt_compiler",
            champion_suites=champion,
            peer_suites=peers,
            required_peers=list(peers),
            bootstrap_iterations=300,
        )
        self.assertEqual(result["status"], core.CHAMPION_STATUS_PASS, result)
        self.assertTrue(result["release_allowed"])

    def test_missing_peer_never_passes(self) -> None:
        result = core.strict_champion_gate(
            champion_name="prompt_compiler",
            champion_suites=bundles(0.99),
            peer_suites={"gepa": bundles(0.50)},
            required_peers=["gepa", "promptfoo"],
            bootstrap_iterations=100,
        )
        self.assertEqual(result["status"], core.CHAMPION_STATUS_NOT_PROVEN)
        self.assertIn("promptfoo", result["missing_peers"])

    def test_missing_dimension_never_passes(self) -> None:
        champion = bundles(0.99)
        peer = bundles(0.50)
        for row in champion["final"]["results"]:
            row.pop("elapsed_seconds")
        result = core.strict_champion_gate(
            champion_name="prompt_compiler",
            champion_suites=champion,
            peer_suites={"gepa": peer},
            required_peers=["gepa"],
            bootstrap_iterations=100,
        )
        self.assertEqual(result["status"], core.CHAMPION_STATUS_NOT_PROVEN)
        self.assertIn({"peer": "gepa", "dimension": "latency_efficiency"}, result["missing_dimensions"])

    def test_tie_below_ceiling_is_not_first(self) -> None:
        tied = bundles(0.80)
        result = core.strict_champion_gate(
            champion_name="prompt_compiler",
            champion_suites=tied,
            peer_suites={"gepa": bundles(0.80)},
            required_peers=["gepa"],
            bootstrap_iterations=100,
        )
        self.assertEqual(result["status"], core.CHAMPION_STATUS_NOT_PROVEN)
        self.assertTrue(result["not_statistically_separated"])

    def test_tie_at_mathematical_ceiling_is_joint_first(self) -> None:
        perfect = bundles(1.0, elapsed=0.0, chars=0)
        result = core.strict_champion_gate(
            champion_name="prompt_compiler",
            champion_suites=perfect,
            peer_suites={"gepa": bundles(1.0, elapsed=0.0, chars=0)},
            required_peers=["gepa"],
            bootstrap_iterations=100,
        )
        self.assertEqual(result["status"], core.CHAMPION_STATUS_PASS, result)
        statuses = {
            row["status"]
            for row in result["comparisons"]["gepa"]["dimensions"].values()
        }
        self.assertEqual(statuses, {"TIED_FIRST_AT_CEILING"})

    def test_peer_advantage_rejects_champion(self) -> None:
        result = core.strict_champion_gate(
            champion_name="prompt_compiler",
            champion_suites=bundles(0.60, elapsed=0.20, chars=200),
            peer_suites={"gepa": bundles(0.90, elapsed=0.01, chars=60)},
            required_peers=["gepa"],
            bootstrap_iterations=100,
        )
        self.assertEqual(result["status"], core.CHAMPION_STATUS_REJECTED)
        self.assertTrue(result["peer_better"])

    def test_budget_is_conserved_and_every_arm_is_probed(self) -> None:
        plan = core.adaptive_budget_plan(
            total_budget=101,
            arms=["gepa", "autoresearch", "meta_harness", "promptfoo"],
            minimum_probe=5,
        )
        self.assertEqual(sum(plan.allocations.values()), 101)
        self.assertTrue(all(value >= 5 for value in plan.allocations.values()))
        self.assertIn("prompt_compiler", plan.allocations)

    def test_budget_rejects_impossible_minimum_probe(self) -> None:
        with self.assertRaises(core.ChampionContractError):
            core.adaptive_budget_plan(
                total_budget=9,
                arms=["gepa", "autoresearch"],
                minimum_probe=4,
            )

    def test_weak_redteam_gap_routes_more_weight_to_promptfoo(self) -> None:
        plan = core.adaptive_budget_plan(
            total_budget=200,
            arms=["gepa", "autoresearch", "meta_harness", "promptfoo"],
            minimum_probe=5,
            dimension_gaps={"redteam": 1.0},
            synthesis_share=0.05,
        )
        self.assertGreater(plan.allocations["promptfoo"], plan.allocations["gepa"])
        self.assertGreater(plan.allocations["promptfoo"], plan.allocations["meta_harness"])

    def test_evaluation_cache_deduplicates_exact_contract(self) -> None:
        cache = core.EvaluationCache()
        key = cache.key(
            candidate="x",
            case={"id": "c"},
            role_identity="model-a",
            repeat=1,
            phase="validation",
        )
        self.assertIsNone(cache.get(key))
        cache.put(key, {"score": 1})
        self.assertEqual(cache.get(key), {"score": 1})
        self.assertEqual(cache.stats(), {"entries": 1, "hits": 1, "misses": 1})

    def test_robust_key_prefers_weakest_dimension_over_mean(self) -> None:
        balanced = {"overall": 0.80, "hard_safety": 1.0, "weakest_slice": 0.75, "correctness": 0.80}
        brittle = {"overall": 0.95, "hard_safety": 1.0, "weakest_slice": 0.30, "correctness": 0.95}
        self.assertGreater(core.robust_candidate_key(balanced), core.robust_candidate_key(brittle))

    def test_registry_requires_dual_role(self) -> None:
        valid = {
            "competitors": [
                {
                    "name": "x",
                    "required": True,
                    "roles": ["same_layer_competitor", "routable_executor"],
                }
            ]
        }
        invalid = {"competitors": [{"name": "x", "roles": ["same_layer_competitor"]}]}
        self.assertEqual(core.verify_competitor_registry(valid)["status"], "PASS")
        self.assertEqual(core.verify_competitor_registry(invalid)["status"], "BLOCKED")

    def test_shipped_registry_has_four_required_core_competitors(self) -> None:
        path = Path(__file__).resolve().parents[1] / "references" / "COMPETITOR_REGISTRY.json"
        registry = json.loads(path.read_text(encoding="utf-8"))
        result = core.verify_competitor_registry(registry)
        self.assertEqual(result["status"], "PASS", result)
        self.assertEqual(
            set(result["required_competitors"]),
            {"gepa", "autoresearch", "meta_harness", "promptfoo"},
        )

    def test_dimension_gap_marks_unknown_as_maximum(self) -> None:
        gap = core.dimension_gap_from_summaries(
            {"overall": 0.9, "redteam": None},
            {"peer": {"overall": 0.8, "redteam": 0.7}},
        )
        self.assertEqual(gap["overall"], 0.0)
        self.assertEqual(gap["redteam"], 1.0)


    def test_project_specific_dimension_can_be_frozen_and_proven(self) -> None:
        champion = bundles(0.95, elapsed=0.01, chars=60)
        peer = bundles(0.70, elapsed=0.10, chars=180)
        for bundle, value in ((champion, 0.97), (peer, 0.60)):
            for suite_payload in bundle.values():
                for row in suite_payload["results"]:
                    row["dimensions"]["domain_fidelity"] = value
        result = core.strict_champion_gate(
            champion_name="prompt_compiler",
            champion_suites=champion,
            peer_suites={"gepa": peer},
            required_peers=["gepa"],
            dimensions=[
                *[core.DimensionSpec(name=name) for name in core.MANDATORY_DIMENSIONS],
                core.DimensionSpec(name="domain_fidelity"),
            ],
            bootstrap_iterations=100,
        )
        self.assertEqual(result["status"], core.CHAMPION_STATUS_PASS, result)
        self.assertEqual(
            result["comparisons"]["gepa"]["dimensions"]["domain_fidelity"]["status"],
            "STRICTLY_FIRST",
        )

    def test_project_specific_dimension_missing_evidence_blocks(self) -> None:
        result = core.strict_champion_gate(
            champion_name="prompt_compiler",
            champion_suites=bundles(0.95),
            peer_suites={"gepa": bundles(0.70)},
            required_peers=["gepa"],
            dimensions=[core.DimensionSpec(name="domain_fidelity")],
            bootstrap_iterations=100,
        )
        self.assertEqual(result["status"], core.CHAMPION_STATUS_NOT_PROVEN)
        self.assertIn({"peer": "gepa", "dimension": "domain_fidelity"}, result["missing_dimensions"])

    def test_invalid_dimension_name_is_rejected(self) -> None:
        with self.assertRaises(core.ChampionContractError):
            core.strict_champion_gate(
                champion_name="prompt_compiler",
                champion_suites=bundles(0.95),
                peer_suites={"gepa": bundles(0.70)},
                required_peers=["gepa"],
                dimensions=[core.DimensionSpec(name="bad dimension")],
                bootstrap_iterations=10,
            )

    def test_core_self_test(self) -> None:
        self.assertEqual(core.self_test()["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
