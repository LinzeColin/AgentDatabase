from __future__ import annotations

from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from wbi_core.gates import _validate_requirement_coverage, gate_workspace  # noqa: E402
from wbi_core.genesis import verify_genesis  # noqa: E402
from wbi_core.io import load_json, sha256_file, write_json  # noqa: E402


class GateTests(unittest.TestCase):
    def test_all_27_genesis_requirements_are_non_compensatory(self):
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td) / "ws"
            (ws / "evidence/validation").mkdir(parents=True)
            genesis = verify_genesis(ROOT)
            requirements = load_json(ROOT / "constitution/requirements.json")["requirements"]
            proof = ws / "evidence/validation/proof.json"
            write_json(proof, {"status": "PASS", "kind": "test-proof"})
            binding = {"path": "evidence/validation/proof.json", "sha256": sha256_file(proof), "bytes": proof.stat().st_size}
            records = [{"id": item["id"], "status": "PASS", "evidence_bindings": [binding], "unknowns": []} for item in requirements]
            run = {"valid_as_of": "2026-07-26", "genesis": {"baseline_id": genesis["baseline_id"], "baseline_hash": genesis["locked_sha256"]}}
            write_json(ws / "evidence/validation/requirement-coverage.json", {
                "baseline_id": genesis["baseline_id"], "baseline_hash": genesis["locked_sha256"],
                "valid_as_of": "2026-07-26", "requirements": records,
            })
            self.assertEqual(_validate_requirement_coverage(ws, ROOT, run)["status"], "PASS")
            records[18]["status"] = "BLOCKED"
            write_json(ws / "evidence/validation/requirement-coverage.json", {
                "baseline_id": genesis["baseline_id"], "baseline_hash": genesis["locked_sha256"],
                "valid_as_of": "2026-07-26", "requirements": records,
            })
            result = _validate_requirement_coverage(ws, ROOT, run)
            self.assertEqual(result["status"], "BLOCKED")
            self.assertIn("WBI-GB-019", result["blocked_requirements"])

    def test_requirement_ids_cannot_be_reordered_or_omitted(self):
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td) / "ws"
            (ws / "evidence/validation").mkdir(parents=True)
            genesis = verify_genesis(ROOT)
            requirements = load_json(ROOT / "constitution/requirements.json")["requirements"]
            proof = ws / "evidence/validation/proof.json"
            write_json(proof, {"status": "PASS", "kind": "test-proof"})
            binding = {"path": "evidence/validation/proof.json", "sha256": sha256_file(proof), "bytes": proof.stat().st_size}
            records = [{"id": item["id"], "status": "PASS", "evidence_bindings": [binding]} for item in reversed(requirements)]
            run = {"valid_as_of": "2026-07-26", "genesis": {"baseline_id": genesis["baseline_id"], "baseline_hash": genesis["locked_sha256"]}}
            write_json(ws / "evidence/validation/requirement-coverage.json", {
                "baseline_id": genesis["baseline_id"], "baseline_hash": genesis["locked_sha256"],
                "valid_as_of": "2026-07-26", "requirements": records,
            })
            self.assertEqual(_validate_requirement_coverage(ws, ROOT, run)["status"], "BLOCKED")

    def test_requirement_evidence_hash_and_date_are_enforced(self):
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td) / "ws"
            (ws / "evidence/validation").mkdir(parents=True)
            genesis = verify_genesis(ROOT)
            requirements = load_json(ROOT / "constitution/requirements.json")["requirements"]
            proof = ws / "evidence/validation/proof.json"
            write_json(proof, {"status": "PASS"})
            binding = {"path": "evidence/validation/proof.json", "sha256": sha256_file(proof), "bytes": proof.stat().st_size}
            records = [{"id": item["id"], "status": "PASS", "evidence_bindings": [binding]} for item in requirements]
            run = {"valid_as_of": "2026-07-26", "genesis": {"baseline_id": genesis["baseline_id"], "baseline_hash": genesis["locked_sha256"]}}
            coverage = {
                "baseline_id": genesis["baseline_id"], "baseline_hash": genesis["locked_sha256"],
                "valid_as_of": "2026-07-25", "requirements": records,
            }
            write_json(ws / "evidence/validation/requirement-coverage.json", coverage)
            result = _validate_requirement_coverage(ws, ROOT, run)
            self.assertEqual(result["status"], "BLOCKED")
            self.assertTrue(any("valid_as_of" in item for item in result["errors"]))

            coverage["valid_as_of"] = "2026-07-26"
            write_json(proof, {"status": "TAMPERED"})
            write_json(ws / "evidence/validation/requirement-coverage.json", coverage)
            result = _validate_requirement_coverage(ws, ROOT, run)
            self.assertEqual(result["status"], "BLOCKED")
            self.assertTrue(any("hash mismatch" in item for item in result["errors"]))

    def test_malformed_workspace_fails_closed_without_traceback(self):
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td) / "ws"
            ws.mkdir()
            write_json(ws / "run.json", {"run_id": "broken"})
            write_json(ws / "state.json", {"run_id": "broken"})
            result = gate_workspace(ws)
            self.assertEqual(result["status"], "BLOCKED")
            self.assertTrue(result["errors"])
            self.assertIn("never a PASS", result["claim_boundary"])

    def test_invalid_json_workspace_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td) / "ws"
            ws.mkdir()
            (ws / "run.json").write_text("{invalid", encoding="utf-8")
            write_json(ws / "state.json", {"run_id": "broken"})
            result = gate_workspace(ws)
            self.assertEqual(result["status"], "BLOCKED")
            self.assertTrue(any("could not safely evaluate" in item for item in result["errors"]))


if __name__ == "__main__":
    unittest.main()
