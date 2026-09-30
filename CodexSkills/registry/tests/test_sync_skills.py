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
                source_roots={"codex": root},
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
                source_roots={"codex": root},
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
        self.source = self.root / "local"
        self.source.mkdir()
        self.local = self.source / "demo-skill"
        self.local.mkdir(parents=True)
        (self.local / "SKILL.md").write_text(
            "---\nname: demo-skill\ndescription: Demo registry migration.\n---\n",
            encoding="utf-8",
        )
        self.original_sources = sync_skills.SOURCES
        sync_skills.SOURCES = {
            "codex": {"path": str(self.source), "label": "Codex test source"}
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
            source_roots={"codex": self.source},
        )
        self.assertEqual(dry_run["updated"], [])

        (self.local / "SKILL.md").write_text(
            "---\nname: demo-skill\ndescription: Updated demo.\n---\n",
            encoding="utf-8",
        )
        changed = sync_skills.mirror(
            {("codex", "demo-skill"): str(self.local)},
            str(self.registry),
            source_roots={"codex": self.source},
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
        with mock.patch.object(
            sync_skills.os,
            "open",
            side_effect=OSError("synthetic read failure"),
        ):
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
            "codex-system": {"path": str(existing), "label": "Existing system"},
            "claude": {"path": str(existing), "label": "Existing claude"},
            "agents": {"path": str(missing), "label": "Missing source"},
        }

        with self.assertRaisesRegex(RuntimeError, "防止把缺失来源误判为删除"):
            sync_skills.inventory()

    def test_selected_inventory_does_not_require_unselected_sources(self) -> None:
        selected = self.root / "selected-source"
        selected.mkdir()
        (selected / "demo-skill").mkdir()
        (selected / "unrelated").symlink_to("demo-skill")
        missing = self.root / "missing-source"
        sync_skills.SOURCES = {
            "codex": {"path": str(selected), "label": "Selected source"},
            "codex-system": {"path": str(missing), "label": "Missing system"},
            "claude": {"path": str(missing), "label": "Missing claude"},
            "agents": {"path": str(missing), "label": "Missing agents"},
        }

        observed = sync_skills.inventory(
            source_namespaces=("codex",),
            selected_skill_slugs={"codex": ("demo-skill",)},
        )

        self.assertEqual(
            observed,
            {("codex", "demo-skill"): str((selected / "demo-skill").resolve())},
        )

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
                    source_roots={"codex": self.source},
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

    def test_main_only_scope_skips_unrelated_alias_parity(self) -> None:
        selected = {("codex", "demo-skill"): str(self.local)}
        with (
            mock.patch.object(sync_skills, "inventory", return_value=selected) as inventory,
            mock.patch.object(sync_skills, "persona_shrink_gate") as persona_shrink_gate,
            mock.patch.object(
                sync_skills,
                "mirror",
                return_value={"added": ["codex/demo-skill"], "updated": [], "removed": []},
            ) as mirror,
            mock.patch.object(
                sys,
                "argv",
                ["sync_skills.py", "--only", "codex/demo-skill", "--dry-run"],
            ),
        ):
            self.assertEqual(sync_skills.main(), 0)

        inventory.assert_called_once_with(
            enforce_exact_aliases=False,
            source_namespaces=("codex",),
            selected_skill_slugs={"codex": ("demo-skill",)},
        )
        persona_shrink_gate.assert_not_called()
        mirror.assert_called_once_with(
            selected,
            mock.ANY,
            dry_run=True,
            propagate_deletions=False,
        )


class SyncSkillsVersionDowngradeGateTests(unittest.TestCase):
    """「任何 Skill 不许降版本」硬门（2026-07-25 dynamic-personal-profile-update 事故）。"""

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.registry = self.root / "CodexSkills" / "registry"
        self.source = self.root / "local"
        self.source.mkdir()
        self.original_sources = sync_skills.SOURCES
        sync_skills.SOURCES = {
            "codex": {"path": str(self.source), "label": "Codex test source"}
        }

    def tearDown(self) -> None:
        sync_skills.SOURCES = self.original_sources
        self.temp.cleanup()

    def _skill(self, base: Path, slug: str, *, frontmatter_version=None, version_file=None, registry_version=None) -> Path:
        directory = base / slug
        directory.mkdir(parents=True, exist_ok=True)
        extra = f"version: {frontmatter_version}\n" if frontmatter_version else ""
        (directory / "SKILL.md").write_text(
            f"---\nname: {slug}\ndescription: Test skill.\n{extra}---\n",
            encoding="utf-8",
        )
        if version_file:
            (directory / "VERSION").write_text(f"{version_file}\n", encoding="utf-8")
        if registry_version:
            (directory / "registry.yaml").write_text(
                f'schema_version: "skill_registry.v1"\nversion: "{registry_version}"\n',
                encoding="utf-8",
            )
        return directory

    def test_replay_of_0725_stale_copy_is_blocked(self) -> None:
        # 仓库：registry.yaml 声明 0.0.0.2；本机陈旧副本没有任何版本声明（事故原样）。
        self._skill(self.registry / "codex", "dynamic-personal-profile-update", registry_version="0.0.0.2")
        local = self._skill(self.source, "dynamic-personal-profile-update")
        findings = sync_skills.version_downgrade_gate(
            {("codex", "dynamic-personal-profile-update"): str(local)},
            str(self.registry),
            include_deletions=False,
        )
        self.assertEqual([row[:3] for row in findings], [("codex/dynamic-personal-profile-update", "0.0.0.2", None)])

    def test_lower_local_version_is_blocked_and_equal_or_higher_passes(self) -> None:
        self._skill(self.registry / "codex", "demo", version_file="0.0.0.2")
        for local_version, blocked in (("0.0.0.1", True), ("0.0.0.2", False), ("v0.0.0.3", False)):
            local = self._skill(self.source, "demo", version_file=local_version)
            findings = sync_skills.version_downgrade_gate(
                {("codex", "demo"): str(local)}, str(self.registry), include_deletions=False
            )
            self.assertEqual(bool(findings), blocked, local_version)

    def test_versions_compare_numerically_not_lexically(self) -> None:
        self._skill(self.registry / "codex", "demo", frontmatter_version='"v0.0.0.9"')
        local = self._skill(self.source, "demo", version_file="v0.0.0.10")
        self.assertEqual(
            sync_skills.version_downgrade_gate(
                {("codex", "demo"): str(local)}, str(self.registry), include_deletions=False
            ),
            [],
        )
        self.assertEqual(sync_skills._compare_versions((0, 0, 2), (0, 0, 0, 2)), 1)

    def test_unversioned_repo_skill_and_new_skill_are_not_blocked(self) -> None:
        self._skill(self.registry / "codex", "plain")
        plain = self._skill(self.source, "plain")
        fresh = self._skill(self.source, "fresh", version_file="0.0.0.1")
        self.assertEqual(
            sync_skills.version_downgrade_gate(
                {("codex", "plain"): str(plain), ("codex", "fresh"): str(fresh)},
                str(self.registry),
                include_deletions=True,
            ),
            [],
        )

    def test_deleting_a_versioned_skill_is_blocked_only_on_full_sync(self) -> None:
        self._skill(self.registry / "codex", "versioned", registry_version="0.0.0.2")
        self._skill(self.registry / "codex", "unversioned")
        full = sync_skills.version_downgrade_gate({}, str(self.registry), include_deletions=True)
        self.assertEqual([row[:3] for row in full], [("codex/versioned", "0.0.0.2", None)])
        self.assertEqual(sync_skills.version_downgrade_gate({}, str(self.registry), include_deletions=False), [])

    def test_main_stops_before_mirror_and_explicit_allow_passes(self) -> None:
        self._skill(self.registry / "codex", "demo", version_file="0.0.0.2")
        local = self._skill(self.source, "demo", version_file="0.0.0.1")
        selected = {("codex", "demo"): str(local)}
        for argv, expected, mirror_called in (
            (["sync_skills.py", "--only", "codex/demo", "--dry-run"], 2, False),
            (["sync_skills.py", "--only", "codex/demo", "--dry-run", "--allow-version-downgrade", "codex/demo"], 0, True),
        ):
            with (
                mock.patch.object(sync_skills, "repo_root", return_value=str(self.root)),
                mock.patch.object(sync_skills, "inventory", return_value=dict(selected)),
                mock.patch.object(
                    sync_skills,
                    "mirror",
                    return_value={"added": [], "updated": ["codex/demo"], "removed": []},
                ) as mirror,
                mock.patch.object(sys, "argv", argv),
            ):
                self.assertEqual(sync_skills.main(), expected)
            self.assertEqual(mirror.called, mirror_called)
            self.assertEqual((self.registry / "codex/demo/VERSION").read_text(encoding="utf-8"), "0.0.0.2\n")


if __name__ == "__main__":
    unittest.main()
