import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path


MODULE_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = MODULE_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from project_cost_table.security import (  # noqa: E402
    FileSecurityError,
    SecurityProfile,
    inspect_ooxml,
    preflight_source_file,
    require_safe_ooxml,
)
from synthetic_builders import write_xlsx  # noqa: E402


PROFILE = SecurityProfile.from_yaml(MODULE_ROOT / "config" / "security_limits.yml")
OLE_HEADER = bytes.fromhex("D0CF11E0A1B11AE1")


class OoxmlSecurityTests(unittest.TestCase):
    def test_minimal_value_only_xlsx_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            book = root / "safe.xlsx"
            write_xlsx(book)
            report = require_safe_ooxml(root, book, profile=PROFILE)
            self.assertEqual(report.blocker_codes, ())
            self.assertEqual(report.formula_cell_count, 0)
            source = preflight_source_file(root, book, expected_kind="xlsx", profile=PROFILE)
            self.assertEqual(source.status, "PREFLIGHT_PASS")
            self.assertTrue(source.structured_data_allowed)

    def test_formula_cells_are_detected_and_blocked_without_execution(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            book = root / "formula.xlsx"
            write_xlsx(book, formula="1/0")
            report = inspect_ooxml(root, book, profile=PROFILE)
            self.assertEqual(report.formula_cell_count, 1)
            self.assertIn("OOXML_FORMULA_CELLS", report.blocker_codes)
            with self.assertRaises(FileSecurityError) as caught:
                require_safe_ooxml(root, book, profile=PROFILE)
            self.assertEqual(caught.exception.code, "OOXML_BLOCKED")

    def test_dde_formula_gets_specific_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            book = root / "dde.xlsx"
            write_xlsx(book, formula="'app'|'argument'!A0")
            report = inspect_ooxml(root, book, profile=PROFILE)
            self.assertEqual(report.dde_formula_count, 1)
            self.assertIn("OOXML_DDE_FORMULA", report.blocker_codes)

    def test_macro_extension_vba_part_and_macro_content_type_fail(self) -> None:
        variants = (
            ("macro.xlsm", {}, "MACRO_ENABLED_EXTENSION"),
            ("vba.xlsx", {"include_vba": True}, "OOXML_ACTIVE_CONTENT_PART"),
            ("type.xlsx", {"macro_content_type": True}, "OOXML_ACTIVE_CONTENT_TYPE"),
        )
        for filename, options, expected in variants:
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                book = root / filename
                write_xlsx(book, **options)
                if expected == "MACRO_ENABLED_EXTENSION":
                    with self.assertRaises(FileSecurityError) as caught:
                        inspect_ooxml(root, book, profile=PROFILE)
                    self.assertEqual(caught.exception.code, expected)
                else:
                    report = inspect_ooxml(root, book, profile=PROFILE)
                    self.assertIn(expected, report.blocker_codes)

    def test_external_relationship_connection_and_external_link_part_fail(self) -> None:
        variants = (
            ({"external_relationship": True}, "OOXML_EXTERNAL_RELATIONSHIP"),
            ({"include_connection": True}, "OOXML_DATA_CONNECTION"),
            ({"include_external_link_part": True}, "OOXML_ACTIVE_CONTENT_PART"),
        )
        for options, expected in variants:
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                book = root / "active.xlsx"
                write_xlsx(book, **options)
                report = inspect_ooxml(root, book, profile=PROFILE)
                self.assertIn(expected, report.blocker_codes)

    def test_image_only_sheet_blocks_structured_use(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            book = root / "image.xlsx"
            write_xlsx(book, image_only=True)
            report = inspect_ooxml(root, book, profile=PROFILE)
            self.assertEqual(report.image_only_sheet_count, 1)
            self.assertIn("OOXML_IMAGE_ONLY_SHEET", report.blocker_codes)

    def test_hidden_very_hidden_and_named_ranges_are_metadata_warnings(self) -> None:
        for state, attribute in (("hidden", "hidden_sheet_count"), ("veryHidden", "very_hidden_sheet_count")):
            with self.subTest(state=state), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                book = root / "metadata.xlsx"
                write_xlsx(book, sheet_state=state, defined_name=("SYNTH_NAME", "Sheet1!$A$1"))
                report = inspect_ooxml(root, book, profile=PROFILE)
                self.assertEqual(getattr(report, attribute), 1)
                self.assertEqual(report.named_range_count, 1)
                self.assertEqual(report.blocker_codes, ())

    def test_autorun_and_dde_defined_names_are_blocked(self) -> None:
        variants = (
            (("_xlnm.Auto_Open", "Sheet1!$A$1"), "OOXML_AUTORUN_DEFINED_NAME"),
            (("SYNTH", "'app'|'argument'!A0"), "OOXML_DDE_DEFINED_NAME"),
        )
        for defined_name, expected in variants:
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                book = root / "defined-name.xlsx"
                write_xlsx(book, defined_name=defined_name)
                report = inspect_ooxml(root, book, profile=PROFILE)
                self.assertIn(expected, report.blocker_codes)

    def test_dtd_and_xml_size_limit_fail_before_parse(self) -> None:
        dtd = b'<?xml version="1.0"?><!DOCTYPE workbook [<!ENTITY x "x">]><workbook>&x;</workbook>'
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            book = root / "dtd.xlsx"
            write_xlsx(book, workbook_override=dtd)
            with self.assertRaises(FileSecurityError) as caught:
                inspect_ooxml(root, book, profile=PROFILE)
            self.assertEqual(caught.exception.code, "XML_DTD_FORBIDDEN")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            book = root / "large-xml.xlsx"
            write_xlsx(book)
            strict = replace(PROFILE, xml_single_part_bytes_max=32)
            with self.assertRaises(FileSecurityError) as caught:
                inspect_ooxml(root, book, profile=strict)
            self.assertEqual(caught.exception.code, "XML_PART_SIZE_LIMIT")

    def test_missing_required_part_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            book = root / "missing.xlsx"
            write_xlsx(book, omit_required=("xl/workbook.xml",))
            with self.assertRaises(FileSecurityError) as caught:
                inspect_ooxml(root, book, profile=PROFILE)
            self.assertEqual(caught.exception.code, "OOXML_REQUIRED_PART_MISSING")


class SourceTypePreflightTests(unittest.TestCase):
    def test_legacy_xls_is_explicitly_blocked_not_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            book = root / "legacy.xls"
            book.write_bytes(OLE_HEADER + b"synthetic")
            with self.assertRaises(FileSecurityError) as caught:
                preflight_source_file(root, book, expected_kind="xls", profile=PROFILE)
            self.assertEqual(caught.exception.code, "UNSUPPORTED_LEGACY_XLS")

    def test_pdf_signature_passes_container_gate_but_not_structured_data(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            document = root / "document.pdf"
            document.write_bytes(b"%PDF-1.7\nsynthetic\n%%EOF")
            report = preflight_source_file(root, document, expected_kind="pdf", profile=PROFILE)
            self.assertEqual(report.status, "CONTAINER_PREFLIGHT_PASS")
            self.assertFalse(report.structured_data_allowed)

    def test_pdf_missing_eof_encryption_and_active_content_fail(self) -> None:
        variants = (
            (b"%PDF-1.7\nno terminator", "PDF_EOF_MISSING"),
            (b"%PDF-1.7\n/Encrypt 1 0 R\n%%EOF", "PDF_ENCRYPTED"),
            (b"%PDF-1.7\n/OpenAction 1 0 R\n%%EOF", "PDF_ACTIVE_CONTENT"),
            (b"%PDF-1.7\n/JavaScript 1 0 R\n%%EOF", "PDF_ACTIVE_CONTENT"),
        )
        for payload, expected in variants:
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                document = root / "blocked.pdf"
                document.write_bytes(payload)
                with self.assertRaises(FileSecurityError) as caught:
                    preflight_source_file(root, document, expected_kind="pdf", profile=PROFILE)
                self.assertEqual(caught.exception.code, expected)

    def test_extension_signature_mismatch_and_unknown_type_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fake = root / "fake.pdf"
            fake.write_bytes(b"not-a-pdf")
            with self.assertRaises(FileSecurityError) as mismatch:
                preflight_source_file(root, fake, expected_kind="pdf", profile=PROFILE)
            self.assertEqual(mismatch.exception.code, "TYPE_SIGNATURE_MISMATCH")
            with self.assertRaises(FileSecurityError) as unknown:
                preflight_source_file(root, fake, expected_kind="unknown", profile=PROFILE)
            self.assertEqual(unknown.exception.code, "UNSUPPORTED_EXPECTED_TYPE")


if __name__ == "__main__":
    unittest.main()
