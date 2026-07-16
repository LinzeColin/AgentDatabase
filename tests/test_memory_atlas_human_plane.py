from __future__ import annotations

import json
import subprocess
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

from audit_memory_atlas_human_plane import (
    CHANGE_USAGE_MAP_CONTRACT,
    EXPECTED_FILES,
    MACHINE_PLANE_CLEANUP_CONTRACT,
    MACHINE_TRUTH_INDEX_CONTRACT,
    OWNER_ENTRY_CONTRACT,
    audit,
    validate_machine_plane_cleanup_contract,
)


VALID_BODY = "这是面向所有者的中文结论和执行说明，包含明确边界、验证方法、失败停止条件与恢复步骤。" * 12


class HumanPlaneAuditTests(unittest.TestCase):
    @staticmethod
    def valid_machine_truth_index_text(contract: dict[str, object]) -> str:
        lines = [
            "# Memory Atlas 机器真相索引",
            "",
            "## 结论",
            "",
            "- 本页只保存路径与职责，不复制执行事实。",
            "",
            "## 操作",
            "",
            "- 修改事实时打开对应 canonical target。",
            "",
            "## 五域索引",
        ]
        domains = contract["domains"]
        assert isinstance(domains, list)
        for domain in domains:
            assert isinstance(domain, dict)
            lines.extend(["", f"### {domain['id']}｜{domain['label']}", ""])
            entries = domain["entries"]
            assert isinstance(entries, list)
            for entry in entries:
                assert isinstance(entry, dict)
                path = str(entry["path"])
                lines.append(f"- [{path}](../{path})")
        lines.extend(
            [
                "",
                "## 变更规则",
                "",
                "- 只编辑 canonical owner。",
                "",
                "## 边界",
                "",
                "- 本 Task 不删除历史目录或证据。",
            ]
        )
        return "\n".join(lines) + "\n"

    @staticmethod
    def valid_change_map_text(contract: dict[str, object]) -> str:
        lines = [
            "# Memory Atlas v1.2.1 变化与使用地图",
            "",
            "## 结论",
            "",
            "当前仍未推送 GitHub main、未部署，后续能力尚未完成。",
            "",
            "## 操作",
            "",
            "先看变化，再选择一个流程执行。",
            "",
            "## 本次交付改变了什么",
        ]
        categories = contract["change_categories"]
        assert isinstance(categories, dict)
        for category_name, raw_items in categories.items():
            lines.extend(["", f"### {category_name}", ""])
            assert isinstance(raw_items, list)
            for item in raw_items:
                assert isinstance(item, dict)
                lines.append(f"- {item['name']}：{item['description']}")
        lines.extend(["", "## 五个核心用户流程"])
        workflows = contract["workflows"]
        assert isinstance(workflows, list)
        for index, workflow in enumerate(workflows, start=1):
            assert isinstance(workflow, dict)
            lines.extend(
                [
                    "",
                    f"### {index}. {workflow['name']}",
                    "",
                    f"- 入口：{workflow['entry']}",
                ]
            )
            steps = workflow["steps"]
            assert isinstance(steps, list)
            lines.extend(f"- 步骤：{step}" for step in steps)
            lines.extend(
                [
                    f"- 结果：{workflow['result']}",
                    f"- 当前状态：{workflow['current_state']}",
                    f"- 边界：{workflow['boundary']}",
                ]
            )
        lines.extend(
            [
                "",
                "## 尚未交付",
                "",
                "- 后续能力尚未完成。",
                "",
                "## 后续路线",
                "",
                "- 按 TaskPack 顺序继续。",
                "",
                "## 交付规则",
                "",
                "- 一次 run 只完成一个 Task。",
            ]
        )
        return "\n".join(lines) + "\n"

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
        change_map_contract = json.loads((ROOT / CHANGE_USAGE_MAP_CONTRACT).read_text(encoding="utf-8"))
        (database_dir / CHANGE_USAGE_MAP_CONTRACT).write_text(
            json.dumps(change_map_contract, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        machine_truth_contract = json.loads((ROOT / MACHINE_TRUTH_INDEX_CONTRACT).read_text(encoding="utf-8"))
        (database_dir / MACHINE_TRUTH_INDEX_CONTRACT).write_text(
            json.dumps(machine_truth_contract, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        for domain in machine_truth_contract["domains"]:
            for entry in domain["entries"]:
                target = database_dir / entry["path"]
                if entry["target_kind"] == "directory":
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text("test fixture\n", encoding="utf-8")
        machine_dir = database_dir / "机器治理"
        machine_dir.mkdir(exist_ok=True)
        (machine_dir / "README.md").write_text(
            self.valid_machine_truth_index_text(machine_truth_contract),
            encoding="utf-8",
        )
        (human_dir / "版本路线图.md").write_text(
            self.valid_change_map_text(change_map_contract),
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

    def test_change_usage_map_requires_all_three_change_categories(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_dir = self.make_database(Path(temp_dir))
            target = database_dir / "人类可读" / "版本路线图.md"
            target.write_text(target.read_text(encoding="utf-8").replace("### 删除或隐藏", "### 其他"), encoding="utf-8")
            report = audit(database_dir)

        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any("缺少变化类别：删除或隐藏" in error for error in report["errors"]))

    def test_change_usage_map_contract_requires_exactly_five_workflows(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_dir = self.make_database(Path(temp_dir))
            contract_path = database_dir / CHANGE_USAGE_MAP_CONTRACT
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            contract["workflows"] = contract["workflows"][:-1]
            contract_path.write_text(json.dumps(contract, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            report = audit(database_dir)

        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any("精确定义五个核心用户流程" in error for error in report["errors"]))

    def test_change_usage_map_contract_cannot_weaken_size_limits(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_dir = self.make_database(Path(temp_dir))
            contract_path = database_dir / CHANGE_USAGE_MAP_CONTRACT
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            contract["max_lines"] = 1600
            contract_path.write_text(json.dumps(contract, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            report = audit(database_dir)

        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any("不得放宽 max_lines" in error for error in report["errors"]))

    def test_machine_truth_index_requires_exact_five_domains(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_dir = self.make_database(Path(temp_dir))
            contract_path = database_dir / MACHINE_TRUTH_INDEX_CONTRACT
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            contract["domains"] = contract["domains"][:-1]
            contract_path.write_text(json.dumps(contract, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            report = audit(database_dir)

        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any("精确定义 requirements/source/model/acceptance/evidence 五域" in error for error in report["errors"]))

    def test_machine_truth_index_rejects_fact_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_dir = self.make_database(Path(temp_dir))
            contract_path = database_dir / MACHINE_TRUTH_INDEX_CONTRACT
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            contract["current_status"] = "complete"
            contract["domains"][0]["status"] = "complete"
            contract["domains"][0]["entries"][0]["status"] = "complete"
            contract_path.write_text(json.dumps(contract, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            report = audit(database_dir)

        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any("合同只能保存 schema、边界、所有权规则与五域" in error for error in report["errors"]))
        self.assertTrue(any("真相域只能保存 id、label、purpose 与 entries" in error for error in report["errors"]))
        self.assertTrue(any("只能保存路径与所有权字段" in error for error in report["errors"]))

    def test_machine_truth_index_rejects_missing_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_dir = self.make_database(Path(temp_dir))
            (database_dir / "config" / "data_sources" / "source_registry.json").unlink()
            report = audit(database_dir)

        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any("机器真相索引文件目标不存在" in error for error in report["errors"]))

    def test_machine_truth_index_cannot_weaken_limits(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_dir = self.make_database(Path(temp_dir))
            contract_path = database_dir / MACHINE_TRUTH_INDEX_CONTRACT
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            contract["max_lines"] = 800
            contract_path.write_text(json.dumps(contract, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            report = audit(database_dir)

        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any("不得放宽 max_lines" in error for error in report["errors"]))

    def test_machine_gate_markers_cannot_pollute_human_plane(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database_dir = self.make_database(Path(temp_dir))
            target = database_dir / "人类可读" / "快速开始.md"
            target.write_text(target.read_text(encoding="utf-8") + "\nvalidate:v1.2-s01\n", encoding="utf-8")
            owner_target = database_dir / "功能清单.md"
            owner_target.write_text(
                owner_target.read_text(encoding="utf-8") + "\nACC-MA-V121-S05-P3-T1\n",
                encoding="utf-8",
            )
            report = audit(database_dir)

        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any("被机器门禁、状态或 hash 污染" in error for error in report["errors"]))
        self.assertTrue(any("功能清单.md 被机器门禁、状态或 hash 污染" in error for error in report["errors"]))

    def test_machine_cleanup_contract_rejects_unapproved_candidate(self) -> None:
        contract = json.loads((ROOT / MACHINE_PLANE_CLEANUP_CONTRACT).read_text(encoding="utf-8"))
        contract["candidates"][0]["approval"] = "pending"

        errors = validate_machine_plane_cleanup_contract(contract)

        self.assertTrue(any("只允许删除已批准候选" in error for error in errors))

    def test_machine_cleanup_contract_rejects_candidate_set_drift(self) -> None:
        contract = json.loads((ROOT / MACHINE_PLANE_CLEANUP_CONTRACT).read_text(encoding="utf-8"))
        contract["candidates"] = contract["candidates"][:-1]

        errors = validate_machine_plane_cleanup_contract(contract)

        self.assertTrue(any("必须精确为八个逐 Stage README" in error for error in errors))

    def test_machine_cleanup_contract_rejects_weakened_inventory(self) -> None:
        contract = json.loads((ROOT / MACHINE_PLANE_CLEANUP_CONTRACT).read_text(encoding="utf-8"))
        contract["inventory_after"]["machine_file_count"] = 999
        contract["protected_sets"][0]["manifest_sha256"] = "0" * 64

        errors = validate_machine_plane_cleanup_contract(contract)

        self.assertTrue(any("after inventory 不得变更" in error for error in errors))
        self.assertTrue(any("受保护基线不得变更" in error for error in errors))

    def test_machine_cleanup_candidates_are_git_recoverable(self) -> None:
        contract = json.loads((ROOT / MACHINE_PLANE_CLEANUP_CONTRACT).read_text(encoding="utf-8"))
        source_commit = contract["source_commit"]

        for candidate in contract["candidates"]:
            repo_path = f"OpenAIDatabase/{candidate['path']}"
            with self.subTest(path=repo_path):
                result = subprocess.run(
                    ["git", "cat-file", "-e", f"{source_commit}:{repo_path}"],
                    cwd=REPO_ROOT,
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)

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
        self.assertEqual(report["change_usage_map"]["workflow_count"], 5)
        self.assertEqual(report["machine_truth_index"]["domain_count"], 5)
        self.assertEqual(report["machine_truth_index"]["target_count"], 11)
        self.assertEqual(report["machine_plane_cleanup"]["candidate_count"], 8)
        self.assertEqual(report["machine_plane_cleanup"]["deleted_count"], 8)
        self.assertEqual(report["machine_plane_cleanup"]["machine_file_count"], 159)
        self.assertEqual(report["machine_plane_cleanup"]["nested_readmes"], [])
        self.assertEqual(report["machine_plane_cleanup"]["protected_sets"]["active_configs"]["file_count"], 33)
        self.assertEqual(report["machine_plane_cleanup"]["protected_sets"]["evidence_payload"]["file_count"], 124)
        self.assertIn("机器治理/README.md", rendered)
        self.assertIn("## 本次交付改变了什么", rendered["人类可读/版本路线图.md"])
        self.assertIn("## 尚未交付", rendered["人类可读/版本路线图.md"])

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

        rendered = lean_governance.rendered_project_texts(project_facts, roadmap, [])
        feature_list = rendered["功能清单.md"]

        self.assertEqual(set(rendered), {"功能清单.md", "开发记录.md", "模型参数文件.md"})
        self.assertNotIn("人类可读/版本路线图.md", rendered)
        self.assertIn("## 摘要", feature_list)
        self.assertIn("## 功能概览", feature_list)
        self.assertIn("## 证据", feature_list)
        self.assertNotIn("## 当前状态", feature_list)


if __name__ == "__main__":
    unittest.main()
