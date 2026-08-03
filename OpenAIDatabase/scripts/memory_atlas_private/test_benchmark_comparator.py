from __future__ import annotations
import copy, json, unittest
from pathlib import Path
from benchmark_comparator import compare
ROOT=Path(__file__).resolve().parents[2]
class BenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.registry=json.loads((ROOT/'benchmark/registry.v1.json').read_text(encoding='utf-8'))
        self.metrics=json.loads((ROOT/'fixtures/personal_benchmark_metrics.synthetic.json').read_text(encoding='utf-8'))
    def test_no_percentile_and_direction_only(self):
        result=compare(self.metrics,self.registry)
        self.assertTrue(all(row['percentile'] is None for row in result['comparisons']))
        self.assertIn(result['state'],{'DIRECTION_ONLY','INSUFFICIENT_DATA','NOT_COMPARABLE'})
    def test_exact_contract_can_compare(self):
        b=self.registry['benchmarks'][0]; exact={b['metric_key']:{k:b[k] for k in ('taxonomy_id','unit','window_definition','population_scope','inclusion_rule')}|{'sample_size':500,'value':0.42}}
        result=compare(exact,{'benchmarks':[b]})
        self.assertEqual(result['state'],'DIRECTLY_COMPARABLE'); self.assertIsNotNone(result['comparisons'][0]['delta'])
    def test_mismatch_refuses_delta(self):
        b=copy.deepcopy(self.registry['benchmarks'][0]); p={b['metric_key']:{'value':0.5,'sample_size':999,'taxonomy_id':'other','unit':b['unit'],'window_definition':b['window_definition'],'population_scope':b['population_scope'],'inclusion_rule':b['inclusion_rule']}}
        row=compare(p,{'benchmarks':[b]})['comparisons'][0]
        self.assertEqual(row['comparability_state'],'DIRECTION_ONLY'); self.assertIsNone(row['delta'])
if __name__=='__main__': unittest.main()
