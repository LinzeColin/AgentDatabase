from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / "scripts"))

from wbi_core.coverage import evaluate_skill_coverage
from wbi_core.shadowing import evaluate_skill_shadowing
from wbi_core.stochastic import compare_stochastic_results
from wbi_core.io import write_json


class CoverageShadowingStochasticTests(unittest.TestCase):
    def test_coverage_fails_when_hard_behavior_unexercised(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); constraints=root/'constraints.json'; trajectories=root/'t.jsonl'
            write_json(constraints,{"constraints":[{"constraint_id":"C1","severity":"HARD","family":"safety"},{"constraint_id":"C2","severity":"NORMAL","family":"quality"}]})
            trajectories.write_text(json.dumps({"task_family":"quality","satisfied_constraints":["C2"],"failed_constraints":[],"exercised_constraints":["C2"]})+'\n')
            result=evaluate_skill_coverage(constraints,trajectories)
            self.assertEqual(result["coverage_status"],"INCOMPLETE")
            self.assertEqual(result["hard_uncovered"],["C1"])

    def test_coverage_passes_when_contract_is_exercised(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); constraints=root/'constraints.json'; trajectories=root/'t.jsonl'
            write_json(constraints,{"constraints":[{"constraint_id":"C1","severity":"HARD","family":"safety"},{"constraint_id":"C2","severity":"NORMAL","family":"quality"}]})
            trajectories.write_text('\n'.join([json.dumps({"task_family":"safety","satisfied_constraints":["C1"],"failed_constraints":[],"exercised_constraints":["C1"]}),json.dumps({"task_family":"quality","satisfied_constraints":["C2"],"failed_constraints":[],"exercised_constraints":["C2"]})])+'\n')
            self.assertEqual(evaluate_skill_coverage(constraints,trajectories)["coverage_status"],"PASS")

    def test_shadowing_detects_library_regression(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'records.jsonl'
            p.write_text('\n'.join([json.dumps({"query_id":"q1","intended_skill":"a","selected_skill":"b","ranked_skills":["b","a"],"single_skill_outcome":1.0,"library_outcome":0.5}),json.dumps({"query_id":"q2","intended_skill":None,"selected_skill":"b","ranked_skills":["b"],"single_skill_outcome":1.0,"library_outcome":0.8})])+'\n')
            result=evaluate_skill_shadowing(p)
            self.assertEqual(result["shadowing_status"],"SHADOWING_RISK")
            self.assertTrue(result["blockers"])

    def test_shadowing_passes_clean_selection(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'records.jsonl'
            rows=[]
            for i in range(10): rows.append({"query_id":"q%d"%i,"intended_skill":"a","selected_skill":"a","ranked_skills":["a","b"],"single_skill_outcome":1.0,"library_outcome":1.0})
            rows.append({"query_id":"negative","intended_skill":None,"selected_skill":"NO_SKILL","ranked_skills":[],"single_skill_outcome":1.0,"library_outcome":1.0})
            p.write_text('\n'.join(json.dumps(x) for x in rows)+'\n')
            self.assertEqual(evaluate_skill_shadowing(p)["shadowing_status"],"PASS")

    def test_stochastic_comparison_is_inconclusive_underpowered(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'r.jsonl'; rows=[]
            for system in ('base','cand'):
                for i in range(5): rows.append({"system_id":system,"success":i<4})
            p.write_text('\n'.join(json.dumps(x) for x in rows)+'\n')
            self.assertEqual(compare_stochastic_results(p,baseline_id='base',candidate_id='cand',minimum_trials=20)["stochastic_decision"],"INCONCLUSIVE")

    def test_stochastic_comparison_supports_clear_candidate(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'r.jsonl'; rows=[]
            rows += [{"system_id":"base","success":i<5} for i in range(40)]
            rows += [{"system_id":"cand","success":i<35} for i in range(40)]
            p.write_text('\n'.join(json.dumps(x) for x in rows)+'\n')
            self.assertEqual(compare_stochastic_results(p,baseline_id='base',candidate_id='cand',minimum_trials=20)["stochastic_decision"],"SUPPORTED")


if __name__ == '__main__':
    unittest.main()
