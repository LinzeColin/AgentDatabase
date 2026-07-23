from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

MODULE_PATH = Path(__file__).resolve().parents[2] / "sync_skills.py"
SPEC = importlib.util.spec_from_file_location("sync_skills_under_test", MODULE_PATH)
assert SPEC and SPEC.loader
sync_skills = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sync_skills)


class SyncSkillsRegistryRoutingTests(unittest.TestCase):
    def test_all_sources_use_registry_route_and_persona_preserves_repo_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            local_builder = root / "local-persona-builder"
            local_builder.mkdir()
            (local_builder / "SKILL.md").write_text(
                "---\nname: persona-distiller\ndescription: Test persona builder.\n---\n",
                encoding="utf-8",
            )
            local_group = root / "local-persona-group"
            local_group.mkdir()
            (local_group / "SKILL.md").write_text(
                "---\nname: persona-distiller-group\ndescription: Test persona group.\n---\n",
                encoding="utf-8",
            )
            (local_group / "team-index.json").write_text(json.dumps({
                "products": [{
                    "canonical_name": "Example Person",
                    "registration_category": "技术工程师",
                    "latest_product_version": "0.0.0.1",
                    "latest_artifact": "技术工程师/example/versions/0.0.0.1/example.zip",
                }],
            }), encoding="utf-8")
            mirror_root = root / "CodexSkills"
            registry = mirror_root / "registry"
            unrelated = registry / "codex" / "unrelated"
            unrelated.mkdir(parents=True)
            (unrelated / "SKILL.md").write_text("---\nname: unrelated\ndescription: Keep.\n---\n", encoding="utf-8")

            changes = sync_skills.mirror(
                {
                    ("codex", "persona-distiller"): str(local_builder),
                    ("codex", "persona-distiller-group"): str(local_group),
                },
                str(registry),
                propagate_deletions=False,
            )
            routed = registry / "codex" / "persona-distiller"
            group_routed = registry / "codex" / "persona-distiller-group"
            self.assertIn("codex/persona-distiller", changes["added"])
            self.assertIn("codex/persona-distiller-group", changes["added"])
            self.assertTrue((routed / "SKILL.md").is_file())
            self.assertTrue((group_routed / "SKILL.md").is_file())
            self.assertFalse((mirror_root / "codex" / "persona-distiller").exists())
            self.assertTrue(unrelated.is_dir())
            self.assertEqual(
                sync_skills.mirror_relative_path("agents", "example"),
                "agents/example",
            )

            (routed / "registry.yaml").write_text("identity: persona-distiller\n", encoding="utf-8")
            (local_builder / "README.md").write_text("updated\n", encoding="utf-8")
            sync_skills.mirror(
                {("codex", "persona-distiller"): str(local_builder)},
                str(registry),
                propagate_deletions=False,
            )
            self.assertEqual(
                (routed / "registry.yaml").read_text(encoding="utf-8"),
                "identity: persona-distiller\n",
            )

            sync_skills.build_index(str(registry), str(mirror_root))
            index = json.loads((mirror_root / "index.json").read_text(encoding="utf-8"))
            persona = next(item for item in index["skills"] if item["slug"] == "persona-distiller")
            self.assertEqual(
                persona["entry"],
                "registry/codex/persona-distiller/SKILL.md",
            )
            readme = (mirror_root / "README.md").read_text(encoding="utf-8")
            self.assertIn("不得在不同身份下重复登记", readme)
            self.assertIn("单次运行不编号", readme)
            self.assertIn("0.0.0.1", readme)
            self.assertIn("Example Person", readme)
            self.assertIn("persona-distiller-group/技术工程师/", readme)
            self.assertNotIn("persona-distiller/产物登记/", readme)
            self.assertIn("| `registry/codex/` |", readme)

    def test_deletion_propagation_is_limited_to_skill_source_namespaces(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mirror_root = Path(tmp) / "CodexSkills"
            registry = mirror_root / "registry"
            obsolete = registry / "codex" / "obsolete"
            auto = registry / "auto"
            tests = registry / "tests"
            for directory in (obsolete, auto, tests):
                directory.mkdir(parents=True)
                (directory / "keep.txt").write_text("fixture\n", encoding="utf-8")

            changes = sync_skills.mirror({}, str(registry), propagate_deletions=True)

            self.assertEqual(changes["removed"], ["codex/obsolete"])
            self.assertFalse(obsolete.exists())
            self.assertTrue(auto.is_dir())
            self.assertTrue(tests.is_dir())


class SyncSkillsFailClosedTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.catalog = self.root / "CodexSkills"
        self.registry = self.catalog / "registry"
        self.local = self.root / "local-skill"
        self.local.mkdir(parents=True)
        (self.local / "SKILL.md").write_text(
            "---\nname: demo-skill\ndescription: Demo registry migration.\n---\n",
            encoding="utf-8",
        )
        self.original_sources = sync_skills.SOURCES
        sync_skills.SOURCES = {
            "codex": {"path": str(self.root / "local"), "label": "Codex test source"}
        }

    def tearDown(self) -> None:
        sync_skills.SOURCES = self.original_sources
        self.temp.cleanup()

    def test_mirror_preserves_repo_owned_registry_metadata(self) -> None:
        destination = self.registry / "codex/demo-skill"
        destination.mkdir(parents=True)
        (destination / "SKILL.md").write_bytes((self.local / "SKILL.md").read_bytes())
        metadata = b'schema_version: "skill_registry.v1"\n'
        (destination / "registry.yaml").write_bytes(metadata)

        dry_run = sync_skills.mirror(
            {("codex", "demo-skill"): str(self.local)},
            str(self.registry),
            dry_run=True,
        )
        self.assertEqual(dry_run["updated"], [])

        (self.local / "SKILL.md").write_text(
            "---\nname: demo-skill\ndescription: Updated demo.\n---\n",
            encoding="utf-8",
        )
        changed = sync_skills.mirror(
            {("codex", "demo-skill"): str(self.local)},
            str(self.registry),
        )
        self.assertEqual(changed["updated"], ["codex/demo-skill"])
        self.assertEqual((destination / "registry.yaml").read_bytes(), metadata)

    def test_root_compatibility_index_does_not_overwrite_registry_records(self) -> None:
        destination = self.registry / "codex/demo-skill"
        destination.mkdir(parents=True)
        (destination / "SKILL.md").write_bytes((self.local / "SKILL.md").read_bytes())
        (self.registry / "index.json").write_text('{"sentinel": true}\n', encoding="utf-8")
        (self.registry / "README.md").write_text("registry sentinel\n", encoding="utf-8")

        count, unique, _ = sync_skills.build_index(
            str(self.registry),
            str(self.catalog),
        )

        self.assertEqual((count, unique), (1, 1))
        index = json.loads((self.catalog / "index.json").read_text(encoding="utf-8"))
        self.assertEqual(index["skills"][0]["entry"], "registry/codex/demo-skill/SKILL.md")
        self.assertEqual(
            json.loads((self.registry / "index.json").read_text(encoding="utf-8")),
            {"sentinel": True},
        )
        self.assertEqual(
            (self.registry / "README.md").read_text(encoding="utf-8"),
            "registry sentinel\n",
        )

    def test_credential_gate_fails_closed_on_read_error(self) -> None:
        destination = self.registry / "codex/demo-skill"
        destination.mkdir(parents=True)
        target = destination / "SKILL.md"
        target.write_bytes((self.local / "SKILL.md").read_bytes())
        real_open = open

        def selective_open(path, *args, **kwargs):
            if Path(path) == target:
                raise OSError("synthetic read failure")
            return real_open(path, *args, **kwargs)

        with mock.patch("builtins.open", side_effect=selective_open):
            with self.assertRaisesRegex(RuntimeError, "凭据扫描无法读取文件"):
                sync_skills.credential_gate(str(self.registry))

    def test_credential_gate_scans_large_file_across_chunk_boundary(self) -> None:
        destination = self.registry / "codex/demo-skill"
        destination.mkdir(parents=True)
        target = destination / "large-payload.bin"
        boundary = 20 * 1024 * 1024
        with target.open("wb") as handle:
            handle.seek(boundary - 2)
            handle.write(b"ghp_" + b"A" * 24)

        self.assertGreater(target.stat().st_size, boundary)
        self.assertEqual(
            sync_skills.credential_gate(str(self.registry)),
            [("codex/demo-skill/large-payload.bin", "GitHub 令牌")],
        )

    def test_inventory_fails_closed_when_declared_source_is_missing(self) -> None:
        existing = self.root / "existing-source"
        existing.mkdir()
        missing = self.root / "missing-source"
        sync_skills.SOURCES = {
            "codex": {"path": str(existing), "label": "Existing source"},
            "agents": {"path": str(missing), "label": "Missing source"},
        }

        with self.assertRaisesRegex(RuntimeError, "防止把缺失来源误判为删除"):
            sync_skills.inventory()

    def test_deletion_propagation_fails_closed_when_removal_fails(self) -> None:
        obsolete = self.registry / "codex/obsolete"
        obsolete.mkdir(parents=True)
        (obsolete / "SKILL.md").write_text("obsolete\n", encoding="utf-8")

        with mock.patch.object(
            sync_skills.shutil,
            "rmtree",
            side_effect=OSError("synthetic removal failure"),
        ):
            with self.assertRaisesRegex(RuntimeError, "无法删除仓库镜像目录"):
                sync_skills.mirror(
                    {},
                    str(self.registry),
                    propagate_deletions=True,
                )

        self.assertTrue(obsolete.is_dir())

    def test_skill_replacement_fails_closed_when_removal_fails(self) -> None:
        destination = self.registry / "codex/demo-skill"
        destination.mkdir(parents=True)
        original = b"existing repository bytes\n"
        (destination / "SKILL.md").write_bytes(original)

        with mock.patch.object(
            sync_skills.shutil,
            "rmtree",
            side_effect=OSError("synthetic removal failure"),
        ):
            with self.assertRaisesRegex(RuntimeError, "无法替换仓库镜像目录"):
                sync_skills.mirror(
                    {("codex", "demo-skill"): str(self.local)},
                    str(self.registry),
                    propagate_deletions=False,
                )

        self.assertEqual((destination / "SKILL.md").read_bytes(), original)

    def test_main_stops_before_mirror_when_inventory_is_incomplete(self) -> None:
        with (
            mock.patch.object(
                sync_skills,
                "inventory",
                side_effect=RuntimeError("synthetic incomplete inventory"),
            ),
            mock.patch.object(sync_skills, "mirror") as mirror,
            mock.patch.object(sys, "argv", ["sync_skills.py", "--no-push"]),
        ):
            self.assertEqual(sync_skills.main(), 2)
        mirror.assert_not_called()


if __name__ == "__main__":
    unittest.main()
