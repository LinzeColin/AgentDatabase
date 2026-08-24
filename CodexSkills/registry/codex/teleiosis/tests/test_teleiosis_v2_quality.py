from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = SKILL_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from wbi_market.common import object_sha256, read_json
from wbi_market.experiments import make_assignments
from wbi_market.quality import (
    contamination_audit,
    environment_parity,
    evidence_chain_digest,
    exclusive_assignment_integrity,
    judge_calibration,
    market_temporal_integrity,
    paired_assignment_integrity,
    power_plan,
    quality_audit,
    referential_integrity,
    sample_ratio_mismatch,
)


def load_spec():
    return read_json(SKILL_ROOT / "assets/market/templates/experiment_spec.json")


def task(task_id, partition="validation", prompt=None):
    return {"task_id":task_id,"cluster_id":"cluster-"+task_id,"partition":partition,"prompt":prompt or ("任务 "+task_id),"origin":"synthetic","oracle":{"type":"deterministic","expected":"success"},"protected":False,"sensitivity":"public"}


def env():
    return {"model_snapshot":"model-pinned-demo","runtime_version":"runtime-1.0.0","tools":["shell"],"permissions":["read","write-worktree"],"budget":{"tokens":2000,"cost_usd":0.1,"wall_seconds":60},"system_digest":"sha256:"+"1"*64,"dataset_digest":"sha256:"+"2"*64}


def result(spec, task_id, arm, rep=1, partition="validation"):
    return {"experiment_id":spec["experiment_id"],"run_id":f"run-{task_id}-{arm['id']}-{rep}","task_id":task_id,"partition":partition,"arm_id":arm["id"],"repetition":rep,"status":"completed","outcome":{"success":True,"score":0.9,"accepted":True},"usage":{"tokens":1000,"cost_usd":0.02,"latency_ms":1000,"tool_calls":2},"evidence_kind":"offline","artifact_digest":None if arm["kind"]=="no_skill" else arm["artifact_digest"],"trace_digest":"sha256:"+object_sha256([task_id,arm["id"],rep]),"environment":env(),"hard_failures":[],"protected":False}


class QualityTests(unittest.TestCase):
    def test_contamination_exact_and_near_duplicate_blocks(self):
        rows=[task("visible","validation","install package safely now"), task("secret","sealed_holdout","install package safely now")]
        report=contamination_audit(rows)
        self.assertEqual(report["status"],"BLOCKED")
        self.assertTrue(any(x["type"].startswith("exact_") or x["type"].startswith("near_") for x in report["findings"]))

    def test_clean_contamination_passes(self):
        report=contamination_audit([task("a","validation","validate json schema"),task("b","sealed_holdout","recover database journal")])
        self.assertEqual(report["status"],"PASS")

    def test_paired_assignment_integrity_and_srm_pass(self):
        spec=load_spec(); tasks=[task(f"t{i}") for i in range(20)]
        assignments,blind=make_assignments(spec,tasks)
        arms=[a["id"] for a in spec["arms"]]
        self.assertEqual(paired_assignment_integrity(assignments,arms,blind)["status"],"PASS")
        self.assertEqual(sample_ratio_mismatch(assignments,spec["assignment_guard"]["expected_weights"],blind)["status"],"PASS")

    def test_srm_detects_imbalance(self):
        rows=[{"task_id":f"t{i}","repetition":1,"arm_id":"candidate"} for i in range(100)] + [{"task_id":f"b{i}","repetition":1,"arm_id":"baseline"} for i in range(2)]
        report=sample_ratio_mismatch(rows,{"candidate":1.0,"baseline":1.0},alpha=0.001)
        self.assertEqual(report["status"],"BLOCKED")

    def test_exclusive_assignment_detects_cross_arm_exposure(self):
        rows=[{"user_id":"u1","task_id":"a","repetition":1,"arm_id":"candidate"},{"user_id":"u1","task_id":"b","repetition":1,"arm_id":"baseline"}]
        self.assertEqual(exclusive_assignment_integrity(rows,"user_id")["status"],"BLOCKED")

    def test_environment_mismatch_blocks(self):
        spec=load_spec(); rows=[result(spec,"t",spec["arms"][0]),result(spec,"t",spec["arms"][1])]
        rows[1]["environment"]["runtime_version"]="runtime-2.0"
        report=environment_parity(rows,spec["environment_parity"]["required_fields"])
        self.assertEqual(report["status"],"BLOCKED")

    def test_power_plan_requires_adequate_n(self):
        spec=load_spec(); self.assertEqual(power_plan(spec)["status"],"PASS")
        spec["analysis_plan"]["planned_sample_size_per_arm"]=10
        self.assertEqual(power_plan(spec)["status"],"REHEAT_REQUIRED")

    def test_judge_disabled_is_not_applicable(self):
        policy=copy.deepcopy(load_spec()["judge_policy"]); policy["enabled"]=False
        self.assertEqual(judge_calibration([],policy)["status"],"NOT_APPLICABLE")

    def test_market_temporal_integrity(self):
        spec=load_spec(); spec["evidence_target"]="lab"
        self.assertEqual(market_temporal_integrity([],spec)["status"],"NOT_APPLICABLE")
        spec["evidence_target"]="market_validated"
        stale={"event_id":"e1","timestamp":"2020-01-01T00:00:00Z","arm_id":"candidate"}
        self.assertEqual(market_temporal_integrity([stale],spec)["status"],"BLOCKED")

    def test_referential_integrity_and_full_quality(self):
        spec=load_spec(); tasks=[task("t1")]
        assignments,blind=make_assignments(spec,tasks)
        results=[result(spec,"t1",arm) for arm in spec["arms"]]
        self.assertEqual(referential_integrity(tasks,results,[],spec)["status"],"PASS")
        lab=copy.deepcopy(spec); lab["evidence_target"]="lab"
        calibration=[{"gold_label":"pass","judge_label":"pass"} for _ in range(20)]
        report=quality_audit(lab,tasks,assignments,results,calibration=calibration,blind_map=blind)
        self.assertEqual(report["status"],"PASS",report)

    def test_evidence_chain_complete_and_incomplete(self):
        parts={k:"sha256:"+str(i)*64 for i,k in enumerate(["subject_digest","spec_digest","dataset_digest","assignment_digest","result_digest","quality_audit_digest","summary_digest","gate_digest"],1)}
        self.assertEqual(evidence_chain_digest(parts)["status"],"PASS")
        parts.pop("gate_digest")
        self.assertEqual(evidence_chain_digest(parts)["status"],"BLOCKED")

if __name__ == "__main__":
    unittest.main(verbosity=2)
