from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from helpers import create_target, run_script


class VersioningTests(unittest.TestCase):
    def test_snapshot_diff_verify_and_rollback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = create_target(Path(tmp))
            original = (target / 'persona.md').read_text(encoding='utf-8')
            first = json.loads(run_script('version_manager.py', 'snapshot', target, '--reason', 'initial').stdout)
            first_id = first['version_id']
            (target / 'persona.md').write_text(original + '\nA changed line.\n', encoding='utf-8')
            second = json.loads(run_script('version_manager.py', 'snapshot', target, '--reason', 'changed').stdout)
            self.assertNotEqual(first_id, second['version_id'])
            diff = json.loads(run_script('version_manager.py', 'diff', target, '--from', first_id, '--to', second['version_id']).stdout)
            self.assertIn('persona.md', diff['modified'])
            verified = json.loads(run_script('version_manager.py', 'verify', target, '--version', first_id).stdout)
            self.assertTrue(verified['ok'])
            rollback = json.loads(run_script('version_manager.py', 'rollback', target, '--version', first_id).stdout)
            self.assertTrue(rollback['ok'])
            self.assertEqual((target / 'persona.md').read_text(encoding='utf-8'), original)
            self.assertIsNotNone(rollback['pre_rollback_backup'])


if __name__ == '__main__':
    unittest.main()
