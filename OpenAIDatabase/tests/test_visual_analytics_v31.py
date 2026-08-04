from __future__ import annotations
import copy, json, unittest
from pathlib import Path
from OpenAIDatabase.scripts.memory_atlas_private.visual_analytics import build_visual_analytics
ROOT = Path(__file__).resolve().parents[1]

class VisualAnalyticsTests(unittest.TestCase):
    def setUp(self):
        self.events=json.loads((ROOT/'fixtures/normalized_events.synthetic.json').read_text(encoding='utf-8'))
    def test_deterministic_and_separate_bases(self):
        a=build_visual_analytics(self.events); b=build_visual_analytics(copy.deepcopy(self.events))
        self.assertEqual(a,b); self.assertEqual(len(a['visuals']),3)
        self.assertEqual(a['metrics']['verified_outcome_rate_event']['denominator_basis'],'event_count')
        self.assertEqual(a['metrics']['verified_outcome_rate_work_time']['denominator_basis'],'known_work_time_minutes')
        self.assertTrue(a['metrics']['verification_debt_proxy_event']['proxy'])
    def test_time_to_truth_requires_evidence(self):
        value=build_visual_analytics(self.events)
        trend=next(row for row in value['visuals'] if row['id']=='verification_debt_trend')['rows']
        self.assertEqual(trend[1]['time_to_truth_hours'],12.0)
        self.assertIsNone(trend[0]['time_to_truth_hours'])
        self.assertEqual(trend[1]['time_to_truth_sample_count'],1)
    def test_verified_at_before_event_fails(self):
        broken=copy.deepcopy(self.events); broken[1]['verified_at']='2026-07-27T00:00:00Z'
        with self.assertRaises(ValueError): build_visual_analytics(broken)
    def test_bad_event_fails(self):
        broken=copy.deepcopy(self.events); broken[0].pop('model_tool')
        with self.assertRaises(ValueError): build_visual_analytics(broken)
    def test_empty_truthful(self):
        value=build_visual_analytics([])
        self.assertEqual(value['event_count'],0); self.assertIsNone(value['metrics']['verified_outcome_rate_event']['value'])

if __name__=='__main__': unittest.main()
