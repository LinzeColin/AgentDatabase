from __future__ import annotations
import copy,json,tempfile,unittest
from pathlib import Path
from live_snapshot_store import LiveSnapshotStore,SnapshotStoreError
ROOT=Path(__file__).resolve().parents[2]
class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.store=LiveSnapshotStore(Path(self.tmp.name),ROOT/'schema/memory_atlas.live_snapshot.v1.schema.json'); self.snapshot=json.loads((ROOT/'fixtures/live_snapshot.synthetic.json').read_text())
    def tearDown(self): self.tmp.cleanup()
    def test_publish_current_history_previous(self):
        first=self.store.publish(self.snapshot); self.assertEqual(first['state'],'PUBLISHED'); self.assertEqual(first['trace_id'],self.snapshot['run']['trace_id']); self.assertEqual(first['deployment_revision'],self.snapshot['release']['deployment_revision']); self.assertTrue(self.store.current.exists())
        second=copy.deepcopy(self.snapshot); second['run']['run_id']='synthetic-run-2'; second['run']['trace_id']='synthetic-trace-2'; second['run']['source_completed_at']='2026-08-03T10:25:00Z'; second['generated_at']='2026-08-03T10:26:00Z'
        for row in second['truth']['same_run_evidence'].values():
            if row['state']=='PASS': row['run_id']=second['run']['run_id']; row['trace_id']=second['run']['trace_id']
        self.store.publish(second); self.assertTrue(self.store.previous.exists()); self.assertEqual(self.store.read_current()['run']['run_id'],'synthetic-run-2')
    def test_regression_refused(self):
        self.store.publish(self.snapshot); old=copy.deepcopy(self.snapshot); old['run']['run_id']='old-run-0001'; old['run']['trace_id']='old-trace-0001'; old['run']['source_completed_at']='2026-08-03T09:00:00Z'
        for row in old['truth']['same_run_evidence'].values():
            if row['state']=='PASS': row['run_id']=old['run']['run_id']; row['trace_id']=old['run']['trace_id']
        with self.assertRaises(SnapshotStoreError): self.store.publish(old)
        self.assertEqual(self.store.read_current()['run']['run_id'],self.snapshot['run']['run_id'])
    def test_authority_mismatch_refused(self):
        broken=copy.deepcopy(self.snapshot); broken['truth']['same_run_evidence']['r2_readback']['run_id']='wrong'
        with self.assertRaises(SnapshotStoreError): self.store.publish(broken)
    def test_recovery_only_when_invalid(self):
        self.store.publish(self.snapshot); self.assertEqual(self.store.recover_previous_if_current_invalid()['state'],'NO_ACTION')
if __name__=='__main__': unittest.main()
