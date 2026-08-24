from __future__ import annotations
import unittest,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from wbi_engineering.coverage import behavior_coverage,shadowing
from wbi_engineering.stochastic import paired_comparison
from wbi_engineering.evidence import validate_lease
from wbi_engineering.utility import utility_gate
from wbi_engineering.environment import environment_strength
from wbi_engineering.panel import independent_panel
class EngineeringTests(unittest.TestCase):
 def test_coverage(self):self.assertTrue(behavior_coverage(['a'],[{'id':'a','status':'PASS'}])['valid'])
 def test_shadowing(self):self.assertEqual(shadowing([{'slug':'a','description':'white box skill test'},{'slug':'b','description':'white box skill test'}])['collision_count'],1)
 def test_stochastic_inconclusive_or_improved(self):self.assertIn(paired_comparison([0,0,0],[1,1,1],100,1)['decision'],{'IMPROVED'})
 def test_lease_stale(self):self.assertEqual(validate_lease({'candidate_hash':'a','expires_at':'2026-01-01T00:00:00Z'},{'candidate_hash':'b'},'2026-07-29T00:00:00Z')['state'],'STALE')
 def test_utility_hard_failure(self):self.assertEqual(utility_gate({'outcome_gain':10},['SECURITY'])['decision'],'REVERT')
 def test_environment_not_claimed(self):self.assertEqual(environment_strength({})['status'],'NOT_PROVEN')
 def test_panel_unavailable(self):self.assertEqual(independent_panel([],None)['status'],'INDEPENDENT_REVIEW_UNAVAILABLE')
if __name__=='__main__':unittest.main()
