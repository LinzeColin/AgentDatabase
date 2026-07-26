from __future__ import annotations

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence, Tuple

from CodexSkills.governance.promotion.rollback_controller import (
    ROLLBACK_DRILL_SCHEMA_ID,
    RollbackControllerError,
    append_rollback_decision,
    build_rollback_contract,
    lifecycle_ledger_digest,
    replay_lifecycle_ledger,
)
from CodexSkills.governance.tests.test_mechanism_contract import (
    BUNDLE,
    DIGEST_B,
    DIGEST_C,
    DIGEST_D,
    SRV,
    artifact,
    finalize_self_digest,
    uid,
)
from CodexSkills.governance.tests.test_promotion_controller import (
    BASELINE,
    CANDIDATE_1,
    CANDIDATE_2,
    IDENTITY,
    PromotionFixture,
)
from CodexSkills.governance.tools.build_rollback_revocation_controller import (
    CONTROLLER_PATH,
    DRILL_SCHEMA_PATH,
    NEXT_PHASE,
    OUTPUT_PATH,
    READINESS_SCHEMA_PATH,
    build_drill_schema,
    build_readiness,
    build_readiness_schema,
)
from CodexSkills.governance.tools.canonical_json import (
    canonical_digest,
    parse_json_bytes,
)


ROOT = Path(__file__).resolve().parents[3]
GOVERNANCE = ROOT / "CodexSkills" / "governance"


class RollbackFixture:
    def __init__(self) -> None:
        self.promotion = PromotionFixture()
        (
            self.evidence_1,
            self.scorecards_1,
            self.eval_runs_1,
            self.promote_1,
        ) = self.promotion.material(
            candidate_uid=CANDIDATE_1,
            baseline_uid=BASELINE,
            suffix_offset=10,
            action="PROMOTE",
            hard_gates_passed=True,
            previous_champion_uid=BASELINE,
            decided_at="2026-07-23T00:00:01.000000Z",
        )
        self.drill_schema = build_drill_schema()
        self.drill_schema_digest = canonical_digest(self.drill_schema)
        self.rollback_bundle = build_rollback_contract(
            self.promotion.bundle,
            self.drill_schema,
            self.drill_schema_digest,
        )

    @staticmethod
    def ledger_digest(
        registry_digest: str,
        decisions: Sequence[Mapping[str, Any]],
    ) -> str:
        return lifecycle_ledger_digest(
            registry_digest,
            [decision["action"] for decision in decisions],
            [decision["decision_digest"] for decision in decisions],
            [decision["evidence_bundle_digest"] for decision in decisions],
        )

    def rollback_material(
        self,
        *,
        existing_decisions: Sequence[Mapping[str, Any]],
        action: str,
        current_uid: str,
        target_uid: str,
        current_event_digest: str,
        target_event_digest: Any,
        current_model_digest: str,
        target_model_digest: str,
        suffix: int,
        completed_at: str,
        decided_at: str,
        emergency: bool,
    ) -> Tuple[Dict[str, Any], Dict[str, Any], str]:
        predecessor_digest = self.ledger_digest(
            self.promotion.registry.registry_snapshot_digest,
            existing_decisions,
        )
        verification_digests = (
            "5" * 64,
            "6" * 64,
            "7" * 64,
            "8" * 64,
            "9" * 64,
        )
        kinds = (
            "REFERENCE_CLOSURE",
            "RESTORE_PLAN",
            "RESTORE_TEST",
            "STATE_SNAPSHOT",
            "TRIGGER",
        )
        notification_receipt_digest = "a" * 64
        drill: Dict[str, Any] = {
            "schema_version": ROLLBACK_DRILL_SCHEMA_ID,
            "protocol_revision": self.promotion.bundle.protocol_revision,
            "bundle_digest": BUNDLE,
            "rollback_drill_uid": uid(
                "rbd",
                "0" * 24 + f"{suffix:02d}",
            ),
            "action": action,
            "execution_mode": (
                "EMERGENCY_POST_CONTAINMENT"
                if emergency
                else "PLANNED_PRE_WRITE"
            ),
            "skill_identity_uid": IDENTITY,
            "current_champion_ref": {
                "skill_version_uid": current_uid,
                "version_record_digest": (
                    self.promotion.version_digests[current_uid]
                ),
                "model_snapshot_digest": current_model_digest,
                "decision_digest": current_event_digest,
            },
            "rollback_target_ref": {
                "skill_version_uid": target_uid,
                "version_record_digest": (
                    self.promotion.version_digests[target_uid]
                ),
                "model_snapshot_digest": target_model_digest,
                "decision_digest": target_event_digest,
            },
            "registry_snapshot_digest": (
                self.promotion.registry.registry_snapshot_digest
            ),
            "predecessor_ledger": {
                "artifact_digest": predecessor_digest,
                "decision_count": len(existing_decisions),
            },
            "verification_evidence_refs": [
                {
                    "kind": kind,
                    "artifact_digest": digest,
                }
                for kind, digest in zip(kinds, verification_digests)
            ],
            "trigger_codes": ["CRITICAL_DETERMINISTIC_SIGNAL"],
            "known_risk_codes": ["SIDE_EFFECT_REGRESSION"],
            "policy_snapshot_digest": DIGEST_C,
            "environment_fingerprint_digest": DIGEST_D,
            "notification_receipt_digest": (
                notification_receipt_digest
            ),
            "notification_mode": (
                "POST_CONTAINMENT_SENT"
                if emergency
                else "PRE_WRITE_SENT"
            ),
            "containment_evidence": (
                {"evidence_digest": DIGEST_B}
                if emergency
                else None
            ),
            "state_write_observed": emergency,
            "restore_target_content_verified": True,
            "restore_target_reference_closure_verified": True,
            "rollback_target_restorable": True,
            "history_rewrite_performed": False,
            "drill_status": "PASS",
            "completed_at": completed_at,
            "actor": "SKILLOPS_ROLLBACK_CONTROLLER",
            "evidence_bundle_digest": "0" * 64,
        }
        drill["evidence_bundle_digest"] = canonical_digest(
            drill,
            "/evidence_bundle_digest",
        )
        decision = artifact(
            "promotion-decision",
            {
                "promotion_decision_uid": uid(
                    "prd",
                    "0" * 24 + f"{suffix:02d}",
                ),
                "srv_revision": self.promotion.versions[current_uid][
                    "srv_revision"
                ],
                "action": action,
                "stage": (
                    "ROLLED_BACK" if action == "ROLLBACK" else "REVOKED"
                ),
                "impact": "MAJOR",
                "candidate_skill_version_uid": current_uid,
                "previous_champion_version_uid": current_uid,
                "resulting_champion_version_uid": target_uid,
                "candidate_model_snapshot_digest": current_model_digest,
                "baseline_model_snapshot_digest": target_model_digest,
                "from_status": "CHAMPION",
                "to_status": (
                    "DEPRECATED" if action == "ROLLBACK" else "REVOKED"
                ),
                "evidence_bundle_digest": drill[
                    "evidence_bundle_digest"
                ],
                "hard_gates_passed": True,
                "known_risk_codes": ["SIDE_EFFECT_REGRESSION"],
                "reason_codes": ["CRITICAL_DETERMINISTIC_SIGNAL"],
                "actor": "SKILLOPS_PROMOTION_CONTROLLER",
                "major_change": True,
                "notification_receipt_digest": (
                    notification_receipt_digest
                ),
                "notification_mode": (
                    "POST_CONTAINMENT_SENT"
                    if emergency
                    else "PRE_WRITE_SENT"
                ),
                "owner_approval_required": False,
                "emergency_containment": emergency,
                "rollback_target_version_uid": target_uid,
                "decided_at": decided_at,
            },
        )
        finalize_self_digest(
            self.promotion.bundle,
            (
                "urn:linzecolin:agentdatabase:skillops:"
                "schema:promotion-decision:v1"
            ),
            decision,
        )
        return drill, decision, predecessor_digest


class RollbackRevocationControllerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = RollbackFixture()
        self.current_model = self.fixture.promote_1[
            "candidate_model_snapshot_digest"
        ]
        self.baseline_model = self.fixture.promote_1[
            "baseline_model_snapshot_digest"
        ]

    def _base_maps(self):
        return (
            {
                self.fixture.evidence_1["evidence_bundle_digest"]:
                self.fixture.evidence_1
            },
            dict(self.fixture.scorecards_1),
            dict(self.fixture.eval_runs_1),
        )

    def _append(
        self,
        drill,
        decision,
        predecessor_digest,
        *,
        existing=None,
        promotion_evidence=None,
        scorecards=None,
        eval_runs=None,
        drills=None,
        expected_predecessor=None,
    ):
        base_evidence, base_scorecards, base_eval_runs = self._base_maps()
        return append_rollback_decision(
            self.fixture.promotion.bundle,
            self.fixture.promotion.registry,
            rollback_drill_schema=self.fixture.drill_schema,
            expected_rollback_drill_schema_digest=(
                self.fixture.drill_schema_digest
            ),
            promotion_evidence_by_digest=(
                base_evidence
                if promotion_evidence is None
                else promotion_evidence
            ),
            rollback_drill_by_digest=(
                {drill["evidence_bundle_digest"]: drill}
                if drills is None
                else drills
            ),
            scorecards_by_digest=(
                base_scorecards if scorecards is None else scorecards
            ),
            eval_runs_by_digest=(
                base_eval_runs if eval_runs is None else eval_runs
            ),
            existing_decisions=(
                [self.fixture.promote_1]
                if existing is None
                else existing
            ),
            decision=decision,
            expected_predecessor_ledger_digest=(
                predecessor_digest
                if expected_predecessor is None
                else expected_predecessor
            ),
            expected_bundle_digest=BUNDLE,
        )

    def test_planned_rollback_appends_event_and_restores_prior_champion(self):
        drill, decision, predecessor = self.fixture.rollback_material(
            existing_decisions=[self.fixture.promote_1],
            action="ROLLBACK",
            current_uid=CANDIDATE_1,
            target_uid=BASELINE,
            current_event_digest=self.fixture.promote_1[
                "decision_digest"
            ],
            target_event_digest=None,
            current_model_digest=self.current_model,
            target_model_digest=self.baseline_model,
            suffix=30,
            completed_at="2026-07-23T00:00:02.000000Z",
            decided_at="2026-07-23T00:00:03.000000Z",
            emergency=False,
        )
        original_decision = copy.deepcopy(decision)
        original_drill = copy.deepcopy(drill)
        result = self._append(drill, decision, predecessor)
        self.assertEqual(
            decision,
            json.loads(result.canonical_decision_bytes),
        )
        self.assertEqual(
            drill,
            json.loads(result.canonical_drill_evidence_bytes),
        )
        self.assertEqual(((IDENTITY, BASELINE),), result.ledger_view.champion_by_scope)
        self.assertEqual(1, result.ledger_view.promote_count)
        self.assertEqual(1, result.ledger_view.rollback_count)
        self.assertEqual(0, result.ledger_view.revoke_count)
        self.assertIn(
            (CANDIDATE_1, "DEPRECATED"),
            result.ledger_view.lifecycle_overrides,
        )
        self.assertEqual(original_decision, decision)
        self.assertEqual(original_drill, drill)

    def test_emergency_revoke_contains_then_notifies_and_restores(self):
        drill, decision, predecessor = self.fixture.rollback_material(
            existing_decisions=[self.fixture.promote_1],
            action="REVOKE",
            current_uid=CANDIDATE_1,
            target_uid=BASELINE,
            current_event_digest=self.fixture.promote_1[
                "decision_digest"
            ],
            target_event_digest=None,
            current_model_digest=self.current_model,
            target_model_digest=self.baseline_model,
            suffix=31,
            completed_at="2026-07-23T00:00:02.000000Z",
            decided_at="2026-07-23T00:00:03.000000Z",
            emergency=True,
        )
        result = self._append(drill, decision, predecessor)
        self.assertEqual((CANDIDATE_1,), result.ledger_view.revoked_version_uids)
        self.assertEqual(((IDENTITY, BASELINE),), result.ledger_view.champion_by_scope)
        self.assertEqual(1, result.ledger_view.revoke_count)

    def test_non_historical_target_and_reference_drift_fail_closed(self):
        drill, decision, predecessor = self.fixture.rollback_material(
            existing_decisions=[self.fixture.promote_1],
            action="ROLLBACK",
            current_uid=CANDIDATE_1,
            target_uid=CANDIDATE_2,
            current_event_digest=self.fixture.promote_1[
                "decision_digest"
            ],
            target_event_digest=None,
            current_model_digest=self.current_model,
            target_model_digest=DIGEST_C,
            suffix=32,
            completed_at="2026-07-23T00:00:02.000000Z",
            decided_at="2026-07-23T00:00:03.000000Z",
            emergency=False,
        )
        with self.assertRaisesRegex(
            RollbackControllerError,
            "ROLLBACK_TARGET_NOT_RESTORABLE_PRIOR_CHAMPION",
        ):
            self._append(drill, decision, predecessor)

        drill, decision, predecessor = self.fixture.rollback_material(
            existing_decisions=[self.fixture.promote_1],
            action="ROLLBACK",
            current_uid=CANDIDATE_1,
            target_uid=BASELINE,
            current_event_digest=self.fixture.promote_1[
                "decision_digest"
            ],
            target_event_digest=None,
            current_model_digest=self.current_model,
            target_model_digest=self.baseline_model,
            suffix=33,
            completed_at="2026-07-23T00:00:02.000000Z",
            decided_at="2026-07-23T00:00:03.000000Z",
            emergency=False,
        )
        drifted = copy.deepcopy(drill)
        drifted["rollback_target_ref"]["version_record_digest"] = "f" * 64
        drifted["evidence_bundle_digest"] = canonical_digest(
            drifted,
            "/evidence_bundle_digest",
        )
        drifted_decision = copy.deepcopy(decision)
        drifted_decision["evidence_bundle_digest"] = drifted[
            "evidence_bundle_digest"
        ]
        finalize_self_digest(
            self.fixture.promotion.bundle,
            (
                "urn:linzecolin:agentdatabase:skillops:"
                "schema:promotion-decision:v1"
            ),
            drifted_decision,
        )
        with self.assertRaisesRegex(
            RollbackControllerError,
            "ROLLBACK_DRILL_REFERENCE_CLOSURE_MISMATCH",
        ):
            self._append(drifted, drifted_decision, predecessor)

    def test_history_truncation_and_predecessor_substitution_fail_closed(self):
        drill, decision, predecessor = self.fixture.rollback_material(
            existing_decisions=[self.fixture.promote_1],
            action="ROLLBACK",
            current_uid=CANDIDATE_1,
            target_uid=BASELINE,
            current_event_digest=self.fixture.promote_1[
                "decision_digest"
            ],
            target_event_digest=None,
            current_model_digest=self.current_model,
            target_model_digest=self.baseline_model,
            suffix=34,
            completed_at="2026-07-23T00:00:02.000000Z",
            decided_at="2026-07-23T00:00:03.000000Z",
            emergency=False,
        )
        with self.assertRaisesRegex(
            RollbackControllerError,
            "ROLLBACK_PREDECESSOR_LEDGER_DIGEST_MISMATCH",
        ):
            self._append(
                drill,
                decision,
                predecessor,
                expected_predecessor="f" * 64,
            )

        rewritten = copy.deepcopy(self.fixture.promote_1)
        rewritten["reason_codes"] = ["REPLAYED_HISTORY"]
        finalize_self_digest(
            self.fixture.promotion.bundle,
            (
                "urn:linzecolin:agentdatabase:skillops:"
                "schema:promotion-decision:v1"
            ),
            rewritten,
        )
        with self.assertRaisesRegex(
            RollbackControllerError,
            "ROLLBACK_DRILL_REFERENCE_CLOSURE_MISMATCH",
        ):
            self._append(
                drill,
                decision,
                predecessor,
                existing=[rewritten],
            )

    def test_planned_and_emergency_notification_order_cannot_swap(self):
        drill, decision, predecessor = self.fixture.rollback_material(
            existing_decisions=[self.fixture.promote_1],
            action="ROLLBACK",
            current_uid=CANDIDATE_1,
            target_uid=BASELINE,
            current_event_digest=self.fixture.promote_1[
                "decision_digest"
            ],
            target_event_digest=None,
            current_model_digest=self.current_model,
            target_model_digest=self.baseline_model,
            suffix=35,
            completed_at="2026-07-23T00:00:02.000000Z",
            decided_at="2026-07-23T00:00:03.000000Z",
            emergency=False,
        )
        invalid = copy.deepcopy(drill)
        invalid["state_write_observed"] = True
        invalid["evidence_bundle_digest"] = canonical_digest(
            invalid,
            "/evidence_bundle_digest",
        )
        invalid_decision = copy.deepcopy(decision)
        invalid_decision["evidence_bundle_digest"] = invalid[
            "evidence_bundle_digest"
        ]
        finalize_self_digest(
            self.fixture.promotion.bundle,
            (
                "urn:linzecolin:agentdatabase:skillops:"
                "schema:promotion-decision:v1"
            ),
            invalid_decision,
        )
        with self.assertRaisesRegex(
            RollbackControllerError,
            "ROLLBACK_PLANNED_NOTIFICATION_ORDER_INVALID",
        ):
            self._append(invalid, invalid_decision, predecessor)

        emergency, emergency_decision, predecessor = (
            self.fixture.rollback_material(
                existing_decisions=[self.fixture.promote_1],
                action="REVOKE",
                current_uid=CANDIDATE_1,
                target_uid=BASELINE,
                current_event_digest=self.fixture.promote_1[
                    "decision_digest"
                ],
                target_event_digest=None,
                current_model_digest=self.current_model,
                target_model_digest=self.baseline_model,
                suffix=36,
                completed_at="2026-07-23T00:00:02.000000Z",
                decided_at="2026-07-23T00:00:03.000000Z",
                emergency=True,
            )
        )
        emergency["containment_evidence"] = None
        emergency["evidence_bundle_digest"] = canonical_digest(
            emergency,
            "/evidence_bundle_digest",
        )
        emergency_decision["evidence_bundle_digest"] = emergency[
            "evidence_bundle_digest"
        ]
        finalize_self_digest(
            self.fixture.promotion.bundle,
            (
                "urn:linzecolin:agentdatabase:skillops:"
                "schema:promotion-decision:v1"
            ),
            emergency_decision,
        )
        with self.assertRaisesRegex(
            RollbackControllerError,
            "ROLLBACK_EMERGENCY_NOTIFICATION_ORDER_INVALID",
        ):
            self._append(emergency, emergency_decision, predecessor)

    def test_interleaved_promotion_after_rollback_is_deterministic(self):
        rollback_drill, rollback, _ = self.fixture.rollback_material(
            existing_decisions=[self.fixture.promote_1],
            action="ROLLBACK",
            current_uid=CANDIDATE_1,
            target_uid=BASELINE,
            current_event_digest=self.fixture.promote_1[
                "decision_digest"
            ],
            target_event_digest=None,
            current_model_digest=self.current_model,
            target_model_digest=self.baseline_model,
            suffix=37,
            completed_at="2026-07-23T00:00:02.000000Z",
            decided_at="2026-07-23T00:00:03.000000Z",
            emergency=False,
        )
        evidence_2, scorecards_2, eval_runs_2, promote_2 = (
            self.fixture.promotion.material(
                candidate_uid=CANDIDATE_2,
                baseline_uid=BASELINE,
                suffix_offset=40,
                action="PROMOTE",
                hard_gates_passed=True,
                previous_champion_uid=BASELINE,
                decided_at="2026-07-23T00:00:04.000000Z",
            )
        )
        base_evidence, base_scorecards, base_eval_runs = self._base_maps()
        view = replay_lifecycle_ledger(
            self.fixture.promotion.bundle,
            self.fixture.promotion.registry,
            rollback_drill_schema=self.fixture.drill_schema,
            expected_rollback_drill_schema_digest=(
                self.fixture.drill_schema_digest
            ),
            promotion_evidence_by_digest={
                **base_evidence,
                evidence_2["evidence_bundle_digest"]: evidence_2,
            },
            rollback_drill_by_digest={
                rollback_drill["evidence_bundle_digest"]: rollback_drill,
            },
            scorecards_by_digest={**base_scorecards, **scorecards_2},
            eval_runs_by_digest={**base_eval_runs, **eval_runs_2},
            decisions=[
                self.fixture.promote_1,
                rollback,
                promote_2,
            ],
            expected_bundle_digest=BUNDLE,
        )
        self.assertEqual(((IDENTITY, CANDIDATE_2),), view.champion_by_scope)
        self.assertEqual(2, view.promote_count)
        self.assertEqual(1, view.rollback_count)

    def test_revoked_version_can_never_be_restore_target(self):
        revoke_drill, revoke, _ = self.fixture.rollback_material(
            existing_decisions=[self.fixture.promote_1],
            action="REVOKE",
            current_uid=CANDIDATE_1,
            target_uid=BASELINE,
            current_event_digest=self.fixture.promote_1[
                "decision_digest"
            ],
            target_event_digest=None,
            current_model_digest=self.current_model,
            target_model_digest=self.baseline_model,
            suffix=50,
            completed_at="2026-07-23T00:00:02.000000Z",
            decided_at="2026-07-23T00:00:03.000000Z",
            emergency=True,
        )
        evidence_2, scorecards_2, eval_runs_2, promote_2 = (
            self.fixture.promotion.material(
                candidate_uid=CANDIDATE_2,
                baseline_uid=BASELINE,
                suffix_offset=60,
                action="PROMOTE",
                hard_gates_passed=True,
                previous_champion_uid=BASELINE,
                decided_at="2026-07-23T00:00:04.000000Z",
            )
        )
        existing = [self.fixture.promote_1, revoke, promote_2]
        rollback_drill, rollback, _ = self.fixture.rollback_material(
            existing_decisions=existing,
            action="ROLLBACK",
            current_uid=CANDIDATE_2,
            target_uid=CANDIDATE_1,
            current_event_digest=promote_2["decision_digest"],
            target_event_digest=self.fixture.promote_1[
                "decision_digest"
            ],
            current_model_digest=promote_2[
                "candidate_model_snapshot_digest"
            ],
            target_model_digest=self.current_model,
            suffix=70,
            completed_at="2026-07-23T00:00:05.000000Z",
            decided_at="2026-07-23T00:00:06.000000Z",
            emergency=False,
        )
        base_evidence, base_scorecards, base_eval_runs = self._base_maps()
        with self.assertRaisesRegex(
            RollbackControllerError,
            "ROLLBACK_TARGET_NOT_RESTORABLE_PRIOR_CHAMPION",
        ):
            self._append(
                rollback_drill,
                rollback,
                "0" * 64,
                existing=existing,
                promotion_evidence={
                    **base_evidence,
                    evidence_2["evidence_bundle_digest"]: evidence_2,
                },
                scorecards={**base_scorecards, **scorecards_2},
                eval_runs={**base_eval_runs, **eval_runs_2},
                drills={
                    revoke_drill["evidence_bundle_digest"]: revoke_drill,
                    rollback_drill["evidence_bundle_digest"]:
                    rollback_drill,
                },
            )

    def test_schema_trust_and_failed_drill_claims_fail_closed(self):
        with self.assertRaisesRegex(
            RollbackControllerError,
            "ROLLBACK_DRILL_SCHEMA_TRUST_MISMATCH",
        ):
            build_rollback_contract(
                self.fixture.promotion.bundle,
                self.fixture.drill_schema,
                "f" * 64,
            )

        drill, decision, predecessor = self.fixture.rollback_material(
            existing_decisions=[self.fixture.promote_1],
            action="ROLLBACK",
            current_uid=CANDIDATE_1,
            target_uid=BASELINE,
            current_event_digest=self.fixture.promote_1[
                "decision_digest"
            ],
            target_event_digest=None,
            current_model_digest=self.current_model,
            target_model_digest=self.baseline_model,
            suffix=71,
            completed_at="2026-07-23T00:00:02.000000Z",
            decided_at="2026-07-23T00:00:03.000000Z",
            emergency=False,
        )
        invalid = copy.deepcopy(drill)
        invalid["restore_target_content_verified"] = False
        invalid["evidence_bundle_digest"] = canonical_digest(
            invalid,
            "/evidence_bundle_digest",
        )
        invalid_decision = copy.deepcopy(decision)
        invalid_decision["evidence_bundle_digest"] = invalid[
            "evidence_bundle_digest"
        ]
        finalize_self_digest(
            self.fixture.promotion.bundle,
            (
                "urn:linzecolin:agentdatabase:skillops:"
                "schema:promotion-decision:v1"
            ),
            invalid_decision,
        )
        with self.assertRaisesRegex(
            RollbackControllerError,
            "LIFECYCLE_ROLLBACK_DRILL_INVALID",
        ):
            self._append(invalid, invalid_decision, predecessor)

    def test_drill_time_and_verification_closure_fail_closed(self):
        drill, decision, predecessor = self.fixture.rollback_material(
            existing_decisions=[self.fixture.promote_1],
            action="ROLLBACK",
            current_uid=CANDIDATE_1,
            target_uid=BASELINE,
            current_event_digest=self.fixture.promote_1[
                "decision_digest"
            ],
            target_event_digest=None,
            current_model_digest=self.current_model,
            target_model_digest=self.baseline_model,
            suffix=72,
            completed_at="2026-07-23T00:00:04.000000Z",
            decided_at="2026-07-23T00:00:03.000000Z",
            emergency=False,
        )
        with self.assertRaisesRegex(
            RollbackControllerError,
            "ROLLBACK_DRILL_AFTER_DECISION_FORBIDDEN",
        ):
            self._append(drill, decision, predecessor)

        drill, decision, predecessor = self.fixture.rollback_material(
            existing_decisions=[self.fixture.promote_1],
            action="ROLLBACK",
            current_uid=CANDIDATE_1,
            target_uid=BASELINE,
            current_event_digest=self.fixture.promote_1[
                "decision_digest"
            ],
            target_event_digest=None,
            current_model_digest=self.current_model,
            target_model_digest=self.baseline_model,
            suffix=73,
            completed_at="2026-07-23T00:00:02.000000Z",
            decided_at="2026-07-23T00:00:03.000000Z",
            emergency=False,
        )
        incomplete = copy.deepcopy(drill)
        incomplete["verification_evidence_refs"][4]["kind"] = (
            "REFERENCE_CLOSURE"
        )
        incomplete["evidence_bundle_digest"] = canonical_digest(
            incomplete,
            "/evidence_bundle_digest",
        )
        incomplete_decision = copy.deepcopy(decision)
        incomplete_decision["evidence_bundle_digest"] = incomplete[
            "evidence_bundle_digest"
        ]
        finalize_self_digest(
            self.fixture.promotion.bundle,
            (
                "urn:linzecolin:agentdatabase:skillops:"
                "schema:promotion-decision:v1"
            ),
            incomplete_decision,
        )
        with self.assertRaisesRegex(
            RollbackControllerError,
            "ROLLBACK_DRILL_VERIFICATION_CLOSURE_INCOMPLETE",
        ):
            self._append(
                incomplete,
                incomplete_decision,
                predecessor,
            )

    def test_builder_is_byte_equivalent_and_real_registry_is_not_actionable(self):
        process = subprocess.run(
            [
                sys.executable,
                "-B",
                str(
                    GOVERNANCE
                    / "tools"
                    / "build_rollback_revocation_controller.py"
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
        self.assertIn("ROLLBACK_CONTROLLER_BYTE_EQUIVALENT", process.stdout)
        readiness = parse_json_bytes(OUTPUT_PATH.read_bytes())
        self.assertEqual(build_readiness(), readiness)
        self.assertEqual(
            build_drill_schema(),
            parse_json_bytes(DRILL_SCHEMA_PATH.read_bytes()),
        )
        self.assertEqual(
            build_readiness_schema(),
            parse_json_bytes(READINESS_SCHEMA_PATH.read_bytes()),
        )
        self.assertEqual(NEXT_PHASE, readiness["next_phase"])
        self.assertFalse(
            readiness["registry_observation"][
                "real_rollback_revocation_execution_permitted"
            ]
        )
        self.assertFalse((ROOT / "CodexSkills" / "VERSION").exists())
        self.assertTrue(CONTROLLER_PATH.is_file())


if __name__ == "__main__":
    unittest.main()
