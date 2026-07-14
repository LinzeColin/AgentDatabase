from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from audit_memory_atlas_human_plane import EXPECTED_FILES, audit


VALID_BODY = "这是面向所有者的中文结论和执行说明，包含明确边界、验证方法、失败停止条件与恢复步骤。" * 12


class HumanPlaneAuditTests(unittest.TestCase):
    def make_database(self, root: Path) -> Path:
        database_dir = root / "OpenAIDatabase"
        human_dir = database_dir / "人类可读"
        human_dir.mkdir(parents=True)
        for name in EXPECTED_FILES:
            (human_dir / name).write_text(
                f"# 中文标题\n\n## 结论\n\n{VALID_BODY}\n\n## 操作\n\n{VALID_BODY}\n",
                encoding="utf-8",
            )
        return database_dir

    def test_valid_seven_file_plane_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report = audit(self.make_database(Path(temp_dir)))

        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["file_count"], 7)
        self.assertEqual(report["nested_file_count"], 0)

    def test_missing_required_file_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_dir = self.make_database(Path(temp_dir))
            (database_dir / "人类可读" / "快速开始.md").unlink()
            report = audit(database_dir)

        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any("核心文件集合不一致" in error for error in report["errors"]))

    def test_mojibake_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_dir = self.make_database(Path(temp_dir))
            target = database_dir / "人类可读" / "快速开始.md"
            target.write_text(target.read_text(encoding="utf-8") + "\n锟斤拷\n", encoding="utf-8")
            report = audit(database_dir)

        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any("乱码标记" in error for error in report["errors"]))

    def test_inline_link_cannot_escape_human_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_dir = self.make_database(Path(temp_dir))
            outside = database_dir / "outside.md"
            outside.write_text("outside", encoding="utf-8")
            target = database_dir / "人类可读" / "快速开始.md"
            target.write_text(target.read_text(encoding="utf-8") + "\n[越界](../outside.md)\n", encoding="utf-8")
            report = audit(database_dir)

        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any("人类目录外链接" in error for error in report["errors"]))

    def test_reference_style_link_cannot_escape_human_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_dir = self.make_database(Path(temp_dir))
            outside = database_dir / "outside.md"
            outside.write_text("outside", encoding="utf-8")
            target = database_dir / "人类可读" / "快速开始.md"
            target.write_text(
                target.read_text(encoding="utf-8") + "\n[越界][详情]\n\n[详情]: ../outside.md\n",
                encoding="utf-8",
            )
            report = audit(database_dir)

        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any("人类目录外链接" in error for error in report["errors"]))

    def test_absolute_local_link_cannot_escape_human_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_dir = self.make_database(Path(temp_dir))
            outside = database_dir / "outside.md"
            outside.write_text("outside", encoding="utf-8")
            target = database_dir / "人类可读" / "快速开始.md"
            target.write_text(
                target.read_text(encoding="utf-8") + f"\n[绝对路径](<{outside}>)\n",
                encoding="utf-8",
            )
            report = audit(database_dir)

        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any("人类目录外链接" in error for error in report["errors"]))


if __name__ == "__main__":
    unittest.main()
