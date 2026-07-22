#!/usr/bin/env python3
"""Standard-library tests for verifier v2.1 Product-Design-aligned payload."""

from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True


PAYLOAD = Path(__file__).resolve().parent.parent


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


gallery = load_module("verifier_make_gallery_v21", PAYLOAD / "scripts/make_gallery.py")
initializer = load_module("verifier_init_v21", PAYLOAD / "scripts/init_acceptance_run.py")
finalizer = load_module("verifier_finalize_v21", PAYLOAD / "scripts/finalize_acceptance_run.py")
ingester = load_module("verifier_ingest_taskpack_v21", PAYLOAD / "scripts/ingest_taskpack.py")
packager = load_module(
    "verifier_package_review_taskpack_v21", PAYLOAD / "scripts/package_review_taskpack.py"
)
validator = load_module("verifier_validate_v21", PAYLOAD / "scripts/validate_pack.py")


TINY_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


def prepare_valid_pass(root: Path, *, ai: bool = False) -> Path:
    run_dir = initializer.initialize(
        root,
        "EEI",
        "run-001",
        decision_scope="developer_check",
        target_path="apps/eei",
    )
    manifest_path = run_dir / "RUN_MANIFEST.yaml"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["run"].update(
        {
            "ended_at": manifest["run"]["started_at"],
            "verifier_identity": "fresh-verifier-test",
            "independence_evidence": "separate test context",
            "profile": "quick",
            "risk_level": "low",
            "risk_triggers": ["local isolated developer check"],
        }
    )
    manifest["scope"].update(
        {
            "acceptance_closure": ["apps/eei", "packages/shared-auth"],
            "closure_evidence": ["raw-results/scope.txt"],
            "included_paths": ["apps/eei", "packages/shared-auth"],
            "excluded_projects": ["PFI"],
        }
    )
    manifest["subject"].update(
        {
            "repository": "https://example.invalid/repo.git",
            "repository_root": "/tmp/repo",
            "branch": "main",
            "git_head": "a" * 40,
            "git_status": "clean",
            "source_dirty": False,
            "signature_verification": {
                "status": "NOT_RUN",
                "reason": "signature verification is not required for this developer check",
                "evidence_paths": [],
            },
        }
    )
    manifest["environment"].update(
        {"class": "local", "os_arch": "linux-x86_64", "entrypoints": ["http://127.0.0.1:3000"]}
    )
    manifest["evidence"]["redaction_reviewed"] = True
    manifest["verdict"].update(
        {
            "value": "PASS",
            "action": "NONE",
            "reason": "核心用户任务和必要门均通过",
            "owner_next_action": "接受本次开发检查结果",
        }
    )

    evidence_dir = run_dir / "raw-results"
    (evidence_dir / "scope.txt").write_text("scope resolved\n", encoding="utf-8")
    gates = [
        ("G-001", "subject_identity", "PASS"),
        ("G-002", "build_start_health", "PASS"),
        ("G-003", "core_journey", "PASS"),
        ("G-004", "data_or_output", "PASS"),
        ("G-005", "changed_scope_regression", "PASS"),
    ]
    results = []
    for test_id, gate, status in gates:
        filename = f"{test_id}.json"
        (evidence_dir / filename).write_text(
            json.dumps({"test_id": test_id, "status": status}) + "\n",
            encoding="utf-8",
        )
        results.append(
            {
                "test_id": test_id,
                "gate": gate,
                "status": status,
                "blocking": True,
                "expected": f"{gate} is satisfied",
                "actual": f"{gate} satisfied",
                "attempts": 1,
                "reason": "",
                "evidence_paths": [f"raw-results/{filename}"],
            }
        )
    results.append(
        {
            "test_id": "G-006",
            "gate": "safety_security",
            "status": "NOT_APPLICABLE",
            "blocking": True,
            "expected": "安全维度按风险适用",
            "actual": "",
            "attempts": 0,
            "reason": "纯本地无网络、无身份、无数据写入的隔离检查",
            "evidence_paths": [],
        }
    )

    if ai:
        trial_records = []
        for trial_number in range(1, 4):
            reset_name = f"AI-001__trial-{trial_number}__reset.json"
            outcome_name = f"AI-001__trial-{trial_number}__outcome.json"
            trace_name = f"AI-001__trial-{trial_number}__trace.json"
            (evidence_dir / reset_name).write_text(
                json.dumps({"trial": trial_number, "state": "clean"}) + "\n",
                encoding="utf-8",
            )
            (evidence_dir / outcome_name).write_text(
                json.dumps({"trial": trial_number, "world_state": "correct"}) + "\n",
                encoding="utf-8",
            )
            (evidence_dir / trace_name).write_text(
                json.dumps({"trial": trial_number, "trace": "world state verified"}) + "\n",
                encoding="utf-8",
            )
            trial_records.append(
                {
                    "trial_id": f"AI-001-T{trial_number}",
                    "context_id": f"fresh-context-{trial_number}",
                    "task_slice": "core-task",
                    "status": "PASS",
                    "outcome": "correct external world state",
                    "reset_evidence_path": f"raw-results/{reset_name}",
                    "outcome_evidence_path": f"raw-results/{outcome_name}",
                    "trace_path": f"raw-results/{trace_name}",
                    "cost": 0.01,
                    "latency_ms": 120 + trial_number,
                }
            )
        for filename, value in (
            ("AI-001.json", {"trials": ["PASS", "PASS", "PASS"]}),
            ("AI-cost.json", {"cost": 0.03, "latency_ms": [121, 122, 123]}),
            ("AI-safety.json", {"prompt_injection": "PASS", "tool_permissions": "PASS"}),
            ("AI-evaluator.json", {"grader": "deterministic world-state oracle", "independent": True}),
        ):
            (evidence_dir / filename).write_text(json.dumps(value) + "\n", encoding="utf-8")
        manifest["ai_system"].update(
            {
                "applicable": True,
                "model_provider": "test-provider",
                "model_id": "test-model",
                "model_snapshot": "snapshot-1",
                "model_snapshot_reason": "",
                "prompt_or_policy_hash": "b" * 64,
                "toolset_or_harness_hash": "c" * 64,
                "retrieval_snapshot": "none",
                "trial_count": 3,
                "task_slices": ["core-task"],
                "trial_records": trial_records,
                "success_threshold": 1.0,
                "observed_pass_rate": 1.0,
                "outcome_grader": "deterministic world-state assertion",
                "judge_calibration": "not-applicable; deterministic grader",
                "evaluator_independence": {
                    "primary_grader_type": "deterministic",
                    "generator_is_sole_judge": False,
                    "cross_model_review": False,
                    "blind_evaluation": False,
                    "independent_evaluator_ids": ["deterministic-world-state-oracle-v1"],
                    "disagreement_policy": "deterministic invariant wins; ambiguous evidence blocks",
                    "evidence_paths": ["raw-results/AI-evaluator.json"],
                },
                "baseline_reference": "baseline-1",
                "baseline_reason_if_absent": "",
                "safety_checks": ["prompt injection", "tool permissions"],
                "safety_gate_status": "PASS",
                "safety_evidence_paths": ["raw-results/AI-safety.json"],
                "cost_latency_evidence_paths": ["raw-results/AI-cost.json"],
                "trace_paths": [],
            }
        )
        results.append(
            {
                "test_id": "AI-001",
                "gate": "ai_eval",
                "status": "PASS",
                "blocking": True,
                "expected": "three trials reach the correct world state",
                "actual": "P/P/P and world state verified",
                "attempts": 3,
                "reason": "",
                "evidence_paths": ["raw-results/AI-001.json"],
            }
        )

    manifest["results"] = results
    (evidence_dir / "change-impact.json").write_text(
        json.dumps({"change_id": "current-subject", "paths": ["apps/eei"]}) + "\n",
        encoding="utf-8",
    )
    manifest["traceability"].update({"status": "PASS", "reason": ""})
    linked_test_ids = ["G-003", "G-004", "G-005"]
    if ai:
        linked_test_ids.append("AI-001")
    traceability = {
        "_format_note": "Strict JSON test fixture",
        "schema_version": "2.1",
        "target_project_name": "EEI",
        "subject_identity": "a" * 40,
        "taskpack_digest_sha256": "",
        "rows": [
            {
                "requirement_id": "REQ-LOCAL-001",
                "acceptance_id": "AC-LOCAL-001",
                "oracle_id": "OR-LOCAL-001",
                "task_ids": [],
                "test_ids": linked_test_ids,
                "evidence_paths": ["raw-results/G-003.json", "raw-results/G-004.json"],
                "blocking": True,
                "status": "PASS",
                "reason": "",
            }
        ],
        "change_impact": [
            {
                "change_id": "current-subject",
                "changed_paths": ["apps/eei"],
                "impacted_acceptance_ids": ["AC-LOCAL-001"],
                "non_impact_reason": "",
                "test_ids": linked_test_ids,
                "evidence_paths": ["raw-results/change-impact.json"],
            }
        ],
    }
    (run_dir / "TRACEABILITY_MATRIX.json").write_text(
        json.dumps(traceability, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (run_dir / "VERDICT.md").write_text(
        """ACTION: NONE

# 验收结论 — EEI aaaaaaaaaaaa

## 你只需要先看这里

- 本次验收：EEI（apps/eei）
- 不可变版本：aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
- 结论适用范围：开发检查
- 结论：本范围检查通过
- 一句话原因：核心用户任务和必要门均通过
- 你现在只需要做：接受本次开发检查结果
- Evidence root：见 FINAL_DECISION.json
- Verdict：PASS

---

## 技术记录

所有原始证据见 RUN_MANIFEST.yaml 与 raw-results/。
""",
        encoding="utf-8",
    )
    return run_dir


def prepare_valid_release_candidate(root: Path) -> Path:
    run_dir = prepare_valid_pass(root)
    manifest_path = run_dir / "RUN_MANIFEST.yaml"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    evidence_dir = run_dir / "raw-results"
    artifact_sha = "d" * 64

    evidence_payloads = {
        "source-to-artifact.json": {"git_head": "a" * 40, "artifact_sha256": artifact_sha},
        "capacity.json": {"status": "PASS", "capacity": "within objective"},
        "rollback.json": {"status": "PASS", "method": "redeploy previous immutable artifact"},
        "operational.json": {"status": "PASS", "alerts": "tested", "runbook": "available"},
    }
    for filename, value in evidence_payloads.items():
        (evidence_dir / filename).write_text(json.dumps(value) + "\n", encoding="utf-8")

    manifest["subject"].update(
        {
            "build_id": "build-42",
            "artifact_path": "artifacts/eei.tar.gz",
            "artifact_sha256": artifact_sha,
            "source_to_artifact_mapping_evidence": ["raw-results/source-to-artifact.json"],
        }
    )
    manifest["baseline"].update(
        {
            "reference": "",
            "acceptance_pack_hash": "",
            "comparison_status": "NOT_RUN",
            "reason_if_absent": "first accepted release candidate; no prior acceptance pack",
            "evidence_paths": [],
        }
    )
    manifest["release"].update(
        {
            "decision_scope": "release_candidate",
            "intent": "internal",
            "strategy": "not-applicable",
            "candidate_version": "build-42",
            "candidate_identity": artifact_sha,
            "health_signals": ["error rate", "p95 latency"],
            "business_invariants": ["core task result remains correct"],
            "abort_conditions": ["core task failure", "data invariant violation"],
            "rollback_or_rollforward": {
                "method": "redeploy previous immutable artifact",
                "tested": True,
                "status": "PASS",
                "reason": "",
                "evidence_paths": ["raw-results/rollback.json"],
            },
        }
    )
    manifest["operations"].update(
        {
            "owner_or_oncall": "release-owner",
            "runbook_paths": ["docs/runbook.md"],
            "dashboard_or_query_refs": ["dashboard://eei-release"],
            "alert_tests": ["synthetic alert routing test PASS"],
            "slo_or_health_objectives": ["core task success >= objective"],
            "capacity_evidence_paths": ["raw-results/capacity.json"],
            "backup_restore": {
                "status": "NOT_APPLICABLE",
                "reason": "candidate has no persistent data or migration",
                "evidence_paths": [],
            },
        }
    )
    for test_id, gate, filename in (
        ("G-007", "operational_readiness", "operational.json"),
        ("G-008", "rollback_or_rollforward", "rollback.json"),
    ):
        manifest["results"].append(
            {
                "test_id": test_id,
                "gate": gate,
                "status": "PASS",
                "blocking": True,
                "expected": f"{gate} passes",
                "actual": f"{gate} passed",
                "attempts": 1,
                "reason": "",
                "evidence_paths": [f"raw-results/{filename}"],
            }
        )
    traceability_path = run_dir / "TRACEABILITY_MATRIX.json"
    traceability = json.loads(traceability_path.read_text(encoding="utf-8"))
    traceability["subject_identity"] = artifact_sha
    traceability_path.write_text(
        json.dumps(traceability, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (run_dir / "VERDICT.md").write_text(
        f"""ACTION: NONE

# 验收结论 — EEI build-42

## 你只需要先看这里

- 本次验收：EEI（apps/eei）
- 不可变版本：{artifact_sha}
- 结论适用范围：release_candidate
- 结论：候选可进入受控发布
- 一句话原因：身份、核心任务、运营和恢复门均通过
- 你现在只需要做：按发布计划进入受控发布
- Evidence root：见 FINAL_DECISION.json
- Verdict：PASS

---

## 技术记录

所有原始证据见 RUN_MANIFEST.yaml 与 raw-results/。
""",
        encoding="utf-8",
    )
    return run_dir


def make_product_design_taskpack(root: Path) -> Path:
    source = root / "product-design-taskpack"
    source.mkdir()
    contents = {
        "MANIFEST.yaml": 'version: "1.4.0"\nfiles: 7\n',
        "PURSUE_GOAL.md": "# Ship a verifiably correct EEI outcome\n",
        "DECISION_PRD.md": "# PRD\nREQ-001: user completes the core task.\n",
        "TECHNICAL_OPERATIONS_DESIGN.md": "# Technical and operations design\n",
        "ROADMAP.md": "# Roadmap\nStage 1 / Phase 1 / Task T-001\n",
        "TASK_GRAPH.yaml": "tasks:\n  - id: T-001\n    acceptance_ids: [AC-001]\n",
        "ACCEPTANCE_CONTRACT.yaml": (
            "acceptance:\n"
            "  - id: AC-001\n"
            "    requirement_id: REQ-001\n"
            "    oracle_id: OR-001\n"
            "    threshold: core journey and persisted output pass\n"
        ),
    }
    for name, content in contents.items():
        (source / name).write_text(content, encoding="utf-8")
    return source


def prepare_authoritative_taskpack_pass(root: Path) -> Path:
    run_dir = prepare_valid_pass(root)
    source = make_product_design_taskpack(root)
    result = ingester.ingest(
        source,
        run_dir,
        authoritative=True,
        authorization_reference="owner-approved exact Product-Design-Taskpack",
    )
    manifest_path = run_dir / "RUN_MANIFEST.yaml"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert result["acceptance_ids"] == ["AC-001"]
    assert result["task_ids"] == ["T-001"]
    evidence_dir = run_dir / "raw-results"
    (evidence_dir / "taskpack-compatibility.json").write_text(
        json.dumps({"target": "EEI", "acceptance_ids": ["AC-001"], "task_ids": ["T-001"], "status": "PASS"}) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "taskpack-drift-review.json").write_text(
        json.dumps({"subject": "a" * 40, "drift": [], "status": "PASS"}) + "\n",
        encoding="utf-8",
    )
    manifest["taskpack"].update(
        {
            "compatibility_status": "PASS",
            "compatibility_reason": "",
            "drift_status": "PASS",
            "drift_items": [],
            "compatibility_evidence_paths": ["raw-results/taskpack-compatibility.json"],
            "drift_evidence_paths": ["raw-results/taskpack-drift-review.json"],
            "evidence_paths": [
                "raw-results/taskpack-lock.json",
                "raw-results/taskpack-compatibility.json",
                "raw-results/taskpack-drift-review.json",
            ],
        }
    )
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    trace_path = run_dir / "TRACEABILITY_MATRIX.json"
    trace = json.loads(trace_path.read_text(encoding="utf-8"))
    trace["taskpack_digest_sha256"] = result["pack_digest_sha256"]
    trace["rows"] = [
        {
            "requirement_id": "REQ-001",
            "acceptance_id": "AC-001",
            "oracle_id": "OR-001",
            "task_ids": ["T-001"],
            "test_ids": ["G-003", "G-004", "G-005"],
            "evidence_paths": ["raw-results/G-003.json", "raw-results/G-004.json"],
            "blocking": True,
            "status": "PASS",
            "reason": "",
        }
    ]
    trace["change_impact"] = [
        {
            "change_id": "current-subject",
            "changed_paths": ["apps/eei"],
            "impacted_acceptance_ids": ["AC-001"],
            "non_impact_reason": "",
            "test_ids": ["G-003", "G-004", "G-005"],
            "evidence_paths": ["raw-results/change-impact.json"],
        }
    ]
    trace_path.write_text(
        json.dumps(trace, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return run_dir


class GalleryTests(unittest.TestCase):
    def test_gallery_embeds_and_escapes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "screenshots").mkdir()
            (root / "screenshots/ref.png").write_bytes(TINY_PNG)
            (root / "screenshots/actual.png").write_bytes(TINY_PNG)
            csv_path = root / "pairs.csv"
            csv_path.write_text(
                "id,label,reference,actual,status,severity,note\n"
                '<script>alert(1)</script>,"<script>alert(1)</script>",screenshots/ref.png,screenshots/actual.png,PASS,L2,ok\n',
                encoding="utf-8",
            )
            output = root / "gallery.html"
            self.assertEqual(gallery.generate_gallery(csv_path, output, 1024 * 1024), 1)
            document = output.read_text(encoding="utf-8")
            self.assertIn("data:image/png;base64,", document)
            self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", document)
            self.assertNotIn("<script>", document)
            self.assertIn("Content-Security-Policy", document)

    def test_path_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            outside = root.parent / "outside-verifier-test.png"
            outside.write_bytes(TINY_PNG)
            try:
                csv_path = root / "pairs.csv"
                csv_path.write_text(
                    f"id,label,reference,actual,status,severity,note\nH-001,x,,../{outside.name},PASS,,\n",
                    encoding="utf-8",
                )
                with self.assertRaises(gallery.GalleryError):
                    gallery.generate_gallery(csv_path, root / "gallery.html", 1024 * 1024)
            finally:
                outside.unlink(missing_ok=True)


class InitializerTests(unittest.TestCase):
    def test_initializer_creates_complete_run_and_supports_unicode_project(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            destination = initializer.initialize(root, "验收项目", "run-001")
            self.assertTrue(destination.is_dir())
            for name in (
                "VERDICT.md",
                "RUN_MANIFEST.yaml",
                "RELEASE_ASSURANCE.md",
                "AI_EVAL_MATRIX.md",
                "TRACEABILITY_MATRIX.json",
            ):
                self.assertTrue((destination / name).is_file())
            manifest = json.loads((destination / "RUN_MANIFEST.yaml").read_text(encoding="utf-8"))
            self.assertEqual(manifest["scope"]["target_project_name"], "验收项目")
            self.assertEqual(manifest["release"]["decision_scope"], "release_candidate")
            with self.assertRaises(FileExistsError):
                initializer.initialize(root, "验收项目", "run-001")


class FinalizerTests(unittest.TestCase):
    def test_valid_pass_can_be_finalized_verified_and_tamper_is_detected(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = prepare_valid_pass(Path(temporary))
            decision = finalizer.finalize(run_dir)
            self.assertEqual(decision["verdict"], "PASS")
            self.assertEqual(finalizer.verify(run_dir)["evidence_root_sha256"], decision["evidence_root_sha256"])
            (run_dir / "raw-results/G-003.json").write_text("tampered\n", encoding="utf-8")
            with self.assertRaises(finalizer.RunValidationError):
                finalizer.verify(run_dir)

    def test_tampered_decision_and_checksum_list_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = prepare_valid_pass(Path(temporary))
            finalizer.finalize(run_dir)
            decision_path = run_dir / "FINAL_DECISION.json"
            decision = json.loads(decision_path.read_text(encoding="utf-8"))
            decision["owner_next_action"] = "tampered"
            decision_path.write_text(json.dumps(decision, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            with self.assertRaises(finalizer.RunValidationError):
                finalizer.verify(run_dir)

        with tempfile.TemporaryDirectory() as temporary:
            run_dir = prepare_valid_pass(Path(temporary))
            finalizer.finalize(run_dir)
            sums_path = run_dir / "SHA256SUMS.txt"
            sums_path.write_text(sums_path.read_text(encoding="utf-8") + "0" * 64 + "  ghost\n", encoding="utf-8")
            with self.assertRaises(finalizer.RunValidationError):
                finalizer.verify(run_dir)

    def test_symlink_run_directory_is_rejected(self):
        if not hasattr(Path, "symlink_to"):
            self.skipTest("symlink unsupported")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_dir = prepare_valid_pass(root)
            link = root / "run-link"
            try:
                link.symlink_to(run_dir, target_is_directory=True)
            except OSError as error:
                self.skipTest(f"symlink unavailable: {error}")
            with self.assertRaises(finalizer.RunValidationError):
                finalizer.finalize(link)

    def test_positive_verdict_without_identity_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = prepare_valid_pass(Path(temporary))
            manifest_path = run_dir / "RUN_MANIFEST.yaml"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["subject"]["git_head"] = ""
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            _, errors = finalizer.validate_run(run_dir)
            self.assertTrue(any("identity" in error for error in errors), errors)

    def test_pass_with_blocking_not_run_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = prepare_valid_pass(Path(temporary))
            manifest_path = run_dir / "RUN_MANIFEST.yaml"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["results"][2].update(
                {"status": "NOT_RUN", "actual": "", "attempts": 0, "reason": "browser unavailable", "evidence_paths": []}
            )
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            _, errors = finalizer.validate_run(run_dir)
            self.assertTrue(any("PASS cannot contain blocking" in error for error in errors), errors)

    def test_ai_positive_verdict_requires_multiple_trials(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = prepare_valid_pass(Path(temporary), ai=True)
            manifest_path = run_dir / "RUN_MANIFEST.yaml"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["ai_system"]["trial_count"] = 1
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            _, errors = finalizer.validate_run(run_dir)
            self.assertTrue(any("trial_count >= 3" in error for error in errors), errors)

    def test_non_waivable_finding_cannot_be_risk_accepted(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = prepare_valid_pass(Path(temporary))
            manifest_path = run_dir / "RUN_MANIFEST.yaml"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["verdict"].update(
                {
                    "value": "PASS_WITH_RISKS",
                    "action": "ACT",
                    "reason": "owner proposes risk acceptance",
                    "owner_next_action": "accept risk",
                }
            )
            manifest["findings"] = [
                {
                    "id": "SEC-001",
                    "type": "PRODUCT_DEFECT",
                    "severity": "L1",
                    "status": "WAIVED",
                    "category": "AUTHZ_BYPASS",
                    "non_waivable": True,
                    "evidence_paths": ["raw-results/G-003.json"],
                }
            ]
            manifest["waivers"] = [
                {
                    "id": "W-001",
                    "finding_id": "SEC-001",
                    "owner": "owner",
                    "reason": "temporary",
                    "compensating_controls": ["manual review"],
                    "residual_risk": "auth bypass remains",
                    "applies_to_identity": "a" * 40,
                    "expires_at": "2026-07-20T00:00:00Z",
                    "retest_plan": "retest after fix",
                }
            ]
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            (run_dir / "VERDICT.md").write_text(
                "ACTION: ACT\n\n# 验收结论 — EEI\n\n## 你只需要先看这里\n\n- 结论：带风险\n- Verdict：PASS_WITH_RISKS\n\n---\n",
                encoding="utf-8",
            )
            _, errors = finalizer.validate_run(run_dir)
            self.assertTrue(any("non-waivable" in error for error in errors), errors)


    def test_valid_release_candidate_can_be_finalized(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = prepare_valid_release_candidate(Path(temporary))
            decision = finalizer.finalize(run_dir)
            self.assertEqual(decision["decision_scope"], "release_candidate")
            self.assertEqual(decision["candidate_identity"], "d" * 64)

    def test_release_candidate_identity_cannot_be_mutable_build_id(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = prepare_valid_release_candidate(Path(temporary))
            manifest_path = run_dir / "RUN_MANIFEST.yaml"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["release"]["candidate_identity"] = "build-42"
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            _, errors = finalizer.validate_run(run_dir)
            self.assertTrue(any("immutable bytes" in error or "not bound" in error for error in errors), errors)

    def test_baseline_reference_requires_acceptance_pack_hash(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = prepare_valid_release_candidate(Path(temporary))
            manifest_path = run_dir / "RUN_MANIFEST.yaml"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            (run_dir / "raw-results/baseline.json").write_text('{"status":"PASS"}\n', encoding="utf-8")
            manifest["baseline"].update(
                {
                    "reference": "release-41",
                    "acceptance_pack_hash": "",
                    "comparison_status": "PASS",
                    "reason_if_absent": "",
                    "evidence_paths": ["raw-results/baseline.json"],
                }
            )
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            _, errors = finalizer.validate_run(run_dir)
            self.assertTrue(any("acceptance_pack_hash" in error for error in errors), errors)

    def test_waived_finding_requires_exactly_one_matching_waiver(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = prepare_valid_pass(Path(temporary))
            manifest_path = run_dir / "RUN_MANIFEST.yaml"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["verdict"].update(
                {
                    "value": "PASS_WITH_RISKS",
                    "action": "ACT",
                    "reason": "low residual risk",
                    "owner_next_action": "accept the time-bounded residual risk",
                }
            )
            manifest["findings"] = [
                {
                    "id": "UX-001",
                    "type": "PRODUCT_DEFECT",
                    "severity": "L2",
                    "status": "WAIVED",
                    "category": "LOCAL_USABILITY",
                    "non_waivable": False,
                    "evidence_paths": ["raw-results/G-003.json"],
                }
            ]
            manifest["waivers"] = []
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            (run_dir / "VERDICT.md").write_text(
                "ACTION: ACT\n\n# 验收结论 — EEI\n\n## 你只需要先看这里\n\n- Verdict：PASS_WITH_RISKS\n\n---\n",
                encoding="utf-8",
            )
            _, errors = finalizer.validate_run(run_dir)
            self.assertTrue(any("exactly one matching waiver" in error for error in errors), errors)

    def test_critical_independent_passes_require_distinct_contexts_and_same_subject(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = prepare_valid_pass(Path(temporary))
            manifest_path = run_dir / "RUN_MANIFEST.yaml"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            (run_dir / "raw-results/critical-pass-1.json").write_text('{"pass":1}\n', encoding="utf-8")
            (run_dir / "raw-results/critical-pass-2.json").write_text('{"pass":2}\n', encoding="utf-8")
            (run_dir / "raw-results/G-006.json").write_text('{"status":"PASS"}\n', encoding="utf-8")
            manifest["run"].update(
                {
                    "risk_level": "critical",
                    "profile": "deep",
                    "independent_passes": 2,
                    "independent_pass_records": [
                        {
                            "verifier_identity": "fresh-verifier-test",
                            "context_id": "same-context",
                            "verdict": "PASS",
                            "subject_identity": "a" * 40,
                            "evidence_root_sha256": "1" * 64,
                            "evidence_paths": ["raw-results/critical-pass-1.json"],
                        },
                        {
                            "verifier_identity": "second-verifier",
                            "context_id": "same-context",
                            "verdict": "PASS",
                            "subject_identity": "b" * 40,
                            "evidence_root_sha256": "2" * 64,
                            "evidence_paths": ["raw-results/critical-pass-2.json"],
                        },
                    ],
                }
            )
            manifest["results"][-1].update(
                {
                    "status": "PASS",
                    "actual": "safety gate passed",
                    "attempts": 1,
                    "reason": "",
                    "evidence_paths": ["raw-results/G-006.json"],
                }
            )
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            _, errors = finalizer.validate_run(run_dir)
            self.assertTrue(any("distinct context IDs" in error for error in errors), errors)
            self.assertTrue(any("does not match acceptance subject" in error for error in errors), errors)

    def test_ai_observed_rate_and_contexts_are_derived_from_trials(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = prepare_valid_pass(Path(temporary), ai=True)
            manifest_path = run_dir / "RUN_MANIFEST.yaml"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["ai_system"]["observed_pass_rate"] = 0.5
            manifest["ai_system"]["trial_records"][1]["context_id"] = manifest["ai_system"]["trial_records"][0]["context_id"]
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            _, errors = finalizer.validate_run(run_dir)
            self.assertTrue(any("observed_pass_rate does not match" in error for error in errors), errors)
            self.assertTrue(any("duplicate AI context_id" in error for error in errors), errors)


class TaskpackAlignmentTests(unittest.TestCase):
    def test_authoritative_taskpack_traceability_and_attestation_finalize(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = prepare_authoritative_taskpack_pass(Path(temporary))
            decision = finalizer.finalize(run_dir)
            self.assertTrue(decision["taskpack_detected"])
            self.assertEqual(decision["traceability_status"], "PASS")
            self.assertEqual(decision["traceability_declared_acceptance_count"], 1)
            attestation = json.loads(
                (run_dir / "ACCEPTANCE_ATTESTATION.intoto.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                attestation["predicateType"],
                "https://in-toto.io/attestation/test-result/v0.1",
            )
            configuration_names = {
                item["name"] for item in attestation["predicate"]["configuration"]
            }
            self.assertIn("taskpack/acceptance_contract.yaml", configuration_names)
            self.assertIn("taskpack/TASKPACK_SOURCE_SNAPSHOT.zip", configuration_names)
            self.assertIn("raw-results/taskpack-lock.json", configuration_names)
            self.assertIn("TRACEABILITY_MATRIX.json", configuration_names)
            self.assertEqual(
                decision["taskpack_contract_digest_sha256"],
                json.loads((run_dir / "RUN_MANIFEST.yaml").read_text(encoding="utf-8"))["taskpack"]["contract_digest_sha256"],
            )
            self.assertEqual(
                decision["taskpack_source_snapshot_sha256"],
                json.loads((run_dir / "RUN_MANIFEST.yaml").read_text(encoding="utf-8"))["taskpack"]["source_snapshot_sha256"],
            )
            self.assertEqual(decision["taskpack_source_file_count"], 7)

    def test_ancillary_taskpack_file_changes_full_pack_but_not_contract_digest(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            results = []
            for label, schema_value in (("one", "v1"), ("two", "v2")):
                workspace = root / label
                workspace.mkdir()
                run_dir = initializer.initialize(
                    workspace,
                    "EEI",
                    f"ancillary-{label}",
                    decision_scope="developer_check",
                    target_path="apps/eei",
                )
                source = make_product_design_taskpack(workspace)
                schema = source / "schemas/contract.json"
                schema.parent.mkdir()
                schema.write_text(
                    json.dumps({"schema": schema_value}, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                result = ingester.ingest(
                    source,
                    run_dir,
                    authoritative=True,
                    authorization_reference="owner-approved",
                )
                results.append((run_dir, result))

            first_run, first = results[0]
            second_run, second = results[1]
            self.assertNotEqual(first["pack_digest_sha256"], second["pack_digest_sha256"])
            self.assertEqual(first["contract_digest_sha256"], second["contract_digest_sha256"])
            self.assertEqual(first["source_file_count"], 8)
            self.assertEqual(second["source_file_count"], 8)
            self.assertTrue((first_run / "taskpack/TASKPACK_SOURCE_SNAPSHOT.zip").is_file())
            self.assertTrue((second_run / "taskpack/TASKPACK_SOURCE_SNAPSHOT.zip").is_file())

    def test_taskpack_source_snapshot_tamper_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = prepare_authoritative_taskpack_pass(Path(temporary))
            snapshot = run_dir / "taskpack/TASKPACK_SOURCE_SNAPSHOT.zip"
            snapshot.write_bytes(snapshot.read_bytes() + b"tamper")
            _, errors = finalizer.validate_run(run_dir)
            self.assertTrue(any("source snapshot digest mismatch" in error for error in errors), errors)

    def test_taskpack_lock_inventory_tamper_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = prepare_authoritative_taskpack_pass(Path(temporary))
            lock_path = run_dir / "raw-results/taskpack-lock.json"
            lock = json.loads(lock_path.read_text(encoding="utf-8"))
            lock["source_files"][0]["sha256"] = "f" * 64
            lock_path.write_text(
                json.dumps(lock, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            _, errors = finalizer.validate_run(run_dir)
            self.assertTrue(
                any(
                    "pack digest does not match source_files" in error
                    or "source snapshot inventory mismatch" in error
                    for error in errors
                ),
                errors,
            )

    def test_taskpack_drift_is_non_positive(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = prepare_authoritative_taskpack_pass(Path(temporary))
            drift_evidence = run_dir / "raw-results/taskpack-drift.json"
            drift_evidence.write_text('{"oracle":"relaxed"}\n', encoding="utf-8")
            manifest_path = run_dir / "RUN_MANIFEST.yaml"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["taskpack"].update(
                {
                    "drift_status": "FAIL",
                    "drift_items": [
                        {
                            "id": "DRIFT-001",
                            "type": "ACCEPTANCE_ORACLE_DRIFT",
                            "before": "AC-001 requires persisted output",
                            "after": "implementation checks HTTP 200 only",
                            "impact": "false positive acceptance is possible",
                            "evidence_paths": ["raw-results/taskpack-drift.json"],
                        }
                    ],
                }
            )
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            _, errors = finalizer.validate_run(run_dir)
            self.assertTrue(any("drift_status=PASS" in error for error in errors), errors)
            self.assertTrue(any("drift_items" in error for error in errors), errors)

    def test_traceability_must_exactly_cover_authoritative_acceptance_ids(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = prepare_authoritative_taskpack_pass(Path(temporary))
            manifest_path = run_dir / "RUN_MANIFEST.yaml"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["taskpack"]["acceptance_ids"].append("AC-002")
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            _, errors = finalizer.validate_run(run_dir)
            self.assertTrue(any("does not exactly cover" in error for error in errors), errors)

    def test_authorized_taskpack_digest_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = prepare_authoritative_taskpack_pass(Path(temporary))
            manifest_path = run_dir / "RUN_MANIFEST.yaml"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["taskpack"]["authorized_pack_digest_sha256"] = "f" * 64
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            _, errors = finalizer.validate_run(run_dir)
            self.assertTrue(any("authorized pack digest" in error for error in errors), errors)

    def test_attestation_tamper_is_detected(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = prepare_authoritative_taskpack_pass(Path(temporary))
            finalizer.finalize(run_dir)
            path = run_dir / "ACCEPTANCE_ATTESTATION.intoto.json"
            value = json.loads(path.read_text(encoding="utf-8"))
            value["predicate"]["result"] = "FAILED"
            path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
            with self.assertRaises(finalizer.RunValidationError):
                finalizer.verify(run_dir)

    def test_dirty_positive_run_requires_hashed_snapshot(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = prepare_valid_pass(Path(temporary))
            manifest_path = run_dir / "RUN_MANIFEST.yaml"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["subject"]["source_dirty"] = True
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            _, errors = finalizer.validate_run(run_dir)
            self.assertTrue(any("dirty source" in error for error in errors), errors)

    def test_ingester_rejects_ambiguous_role(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_dir = initializer.initialize(
                root, "EEI", "ambiguous", decision_scope="developer_check", target_path="apps/eei"
            )
            source = make_product_design_taskpack(root)
            (source / "DECISION_PRD.md").unlink()
            for directory in (source / "a", source / "b"):
                directory.mkdir()
                (directory / "PRD.md").write_text("# duplicate role\n", encoding="utf-8")
            with self.assertRaises(ingester.TaskpackError):
                ingester.ingest(
                    source,
                    run_dir,
                    authoritative=True,
                    authorization_reference="owner-approved",
                )

    def test_ingester_rejects_cross_alias_role_ambiguity(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_dir = initializer.initialize(
                root, "EEI", "cross-alias-ambiguity", decision_scope="developer_check", target_path="apps/eei"
            )
            source = make_product_design_taskpack(root)
            (source / "PRD.md").write_text("# conflicting second PRD role\n", encoding="utf-8")
            with self.assertRaises(ingester.TaskpackError):
                ingester.ingest(
                    source,
                    run_dir,
                    authoritative=True,
                    authorization_reference="owner-approved",
                )

    def test_ingester_prefers_shallowest_role_over_nested_alias(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_dir = initializer.initialize(
                root, "EEI", "shallowest-role", decision_scope="developer_check", target_path="apps/eei"
            )
            source = make_product_design_taskpack(root)
            appendix = source / "appendix"
            appendix.mkdir()
            (source / "DECISION_PRD.md").replace(appendix / "DECISION_PRD.md")
            (source / "PRD.md").write_text("# authoritative root PRD\n", encoding="utf-8")
            result = ingester.ingest(
                source,
                run_dir,
                authoritative=True,
                authorization_reference="owner-approved",
            )
            self.assertTrue(result["ok"])
            self.assertEqual(
                (run_dir / "taskpack/prd.md").read_text(encoding="utf-8"),
                "# authoritative root PRD\n",
            )

    def test_ingester_rejects_zip_path_traversal(self):
        import zipfile

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_dir = initializer.initialize(
                root, "EEI", "zip-traversal", decision_scope="developer_check", target_path="apps/eei"
            )
            archive = root / "unsafe.zip"
            with zipfile.ZipFile(archive, "w") as handle:
                handle.writestr("../escape.txt", "bad")
            with self.assertRaises(ingester.TaskpackError):
                ingester.ingest(
                    archive,
                    run_dir,
                    authoritative=True,
                    authorization_reference="owner-approved",
                )


    def test_ingester_rejects_duplicate_zip_members(self):
        import warnings
        import zipfile

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_dir = initializer.initialize(
                root, "EEI", "zip-duplicate", decision_scope="developer_check", target_path="apps/eei"
            )
            archive = root / "duplicate.zip"
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                with zipfile.ZipFile(archive, "w") as handle:
                    handle.writestr("MANIFEST.yaml", "version: 1\n")
                    handle.writestr("MANIFEST.yaml", "version: 2\n")
            with self.assertRaises(ingester.TaskpackError):
                ingester.ingest(
                    archive,
                    run_dir,
                    authoritative=True,
                    authorization_reference="owner-approved",
                )

    def test_ai_overall_average_cannot_hide_failed_task_slice(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = prepare_valid_pass(Path(temporary), ai=True)
            manifest_path = run_dir / "RUN_MANIFEST.yaml"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            evidence_dir = run_dir / "raw-results"
            extra_records = []
            for trial_number, status in enumerate(("PASS", "PASS", "FAIL"), start=1):
                reset_name = f"AI-002__trial-{trial_number}__reset.json"
                outcome_name = f"AI-002__trial-{trial_number}__outcome.json"
                trace_name = f"AI-002__trial-{trial_number}__trace.json"
                (evidence_dir / reset_name).write_text(
                    json.dumps({"trial": trial_number, "state": "clean"}) + "\n",
                    encoding="utf-8",
                )
                (evidence_dir / outcome_name).write_text(
                    json.dumps({"trial": trial_number, "status": status}) + "\n",
                    encoding="utf-8",
                )
                (evidence_dir / trace_name).write_text(
                    json.dumps({"trial": trial_number, "trace": "checked"}) + "\n",
                    encoding="utf-8",
                )
                extra_records.append(
                    {
                        "trial_id": f"AI-002-T{trial_number}",
                        "context_id": f"side-effect-context-{trial_number}",
                        "task_slice": "critical-side-effect",
                        "status": status,
                        "outcome": "correct" if status == "PASS" else "duplicate side effect",
                        "reset_evidence_path": f"raw-results/{reset_name}",
                        "outcome_evidence_path": f"raw-results/{outcome_name}",
                        "trace_path": f"raw-results/{trace_name}",
                        "cost": 0.01,
                        "latency_ms": 150 + trial_number,
                    }
                )
            manifest["ai_system"]["task_slices"] = ["core-task", "critical-side-effect"]
            manifest["ai_system"]["trial_records"].extend(extra_records)
            manifest["ai_system"]["trial_count"] = 6
            manifest["ai_system"]["success_threshold"] = 0.8
            manifest["ai_system"]["observed_pass_rate"] = 5 / 6
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            _, errors = finalizer.validate_run(run_dir)
            self.assertTrue(
                any("critical-side-effect" in error and "below success_threshold" in error for error in errors),
                errors,
            )

    def test_ai_generator_cannot_be_sole_judge(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = prepare_valid_pass(Path(temporary), ai=True)
            manifest_path = run_dir / "RUN_MANIFEST.yaml"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["ai_system"]["evaluator_independence"].update(
                {
                    "primary_grader_type": "model",
                    "generator_is_sole_judge": True,
                    "cross_model_review": False,
                    "blind_evaluation": False,
                    "independent_evaluator_ids": ["test-model"],
                }
            )
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            _, errors = finalizer.validate_run(run_dir)
            self.assertTrue(any("sole judge" in error for error in errors), errors)
            self.assertTrue(any("cross_model_review" in error for error in errors), errors)
            self.assertTrue(any("distinct from the generator" in error for error in errors), errors)


class ReviewTaskpackTests(unittest.TestCase):
    def test_sealed_run_packages_as_one_deterministic_builder_zip(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_dir = prepare_valid_pass(root)
            decision = finalizer.finalize(run_dir)
            before = finalizer.verify(run_dir)["evidence_root_sha256"]

            first = packager.package_review_taskpack(run_dir, root / "first.zip")
            second = packager.package_review_taskpack(run_dir, root / "second.zip")

            self.assertEqual(first["evidence_root_sha256"], decision["evidence_root_sha256"])
            self.assertEqual(first["sha256"], second["sha256"])
            self.assertEqual(
                hashlib.sha256((root / "first.zip").read_bytes()).hexdigest(), first["sha256"]
            )
            self.assertEqual(finalizer.verify(run_dir)["evidence_root_sha256"], before)
            self.assertFalse(any(path.suffix == ".zip" for path in run_dir.iterdir()))

            with zipfile.ZipFile(root / "first.zip") as archive:
                names = set(archive.namelist())
                self.assertIn("README_FIRST.md", names)
                for required in packager.REQUIRED_SEALED_FILES:
                    self.assertIn(f"{run_dir.name}/{required}", names)
                entrypoint = archive.read("README_FIRST.md").decode("utf-8")
                self.assertIn("开发 Agent 先看这里", entrypoint)
                self.assertIn(decision["evidence_root_sha256"], entrypoint)

    def test_unsealed_tampered_or_existing_output_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            unsealed = prepare_valid_pass(root)
            with self.assertRaises(packager.ReviewTaskpackError):
                packager.package_review_taskpack(unsealed)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_dir = prepare_valid_pass(root)
            finalizer.finalize(run_dir)
            existing = root / "existing.zip"
            existing.write_bytes(b"do-not-overwrite")
            with self.assertRaises(packager.ReviewTaskpackError):
                packager.package_review_taskpack(run_dir, existing)
            self.assertEqual(existing.read_bytes(), b"do-not-overwrite")

            (run_dir / "raw-results/G-003.json").write_text("tampered\n", encoding="utf-8")
            with self.assertRaises(packager.ReviewTaskpackError):
                packager.package_review_taskpack(run_dir, root / "tampered.zip")
            self.assertFalse((root / "tampered.zip").exists())


class PayloadValidationTests(unittest.TestCase):
    def test_payload_validates(self):
        self.assertEqual(validator.validate(PAYLOAD), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
