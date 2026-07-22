from __future__ import annotations

import dataclasses
import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path


MODULE_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = MODULE_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from project_cost_table.accounting_basis import (
    AccountingBasisError,
    AccountingBasisPolicy,
    AccountingScope,
    BasisId,
    BasisRunContext,
    ClosedPeriodRecord,
    ClosedPeriodSnapshot,
    LedgerIdentityBinding,
    public_accounting_summary,
    reconcile_accounting_bases,
)

from r5_helpers import (
    EVIDENCE,
    ACCOUNTING_SCOPES,
    SCOPE_FINGERPRINT,
    accounting_policy_mapping,
    active_accounting_policy,
    identity_bindings,
    identity_record,
    read_rows,
    standard_rows,
)


class AccountingBasisTests(unittest.TestCase):
    def _result(self, rows=None, *, policy=None, context=None, binding_transform=None):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        reader = read_rows(Path(temporary.name), rows or standard_rows())
        bindings = identity_bindings(reader.records)
        if binding_transform is not None:
            bindings = binding_transform(bindings)
        result = reconcile_accounting_bases(
            reader.records,
            identity_bindings=bindings,
            policy=policy or active_accounting_policy(),
            context=context
            or BasisRunContext(
                mode="calculate",
                period_start="2000-01-01",
                period_end="2000-01-31",
                as_of="2000-01-31",
                requested_scopes=ACCOUNTING_SCOPES,
            ),
        )
        return reader, result

    def test_two_basis_views_reconcile_without_cross_adding(self) -> None:
        reader, result = self._result()
        views = result.view_map()
        self.assertEqual(views[BasisId.JOB_COST_INCURRED].amount_minor, 10000)
        self.assertEqual(views[BasisId.GL_RECOGNIZED_COGS].amount_minor, 8000)
        self.assertNotEqual(sum(item.amount_minor for item in views.values()), 10000)
        self.assertEqual(result.bridges[0].expected_closing_wip_minor, 2000)
        self.assertEqual(result.bridges[0].bridge_delta_minor, 0)
        self.assertEqual(result.bridges[0].transfer_control_delta_minor, 0)
        self.assertEqual(result.conservation.row_delta, 0)
        self.assertEqual(result.conservation.debit_delta_minor, 0)
        self.assertEqual(result.conservation.credit_delta_minor, 0)
        self.assertEqual(
            dict(result.conservation.exclusion_counts),
            {"AFTER_PERIOD": 1, "EXCLUDED_DRAFT": 1},
        )
        self.assertEqual(len(result.account_controls), 2)
        self.assertEqual(len(reader.records), 7)

    def test_public_summary_contains_no_amount_hash_or_identity_dimension(self) -> None:
        _, result = self._result()
        payload = json.dumps(public_accounting_summary(result), sort_keys=True)
        for forbidden in ("amount", "sha256", "PROJECT-CANONICAL-1", "ENTITY-CANONICAL-1", "5001", "8000"):
            self.assertNotIn(forbidden, payload)
        self.assertIn("JOB_COST_INCURRED", payload)
        self.assertIn("GL_RECOGNIZED_COGS", payload)

    def test_nonzero_wip_or_transfer_delta_blocks_both_bases(self) -> None:
        with self.assertRaises(AccountingBasisError) as caught:
            self._result(standard_rows(closing="21.00"))
        self.assertEqual(caught.exception.code, "BLOCKED_WIP_BRIDGE")
        self.assertEqual(caught.exception.private_diagnostics[0].bridge_delta_minor, -100)

        rows = standard_rows()
        rows[3][11] = "70.00"
        with self.assertRaises(AccountingBasisError) as caught:
            self._result(rows)
        self.assertEqual(caught.exception.code, "BLOCKED_WIP_BRIDGE")
        self.assertEqual(caught.exception.private_diagnostics[0].transfer_control_delta_minor, -1000)

    def test_unknown_status_account_currency_policy_or_identity_fail_closed(self) -> None:
        cases = []
        rows = standard_rows()
        rows[2][14] = "UNMAPPED_STATUS"
        cases.append((rows, None, None, "BLOCKED_STATUS_POLICY"))
        rows = standard_rows()
        rows[2][4] = "9999"
        cases.append((rows, None, None, "BLOCKED_ACCOUNT_POLICY"))
        rows = standard_rows()
        rows[2][13] = "USD"
        cases.append((rows, None, None, "BLOCKED_CURRENCY"))
        for rows, policy, transform, code in cases:
            with self.subTest(code=code):
                with self.assertRaises(AccountingBasisError) as caught:
                    self._result(rows, policy=policy, binding_transform=transform)
                self.assertEqual(caught.exception.code, code)

        with self.assertRaises(AccountingBasisError) as caught:
            self._result(binding_transform=lambda bindings: bindings[1:])
        self.assertEqual(caught.exception.code, "BLOCKED_IDENTITY")

        inactive = AccountingBasisPolicy.from_mapping(accounting_policy_mapping(status="TEMPLATE_NOT_ACTIVE"))
        with self.assertRaises(AccountingBasisError) as caught:
            self._result(policy=inactive)
        self.assertEqual(caught.exception.code, "ACCOUNTING_POLICY_NOT_ACTIVE")

    def test_blank_counter_side_requires_evidence_backed_policy_choice(self) -> None:
        rows = standard_rows()
        rows[2][11] = None
        with self.assertRaises(AccountingBasisError) as caught:
            self._result(rows)
        self.assertEqual(caught.exception.code, "BLOCKED_LEDGER_AMOUNT")

        mapping = accounting_policy_mapping()
        mapping["blank_counter_side_as_zero"] = True
        policy = AccountingBasisPolicy.from_mapping(mapping)
        _, result = self._result(rows, policy=policy)
        self.assertEqual(result.view_map()[BasisId.JOB_COST_INCURRED].amount_minor, 10000)

    def test_metric_specific_as_of_exclusion_is_conserved(self) -> None:
        context = BasisRunContext(
            mode="calculate",
            period_start="2000-01-01",
            period_end="2000-02-29",
            as_of="2000-01-31",
            requested_scopes=ACCOUNTING_SCOPES,
        )
        _, result = self._result(context=context)
        self.assertEqual(dict(result.conservation.exclusion_counts)["AFTER_AS_OF"], 1)
        self.assertEqual(result.conservation.row_delta, 0)

    def test_exact_requested_scope_excludes_other_project_without_cross_aggregation(self) -> None:
        primary = standard_rows()
        other = [list(row) for row in standard_rows()[1:6]]
        for index, row in enumerate(other, start=1):
            row[1] = "PROJECT-OTHER"
            row[3] = "CONTRACT-2"
            row[5] = "OTHER-V-%d" % index
            row[6] = "OTHER-%d" % index
        rows = [*primary[:-1], *other, primary[-1]]
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        reader = read_rows(Path(temporary.name), rows)
        primary_identity = identity_record()
        other_identity = dataclasses.replace(
            primary_identity,
            canonical_project_id="PROJECT-CANONICAL-2",
            project_code="PROJECT-OTHER",
            contract_ids=("CONTRACT-2",),
            source_aliases=("source://kingdee/SYNTHETIC-PROJECT-OTHER",),
            mapping_resolution_ref="identity_resolution_" + "2" * 32,
        )
        other_identity.validate()
        bindings = tuple(
            LedgerIdentityBinding(
                source_record_ref=record.source_record_ref,
                identity_record=other_identity if record.project_source_key == "PROJECT-OTHER" else primary_identity,
                canonical_contract_id="CONTRACT-2" if record.project_source_key == "PROJECT-OTHER" else "CONTRACT-1",
                binding_evidence_ref=EVIDENCE,
            )
            for record in reader.records
        )
        result = reconcile_accounting_bases(
            reader.records,
            identity_bindings=bindings,
            policy=active_accounting_policy(),
            context=BasisRunContext(
                "calculate",
                "2000-01-01",
                "2000-01-31",
                "2000-01-31",
                ACCOUNTING_SCOPES,
            ),
        )
        self.assertEqual(result.view_map()[BasisId.JOB_COST_INCURRED].amount_minor, 10000)
        self.assertEqual(result.view_map()[BasisId.GL_RECOGNIZED_COGS].amount_minor, 8000)
        self.assertEqual(dict(result.conservation.exclusion_counts)["OUTSIDE_REQUESTED_SCOPE"], 5)

        unmatched_scope = (
            AccountingScope("PROJECT-NOT-PRESENT", "ENTITY-CANONICAL-1", "WBS-CANONICAL-1", "CONTRACT-1"),
        )
        with self.assertRaises(AccountingBasisError) as caught:
            self._result(
                context=BasisRunContext(
                    "calculate",
                    "2000-01-01",
                    "2000-01-31",
                    "2000-01-31",
                    unmatched_scope,
                )
            )
        self.assertEqual(caught.exception.code, "BLOCKED_WIP_CONTROL")

    def test_closed_period_snapshot_and_restatement_never_overwrite_history(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        reader = read_rows(Path(temporary.name), standard_rows())
        closed_records = tuple(
            ClosedPeriodRecord(item.source_business_key_hash, item.normalized_business_digest)
            for item in reader.records
            if date.fromisoformat(item.posting_date or "9999-12-31") <= date(2000, 1, 31)
        )
        snapshot = ClosedPeriodSnapshot.create(
            scope_fingerprint=SCOPE_FINGERPRINT,
            period_start="2000-01-01",
            closed_through="2000-01-31",
            records=closed_records,
            evidence_refs=(EVIDENCE,),
        )
        policy = active_accounting_policy(closed_through="2000-01-31")
        calculate = BasisRunContext(
            mode="calculate",
            period_start="2000-01-01",
            period_end="2000-01-31",
            as_of="2000-01-31",
            requested_scopes=ACCOUNTING_SCOPES,
            prior_closed_snapshot=snapshot,
        )
        result = reconcile_accounting_bases(
            reader.records,
            identity_bindings=identity_bindings(reader.records),
            policy=policy,
            context=calculate,
        )
        self.assertEqual(result.late_posting_record_count, 0)

        changed_temporary = tempfile.TemporaryDirectory()
        self.addCleanup(changed_temporary.cleanup)
        changed_rows = standard_rows(closing="21.00")
        changed_rows[2][10] = "101.00"
        changed = list(read_rows(Path(changed_temporary.name), changed_rows).records)
        with self.assertRaises(AccountingBasisError) as caught:
            reconcile_accounting_bases(
                changed,
                identity_bindings=identity_bindings(changed),
                policy=policy,
                context=calculate,
            )
        self.assertEqual(caught.exception.code, "RESTATEMENT_REQUIRED")

        restate = BasisRunContext(
            mode="restate",
            period_start="2000-01-01",
            period_end="2000-01-31",
            as_of="2000-01-31",
            requested_scopes=ACCOUNTING_SCOPES,
            prior_closed_snapshot=snapshot,
            supersedes_run_ref="run_prior_opaque_ref",
        )
        result = reconcile_accounting_bases(
            changed,
            identity_bindings=identity_bindings(changed),
            policy=policy,
            context=restate,
        )
        self.assertEqual(result.late_posting_record_count, 2)

        without_snapshot = dataclasses.replace(calculate, prior_closed_snapshot=None)
        with self.assertRaises(AccountingBasisError) as caught:
            reconcile_accounting_bases(
                reader.records,
                identity_bindings=identity_bindings(reader.records),
                policy=policy,
                context=without_snapshot,
            )
        self.assertEqual(caught.exception.code, "CLOSED_PERIOD_SNAPSHOT_REQUIRED")

        tampered = list(reader.records)
        tampered[1] = dataclasses.replace(tampered[1], debit_minor=10100)
        with self.assertRaises(AccountingBasisError) as caught:
            reconcile_accounting_bases(
                tampered,
                identity_bindings=identity_bindings(tampered),
                policy=active_accounting_policy(),
                context=BasisRunContext(
                    "calculate",
                    "2000-01-01",
                    "2000-01-31",
                    "2000-01-31",
                    ACCOUNTING_SCOPES,
                ),
            )
        self.assertEqual(caught.exception.code, "LEDGER_RECORD_TAMPERED")

    def test_duplicate_stable_line_and_relaxed_period_policy_are_blocked(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        reader = read_rows(Path(temporary.name), standard_rows())
        duplicate = reader.records + (reader.records[0],)
        with self.assertRaises(AccountingBasisError) as caught:
            reconcile_accounting_bases(
                duplicate,
                identity_bindings=identity_bindings(duplicate),
                policy=active_accounting_policy(),
                context=BasisRunContext(
                    "calculate",
                    "2000-01-01",
                    "2000-01-31",
                    "2000-01-31",
                    ACCOUNTING_SCOPES,
                ),
            )
        self.assertEqual(caught.exception.code, "DUPLICATE_SOURCE_RECORD_REF")

        mapping = accounting_policy_mapping()
        mapping["period_policy"]["late_posting_mode"] = "IGNORE_LATE_POSTINGS"
        with self.assertRaises(AccountingBasisError) as caught:
            AccountingBasisPolicy.from_mapping(mapping)
        self.assertEqual(caught.exception.code, "ACCOUNTING_POLICY_PERIOD")

        split_bridge = accounting_policy_mapping()
        split_bridge["account_rules"][1]["bridge_group_id"] = "UNRELATED-COGS-GROUP"
        with self.assertRaises(AccountingBasisError) as caught:
            AccountingBasisPolicy.from_mapping(split_bridge)
        self.assertEqual(caught.exception.code, "ACCOUNTING_POLICY_INCOMPLETE")

    def test_aggregate_minor_unit_overflow_is_blocked(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        rows = standard_rows()
        rows[2][10] = "92233720368547758.07"
        rows[6][10] = "92233720368547758.07"
        rows[6][14] = "POSTED"
        reader = read_rows(Path(temporary.name), rows)
        records = list(reader.records)
        with self.assertRaises(AccountingBasisError) as caught:
            reconcile_accounting_bases(
                records,
                identity_bindings=identity_bindings(records),
                policy=active_accounting_policy(),
                context=BasisRunContext(
                    "calculate",
                    "2000-01-01",
                    "2000-01-31",
                    "2000-01-31",
                    ACCOUNTING_SCOPES,
                ),
            )
        self.assertEqual(caught.exception.code, "BLOCKED_AGGREGATE_OVERFLOW")


if __name__ == "__main__":
    unittest.main()
