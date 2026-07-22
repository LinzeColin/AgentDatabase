import sys
import unittest
from decimal import Decimal, ROUND_DOWN, localcontext
from pathlib import Path


MODULE_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = MODULE_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from project_cost_table.money import (  # noqa: E402
    BlankPolicy,
    MoneyParseError,
    MoneyProfile,
    MoneyProfileError,
    RoundingLayer,
    minor_units_to_decimal,
    parse_money,
)


PROFILE = MoneyProfile.from_yaml(MODULE_ROOT / "config" / "money_profile.yml")


class StrictMoneyTests(unittest.TestCase):
    def parse(self, value, **kwargs):
        return parse_money(
            value,
            profile=PROFILE,
            rounding_layer=kwargs.pop("rounding_layer", RoundingLayer.SOURCE_PARSE),
            **kwargs,
        )

    def test_parentheses_grouping_and_ascii_signs(self) -> None:
        self.assertEqual(self.parse("(1,234.56)").minor_units, -123456)
        self.assertEqual(self.parse("+1,234.56").minor_units, 123456)
        self.assertEqual(self.parse("-1,234.56").minor_units, -123456)

    def test_half_cent_rounds_once_half_up(self) -> None:
        positive = self.parse("1.005")
        negative = self.parse("-1.005")
        self.assertEqual(positive.minor_units, 101)
        self.assertEqual(negative.minor_units, -101)
        self.assertTrue(positive.was_rounded)
        self.assertEqual(positive.rounding_layer, RoundingLayer.SOURCE_PARSE)

    def test_negative_zero_is_canonical_but_auditable(self) -> None:
        for text in ("-0.00", "(0.00)"):
            with self.subTest(text=text):
                result = self.parse(text)
                self.assertEqual(result.minor_units, 0)
                self.assertEqual(result.decimal_value, Decimal("0"))
                self.assertTrue(result.negative_zero_input)

    def test_blank_requires_explicit_policy(self) -> None:
        for value in (None, "", "   "):
            with self.subTest(value=value):
                with self.assertRaisesRegex(MoneyParseError, "BLANK_AMOUNT"):
                    self.parse(value)
                self.assertIsNone(self.parse(value, blank_policy=BlankPolicy.NULL))
                zero = self.parse(value, blank_policy=BlankPolicy.ZERO)
                self.assertEqual(zero.minor_units, 0)
                self.assertTrue(zero.blank_input)

    def test_dash_is_not_silently_blank_or_zero(self) -> None:
        with self.assertRaises(MoneyParseError) as caught:
            self.parse("-")
        self.assertEqual(caught.exception.code, "INVALID_AMOUNT_TEXT")

    def test_excessive_scale_fails_while_registered_scale_passes(self) -> None:
        self.assertEqual(self.parse("1.000001").minor_units, 100)
        with self.assertRaises(MoneyParseError) as caught:
            self.parse("1.0000001")
        self.assertEqual(caught.exception.code, "EXCESSIVE_INPUT_SCALE")

    def test_unicode_signs_fail_closed(self) -> None:
        for sign in ("\u2212", "\uff0d", "\uff0b", "\u2014"):
            with self.subTest(sign=ord(sign)):
                with self.assertRaises(MoneyParseError) as caught:
                    self.parse(sign + "1.00")
                self.assertEqual(caught.exception.code, "UNSUPPORTED_UNICODE_SIGN")

    def test_invalid_nonempty_text_never_becomes_zero(self) -> None:
        invalid = ("12x.34", "1,23.45", "1e3", "$1.00", "--1", "1.2.3", "(+1.00)")
        for text in invalid:
            with self.subTest(text=text):
                with self.assertRaises(MoneyParseError):
                    self.parse(text, blank_policy=BlankPolicy.ZERO)

    def test_float_bool_nan_and_infinity_are_forbidden(self) -> None:
        for value in (1.1, True, False, Decimal("NaN"), Decimal("Infinity")):
            with self.subTest(input_type=type(value).__name__):
                with self.assertRaises(MoneyParseError):
                    self.parse(value)

    def test_signed_64_bit_minor_ceiling(self) -> None:
        boundary = self.parse("92233720368547758.07")
        self.assertEqual(boundary.minor_units, 9223372036854775807)
        with self.assertRaises(MoneyParseError) as caught:
            self.parse("92233720368547758.075")
        self.assertEqual(caught.exception.code, "MINOR_UNIT_OVERFLOW")

    def test_integer_and_decimal_inputs_remain_exact(self) -> None:
        self.assertEqual(self.parse(12).minor_units, 1200)
        self.assertEqual(self.parse(Decimal("12.345")).minor_units, 1235)

    def test_minor_unit_round_trip_and_type_gate(self) -> None:
        self.assertEqual(minor_units_to_decimal(-12345, profile=PROFILE), Decimal("-123.45"))
        with self.assertRaises(MoneyParseError):
            minor_units_to_decimal(1.0, profile=PROFILE)

    def test_minor_unit_round_trip_property_sample(self) -> None:
        for minor_units in range(-10000, 10001, 137):
            with self.subTest(minor_units=minor_units):
                decimal_value = minor_units_to_decimal(minor_units, profile=PROFILE)
                reparsed = self.parse(decimal_value)
                self.assertEqual(reparsed.minor_units, minor_units)

    def test_ambient_decimal_context_cannot_change_result(self) -> None:
        with localcontext() as ambient:
            ambient.prec = 3
            ambient.rounding = ROUND_DOWN
            result = self.parse("123456789.005")
        self.assertEqual(result.minor_units, 12345678901)

    def test_rounding_layer_must_be_explicit_enum(self) -> None:
        with self.assertRaises(MoneyParseError) as caught:
            parse_money("1.00", profile=PROFILE, rounding_layer="SOURCE_PARSE")
        self.assertEqual(caught.exception.code, "INVALID_ROUNDING_LAYER")

    def test_profile_rejects_float_enablement_unknown_rounding_and_coercion(self) -> None:
        base = {
            "schema_version": "kmfa.project_cost.money_profile.v1",
            "profile_id": "TEST",
            "currency": "CNY",
            "minor_unit_scale": 2,
            "rounding": "ROUND_HALF_UP",
            "decimal_context_precision": 38,
            "max_input_scale": 6,
            "max_abs_minor_units": 100,
            "float_input_allowed": False,
            "default_blank_policy": "ERROR",
        }
        invalid_float = dict(base, float_input_allowed=True)
        invalid_rounding = dict(base, rounding="ROUND_HALF_EVEN")
        invalid_bool_scale = dict(base, max_input_scale=True)
        invalid_float_precision = dict(base, decimal_context_precision=38.0)
        with self.assertRaises(MoneyProfileError):
            MoneyProfile.from_mapping(invalid_float)
        with self.assertRaises(MoneyProfileError):
            MoneyProfile.from_mapping(invalid_rounding)
        with self.assertRaises(MoneyProfileError):
            MoneyProfile.from_mapping(invalid_bool_scale)
        with self.assertRaises(MoneyProfileError):
            MoneyProfile.from_mapping(invalid_float_precision)

    def test_error_does_not_echo_sensitive_amount_text(self) -> None:
        secret = "987654x.32"
        with self.assertRaises(MoneyParseError) as caught:
            self.parse(secret)
        self.assertNotIn(secret, str(caught.exception))
        self.assertEqual(caught.exception.as_dict()["input_type"], "str")


if __name__ == "__main__":
    unittest.main()
