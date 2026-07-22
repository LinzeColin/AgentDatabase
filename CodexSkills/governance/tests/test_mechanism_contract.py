#!/usr/bin/env python3
"""Positive, negative, privacy, and determinism gates for Mechanism M0a."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, Mapping


GOVERNANCE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = GOVERNANCE_DIR.parents[1]
TOOLS_DIR = GOVERNANCE_DIR / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from canonical_json import (  # noqa: E402
    CanonicalizationError,
    canonical_digest,
    canonicalize_bytes,
    canonicalize_object,
    parse_json_bytes,
    verify_vendor,
)
from validate_mechanism import (  # noqa: E402
    CANONICAL_MANIFEST_PATH,
    CORE_HARD_GATE_CODES,
    ContractError,
    Draft202012Validator,
    EVAL_DIMENSION_CODES,
    SCHEMA_PREFIX,
    TrustTuple,
    Unresolvable,
    capability_gate,
    is_repo_relative_posix_path,
    lint_schema_documents,
    load_draft_contract,
    load_trusted_bundle,
    scan_public_value,
    strict_load,
    validate_instance,
)


PROTOCOL = "urn:linzecolin:agentdatabase:skillops:protocol:cross-pack:v1"
BUNDLE = "a" * 64
DIGEST_B = "b" * 64
DIGEST_C = "c" * 64
DIGEST_D = "d" * 64
ULID_0 = "0" * 26
ULID_1 = "0" * 25 + "1"
TS = "2026-07-23T00:00:00.000000Z"
SRV = "v0.0.0.3"
DIMENSIONS = sorted(EVAL_DIMENSION_CODES)
HARD_GATES = sorted(CORE_HARD_GATE_CODES)


def uid(prefix: str, suffix: str = ULID_0) -> str:
    return f"{prefix}_{suffix}"


def sid(name: str, version: int = 1) -> str:
    return f"{SCHEMA_PREFIX}{name}:v{version}"


def artifact(name: str, fields: Mapping[str, Any], version: int = 1) -> Dict[str, Any]:
    return {
        "schema_version": sid(name, version),
        "protocol_revision": PROTOCOL,
        "bundle_digest": BUNDLE,
        **fields,
    }


def finalize_self_digest(bundle: Any, schema_id: str, value: Dict[str, Any]) -> Dict[str, Any]:
    pointer = bundle.self_digest_pointers[schema_id]
    if pointer:
        field = pointer[1:]
        value[field] = "0" * 64
        value[field] = canonical_digest(value, pointer)
    return value


def permissions() -> Dict[str, Any]:
    return {
        "external_side_effect": "NONE",
        "filesystem_write": "WORKSPACE_ONLY",
        "network": "NONE",
        "secrets": "NONE",
    }


def representative_artifacts(bundle: Any, interface: Mapping[str, Any]) -> Dict[str, Dict[str, Any]]:
    identity = artifact(
        "skill-identity",
        {
            "skill_identity_uid": uid("ski"),
            "srv_revision": SRV,
            "canonical_name": "fixture-skill",
            "summary": "Deterministic Mechanism fixture.",
            "owner_ref": "owner-primary",
            "lifecycle_status": "REGISTERED",
            "capability_codes": ["FIXTURE_CAPABILITY"],
            "applicability_manifest_digest": DIGEST_B,
            "input_contract_digest": DIGEST_C,
            "output_contract_digest": DIGEST_D,
            "instance_uids": [uid("skinst")],
            "created_at": TS,
            "updated_at": TS,
            "supersedes_identity_uid": None,
        },
    )
    instance = artifact(
        "skill-instance",
        {
            "skill_instance_uid": uid("skinst"),
            "skill_identity_uid": uid("ski"),
            "source_class": "CODEX",
            "source_relative_path": "codex/fixture-skill",
            "source_fingerprint_digest": DIGEST_B,
            "provenance": {
                "kind": "LOCAL_MANAGED",
                "upstream_repo": None,
                "git_object_id": None,
                "license_state": "KNOWN_ALLOWED",
                "license_id": "Apache-2.0",
                "trust_tier": "LOCAL_TRUSTED",
            },
            "permissions": permissions(),
            "tool_codes": ["LOCAL_FILESYSTEM"],
            "data_class_codes": ["PUBLIC_METADATA"],
            "first_seen_at": TS,
            "last_seen_at": TS,
            "parent_instance_uids": [],
            "moved_from_instance_uid": None,
            "forked_from_instance_uid": None,
            "version_uids": [uid("skv")],
            "lifecycle_status": "REGISTERED",
        },
    )
    version = artifact(
        "skill-version",
        {
            "skill_version_uid": uid("skv"),
            "skill_instance_uid": uid("skinst"),
            "srv_revision": SRV,
            "content_digest": DIGEST_B,
            "tree_digest": DIGEST_C,
            "metadata_digest": DIGEST_D,
            "dependency_manifest_digest": DIGEST_B,
            "permission_manifest_digest": DIGEST_C,
            "source_material_policy_id": "urn:linzecolin:agentdatabase:skillops:policy:source-material:v1",
            "source_material_policy_digest": DIGEST_B,
            "source_observed_at": TS,
            "git_object_id": "sha1:" + "1" * 40,
            "dependencies": [
                {
                    "dependency_type": "RUNTIME",
                    "reference": "python3",
                    "resolved_digest": None,
                    "required": True,
                }
            ],
            "permissions": permissions(),
            "compatibility_codes": ["PYTHON_3_9_PLUS"],
            "trust_tier": "LOCAL_TRUSTED",
            "lifecycle_status": "REGISTERED",
            "eval_profile_uid": uid("evp"),
            "supersedes_version_uid": None,
            "created_at": TS,
        },
    )
    lineage = artifact(
        "identity-lineage-event",
        {
            "event_uid": uid("evt"),
            "event_type": "ALIAS_ADDED",
            "source_identity_uids": [uid("ski")],
            "target_identity_uids": [uid("ski", ULID_1)],
            "reason_codes": ["EVIDENCE_CONFIRMED"],
            "evidence_digests": [DIGEST_B],
            "actor": "SKILLOPS_CONTROLLER",
            "occurred_at": TS,
        },
    )
    profile = artifact(
        "eval-profile",
        {
            "eval_profile_uid": uid("evp"),
            "skill_identity_uid": uid("ski"),
            "srv_revision": SRV,
            "risk_class": "LOW",
            "dataset_manifest_digests": [DIGEST_B],
            "evaluator_manifest_digests": [DIGEST_C],
            "tool_manifest_digest": DIGEST_D,
            "policy_snapshot_digest": DIGEST_B,
            "routing_sets": {
                "positive_digest": DIGEST_B,
                "missed_trigger_digest": DIGEST_C,
                "false_trigger_digest": DIGEST_D,
                "conflict_digest": DIGEST_B,
                "abstention_digest": DIGEST_C,
            },
            "deterministic_check_manifest_digests": [DIGEST_D],
            "confirmed_regression_manifest_digests": [DIGEST_B],
            "judge_rubric_digest": DIGEST_B,
            "human_calibration_manifest_digest": DIGEST_C,
            "sealed_holdout_manifest_digest": DIGEST_D,
            "dimension_weights_bps": [
                {"dimension_code": "EFFICIENCY", "weight_bps": 1000},
                {"dimension_code": "MAINTAINABILITY", "weight_bps": 500},
                {"dimension_code": "NEGATIVE_CAPABILITY", "weight_bps": 1000},
                {"dimension_code": "OUTCOME", "weight_bps": 3000},
                {"dimension_code": "RELIABILITY", "weight_bps": 1500},
                {"dimension_code": "ROUTING", "weight_bps": 1000},
                {"dimension_code": "SAFETY_GOVERNANCE", "weight_bps": 2000},
            ],
            "hard_gate_codes": HARD_GATES,
            "minimum_sample_count": 1,
            "sealed_holdout_required": True,
            "optimizer_may_read_sealed_labels": False,
            "optimizer_may_mutate_evaluator": False,
            "optimizer_may_mutate_profile": False,
            "optimizer_may_mutate_promotion_controller": False,
            "freshness_policy": {
                "max_age_days": 30,
                "retest_triggers": ["INCIDENT", "MODEL_CHANGE", "POLICY_CHANGE", "SKILL_CHANGE"],
            },
            "created_at": TS,
            "updated_at": TS,
            "supersedes_profile_uid": None,
        },
    )
    eval_run = artifact(
        "eval-run",
        {
            "eval_run_uid": uid("evr"),
            "skill_version_uid": uid("skv"),
            "eval_profile_uid": uid("evp"),
            "skill_version_record_digest": DIGEST_B,
            "eval_profile_digest": DIGEST_C,
            "dataset_manifest_digests": [DIGEST_B],
            "evaluator_manifest_digests": [DIGEST_C],
            "rubric_digest": DIGEST_D,
            "sealed_access_audit_digest": DIGEST_D,
            "tool_manifest_digest": DIGEST_B,
            "policy_snapshot_digest": DIGEST_C,
            "binding_state": "BOUND",
            "controlled_invocation_envelope_digest": DIGEST_B,
            "run_event_refs": [
                {"run_uid": uid("run"), "event_digest": DIGEST_C, "event_bundle_digest": BUNDLE}
            ],
            "model_snapshot": {
                "provider_code": "OPENAI",
                "requested_alias": None,
                "resolved_id": "fixture-model",
                "observed_at": TS,
            },
            "environment_fingerprint_digest": DIGEST_D,
            "started_at": TS,
            "finished_at": TS,
            "status": "PASS",
            "result_artifact_digests": [DIGEST_B],
        },
    )
    scorecard = artifact(
        "scorecard",
        {
            "scorecard_uid": uid("sc"),
            "skill_version_uid": uid("skv"),
            "eval_profile_uid": uid("evp"),
            "eval_run_uid": uid("evr"),
            "skill_version_record_digest": DIGEST_B,
            "eval_profile_digest": DIGEST_C,
            "model_snapshot_digest": DIGEST_D,
            "environment_fingerprint_digest": DIGEST_B,
            "dataset_manifest_digests": [DIGEST_B],
            "evaluator_manifest_digests": [DIGEST_C],
            "evaluated_at": TS,
            "hard_gates": [
                {"gate_code": code, "passed": True, "evidence_digest": DIGEST_B}
                for code in HARD_GATES
            ],
            "dimensions": [
                {"dimension_code": code, "score_bps": 9000, "sample_count": 1, "coverage_bps": 10000}
                for code in DIMENSIONS
            ],
            "routing_results": {
                "positive": {"sample_count": 1, "correct_count": 1, "score_bps": 10000},
                "missed_trigger": {"sample_count": 1, "correct_count": 1, "score_bps": 10000},
                "false_trigger": {"sample_count": 1, "correct_count": 1, "score_bps": 10000},
                "conflict": {"sample_count": 1, "correct_count": 1, "score_bps": 10000},
                "abstention": {"sample_count": 1, "correct_count": 1, "score_bps": 10000},
            },
            "judge_calibration": {
                "state": "CALIBRATED",
                "agreement_bps": 9000,
                "bias_bps": 0,
                "drift_bps": 100,
                "evidence_digest": DIGEST_D,
                "sole_decision_authority": False,
            },
            "weighted_score_bps": 9400,
            "promotion_eligible": True,
            "confidence_bps": 9000,
            "coverage_bps": 10000,
            "freshness_state": "FRESH",
            "freshness_valid_until": "2026-08-22",
            "critical_incident_count": 0,
            "critical_incident_evidence_digests": [],
            "evidence_bundle_digest": DIGEST_C,
        },
    )
    evidence_ref_score = {
        "schema_id": sid("scorecard"),
        "artifact_uid": uid("sc"),
        "artifact_digest": DIGEST_B,
    }
    evidence_ref_run = {
        "schema_id": sid("eval-run"),
        "artifact_uid": uid("evr"),
        "artifact_digest": DIGEST_C,
    }
    evidence = artifact(
        "promotion-evidence-bundle",
        {
            "promotion_bundle_uid": uid("peb"),
            "candidate_skill_version_uid": uid("skv", ULID_1),
            "baseline_skill_version_uid": uid("skv"),
            "scorecard_refs": [evidence_ref_score],
            "eval_run_refs": [evidence_ref_run],
            "candidate_model_snapshot_digest": DIGEST_B,
            "baseline_model_snapshot_digest": DIGEST_C,
            "environment_fingerprint_digest": DIGEST_D,
            "tool_manifest_digest": DIGEST_B,
            "dataset_manifest_digests": [DIGEST_B],
            "evaluator_manifest_digests": [DIGEST_C],
            "rubric_digest": DIGEST_D,
            "policy_snapshot_digest": DIGEST_B,
            "causal_matrix": [
                {"cell": "BASELINE", "skill_version_uid": uid("skv"), "model_snapshot_digest": DIGEST_C, "eval_run_digest": DIGEST_B, "status": "PASS"},
                {"cell": "INTERACTION", "skill_version_uid": uid("skv", ULID_1), "model_snapshot_digest": DIGEST_B, "eval_run_digest": DIGEST_C, "status": "PASS"},
                {"cell": "MODEL_EFFECT", "skill_version_uid": uid("skv"), "model_snapshot_digest": DIGEST_B, "eval_run_digest": DIGEST_D, "status": "PASS"},
                {"cell": "SKILL_EFFECT", "skill_version_uid": uid("skv", ULID_1), "model_snapshot_digest": DIGEST_C, "eval_run_digest": DIGEST_D, "status": "PASS"},
            ],
            "shadow_evidence_digest": DIGEST_C,
            "canary_evidence_digest": DIGEST_D,
            "hard_gates_passed": True,
            "risk_tier": "LOW",
            "known_risk_codes": [],
            "rollback_target_version_uid": uid("skv"),
            "notification_required": False,
            "notification_receipt_digest": None,
            "created_at": TS,
            "actor": "SKILLOPS_PROMOTION_CONTROLLER",
        },
    )
    decision = artifact(
        "promotion-decision",
        {
            "promotion_decision_uid": uid("prd"),
            "srv_revision": SRV,
            "action": "PROMOTE",
            "stage": "CHAMPION",
            "impact": "MINOR",
            "candidate_skill_version_uid": uid("skv", ULID_1),
            "previous_champion_version_uid": uid("skv"),
            "resulting_champion_version_uid": uid("skv", ULID_1),
            "candidate_model_snapshot_digest": DIGEST_B,
            "baseline_model_snapshot_digest": DIGEST_C,
            "from_status": "CHALLENGER",
            "to_status": "CHAMPION",
            "evidence_bundle_digest": DIGEST_B,
            "hard_gates_passed": True,
            "known_risk_codes": [],
            "reason_codes": ["HARD_GATES_PASSED"],
            "actor": "SKILLOPS_PROMOTION_CONTROLLER",
            "major_change": False,
            "notification_receipt_digest": None,
            "notification_mode": "NOT_REQUIRED",
            "owner_approval_required": False,
            "emergency_containment": False,
            "rollback_target_version_uid": uid("skv"),
            "decided_at": TS,
        },
    )
    transition = artifact(
        "iteration-transition",
        {
            "iteration_transition_uid": uid("itr"),
            "from_skill_version_uid": uid("skv"),
            "to_skill_version_uid": uid("skv", ULID_1),
            "phase": "SHADOW",
            "experiment_matrix_digest": DIGEST_B,
            "optimizer_evaluator_isolation_digest": DIGEST_C,
            "side_effect_budget": 0,
            "early_stop_codes": ["PRIVACY_GATE_FAILED"],
            "rollback_target_version_uid": uid("skv"),
            "occurred_at": TS,
        },
    )
    passport = artifact(
        "skill-passport",
        {
            "passport_uid": uid("spp"),
            "skill_identity_uid": uid("ski"),
            "active_skill_version_uid": uid("skv"),
            "canonical_name": "fixture-skill",
            "summary": "Deterministic derived passport fixture.",
            "owner_ref": "owner-primary",
            "lifecycle_status": "CHAMPION",
            "provenance": {
                "source_class": "CODEX",
                "source_relative_path": "codex/fixture-skill",
                "content_digest": DIGEST_B,
                "tree_digest": DIGEST_C,
                "license_state": "KNOWN_ALLOWED",
                "trust_tier": "LOCAL_TRUSTED",
            },
            "permissions": {
                "tool_codes": ["LOCAL_FILESYSTEM"],
                "network": "NONE",
                "filesystem_write": "WORKSPACE_ONLY",
                "external_side_effect": "NONE",
                "data_class_codes": ["PUBLIC_METADATA"],
            },
            "applicability_codes": ["CODE_REVIEW"],
            "negative_capability_codes": [],
            "use_when_codes": ["CODE_REVIEW_REQUESTED"],
            "do_not_use_when_codes": ["NO_WORKSPACE"],
            "abstain_when_codes": ["AUTHORITY_MISSING"],
            "risk_tier": "LOW",
            "permission_summary_codes": ["WORKSPACE_WRITE"],
            "scorecard_uid": uid("sc"),
            "scorecard_digest": DIGEST_B,
            "weighted_score_bps": 9000,
            "confidence_bps": 9000,
            "coverage_bps": 10000,
            "freshness_state": "FRESH",
            "freshness_valid_until": "2026-08-22",
            "last_evaluated_at": TS,
            "champion_model_snapshot_digest": DIGEST_D,
            "known_failure_mode_codes": [],
            "rollback_target_version_uid": uid("skv"),
            "source_fact_digests": [DIGEST_C],
            "generated_at": TS,
        },
    )
    graph = artifact(
        "capability-graph",
        {
            "graph_uid": uid("cpg"),
            "source_snapshot_digest": DIGEST_B,
            "nodes": [
                {"uid": uid("ski"), "node_type": "SKILL_IDENTITY", "label_code": "FIXTURE_SKILL", "lifecycle_status": "CHAMPION"},
                {"uid": uid("skv"), "node_type": "SKILL_VERSION", "label_code": "FIXTURE_VERSION", "lifecycle_status": "CHAMPION"},
            ],
            "edges": [
                {"from_uid": uid("ski"), "to_uid": uid("skv"), "edge_type": "PROVIDES", "evidence_digest": DIGEST_C, "confidence_bps": 10000}
            ],
            "node_count": 2,
            "edge_count": 1,
            "generated_at": TS,
        },
    )
    envelope = artifact(
        "artifact-envelope",
        {
            "envelope_uid": uid("env"),
            "artifact_schema_id": sid("skill-identity"),
            "artifact_uid": uid("ski"),
            "artifact_digest": DIGEST_B,
            "artifact_schema_digest": DIGEST_C,
            "artifact_repo_path": "CodexSkills/governance/artifacts/fixture.json",
            "immutable": True,
            "created_at": TS,
        },
    )
    manifest = {
        "schema_version": sid("schema-bundle-manifest"),
        "protocol_revision": PROTOCOL,
        "srv_revision": SRV,
        "canonicalization": {
            "scheme": "RFC8785_JCS",
            "input_profile": "I_JSON",
            "encoding": "UTF-8",
            "unicode_normalization": "NONE",
            "duplicate_keys": "REJECT",
            "self_digest_exclusion": "EXACT_DECLARED_JSON_POINTER_ONLY",
        },
        "digest_algorithm": "SHA-256",
        "test_vectors_digest": interface["canonicalization"]["test_vectors_digest"],
        "schemas": interface["mechanism_schema_entries"],
        "schema_count": interface["mechanism_schema_count"],
        "policies": interface["mechanism_policy_entries"],
        "policy_count": interface["mechanism_policy_count"],
        "compatibility": {
            "active_bundle_mode": "EXACT_DIGEST",
            "accepted_predecessor_bundle_digests": [],
            "predecessor_acceptance_expires_at": None,
        },
    }
    values = {
        "skill-identity": identity,
        "skill-instance": instance,
        "skill-version": version,
        "identity-lineage-event": lineage,
        "eval-profile": profile,
        "eval-run": eval_run,
        "scorecard": scorecard,
        "promotion-evidence-bundle": evidence,
        "promotion-decision": decision,
        "iteration-transition": transition,
        "skill-passport": passport,
        "capability-graph": graph,
        "artifact-envelope": envelope,
        "schema-bundle-manifest": manifest,
    }
    for name, value in values.items():
        finalize_self_digest(bundle, sid(name), value)
    return values


class MechanismContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bundle = load_draft_contract()
        cls.interface = strict_load(GOVERNANCE_DIR / "draft-interface.json")
        cls.artifacts = representative_artifacts(cls.bundle, cls.interface)
        cls.fixture_dir = GOVERNANCE_DIR / "fixtures" / "negative"

    def test_01_runtime_gate_and_vendor_provenance(self) -> None:
        versions = capability_gate()
        self.assertTrue(versions["jsonschema"].startswith("4."))
        self.assertTrue(versions["referencing"].startswith("0."))
        verify_vendor()
        provenance = strict_load(
            GOVERNANCE_DIR / "vendor" / "json_canonicalization" / "PROVENANCE.json"
        )
        self.assertEqual(provenance["upstream_commit"], "19d51d7fe467d4706a3ff08adf8a748f29fc21e0")
        self.assertFalse(provenance["runtime_network_required"])
        self.assertFalse(provenance["vendored_files_modified"])
        namespace_probe = (
            "import sys,types;"
            "sentinel=types.ModuleType('org');sys.modules['org']=sentinel;"
            f"sys.path.insert(0,{str(TOOLS_DIR)!r});"
            "from canonical_json import canonicalize_object;"
            "assert canonicalize_object({'b':1,'a':2})==b'{\"a\":2,\"b\":1}';"
            "assert sys.modules['org'] is sentinel"
        )
        process = subprocess.run(
            [sys.executable, "-B", "-c", namespace_probe],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        self.assertEqual(process.returncode, 0, process.stderr)

    def test_02_builder_is_byte_deterministic(self) -> None:
        process = subprocess.run(
            [sys.executable, "-B", str(TOOLS_DIR / "build_draft.py"), "--check"],
            cwd=REPO_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertIn("DRAFT_BYTE_EQUIVALENT", process.stdout)

    def test_03_canonicalization_vectors(self) -> None:
        vectors = strict_load(GOVERNANCE_DIR / "test_vectors" / "canonicalization-v1.json")
        for case in vectors["cases"]:
            with self.subTest(case=case["id"]):
                actual = canonicalize_bytes(case["input_json"].encode("utf-8"))
                self.assertEqual(actual.decode("utf-8"), case["expected_canonical_json"])
                self.assertEqual(hashlib.sha256(actual).hexdigest(), case["expected_sha256"])
        exclusion = vectors["self_exclusion"]
        self.assertEqual(
            canonical_digest(exclusion["input"], exclusion["pointer"]),
            exclusion["expected_sha256"],
        )

    def test_04_schema_bundle_is_closed_and_offline(self) -> None:
        self.assertEqual(len(self.bundle.schemas), 21)
        self.assertEqual(len(self.bundle.policies), 5)
        lint_schema_documents(self.bundle.schemas)
        self.assertEqual(
            sorted(self.bundle.schemas, key=lambda value: value.encode("ascii")),
            [entry["id"] for entry in self.interface["mechanism_schema_entries"]],
        )
        unknown_schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$ref": sid("not-in-bundle"),
        }
        with self.assertRaises(Unresolvable):
            list(
                Draft202012Validator(
                    unknown_schema,
                    registry=self.bundle.registry,
                ).iter_errors({})
            )
        process = subprocess.run(
            [
                sys.executable,
                "-B",
                str(TOOLS_DIR / "validate_mechanism.py"),
                "lint-schema-set",
                "--schema-dir",
                str(GOVERNANCE_DIR / "schemas"),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertIn("SCHEMA_SET_VALID schemas=21", process.stdout)

    def test_05_strict_formats_and_uid_contract(self) -> None:
        checker = self.bundle.format_checker
        self.assertTrue(checker.conforms(TS, "utc-z-timestamp-v1"))
        self.assertTrue(checker.conforms("2024-02-29T23:59:59.123456Z", "utc-z-timestamp-v1"))
        self.assertFalse(checker.conforms("2026-02-30T04:15:00.000000Z", "utc-z-timestamp-v1"))
        self.assertFalse(checker.conforms("2026-07-23T04:15:00.000000+10:00", "utc-z-timestamp-v1"))
        self.assertFalse(checker.conforms("not-a-time", "utc-z-timestamp-v1"))
        uid_schema = self.bundle.schemas[sid("common-definitions")]["$defs"]["skill_identity_uid"]
        validator = Draft202012Validator(uid_schema)
        self.assertTrue(validator.is_valid(uid("ski")))
        self.assertFalse(validator.is_valid("ski_" + "0" * 24))
        self.assertFalse(validator.is_valid("ski_8" + "0" * 25))
        self.assertFalse(validator.is_valid("ski_0" + "I" * 25))

    def test_06_repo_path_and_symlink_public_target_contract(self) -> None:
        self.assertTrue(is_repo_relative_posix_path("codex/skill/SKILL.md"))
        self.assertTrue(is_repo_relative_posix_path("shared/normalized/target"))
        for invalid in ("../escape", "a/../b", "/Users/alice/file", "a\\b", "a//b", "a/./b"):
            with self.subTest(path=invalid):
                self.assertFalse(is_repo_relative_posix_path(invalid))
        source_policy = self.bundle.policies[
            "urn:linzecolin:agentdatabase:skillops:policy:source-material:v1"
        ]
        self.assertFalse(source_policy["symlink_policy"]["raw_target_public"])
        self.assertEqual(source_policy["symlink_policy"]["public_target_field"], "normalized_target_ref")
        patterns = {entry["pattern"] for entry in source_policy["exclusions"]}
        self.assertIn("**/.git", patterns)
        self.assertIn("**/.git/**", patterns)
        self.assertFalse(source_policy["size_skip_allowed"])

    def test_07_binding_state_machine(self) -> None:
        unknown = {"binding_state": "UNKNOWN", "unknown_reason_code": "EXACT_BINDING_UNPROVEN"}
        validate_instance(self.bundle, unknown, sid("skill-binding"), verify_digest=False)
        bound = {
            "binding_state": "BOUND",
            "skill_ref": {
                "skill_identity_uid": uid("ski"),
                "skill_instance_uid": uid("skinst"),
                "skill_version_uid": uid("skv"),
                "content_digest": BUNDLE,
                "tree_digest": DIGEST_B,
                "version_record_digest": DIGEST_C,
                "registry_snapshot_digest": DIGEST_D,
            },
            "controlled_invocation": {
                "invocation_uid": uid("inv"),
                "invocation_envelope_digest": DIGEST_B,
                "surface_class": "CODEX_CLI",
                "observed_at": TS,
                "evidence_type": "CONTROLLED_INVOCATION_EXACT_VERSION",
            },
        }
        validate_instance(self.bundle, bound, sid("skill-binding"), verify_digest=False)
        bound["controlled_invocation"]["surface_class"] = "CODEX_DESKTOP"
        with self.assertRaisesRegex(ContractError, "SCHEMA_VALIDATION_FAILED"):
            validate_instance(self.bundle, bound, sid("skill-binding"), verify_digest=False)

    def test_08_every_mechanism_artifact_shape_has_a_valid_fixture(self) -> None:
        expected = {
            "skill-identity", "skill-instance", "skill-version", "identity-lineage-event",
            "eval-profile", "eval-run", "scorecard", "promotion-evidence-bundle",
            "promotion-decision", "iteration-transition", "skill-passport",
            "capability-graph", "artifact-envelope", "schema-bundle-manifest",
        }
        self.assertEqual(set(self.artifacts), expected)
        for name, instance in self.artifacts.items():
            with self.subTest(schema=name):
                validate_instance(
                    self.bundle,
                    instance,
                    sid(name),
                    expected_bundle_digest=None if name == "schema-bundle-manifest" else BUNDLE,
                )

    def test_09_semantic_gates_fail_closed(self) -> None:
        bad_profile = dict(self.artifacts["eval-profile"])
        bad_profile["dimension_weights_bps"] = [
            {**item, "weight_bps": 0 if item["dimension_code"] == "EFFICIENCY" else item["weight_bps"]}
            for item in self.artifacts["eval-profile"]["dimension_weights_bps"]
        ]
        with self.assertRaisesRegex(ContractError, "EVAL_WEIGHT_SUM_NOT_10000"):
            validate_instance(self.bundle, bad_profile, sid("eval-profile"), expected_bundle_digest=BUNDLE)
        bad_score = dict(self.artifacts["scorecard"])
        bad_score["hard_gates"] = [dict(gate) for gate in self.artifacts["scorecard"]["hard_gates"]]
        bad_score["hard_gates"][0]["passed"] = False
        bad_score["promotion_eligible"] = True
        with self.assertRaisesRegex(ContractError, "SELF_DIGEST_MISMATCH"):
            validate_instance(self.bundle, bad_score, sid("scorecard"), expected_bundle_digest=BUNDLE)
        finalize_self_digest(self.bundle, sid("scorecard"), bad_score)
        with self.assertRaisesRegex(ContractError, "FAILED_HARD_GATE_CANNOT_PROMOTE"):
            validate_instance(self.bundle, bad_score, sid("scorecard"), expected_bundle_digest=BUNDLE)
        untrusted_instance = dict(self.artifacts["skill-instance"])
        untrusted_instance["provenance"] = {
            **untrusted_instance["provenance"],
            "license_state": "UNKNOWN",
            "trust_tier": "UNVERIFIED",
        }
        untrusted_instance["lifecycle_status"] = "CHAMPION"
        with self.assertRaisesRegex(ContractError, "UNRESOLVED_PROVENANCE_MUST_QUARANTINE"):
            validate_instance(
                self.bundle,
                untrusted_instance,
                sid("skill-instance"),
                expected_bundle_digest=BUNDLE,
            )
        invalid_promotion = dict(self.artifacts["promotion-decision"])
        invalid_promotion["from_status"] = "UNKNOWN"
        finalize_self_digest(self.bundle, sid("promotion-decision"), invalid_promotion)
        with self.assertRaisesRegex(ContractError, "PROMOTION_LIFECYCLE_TRANSITION_INVALID"):
            validate_instance(
                self.bundle,
                invalid_promotion,
                sid("promotion-decision"),
                expected_bundle_digest=BUNDLE,
            )
        unsafe_shadow = dict(self.artifacts["iteration-transition"])
        unsafe_shadow["side_effect_budget"] = 1
        finalize_self_digest(self.bundle, sid("iteration-transition"), unsafe_shadow)
        with self.assertRaisesRegex(ContractError, "SHADOW_SIDE_EFFECT_BUDGET_MUST_BE_ZERO"):
            validate_instance(
                self.bundle,
                unsafe_shadow,
                sid("iteration-transition"),
                expected_bundle_digest=BUNDLE,
            )

    def test_10_public_value_scans_values_not_only_keys(self) -> None:
        scan_public_value({"recipient_ref": "owner-primary", "status": "PASS"}, self.bundle.policies)
        for name, artifact_value in self.artifacts.items():
            with self.subTest(public_artifact=name):
                scan_public_value(artifact_value, self.bundle.policies)
        scan_public_value({"artifact_digest": DIGEST_B}, self.bundle.policies)
        with self.assertRaisesRegex(ContractError, "PUBLIC_EMAIL_BLOCK"):
            scan_public_value({"recipient_ref": "owner@example.com"}, self.bundle.policies)
        with self.assertRaisesRegex(ContractError, "PUBLIC_ABSOLUTE_PATH_BLOCK"):
            scan_public_value({"note": "read /Users/alice/private.json"}, self.bundle.policies)
        with self.assertRaisesRegex(ContractError, "PUBLIC_HIGH_ENTROPY_FREE_STRING_BLOCK"):
            scan_public_value({"note": "Q7vN9pL2xR4mT8kW3cF6jH1sD5aZ0uYbE9gC"}, self.bundle.policies)
        with self.assertRaisesRegex(ContractError, "PUBLIC_HIGH_ENTROPY_FREE_STRING_BLOCK"):
            scan_public_value({"note": DIGEST_B}, self.bundle.policies)
        with self.assertRaisesRegex(ContractError, "PUBLIC_FORBIDDEN_FIELD"):
            scan_public_value({"details": {"email": "redacted"}}, self.bundle.policies)
        digest_fields = set()

        def collect_digest_fields(node: Any) -> None:
            if isinstance(node, dict):
                properties = node.get("properties", {})
                if isinstance(properties, dict):
                    for key, child_schema in properties.items():
                        if (
                            (key.endswith("_digest") or key.endswith("_digests") or key.endswith("_sha256"))
                            and not isinstance(child_schema.get("const") if isinstance(child_schema, dict) else None, bool)
                        ):
                            digest_fields.add(key)
                for child in node.values():
                    collect_digest_fields(child)
            elif isinstance(node, list):
                for child in node:
                    collect_digest_fields(child)

        for schema in self.bundle.schemas.values():
            collect_digest_fields(schema)
        allowed = set(
            self.bundle.policies[
                "urn:linzecolin:agentdatabase:skillops:policy:public-value:v1"
            ]["allowed_high_entropy_field_names"]
        )
        self.assertFalse(digest_fields.difference(allowed))

    def test_11_negative_fixture_index_is_complete_and_enforced(self) -> None:
        index = strict_load(self.fixture_dir / "index.json")
        self.assertEqual(len(index["cases"]), 21)
        seen = set()
        for case in index["cases"]:
            self.assertNotIn(case["id"], seen)
            seen.add(case["id"])
            path = self.fixture_dir / case["path"]
            self.assertTrue(path.is_file())
            code = case["expected_code"]
            with self.subTest(case=case["id"]):
                if case["id"] in {"DUPLICATE_KEY", "NAN", "INFINITY", "LONE_SURROGATE"}:
                    with self.assertRaisesRegex(CanonicalizationError, code):
                        parse_json_bytes(path.read_bytes())
                elif case["id"].startswith("PUBLIC_"):
                    with self.assertRaisesRegex(ContractError, code):
                        scan_public_value(strict_load(path), self.bundle.policies)
                elif case["id"].startswith("TIMESTAMP_"):
                    value = strict_load(path)["value"]
                    self.assertFalse(self.bundle.format_checker.conforms(value, "utc-z-timestamp-v1"))
                elif case["id"] == "PATH_TRAVERSAL":
                    self.assertFalse(is_repo_relative_posix_path(strict_load(path)["value"]))
                elif case["id"] == "UNKNOWN_BINDING_WITH_SKILL_REF":
                    with self.assertRaisesRegex(ContractError, code):
                        validate_instance(self.bundle, strict_load(path), sid("skill-binding"), verify_digest=False)
                elif case["id"].startswith("SCHEMA_"):
                    document = strict_load(path)
                    with self.assertRaisesRegex(ContractError, code):
                        lint_schema_documents({document["$id"]: document})
                elif case["id"] == "BUNDLE_MISMATCH":
                    with self.assertRaisesRegex(ContractError, code):
                        validate_instance(
                            self.bundle,
                            strict_load(path),
                            sid("skill-identity"),
                            expected_bundle_digest=BUNDLE,
                        )
                else:  # pragma: no cover - makes new fixtures fail until routed explicitly
                    self.fail(f"unrouted negative fixture: {case['id']}")

    def test_12_policy_p0_invariants(self) -> None:
        retention = self.bundle.policies[
            "urn:linzecolin:agentdatabase:skillops:policy:retention:v2"
        ]
        self.assertEqual(retention["clock_basis"], "UTC_WALL_CLOCK")
        self.assertFalse(retention["persistent_managed_raw_default_enabled"])
        self.assertEqual(retention["managed_raw_max_hours"], 72)
        self.assertEqual(retention["ttl_enforcement_availability"], "LOCAL_RUNTIME_AVAILABLE_ONLY")
        self.assertFalse(retention["offline_period_hard_guarantee_claimed"])
        self.assertTrue(retention["offline_resume_first_cycle_receipt_required"])
        self.assertTrue(retention["offline_gap_receipt_required"])
        notification = self.bundle.policies[
            "urn:linzecolin:agentdatabase:skillops:policy:notification:v1"
        ]
        self.assertNotIn("@", notification["recipient_ref"])
        self.assertTrue(notification["actual_recipient_mapping_repo_external"])
        version = self.bundle.policies[
            "urn:linzecolin:agentdatabase:skillops:policy:version:v2"
        ]
        self.assertTrue(version["daily_transaction_uid_separate"])
        self.assertEqual(version["srv_update_mode"], "GLOBAL_ATOMIC_INCREMENT")
        self.assertFalse(version["srv_reuse_allowed"])
        self.assertFalse(version["srv_last_component_bounded"])
        self.assertEqual(version["timezone"], "Australia/Sydney")
        self.assertEqual(version["daily_schedule_local"], "04:15")
        self.assertTrue(version["sunday_forced_full"])
        self.assertFalse(version["late_start_rejected"])
        self.assertTrue(version["manual_uses_same_orchestrator"])

    def test_13_bundle_members_have_no_bundle_self_cycle(self) -> None:
        for schema_id, document in self.bundle.schemas.items():
            if schema_id == sid("schema-bundle-manifest"):
                continue
            self.assertNotIn("bundle_digest", document)
        for policy in self.bundle.policies.values():
            self.assertNotIn("bundle_digest", policy)
        self.assertEqual(
            self.interface["trust_bootstrap"]["canonical_manifest_path"],
            CANONICAL_MANIFEST_PATH,
        )
        self.assertFalse(self.interface["trust_bootstrap"]["repo_self_report_is_trusted"])

    def test_14_trust_bootstrap_binds_external_git_object_and_digest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)

            def copy_member(relative_path: str) -> None:
                source = REPO_ROOT / relative_path
                target = repo / relative_path
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)

            schema_entries = [dict(entry) for entry in self.interface["mechanism_schema_entries"]]
            policy_entries = [dict(entry) for entry in self.interface["mechanism_policy_entries"]]
            for entry in schema_entries + policy_entries:
                copy_member(entry["relative_path"])
            copy_member("CodexSkills/governance/test_vectors/canonicalization-v1.json")
            common_id = sid("common-definitions")
            for contract in self.interface[
                "auto_public_schema_contracts_required_for_complete_bundle"
            ]:
                schema_id = contract["id"]
                name = schema_id[len(SCHEMA_PREFIX):].rsplit(":v", 1)[0]
                digest_field = contract["self_digest_pointer"][1:]
                relative_path = f"CodexSkills/auto/schemas/public/{name}.schema.json"
                document = {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "$id": schema_id,
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "schema_version": {"const": schema_id},
                        "protocol_revision": {"const": PROTOCOL},
                        "bundle_digest": {"$ref": f"{common_id}#/$defs/sha256"},
                        digest_field: {"$ref": f"{common_id}#/$defs/sha256"},
                    },
                    "required": [
                        "schema_version", "protocol_revision", "bundle_digest", digest_field,
                    ],
                }
                target = repo / relative_path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(
                    json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                schema_entries.append(
                    {
                        "id": schema_id,
                        "owner_plane": "AUTO",
                        "relative_path": relative_path,
                        "schema_version": schema_id,
                        "schema_sha256": hashlib.sha256(canonicalize_object(document)).hexdigest(),
                        "compatibility": "EXACT_ONLY",
                        "self_digest_pointer": contract["self_digest_pointer"],
                    }
                )
            schema_entries.sort(key=lambda entry: entry["id"].encode("ascii"))
            manifest = {
                "schema_version": sid("schema-bundle-manifest"),
                "protocol_revision": PROTOCOL,
                "srv_revision": SRV,
                "canonicalization": {
                    "scheme": "RFC8785_JCS",
                    "input_profile": "I_JSON",
                    "encoding": "UTF-8",
                    "unicode_normalization": "NONE",
                    "duplicate_keys": "REJECT",
                    "self_digest_exclusion": "EXACT_DECLARED_JSON_POINTER_ONLY",
                },
                "digest_algorithm": "SHA-256",
                "test_vectors_digest": self.interface["canonicalization"]["test_vectors_digest"],
                "schemas": schema_entries,
                "schema_count": len(schema_entries),
                "policies": policy_entries,
                "policy_count": len(policy_entries),
                "compatibility": {
                    "active_bundle_mode": "EXACT_DIGEST",
                    "accepted_predecessor_bundle_digests": [],
                    "predecessor_acceptance_expires_at": None,
                },
                "bundle_digest": "0" * 64,
            }
            manifest["bundle_digest"] = canonical_digest(manifest, "/bundle_digest")
            manifest_path = repo / CANONICAL_MANIFEST_PATH
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            for command in (
                ["git", "init", "-q"],
                ["git", "config", "user.name", "Mechanism Test"],
                ["git", "config", "user.email", "mechanism-test@example.invalid"],
                ["git", "add", "CodexSkills"],
                ["git", "commit", "-q", "-m", "trusted bundle fixture"],
            ):
                process = subprocess.run(
                    command,
                    cwd=repo,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                )
                self.assertEqual(process.returncode, 0, process.stderr)
            head = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=repo, text=True
            ).strip()
            manifest_path.write_text("{}\n", encoding="utf-8")
            trusted = load_trusted_bundle(
                repo,
                TrustTuple(
                    verified_git_object_id=f"sha1:{head}",
                    expected_bundle_digest=manifest["bundle_digest"],
                    canonical_manifest_path=CANONICAL_MANIFEST_PATH,
                    mode="CANDIDATE",
                ),
            )
            self.assertEqual(len(trusted.schemas), 29)
            self.assertEqual(len(trusted.policies), 5)

        trust = TrustTuple(
            verified_git_object_id="sha1:" + "0" * 40,
            expected_bundle_digest="not-a-digest",
            canonical_manifest_path=CANONICAL_MANIFEST_PATH,
            mode="ACTIVE",
        )
        with self.assertRaisesRegex(ContractError, "TRUST_EXPECTED_BUNDLE_DIGEST_INVALID"):
            load_trusted_bundle(REPO_ROOT, trust)
        wrong_path = TrustTuple(
            verified_git_object_id="sha1:" + "0" * 40,
            expected_bundle_digest=BUNDLE,
            canonical_manifest_path="CodexSkills/governance/self-reported.json",
            mode="ACTIVE",
        )
        with self.assertRaisesRegex(ContractError, "TRUST_CANONICAL_MANIFEST_PATH_MISMATCH"):
            load_trusted_bundle(REPO_ROOT, wrong_path)

    def test_15_m0a_cannot_claim_activation(self) -> None:
        self.assertEqual(self.interface["status"], "DRAFT_NON_ACTIVE")
        self.assertTrue(self.interface["activation_forbidden"])
        self.assertFalse((REPO_ROOT / "CodexSkills" / "VERSION").exists())
        self.assertFalse((REPO_ROOT / CANONICAL_MANIFEST_PATH).exists())
        self.assertEqual(
            self.interface["auto_public_schema_ids_required_for_complete_bundle"],
            sorted(
                self.interface["auto_public_schema_ids_required_for_complete_bundle"],
                key=lambda value: value.encode("ascii"),
            ),
        )
        self.assertEqual(len(self.interface["auto_public_schema_ids_required_for_complete_bundle"]), 8)
        contracts = self.interface["auto_public_schema_contracts_required_for_complete_bundle"]
        self.assertEqual([entry["id"] for entry in contracts], self.interface["auto_public_schema_ids_required_for_complete_bundle"])
        self.assertTrue(all(entry["owner_plane"] == "AUTO" for entry in contracts))
        self.assertTrue(all(entry["self_digest_pointer"] for entry in contracts))
        self.assertEqual(len(self.interface["auto_private_schema_ids_excluded_from_shared_bundle"]), 4)
        self.assertEqual(self.interface["complete_bundle_contract"]["schema_count"], 29)
        self.assertEqual(self.interface["complete_bundle_contract"]["policy_count"], 5)
        baseline = self.interface["run_surface_baseline_contract"]
        self.assertEqual(
            baseline["input_count"],
            baseline["mapped_count"]
            + baseline["unmapped_count"]
            + baseline["policy_excluded_count"]
            + baseline["quarantined_count"],
        )
        self.assertEqual(baseline["historical_public_run_events"], 0)
        self.assertEqual(baseline["coverage_state"], "UNKNOWN")
        self.assertTrue(self.interface["consumer_first_contract"]["must_land_before_canonical_publish"])


if __name__ == "__main__":
    unittest.main()
