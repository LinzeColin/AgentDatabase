from __future__ import annotations
import copy,json,unittest
from pathlib import Path
from same_run_oracle import evaluate
ROOT=Path(__file__).resolve().parents[2]  # OpenAIDatabase/ — the oracles live under scripts/
class SameRunTests(unittest.TestCase):
 def setUp(self): self.snapshot=json.loads((ROOT/'fixtures/live_snapshot.synthetic.json').read_text()); self.receipts=json.loads((ROOT/'fixtures/same_run_receipts.synthetic.json').read_text())
 def test_stable_passes(self): self.assertEqual(evaluate(self.snapshot,self.receipts,mode='stable')['verdict'],'PASS')
 def test_stitched_fails(self):
  r=copy.deepcopy(self.receipts); r['receipts']['status_projection']['run_id']='other'; self.assertEqual(evaluate(self.snapshot,r,mode='stable')['verdict'],'FAIL')
 def test_core_does_not_require_restore(self):
  r=copy.deepcopy(self.receipts); r['receipts'].pop('restore_receipt'); self.assertEqual(evaluate(self.snapshot,r,mode='core')['verdict'],'PASS')
 def test_deployment_stitch_fails(self):
  r=copy.deepcopy(self.receipts); r['receipts']['browser_receipt']['deployment_revision']='other'; self.assertEqual(evaluate(self.snapshot,r,mode='stable')['verdict'],'FAIL')
if __name__=='__main__': unittest.main()
