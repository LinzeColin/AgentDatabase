from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from wbi_core.io import bind_files, sha256_file, write_json  # noqa: E402
from wbi_core.luban import (  # noqa: E402
    resolve_release_profile, seal_research, validate_ecosystem, validate_live_artifacts,
    validate_mechanism_adoption, validate_premise, validate_release_readiness, validate_research_seal,
    validate_run_contract,
)


class LubanTests(unittest.TestCase):
    def test_premise_is_pre_edit_and_retire_is_non_destructive(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "premise.json"
            questions = [
                {"id": item, "verdict": "成立", "evidence": ["evidence"]}
                for item in ("real-problem", "unique-value", "install-reason", "observable-artifact")
            ]
            write_json(path, {"completed_before_first_change": True, "target_baseline_tree_hash": "a" * 64, "questions": questions, "decision": "RETIRE", "mutation_allowed": False, "architecture_or_exit_plan": {"action": "preserve and recommend retirement"}})
            self.assertEqual(validate_premise(path, "a" * 64), [])
            data = json.loads(path.read_text())
            data["mutation_allowed"] = True
            write_json(path, data)
            self.assertTrue(validate_premise(path, "a" * 64))

    def test_ecosystem_requires_falsifiable_strategy(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "eco.json"
            write_json(path, json.loads((ROOT / "templates/ecosystem-position.json").read_text()))
            self.assertTrue(validate_ecosystem(path))

    def test_live_artifacts_reject_dry_run_and_check_hash(self):
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            artifact = ws / "artifact.txt"
            artifact.write_text("real", encoding="utf-8")
            record = {
                "status": "PASS", "dry_run_only": False, "mock_only": False,
                "target_artifacts": [{"artifact_id": "target", "observed_at": "2026-07-26", "observation": "opened", "freshness": "current", "reproduction": ["cat artifact.txt"], "local_path": "artifact.txt", "sha256": sha256_file(artifact)}],
                "peer_artifacts": [],
            }
            for peer_id in ("p1", "p2"):
                peer_file = ws / (peer_id + ".txt")
                peer_file.write_text("observed " + peer_id, encoding="utf-8")
                record["peer_artifacts"].append({
                    "artifact_id": peer_id, "observed_at": "2026-07-26", "observation": "opened and inspected",
                    "freshness": "current", "reproduction": ["cat %s.txt" % peer_id],
                    "local_path": peer_file.name, "sha256": sha256_file(peer_file),
                })
            path = ws / "live.json"
            write_json(path, record)
            self.assertEqual(validate_live_artifacts(path, ws), [])
            record["dry_run_only"] = True
            write_json(path, record)
            self.assertTrue(validate_live_artifacts(path, ws))

    def test_live_artifact_claim_without_local_capture_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            path = ws / "live.json"
            write_json(path, {
                "status": "PASS", "dry_run_only": False, "mock_only": False,
                "target_artifacts": [{"artifact_id": "t", "observed_at": "2026-07-26", "observation": "claimed", "freshness": "current", "reproduction": ["open"]}],
                "peer_artifacts": [
                    {"artifact_id": "p1", "observed_at": "2026-07-26", "observation": "claimed", "freshness": "current", "reproduction": ["open"]},
                    {"artifact_id": "p2", "observed_at": "2026-07-26", "observation": "claimed", "freshness": "current", "reproduction": ["open"]},
                ],
            })
            self.assertTrue(any("locally captured" in item for item in validate_live_artifacts(path, ws)))

    def test_mechanism_adoption_requires_traceable_verification(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "adoption.json"
            record = {
                "source_url": "https://example.com/project", "source_type": "direct-peer", "license_status": "observed",
                "mechanism": "ratchet", "adopted_abstraction": "keep or revert", "copy_mode": "no-code-copied",
                "deliberately_not_adopted": "scalar-only score", "teleiosis_extension": "hard gates", "verification": ["test"],
            }
            write_json(path, {"status": "PASS", "records": [record]})
            self.assertEqual(validate_mechanism_adoption(path), [])
            record["verification"] = []
            write_json(path, {"status": "PASS", "records": [record]})
            self.assertTrue(validate_mechanism_adoption(path))

    def test_research_seal_rechecks_actual_files_not_only_embedded_digest(self):
        with tempfile.TemporaryDirectory() as td:
            import shutil
            from wbi_core.workspace import init_run
            root = Path(td)
            target = root / "target"
            shutil.copytree(ROOT, target, ignore=shutil.ignore_patterns(".git", "__pycache__", "MANIFEST.sha256"))
            ws = root / "run"
            run = init_run(target, ws, ROOT, ["incremental"], valid_as_of="2026-07-26")
            contract_path = ws / "control/contracts/run-contract.json"
            contract = json.loads(contract_path.read_text())
            contract.update({
                "goal": "improve the target safely", "scope": ["target Skill"], "non_goals": ["production deployment"],
                "hard_requirements": ["no evidence fabrication"], "knowns": [], "unknowns": [], "dependencies": [],
                "risks": ["regression"], "acceptance_criteria": ["tests pass"], "user_constraints": ["keep Genesis"],
            })
            write_json(contract_path, contract)
            (ws / "evidence/research/source.txt").write_text("original", encoding="utf-8")
            (ws / "competitors").mkdir(parents=True, exist_ok=True)
            (ws / "competitors/dataset.jsonl").write_text("{}\n", encoding="utf-8")
            seal = seal_research(ws, "stable")
            self.assertEqual(seal["status"], "SEALED", seal)
            self.assertEqual(validate_research_seal(ws / "evidence/research/research-seal.json", run["target"]["baseline_tree_hash"]), [])
            (ws / "evidence/research/source.txt").chmod(0o644)
            (ws / "evidence/research/source.txt").write_text("tampered", encoding="utf-8")
            self.assertTrue(any("changed" in item for item in validate_research_seal(ws / "evidence/research/research-seal.json", run["target"]["baseline_tree_hash"])))

    def test_run_contract_must_be_explicit_before_research_seal(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "run-contract.json"
            write_json(path, {"schema_version": "1.0", "run_id": "r", "goal": "", "scope": [], "non_goals": [],
                              "hard_requirements": [], "knowns": [], "unknowns": [], "dependencies": [], "risks": [],
                              "acceptance_criteria": [], "user_constraints": []})
            errors = validate_run_contract(path, "r")
            self.assertTrue(any("goal is empty" in item for item in errors))
            self.assertTrue(any("scope" in item for item in errors))

    def test_release_profiles_do_not_force_visual_showcase_on_infrastructure(self):
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td)
            path = workspace / "release.json"
            keys = ("ten_second_value", "shortest_install", "first_invocation", "three_real_scenarios", "release_notes", "deterministic_package", "post_install_test", "rollback", "reheat_entry")
            common = {key: True for key in keys}
            evidence_file = workspace / "release-proof.txt"
            evidence_file.write_text("healthcheck runbook transcript install rollback reheat", encoding="utf-8")
            bindings = bind_files(workspace, ["release-proof.txt"], label="release")
            check_evidence = {key: ["release-proof.txt"] for key in keys}
            write_json(path, {
                "status": "PASS", "checks": common, "evidence_bindings": bindings, "check_evidence": check_evidence,
                "profile_evidence": {"profile": "infrastructure", "healthcheck": "release-proof.txt", "runbook": "release-proof.txt", "verification_transcript": "release-proof.txt"},
            })
            self.assertEqual(validate_release_readiness(path, "infrastructure", workspace), [])
            self.assertTrue(validate_release_readiness(path, "public", workspace))

    def test_custom_release_profile_uses_frozen_external_contract(self):
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td)
            (workspace / "evidence/validation").mkdir(parents=True)
            (workspace / "control/contracts").mkdir(parents=True)
            path = workspace / "evidence/validation/release-readiness.json"
            keys = ("ten_second_value", "shortest_install", "first_invocation", "three_real_scenarios", "release_notes", "deterministic_package", "post_install_test", "rollback", "reheat_entry")
            common = {key: True for key in keys}
            contract_path = workspace / "control/contracts/release-profile-contract.json"
            contract = {
                "schema_version": "1.0", "status": "FROZEN", "profile": "regulatory-evidence",
                "required_profile_evidence": ["audit-trail", "regulatory-mapping"],
                "rationale": "regulated output needs traceability",
            }
            write_json(contract_path, contract)
            write_json(workspace / "run.json", {
                "release_profile_contract": {
                    "profile": "regulatory-evidence", "path": str(contract_path), "sha256": sha256_file(contract_path)
                }
            })
            proof = workspace / "evidence/validation/release-proof.txt"
            proof.write_text("audit trail and mapping", encoding="utf-8")
            bindings = bind_files(workspace, ["evidence/validation/release-proof.txt"], label="release")
            write_json(path, {
                "status": "PASS", "checks": common, "evidence_bindings": bindings,
                "check_evidence": {key: ["evidence/validation/release-proof.txt"] for key in keys},
                "profile_evidence": {"profile": "regulatory-evidence", "audit-trail": "evidence/validation/release-proof.txt", "regulatory-mapping": "evidence/validation/release-proof.txt"},
            })
            self.assertEqual(validate_release_readiness(path, "regulatory-evidence", workspace), [])
            data = json.loads(path.read_text())
            data["profile_evidence"].pop("audit-trail")
            write_json(path, data)
            self.assertTrue(any("audit-trail" in item for item in validate_release_readiness(path, "regulatory-evidence", workspace)))


if __name__ == "__main__":
    unittest.main()
