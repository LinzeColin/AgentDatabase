from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Optional
from unittest import mock

from jsonschema import Draft202012Validator, FormatChecker


MODULE_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = MODULE_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from project_cost_table.inventory import FileIdentity, source_id_for_relative_path
from project_cost_table.manifest import SourceSelection
from project_cost_table.money import MoneyProfile
from project_cost_table.readers.kingdee import (
    KingdeeReaderError,
    KingdeeReaderProfile,
    public_reader_summary,
    read_kingdee_ledger,
)
from project_cost_table.security import OLE_SIGNATURE, SecurityProfile
import project_cost_table.readers.kingdee as kingdee_module

from r5_helpers import (
    HEADERS,
    active_reader_profile,
    reader_profile_mapping,
    source_selection,
    standard_rows,
)
from synthetic_builders import NumericCell, write_tabular_xlsx


class KingdeeReaderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.security = SecurityProfile.from_yaml(MODULE_ROOT / "config" / "security_limits.yml")
        self.money = MoneyProfile.from_yaml(MODULE_ROOT / "config" / "money_profile.yml")

    def _read(self, root: Path, rows: list, *, profile: Optional[KingdeeReaderProfile] = None):
        profile = profile or active_reader_profile()
        path = root / "ledger.xlsx"
        write_tabular_xlsx(path, rows)
        return read_kingdee_ledger(
            input_root=root,
            selection=source_selection(root, path.name, profile),
            reader_profile=profile,
            security_profile=self.security,
            money_profile=self.money,
        )

    def test_value_only_xlsx_preserves_fields_and_conserves_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = self._read(Path(temporary), standard_rows())
        self.assertEqual(len(result.records), 7)
        self.assertEqual(result.control.physical_data_row_count, 8)
        self.assertEqual(result.control.empty_row_count, 1)
        self.assertEqual(result.control.row_conservation_delta, 0)
        self.assertEqual(result.records[1].account_code, "5001")
        self.assertEqual(result.records[1].posting_date, "2000-01-31")
        self.assertEqual(result.records[1].debit_minor, 10000)
        self.assertEqual(result.records[0].balance_minor, 0)
        self.assertIsNone(result.records[0].debit_minor)
        self.assertRegex(result.records[0].source_record_ref, r"^rec_source_[0-9a-f]{32}$")
        self.assertRegex(result.records[0].source_business_key_hash, r"^ledger_line_[0-9a-f]{32}$")
        self.assertEqual(result.control.debit.total_minor, 195600)
        self.assertEqual(result.control.credit.total_minor, 8000)
        schema = json.loads((MODULE_ROOT / "schemas" / "kingdee_ledger_record.schema.json").read_text(encoding="utf-8"))
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        self.assertEqual(list(validator.iter_errors(result.records[0].as_private_dict())), [])

    def test_public_summary_redacts_paths_hashes_accounts_and_amounts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = self._read(Path(temporary), standard_rows())
            payload = json.dumps(public_reader_summary(result), sort_keys=True)
        for forbidden in ("sha256", "ledger.xlsx", "5001", "10000", "PROJECT-S", "Entity"):
            self.assertNotIn(forbidden, payload)
        self.assertIn('"row_conservation_delta": 0', payload)

    def test_business_fingerprint_ignores_zip_metadata_and_row_order(self) -> None:
        rows = standard_rows()
        reordered = [rows[0], rows[2], rows[1], *rows[3:]]
        with tempfile.TemporaryDirectory() as first_temp, tempfile.TemporaryDirectory() as second_temp:
            first = self._read(Path(first_temp), rows)
            second = self._read(Path(second_temp), reordered)
        self.assertNotEqual(first.source_sha256, second.source_sha256)
        self.assertEqual(first.business_fingerprint, second.business_fingerprint)

    def test_schema_digest_reader_and_active_profile_drift_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "ledger.xlsx"
            write_tabular_xlsx(path, standard_rows())
            profile = active_reader_profile()
            selection = source_selection(root, path.name, profile)
            cases = []
            drift_headers = list(HEADERS)
            drift_headers[0] = "ChangedEntity"
            cases.append((drift_headers, selection, profile, "LEDGER_SCHEMA_DRIFT"))
            inactive = KingdeeReaderProfile.from_mapping(reader_profile_mapping(status="TEMPLATE_NOT_ACTIVE"))
            cases.append((list(HEADERS), source_selection(root, path.name, inactive), inactive, "READER_PROFILE_NOT_ACTIVE"))
            for headers, selected, selected_profile, code in cases:
                with self.subTest(code=code):
                    write_tabular_xlsx(path, [headers, *standard_rows()[1:]])
                    selected = source_selection(root, path.name, selected_profile)
                    with self.assertRaises(KingdeeReaderError) as caught:
                        read_kingdee_ledger(
                            input_root=root,
                            selection=selected,
                            reader_profile=selected_profile,
                            security_profile=self.security,
                            money_profile=self.money,
                        )
                    self.assertEqual(caught.exception.code, code)
            write_tabular_xlsx(path, standard_rows())
            stale_selection = source_selection(root, path.name, profile)
            path.write_bytes(path.read_bytes() + b"drift")
            with self.assertRaises(KingdeeReaderError) as caught:
                read_kingdee_ledger(
                    input_root=root,
                    selection=stale_selection,
                    reader_profile=profile,
                    security_profile=self.security,
                    money_profile=self.money,
                )
            self.assertEqual(caught.exception.code, "LEDGER_SOURCE_DIGEST_DRIFT")

    def test_invalid_amount_and_missing_headers_never_become_zero(self) -> None:
        rows = standard_rows()
        rows[2][10] = "not-an-amount"
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(KingdeeReaderError) as caught:
                self._read(Path(temporary), rows)
        self.assertEqual(caught.exception.code, "LEDGER_AMOUNT_INVALID_AMOUNT_TEXT")
        self.assertEqual(caught.exception.column_id, "debit")
        self.assertEqual(caught.exception.partial_control.parse_failure_count, 1)
        self.assertEqual(caught.exception.partial_control.row_conservation_delta, 0)
        self.assertNotIn("not-an-amount", str(caught.exception))
        self.assertNotIn("not-an-amount", json.dumps(caught.exception.as_dict()))

        duplicate_headers = list(HEADERS)
        duplicate_headers[-1] = duplicate_headers[-2]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            profile = active_reader_profile()
            path = root / "ledger.xlsx"
            write_tabular_xlsx(path, [duplicate_headers, *standard_rows()[1:]])
            with self.assertRaises(KingdeeReaderError) as caught:
                read_kingdee_ledger(
                    input_root=root,
                    selection=source_selection(root, path.name, profile),
                    reader_profile=profile,
                    security_profile=self.security,
                    money_profile=self.money,
                )
        self.assertEqual(caught.exception.code, "LEDGER_DUPLICATE_HEADER")

    def test_governed_excel_serial_date_and_fictitious_1900_date(self) -> None:
        rows = standard_rows()[:2]
        rows[1][7] = NumericCell("1")
        rows[1][8] = NumericCell("1")
        rows[1][9] = NumericCell("1")
        with tempfile.TemporaryDirectory() as temporary:
            result = self._read(Path(temporary), rows)
        self.assertEqual(result.records[0].posting_date, "1900-01-01")
        rows[1][9] = NumericCell("60")
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(KingdeeReaderError) as caught:
                self._read(Path(temporary), rows)
        self.assertEqual(caught.exception.code, "LEDGER_DATE_PARSE")

    def test_legacy_xls_is_a_hard_block_not_an_empty_reader_result(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "ledger.xls"
            path.write_bytes(OLE_SIGNATURE + b"synthetic-public-legacy-xls")
            profile = active_reader_profile()
            metadata = path.stat()
            selection = SourceSelection(
                slot_id="general_ledger",
                source_id=source_id_for_relative_path(path.name),
                private_relative_path=path.name,
                sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                identity=FileIdentity(
                    metadata.st_dev,
                    metadata.st_ino,
                    metadata.st_size,
                    metadata.st_mtime_ns,
                    metadata.st_nlink,
                ),
                reader=profile.reader_id,
                reader_version=profile.reader_version,
                logical_source_period="2000-01",
                schema_id=profile.schema_id,
                schema_fingerprint=profile.schema_fingerprint,
                selection_resolution_ref=None,
            )
            with self.assertRaises(KingdeeReaderError) as caught:
                read_kingdee_ledger(
                    input_root=root,
                    selection=selection,
                    reader_profile=profile,
                    security_profile=self.security,
                    money_profile=self.money,
                )
        self.assertEqual(caught.exception.code, "UNSUPPORTED_LEGACY_XLS")

    def test_source_change_during_business_parse_is_discarded(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "ledger.xlsx"
            write_tabular_xlsx(path, standard_rows())
            profile = active_reader_profile()
            selection = source_selection(root, path.name, profile)
            original = kingdee_module._parse_xlsx

            def parse_then_tamper(source, **kwargs):
                result = original(source, **kwargs)
                with path.open("ab") as handle:
                    handle.write(b"changed-during-parse")
                return result

            with mock.patch.object(kingdee_module, "_parse_xlsx", side_effect=parse_then_tamper):
                with self.assertRaises(KingdeeReaderError) as caught:
                    read_kingdee_ledger(
                        input_root=root,
                        selection=selection,
                        reader_profile=profile,
                        security_profile=self.security,
                        money_profile=self.money,
                    )
        self.assertEqual(caught.exception.code, "LEDGER_SOURCE_CHANGED_DURING_PARSE")

    def test_same_bytes_replacement_requires_manifest_reselection(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "ledger.xlsx"
            write_tabular_xlsx(path, standard_rows())
            profile = active_reader_profile()
            selection = source_selection(root, path.name, profile)
            replacement = root / "replacement.xlsx"
            replacement.write_bytes(path.read_bytes())
            os.replace(replacement, path)
            with self.assertRaises(KingdeeReaderError) as caught:
                read_kingdee_ledger(
                    input_root=root,
                    selection=selection,
                    reader_profile=profile,
                    security_profile=self.security,
                    money_profile=self.money,
                )
        self.assertEqual(caught.exception.code, "LEDGER_SELECTION_IDENTITY_DRIFT")


if __name__ == "__main__":
    unittest.main()
