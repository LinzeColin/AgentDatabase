from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[2] / "sync_skills.py"
SPEC = importlib.util.spec_from_file_location("sync_skills_under_test", MODULE_PATH)
assert SPEC and SPEC.loader
sync_skills = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sync_skills)


class SyncSkillsRegistryRoutingTests(unittest.TestCase):
    def test_all_sources_use_registry_route_and_persona_preserves_repo_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            local = root / "local-persona"
            local.mkdir()
            (local / "SKILL.md").write_text(
                "---\nname: persona-distiller\ndescription: Test persona builder.\n---\n",
                encoding="utf-8",
            )
            (local / "persona-registry-index.json").write_text(json.dumps({
                "products": [{
                    "canonical_name": "Example Person",
                    "registration_category": "技术工程",
                    "latest_product_version": "0.0.0.1",
                    "latest_artifact": "技术工程/example/versions/0.0.0.1/example.zip",
                }],
            }), encoding="utf-8")
            mirror_root = root / "CodexSkills"
            unrelated = mirror_root / "registry" / "codex" / "unrelated"
            unrelated.mkdir(parents=True)
            (unrelated / "SKILL.md").write_text("---\nname: unrelated\ndescription: Keep.\n---\n", encoding="utf-8")

            changes = sync_skills.mirror(
                {("codex", "persona-distiller"): str(local)},
                str(mirror_root),
                propagate_deletions=False,
            )
            routed = mirror_root / "registry" / "codex" / "persona-distiller"
            self.assertIn("registry/codex/persona-distiller", changes["added"])
            self.assertTrue((routed / "SKILL.md").is_file())
            self.assertFalse((mirror_root / "codex" / "persona-distiller").exists())
            self.assertTrue(unrelated.is_dir())
            self.assertEqual(
                sync_skills.mirror_relative_path("agents", "example"),
                "registry/agents/example",
            )

            (routed / "registry.yaml").write_text("identity: persona-distiller\n", encoding="utf-8")
            (local / "README.md").write_text("updated\n", encoding="utf-8")
            sync_skills.mirror(
                {("codex", "persona-distiller"): str(local)},
                str(mirror_root),
                propagate_deletions=False,
            )
            self.assertEqual(
                (routed / "registry.yaml").read_text(encoding="utf-8"),
                "identity: persona-distiller\n",
            )

            sync_skills.build_index(str(mirror_root))
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
            self.assertIn("persona-distiller/技术工程/", readme)
            self.assertNotIn("persona-distiller/产物登记/", readme)
            self.assertIn("| `registry/codex/` |", readme)

    def test_deletion_propagation_is_limited_to_skill_source_namespaces(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            mirror_root = Path(tmp) / "CodexSkills"
            obsolete = mirror_root / "registry" / "codex" / "obsolete"
            auto = mirror_root / "registry" / "auto"
            tests = mirror_root / "registry" / "tests"
            for directory in (obsolete, auto, tests):
                directory.mkdir(parents=True)
                (directory / "keep.txt").write_text("fixture\n", encoding="utf-8")

            changes = sync_skills.mirror({}, str(mirror_root), propagate_deletions=True)

            self.assertEqual(changes["removed"], ["registry/codex/obsolete"])
            self.assertFalse(obsolete.exists())
            self.assertTrue(auto.is_dir())
            self.assertTrue(tests.is_dir())


if __name__ == "__main__":
    unittest.main()
