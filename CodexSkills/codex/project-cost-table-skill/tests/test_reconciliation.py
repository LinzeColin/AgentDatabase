import json
import random
import unittest
from dataclasses import replace

from project_cost_table.dedup import deduplicate_events
from project_cost_table.events import SourceEventStatus
from project_cost_table.links import LinkStatus, MatchMethod, RelationType, create_event_link, reconcile_event_links
from project_cost_table.reconciliation import (
    ParseErrorAmount,
    ReconciliationError,
    build_source_conservation,
    combine_r7_reconciliation,
)

from r7_helpers import EVIDENCE, relation_event


class SourceReconciliationTests(unittest.TestCase):
    def test_source_control_equals_included_excluded_pending_and_parse_error_pools(self) -> None:
        active = relation_event("active", amount_minor=10_000, event_date="2000-01-01")
        duplicate = relation_event(
            "duplicate",
            source_key_seed="active",
            digest_seed="digest:active",
            artifact_seed="duplicate-download",
            amount_minor=10_000,
            document_id="DOC-active",
            event_date="2000-01-01",
        )
        pending = relation_event(
            "pending",
            amount_minor=2_000,
            event_status=SourceEventStatus.SOURCE_PENDING,
            event_date="2000-02-01",
        )
        cancelled = relation_event(
            "cancelled",
            amount_minor=3_000,
            event_status=SourceEventStatus.SOURCE_CANCELLED,
            event_date="2000-03-01",
        )
        events = [cancelled, duplicate, active, pending]
        dedup = deduplicate_events(events)
        report = build_source_conservation(
            events,
            dedup_result=dedup,
            parse_errors=[ParseErrorAmount("parse_error_" + "1" * 32, 500, "SYNTHETIC_PARSE_ERROR")],
        )
        self.assertEqual(report.source_control_amount_minor, 25_500)
        self.assertEqual(report.included_amount_minor, 10_000)
        self.assertEqual(report.excluded_amount_minor, 13_000)
        self.assertEqual(report.pending_amount_minor, 2_000)
        self.assertEqual(report.parse_error_amount_minor, 500)
        self.assertEqual(report.source_conservation_delta_minor, 0)
        self.assertEqual(report.source_conservation_absolute_delta_minor, 0)
        self.assertEqual(report.dual_channel_delta_minor, 0)
        self.assertEqual(report.dual_channel_absolute_delta_minor, 0)
        self.assertEqual(report.conservation_status, "PASS")
        self.assertEqual(report.execution_status, "BLOCKED")
        self.assertFalse(report.formal_ready)

    def test_signed_reversal_nets_to_zero_while_absolute_conservation_remains_visible(self) -> None:
        original = relation_event("original", amount_minor=10_000, event_date="2000-01-01")
        reversal = relation_event(
            "reversal",
            amount_minor=-10_000,
            event_status=SourceEventStatus.SOURCE_REVERSED,
            reversal_of_event_id=original.economic_event_id,
            event_date="2000-01-02",
        )
        events = [reversal, original]
        report = build_source_conservation(events, dedup_result=deduplicate_events(events))
        self.assertEqual(report.source_control_amount_minor, 0)
        self.assertEqual(report.included_amount_minor, 0)
        self.assertEqual(report.source_control_absolute_minor, 20_000)
        self.assertEqual(report.included_absolute_minor, 20_000)
        self.assertEqual(report.execution_status, "PASS")

    def test_duplicate_insertion_keeps_included_amount_stable_and_moves_alias_to_excluded(self) -> None:
        original = relation_event("stable", amount_minor=12_345)
        duplicate = relation_event(
            "stable-alias",
            source_key_seed="stable",
            digest_seed="digest:stable",
            artifact_seed="another-download",
            amount_minor=12_345,
            document_id="DOC-stable",
        )
        one = build_source_conservation([original], dedup_result=deduplicate_events([original]))
        two = build_source_conservation(
            [duplicate, original], dedup_result=deduplicate_events([duplicate, original])
        )
        self.assertEqual(one.included_amount_minor, two.included_amount_minor)
        self.assertEqual(two.excluded_amount_minor, 12_345)
        self.assertEqual(two.source_conservation_delta_minor, 0)

    def test_order_metamorphism_is_byte_deterministic(self) -> None:
        events = [
            relation_event("order-a", amount_minor=111, event_date="2000-01-01"),
            relation_event("order-b", amount_minor=-22, event_date="2000-01-02"),
        ]
        first = build_source_conservation(events, dedup_result=deduplicate_events(events))
        second_events = list(reversed(events))
        second = build_source_conservation(second_events, dedup_result=deduplicate_events(second_events))
        self.assertEqual(first.as_private_dict(), second.as_private_dict())

    def test_tamper_evident_reconciliation_rejects_changed_channel_total(self) -> None:
        event = relation_event("tamper", amount_minor=100)
        report = build_source_conservation([event], dedup_result=deduplicate_events([event]))
        with self.assertRaises(ReconciliationError) as caught:
            replace(report, channel_b_included_amount_minor=99).validate()
        self.assertEqual(caught.exception.code, "DUAL_CHANNEL_DELTA_INVALID")

    def test_combined_r7_controls_block_candidate_links_but_do_not_claim_metric_or_company_approval(self) -> None:
        cost = relation_event("combined-cost")
        from project_cost_table.events import EventDirection, LifecycleStage

        cash = relation_event(
            "combined-cash",
            direction=EventDirection.CASH_OUT,
            stage=LifecycleStage.PAID,
        )
        link = create_event_link(
            relation_type=RelationType.SETTLES,
            source_events=[cost],
            target_events=[cash],
            source_allocations={cost.relation_event_ref: 10_000},
            target_allocations={cash.relation_event_ref: 10_000},
            status=LinkStatus.CANDIDATE,
            match_method=MatchMethod.AMOUNT_DATE_TEXT_SIMILARITY,
        )
        events = [cost, cash]
        source = build_source_conservation(events, dedup_result=deduplicate_events(events))
        combined = combine_r7_reconciliation(source, reconcile_event_links([link]))
        self.assertEqual(combined.status, "BLOCKED_R7_CONTROLS")
        payload = combined.as_private_dict()
        self.assertEqual(payload["metric_inclusion_status"], "NOT_EVALUATED_R7")
        self.assertFalse(payload["company_approval_state_managed"])
        self.assertFalse(combined.formal_ready)

    def test_public_summary_is_aggregate_only(self) -> None:
        event = relation_event("public-reconciliation", amount_minor=123)
        report = build_source_conservation([event], dedup_result=deduplicate_events([event]))
        public = json.dumps(report.as_public_summary())
        self.assertNotIn("relation_event_", public)
        self.assertNotIn("PROJECT-S", public)
        self.assertNotIn("identity", public.casefold())

    def test_signed_and_absolute_conservation_property_sample(self) -> None:
        generator = random.Random(707)
        statuses = (
            SourceEventStatus.SOURCE_ACTIVE,
            SourceEventStatus.SOURCE_PENDING,
            SourceEventStatus.SOURCE_CANCELLED,
        )
        events = []
        for number in range(64):
            magnitude = generator.randint(1, 1_000_000) + number * 1_000_001
            amount = magnitude if generator.randrange(2) else -magnitude
            events.append(
                relation_event(
                    "property-%03d" % number,
                    amount_minor=amount,
                    event_status=statuses[number % len(statuses)],
                    event_date="2000-%02d-%02d" % (1 + number // 28, 1 + number % 28),
                )
            )
        report = build_source_conservation(events, dedup_result=deduplicate_events(events))
        self.assertEqual(report.source_conservation_delta_minor, 0)
        self.assertEqual(report.source_conservation_absolute_delta_minor, 0)
        self.assertEqual(report.dual_channel_delta_minor, 0)
        self.assertEqual(report.dual_channel_absolute_delta_minor, 0)
        self.assertEqual(report.source_control_count, 64)


if __name__ == "__main__":
    unittest.main()
