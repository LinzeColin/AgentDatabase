from __future__ import annotations
import json,tempfile,unittest
from pathlib import Path
from OpenAIDatabase.scripts.memory_atlas_private.api_live_snapshot import response
from OpenAIDatabase.scripts.memory_atlas_private.live_snapshot_store import LiveSnapshotStore
ROOT=Path(__file__).resolve().parents[1]
class ApiTests(unittest.TestCase):
    def setUp(self): self.tmp=tempfile.TemporaryDirectory(); self.root=Path(self.tmp.name); self.schema=ROOT/'schema/memory_atlas.live_snapshot.v1.schema.json'
    def tearDown(self): self.tmp.cleanup()
    def test_403(self): self.assertEqual(response(self.root,self.schema,authorized=False)[0],403)
    def test_404(self): self.assertEqual(response(self.root,self.schema,authorized=True)[0],404)
    def test_200_identity_and_no_store(self):
        s=json.loads((ROOT/'fixtures/live_snapshot.synthetic.json').read_text()); LiveSnapshotStore(self.root,self.schema).publish(s)
        status,headers,body=response(self.root,self.schema,authorized=True); self.assertEqual(status,200); self.assertIn('no-store',headers['Cache-Control']); self.assertEqual(headers['X-Memory-Atlas-Trace-Id'],s['run']['trace_id']); self.assertEqual(json.loads(body)['run']['run_id'],s['run']['run_id'])
    def test_503_invalid(self):
        self.root.mkdir(exist_ok=True); (self.root/'current.json').write_text('{}')
        self.assertEqual(response(self.root,self.schema,authorized=True)[0],503)
if __name__=='__main__': unittest.main()
