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

    def test_verifier_v022_archive_exception_is_exact(self) -> None:
        approved = (
            "OpenAIDatabase/docs/source_packages/"
            "verifier_v0_0_2_2/verifier-skill-v0.0.2.2.zip"
        )
        nearby = f"{approved}.copy.zip"
        violations = hygiene.evaluate_inventory(
            {
                approved: 533_392,
                nearby: 533_392,
            },
            self.policy,
        )
        self.assertEqual(
            violations,
            [
                {
                    "path": nearby,
                    "reason": "unapproved_tracked_archive",
                    "bytes": 533_392,
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

    def test_persona_distiller_large_object_ceilings_are_exact(self) -> None:
        """2026-08-20 新开的三个 2 MiB 口子：每个都要能挡住多一个字节。

        白名单是「口子」不是「豁免」—— 只加条目不加负控，等于把上界写成无穷。
        """
        cap = 2 * 1024 * 1024
        pd = "CodexSkills/skill_log_evals/persona-distiller"
        prefixes = (
            f"{pd}/_ledgers/",
            f"{pd}/_corpora/wip-galen-101/raw/",
            "CodexSkills/registry/codex/persona-distiller-group/evidence/",
        )
        for prefix in prefixes:
            with self.subTest(prefix=prefix):
                violations = hygiene.evaluate_inventory(
                    {
                        f"{prefix}at_ceiling.json": cap,
                        f"{prefix}over_ceiling.json": cap + 1,
                    },
                    self.policy,
                )
                self.assertEqual(
                    violations,
                    [
                        {
                            "path": f"{prefix}over_ceiling.json",
                            "reason": "tracked_blob_exceeds_bound",
                            "bytes": cap + 1,
                            "max_bytes": cap,
                        }
                    ],
                )

    def test_persona_distiller_refetch_bodies_stay_untracked(self) -> None:
        """_refetch/items/ 的正文若再被跟踪，必须重新报错。

        它们是 2026-08-20 之前唯一没被 .gitignore 五条规则盖到的一类，
        63.1 MB 就是这么混进来的。规则删掉后这条会红。
        """
        body = (
            f"CodexSkills/skill_log_evals/persona-distiller/_corpora/"
            f"wip-adams-131/workspaces/comfort-avery-adams/_refetch/items/"
            f"whoswhoinenginee00leon.txt"
        )
        violations = hygiene.evaluate_inventory({body: 19_005_952}, self.policy)
        self.assertEqual(
            [row["reason"] for row in violations], ["tracked_blob_exceeds_bound"]
        )

    def test_new_persona_archives_are_allowlisted_one_by_one(self) -> None:
        """新加的 8 个交付物 zip 沿用既有 108 条的样式：精确到文件，不是目录前缀。

        写成目录前缀的话，往那棵树里塞任何 zip 都不会被发现。
        """
        approved = (
            "CodexSkills/registry/codex/persona-distiller-group/财务合规师/"
            "walter-a-shewhart/versions/0.0.0.1/"
            "walter-a-shewhart-persona-distillation-delivery-v0.0.0.1.zip"
        )
        self.assertIn(approved, self.policy["allowed_archive_prefixes"])
        nearby = f"{approved}.copy.zip"
        violations = hygiene.evaluate_inventory(
            {approved: 73_530, nearby: 73_530}, self.policy
        )
        self.assertEqual(
            violations,
            [
                {
                    "path": nearby,
                    "reason": "unapproved_tracked_archive",
                    "bytes": 73_530,
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()
