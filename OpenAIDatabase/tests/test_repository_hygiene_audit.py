from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


DATABASE_DIR = Path(__file__).resolve().parents[1]
ROOT = DATABASE_DIR.parent
SCRIPTS_DIR = DATABASE_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import repository_hygiene_audit as hygiene  # noqa: E402


class RepositoryHygieneAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = json.loads(
            (DATABASE_DIR / "config/storage/repository_hygiene.json").read_text(
                encoding="utf-8"
            )
        )

    def test_current_migrated_worktree_is_within_declared_bounds(self) -> None:
        report = hygiene.audit(ROOT)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["violations"], [])
        self.assertEqual(report["policy_errors"], [])

    def test_large_unapproved_blob_and_secret_filename_fail_closed(self) -> None:
        violations = hygiene.evaluate_inventory(
            {
                "unexpected.bin": 1_048_577,
                "config/.env": 10,
            },
            self.policy,
        )
        self.assertEqual(
            {row["reason"] for row in violations},
            {"tracked_blob_exceeds_bound", "forbidden_credential_shape"},
        )


if __name__ == "__main__":
    unittest.main()
