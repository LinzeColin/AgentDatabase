from __future__ import annotations

import sys
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = SKILL_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from wbi_market.cluster_stats import aggregate_cluster_effects  # noqa: E402


class ClusterStatisticsTests(unittest.TestCase):
    def test_repeated_trials_do_not_inflate_unit_of_inference(self):
        rows = []
        for cluster in ("cluster-a", "cluster-b"):
            for task in range(3):
                for trial in range(20):
                    for arm, score, success, cost in (
                        ("candidate", 0.9, True, 0.02),
                        ("baseline", 0.7, task != 0, 0.01),
                    ):
                        rows.append(
                            {
                                "cluster_id": cluster,
                                "task_id": f"{cluster}-task-{task}",
                                "trial_id": str(trial),
                                "arm_id": arm,
                                "success": success,
                                "score": score,
                                "cost_usd": cost,
                                "latency_ms": 1000,
                            }
                        )
        result = aggregate_cluster_effects(rows, "candidate", "baseline", bootstrap_samples=200)
        self.assertEqual(result["paired_clusters"], 2)
        self.assertEqual(result["metrics"]["score_delta"]["n_clusters"], 2)
        self.assertTrue(result["repeated_trials_aggregated_before_inference"])
        self.assertEqual(result["unit_of_inference"], "cluster")

    def test_budget_normalized_utility_is_reported(self):
        rows = [
            {"cluster_id": "c", "task_id": "t", "trial_id": "1", "arm_id": "candidate", "success": True, "score": 0.9, "cost_usd": 0.03, "latency_ms": 1000},
            {"cluster_id": "c", "task_id": "t", "trial_id": "1", "arm_id": "baseline", "success": True, "score": 0.8, "cost_usd": 0.01, "latency_ms": 900},
        ]
        result = aggregate_cluster_effects(rows, "candidate", "baseline", bootstrap_samples=20)
        self.assertIn("score_per_usd_delta", result["metrics"])
        self.assertLess(result["metrics"]["score_per_usd_delta"]["mean"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
