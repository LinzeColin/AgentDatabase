from __future__ import annotations

import copy
import hashlib
import io
import sys
import unittest
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
APP_SCRIPTS = ROOT / "apps/memory-atlas/scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


class ChildProcessAdapterTests(unittest.TestCase):
    def test_child_stdout_stderr_and_exit_code_are_preserved(self) -> None:
        from memory_atlas_cli.child_process import run_child_command

        stdout = io.StringIO()
        stderr = io.StringIO()
        returncode = run_child_command(
            [
                sys.executable,
                "-c",
                "import sys; sys.stdout.write('OUT'); sys.stderr.write('ERR'); raise SystemExit(7)",
            ],
            cwd=ROOT,
            stdout_stream=stdout,
            stderr_stream=stderr,
        )

        self.assertEqual(returncode, 7)
        self.assertEqual(stdout.getvalue(), "OUT")
        self.assertEqual(stderr.getvalue(), "ERR")

    def test_transform_failure_still_forwards_child_stderr(self) -> None:
        from memory_atlas_cli.child_process import run_child_command

        stderr = io.StringIO()

        def reject_output(_stdout: str, _returncode: int) -> str:
            raise ValueError("invalid child payload")

        with self.assertRaisesRegex(ValueError, "invalid child payload"):
            run_child_command(
                [
                    sys.executable,
                    "-c",
                    "import sys; sys.stdout.write('not-json'); sys.stderr.write('CHILD-ERROR')",
                ],
                cwd=ROOT,
                stderr_stream=stderr,
                stdout_transform=reject_output,
            )

        self.assertEqual(stderr.getvalue(), "CHILD-ERROR")

    def test_command_modules_use_one_child_process_adapter(self) -> None:
        for module_name in ("analyze.py", "apply.py", "build.py", "push.py", "sync.py"):
            with self.subTest(module=module_name):
                source = (SCRIPTS / "memory_atlas_cli" / module_name).read_text(encoding="utf-8")
                self.assertIn("run_child_command", source)
                self.assertNotIn("subprocess.run(", source)
                self.assertNotIn("import subprocess", source)


class ScriptMigrationMapTests(unittest.TestCase):
    def load_contract(self):
        from memory_atlas_cli.script_migrations import load_script_migration_map

        return load_script_migration_map(ROOT)

    def validate_contract(self, payload):
        from memory_atlas_cli.script_migrations import validate_script_migration_map

        return validate_script_migration_map(payload, ROOT)

    @staticmethod
    def inventory_files() -> list[Path]:
        suffixes = {".py", ".cjs", ".mjs", ".js", ".sh"}
        keywords = ("build", "sync", "audit", "validate")
        return sorted(
            path
            for directory in (SCRIPTS, APP_SCRIPTS)
            for path in directory.iterdir()
            if path.is_file()
            and path.suffix in suffixes
            and any(keyword in path.name for keyword in keywords)
        )

    @staticmethod
    def matched_families(path: Path) -> list[str]:
        family_keywords = (
            ("build", "build"),
            ("sync", "sync"),
            ("audit", "audit"),
            ("validator", "validate"),
        )
        return [family for family, keyword in family_keywords if keyword in path.name]

    def test_map_is_valid_and_covers_all_four_families(self) -> None:
        payload = self.load_contract()

        self.assertEqual(self.validate_contract(payload), [])
        self.assertEqual(
            {item["family"] for item in payload["families"]},
            {"build", "sync", "audit", "validator"},
        )
        self.assertEqual(payload["summary"]["deleted_script_count"], 139)
        self.assertEqual(len(payload["deleted_scripts"]), 139)
        self.assertEqual(len(payload["equivalence_tests"]), 1)
        self.assertEqual(payload["summary"]["consolidated_execution_module_count"], 5)
        self.assertEqual(payload["summary"]["consolidated_execution_block_count"], 8)
        self.assertEqual(payload["summary"]["validator_profile_count_created"], 4)
        self.assertEqual(
            payload["profile_consolidation"],
            {
                "task_id": "S04-P3-T1",
                "status": "completed_local_only",
                "public_profile_count": 4,
                "public_profiles": ["fast", "sync", "ui", "release"],
            },
        )
        self.assertEqual(
            payload["command_migration"],
            {
                "task_id": "S04-P3-T3",
                "status": "completed_local_only",
                "migration_map": "config/memory_atlas_legacy_command_migrations.json",
                "compatibility_mode": "lookup_only",
                "removal_version": "v1.2.2",
                "public_aliases_restored": False,
            },
        )
        self.assertIs(payload["inventory"]["recursive"], False)

        validator_family = next(row for row in payload["families"] if row["family"] == "validator")
        for item in validator_family["scripts"]:
            self.assertEqual(item["status"], "profiled_in_s04_p3_t1")
            self.assertIn(item["canonical_command"], {"npm run validate:fast", "npm run validate:ui"})

    def test_inventory_count_and_exact_hash_facts_match_tracked_sources(self) -> None:
        payload = self.load_contract()
        files = self.inventory_files()
        hashes: dict[str, list[str]] = defaultdict(list)
        for path in files:
            hashes[hashlib.sha256(path.read_bytes()).hexdigest()].append(path.name)
        duplicate_groups = [paths for paths in hashes.values() if len(paths) > 1]

        self.assertEqual(len(files), payload["inventory"]["scanned_script_count"])
        self.assertEqual(len(duplicate_groups), payload["inventory"]["exact_sha256_duplicate_group_count"])
        self.assertEqual(duplicate_groups, [])

    def test_every_scoped_script_is_mapped_with_hash_family_and_disposition(self) -> None:
        payload = self.load_contract()
        files = self.inventory_files()
        mapped = payload["inventory"]["scoped_scripts"]
        mapped_by_path = {item["path"]: item for item in mapped}
        actual_by_path = {path.relative_to(ROOT).as_posix(): path for path in files}
        deleted_by_path = {item["path"]: item for item in payload["deleted_scripts"]}

        self.assertEqual(len(mapped_by_path), len(mapped))
        self.assertEqual(set(mapped_by_path), set(actual_by_path) | set(deleted_by_path))
        self.assertTrue(set(actual_by_path).isdisjoint(deleted_by_path))
        self.assertEqual(payload["inventory"]["baseline_scoped_script_count"], 208)
        self.assertEqual(
            payload["inventory"]["retained_default_deletion_blocker"],
            "equivalent_command_callers_and_behavior_parity_not_all_proven",
        )
        self.assertEqual(payload["summary"]["mapped_scoped_script_count"], len(mapped))
        for relative, path in actual_by_path.items():
            with self.subTest(path=relative):
                item = mapped_by_path[relative]
                self.assertEqual(item["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
                self.assertEqual(item["matched_families"], self.matched_families(path))
                self.assertEqual(item["disposition"], "retained")
        registered_test_ids = {item["test_id"] for item in payload["equivalence_tests"]}
        for relative, deletion in deleted_by_path.items():
            with self.subTest(deleted_path=relative):
                item = mapped_by_path[relative]
                self.assertEqual(item["disposition"], "deleted")
                self.assertTrue(item["baseline"])
                self.assertFalse((ROOT / relative).exists())
                self.assertTrue(deletion["equivalent_command"])
                self.assertTrue(deletion["callers_migrated"])
                self.assertFalse(deletion["behavior_parity_verified"])
                self.assertTrue(deletion["approved_low_value_retirement"])
                self.assertTrue(deletion["replacement_risk_coverage_verified"])
                self.assertEqual(
                    deletion["retirement_review"],
                    "config/memory_atlas_test_value_review.json",
                )
                self.assertTrue(set(deletion["equivalence_test_ids"]).issubset(registered_test_ids))

    def test_unmapped_or_forged_scoped_inventory_entry_fails_closed(self) -> None:
        payload = copy.deepcopy(self.load_contract())
        payload["inventory"]["scoped_scripts"].pop()
        payload["inventory"]["baseline_scoped_script_count"] = 0
        payload["summary"]["mapped_scoped_script_count"] -= 1

        errors = self.validate_contract(payload)

        self.assertTrue(any("baseline_scoped_script_count" in error for error in errors))
        self.assertTrue(any("scoped script mapping" in error for error in errors))

        payload = copy.deepcopy(self.load_contract())
        payload["inventory"]["scoped_scripts"][0]["sha256"] = "0" * 64

        errors = self.validate_contract(payload)

        self.assertTrue(any("SHA-256 mismatch" in error for error in errors))

    def test_every_retained_script_exists_and_has_a_deletion_blocker(self) -> None:
        payload = self.load_contract()
        retained = [item for family in payload["families"] for item in family["scripts"]]

        self.assertGreater(len(retained), 0)
        for item in retained:
            with self.subTest(path=item["path"]):
                self.assertTrue((ROOT / item["path"]).is_file())
                self.assertTrue(item["deletion_blockers"])
                self.assertNotEqual(item["status"], "removed")

    def test_removed_entry_requires_command_tests_callers_and_retirement_evidence(self) -> None:
        payload = copy.deepcopy(self.load_contract())
        payload["deleted_scripts"].append(
            {
                "path": "scripts/removed_without_proof.py",
                "equivalent_command": "",
                "equivalence_test_ids": [],
                "callers_migrated": False,
                "behavior_parity_verified": False,
                "approved_low_value_retirement": False,
                "retirement_review": "",
                "replacement_risk_coverage_verified": False,
            }
        )
        payload["summary"]["deleted_script_count"] = 1

        errors = self.validate_contract(payload)

        self.assertTrue(any("equivalent_command" in error for error in errors))
        self.assertTrue(any("equivalence_test_ids" in error for error in errors))
        self.assertTrue(any("callers_migrated" in error for error in errors))
        self.assertTrue(any("behavior parity or approved low-value retirement" in error for error in errors))

    def test_removed_entry_test_ids_must_be_registered(self) -> None:
        payload = copy.deepcopy(self.load_contract())
        payload["deleted_scripts"].append(
            {
                "path": "scripts/already_absent.py",
                "equivalent_command": "python3 scripts/atlasctl.py audit --check example",
                "equivalence_test_ids": ["missing-test-id"],
                "callers_migrated": True,
                "behavior_parity_verified": True,
                "approved_low_value_retirement": False,
                "retirement_review": "",
                "replacement_risk_coverage_verified": False,
            }
        )
        payload["summary"]["deleted_script_count"] = 1

        errors = self.validate_contract(payload)

        self.assertTrue(any("unregistered equivalence test" in error for error in errors))

    def test_fake_registered_test_cannot_satisfy_retirement_gate(self) -> None:
        payload = copy.deepcopy(self.load_contract())
        payload["equivalence_tests"] = [{"test_id": "fake-parity"}]
        payload["deleted_scripts"].append(
            {
                "path": "scripts/already_absent.py",
                "equivalent_command": "python3 scripts/atlasctl.py audit --check example",
                "equivalence_test_ids": ["fake-parity"],
                "callers_migrated": True,
                "behavior_parity_verified": False,
                "approved_low_value_retirement": True,
                "retirement_review": "config/memory_atlas_test_value_review.json",
                "replacement_risk_coverage_verified": True,
            }
        )
        payload["summary"]["deleted_script_count"] = 1

        errors = self.validate_contract(payload)

        self.assertTrue(any("test_command" in error for error in errors))
        self.assertTrue(any("test_file" in error for error in errors))
        self.assertTrue(any("test_case" in error for error in errors))
        self.assertTrue(any("approved retirement evidence" in error for error in errors))

    def test_contract_drift_and_out_of_scope_retained_path_fail_closed(self) -> None:
        payload = copy.deepcopy(self.load_contract())
        payload["inventory"]["scanned_script_count"] = 0
        payload["inventory"]["recursive"] = True
        payload["deletion_policy"]["equivalent_command_required"] = False
        payload["summary"]["retained_representative_script_count"] = 0
        payload["profile_consolidation"]["status"] = "pending"
        payload["safety"]["raw_mutation"] = True
        payload["command_migration"]["removal_version"] = "indefinite"
        payload["families"][0]["scripts"][0]["path"] = "功能清单.md"

        errors = self.validate_contract(payload)

        self.assertTrue(any("scanned_script_count" in error for error in errors))
        self.assertTrue(any("recursive" in error for error in errors))
        self.assertTrue(any("deletion_policy" in error for error in errors))
        self.assertTrue(any("retained_representative_script_count" in error for error in errors))
        self.assertTrue(any("profile consolidation" in error for error in errors))
        self.assertTrue(any("safety" in error for error in errors))
        self.assertTrue(any("command migration" in error for error in errors))
        self.assertTrue(any("audited script roots" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
