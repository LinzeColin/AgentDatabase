from __future__ import annotations

import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path


DATABASE_DIR = Path(__file__).resolve().parents[1]
SCRIPT = DATABASE_DIR / "scripts/validate_private_encrypted_backup_policy.py"
POLICY_PATH = DATABASE_DIR / "config/storage/private_encrypted_backup_policy.json"
PUBLIC_POLICY_PATH = DATABASE_DIR / "config/storage/public_encrypted_backup_policy.json"
SCRIPTS_DIR = DATABASE_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def load_module():
    spec = importlib.util.spec_from_file_location("private_encrypted_backup_policy", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load private encrypted backup policy validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PrivateEncryptedBackupPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()
        cls.policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
        cls.public_policy = json.loads(PUBLIC_POLICY_PATH.read_text(encoding="utf-8"))

    def test_ready_policy_targets_private_database_and_isolated_workspace(self) -> None:
        result = self.module.validate_policy(self.policy, self.public_policy, require_ready=True)
        self.assertEqual(result["status"], "PASS")
        self.assertTrue(result["ready_for_upload"])
        self.assertEqual(result["release_repository"], "LinzeColin/Private-Database")
        self.assertEqual(
            result["workspace_isolation"],
            "protected_incremental_journal_plus_system_temporary_payloads",
        )
        registry = json.loads(
            (DATABASE_DIR.parent / "ops/memory-atlas/source-registry.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            self.policy["scope"]["logical_sources"],
            [row["source_id"] for row in registry["sources"]],
        )
        self.assertEqual(self.policy["scope"]["logical_sources"], self.module.EXPECTED_LOGICAL_SOURCES)

    def test_policy_rejects_another_repository_or_shared_workspace_writes(self) -> None:
        candidate = copy.deepcopy(self.policy)
        candidate["release"]["repository"] = "LinzeColin/AgentDatabase"
        with self.assertRaisesRegex(self.module.PrivateBackupPolicyError, "release_policy_invalid"):
            self.module.validate_policy(candidate, self.public_policy)
        candidate = copy.deepcopy(self.policy)
        candidate["automation"]["shared_cwd_write_allowed"] = True
        with self.assertRaisesRegex(self.module.PrivateBackupPolicyError, "automation_policy_invalid"):
            self.module.validate_policy(candidate, self.public_policy)
        candidate = copy.deepcopy(self.policy)
        candidate["automation"]["local_script_creation_allowed"] = True
        with self.assertRaisesRegex(self.module.PrivateBackupPolicyError, "automation_policy_invalid"):
            self.module.validate_policy(candidate, self.public_policy)

    def test_policy_rejects_source_deletion_or_local_key_copy(self) -> None:
        candidate = copy.deepcopy(self.policy)
        candidate["scope"]["automatic_source_deletion_allowed"] = True
        with self.assertRaisesRegex(self.module.PrivateBackupPolicyError, "scope_policy_invalid"):
            self.module.validate_policy(candidate, self.public_policy)
        candidate = copy.deepcopy(self.policy)
        candidate["unified_key"]["identity_file_persisted"] = True
        with self.assertRaisesRegex(self.module.PrivateBackupPolicyError, "unified_key_policy_invalid"):
            self.module.validate_policy(candidate, self.public_policy)

    def test_policy_rejects_a_key_id_that_diverges_from_canonical_public_key(self) -> None:
        candidate = copy.deepcopy(self.policy)
        candidate["unified_key"]["key_id"] = "different-key"
        with self.assertRaisesRegex(self.module.PrivateBackupPolicyError, "unified_key_policy_invalid"):
            self.module.validate_policy(candidate, self.public_policy)


if __name__ == "__main__":
    unittest.main()
