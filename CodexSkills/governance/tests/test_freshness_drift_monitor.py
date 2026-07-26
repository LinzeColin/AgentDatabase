from __future__ import annotations

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Tuple

from CodexSkills.governance.monitoring.freshness_drift import (
    OBSERVATION_SCHEMA_ID,
    REPORT_SCHEMA_ID,
    FreshnessDriftError,
    append_monitored_promotion_decision,
    build_monitor_contract,
    evaluate_freshness_drift,
    validate_freshness_drift_report,
)
from CodexSkills.governance.promotion.controller import (
    EVAL_RUN_SCHEMA_ID,
    PROMOTION_DECISION_SCHEMA_ID,
    PROMOTION_EVIDENCE_SCHEMA_ID,
    SCORECARD_SCHEMA_ID,
    promotion_ledger_digest,
)
from CodexSkills.governance.tests.test_mechanism_contract import (
    BUNDLE,
    DIGEST_B,
    DIGEST_C,
    DIGEST_D,
    finalize_self_digest,
    representative_artifacts,
    uid,
)
from CodexSkills.governance.tests.test_promotion_controller import (
    BASELINE,
    CANDIDATE_1,
    IDENTITY,
    PromotionFixture,
)
from CodexSkills.governance.tools.build_freshness_drift_monitor import (
    NEXT_PHASE,
    OBSERVATION_SCHEMA_PATH,
    OUTPUT_PATH,
    READINESS_SCHEMA_PATH,
    REPORT_SCHEMA_PATH,
    build_observation_schema,
    build_readiness,
    build_readiness_schema,
    build_report_schema,
)
from CodexSkills.governance.tools.canonical_json import (
    canonical_digest,
    parse_json_bytes,
)
from CodexSkills.governance.tools.validate_mechanism import strict_load


ROOT = Path(__file__).resolve().parents[3]
GOVERNANCE = ROOT / "CodexSkills" / "governance"


class FreshnessFixture:
    def __init__(self) -> None:
        self.promotion = PromotionFixture()
        (
            evidence,
            scorecards,
            eval_runs,
            decision,
        ) = self.promotion.material(
            candidate_uid=CANDIDATE_1,
            baseline_uid=BASELINE,
            suffix_offset=10,
            action="PROMOTE",
            hard_gates_passed=True,
            previous_champion_uid=BASELINE,
            decided_at="2026-07-24T01:00:00.000000Z",
        )
        artifacts = representative_artifacts(
            self.promotion.bundle,
            strict_load(GOVERNANCE / "draft-interface.json"),
        )
        profile = copy.deepcopy(artifacts["eval-profile"])
        profile.update(
            {
                "skill_identity_uid": IDENTITY,
                "dataset_manifest_digests": evidence[
                    "dataset_manifest_digests"
                ],
                "evaluator_manifest_digests": evidence[
                    "evaluator_manifest_digests"
                ],
                "tool_manifest_digest": evidence["tool_manifest_digest"],
                "policy_snapshot_digest": evidence[
                    "policy_snapshot_digest"
                ],
                "minimum_sample_count": 4,
                "freshness_policy": {
                    "max_age_days": 30,
                    "retest_triggers": [
                        "DATASET_CHANGE",
                        "DEPENDENCY_CHANGE",
                        "EVALUATOR_CHANGE",
                        "INCIDENT",
                        "MODEL_CHANGE",
                        "POLICY_CHANGE",
                        "SCORE_DRIFT",
                        "SKILL_CHANGE",
                        "TOOL_CHANGE",
                    ],
                },
            }
        )
        self.profile = profile
        self.profile_digest = canonical_digest(profile)

        old_to_new: Dict[str, str] = {}
        rebound_runs: Dict[str, Mapping[str, Any]] = {}
        for old_digest, old_run in eval_runs.items():
            run = copy.deepcopy(old_run)
            run["eval_profile_digest"] = self.profile_digest
            finalize_self_digest(
                self.promotion.bundle,
                EVAL_RUN_SCHEMA_ID,
                run,
            )
            old_to_new[old_digest] = run["eval_run_digest"]
            rebound_runs[run["eval_run_digest"]] = run

        scorecard = copy.deepcopy(next(iter(scorecards.values())))
        scorecard["eval_profile_digest"] = self.profile_digest
        finalize_self_digest(
            self.promotion.bundle,
            SCORECARD_SCHEMA_ID,
            scorecard,
        )

        evidence = copy.deepcopy(evidence)
        evidence["scorecard_refs"][0]["artifact_digest"] = scorecard[
            "scorecard_digest"
        ]
        for ref in evidence["eval_run_refs"]:
            ref["artifact_digest"] = old_to_new[ref["artifact_digest"]]
        for cell in evidence["causal_matrix"]:
            cell["eval_run_digest"] = old_to_new[cell["eval_run_digest"]]
        finalize_self_digest(
            self.promotion.bundle,
            PROMOTION_EVIDENCE_SCHEMA_ID,
            evidence,
        )
        decision = copy.deepcopy(decision)
        decision["evidence_bundle_digest"] = evidence[
            "evidence_bundle_digest"
        ]
        finalize_self_digest(
            self.promotion.bundle,
            PROMOTION_DECISION_SCHEMA_ID,
            decision,
        )

        self.evidence = evidence
        self.scorecard = scorecard
        self.eval_runs = rebound_runs
        self.decision = decision
        self.observation_schema = build_observation_schema()
        self.report_schema = build_report_schema()
        self.bundle = build_monitor_contract(
            self.promotion.bundle,
            self.observation_schema,
            canonical_digest(self.observation_schema),
            self.report_schema,
            canonical_digest(self.report_schema),
        )

    def observation(
        self,
        *,
        scorecard: Optional[Mapping[str, Any]] = None,
        profile: Optional[Mapping[str, Any]] = None,
        observed_at: str = "2026-07-24T00:00:00.000000Z",
    ) -> Dict[str, Any]:
        score = scorecard or self.scorecard
        selected_profile = profile or self.profile
        value: Dict[str, Any] = {
            "schema_version": OBSERVATION_SCHEMA_ID,
            "protocol_revision": self.bundle.protocol_revision,
            "bundle_digest": BUNDLE,
            "observation_uid": uid("fdo"),
            "skill_version_uid": score["skill_version_uid"],
            "skill_version_record_digest": score[
                "skill_version_record_digest"
            ],
            "scorecard_ref": {
                "scorecard_uid": score["scorecard_uid"],
                "artifact_digest": score["scorecard_digest"],
            },
            "eval_profile_ref": {
                "eval_profile_uid": selected_profile["eval_profile_uid"],
                "artifact_digest": canonical_digest(selected_profile),
            },
            "context": {
                "model_snapshot_digest": score["model_snapshot_digest"],
                "tool_manifest_digest": selected_profile[
                    "tool_manifest_digest"
                ],
                "dataset_manifest_digests": selected_profile[
                    "dataset_manifest_digests"
                ],
                "evaluator_manifest_digests": selected_profile[
                    "evaluator_manifest_digests"
                ],
                "policy_snapshot_digest": selected_profile[
                    "policy_snapshot_digest"
                ],
                "environment_fingerprint_digest": score[
                    "environment_fingerprint_digest"
                ],
            },
            "dependency_context": {
                "baseline": {
                    "dependency_manifest_digest": DIGEST_B,
                },
                "current": {
                    "dependency_manifest_digest": DIGEST_B,
                },
            },
            "behavior_metrics": [
                {
                    "dimension_code": entry["dimension_code"],
                    "score_bps": entry["score_bps"],
                    "evidence_digest": DIGEST_B,
                }
                for entry in score["dimensions"]
            ],
            "latency": {
                "baseline": {
                    "sample_count": 4,
                    "p50_milliseconds": 10,
                    "p95_milliseconds": 20,
                    "max_milliseconds": 30,
                    "evidence_digest": DIGEST_B,
                },
                "current": {
                    "sample_count": 4,
                    "p50_milliseconds": 10,
                    "p95_milliseconds": 20,
                    "max_milliseconds": 30,
                    "evidence_digest": DIGEST_C,
                },
            },
            "critical_incident_count": 0,
            "critical_incident_evidence_digests": [],
            "observed_at": observed_at,
            "actor": "SKILLOPS_FRESHNESS_DRIFT_MONITOR",
            "evidence_bundle_digest": "0" * 64,
        }
        return finalize_self_digest(
            self.bundle,
            OBSERVATION_SCHEMA_ID,
            value,
        )

    def report(
        self,
        observation: Mapping[str, Any],
        *,
        scorecard: Optional[Mapping[str, Any]] = None,
        profile: Optional[Mapping[str, Any]] = None,
        decision_digest: Optional[str] = None,
        mode: str = "PROMOTION_GATE",
    ) -> Dict[str, Any]:
        return evaluate_freshness_drift(
            self.bundle,
            eval_profile=profile or self.profile,
            scorecard=scorecard or self.scorecard,
            observation=observation,
            report_uid=uid("fdr"),
            mode=mode,
            promotion_decision_digest=(
                self.decision["decision_digest"]
                if decision_digest is None and mode == "PROMOTION_GATE"
                else decision_digest
            ),
            expected_bundle_digest=BUNDLE,
        )

    def rebind_scorecard(
        self,
        scorecard: Mapping[str, Any],
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        evidence = copy.deepcopy(self.evidence)
        evidence["scorecard_refs"][0]["artifact_digest"] = scorecard[
            "scorecard_digest"
        ]
        finalize_self_digest(
            self.promotion.bundle,
            PROMOTION_EVIDENCE_SCHEMA_ID,
            evidence,
        )
        decision = copy.deepcopy(self.decision)
        decision["evidence_bundle_digest"] = evidence[
            "evidence_bundle_digest"
        ]
        finalize_self_digest(
            self.promotion.bundle,
            PROMOTION_DECISION_SCHEMA_ID,
            decision,
        )
        return evidence, decision

    def append(
        self,
        *,
        profile: Mapping[str, Any],
        observation: Mapping[str, Any],
        report: Mapping[str, Any],
        evidence: Mapping[str, Any],
        scorecard: Mapping[str, Any],
        decision: Mapping[str, Any],
    ):
        return append_monitored_promotion_decision(
            self.bundle,
            self.promotion.registry,
            eval_profiles_by_digest={
                canonical_digest(profile): profile,
            },
            observations_by_digest={
                observation["evidence_bundle_digest"]: observation,
            },
            reports_by_digest={
                report["evidence_bundle_digest"]: report,
            },
            evidence_by_digest={
                evidence["evidence_bundle_digest"]: evidence,
            },
            scorecards_by_digest={
                scorecard["scorecard_digest"]: scorecard,
            },
            eval_runs_by_digest=self.eval_runs,
            existing_decisions=(),
            decision=decision,
            expected_predecessor_ledger_digest=promotion_ledger_digest(
                self.promotion.registry.registry_snapshot_digest,
                (),
            ),
            expected_bundle_digest=BUNDLE,
        )


class FreshnessDriftMonitorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = FreshnessFixture()

    def test_clear_report_is_canonical_and_can_delegate_promotion(self):
        observation = self.fixture.observation()
        report = self.fixture.report(observation)
        self.assertEqual([], report["alerts"])
        self.assertEqual("FRESH", report["freshness"]["state"])
        self.assertEqual("PASS", report["promotion_gate"]["status"])
        self.assertTrue(
            report["promotion_gate"][
                "scorecard_effective_promotion_eligible"
            ]
        )
        self.assertFalse(
            report["promotion_gate"][
                "stale_score_independent_promotion_permitted"
            ]
        )
        result = self.fixture.append(
            profile=self.fixture.profile,
            observation=observation,
            report=report,
            evidence=self.fixture.evidence,
            scorecard=self.fixture.scorecard,
            decision=self.fixture.decision,
        )
        self.assertEqual(1, result.promotion_result.ledger_view.promote_count)
        self.assertEqual(
            (report["evidence_bundle_digest"],),
            result.report_digests,
        )
        self.assertEqual(
            report,
            json.loads(result.canonical_report_bytes[0]),
        )
        self.assertEqual(64, len(result.authorization_digest))

    def test_fresh_label_with_expired_date_cannot_promote(self):
        scorecard = copy.deepcopy(self.fixture.scorecard)
        scorecard["freshness_valid_until"] = "2026-07-23"
        finalize_self_digest(
            self.fixture.bundle,
            SCORECARD_SCHEMA_ID,
            scorecard,
        )
        evidence, decision = self.fixture.rebind_scorecard(scorecard)
        observation = self.fixture.observation(scorecard=scorecard)
        report = self.fixture.report(
            observation,
            scorecard=scorecard,
            decision_digest=decision["decision_digest"],
        )
        self.assertEqual("FRESH", scorecard["freshness_state"])
        self.assertEqual("STALE", report["freshness"]["state"])
        self.assertIn(
            "SCORECARD_VALIDITY_EXPIRED",
            [alert["code"] for alert in report["alerts"]],
        )
        self.assertEqual("BLOCKED", report["promotion_gate"]["status"])
        with self.assertRaisesRegex(
            FreshnessDriftError,
            "FRESHNESS_DRIFT_PROMOTION_GATE_BLOCKED",
        ):
            self.fixture.append(
                profile=self.fixture.profile,
                observation=observation,
                report=report,
                evidence=evidence,
                scorecard=scorecard,
                decision=decision,
            )

    def test_max_age_boundary_is_inclusive_then_stale(self):
        profile = copy.deepcopy(self.fixture.profile)
        profile["freshness_policy"]["max_age_days"] = 1
        scorecard = copy.deepcopy(self.fixture.scorecard)
        scorecard["eval_profile_digest"] = canonical_digest(profile)
        scorecard["freshness_valid_until"] = "2026-08-22"
        finalize_self_digest(
            self.fixture.bundle,
            SCORECARD_SCHEMA_ID,
            scorecard,
        )
        exact = self.fixture.observation(
            scorecard=scorecard,
            profile=profile,
            observed_at="2026-07-24T00:00:00.000000Z",
        )
        exact_report = self.fixture.report(
            exact,
            scorecard=scorecard,
            profile=profile,
        )
        self.assertEqual("FRESH", exact_report["freshness"]["state"])
        self.assertNotIn(
            "SCORECARD_MAX_AGE_EXCEEDED",
            [alert["code"] for alert in exact_report["alerts"]],
        )

        late = self.fixture.observation(
            scorecard=scorecard,
            profile=profile,
            observed_at="2026-07-24T00:00:00.000001Z",
        )
        late_report = self.fixture.report(
            late,
            scorecard=scorecard,
            profile=profile,
        )
        self.assertEqual("STALE", late_report["freshness"]["state"])
        self.assertIn(
            "SCORECARD_MAX_AGE_EXCEEDED",
            [alert["code"] for alert in late_report["alerts"]],
        )

    def test_behavior_change_emits_blocking_alert(self):
        observation = self.fixture.observation()
        observation["behavior_metrics"][0]["score_bps"] -= 1
        finalize_self_digest(
            self.fixture.bundle,
            OBSERVATION_SCHEMA_ID,
            observation,
        )
        report = self.fixture.report(observation)
        behavior_alert = next(
            alert
            for alert in report["alerts"]
            if alert["code"] == "BEHAVIOR_SCORE_CHANGE"
        )
        self.assertEqual(
            ["EFFICIENCY"],
            behavior_alert["subject_codes"],
        )
        self.assertEqual("BLOCKED", report["promotion_gate"]["status"])
        self.assertIn("SCORE_DRIFT", report["retest_trigger_codes"])

    def test_latency_regression_and_sample_shortfall_both_alert(self):
        observation = self.fixture.observation()
        observation["latency"]["baseline"]["sample_count"] = 3
        observation["latency"]["current"].update(
            {
                "sample_count": 3,
                "p50_milliseconds": 15,
                "p95_milliseconds": 21,
                "max_milliseconds": 31,
            }
        )
        finalize_self_digest(
            self.fixture.bundle,
            OBSERVATION_SCHEMA_ID,
            observation,
        )
        report = self.fixture.report(observation)
        codes = {alert["code"] for alert in report["alerts"]}
        self.assertIn("LATENCY_P95_REGRESSION", codes)
        self.assertIn("LATENCY_SAMPLE_INSUFFICIENT", codes)
        sample_alert = next(
            alert
            for alert in report["alerts"]
            if alert["code"] == "LATENCY_SAMPLE_INSUFFICIENT"
        )
        self.assertEqual(
            ["BASELINE_SAMPLE_COUNT", "CURRENT_SAMPLE_COUNT"],
            sample_alert["subject_codes"],
        )
        self.assertTrue(
            report["promotion_gate"]["re_evaluation_required"]
        )

    def test_context_incident_and_profile_trigger_gap_are_closed(self):
        profile = copy.deepcopy(self.fixture.profile)
        profile["freshness_policy"]["retest_triggers"].remove(
            "TOOL_CHANGE"
        )
        scorecard = copy.deepcopy(self.fixture.scorecard)
        scorecard["eval_profile_digest"] = canonical_digest(profile)
        finalize_self_digest(
            self.fixture.bundle,
            SCORECARD_SCHEMA_ID,
            scorecard,
        )
        observation = self.fixture.observation(
            scorecard=scorecard,
            profile=profile,
        )
        observation["context"].update(
            {
                "model_snapshot_digest": "1" * 64,
                "tool_manifest_digest": "2" * 64,
                "dataset_manifest_digests": ["3" * 64],
                "evaluator_manifest_digests": ["4" * 64],
                "policy_snapshot_digest": "5" * 64,
                "environment_fingerprint_digest": "6" * 64,
            }
        )
        observation["dependency_context"]["current"][
            "dependency_manifest_digest"
        ] = "7" * 64
        observation["critical_incident_count"] = 1
        observation["critical_incident_evidence_digests"] = ["8" * 64]
        finalize_self_digest(
            self.fixture.bundle,
            OBSERVATION_SCHEMA_ID,
            observation,
        )
        report = self.fixture.report(
            observation,
            scorecard=scorecard,
            profile=profile,
        )
        codes = {alert["code"] for alert in report["alerts"]}
        expected = {
            "DATASET_CHANGE",
            "DEPENDENCY_CHANGE",
            "ENVIRONMENT_CHANGE",
            "EVALUATOR_CHANGE",
            "INCIDENT_OBSERVED",
            "MODEL_CHANGE",
            "POLICY_CHANGE",
            "PROFILE_RETEST_TRIGGER_GAP",
            "TOOL_CHANGE",
        }
        self.assertTrue(expected.issubset(codes))
        self.assertEqual(
            ["TOOL_CHANGE"],
            report["missing_profile_trigger_codes"],
        )

    def test_observation_digest_reference_and_time_tamper_fail_closed(self):
        observation = self.fixture.observation()
        observation["scorecard_ref"]["artifact_digest"] = "f" * 64
        finalize_self_digest(
            self.fixture.bundle,
            OBSERVATION_SCHEMA_ID,
            observation,
        )
        with self.assertRaisesRegex(
            FreshnessDriftError,
            "FRESHNESS_DRIFT_REFERENCE_CLOSURE_MISMATCH",
        ):
            self.fixture.report(observation)

        observation = self.fixture.observation(
            observed_at="2026-07-22T23:59:59.999999Z"
        )
        with self.assertRaisesRegex(
            FreshnessDriftError,
            "FRESHNESS_DRIFT_TIME_ORDER_INVALID",
        ):
            self.fixture.report(observation)

    def test_fake_clear_report_fails_exact_recomputation(self):
        observation = self.fixture.observation()
        observation["behavior_metrics"][0]["score_bps"] -= 1
        finalize_self_digest(
            self.fixture.bundle,
            OBSERVATION_SCHEMA_ID,
            observation,
        )
        report = self.fixture.report(observation)
        report["alerts"] = []
        report["retest_trigger_codes"] = []
        report["missing_profile_trigger_codes"] = []
        report["promotion_gate"].update(
            {
                "status": "PASS",
                "scorecard_effective_promotion_eligible": True,
                "re_evaluation_required": False,
            }
        )
        finalize_self_digest(
            self.fixture.bundle,
            REPORT_SCHEMA_ID,
            report,
        )
        with self.assertRaisesRegex(
            FreshnessDriftError,
            "FRESHNESS_DRIFT_REPORT_RECOMPUTATION_MISMATCH",
        ):
            validate_freshness_drift_report(
                self.fixture.bundle,
                eval_profile=self.fixture.profile,
                scorecard=self.fixture.scorecard,
                observation=observation,
                report=report,
                expected_bundle_digest=BUNDLE,
            )

    def test_decision_binding_and_decision_time_are_enforced(self):
        observation = self.fixture.observation()
        wrong_report = self.fixture.report(
            observation,
            decision_digest="f" * 64,
        )
        with self.assertRaisesRegex(
            FreshnessDriftError,
            "FRESHNESS_DRIFT_PROMOTION_GATE_BLOCKED",
        ):
            self.fixture.append(
                profile=self.fixture.profile,
                observation=observation,
                report=wrong_report,
                evidence=self.fixture.evidence,
                scorecard=self.fixture.scorecard,
                decision=self.fixture.decision,
            )

        late_observation = self.fixture.observation(
            observed_at="2026-07-24T02:00:00.000000Z"
        )
        late_report = self.fixture.report(late_observation)
        with self.assertRaisesRegex(
            FreshnessDriftError,
            "FRESHNESS_DRIFT_PROMOTION_GATE_BLOCKED",
        ):
            self.fixture.append(
                profile=self.fixture.profile,
                observation=late_observation,
                report=late_report,
                evidence=self.fixture.evidence,
                scorecard=self.fixture.scorecard,
                decision=self.fixture.decision,
            )

    def test_builder_is_byte_equivalent_and_non_active(self):
        process = subprocess.run(
            [
                sys.executable,
                "-B",
                str(
                    GOVERNANCE
                    / "tools"
                    / "build_freshness_drift_monitor.py"
                ),
                "--check",
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertIn(
            "FRESHNESS_DRIFT_MONITOR_BYTE_EQUIVALENT",
            process.stdout,
        )
        self.assertEqual(
            build_observation_schema(),
            parse_json_bytes(OBSERVATION_SCHEMA_PATH.read_bytes()),
        )
        self.assertEqual(
            build_report_schema(),
            parse_json_bytes(REPORT_SCHEMA_PATH.read_bytes()),
        )
        self.assertEqual(
            build_readiness_schema(),
            parse_json_bytes(READINESS_SCHEMA_PATH.read_bytes()),
        )
        readiness = build_readiness()
        self.assertEqual(
            readiness,
            parse_json_bytes(OUTPUT_PATH.read_bytes()),
        )
        self.assertEqual(
            "DRAFT_NON_ACTIVE_FRESHNESS_DRIFT_MONITOR_READY",
            readiness["status"],
        )
        self.assertEqual(NEXT_PHASE, readiness["next_phase"])
        self.assertFalse(
            readiness["monitor_contract"][
                "stale_score_independent_promotion_permitted"
            ]
        )
        self.assertFalse(
            readiness["registry_observation"][
                "real_monitor_execution_permitted"
            ]
        )
        self.assertFalse((ROOT / "CodexSkills" / "VERSION").exists())
        candidate_ids = set(self.promotion_bundle_schema_ids())
        self.assertNotIn(OBSERVATION_SCHEMA_ID, candidate_ids)
        self.assertNotIn(REPORT_SCHEMA_ID, candidate_ids)

    def promotion_bundle_schema_ids(self):
        return self.fixture.promotion.bundle.schemas


if __name__ == "__main__":
    unittest.main()
