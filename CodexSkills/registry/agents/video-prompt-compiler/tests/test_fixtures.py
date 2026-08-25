from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import route_request


class FixtureRoutingTests(unittest.TestCase):
    def test_all_fixtures(self):
        for line in (ROOT / "tests" / "fixtures.jsonl").read_text(encoding="utf-8").splitlines():
            case = json.loads(line)
            with self.subTest(idea=case["idea"]):
                result = route_request.route_request(case["idea"])
                self.assertEqual(result.route, case["expected_route"])
                self.assertEqual(result.primary_preset, case["expected_preset"])


if __name__ == "__main__":
    unittest.main()
