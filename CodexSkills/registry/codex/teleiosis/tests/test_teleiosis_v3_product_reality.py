from __future__ import annotations
import copy, json, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; SCRIPTS=ROOT/'scripts'
if str(SCRIPTS) not in sys.path: sys.path.insert(0,str(SCRIPTS))
from wbi_product.contracts import REQUIRED_CAPABILITIES, validate_product_reality_run
from wbi_product.gate import evaluate_product_reality

class ProductRealityTests(unittest.TestCase):
    def setUp(self): self.example=json.loads((ROOT/'assets/product/templates/product_reality_run.example.json').read_text(encoding='utf-8'))
    def test_valid_example_stops_at_field_pending(self):
        self.assertEqual(validate_product_reality_run(self.example),[]); result=evaluate_product_reality(self.example); self.assertEqual(result['state'],'FIELD_VALIDATION_PENDING'); self.assertFalse(result['derived']['field_validation_complete'])
    def test_no_field_cannot_be_upgraded(self):
        value=copy.deepcopy(self.example); value['field_experiments'][0]['evidence_class']='SYNTHETIC'; value['field_experiments'][0].pop('consent_ref',None)
        result=evaluate_product_reality(value); self.assertEqual(result['state'],'FIELD_VALIDATION_PENDING'); self.assertFalse(result['derived']['field_validation_complete'])
    def test_pending_provenance_blocks(self):
        value=copy.deepcopy(self.example); value['provenance'][0]['status']='PENDING'; self.assertEqual(evaluate_product_reality(value)['state'],'BLOCKED')
    def test_approved_provenance_requires_review_fields(self):
        value=copy.deepcopy(self.example); value['provenance'][0].pop('reviewer'); result=evaluate_product_reality(value); self.assertEqual(result['state'],'BLOCKED'); self.assertTrue(any(r['code']=='PROVENANCE_APPROVAL_INCOMPLETE' for r in result['reasons']))
    def test_census_deletion_cannot_shrink_denominator(self):
        value=copy.deepcopy(self.example); value['runtime_items']=[] if False else value.get('runtime_items'); value['census']['runtime_items']=[]
        result=evaluate_product_reality(value); self.assertEqual(result['state'],'BLOCKED'); self.assertTrue(result['derived']['source_only'])
    def test_all_eight_dimensions_required(self):
        value=copy.deepcopy(self.example); value['coverage']=[x for x in value['coverage'] if x['dimension']!='Fault']; self.assertEqual(evaluate_product_reality(value)['state'],'BLOCKED')
    def test_negative_control_must_detect_mutation(self):
        value=copy.deepcopy(self.example); value['negative_controls'][0]['observed_failure']=False; result=evaluate_product_reality(value); self.assertEqual(result['state'],'BLOCKED'); self.assertTrue(any(r['code']=='NEGATIVE_CONTROL_MISSING_OR_SURVIVED' for r in result['reasons']))
    def test_open_p1_blocks(self):
        value=copy.deepcopy(self.example); value['defects'][0].update({'severity':'P1','status':'OPEN'}); self.assertEqual(evaluate_product_reality(value)['state'],'BLOCKED')
    def test_full_capability_manifest_is_mandatory(self):
        value=copy.deepcopy(self.example); value['capability_manifest']=value['capability_manifest'][:-1]; errors=validate_product_reality_run(value); self.assertTrue(any('全量能力' in e for e in errors))
    def test_product_gate_never_returns_pass(self):
        state=evaluate_product_reality(self.example)['state']; self.assertNotIn(state,{'PASS','VERIFIED','PRODUCTION_READY'})
    def test_capture_recapture_is_signal_only(self):
        result=evaluate_product_reality(self.example); self.assertIsNotNone(result['derived']['capture_recapture_estimated_total_defects']); self.assertEqual(result['derived']['capture_recapture_use'],'RESIDUAL_RISK_SIGNAL_ONLY')

if __name__=='__main__': unittest.main(verbosity=2)
