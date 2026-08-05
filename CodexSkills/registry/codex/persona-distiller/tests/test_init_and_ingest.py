from __future__ import annotations

import json
import tempfile
import unittest
from email.message import EmailMessage
from pathlib import Path

from helpers import create_target, run_script


class InitAndIngestTests(unittest.TestCase):
    def test_init_target_structure_and_frontmatter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = create_target(Path(tmp))
            self.assertTrue((target / 'SKILL.md').is_file())
            self.assertTrue((target / 'evidence/source-ledger.jsonl').is_file())
            skill = (target / 'SKILL.md').read_text(encoding='utf-8')
            self.assertIn('name: example-thinker', skill)
            meta = json.loads((target / 'meta.json').read_text(encoding='utf-8'))
            self.assertEqual(meta['profile'], 'quick')
            self.assertEqual(meta['status'], 'draft')
            self.assertEqual(meta['identity_selection']['primary'], 'thinker-educator')
            # ★ v0.0.0.150：夹具不再写空候选数组（空 → `unverified`，那是「没核」不是「干净」），
            #   所以这里从 'none' 改成 'single'。
            self.assertEqual(meta['namesake_gate']['resolution'], 'single')
            self.assertEqual(meta['normalized_name'], 'examplethinker')
            # ★ 同上：夹具现在给的是一个已解析的单候选，所以这里绑定了 uid 而不是 None。
            self.assertEqual(meta['chosen_subject_uid'], 'example-thinker')
            self.assertEqual(meta['builder_version'], 'v0.0.0.5')
            self.assertIsNone(meta['product_version'])
            self.assertFalse(meta['runtime_invocation_versioning'])
            self.assertTrue((target / 'route-manifest.json').is_file())
            self.assertTrue((target / 'runtime/invocations.jsonl').is_file())
            self.assertTrue((target / 'scripts/runtime_recorder.py').is_file())
            self.assertFalse((target / 'runtime/state.json').exists())
            self.assertFalse((target / 'scripts/invocation_manager.py').exists())

    def test_ingest_text_subtitle_email_and_holdout_protection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = create_target(root)
            text = root / 'note.md'
            text.write_text('A primary note with a decision trace.\n' * 10, encoding='utf-8')
            srt = root / 'talk.srt'
            srt.write_text('1\n00:00:00,000 --> 00:00:01,000\nHello world\n\n2\n00:00:01,100 --> 00:00:02,000\nSecond line\n', encoding='utf-8')
            msg = EmailMessage()
            msg['From'] = 'author@example.test'
            msg['To'] = 'reader@example.test'
            msg['Subject'] = 'Decision note'
            msg.set_content('Email body with reasoning.')
            eml = root / 'mail.eml'
            eml.write_bytes(msg.as_bytes())
            completed = run_script('ingest.py', target, text, srt, eml, '--tier', 'P1', '--author', 'Example Thinker', '--dimension', 'conversations', '--redact-pii')
            payload = json.loads(completed.stdout)
            self.assertEqual(payload['registered'], 3)
            ledger = [json.loads(line) for line in (target / 'evidence/source-ledger.jsonl').read_text(encoding='utf-8').splitlines()]
            self.assertEqual(len(ledger), 3)
            self.assertTrue(all(record['extraction_status'] == 'normalized' for record in ledger))
            normalized_email = target / ledger[2]['normalized_path']
            self.assertIn('[REDACTED:email]', normalized_email.read_text(encoding='utf-8'))

            # A byte-identical source cannot be moved into Holdout after being seen by builders.
            duplicate = run_script('ingest.py', target, text, '--holdout', '--tier', 'P1', '--author', 'Example Thinker', '--dimension', 'decisions', check=False)
            self.assertNotEqual(duplicate.returncode, 0)
            self.assertIn('Cross-split duplicate', duplicate.stderr)


if __name__ == '__main__':
    unittest.main()
