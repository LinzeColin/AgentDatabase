from __future__ import annotations

import concurrent.futures
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import create_target, run_target_script


class RuntimeConcurrencyTests(unittest.TestCase):
    def test_concurrent_audit_records_remain_complete_and_unnumbered(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = create_target(Path(tmp))
            script = target / 'scripts' / 'runtime_recorder.py'

            def record(index: int) -> dict[str, object]:
                completed = subprocess.run(
                    [
                        sys.executable,
                        str(script),
                        'record',
                        '--status',
                        'completed',
                        '--task',
                        f'job-{index}',
                        '--lock-timeout',
                        '30',
                    ],
                    cwd=target,
                    text=True,
                    capture_output=True,
                    timeout=60,
                )
                if completed.returncode != 0:
                    raise AssertionError(completed.stderr)
                return json.loads(completed.stdout)

            with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
                records = list(pool.map(record, range(1, 31)))
            self.assertEqual(len(records), 30)
            self.assertTrue(all(not {'run_id', 'artifact_version', 'serial'} & set(item) for item in records))
            verify = json.loads(run_target_script(target, 'runtime_recorder.py', 'verify').stdout)
            self.assertTrue(verify['valid'], verify)
            self.assertEqual(verify['record_count'], 30)
            self.assertEqual(verify['numbered_records'], 0)


if __name__ == '__main__':
    unittest.main()
