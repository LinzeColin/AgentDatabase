from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from helpers import ROOT, write_json
from teleiosis_core.common import TeleiosisError
from teleiosis_core.semantic import classify_task, reconcile, validate_semantic_spec


def base_task(task_id: str, path: str) -> dict:
    return {
        "id": task_id,
        "semantic_goal": "保留或实现目标语义",
        "impact_boundary": "仅限测试目录",
        "paths": [path],
        "required_paths": [],
        "expected_hashes": {},
        "equivalence_markers": {},
        "blockers": [],
        "conflict_markers": [],
    }


class V5SemanticTests(unittest.TestCase):
    def test_semantic_reconcile_all_classifications(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            (repo / "exact.txt").write_text("exact\n", encoding="utf-8")
            (repo / "equiv.txt").write_text("alpha beta gamma\n", encoding="utf-8")
            (repo / "adapt.txt").write_text("older implementation\n", encoding="utf-8")
            (repo / "conflict.txt").write_text("FORBIDDEN_GENESIS_OVERRIDE\n", encoding="utf-8")

            tasks = []
            exact = base_task("S1", "exact.txt")
            exact["expected_hashes"] = {"exact.txt": hashlib.sha256((repo / "exact.txt").read_bytes()).hexdigest()}
            tasks.append(exact)
            equiv = base_task("S2", "equiv.txt")
            equiv["equivalence_markers"] = {"equiv.txt": ["alpha", "gamma"]}
            tasks.append(equiv)
            tasks.append(base_task("S3", "missing.txt"))
            tasks.append(base_task("S4", "adapt.txt"))
            conflict = base_task("S5", "conflict.txt")
            conflict["conflict_markers"] = ["FORBIDDEN_GENESIS_OVERRIDE"]
            tasks.append(conflict)
            blocked = base_task("S6", "adapt.txt")
            blocked["blockers"] = ["required-control-file.txt"]
            tasks.append(blocked)
            obsolete = base_task("S7", "irrelevant.txt")
            obsolete["obsolete"] = True
            tasks.append(obsolete)
            spec = {"schema_version": "teleiosis.semantic_reconcile_spec.v5", "tasks": tasks}
            spec_path = Path(tmp) / "spec.json"
            output = Path(tmp) / "report.json"
            write_json(spec_path, spec)
            report = reconcile(repo, spec_path, output)
            self.assertEqual(report["status"], "BLOCKED")
            self.assertEqual(report["counts"], {
                "adapt": 1, "apply": 1, "blocked": 1, "conflict": 1,
                "equivalent": 1, "obsolete": 1, "satisfied": 1,
            })
            self.assertTrue(output.is_file())
            self.assertFalse(report["rules"]["fixed_repository_sha_gate"])
            self.assertFalse(report["rules"]["whole_tree_overwrite"])

    def test_semantic_reconcile_preserves_upstream_equivalent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            (repo / "feature.py").write_text("def stage0():\n    return 'semantic-delta'\n", encoding="utf-8")
            task = base_task("EQ", "feature.py")
            task["equivalence_markers"] = {"feature.py": ["stage0", "semantic-delta"]}
            result = classify_task(repo, task)
            self.assertEqual(result["classification"], "equivalent")

    def test_semantic_spec_rejects_parent_escape(self) -> None:
        task = base_task("BAD", "../escape")
        spec = {"schema_version": "teleiosis.semantic_reconcile_spec.v5", "tasks": [task]}
        with self.assertRaises(TeleiosisError) as ctx:
            validate_semantic_spec(spec)
        self.assertEqual(ctx.exception.code, "UNSAFE_PATH")

    def test_packaged_semantic_example_is_valid(self) -> None:
        data = json.loads((ROOT / "templates/semantic-reconcile-spec.example.json").read_text(encoding="utf-8"))
        validated = validate_semantic_spec(data)
        self.assertGreaterEqual(len(validated["tasks"]), 1)
        self.assertEqual(len(validated["spec_hash"]), 64)


if __name__ == "__main__":
    unittest.main()
