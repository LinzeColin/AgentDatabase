import re
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
APP = REPOSITORY_ROOT / "MemoryAtlas"
APP_SOURCE_FILES = (
    APP / "src" / "shared" / "atlas" / "constants.tsx",
    APP / "src" / "app" / "MemoryAtlasShell.tsx",
    APP / "src" / "features" / "settings" / "InteractionLens.tsx",
    APP / "src" / "features" / "sync" / "CommandPalettePanel.tsx",
    APP / "src" / "components" / "VisualWorkflowWorkbench.tsx",
)
CHINESE_COPY = APP / "src" / "i18n" / "zh-CN.ts"
BROWSER_VALIDATOR = (
    APP / "scripts" / "validate_memory_atlas_v1_2_home_multiviewport.cjs"
)


def test_v1_2_release_identity_and_question_navigation_copy() -> None:
    copy = CHINESE_COPY.read_text(encoding="utf-8")

    for required in (
        'brandTitle: "Memory Atlas"',
        'productName: "记忆决策台 · v1.2"',
        'topbarEyebrow: "先看变化，再核对证据，最后决定下一步"',
        'home: "发生了什么"',
        'galaxy: "哪些主题在变化"',
        'notion: "资料如何关联"',
        'roi: "哪里值得投入"',
        'obsidian: "关系网络"',
        'timeline: "变化何时发生"',
        'contribution: "投入节奏"',
        'wordcloud: "反复出现什么"',
        'search: "查找与核对"',
        'summary: "决定下一步"',
        'nodes: "图谱项"',
        'edges: "关联"',
        'pendingProposal: "待授权提案"',
        'weatherTitle: "记忆天气"',
    ):
        assert required in copy


def test_product_shell_exposes_r2_identity_groups_and_folded_machine_details() -> None:
    source = "\n".join(path.read_text(encoding="utf-8") for path in APP_SOURCE_FILES)

    for required in (
        'const PRODUCT_IDENTITY_VERSION = "memory_atlas_product_identity.v1_2_r2"',
        "const navigationGroups",
        "data-r2-release-identity={PRODUCT_IDENTITY_VERSION}",
        "data-nav-question-group={group.id}",
        'className="sidebar-data-status"',
        'className="lens-technical-details"',
        'className="command-technical-details"',
        'scrollIntoView({ block: "nearest", inline: "nearest" })',
    ):
        assert required in source

    assert re.search(
        r'className="[^"]*\bformula-technical-details\b[^"]*"',
        source,
    )


def test_browser_gate_covers_r2_identity_copy_disclosure_and_focus() -> None:
    validator = BROWSER_VALIDATOR.read_text(encoding="utf-8")

    for required in (
        "assertReleaseIdentityAndNavigation",
        "assertDefaultSurfaceHasNoInternalCopy",
        "assertMachineDetailsFolded",
        "assertDefaultScanOrderAndFocus",
        "assertResponsiveProductHierarchy",
        "fullyVisibleAfterFocus",
        "memory_atlas_product_identity.v1_2_r2",
        "python3 scripts/atlasctl.py",
        "No automatic send",
        "Universe State",
    ):
        assert required in validator
