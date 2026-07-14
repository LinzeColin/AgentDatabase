from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
REPO_ROOT = ROOT.parent
ROOT_SCRIPTS = REPO_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
if str(ROOT_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(ROOT_SCRIPTS))

from audit_memory_atlas_human_plane import EXPECTED_FILES, OWNER_ENTRY_CONTRACT, audit


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
        contract = json.loads((ROOT / OWNER_ENTRY_CONTRACT).read_text(encoding="utf-8"))
        config_dir = database_dir / "config"
        config_dir.mkdir()
        (database_dir / OWNER_ENTRY_CONTRACT).write_text(
            json.dumps(contract, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        for filename, file_contract in contract["files"].items():
            sections = [
                "## 当前状态",
                "- Task Pack 进度：30/149。",
                "- 当前 Task：S05-P1-T3。",
                "- 发布状态：未发布。",
                "",
                "## 下一步",
                "- 下一 Task：只执行 S05-P1-T3。",
            ]
            for section in file_contract["required_sections"]:
                if section not in {"## 当前状态", "## 下一步"}:
                    body = "- 直接说明当前结论和操作。"
                    if section == "## 关键参数":
                        body = "- " + "、".join(contract["key_parameter_ids"])
                    sections.extend(["", section, body])
            (database_dir / filename).write_text(
                f"# {Path(filename).stem}\n\n" + "\n".join(sections) + "\n",
                encoding="utf-8",
            )
        return database_dir

    def test_valid_seven_file_plane_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report = audit(self.make_database(Path(temp_dir)))

        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["file_count"], 7)
        self.assertEqual(report["nested_file_count"], 0)
        self.assertEqual(len(report["owner_entries"]), 3)

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

    def test_owner_entry_missing_next_step_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_dir = self.make_database(Path(temp_dir))
            target = database_dir / "功能清单.md"
            target.write_text(target.read_text(encoding="utf-8").replace("## 下一步", "## 后续"), encoding="utf-8")
            report = audit(database_dir)

        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any("缺少必需段落：## 下一步" in error for error in report["errors"]))

    def test_owner_entry_next_step_must_be_in_first_eighteen_lines(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_dir = self.make_database(Path(temp_dir))
            target = database_dir / "开发记录.md"
            text = target.read_text(encoding="utf-8").replace("## 下一步", ("占位\n" * 20) + "## 下一步")
            target.write_text(text, encoding="utf-8")
            report = audit(database_dir)

        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any("下一步出现过晚" in error for error in report["errors"]))

    def test_owner_entry_size_limit_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_dir = self.make_database(Path(temp_dir))
            target = database_dir / "模型参数文件.md"
            target.write_text(target.read_text(encoding="utf-8") + ("参数说明" * 2000), encoding="utf-8")
            report = audit(database_dir)

        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any("超过 6000 bytes" in error for error in report["errors"]))

    def test_owner_contract_cannot_weaken_two_minute_limits(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_dir = self.make_database(Path(temp_dir))
            contract_path = database_dir / OWNER_ENTRY_CONTRACT
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            contract["max_bytes_per_file"] = 60000
            contract_path.write_text(json.dumps(contract, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            report = audit(database_dir)

        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any("不得放宽 max_bytes_per_file" in error for error in report["errors"]))

    def test_current_owner_entries_are_renderer_owned_and_concise(self) -> None:
        import lean_governance
        import validate_project_governance

        project_facts, roadmap, events = lean_governance.load_project_facts(ROOT)
        rendered = lean_governance.rendered_project_texts(project_facts, roadmap, events)
        report = audit(ROOT)
        validation = validate_project_governance.Validation()
        validate_project_governance.check_human_entry_quality(validation, ROOT, True, "OpenAIDatabase")

        self.assertEqual(report["status"], "PASS", report["errors"])
        self.assertEqual(validation.errors, [])
        for filename, expected in rendered.items():
            with self.subTest(filename=filename):
                self.assertEqual((ROOT / filename).read_text(encoding="utf-8"), expected)
        self.assertTrue(all(int(item["next_heading_line"]) <= 18 for item in report["owner_entries"]))

    def test_non_memory_atlas_project_keeps_generic_renderer(self) -> None:
        import lean_governance

        project_facts = {
            "project_id": "ExampleProject",
            "version": "1.0.0",
            "fact_level": "EXTRACTED",
            "features": [],
            "evidence_refs": [],
        }
        roadmap = {
            "project_id": "ExampleProject",
            "current_stage_id": "S1",
            "current_phase_id": "P1",
            "current_task_id": "T1",
            "next_gate_id": "G1",
            "stages": [],
        }

        rendered = lean_governance.render_feature_list(project_facts, roadmap)

        self.assertIn("## 摘要", rendered)
        self.assertIn("## 功能概览", rendered)
        self.assertIn("## 证据", rendered)
        self.assertNotIn("## 当前状态", rendered)


if __name__ == "__main__":
    unittest.main()
