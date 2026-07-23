from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "sync_skills.py"
SPEC = importlib.util.spec_from_file_location("sync_skills_under_test", MODULE_PATH)
assert SPEC and SPEC.loader
sync_skills = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sync_skills)


class SyncSkillsRegistryRoutingTests(unittest.TestCase):
    def test_persona_distiller_uses_registry_route_and_preserves_repo_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            local = root / "local-persona"
            local.mkdir()
            (local / "SKILL.md").write_text(
                "---\nname: persona-distiller\ndescription: Test persona builder.\n---\n",
                encoding="utf-8",
            )
            product_root = local / "产物登记"
            product_root.mkdir()
            (product_root / "index.json").write_text(json.dumps({
                "products": [{
                    "canonical_name": "Example Person",
                    "registration_category": "技术工程",
                    "latest_model_version": "0.1.0",
                    "latest_artifact": "技术工程/example/versions/0.1.0/example.zip",
                }],
            }), encoding="utf-8")
            mirror_root = root / "CodexSkills"
            unrelated = mirror_root / "codex" / "unrelated"
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
            self.assertIn("Example Person", readme)


if __name__ == "__main__":
    unittest.main()
