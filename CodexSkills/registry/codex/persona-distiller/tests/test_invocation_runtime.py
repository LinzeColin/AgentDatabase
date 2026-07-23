from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from helpers import create_target, run_target_script


class InvocationRuntimeTests(unittest.TestCase):
    def test_menu_and_invalid_identity_do_not_consume_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = create_target(Path(tmp))
            run_target_script(target, 'runtime_router.py', 'menu')
            failed = run_target_script(target, 'invocation_manager.py', 'begin', '--identity', '7', '--task', 'x', check=False)
            self.assertNotEqual(failed.returncode, 0)
            state = json.loads((target / 'runtime/state.json').read_text())
            self.assertEqual(state['last_serial'], 0)
            self.assertFalse(any((target / 'runtime/runs').glob('0.0.0.*')))

    def test_first_failed_then_completed_runs_are_immutable_and_monotonic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = create_target(Path(tmp))
            first = json.loads(run_target_script(
                target, 'invocation_manager.py', 'begin', '--identity', '1', '--task', 'diagnose system'
            ).stdout)
            self.assertEqual(first['artifact_version'], '0.0.0.1')
            self.assertIsNone(first['task_content'])
            self.assertEqual(first['privacy_mode'], 'metadata')
            failed = json.loads(run_target_script(
                target, 'invocation_manager.py', 'fail', '0.0.0.1', '--error', 'tool unavailable', '--summary', 'partial analysis'
            ).stdout)
            self.assertEqual(failed['status'], 'failed')
            second = json.loads(run_target_script(
                target, 'invocation_manager.py', 'begin', '--identity', '沿用上次身份', '--task', 'retry'
            ).stdout)
            self.assertEqual(second['artifact_version'], '0.0.0.2')
            result_file = Path(tmp) / 'result.md'
            result_file.write_text('verified output', encoding='utf-8')
            completed = json.loads(run_target_script(
                target, 'invocation_manager.py', 'complete', '0.0.0.2', '--summary', 'done', '--result-path', result_file
            ).stdout)
            self.assertEqual(completed['status'], 'completed')
            self.assertEqual(completed['result_sha256'], hashlib.sha256(result_file.read_bytes()).hexdigest())
            self.assertEqual(completed['artifacts'][0]['logical_versioned_name'], 'result-v0.0.0.2.md')
            artifact_manifest = json.loads((target / 'runtime/runs/0.0.0.2/artifact-manifest.json').read_text())
            self.assertEqual(artifact_manifest['status'], 'completed')
            self.assertEqual(artifact_manifest['response_label'], '运行版本：0.0.0.2')
            terminal_again = run_target_script(
                target, 'invocation_manager.py', 'complete', '0.0.0.2', '--summary', 'mutate', check=False
            )
            self.assertNotEqual(terminal_again.returncode, 0)
            verify = json.loads(run_target_script(target, 'invocation_manager.py', 'verify').stdout)
            self.assertTrue(verify['valid'], verify)
            self.assertEqual(verify['serials'], [1, 2])

    def test_nine_hundred_ninety_ninth_invocation_format(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = create_target(Path(tmp))
            state_path = target / 'runtime/state.json'
            state = json.loads(state_path.read_text())
            state['last_serial'] = 998
            state_path.write_text(json.dumps(state), encoding='utf-8')
            record = json.loads(run_target_script(
                target, 'invocation_manager.py', 'begin', '--identity', '5', '--task', 'teach'
            ).stdout)
            self.assertEqual(record['artifact_version'], '0.0.0.999')

    def test_explicit_override_requires_audit_flag_and_never_reuses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = create_target(Path(tmp))
            denied = run_target_script(
                target, 'invocation_manager.py', 'begin', '--identity', '2', '--version-override', '0.0.0.20', check=False
            )
            self.assertNotEqual(denied.returncode, 0)
            accepted = json.loads(run_target_script(
                target, 'invocation_manager.py', 'begin', '--identity', '2', '--version-override', '0.0.0.20', '--allow-override'
            ).stdout)
            self.assertEqual(accepted['artifact_version'], '0.0.0.20')
            self.assertTrue(accepted['version_override'])
            reuse = run_target_script(
                target, 'invocation_manager.py', 'begin', '--identity', '2', '--version-override', '0.0.0.20', '--allow-override', check=False
            )
            self.assertNotEqual(reuse.returncode, 0)
            next_record = json.loads(run_target_script(
                target, 'invocation_manager.py', 'begin', '--identity', '2'
            ).stdout)
            self.assertEqual(next_record['artifact_version'], '0.0.0.21')


    def test_stale_started_run_can_be_recovered_without_reusing_serial(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = create_target(Path(tmp))
            first = json.loads(run_target_script(
                target, 'invocation_manager.py', 'begin', '--identity', '1', '--task', 'crash simulation'
            ).stdout)
            recovered = json.loads(run_target_script(
                target, 'invocation_manager.py', 'recover', '--older-than-seconds', '0'
            ).stdout)
            self.assertEqual(recovered['recovered'], ['0.0.0.1'])
            record = json.loads((target / 'runtime/runs/0.0.0.1/run.json').read_text())
            self.assertEqual(record['status'], 'failed')
            self.assertEqual(record['error'], 'interrupted-before-terminal-record')
            second = json.loads(run_target_script(
                target, 'invocation_manager.py', 'begin', '--identity', '1', '--task', 'next'
            ).stdout)
            self.assertEqual(second['artifact_version'], '0.0.0.2')

    def test_state_behind_committed_history_is_reconciled_on_next_begin(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = create_target(Path(tmp))
            json.loads(run_target_script(target, 'invocation_manager.py', 'begin', '--identity', '3').stdout)
            state_path = target / 'runtime/state.json'
            state = json.loads(state_path.read_text())
            state['last_serial'] = 0
            state['last_artifact_version'] = None
            state_path.write_text(json.dumps(state), encoding='utf-8')
            next_record = json.loads(run_target_script(target, 'invocation_manager.py', 'begin', '--identity', '3').stdout)
            self.assertEqual(next_record['artifact_version'], '0.0.0.2')
            self.assertTrue(json.loads(run_target_script(target, 'invocation_manager.py', 'verify').stdout)['valid'])

    def test_store_task_is_explicit_opt_in(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = create_target(Path(tmp))
            record = json.loads(run_target_script(
                target, 'invocation_manager.py', 'begin', '--identity', '6', '--task', 'sensitive body', '--store-task'
            ).stdout)
            self.assertEqual(record['task_content'], 'sensitive body')
            self.assertEqual(record['privacy_mode'], 'content')


if __name__ == '__main__':
    unittest.main()
