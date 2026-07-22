import sys
import unittest
from pathlib import Path


MODULE_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = MODULE_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from project_cost_table.security import escape_spreadsheet_text  # noqa: E402


class SpreadsheetTextSafetyTests(unittest.TestCase):
    def test_formula_leading_text_is_escaped(self) -> None:
        dangerous = ("=1+1", "+1", "-1", "@name", "\tformula", "\rformula", "\nformula", "  =formula")
        for value in dangerous:
            with self.subTest(value=repr(value)):
                escaped = escape_spreadsheet_text(value)
                self.assertTrue(escaped.startswith("'"))
                self.assertEqual(escaped[1:], value)

    def test_safe_and_already_escaped_text_is_stable(self) -> None:
        for value in ("", "plain text", "123", "'=-already-safe"):
            with self.subTest(value=value):
                self.assertEqual(escape_spreadsheet_text(value), value)

    def test_numeric_values_must_use_numeric_writer(self) -> None:
        for value in (1, 1.5, None):
            with self.subTest(input_type=type(value).__name__):
                with self.assertRaises(TypeError):
                    escape_spreadsheet_text(value)


if __name__ == "__main__":
    unittest.main()
