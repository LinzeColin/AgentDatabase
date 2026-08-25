from __future__ import annotations

import copy
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = SKILL_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

import wbi_market as market_package  # noqa: E402
import importlib.util
_spec = importlib.util.spec_from_file_location("wbi_market_cli", SCRIPTS_ROOT / "wbi_market.py")
market_lab = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(market_lab)
from wbi_market.common import object_sha256, read_json, write_json, write_jsonl  # noqa: E402
from wbi_market.experiments import (  # noqa: E402
    make_assignments,
    make_candidate_visible_dataset,
    make_holdout_manifest,
)
from wbi_market.integrity import seal_tree, verify_tree  # noqa: E402
from wbi_market.metrics import (  # noqa: E402
    aggregate_evidence,
    build_next_iteration_plan,
    decide_gate,
)
from wbi_market.privacy import anonymize_feedback_rows  # noqa: E402
from wbi_market.specs import validate_experiment_spec, validate_feedback, validate_task  # noqa: E402
from wbi_market.stress import STRESS_CATEGORIES, expand_tasks  # noqa: E402


def load_spec() -> dict:
    return read_json(SKILL_ROOT / "assets" / "market" / "templates" / "experiment_spec.json")


def passing_quality_report(spec: dict) -> dict:
    payload = {
        "schema_version": "2.0",
        "spec_digest": object_sha256(spec),
        "valid": True,
        "status": "PASS",
        "blocking_reports": [],
        "reheat_reports": [],
    }
    payload["quality_audit_digest"] = object_sha256(payload)
    return payload


def base_task(task_id: str = "task-001", partition: str = "validation", protected: bool = False) -> dict:
    return {
        "task_id": task_id,
        "cluster_id": f"cluster-{task_id}",
        "partition": partition,
        "prompt": f"执行任务 {task_id}",
        "origin": "synthetic" if partition != "market_live" else "user_opt_in",
        "oracle": {"type": "deterministic", "expected": "success"},
        "protected": protected,
        "sensitivity": "public",
        **({"consent_ref": f"consent-{task_id}"} if partition == "market_live" else {}),
    }


def result_record(
    spec: dict,
    task_id: str,
    arm: dict,
    repetition: int,
    success: bool,
    score: float,
    *,
    protected: bool = False,
    cost: float = 0.02,
    latency: float = 1000.0,
    evidence_kind: str = "offline",
    hard_failures=None,
    digest_override=None,
) -> dict:
    return {
        "experiment_id": spec["experiment_id"],
        "run_id": f"run-{task_id}-{arm['id']}-{repetition}",
        "task_id": task_id,
        "partition": "incident_replay" if protected else "validation",
        "arm_id": arm["id"],
        "repetition": repetition,
        "status": "completed",
        "outcome": {
            "success": success,
            "score": score,
            "accepted": success,
            "human_edit_seconds": 0 if success else 60,
        },
        "usage": {
            "tokens": 1000,
            "cost_usd": cost,
            "latency_ms": latency,
            "tool_calls": 2,
        },
        "evidence_kind": evidence_kind,
        "protected": protected,
        "hard_failures": list(hard_failures or []),
        "artifact_digest": digest_override
        if digest_override is not None
        else (None if arm["kind"] == "no_skill" else arm["artifact_digest"]),
        "trace_digest": f"sha256:{object_sha256([task_id, arm['id'], repetition])}",
        "environment": {
            "model_snapshot": "model-pinned-demo",
            "runtime_version": "runtime-1.0.0",
            "tools": ["shell"],
            "permissions": ["read", "write-worktree"],
            "budget": {"tokens": 2000, "cost_usd": 0.1, "wall_seconds": 60},
            "system_digest": "sha256:" + "1" * 64,
            "dataset_digest": "sha256:" + "2" * 64,
        },
    }


def good_results(spec: dict, task_count: int = 24, protected_every: int = 5):
    rows = []
    for index in range(task_count):
        task_id = f"task-{index:04d}"
        protected = protected_every > 0 and index % protected_every == 0
        for repetition in range(1, spec["repetitions"] + 1):
            for arm in spec["arms"]:
                kind = arm["kind"]
                if kind == "candidate":
                    success, score, cost, latency = True, 0.94, 0.021, 1050
                elif kind == "baseline":
                    success, score, cost, latency = index % 8 != 0, 0.82, 0.020, 1000
                elif kind == "no_skill":
                    success, score, cost, latency = index % 5 != 0, 0.72, 0.018, 900
                elif kind == "competitor":
                    success, score, cost, latency = index % 10 != 0, 0.84, 0.023, 1100
                else:
                    success, score, cost, latency = index % 7 != 0, 0.79, 0.019, 950
                rows.append(
                    result_record(
                        spec,
                        task_id,
                        arm,
                        repetition,
                        success,
                        score,
                        protected=protected,
                        cost=cost,
                        latency=latency,
                    )
                )
    return rows


def market_feedback(
    spec: dict,
    count: int = 24,
    source: str = "external_acceptor",
    *,
    candidate_accepted: bool = True,
    baseline_accepted: bool = True,
):
    rows = []
    arm_map = {arm["id"]: arm for arm in spec["arms"]}
    for arm_id, accepted in (("candidate", candidate_accepted), ("baseline", baseline_accepted)):
        arm = arm_map[arm_id]
        for index in range(count):
            task_id = f"task-{index:04d}"
            row = {
                "event_id": f"event-{arm_id}-{index:04d}",
                "timestamp": "2026-07-29T00:00:00Z",
                "experiment_id": spec["experiment_id"],
                "run_id": f"run-{task_id}-{arm_id}-1",
                "task_id": task_id,
                "arm_id": arm_id,
                "artifact_digest": arm["artifact_digest"],
                "source": source,
                "completion": "complete" if accepted else "partial",
                "consent_ref": f"consent-{arm_id}-{index:04d}",
                "incident_severity": "none",
                "accepted": accepted,
                "would_reuse": accepted,
                "human_edit_seconds": 10 if arm_id == "candidate" else 20,
                "time_saved_minutes": 20 if arm_id == "candidate" else 10,
            }
            if source == "blind_canary":
                row["assignment_id"] = f"asg-{arm_id}-{index:04d}"
                row["randomized"] = True
            if source in {"external_acceptor", "micro_bounty"}:
                row["acceptance_ref"] = f"acceptance-{arm_id}-{index:04d}"
            if source == "micro_bounty":
                row["paid_value_usd"] = 10.0 if accepted else 0.0
            rows.append(row)
    return rows


class SkillStructureTests(unittest.TestCase):
    def test_doctor_passes(self):
        report = market_lab.doctor_skill(SKILL_ROOT)
        self.assertTrue(report["valid"], report)
        self.assertEqual(report["errors"], [])

    def test_skill_frontmatter_only_name_description(self):
        frontmatter = market_lab._parse_frontmatter(SKILL_ROOT / "SKILL.md")
        self.assertIn("name", frontmatter)
        self.assertIn("description", frontmatter)
        self.assertEqual(frontmatter["name"], "teleiosis")

    def test_market_lab_is_embedded_not_standalone(self):
        self.assertFalse((SKILL_ROOT / "scripts" / "market_lab.py").exists())
        self.assertFalse((SKILL_ROOT / "scripts" / "marketlab").exists())
        self.assertEqual((SKILL_ROOT / "VERSION").read_text(encoding="utf-8").strip(), "v0.0.0.3")
        self.assertEqual(market_package.__version__, "0.0.0.3")


class ContractTests(unittest.TestCase):
    def test_default_spec_valid(self):
        self.assertEqual(validate_experiment_spec(load_spec()), [])

    def test_no_skill_is_mandatory(self):
        spec = load_spec()
        spec["arms"] = [arm for arm in spec["arms"] if arm["kind"] != "no_skill"]
        errors = validate_experiment_spec(spec)
        self.assertTrue(any("no_skill" in item for item in errors))

    def test_market_live_requires_consent(self):
        task = base_task(partition="market_live")
        task.pop("consent_ref")
        errors = validate_task(task)
        self.assertTrue(any("consent_ref" in item for item in errors))

    def test_blind_canary_requires_assignment_and_randomization(self):
        spec = load_spec()
        row = market_feedback(spec, 1, source="blind_canary")[0]
        row.pop("assignment_id")
        row["randomized"] = False
        errors = validate_feedback(row, [arm["id"] for arm in spec["arms"]])
        self.assertTrue(any("assignment_id" in item for item in errors))
        self.assertTrue(any("randomized=true" in item for item in errors))


class StressAndAssignmentTests(unittest.TestCase):
    def test_all_six_stress_categories_deterministic(self):
        task = base_task()
        first = list(expand_tasks([task], list(STRESS_CATEGORIES), 1, 42, False))
        second = list(expand_tasks([task], list(STRESS_CATEGORIES), 1, 42, False))
        self.assertEqual(first, second)
        categories = {row["metadata"]["stress"]["category"] for row in first}
        self.assertEqual(categories, set(STRESS_CATEGORIES))
        self.assertEqual(len(first), 6)

    def test_full_factorial_assignments_and_blinding(self):
        spec = load_spec()
        tasks = [base_task("task-a"), base_task("task-b")]
        assignments, blind_map = make_assignments(spec, tasks)
        expected = len(tasks) * spec["repetitions"] * len(spec["arms"])
        self.assertEqual(len(assignments), expected)
        self.assertTrue(blind_map["controller_only"])
        arm_ids = {arm["id"] for arm in spec["arms"]}
        self.assertEqual(set(blind_map["mapping"].values()), arm_ids)
        self.assertFalse(any("arm_id" in row for row in assignments))
        grouped = {}
        for row in assignments:
            key = (row["task_id"], row["repetition"])
            grouped.setdefault(key, set()).add(row["condition_code"])
        self.assertTrue(all(len(codes) == len(spec["arms"]) for codes in grouped.values()))

    def test_holdout_content_not_disclosed(self):
        holdout = base_task("holdout-1", partition="sealed_holdout")
        validation = base_task("validation-1")
        manifest = make_holdout_manifest([holdout, validation])
        self.assertEqual(manifest["count"], 1)
        encoded = json.dumps(manifest, ensure_ascii=False)
        self.assertNotIn(holdout["prompt"], encoded)
        visible = list(make_candidate_visible_dataset([holdout, validation]))
        self.assertEqual([item["task_id"] for item in visible], ["validation-1"])


class PrivacyTests(unittest.TestCase):
    def test_feedback_anonymizer_redacts_and_hashes(self):
        row = market_feedback(load_spec(), 1, source="opt_in_user")[0]
        row.update(
            {
                "user_id": "user-123",
                "email": "person@example.com",
                "raw_prompt": "secret prompt",
                "notes": "token sk-abcdefghijklmnop and /Users/alice/private.txt",
            }
        )
        iterator, report = anonymize_feedback_rows([row], "a-secure-salt-value")
        output = list(iterator)[0]
        self.assertTrue(output["user_id"].startswith("anon-"))
        self.assertEqual(output["raw_prompt"], "[REDACTED_FIELD]")
        self.assertIn("[REDACTED_SECRET]", output["notes"])
        self.assertIn("[REDACTED_HOME]", output["notes"])
        self.assertGreaterEqual(report["sensitive_fields_removed"], 1)


class AggregateAndGateTests(unittest.TestCase):
    def test_gate_blocks_without_frozen_quality_audit(self):
        spec = load_spec()
        summary = aggregate_evidence(spec, good_results(spec), market_feedback(spec))
        gate = decide_gate(spec, summary)
        self.assertEqual(gate["decision"], "BLOCKED")
        self.assertIn("QUALITY_AUDIT_FAILED", {item["code"] for item in gate["reasons"]})

    def test_market_validated_candidate_is_evidence_ready(self):
        spec = load_spec()
        results = good_results(spec)
        feedback = market_feedback(spec, 24, source="external_acceptor")
        summary = aggregate_evidence(spec, results, feedback)
        self.assertEqual(summary["evidence_level"], 6)
        gate = decide_gate(spec, summary, passing_quality_report(spec))
        self.assertEqual(gate["decision"], "EVIDENCE_READY_FOR_TELEIOSIS", gate)
        plan = build_next_iteration_plan(spec, summary, gate)
        self.assertEqual(plan["actions"][0]["type"], "controlled-promotion")
        self.assertIsNotNone(plan["plan_digest"])

    def test_candidate_only_feedback_cannot_be_evidence_ready(self):
        spec = load_spec()
        feedback = [row for row in market_feedback(spec) if row["arm_id"] == "candidate"]
        summary = aggregate_evidence(spec, good_results(spec), feedback)
        gate = decide_gate(spec, summary, passing_quality_report(spec))
        self.assertEqual(gate["decision"], "REHEAT_REQUIRED")
        codes = {reason["code"] for reason in gate["reasons"]}
        self.assertIn("INSUFFICIENT_COMPARABLE_MARKET_EVENTS", codes)
        self.assertIn("MARKET_EVIDENCE_NOT_COMPARABLE", codes)

    def test_feedback_identity_mismatch_blocks(self):
        spec = load_spec()
        feedback = market_feedback(spec)
        feedback[0]["artifact_digest"] = "wrong-market-artifact"
        summary = aggregate_evidence(spec, good_results(spec), feedback)
        gate = decide_gate(spec, summary, passing_quality_report(spec))
        self.assertEqual(gate["decision"], "BLOCKED")
        self.assertGreater(summary["data_quality"]["feedback_identity_mismatch_count"], 0)

    def test_orphan_market_feedback_blocks(self):
        spec = load_spec()
        feedback = market_feedback(spec)
        feedback[0]["run_id"] = "run-does-not-exist"
        summary = aggregate_evidence(spec, good_results(spec), feedback)
        gate = decide_gate(spec, summary, passing_quality_report(spec))
        self.assertEqual(gate["decision"], "BLOCKED")
        self.assertGreater(summary["data_quality"]["feedback_orphan_run_count"], 0)

    def test_lower_market_acceptance_keeps_baseline(self):
        spec = load_spec()
        feedback = market_feedback(
            spec,
            candidate_accepted=False,
            baseline_accepted=True,
        )
        summary = aggregate_evidence(spec, good_results(spec), feedback)
        gate = decide_gate(spec, summary, passing_quality_report(spec))
        self.assertEqual(gate["decision"], "KEEP_BASELINE", gate)
        self.assertIn(
            "MARKET_ACCEPTANCE_DELTA_BELOW_TARGET",
            {reason["code"] for reason in gate["reasons"]},
        )

    def test_simulation_and_result_labels_cannot_create_market_evidence(self):
        spec = load_spec()
        results = good_results(spec)
        for row in results:
            row["evidence_kind"] = "economic"
        summary = aggregate_evidence(spec, results, None)
        self.assertLessEqual(summary["evidence_level"], 4)
        gate = decide_gate(spec, summary, passing_quality_report(spec))
        self.assertEqual(gate["decision"], "REHEAT_REQUIRED")
        codes = {reason["code"] for reason in gate["reasons"]}
        self.assertIn("EVIDENCE_LEVEL_BELOW_TARGET", codes)

    def test_identity_mismatch_blocks(self):
        spec = load_spec()
        results = good_results(spec)
        candidate = next(arm for arm in spec["arms"] if arm["kind"] == "candidate")
        for row in results:
            if row["arm_id"] == candidate["id"]:
                row["artifact_digest"] = "wrong-digest"
                break
        summary = aggregate_evidence(spec, results, market_feedback(spec))
        gate = decide_gate(spec, summary, passing_quality_report(spec))
        self.assertEqual(gate["decision"], "BLOCKED")

    def test_high_market_incident_blocks(self):
        spec = load_spec()
        feedback = market_feedback(spec)
        feedback[0]["source"] = "incident_report"
        feedback[0]["incident_severity"] = "high"
        summary = aggregate_evidence(spec, good_results(spec), feedback)
        gate = decide_gate(spec, summary, passing_quality_report(spec))
        self.assertEqual(gate["decision"], "BLOCKED")

    def test_protected_regression_reverts(self):
        spec = load_spec()
        results = good_results(spec)
        for row in results:
            if row["arm_id"] == "candidate" and row["protected"]:
                row["outcome"]["success"] = False
                row["outcome"]["score"] = 0.1
        summary = aggregate_evidence(spec, results, market_feedback(spec))
        gate = decide_gate(spec, summary, passing_quality_report(spec))
        self.assertEqual(gate["decision"], "REVERT")
        self.assertIn("PROTECTED_TASK_REGRESSION", {item["code"] for item in gate["reasons"]})

    def test_duplicate_results_fail_closed(self):
        spec = load_spec()
        rows = good_results(spec, task_count=1)
        rows.append(copy.deepcopy(rows[0]))
        with self.assertRaises(Exception):
            aggregate_evidence(spec, rows, None)

    def test_ten_thousand_task_streaming_summary(self):
        spec = load_spec()
        spec["repetitions"] = 1
        spec["evidence_target"] = "lab"
        spec["gates"]["min_paired_tasks"] = 100
        spec["gates"]["min_market_events_per_arm"] = 0

        def rows():
            for index in range(10000):
                task_id = f"scale-{index:05d}"
                for arm in spec["arms"]:
                    if arm["kind"] == "candidate":
                        success, score = True, 0.9
                    else:
                        success, score = index % 10 != 0, 0.75
                    yield result_record(spec, task_id, arm, 1, success, score)

        summary = aggregate_evidence(spec, rows(), None)
        self.assertEqual(summary["records_total"], 50000)
        self.assertEqual(summary["candidate_pairs"]["baseline"]["paired_tasks"], 10000)


class IntegrityTests(unittest.TestCase):
    def test_seal_detects_tamper(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "tree"
            root.mkdir()
            (root / "a.txt").write_text("alpha", encoding="utf-8")
            manifest_path = Path(directory) / "manifest.json"
            manifest = seal_tree(root, manifest_path)
            self.assertTrue(verify_tree(root, manifest)["valid"])
            (root / "a.txt").write_text("tampered", encoding="utf-8")
            report = verify_tree(root, manifest)
            self.assertFalse(report["valid"])
            self.assertEqual(report["changed"], ["a.txt"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
