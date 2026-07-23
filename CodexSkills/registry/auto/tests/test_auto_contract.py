from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
AUTO_DIR = REPO_ROOT / "CodexSkills" / "registry" / "auto"
GOVERNANCE_TOOLS = REPO_ROOT / "CodexSkills" / "governance" / "tools"
AUTO_TOOLS = AUTO_DIR / "tools"
sys.path.insert(0, str(GOVERNANCE_TOOLS))
sys.path.insert(0, str(AUTO_TOOLS))

from canonical_json import canonical_digest  # noqa: E402
from validate_auto import (  # noqa: E402
    BASELINE_BREAKDOWN,
    BASELINE_UNMAPPED,
    PRIVATE_SELF_POINTERS,
    PUBLIC_SELF_POINTERS,
    ContractError,
    load_auto_contract,
    scan_public_value,
    validate_auto_instance,
)


PROTOCOL = "urn:linzecolin:agentdatabase:skillops:protocol:cross-pack:v1"
SCHEMA_PREFIX = "urn:linzecolin:agentdatabase:skillops:schema:"
BUNDLE = "a" * 64
DIGEST = "b" * 64
SECOND_DIGEST = "c" * 64
GIT_HEAD = "sha1:" + "d" * 40
T0 = "2026-07-23T00:00:00.000000Z"
T1 = "2026-07-23T00:01:00.000000Z"
T2 = "2026-07-23T00:02:00.000000Z"


def uid(prefix: str, discriminator: str = "0") -> str:
    return f"{prefix}_{discriminator}{'0' * 25}"


def schema_id(name: str, version: int) -> str:
    return f"{SCHEMA_PREFIX}{name}:v{version}"


def seal(instance: dict, pointer: str) -> dict:
    result = copy.deepcopy(instance)
    field = pointer[1:]
    result[field] = "0" * 64
    result[field] = canonical_digest(result, pointer)
    return result


def base(schema: str, digest_field: str) -> dict:
    return {
        "schema_version": schema,
        "protocol_revision": PROTOCOL,
        "bundle_digest": BUNDLE,
        digest_field: "0" * 64,
    }


def source_inventory() -> dict:
    value = {
        **base(schema_id("source-inventory", 1), "inventory_digest"),
        "inventory_uid": uid("sinv"),
        "source_class": "CODEX",
        "source_root_ref": "codex-skills-root",
        "observed_started_at": T0,
        "observed_finished_at": T1,
        "adapter_id": "skill-source-adapter",
        "adapter_version": "1.0.0",
        "adapter_schema_digest": DIGEST,
        "source_material_policy_id": (
            "urn:linzecolin:agentdatabase:skillops:policy:source-material:v1"
        ),
        "source_material_policy_digest": SECOND_DIGEST,
        "completeness_status": "COMPLETE_AFTER_POLICY_EXCLUSIONS",
        "included_file_count": 1,
        "included_bytes": 128,
        "included_tree_digest": DIGEST,
        "excluded_node_count": 0,
        "excluded_file_count": 0,
        "excluded_bytes": 0,
        "exclusions": [],
        "symlink_alias_count": 0,
        "symlink_aliases": [],
        "oversize_blocked_count": 0,
        "scan_error_counts": [],
    }
    return seal(value, "/inventory_digest")


def run_event(*, bound: bool = False, correction: bool = False) -> dict:
    value = {
        **base(schema_id("public-run-event", 2), "event_digest"),
        "event_uid": uid("evt", "1"),
        "run_uid": uid("run"),
        "event_type": "BINDING_CORRECTION" if correction else "RUN_OBSERVED",
        "occurred_at": T1,
        "surface_class": "CODEX_CLI" if bound else "CODEX_AUTOMATION",
        "actor_role": "CLI" if bound else "AUTOMATION",
        "adapter_id": "run-observer-adapter",
        "adapter_version": "2.0.0",
        "adapter_schema_digest": DIGEST,
        "mapping_policy_id": (
            "urn:linzecolin:agentdatabase:skillops:policy:run-mapping:v1"
        ),
        "mapping_policy_digest": SECOND_DIGEST,
        "trigger_kind": "MANUAL",
        "run_status": "SUCCESS",
        "model_ref": "gpt-5-6-sol",
        "reasoning_effort": "ULTRA",
        "metrics": {
            "duration_ms": 1000,
            "tool_call_count": 2,
            "input_tokens": None,
            "output_tokens": None,
            "token_usage_status": "UNAVAILABLE",
        },
        "binding_state": "BOUND" if bound else "UNKNOWN",
        "redaction": {
            "policy_snapshot_digest": DIGEST,
            "unknown_fields_dropped": 0,
            "omitted_category_codes": [],
            "post_serialization_scan_passed": True,
        },
        "immutable": True,
    }
    if bound:
        value["skill_ref"] = {
            "skill_identity_uid": uid("ski"),
            "skill_instance_uid": uid("skinst"),
            "skill_version_uid": uid("skv"),
            "content_digest": DIGEST,
            "tree_digest": SECOND_DIGEST,
            "version_record_digest": DIGEST,
            "registry_snapshot_digest": SECOND_DIGEST,
        }
        value["controlled_invocation"] = {
            "invocation_uid": uid("inv"),
            "invocation_envelope_digest": DIGEST,
            "surface_class": "CODEX_CLI",
            "observed_at": T1,
            "evidence_type": "CONTROLLED_INVOCATION_EXACT_VERSION",
        }
    else:
        value["unknown_reason_code"] = "MAPPING_NOT_PROVABLE"
    if correction:
        value["supersedes_event_uid"] = uid("evt", "2")
        value["supersedes_event_digest"] = SECOND_DIGEST
    return seal(value, "/event_digest")


def run_coverage_baseline() -> dict:
    value = {
        **base(schema_id("source-coverage-receipt", 1), "receipt_digest"),
        "receipt_uid": uid("cov"),
        "coverage_subject": "RUN_SURFACE",
        "coverage_state": "UNKNOWN",
        "adapter_scope": "codex-run-stores",
        "adapter_id": "codex-run-adapter",
        "adapter_version": "1.0.0",
        "adapter_schema_digest": DIGEST,
        "observation_window_started_at": T0,
        "observation_window_finished_at": T1,
        "heartbeat_at": T2,
        "reason_codes": ["BASELINE_ONLY", "UNMAPPED_RECORDS"],
        "mapping_policy_id": (
            "urn:linzecolin:agentdatabase:skillops:policy:run-mapping:v1"
        ),
        "mapping_policy_digest": SECOND_DIGEST,
        "input_record_count": 577,
        "mapped_input_record_count": 559,
        "unmapped_record_count": 18,
        "policy_excluded_record_count": 0,
        "quarantined_input_record_count": 0,
        "observed_run_count": 0,
        "projected_bound_run_count": 0,
        "projected_unknown_run_count": 0,
        "quarantined_run_count": 0,
        "projected_event_count": 0,
        "surface_breakdown": [
            {"surface_class": surface, "actor_role": role, "count": count}
            for surface, role, count in BASELINE_BREAKDOWN
        ],
        "unmapped_reasons": [
            {"reason_code": reason, "count": count}
            for reason, count in BASELINE_UNMAPPED
        ],
        "baseline_action_code": "BASELINE_ESTABLISHED_NO_HISTORICAL_BACKFILL",
        "cutover_at": T2,
        "public_safe_watermark_ref": "initial-codex-watermark",
        "historical_public_run_event_count": 0,
    }
    return seal(value, "/receipt_digest")


def skill_source_coverage() -> dict:
    value = {
        **base(schema_id("source-coverage-receipt", 1), "receipt_digest"),
        "receipt_uid": uid("cov", "1"),
        "coverage_subject": "SKILL_SOURCE",
        "coverage_state": "COVERED",
        "adapter_scope": "codex-skill-sources",
        "adapter_id": "skill-source-adapter",
        "adapter_version": "1.0.0",
        "adapter_schema_digest": DIGEST,
        "observation_window_started_at": T0,
        "observation_window_finished_at": T1,
        "heartbeat_at": T2,
        "reason_codes": [],
        "source_class": "CODEX",
        "inventory_uid": uid("sinv"),
        "inventory_digest": SECOND_DIGEST,
        "inventory_completeness_status": "COMPLETE_AFTER_POLICY_EXCLUSIONS",
        "source_material_policy_id": (
            "urn:linzecolin:agentdatabase:skillops:policy:source-material:v1"
        ),
        "source_material_policy_digest": DIGEST,
    }
    return seal(value, "/receipt_digest")


def auto_receipt() -> dict:
    value = {
        **base(schema_id("auto-receipt", 2), "receipt_digest"),
        "receipt_uid": uid("ar"),
        "auto_transaction_uid": uid("atx"),
        "trigger_kind": "MANUAL",
        "started_at": T0,
        "finished_at": T2,
        "execution_profile": {
            "model_ref": "gpt-5-6-sol",
            "reasoning_effort": "ULTRA",
        },
        "final_action": "PUBLISH",
        "overall_status": "SUCCESS",
        "settled_lanes": ["REGISTRY", "RUN_LOG"],
        "lane_results": [
            {
                "lane": "REGISTRY",
                "status": "SETTLED",
                "input_count": 1,
                "published_count": 1,
                "quarantined_count": 0,
            },
            {
                "lane": "RUN_LOG",
                "status": "SETTLED",
                "input_count": 1,
                "published_count": 1,
                "quarantined_count": 0,
            },
        ],
        "publication": {
            "manifest_digest": DIGEST,
            "observed_remote_head": GIT_HEAD,
        },
        "reason_codes": [],
    }
    return seal(value, "/receipt_digest")


def publication_manifest() -> dict:
    value = {
        **base(schema_id("publication-manifest", 1), "manifest_digest"),
        "manifest_uid": uid("pub"),
        "auto_transaction_uid": uid("atx"),
        "trigger_kind": "SCHEDULED",
        "created_at": T1,
        "mechanism_srv_revision": "v0.0.0.3",
        "expected_remote_head": GIT_HEAD,
        "settled_lanes": ["REGISTRY", "RUN_LOG"],
        "lane_manifests": [
            {
                "lane": "REGISTRY",
                "lane_transaction_uid": uid("ltx"),
                "source_watermark_ref": "registry-watermark",
                "artifact_count": 1,
                "artifacts": [
                    {
                        "artifact_uid": uid("spp"),
                        "artifact_schema_id": schema_id("skill-passport", 1),
                        "artifact_digest": DIGEST,
                        "artifact_repo_path": "CodexSkills/registry/passports/example.json",
                    }
                ],
            },
            {
                "lane": "RUN_LOG",
                "lane_transaction_uid": uid("ltx", "1"),
                "source_watermark_ref": "run-log-watermark",
                "artifact_count": 1,
                "artifacts": [
                    {
                        "artifact_uid": uid("evt"),
                        "artifact_schema_id": schema_id("public-run-event", 2),
                        "artifact_digest": SECOND_DIGEST,
                        "artifact_repo_path": (
                            "OpenAIDatabase/data/run_logs/skills_runs/example.json"
                        ),
                    }
                ],
            },
        ],
        "shared_gates": [
            {"gate_code": code, "status": "PASS", "evidence_digest": DIGEST}
            for code in (
                "BUNDLE_DIGEST",
                "EXPECTED_REMOTE_HEAD",
                "LOCK_OWNERSHIP",
                "PATH_BOUNDARY",
                "POLICY_DIGEST",
                "PRIVACY",
            )
        ],
    }
    return seal(value, "/manifest_digest")


def notification_receipt() -> dict:
    value = {
        **base(schema_id("notification-receipt", 3), "receipt_digest"),
        "receipt_uid": uid("nrc"),
        "notification_uid": uid("ntf"),
        "auto_transaction_uid": uid("atx"),
        "impact": "ROUTINE",
        "notification_mode": "AUTOMATIC_NOTIFICATION_ONLY",
        "timing": "NOT_REQUIRED",
        "provider_code": "NONE",
        "provider_status": "NOT_REQUIRED",
        "recipient_ref": "owner-private-recipient",
        "notification_policy_id": (
            "urn:linzecolin:agentdatabase:skillops:policy:notification:v1"
        ),
        "policy_snapshot_digest": DIGEST,
        "metadata_digest": SECOND_DIGEST,
        "created_at": T1,
        "approval_required": False,
        "owner_reply_required": False,
    }
    return seal(value, "/receipt_digest")


def retention_receipt() -> dict:
    value = {
        **base(schema_id("retention-receipt", 2), "receipt_digest"),
        "receipt_uid": uid("rtr"),
        "retention_action_uid": uid("rta"),
        "auto_transaction_uid": uid("atx"),
        "executed_at": T2,
        "cutoff_at": T0,
        "clock_basis": "UTC_WALL_CLOCK",
        "scope": "GIT_CURRENT_TREE",
        "action": "NO_CANDIDATE",
        "retention_policy_id": (
            "urn:linzecolin:agentdatabase:skillops:policy:retention:v2"
        ),
        "policy_snapshot_digest": DIGEST,
        "selected_count": 0,
        "selected_bytes": 0,
        "affected_count": 0,
        "affected_bytes": 0,
        "protected_candidate_count": 0,
        "legacy_candidate_count": 0,
        "reprojection_status": "NOT_APPLICABLE",
        "offline_duration_seconds": 0,
        "ttl_breach": False,
        "history_rewrite_performed": False,
        "hard_delete_claimed": False,
        "evidence_digest": SECOND_DIGEST,
    }
    return seal(value, "/receipt_digest")


def migration_receipt() -> dict:
    value = {
        **base(schema_id("migration-receipt", 2), "receipt_digest"),
        "receipt_uid": uid("mgr"),
        "migration_uid": uid("mig"),
        "source_generation_uid": uid("gen"),
        "adapter_scope": "codex-run-stores",
        "adapter_id": "codex-run-adapter",
        "adapter_version": "1.0.0",
        "adapter_schema_digest": DIGEST,
        "mapping_policy_id": (
            "urn:linzecolin:agentdatabase:skillops:policy:run-mapping:v1"
        ),
        "mapping_policy_digest": SECOND_DIGEST,
        "baseline_action_code": "BASELINE_ESTABLISHED_NO_HISTORICAL_BACKFILL",
        "coverage_state": "UNKNOWN",
        "cutover_at": T2,
        "public_safe_watermark_ref": "initial-codex-watermark",
        "private_exact_cursor_stored": True,
        "input_record_count": 577,
        "mapped_input_record_count": 559,
        "unmapped_record_count": 18,
        "policy_excluded_record_count": 0,
        "quarantined_input_record_count": 0,
        "surface_breakdown": [
            {"surface_class": surface, "actor_role": role, "count": count}
            for surface, role, count in BASELINE_BREAKDOWN
        ],
        "unmapped_reasons": [
            {"reason_code": reason, "count": count}
            for reason, count in BASELINE_UNMAPPED
        ],
        "historical_public_run_event_count": 0,
        "legacy_local_mutation_performed": False,
        "evidence_digest": DIGEST,
    }
    return seal(value, "/receipt_digest")


def queue_envelope() -> dict:
    value = {
        **base(schema_id("public-queue-envelope", 2), "envelope_digest"),
        "envelope_uid": uid("env"),
        "auto_transaction_uid": uid("atx"),
        "lane": "RUN_LOG",
        "artifact_schema_id": schema_id("public-run-event", 2),
        "artifact_uid": uid("evt"),
        "artifact_digest": DIGEST,
        "artifact_repo_path": "OpenAIDatabase/data/run_logs/skills_runs/example.json",
        "queue_state": "READY",
        "sealed_at": T1,
        "retry_count": 0,
    }
    return seal(value, "/envelope_digest")


def watermark() -> dict:
    value = {
        **base(schema_id("watermark", 2), "state_digest"),
        "watermark_uid": uid("wm"),
        "updated_at": T2,
        "baseline_established": True,
        "lane_states": [
            {
                "lane": "REGISTRY",
                "source_generation_uid": uid("gen"),
                "cursor_token": "private-registry-cursor",
                "public_watermark_ref": "registry-watermark",
                "last_settled_manifest_digest": None,
                "last_settled_remote_head": None,
            },
            {
                "lane": "RUN_LOG",
                "source_generation_uid": uid("gen", "1"),
                "cursor_token": "private-run-log-cursor",
                "public_watermark_ref": "run-log-watermark",
                "last_settled_manifest_digest": None,
                "last_settled_remote_head": None,
            },
        ],
    }
    return seal(value, "/state_digest")


def lock_state() -> dict:
    value = {
        **base(schema_id("lock-state", 1), "state_digest"),
        "lock_uid": uid("lck"),
        "owner_run_uid": uid("run"),
        "generation": 1,
        "status": "HELD",
        "acquired_at": T0,
        "heartbeat_at": T1,
        "lease_expires_at": T2,
    }
    return seal(value, "/state_digest")


def raw_segment() -> dict:
    value = {
        **base(schema_id("raw-segment", 2), "segment_digest"),
        "segment_uid": uid("raw"),
        "source_generation_uid": uid("gen"),
        "adapter_id": "codex-run-adapter",
        "adapter_version": "1.0.0",
        "persistence_mode": "DISABLED",
        "managed_owned": True,
        "protected_or_legacy": False,
        "ownership_marker_digest": DIGEST,
        "payload_digest": SECOND_DIGEST,
        "record_count": 0,
        "byte_count": 0,
        "created_at": T0,
        "sealed_at": T1,
        "expires_at": T2,
    }
    return seal(value, "/segment_digest")


PUBLIC_FIXTURES = {
    schema_id("auto-receipt", 2): auto_receipt,
    schema_id("migration-receipt", 2): migration_receipt,
    schema_id("notification-receipt", 3): notification_receipt,
    schema_id("public-run-event", 2): run_event,
    schema_id("publication-manifest", 1): publication_manifest,
    schema_id("retention-receipt", 2): retention_receipt,
    schema_id("source-coverage-receipt", 1): skill_source_coverage,
    schema_id("source-inventory", 1): source_inventory,
}
PRIVATE_FIXTURES = {
    schema_id("lock-state", 1): lock_state,
    schema_id("public-queue-envelope", 2): queue_envelope,
    schema_id("raw-segment", 2): raw_segment,
    schema_id("watermark", 2): watermark,
}


class AutoContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = load_auto_contract()

    def assert_rejected(self, schema: str, value: dict, code: str) -> None:
        pointer = {**PUBLIC_SELF_POINTERS, **PRIVATE_SELF_POINTERS}[schema]
        candidate = seal(value, pointer)
        with self.assertRaisesRegex(ContractError, code):
            validate_auto_instance(
                self.contract,
                candidate,
                schema,
                expected_bundle_digest=BUNDLE,
            )

    def test_builder_is_byte_equivalent(self) -> None:
        environment = dict(os.environ)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        process = subprocess.run(
            [
                "/usr/bin/python3",
                "-B",
                str(AUTO_TOOLS / "build_schemas.py"),
                "--check",
            ],
            cwd=REPO_ROOT,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertIn("AUTO_DRAFT_BYTE_EQUIVALENT", process.stdout)

    def test_exact_schema_ownership_and_offline_registry(self) -> None:
        self.assertEqual(set(PUBLIC_SELF_POINTERS), set(PUBLIC_FIXTURES))
        self.assertEqual(set(PRIVATE_SELF_POINTERS), set(PRIVATE_FIXTURES))
        self.assertEqual(len(self.contract.shared.schemas), 29)
        self.assertEqual(len(self.contract.development.schemas), 33)
        self.assertTrue(set(PRIVATE_SELF_POINTERS).isdisjoint(self.contract.shared.schemas))
        self.assertTrue(set(PRIVATE_SELF_POINTERS).issubset(self.contract.development.schemas))
        self.assertFalse(self.contract.interface["auto_private_schemas_in_shared_bundle"])

    def test_every_object_is_closed_and_refs_are_offline_urns(self) -> None:
        forbidden = {
            "$anchor",
            "$dynamicAnchor",
            "$dynamicRef",
            "$recursiveAnchor",
            "$recursiveRef",
        }
        for schema_id_value in sorted(
            {**PUBLIC_SELF_POINTERS, **PRIVATE_SELF_POINTERS}
        ):
            schema = self.contract.development.schemas[schema_id_value]
            stack = [schema]
            while stack:
                node = stack.pop()
                if isinstance(node, dict):
                    self.assertFalse(forbidden.intersection(node), schema_id_value)
                    if node.get("type") == "object":
                        self.assertIs(node.get("additionalProperties"), False, schema_id_value)
                    if node.get("type") == "string":
                        self.assertTrue(
                            any(
                                key in node
                                for key in (
                                    "$ref",
                                    "const",
                                    "enum",
                                    "format",
                                    "maxLength",
                                    "pattern",
                                )
                            ),
                            f"unbounded string in {schema_id_value}: {node}",
                        )
                    reference = node.get("$ref")
                    if reference is not None:
                        self.assertTrue(reference.startswith("urn:linzecolin:"), reference)
                    stack.extend(node.values())
                elif isinstance(node, list):
                    stack.extend(node)

    def test_all_public_and_private_fixtures_validate(self) -> None:
        for schema, factory in {**PUBLIC_FIXTURES, **PRIVATE_FIXTURES}.items():
            with self.subTest(schema=schema):
                validate_auto_instance(
                    self.contract,
                    factory(),
                    schema,
                    expected_bundle_digest=BUNDLE,
                )
        validate_auto_instance(
            self.contract,
            run_coverage_baseline(),
            schema_id("source-coverage-receipt", 1),
            expected_bundle_digest=BUNDLE,
        )
        validate_auto_instance(
            self.contract,
            run_event(bound=True),
            schema_id("public-run-event", 2),
            expected_bundle_digest=BUNDLE,
        )
        validate_auto_instance(
            self.contract,
            run_event(correction=True),
            schema_id("public-run-event", 2),
            expected_bundle_digest=BUNDLE,
        )

    def test_public_digest_field_contract_and_negative_scanner(self) -> None:
        policy = self.contract.shared.policies
        for field in (
            "adapter_schema_digest",
            "included_tree_digest",
            "mapping_policy_digest",
            "supersedes_event_digest",
        ):
            scan_public_value({field: DIGEST}, policy)
            with self.assertRaisesRegex(
                ContractError, "PUBLIC_APPROVED_DIGEST_MALFORMED"
            ):
                scan_public_value({field: "not-a-sha256"}, policy)
        with self.assertRaisesRegex(
            ContractError, "PUBLIC_HIGH_ENTROPY_FREE_STRING_BLOCK"
        ):
            scan_public_value({"generic_digest": DIGEST}, policy)

    def test_public_privacy_negative_values(self) -> None:
        policy = self.contract.shared.policies
        for value, code in (
            ({"recipient_ref": "owner@example.invalid"}, "PUBLIC_EMAIL_BLOCK"),
            ({"source_root_ref": "/Users/example/private"}, "PUBLIC_ABSOLUTE_PATH_BLOCK"),
            ({"raw": "opaque"}, "PUBLIC_FORBIDDEN_FIELD"),
        ):
            with self.subTest(code=code):
                with self.assertRaisesRegex(ContractError, code):
                    scan_public_value(value, policy)

    def test_run_binding_and_immutable_correction(self) -> None:
        schema = schema_id("public-run-event", 2)
        unknown = run_event()
        unknown["skill_ref"] = run_event(bound=True)["skill_ref"]
        self.assert_rejected(schema, unknown, "SCHEMA_VALIDATION_FAILED")

        bound = run_event(bound=True)
        del bound["controlled_invocation"]
        self.assert_rejected(schema, bound, "SCHEMA_VALIDATION_FAILED")

        actor_mismatch = run_event()
        actor_mismatch["actor_role"] = "USER"
        self.assert_rejected(schema, actor_mismatch, "SCHEMA_VALIDATION_FAILED")

        eval_linkage = run_event()
        eval_linkage["eval_refs"] = []
        self.assert_rejected(schema, eval_linkage, "SCHEMA_VALIDATION_FAILED")

        correction = run_event(correction=True)
        correction["supersedes_event_uid"] = correction["event_uid"]
        self.assert_rejected(schema, correction, "RUN_EVENT_CANNOT_SUPERSEDE_SELF")

    def test_no_time_window_and_manual_scheduled_share_contract(self) -> None:
        schema = schema_id("public-run-event", 2)
        manual = run_event()
        scheduled = run_event()
        scheduled["trigger_kind"] = "SCHEDULED"
        scheduled = seal(scheduled, "/event_digest")
        for value in (manual, scheduled):
            validate_auto_instance(
                self.contract,
                value,
                schema,
                expected_bundle_digest=BUNDLE,
            )
        serialized = json.dumps(self.contract.development.schemas)
        self.assertNotIn("MISSED_WINDOW", serialized)
        self.assertNotIn("late_window", serialized)
        self.assertNotIn("UNKNOWN_LEGACY", serialized)
        version_policy = self.contract.shared.policies[
            "urn:linzecolin:agentdatabase:skillops:policy:version:v2"
        ]
        self.assertEqual(version_policy["timezone"], "Australia/Sydney")
        self.assertEqual(version_policy["daily_schedule_local"], "04:15")
        self.assertTrue(version_policy["sunday_forced_full"])
        self.assertTrue(version_policy["manual_uses_same_orchestrator"])
        self.assertFalse(version_policy["late_start_rejected"])

    def test_strict_utc_context_and_self_digest(self) -> None:
        schema = schema_id("public-run-event", 2)
        offset = run_event()
        offset["occurred_at"] = "2026-07-23T10:01:00.000000+10:00"
        self.assert_rejected(schema, offset, "SCHEMA_VALIDATION_FAILED")

        mismatch = run_event()
        mismatch["bundle_digest"] = SECOND_DIGEST
        mismatch = seal(mismatch, "/event_digest")
        with self.assertRaisesRegex(ContractError, "CONTEXT_BUNDLE_DIGEST_MISMATCH"):
            validate_auto_instance(
                self.contract,
                mismatch,
                schema,
                expected_bundle_digest=BUNDLE,
            )

        tampered = run_event()
        tampered["run_status"] = "FAILED"
        with self.assertRaisesRegex(ContractError, "SELF_DIGEST_MISMATCH"):
            validate_auto_instance(
                self.contract,
                tampered,
                schema,
                expected_bundle_digest=BUNDLE,
            )

    def test_baseline_is_exact_and_never_backfills_events(self) -> None:
        schema = schema_id("source-coverage-receipt", 1)
        baseline = run_coverage_baseline()
        self.assertEqual(baseline["historical_public_run_event_count"], 0)
        self.assertEqual(
            baseline["input_record_count"],
            baseline["mapped_input_record_count"] + baseline["unmapped_record_count"],
        )
        broken = copy.deepcopy(baseline)
        broken["mapped_input_record_count"] = 558
        self.assert_rejected(schema, broken, "COVERAGE_INPUT_RECONCILIATION_MISMATCH")

        migration_schema = schema_id("migration-receipt", 2)
        historical = migration_receipt()
        historical["historical_public_run_event_count"] = 1
        self.assert_rejected(migration_schema, historical, "SCHEMA_VALIDATION_FAILED")

    def test_coverage_reconciliation_and_lane_isolation(self) -> None:
        coverage_schema = schema_id("source-coverage-receipt", 1)
        covered = run_coverage_baseline()
        covered.pop("baseline_action_code")
        covered.pop("cutover_at")
        covered.pop("public_safe_watermark_ref")
        covered.pop("historical_public_run_event_count")
        covered["coverage_state"] = "COVERED"
        self.assert_rejected(
            coverage_schema, covered, "COVERAGE_COVERED_WITH_UNSETTLED_RECORDS"
        )

        receipt_schema = schema_id("auto-receipt", 2)
        partial = auto_receipt()
        partial["overall_status"] = "PARTIAL"
        partial["settled_lanes"] = ["REGISTRY"]
        partial["lane_results"][1].update(
            status="QUARANTINED", published_count=0, quarantined_count=1
        )
        partial = seal(partial, "/receipt_digest")
        validate_auto_instance(
            self.contract,
            partial,
            receipt_schema,
            expected_bundle_digest=BUNDLE,
        )

        registry_only = auto_receipt()
        registry_only["settled_lanes"] = ["REGISTRY"]
        registry_only["lane_results"][1].update(
            status="NO_CHANGE", input_count=0, published_count=0, quarantined_count=0
        )
        registry_only = seal(registry_only, "/receipt_digest")
        validate_auto_instance(
            self.contract,
            registry_only,
            receipt_schema,
            expected_bundle_digest=BUNDLE,
        )

        partial_inventory = skill_source_coverage()
        partial_inventory["coverage_state"] = "UNKNOWN"
        partial_inventory["reason_codes"] = ["INVENTORY_INCOMPLETE"]
        del partial_inventory["inventory_uid"]
        self.assert_rejected(
            coverage_schema, partial_inventory, "COVERAGE_INVENTORY_REFERENCE_PARTIAL"
        )

    def test_publication_gates_and_artifact_counts(self) -> None:
        schema = schema_id("publication-manifest", 1)
        missing_gate = publication_manifest()
        missing_gate["shared_gates"].pop()
        self.assert_rejected(schema, missing_gate, "SCHEMA_VALIDATION_FAILED")

        wrong_count = publication_manifest()
        wrong_count["lane_manifests"][0]["artifact_count"] = 2
        self.assert_rejected(schema, wrong_count, "PUBLICATION_ARTIFACT_COUNT_MISMATCH")

        outside_root = publication_manifest()
        outside_root["lane_manifests"][1]["artifacts"][0]["artifact_repo_path"] = (
            "OpenAIDatabase/data/run_logs/agent_runs/example.json"
        )
        self.assert_rejected(schema, outside_root, "PUBLICATION_RUN_LOG_PATH_INVALID")

        private_schema = publication_manifest()
        private_schema["lane_manifests"][0]["artifacts"][0]["artifact_schema_id"] = (
            schema_id("watermark", 2)
        )
        self.assert_rejected(
            schema, private_schema, "PUBLICATION_ARTIFACT_SCHEMA_NOT_IN_SHARED_BUNDLE"
        )

    def test_notification_and_retention_truthfulness(self) -> None:
        notification_schema = schema_id("notification-receipt", 3)
        major = notification_receipt()
        major["impact"] = "MAJOR"
        self.assert_rejected(
            notification_schema, major, "NOTIFICATION_MAJOR_CANNOT_BE_NOT_REQUIRED"
        )

        failed_major = notification_receipt()
        failed_major.update(
            impact="MAJOR",
            timing="PRE_WRITE",
            provider_code="EMAIL_PROVIDER",
            provider_status="FAILED",
            failure_code="PROVIDER_TIMEOUT",
        )
        failed_major = seal(failed_major, "/receipt_digest")
        validate_auto_instance(
            self.contract,
            failed_major,
            notification_schema,
            expected_bundle_digest=BUNDLE,
        )

        sent_major = notification_receipt()
        sent_major.update(
            impact="MAJOR",
            timing="PRE_WRITE",
            provider_code="EMAIL_PROVIDER",
            provider_status="SENT",
            provider_receipt_ref="provider-receipt-safe",
            sent_at=T2,
        )
        sent_major = seal(sent_major, "/receipt_digest")
        validate_auto_instance(
            self.contract,
            sent_major,
            notification_schema,
            expected_bundle_digest=BUNDLE,
        )

        retention_schema = schema_id("retention-receipt", 2)
        false_breach = retention_receipt()
        false_breach["ttl_breach"] = True
        self.assert_rejected(
            retention_schema, false_breach, "RETENTION_TTL_BREACH_EVIDENCE_INCOMPLETE"
        )

    def test_private_state_fail_closed(self) -> None:
        raw_schema = schema_id("raw-segment", 2)
        persisted = raw_segment()
        persisted["record_count"] = 1
        persisted["byte_count"] = 10
        self.assert_rejected(raw_schema, persisted, "RAW_DISABLED_WITH_PERSISTED_CONTENT")

        lock_schema = schema_id("lock-state", 1)
        released = lock_state()
        released["status"] = "RELEASED"
        self.assert_rejected(lock_schema, released, "LOCK_RELEASE_TIME_REQUIRED")

        watermark_schema = schema_id("watermark", 2)
        partial = watermark()
        partial["lane_states"][0]["last_settled_manifest_digest"] = DIGEST
        self.assert_rejected(
            watermark_schema, partial, "WATERMARK_SETTLEMENT_EVIDENCE_PARTIAL"
        )


if __name__ == "__main__":
    unittest.main()
