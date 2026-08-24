#!/usr/bin/env python3
"""Contract tests for fail-closed external adapter normalization."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
PAYLOAD = Path(__file__).resolve().parent.parent


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


normalizer = load_module("verifier_adapter_normalizer", PAYLOAD / "scripts/normalize_adapter_result.py")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def valid_payload(adapter_type: str = "test_execution") -> dict:
    data = b'{"ok":true}\n'
    return {
        "schema_version": "1.0",
        "adapter_type": adapter_type,
        "adapter": {"name": "runner", "version": "1.0.0", "source": "project-native"},
        "subject_identity": "sha256:" + "a" * 64,
        "execution": {"argv": ["runner", "--json"], "cwd": ".", "exit_code": 0, "timed_out": False},
        "status_mapping": {
            "source_status": "passed",
            "normalized_status": "PASS",
            "mapping_rule": "source passed, complete result, exit 0",
        },
        "raw_evidence": [{"path": "raw/result.json", "sha256": digest(data), "size": len(data), "media_type": "application/json"}],
        "claims": [{"claim_id": "T-1", "status": "PASS", "oracle": "observable condition", "evidence_refs": ["raw/result.json"]}],
        "limitations": [],
    }


class AdapterContractTests(unittest.TestCase):
    def test_all_six_adapter_types_normalize(self):
        for adapter_type in sorted(normalizer.ADAPTER_TYPES):
            with self.subTest(adapter_type=adapter_type):
                result = normalizer.normalize(valid_payload(adapter_type))
                self.assertEqual(result["adapter_type"], adapter_type)
                self.assertFalse(result["verdict_eligible"])
                self.assertEqual(result["decision_authority"], "none")

    def test_real_evidence_hash_is_verified(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            evidence = root / "raw/result.json"
            evidence.parent.mkdir()
            evidence.write_bytes(b'{"ok":true}\n')
            result = normalizer.normalize(valid_payload(), root)
            self.assertEqual(result["normalized_status"], "PASS")

    def test_hash_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            evidence = root / "raw/result.json"
            evidence.parent.mkdir()
            evidence.write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError, "mismatch"):
                normalizer.normalize(valid_payload(), root)

    def test_direct_verdict_is_rejected(self):
        payload = valid_payload()
        payload["verdict"] = "PASS"
        with self.assertRaisesRegex(ValueError, "authority"):
            normalizer.normalize(payload)

    def test_nested_release_approval_is_rejected(self):
        payload = valid_payload()
        payload["metadata"] = {"release_decision": "ship"}
        with self.assertRaisesRegex(ValueError, "authority"):
            normalizer.normalize(payload)

    def test_warning_cannot_map_to_pass(self):
        payload = valid_payload()
        payload["status_mapping"]["source_status"] = "warning"
        with self.assertRaisesRegex(ValueError, "cannot map to PASS"):
            normalizer.normalize(payload)

    def test_skipped_cannot_map_to_pass(self):
        payload = valid_payload()
        payload["status_mapping"]["source_status"] = "skipped"
        with self.assertRaisesRegex(ValueError, "cannot map to PASS"):
            normalizer.normalize(payload)

    def test_timeout_cannot_map_to_pass(self):
        payload = valid_payload()
        payload["execution"]["timed_out"] = True
        with self.assertRaisesRegex(ValueError, "timed-out"):
            normalizer.normalize(payload)

    def test_pass_requires_raw_evidence(self):
        payload = valid_payload()
        payload["raw_evidence"] = []
        payload["claims"][0]["evidence_refs"] = []
        with self.assertRaisesRegex(ValueError, "PASS requires"):
            normalizer.normalize(payload)

    def test_pass_claim_requires_evidence_reference(self):
        payload = valid_payload()
        payload["claims"][0]["evidence_refs"] = []
        with self.assertRaisesRegex(ValueError, "PASS requires evidence_refs"):
            normalizer.normalize(payload)

    def test_unknown_evidence_reference_is_rejected(self):
        payload = valid_payload()
        payload["claims"][0]["evidence_refs"] = ["raw/missing.json"]
        with self.assertRaisesRegex(ValueError, "unknown evidence"):
            normalizer.normalize(payload)

    def test_top_level_pass_cannot_hide_failure(self):
        payload = valid_payload()
        payload["claims"][0]["status"] = "FAIL"
        with self.assertRaisesRegex(ValueError, "cannot hide"):
            normalizer.normalize(payload)

    def test_non_pass_result_can_be_normalized_without_evidence(self):
        payload = valid_payload()
        payload["status_mapping"] = {"source_status": "failed", "normalized_status": "FAIL", "mapping_rule": "tool failure"}
        payload["raw_evidence"] = []
        payload["claims"] = [{"claim_id": "T-1", "status": "FAIL", "oracle": "observable condition", "evidence_refs": []}]
        result = normalizer.normalize(payload)
        self.assertEqual(result["normalized_status"], "FAIL")

    def test_duplicate_claim_id_is_rejected(self):
        payload = valid_payload()
        payload["claims"].append(dict(payload["claims"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate claim_id"):
            normalizer.normalize(payload)

    def test_path_traversal_is_rejected(self):
        payload = valid_payload()
        payload["raw_evidence"][0]["path"] = "../result.json"
        with self.assertRaisesRegex(ValueError, "unsafe"):
            normalizer.normalize(payload)

    def test_case_colliding_evidence_paths_are_rejected(self):
        payload = valid_payload()
        second = dict(payload["raw_evidence"][0])
        second["path"] = "RAW/RESULT.JSON"
        payload["raw_evidence"].append(second)
        with self.assertRaisesRegex(ValueError, "case-colliding"):
            normalizer.normalize(payload)

    def test_duplicate_json_keys_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "bad.json"
            path.write_text('{"schema_version":"1.0","schema_version":"2.0"}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
                normalizer.load_json_no_duplicates(path)

    def test_invalid_adapter_type_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unsupported adapter_type"):
            normalizer.normalize(valid_payload("magic_verdict"))

    def test_subject_identity_cannot_be_empty(self):
        payload = valid_payload()
        payload["subject_identity"] = ""
        with self.assertRaisesRegex(ValueError, "subject_identity"):
            normalizer.normalize(payload)

    def test_argv_must_be_an_array(self):
        payload = valid_payload()
        payload["execution"]["argv"] = "runner --json"
        with self.assertRaisesRegex(ValueError, "argv"):
            normalizer.normalize(payload)

    def test_template_contract_lists_same_adapter_types(self):
        contract = json.loads((PAYLOAD / "templates/ADAPTER_CONTRACT.json").read_text(encoding="utf-8"))
        self.assertEqual(set(contract["allowed_adapter_types"]), normalizer.ADAPTER_TYPES)
        self.assertEqual(contract["decision_authority"], "none")


    def test_partial_cannot_map_to_pass(self):
        payload = valid_payload()
        payload["status_mapping"]["source_status"] = "partial"
        with self.assertRaisesRegex(ValueError, "cannot map to PASS"):
            normalizer.normalize(payload)

    def test_mapping_rule_is_required(self):
        payload = valid_payload()
        payload["status_mapping"]["mapping_rule"] = ""
        with self.assertRaisesRegex(ValueError, "mapping_rule"):
            normalizer.normalize(payload)

    def test_uppercase_digest_is_rejected(self):
        payload = valid_payload()
        payload["raw_evidence"][0]["sha256"] = payload["raw_evidence"][0]["sha256"].upper()
        with self.assertRaisesRegex(ValueError, "lowercase SHA-256"):
            normalizer.normalize(payload)

    @unittest.skipIf(not hasattr(Path, "symlink_to"), "symlink unavailable")
    def test_evidence_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            real = root / "real.json"
            real.write_bytes(b'{"ok":true}\n')
            link = root / "raw/result.json"
            link.parent.mkdir()
            link.symlink_to(real)
            with self.assertRaisesRegex(ValueError, "symlink"):
                normalizer.normalize(valid_payload(), root)

    def test_too_short_subject_identity_is_rejected(self):
        payload = valid_payload()
        payload["subject_identity"] = "abc"
        with self.assertRaisesRegex(ValueError, "too weak"):
            normalizer.normalize(payload)


if __name__ == "__main__":
    unittest.main(verbosity=2)
