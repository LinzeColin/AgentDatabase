from __future__ import annotations
"""A green scan only means something if the scanner catches planted leaks."""
import json, tempfile, unittest
from pathlib import Path
from privacy_and_dependency_scan import scan_imports, scan_payload

ROOT = Path(__file__).resolve().parents[2]  # OpenAIDatabase/


class PrivacyScanTests(unittest.TestCase):
    def setUp(self) -> None:
        self.clean = json.loads((ROOT / "fixtures/live_snapshot.synthetic.json").read_text())

    def test_clean_snapshot_has_no_findings(self) -> None:
        self.assertEqual(scan_payload(self.clean, "clean"), [])

    def test_object_key_is_caught(self) -> None:
        leaked = json.loads(json.dumps(self.clean))
        leaked["coverage"]["sources"][0]["object_key"] = "private-agentdatabase/sha256/ab/abc"
        kinds = {row["kind"] for row in scan_payload(leaked, "leaked")}
        self.assertIn("forbidden_key", kinds)
        self.assertIn("r2_object_prefix", kinds)

    def test_private_path_in_a_value_is_caught(self) -> None:
        leaked = json.loads(json.dumps(self.clean))
        leaked["freshness"]["reason_zh"] = "读取 /srv/linze/secrets/memory-atlas.env 失败"
        self.assertEqual([row["kind"] for row in scan_payload(leaked, "leaked")], ["absolute_private_path"])

    def test_a_digest_outside_release_identity_is_still_caught(self) -> None:
        leaked = json.loads(json.dumps(self.clean))
        leaked["run"]["reconciled_at"] = "f" * 64
        self.assertEqual([row["kind"] for row in scan_payload(leaked, "leaked")], ["bare_sha256"])

    def test_bearer_token_is_caught(self) -> None:
        leaked = json.loads(json.dumps(self.clean))
        leaked["truth"]["limitations"] = ["Bearer ghp_" + "a" * 30]
        kinds = {row["kind"] for row in scan_payload(leaked, "leaked")}
        self.assertTrue({"bearer_or_key"} <= kinds)


class DependencyScanTests(unittest.TestCase):
    def test_serving_modules_import_no_model_runtime(self) -> None:
        self.assertEqual(scan_imports(["OpenAIDatabase/scripts/memory_atlas_private/live_snapshot_adapter.py"]), [])

    def test_a_planted_model_import_is_caught(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT.parent) as raw:
            planted = Path(raw) / "planted.py"
            planted.write_text("import openai\nclient = openai.OpenAI()\n", encoding="utf-8")
            findings = scan_imports([str(planted.relative_to(ROOT.parent))])
        self.assertEqual([row["kind"] for row in findings], ["model_import"])

    def test_a_planted_model_call_is_caught(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT.parent) as raw:
            planted = Path(raw) / "planted.py"
            planted.write_text("def go(c):\n    return c.embeddings.create(input='x')\n", encoding="utf-8")
            findings = scan_imports([str(planted.relative_to(ROOT.parent))])
        self.assertEqual([row["kind"] for row in findings], ["model_call"])


if __name__ == "__main__":
    unittest.main()
