from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from helpers import create_target, run_script


class LedgerAndCorrectionTests(unittest.TestCase):
    def test_claim_rejects_holdout_and_accepts_train(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = create_target(root)
            train = root / 'train.md'
            train.write_text('train evidence\n' * 20, encoding='utf-8')
            holdout = root / 'holdout.md'
            holdout.write_text('holdout evidence\n' * 20, encoding='utf-8')
            train_id = json.loads(run_script('ingest.py', target, train, '--tier', 'P1', '--dimension', 'decisions').stdout)['results'][0]['source_id']
            holdout_id = json.loads(run_script('ingest.py', target, holdout, '--holdout', '--tier', 'P1', '--dimension', 'decisions').stdout)['results'][0]['source_id']
            rejected = run_script(
                'ledger.py', 'claim-add', target, '--claim', 'Bad leaked Claim', '--category', 'heuristic', '--status', 'pattern', '--source', holdout_id,
                check=False,
            )
            self.assertNotEqual(rejected.returncode, 0)
            accepted = run_script(
                'ledger.py', 'claim-add', target, '--claim', 'Evidence-backed Claim', '--category', 'fact', '--status', 'fact', '--source', train_id,
                '--confidence', '0.8', '--time-scope', 'test period',
            )
            payload = json.loads(accepted.stdout)
            self.assertTrue(payload['claim_id'].startswith('clm-'))
            validated = run_script('ledger.py', 'validate', target)
            self.assertTrue(json.loads(validated.stdout)['ok'])

    def test_correction_log_is_append_only_and_active_projection_updates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = create_target(Path(tmp))
            added = run_script('correction_manager.py', 'add', target, '--text', 'Prefer a reversible experiment first.', '--scope', 'persona')
            correction_id = json.loads(added.stdout)['event']['correction_id']
            active = (target / 'corrections/ACTIVE.md').read_text(encoding='utf-8')
            self.assertIn(correction_id, active)
            run_script('correction_manager.py', 'status', target, '--correction-id', correction_id, '--status', 'resolved', '--rationale', 'Superseded by later evidence.')
            events = (target / 'corrections/corrections.jsonl').read_text(encoding='utf-8').splitlines()
            self.assertEqual(len(events), 2)
            self.assertNotIn(correction_id, (target / 'corrections/ACTIVE.md').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
