from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
    CRYPTO_AVAILABLE = True
except Exception:  # optional formal-review verification dependency
    Ed25519PrivateKey = None
    Encoding = None
    PublicFormat = None
    CRYPTO_AVAILABLE = False

from wbi_core.io import canonical_json, sha256_file, write_json
from wbi_core.review_adapter import inspect_review_adapter, validate_attestation, validate_review_adapter_contract


@unittest.skipUnless(CRYPTO_AVAILABLE, "cryptography is optional; formal Ed25519 protocol tests require it")
class ReviewAdapterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.workspace = self.root / "workspace"; self.workspace.mkdir()
        self.target = self.root / "target"; self.target.mkdir()
        self.optimizer = self.root / "optimizer"; self.optimizer.mkdir()
        self.external = self.root / "external"; self.external.mkdir()
        self.adapter = self.external / "attestor"; self.adapter.write_text("#!/bin/sh\n", encoding="utf-8")
        self.receipts = self.external / "receipts"; self.receipts.mkdir()
        self.private_key = Ed25519PrivateKey.generate()
        self.public_key_path = self.external / "trust-anchor.pem"
        self.public_key_path.write_bytes(
            self.private_key.public_key().public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)
        )
        self.packet = self.external / "packet-index.json"
        write_json(self.packet, {"packets": []})
        self.packet_hash = sha256_file(self.packet)

    def tearDown(self):
        self.tmp.cleanup()

    def contract(self):
        return {
            "schema_version": "1.0", "status": "FROZEN", "provider": "provider", "adapter_version": "1",
            "deployment_identity": "dep-1", "adapter_path": str(self.adapter), "adapter_sha256": sha256_file(self.adapter),
            "receipt_root": str(self.receipts),
            "capabilities": ["independent-subagents", "read-only-verifier", "provider-identifiable-runs"],
            "candidate_can_write_receipts": False, "candidate_can_access_signing_key": False,
            "shell_execution": False, "attestation_mode": "FORMAL_EXTERNAL", "formal_attestation": True,
            "trust_mode": "ED25519_SIGNED_RECEIPTS", "signature_algorithm": "ed25519",
            "trust_anchor_path": str(self.public_key_path), "trust_anchor_sha256": sha256_file(self.public_key_path),
            "trust_anchor_provisioning": "PRE_EXISTING_EXTERNAL", "isolation_mode": "REMOTE_PROVIDER",
        }

    def _signed_receipt(self, name, value):
        receipt = self.receipts / (name + ".json")
        receipt.write_bytes(canonical_json(value))
        signature = self.receipts / (name + ".sig")
        signature.write_bytes(self.private_key.sign(receipt.read_bytes()))
        return receipt, signature

    def attestation(self):
        seats = []
        for review_round in (1, 2):
            for seat_number in range(1, 7):
                index = (review_round - 1) * 6 + seat_number
                receipt_value = {
                    "schema_version": "1.0", "receipt_kind": "review-seat", "provider": "provider",
                    "packet_index_sha256": self.packet_hash, "actor_id": "a%d" % index,
                    "context_id": "c%d" % index, "provider_run_id": "r%d" % index,
                    "provider_request_id": "request-%d" % index, "verdict": "PASS",
                    "review_round": review_round, "seat_number": seat_number,
                    "runtime": "external-runtime", "model": "model-family-%d" % (1 + index % 2),
                    "started_at": "2026-07-26T00:00:00Z", "finished_at": "2026-07-26T00:00:01Z",
                }
                receipt, signature = self._signed_receipt("seat-%d" % index, receipt_value)
                seats.append({
                    "review_round": review_round, "seat_number": seat_number,
                    "actor_id": "a%d" % index, "context_id": "c%d" % index,
                    "provider_run_id": "r%d" % index, "verdict": "PASS",
                    "provider_receipt_path": str(receipt), "provider_receipt_sha256": sha256_file(receipt),
                    "provider_receipt_signature_path": str(signature),
                    "provider_receipt_signature_sha256": sha256_file(signature),
                })
        verifier_value = {
            "schema_version": "1.0", "receipt_kind": "final-verifier", "provider": "provider",
            "packet_index_sha256": self.packet_hash, "actor_id": "verifier", "context_id": "vc",
            "provider_run_id": "vr", "provider_request_id": "request-verifier", "verdict": "PASS",
            "read_only": True, "runtime": "external-runtime", "model": "independent-verifier-model",
            "started_at": "2026-07-26T00:00:02Z", "finished_at": "2026-07-26T00:00:03Z",
        }
        verifier_receipt, verifier_signature = self._signed_receipt("verifier", verifier_value)
        payload = {
            "schema_version": "1.0", "attestation_mode": "FORMAL_EXTERNAL",
            "adapter_sha256": sha256_file(self.adapter), "trust_anchor_sha256": sha256_file(self.public_key_path),
            "provider": "provider", "deployment_identity": "dep-1",
            "packet_index_sha256": self.packet_hash, "review_seats": seats,
            "final_verifier": {
                "actor_id": "verifier", "context_id": "vc", "provider_run_id": "vr",
                "read_only": True, "verdict": "PASS",
                "provider_receipt_path": str(verifier_receipt),
                "provider_receipt_sha256": sha256_file(verifier_receipt),
                "provider_receipt_signature_path": str(verifier_signature),
                "provider_receipt_signature_sha256": sha256_file(verifier_signature),
            },
            "candidate_authored": False,
            "residual_trust": ["External provider identity and organisational separation remain trust assumptions"],
        }
        attestation_signature = self.receipts / "attestation.sig"
        attestation_signature.write_bytes(self.private_key.sign(canonical_json(payload)))
        payload["attestation_signature_path"] = str(attestation_signature)
        payload["attestation_signature_sha256"] = sha256_file(attestation_signature)
        return payload

    def test_valid_external_contract(self):
        self.assertEqual(
            validate_review_adapter_contract(
                self.contract(), workspace=self.workspace, target=self.target, optimizer_root=self.optimizer
            ), []
        )

    def test_valid_signed_2x6_plus_one_attestation(self):
        self.assertEqual(validate_attestation(self.attestation(), self.contract(), packet_index_sha256=self.packet_hash), [])

    def test_bundled_adapter_rejected_as_formal_root(self):
        errors = validate_review_adapter_contract(
            self.contract(), workspace=self.workspace, target=self.target, optimizer_root=self.optimizer,
            bundled_root=self.external,
        )
        self.assertTrue(any("bundled" in item for item in errors))

    def test_candidate_writable_receipts_rejected(self):
        value = self.contract(); value["candidate_can_write_receipts"] = True
        self.assertTrue(any(
            "candidate_can_write" in item for item in validate_review_adapter_contract(
                value, workspace=self.workspace, target=self.target, optimizer_root=self.optimizer
            )
        ))

    def test_candidate_access_to_signing_key_rejected(self):
        value = self.contract(); value["candidate_can_access_signing_key"] = True
        self.assertTrue(any(
            "candidate_can_access_signing_key" in item for item in validate_review_adapter_contract(
                value, workspace=self.workspace, target=self.target, optimizer_root=self.optimizer
            )
        ))

    def test_diagnostic_fixture_never_becomes_formal(self):
        contract = self.contract()
        contract.update({
            "attestation_mode": "DIAGNOSTIC_FIXTURE", "formal_attestation": False,
            "trust_mode": "DIAGNOSTIC_FIXTURE", "signature_algorithm": None,
        })
        contract.pop("trust_anchor_path"); contract.pop("trust_anchor_sha256")
        contract.pop("trust_anchor_provisioning"); contract.pop("isolation_mode")
        cpath = self.external / "diagnostic-contract.json"; write_json(cpath, contract)
        result = inspect_review_adapter(
            cpath, workspace=self.workspace, target=self.target, optimizer_root=self.optimizer
        )
        self.assertEqual(result["adapter_contract_status"], "PASS")
        self.assertEqual(result["formal_review_capability"], "DIAGNOSTIC_ONLY")
        self.assertTrue(any("diagnostic fixture" in item for item in validate_attestation(
            self.attestation(), contract, packet_index_sha256=self.packet_hash
        )))

    def test_self_signed_candidate_attestation_rejected(self):
        value = self.attestation(); value["candidate_authored"] = True
        self.assertTrue(any(
            "candidate-authored" in item for item in validate_attestation(
                value, self.contract(), packet_index_sha256=self.packet_hash
            )
        ))

    def test_reused_reviewer_provider_run_rejected(self):
        value = self.attestation(); value["review_seats"][1]["provider_run_id"] = value["review_seats"][0]["provider_run_id"]
        self.assertTrue(any(
            "provider_run_id reused" in item for item in validate_attestation(
                value, self.contract(), packet_index_sha256=self.packet_hash
            )
        ))

    def test_two_rounds_of_six_are_mandatory(self):
        value = self.attestation(); value["review_seats"][0]["review_round"] = 2
        self.assertTrue(any(
            "two rounds of six" in item or "duplicate 2x6" in item for item in validate_attestation(
                value, self.contract(), packet_index_sha256=self.packet_hash
            )
        ))

    def test_verifier_identity_must_be_distinct(self):
        value = self.attestation(); value["final_verifier"]["context_id"] = value["review_seats"][0]["context_id"]
        self.assertTrue(any(
            "reuses a reviewer" in item for item in validate_attestation(
                value, self.contract(), packet_index_sha256=self.packet_hash
            )
        ))

    def test_packet_hash_drift_rejected(self):
        self.assertTrue(any(
            "packet index hash" in item for item in validate_attestation(
                self.attestation(), self.contract(), packet_index_sha256="0" * 64
            )
        ))

    def test_arbitrary_unsigned_receipt_rejected(self):
        value = self.attestation()
        signature_path = Path(value["review_seats"][0]["provider_receipt_signature_path"])
        signature_path.write_bytes(b"not-a-valid-signature")
        value["review_seats"][0]["provider_receipt_signature_sha256"] = sha256_file(signature_path)
        self.assertTrue(any(
            "signature verification failed" in item for item in validate_attestation(
                value, self.contract(), packet_index_sha256=self.packet_hash
            )
        ))

    def test_attestation_signature_is_mandatory(self):
        value = self.attestation(); value.pop("attestation_signature_path"); value.pop("attestation_signature_sha256")
        self.assertTrue(any(
            "attestation signature path" in item for item in validate_attestation(
                value, self.contract(), packet_index_sha256=self.packet_hash
            )
        ))

    def test_provider_receipt_content_must_bind_seat(self):
        value = self.attestation()
        value["review_seats"][0]["actor_id"] = "tampered-actor"
        self.assertTrue(any(
            "actor_id binding mismatch" in item for item in validate_attestation(
                value, self.contract(), packet_index_sha256=self.packet_hash
            )
        ))


if __name__ == "__main__":
    unittest.main()
