from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from CodexSkills.governance.release.foundations import (
    LOCKED_MAJOR_TRIGGER_CODES,
    MATERIAL_TRIGGER_CODES,
    ROUTINE_TRIGGER_CODES,
)
from CodexSkills.governance.release.version_policy_v3.contract import (
    SCHEDULE_CANDIDATES,
    UNRESOLVED_SCHEDULE_CODE,
    V2_MISSING_MAJOR_TRIGGER_CODES,
    VERSION_POLICY_DRAFT_INTERFACE_SCHEMA_ID,
    VERSION_POLICY_V3_SCHEMA_ID,
    VersionPolicyV3Error,
    assert_schedule_activation_permitted,
    classify_v3_impact,
    validate_v2_to_v3_compatibility,
    validate_version_policy_v3,
)
from CodexSkills.governance.tools.build_version_policy_v3_draft import (
    CANDIDATE_MANIFEST_PATH,
    CONTROL_INTERFACE_PATH,
    INTERFACE_PATH,
    INTERFACE_SCHEMA_PATH,
    NOTIFICATION_POLICY_PATH,
    POLICY_PATH,
    POLICY_SCHEMA_PATH,
    PREDECESSOR_POLICY_PATH,
    build_interface,
    build_policy,
    render_interface,
    render_policy,
    validate_interface,
)
from CodexSkills.governance.tools.canonical_json import (
    parse_json_bytes,
)


ROOT = Path(__file__).resolve().parents[3]
GOVERNANCE = ROOT / "CodexSkills" / "governance"
COMMON_SCHEMA_PATH = (
    GOVERNANCE / "schemas" / "common-definitions.schema.json"
)
PUBLIC_VALUE_POLICY_PATH = (
    GOVERNANCE / "policies-v2" / "public-value-policy.v2.json"
)
sys.path.insert(0, str(GOVERNANCE / "tools"))
from validate_mechanism import scan_public_value  # noqa: E402


def _load(path: Path):
    return parse_json_bytes(path.read_bytes())


def _registry_documents():
    documents = [
        _load(COMMON_SCHEMA_PATH),
        _load(POLICY_SCHEMA_PATH),
        _load(INTERFACE_SCHEMA_PATH),
    ]
    return {document["$id"]: document for document in documents}


def _schema_errors(schema_id: str, value):
    documents = _registry_documents()
    registry = Registry().with_resources(
        (identifier, Resource.from_contents(document))
        for identifier, document in documents.items()
    )
    return list(
        Draft202012Validator(
            documents[schema_id],
            registry=registry,
        ).iter_errors(value)
    )


class VersionPolicyV3DraftTests(unittest.TestCase):
    def test_policy_and_interface_are_byte_equivalent(self):
        self.assertEqual(render_policy(), POLICY_PATH.read_bytes())
        self.assertEqual(render_interface(), INTERFACE_PATH.read_bytes())
        self.assertEqual(build_policy(), _load(POLICY_PATH))
        self.assertEqual(build_interface(), _load(INTERFACE_PATH))
        validate_interface(_load(INTERFACE_PATH))

    def test_policy_and_interface_validate_offline(self):
        policy = _load(POLICY_PATH)
        policy_schema = _load(POLICY_SCHEMA_PATH)
        interface = _load(INTERFACE_PATH)
        interface_schema = _load(INTERFACE_SCHEMA_PATH)
        self.assertEqual(
            [],
            _schema_errors(
                VERSION_POLICY_V3_SCHEMA_ID,
                policy,
            ),
        )
        self.assertEqual(
            [],
            _schema_errors(
                VERSION_POLICY_DRAFT_INTERFACE_SCHEMA_ID,
                interface,
            ),
        )
        self.assertEqual(set(policy), set(policy_schema["properties"]))
        self.assertEqual(set(policy), set(policy_schema["required"]))
        self.assertEqual(
            set(interface),
            set(interface_schema["properties"]),
        )
        self.assertEqual(
            set(interface),
            set(interface_schema["required"]),
        )
        for document in _registry_documents().values():
            Draft202012Validator.check_schema(document)

    def test_locked_impact_sets_are_exact_and_cannot_downgrade(self):
        policy = _load(POLICY_PATH)
        self.assertEqual(
            "PATCH",
            classify_v3_impact(sorted(ROUTINE_TRIGGER_CODES), policy),
        )
        self.assertEqual(
            "MINOR",
            classify_v3_impact(sorted(MATERIAL_TRIGGER_CODES), policy),
        )
        self.assertEqual(
            "MAJOR",
            classify_v3_impact(sorted(LOCKED_MAJOR_TRIGGER_CODES), policy),
        )
        for code in sorted(LOCKED_MAJOR_TRIGGER_CODES):
            with self.subTest(major_code=code):
                self.assertEqual(
                    "MAJOR",
                    classify_v3_impact(
                        [code, "DERIVED_VIEW_REBUILD"],
                        policy,
                    ),
                )
        self.assertFalse(policy["impact_downgrade_allowed"])

    def test_unknown_duplicate_and_tampered_triggers_fail_closed(self):
        policy = _load(POLICY_PATH)
        with self.assertRaisesRegex(
            VersionPolicyV3Error,
            "VERSION_POLICY_V3_TRIGGER_UNKNOWN",
        ):
            classify_v3_impact(["UNDECLARED_CHANGE"], policy)
        with self.assertRaisesRegex(
            VersionPolicyV3Error,
            "VERSION_POLICY_V3_TRIGGER_DUPLICATE",
        ):
            classify_v3_impact(
                ["DERIVED_VIEW_REBUILD", "DERIVED_VIEW_REBUILD"],
                policy,
            )
        tampered = copy.deepcopy(policy)
        tampered["major_trigger_codes"].remove(
            "PRIVACY_POLICY_CHANGE"
        )
        with self.assertRaisesRegex(
            VersionPolicyV3Error,
            "VERSION_POLICY_V3_MAJOR_TRIGGER_SET_INVALID",
        ):
            validate_version_policy_v3(tampered)

    def test_v2_gap_is_closed_without_dropping_existing_major_codes(self):
        predecessor = _load(PREDECESSOR_POLICY_PATH)
        policy = _load(POLICY_PATH)
        result = validate_v2_to_v3_compatibility(
            predecessor,
            policy,
            _load(NOTIFICATION_POLICY_PATH),
        )
        self.assertEqual(
            list(V2_MISSING_MAJOR_TRIGGER_CODES),
            result["missing_major_trigger_codes_closed"],
        )
        self.assertTrue(
            set(predecessor["major_trigger_codes"]).issubset(
                policy["major_trigger_codes"]
            )
        )
        self.assertEqual(
            13,
            len(policy["major_trigger_codes"]),
        )
        self.assertEqual(
            "CONSUMER_FIRST_REPLACEMENT",
            result["compatibility_mode"],
        )

    def test_srv_and_daily_transaction_semantics_are_separate(self):
        policy = _load(POLICY_PATH)
        self.assertEqual(
            "ONE_SRV_PER_ACCEPTED_CANONICAL_TRANSACTION",
            policy["transaction_semantics"],
        )
        self.assertFalse(policy["daily_run_increments_srv"])
        self.assertFalse(
            policy["srv_revision_used_as_daily_sequence"]
        )
        self.assertTrue(policy["daily_transaction_uid_separate"])
        self.assertEqual(
            "AUTO_TRANSACTION_UID",
            policy["daily_transaction_uid_kind"],
        )
        self.assertFalse(policy["independent_subsystem_counters"])

    def test_schedule_remains_unresolved_and_blocks_activation(self):
        policy = _load(POLICY_PATH)
        self.assertEqual(
            "UNRESOLVED",
            policy["daily_schedule_authority_state"],
        )
        self.assertIsNone(policy["daily_schedule_local"])
        self.assertEqual(
            list(SCHEDULE_CANDIDATES),
            policy["daily_schedule_candidate_local_times"],
        )
        self.assertEqual(
            UNRESOLVED_SCHEDULE_CODE,
            policy["schedule_conflict_code"],
        )
        with self.assertRaisesRegex(
            VersionPolicyV3Error,
            "VERSION_POLICY_V3_SCHEDULE_AUTHORITY_UNRESOLVED",
        ):
            assert_schedule_activation_permitted(policy)

    def test_only_directly_resolved_candidate_times_can_activate(self):
        for selected in SCHEDULE_CANDIDATES:
            resolved = copy.deepcopy(_load(POLICY_PATH))
            resolved["daily_schedule_authority_state"] = "RESOLVED"
            resolved["daily_schedule_local"] = selected
            resolved["schedule_conflict_code"] = None
            resolved["schedule_activation_permitted"] = True
            with self.subTest(selected=selected):
                validate_version_policy_v3(resolved)
                self.assertEqual(
                    [],
                    _schema_errors(
                        VERSION_POLICY_V3_SCHEMA_ID,
                        resolved,
                    ),
                )
                assert_schedule_activation_permitted(resolved)
        invalid = copy.deepcopy(_load(POLICY_PATH))
        invalid["daily_schedule_authority_state"] = "RESOLVED"
        invalid["daily_schedule_local"] = "03:00"
        invalid["schedule_conflict_code"] = None
        invalid["schedule_activation_permitted"] = True
        with self.assertRaisesRegex(
            VersionPolicyV3Error,
            "VERSION_POLICY_V3_RESOLVED_SCHEDULE_INVALID",
        ):
            validate_version_policy_v3(invalid)
        self.assertTrue(
            _schema_errors(VERSION_POLICY_V3_SCHEMA_ID, invalid)
        )

    def test_notification_contract_is_one_way_and_repo_external(self):
        policy = _load(POLICY_PATH)
        self.assertTrue(
            policy["planned_major_provider_sent_before_write"]
        )
        self.assertFalse(
            policy["planned_major_write_without_sent_allowed"]
        )
        self.assertFalse(policy["owner_approval_required"])
        self.assertFalse(policy["owner_reply_required"])
        self.assertTrue(
            policy["actual_recipient_mapping_repo_external"]
        )
        self.assertNotIn(b"@", POLICY_PATH.read_bytes())
        predecessor = _load(PREDECESSOR_POLICY_PATH)
        notification = copy.deepcopy(_load(NOTIFICATION_POLICY_PATH))
        notification["automatic"] = False
        with self.assertRaisesRegex(
            VersionPolicyV3Error,
            "VERSION_POLICY_V3_NOTIFICATION_PREDECESSOR_INVALID",
        ):
            validate_v2_to_v3_compatibility(
                predecessor,
                policy,
                notification,
            )

    def test_public_policy_scanner_accepts_only_sanitized_draft(self):
        public_policy = _load(PUBLIC_VALUE_POLICY_PATH)
        trusted = {public_policy["policy_id"]: public_policy}
        scan_public_value(_load(POLICY_PATH), trusted)
        scan_public_value(_load(INTERFACE_PATH), trusted)

    def test_candidate_and_control_remain_unchanged(self):
        candidate = _load(CANDIDATE_MANIFEST_PATH)
        interface = _load(INTERFACE_PATH)
        self.assertEqual(31, candidate["schema_count"])
        self.assertEqual(5, candidate["policy_count"])
        self.assertEqual(
            candidate["bundle_digest"],
            interface["candidate_bundle"]["bundle_digest"],
        )
        self.assertNotIn(
            VERSION_POLICY_V3_SCHEMA_ID,
            {row["id"] for row in candidate["schemas"]},
        )
        self.assertNotIn(
            policy_id := _load(POLICY_PATH)["policy_id"],
            {row["id"] for row in candidate["policies"]},
        )
        self.assertEqual(
            "urn:linzecolin:agentdatabase:skillops:policy:version:v3",
            policy_id,
        )
        self.assertTrue(interface["control_interface"]["unchanged"])
        self.assertEqual(
            "8caf7e5dbb922714c3afa39040e55b8a83015ea0f02de153e19cc3010b0e0e1a",
            interface["control_interface"]["artifact_digest"],
        )
        self.assertTrue(CONTROL_INTERFACE_PATH.is_file())

    def test_interface_keeps_every_write_and_activation_gate_closed(self):
        interface = _load(INTERFACE_PATH)
        self.assertEqual(
            "DRAFT_NON_ACTIVE_CONSUMER_FIRST_REQUIRED",
            interface["status"],
        )
        self.assertFalse(interface["release_write_permitted"])
        self.assertFalse(
            interface["canonical_publication_permitted"]
        )
        self.assertTrue(interface["activation_forbidden"])
        self.assertFalse(
            interface["promotion_to_candidate_performed"]
        )
        self.assertFalse(interface["version_file_created"])
        self.assertFalse(
            interface["compatibility"]["consumer_first_verified"]
        )
        self.assertFalse(
            interface["compatibility"][
                "candidate_materialization_permitted"
            ]
        )
        self.assertFalse(
            (ROOT / "CodexSkills" / "VERSION").exists()
        )
        self.assertEqual(interface["digest_algorithm"], "SHA-256")
        self.assertEqual(
            interface["self_digest_pointer"],
            "/artifact_digest",
        )
        self.assertEqual(
            interface["canonicalization"],
            {
                "duplicate_keys": "REJECT",
                "encoding": "UTF-8",
                "input_profile": "I_JSON",
                "scheme": "RFC8785_JCS",
                "self_digest_exclusion": (
                    "EXACT_DECLARED_JSON_POINTER_ONLY"
                ),
                "unicode_normalization": "NONE",
            },
        )
        self.assertEqual(
            interface["draft_trust_contract"],
            {
                "canonical_path": (
                    "CodexSkills/governance/release/"
                    "version_policy_v3/draft-interface.json"
                ),
                "expected_mode": (
                    "DRAFT_NON_ACTIVE_VERSION_POLICY"
                ),
                "external_expected_raw_sha256_required": True,
                "external_verified_git_object_required": True,
                "repository_self_report_is_not_trust_root": True,
            },
        )


if __name__ == "__main__":
    unittest.main()
