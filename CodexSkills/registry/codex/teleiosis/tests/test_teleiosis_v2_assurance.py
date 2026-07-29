from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = SKILL_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from wbi_market.assurance import evaluate_assurance, evaluate_sequential_canary  # noqa: E402


def good_record() -> dict:
    return {
        "traces": [
            {
                "run_id": "run-1",
                "task_id": "task-1",
                "arm_id": "candidate",
                "subject_digest": "a" * 64,
                "environment_digest": "b" * 64,
                "tool_trace_digest": "c" * 64,
                "artifact_digest": "d" * 64,
                "handoff_digest": "e" * 64,
            }
        ],
        "evaluator_separation": {"generator_ids": ["generator-1"], "evaluator_ids": ["judge-1"]},
        "judge_calibration": {
            "sample_size": 30,
            "agreement": 0.9,
            "cohens_kappa": 0.75,
            "min_sample_size": 20,
            "min_agreement": 0.8,
            "min_cohens_kappa": 0.6,
        },
        "providers": [
            {
                "id": "adapter-1",
                "version": "1.2.3",
                "status": "pinned",
                "source_url": "https://github.com/LinzeColin/AgentDatabase",
                "valid_until": "2026-12-31",
            }
        ],
        "contamination": {
            "candidate_holdout_access_count": 0,
            "max_overlap_ratio": 0.0,
            "allowed_overlap_ratio": 0.0,
        },
        "quality_reports": {
            "contamination": {"status": "PASS", "audit_digest": "1" * 64},
            "assignment": {"status": "PASS", "audit_digest": "2" * 64},
            "sample_ratio_mismatch": {"status": "PASS", "audit_digest": "3" * 64},
            "environment_parity": {"status": "PASS", "audit_digest": "4" * 64},
            "power_plan": {"status": "PASS", "audit_digest": "5" * 64},
            "referential_integrity": {"status": "PASS", "audit_digest": "6" * 64},
            "judge_calibration": {"status": "PASS", "audit_digest": "7" * 64},
            "market_temporal_integrity": {"status": "PASS", "audit_digest": "8" * 64},
        },
        "evidence_chain": {"status": "PASS", "evidence_chain_digest": "9" * 64},
        "canary": {
            "stop_rules_predeclared": True,
            "critical_incidents": 0,
            "stop_triggered": False,
            "candidate_stopped": False,
        },
        "freshness": {
            "checked_at": "2026-07-29",
            "max_age_days": 30,
            "reheat_triggered": False,
            "reheat_acknowledged": False,
        },
    }


class AssuranceTests(unittest.TestCase):
    def test_good_assurance_passes_but_does_not_promote(self):
        result = evaluate_assurance(good_record(), as_of="2026-07-29")
        self.assertEqual(result["status"], "PASS", result)
        self.assertEqual(result["final_authority"], "teleiosis")
        self.assertEqual(result["market_kernel_authority"], "evidence_only")
        self.assertNotIn("PROMOTE", str(result))

    def test_generator_evaluator_overlap_blocks(self):
        record = good_record()
        record["evaluator_separation"]["evaluator_ids"] = ["generator-1"]
        result = evaluate_assurance(record, as_of="2026-07-29")
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("GENERATOR_EVALUATOR_OVERLAP", {row["code"] for row in result["failures"]})

    def test_expired_provider_blocks(self):
        record = good_record()
        record["providers"][0]["valid_until"] = "2026-07-01"
        result = evaluate_assurance(record, as_of="2026-07-29")
        self.assertIn("PROVIDER_EVIDENCE_EXPIRED", {row["code"] for row in result["failures"]})

    def test_holdout_contamination_blocks(self):
        record = good_record()
        record["contamination"]["candidate_holdout_access_count"] = 1
        result = evaluate_assurance(record, as_of="2026-07-29")
        self.assertIn("SEALED_HOLDOUT_ACCESSED", {row["code"] for row in result["failures"]})

    def test_bad_judge_calibration_blocks(self):
        record = good_record()
        record["judge_calibration"]["cohens_kappa"] = 0.2
        result = evaluate_assurance(record, as_of="2026-07-29")
        self.assertIn("JUDGE_KAPPA_TOO_LOW", {row["code"] for row in result["failures"]})


    def test_quality_gate_failure_blocks(self):
        record = good_record()
        record["quality_reports"]["sample_ratio_mismatch"]["status"] = "BLOCKED"
        result = evaluate_assurance(record, as_of="2026-07-29")
        self.assertIn("QUALITY_GATE_NOT_PASS", {row["code"] for row in result["failures"]})

    def test_missing_evidence_chain_blocks(self):
        record = good_record()
        record.pop("evidence_chain")
        result = evaluate_assurance(record, as_of="2026-07-29")
        self.assertIn("EVIDENCE_CHAIN_UNPROVEN", {row["code"] for row in result["failures"]})

    def test_sequential_canary_enforces_stop(self):
        contract = {"predeclared": True, "max_critical_incidents": 0, "max_failure_rate": 0.2, "min_observations": 5}
        observations = [{"completed": True, "incident_severity": "none"} for _ in range(4)]
        observations.append({"completed": False, "incident_severity": "critical"})
        result = evaluate_sequential_canary(contract, observations)
        self.assertTrue(result["stop"])
        self.assertEqual(result["decision"], "STOP_CANDIDATE")


if __name__ == "__main__":
    unittest.main(verbosity=2)
