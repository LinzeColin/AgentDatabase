from __future__ import annotations

import copy
import json
import unittest

from helpers import ROOT, load_json
from teleiosis_core.common import TeleiosisError
from teleiosis_core.review import validate_persona_evidence, validate_reviews
from teleiosis_core.skill_audit import validate_three_passes
from teleiosis_core.taskpack import fresh_builder_simulation, validate_taskpack, validate_traceability


class V5GovernanceTests(unittest.TestCase):
    def test_taskpack_validation(self) -> None:
        result = validate_taskpack(ROOT)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["traceability"]["criteria"], 30)
        self.assertEqual(result["traceability"]["mapped"], 30)
        self.assertEqual(result["traceability"]["tasks"], 30)

    def test_skill_audit(self) -> None:
        result = validate_three_passes(ROOT)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual([item["pass"] for item in result["passes"]], ["A", "B", "C"])
        self.assertEqual(len({item["input_hash"] for item in result["passes"]}), 3)
        self.assertEqual(result["formal_verifier_pass"], "NOT_ISSUED")

    def test_persona_gate(self) -> None:
        evidence = load_json("evidence/preparation/persona-team-evidence.json")
        result = validate_persona_evidence(evidence)
        self.assertEqual(result["status"], "INSUFFICIENT_ROSTER_FALLBACK")
        self.assertFalse(evidence["persona_contributions_counted"])
        self.assertEqual(evidence["fallback_mode"], "neutral_functional_roles")

    def test_persona_without_dossier_cannot_claim_valid_call(self) -> None:
        invalid = {
            "status": "VALID_PERSONA_TEAM_CALL",
            "dossier_hash": None,
            "claim_ids": [],
            "divergences_presented": False,
        }
        with self.assertRaises(TeleiosisError) as ctx:
            validate_persona_evidence(invalid)
        self.assertEqual(ctx.exception.code, "PERSONA_DOSSIER_GATE")

    def test_review_contract(self) -> None:
        result = validate_reviews(ROOT)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["ten_lens"]["lenses"], 10)
        self.assertEqual([item["roles"] for item in result["role_rounds"]], [6, 6])
        self.assertEqual(result["formal_independent_review"], "UNAVAILABLE")

    def test_fresh_builder_v5(self) -> None:
        result = fresh_builder_simulation(ROOT)
        self.assertEqual(result["status"], "ACCEPTANCE_PASS")
        self.assertTrue(result["only_environment_bound_unknowns_remain"])
        self.assertEqual(result["environment_bound_tasks"], 3)

    def test_traceability_cycle_is_rejected(self) -> None:
        acceptance = load_json("ACCEPTANCE_CONTRACT.json")
        dag = load_json("TASK_DAG.json")
        trace = load_json("TRACEABILITY_MATRIX.json")
        broken = copy.deepcopy(dag)
        broken["tasks"][0]["dependencies"] = [broken["tasks"][-1]["id"]]
        with self.assertRaises(TeleiosisError) as ctx:
            validate_traceability(acceptance, broken, trace)
        self.assertEqual(ctx.exception.code, "DAG_CYCLE")


if __name__ == "__main__":
    unittest.main()
