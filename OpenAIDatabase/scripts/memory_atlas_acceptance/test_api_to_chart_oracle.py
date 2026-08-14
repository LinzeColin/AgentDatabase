from __future__ import annotations
import copy,json,unittest
from pathlib import Path
from api_to_chart_oracle import evaluate
ROOT=Path(__file__).resolve().parents[2]  # OpenAIDatabase/ — the oracles live under scripts/
class OracleTests(unittest.TestCase):
 def setUp(self): self.snapshot=json.loads((ROOT/'fixtures/live_snapshot.synthetic.json').read_text()); self.receipt=json.loads((ROOT/'fixtures/browser_receipt.synthetic.json').read_text())
 def test_matching_passes(self): self.assertEqual(evaluate(self.snapshot,self.receipt)['verdict'],'PASS')
 def test_changed_chart_fails(self):
  r=copy.deepcopy(self.receipt); r['values']['verified_outcome_rate_event']=0.99; self.assertEqual(evaluate(self.snapshot,r)['verdict'],'FAIL')
 def test_stitched_run_fails(self):
  r=copy.deepcopy(self.receipt); r['trace_id']='other'; self.assertEqual(evaluate(self.snapshot,r)['verdict'],'FAIL')
 def test_missing_no_store_fails(self):
  r=copy.deepcopy(self.receipt); r['api_cache_control']='private, max-age=300'; self.assertEqual(evaluate(self.snapshot,r)['verdict'],'FAIL')
if __name__=='__main__': unittest.main()
