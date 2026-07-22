import json
import random
import tempfile
import unittest
from pathlib import Path

from project_cost_table.events import (
    EventDirection,
    EventIdentityBinding,
    LifecycleStage,
    RelationIdentityStatus,
    SourceEventStatus,
    relation_event_from_lifecycle_candidate,
)
from project_cost_table.links import (
    LinkCompletionStatus,
    LinkError,
    LinkStatus,
    MatchMethod,
    RelationType,
    create_event_link,
    reconcile_event_links,
)

from r6_helpers import read_rows, business_row
from r7_helpers import EVIDENCE, INPUT_RESOLUTION, opaque, relation_event


class EventLinkTests(unittest.TestCase):
    def allocation(self, event, amount=None):
        return {event.relation_event_ref: abs(event.base_amount_minor) if amount is None else amount}

    def test_one_to_many_and_many_to_one_allocations_conserve_zero_cents(self) -> None:
        contract = relation_event(
            "contract",
            direction=EventDirection.REVENUE,
            stage=LifecycleStage.CONTRACT_VALUE,
            amount_minor=10_000,
        )
        invoice_a = relation_event(
            "invoice-a",
            direction=EventDirection.REVENUE,
            stage=LifecycleStage.BILLED,
            amount_minor=6_000,
        )
        invoice_b = relation_event(
            "invoice-b",
            direction=EventDirection.REVENUE,
            stage=LifecycleStage.BILLED,
            amount_minor=4_000,
        )
        one_to_many = create_event_link(
            relation_type=RelationType.INVOICES,
            source_events=[contract],
            target_events=[invoice_b, invoice_a],
            source_allocations={contract.relation_event_ref: 10_000},
            target_allocations={invoice_a.relation_event_ref: 6_000, invoice_b.relation_event_ref: 4_000},
            status=LinkStatus.APPROVED,
            match_method=MatchMethod.STABLE_IDENTIFIER,
            evidence_refs=(EVIDENCE,),
        )
        self.assertEqual(one_to_many.allocation_delta_minor, 0)
        self.assertEqual(one_to_many.completion_status, LinkCompletionStatus.FULLY_ALLOCATED)

        change_a = relation_event(
            "change-a",
            direction=EventDirection.REVENUE,
            stage=LifecycleStage.CONTRACT_VALUE,
            amount_minor=6_000,
        )
        change_b = relation_event(
            "change-b",
            direction=EventDirection.REVENUE,
            stage=LifecycleStage.CONTRACT_VALUE,
            amount_minor=4_000,
        )
        combined_invoice = relation_event(
            "combined",
            direction=EventDirection.REVENUE,
            stage=LifecycleStage.BILLED,
            amount_minor=10_000,
        )
        many_to_one = create_event_link(
            relation_type=RelationType.INVOICES,
            source_events=[change_a, change_b],
            target_events=[combined_invoice],
            source_allocations={change_a.relation_event_ref: 6_000, change_b.relation_event_ref: 4_000},
            target_allocations={combined_invoice.relation_event_ref: 10_000},
            status=LinkStatus.APPROVED,
            match_method=MatchMethod.VALIDATED_IDENTITY_CONTRACT,
            evidence_refs=(EVIDENCE,),
        )
        self.assertEqual(many_to_one.allocation_delta_minor, 0)
        self.assertEqual(many_to_one.completion_status, LinkCompletionStatus.FULLY_ALLOCATED)

    def test_invoice_to_gl_and_gl_to_payment_are_separate_axes(self) -> None:
        invoice = relation_event(
            "invoice",
            direction=EventDirection.REVENUE,
            stage=LifecycleStage.BILLED,
            amount_minor=10_000,
        )
        revenue_gl = relation_event(
            "revenue-gl",
            direction=EventDirection.REVENUE,
            stage=LifecycleStage.RECOGNIZED_REVENUE,
            amount_minor=10_000,
        )
        invoice_gl = create_event_link(
            relation_type=RelationType.POSTS_TO_GL,
            source_events=[invoice],
            target_events=[revenue_gl],
            source_allocations=self.allocation(invoice),
            target_allocations=self.allocation(revenue_gl),
            status=LinkStatus.APPROVED,
            match_method=MatchMethod.STABLE_IDENTIFIER,
            evidence_refs=(EVIDENCE,),
        )

        cost_gl = relation_event("cost-gl", amount_minor=7_500)
        payment = relation_event(
            "payment",
            direction=EventDirection.CASH_OUT,
            stage=LifecycleStage.PAID,
            amount_minor=7_500,
        )
        gl_payment = create_event_link(
            relation_type=RelationType.SETTLES,
            source_events=[cost_gl],
            target_events=[payment],
            source_allocations=self.allocation(cost_gl),
            target_allocations=self.allocation(payment),
            status=LinkStatus.APPROVED,
            match_method=MatchMethod.STABLE_IDENTIFIER,
            evidence_refs=(EVIDENCE,),
        )
        result = reconcile_event_links([gl_payment, invoice_gl])
        self.assertEqual(result.status, "PASS")
        self.assertEqual(result.allocation_conservation_delta_minor, 0)

    def test_same_invoice_can_participate_once_per_different_relation_axis(self) -> None:
        contract = relation_event(
            "contract-axis",
            direction=EventDirection.REVENUE,
            stage=LifecycleStage.CONTRACT_VALUE,
            amount_minor=10_000,
        )
        invoice = relation_event(
            "invoice-axis",
            direction=EventDirection.REVENUE,
            stage=LifecycleStage.BILLED,
            amount_minor=10_000,
        )
        gl = relation_event(
            "gl-axis",
            direction=EventDirection.REVENUE,
            stage=LifecycleStage.RECOGNIZED_REVENUE,
            amount_minor=10_000,
        )
        contract_invoice = create_event_link(
            relation_type=RelationType.INVOICES,
            source_events=[contract],
            target_events=[invoice],
            source_allocations=self.allocation(contract),
            target_allocations=self.allocation(invoice),
            status=LinkStatus.APPROVED,
            match_method=MatchMethod.STABLE_IDENTIFIER,
            evidence_refs=(EVIDENCE,),
        )
        invoice_gl = create_event_link(
            relation_type=RelationType.POSTS_TO_GL,
            source_events=[invoice],
            target_events=[gl],
            source_allocations=self.allocation(invoice),
            target_allocations=self.allocation(gl),
            status=LinkStatus.APPROVED,
            match_method=MatchMethod.STABLE_IDENTIFIER,
            evidence_refs=(EVIDENCE,),
        )
        result = reconcile_event_links([invoice_gl, contract_invoice])
        self.assertEqual(result.status, "PASS")

    def test_partial_allocation_preserves_visible_residual_and_blocks_link_set(self) -> None:
        contract = relation_event(
            "partial-contract",
            direction=EventDirection.REVENUE,
            stage=LifecycleStage.CONTRACT_VALUE,
            amount_minor=10_000,
        )
        invoice = relation_event(
            "partial-invoice",
            direction=EventDirection.REVENUE,
            stage=LifecycleStage.BILLED,
            amount_minor=6_000,
        )
        link = create_event_link(
            relation_type=RelationType.INVOICES,
            source_events=[contract],
            target_events=[invoice],
            source_allocations={contract.relation_event_ref: 6_000},
            target_allocations={invoice.relation_event_ref: 6_000},
            status=LinkStatus.APPROVED,
            match_method=MatchMethod.STABLE_IDENTIFIER,
            evidence_refs=(EVIDENCE,),
        )
        self.assertEqual(link.source_residual_base_amount_minor, 4_000)
        self.assertEqual(link.target_residual_base_amount_minor, 0)
        self.assertEqual(link.completion_status, LinkCompletionStatus.PENDING_RESIDUAL)
        result = reconcile_event_links([link])
        self.assertEqual(result.status, "BLOCKED")
        self.assertIn("PENDING_LINK_RESIDUAL", result.conflict_codes)
        self.assertFalse(result.formal_ready)

    def test_separate_partial_links_form_one_complete_match_group_without_false_residual(self) -> None:
        contract = relation_event(
            "group-contract",
            direction=EventDirection.REVENUE,
            stage=LifecycleStage.CONTRACT_VALUE,
            amount_minor=10_000,
        )
        invoices = [
            relation_event(
                "group-invoice-60",
                direction=EventDirection.REVENUE,
                stage=LifecycleStage.BILLED,
                amount_minor=6_000,
            ),
            relation_event(
                "group-invoice-40",
                direction=EventDirection.REVENUE,
                stage=LifecycleStage.BILLED,
                amount_minor=4_000,
            ),
        ]
        links = []
        for invoice in invoices:
            amount = abs(invoice.base_amount_minor)
            links.append(
                create_event_link(
                    relation_type=RelationType.INVOICES,
                    source_events=[contract],
                    target_events=[invoice],
                    source_allocations={contract.relation_event_ref: amount},
                    target_allocations={invoice.relation_event_ref: amount},
                    status=LinkStatus.APPROVED,
                    match_method=MatchMethod.STABLE_IDENTIFIER,
                    evidence_refs=(EVIDENCE,),
                )
            )
        self.assertTrue(all(item.completion_status == LinkCompletionStatus.PENDING_RESIDUAL for item in links))
        result = reconcile_event_links(links)
        self.assertEqual(result.status, "PASS")
        self.assertEqual(result.pending_residual_count, 0)
        self.assertEqual(len(result.match_groups), 1)
        self.assertEqual(result.match_groups[0].residual_capacity_minor, 0)
        self.assertEqual(result.match_groups[0].status, "PASS")

    def test_reversal_preserves_signed_events_and_nets_to_zero(self) -> None:
        original = relation_event("original", amount_minor=10_000)
        reversal = relation_event(
            "reversal",
            amount_minor=-10_000,
            event_status=SourceEventStatus.SOURCE_REVERSED,
            reversal_of_event_id=original.economic_event_id,
        )
        link = create_event_link(
            relation_type=RelationType.REVERSES,
            source_events=[original],
            target_events=[reversal],
            source_allocations=self.allocation(original),
            target_allocations=self.allocation(reversal),
            status=LinkStatus.APPROVED,
            match_method=MatchMethod.REVERSAL_LINEAGE,
            evidence_refs=(EVIDENCE,),
        )
        self.assertEqual(original.base_amount_minor + reversal.base_amount_minor, 0)
        self.assertEqual(link.allocated_base_amount_minor, 10_000)
        self.assertEqual(link.allocation_delta_minor, 0)

    def test_similarity_can_only_be_candidate_and_approved_link_needs_evidence(self) -> None:
        cost = relation_event("candidate-cost")
        cash = relation_event(
            "candidate-cash",
            direction=EventDirection.CASH_OUT,
            stage=LifecycleStage.PAID,
        )
        with self.assertRaises(LinkError) as similarity:
            create_event_link(
                relation_type=RelationType.SETTLES,
                source_events=[cost],
                target_events=[cash],
                source_allocations=self.allocation(cost),
                target_allocations=self.allocation(cash),
                status=LinkStatus.APPROVED,
                match_method=MatchMethod.AMOUNT_DATE_TEXT_SIMILARITY,
                evidence_refs=(EVIDENCE,),
            )
        self.assertEqual(similarity.exception.code, "LINK_SIMILARITY_CANNOT_APPROVE")
        with self.assertRaises(LinkError) as evidence:
            create_event_link(
                relation_type=RelationType.SETTLES,
                source_events=[cost],
                target_events=[cash],
                source_allocations=self.allocation(cost),
                target_allocations=self.allocation(cash),
                status=LinkStatus.APPROVED,
                match_method=MatchMethod.STABLE_IDENTIFIER,
            )
        self.assertEqual(evidence.exception.code, "LINK_APPROVED_EVIDENCE_REQUIRED")

        candidate = create_event_link(
            relation_type=RelationType.SETTLES,
            source_events=[cost],
            target_events=[cash],
            source_allocations=self.allocation(cost),
            target_allocations=self.allocation(cash),
            status=LinkStatus.CANDIDATE,
            match_method=MatchMethod.AMOUNT_DATE_TEXT_SIMILARITY,
        )
        result = reconcile_event_links([candidate])
        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.candidate_link_count, 1)

    def test_cross_scope_or_ambiguous_allocation_requires_allowed_type_and_input_resolution(self) -> None:
        cost = relation_event("cross-cost", project="PROJECT-A")
        cash = relation_event(
            "cross-cash",
            direction=EventDirection.CASH_OUT,
            stage=LifecycleStage.PAID,
            project="PROJECT-B",
        )
        with self.assertRaises(LinkError) as unresolved:
            create_event_link(
                relation_type=RelationType.SETTLES,
                source_events=[cost],
                target_events=[cash],
                source_allocations=self.allocation(cost),
                target_allocations=self.allocation(cash),
                status=LinkStatus.APPROVED,
                match_method=MatchMethod.STABLE_IDENTIFIER,
                evidence_refs=(EVIDENCE,),
            )
        self.assertEqual(unresolved.exception.code, "LINK_SCOPE_RESOLUTION_REQUIRED")
        resolved = create_event_link(
            relation_type=RelationType.SETTLES,
            source_events=[cost],
            target_events=[cash],
            source_allocations=self.allocation(cost),
            target_allocations=self.allocation(cash),
            status=LinkStatus.APPROVED,
            match_method=MatchMethod.INPUT_RESOLUTION_ALLOCATION,
            input_resolution_ref=INPUT_RESOLUTION,
            evidence_refs=(EVIDENCE,),
        )
        self.assertEqual(resolved.status, LinkStatus.APPROVED)

        unresolved_cash = relation_event(
            "ambiguous-cash",
            direction=EventDirection.CASH_OUT,
            stage=LifecycleStage.PAID,
            identity_status=RelationIdentityStatus.ALLOCATION_REQUIRED,
        )
        allocated = create_event_link(
            relation_type=RelationType.ALLOCATES_TO,
            source_events=[unresolved_cash],
            target_events=[cost],
            source_allocations=self.allocation(unresolved_cash),
            target_allocations=self.allocation(cost),
            status=LinkStatus.APPROVED,
            match_method=MatchMethod.INPUT_RESOLUTION_ALLOCATION,
            input_resolution_ref=INPUT_RESOLUTION,
            evidence_refs=(EVIDENCE,),
        )
        self.assertEqual(allocated.allocation_delta_minor, 0)

    def test_combined_links_detect_same_axis_overallocation(self) -> None:
        contract = relation_event(
            "over-contract",
            direction=EventDirection.REVENUE,
            stage=LifecycleStage.CONTRACT_VALUE,
            amount_minor=10_000,
        )
        invoice_a = relation_event(
            "over-invoice-a",
            direction=EventDirection.REVENUE,
            stage=LifecycleStage.BILLED,
            amount_minor=7_000,
        )
        invoice_b = relation_event(
            "over-invoice-b",
            direction=EventDirection.REVENUE,
            stage=LifecycleStage.BILLED,
            amount_minor=7_000,
        )
        links = []
        for invoice in (invoice_a, invoice_b):
            links.append(
                create_event_link(
                    relation_type=RelationType.INVOICES,
                    source_events=[contract],
                    target_events=[invoice],
                    source_allocations={contract.relation_event_ref: 7_000},
                    target_allocations={invoice.relation_event_ref: 7_000},
                    status=LinkStatus.APPROVED,
                    match_method=MatchMethod.STABLE_IDENTIFIER,
                    evidence_refs=(EVIDENCE,),
                )
            )
        result = reconcile_event_links(links)
        self.assertEqual(result.status, "BLOCKED")
        self.assertIn("LINK_AXIS_OVERALLOCATED", result.conflict_codes)

    def test_r6_candidate_adapter_preserves_original_event_and_requires_r7_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = read_rows(Path(temporary), "cash_out", [business_row("cash_out")])
        candidate = result.events[0]
        binding = EventIdentityBinding(
            economic_event_id=candidate.economic_event_id,
            identity_status=RelationIdentityStatus.VALIDATED_IDENTITY,
            legal_entity_id="ENTITY-S",
            canonical_project_id="PROJECT-S",
            wbs_or_cost_code="WBS-S",
            canonical_contract_id="CONTRACT-S",
            identity_record_ref=opaque("identity_record_", "adapter"),
            mapping_resolution_ref=opaque("identity_resolution_", "adapter"),
            evidence_refs=(EVIDENCE,),
        )
        relation = relation_event_from_lifecycle_candidate(
            candidate,
            identity_binding=binding,
            source_system_id="synthetic.r6",
            source_artifact_sha256="a" * 64,
        )
        self.assertEqual(relation.economic_event_id, candidate.economic_event_id)
        self.assertEqual(relation.lifecycle_stage, LifecycleStage.PAID)
        self.assertEqual(relation.metric_inclusion_status, "NOT_EVALUATED_R7")
        self.assertEqual(candidate.metric_inclusion_status, "NOT_EVALUATED_R6")

    def test_public_link_summary_contains_no_business_identifiers_or_approval_owner(self) -> None:
        cost = relation_event("public-cost")
        cash = relation_event(
            "public-cash",
            direction=EventDirection.CASH_OUT,
            stage=LifecycleStage.PAID,
        )
        link = create_event_link(
            relation_type=RelationType.SETTLES,
            source_events=[cost],
            target_events=[cash],
            source_allocations=self.allocation(cost),
            target_allocations=self.allocation(cash),
            status=LinkStatus.APPROVED,
            match_method=MatchMethod.STABLE_IDENTIFIER,
            evidence_refs=(EVIDENCE,),
        )
        public = json.dumps(reconcile_event_links([link]).as_public_summary())
        self.assertNotIn("PROJECT-S", public)
        self.assertNotIn(link.link_id, public)
        self.assertNotIn("approver", public.casefold())

    def test_one_to_many_allocation_property_sample(self) -> None:
        generator = random.Random(717)
        for case in range(24):
            part_count = generator.randint(1, 6)
            parts = [generator.randint(1, 100_000) for _ in range(part_count)]
            total = sum(parts)
            contract = relation_event(
                "property-contract-%02d" % case,
                direction=EventDirection.REVENUE,
                stage=LifecycleStage.CONTRACT_VALUE,
                amount_minor=total,
            )
            invoices = [
                relation_event(
                    "property-invoice-%02d-%02d" % (case, number),
                    direction=EventDirection.REVENUE,
                    stage=LifecycleStage.BILLED,
                    amount_minor=amount,
                )
                for number, amount in enumerate(parts)
            ]
            link = create_event_link(
                relation_type=RelationType.INVOICES,
                source_events=[contract],
                target_events=invoices,
                source_allocations={contract.relation_event_ref: total},
                target_allocations={item.relation_event_ref: abs(item.base_amount_minor) for item in invoices},
                status=LinkStatus.APPROVED,
                match_method=MatchMethod.STABLE_IDENTIFIER,
                evidence_refs=(EVIDENCE,),
            )
            result = reconcile_event_links([link])
            self.assertEqual(link.allocation_delta_minor, 0)
            self.assertEqual(result.status, "PASS")


if __name__ == "__main__":
    unittest.main()
