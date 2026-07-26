from __future__ import annotations

import copy
import subprocess
import unittest
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

from CodexSkills.governance.release.policy_protection import (
    AUDIT_REQUIREMENTS,
    OBSERVATION_SCHEMA_ID,
    REPORT_SCHEMA_ID,
    EvaluatorReleaseProtectionError,
    append_release_protected_promotion_decision,
    build_protection_contract,
    evaluate_evaluator_release_protection,
    validate_evaluator_release_protection_report,
)
from CodexSkills.governance.tests.test_freshness_drift_monitor import (
    FreshnessFixture,
)
from CodexSkills.governance.tests.test_mechanism_contract import (
    BUNDLE,
    finalize_self_digest,
    uid,
)
from CodexSkills.governance.tools.build_evaluator_release_protection import (
    M056_CONTROLLER_PATH,
    M056_CONTROLLER_RAW_SHA256,
    NEXT_PHASE,
    OBSERVATION_SCHEMA_PATH,
    OUTPUT_PATH,
    READINESS_SCHEMA_PATH,
    REPORT_SCHEMA_PATH,
    VERSION_POLICY_PATH,
    VERSION_POLICY_SHA256,
    build_observation_schema,
    build_readiness,
    build_readiness_schema,
    build_report_schema,
    render_observation_schema,
    render_readiness,
    render_readiness_schema,
    render_report_schema,
)
from CodexSkills.governance.tools.canonical_json import (
    canonical_digest,
    parse_json_bytes,
)
from CodexSkills.governance.tools.validate_mechanism import (
    ContractError,
    scan_public_value,
)


ROOT = Path(__file__).resolve().parents[3]
GOVERNANCE = ROOT / "CodexSkills" / "governance"


def _load(path: Path) -> Mapping[str, Any]:
    value = parse_json_bytes(path.read_bytes())
    if not isinstance(value, dict):
        raise AssertionError(path)
    return value


class ProtectionFixture:
    def __init__(self) -> None:
        self.freshness = FreshnessFixture()
        self.observation_schema = build_observation_schema()
        self.report_schema = build_report_schema()
        self.bundle = build_protection_contract(
            self.freshness.bundle,
            self.observation_schema,
            canonical_digest(self.observation_schema),
            self.report_schema,
            canonical_digest(self.report_schema),
        )
        self.version_policy = _load(VERSION_POLICY_PATH)

    def release_snapshot(self) -> Dict[str, Any]:
        codes = (
            ("NOTIFICATION", "notification:v1", "1"),
            ("PUBLIC_VALUE", "public-value:v2", "2"),
            ("RETENTION", "retention:v3", "3"),
            ("SOURCE_MATERIAL", "source-material:v1", "4"),
            ("VERSION", "version:v2", "5"),
        )
        return {
            "policy_snapshot_digest": self.freshness.evidence[
                "policy_snapshot_digest"
            ],
            "policy_descriptors": [
                {
                    "policy_code": code,
                    "policy_id": (
                        "urn:linzecolin:agentdatabase:skillops:policy:"
                        + suffix
                    ),
                    "policy_sha256": digit * 64,
                }
                for code, suffix, digit in codes
            ],
            "promotion_controller": {
                "canonical_path": M056_CONTROLLER_PATH,
                "artifact_digest": M056_CONTROLLER_RAW_SHA256,
            },
        }

    def isolation_audit(self) -> Dict[str, Any]:
        return {
            "audit_uid": uid("era"),
            "optimizer_actor_ref": "OPTIMIZER_PRIMARY",
            "evaluator_actor_ref": "EVALUATOR_INDEPENDENT",
            "release_actor_ref": "RELEASE_AUTHORIZER_PRIMARY",
            "roles_distinct": True,
            "attempts": [
                {
                    "attempt_code": attempt_code,
                    "resource_code": resource_code,
                    "operation": operation,
                    "outcome": "DENIED",
                    "evidence_digest": format(index, "x") * 64,
                }
                for index, (
                    attempt_code,
                    resource_code,
                    operation,
                ) in enumerate(AUDIT_REQUIREMENTS, start=1)
            ],
            "forbidden_attempt_count": len(AUDIT_REQUIREMENTS),
            "denied_attempt_count": len(AUDIT_REQUIREMENTS),
            "allowed_forbidden_attempt_count": 0,
            "completed_at": "2026-07-24T00:30:00.000000Z",
        }

    def observation(
        self,
        *,
        proposed_profile: Optional[Mapping[str, Any]] = None,
        proposed_snapshot: Optional[Mapping[str, Any]] = None,
        source_role: str = "OPTIMIZER",
    ) -> Dict[str, Any]:
        audit = self.isolation_audit()
        actor_ref = {
            "OPTIMIZER": audit["optimizer_actor_ref"],
            "INDEPENDENT_EVALUATOR": audit["evaluator_actor_ref"],
            "RELEASE_AUTHORIZER": audit["release_actor_ref"],
        }[source_role]
        baseline_snapshot = self.release_snapshot()
        value: Dict[str, Any] = {
            "schema_version": OBSERVATION_SCHEMA_ID,
            "protocol_revision": self.bundle.protocol_revision,
            "bundle_digest": BUNDLE,
            "observation_uid": uid("ero"),
            "promotion_decision_ref": {
                "decision_digest": self.freshness.decision[
                    "decision_digest"
                ],
            },
            "promotion_evidence_ref": {
                "artifact_digest": self.freshness.evidence[
                    "evidence_bundle_digest"
                ],
            },
            "baseline_eval_profiles": [
                copy.deepcopy(self.freshness.profile)
            ],
            "proposed_eval_profiles": [
                copy.deepcopy(
                    proposed_profile or self.freshness.profile
                )
            ],
            "baseline_release_snapshot": baseline_snapshot,
            "proposed_release_snapshot": copy.deepcopy(
                proposed_snapshot or baseline_snapshot
            ),
            "change_origin": {
                "source_role": source_role,
                "actor_ref": actor_ref,
            },
            "isolation_audit": audit,
            "optimizer_evaluator_isolation_digest": canonical_digest(
                audit
            ),
            "observed_at": "2026-07-24T00:30:00.000000Z",
            "actor": "SKILLOPS_EVALUATOR_RELEASE_GUARD",
            "evidence_bundle_digest": "0" * 64,
        }
        return finalize_self_digest(
            self.bundle,
            OBSERVATION_SCHEMA_ID,
            value,
        )

    def refinalize(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        observation["optimizer_evaluator_isolation_digest"] = (
            canonical_digest(observation["isolation_audit"])
        )
        return finalize_self_digest(
            self.bundle,
            OBSERVATION_SCHEMA_ID,
            observation,
        )

    def report(self, observation: Mapping[str, Any]) -> Dict[str, Any]:
        return evaluate_evaluator_release_protection(
            self.bundle,
            observation=observation,
            promotion_evidence=self.freshness.evidence,
            decision=self.freshness.decision,
            scorecards_by_digest={
                self.freshness.scorecard["scorecard_digest"]:
                self.freshness.scorecard,
            },
            report_uid=uid("err"),
            version_policy=self.version_policy,
            expected_version_policy_sha256=VERSION_POLICY_SHA256,
            expected_promotion_controller_path=M056_CONTROLLER_PATH,
            expected_promotion_controller_digest=(
                M056_CONTROLLER_RAW_SHA256
            ),
            expected_bundle_digest=BUNDLE,
        )

    def append(
        self,
        observation: Mapping[str, Any],
        report: Mapping[str, Any],
    ):
        freshness_observation = self.freshness.observation()
        freshness_report = self.freshness.report(
            freshness_observation
        )
        from CodexSkills.governance.promotion.controller import (
            promotion_ledger_digest,
        )

        return append_release_protected_promotion_decision(
            self.bundle,
            self.freshness.promotion.registry,
            eval_profiles_by_digest={
                self.freshness.profile_digest:
                self.freshness.profile,
            },
            freshness_observations_by_digest={
                freshness_observation["evidence_bundle_digest"]:
                freshness_observation,
            },
            freshness_reports_by_digest={
                freshness_report["evidence_bundle_digest"]:
                freshness_report,
            },
            protection_observations_by_digest={
                observation["evidence_bundle_digest"]: observation,
            },
            protection_reports_by_digest={
                report["evidence_bundle_digest"]: report,
            },
            evidence_by_digest={
                self.freshness.evidence["evidence_bundle_digest"]:
                self.freshness.evidence,
            },
            scorecards_by_digest={
                self.freshness.scorecard["scorecard_digest"]:
                self.freshness.scorecard,
            },
            eval_runs_by_digest=self.freshness.eval_runs,
            existing_decisions=(),
            decision=self.freshness.decision,
            version_policy=self.version_policy,
            expected_version_policy_sha256=VERSION_POLICY_SHA256,
            expected_promotion_controller_path=M056_CONTROLLER_PATH,
            expected_promotion_controller_digest=(
                M056_CONTROLLER_RAW_SHA256
            ),
            expected_predecessor_ledger_digest=promotion_ledger_digest(
                self.freshness.promotion.registry.registry_snapshot_digest,
                (),
            ),
            expected_bundle_digest=BUNDLE,
        )


class EvaluatorReleaseProtectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = ProtectionFixture()

    def test_unchanged_protected_surfaces_pass_and_delegate(self):
        observation = self.fixture.observation()
        report = self.fixture.report(observation)
        self.assertEqual("NONE", report["impact"])
        self.assertEqual([], report["detected_changes"])
        self.assertEqual([], report["major_trigger_codes"])
        self.assertEqual("PASS", report["promotion_gate"]["status"])
        self.assertTrue(
            report["promotion_gate"]["m058_delegation_permitted"]
        )
        self.assertFalse(
            report["promotion_gate"][
                "optimizer_self_improvement_permitted"
            ]
        )
        result = self.fixture.append(observation, report)
        self.assertEqual(
            1,
            result.monitored_result.promotion_result.ledger_view.promote_count,
        )
        self.assertEqual(
            report["evidence_bundle_digest"],
            result.protection_report_digest,
        )

    def test_optimizer_evaluator_change_is_major_and_blocked(self):
        proposed = copy.deepcopy(self.fixture.freshness.profile)
        proposed["evaluator_manifest_digests"] = ["8" * 64]
        observation = self.fixture.observation(
            proposed_profile=proposed
        )
        report = self.fixture.report(observation)
        self.assertEqual("MAJOR", report["impact"])
        self.assertEqual(
            ["EVALUATOR_OR_HOLDOUT_CHANGE"],
            report["major_trigger_codes"],
        )
        self.assertEqual(
            ["EVALUATOR_MANIFEST_CHANGE"],
            [
                entry["change_code"]
                for entry in report["detected_changes"]
            ],
        )
        self.assertEqual("BLOCKED", report["promotion_gate"]["status"])
        self.assertEqual(
            "OPTIMIZER_PROTECTED_CHANGE_BLOCKED",
            report["promotion_gate"]["reason_code"],
        )
        with self.assertRaisesRegex(
            EvaluatorReleaseProtectionError,
            "EVALUATOR_RELEASE_PROMOTION_GATE_BLOCKED",
        ):
            self.fixture.append(observation, report)

    def test_judge_weights_hard_gates_and_controller_are_protected(self):
        cases = []
        weights = copy.deepcopy(self.fixture.freshness.profile)
        weights["dimension_weights_bps"][0]["weight_bps"] += 1
        weights["dimension_weights_bps"][1]["weight_bps"] -= 1
        cases.append(("JUDGE_WEIGHT_CHANGE", weights, None))

        controller = self.fixture.release_snapshot()
        controller["promotion_controller"]["artifact_digest"] = "9" * 64
        cases.append(
            (
                "PROMOTION_CONTROLLER_CHANGE",
                self.fixture.freshness.profile,
                controller,
            )
        )
        for expected, profile, snapshot in cases:
            with self.subTest(expected=expected):
                observation = self.fixture.observation(
                    proposed_profile=profile,
                    proposed_snapshot=snapshot,
                )
                report = self.fixture.report(observation)
                self.assertEqual("MAJOR", report["impact"])
                self.assertIn(
                    "HARD_GATE_CHANGE",
                    report["major_trigger_codes"],
                )
                self.assertIn(
                    expected,
                    [
                        entry["change_code"]
                        for entry in report["detected_changes"]
                    ],
                )
                self.assertEqual(
                    "BLOCKED",
                    report["promotion_gate"]["status"],
                )
        gates = copy.deepcopy(self.fixture.freshness.profile)
        gates["hard_gate_codes"] = list(
            reversed(gates["hard_gate_codes"])
        )
        observation = self.fixture.observation(
            proposed_profile=gates
        )
        with self.assertRaisesRegex(
            EvaluatorReleaseProtectionError,
            "EVALUATOR_RELEASE_PROPOSED_PROFILE_ENTRY_INVALID",
        ):
            self.fixture.report(observation)

    def test_each_release_policy_change_maps_to_locked_major_trigger(self):
        expected = {
            "NOTIFICATION": "NOTIFICATION_POLICY_CHANGE",
            "PUBLIC_VALUE": "PRIVACY_POLICY_CHANGE",
            "RETENTION": "RETENTION_POLICY_CHANGE",
            "SOURCE_MATERIAL": "SOURCE_LAYOUT_CHANGE",
            "VERSION": "HARD_GATE_CHANGE",
        }
        for index, (policy_code, trigger) in enumerate(
            expected.items()
        ):
            proposed = self.fixture.release_snapshot()
            proposed["policy_descriptors"][index][
                "policy_sha256"
            ] = "a" * 64
            observation = self.fixture.observation(
                proposed_snapshot=proposed
            )
            report = self.fixture.report(observation)
            with self.subTest(policy_code=policy_code):
                self.assertEqual("MAJOR", report["impact"])
                self.assertEqual([trigger], report["major_trigger_codes"])
                self.assertTrue(
                    report["promotion_gate"][
                        "separate_major_release_required"
                    ]
                )

    def test_independent_change_still_requires_separate_major_release(self):
        proposed = copy.deepcopy(self.fixture.freshness.profile)
        proposed["judge_rubric_digest"] = "9" * 64
        observation = self.fixture.observation(
            proposed_profile=proposed,
            source_role="INDEPENDENT_EVALUATOR",
        )
        report = self.fixture.report(observation)
        self.assertEqual("MAJOR", report["impact"])
        self.assertEqual(
            "INDEPENDENT_MAJOR_RELEASE_REQUIRED",
            report["promotion_gate"]["reason_code"],
        )
        self.assertFalse(
            report["promotion_gate"][
                "protected_release_write_permitted"
            ]
        )
        self.assertFalse(
            report["promotion_gate"]["m058_delegation_permitted"]
        )

    def test_access_denial_audit_is_exact_and_cannot_be_forged(self):
        duplicate = self.fixture.observation()
        duplicate["isolation_audit"]["attempts"][1][
            "evidence_digest"
        ] = duplicate["isolation_audit"]["attempts"][0][
            "evidence_digest"
        ]
        self.fixture.refinalize(duplicate)
        with self.assertRaisesRegex(
            EvaluatorReleaseProtectionError,
            "EVALUATOR_RELEASE_AUDIT_EVIDENCE_REUSED",
        ):
            self.fixture.report(duplicate)

        wrong_actor = self.fixture.observation()
        wrong_actor["change_origin"]["actor_ref"] = (
            "EVALUATOR_INDEPENDENT"
        )
        self.fixture.refinalize(wrong_actor)
        with self.assertRaisesRegex(
            EvaluatorReleaseProtectionError,
            "EVALUATOR_RELEASE_CHANGE_ORIGIN_ACTOR_MISMATCH",
        ):
            self.fixture.report(wrong_actor)

        allowed = self.fixture.observation()
        allowed["isolation_audit"]["attempts"][0]["outcome"] = "ALLOWED"
        self.fixture.refinalize(allowed)
        with self.assertRaisesRegex(
            EvaluatorReleaseProtectionError,
            "EVALUATOR_RELEASE_OBSERVATION_INVALID",
        ):
            self.fixture.report(allowed)

    def test_reference_time_and_baseline_controller_closure_fail_closed(self):
        wrong_controller = self.fixture.observation()
        wrong_controller["baseline_release_snapshot"][
            "promotion_controller"
        ]["artifact_digest"] = "f" * 64
        self.fixture.refinalize(wrong_controller)
        with self.assertRaisesRegex(
            EvaluatorReleaseProtectionError,
            "EVALUATOR_RELEASE_PROTECTED_SNAPSHOT_CLOSURE_MISMATCH",
        ):
            self.fixture.report(wrong_controller)

        late = self.fixture.observation()
        late["observed_at"] = "2026-07-24T02:00:00.000000Z"
        late["isolation_audit"][
            "completed_at"
        ] = "2026-07-24T02:00:00.000000Z"
        self.fixture.refinalize(late)
        with self.assertRaisesRegex(
            EvaluatorReleaseProtectionError,
            "EVALUATOR_RELEASE_OBSERVATION_AFTER_DECISION",
        ):
            self.fixture.report(late)

    def test_report_and_version_policy_claims_are_recomputed(self):
        proposed = copy.deepcopy(self.fixture.freshness.profile)
        proposed["sealed_holdout_manifest_digest"] = "9" * 64
        observation = self.fixture.observation(
            proposed_profile=proposed
        )
        report = self.fixture.report(observation)
        forged = copy.deepcopy(report)
        forged["impact"] = "NONE"
        forged["promotion_gate"]["status"] = "PASS"
        forged["promotion_gate"]["m058_delegation_permitted"] = True
        finalize_self_digest(
            self.fixture.bundle,
            REPORT_SCHEMA_ID,
            forged,
        )
        with self.assertRaisesRegex(
            EvaluatorReleaseProtectionError,
            "EVALUATOR_RELEASE_REPORT_RECOMPUTATION_MISMATCH",
        ):
            validate_evaluator_release_protection_report(
                self.fixture.bundle,
                observation=observation,
                promotion_evidence=self.fixture.freshness.evidence,
                decision=self.fixture.freshness.decision,
                scorecards_by_digest={
                    self.fixture.freshness.scorecard[
                        "scorecard_digest"
                    ]: self.fixture.freshness.scorecard,
                },
                report=forged,
                version_policy=self.fixture.version_policy,
                expected_version_policy_sha256=VERSION_POLICY_SHA256,
                expected_promotion_controller_path=M056_CONTROLLER_PATH,
                expected_promotion_controller_digest=(
                    M056_CONTROLLER_RAW_SHA256
                ),
                expected_bundle_digest=BUNDLE,
            )
        tampered_policy = copy.deepcopy(self.fixture.version_policy)
        tampered_policy["major_trigger_codes"].remove(
            "HARD_GATE_CHANGE"
        )
        with self.assertRaisesRegex(
            EvaluatorReleaseProtectionError,
            "EVALUATOR_RELEASE_VERSION_POLICY_INVALID",
        ):
            evaluate_evaluator_release_protection(
                self.fixture.bundle,
                observation=observation,
                promotion_evidence=self.fixture.freshness.evidence,
                decision=self.fixture.freshness.decision,
                scorecards_by_digest={
                    self.fixture.freshness.scorecard[
                        "scorecard_digest"
                    ]: self.fixture.freshness.scorecard,
                },
                report_uid=uid("err"),
                version_policy=tampered_policy,
                expected_version_policy_sha256=VERSION_POLICY_SHA256,
                expected_promotion_controller_path=M056_CONTROLLER_PATH,
                expected_promotion_controller_digest=(
                    M056_CONTROLLER_RAW_SHA256
                ),
                expected_bundle_digest=BUNDLE,
            )

    def test_generated_schemas_and_readiness_are_exact_public_contracts(self):
        self.assertEqual(
            render_observation_schema(),
            OBSERVATION_SCHEMA_PATH.read_bytes(),
        )
        self.assertEqual(
            render_report_schema(),
            REPORT_SCHEMA_PATH.read_bytes(),
        )
        self.assertEqual(
            render_readiness_schema(),
            READINESS_SCHEMA_PATH.read_bytes(),
        )
        self.assertEqual(render_readiness(), OUTPUT_PATH.read_bytes())
        self.assertEqual(
            build_observation_schema(),
            _load(OBSERVATION_SCHEMA_PATH),
        )
        self.assertEqual(
            build_report_schema(),
            _load(REPORT_SCHEMA_PATH),
        )
        self.assertEqual(
            build_readiness_schema(),
            _load(READINESS_SCHEMA_PATH),
        )
        readiness = build_readiness()
        self.assertEqual(readiness, _load(OUTPUT_PATH))
        self.assertEqual(NEXT_PHASE, readiness["next_phase"])
        self.assertFalse(
            readiness["nonmutation"]["release_write_permitted"]
        )
        self.assertFalse(
            readiness["registry_observation"][
                "real_protection_execution_permitted"
            ]
        )
        scan_public_value(
            readiness,
            self.fixture.bundle.policies,
        )

    def test_schema_trust_and_candidate_nonmutation_are_enforced(self):
        tampered = build_observation_schema()
        tampered["title"] = "tampered"
        with self.assertRaisesRegex(
            EvaluatorReleaseProtectionError,
            "EVALUATOR_RELEASE_SCHEMA_TRUST_MISMATCH",
        ):
            build_protection_contract(
                self.fixture.freshness.bundle,
                tampered,
                canonical_digest(build_observation_schema()),
                build_report_schema(),
                canonical_digest(build_report_schema()),
            )
        self.assertFalse((ROOT / "CodexSkills" / "VERSION").exists())
        changed = subprocess.run(
            [
                "git",
                "diff",
                "--name-only",
                "HEAD",
                "--",
                "CodexSkills/registry/auto",
                "OpenAIDatabase",
                "CodexSkills/VERSION",
            ],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
            text=True,
        ).stdout
        self.assertEqual("", changed)


if __name__ == "__main__":
    unittest.main()
