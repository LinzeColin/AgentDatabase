from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from helpers import ROOT
from teleiosis_core.integrity import verify_v3_lineage


class V5LineageTests(unittest.TestCase):
    def test_v3_lineage(self) -> None:
        result = verify_v3_lineage(ROOT)
        self.assertEqual(result["status"], "FUNCTIONAL_SUPERSET_WITH_SOURCE_BOUNDARY")
        self.assertEqual(result["manifest_entries"], 444)

    def test_v3_snapshot_hashes_are_exact(self) -> None:
        expected = {
            "SKILL.md": "6585cbcfdf9c516d72d558d18151d66702fe4678fec89fcdda0e44d6ad9158fd",
            "README.md": "45446884ad930437c1bd9eaa22410fca71c2e233549a47c8004ed716fe3b1e36",
            "MANIFEST.sha256": "a503f9288d51fc695f28fe185a728b537ba39519c1f5fb55a099c62979d71b52",
        }
        base = ROOT / "legacy/v0.0.0.3"
        for name, digest in expected.items():
            self.assertEqual(hashlib.sha256((base / name).read_bytes()).hexdigest(), digest)

    def test_v3_manifest_has_unique_paths(self) -> None:
        lines = [line for line in (ROOT / "legacy/v0.0.0.3/MANIFEST.sha256").read_text(encoding="utf-8").splitlines() if line.strip()]
        paths = [line.split("  ", 1)[1] for line in lines]
        self.assertEqual(len(lines), 444)
        self.assertEqual(len(paths), len(set(paths)))

    def test_lineage_claim_is_honest(self) -> None:
        data = json.loads((ROOT / "legacy/v0.0.0.3/SEMANTIC_INHERITANCE.json").read_text(encoding="utf-8"))
        self.assertFalse(data["byte_exact_full_v3_copy"])
        self.assertIn("没有冒充取得", data["source_boundary"])
        self.assertIn("FULL_NO_ROUTING", data["preserved_semantics"])


if __name__ == "__main__":
    unittest.main()
