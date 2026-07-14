import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "apps" / "memory-atlas" / "src"
ZH_CN = SRC / "i18n" / "zh-CN.ts"
TYPES = SRC / "i18n" / "types.ts"
HELP = SRC / "components" / "help" / "MemoryAtlasHelpPanel.tsx"
SHELL = SRC / "app" / "MemoryAtlasShell.tsx"
EDITOR = SRC / "components" / "ProposalEditor.tsx"
DIFF = SRC / "components" / "ProposalDiffPreview.tsx"
WRITEBACK = SRC / "features" / "actions" / "WritebackProposalPanel.tsx"
INSPECTOR = SRC / "features" / "settings" / "InspectorWorkspace.tsx"
VISUAL_AUDIT = ROOT / "scripts" / "audit_memory_atlas_visual_acceptance.py"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class ZhCnCopySourceTest(unittest.TestCase):
    def test_zh_cn_copy_source_has_versioned_glossary_and_reusable_maps(self) -> None:
        source = read(ZH_CN)
        type_source = read(TYPES)

        self.assertIn(
            'ZH_CN_COPY_SOURCE_VERSION = "memory_atlas.zh_cn_copy.v1_2_1_s05_p3_t3"',
            source,
        )
        for term in ("Agent", "API", "JSON", "WebGL", "ROI", "schema"):
            self.assertIn(f'term: "{term}"', source)
        for field in (
            "importance",
            "priority",
            "note",
            "status",
            "original_value",
            "proposed_value",
            "impact_summary",
            "rollback_metadata",
            "saved_at",
        ):
            self.assertIn(f'{field}: "', source)
        for group in (
            "importance",
            "priority",
            "status",
            "rollbackUnit",
            "proposalLineage",
            "runtimeLifecycle",
            "serverMode",
            "boolean",
        ):
            self.assertIn(f"{group}: {{", source)
        for status in (
            'needs_review: "需要复核"',
            'ready_for_agent_apply: "可交受控代理应用"',
            'reverted: "已回滚"',
        ):
            self.assertIn(status, source)

        self.assertIn("UiFieldKey", type_source)
        self.assertIn("UiEnumGroup", type_source)
        self.assertIn("glossary:", type_source)
        self.assertIn("fields:", type_source)
        self.assertIn("enums:", type_source)
        for unexplained in (
            "source_contract.writeback_policy",
            'label: "Presentation"',
            'label: "Analysis"',
            'debugTitle: "高级详情 / Agent Inspector"',
        ):
            self.assertNotIn(unexplained, source)

    def test_copy_helpers_hide_unknown_machine_enums_without_mutating_values(self) -> None:
        source = read(ZH_CN)

        self.assertIn("export function zhCNFieldLabel", source)
        self.assertIn("export function zhCNEnumLabel", source)
        self.assertIn("export function zhCNProposalValue", source)
        self.assertIn("zhCNCopy.enums.unknownValue", source)
        enum_helper = source.split("export function zhCNEnumLabel", 1)[1].split("\n}", 1)[0]
        self.assertNotIn("return value", enum_helper)

    def test_help_panel_renders_chinese_copy_and_visible_glossary(self) -> None:
        source = read(HELP)

        self.assertIn("copy.eyebrow", source)
        self.assertIn("copy.durationLabel", source)
        self.assertIn("copy.glossaryTitle", source)
        self.assertIn("copy.glossary.map", source)
        self.assertNotIn("Memory Atlas Help", source)
        self.assertNotIn(">3 min<", source)

    def test_proposal_editor_uses_chinese_field_and_enum_copy(self) -> None:
        source = read(EDITOR)

        self.assertIn("zhCNFieldLabel", source)
        self.assertIn("zhCNProposalValue", source)
        self.assertIn("uiCopy.proposal.editorTitle", source)
        self.assertIn("uiCopy.proposal.savedAtPrefix", source)
        self.assertNotIn(">Proposal UI<", source)
        self.assertNotIn(">note<", source)
        self.assertNotIn("`saved_at ", source)

        # Export/API contracts remain English and byte-compatible.
        for contract in (
            'field="importance"',
            'field="priority"',
            "schema_version: EXPORT_SCHEMA_VERSION",
            "original_value:",
            "proposed_value:",
            "rollback_metadata:",
            "proposal_only: true",
        ):
            self.assertIn(contract, source)

    def test_proposal_diff_and_writeback_use_shared_copy_without_raw_ui_fields(self) -> None:
        diff_source = read(DIFF)
        writeback_source = read(WRITEBACK)

        self.assertIn("zhCNFieldLabel", diff_source)
        self.assertIn("zhCNProposalValue", diff_source)
        self.assertIn("uiCopy.proposal.diffPreviewTitle", diff_source)
        self.assertNotIn(">Proposal Diff Preview<", diff_source)
        self.assertNotIn(">original_value<", diff_source)
        self.assertNotIn(">proposed_value<", diff_source)
        self.assertIn('zhCNEnumLabel("rollbackUnit"', writeback_source)
        self.assertIn('zhCNEnumLabel("proposalLineage", "parent")', writeback_source)
        self.assertIn('zhCNEnumLabel("proposalLineage", "root")', writeback_source)

    def test_shell_and_inspector_translate_runtime_and_visible_enum_values(self) -> None:
        shell_source = read(SHELL)
        inspector_source = read(INSPECTOR)

        self.assertIn("ZH_CN_COPY_SOURCE_VERSION", shell_source)
        self.assertIn('zhCNEnumLabel("runtimeLifecycle"', shell_source)
        self.assertIn('zhCNEnumLabel("serverMode"', shell_source)
        self.assertIn("data-s05-p3-t1-zh-cn-copy", shell_source)
        self.assertIn("humanCategoryLabel(node.category)", inspector_source)
        self.assertIn('zhCNEnumLabel("confidence"', inspector_source)
        self.assertIn('zhCNEnumLabel("importance"', inspector_source)

        audit_source = read(VISUAL_AUDIT)
        self.assertIn('"高级详情 / 代理检查器" in ui_source', audit_source)
        self.assertNotIn('"高级详情 / Agent Inspector" in ui_source', audit_source)


if __name__ == "__main__":
    unittest.main()
