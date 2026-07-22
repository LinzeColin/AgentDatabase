"""Strict Decimal-to-minor-unit money primitives."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, Overflow, ROUND_HALF_UP, localcontext
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

import yaml


ASCII_AMOUNT = re.compile(r"^[+-]?(?:[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+)(?:\.[0-9]+)?$")
UNSUPPORTED_SIGN_CHARS = frozenset("\u2010\u2011\u2012\u2013\u2014\u2212\ufe63\uff0b\uff0d")


class BlankPolicy(str, Enum):
    ERROR = "ERROR"
    NULL = "NULL"
    ZERO = "ZERO"


class RoundingLayer(str, Enum):
    SOURCE_PARSE = "SOURCE_PARSE"
    LINE_FORMULA = "LINE_FORMULA"
    ALLOCATION_RESIDUAL = "ALLOCATION_RESIDUAL"
    SUBTOTAL_DISPLAY = "SUBTOTAL_DISPLAY"
    TAX_CALCULATION = "TAX_CALCULATION"


class MoneyProfileError(RuntimeError):
    """Raised when a money profile is invalid or unsupported."""


class MoneyParseError(ValueError):
    """Structured fail-closed error without echoing a sensitive amount."""

    def __init__(self, code: str, message: str, value: Any = None) -> None:
        super().__init__("%s: %s" % (code, message))
        self.code = code
        self.message = message
        self.input_type = type(value).__name__

    def as_dict(self) -> Dict[str, str]:
        return {"code": self.code, "message": self.message, "input_type": self.input_type}


@dataclass(frozen=True)
class MoneyProfile:
    profile_id: str
    currency: str
    minor_unit_scale: int
    rounding: str
    decimal_context_precision: int
    max_input_scale: int
    max_abs_minor_units: int
    float_input_allowed: bool
    default_blank_policy: BlankPolicy

    @classmethod
    def from_mapping(cls, config: Mapping[str, Any]) -> "MoneyProfile":
        if config.get("schema_version") != "kmfa.project_cost.money_profile.v1":
            raise MoneyProfileError("unsupported money profile schema")
        string_fields = ("profile_id", "currency", "rounding", "default_blank_policy")
        integer_fields = (
            "minor_unit_scale",
            "decimal_context_precision",
            "max_input_scale",
            "max_abs_minor_units",
        )
        if any(not isinstance(config.get(field), str) for field in string_fields):
            raise MoneyProfileError("money profile string fields must use exact string types")
        if any(type(config.get(field)) is not int for field in integer_fields):
            raise MoneyProfileError("money profile numeric fields must use exact integer types")
        if type(config.get("float_input_allowed")) is not bool:
            raise MoneyProfileError("float_input_allowed must use an exact boolean type")
        try:
            profile = cls(
                profile_id=config["profile_id"],
                currency=config["currency"],
                minor_unit_scale=config["minor_unit_scale"],
                rounding=config["rounding"],
                decimal_context_precision=config["decimal_context_precision"],
                max_input_scale=config["max_input_scale"],
                max_abs_minor_units=config["max_abs_minor_units"],
                float_input_allowed=config["float_input_allowed"],
                default_blank_policy=BlankPolicy(config["default_blank_policy"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise MoneyProfileError("invalid money profile fields") from exc
        if not profile.profile_id or profile.currency != "CNY":
            raise MoneyProfileError("profile_id and CNY currency are required")
        if profile.minor_unit_scale != 2:
            raise MoneyProfileError("product 0.2.0 supports exactly two CNY minor-unit decimals")
        if profile.rounding != "ROUND_HALF_UP":
            raise MoneyProfileError("unsupported rounding mode")
        if profile.decimal_context_precision < 28 or profile.max_input_scale < profile.minor_unit_scale:
            raise MoneyProfileError("money precision or scale is unsafe")
        if profile.max_abs_minor_units <= 0:
            raise MoneyProfileError("max_abs_minor_units must be positive")
        if not isinstance(profile.float_input_allowed, bool) or profile.float_input_allowed:
            raise MoneyProfileError("float money input must remain disabled")
        return profile

    @classmethod
    def from_yaml(cls, path: Path) -> "MoneyProfile":
        try:
            value = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, yaml.YAMLError) as exc:
            raise MoneyProfileError("cannot load money profile") from exc
        if not isinstance(value, dict):
            raise MoneyProfileError("money profile must be a mapping")
        return cls.from_mapping(value)


@dataclass(frozen=True)
class MoneyValue:
    currency: str
    decimal_value: Decimal
    minor_units: int
    input_scale: int
    rounding_layer: RoundingLayer
    was_rounded: bool
    negative_zero_input: bool
    blank_input: bool


def _decimal_scale(value: Decimal) -> int:
    exponent = value.as_tuple().exponent
    return max(0, -exponent)


def _blank_value(profile: MoneyProfile, layer: RoundingLayer) -> MoneyValue:
    return MoneyValue(
        currency=profile.currency,
        decimal_value=Decimal("0"),
        minor_units=0,
        input_scale=0,
        rounding_layer=layer,
        was_rounded=False,
        negative_zero_input=False,
        blank_input=True,
    )


def parse_money(
    value: Any,
    *,
    profile: MoneyProfile,
    rounding_layer: RoundingLayer,
    blank_policy: Optional[BlankPolicy] = None,
) -> Optional[MoneyValue]:
    """Parse a money value exactly and round once at an explicit layer."""

    if not isinstance(rounding_layer, RoundingLayer):
        raise MoneyParseError("INVALID_ROUNDING_LAYER", "rounding layer must be registered and explicit", rounding_layer)
    policy = blank_policy or profile.default_blank_policy
    if not isinstance(policy, BlankPolicy):
        raise MoneyParseError("INVALID_BLANK_POLICY", "blank policy must be explicit", policy)
    if isinstance(value, bool) or isinstance(value, float):
        raise MoneyParseError("FLOAT_OR_BOOL_FORBIDDEN", "binary float and bool money inputs are forbidden", value)

    negative_parentheses = False
    blank_input = value is None
    if isinstance(value, str):
        text = value.strip()
        blank_input = text == ""
        if not blank_input:
            if any(character in UNSUPPORTED_SIGN_CHARS for character in text):
                raise MoneyParseError(
                    "UNSUPPORTED_UNICODE_SIGN",
                    "confusable Unicode sign characters require source-specific resolution",
                    value,
                )
            if text.startswith("(") or text.endswith(")"):
                if not (text.startswith("(") and text.endswith(")")):
                    raise MoneyParseError("INVALID_PARENTHESES", "unbalanced amount parentheses", value)
                negative_parentheses = True
                text = text[1:-1].strip()
                if text.startswith(("+", "-")):
                    raise MoneyParseError("AMBIGUOUS_SIGN", "parentheses cannot be combined with a sign", value)
            if not ASCII_AMOUNT.fullmatch(text):
                raise MoneyParseError("INVALID_AMOUNT_TEXT", "amount text does not match the strict grammar", value)
            try:
                amount = Decimal(text.replace(",", ""))
            except InvalidOperation as exc:
                raise MoneyParseError("INVALID_DECIMAL", "amount cannot be represented exactly", value) from exc
            if negative_parentheses:
                amount = -amount
    elif isinstance(value, int):
        amount = Decimal(value)
    elif isinstance(value, Decimal):
        amount = value
    elif value is not None:
        raise MoneyParseError("UNSUPPORTED_INPUT_TYPE", "money input must be str, int, Decimal, or None", value)

    if blank_input:
        if policy is BlankPolicy.ERROR:
            raise MoneyParseError("BLANK_AMOUNT", "blank amount is not allowed", value)
        if policy is BlankPolicy.NULL:
            return None
        return _blank_value(profile, rounding_layer)

    if not amount.is_finite():
        raise MoneyParseError("NON_FINITE_AMOUNT", "NaN and infinity are forbidden", value)
    input_scale = _decimal_scale(amount)
    if input_scale > profile.max_input_scale:
        raise MoneyParseError(
            "EXCESSIVE_INPUT_SCALE",
            "money input exceeds the registered source precision",
            value,
        )
    negative_zero = amount.is_zero() and (amount.is_signed() or negative_parentheses)
    quantum = Decimal(1).scaleb(-profile.minor_unit_scale)
    try:
        with localcontext() as context:
            context.prec = profile.decimal_context_precision
            context.rounding = ROUND_HALF_UP
            context.traps[InvalidOperation] = True
            context.traps[Overflow] = True
            rounded = amount.quantize(quantum)
            minor_units = int(rounded.scaleb(profile.minor_unit_scale))
    except (InvalidOperation, Overflow, ValueError) as exc:
        raise MoneyParseError("DECIMAL_CONTEXT_OVERFLOW", "amount exceeds the decimal context", value) from exc
    if abs(minor_units) > profile.max_abs_minor_units:
        raise MoneyParseError("MINOR_UNIT_OVERFLOW", "amount exceeds the registered integer ceiling", value)
    canonical = Decimal("0") if rounded.is_zero() else rounded
    return MoneyValue(
        currency=profile.currency,
        decimal_value=canonical,
        minor_units=minor_units,
        input_scale=input_scale,
        rounding_layer=rounding_layer,
        was_rounded=input_scale > profile.minor_unit_scale,
        negative_zero_input=negative_zero,
        blank_input=False,
    )


def minor_units_to_decimal(minor_units: int, *, profile: MoneyProfile) -> Decimal:
    if isinstance(minor_units, bool) or not isinstance(minor_units, int):
        raise MoneyParseError("INVALID_MINOR_UNIT_TYPE", "minor units must be an integer", minor_units)
    if abs(minor_units) > profile.max_abs_minor_units:
        raise MoneyParseError("MINOR_UNIT_OVERFLOW", "minor units exceed the registered ceiling", minor_units)
    return Decimal(minor_units).scaleb(-profile.minor_unit_scale)
