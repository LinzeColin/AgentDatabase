from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


DATABASE_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = DATABASE_DIR / "scripts"
FIXTURE = DATABASE_DIR / "tests/fixtures/memory_settlement_defaults.json"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import memory_settlement_policy as policy  # noqa: E402


class MemorySettlementPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.defaults = json.loads(FIXTURE.read_text(encoding="utf-8"))["defaults"]

    def test_local_policy_replaces_retired_root_dependency(self) -> None:
        self.assertFalse((DATABASE_DIR.parent / "scripts/agent_loop").exists())
        self.assertEqual(policy.decide(self.defaults)["action"], "MERGE_DELETE")

    def test_duplicate_and_untrusted_orphan_fail_safe(self) -> None:
        duplicate = policy.decide({**self.defaults, "duplicate_event": True})
        orphan = policy.decide(
            {
                **self.defaults,
                "orphan": True,
                "pr_state": "missing",
                "trusted_marker": False,
            }
        )
        self.assertEqual(duplicate["action"], "NOOP")
        self.assertEqual(orphan["action"], "BLOCK")

    def test_missing_boolean_is_rejected(self) -> None:
        invalid = dict(self.defaults)
        invalid.pop("required_checks_pass")
        with self.assertRaisesRegex(
            policy.SettlementPolicyError,
            "required_checks_pass must be boolean",
        ):
            policy.decide(invalid)


if __name__ == "__main__":
    unittest.main()
