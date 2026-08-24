from __future__ import annotations

from pathlib import Path
import shutil
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from wbi_core.install import _freeze_archive, _install_lock, inspect_install_transaction, install_archive, recover_install_transactions, rollback_install  # noqa: E402
from wbi_core.io import copy_clean, load_json, sha256_file, sha256_tree, utc_now, write_json  # noqa: E402
from wbi_core.package import package_skill  # noqa: E402
from wbi_core.provenance import generate_release_receipt  # noqa: E402

GENESIS = "14ab08b9053db4ca87140e59a49f1de8105a718a87ec2d55590c6487c1a77086"
EFFECTIVE = "fe80c467f8ecbe8343ef0c09ef5e6f9fd9683803c8260c9188998c7e3dfca0a2"


class ReleaseTests(unittest.TestCase):


    def test_release_optimizer_install_requires_exact_external_archive_anchor(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "teleiosis"
            copy_clean(ROOT, source)
            archive = base / "skill.zip"
            self.assertEqual(package_skill(source, archive, GENESIS, verification_level="structural")["status"], "PASS")
            missing = install_archive(archive, base / "skills-missing", GENESIS, verification_level="release")
            self.assertEqual(missing["status"], "FAIL", missing)
            self.assertEqual(missing["stage"], "external-archive-anchor")
            wrong = install_archive(
                archive, base / "skills-wrong", GENESIS, verification_level="release",
                expected_archive_sha256="0" * 64,
            )
            self.assertEqual(wrong["status"], "FAIL", wrong)
            self.assertEqual(wrong["stage"], "external-archive-anchor")
            effective_missing = install_archive(
                archive, base / "skills-effective-missing", GENESIS, verification_level="release",
                expected_archive_sha256=sha256_file(archive),
            )
            self.assertEqual(effective_missing["status"], "FAIL", effective_missing)
            self.assertEqual(effective_missing["stage"], "external-effective-genesis-anchor")
            effective_wrong = install_archive(
                archive, base / "skills-effective-wrong", GENESIS, verification_level="release",
                expected_archive_sha256=sha256_file(archive), expected_effective_genesis_hash="0" * 64,
            )
            self.assertEqual(effective_wrong["status"], "FAIL", effective_wrong)
            self.assertEqual(effective_wrong["stage"], "validation")
            anchored = install_archive(
                archive, base / "skills-pass", GENESIS, verification_level="structural",
                expected_archive_sha256=sha256_file(archive),
            )
            self.assertEqual(anchored["status"], "PASS", anchored)
            self.assertTrue(anchored["external_archive_anchor_verified"])


    def test_actual_release_install_cli_returns_without_recursive_full_suite(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "teleiosis"
            copy_clean(ROOT, source)
            archive = base / "skill.zip"
            self.assertEqual(package_skill(source, archive, GENESIS, verification_level="structural")["status"], "PASS")
            env = dict(os.environ)
            env["WBI_COMMAND_TIMEOUT_SECONDS"] = "20"
            completed = __import__("subprocess").run([
                sys.executable, str(ROOT / "scripts/wbi.py"), "install", str(archive),
                "--skills-root", str(base / "skills"), "--profile", "optimizer",
                "--verification-level", "release", "--expected-genesis-hash", GENESIS,
                "--expected-effective-genesis-hash", EFFECTIVE,
                "--expected-archive-sha256", sha256_file(archive),
            ], text=True, capture_output=True, env=env, timeout=25)
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["status"], "PASS", payload)
            self.assertNotIn("self_test", payload["checks"])
            self.assertEqual(payload["checks"]["release_smoke"]["returncode"], 0)
            self.assertEqual(payload["checks"]["post_install_release_smoke"]["returncode"], 0)

    def test_concurrent_install_is_blocked_by_process_scoped_lock(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "teleiosis"
            copy_clean(ROOT, source)
            archive = base / "skill.zip"
            self.assertEqual(package_skill(source, archive, GENESIS, verification_level="structural")["status"], "PASS")
            skills = base / "skills"
            skills.mkdir()
            with _install_lock(skills):
                result = install_archive(archive, skills, GENESIS, profile="optimizer")
                recovery = recover_install_transactions(skills, GENESIS, "optimizer", "teleiosis", EFFECTIVE)
            self.assertEqual(result["status"], "BLOCKED")
            self.assertEqual(result["stage"], "install-lock")
            self.assertEqual(recovery["status"], "BLOCKED")
            self.assertTrue(any("active" in item["error"] for item in recovery["unresolved"]))

    def test_interrupted_backup_rename_reconstructs_receipt_and_restores_predecessor(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            skills = base / "skills"
            destination = skills / "generic-skill"
            destination.mkdir(parents=True)
            (destination / "SKILL.md").write_text(
                "---\nname: generic-skill\ndescription: Original predecessor.\n---\n\n# Use\n",
                encoding="utf-8",
            )
            predecessor_hash = sha256_tree(destination)
            backup = skills / ".generic-skill.backup.interrupted"
            os.replace(str(destination), str(backup))
            transaction_dir = skills / ".wbi-install-transactions"
            transaction_dir.mkdir()
            receipt = transaction_dir / "backupwindow.json"
            write_json(receipt, {
                "schema_version": "1.0", "transaction_id": "backupwindow",
                "created_at": utc_now(), "updated_at": utc_now(), "status": "BACKUP_PLANNED",
                "destination_name": "generic-skill", "destination": str(destination),
                "profile": "generic", "staged_tree_hash": "0" * 64,
                "predecessor_tree_hash": predecessor_hash, "backup": str(backup), "incoming": None,
            })
            recovered = recover_install_transactions(skills, profile="generic", destination_name="generic-skill")
            self.assertEqual(recovered["status"], "PASS", recovered)
            self.assertTrue(destination.is_dir())
            self.assertTrue((destination / "SKILL.md").is_file())
            self.assertFalse(backup.exists())
            self.assertEqual(load_json(receipt)["status"], "RECOVERED_ROLLED_BACK")

    def test_interrupted_incoming_copy_is_removed_without_guessing_a_switch(self):
        with tempfile.TemporaryDirectory() as td:
            skills = Path(td) / "skills"
            skills.mkdir()
            incoming = skills / ".generic-skill.incoming.interrupted"
            incoming.mkdir()
            (incoming / "partial.txt").write_text("partial", encoding="utf-8")
            transaction_dir = skills / ".wbi-install-transactions"
            transaction_dir.mkdir()
            receipt = transaction_dir / "incomingwindow.json"
            write_json(receipt, {
                "schema_version": "1.0", "transaction_id": "incomingwindow",
                "created_at": utc_now(), "updated_at": utc_now(), "status": "INCOMING_READY",
                "destination_name": "generic-skill", "destination": str(skills / "generic-skill"),
                "profile": "generic", "staged_tree_hash": "0" * 64,
                "predecessor_tree_hash": None, "backup": None, "incoming": str(incoming),
            })
            recovered = recover_install_transactions(skills, profile="generic", destination_name="generic-skill")
            self.assertEqual(recovered["status"], "PASS", recovered)
            self.assertFalse(incoming.exists())
            self.assertEqual(load_json(receipt)["status"], "ABORTED_NO_SWITCH")

    def test_interrupted_switched_install_reconciles_from_tree_and_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "teleiosis"
            copy_clean(ROOT, source)
            archive = base / "skill.zip"
            self.assertEqual(package_skill(source, archive, GENESIS, verification_level="structural")["status"], "PASS")
            skills = base / "skills"
            installed = install_archive(archive, skills, GENESIS, profile="optimizer")
            self.assertEqual(installed["status"], "PASS")
            transaction_dir = skills / ".wbi-install-transactions"
            fake = transaction_dir / "interrupted.json"
            write_json(fake, {
                "schema_version": "1.0", "transaction_id": "interrupted", "created_at": utc_now(),
                "updated_at": utc_now(), "status": "SWITCHED", "destination_name": "teleiosis",
                "profile": "optimizer", "expected_genesis_hash": GENESIS,
                "staged_tree_hash": sha256_tree(skills / "teleiosis", exclude={"MANIFEST.sha256"}),
                "backup": None,
            })
            recovered = recover_install_transactions(skills, GENESIS, "optimizer", "teleiosis", EFFECTIVE)
            self.assertEqual(recovered["status"], "PASS", recovered)
            self.assertEqual(load_json(fake)["status"], "RECOVERED_COMMITTED")

    def test_explicit_rollback_updates_install_transaction_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "teleiosis"
            copy_clean(ROOT, source)
            archive = base / "skill.zip"
            self.assertEqual(package_skill(source, archive, GENESIS, verification_level="structural")["status"], "PASS")
            skills = base / "skills"
            self.assertEqual(install_archive(archive, skills, GENESIS, profile="optimizer")["status"], "PASS")
            (skills / "teleiosis/old-sentinel.txt").write_text("old", encoding="utf-8")
            upgraded = install_archive(archive, skills, GENESIS, replace=True, profile="optimizer")
            transaction_path = Path(upgraded["transaction_receipt"])
            self.assertEqual(load_json(transaction_path)["status"], "COMMITTED")
            rolled = rollback_install(skills / "teleiosis", Path(upgraded["backup"]))
            self.assertEqual(rolled["status"], "PASS", rolled)
            self.assertEqual(load_json(transaction_path)["status"], "ROLLED_BACK_BY_REQUEST")

    def test_release_install_uses_non_recursive_smoke_and_writes_transaction_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "teleiosis"
            copy_clean(ROOT, source)
            archive = base / "skill.zip"
            self.assertEqual(package_skill(source, archive, GENESIS, verification_level="structural")["status"], "PASS")

            calls = []
            def fake_check(_root, arguments, _expected, _effective=""):
                calls.append(list(arguments))
                return {
                    "command": list(arguments), "returncode": 0, "timed_out": False,
                    "timeout_seconds": 10, "stdout": "{}", "stderr": "",
                }

            with patch("wbi_core.install._optimizer_check", side_effect=fake_check):
                result = install_archive(
                    archive, base / "skills", GENESIS, profile="optimizer", verification_level="release",
                    expected_archive_sha256=sha256_file(archive), expected_effective_genesis_hash=EFFECTIVE,
                )
            self.assertEqual(result["status"], "PASS", result)
            self.assertNotIn(["self-test"], calls)
            self.assertGreaterEqual(calls.count(["release-smoke", "--expected-genesis-hash", GENESIS, "--expected-effective-genesis-hash", EFFECTIVE]), 2)
            receipt = Path(result["transaction_receipt"])
            self.assertTrue(receipt.is_file())
            payload = json.loads(receipt.read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "COMMITTED")
            self.assertEqual(payload["archive_sha256"], sha256_file(archive))

    def test_deep_install_is_explicit_and_runs_full_suite_only_before_switch(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "teleiosis"
            copy_clean(ROOT, source)
            archive = base / "skill.zip"
            self.assertEqual(package_skill(source, archive, GENESIS, verification_level="structural")["status"], "PASS")
            calls = []
            def fake_check(_root, arguments, _expected, _effective=""):
                calls.append(list(arguments))
                return {
                    "command": list(arguments), "returncode": 0, "timed_out": False,
                    "timeout_seconds": 10, "stdout": "{}", "stderr": "",
                }
            with patch.dict(os.environ, {"WBI_NESTED_SELF_TEST": ""}), patch("wbi_core.install._optimizer_check", side_effect=fake_check):
                result = install_archive(
                    archive, base / "skills", GENESIS, profile="optimizer", verification_level="deep",
                    expected_archive_sha256=sha256_file(archive), expected_effective_genesis_hash=EFFECTIVE,
                )
            self.assertEqual(result["status"], "PASS", result)
            self.assertEqual(calls.count(["self-test"]), 1)
            self.assertGreaterEqual(calls.count(["release-smoke", "--expected-genesis-hash", GENESIS, "--expected-effective-genesis-hash", EFFECTIVE]), 2)

    def test_atomic_install_backup_and_rollback(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "teleiosis"
            copy_clean(ROOT, source)
            archive = base / "skill.zip"
            self.assertEqual(package_skill(source, archive, GENESIS)["status"], "PASS")
            skills = base / "skills"
            first = install_archive(archive, skills, GENESIS)
            self.assertEqual(first["status"], "PASS", first)
            (skills / "teleiosis/old-sentinel.txt").write_text("old", encoding="utf-8")
            second = install_archive(archive, skills, GENESIS, replace=True)
            self.assertEqual(second["status"], "PASS", second)
            self.assertFalse((skills / "teleiosis/old-sentinel.txt").exists())
            backup = Path(second["backup"])
            self.assertTrue((backup / "old-sentinel.txt").is_file())
            rolled = rollback_install(skills / "teleiosis", backup)
            self.assertEqual(rolled["status"], "PASS")
            self.assertTrue((skills / "teleiosis/old-sentinel.txt").is_file())

    def test_rollback_rejects_arbitrary_or_tampered_same_parent_directory(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            destination = base / "teleiosis"
            destination.mkdir()
            arbitrary = base / "other"
            arbitrary.mkdir()
            self.assertEqual(rollback_install(destination, arbitrary)["status"], "FAIL")

            source = base / "source" / "teleiosis"
            source.parent.mkdir()
            copy_clean(ROOT, source)
            archive = base / "skill.zip"
            self.assertEqual(package_skill(source, archive, GENESIS)["status"], "PASS")
            skills = base / "skills"
            self.assertEqual(install_archive(archive, skills, GENESIS)["status"], "PASS")
            (skills / "teleiosis/sentinel.txt").write_text("old", encoding="utf-8")
            upgraded = install_archive(archive, skills, GENESIS, replace=True)
            backup = Path(upgraded["backup"])
            (backup / "sentinel.txt").write_text("tampered", encoding="utf-8")
            result = rollback_install(skills / "teleiosis", backup)
            self.assertEqual(result["status"], "FAIL")
            self.assertTrue(any("hash mismatch" in item for item in result["errors"]))

    def test_install_requires_explicit_replace(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "teleiosis"
            copy_clean(ROOT, source)
            archive = base / "skill.zip"
            package_skill(source, archive, GENESIS)
            skills = base / "skills"
            install_archive(archive, skills, GENESIS)
            self.assertEqual(install_archive(archive, skills, GENESIS)["status"], "BLOCKED")

    def test_optimizer_package_and_install_require_external_genesis_anchor(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "teleiosis"
            copy_clean(ROOT, source)
            archive = base / "skill.zip"
            result = package_skill(source, archive)
            self.assertEqual(result["stage"], "external-genesis-anchor")

    def test_generic_package_and_install_never_execute_target_code(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "generic-skill"
            (source / "scripts").mkdir(parents=True)
            marker = base / "executed.txt"
            (source / "SKILL.md").write_text(
                "---\nname: generic-skill\ndescription: A generic test Skill.\n---\n\n# Use\n\nRun only when invoked by the user.\n",
                encoding="utf-8",
            )
            (source / "scripts/payload.py").write_text(
                "from pathlib import Path\nPath(%r).write_text('executed')\n" % str(marker), encoding="utf-8"
            )
            archive = base / "generic.zip"
            packaged = package_skill(source, archive)
            self.assertEqual(packaged["status"], "PASS", packaged)
            self.assertFalse(marker.exists())
            installed = install_archive(archive, base / "skills")
            self.assertEqual(installed["status"], "PASS", installed)
            self.assertFalse(marker.exists())
            self.assertFalse(installed["checks"]["executed_target_code"])

    def test_release_receipt_claims_are_derived_from_real_results(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "teleiosis"
            copy_clean(ROOT, source)
            archive = base / "skill.zip"
            packaged = package_skill(source, archive, GENESIS)
            self.assertEqual(packaged["status"], "PASS", packaged)
            installed = install_archive(archive, base / "skills", GENESIS)
            self.assertEqual(installed["status"], "PASS", installed)
            output = base / "receipt.json"
            receipt = generate_release_receipt(
                source, archive, output, gate_result={"status": "BLOCKED"}, install_result=installed, expected_genesis_hash=GENESIS
            )
            self.assertTrue(receipt["claims"]["archive_structurally_valid"])
            self.assertTrue(receipt["claims"]["installable"])
            self.assertTrue(receipt["claims"]["deterministically_packaged"])
            self.assertFalse(receipt["claims"]["formal_independent_promotion"])
            observed = inspect_install_transaction(
                base / "skills", installed["transaction_id"], verify_installed=True,
                expected_genesis_hash=GENESIS, profile="optimizer",
            )
            receipt_from_durable_status = generate_release_receipt(
                source, archive, base / "receipt-from-status.json", install_result=observed,
                expected_genesis_hash=GENESIS,
            )
            self.assertTrue(receipt_from_durable_status["claims"]["installable"])
            unproven = generate_release_receipt(source, archive, base / "receipt-unproven.json", expected_genesis_hash=GENESIS)
            self.assertFalse(unproven["claims"]["installable"])

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_installer_rejects_symlinked_internal_lock_and_transaction_controls(self):
        if os.name != "posix":
            self.skipTest("symbolic link control-path test requires POSIX")
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "generic-skill"
            source.mkdir()
            (source / "SKILL.md").write_text(
                "---\nname: generic-skill\ndescription: Internal control path test.\n---\n\n# Use\n",
                encoding="utf-8",
            )
            archive = base / "generic.zip"
            self.assertEqual(package_skill(source, archive)["status"], "PASS")

            skills_lock = base / "skills-lock"
            skills_lock.mkdir()
            external_lock = base / "external-lock"
            external_lock.write_text("external", encoding="utf-8")
            (skills_lock / ".wbi-install.lock").symlink_to(external_lock)
            blocked = install_archive(archive, skills_lock, profile="generic")
            self.assertEqual(blocked["status"], "BLOCKED", blocked)
            self.assertEqual(blocked["stage"], "install-lock")

            skills_tx = base / "skills-tx"
            skills_tx.mkdir()
            external_tx = base / "external-tx"
            external_tx.mkdir()
            (skills_tx / ".wbi-install-transactions").symlink_to(external_tx, target_is_directory=True)
            blocked = install_archive(archive, skills_tx, profile="generic")
            self.assertEqual(blocked["status"], "BLOCKED", blocked)
            self.assertEqual(blocked["stage"], "recovery-required")

    def test_archive_freeze_detects_input_change(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "input.zip"
            target = base / "frozen.zip"
            source.write_bytes(b"archive")
            with patch("wbi_core.install.sha256_file", side_effect=["a" * 64, "a" * 64, "b" * 64]):
                with self.assertRaisesRegex(ValueError, "changed"):
                    _freeze_archive(source, target)
            self.assertFalse(target.exists())

    def test_install_and_rollback_reject_symlinked_control_paths(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "generic-skill"
            source.mkdir()
            (source / "SKILL.md").write_text(
                "---\nname: generic-skill\ndescription: Symlink boundary test.\n---\n\n# Use\n",
                encoding="utf-8",
            )
            archive = base / "generic.zip"
            self.assertEqual(package_skill(source, archive)["status"], "PASS")
            archive_link = base / "archive-link.zip"
            archive_link.symlink_to(archive)
            self.assertEqual(install_archive(archive_link, base / "skills", profile="generic")["status"], "FAIL")

            real_skills = base / "real-skills"
            real_skills.mkdir()
            skills_link = base / "skills-link"
            skills_link.symlink_to(real_skills, target_is_directory=True)
            self.assertEqual(install_archive(archive, skills_link, profile="generic")["status"], "BLOCKED")

            skills = base / "safe-skills"
            skills.mkdir()
            external = base / "external"
            external.mkdir()
            (skills / "generic-skill").symlink_to(external, target_is_directory=True)
            blocked = install_archive(archive, skills, replace=True, profile="generic")
            self.assertEqual(blocked["status"], "BLOCKED")

            destination = base / "destination"
            destination.mkdir()
            backup_real = base / ".destination.backup.real"
            backup_real.mkdir()
            backup_link = base / ".destination.backup.link"
            backup_link.symlink_to(backup_real, target_is_directory=True)
            self.assertEqual(rollback_install(destination, backup_link)["status"], "FAIL")

    def test_cli_result_file_and_install_status_verify_committed_destination(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "generic-skill"
            source.mkdir()
            (source / "SKILL.md").write_text(
                "---\nname: generic-skill\ndescription: Durable install status test.\n---\n\n# Use\n",
                encoding="utf-8",
            )
            archive = base / "generic.zip"
            self.assertEqual(package_skill(source, archive)["status"], "PASS")
            skills = base / "skills"
            result_file = base / "install-result.json"
            completed = __import__("subprocess").run([
                sys.executable, str(ROOT / "scripts/wbi.py"), "install", str(archive),
                "--skills-root", str(skills), "--profile", "generic",
                "--verification-level", "structural", "--result-file", str(result_file),
            ], text=True, capture_output=True, timeout=30)
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            stdout_payload = json.loads(completed.stdout)
            file_payload = load_json(result_file)
            self.assertEqual(file_payload["transaction_id"], stdout_payload["transaction_id"])
            observed = inspect_install_transaction(skills, stdout_payload["transaction_id"], verify_installed=True, profile="generic")
            self.assertEqual(observed["status"], "PASS", observed)
            self.assertEqual(observed["observed_transaction_status"], "COMMITTED")
            self.assertEqual(observed["installed_verification"]["status"], "PASS")
            status = __import__("subprocess").run([
                sys.executable, str(ROOT / "scripts/wbi.py"), "install-status",
                "--skills-root", str(skills), "--transaction-id", stdout_payload["transaction_id"],
                "--verify-installed", "--profile", "generic",
            ], text=True, capture_output=True, timeout=30)
            self.assertEqual(status.returncode, 0, status.stdout + status.stderr)
            self.assertEqual(json.loads(status.stdout)["installed_verification"]["status"], "PASS")

    def test_install_status_detects_committed_destination_tamper(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "generic-skill"
            source.mkdir()
            (source / "SKILL.md").write_text(
                "---\nname: generic-skill\ndescription: Tamper detection test.\n---\n\n# Use\n",
                encoding="utf-8",
            )
            archive = base / "generic.zip"
            self.assertEqual(package_skill(source, archive)["status"], "PASS")
            skills = base / "skills"
            installed = install_archive(archive, skills, profile="generic")
            self.assertEqual(installed["status"], "PASS")
            (skills / "generic-skill/SKILL.md").write_text("tampered", encoding="utf-8")
            observed = inspect_install_transaction(skills, installed["transaction_id"], verify_installed=True, profile="generic")
            self.assertEqual(observed["status"], "BLOCKED")
            self.assertEqual(observed["installed_verification"]["status"], "FAIL")

    def test_new_backup_receipt_covers_manifest_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "teleiosis"
            copy_clean(ROOT, source)
            archive = base / "skill.zip"
            self.assertEqual(package_skill(source, archive, GENESIS)["status"], "PASS")
            skills = base / "skills"
            self.assertEqual(install_archive(archive, skills, GENESIS)["status"], "PASS")
            upgraded = install_archive(archive, skills, GENESIS, replace=True)
            self.assertEqual(upgraded["status"], "PASS", upgraded)
            backup = Path(upgraded["backup"])
            receipt = load_json(backup / ".wbi-backup-receipt.json")
            self.assertEqual(receipt["schema_version"], "1.1")
            manifest = backup / "MANIFEST.sha256"
            manifest.write_text(manifest.read_text(encoding="utf-8") + "tampered\n", encoding="utf-8")
            rolled = rollback_install(skills / "teleiosis", backup)
            self.assertEqual(rolled["status"], "FAIL")
            self.assertTrue(any("hash mismatch" in item for item in rolled["errors"]))

    def test_legacy_backup_receipt_remains_explicitly_compatible(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            destination = base / "teleiosis"
            destination.mkdir()
            (destination / "current.txt").write_text("current", encoding="utf-8")
            backup = base / ".teleiosis.backup.legacy"
            backup.mkdir()
            (backup / "old.txt").write_text("old", encoding="utf-8")
            (backup / "MANIFEST.sha256").write_text("legacy-manifest-not-covered\n", encoding="utf-8")
            write_json(backup / ".wbi-backup-receipt.json", {
                "schema_version": "1.0", "destination_name": "teleiosis", "backup_name": backup.name,
                "source_tree_hash": sha256_tree(backup, exclude={".wbi-backup-receipt.json", "MANIFEST.sha256"}),
            })
            rolled = rollback_install(destination, backup)
            self.assertEqual(rolled["status"], "PASS", rolled)
            self.assertTrue(rolled["legacy_receipt"])
            self.assertTrue((destination / "old.txt").is_file())
            self.assertFalse((destination / ".wbi-backup-receipt.json").exists())

    def test_invalid_archive_receipt_is_a_failure(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "teleiosis"
            copy_clean(ROOT, source)
            archive = base / "invalid.zip"
            archive.write_bytes(b"not-a-zip")
            receipt = generate_release_receipt(source, archive, base / "receipt.json", expected_genesis_hash=GENESIS)
            self.assertEqual(receipt["receipt_status"], "FAIL")
            self.assertFalse(receipt["claims"]["archive_structurally_valid"])

    def test_cli_errors_are_structured_without_traceback(self):
        completed = __import__("subprocess").run(
            [sys.executable, str(ROOT / "scripts/wbi.py"), "validate", "/definitely/missing/skill", "--strict"],
            text=True, capture_output=True,
        )
        self.assertEqual(completed.returncode, 2)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "FAIL")
        self.assertNotIn("Traceback", completed.stderr)

    def test_cli_receipt_returns_failure_for_invalid_archive(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            archive = base / "invalid.zip"
            archive.write_bytes(b"not-a-zip")
            output = base / "receipt.json"
            completed = __import__("subprocess").run([
                sys.executable, str(ROOT / "scripts/wbi.py"), "release-receipt",
                "--skill-dir", str(ROOT), "--archive", str(archive), "--output", str(output),
                "--expected-genesis-hash", GENESIS,
            ], text=True, capture_output=True)
            self.assertEqual(completed.returncode, 2, completed.stdout + completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["status"], "FAIL")
            self.assertEqual(payload["receipt"]["receipt_status"], "FAIL")


    def test_git_provenance_probe_is_bounded_and_fail_closed(self):
        from wbi_core.provenance import _git_value
        result = {
            "returncode": 124, "timed_out": True, "stdout": "partial", "stderr": "timeout",
            "stdout_truncated": False, "stderr_truncated": False, "stdout_bytes": 7, "stderr_bytes": 7,
            "timeout_seconds": 10, "elapsed_seconds": 10.0,
        }
        with patch("wbi_core.provenance.run_bounded", return_value=result) as bounded:
            self.assertIsNone(_git_value(ROOT, ["rev-parse", "HEAD"]))
        _, kwargs = bounded.call_args
        self.assertEqual(kwargs["timeout_seconds"], 10)
        self.assertEqual(kwargs["max_output_bytes"], 64 * 1024)
        self.assertEqual(kwargs["env"]["GIT_TERMINAL_PROMPT"], "0")



    def test_package_timeout_validation_only_applies_when_optimizer_commands_execute(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "teleiosis"
            copy_clean(ROOT, source)
            with patch.dict(os.environ, {"WBI_COMMAND_TIMEOUT_SECONDS": "0"}):
                structural = package_skill(source, base / "structural.zip", GENESIS, verification_level="structural")
                release = package_skill(source, base / "release.zip", GENESIS, verification_level="release", expected_effective_genesis_hash=EFFECTIVE)
            self.assertEqual(structural["status"], "PASS", structural)
            self.assertEqual(release["status"], "FAIL", release)
            self.assertEqual(release["stage"], "prepackage-command-policy")



if __name__ == "__main__":
    unittest.main()
