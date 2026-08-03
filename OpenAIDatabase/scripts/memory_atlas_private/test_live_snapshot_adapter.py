from __future__ import annotations
import copy,json,unittest
from pathlib import Path
from live_snapshot_adapter import build_live_snapshot,LiveSnapshotError
ROOT=Path(__file__).resolve().parents[2]
class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.private=json.loads((ROOT/'fixtures/private_analytics.synthetic.json').read_text())
        self.visual=json.loads((ROOT/'fixtures/visual_analytics.synthetic.json').read_text())
        self.runtime=json.loads((ROOT/'fixtures/runtime_evidence.synthetic.json').read_text())
        self.benchmark=json.loads((ROOT/'fixtures/benchmark_result.synthetic.json').read_text())
    def build(self,private=None,visual=None,runtime=None): return build_live_snapshot(private or self.private,visual or self.visual,runtime or self.runtime,self.benchmark,evaluated_at='2026-08-03T10:18:00Z')
    def test_split_metrics_and_privacy(self):
        v=self.build(); self.assertEqual(v['run']['trace_id'],self.runtime['trace_id']); self.assertEqual(len(v['visuals']),3)
        self.assertEqual(v['analysis']['verified_outcome_rate_event']['denominator_basis'],'event_count')
        self.assertEqual(v['analysis']['verified_outcome_rate_work_time']['denominator_basis'],'known_work_time_minutes')
        self.assertTrue(v['analysis']['verification_debt_proxy_event']['proxy']); self.assertFalse(v['privacy']['raw_content_included'])
    def test_legacy_mixed_rate_not_trusted(self):
        p=copy.deepcopy(self.private); p['behavior_economics']['verified_outcome_rate']=0.999
        v=self.build(private=p); self.assertNotEqual(v['analysis']['verified_outcome_rate_event']['value'],0.999); self.assertTrue(v['analysis']['legacy_verified_outcome_rate']['compatibility_only'])
    def test_nonterminal_refused(self):
        p=copy.deepcopy(self.private); p['run']['state']='REFRESHING_ATLAS'
        with self.assertRaises(LiveSnapshotError): self.build(private=p)
    def test_same_run_refused(self):
        r=copy.deepcopy(self.runtime); r['same_run_evidence']['r2_readback']['trace_id']='other'
        with self.assertRaises(LiveSnapshotError): self.build(runtime=r)
    def test_tier_b_missing_degrades_without_emptying(self):
        v=self.build(); self.assertEqual(v['coverage']['product_state'],'DEGRADED'); self.assertGreater(v['analysis']['event_count'],0)
if __name__=='__main__': unittest.main()
