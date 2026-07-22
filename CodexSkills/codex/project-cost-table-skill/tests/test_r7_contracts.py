import inspect
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from project_cost_table.dedup import deduplicate_events
from project_cost_table.events import EventDirection, LifecycleStage
from project_cost_table.links import LinkStatus, MatchMethod, RelationType, create_event_link
from project_cost_table.reconciliation import build_source_conservation

from r7_helpers import EVIDENCE, relation_event


MODULE_ROOT = Path(__file__).resolve().parents[1]


class R7ContractTests(unittest.TestCase):
    def validate_schema(self, name: str, payload: dict) -> None:
        schema = json.loads((MODULE_ROOT / "schemas" / name).read_text(encoding="utf-8"))
        errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(payload))
        self.assertEqual(errors, [], [item.message for item in errors])

    def test_relation_dedup_link_and_reconciliation_payloads_match_public_schemas(self) -> None:
        contract = relation_event(
            "schema-contract",
            direction=EventDirection.REVENUE,
            stage=LifecycleStage.CONTRACT_VALUE,
            amount_minor=1_000,
        )
        invoice = relation_event(
            "schema-invoice",
            direction=EventDirection.REVENUE,
            stage=LifecycleStage.BILLED,
            amount_minor=1_000,
        )
        dedup = deduplicate_events([contract, invoice])
        link = create_event_link(
            relation_type=RelationType.INVOICES,
            source_events=[contract],
            target_events=[invoice],
            source_allocations={contract.relation_event_ref: 1_000},
            target_allocations={invoice.relation_event_ref: 1_000},
            status=LinkStatus.APPROVED,
            match_method=MatchMethod.STABLE_IDENTIFIER,
            evidence_refs=(EVIDENCE,),
        )
        reconciliation = build_source_conservation([invoice, contract], dedup_result=dedup)
        self.validate_schema("relation_event.schema.json", contract.as_private_dict())
        for decision in dedup.decisions:
            self.validate_schema("dedup_decision.schema.json", decision.as_dict())
        self.validate_schema("event_link.schema.json", link.as_private_dict())
        self.validate_schema("source_conservation.schema.json", reconciliation.as_private_dict())

    def test_dual_channels_are_separate_implementations_and_all_r7_money_uses_minor_units(self) -> None:
        source = inspect.getsource(build_source_conservation)
        self.assertIn("Channel A: direct included-row iteration", source)
        self.assertIn("Channel B: an independent control-minus-nonincluded implementation", source)
        self.assertIn("channel_a_signed", source)
        self.assertIn("channel_b_signed", source)
        for module_name in ("events.py", "dedup.py", "links.py", "reconciliation.py"):
            text = (MODULE_ROOT / "src" / "project_cost_table" / module_name).read_text(encoding="utf-8")
            self.assertNotIn("float(", text)
            self.assertNotIn("company_approver", text.casefold())
            self.assertNotIn("finance_owner", text.casefold())

    def test_r7_review_tasks_never_assign_an_internal_owner_or_approver(self) -> None:
        text = "\n".join(
            (MODULE_ROOT / "src" / "project_cost_table" / name).read_text(encoding="utf-8")
            for name in ("dedup.py", "links.py", "reconciliation.py")
        ).casefold()
        for forbidden in (
            "approval_assignee",
            "authorized_person",
            "finance_owner",
            "company_approver",
            "approver_id",
        ):
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
