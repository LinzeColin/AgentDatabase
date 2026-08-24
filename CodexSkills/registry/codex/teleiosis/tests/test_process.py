from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from wbi_core.process import run_bounded, run_bounded_to_file  # noqa: E402


class ProcessTests(unittest.TestCase):
    def test_timeout_is_structured_and_kills_process_group(self):
        with tempfile.TemporaryDirectory() as td:
            marker = Path(td) / "child-survived.txt"
            child = "import time; from pathlib import Path; time.sleep(0.6); Path(%r).write_text('bad')" % str(marker)
            parent = (
                "import subprocess,sys,time; "
                "subprocess.Popen([sys.executable,'-c',%r]); time.sleep(10)" % child
            )
            result = run_bounded([sys.executable, "-c", parent], timeout_seconds=0.2)
            self.assertTrue(result["timed_out"])
            self.assertNotEqual(result["returncode"], 0)
            self.assertGreaterEqual(result["elapsed_seconds"], 0.1)
            self.assertLess(result["elapsed_seconds"], 3.0)
            time.sleep(0.8)
            if os.name == "posix":
                self.assertFalse(marker.exists(), "grandchild survived the bounded process group")

    def test_output_and_input_are_bounded_without_losing_tail(self):
        command = [sys.executable, "-c", "import sys; sys.stdout.write('A'*2000 + 'TAIL'); sys.stderr.write('E'*2000 + 'ERRTAIL')"]
        result = run_bounded(command, timeout_seconds=2, max_output_bytes=512)
        self.assertTrue(result["stdout_truncated"])
        self.assertTrue(result["stderr_truncated"])
        self.assertGreater(result["stdout_bytes"], 512)
        self.assertIn("TAIL", result["stdout"])
        self.assertIn("ERRTAIL", result["stderr"])
        self.assertLessEqual(len(result["stdout"].encode("utf-8")), 512)
        with self.assertRaisesRegex(ValueError, "max_input_bytes"):
            run_bounded([sys.executable, "-c", "pass"], input_text="x" * 513, max_input_bytes=512)


    def test_binary_output_streams_to_file_and_enforces_limit(self):
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / "artifact.bin"
            result = run_bounded_to_file(
                [sys.executable, "-c", "import sys; sys.stdout.buffer.write(b'x'*4096)"],
                output, timeout_seconds=2, max_output_bytes=1024,
            )
            self.assertTrue(result["output_limit_exceeded"])
            self.assertFalse(output.exists())
            self.assertEqual(result["output_bytes"], 4096)
            self.assertGreaterEqual(result["elapsed_seconds"], 0.0)

            result = run_bounded_to_file(
                [sys.executable, "-c", "import sys; sys.stdout.buffer.write(b'ok')"],
                output, timeout_seconds=2, max_output_bytes=1024,
            )
            self.assertEqual(result["returncode"], 0)
            self.assertFalse(result["output_limit_exceeded"])
            self.assertEqual(output.read_bytes(), b"ok")

    def test_binary_output_timeout_is_structured(self):
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / "artifact.bin"
            result = run_bounded_to_file(
                [sys.executable, "-c", "import time; time.sleep(5)"],
                output, timeout_seconds=0.1, max_output_bytes=1024,
            )
            self.assertTrue(result["timed_out"])
            self.assertNotEqual(result["returncode"], 0)

    def test_invalid_timeout_and_empty_command_are_rejected(self):
        with self.assertRaises(ValueError):
            run_bounded([], timeout_seconds=1)
        with self.assertRaises(ValueError):
            run_bounded([sys.executable, "-c", "pass"], timeout_seconds=0)
        with self.assertRaises(ValueError):
            run_bounded([sys.executable, "-c", "pass"], timeout_seconds=True)


if __name__ == "__main__":
    unittest.main()
