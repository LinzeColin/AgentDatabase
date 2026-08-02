from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from helpers import ROOT
from teleiosis_core.doctor import doctor
from teleiosis_core.installer import install
from teleiosis_core.integrity import verify_release
from teleiosis_core.packaging import build_deterministic_zip, safe_extract


class V5FullTests(unittest.TestCase):
    def test_full_release_v5(self) -> None:
        result = verify_release(ROOT, strict=True)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["version"], "v0.0.0.5")
        self.assertEqual(result["checks"]["preparation"]["regression"]["records"], 8192)

    def test_doctor_is_complete(self) -> None:
        result = doctor(ROOT)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["checks"]["release"]["status"], "PASS")
        self.assertEqual(result["checks"]["fresh_builder"]["status"], "ACCEPTANCE_PASS")

    def test_raw_validation_evidence(self) -> None:
        index = json.loads((ROOT / "evidence/validation/RAW_EVIDENCE_INDEX.json").read_text(encoding="utf-8"))
        self.assertEqual(index["schema_version"], "teleiosis.raw_evidence_index.v5")
        self.assertIn(index["status"], {"PREPARED_FOR_EXECUTION", "PASS"})
        self.assertIsInstance(index["entries"], list)
        raw = ROOT / "evidence/validation/raw"
        self.assertTrue(raw.is_dir())

    def test_reproducible_package_v5(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            a = Path(tmp) / "a.zip"
            b = Path(tmp) / "b.zip"
            first = build_deterministic_zip(ROOT, a)
            second = build_deterministic_zip(ROOT, b)
            self.assertEqual(hashlib.sha256(a.read_bytes()).hexdigest(), hashlib.sha256(b.read_bytes()).hexdigest())
            self.assertEqual(first["files"], second["files"])
            self.assertGreater(first["zip_bytes"], 1_000_000)

    def test_cold_extract_and_dry_run_install(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            archive = base / "teleiosis.zip"
            build_deterministic_zip(ROOT, archive)
            extracted = safe_extract(archive, base / "extract")
            verified = verify_release(extracted, strict=True)
            self.assertEqual(verified["status"], "PASS")
            plan = install(skills_root=base / "skills", source=extracted, dry_run=True)
            self.assertEqual(plan["status"], "DRY_RUN_READY")
            self.assertFalse((base / "skills/teleiosis").exists())

    def test_final_zip_v5_contract(self) -> None:
        release = json.loads((ROOT / "metadata/release.json").read_text(encoding="utf-8"))
        summary = json.loads((ROOT / "evidence/validation/final-validation-summary.json").read_text(encoding="utf-8"))
        self.assertEqual(release["version"], "v0.0.0.5")
        self.assertIn(summary["status"], {"LOCAL_ENGINEERING_PASS", "PASS"})
        self.assertEqual(summary["formal_pass_authority"], "external independent verifier")


if __name__ == "__main__":
    unittest.main()
