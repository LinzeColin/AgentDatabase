from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = ROOT / "scripts"
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from wbi_run.core import (  # noqa: E402
    build_contract,
    init_run,
    load_json,
    record_stage,
    run_status,
    simulate_run,
    validate_run,
)


def capability_file(workspace: Path, module: str, stage: int) -> Path:
    manifest = json.loads((ROOT / "modules" / {"T": "raw_teleiosis", "S": "skill_market_lab", "P": "product_reality_lab"}[module] / "CAPABILITIES.json").read_text(encoding="utf-8"))
    path = workspace / f"capability-{stage:03d}.json"
    path.write_text(json.dumps({
        "schema_version": "teleiosis.capability_results.v1",
        "module": module,
        "global_stage": stage,
        "results": [
            {"id": row["id"], "status": "EXECUTED", "reason": "", "evidence_refs": ["fixture://evidence"]}
            for row in manifest["capabilities"]
        ],
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


class FullRunContractTests(unittest.TestCase):
    def test_contract_is_three_groups_three_rounds_and_no_router(self) -> None:
        contract = build_contract()
        self.assertEqual(contract["execution_mode"], "FULL_NO_ROUTING")
        self.assertEqual(contract["groups"], 3)
        self.assertEqual(contract["rounds_per_group"], 3)
        self.assertEqual(contract["module_stages"], 27)
        self.assertEqual(contract["candidate_revisions"], 27)
        self.assertEqual(contract["round_sequence"], ["T", "C", "S", "C", "P", "C"])
        self.assertFalse(contract["fixed_sha_precondition"])
        self.assertEqual(contract["candidate_semantics"], "C_IS_ITERATION_OBJECT_REVISION_NOT_SHA_CHECKPOINT")
        self.assertEqual([x["module"] for x in contract["stages"]], ["T", "S", "P"] * 9)

    def test_only_one_registry_skill_and_three_complete_internal_modules(self) -> None:
        self.assertEqual(len(list(ROOT.rglob("SKILL.md"))), 1)
        for slug in ("raw_teleiosis", "skill_market_lab", "product_reality_lab"):
            module = ROOT / "modules" / slug
            self.assertTrue((module / "MODULE.md").is_file())
            manifest = json.loads((module / "CAPABILITIES.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["execution_mode"], "FULL_NO_ROUTING")
            self.assertGreaterEqual(len(manifest["capabilities"]), 12)

    def test_readme_states_c_is_candidate_and_flow_is_permanent(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for token in ("T1 -> C1 -> S1 -> C2 -> P1 -> C3", "连续三轮", "连续三组", "不是 SHA 检查点", "FULL_NO_ROUTING"):
            self.assertIn(token, readme)

    def test_candidate_can_change_between_stages_without_fixed_hash_precondition(self) -> None:
        with tempfile.TemporaryDirectory(prefix="teleiosis-v3-candidate-") as td:
            base = Path(td)
            subject = base / "subject"
            subject.mkdir()
            (subject / "value.txt").write_text("baseline\n", encoding="utf-8")
            workspace = base / "workspace"
            init_run(subject, workspace)
            candidate = workspace / "candidate"
            (candidate / "value.txt").write_text("after T\n", encoding="utf-8")
            first = record_stage(workspace, "T", "EXECUTED", capability_file(workspace, "T", 1), decision="KEEP")
            self.assertIn("value.txt", first["revision"]["changed_files"]["modified"])
            first_fingerprint = first["revision"]["content_fingerprint"]
            (candidate / "value.txt").write_text("after S\n", encoding="utf-8")
            second = record_stage(workspace, "S", "EXECUTED", capability_file(workspace, "S", 2), decision="KEEP")
            self.assertNotEqual(first_fingerprint, second["revision"]["content_fingerprint"])
            self.assertFalse(second["revision"]["fixed_sha_precondition"])
            self.assertEqual(second["revision"]["parent_revision_id"], first["revision"]["revision_id"])

    def test_wrong_module_order_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="teleiosis-v3-order-") as td:
            base = Path(td)
            subject = base / "subject"
            subject.mkdir()
            (subject / "x").write_text("x", encoding="utf-8")
            workspace = base / "workspace"
            init_run(subject, workspace)
            with self.assertRaisesRegex(ValueError, "wrong module order"):
                record_stage(workspace, "S", "EXECUTED", capability_file(workspace, "S", 1))

    def test_no_change_still_requires_full_capability_manifest(self) -> None:
        with tempfile.TemporaryDirectory(prefix="teleiosis-v3-nochange-") as td:
            base = Path(td)
            subject = base / "subject"
            subject.mkdir()
            (subject / "x").write_text("x", encoding="utf-8")
            workspace = base / "workspace"
            init_run(subject, workspace)
            result = record_stage(workspace, "T", "EXECUTED", capability_file(workspace, "T", 1), decision="NO_CHANGE")
            self.assertEqual(result["revision"]["decision"], "NO_CHANGE")
            self.assertEqual(result["revision"]["changed_files"], {"added": [], "removed": [], "modified": []})
            self.assertGreaterEqual(len(result["revision"]["capability_results"]), 12)

    def test_full_simulation_produces_27_real_candidate_revisions(self) -> None:
        with tempfile.TemporaryDirectory(prefix="teleiosis-v3-sim-") as td:
            base = Path(td)
            subject = base / "subject"
            subject.mkdir()
            (subject / "SKILL.md").write_text("---\nname: fixture\ndescription: fixture\n---\n", encoding="utf-8")
            workspace = base / "workspace"
            result = simulate_run(subject, workspace)
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["revision_count"], 27)
            self.assertEqual(result["module_counts"], {"T": 9, "S": 9, "P": 9})
            self.assertEqual(result["fixed_sha_preconditions"], 0)
            state = load_json(workspace / "RUN_STATE.json")
            self.assertEqual(len(state["revisions"]), 27)
            self.assertEqual(run_status(workspace)["status"], "COMPLETE")
            self.assertEqual(validate_run(workspace, require_complete=True)["status"], "PASS")

    def test_v2_sha_cycle_is_not_the_public_entry(self) -> None:
        public = (ROOT / "scripts" / "teleiosis_cycle.py").read_text(encoding="utf-8")
        self.assertIn("from teleiosis_run import main", public)
        self.assertTrue((ROOT / "scripts" / "teleiosis_cycle_v2_legacy.py").is_file())
        self.assertTrue((ROOT / "scripts" / "wbi_cycle").is_dir())

    def test_release_metadata_uses_v3_candidate_semantics(self) -> None:
        release = json.loads((ROOT / "metadata" / "release.json").read_text(encoding="utf-8"))
        self.assertEqual(release["version"], "v0.0.0.3")
        self.assertEqual(release["candidate_semantics"], "C_IS_ITERATION_OBJECT_REVISION_NOT_SHA_CHECKPOINT")
        self.assertEqual(release["repo_integration"], "MOVING_MAIN_SEMANTIC_ADAPT_NO_FIXED_SHA_PRECONDITION")
        self.assertFalse(release["required_run"]["routing"])

    def test_latest_effective_genesis_is_v3(self) -> None:
        lock = json.loads((ROOT / "constitution" / "effective-genesis-lock.v0.0.0.3.json").read_text(encoding="utf-8"))
        projection = json.loads((ROOT / "constitution" / "effective-requirements.v0.0.0.3.json").read_text(encoding="utf-8"))
        self.assertEqual(lock["effective_version"], "v0.0.0.3")
        self.assertEqual(projection["effective_version"], "v0.0.0.3")
        self.assertIn("WBI-GB-029", [row["id"] for row in projection["requirements"]])


if __name__ == "__main__":
    unittest.main()
