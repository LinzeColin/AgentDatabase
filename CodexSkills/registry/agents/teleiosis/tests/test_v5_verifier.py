from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from helpers import ROOT
from teleiosis_core.common import TeleiosisError
from teleiosis_core.verifier_handoff import build_handoff, subject_identity, validate_handoff


class V5VerifierTests(unittest.TestCase):
    def test_verifier_handoff_v5(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "acceptance-review.zip"
            built = build_handoff(path, ROOT)
            self.assertEqual(built["status"], "READY_FOR_EXTERNAL_VERIFIER")
            self.assertEqual(built["formal_pass"], "NOT_ISSUED")
            checked = validate_handoff(path)
            self.assertEqual(checked["status"], "PASS")
            self.assertEqual(checked["subject_hash"], built["subject_hash"])

    def test_subject_identity_is_bound_to_candidate(self) -> None:
        identity = subject_identity(ROOT)
        self.assertEqual(identity["name"], "teleiosis")
        self.assertEqual(identity["version"], "v0.0.0.5")
        self.assertEqual(identity["formal_pass"], "NOT_ISSUED")
        for field in ("candidate_tree_digest", "acceptance_sha256", "manifest_sha256", "subject_hash"):
            self.assertEqual(len(identity[field]), 64)

    def test_handoff_inside_package_is_refused(self) -> None:
        with self.assertRaises(TeleiosisError) as ctx:
            build_handoff(ROOT / "forbidden-handoff.zip", ROOT)
        self.assertEqual(ctx.exception.code, "HANDOFF_INSIDE_PACKAGE")
        self.assertFalse((ROOT / "forbidden-handoff.zip").exists())

    def test_handoff_tampered_formal_pass_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            original = base / "original.zip"
            tampered = base / "tampered.zip"
            build_handoff(original, ROOT)
            with zipfile.ZipFile(original, "r") as src, zipfile.ZipFile(tampered, "w", compression=zipfile.ZIP_DEFLATED) as dst:
                for info in src.infolist():
                    data = src.read(info.filename)
                    if info.filename == "SUBJECT_IDENTITY.json":
                        payload = json.loads(data.decode("utf-8"))
                        payload["formal_pass"] = "PASS"
                        data = json.dumps(payload).encode("utf-8")
                    dst.writestr(info.filename, data)
            with self.assertRaises(TeleiosisError) as ctx:
                validate_handoff(tampered)
            self.assertEqual(ctx.exception.code, "HANDOFF_FORMAL_PASS")


if __name__ == "__main__":
    unittest.main()
