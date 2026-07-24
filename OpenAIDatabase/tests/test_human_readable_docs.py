from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
DATABASE_DIR = TEST_DIR.parent
REPO_ROOT = DATABASE_DIR.parent
SCRIPTS_DIR = DATABASE_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from update_human_readable_recurring import (  # noqa: E402
    ConsolidationError,
    build_consolidated_document,
    load_config as load_update_config,
    replace_generated_block,
)
from validate_human_readable_docs import (  # noqa: E402
    load_config as load_validation_config,
    validate_repository,
)


class HumanReadableConsolidationTests(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.config_path = DATABASE_DIR / "config/human_readable_merge.v1.json"
        cls.config = load_update_config(cls.config_path)
        fixture_dir = TEST_DIR / "fixtures/human_readable_docs"
        cls.base = (fixture_dir / "base_index.md").read_text(encoding="utf-8")
        cls.summary = (fixture_dir / "summary.md").read_text(encoding="utf-8")
        cls.status = (fixture_dir / "status.md").read_text(encoding="utf-8")

    def test_generated_refresh_preserves_static_and_rewrites_legacy_paths(self) -> None:
        assembled = build_consolidated_document(
            self.base,
            self.summary,
            self.status,
            self.config,
        )
        self.assertIn("STATIC-SENTINEL", assembled)
        self.assertIn(
            "00_快速入口与Recurring.md#src-00-recurring-status",
            assembled,
        )
        self.assertIn(
            "./00_快速入口与Recurring.md#src-00-recurring-analysis",
            assembled,
        )
        self.assertNotIn("`00_Recurring运行状态.md`", assembled)
        self.assertNotIn("](./00_Recurring分析_最新.md)", assembled)

    def test_generated_refresh_is_idempotent(self) -> None:
        first = build_consolidated_document(
            self.base,
            self.summary,
            self.status,
            self.config,
        )
        second = build_consolidated_document(
            first,
            self.summary,
            self.status,
            self.config,
        )
        self.assertEqual(first, second)

    def test_duplicate_or_missing_generated_markers_fail_closed(self) -> None:
        duplicate = self.base + "\n<!-- BEGIN GENERATED: recurring-analysis -->\nx\n<!-- END GENERATED: recurring-analysis -->\n"
        with self.assertRaises(ConsolidationError):
            replace_generated_block(duplicate, "recurring-analysis", "replacement")
        with self.assertRaises(ConsolidationError):
            replace_generated_block("no markers", "recurring-analysis", "replacement")

    def _copy_contract_repo(self, root: Path) -> None:
        shutil.copytree(
            DATABASE_DIR / "人类可读",
            root / "OpenAIDatabase/人类可读",
        )
        config_target = root / "OpenAIDatabase/config/human_readable_merge.v1.json"
        config_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.config_path, config_target)

    def test_repository_contract_passes(self) -> None:
        config = load_validation_config(self.config_path)
        self.assertEqual(validate_repository(REPO_ROOT, config), [])

    def test_extra_markdown_file_fails_exact_count(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._copy_contract_repo(root)
            (root / "OpenAIDatabase/人类可读/08_不应存在.md").write_text(
                "# extra\n", encoding="utf-8"
            )
            config = load_validation_config(
                root / "OpenAIDatabase/config/human_readable_merge.v1.json"
            )
            errors = validate_repository(root, config)
            self.assertTrue(any("expected exactly 8" in error for error in errors), errors)
            self.assertTrue(any("filename set mismatch" in error for error in errors), errors)

    def test_static_source_tampering_fails_hash_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._copy_contract_repo(root)
            target = root / "OpenAIDatabase/人类可读/07_DiffNarrator与Apply回滚.md"
            target.write_text(
                target.read_text(encoding="utf-8").replace(
                    "# Diff Narrator 说明",
                    "# Diff Narrator 说明（被篡改）",
                    1,
                ),
                encoding="utf-8",
            )
            config = load_validation_config(
                root / "OpenAIDatabase/config/human_readable_merge.v1.json"
            )
            errors = validate_repository(root, config)
            self.assertTrue(any("static source body changed" in error for error in errors), errors)

    def test_source_order_tampering_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._copy_contract_repo(root)
            target = root / "OpenAIDatabase/人类可读/07_DiffNarrator与Apply回滚.md"
            text = target.read_text(encoding="utf-8")
            first = text.index("<!-- BEGIN SOURCE: src-35-diff-narrator;")
            second = text.index("<!-- BEGIN SOURCE: src-36-apply-rollback;")
            prefix = text[:first]
            block_a = text[first:second]
            block_b = text[second:]
            target.write_text(prefix + block_b + "\n" + block_a, encoding="utf-8")
            config = load_validation_config(
                root / "OpenAIDatabase/config/human_readable_merge.v1.json"
            )
            errors = validate_repository(root, config)
            self.assertTrue(any("source order violation" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
