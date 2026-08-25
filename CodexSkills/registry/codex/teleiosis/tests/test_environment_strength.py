from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / "scripts"))

from wbi_core.environment_strength import capture_environment_snapshot, attest_environment_strength
from wbi_core.io import write_json


class EnvironmentStrengthTests(unittest.TestCase):
    def make_evidence(self, root: Path):
        paths = []
        for name in ("frontier", "benchmark", "coverage", "shadowing"):
            path = root / (name + ".json")
            write_json(path, {"status": "PASS", "name": name})
            paths.append(path)
        return paths

    def test_missing_evidence_can_snapshot_but_cannot_claim_strength(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            target = root / "target"; target.mkdir(); (target / "SKILL.md").write_text("x", encoding="utf-8")
            optimizer = root / "optimizer"; optimizer.mkdir(); (optimizer / "SKILL.md").write_text("y", encoding="utf-8")
            snap_path = root / "snapshot.json"
            snap = capture_environment_snapshot(target, optimizer, valid_as_of="2026-07-26", output=snap_path)
            self.assertEqual(snap["snapshot_status"], "PASS")
            candidate_set = root / "candidates.json"
            write_json(candidate_set, {
                "selected_candidate": "c1", "metrics": [{"name": "quality", "direction": "maximize"}],
                "candidates": [{"candidate_id": "c1", "metrics": {"quality": 1.0}, "hard_gate_failures": []}],
                "required_evidence_states": {},
            })
            result = attest_environment_strength(snap_path, candidate_set, checked_at="2026-07-27T00:00:00+00:00")
            self.assertEqual(result["environment_strength_status"], "NOT_PROVEN")

    def test_full_evidence_supports_bounded_pareto_attestation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            target = root / "target"; target.mkdir(); (target / "SKILL.md").write_text("x", encoding="utf-8")
            optimizer = root / "optimizer"; optimizer.mkdir(); (optimizer / "SKILL.md").write_text("y", encoding="utf-8")
            frontier, benchmark, coverage, shadowing = self.make_evidence(root)
            snap_path = root / "snapshot.json"
            capture_environment_snapshot(
                target, optimizer, valid_as_of="2026-07-26", validity_days=30,
                frontier_scan=frontier, benchmark_summary=benchmark,
                coverage_summary=coverage, shadowing_summary=shadowing, output=snap_path,
            )
            candidate_set = root / "candidates.json"
            write_json(candidate_set, {
                "selected_candidate": "c2",
                "metrics": [{"name": "quality", "direction": "maximize"}, {"name": "cost", "direction": "minimize"}],
                "candidates": [
                    {"candidate_id": "c1", "metrics": {"quality": 0.8, "cost": 5}, "hard_gate_failures": []},
                    {"candidate_id": "c2", "metrics": {"quality": 0.9, "cost": 4}, "hard_gate_failures": []},
                ],
                "required_evidence_states": {
                    "frontier": "PASS", "benchmark_integrity": "VALID", "outcome": "SUPPORTED",
                    "coverage": "PASS", "shadowing": "PASS", "cost_evidence": "MEASURED",
                    "engineering_release": "INSTALLABLE",
                },
            })
            result = attest_environment_strength(snap_path, candidate_set, checked_at="2026-07-27T00:00:00+00:00")
            self.assertEqual(result["environment_strength_status"], "PARETO_UNDOMINATED_FOR_VERIFIED_CURRENT_ENVIRONMENT")
            self.assertEqual(result["pareto_frontier"], ["c2"])

    def test_expiry_forces_reheat(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            target = root / "target"; target.mkdir(); (target / "SKILL.md").write_text("x", encoding="utf-8")
            optimizer = root / "optimizer"; optimizer.mkdir(); (optimizer / "SKILL.md").write_text("y", encoding="utf-8")
            paths = self.make_evidence(root)
            snap_path = root / "snapshot.json"
            capture_environment_snapshot(target, optimizer, valid_as_of="2026-07-01", validity_days=1, frontier_scan=paths[0], benchmark_summary=paths[1], coverage_summary=paths[2], shadowing_summary=paths[3], output=snap_path)
            cs = root / "c.json"
            write_json(cs, {"selected_candidate":"c", "metrics":[{"name":"q","direction":"maximize"}], "candidates":[{"candidate_id":"c","metrics":{"q":1},"hard_gate_failures":[]}], "required_evidence_states":{}})
            result = attest_environment_strength(snap_path, cs, checked_at="2026-07-26T00:00:00+00:00")
            self.assertEqual(result["environment_strength_status"], "REHEAT_REQUIRED")

    def test_dominated_candidate_is_regressed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); target=root/'t'; optimizer=root/'o'; target.mkdir(); optimizer.mkdir(); (target/'SKILL.md').write_text('x'); (optimizer/'SKILL.md').write_text('y')
            paths=self.make_evidence(root); snap=root/'s.json'
            capture_environment_snapshot(target,optimizer,valid_as_of='2026-07-26',frontier_scan=paths[0],benchmark_summary=paths[1],coverage_summary=paths[2],shadowing_summary=paths[3],output=snap)
            cs=root/'c.json'; write_json(cs,{"selected_candidate":"weak","metrics":[{"name":"q","direction":"maximize"}],"candidates":[{"candidate_id":"weak","metrics":{"q":0.5},"hard_gate_failures":[]},{"candidate_id":"strong","metrics":{"q":1.0},"hard_gate_failures":[]}],"required_evidence_states":{}})
            self.assertEqual(attest_environment_strength(snap,cs,checked_at='2026-07-27T00:00:00+00:00')["environment_strength_status"],"REGRESSED")


if __name__ == "__main__":
    unittest.main()
