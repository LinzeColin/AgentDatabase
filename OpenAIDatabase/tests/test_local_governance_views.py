from __future__ import annotations

import sys
import unittest
from pathlib import Path


DATABASE_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = DATABASE_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import lean_governance  # noqa: E402


class LocalGovernanceViewTests(unittest.TestCase):
    def test_current_canonical_facts_render_all_owner_views(self) -> None:
        views = lean_governance.build_views(DATABASE_DIR)
        self.assertEqual(set(views), set(lean_governance.VIEW_NAMES))
        self.assertIn("project_id: `OpenAIDatabase`", views["功能清单.md"])
        self.assertIn("## Stage -> Phase -> Task", views["开发记录.md"])
        self.assertIn("active_model_count", views["模型参数文件.md"])
        self.assertNotIn("LinzeColin/CodexProject", "\n".join(views.values()))

    def test_governance_validation_fails_closed_on_view_drift(self) -> None:
        report = lean_governance._validate(DATABASE_DIR, enforce_sync=True)
        self.assertIn(report["status"], {"PASS", "FAIL_CLOSED"})
        if report["status"] == "FAIL_CLOSED":
            self.assertTrue(
                all(error.startswith("generated_view_drift:") for error in report["errors"])
            )


if __name__ == "__main__":
    unittest.main()
