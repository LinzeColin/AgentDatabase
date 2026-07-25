from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from helpers import create_target, populate_release_ready, run_script


class QualityAndEvaluationTests(unittest.TestCase):
    def test_release_quality_gate_and_eval_aggregate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = create_target(root)
            populate_release_ready(target, root / 'materials')
            quality = run_script('quality_check.py', target, '--phase', 'release')
            payload = json.loads(quality.stdout)
            self.assertTrue(payload['passed'], payload)
            aggregate = run_script('eval_runner.py', 'aggregate', target)
            data = json.loads(aggregate.stdout)
            self.assertTrue(data['passed'], data)
            self.assertGreater(data['candidate_baseline_delta'], 0.1)

    def test_prepare_creates_private_mapping_and_blind_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = create_target(root)
            populate_release_ready(target, root / 'materials')
            prepared = run_script('eval_runner.py', 'prepare', target, '--seed', '7')
            run_id = json.loads(prepared.stdout)['run_id']
            private = json.loads((target / 'evals/run-plan.json').read_text(encoding='utf-8'))
            packet = json.loads((target / 'evals/judge-packet.json').read_text(encoding='utf-8'))
            self.assertEqual(private['run_id'], run_id)
            self.assertIn('mapping', private['cases'][0])
            self.assertNotIn('mapping', packet['cases'][0])

    def test_holdout_leakage_hard_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = create_target(root)
            fixture = populate_release_ready(target, root / 'materials')
            claims_path = target / 'evidence/claims.jsonl'
            rows = [json.loads(line) for line in claims_path.read_text(encoding='utf-8').splitlines()]
            rows[0]['source_ids'].append(fixture['holdout_id'])
            claims_path.write_text('\n'.join(json.dumps(row) for row in rows) + '\n', encoding='utf-8')
            failed = run_script('quality_check.py', target, '--phase', 'release', check=False)
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn('holdout', failed.stdout.lower())


if __name__ == '__main__':
    unittest.main()
