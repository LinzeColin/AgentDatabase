from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from memory_atlas_cli.public_raw_layout import (  # noqa: E402
    LAYOUT_CONFIG_PATH,
    PublicRawLayoutError,
    audit_public_raw_layout,
    classify_public_raw_path,
    validate_layout_contract,
)


def canonical_contract() -> dict:
    return json.loads((ROOT / LAYOUT_CONFIG_PATH).read_text(encoding="utf-8"))


def fixture_registry() -> dict:
    return {
        "sync_sources": [
            {
                "source_id": "chatgpt",
                "source_type": "chatgpt_export",
                "status": "active_manual",
                "archive_path": "data/public_raw/chatgpt",
            },
            {
                "source_id": "codex",
                "source_type": "codex_local",
                "status": "active_local",
                "archive_path": "data/public_raw/codex",
            },
            {
                "source_id": "generic_agent_template",
                "source_type": "generic_agent",
                "status": "template",
                "archive_path": "data/public_raw/agents/{source_id}",
            },
            {
                "source_id": "codex-reviewer",
                "source_type": "generic_agent",
                "status": "active_manual",
                "archive_path": "data/public_raw/agents/codex-reviewer",
            },
        ]
    }


def write_fixture_tree(database: Path) -> None:
    files = {
        "data/public_raw/README.md": "# Public raw\n",
        "data/public_raw/chatgpt/conversation.json": "{}\n",
        "data/public_raw/codex/session.json": "{}\n",
        "data/public_raw/codex/sessions/session.jsonl": "{}\n",
        "data/public_raw/agents/codex-reviewer/review.json": "{}\n",
    }
    for relative, content in files.items():
        path = database / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    contract = database / LAYOUT_CONFIG_PATH
    contract.parent.mkdir(parents=True, exist_ok=True)
    contract.write_text(json.dumps(canonical_contract()), encoding="utf-8")


class PublicRawLayoutTests(unittest.TestCase):
    def test_canonical_layout_is_tracked_recoverable_and_runtime_isolated(self) -> None:
        result = audit_public_raw_layout(ROOT)

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["task_id"], "S06-P1-T2")
        self.assertEqual(result["layout"]["file_count"], result["layout"]["tracked_file_count"])
        self.assertGreater(result["layout"]["source_file_counts"]["chatgpt"], 0)
        self.assertGreater(result["layout"]["source_file_counts"]["codex"], 0)
        self.assertGreater(result["layout"]["source_file_counts"]["codex-reviewer"], 0)
        self.assertEqual(result["isolation"]["frontend"]["vite_public_dir"], "data/derived/visualization")
        self.assertEqual(result["isolation"]["default_codex_route"]["public_raw_source_count"], 0)
        self.assertIs(result["raw_content_read"], False)
        self.assertIs(result["raw_mutation"], False)
        self.assertIs(result["remote_push"], False)

    def test_atlasctl_exposes_the_canonical_layout_audit(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/atlasctl.py", "audit", "--check", "public-raw-layout"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(payload["check"], "public-raw-layout")

    def test_atlasctl_wraps_registry_failure_without_traceback_or_local_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary)
            layout = database / LAYOUT_CONFIG_PATH
            layout.parent.mkdir(parents=True)
            layout.write_text(json.dumps(canonical_contract()), encoding="utf-8")
            registry = database / "config/data_sources/source_registry.json"
            registry.write_text("{not-json\n", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/atlasctl.py",
                    "audit",
                    "--check",
                    "public-raw-layout",
                    "--database-dir",
                    str(database),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(result.returncode, 2)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "FAIL_CLOSED")
        self.assertEqual(payload["dependency"], "config/data_sources/source_registry.json")
        self.assertNotIn("Traceback", result.stderr)
        self.assertNotIn(str(database), result.stdout + result.stderr)

    def test_path_classifier_preserves_source_identity(self) -> None:
        agents = {"codex-reviewer"}
        self.assertEqual(classify_public_raw_path(Path("README.md"), agents), "control")
        self.assertEqual(classify_public_raw_path(Path("chatgpt/event.json"), agents), "chatgpt")
        self.assertEqual(classify_public_raw_path(Path("codex/sessions/event.jsonl"), agents), "codex")
        self.assertEqual(
            classify_public_raw_path(Path("agents/codex-reviewer/review.json"), agents),
            "codex-reviewer",
        )
        with self.assertRaises(PublicRawLayoutError):
            classify_public_raw_path(Path("agents/unregistered/review.json"), agents)

    def test_configured_agent_can_wait_for_its_first_sync_without_a_placeholder_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary)
            write_fixture_tree(database)
            registry = fixture_registry()
            registry["sync_sources"].append(
                {
                    "source_id": "new-agent",
                    "source_type": "generic_agent",
                    "status": "configured",
                    "archive_path": "data/public_raw/agents/new-agent",
                }
            )

            result = audit_public_raw_layout(
                database,
                registry=registry,
                verify_runtime_isolation=False,
                enforce_git_tracking=False,
            )

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["layout"]["source_file_counts"]["new-agent"], 0)

    def test_contract_rejects_layout_or_isolation_drift(self) -> None:
        mutations = {
            "raw root": lambda payload: payload.update({"root": "data/raw"}),
            "deep layout": lambda payload: payload["shallow_layout"].update(
                {"max_directory_depth_below_root": 3}
            ),
            "frontend raw publicDir": lambda payload: payload["isolation"].update(
                {"expected_vite_public_dir": "data/public_raw"}
            ),
            "restore task claimed early": lambda payload: payload["recovery_layout"].update(
                {"restore_implementation_task": "S06-P1-T2"}
            ),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                payload = canonical_contract()
                mutate(payload)
                with self.assertRaises(PublicRawLayoutError):
                    validate_layout_contract(payload)

    def test_layout_rejects_unknown_deep_missing_and_symlink_entries(self) -> None:
        cases = {
            "unknown root": lambda root: (root / "data/public_raw/other/file.json").parent.mkdir(
                parents=True, exist_ok=True
            ),
            "deep directory": lambda root: (root / "data/public_raw/chatgpt/year/month/file.json").parent.mkdir(
                parents=True, exist_ok=True
            ),
            "unregistered agent": lambda root: (
                root / "data/public_raw/agents/unknown/file.json"
            ).parent.mkdir(parents=True, exist_ok=True),
            "missing active source": lambda root: (
                root / "data/public_raw/agents/codex-reviewer/review.json"
            ).unlink(),
        }
        for label, mutate in cases.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                database = Path(temporary)
                write_fixture_tree(database)
                mutate(database)
                with self.assertRaises(PublicRawLayoutError):
                    audit_public_raw_layout(
                        database,
                        registry=fixture_registry(),
                        verify_runtime_isolation=False,
                        enforce_git_tracking=False,
                    )

        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary)
            write_fixture_tree(database)
            target = database / "outside"
            target.mkdir()
            (database / "data/public_raw/agents/link").symlink_to(target, target_is_directory=True)
            with self.assertRaises(PublicRawLayoutError):
                audit_public_raw_layout(
                    database,
                    registry=fixture_registry(),
                    verify_runtime_isolation=False,
                    enforce_git_tracking=False,
                )

    def test_built_dist_rejects_a_public_raw_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            dist = Path(temporary) / "dist"
            normal = dist / "assets/index.js"
            normal.parent.mkdir(parents=True)
            normal.write_text("export {};\n", encoding="utf-8")
            leaked = dist / "public_raw/leak.json"
            leaked.parent.mkdir(parents=True)
            leaked.write_text("{}\n", encoding="utf-8")
            with self.assertRaisesRegex(PublicRawLayoutError, "contains public_raw paths"):
                from memory_atlas_cli import public_raw_layout

                public_raw_layout._audit_built_dist(dist)

    def test_built_dist_rejects_a_symlink_with_a_renamed_raw_path(self) -> None:
        from memory_atlas_cli import public_raw_layout

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "raw.json"
            target.write_text("{}\n", encoding="utf-8")
            linked = root / "dist/assets/renamed.json"
            linked.parent.mkdir(parents=True)
            linked.symlink_to(target)

            with self.assertRaisesRegex(PublicRawLayoutError, "symlink is forbidden in frontend build"):
                public_raw_layout._audit_built_dist(root / "dist")

    def test_frontend_isolation_rejects_an_allow_path_inside_public_raw(self) -> None:
        from memory_atlas_cli import public_raw_layout

        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary).resolve()
            (database / "data/public_raw/chatgpt").mkdir(parents=True)
            (database / "data/derived/visualization").mkdir(parents=True)
            (database / "apps/memory-atlas/src").mkdir(parents=True)
            resolved = {
                "publicDir": str(database / "data/derived/visualization"),
                "outDir": str(database / "apps/memory-atlas/dist"),
                "allow": [str(database / "data/public_raw/chatgpt")],
            }

            with patch.object(public_raw_layout, "_resolve_vite_config", return_value=resolved):
                with self.assertRaisesRegex(PublicRawLayoutError, "server.fs.allow exposes"):
                    public_raw_layout._audit_frontend_isolation(
                        database,
                        canonical_contract(),
                        require_built_dist=False,
                    )


if __name__ == "__main__":
    unittest.main()
