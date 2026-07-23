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
    def test_concurrent_allocations_are_unique_and_contiguous(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = create_target(Path(tmp))
            script = target / 'scripts' / 'invocation_manager.py'

            def allocate(index: int) -> int:
                completed = subprocess.run(
                    [sys.executable, str(script), 'begin', '--identity', '1', '--task', f'job-{index}', '--lock-timeout', '30'],
                    cwd=target, text=True, capture_output=True, timeout=60,
                )
                if completed.returncode != 0:
                    raise AssertionError(completed.stderr)
                return json.loads(completed.stdout)['serial']

            with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
                serials = list(pool.map(allocate, range(1, 31)))
            self.assertEqual(sorted(serials), list(range(1, 31)))
            verify = json.loads(run_target_script(target, 'invocation_manager.py', 'verify').stdout)
            self.assertTrue(verify['valid'], verify)
            self.assertEqual(verify['last_serial'], 30)
            self.assertEqual(verify['run_count'], 30)


if __name__ == '__main__':
    unittest.main()
