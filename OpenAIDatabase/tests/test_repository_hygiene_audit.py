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

    def test_voice_router_archive_exception_is_exact(self) -> None:
        approved = (
            "OpenAIDatabase/docs/source_packages/"
            "codex_adaptive_voice_router_v1_1_1/"
            "codex-adaptive-human-voice-router-v1.1.1.zip"
        )
        nearby = f"{approved}.copy.zip"
        violations = hygiene.evaluate_inventory(
            {
                approved: 31_551,
                nearby: 31_551,
            },
            self.policy,
        )
        self.assertEqual(
            violations,
            [
                {
                    "path": nearby,
                    "reason": "unapproved_tracked_archive",
                    "bytes": 31_551,
                }
            ],
        )

    def test_verifier_archive_exception_is_exact(self) -> None:
        approved = (
            "OpenAIDatabase/docs/source_packages/"
            "verifier_v2_1_product_design_aligned/"
            "verifier-v2.1-product-design-aligned-single-review.zip"
        )
        nearby = f"{approved}.copy.zip"
        violations = hygiene.evaluate_inventory(
            {
                approved: 196_507,
                nearby: 196_507,
            },
            self.policy,
        )
        self.assertEqual(
            violations,
            [
                {
                    "path": nearby,
                    "reason": "unapproved_tracked_archive",
                    "bytes": 196_507,
                }
            ],
        )

    def test_registered_persona_archive_exceptions_are_exact(self) -> None:
        approved = [
            (
                "CodexSkills/registry/codex/persona-distiller-group/政治法律家/"
                "beth-wilkinson/versions/0.0.0.1/"
                "beth-wilkinson-persona-distillation-delivery-v0.0.0.1.zip"
            ),
            (
                "CodexSkills/registry/codex/persona-distiller-group/政治法律家/"
                "evan-r-chesler/versions/0.0.0.1/"
                "evan-r-chesler-persona-distillation-delivery-v0.0.0.1.zip"
            ),
            (
                "CodexSkills/registry/codex/persona-distiller-group/政治法律家/"
                "theodore-v-wells-jr/versions/0.0.0.1/"
                "theodore-v-wells-jr-persona-distillation-delivery-v0.0.0.1.zip"
            ),
            (
                "CodexSkills/registry/codex/persona-distiller-group/多重身份/"
                "robert-a-kindler/versions/0.0.0.1/"
                "robert-a-kindler-persona-distillation-delivery-v0.0.0.1.zip"
            ),
            (
                "CodexSkills/registry/codex/persona-distiller-group/政治法律家/"
                "h-rodgin-cohen/versions/0.0.0.1/"
                "h-rodgin-cohen-persona-distillation-delivery-v0.0.0.1.zip"
            ),
            (
                "CodexSkills/registry/codex/persona-distiller-group/政治法律家/"
                "scott-a-barshay/versions/0.0.0.1/"
                "scott-a-barshay-persona-distillation-delivery-v0.0.0.1.zip"
            ),
        ]
        inventory = {
            **{path: 200_000 for path in approved},
            **{f"{path}.copy.zip": 200_000 for path in approved},
        }
        violations = hygiene.evaluate_inventory(inventory, self.policy)
        self.assertEqual(
            violations,
            [
                {
                    "path": f"{path}.copy.zip",
                    "reason": "unapproved_tracked_archive",
                    "bytes": 200_000,
                }
                for path in sorted(approved)
            ],
        )

    def test_recurring_prompt_large_object_ceiling_is_exact(self) -> None:
        prefix = (
            "OpenAIDatabase/data/derived/behavior_intelligence/"
            "recurring_prompts/"
        )
        current = f"{prefix}occurrences.jsonl"
        violations = hygiene.evaluate_inventory(
            {
                current: 95_617_956,
                f"{prefix}growth.jsonl": 95_617_957,
            },
            self.policy,
        )
        self.assertEqual(
            violations,
            [
                {
                    "path": f"{prefix}growth.jsonl",
                    "reason": "tracked_blob_exceeds_bound",
                    "bytes": 95_617_957,
                    "max_bytes": 95_617_956,
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()
