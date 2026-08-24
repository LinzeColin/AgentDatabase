from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import install


class InstallTests(unittest.TestCase):
    def test_custom_install_preserves_runtime_research_and_handoff(self):
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / "video-prompt-compiler"
            install.install(destination, force=False, dry_run=False)
            required = (
                "SKILL.md",
                ".ramify/HANDOFF.md",
                "research/comparison_matrix.csv",
                "taskpack/CODEX_EXECUTION.md",
                "scripts/route_request.py",
            )
            for relative in required:
                self.assertTrue((destination / relative).is_file(), relative)


if __name__ == "__main__":
    unittest.main()
