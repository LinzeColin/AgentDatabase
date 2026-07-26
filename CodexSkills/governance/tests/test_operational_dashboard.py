"""Regression gates for Mechanism M-067 dashboards and actionable alerts."""

from __future__ import annotations

import copy
import hashlib
import inspect
import unittest
from unittest import mock

from CodexSkills.governance.monitoring import operational_dashboard as policy
from CodexSkills.governance.monitoring.operational_dashboard import (
    OperationalDashboardError,
    build_dashboard,
    validate_dashboard,
)
from CodexSkills.governance.tools import build_operational_dashboard as builder
from CodexSkills.governance.tools.canonical_json import (
    canonical_digest,
    parse_json_bytes,
)
from CodexSkills.governance.tools.validate_mechanism import (
    scan_public_value,
    validate_instance,
)


class OperationalDashboardTests(unittest.TestCase):
    """Every derived alert must retain owner, action, and evidence."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.documents = builder._documents()
        cls.dashboard = parse_json_bytes(
            cls.documents[builder.DASHBOARD_PATH]
        )
        cls.readiness = parse_json_bytes(
            cls.documents[builder.READINESS_PATH]
        )
        cls.sources, cls.links = builder._source_documents()

    def variant(self, code, changes):
        sources = copy.deepcopy(self.sources)
        links = copy.deepcopy(self.links)
        target = sources[code]
        changes(target)
        target["artifact_digest"] = canonical_digest(
            target,
            policy.SELF_POINTER,
        )
        for link in links:
            if link["evidence_code"] == code:
                link["artifact_digest"] = target["artifact_digest"]
                link["status"] = target["status"]
        return sources, links

    def test_01_builder_is_byte_equivalent_and_sources_are_exact(self):
        builder._check()
        sources, links = builder._source_documents()
        self.assertEqual(set(sources), set(policy.SOURCE_CODES))
        self.assertEqual(
            [item["evidence_code"] for item in links],
            list(policy.SOURCE_CODES),
        )
        self.assertEqual(
            self.readiness["task_contract"]["implemented_task_ids"],
            ["M-067"],
        )
        self.assertEqual(
            self.readiness["next_phase"],
            "MECHANISM_THREE_REPRESENTATIVE_PILOTS",
        )
        self.assertEqual(self.readiness["schema_closure_count"], 37)

    def test_02_dashboard_has_all_five_views_and_current_truth(self):
        self.assertEqual(
            [view["view_code"] for view in self.dashboard["views"]],
            list(policy.VIEW_CODES),
        )
        states = {
            view["view_code"]: view["status"]
            for view in self.dashboard["views"]
        }
        self.assertEqual(
            states,
            {
                "HEALTH": "CRITICAL",
                "PRIVACY": "CRITICAL",
                "FRESHNESS": "WARNING",
                "RETENTION": "CRITICAL",
                "CAPACITY": "WARNING",
            },
        )
        self.assertEqual(
            self.dashboard["summary"]["alert_count"],
            4,
        )
        self.assertEqual(
            self.dashboard["summary"]["critical_count"],
            2,
        )
        self.assertEqual(
            self.dashboard["summary"]["warning_count"],
            2,
        )
        self.assertFalse(
            self.dashboard["summary"]["production_dashboard_ready"]
        )

    def test_03_every_alert_has_owner_action_and_evidence_link(self):
        evidence_codes = {
            item["evidence_code"]
            for item in self.dashboard["source_evidence"]
        }
        for alert in self.dashboard["alerts"]:
            with self.subTest(alert=alert["alert_uid"]):
                self.assertIn(alert["owner"], policy.OWNERS)
                self.assertIn(alert["action_code"], policy.ACTIONS)
                self.assertTrue(alert["evidence_link_codes"])
                self.assertTrue(
                    set(alert["evidence_link_codes"]).issubset(
                        evidence_codes
                    )
                )

    def test_04_alert_and_dashboard_digests_recompute(self):
        for alert in self.dashboard["alerts"]:
            self.assertEqual(
                alert["artifact_digest"],
                canonical_digest(alert, policy.SELF_POINTER),
            )
        self.assertEqual(
            self.dashboard["artifact_digest"],
            canonical_digest(self.dashboard, policy.SELF_POINTER),
        )
        validate_dashboard(self.dashboard, self.sources, self.links)

    def test_05_markdown_links_every_actionable_alert(self):
        markdown = self.documents[builder.MARKDOWN_PATH].decode("utf-8")
        for alert in self.dashboard["alerts"]:
            self.assertIn(alert["action_code"], markdown)
            self.assertIn(alert["owner"], markdown)
            for code in alert["evidence_link_codes"]:
                self.assertIn("[" + code + "](", markdown)
        self.assertIn(
            "accountable owner, one fixed action code",
            markdown,
        )

    def test_06_caller_cannot_change_owner_or_action(self):
        for field, value in (
            ("owner", "MECHANISM"),
            (
                "action_code",
                "CAPTURE_REAL_COLD_WARM_CAPACITY_BASELINES",
            ),
        ):
            altered = copy.deepcopy(self.dashboard)
            altered["alerts"][1][field] = value
            altered["alerts"][1]["artifact_digest"] = canonical_digest(
                altered["alerts"][1],
                policy.SELF_POINTER,
            )
            altered["artifact_digest"] = canonical_digest(
                altered,
                policy.SELF_POINTER,
            )
            with self.assertRaisesRegex(
                OperationalDashboardError,
                "DASHBOARD_DERIVATION_MISMATCH",
            ):
                validate_dashboard(altered, self.sources, self.links)

    def test_07_caller_cannot_remove_evidence_and_rehash(self):
        altered = copy.deepcopy(self.dashboard)
        altered["alerts"][0]["evidence_link_codes"] = []
        altered["alerts"][0]["artifact_digest"] = canonical_digest(
            altered["alerts"][0],
            policy.SELF_POINTER,
        )
        altered["artifact_digest"] = canonical_digest(
            altered,
            policy.SELF_POINTER,
        )
        with self.assertRaisesRegex(
            OperationalDashboardError,
            "DASHBOARD_DERIVATION_MISMATCH",
        ):
            validate_dashboard(altered, self.sources, self.links)

    def test_08_missing_or_reordered_source_evidence_fails_closed(self):
        with self.assertRaisesRegex(
            OperationalDashboardError,
            "DASHBOARD_SOURCE_SET_INCOMPLETE",
        ):
            build_dashboard(
                {
                    key: value
                    for key, value in self.sources.items()
                    if key != "CAPACITY"
                },
                self.links,
            )
        reordered = list(reversed(self.links))
        with self.assertRaisesRegex(
            OperationalDashboardError,
            "DASHBOARD_EVIDENCE_ORDER_OR_SET_INVALID",
        ):
            build_dashboard(self.sources, reordered)

    def test_09_source_self_digest_and_git_raw_drift_fail_closed(self):
        altered = copy.deepcopy(self.sources)
        altered["CAPACITY"]["artifact_digest"] = "a" * 64
        with self.assertRaisesRegex(
            OperationalDashboardError,
            "DASHBOARD_SOURCE_SELF_DIGEST_MISMATCH",
        ):
            build_dashboard(altered, self.links)
        original = builder._git_blob

        def drift(object_id, relative_path):
            raw = original(object_id, relative_path)
            if relative_path == builder.SOURCE_CONTRACTS[
                "CAPACITY"
            ]["canonical_path"]:
                return raw + b" "
            return raw

        with mock.patch.object(builder, "_git_blob", side_effect=drift):
            with self.assertRaisesRegex(
                builder.OperationalDashboardBuildError,
                "M067_SOURCE_RAW_DRIFT:CAPACITY",
            ):
                builder._source_documents()

    def test_10_enabled_persistent_raw_is_a_mechanism_critical(self):
        sources, links = self.variant(
            "MANAGED_RAW",
            lambda value: value["managed_raw_policy_contract"].update(
                {"persistent_managed_raw_default_enabled": True}
            ),
        )
        dashboard = build_dashboard(sources, links)
        privacy = [
            item for item in dashboard["alerts"]
            if item["category"] == "PRIVACY"
        ][0]
        self.assertEqual(privacy["owner"], "MECHANISM")
        self.assertEqual(
            privacy["action_code"],
            "DISABLE_PERSISTENT_MANAGED_RAW_DEFAULT",
        )
        self.assertTrue(privacy["blocking"])

    def test_11_certified_managed_raw_clears_privacy_alert(self):
        def certify(value):
            value["managed_raw_policy_contract"].update(
                {
                    "production_certification_status": "GRANTED",
                    "real_execution_permitted": True,
                }
            )

        sources, links = self.variant("MANAGED_RAW", certify)
        dashboard = build_dashboard(sources, links)
        self.assertNotIn(
            "PRIVACY",
            [item["category"] for item in dashboard["alerts"]],
        )

    def test_12_monitor_execution_clears_freshness_alert(self):
        def ready(value):
            value["nonmutation"]["monitor_execution_permitted"] = True
            value["registry_observation"][
                "real_monitor_execution_permitted"
            ] = True

        sources, links = self.variant("FRESHNESS", ready)
        dashboard = build_dashboard(sources, links)
        self.assertNotIn(
            "FRESHNESS",
            [item["category"] for item in dashboard["alerts"]],
        )

    def test_13_bound_active_tree_clears_retention_alert(self):
        def ready(value):
            value["active_tree_contract"].update(
                {
                    "auto_executor_integration_status": "BOUND",
                    "real_execution_permitted": True,
                }
            )

        sources, links = self.variant("ACTIVE_TREE", ready)
        dashboard = build_dashboard(sources, links)
        self.assertNotIn(
            "RETENTION",
            [item["category"] for item in dashboard["alerts"]],
        )

    def test_14_real_cold_warm_profiles_clear_capacity_alert(self):
        def calibrate(value):
            value["calibration_state"].update(
                {
                    "state": "CALIBRATED",
                    "real_profile_count": 8,
                    "hardware_baseline_verified": True,
                    "cold_cache_baseline_verified": True,
                    "warm_cache_baseline_verified": True,
                    "ten_thousand_event_baseline_verified": True,
                    "production_sla_proven": True,
                }
            )

        sources, links = self.variant("CAPACITY", calibrate)
        dashboard = build_dashboard(sources, links)
        self.assertNotIn(
            "CAPACITY",
            [item["category"] for item in dashboard["alerts"]],
        )

    def test_15_schema_validation_is_offline_and_public_safe(self):
        base = builder._candidate_plus_performance()
        alert_schema = builder.build_alert_schema()
        dashboard_schema = builder.build_dashboard_schema()
        readiness_schema = builder.build_readiness_schema(self.readiness)
        contract = builder._extend_bundle(
            base,
            {
                policy.ALERT_SCHEMA_ID: alert_schema,
                policy.DASHBOARD_SCHEMA_ID: dashboard_schema,
                builder.READINESS_SCHEMA_ID: readiness_schema,
            },
            {
                policy.ALERT_SCHEMA_ID: policy.SELF_POINTER,
                policy.DASHBOARD_SCHEMA_ID: policy.SELF_POINTER,
                builder.READINESS_SCHEMA_ID: policy.SELF_POINTER,
            },
        )
        for instance, schema_id in (
            (self.dashboard, policy.DASHBOARD_SCHEMA_ID),
            (self.readiness, builder.READINESS_SCHEMA_ID),
        ):
            validate_instance(
                contract,
                instance,
                schema_id,
                expected_bundle_digest=policy.CANDIDATE_BUNDLE_DIGEST,
                verify_digest=True,
                public=True,
            )
            scan_public_value(instance, contract.policies)

    def test_16_readiness_does_not_claim_live_or_notification(self):
        current = self.readiness["current_projection"]
        self.assertFalse(current["production_dashboard_ready"])
        self.assertFalse(current["notification_sent"])
        nonmutation = self.readiness["nonmutation"]
        self.assertFalse(nonmutation["real_telemetry_collected"])
        self.assertFalse(nonmutation["notification_sent"])
        self.assertFalse(nonmutation["state_write_permitted"])
        self.assertFalse(nonmutation["canonical_publication_permitted"])

    def test_17_guard_has_no_runtime_or_side_effect_capability(self):
        source = inspect.getsource(policy)
        for forbidden in (
            "from pathlib",
            "import os",
            "import subprocess",
            "import socket",
            "import time",
            "Path(",
            "open(",
            "write_bytes(",
            "send(",
            "requests.",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)

    def test_18_handoff_binds_exact_m067_artifact_digests(self):
        handoff = (
            builder.GOVERNANCE_DIR / "HANDOFF.md"
        ).read_text(encoding="utf-8")
        expected = {
            builder.COMPONENT_PATH: (
                "d4cce58cacbd90e92fa02873d39c369a4a2a6c8007a64a14b56b79df97de68e5"
            ),
            builder.DASHBOARD_PATH: (
                "8eb694589f5fed6e98668839a7f5039829896d74edbb40df4c68e81b666d69e6"
            ),
            builder.MARKDOWN_PATH: (
                "c9f63222769e818cdede952699f039c5b98b0664c3b72bf728d7db574fef2a97"
            ),
            builder.READINESS_PATH: (
                "342359e4194346b0b41cd75fd14bda456f3ec85fc9d8a59656cfa18a51188f12"
            ),
            builder.ALERT_SCHEMA_PATH: (
                "5853c126c7697873f1dc54d81f49f5cb1cfebb5aed0583203cb5dfd4ba5cfadc"
            ),
            builder.DASHBOARD_SCHEMA_PATH: (
                "106755f3f0d1386604a6e82b7061441d1310068da589d46ed4f839a291ecf6e9"
            ),
            builder.READINESS_SCHEMA_PATH: (
                "eb3209bc9d5e15b605338b5e421c259deee36bfdad31b2197ec916504cc64a7c"
            ),
        }
        for path, digest in expected.items():
            with self.subTest(path=path):
                self.assertEqual(
                    hashlib.sha256(path.read_bytes()).hexdigest(),
                    digest,
                )
                self.assertIn(digest, handoff)
        self.assertIn(self.dashboard["artifact_digest"], handoff)
        self.assertIn(self.readiness["artifact_digest"], handoff)


if __name__ == "__main__":
    unittest.main()
