from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from wbi_core.smoke import run_release_smoke  # noqa: E402

GENESIS = "14ab08b9053db4ca87140e59a49f1de8105a718a87ec2d55590c6487c1a77086"


class ReleaseSmokeTests(unittest.TestCase):
    def test_release_smoke_is_non_recursive_and_covers_install_primitives(self):
        result = run_release_smoke(ROOT, GENESIS)
        self.assertEqual(result["status"], "PASS", result)
        self.assertFalse(result["recursive_full_suite"])
        self.assertEqual(result["profile"], "optimizer")
        self.assertEqual(result["checks"]["strict_validation"], "PASS")
        self.assertEqual(result["checks"]["python_ast"], "PASS")
        self.assertEqual(result["checks"]["json_documents"], "PASS")
        self.assertEqual(result["checks"]["cli_surface"], "PASS")
        self.assertEqual(result["checks"]["generic_package_install_rollback"], "PASS")


if __name__ == "__main__":
    unittest.main()
