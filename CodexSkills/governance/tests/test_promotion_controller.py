from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path
from typing import Any, Dict, Mapping, Tuple

from CodexSkills.governance.promotion.controller import (
    EVAL_RUN_SCHEMA_ID,
    PROMOTION_DECISION_SCHEMA_ID,
    PROMOTION_EVIDENCE_SCHEMA_ID,
    REGISTRY_SNAPSHOT_SCHEMA_ID,
    SCORECARD_SCHEMA_ID,
    PromotionControllerError,
    append_promotion_decision,
    build_registry_view,
    promotion_ledger_digest,
    replay_promotion_ledger,
)
from CodexSkills.governance.tests.test_mechanism_contract import (
    BUNDLE,
    DIGEST_B,
    DIGEST_C,
    DIGEST_D,
    HARD_GATES,
    PROTOCOL,
    SRV,
    TS,
    artifact,
    finalize_self_digest,
    representative_artifacts,
    sid,
    uid,
)
from CodexSkills.governance.tools.canonical_json import (
    canonical_digest,
    parse_json_bytes,
)
from CodexSkills.governance.tools.build_promotion_controller import (
    CONTROLLER_PATH,
    NEXT_PHASE,
    OUTPUT_PATH,
    SCHEMA_PATH,
    build_readiness,
    build_schema,
)
from CodexSkills.governance.tools.validate_mechanism import (
    load_draft_contract,
    strict_load,
)


ROOT = Path(__file__).resolve().parents[3]
GOVERNANCE = ROOT / "CodexSkills" / "governance"
INTERFACE = GOVERNANCE / "draft-interface.json"

CANDIDATE_1 = uid("skv", "0" * 25 + "1")
CANDIDATE_2 = uid("skv", "0" * 25 + "2")
BASELINE = uid("skv")
IDENTITY = uid("ski")
INSTANCE = uid("skinst")


def _wrap(record: Mapping[str, Any], digest_field: str) -> Dict[str, Any]:
    return {
        "record": copy.deepcopy(dict(record)),
        digest_field: canonical_digest(record),
    }


def _snapshot(
    identity: Mapping[str, Any],
    instance: Mapping[str, Any],
    versions: Tuple[Mapping[str, Any], ...],
) -> Dict[str, Any]:
    value = {
        "schema_version": REGISTRY_SNAPSHOT_SCHEMA_ID,
        "protocol_revision": PROTOCOL,
        "bundle_digest": BUNDLE,
        "registry_snapshot_digest": "0" * 64,
        "status": "REGISTERED",
        "counts": {
            "identity_count": 1,
            "instance_count": 1,
            "version_count": len(versions),
        },
        "identities": [_wrap(identity, "artifact_digest")],
        "instances": [_wrap(instance, "artifact_digest")],
        "versions": [
            _wrap(version, "version_record_digest")
            for version in versions
        ],
    }
    value["registry_snapshot_digest"] = canonical_digest(
        value,
        "/registry_snapshot_digest",
    )
    return value


def _model(name: str) -> Dict[str, Any]:
    return {
        "provider_code": "OPENAI",
        "requested_alias": None,
        "resolved_id": name,
        "observed_at": TS,
    }


class PromotionFixture:
    def __init__(self) -> None:
        self.bundle = load_draft_contract()
        base = representative_artifacts(
            self.bundle,
            strict_load(INTERFACE),
        )
        self.identity = copy.deepcopy(base["skill-identity"])
        self.identity["lifecycle_status"] = "CHAMPION"
        self.instance = copy.deepcopy(base["skill-instance"])
        self.instance["lifecycle_status"] = "CHAMPION"

        baseline = copy.deepcopy(base["skill-version"])
        baseline["lifecycle_status"] = "CHAMPION"
        candidate_1 = copy.deepcopy(baseline)
        candidate_1.update(
            {
                "skill_version_uid": CANDIDATE_1,
                "lifecycle_status": "CHALLENGER",
                "supersedes_version_uid": BASELINE,
                "content_digest": "1" * 64,
                "tree_digest": "2" * 64,
            }
        )
        candidate_2 = copy.deepcopy(candidate_1)
        candidate_2.update(
            {
                "skill_version_uid": CANDIDATE_2,
                "supersedes_version_uid": CANDIDATE_1,
                "content_digest": "3" * 64,
                "tree_digest": "4" * 64,
            }
        )
        self.versions = {
            BASELINE: baseline,
            CANDIDATE_1: candidate_1,
            CANDIDATE_2: candidate_2,
        }
        self.instance["version_uids"] = sorted(self.versions)
        self.snapshot = _snapshot(
            self.identity,
            self.instance,
            tuple(self.versions[version] for version in sorted(self.versions)),
        )
        self.registry = build_registry_view(
            self.bundle,
            self.snapshot,
            expected_bundle_digest=BUNDLE,
            expected_registry_snapshot_digest=self.snapshot[
                "registry_snapshot_digest"
            ],
        )
        self.version_digests = {
            uid_value: canonical_digest(record)
            for uid_value, record in self.versions.items()
        }

    def _eval_run(
        self,
        *,
        suffix: str,
        version_uid: str,
        model: Mapping[str, Any],
        status: str,
    ) -> Dict[str, Any]:
        value = artifact(
            "eval-run",
            {
                "eval_run_uid": uid("evr", suffix),
                "skill_version_uid": version_uid,
                "eval_profile_uid": uid("evp"),
                "skill_version_record_digest": self.version_digests[
                    version_uid
                ],
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
                    {
                        "run_uid": uid("run", suffix),
                        "event_digest": DIGEST_C,
                        "event_bundle_digest": BUNDLE,
                    }
                ],
                "model_snapshot": copy.deepcopy(dict(model)),
                "environment_fingerprint_digest": DIGEST_D,
                "started_at": TS,
                "finished_at": TS,
                "status": status,
                "result_artifact_digests": [DIGEST_B],
            },
        )
        return finalize_self_digest(
            self.bundle,
            EVAL_RUN_SCHEMA_ID,
            value,
        )

    def _scorecard(
        self,
        *,
        suffix: str,
        candidate_uid: str,
        eval_run: Mapping[str, Any],
        model_digest: str,
        hard_gates_passed: bool,
    ) -> Dict[str, Any]:
        value = artifact(
            "scorecard",
            {
                "scorecard_uid": uid("sc", suffix),
                "skill_version_uid": candidate_uid,
                "eval_profile_uid": uid("evp"),
                "eval_run_uid": eval_run["eval_run_uid"],
                "skill_version_record_digest": self.version_digests[
                    candidate_uid
                ],
                "eval_profile_digest": DIGEST_C,
                "model_snapshot_digest": model_digest,
                "environment_fingerprint_digest": DIGEST_D,
                "dataset_manifest_digests": [DIGEST_B],
                "evaluator_manifest_digests": [DIGEST_C],
                "evaluated_at": TS,
                "hard_gates": [
                    {
                        "gate_code": code,
                        "passed": (
                            hard_gates_passed
                            or index > 0
                        ),
                        "evidence_digest": DIGEST_B,
                    }
                    for index, code in enumerate(HARD_GATES)
                ],
                "dimensions": [
                    {
                        "dimension_code": code,
                        "score_bps": 9000,
                        "sample_count": 1,
                        "coverage_bps": 10000,
                    }
                    for code in (
                        "EFFICIENCY",
                        "MAINTAINABILITY",
                        "NEGATIVE_CAPABILITY",
                        "OUTCOME",
                        "RELIABILITY",
                        "ROUTING",
                        "SAFETY_GOVERNANCE",
                    )
                ],
                "routing_results": {
                    code: {
                        "sample_count": 1,
                        "correct_count": 1,
                        "score_bps": 10000,
                    }
                    for code in (
                        "positive",
                        "missed_trigger",
                        "false_trigger",
                        "conflict",
                        "abstention",
                    )
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
                "promotion_eligible": hard_gates_passed,
                "confidence_bps": 9000,
                "coverage_bps": 10000,
                "freshness_state": "FRESH",
                "freshness_valid_until": "2026-08-22",
                "critical_incident_count": 0,
                "critical_incident_evidence_digests": [],
                "evidence_bundle_digest": DIGEST_C,
            },
        )
        return finalize_self_digest(
            self.bundle,
            SCORECARD_SCHEMA_ID,
            value,
        )

    def material(
        self,
        *,
        candidate_uid: str,
        baseline_uid: str,
        suffix_offset: int,
        action: str,
        hard_gates_passed: bool,
        previous_champion_uid: str,
        decided_at: str,
    ) -> Tuple[
        Dict[str, Any],
        Dict[str, Mapping[str, Any]],
        Dict[str, Mapping[str, Any]],
        Dict[str, Any],
    ]:
        baseline_model = _model("baseline-model-" + str(suffix_offset))
        candidate_model = _model("candidate-model-" + str(suffix_offset))
        baseline_model_digest = canonical_digest(baseline_model)
        candidate_model_digest = canonical_digest(candidate_model)
        cells = (
            ("BASELINE", baseline_uid, baseline_model, "PASS"),
            (
                "INTERACTION",
                candidate_uid,
                candidate_model,
                "PASS",
            ),
            (
                "MODEL_EFFECT",
                baseline_uid,
                candidate_model,
                "PASS",
            ),
            (
                "SKILL_EFFECT",
                candidate_uid,
                baseline_model,
                "PASS",
            ),
        )
        eval_runs = []
        matrix = []
        for index, (cell, version_uid, model, status) in enumerate(cells):
            suffix = "0" * 24 + f"{suffix_offset + index:02d}"
            run = self._eval_run(
                suffix=suffix,
                version_uid=version_uid,
                model=model,
                status=status,
            )
            eval_runs.append(run)
            matrix.append(
                {
                    "cell": cell,
                    "skill_version_uid": version_uid,
                    "model_snapshot_digest": canonical_digest(model),
                    "eval_run_digest": run["eval_run_digest"],
                    "status": status,
                }
            )
        interaction = next(
            run
            for run, cell in zip(eval_runs, cells)
            if cell[0] == "INTERACTION"
        )
        scorecard = self._scorecard(
            suffix="0" * 24 + f"{suffix_offset:02d}",
            candidate_uid=candidate_uid,
            eval_run=interaction,
            model_digest=candidate_model_digest,
            hard_gates_passed=hard_gates_passed,
        )
        eval_refs = sorted(
            (
                {
                    "schema_id": EVAL_RUN_SCHEMA_ID,
                    "artifact_uid": run["eval_run_uid"],
                    "artifact_digest": run["eval_run_digest"],
                }
                for run in eval_runs
            ),
            key=lambda item: (
                item["schema_id"],
                item["artifact_uid"],
                item["artifact_digest"],
            ),
        )
        evidence = artifact(
            "promotion-evidence-bundle",
            {
                "promotion_bundle_uid": uid(
                    "peb",
                    "0" * 24 + f"{suffix_offset:02d}",
                ),
                "candidate_skill_version_uid": candidate_uid,
                "baseline_skill_version_uid": baseline_uid,
                "scorecard_refs": [
                    {
                        "schema_id": SCORECARD_SCHEMA_ID,
                        "artifact_uid": scorecard["scorecard_uid"],
                        "artifact_digest": scorecard["scorecard_digest"],
                    }
                ],
                "eval_run_refs": eval_refs,
                "candidate_model_snapshot_digest": candidate_model_digest,
                "baseline_model_snapshot_digest": baseline_model_digest,
                "environment_fingerprint_digest": DIGEST_D,
                "tool_manifest_digest": DIGEST_B,
                "dataset_manifest_digests": [DIGEST_B],
                "evaluator_manifest_digests": [DIGEST_C],
                "rubric_digest": DIGEST_D,
                "policy_snapshot_digest": DIGEST_C,
                "causal_matrix": sorted(
                    matrix,
                    key=lambda item: item["cell"],
                ),
                "shadow_evidence_digest": DIGEST_C,
                "canary_evidence_digest": DIGEST_D,
                "hard_gates_passed": hard_gates_passed,
                "risk_tier": "LOW",
                "known_risk_codes": [],
                "rollback_target_version_uid": baseline_uid,
                "notification_required": False,
                "notification_receipt_digest": None,
                "created_at": TS,
                "actor": "SKILLOPS_PROMOTION_CONTROLLER",
            },
        )
        finalize_self_digest(
            self.bundle,
            PROMOTION_EVIDENCE_SCHEMA_ID,
            evidence,
        )
        decision = artifact(
            "promotion-decision",
            {
                "promotion_decision_uid": uid(
                    "prd",
                    "0" * 24 + f"{suffix_offset:02d}",
                ),
                "srv_revision": SRV,
                "action": action,
                "stage": (
                    "CHAMPION" if action == "PROMOTE" else "REJECTED"
                ),
                "impact": "MINOR",
                "candidate_skill_version_uid": candidate_uid,
                "previous_champion_version_uid": previous_champion_uid,
                "resulting_champion_version_uid": (
                    candidate_uid
                    if action == "PROMOTE"
                    else previous_champion_uid
                ),
                "candidate_model_snapshot_digest": candidate_model_digest,
                "baseline_model_snapshot_digest": baseline_model_digest,
                "from_status": "CHALLENGER",
                "to_status": (
                    "CHAMPION"
                    if action == "PROMOTE"
                    else "QUARANTINED"
                ),
                "evidence_bundle_digest": evidence[
                    "evidence_bundle_digest"
                ],
                "hard_gates_passed": hard_gates_passed,
                "known_risk_codes": [],
                "reason_codes": [
                    (
                        "HARD_GATES_PASSED"
                        if action == "PROMOTE"
                        else "HARD_GATE_FAILED"
                    )
                ],
                "actor": "SKILLOPS_PROMOTION_CONTROLLER",
                "major_change": False,
                "notification_receipt_digest": None,
                "notification_mode": "NOT_REQUIRED",
                "owner_approval_required": False,
                "emergency_containment": False,
                "rollback_target_version_uid": baseline_uid,
                "decided_at": decided_at,
            },
        )
        finalize_self_digest(
            self.bundle,
            PROMOTION_DECISION_SCHEMA_ID,
            decision,
        )
        return (
            evidence,
            {
                scorecard["scorecard_digest"]: scorecard,
            },
            {
                run["eval_run_digest"]: run
                for run in eval_runs
            },
            decision,
        )


class PromotionControllerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = PromotionFixture()
        (
            self.evidence_1,
            self.scorecards_1,
            self.eval_runs_1,
            self.promote_1,
        ) = self.fixture.material(
            candidate_uid=CANDIDATE_1,
            baseline_uid=BASELINE,
            suffix_offset=10,
            action="PROMOTE",
            hard_gates_passed=True,
            previous_champion_uid=BASELINE,
            decided_at="2026-07-23T00:00:01.000000Z",
        )

    def _replay(
        self,
        decisions,
        evidences=None,
        scorecards=None,
        eval_runs=None,
    ):
        return replay_promotion_ledger(
            self.fixture.bundle,
            self.fixture.registry,
            evidence_by_digest=(
                evidences
                if evidences is not None
                else {
                    self.evidence_1["evidence_bundle_digest"]:
                    self.evidence_1
                }
            ),
            scorecards_by_digest=(
                scorecards
                if scorecards is not None
                else self.scorecards_1
            ),
            eval_runs_by_digest=(
                eval_runs
                if eval_runs is not None
                else self.eval_runs_1
            ),
            decisions=decisions,
            expected_bundle_digest=BUNDLE,
        )

    def test_promote_appends_canonical_event_and_one_champion(self):
        original_decision = copy.deepcopy(self.promote_1)
        original_snapshot = copy.deepcopy(self.fixture.snapshot)
        result = append_promotion_decision(
            self.fixture.bundle,
            self.fixture.registry,
            evidence_by_digest={
                self.evidence_1["evidence_bundle_digest"]:
                self.evidence_1
            },
            scorecards_by_digest=self.scorecards_1,
            eval_runs_by_digest=self.eval_runs_1,
            existing_decisions=(),
            decision=self.promote_1,
            expected_predecessor_ledger_digest=promotion_ledger_digest(
                self.fixture.registry.registry_snapshot_digest,
                (),
            ),
            expected_bundle_digest=BUNDLE,
        )
        self.assertEqual(
            self.promote_1,
            json.loads(result.canonical_decision_bytes),
        )
        self.assertEqual(
            self.promote_1["decision_digest"],
            result.decision_digest,
        )
        self.assertEqual(
            promotion_ledger_digest(
                self.fixture.registry.registry_snapshot_digest,
                (),
            ),
            result.predecessor_ledger_digest,
        )
        self.assertEqual(
            promotion_ledger_digest(
                self.fixture.registry.registry_snapshot_digest,
                (self.promote_1["decision_digest"],),
            ),
            result.ledger_view.ledger_digest,
        )
        self.assertEqual(
            ((IDENTITY, CANDIDATE_1),),
            result.ledger_view.champion_by_scope,
        )
        self.assertEqual(1, result.ledger_view.promote_count)
        self.assertEqual(0, result.ledger_view.reject_count)
        self.assertEqual(original_decision, self.promote_1)
        self.assertEqual(original_snapshot, self.fixture.snapshot)

        with self.assertRaisesRegex(
            PromotionControllerError,
            "PROMOTION_PREDECESSOR_LEDGER_DIGEST_MISMATCH",
        ):
            append_promotion_decision(
                self.fixture.bundle,
                self.fixture.registry,
                evidence_by_digest={
                    self.evidence_1["evidence_bundle_digest"]:
                    self.evidence_1
                },
                scorecards_by_digest=self.scorecards_1,
                eval_runs_by_digest=self.eval_runs_1,
                existing_decisions=(),
                decision=self.promote_1,
                expected_predecessor_ledger_digest="f" * 64,
                expected_bundle_digest=BUNDLE,
            )

    def test_promote_then_reject_preserves_current_champion(self):
        evidence_2, scorecards_2, eval_runs_2, reject_2 = (
            self.fixture.material(
                candidate_uid=CANDIDATE_2,
                baseline_uid=CANDIDATE_1,
                suffix_offset=20,
                action="REJECT",
                hard_gates_passed=False,
                previous_champion_uid=CANDIDATE_1,
                decided_at="2026-07-23T00:00:02.000000Z",
            )
        )
        view = self._replay(
            [self.promote_1, reject_2],
            evidences={
                self.evidence_1["evidence_bundle_digest"]:
                self.evidence_1,
                evidence_2["evidence_bundle_digest"]: evidence_2,
            },
            scorecards={**self.scorecards_1, **scorecards_2},
            eval_runs={**self.eval_runs_1, **eval_runs_2},
        )
        self.assertEqual(((IDENTITY, CANDIDATE_1),), view.champion_by_scope)
        self.assertEqual((CANDIDATE_1, CANDIDATE_2), view.terminal_candidate_version_uids)
        self.assertEqual(1, view.promote_count)
        self.assertEqual(1, view.reject_count)

    def test_gate_claim_tampering_cannot_promote(self):
        tampered_scorecard = copy.deepcopy(
            next(iter(self.scorecards_1.values()))
        )
        tampered_scorecard["hard_gates"][0]["passed"] = False
        tampered_scorecard["promotion_eligible"] = False
        finalize_self_digest(
            self.fixture.bundle,
            SCORECARD_SCHEMA_ID,
            tampered_scorecard,
        )
        tampered_evidence = copy.deepcopy(self.evidence_1)
        tampered_evidence["scorecard_refs"][0]["artifact_digest"] = (
            tampered_scorecard["scorecard_digest"]
        )
        finalize_self_digest(
            self.fixture.bundle,
            PROMOTION_EVIDENCE_SCHEMA_ID,
            tampered_evidence,
        )
        tampered_decision = copy.deepcopy(self.promote_1)
        tampered_decision["evidence_bundle_digest"] = tampered_evidence[
            "evidence_bundle_digest"
        ]
        finalize_self_digest(
            self.fixture.bundle,
            PROMOTION_DECISION_SCHEMA_ID,
            tampered_decision,
        )
        with self.assertRaisesRegex(
            PromotionControllerError,
            "PROMOTION_EVIDENCE_ELIGIBILITY_CLAIM_MISMATCH",
        ):
            self._replay(
                [tampered_decision],
                evidences={
                    tampered_evidence["evidence_bundle_digest"]:
                    tampered_evidence,
                },
                scorecards={
                    tampered_scorecard["scorecard_digest"]:
                    tampered_scorecard,
                },
            )

    def test_cross_scope_or_non_current_rollback_fails_closed(self):
        tampered = copy.deepcopy(self.promote_1)
        tampered["previous_champion_version_uid"] = None
        finalize_self_digest(
            self.fixture.bundle,
            PROMOTION_DECISION_SCHEMA_ID,
            tampered,
        )
        with self.assertRaisesRegex(
            PromotionControllerError,
            "PROMOTION_PREVIOUS_CHAMPION_MISMATCH",
        ):
            self._replay([tampered])

        tampered_evidence = copy.deepcopy(self.evidence_1)
        tampered_evidence["rollback_target_version_uid"] = CANDIDATE_2
        finalize_self_digest(
            self.fixture.bundle,
            PROMOTION_EVIDENCE_SCHEMA_ID,
            tampered_evidence,
        )
        tampered = copy.deepcopy(self.promote_1)
        tampered["evidence_bundle_digest"] = tampered_evidence[
            "evidence_bundle_digest"
        ]
        tampered["rollback_target_version_uid"] = CANDIDATE_2
        finalize_self_digest(
            self.fixture.bundle,
            PROMOTION_DECISION_SCHEMA_ID,
            tampered,
        )
        with self.assertRaisesRegex(
            PromotionControllerError,
            "PROMOTION_DECISION_SCOPE_OR_ROLLBACK_MISMATCH",
        ):
            self._replay(
                [tampered],
                evidences={
                    tampered_evidence["evidence_bundle_digest"]:
                    tampered_evidence,
                },
            )

    def test_append_only_uid_digest_time_and_candidate_uniqueness(self):
        duplicate = copy.deepcopy(self.promote_1)
        with self.assertRaisesRegex(
            PromotionControllerError,
            "PROMOTION_DECISION_UID_DUPLICATE",
        ):
            self._replay(
                [self.promote_1, duplicate],
                evidences={
                    self.evidence_1["evidence_bundle_digest"]:
                    self.evidence_1
                },
            )

        evidence_2, scorecards_2, eval_runs_2, decision_2 = (
            self.fixture.material(
                candidate_uid=CANDIDATE_2,
                baseline_uid=CANDIDATE_1,
                suffix_offset=20,
                action="REJECT",
                hard_gates_passed=False,
                previous_champion_uid=CANDIDATE_1,
                decided_at="2026-07-23T00:00:00.000000Z",
            )
        )
        with self.assertRaisesRegex(
            PromotionControllerError,
            "PROMOTION_LEDGER_TIME_ORDER_INVALID",
        ):
            self._replay(
                [self.promote_1, decision_2],
                evidences={
                    self.evidence_1["evidence_bundle_digest"]:
                    self.evidence_1,
                    evidence_2["evidence_bundle_digest"]: evidence_2,
                },
                scorecards={**self.scorecards_1, **scorecards_2},
                eval_runs={**self.eval_runs_1, **eval_runs_2},
            )

    def test_rollback_and_revocation_are_separate_fail_closed_phase(self):
        for action in ("ROLLBACK", "REVOKE"):
            decision = copy.deepcopy(self.promote_1)
            decision["action"] = action
            finalize_self_digest(
                self.fixture.bundle,
                PROMOTION_DECISION_SCHEMA_ID,
                decision,
            )
            with self.subTest(action=action), self.assertRaisesRegex(
                PromotionControllerError,
                "PROMOTION_ROLLBACK_REVOCATION_PHASE_REQUIRED",
            ):
                self._replay([decision])

    def test_registry_rejects_two_base_champions_and_digest_drift(self):
        snapshot = copy.deepcopy(self.fixture.snapshot)
        candidate = snapshot["versions"][1]["record"]
        candidate["lifecycle_status"] = "CHAMPION"
        snapshot["versions"][1]["version_record_digest"] = canonical_digest(
            candidate
        )
        snapshot["registry_snapshot_digest"] = canonical_digest(
            snapshot,
            "/registry_snapshot_digest",
        )
        with self.assertRaisesRegex(
            PromotionControllerError,
            "PROMOTION_REGISTRY_MULTIPLE_CHAMPIONS_PER_SCOPE",
        ):
            build_registry_view(
                self.fixture.bundle,
                snapshot,
                expected_bundle_digest=BUNDLE,
                expected_registry_snapshot_digest=snapshot[
                    "registry_snapshot_digest"
                ],
            )

        drifted = copy.deepcopy(self.fixture.snapshot)
        drifted["counts"]["version_count"] += 1
        drifted["registry_snapshot_digest"] = canonical_digest(
            drifted,
            "/registry_snapshot_digest",
        )
        with self.assertRaisesRegex(
            PromotionControllerError,
            "PROMOTION_REGISTRY_VERSION_COUNT_MISMATCH",
        ):
            build_registry_view(
                self.fixture.bundle,
                drifted,
                expected_bundle_digest=BUNDLE,
                expected_registry_snapshot_digest=drifted[
                    "registry_snapshot_digest"
                ],
            )

    def test_unused_artifacts_and_evidence_are_forbidden(self):
        extra_evidence = copy.deepcopy(self.evidence_1)
        extra_evidence["promotion_bundle_uid"] = uid(
            "peb",
            "0" * 25 + "9",
        )
        finalize_self_digest(
            self.fixture.bundle,
            PROMOTION_EVIDENCE_SCHEMA_ID,
            extra_evidence,
        )
        with self.assertRaisesRegex(
            PromotionControllerError,
            "PROMOTION_UNUSED_EVIDENCE_FORBIDDEN",
        ):
            self._replay(
                [self.promote_1],
                evidences={
                    self.evidence_1["evidence_bundle_digest"]:
                    self.evidence_1,
                    extra_evidence["evidence_bundle_digest"]:
                    extra_evidence,
                },
            )

    def test_builder_is_byte_equivalent_and_real_registry_is_not_promotable(self):
        process = subprocess.run(
            [
                sys.executable,
                "-B",
                str(
                    GOVERNANCE
                    / "tools"
                    / "build_promotion_controller.py"
                ),
                "--check",
            ],
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        self.assertEqual(0, process.returncode, process.stderr)
        self.assertIn(
            "PROMOTION_CONTROLLER_BYTE_EQUIVALENT",
            process.stdout,
        )
        readiness = parse_json_bytes(OUTPUT_PATH.read_bytes())
        self.assertEqual(build_readiness(), readiness)
        self.assertEqual(build_schema(), parse_json_bytes(SCHEMA_PATH.read_bytes()))
        self.assertEqual(NEXT_PHASE, readiness["next_phase"])
        self.assertEqual(
            0,
            readiness["registry_observation"][
                "challenger_version_count"
            ],
        )
        self.assertEqual(
            0,
            readiness["registry_observation"]["base_champion_count"],
        )
        self.assertFalse(
            readiness["registry_observation"][
                "real_promotion_execution_permitted"
            ]
        )
        self.assertEqual(
            hashlib.sha256(CONTROLLER_PATH.read_bytes()).hexdigest(),
            readiness["controller_contract"]["content_digest"],
        )
        self.assertFalse(
            (ROOT / "CodexSkills" / "VERSION").exists()
        )


if __name__ == "__main__":
    unittest.main()
