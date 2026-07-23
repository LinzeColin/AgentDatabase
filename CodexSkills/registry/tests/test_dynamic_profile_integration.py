from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
CATALOG = REPO_ROOT / "CodexSkills"
REGISTRY = CATALOG / "registry"
SKILL = REGISTRY / "codex/dynamic-personal-profile-update"


class DynamicProfileIntegrationTests(unittest.TestCase):
    def test_all_source_namespaces_live_under_registry(self) -> None:
        for source in ("agents", "claude", "codex-system", "codex"):
            self.assertTrue((REGISTRY / source).is_dir(), source)
            self.assertFalse((CATALOG / source).exists(), source)

    def test_root_compatibility_index_resolves_every_entry(self) -> None:
        index = json.loads((CATALOG / "index.json").read_text(encoding="utf-8"))
        self.assertEqual(index["skill_instance_count"], len(index["skills"]))
        indexed = {(skill["source"], skill["slug"]) for skill in index["skills"]}
        actual = {
            (source, path.name)
            for source in ("agents", "claude", "codex-system", "codex")
            for path in (REGISTRY / source).iterdir()
            if path.is_dir()
        }
        self.assertEqual(indexed, actual)
        missing = [
            skill["entry"]
            for skill in index["skills"]
            if not (CATALOG / skill["entry"]).is_file()
        ]
        self.assertEqual(missing, [])
        dynamic = [
            skill
            for skill in index["skills"]
            if skill["source"] == "codex"
            and skill["slug"] == "dynamic-personal-profile-update"
        ]
        self.assertEqual(len(dynamic), 1)
        self.assertEqual(
            dynamic[0]["entry"],
            "registry/codex/dynamic-personal-profile-update/SKILL.md",
        )

    def test_registry_record_and_patch_version_are_resolvable(self) -> None:
        index = json.loads((REGISTRY / "index.json").read_text(encoding="utf-8"))
        records = [
            record
            for record in index["skills"]
            if record["skill_id"] == "dynamic-personal-profile-update"
        ]
        self.assertEqual(len(records), 1)
        self.assertEqual(
            len({record["skill_id"] for record in index["skills"]}),
            len(index["skills"]),
        )
        record = records[0]
        self.assertEqual(record["skill_id"], "dynamic-personal-profile-update")
        self.assertRegex(record["version"], r"^0\.0\.0\.\d+$")
        self.assertTrue((REGISTRY / record["entry"]).is_file())
        self.assertTrue((REGISTRY / record["skill_entry"]).is_file())
        registry_text = (SKILL / "registry.yaml").read_text(encoding="utf-8")
        self.assertIn('schema_version: "skill_registry.v1"', registry_text)
        self.assertIn('version: "0.0.0.1"', registry_text)

    def test_dynamic_profile_route_is_derived_read_only(self) -> None:
        routes_path = REPO_ROOT / "OpenAIDatabase/config/context_sources/resource_routes.json"
        routes = json.loads(routes_path.read_text(encoding="utf-8"))["routes"]
        dynamic = [route for route in routes if route["intent"] == "dynamic_profile"]
        self.assertEqual(len(dynamic), 1)
        self.assertEqual(
            dynamic[0]["read_order"],
            ["data/derived/profile/DYNAMIC_PROFILE.md"],
        )
        self.assertEqual(dynamic[0]["access"], "read_only_derived")
        self.assertIs(dynamic[0]["canonical"], False)
        startup = [route for route in routes if route["intent"] == "startup"]
        self.assertEqual(startup[0]["read_order"], ["data/memory/agent-memory.json"])

    def test_workflow_has_schedule_tests_and_exact_commit_allowlist(self) -> None:
        workflow = (
            REPO_ROOT / ".github/workflows/dynamic-profile-update.yml"
        ).read_text(encoding="utf-8")
        self.assertIn('cron: "17 1 */3 * *"', workflow)
        self.assertRegex(workflow, r"permissions:\n  contents: write\n")
        self.assertIn(
            "if: github.ref_name == github.event.repository.default_branch",
            workflow,
        )
        self.assertIn(
            "uses: actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5",
            workflow,
        )
        self.assertNotIn("uses: actions/checkout@v4", workflow)
        self.assertIn("Run deterministic regression tests", workflow)
        self.assertIn('git status --porcelain --untracked-files=all -- "$profile"', workflow)
        self.assertIn("git ls-files --others --exclude-standard", workflow)
        self.assertIn('if [ "$(git diff --cached --name-only)" != "$profile" ]', workflow)
        self.assertNotRegex(workflow, r"(?m)^\s+(issues|pull-requests|packages|deployments):")


if __name__ == "__main__":
    unittest.main()
