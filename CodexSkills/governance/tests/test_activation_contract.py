#!/usr/bin/env python3
"""M0c-A activation intent/settlement positive and negative contract gates."""

from __future__ import annotations

import copy
import hashlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path
from typing import Any, Dict, Mapping


GOVERNANCE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = GOVERNANCE_DIR.parents[1]
TOOLS_DIR = GOVERNANCE_DIR / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from build_activation_control import (  # noqa: E402
    CANDIDATE_BUNDLE_DIGEST,
    CANDIDATE_BUNDLE_GIT_OBJECT_ID,
    CONTROL_INTERFACE_PATH,
    CONTROL_INTERFACE_REPO_PATH,
    INTENT_ID,
    INTENT_SCHEMA_PATH,
    NOTIFICATION_AFFECTED_PATH_REFS,
    SETTLEMENT_ID,
    SETTLEMENT_SCHEMA_PATH,
    TARGET_SRV_REVISION,
)
from canonical_json import canonical_digest, canonicalize_object  # noqa: E402
from validate_activation import (  # noqa: E402
    HANDOFF_PATH,
    NOTIFICATION_RECEIPT_ID,
    VERSION_PATH,
    ActivationControlTrustTuple,
    CONTROL_MODE,
    CONTROL_SCHEMA_REPO_PATHS,
    ContractError,
    _regular_file_under,
    load_activation_bundle,
    notification_metadata,
    validate_intent,
    validate_settlement,
)
from validate_mechanism import scan_public_value, strict_load  # noqa: E402


PROTOCOL = "urn:linzecolin:agentdatabase:skillops:protocol:cross-pack:v1"
REMOTE_HEAD = "sha1:" + "a" * 40
ULID_0 = "0" * 26
ULID_1 = "0" * 25 + "1"
ULID_2 = "0" * 25 + "2"
ULID_3 = "0" * 25 + "3"
TS_0 = "2026-07-23T00:00:00.000000Z"
TS_1 = "2026-07-23T00:00:01.000000Z"
TS_2 = "2026-07-23T00:00:02.000000Z"


def uid(prefix: str, suffix: str = ULID_0) -> str:
    return f"{prefix}_{suffix}"


def sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def activation_paths(activation_uid: str) -> Mapping[str, str]:
    prefix = "CodexSkills/governance/activation-receipts/" + activation_uid
    return {
        "intent": prefix + ".intent.json",
        "notification": prefix + ".notification-receipt.json",
        "settlement": prefix + ".settlement.json",
    }


def intent_fixture() -> Dict[str, Any]:
    activation_uid = uid("act")
    paths = activation_paths(activation_uid)
    rows = [
        {
            "artifact_repo_path": VERSION_PATH,
            "artifact_role": "ACTIVE_VERSION_MARKER",
            "digest_availability": "BOUND_IN_INTENT",
            "artifact_digest": sha((TARGET_SRV_REVISION + "\n").encode("ascii")),
        },
        {
            "artifact_repo_path": HANDOFF_PATH,
            "artifact_role": "MECHANISM_HANDOFF",
            "digest_availability": "DERIVED_AFTER_PROVIDER_SENT",
        },
        {
            "artifact_repo_path": paths["intent"],
            "artifact_role": "ACTIVATION_INTENT",
            "digest_availability": "SELF_DIGESTED_INTENT",
        },
        {
            "artifact_repo_path": paths["notification"],
            "artifact_role": "NOTIFICATION_RECEIPT",
            "digest_availability": "DERIVED_AFTER_PROVIDER_SENT",
        },
        {
            "artifact_repo_path": paths["settlement"],
            "artifact_role": "ACTIVATION_SETTLEMENT",
            "digest_availability": "DERIVED_AFTER_PROVIDER_SENT",
        },
    ]
    value = {
        "schema_version": INTENT_ID,
        "protocol_revision": PROTOCOL,
        "bundle_digest": CANDIDATE_BUNDLE_DIGEST,
        "activation_uid": activation_uid,
        "envelope_uid": uid("env"),
        "notification_uid": uid("ntf"),
        "auto_transaction_uid": uid("atx"),
        "bundle_git_object_id": CANDIDATE_BUNDLE_GIT_OBJECT_ID,
        "expected_remote_head": REMOTE_HEAD,
        "candidate_manifest_path": (
            "CodexSkills/governance/bundles/schema-bundle-manifest.v1.json"
        ),
        "target_srv_revision": TARGET_SRV_REVISION,
        "impact": "MAJOR",
        "change_code": "ACTIVE_BUNDLE_CHANGE",
        "planned_action": "ACTIVATE",
        "notification_timing": "PRE_WRITE",
        "recipient_ref": "owner-primary",
        "rollback_target_ref": REMOTE_HEAD,
        "notification_affected_path_refs": list(
            NOTIFICATION_AFFECTED_PATH_REFS
        ),
        "planned_artifacts": sorted(
            rows, key=lambda row: row["artifact_repo_path"]
        ),
        "created_at": TS_0,
        "envelope_digest": "0" * 64,
    }
    value["envelope_digest"] = canonical_digest(value, "/envelope_digest")
    return value


def receipt_fixture(intent: Mapping[str, Any]) -> Dict[str, Any]:
    notification_policy = strict_load(
        GOVERNANCE_DIR / "policies" / "notification-policy.v1.json"
    )
    value = {
        "schema_version": NOTIFICATION_RECEIPT_ID,
        "protocol_revision": PROTOCOL,
        "bundle_digest": CANDIDATE_BUNDLE_DIGEST,
        "receipt_uid": uid("nrc"),
        "notification_uid": intent["notification_uid"],
        "auto_transaction_uid": intent["auto_transaction_uid"],
        "impact": "MAJOR",
        "notification_mode": "AUTOMATIC_NOTIFICATION_ONLY",
        "timing": "PRE_WRITE",
        "provider_code": "EMAIL_PROVIDER",
        "provider_status": "SENT",
        "recipient_ref": "owner-primary",
        "provider_receipt_ref": "gmail-provider-safe",
        "notification_policy_id": (
            "urn:linzecolin:agentdatabase:skillops:policy:notification:v1"
        ),
        "policy_snapshot_digest": sha(
            canonicalize_object(notification_policy)
        ),
        "metadata_digest": sha(
            canonicalize_object(notification_metadata(intent))
        ),
        "created_at": TS_0,
        "sent_at": TS_1,
        "approval_required": False,
        "owner_reply_required": False,
        "receipt_digest": "0" * 64,
    }
    value["receipt_digest"] = canonical_digest(value, "/receipt_digest")
    return value


def settlement_fixture(
    intent: Mapping[str, Any],
    receipt: Mapping[str, Any],
) -> tuple[Dict[str, Any], Dict[str, bytes]]:
    paths = activation_paths(intent["activation_uid"])
    payloads = {
        VERSION_PATH: (TARGET_SRV_REVISION + "\n").encode("ascii"),
        HANDOFF_PATH: (
            b"# Mechanism handoff\n\n"
            b"State: ACTIVE_PENDING_REMOTE_READBACK\n"
            + f"Activation settlement: {paths['settlement']}\n".encode("ascii")
        ),
        paths["intent"]: canonicalize_object(intent),
        paths["notification"]: canonicalize_object(receipt),
    }
    artifacts = [
        {
            "artifact_uid": uid("art", ULID_1),
            "artifact_role": "ACTIVE_VERSION_MARKER",
            "artifact_repo_path": VERSION_PATH,
            "artifact_digest": sha(payloads[VERSION_PATH]),
        },
        {
            "artifact_uid": uid("art", ULID_2),
            "artifact_role": "MECHANISM_HANDOFF",
            "artifact_repo_path": HANDOFF_PATH,
            "artifact_digest": sha(payloads[HANDOFF_PATH]),
        },
        {
            "artifact_uid": intent["envelope_uid"],
            "artifact_role": "ACTIVATION_INTENT",
            "artifact_repo_path": paths["intent"],
            "artifact_digest": sha(payloads[paths["intent"]]),
            "artifact_schema_id": INTENT_ID,
        },
        {
            "artifact_uid": receipt["receipt_uid"],
            "artifact_role": "NOTIFICATION_RECEIPT",
            "artifact_repo_path": paths["notification"],
            "artifact_digest": sha(payloads[paths["notification"]]),
            "artifact_schema_id": NOTIFICATION_RECEIPT_ID,
        },
    ]
    evidence = [
        {
            "evidence_type": "ACTIVATION_INTENT",
            "evidence_uid": intent["envelope_uid"],
            "evidence_digest": intent["envelope_digest"],
            "artifact_repo_path": paths["intent"],
        },
        {
            "evidence_type": "NOTIFICATION_RECEIPT",
            "evidence_uid": receipt["receipt_uid"],
            "evidence_digest": receipt["receipt_digest"],
            "artifact_repo_path": paths["notification"],
        },
    ]
    value = {
        "schema_version": SETTLEMENT_ID,
        "protocol_revision": PROTOCOL,
        "bundle_digest": CANDIDATE_BUNDLE_DIGEST,
        "activation_uid": intent["activation_uid"],
        "envelope_uid": uid("env", ULID_3),
        "auto_transaction_uid": intent["auto_transaction_uid"],
        "expected_remote_head": intent["expected_remote_head"],
        "target_srv_revision": intent["target_srv_revision"],
        "notification_provider_status": "SENT",
        "notification_timing": "PRE_WRITE",
        "recipient_ref": intent["recipient_ref"],
        "evidence_refs": sorted(
            evidence, key=lambda row: row["evidence_type"]
        ),
        "artifacts": sorted(
            artifacts, key=lambda row: row["artifact_repo_path"]
        ),
        "created_at": TS_2,
        "envelope_digest": "0" * 64,
    }
    value["envelope_digest"] = canonical_digest(value, "/envelope_digest")
    return value, payloads


class ActivationControlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bundle = load_activation_bundle(allow_current_draft=True)

    def test_01_generated_control_is_byte_equivalent(self) -> None:
        result = subprocess.run(
            [
                "/usr/bin/python3",
                "-B",
                str(TOOLS_DIR / "build_activation_control.py"),
                "--check",
            ],
            cwd=REPO_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("ACTIVATION_CONTROL_BYTE_EQUIVALENT", result.stdout)

    def test_02_bootstrap_schemas_are_digest_pinned_outside_bundle(self) -> None:
        interface = strict_load(CONTROL_INTERFACE_PATH)
        manifest = strict_load(
            GOVERNANCE_DIR / "bundles" / "schema-bundle-manifest.v1.json"
        )
        self.assertEqual(interface["status"], "DRAFT_NON_ACTIVE")
        self.assertTrue(interface["activation_forbidden"])
        self.assertEqual(interface["bundle_digest"], CANDIDATE_BUNDLE_DIGEST)
        self.assertEqual(interface["candidate_schema_count"], 31)
        self.assertEqual(interface["candidate_policy_count"], 5)
        self.assertEqual(
            interface["next_phase"],
            "AUTO_EXACT_BUNDLE_INTEGRATION",
        )
        self.assertEqual(
            interface["consumer_contract"]["verified_git_object_id"],
            "sha1:91a12e48351be3ee05ec23ef61aec81056b02014",
        )
        self.assertFalse(
            interface["consumer_contract"][
                "canonical_publication_permitted"
            ]
        )
        self.assertFalse(
            interface["transition_contract"][
                "auto_runtime_integration_complete"
            ]
        )
        self.assertFalse(
            interface["transition_contract"]["schedule_authority_resolved"]
        )
        self.assertFalse(interface["transition_contract"]["au_040_complete"])
        self.assertFalse(interface["transition_contract"]["m0c_b_permitted"])
        self.assertEqual(interface["bootstrap_schema_count"], 2)
        self.assertNotIn(
            INTENT_ID, {entry["id"] for entry in manifest["schemas"]}
        )
        self.assertNotIn(
            SETTLEMENT_ID, {entry["id"] for entry in manifest["schemas"]}
        )
        self.assertEqual(manifest["bundle_digest"], CANDIDATE_BUNDLE_DIGEST)
        self.assertFalse((REPO_ROOT / VERSION_PATH).exists())
        observed = {
            INTENT_ID: sha(canonicalize_object(strict_load(INTENT_SCHEMA_PATH))),
            SETTLEMENT_ID: sha(
                canonicalize_object(strict_load(SETTLEMENT_SCHEMA_PATH))
            ),
        }
        self.assertEqual(
            {
                entry["id"]: entry["schema_sha256"]
                for entry in interface["bootstrap_schema_entries"]
            },
            observed,
        )

    def test_03_valid_intent_and_settlement_close_two_stage_handshake(self) -> None:
        intent = intent_fixture()
        receipt = receipt_fixture(intent)
        settlement, payloads = settlement_fixture(intent, receipt)
        validate_intent(
            intent, expected_remote_head=REMOTE_HEAD, bundle=self.bundle
        )
        evidence = validate_settlement(
            settlement,
            intent=intent,
            notification_receipt=receipt,
            artifact_payloads=payloads,
            expected_remote_head=REMOTE_HEAD,
            bundle=self.bundle,
        )
        self.assertEqual(
            evidence["settlement_envelope_digest"],
            settlement["envelope_digest"],
        )

    def test_04_intent_exact_version_digest_and_write_set_cannot_drift(self) -> None:
        intent = intent_fixture()
        intent["planned_artifacts"][0]["artifact_digest"] = "d" * 64
        intent["envelope_digest"] = canonical_digest(
            intent, "/envelope_digest"
        )
        with self.assertRaisesRegex(
            ContractError, "ACTIVATION_INTENT_PLANNED_WRITE_SET_MISMATCH"
        ):
            validate_intent(intent, bundle=self.bundle)

    def test_05_intent_dynamic_artifact_cannot_claim_pre_send_digest(self) -> None:
        intent = intent_fixture()
        row = next(
            item
            for item in intent["planned_artifacts"]
            if item["artifact_role"] == "NOTIFICATION_RECEIPT"
        )
        row["artifact_digest"] = "d" * 64
        intent["envelope_digest"] = canonical_digest(
            intent, "/envelope_digest"
        )
        with self.assertRaises(ContractError):
            validate_intent(intent, bundle=self.bundle)

    def test_06_remote_head_is_external_not_repository_self_report(self) -> None:
        with self.assertRaisesRegex(
            ContractError, "ACTIVATION_INTENT_EXPECTED_HEAD_MISMATCH"
        ):
            validate_intent(
                intent_fixture(),
                expected_remote_head="sha1:" + "f" * 40,
                bundle=self.bundle,
            )

    def test_07_failed_or_unknown_provider_receipt_cannot_settle(self) -> None:
        intent = intent_fixture()
        receipt = receipt_fixture(intent)
        receipt["provider_status"] = "FAILED"
        receipt["failure_code"] = "PROVIDER_TIMEOUT"
        receipt.pop("provider_receipt_ref")
        receipt.pop("sent_at")
        receipt["receipt_digest"] = canonical_digest(
            receipt, "/receipt_digest"
        )
        settlement, payloads = settlement_fixture(intent, receipt)
        with self.assertRaises(ContractError):
            validate_settlement(
                settlement,
                intent=intent,
                notification_receipt=receipt,
                artifact_payloads=payloads,
                bundle=self.bundle,
            )

    def test_08_receipt_and_intent_evidence_digests_are_exact(self) -> None:
        intent = intent_fixture()
        receipt = receipt_fixture(intent)
        settlement, payloads = settlement_fixture(intent, receipt)
        settlement["evidence_refs"][0]["evidence_digest"] = "d" * 64
        settlement["envelope_digest"] = canonical_digest(
            settlement, "/envelope_digest"
        )
        with self.assertRaisesRegex(
            ContractError,
            "ACTIVATION_SETTLEMENT_EVIDENCE_BINDING_MISMATCH",
        ):
            validate_settlement(
                settlement,
                intent=intent,
                notification_receipt=receipt,
                artifact_payloads=payloads,
                bundle=self.bundle,
            )

    def test_09_every_physical_artifact_digest_is_recomputed(self) -> None:
        intent = intent_fixture()
        receipt = receipt_fixture(intent)
        settlement, payloads = settlement_fixture(intent, receipt)
        payloads[HANDOFF_PATH] += b"drift\n"
        with self.assertRaisesRegex(
            ContractError,
            "ACTIVATION_SETTLEMENT_PHYSICAL_DIGEST_MISMATCH",
        ):
            validate_settlement(
                settlement,
                intent=intent,
                notification_receipt=receipt,
                artifact_payloads=payloads,
                bundle=self.bundle,
            )

    def test_09a_public_json_artifact_bytes_must_be_canonical(self) -> None:
        intent = intent_fixture()
        receipt = receipt_fixture(intent)
        settlement, payloads = settlement_fixture(intent, receipt)
        intent_path = activation_paths(intent["activation_uid"])["intent"]
        payloads[intent_path] += b"\n"
        intent_row = next(
            row
            for row in settlement["artifacts"]
            if row["artifact_repo_path"] == intent_path
        )
        intent_row["artifact_digest"] = sha(payloads[intent_path])
        settlement["envelope_digest"] = canonical_digest(
            settlement, "/envelope_digest"
        )
        with self.assertRaisesRegex(
            ContractError, "ACTIVATION_SETTLEMENT_INTENT_BYTES_MISMATCH"
        ):
            validate_settlement(
                settlement,
                intent=intent,
                notification_receipt=receipt,
                artifact_payloads=payloads,
                bundle=self.bundle,
            )

    def test_09b_notification_metadata_digest_cannot_be_reused(self) -> None:
        intent = intent_fixture()
        receipt = receipt_fixture(intent)
        receipt["metadata_digest"] = "d" * 64
        receipt["receipt_digest"] = canonical_digest(
            receipt, "/receipt_digest"
        )
        settlement, payloads = settlement_fixture(intent, receipt)
        with self.assertRaisesRegex(
            ContractError,
            "ACTIVATION_NOTIFICATION_RECEIPT_DIGEST_BINDING_MISMATCH",
        ):
            validate_settlement(
                settlement,
                intent=intent,
                notification_receipt=receipt,
                artifact_payloads=payloads,
                bundle=self.bundle,
            )

    def test_09c_notification_scope_is_public_safe_and_exact_set_is_digest_bound(
        self,
    ) -> None:
        intent = intent_fixture()
        metadata = notification_metadata(intent)
        self.assertEqual(
            metadata["affected_path_refs"],
            list(NOTIFICATION_AFFECTED_PATH_REFS),
        )
        self.assertTrue(
            all(
                intent["activation_uid"] not in path
                for path in metadata["affected_path_refs"]
            )
        )
        self.assertIn(intent["envelope_digest"], metadata["evidence_digests"])
        scan_public_value(metadata, self.bundle.policies)

    def test_10_settlement_self_is_distinguished_not_recursive_artifact(self) -> None:
        intent = intent_fixture()
        receipt = receipt_fixture(intent)
        settlement, payloads = settlement_fixture(intent, receipt)
        settlement_path = activation_paths(intent["activation_uid"])[
            "settlement"
        ]
        payloads[settlement_path] = canonicalize_object(settlement)
        with self.assertRaisesRegex(
            ContractError, "ACTIVATION_SETTLEMENT_PAYLOAD_SET_MISMATCH"
        ):
            validate_settlement(
                settlement,
                intent=intent,
                notification_receipt=receipt,
                artifact_payloads=payloads,
                bundle=self.bundle,
            )

    def test_11_handoff_cannot_embed_settlement_digest_cycle(self) -> None:
        intent = intent_fixture()
        receipt = receipt_fixture(intent)
        settlement, payloads = settlement_fixture(intent, receipt)
        payloads[HANDOFF_PATH] += (
            settlement["envelope_digest"] + "\n"
        ).encode("ascii")
        handoff_row = next(
            row
            for row in settlement["artifacts"]
            if row["artifact_repo_path"] == HANDOFF_PATH
        )
        handoff_row["artifact_digest"] = sha(payloads[HANDOFF_PATH])
        with self.assertRaisesRegex(
            ContractError, "ACTIVATION_HANDOFF_SETTLEMENT_DIGEST_CYCLE"
        ):
            validate_settlement(
                settlement,
                intent=intent,
                notification_receipt=receipt,
                artifact_payloads=payloads,
                bundle=self.bundle,
            )

    def test_12_public_control_never_accepts_actual_recipient(self) -> None:
        intent = intent_fixture()
        intent["recipient_ref"] = "owner" + "@" + "example.invalid"
        intent["envelope_digest"] = canonical_digest(
            intent, "/envelope_digest"
        )
        with self.assertRaises(ContractError):
            validate_intent(intent, bundle=self.bundle)
        with self.assertRaises(ContractError):
            scan_public_value(intent, self.bundle.policies)

    def test_13_unknown_fields_fail_closed(self) -> None:
        intent = intent_fixture()
        intent["caller_verified"] = True
        intent["envelope_digest"] = canonical_digest(
            intent, "/envelope_digest"
        )
        with self.assertRaises(ContractError):
            validate_intent(intent, bundle=self.bundle)

    def test_14_settlement_context_cannot_switch_transaction(self) -> None:
        intent = intent_fixture()
        receipt = receipt_fixture(intent)
        settlement, payloads = settlement_fixture(intent, receipt)
        settlement["auto_transaction_uid"] = uid("atx", ULID_1)
        settlement["envelope_digest"] = canonical_digest(
            settlement, "/envelope_digest"
        )
        with self.assertRaisesRegex(
            ContractError, "ACTIVATION_SETTLEMENT_INTENT_CONTEXT_MISMATCH"
        ):
            validate_settlement(
                settlement,
                intent=intent,
                notification_receipt=receipt,
                artifact_payloads=payloads,
                bundle=self.bundle,
            )

    def test_15_artifact_reader_rejects_symlink_root_parent_and_file(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            root = base / "root"
            root.mkdir()
            directory = root / "a"
            directory.mkdir()
            artifact = directory / "value.json"
            artifact.write_bytes(b"{}")
            self.assertEqual(
                _regular_file_under(root, "a/value.json"),
                b"{}",
            )

            outside = base / "outside.json"
            outside.write_bytes(b"outside")
            artifact.unlink()
            artifact.symlink_to(outside)
            with self.assertRaisesRegex(
                ContractError,
                "ACTIVATION_ARTIFACT_SYMLINK_OR_UNAVAILABLE",
            ):
                _regular_file_under(root, "a/value.json")

            artifact.unlink()
            real_parent = base / "real-parent"
            real_parent.mkdir()
            (real_parent / "value.json").write_bytes(b"{}")
            directory.rmdir()
            directory.symlink_to(real_parent, target_is_directory=True)
            with self.assertRaisesRegex(
                ContractError,
                "ACTIVATION_ARTIFACT_SYMLINK_OR_UNAVAILABLE",
            ):
                _regular_file_under(root, "a/value.json")

            root_alias = base / "root-alias"
            root_alias.symlink_to(root, target_is_directory=True)
            with self.assertRaisesRegex(
                ContractError,
                "ACTIVATION_ARTIFACT_ROOT_NOT_REAL_DIRECTORY",
            ):
                _regular_file_under(root_alias, "a/value.json")

    def test_16_external_control_tuple_is_the_only_runtime_trust_root(
        self,
    ) -> None:
        object_id = "sha1:" + "b" * 40
        control_raw = CONTROL_INTERFACE_PATH.read_bytes()
        blobs = {
            CONTROL_INTERFACE_REPO_PATH: control_raw,
            **{
                relative_path: (
                    INTENT_SCHEMA_PATH
                    if schema_id == INTENT_ID
                    else SETTLEMENT_SCHEMA_PATH
                ).read_bytes()
                for schema_id, relative_path in CONTROL_SCHEMA_REPO_PATHS.items()
            },
        }

        def fake_blob(_repo_root, observed_object_id, relative_path):
            self.assertEqual(observed_object_id, object_id)
            return blobs[relative_path]

        trust = ActivationControlTrustTuple(
            object_id,
            sha(control_raw),
            CONTROL_INTERFACE_REPO_PATH,
            CONTROL_MODE,
        )
        with self.assertRaisesRegex(
            ContractError,
            "ACTIVATION_CONTROL_EXTERNAL_TRUST_TUPLE_REQUIRED",
        ):
            load_activation_bundle()
        with mock.patch(
            "validate_activation._git_blob_for_control",
            side_effect=fake_blob,
        ):
            trusted = load_activation_bundle(trust)
            self.assertIn(INTENT_ID, trusted.schemas)
            self.assertIn(SETTLEMENT_ID, trusted.schemas)
            bad = ActivationControlTrustTuple(
                object_id,
                "d" * 64,
                CONTROL_INTERFACE_REPO_PATH,
                CONTROL_MODE,
            )
            with self.assertRaisesRegex(
                ContractError,
                "ACTIVATION_CONTROL_INTERFACE_RAW_DIGEST_MISMATCH",
            ):
                load_activation_bundle(bad)


if __name__ == "__main__":
    unittest.main()
