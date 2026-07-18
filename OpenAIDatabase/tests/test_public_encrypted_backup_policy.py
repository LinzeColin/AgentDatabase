from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path


DATABASE_DIR = Path(__file__).resolve().parents[1]
SCRIPT = DATABASE_DIR / "scripts/validate_public_encrypted_backup_policy.py"
POLICY_PATH = DATABASE_DIR / "config/storage/public_encrypted_backup_policy.json"


def load_module():
    spec = importlib.util.spec_from_file_location("public_encrypted_backup_policy", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load public encrypted backup policy validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PublicEncryptedBackupPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()
        cls.policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))

    def test_unprovisioned_policy_is_valid_but_not_upload_ready(self) -> None:
        result = self.module.validate_policy(self.policy)
        self.assertEqual(result["status"], "PASS")
        self.assertFalse(result["ready_for_upload"])
        with self.assertRaisesRegex(self.module.BackupPolicyError, "backup_key_not_provisioned"):
            self.module.validate_policy(self.policy, require_ready=True)

    def test_policy_rejects_plaintext_or_git_tracked_ciphertext(self) -> None:
        for key in ("plaintext_publication_allowed", "git_tracked_ciphertext_allowed"):
            candidate = copy.deepcopy(self.policy)
            candidate["scope"][key] = True
            with self.subTest(key=key), self.assertRaisesRegex(
                self.module.BackupPolicyError, "scope_policy_invalid"
            ):
                self.module.validate_policy(candidate)

    def test_policy_rejects_automatic_source_deletion_and_unified_key_export(self) -> None:
        candidate = copy.deepcopy(self.policy)
        candidate["scope"]["automatic_source_deletion_allowed"] = True
        with self.assertRaisesRegex(self.module.BackupPolicyError, "scope_policy_invalid"):
            self.module.validate_policy(candidate)
        candidate = copy.deepcopy(self.policy)
        candidate["unified_key"]["key_export_allowed"] = True
        with self.assertRaisesRegex(self.module.BackupPolicyError, "unified_key_policy_invalid"):
            self.module.validate_policy(candidate)

    def test_policy_rejects_a_manifest_that_can_name_or_expose_sources(self) -> None:
        for key in (
            "source_absolute_path_allowed",
            "source_file_name_allowed",
            "plaintext_content_allowed",
            "credential_or_key_material_allowed",
        ):
            candidate = copy.deepcopy(self.policy)
            candidate["manifest"][key] = True
            with self.subTest(key=key), self.assertRaisesRegex(
                self.module.BackupPolicyError, "manifest_policy_invalid"
            ):
                self.module.validate_policy(candidate)


if __name__ == "__main__":
    unittest.main()
