from __future__ import annotations

import json
import unittest
from pathlib import Path

from helpers import ROOT, load_json
from teleiosis_core.integrity import (
    GENESIS_SHA256,
    parse_frontmatter,
    verify_capabilities,
    verify_dag,
    verify_docs_and_markers,
    verify_genesis,
    verify_json_files,
    verify_manifest,
    verify_release,
    verify_traceability,
    verify_truth_boundaries,
    verify_version,
)


class IntegrityTests(unittest.TestCase):
    def test_version_consistency(self) -> None:
        result = verify_version(ROOT)
        self.assertEqual(set(result.values()), {"v0.0.0.5"})

    def test_frontmatter_identity(self) -> None:
        fm = parse_frontmatter(ROOT / "SKILL.md")
        self.assertEqual(fm["name"], "teleiosis")
        self.assertEqual(fm["metadata.scope_mode"], "FULL_NO_ROUTING")

    def test_genesis_lock(self) -> None:
        result = verify_genesis(ROOT)
        self.assertEqual(result["locked_sha256"], GENESIS_SHA256)
        self.assertEqual(result["requirements"], 42)

    def test_amendment_three_exists(self) -> None:
        text = (ROOT / "constitution/amendments/WBI-GB-AMENDMENT-003-v0.0.0.4.zh-CN.md").read_text(encoding="utf-8")
        self.assertIn("WBI-GB-030", text)
        self.assertIn("WBI-GB-032", text)

    def test_amendment_four_exists(self) -> None:
        text = (ROOT / "constitution/amendments/WBI-GB-AMENDMENT-004-v0.0.0.5.zh-CN.md").read_text(encoding="utf-8")
        self.assertIn("WBI-GB-033", text)
        self.assertIn("WBI-GB-042", text)

    def test_json_syntax(self) -> None:
        self.assertGreater(verify_json_files(ROOT)["json_files"], 20)

    def test_capability_manifests(self) -> None:
        result = verify_capabilities(ROOT)
        self.assertEqual(list(result["modules"]), ["T", "S", "P", "A"])
        self.assertGreaterEqual(result["total"], 60)

    def test_task_dag_acyclic(self) -> None:
        self.assertTrue(verify_dag(ROOT)["acyclic"])

    def test_traceability_complete(self) -> None:
        result = verify_traceability(ROOT)
        self.assertEqual(result["requirements"], 30)
        self.assertEqual(result["mapped"], 30)

    def test_truth_boundaries(self) -> None:
        result = verify_truth_boundaries(ROOT)
        self.assertEqual(result["formal_independent_review"], "UNAVAILABLE")

    def test_chinese_human_docs(self) -> None:
        result = verify_docs_and_markers(ROOT)
        self.assertEqual(len(result["chinese_docs"]), 4)

    def test_manifest_strict(self) -> None:
        result = verify_manifest(ROOT, strict=True)
        self.assertGreater(result["files"], 70)

    def test_full_release_validation(self) -> None:
        result = verify_release(ROOT, strict=True)
        self.assertEqual(result["status"], "PASS")

    def test_single_skill_architecture(self) -> None:
        release = load_json("metadata/release.json")
        self.assertEqual(release["architecture"], "single-skill-four-built-in-full-run-engines")
        self.assertEqual(release["name"], "teleiosis")

    def test_source_owner_hash(self) -> None:
        ledger = load_json("metadata/source-ledger.json")
        owner = next(item for item in ledger["sources"] if item["id"] == "SRC-OWNER-HOTKEY")
        self.assertEqual(owner["sha256"], "7c062db3acfc0c19cee61d7c4e28157e67c6d04df45321ab0e3a7263b7458e45")

    def test_no_formal_pass_claim_in_state(self) -> None:
        state = load_json("CANONICAL_STATE.json")
        self.assertEqual(state["current_phase"], "FROZEN_CANDIDATE")
        self.assertEqual(state["release_status"]["formal_independent_review"], "UNAVAILABLE")

    def test_task_dag_has_full_execution_contract(self) -> None:
        data = load_json("TASK_DAG.json")
        required = {"input", "output", "dependencies", "implementation_steps", "acceptance", "oracle", "test", "threshold", "evidence", "risk", "rollback", "stop_condition"}
        self.assertEqual(len(data["tasks"]), 30)
        for task in data["tasks"]:
            self.assertTrue(required.issubset(task), task["id"])
            self.assertTrue(task["implementation_steps"], task["id"])
            self.assertTrue((ROOT / task["output"]).exists(), task["id"])
            self.assertTrue((ROOT / task["evidence"]).exists(), task["id"])

    def test_entrypoints_disable_bytecode_cache(self) -> None:
        paths = [ROOT / "START_HERE.py", ROOT / "install.py", *(ROOT / "scripts").glob("*.py")]
        for path in paths:
            self.assertIn("sys.dont_write_bytecode = True", path.read_text(encoding="utf-8"), path.name)


if __name__ == "__main__":
    unittest.main()
