import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from project_cost_table.events import EconomicEventError, EventDirection, LifecycleStage
from project_cost_table.money import MoneyProfile
from project_cost_table.readers.lifecycle import (
    LifecycleReaderError,
    public_lifecycle_batch_summary,
    public_lifecycle_reader_summary,
    read_lifecycle_batch,
    read_lifecycle_source,
)
from project_cost_table.security import SecurityProfile

from r6_helpers import (
    HEADERS,
    MODULE_ROOT,
    active_reader_profile,
    business_row,
    read_rows,
    source_selection,
    write_source,
)
from synthetic_builders import write_tabular_xlsx, write_xlsx


class LifecycleReaderTests(unittest.TestCase):
    def security(self) -> SecurityProfile:
        return SecurityProfile.from_yaml(MODULE_ROOT / "config" / "security_limits.yml")

    def money(self) -> MoneyProfile:
        return MoneyProfile.from_yaml(MODULE_ROOT / "config" / "money_profile.yml")

    def test_four_slots_emit_only_their_governed_lifecycle_candidates(self) -> None:
        cases = (
            ("project_billing", EventDirection.REVENUE, LifecycleStage.BILLED),
            ("cash_out", EventDirection.CASH_OUT, LifecycleStage.PAID),
            ("cash_in", EventDirection.CASH_IN, LifecycleStage.COLLECTED),
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for slot_id, direction, stage in cases:
                case_root = root / slot_id
                case_root.mkdir()
                with self.subTest(slot_id=slot_id):
                    result = read_rows(case_root, slot_id, [business_row(slot_id)])
                    self.assertEqual(len(result.events), 1)
                    event = result.events[0]
                    self.assertEqual((event.direction, event.lifecycle_stage), (direction, stage))
                    self.assertEqual(event.identity_status, "PENDING_IDENTITY")
                    self.assertEqual(event.metric_inclusion_status, "NOT_EVALUATED_R6")

            contract_root = root / "contract"
            contract_root.mkdir()
            contract = read_rows(
                contract_root,
                "contract_and_changes",
                [
                    business_row("contract_and_changes", document_id="C-1", event_type="CUSTOMER_CONTRACT"),
                    business_row("contract_and_changes", document_id="S-1", event_type="SUPPLIER_COMMITMENT"),
                ],
            )
            self.assertEqual(
                {(item.direction, item.lifecycle_stage) for item in contract.events},
                {
                    (EventDirection.REVENUE, LifecycleStage.CONTRACT_VALUE),
                    (EventDirection.COST, LifecycleStage.COMMITMENT),
                },
            )

    def test_invoice_preserves_gross_net_tax_and_source_arithmetic_delta(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = read_rows(
                Path(temporary),
                "project_billing",
                [business_row("project_billing", gross="100.00", net="80.00", tax="15.00")],
            )
            record = result.records[0]
            event = result.events[0]
            self.assertEqual(record.source_arithmetic_status, "SOURCE_ARITHMETIC_DELTA")
            self.assertEqual(record.source_arithmetic_delta_minor, 500)
            self.assertEqual(event.source_arithmetic_delta_minor, 500)
            self.assertEqual((event.gross_amount_minor, event.net_amount_minor, event.tax_amount_minor), (10000, 8000, 1500))
            self.assertEqual(result.control.source_arithmetic_anomaly_count, 1)

    def test_payment_free_text_never_becomes_project_or_cost_recognition(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = read_rows(
                Path(temporary),
                "cash_out",
                [business_row("cash_out", project=None, note="candidate project text")],
            )
            event = result.events[0]
            self.assertIsNone(event.project_source_key)
            self.assertTrue(event.free_text_candidate_present)
            self.assertEqual(event.direction, EventDirection.CASH_OUT)
            self.assertEqual(event.lifecycle_stage, LifecycleStage.PAID)
            self.assertNotEqual(event.direction, EventDirection.COST)

    def test_unknown_status_event_type_and_row_kind_fail_closed(self) -> None:
        cases = (
            (business_row("cash_out", status="UNKNOWN"), "BLOCKED_STATUS_POLICY"),
            (business_row("cash_out", event_type="UNKNOWN"), "BLOCKED_EVENT_TYPE_POLICY"),
            (business_row("cash_out", row_kind="UNKNOWN"), "BLOCKED_ROW_KIND_POLICY"),
        )
        for row, expected_code in cases:
            with tempfile.TemporaryDirectory() as temporary, self.subTest(code=expected_code):
                with self.assertRaises(LifecycleReaderError) as caught:
                    read_rows(Path(temporary), "cash_out", [row])
                self.assertEqual(caught.exception.code, expected_code)

    def test_required_field_currency_header_formula_and_legacy_xls_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaises(LifecycleReaderError) as required:
                read_rows(root, "cash_out", [business_row("cash_out", document_id=None)], name="missing.xlsx")
            self.assertEqual(required.exception.code, "BLOCKED_REQUIRED_SOURCE_FIELD")

            with self.assertRaises(LifecycleReaderError) as currency:
                read_rows(root, "cash_out", [business_row("cash_out", currency="USD")], name="currency.xlsx")
            self.assertEqual(currency.exception.code, "BLOCKED_CURRENCY")

            with self.assertRaises(LifecycleReaderError) as timestamp:
                read_rows(
                    root,
                    "cash_out",
                    [business_row("cash_out", document_date="2000-01-10T12:30:00")],
                    name="timestamp.xlsx",
                )
            self.assertEqual(timestamp.exception.code, "LIFECYCLE_DATE_PARSE")

            profile = active_reader_profile("cash_out")
            drift = root / "drift.xlsx"
            headers = list(HEADERS)
            headers[0] = "ChangedEntityHeader"
            write_tabular_xlsx(drift, [headers, business_row("cash_out")], sheet_name=profile.sheet_name)
            with self.assertRaises(LifecycleReaderError) as schema:
                read_lifecycle_source(
                    input_root=root,
                    selection=source_selection(root, drift.name, profile),
                    reader_profile=profile,
                    security_profile=self.security(),
                    money_profile=self.money(),
                )
            self.assertEqual(schema.exception.code, "LIFECYCLE_SCHEMA_DRIFT")

            workbook = (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                '<sheets><sheet name="Lifecycle" sheetId="1" state="visible" r:id="rId1"/></sheets></workbook>'
            ).encode("utf-8")
            formula = root / "formula.xlsx"
            write_xlsx(formula, formula="SUM(1,2)", workbook_override=workbook)
            with self.assertRaises(LifecycleReaderError) as formula_error:
                read_lifecycle_source(
                    input_root=root,
                    selection=source_selection(root, formula.name, profile),
                    reader_profile=profile,
                    security_profile=self.security(),
                    money_profile=self.money(),
                )
            self.assertEqual(formula_error.exception.code, "OOXML_BLOCKED")

            legacy = root / "legacy.xls"
            legacy.write_bytes(bytes.fromhex("d0cf11e0a1b11ae1") + b"\x00" * 512)
            with self.assertRaises(LifecycleReaderError) as legacy_error:
                read_lifecycle_source(
                    input_root=root,
                    selection=source_selection(root, legacy.name, profile),
                    reader_profile=profile,
                    security_profile=self.security(),
                    money_profile=self.money(),
                )
            self.assertIn("XLS", legacy_error.exception.code)

    def test_reversed_event_requires_original_key_and_reversal_date(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaises(LifecycleReaderError) as caught:
                read_rows(root, "cash_out", [business_row("cash_out", status="REVERSED")], name="bad.xlsx")
            self.assertEqual(caught.exception.code, "EVENT_REVERSAL_LINEAGE_MISSING")
            good = read_rows(
                root,
                "cash_out",
                [
                    business_row(
                        "cash_out",
                        status="REVERSED",
                        reversal_of="PAYMENT-ORIGINAL",
                        reversal_date="2000-01-20",
                    )
                ],
                name="good.xlsx",
            )
            self.assertEqual(good.events[0].reversal_of_source_key, "PAYMENT-ORIGINAL")

    def test_exact_duplicate_exports_count_once_preserve_aliases_and_business_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            rows = [
                business_row("project_billing", document_id="INV-1", line_id="1"),
                business_row("project_billing", document_id="INV-2", line_id="1"),
            ]
            first_profile = write_source(root / "download-a.xlsx", "project_billing", rows)
            second_profile = write_source(root / "download-b.xlsx", "project_billing", tuple(reversed(rows)))
            first = source_selection(root, "download-a.xlsx", first_profile)
            second = source_selection(root, "download-b.xlsx", second_profile)
            self.assertNotEqual(first.sha256, second.sha256)
            profiles = {first_profile.reader_id: first_profile}
            one = read_lifecycle_batch(
                input_root=root,
                selections=[first],
                reader_profiles=profiles,
                security_profile=self.security(),
                money_profile=self.money(),
            )
            duplicate = read_lifecycle_batch(
                input_root=root,
                selections=[second, first],
                reader_profiles=profiles,
                security_profile=self.security(),
                money_profile=self.money(),
            )
            self.assertEqual(duplicate.control.selected_source_count, 2)
            self.assertEqual(duplicate.control.unique_export_count, 1)
            self.assertEqual(duplicate.control.duplicate_alias_count, 1)
            self.assertEqual(duplicate.control.pre_dedup_event_count, 4)
            self.assertEqual(duplicate.control.emitted_event_count, 2)
            self.assertEqual(duplicate.control.event_count_conservation_delta, 0)
            self.assertEqual(duplicate.control.event_amount_conservation_delta_minor, 0)
            self.assertTrue(all(len(item.source_record_refs) == 2 for item in duplicate.events))
            self.assertEqual(len(duplicate.duplicate_export_groups), 1)
            self.assertEqual(one.business_fingerprint, duplicate.business_fingerprint)

    def test_changed_status_is_not_a_duplicate_export_or_silent_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            profile = write_source(
                root / "approved.xlsx",
                "cash_in",
                [business_row("cash_in", status="APPROVED")],
            )
            write_source(
                root / "pending.xlsx",
                "cash_in",
                [business_row("cash_in", status="PENDING")],
            )
            batch = read_lifecycle_batch(
                input_root=root,
                selections=[
                    source_selection(root, "approved.xlsx", profile),
                    source_selection(root, "pending.xlsx", profile),
                ],
                reader_profiles={profile.reader_id: profile},
                security_profile=self.security(),
                money_profile=self.money(),
            )
            self.assertEqual(batch.control.unique_export_count, 2)
            self.assertEqual(batch.control.duplicate_alias_count, 0)
            self.assertEqual(batch.control.emitted_event_count, 2)
            self.assertEqual(batch.duplicate_export_groups, ())
            self.assertEqual({item.event_status.value for item in batch.events}, {"SOURCE_ACTIVE", "SOURCE_PENDING"})

    def test_control_rows_and_empty_rows_conserve_without_becoming_events(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = read_rows(
                Path(temporary),
                "cash_out",
                [
                    business_row("cash_out"),
                    business_row("cash_out", document_id="TOTAL", row_kind="TOTAL"),
                    [None] * len(HEADERS),
                ],
            )
            self.assertEqual(result.control.physical_data_row_count, 3)
            self.assertEqual(result.control.business_record_count, 1)
            self.assertEqual(result.control.control_record_count, 1)
            self.assertEqual(result.control.empty_row_count, 1)
            self.assertEqual(result.control.row_conservation_delta, 0)
            self.assertEqual(dict(result.control.business_amount_totals)["transaction_amount"], 10000)
            self.assertEqual(dict(result.control.control_amount_totals)["transaction_amount"], 10000)
            self.assertTrue(all(value == 0 for _, value in result.control.amount_partition_deltas))
            self.assertEqual(len(result.events), 1)

    def test_record_event_schemas_and_public_summaries_are_redacted(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            result = read_rows(root, "project_billing", [business_row("project_billing")])
            pairs = (
                (result.records[0].as_private_dict(), "lifecycle_source_record.schema.json"),
                (result.events[0].as_private_dict(), "economic_event_candidate.schema.json"),
            )
            for payload, schema_name in pairs:
                schema = json.loads((MODULE_ROOT / "schemas" / schema_name).read_text(encoding="utf-8"))
                errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(payload))
                self.assertEqual(errors, [])

            batch = read_lifecycle_batch(
                input_root=root,
                selections=[source_selection(root, "source.xlsx", active_reader_profile("project_billing"))],
                reader_profiles={"project_invoice_v2": active_reader_profile("project_billing")},
                security_profile=self.security(),
                money_profile=self.money(),
            )
            public = json.dumps(
                {
                    "reader": public_lifecycle_reader_summary(result),
                    "batch": public_lifecycle_batch_summary(batch),
                },
                sort_keys=True,
            )
            self.assertNotIn("10000", public)
            self.assertNotIn("DOC-1", public)
            self.assertNotIn("PROJECT-S", public)
            self.assertNotIn("source.xlsx", public)
            self.assertNotIn(batch.events[0].economic_event_id, public)

    def test_event_validation_detects_arithmetic_and_authority_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            event = read_rows(
                Path(temporary),
                "project_billing",
                [business_row("project_billing")],
            ).events[0]
            with self.assertRaises(EconomicEventError) as arithmetic:
                replace(event, source_arithmetic_delta_minor=1).validate()
            self.assertEqual(arithmetic.exception.code, "EVENT_SOURCE_ARITHMETIC_INVALID")
            with self.assertRaises(EconomicEventError) as authority:
                replace(event, metric_inclusion_status="FINAL_INCLUDED").validate()
            self.assertEqual(authority.exception.code, "EVENT_AUTHORITY_ESCALATION")


if __name__ == "__main__":
    unittest.main()
