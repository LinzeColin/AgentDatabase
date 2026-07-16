import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT_SCRIPT = ROOT / "scripts" / "audit_memory_atlas_test_value.py"
RUNNER = ROOT / "scripts" / "memory_atlas_validator_profiles.py"


def load_audit_module():
    spec = importlib.util.spec_from_file_location("audit_memory_atlas_test_value", AUDIT_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class MemoryAtlasTestValueAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.audit = load_audit_module()
        self.payload = self.audit.load_test_value_review(ROOT)

    def test_review_contract_covers_complete_baseline_and_current_risk_suite(self) -> None:
        errors = self.audit.audit_test_value_review(self.payload, ROOT)

        self.assertEqual(errors, [])
        self.assertEqual(
            self.payload["baseline"],
            {
                "validator_count": 177,
                "python_test_count": 51,
                "validator_bytes": 2_902_666,
            },
        )
        self.assertEqual(
            self.payload["summary"],
            {
                "deleted_validator_count": 139,
                "deleted_python_test_count": 2,
                "retained_validator_count": 39,
                "retained_baseline_python_test_count": 49,
                "added_python_test_count": 20,
                "current_python_test_count": 69,
            },
        )

    def test_deleted_low_value_validators_have_approved_risk_replacements_and_no_callers(self) -> None:
        deleted = self.payload["candidates"]
        self.assertEqual(len(deleted), 141)
        self.assertTrue(all(item["category"] == "delete" for item in deleted))
        self.assertTrue(all(item["approval"] == "approved" for item in deleted))
        self.assertTrue(all(not (ROOT / item["path"]).exists() for item in deleted))
        self.assertEqual(
            self.audit.find_executable_references(ROOT, {Path(item["path"]).name for item in deleted}),
            {},
        )

        for profile in ("fast", "sync", "ui", "release"):
            result = subprocess.run(
                [sys.executable, str(RUNNER), "--profile", profile, "--plan"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            with self.subTest(profile=profile):
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout)["status"], "PLAN")
                self.assertIn("PLANNED", result.stderr)

    def test_candidate_schema_and_risk_binding_fail_closed(self) -> None:
        broken = copy.deepcopy(self.payload)
        broken["candidates"][0].pop("restore_method")
        broken["retained"][0]["risk_bindings"] = []

        errors = self.audit.audit_test_value_review(broken, ROOT)

        self.assertTrue(any("candidate keys mismatch" in error for error in errors), errors)
        self.assertTrue(any("risk_bindings" in error for error in errors), errors)

    def test_policy_recovery_and_git_baseline_identity_fail_closed(self) -> None:
        broken = copy.deepcopy(self.payload)
        broken["policy"]["remote_push"] = True
        broken["candidates"][0]["restore_method"] = "git restore --source=wrong -- wrong"
        broken["candidates"][0]["path"] = (
            "apps/memory-atlas/scripts/validate_memory_atlas_not_in_baseline.cjs"
        )

        errors = self.audit.audit_test_value_review(broken, ROOT)

        self.assertTrue(any("Task boundary" in error for error in errors), errors)
        self.assertTrue(any("restore_method mismatch" in error for error in errors), errors)
        self.assertTrue(any("Git baseline asset set" in error for error in errors), errors)

    def test_current_executable_reference_to_deleted_path_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_dir = Path(temp_dir)
            script_dir = database_dir / "scripts"
            script_dir.mkdir(parents=True)
            (script_dir / "caller.py").write_text(
                'COMMAND = "validate_memory_atlas_v1_1_6_stage0.cjs"\n',
                encoding="utf-8",
            )

            references = self.audit.find_executable_references(
                database_dir,
                {"validate_memory_atlas_v1_1_6_stage0.cjs"},
            )

        self.assertEqual(references, {"validate_memory_atlas_v1_1_6_stage0.cjs": ["scripts/caller.py"]})


if __name__ == "__main__":
    unittest.main()
