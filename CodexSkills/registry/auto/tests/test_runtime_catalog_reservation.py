from __future__ import annotations

import importlib.util
import json
import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from CodexSkills.registry.auto.runtime.catalog_reservation import (
    AliasSpec,
    CatalogReservationError,
    EXPECTED_SOURCE_ALIASES,
    EXPECTED_SOURCE_ALIAS_COUNT,
    EXPECTED_SOURCE_ALIAS_SET_DIGEST,
    SOURCE_NAMESPACES,
    alias_set_digest,
    assert_exact_alias_set,
    inventory_source_roots,
    is_reserved_registry_relative_path,
    reserved_registry_paths,
)


REPO_ROOT = Path(__file__).resolve().parents[4]
SYNC_PATH = REPO_ROOT / "CodexSkills" / "sync_skills.py"
SPEC = importlib.util.spec_from_file_location(
    "catalog_reservation_sync_under_test",
    SYNC_PATH,
)
assert SPEC and SPEC.loader
sync_skills = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sync_skills)


class RuntimeCatalogReservationTests(unittest.TestCase):
    def test_reserved_catalog_and_global_namespaces_are_exact(self) -> None:
        self.assertEqual(
            reserved_registry_paths(),
            (
                "CodexSkills/registry/agents/_catalog/",
                "CodexSkills/registry/claude/_catalog/",
                "CodexSkills/registry/codex/_catalog/",
                "CodexSkills/registry/codex-system/_catalog/",
                "CodexSkills/registry/_global/",
            ),
        )
        for relative in (
            "agents/_catalog",
            "agents/_catalog/catalog.v1.json",
            "claude/_catalog/catalog.v1.json",
            "codex/_catalog/catalog.v1.json",
            "codex-system/_catalog/catalog.v1.json",
            "_global",
            "_global/registry-snapshot.v1.json",
        ):
            self.assertTrue(
                is_reserved_registry_relative_path(relative),
                relative,
            )
        for relative in (
            "agents/example",
            "codex/catalog",
            "auto/_catalog",
            "../_global",
            "/_global",
        ):
            self.assertFalse(
                is_reserved_registry_relative_path(relative),
                relative,
            )

    def test_frozen_alias_contract_is_exact_20_and_stable(self) -> None:
        self.assertEqual(len(EXPECTED_SOURCE_ALIASES), 20)
        self.assertEqual(EXPECTED_SOURCE_ALIAS_COUNT, 20)
        self.assertEqual(
            alias_set_digest(EXPECTED_SOURCE_ALIASES),
            EXPECTED_SOURCE_ALIAS_SET_DIGEST,
        )
        self.assertEqual(
            EXPECTED_SOURCE_ALIAS_SET_DIGEST,
            "75f6db86e5a18cc000985dc32a719ac7"
            "e0bc15b22b2e3f20c0d32d3138f27387",
        )
        self.assertEqual(
            {
                item.source_namespace
                for item in EXPECTED_SOURCE_ALIASES
            },
            {"codex"},
        )
        self.assertEqual(
            sum(
                item.target_type == "DIRECTORY"
                for item in EXPECTED_SOURCE_ALIASES
            ),
            2,
        )
        self.assertEqual(
            sum(
                item.target_type == "REGULAR_FILE"
                for item in EXPECTED_SOURCE_ALIASES
            ),
            18,
        )

    def test_repository_mirror_has_exact_alias_set_and_real_targets(
        self,
    ) -> None:
        roots = {
            namespace: (
                REPO_ROOT / "CodexSkills" / "registry" / namespace
            )
            for namespace in SOURCE_NAMESPACES
        }
        observed = assert_exact_alias_set(roots)
        self.assertEqual(observed, EXPECTED_SOURCE_ALIASES)
        self.assertEqual(alias_set_digest(observed), EXPECTED_SOURCE_ALIAS_SET_DIGEST)
        for item in observed:
            alias = roots[item.source_namespace] / item.alias_path
            info = os.lstat(alias)
            self.assertTrue(stat.S_ISLNK(info.st_mode))
            self.assertEqual(os.readlink(alias), item.raw_target)

    def test_alias_set_drift_reports_exact_expected_and_observed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            roots = {}
            for namespace in SOURCE_NAMESPACES:
                source = root / namespace
                source.mkdir()
                roots[namespace] = source

            with self.assertRaises(CatalogReservationError) as caught:
                assert_exact_alias_set(roots)

            message = str(caught.exception)
            self.assertIn("SOURCE_ALIAS_SET_DRIFT", message)
            self.assertIn('"expected":[', message)
            self.assertIn('"observed":[]', message)
            self.assertIn('"reason":"SOURCE_ALIAS_SET_DRIFT"', message)
            self.assertNotIn(str(root), message)

    def test_repository_mirror_records_88_and_context_kernel_absence(
        self,
    ) -> None:
        index = json.loads(
            (REPO_ROOT / "CodexSkills/index.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(index["skill_instance_count"], 88)
        self.assertEqual(
            [
                row
                for row in index["skills"]
                if row["source"] == "codex"
                and row["slug"] == "context-kernel"
            ],
            [],
        )
        self.assertFalse(
            (
                REPO_ROOT
                / "CodexSkills/registry/codex/context-kernel"
            ).exists()
        )

    def test_reserved_paths_survive_enumeration_and_deletion(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            registry = Path(temporary) / "registry"
            catalog = registry / "codex/_catalog"
            global_snapshot = registry / "_global"
            obsolete = registry / "codex/obsolete"
            for directory in (catalog, global_snapshot, obsolete):
                directory.mkdir(parents=True)
            (catalog / "catalog.v1.json").write_text(
                "{}\n",
                encoding="utf-8",
            )
            (global_snapshot / "registry-snapshot.v1.json").write_text(
                "{}\n",
                encoding="utf-8",
            )
            (obsolete / "SKILL.md").write_text(
                "# obsolete\n",
                encoding="utf-8",
            )

            changes = sync_skills.mirror(
                {},
                str(registry),
                propagate_deletions=True,
            )

            self.assertEqual(changes["removed"], ["codex/obsolete"])
            self.assertFalse(obsolete.exists())
            self.assertTrue((catalog / "catalog.v1.json").is_file())
            self.assertTrue(
                (
                    global_snapshot / "registry-snapshot.v1.json"
                ).is_file()
            )
            self.assertEqual(
                list(sync_skills.iter_mirrored_skills(str(registry))),
                [],
            )

    def test_registered_alias_is_copied_without_dereference(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            skill = source / "demo"
            skill.mkdir(parents=True)
            (skill / "target.txt").write_text(
                "payload\n",
                encoding="utf-8",
            )
            (skill / "ALIAS.txt").symlink_to("target.txt")
            alias = AliasSpec(
                "codex",
                "demo/ALIAS.txt",
                "target.txt",
                "demo/target.txt",
                "REGULAR_FILE",
            )
            registry = root / "registry"

            sync_skills.mirror(
                {("codex", "demo"): str(skill)},
                str(registry),
                propagate_deletions=False,
                alias_specs=(alias,),
                source_roots={"codex": source},
            )

            mirrored = registry / "codex/demo/ALIAS.txt"
            self.assertTrue(stat.S_ISLNK(os.lstat(mirrored).st_mode))
            self.assertEqual(os.readlink(mirrored), "target.txt")
            self.assertEqual(
                (registry / "codex/demo/target.txt").read_text(
                    encoding="utf-8"
                ),
                "payload\n",
            )
            self.assertEqual(
                sync_skills.credential_gate(
                    str(registry),
                    expected_aliases=(alias,),
                ),
                [],
            )

    def test_unregistered_alias_fails_before_any_deletion(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            skill = source / "demo"
            skill.mkdir(parents=True)
            (skill / "target.txt").write_text("x", encoding="utf-8")
            (skill / "unknown").symlink_to("target.txt")
            registry = root / "registry"
            obsolete = registry / "codex/obsolete"
            obsolete.mkdir(parents=True)
            (obsolete / "SKILL.md").write_text("old", encoding="utf-8")

            with self.assertRaisesRegex(
                RuntimeError,
                "未登记的 Skill alias",
            ):
                sync_skills.mirror(
                    {("codex", "demo"): str(skill)},
                    str(registry),
                    source_roots={"codex": source},
                )

            self.assertTrue(obsolete.is_dir())

    def test_oversize_fails_before_any_deletion(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            skill = source / "demo"
            skill.mkdir(parents=True)
            (skill / "large.bin").write_bytes(b"x" * 9)
            registry = root / "registry"
            obsolete = registry / "codex/obsolete"
            obsolete.mkdir(parents=True)
            (obsolete / "SKILL.md").write_text("old", encoding="utf-8")

            with mock.patch.object(sync_skills, "MAX_FILE_BYTES", 8):
                with self.assertRaisesRegex(
                    RuntimeError,
                    "超过镜像硬限",
                ):
                    sync_skills.mirror(
                        {("codex", "demo"): str(skill)},
                        str(registry),
                        source_roots={"codex": source},
                    )

            self.assertTrue(obsolete.is_dir())

    def test_unclassified_dot_root_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            roots = {}
            for namespace in SOURCE_NAMESPACES:
                source = root / namespace
                (source / "demo").mkdir(parents=True)
                roots[namespace] = source
            (roots["codex"] / ".unknown").write_text(
                "not silently skipped\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                CatalogReservationError,
                "SOURCE_ROOT_UNCLASSIFIED_DOT_ENTRY:codex/.unknown",
            ):
                inventory_source_roots(
                    roots,
                    enforce_exact_aliases=False,
                )

    def test_alias_escape_fails_closed_without_exposing_absolute_root(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            outside = root / "outside"
            outside.write_text("private", encoding="utf-8")
            (source / "escape").symlink_to("../outside")

            with self.assertRaises(CatalogReservationError) as caught:
                from CodexSkills.registry.auto.runtime.catalog_reservation import (
                    observe_alias,
                )

                observe_alias(source, "escape")

            self.assertEqual(
                caught.exception.code,
                "SOURCE_ALIAS_TARGET_ESCAPE",
            )
            self.assertNotIn(str(root), str(caught.exception))

    def test_reserved_catalog_symlink_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            registry = Path(temporary) / "registry"
            source = registry / "codex"
            target = registry / "catalog-target"
            source.mkdir(parents=True)
            target.mkdir()
            (source / "_catalog").symlink_to("../catalog-target")

            with self.assertRaisesRegex(
                RuntimeError,
                "Registry 保留目录不是实际目录",
            ):
                list(sync_skills.iter_mirrored_skills(str(registry)))


if __name__ == "__main__":
    unittest.main()
