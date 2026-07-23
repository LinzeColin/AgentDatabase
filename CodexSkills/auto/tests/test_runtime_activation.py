from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, Mapping
from unittest import mock

from CodexSkills.auto.runtime.activation import (
    CONTROL_INTERFACE_PATH,
    CONTROL_MODE,
    ActivationControlTrustTuple,
    ActivationHandshake,
)
from CodexSkills.auto.runtime.core import AutoRuntimeError, PROTOCOL
from CodexSkills.auto.runtime.notification import NOTIFICATION_POLICY_ID
from CodexSkills.auto.tools.notification_transport_cli import (
    _reject_activation_bypass,
)
from CodexSkills.governance.tools.canonical_json import (
    canonical_digest,
    canonicalize_object,
)

from runtime_helpers import (
    CANDIDATE_DIGEST,
    CANDIDATE_GIT_OBJECT,
    REPO_ROOT,
    context,
)


CONTROL_GIT_OBJECT = (
    "sha1:6769eba64badac04a131bfa00dbb0e1a353ccae0"
)
CONTROL_INTERFACE_RAW_SHA256 = (
    "24af49e7f3c0ecac85154a2a9741d9d8"
    "ceb16368224cbf7900eceac9fe66e0f7"
)
INTENT_ID = (
    "urn:linzecolin:agentdatabase:skillops:schema:activation-intent:v1"
)
SETTLEMENT_ID = (
    "urn:linzecolin:agentdatabase:skillops:"
    "schema:activation-settlement:v1"
)
NOTIFICATION_RECEIPT_ID = (
    "urn:linzecolin:agentdatabase:skillops:"
    "schema:notification-receipt:v3"
)
VERSION_PATH = "CodexSkills/VERSION"
HANDOFF_PATH = "CodexSkills/governance/HANDOFF.md"
REMOTE_HEAD = "sha1:" + "a" * 40
TARGET_SRV_REVISION = "v0.0.0.3"
TS_0 = "2026-07-23T00:00:00.000000Z"
TS_1 = "2026-07-23T00:00:01.000000Z"
TS_2 = "2026-07-23T00:00:02.000000Z"
ULID_0 = "0" * 26
ULID_1 = "0" * 25 + "1"
ULID_2 = "0" * 25 + "2"
ULID_3 = "0" * 25 + "3"


def typed_uid(prefix: str, suffix: str = ULID_0) -> str:
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
    activation_uid = typed_uid("act")
    paths = activation_paths(activation_uid)
    rows = [
        {
            "artifact_repo_path": VERSION_PATH,
            "artifact_role": "ACTIVE_VERSION_MARKER",
            "digest_availability": "BOUND_IN_INTENT",
            "artifact_digest": sha(
                (TARGET_SRV_REVISION + "\n").encode("ascii")
            ),
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
        "bundle_digest": CANDIDATE_DIGEST,
        "activation_uid": activation_uid,
        "envelope_uid": typed_uid("env"),
        "notification_uid": typed_uid("ntf"),
        "auto_transaction_uid": typed_uid("atx"),
        "bundle_git_object_id": CANDIDATE_GIT_OBJECT,
        "expected_remote_head": REMOTE_HEAD,
        "candidate_manifest_path": (
            "CodexSkills/governance/bundles/"
            "schema-bundle-manifest.v1.json"
        ),
        "target_srv_revision": TARGET_SRV_REVISION,
        "impact": "MAJOR",
        "change_code": "ACTIVE_BUNDLE_CHANGE",
        "planned_action": "ACTIVATE",
        "notification_timing": "PRE_WRITE",
        "recipient_ref": "owner-primary",
        "rollback_target_ref": REMOTE_HEAD,
        "notification_affected_path_refs": [
            "CodexSkills/VERSION",
            "CodexSkills/governance",
        ],
        "planned_artifacts": sorted(
            rows, key=lambda row: row["artifact_repo_path"]
        ),
        "created_at": TS_0,
        "envelope_digest": "0" * 64,
    }
    value["envelope_digest"] = canonical_digest(
        value, "/envelope_digest"
    )
    return value


def notification_metadata(intent: Mapping[str, Any]):
    return {
        "impact": "MAJOR",
        "change_code": "ACTIVE_BUNDLE_CHANGE",
        "planned_action": "ACTIVATE",
        "affected_path_refs": [
            "CodexSkills/VERSION",
            "CodexSkills/governance",
        ],
        "evidence_digests": sorted(
            [intent["bundle_digest"], intent["envelope_digest"]]
        ),
        "rollback_target_ref": intent["rollback_target_ref"],
    }


def receipt_fixture(intent: Mapping[str, Any]) -> Dict[str, Any]:
    policy = context().contract.shared.policies[NOTIFICATION_POLICY_ID]
    value = {
        "schema_version": NOTIFICATION_RECEIPT_ID,
        "protocol_revision": PROTOCOL,
        "bundle_digest": CANDIDATE_DIGEST,
        "receipt_uid": typed_uid("nrc"),
        "notification_uid": intent["notification_uid"],
        "auto_transaction_uid": intent["auto_transaction_uid"],
        "impact": "MAJOR",
        "notification_mode": "AUTOMATIC_NOTIFICATION_ONLY",
        "timing": "PRE_WRITE",
        "provider_code": "EMAIL_PROVIDER",
        "provider_status": "SENT",
        "recipient_ref": "owner-primary",
        "provider_receipt_ref": "gmail-provider-safe",
        "notification_policy_id": NOTIFICATION_POLICY_ID,
        "policy_snapshot_digest": sha(canonicalize_object(policy)),
        "metadata_digest": sha(
            canonicalize_object(notification_metadata(intent))
        ),
        "created_at": TS_0,
        "sent_at": TS_1,
        "approval_required": False,
        "owner_reply_required": False,
        "receipt_digest": "0" * 64,
    }
    value["receipt_digest"] = canonical_digest(
        value, "/receipt_digest"
    )
    return value


def settlement_fixture(
    intent: Mapping[str, Any],
    receipt: Mapping[str, Any],
):
    paths = activation_paths(str(intent["activation_uid"]))
    payloads = {
        VERSION_PATH: (TARGET_SRV_REVISION + "\n").encode("ascii"),
        HANDOFF_PATH: (
            b"# Mechanism handoff\n\n"
            b"State: ACTIVE_PENDING_REMOTE_READBACK\n"
            + (
                "Activation settlement: "
                + paths["settlement"]
                + "\n"
            ).encode("ascii")
        ),
        paths["intent"]: canonicalize_object(intent),
        paths["notification"]: canonicalize_object(receipt),
    }
    artifacts = [
        {
            "artifact_uid": typed_uid("art", ULID_1),
            "artifact_role": "ACTIVE_VERSION_MARKER",
            "artifact_repo_path": VERSION_PATH,
            "artifact_digest": sha(payloads[VERSION_PATH]),
        },
        {
            "artifact_uid": typed_uid("art", ULID_2),
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
        "bundle_digest": CANDIDATE_DIGEST,
        "activation_uid": intent["activation_uid"],
        "envelope_uid": typed_uid("env", ULID_3),
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
    value["envelope_digest"] = canonical_digest(
        value, "/envelope_digest"
    )
    return value, payloads


def materialize(root: Path, payloads: Mapping[str, bytes]) -> None:
    for relative_path, payload in payloads.items():
        target = root.joinpath(*relative_path.split("/"))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)


class RuntimeActivationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.trust = ActivationControlTrustTuple(
            CONTROL_GIT_OBJECT,
            CONTROL_INTERFACE_RAW_SHA256,
            CONTROL_INTERFACE_PATH,
            CONTROL_MODE,
        )
        cls.handshake = ActivationHandshake(
            REPO_ROOT,
            context(),
            cls.trust,
        )

    def test_external_control_tuple_loads_exact_31_schema_closure(
        self,
    ) -> None:
        self.assertEqual(len(self.handshake.bundle.schemas), 31)
        self.assertEqual(len(self.handshake.bundle.policies), 5)
        bad = ActivationControlTrustTuple(
            CONTROL_GIT_OBJECT,
            "d" * 64,
            CONTROL_INTERFACE_PATH,
            CONTROL_MODE,
        )
        with self.assertRaisesRegex(
            AutoRuntimeError,
            "ACTIVATION_CONTROL_INTERFACE_RAW_DIGEST_MISMATCH",
        ):
            ActivationHandshake(REPO_ROOT, context(), bad)

    def test_intent_derives_only_frozen_notification_metadata(self) -> None:
        intent = intent_fixture()
        paths = activation_paths(intent["activation_uid"])
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            materialize(
                root,
                {paths["intent"]: canonicalize_object(intent)},
            )
            verified = self.handshake.verify_intent_root(
                root,
                paths["intent"],
                REMOTE_HEAD,
            )
        self.assertEqual(
            dict(verified.notification_metadata),
            notification_metadata(intent),
        )
        self.assertEqual(
            verified.notification_metadata["affected_path_refs"],
            ["CodexSkills/VERSION", "CodexSkills/governance"],
        )
        with self.assertRaises(TypeError):
            verified.notification_metadata["planned_action"] = "STOP"

    def test_settlement_recomputes_exact_four_artifacts_plus_self(
        self,
    ) -> None:
        intent = intent_fixture()
        receipt = receipt_fixture(intent)
        settlement, payloads = settlement_fixture(intent, receipt)
        settlement_path = activation_paths(intent["activation_uid"])[
            "settlement"
        ]
        payloads[settlement_path] = canonicalize_object(settlement)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            materialize(root, payloads)
            verified = self.handshake.verify_settlement_root(
                root,
                settlement_path,
                REMOTE_HEAD,
            )
        self.assertEqual(verified.artifact_paths, tuple(sorted(payloads)))
        self.assertEqual(dict(verified.payloads), payloads)
        self.assertEqual(verified.auto_transaction_uid, typed_uid("atx"))

    def test_failed_receipt_or_physical_drift_cannot_settle(self) -> None:
        intent = intent_fixture()
        receipt = receipt_fixture(intent)
        settlement, payloads = settlement_fixture(intent, receipt)
        settlement_path = activation_paths(intent["activation_uid"])[
            "settlement"
        ]
        payloads[HANDOFF_PATH] += b"drift\n"
        payloads[settlement_path] = canonicalize_object(settlement)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            materialize(root, payloads)
            with self.assertRaisesRegex(
                AutoRuntimeError,
                "ACTIVATION_SETTLEMENT_PHYSICAL_DIGEST_MISMATCH",
            ):
                self.handshake.verify_settlement_root(
                    root,
                    settlement_path,
                    REMOTE_HEAD,
                )

    def test_noncanonical_json_and_symlink_artifacts_fail_closed(self) -> None:
        intent = intent_fixture()
        paths = activation_paths(intent["activation_uid"])
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            root = base / "root"
            root.mkdir()
            materialize(
                root,
                {paths["intent"]: canonicalize_object(intent) + b"\n"},
            )
            with self.assertRaisesRegex(
                AutoRuntimeError,
                "ACTIVATION_INTENT_BYTES_NOT_CANONICAL",
            ):
                self.handshake.verify_intent_root(
                    root,
                    paths["intent"],
                    REMOTE_HEAD,
                )
            target = root.joinpath(*paths["intent"].split("/"))
            target.unlink()
            outside = base / "outside.json"
            outside.write_bytes(canonicalize_object(intent))
            target.symlink_to(outside)
            with self.assertRaisesRegex(
                AutoRuntimeError,
                "ACTIVATION_ARTIFACT_SYMLINK_OR_UNAVAILABLE",
            ):
                self.handshake.verify_intent_root(
                    root,
                    paths["intent"],
                    REMOTE_HEAD,
                )

    def test_local_control_runtime_cannot_replace_external_object(self) -> None:
        with mock.patch(
            "CodexSkills.auto.runtime.activation._git_blob",
            return_value=b"drift",
        ):
            with self.assertRaisesRegex(
                AutoRuntimeError,
                "ACTIVATION_CONTROL_RUNTIME_LOCAL_DRIFT",
            ):
                ActivationHandshake(REPO_ROOT, context(), self.trust)

    def test_generic_notification_cli_cannot_bypass_intent(self) -> None:
        with self.assertRaisesRegex(
            AutoRuntimeError,
            "ACTIVATION_HANDSHAKE_ENTRYPOINT_REQUIRED",
        ):
            _reject_activation_bypass({"planned_action": "ACTIVATE"})
        _reject_activation_bypass({"planned_action": "STOP"})


if __name__ == "__main__":
    unittest.main()
