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
from CodexSkills.registry.auto.tools import build_runtime_interface


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
                "CodexSkills/registry/codex/_delivery-backups/",
                "CodexSkills/registry/codex-system/_catalog/",
                "CodexSkills/registry/_global/",
            ),
        )
        for relative in (
            "agents/_catalog",
            "agents/_catalog/catalog.v1.json",
            "claude/_catalog/catalog.v1.json",
            "codex/_catalog/catalog.v1.json",
            "codex/_delivery-backups/teleiosis/v0.0.0.1/"
            "registry-release-record.json",
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

    def test_repository_mirror_records_89_with_teleiosis_and_no_context_kernel(
        self,
    ) -> None:
        index = json.loads(
            (REPO_ROOT / "CodexSkills/index.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(index["skill_instance_count"], 89)
        self.assertEqual(
            [
                row["slug"]
                for row in index["skills"]
                if row["source"] == "codex"
                and row["slug"] == "teleiosis"
            ],
            ["teleiosis"],
        )
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

    def test_exact_three_path_source_content_materialization_is_closed(
        self,
    ) -> None:
        evidence = (
            build_runtime_interface._source_content_sync_materialization()
        )
        self.assertTrue(evidence["source_content_sync_complete"])
        self.assertTrue(evidence["source_mirror_parity_satisfied"])
        self.assertFalse(evidence["source_root_parity_satisfied"])
        self.assertFalse(evidence["whole_source_parity_satisfied"])
        self.assertEqual(
            evidence["exact_synchronized_paths"],
            [
                "codex/graphify",
                "codex/persona-distiller-group",
                "codex/verifier",
            ],
        )
        self.assertEqual(evidence["remaining_content_drift_paths"], [])
        self.assertEqual(
            [
                row["content_digest"]
                for row in evidence["synchronized_entries"]
            ],
            [
                "816bfb795d8998983a3df2b8786a2d1c"
                "691e9e2280dd7be2bdc07acd47775587",
                "eaf8f8e32b1ade683387346adec8a21b"
                "241541567e910609247426ec3626b921",
                "7727bcfb4d03bcc97fafeedea1f8e773"
                "945e6be70f0351e8ca32525ff1e8d556",
            ],
        )

    def test_source_content_evidence_is_pinned_to_dc653_git_tree(
        self,
    ) -> None:
        original = build_runtime_interface._git_tree_entries
        observations = []

        def observe(object_id, relative_root):
            observations.append((object_id, relative_root))
            return original(object_id, relative_root)

        with mock.patch.object(
            build_runtime_interface,
            "_git_tree_entries",
            side_effect=observe,
        ):
            evidence = (
                build_runtime_interface
                ._source_content_sync_materialization()
            )

        self.assertTrue(evidence["source_content_sync_complete"])
        self.assertEqual(
            {object_id for object_id, _ in observations},
            {
                "sha1:"
                "dc653654603f5bfee3bd41890b49cfad700cf541"
            },
        )
        self.assertEqual(
            {
                relative_root
                for _, relative_root in observations
                if relative_root.endswith("_catalog")
                or relative_root.endswith("_global")
            },
            {
                "CodexSkills/registry/agents/_catalog",
                "CodexSkills/registry/claude/_catalog",
                "CodexSkills/registry/codex/_catalog",
                "CodexSkills/registry/codex-system/_catalog",
                "CodexSkills/registry/_global",
            },
        )
        self.assertIn(
            "CodexSkills/registry/codex/_delivery-backups",
            {relative_root for _, relative_root in observations},
        )

    def test_teleiosis_source_evidence_is_pinned_and_rebuilds_registry(
        self,
    ) -> None:
        evidence = (
            build_runtime_interface
            ._teleiosis_source_sync_materialization()
        )
        self.assertEqual(
            evidence["source_material_git_object_id"],
            "sha1:a8f1f6ff8003db43fad722a5afd3b19615dd325e",
        )
        self.assertEqual(
            evidence["added_source_skill_roots"],
            ["codex/teleiosis"],
        )
        self.assertEqual(evidence["source_skill_count"], 89)
        self.assertEqual(
            evidence["source_content_entry"],
            {
                "alias_count": 0,
                "byte_count": 598392,
                "content_digest": (
                    "252e9cf65b991dd7bd7c36734257b0b5"
                    "da47689cbf2d1c7d7bb4ca766aa93bcb"
                ),
                "regular_file_count": 104,
                "source_relative_path": "codex/teleiosis",
            },
        )
        self.assertTrue(evidence["exact_source_mirror_content_equal"])
        self.assertTrue(evidence["registered_snapshot_rebuild_required"])
        self.assertFalse(
            evidence["registered_snapshot_current_source_compatible"]
        )
        self.assertFalse(evidence["runtime_state_write_permitted"])
        self.assertFalse(evidence["canonical_publication_permitted"])

    def test_teleiosis_source_git_or_index_drift_fails_closed(
        self,
    ) -> None:
        with mock.patch.object(
            build_runtime_interface,
            "TELEIOSIS_SOURCE_MATERIAL_GIT_OBJECT",
            "sha1:" + ("0" * 40),
        ):
            with self.assertRaisesRegex(
                ValueError,
                "AUTO_SOURCE_CONTENT_SYNC_HISTORICAL_TREE_READ_FAILED",
            ):
                (
                    build_runtime_interface
                    ._teleiosis_source_sync_materialization()
                )

        original = build_runtime_interface._git_blob

        def missing_index_entry(object_id, relative_path):
            if (
                object_id
                == build_runtime_interface
                .TELEIOSIS_SOURCE_MATERIAL_GIT_OBJECT
                and relative_path == "CodexSkills/index.json"
            ):
                return b'{"skill_instance_count":89,"skills":[]}\n'
            return original(object_id, relative_path)

        with mock.patch.object(
            build_runtime_interface,
            "_git_blob",
            side_effect=missing_index_entry,
        ):
            with self.assertRaisesRegex(
                ValueError,
                "AUTO_TELEIOSIS_SOURCE_INDEX_CONTRACT_MISMATCH",
            ):
                (
                    build_runtime_interface
                    ._teleiosis_source_sync_materialization()
                )

    def test_current_reserved_payload_is_not_historical_auto_evidence(
        self,
    ) -> None:
        with mock.patch.object(
            build_runtime_interface.os.path,
            "lexists",
            side_effect=AssertionError(
                "current working-tree reserved payload was inspected"
            ),
        ):
            evidence = (
                build_runtime_interface
                ._source_content_sync_materialization()
            )
        self.assertTrue(evidence["reserved_registry_namespaces_preserved"])
        self.assertFalse(
            evidence["catalog_or_snapshot_artifacts_generated"]
        )

    def test_historical_source_content_git_object_drift_fails_closed(
        self,
    ) -> None:
        with mock.patch.object(
            build_runtime_interface,
            "SOURCE_CONTENT_SYNC_MATERIALIZATION_GIT_OBJECT",
            "sha1:" + ("0" * 40),
        ):
            with self.assertRaisesRegex(
                ValueError,
                "AUTO_SOURCE_CONTENT_SYNC_HISTORICAL_TREE_READ_FAILED",
            ):
                build_runtime_interface._source_content_sync_materialization()

    def test_reserved_paths_survive_enumeration_and_deletion(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            registry = Path(temporary) / "registry"
            catalog = registry / "codex/_catalog"
            delivery = registry / "codex/_delivery-backups/teleiosis"
            global_snapshot = registry / "_global"
            obsolete = registry / "codex/obsolete"
            for directory in (
                catalog,
                delivery,
                global_snapshot,
                obsolete,
            ):
                directory.mkdir(parents=True)
            (catalog / "catalog.v1.json").write_text(
                "{}\n",
                encoding="utf-8",
            )
            (global_snapshot / "registry-snapshot.v1.json").write_text(
                "{}\n",
                encoding="utf-8",
            )
            (delivery / "registry-release-record.json").write_text(
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
            self.assertTrue(
                (delivery / "registry-release-record.json").is_file()
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

    def test_wbi_operational_entries_are_explicit_non_skills(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            roots = {}
            for namespace in SOURCE_NAMESPACES:
                source = root / namespace
                (source / "demo").mkdir(parents=True)
                roots[namespace] = source
            (roots["codex"] / ".wbi-install-transactions").mkdir()
            (roots["codex"] / ".wbi-install.lock").write_text(
                "lock\n",
                encoding="utf-8",
            )

            observed = inventory_source_roots(
                roots,
                enforce_exact_aliases=False,
            )

            self.assertEqual(
                observed.skill_counts["codex"],
                1,
            )
            self.assertEqual(
                observed.explicit_non_skill_entries["codex"],
                (
                    {
                        "entry_name": ".wbi-install-transactions",
                        "entry_type": "DIRECTORY",
                        "reason_code": (
                            "NON_SKILL_OPERATIONAL_TRANSACTION_DIRECTORY_"
                            "INCLUDED_IN_SOURCE_COVERAGE"
                        ),
                    },
                    {
                        "entry_name": ".wbi-install.lock",
                        "entry_type": "REGULAR_FILE",
                        "reason_code": (
                            "NON_SKILL_OPERATIONAL_LOCK_FILE_"
                            "INCLUDED_IN_SOURCE_COVERAGE"
                        ),
                    },
                ),
            )

            (roots["codex"] / ".wbi-install-transactions").rmdir()
            (roots["codex"] / ".wbi-install-transactions").write_text(
                "wrong type\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                CatalogReservationError,
                "SOURCE_ROOT_NON_SKILL_TYPE_DRIFT:"
                "codex/.wbi-install-transactions",
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
