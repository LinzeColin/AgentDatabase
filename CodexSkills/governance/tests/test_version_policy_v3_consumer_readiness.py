from __future__ import annotations

import copy
import datetime as dt
import hashlib
import unittest
from pathlib import Path
from types import SimpleNamespace

from CodexSkills.governance.release.version_policy_v3.consumer import (
    CANDIDATE_MANIFEST_PATH,
    DRAFT_INTERFACE_MODE,
    DRAFT_INTERFACE_PATH,
    PREDECESSOR_SELECTION_MODE,
    SUCCESSOR_SELECTION_MODE,
    VERSION_POLICY_CONSUMER_READINESS_SCHEMA_ID,
    VersionPolicyConsumerError,
    VersionPolicyDraftTrustTuple,
    assert_schedule_activation_permitted,
    classify_policy_impact,
    load_trusted_version_policies,
    read_schedule_contract,
)
from CodexSkills.governance.release.version_policy_v3.contract import (
    UNRESOLVED_SCHEDULE_CODE,
    VERSION_POLICY_V2_ID,
    VERSION_POLICY_V3_ID,
)
from CodexSkills.governance.tools.build_version_policy_v3_consumer_readiness import (
    AUTO_GIT_OBJECT,
    AUTO_RUNTIME_INTERFACE_PATH,
    AUTO_RUNTIME_INTERFACE_RAW_SHA256,
    CANDIDATE_BUNDLE_DIGEST,
    CANDIDATE_GIT_OBJECT,
    CANDIDATE_MANIFEST_RAW_SHA256,
    CONTROL_INTERFACE_PATH,
    CONTROL_INTERFACE_RAW_SHA256,
    DRAFT_GIT_OBJECT,
    DRAFT_INTERFACE_RAW_SHA256,
    NEXT_PHASE,
    OUTPUT_PATH,
    SCHEMA_PATH,
    VersionPolicyConsumerReadinessBuildError,
    build_interface,
    build_schema,
    render_interface,
    render_schema,
    validate_interface,
)
from CodexSkills.governance.tools.canonical_json import (
    canonical_digest,
    parse_json_bytes,
)
from CodexSkills.governance.tools.validate_mechanism import TrustTuple
from CodexSkills.registry.auto.runtime.core import (
    AutoRuntimeError,
    FakeClock,
)
from CodexSkills.registry.auto.runtime.notification import (
    FakeNotificationTransport,
    TransactionalNotifier,
)
from CodexSkills.registry.auto.runtime.schedule import SchedulePolicy


ROOT = Path(__file__).resolve().parents[3]


def _candidate_trust() -> TrustTuple:
    return TrustTuple(
        verified_git_object_id=CANDIDATE_GIT_OBJECT,
        expected_bundle_digest=CANDIDATE_BUNDLE_DIGEST,
        canonical_manifest_path=CANDIDATE_MANIFEST_PATH,
        mode="CANDIDATE",
    )


def _draft_trust() -> VersionPolicyDraftTrustTuple:
    return VersionPolicyDraftTrustTuple(
        verified_git_object_id=DRAFT_GIT_OBJECT,
        expected_interface_raw_sha256=DRAFT_INTERFACE_RAW_SHA256,
        canonical_interface_path=DRAFT_INTERFACE_PATH,
        mode=DRAFT_INTERFACE_MODE,
    )


class VersionPolicyV3ConsumerReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.trusted = load_trusted_version_policies(
            ROOT,
            _candidate_trust(),
            CANDIDATE_MANIFEST_RAW_SHA256,
            _draft_trust(),
        )

    def test_artifacts_are_byte_equivalent_closed_and_non_active(self) -> None:
        self.assertEqual(SCHEMA_PATH.read_bytes(), render_schema())
        self.assertEqual(OUTPUT_PATH.read_bytes(), render_interface())
        interface = parse_json_bytes(OUTPUT_PATH.read_bytes())
        self.assertEqual(interface, build_interface())
        self.assertEqual(build_schema()["$id"], VERSION_POLICY_CONSUMER_READINESS_SCHEMA_ID)
        self.assertEqual(
            interface["artifact_digest"],
            canonical_digest(interface, "/artifact_digest"),
        )
        validate_interface(interface)
        self.assertEqual(
            interface["status"],
            "DRAFT_NON_ACTIVE_MECHANISM_CONSUMER_READY",
        )
        self.assertFalse(interface["nonmutation"]["release_write_permitted"])
        self.assertFalse(
            interface["nonmutation"]["canonical_publication_permitted"]
        )
        self.assertTrue(interface["nonmutation"]["activation_forbidden"])
        self.assertFalse(interface["nonmutation"]["version_file_created"])
        self.assertFalse(
            (ROOT / "CodexSkills" / "VERSION").exists()
        )

    def test_external_candidate_and_draft_trust_are_independent(self) -> None:
        self.assertEqual(
            self.trusted.candidate_manifest_raw_sha256,
            CANDIDATE_MANIFEST_RAW_SHA256,
        )
        self.assertEqual(
            self.trusted.draft_interface_raw_sha256,
            DRAFT_INTERFACE_RAW_SHA256,
        )
        bad_draft = VersionPolicyDraftTrustTuple(
            verified_git_object_id=DRAFT_GIT_OBJECT,
            expected_interface_raw_sha256="0" * 64,
            canonical_interface_path=DRAFT_INTERFACE_PATH,
            mode=DRAFT_INTERFACE_MODE,
        )
        with self.assertRaisesRegex(
            VersionPolicyConsumerError,
            "VERSION_POLICY_CONSUMER_DRAFT_INTERFACE_RAW_MISMATCH",
        ):
            load_trusted_version_policies(
                ROOT,
                _candidate_trust(),
                CANDIDATE_MANIFEST_RAW_SHA256,
                bad_draft,
            )
        wrong_mode = VersionPolicyDraftTrustTuple(
            verified_git_object_id=DRAFT_GIT_OBJECT,
            expected_interface_raw_sha256=DRAFT_INTERFACE_RAW_SHA256,
            canonical_interface_path=DRAFT_INTERFACE_PATH,
            mode="CANDIDATE",
        )
        with self.assertRaisesRegex(
            VersionPolicyConsumerError,
            "VERSION_POLICY_CONSUMER_DRAFT_TRUST_INVALID",
        ):
            load_trusted_version_policies(
                ROOT,
                _candidate_trust(),
                CANDIDATE_MANIFEST_RAW_SHA256,
                wrong_mode,
            )
        with self.assertRaisesRegex(
            VersionPolicyConsumerError,
            "VERSION_POLICY_CONSUMER_CANDIDATE_MANIFEST_RAW_MISMATCH",
        ):
            load_trusted_version_policies(
                ROOT,
                _candidate_trust(),
                "0" * 64,
                _draft_trust(),
            )

    def test_explicit_dual_read_classifies_without_hybrid_fallback(self) -> None:
        self.assertEqual(
            classify_policy_impact(
                self.trusted,
                policy_id=VERSION_POLICY_V2_ID,
                selection_mode=PREDECESSOR_SELECTION_MODE,
                trigger_codes=["RETENTION_POLICY_CHANGE"],
            ),
            "MAJOR",
        )
        self.assertEqual(
            classify_policy_impact(
                self.trusted,
                policy_id=VERSION_POLICY_V3_ID,
                selection_mode=SUCCESSOR_SELECTION_MODE,
                trigger_codes=["PRIVACY_POLICY_CHANGE"],
            ),
            "MAJOR",
        )
        with self.assertRaisesRegex(
            VersionPolicyConsumerError,
            "VERSION_POLICY_CONSUMER_PREDECESSOR_TRIGGER_UNSUPPORTED",
        ):
            classify_policy_impact(
                self.trusted,
                policy_id=VERSION_POLICY_V2_ID,
                selection_mode=PREDECESSOR_SELECTION_MODE,
                trigger_codes=["PRIVACY_POLICY_CHANGE"],
            )
        with self.assertRaisesRegex(
            VersionPolicyConsumerError,
            "VERSION_POLICY_CONSUMER_SELECTION_MODE_MISMATCH",
        ):
            classify_policy_impact(
                self.trusted,
                policy_id=VERSION_POLICY_V3_ID,
                selection_mode=PREDECESSOR_SELECTION_MODE,
                trigger_codes=["PRIVACY_POLICY_CHANGE"],
            )
        with self.assertRaisesRegex(
            VersionPolicyConsumerError,
            "VERSION_POLICY_CONSUMER_POLICY_ID_UNSUPPORTED",
        ):
            classify_policy_impact(
                self.trusted,
                policy_id="urn:linzecolin:agentdatabase:skillops:policy:version:v4",
                selection_mode=SUCCESSOR_SELECTION_MODE,
                trigger_codes=["PRIVACY_POLICY_CHANGE"],
            )
        for triggers, code in (
            (
                ["RETENTION_POLICY_CHANGE", "RETENTION_POLICY_CHANGE"],
                "VERSION_POLICY_CONSUMER_TRIGGER_DUPLICATE",
            ),
            (
                ["UNRECOGNIZED_CHANGE"],
                "VERSION_POLICY_CONSUMER_TRIGGER_UNKNOWN",
            ),
        ):
            with self.assertRaisesRegex(VersionPolicyConsumerError, code):
                classify_policy_impact(
                    self.trusted,
                    policy_id=VERSION_POLICY_V3_ID,
                    selection_mode=SUCCESSOR_SELECTION_MODE,
                    trigger_codes=triggers,
                )

    def test_both_schedule_reads_remain_fail_closed(self) -> None:
        predecessor = read_schedule_contract(
            self.trusted,
            policy_id=VERSION_POLICY_V2_ID,
            selection_mode=PREDECESSOR_SELECTION_MODE,
        )
        successor = read_schedule_contract(
            self.trusted,
            policy_id=VERSION_POLICY_V3_ID,
            selection_mode=SUCCESSOR_SELECTION_MODE,
        )
        self.assertEqual(predecessor["observed_daily_schedule_local"], "04:15")
        self.assertIsNone(successor["observed_daily_schedule_local"])
        for observed in (predecessor, successor):
            self.assertEqual(
                observed["daily_schedule_authority_state"],
                "UNRESOLVED",
            )
            self.assertEqual(
                observed["schedule_conflict_code"],
                UNRESOLVED_SCHEDULE_CODE,
            )
            self.assertFalse(observed["schedule_activation_permitted"])
        for policy_id, mode in (
            (VERSION_POLICY_V2_ID, PREDECESSOR_SELECTION_MODE),
            (VERSION_POLICY_V3_ID, SUCCESSOR_SELECTION_MODE),
        ):
            with self.assertRaisesRegex(
                VersionPolicyConsumerError,
                "VERSION_POLICY_CONSUMER_SCHEDULE_AUTHORITY_UNRESOLVED",
            ):
                assert_schedule_activation_permitted(
                    self.trusted,
                    policy_id=policy_id,
                    selection_mode=mode,
                )

    def test_actual_auto_consumers_are_truthfully_v2_only(self) -> None:
        schedule = SchedulePolicy()
        schedule.validate_trusted_policy(self.trusted.predecessor)
        with self.assertRaisesRegex(
            AutoRuntimeError,
            "SCHEDULE_POLICY_CONTRACT_MISMATCH",
        ):
            schedule.validate_trusted_policy(self.trusted.successor)

        contract = SimpleNamespace(shared=self.trusted.candidate_bundle)
        outbox = ROOT / ".version-policy-readiness-outbox-not-created"
        transport = FakeNotificationTransport()
        self.assertFalse(outbox.exists())
        notifier = TransactionalNotifier(
            outbox,
            contract,
            CANDIDATE_BUNDLE_DIGEST,
            FakeClock(
                dt.datetime(
                    2026,
                    7,
                    26,
                    tzinfo=dt.timezone.utc,
                )
            ),
            transport,
        )
        metadata = {
            "impact": "MAJOR",
            "change_code": "RETENTION_POLICY_CHANGE",
            "planned_action": "STOP",
            "affected_path_refs": ["CodexSkills/a"],
            "evidence_digests": ["a" * 64],
        }
        notifier._validate_public_metadata(metadata)
        v3_only = copy.deepcopy(metadata)
        v3_only["change_code"] = "PRIVACY_POLICY_CHANGE"
        with self.assertRaisesRegex(
            AutoRuntimeError,
            "NOTIFICATION_PUBLIC_METADATA_ENUM_INVALID",
        ):
            notifier._validate_public_metadata(v3_only)
        self.assertEqual(transport.send_count, 0)
        self.assertFalse(outbox.exists())

    def test_inventory_and_handoff_keep_cross_plane_gate_false(self) -> None:
        interface = build_interface()
        rows = {
            row["component_id"]: row
            for row in interface["consumer_inventory"]
        }
        self.assertEqual(len(rows), 6)
        self.assertEqual(
            rows["MECHANISM_VERSION_POLICY_DUAL_READ_LOADER"][
                "observed_support"
            ],
            "V2_V3_DUAL_READ",
        )
        self.assertEqual(
            rows["AUTO_SCHEDULE_POLICY_CONSUMER"]["observed_support"],
            "V2_ONLY",
        )
        for component_id, row in rows.items():
            if component_id.startswith("AUTO_"):
                self.assertEqual(
                    row["required_action"],
                    "AUTO_DUAL_READ_INTEGRATION",
                )
                self.assertEqual(
                    row["source_git_object_id"],
                    AUTO_GIT_OBJECT,
                )
        self.assertTrue(
            interface["compatibility"][
                "mechanism_consumer_first_verified"
            ]
        )
        self.assertFalse(
            interface["compatibility"]["auto_consumer_first_verified"]
        )
        self.assertFalse(
            interface["compatibility"][
                "cross_plane_consumer_first_complete"
            ]
        )
        self.assertFalse(
            interface["compatibility"][
                "candidate_materialization_permitted"
            ]
        )
        self.assertEqual(interface["next_phase"], NEXT_PHASE)

    def test_source_interface_and_control_bytes_are_pinned_not_self_trusted(self) -> None:
        interface = build_interface()
        source = interface["source_trust"]
        self.assertTrue(
            source["repository_self_report_is_not_trust_root"]
        )
        self.assertEqual(
            source["predecessor_candidate"]["artifact_digest"],
            CANDIDATE_MANIFEST_RAW_SHA256,
        )
        self.assertEqual(
            source["v3_draft"]["artifact_digest"],
            DRAFT_INTERFACE_RAW_SHA256,
        )
        self.assertEqual(
            interface["nonmutation"]["control_interface"][
                "artifact_digest"
            ],
            CONTROL_INTERFACE_RAW_SHA256,
        )
        auto_interface = ROOT.joinpath(
            *AUTO_RUNTIME_INTERFACE_PATH.split("/")
        ).read_bytes()
        self.assertEqual(
            hashlib.sha256(auto_interface).hexdigest(),
            AUTO_RUNTIME_INTERFACE_RAW_SHA256,
        )

    def test_schema_and_semantic_validation_reject_false_readiness(self) -> None:
        tampered = copy.deepcopy(build_interface())
        tampered["consumer_contract"]["auto_dual_read_verified"] = True
        with self.assertRaisesRegex(
            VersionPolicyConsumerReadinessBuildError,
            "VERSION_POLICY_CONSUMER_READINESS",
        ):
            validate_interface(tampered)
        tampered = copy.deepcopy(build_interface())
        tampered["schedule"]["selected_local_time"] = "05:30"
        with self.assertRaisesRegex(
            VersionPolicyConsumerReadinessBuildError,
            "VERSION_POLICY_CONSUMER_READINESS",
        ):
            validate_interface(tampered)


if __name__ == "__main__":
    unittest.main()
