from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from helpers import create_target, run_target_script


class RuntimeRecordingTests(unittest.TestCase):
    def test_direct_runtime_plan_has_no_identity_gate_or_invocation_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = create_target(Path(tmp), identity='1:40+4:60')
            plan = json.loads(run_target_script(
                target, 'runtime_router.py', 'plan', '--task', '设计并审查一个代码架构',
            ).stdout)
            self.assertFalse(plan['identity_route']['user_selection_required'])
            self.assertIsNone(plan['output_contract']['invocation_version'])
            self.assertFalse(plan['output_contract']['chat_version_label'])
            self.assertFalse(plan['output_contract']['versioned_file_names'])

    def test_completed_and_failed_records_are_unnumbered(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = create_target(root)
            result_file = root / 'result.md'
            result_file.write_text('verified output', encoding='utf-8')
            completed = json.loads(run_target_script(
                target,
                'runtime_recorder.py',
                'record',
                '--status',
                'completed',
                '--task',
                'teach this concept',
                '--summary',
                'done',
                '--result-path',
                result_file,
            ).stdout)
            failed = json.loads(run_target_script(
                target,
                'runtime_recorder.py',
                'record',
                '--status',
                'failed',
                '--task',
                'retry',
                '--summary',
                'partial',
                '--error',
                'tool unavailable',
            ).stdout)
            for record in [completed, failed]:
                self.assertFalse({'run_id', 'artifact_version', 'serial', 'version_override'} & set(record))
            self.assertEqual(
                completed['artifacts'][0]['sha256'],
                hashlib.sha256(result_file.read_bytes()).hexdigest(),
            )
            self.assertEqual(completed['artifacts'][0]['source_name'], 'result.md')
            verify = json.loads(run_target_script(target, 'runtime_recorder.py', 'verify').stdout)
            self.assertTrue(verify['valid'], verify)
            self.assertEqual(verify['record_count'], 2)
            self.assertEqual(verify['numbered_records'], 0)

    def test_task_content_storage_remains_explicit_opt_in(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = create_target(Path(tmp))
            metadata_only = json.loads(run_target_script(
                target,
                'runtime_recorder.py',
                'record',
                '--status',
                'completed',
                '--task',
                'sensitive body',
            ).stdout)
            stored = json.loads(run_target_script(
                target,
                'runtime_recorder.py',
                'record',
                '--status',
                'completed',
                '--task',
                'explicit body',
                '--store-task',
            ).stdout)
            self.assertIsNone(metadata_only['task_content'])
            self.assertEqual(metadata_only['privacy_mode'], 'metadata')
            self.assertEqual(stored['task_content'], 'explicit body')
            self.assertEqual(stored['privacy_mode'], 'content')

    def test_failed_record_requires_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = create_target(Path(tmp))
            failed = run_target_script(
                target,
                'runtime_recorder.py',
                'record',
                '--status',
                'failed',
                '--task',
                'x',
                check=False,
            )
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn('--error is required', failed.stderr)


if __name__ == '__main__':
    unittest.main()
