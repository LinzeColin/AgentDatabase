from __future__ import annotations

from pathlib import Path
import json
import os
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from wbi_core.io import write_json  # noqa: E402
from wbi_core.security import classify_action, default_authority_contract, scan_secrets, validate_sandbox_record  # noqa: E402


class SecurityTests(unittest.TestCase):
    def authority(self):
        return default_authority_contract({"run_id": "r", "target": {"candidates": [{"path": "/tmp/c"}]}})

    def test_reversible_candidate_work_is_authorized_without_repeated_confirmation(self):
        for action in ("READ", "SEARCH", "DOWNLOAD_QUARANTINE", "MODIFY_CANDIDATE", "RUN_LOCAL_TEST", "PACKAGE", "ROLLBACK"):
            self.assertEqual(classify_action(action, self.authority())["status"], "AUTHORIZED")

    def test_remote_and_destructive_actions_remain_explicit(self):
        for action in ("REMOTE_PUSH", "MERGE", "TAG_RELEASE", "DEPLOY_PRODUCTION", "DELETE_FORMAL_DATA", "PURCHASE"):
            self.assertEqual(classify_action(action, self.authority())["status"], "BLOCKED")
            self.assertEqual(classify_action(action, self.authority(), True)["status"], "AUTHORIZED")

    def test_third_party_dynamic_execution_requires_complete_sandbox(self):
        record = {
            "action": "RUN_THIRD_PARTY_SANDBOX", "explicit_authorization": True, "command": ["python", "test.py"],
            "timeout_seconds": 30, "isolation": {"ephemeral": True, "no_host_secrets": True, "no_host_mounts": True, "command_allowlist": True, "timeout": True, "filesystem_diff": True, "network": "off"},
            "exit_status": 0, "stdout_sha256": "a" * 64, "stderr_sha256": "b" * 64,
        }
        self.assertEqual(validate_sandbox_record(record), [])
        record["isolation"]["no_host_mounts"] = False
        self.assertTrue(validate_sandbox_record(record))

    def test_secret_scanner_detects_persisted_token(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "bad.txt").write_text("token=" + "gh" + "p_" + "abcdefghijklmnopqrstuvwxyz0123456789", encoding="utf-8")
            self.assertTrue(scan_secrets(root))

    def test_authority_contract_is_hash_bound_and_cannot_be_reinitialized(self):
        import shutil
        from wbi_core.security import validate_authority, write_default_authority
        from wbi_core.workspace import init_run, verify_run_seal
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            target = root / "target"
            shutil.copytree(ROOT, target, ignore=shutil.ignore_patterns(".git", "__pycache__", "MANIFEST.sha256"))
            ws = root / "run"
            run = init_run(target, ws, ROOT, ["incremental"], valid_as_of="2026-07-26")
            self.assertEqual(validate_authority(ws)["status"], "PASS")
            original = write_default_authority(ws)
            self.assertEqual(original["run_id"], run["run_id"])
            path = ws / "control/contracts/authority-contract.json"
            path.chmod(0o644)
            data = json.loads(path.read_text())
            data["production_environment"] = True
            write_json(path, data)
            self.assertTrue(verify_run_seal(ws, json.loads((ws / "run.json").read_text())))
            self.assertEqual(validate_authority(ws)["status"], "BLOCKED")
            with self.assertRaises(ValueError):
                write_default_authority(ws)


    def test_evidence_command_scan_is_bounded(self):
        from unittest import mock
        from wbi_core.security import validate_authority
        from wbi_core.workspace import init_run
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            target = root / "target"
            shutil.copytree(ROOT, target, ignore=shutil.ignore_patterns(".git", "__pycache__", "MANIFEST.sha256"))
            ws = root / "run"
            init_run(target, ws, ROOT, ["incremental"], valid_as_of="2026-07-26")
            write_json(ws / "evidence/a.json", {"commands": ["echo a"]})
            write_json(ws / "evidence/b.json", {"commands": ["echo b"]})
            with mock.patch.dict(os.environ, {"WBI_MAX_EVIDENCE_JSON_FILES": "1"}):
                result = validate_authority(ws)
            self.assertEqual(result["status"], "BLOCKED", result)
            self.assertTrue(any("scan budget exceeded" in item for item in result["errors"]))

    def test_linked_evidence_root_is_rejected(self):
        from wbi_core.security import validate_authority
        from wbi_core.workspace import init_run
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            target = root / "target"
            shutil.copytree(ROOT, target, ignore=shutil.ignore_patterns(".git", "__pycache__", "MANIFEST.sha256"))
            ws = root / "run"
            init_run(target, ws, ROOT, ["incremental"], valid_as_of="2026-07-26")
            evidence = ws / "evidence"
            shutil.rmtree(evidence)
            external = root / "external-evidence"
            external.mkdir()
            try:
                evidence.symlink_to(external, target_is_directory=True)
            except OSError:
                self.skipTest("symlinks unavailable")
            result = validate_authority(ws)
            self.assertEqual(result["status"], "BLOCKED", result)
            self.assertTrue(any("evidence root" in item for item in result["errors"]))



if __name__ == "__main__":
    unittest.main()
