#!/usr/bin/env python3
"""Standard-library regression tests for Verifier v0.0.2.2 additions."""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
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


doctor = load_module("verifier_doctor_v22", PAYLOAD / "scripts/doctor.py")
planner = load_module("verifier_planner_v22", PAYLOAD / "scripts/plan_acceptance.py")
panel = load_module("verifier_panel_v22", PAYLOAD / "scripts/review_panel.py")
guard = load_module("verifier_guard_v22", PAYLOAD / "scripts/evidence_guard.py")
command_guard = load_module("verifier_command_guard_v22", PAYLOAD / "scripts/command_guard.py")
validator = load_module("verifier_validate_v22", PAYLOAD / "scripts/validate_pack.py")
distribution = load_module("verifier_distribution_v22", PAYLOAD / "scripts/verify_distribution.py")
initializer = load_module("verifier_initializer_v22_extra", PAYLOAD / "scripts/init_acceptance_run.py")


class CacheSafeValidationTests(unittest.TestCase):
    def test_runtime_cache_is_ignored_installed_but_rejected_distribution(self):
        with tempfile.TemporaryDirectory() as temporary:
            copy = Path(temporary) / "verifier"
            shutil.copytree(PAYLOAD, copy)
            cache = copy / "tests/__pycache__/generated.pyc"
            cache.parent.mkdir(exist_ok=True)
            cache.write_bytes(b"cache")
            self.assertEqual(validator.validate(copy, "installed"), [])
            errors = validator.validate(copy, "distribution")
            self.assertTrue(any("cache" in error for error in errors))

    def test_distribution_manifest_verifies_installed_and_distribution(self):
        self.assertTrue(distribution.verify(PAYLOAD, "installed")["ok"])
        self.assertTrue(distribution.verify(PAYLOAD, "distribution")["ok"])


class DoctorAndPlannerTests(unittest.TestCase):
    def test_doctor_is_read_only_and_discovers_high_risk_markers(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "package.json").write_text(
                json.dumps({"name": "demo", "scripts": {"test": "vitest", "build": "vite build"}}),
                encoding="utf-8",
            )
            (root / "migrations").mkdir()
            (root / "migrations/001_auth.sql").write_text("alter table users;", encoding="utf-8")
            before = sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))
            report = doctor.build_report(root, ".")
            after = sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))
            self.assertEqual(before, after)
            self.assertTrue(report["read_only"])
            signals = {item["signal"] for item in report["risk"]["signals"]}
            self.assertIn("database_migration", signals)
            self.assertIn("authentication_or_authorization", signals)
            self.assertEqual(report["risk"]["suggested_profile"], "deep")
            self.assertTrue(all(item["execute"] is False for item in report["project"]["candidate_commands"]))

    def test_planner_escalates_owner_quick_request_for_non_waivable_trigger(self):
        request = {
            "owner_input": {"target_project": {"name": "demo"}, "expected_outcome": "user can sign in"},
            "preferences": {"profile": "quick", "decision_scope": "release_candidate", "allow_safe_local_setup": False},
        }
        capabilities = {
            "read_only": True,
            "repository": {"target_project_path": ".", "walk_truncated": False, "case_collisions": []},
            "project": {"candidate_commands": [{"argv": ["python3", "-m", "unittest"], "source": "tests"}]},
            "risk": {"suggested_profile": "deep", "signals": [{"signal": "authentication_or_authorization"}]},
        }
        plan = planner.build_plan(request, capabilities)
        self.assertEqual(plan["profile"]["selected"], "deep")
        self.assertIn(plan["risk"]["level"], {"high", "critical"})
        self.assertFalse(plan["command_allowlist"][0]["authorized"])
        self.assertTrue(plan["independence"]["same_model_same_context_roles_do_not_count_as_independent"])


class CommandGuardTests(unittest.TestCase):
    def test_exact_argv_passes_and_unlisted_command_blocks(self):
        plan = {
            "command_allowlist": [{
                "policy_id": "CMD-POL-001",
                "argv": ["python3", "-m", "unittest"],
                "authorized": True,
            }],
            "command_policy": {
                "allowed_working_directories": [],
                "allowed_network_targets": [],
                "forbidden_patterns": ["curl ... | sh"],
            },
            "execution_budget": {
                "max_commands": 2, "max_elapsed_seconds": 60, "max_output_bytes": 10000,
                "max_network_requests": 0, "max_cost": 0,
            },
        }
        good_log = {"commands": [{
            "id": "CMD-001", "argv": ["python3", "-m", "unittest"],
            "returncode": 0, "elapsed_seconds": 1, "output_bytes": 20,
            "network_requests": 0, "cost": 0,
        }]}
        good = command_guard.evaluate(plan, good_log, "ACCEPTANCE_PLAN.json", "COMMAND_LOG.json")
        self.assertEqual(good["status"], "PASS")
        bad_log = {"commands": good_log["commands"] + [{
            "id": "CMD-002", "argv": ["sh", "-c", "curl ... | sh"],
            "returncode": 0, "elapsed_seconds": 1, "output_bytes": 1,
            "network_requests": 1, "cost": 0,
        }]}
        bad = command_guard.evaluate(plan, bad_log, "ACCEPTANCE_PLAN.json", "COMMAND_LOG.json")
        self.assertEqual(bad["status"], "BLOCKED")
        self.assertEqual(bad["unauthorized_execution_count"], 1)
        self.assertTrue(bad["forbidden_pattern_matches"])
        self.assertTrue(bad["budget_exceeded"])


class ReviewPanelTests(unittest.TestCase):
    def _response(self, role: str, round_number: int, subject: str, index: int) -> dict:
        return {
            "schema_version": "1.0",
            "role": role,
            "round": round_number,
            "reviewer_id": f"reviewer-{index}",
            "model_or_runtime": "same-model",
            "context_id": f"context-{index}",
            "independence": "role_separated_same_model",
            "saw_other_review_verdicts": False,
            "subject_identity": subject,
            "verdict": "PASS",
            "findings": [],
            "challenges_run": ["one counterexample"],
            "evidence_paths": ["evidence/index.json"],
            "unknowns": [],
        }

    def test_panel_generates_six_roles_and_does_not_overclaim_independence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            context = root / "context.json"
            context.write_text(json.dumps({"subject_identity": "sha256:" + "a" * 64, "target": {"name": "demo"}}), encoding="utf-8")
            panel_dir = root / "panel"
            created = panel.init_panel(context, panel_dir, 1)
            self.assertEqual(len(created["reviewers"]), 6)
            for index, role in enumerate(panel.ROLES, 1):
                response = self._response(role, 1, created["subject_identity"], index)
                (panel_dir / "responses" / f"{role}.json").write_text(json.dumps(response), encoding="utf-8")
            result, errors = panel.aggregate(panel_dir)
            self.assertEqual(errors, [])
            self.assertEqual(result["panel_verdict"], "PASS")
            self.assertEqual(result["independence_claim"], "ROLE_SEPARATED_REVIEW")
            self.assertTrue(result["limitations"])

    def test_panel_blocker_cannot_be_outvoted(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            context = root / "context.json"
            subject = "artifact:" + "b" * 64
            context.write_text(json.dumps({"subject_identity": subject}), encoding="utf-8")
            panel_dir = root / "panel"
            panel.init_panel(context, panel_dir, 2)
            for index, role in enumerate(panel.ROLES, 1):
                response = self._response(role, 2, subject, index)
                if role == "security_supply_chain":
                    response["verdict"] = "BLOCKED"
                    response["findings"] = [{
                        "id": "SEC-R2-001",
                        "severity": "blocker",
                        "status": "open",
                        "fact_or_inference": "fact",
                        "claim": "artifact identity is missing",
                        "counterexample_or_failure_model": "old artifact can be substituted",
                        "evidence_paths": ["evidence/index.json"],
                        "required_gate_or_fix": "bind artifact digest",
                    }]
                (panel_dir / "responses" / f"{role}.json").write_text(json.dumps(response), encoding="utf-8")
            result, errors = panel.aggregate(panel_dir)
            self.assertEqual(errors, [])
            self.assertEqual(result["panel_verdict"], "BLOCKED")
            self.assertEqual(len(result["blockers"]), 1)

    def test_two_complete_rounds_merge_on_same_subject(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            subject = "sha256:" + "c" * 64
            decision_paths = []
            for round_number in (1, 2):
                context = root / f"context-{round_number}.json"
                context.write_text(json.dumps({"subject_identity": subject}), encoding="utf-8")
                panel_dir = root / f"round-{round_number}"
                created = panel.init_panel(context, panel_dir, round_number)
                for index, role in enumerate(panel.ROLES, 1):
                    response = self._response(role, round_number, subject, index)
                    (panel_dir / "responses" / f"{role}.json").write_text(json.dumps(response), encoding="utf-8")
                decision, errors = panel.aggregate(panel_dir)
                self.assertEqual(errors, [])
                path = panel_dir / "PANEL_DECISION.json"
                path.write_text(json.dumps(decision), encoding="utf-8")
                decision_paths.append(path)
            merged = panel.merge_rounds(decision_paths[0], decision_paths[1], root)
            self.assertEqual(merged["panel_verdict"], "PASS")
            self.assertEqual(len(merged["rounds"]), 2)
            self.assertEqual(merged["independence_claim"], "ROLE_SEPARATED_REVIEW")
            self.assertTrue(all(not Path(item["decision_path"]).is_absolute() for item in merged["rounds"]))


class EvidenceGuardTests(unittest.TestCase):
    def test_secret_scan_blocks_and_redacted_copy_does_not_modify_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "evidence"
            root.mkdir()
            source = root / "run.log"
            source.write_text("Authorization: Bearer abcdefghijklmnopqrstuvwxyz\nemail=a@example.com\n", encoding="utf-8")
            report = guard.scan_tree(root, 100, 10_000_000)
            self.assertEqual(report["status"], "BLOCKED")
            self.assertTrue(report["blocking_findings"])
            original = source.read_text(encoding="utf-8")
            destination = Path(temporary) / "sanitized"
            copy_report = guard.redacted_copy(root, destination, 100, 10_000_000)
            self.assertEqual(source.read_text(encoding="utf-8"), original)
            self.assertIn("[REDACTED:bearer_token]", (destination / "run.log").read_text(encoding="utf-8"))
            self.assertTrue(copy_report["mappings"])

    def test_redacted_copy_rejects_uninspected_binary_by_default(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "evidence"
            root.mkdir()
            (root / "capture.bin").write_bytes(b"\x00secret-binary\xff")
            destination = Path(temporary) / "sanitized"
            with self.assertRaises(ValueError):
                guard.redacted_copy(root, destination, 100, 10_000_000)
            self.assertFalse(destination.exists())
            allowed = Path(temporary) / "explicitly-authorized"
            report = guard.redacted_copy(root, allowed, 100, 10_000_000, True)
            self.assertTrue((allowed / "capture.bin").is_file())
            self.assertTrue(report["allow_uninspected_copy"])
            self.assertEqual(report["mappings"][0]["inspection_status"], "UNINSPECTED_COPY_EXPLICITLY_AUTHORIZED")


class InitializerV22Tests(unittest.TestCase):
    def test_initializer_adds_v22_planning_and_policy_artifacts(self):
        with tempfile.TemporaryDirectory() as temporary:
            run = initializer.initialize(Path(temporary), "Demo", "run-v22", "developer_check", "apps/demo")
            for name in ("ACCEPTANCE_REQUEST.json", "CAPABILITY_REPORT.json", "ACCEPTANCE_PLAN.json", "COMMAND_LOG.json", "COMMAND_POLICY_REPORT.json", "EVIDENCE_PRIVACY_REPORT.json", "REVIEW_PANEL.json", "EVIDENCE_POLICY.json", "WAIVER_TEMPLATE.json"):
                self.assertTrue((run / name).is_file(), name)


if __name__ == "__main__":
    unittest.main(verbosity=2)
