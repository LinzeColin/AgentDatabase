"""Locked, value-only Kingdee XLSX reader with source conservation controls."""

from __future__ import annotations

import hashlib
import json
import os
import posixpath
import re
import stat
import unicodedata
import zipfile
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path, PurePosixPath
from typing import Any, BinaryIO, Dict, Iterable, Mapping, Optional, Sequence, Tuple
from xml.etree import ElementTree as ET

from ..config_io import GovernedConfigError, load_governed_yaml_mapping
from ..manifest import SourceSelection
from ..money import BlankPolicy, MoneyParseError, MoneyProfile, RoundingLayer, parse_money
from ..paths import PathSafetyError, resolve_input_file
from ..security import FileSecurityError, SecurityProfile, preflight_source_file


KINGDEE_READER_ID = "kingdee_ledger_v2"
KINGDEE_READER_VERSION = "2.0.0"
KINGDEE_PROFILE_BYTES_MAX = 1024 * 1024
EVIDENCE_REF_RE = re.compile(r"^evidence://sha256/[0-9a-f]{64}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SOURCE_ID_RE = re.compile(r"^src_[0-9a-f]{32}$")
SOURCE_RECORD_REF_RE = re.compile(r"^rec_source_[0-9a-f]{32}$")
LEDGER_LINE_KEY_RE = re.compile(r"^ledger_line_[0-9a-f]{32}$")
SHEET_REF_RE = re.compile(r"^sheet_[0-9a-f]{16}$")
CELL_REF_RE = re.compile(r"^([A-Z]{1,4})([1-9][0-9]*)$")
DATE_FIELDS = ("document_date", "business_date", "posting_date")
AMOUNT_FIELDS = ("debit", "credit", "balance")
CANONICAL_FIELDS = (
    "legal_entity_source_key",
    "project_source_key",
    "wbs_source_key",
    "contract_source_key",
    "account_code",
    "voucher_id",
    "voucher_line_id",
    "document_date",
    "business_date",
    "posting_date",
    "debit",
    "credit",
    "balance",
    "currency",
    "source_status",
    "source_row_kind",
)
ALLOWED_DATE_MODES = frozenset({"ISO_TEXT", "ISO_OR_EXCEL_SERIAL"})


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _strict_text(value: Any, field: str, *, optional: bool = False) -> Optional[str]:
    if value is None and optional:
        return None
    if not isinstance(value, str) or not value or value != value.strip() or unicodedata.normalize("NFC", value) != value:
        raise KingdeeReaderError("READER_PROFILE_SCHEMA", "%s must be nonempty normalized text" % field)
    return value


def _string_tuple(value: Any, field: str, *, allow_empty: bool = True) -> Tuple[str, ...]:
    if not isinstance(value, (list, tuple)) or any(not isinstance(item, str) for item in value):
        raise KingdeeReaderError("READER_PROFILE_SCHEMA", "%s must be a string list" % field)
    result = tuple(value)
    if (not allow_empty and not result) or len(result) != len(set(result)):
        raise KingdeeReaderError("READER_PROFILE_SCHEMA", "%s must be nonempty and unique" % field)
    for item in result:
        _strict_text(item, field)
    return result


class KingdeeReaderError(ValueError):
    """Structured reader failure that never echoes cell content or source paths."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        row_number: Optional[int] = None,
        column_id: Optional[str] = None,
        partial_control: Optional["KingdeeReaderControl"] = None,
    ) -> None:
        super().__init__("%s: %s" % (code, message))
        self.code = code
        self.message = message
        self.row_number = row_number
        self.column_id = column_id
        self.partial_control = partial_control

    def as_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {"code": self.code, "message": self.message}
        if self.row_number is not None:
            result["row_number"] = self.row_number
        if self.column_id is not None:
            result["column_id"] = self.column_id
        if self.partial_control is not None:
            result["partial_control"] = {
                "physical_data_row_count": self.partial_control.physical_data_row_count,
                "emitted_record_count": self.partial_control.emitted_record_count,
                "empty_row_count": self.partial_control.empty_row_count,
                "parse_failure_count": self.partial_control.parse_failure_count,
                "row_conservation_delta": self.partial_control.row_conservation_delta,
            }
        return result


@dataclass(frozen=True)
class KingdeeReaderProfile:
    profile_id: str
    status: str
    reader_id: str
    reader_version: str
    schema_id: str
    sheet_name: str
    header_row: int
    first_data_row: int
    max_data_rows: int
    expected_headers: Tuple[str, ...]
    column_bindings: Tuple[Tuple[str, str], ...]
    date_modes: Tuple[Tuple[str, str], ...]
    evidence_refs: Tuple[str, ...]
    content_sha256: str

    @property
    def schema_fingerprint(self) -> str:
        return _digest(
            {
                "schema_id": self.schema_id,
                "sheet_name": self.sheet_name,
                "header_row": self.header_row,
                "first_data_row": self.first_data_row,
                "expected_headers": list(self.expected_headers),
                "column_bindings": dict(self.column_bindings),
                "date_modes": dict(self.date_modes),
            }
        )

    def binding_map(self) -> Dict[str, str]:
        return dict(self.column_bindings)

    def date_mode_map(self) -> Dict[str, str]:
        return dict(self.date_modes)

    def validate(self, *, require_active: bool = False) -> None:
        for field in ("profile_id", "reader_id", "reader_version", "schema_id", "sheet_name"):
            _strict_text(getattr(self, field), field)
        if self.reader_id != KINGDEE_READER_ID or self.reader_version != KINGDEE_READER_VERSION:
            raise KingdeeReaderError("READER_VERSION_UNSUPPORTED", "reader identity/version is not the locked R5 implementation")
        if self.status not in {"ACTIVE", "TEMPLATE_NOT_ACTIVE"}:
            raise KingdeeReaderError("READER_PROFILE_STATUS", "reader profile status is not registered")
        if any(type(value) is not int for value in (self.header_row, self.first_data_row, self.max_data_rows)):
            raise KingdeeReaderError("READER_PROFILE_SCHEMA", "row controls require exact integers")
        if self.header_row < 1 or self.first_data_row <= self.header_row or not 1 <= self.max_data_rows <= 5_000_000:
            raise KingdeeReaderError("READER_PROFILE_SCHEMA", "row controls are inconsistent or exceed the locked ceiling")
        headers = _string_tuple(self.expected_headers, "expected_headers", allow_empty=False)
        if headers != self.expected_headers:
            raise KingdeeReaderError("READER_PROFILE_SCHEMA", "expected headers must use an immutable tuple")
        bindings = dict(self.column_bindings)
        if len(bindings) != len(self.column_bindings) or set(bindings) != set(CANONICAL_FIELDS):
            raise KingdeeReaderError("READER_PROFILE_SCHEMA", "column bindings must cover every canonical ledger field once")
        if any(not isinstance(key, str) or not isinstance(value, str) for key, value in self.column_bindings):
            raise KingdeeReaderError("READER_PROFILE_SCHEMA", "column bindings must use exact text values")
        if len(set(bindings.values())) != len(bindings) or any(value not in headers for value in bindings.values()):
            raise KingdeeReaderError("READER_PROFILE_SCHEMA", "bound headers must be unique members of the locked header schema")
        date_modes = dict(self.date_modes)
        if len(date_modes) != len(self.date_modes) or set(date_modes) != set(DATE_FIELDS):
            raise KingdeeReaderError("READER_PROFILE_SCHEMA", "date modes must cover all ledger date fields")
        if any(mode not in ALLOWED_DATE_MODES for mode in date_modes.values()):
            raise KingdeeReaderError("READER_PROFILE_SCHEMA", "date mode is not registered")
        refs = _string_tuple(self.evidence_refs, "evidence_refs")
        if refs != self.evidence_refs or any(not EVIDENCE_REF_RE.fullmatch(item) for item in refs):
            raise KingdeeReaderError("READER_PROFILE_EVIDENCE", "reader evidence references must be hash-bound and opaque")
        if not SHA256_RE.fullmatch(self.content_sha256):
            raise KingdeeReaderError("READER_PROFILE_HASH", "reader profile hash is invalid")
        if require_active and (self.status != "ACTIVE" or not self.evidence_refs):
            raise KingdeeReaderError("READER_PROFILE_NOT_ACTIVE", "a hash-bound ACTIVE reader profile is required")

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any], *, content_sha256: Optional[str] = None) -> "KingdeeReaderProfile":
        expected = {
            "schema_version",
            "profile_id",
            "status",
            "reader_id",
            "reader_version",
            "schema_id",
            "sheet_name",
            "header_row",
            "first_data_row",
            "max_data_rows",
            "expected_headers",
            "column_bindings",
            "date_modes",
            "evidence_refs",
        }
        if not isinstance(raw, Mapping) or set(raw) != expected or raw.get("schema_version") != "kmfa.project_cost.kingdee_reader_profile.v1":
            raise KingdeeReaderError("READER_PROFILE_SCHEMA", "reader profile fields differ from v1")
        bindings = raw.get("column_bindings")
        date_modes = raw.get("date_modes")
        if not isinstance(bindings, Mapping) or not isinstance(date_modes, Mapping):
            raise KingdeeReaderError("READER_PROFILE_SCHEMA", "column bindings and date modes must be mappings")
        if (
            set(bindings) != set(CANONICAL_FIELDS)
            or any(not isinstance(key, str) or not isinstance(value, str) for key, value in bindings.items())
            or set(date_modes) != set(DATE_FIELDS)
            or any(not isinstance(key, str) or not isinstance(value, str) for key, value in date_modes.items())
        ):
            raise KingdeeReaderError("READER_PROFILE_SCHEMA", "reader bindings differ from the canonical field contract")
        profile = cls(
            profile_id=_strict_text(raw.get("profile_id"), "profile_id") or "",
            status=_strict_text(raw.get("status"), "status") or "",
            reader_id=_strict_text(raw.get("reader_id"), "reader_id") or "",
            reader_version=_strict_text(raw.get("reader_version"), "reader_version") or "",
            schema_id=_strict_text(raw.get("schema_id"), "schema_id") or "",
            sheet_name=_strict_text(raw.get("sheet_name"), "sheet_name") or "",
            header_row=raw.get("header_row"),
            first_data_row=raw.get("first_data_row"),
            max_data_rows=raw.get("max_data_rows"),
            expected_headers=_string_tuple(raw.get("expected_headers"), "expected_headers", allow_empty=False),
            column_bindings=tuple(sorted((key, value) for key, value in bindings.items())),
            date_modes=tuple(sorted((key, value) for key, value in date_modes.items())),
            evidence_refs=_string_tuple(raw.get("evidence_refs"), "evidence_refs"),
            content_sha256=content_sha256 or _digest(raw),
        )
        profile.validate()
        return profile

    @classmethod
    def from_yaml(cls, path: Path) -> "KingdeeReaderProfile":
        try:
            raw, file_hash = load_governed_yaml_mapping(path, max_bytes=KINGDEE_PROFILE_BYTES_MAX)
        except GovernedConfigError as exc:
            raise KingdeeReaderError(exc.code, exc.message) from exc
        return cls.from_mapping(raw, content_sha256=file_hash)


@dataclass(frozen=True)
class KingdeeLedgerRecord:
    source_record_ref: str
    source_business_key_hash: str
    normalized_business_digest: str
    source_id: str
    source_sha256: str
    slot_id: str
    reader_id: str
    reader_version: str
    schema_id: str
    schema_fingerprint: str
    sheet_name: str
    sheet_ref: str
    row_number: int
    legal_entity_source_key: Optional[str]
    project_source_key: Optional[str]
    wbs_source_key: Optional[str]
    contract_source_key: Optional[str]
    account_code: Optional[str]
    voucher_id: Optional[str]
    voucher_line_id: Optional[str]
    document_date: Optional[str]
    business_date: Optional[str]
    posting_date: Optional[str]
    debit_minor: Optional[int]
    credit_minor: Optional[int]
    balance_minor: Optional[int]
    currency: Optional[str]
    source_status: Optional[str]
    source_row_kind: Optional[str]
    container_source_id: Optional[str] = None
    container_sha256: Optional[str] = None
    archive_member_ref: Optional[str] = None

    def _business_payload(self) -> Dict[str, Any]:
        return {
            "legal_entity_source_key": self.legal_entity_source_key,
            "project_source_key": self.project_source_key,
            "wbs_source_key": self.wbs_source_key,
            "contract_source_key": self.contract_source_key,
            "account_code": self.account_code,
            "voucher_id": self.voucher_id,
            "voucher_line_id": self.voucher_line_id,
            "currency": self.currency,
            "source_status": self.source_status,
            "source_row_kind": self.source_row_kind,
            "document_date": self.document_date,
            "business_date": self.business_date,
            "posting_date": self.posting_date,
            "debit_minor": self.debit_minor,
            "credit_minor": self.credit_minor,
            "balance_minor": self.balance_minor,
        }

    def validate(self) -> None:
        if (
            not SOURCE_ID_RE.fullmatch(self.source_id)
            or not SHA256_RE.fullmatch(self.source_sha256)
            or not SHA256_RE.fullmatch(self.schema_fingerprint)
            or not SHEET_REF_RE.fullmatch(self.sheet_ref)
            or not SOURCE_RECORD_REF_RE.fullmatch(self.source_record_ref)
            or not LEDGER_LINE_KEY_RE.fullmatch(self.source_business_key_hash)
            or not SHA256_RE.fullmatch(self.normalized_business_digest)
        ):
            raise KingdeeReaderError("LEDGER_RECORD_LINEAGE", "ledger record lineage identifiers are invalid")
        if self.container_source_id is not None and not SOURCE_ID_RE.fullmatch(self.container_source_id):
            raise KingdeeReaderError("LEDGER_RECORD_LINEAGE", "container source reference is invalid")
        if self.container_sha256 is not None and not SHA256_RE.fullmatch(self.container_sha256):
            raise KingdeeReaderError("LEDGER_RECORD_LINEAGE", "container digest is invalid")
        if self.archive_member_ref is not None and not re.fullmatch(r"^member_[0-9a-f]{32}$", self.archive_member_ref):
            raise KingdeeReaderError("LEDGER_RECORD_LINEAGE", "archive member reference is invalid")
        container_fields = (self.container_source_id, self.container_sha256, self.archive_member_ref)
        if any(item is None for item in container_fields) and any(item is not None for item in container_fields):
            raise KingdeeReaderError("LEDGER_RECORD_LINEAGE", "container lineage fields must be all null or all populated")
        if (
            self.slot_id != "general_ledger"
            or self.reader_id != KINGDEE_READER_ID
            or self.reader_version != KINGDEE_READER_VERSION
            or type(self.row_number) is not int
            or self.row_number < 1
        ):
            raise KingdeeReaderError("LEDGER_RECORD_SCHEMA", "ledger record reader/schema fields are invalid")
        for value in (self.debit_minor, self.credit_minor, self.balance_minor):
            if value is not None and (isinstance(value, bool) or not isinstance(value, int)):
                raise KingdeeReaderError("LEDGER_RECORD_AMOUNT", "ledger record amounts must be integer minor units or null")
        for field in DATE_FIELDS:
            value = getattr(self, field)
            if value is not None:
                try:
                    date.fromisoformat(value)
                except (TypeError, ValueError) as exc:
                    raise KingdeeReaderError("LEDGER_RECORD_DATE", "ledger record date is not canonical ISO") from exc
        business_digest = _digest(self._business_payload())
        stable_key = _digest(
            {
                "source_id": self.source_id,
                "legal_entity_source_key": self.legal_entity_source_key,
                "voucher_id": self.voucher_id,
                "voucher_line_id": self.voucher_line_id,
                "account_code": self.account_code,
                "posting_date": self.posting_date,
            }
        )
        expected_record_ref = "rec_source_" + _digest(
            {
                "source_id": self.source_id,
                "source_sha256": self.source_sha256,
                "sheet_ref": self.sheet_ref,
                "row_number": self.row_number,
                "business_digest": business_digest,
            }
        )[:32]
        if (
            business_digest != self.normalized_business_digest
            or self.source_business_key_hash != "ledger_line_" + stable_key[:32]
            or self.source_record_ref != expected_record_ref
        ):
            raise KingdeeReaderError("LEDGER_RECORD_TAMPERED", "ledger record content no longer matches its immutable lineage digests")

    def as_private_dict(self) -> Dict[str, Any]:
        self.validate()
        return {
            "schema_version": "kmfa.project_cost.kingdee_ledger_record.v1",
            "source_record_ref": self.source_record_ref,
            "source_business_key_hash": self.source_business_key_hash,
            "normalized_business_digest": self.normalized_business_digest,
            "source_id": self.source_id,
            "source_sha256": self.source_sha256,
            "slot_id": self.slot_id,
            "reader_id": self.reader_id,
            "reader_version": self.reader_version,
            "schema_id": self.schema_id,
            "schema_fingerprint": self.schema_fingerprint,
            "sheet_name": self.sheet_name,
            "sheet_ref": self.sheet_ref,
            "row_number": self.row_number,
            "legal_entity_source_key": self.legal_entity_source_key,
            "project_source_key": self.project_source_key,
            "wbs_source_key": self.wbs_source_key,
            "contract_source_key": self.contract_source_key,
            "account_code": self.account_code,
            "voucher_id": self.voucher_id,
            "voucher_line_id": self.voucher_line_id,
            "document_date": self.document_date,
            "business_date": self.business_date,
            "posting_date": self.posting_date,
            "debit_minor": self.debit_minor,
            "credit_minor": self.credit_minor,
            "balance_minor": self.balance_minor,
            "currency": self.currency,
            "source_status": self.source_status,
            "source_row_kind": self.source_row_kind,
            "container_source_id": self.container_source_id,
            "container_sha256": self.container_sha256,
            "archive_member_ref": self.archive_member_ref,
        }


@dataclass(frozen=True)
class AmountColumnControl:
    positive_count: int
    negative_count: int
    zero_count: int
    null_count: int
    total_minor: int


@dataclass(frozen=True)
class KingdeeReaderControl:
    physical_data_row_count: int
    emitted_record_count: int
    empty_row_count: int
    parse_failure_count: int
    exclusion_counts: Tuple[Tuple[str, int], ...]
    debit: AmountColumnControl
    credit: AmountColumnControl
    balance: AmountColumnControl
    row_conservation_delta: int

    def validate(self) -> None:
        if self.row_conservation_delta != 0:
            raise KingdeeReaderError("READER_ROW_CONSERVATION", "reader row conservation must equal zero")
        if self.physical_data_row_count != self.emitted_record_count + self.empty_row_count + self.parse_failure_count:
            raise KingdeeReaderError("READER_ROW_CONSERVATION", "reader row counts do not conserve")


@dataclass(frozen=True)
class KingdeeReaderResult:
    records: Tuple[KingdeeLedgerRecord, ...]
    control: KingdeeReaderControl
    source_sha256: str
    reader_profile_sha256: str
    schema_fingerprint: str
    business_fingerprint: str


@dataclass(frozen=True)
class _CellValue:
    text: Optional[str]
    kind: str


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _read_xml(archive: zipfile.ZipFile, name: str, security_profile: SecurityProfile) -> ET.Element:
    try:
        info = archive.getinfo(name)
    except KeyError as exc:
        raise KingdeeReaderError("XLSX_REQUIRED_PART_MISSING", "locked workbook part is missing") from exc
    if info.file_size > security_profile.xml_single_part_bytes_max:
        raise KingdeeReaderError("XLSX_XML_SIZE_LIMIT", "workbook XML part exceeds the security ceiling")
    try:
        payload = archive.read(info)
    except (OSError, EOFError, RuntimeError, zipfile.BadZipFile) as exc:
        raise KingdeeReaderError("XLSX_PART_READ", "workbook XML part cannot be read") from exc
    upper = payload.upper()
    if b"<!DOCTYPE" in upper or b"<!ENTITY" in upper:
        raise KingdeeReaderError("XLSX_XML_ENTITY_FORBIDDEN", "DTD/entity content is forbidden")
    try:
        return ET.fromstring(payload)
    except ET.ParseError as exc:
        raise KingdeeReaderError("XLSX_XML_INVALID", "workbook XML is malformed") from exc


def _safe_sheet_target(target: str) -> str:
    if not target or "\\" in target or "\x00" in target or "?" in target or "#" in target:
        raise KingdeeReaderError("XLSX_SHEET_TARGET_UNSAFE", "worksheet relationship target is unsafe")
    normalized = posixpath.normpath(target.lstrip("/")) if target.startswith("/") else posixpath.normpath(posixpath.join("xl", target))
    pure = PurePosixPath(normalized)
    if normalized.startswith("../") or any(part in {"", ".", ".."} for part in pure.parts) or not normalized.startswith("xl/"):
        raise KingdeeReaderError("XLSX_SHEET_TARGET_UNSAFE", "worksheet relationship escapes the workbook root")
    return normalized


def _column_index(reference: str) -> Tuple[int, int]:
    match = CELL_REF_RE.fullmatch(reference)
    if match is None:
        raise KingdeeReaderError("XLSX_CELL_REFERENCE", "cell reference is not canonical")
    letters, row_text = match.groups()
    column = 0
    for character in letters:
        column = column * 26 + ord(character) - 64
    return column, int(row_text)


def _cell_value(cell: ET.Element, shared_strings: Sequence[str]) -> _CellValue:
    if any(_local_name(node.tag) == "f" for node in cell):
        raise KingdeeReaderError("XLSX_FORMULA_CELL", "formula cell reached the value-only reader")
    cell_type = cell.attrib.get("t")
    value_nodes = [node for node in cell if _local_name(node.tag) == "v"]
    if cell_type == "inlineStr":
        return _CellValue("".join(node.text or "" for node in cell.iter() if _local_name(node.tag) == "t"), "text")
    raw = value_nodes[0].text if value_nodes else None
    if cell_type == "s":
        try:
            index = int(raw or "")
            return _CellValue(shared_strings[index], "text")
        except (ValueError, IndexError) as exc:
            raise KingdeeReaderError("XLSX_SHARED_STRING", "shared-string reference is invalid") from exc
    if cell_type in (None, "n"):
        return _CellValue(raw, "number" if raw is not None else "blank")
    if cell_type in {"str", "d"}:
        return _CellValue(raw, "date" if cell_type == "d" else "text")
    if cell_type == "b":
        if raw not in {"0", "1"}:
            raise KingdeeReaderError("XLSX_BOOLEAN_CELL", "boolean cell is invalid")
        return _CellValue(raw, "boolean")
    if cell_type == "e":
        raise KingdeeReaderError("XLSX_ERROR_CELL", "error-valued cells are not valid ledger evidence")
    raise KingdeeReaderError("XLSX_CELL_TYPE", "cell type is not supported by the locked reader")


def _shared_strings(archive: zipfile.ZipFile, security_profile: SecurityProfile) -> Tuple[str, ...]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return ()
    root = _read_xml(archive, "xl/sharedStrings.xml", security_profile)
    values = []
    for node in root:
        if _local_name(node.tag) == "si":
            values.append("".join(item.text or "" for item in node.iter() if _local_name(item.tag) == "t"))
    return tuple(values)


def _workbook_sheet(
    archive: zipfile.ZipFile,
    *,
    profile: KingdeeReaderProfile,
    security_profile: SecurityProfile,
) -> Tuple[str, bool]:
    workbook = _read_xml(archive, "xl/workbook.xml", security_profile)
    date_1904 = False
    sheet_relationship_ids = []
    for node in workbook.iter():
        local = _local_name(node.tag)
        if local == "workbookPr":
            raw_date_system = node.attrib.get("date1904", "0")
            if raw_date_system not in {"0", "false", "FALSE", "1", "true", "TRUE"}:
                raise KingdeeReaderError("XLSX_DATE_SYSTEM", "workbook date system flag is invalid")
            date_1904 = raw_date_system in {"1", "true", "TRUE"}
        elif local == "sheet" and node.attrib.get("name") == profile.sheet_name:
            relationship_id = next((value for key, value in node.attrib.items() if key.endswith("}id")), None)
            if relationship_id is None:
                raise KingdeeReaderError("XLSX_SHEET_RELATIONSHIP", "selected sheet lacks a relationship ID")
            sheet_relationship_ids.append(relationship_id)
    if len(sheet_relationship_ids) != 1:
        raise KingdeeReaderError("XLSX_SHEET_SELECTION", "selected sheet must exist exactly once")
    relations = _read_xml(archive, "xl/_rels/workbook.xml.rels", security_profile)
    targets = []
    for node in relations.iter():
        if _local_name(node.tag) != "Relationship" or node.attrib.get("Id") != sheet_relationship_ids[0]:
            continue
        if node.attrib.get("TargetMode", "").casefold() == "external":
            raise KingdeeReaderError("XLSX_EXTERNAL_SHEET", "external worksheet relationships are forbidden")
        targets.append(_safe_sheet_target(node.attrib.get("Target", "")))
    if len(targets) != 1:
        raise KingdeeReaderError("XLSX_SHEET_RELATIONSHIP", "selected sheet relationship must resolve exactly once")
    return targets[0], date_1904


def _optional_cell_text(value: _CellValue) -> Optional[str]:
    if value.text is None or value.text.strip() == "":
        return None
    return value.text


def _excel_serial_date(raw: str, *, date_1904: bool) -> date:
    try:
        value = Decimal(raw)
    except InvalidOperation as exc:
        raise KingdeeReaderError("LEDGER_DATE_PARSE", "numeric date cannot be represented exactly") from exc
    if not value.is_finite() or value != value.to_integral_value():
        raise KingdeeReaderError("LEDGER_DATE_PARSE", "ledger date serial must be a finite whole day")
    serial = int(value)
    if date_1904:
        if serial < 0:
            raise KingdeeReaderError("LEDGER_DATE_PARSE", "1904-system date serial cannot be negative")
        return date(1904, 1, 1) + timedelta(days=serial)
    if serial <= 0 or serial == 60:
        raise KingdeeReaderError("LEDGER_DATE_PARSE", "invalid or fictitious 1900-system date serial")
    return date(1899, 12, 31) + timedelta(days=serial - (1 if serial > 60 else 0))


def _parse_date_cell(value: _CellValue, *, mode: str, date_1904: bool) -> Optional[str]:
    raw = _optional_cell_text(value)
    if raw is None:
        return None
    if value.kind == "number":
        if mode != "ISO_OR_EXCEL_SERIAL":
            raise KingdeeReaderError("LEDGER_DATE_MODE", "numeric date is forbidden by the locked schema")
        return _excel_serial_date(raw, date_1904=date_1904).isoformat()
    try:
        normalized = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
        parsed = date.fromisoformat(normalized) if len(normalized) == 10 else datetime.fromisoformat(normalized).date()
    except ValueError as exc:
        raise KingdeeReaderError("LEDGER_DATE_PARSE", "ledger date must be governed ISO text or an enabled Excel serial") from exc
    return parsed.isoformat()


def _parse_amount_cell(value: _CellValue, *, money_profile: MoneyProfile) -> Optional[int]:
    raw = _optional_cell_text(value)
    try:
        parsed = parse_money(
            raw,
            profile=money_profile,
            rounding_layer=RoundingLayer.SOURCE_PARSE,
            blank_policy=BlankPolicy.NULL,
        )
    except MoneyParseError as exc:
        raise KingdeeReaderError("LEDGER_AMOUNT_" + exc.code, "ledger amount failed the strict money parser") from exc
    return None if parsed is None else parsed.minor_units


def _amount_control(values: Iterable[Optional[int]]) -> AmountColumnControl:
    positive = negative = zero = null = total = 0
    for value in values:
        if value is None:
            null += 1
        elif value > 0:
            positive += 1
            total += value
        elif value < 0:
            negative += 1
            total += value
        else:
            zero += 1
    return AmountColumnControl(positive, negative, zero, null, total)


def _ledger_record(
    *,
    row_number: int,
    cells: Mapping[str, _CellValue],
    selection: SourceSelection,
    profile: KingdeeReaderProfile,
    money_profile: MoneyProfile,
    date_1904: bool,
    sheet_ref: str,
) -> KingdeeLedgerRecord:
    date_modes = profile.date_mode_map()
    text_fields = {
        field: _optional_cell_text(cells[field])
        for field in CANONICAL_FIELDS
        if field not in DATE_FIELDS and field not in AMOUNT_FIELDS
    }
    dates = {}
    for field in DATE_FIELDS:
        try:
            dates[field] = _parse_date_cell(cells[field], mode=date_modes[field], date_1904=date_1904)
        except KingdeeReaderError as exc:
            raise KingdeeReaderError(exc.code, exc.message, column_id=field) from exc
    amounts = {}
    for field in AMOUNT_FIELDS:
        try:
            amounts[field] = _parse_amount_cell(cells[field], money_profile=money_profile)
        except KingdeeReaderError as exc:
            raise KingdeeReaderError(exc.code, exc.message, column_id=field) from exc
    business = {
        **text_fields,
        **dates,
        "debit_minor": amounts["debit"],
        "credit_minor": amounts["credit"],
        "balance_minor": amounts["balance"],
    }
    business_digest = _digest(business)
    stable_key = _digest(
        {
            "source_id": selection.source_id,
            "legal_entity_source_key": text_fields["legal_entity_source_key"],
            "voucher_id": text_fields["voucher_id"],
            "voucher_line_id": text_fields["voucher_line_id"],
            "account_code": text_fields["account_code"],
            "posting_date": dates["posting_date"],
        }
    )
    record_ref = "rec_source_" + _digest(
        {
            "source_id": selection.source_id,
            "source_sha256": selection.sha256,
            "sheet_ref": sheet_ref,
            "row_number": row_number,
            "business_digest": business_digest,
        }
    )[:32]
    record = KingdeeLedgerRecord(
        source_record_ref=record_ref,
        source_business_key_hash="ledger_line_" + stable_key[:32],
        normalized_business_digest=business_digest,
        source_id=selection.source_id,
        source_sha256=selection.sha256,
        slot_id=selection.slot_id,
        reader_id=selection.reader,
        reader_version=selection.reader_version,
        schema_id=selection.schema_id,
        schema_fingerprint=selection.schema_fingerprint,
        sheet_name=profile.sheet_name,
        sheet_ref=sheet_ref,
        row_number=row_number,
        legal_entity_source_key=text_fields["legal_entity_source_key"],
        project_source_key=text_fields["project_source_key"],
        wbs_source_key=text_fields["wbs_source_key"],
        contract_source_key=text_fields["contract_source_key"],
        account_code=text_fields["account_code"],
        voucher_id=text_fields["voucher_id"],
        voucher_line_id=text_fields["voucher_line_id"],
        document_date=dates["document_date"],
        business_date=dates["business_date"],
        posting_date=dates["posting_date"],
        debit_minor=amounts["debit"],
        credit_minor=amounts["credit"],
        balance_minor=amounts["balance"],
        currency=text_fields["currency"],
        source_status=text_fields["source_status"],
        source_row_kind=text_fields["source_row_kind"],
    )
    record.validate()
    return record


def _parse_xlsx(
    source: BinaryIO,
    *,
    selection: SourceSelection,
    profile: KingdeeReaderProfile,
    security_profile: SecurityProfile,
    money_profile: MoneyProfile,
) -> Tuple[Tuple[KingdeeLedgerRecord, ...], KingdeeReaderControl]:
    try:
        archive_context = zipfile.ZipFile(source)
    except zipfile.BadZipFile as exc:
        raise KingdeeReaderError("XLSX_ARCHIVE_INVALID", "preflighted XLSX cannot be reopened") from exc
    with archive_context as archive:
        sheet_part, date_1904 = _workbook_sheet(archive, profile=profile, security_profile=security_profile)
        sheet_ref = "sheet_" + hashlib.sha256(sheet_part.encode("utf-8")).hexdigest()[:16]
        worksheet = _read_xml(archive, sheet_part, security_profile)
        shared = _shared_strings(archive, security_profile)
        rows: Dict[int, Dict[int, _CellValue]] = {}
        for row in worksheet.iter():
            if _local_name(row.tag) != "row":
                continue
            raw_row_number = row.attrib.get("r")
            try:
                row_number = int(raw_row_number or "")
            except ValueError as exc:
                raise KingdeeReaderError("XLSX_ROW_REFERENCE", "row reference is missing or invalid") from exc
            if row_number in rows:
                raise KingdeeReaderError("XLSX_DUPLICATE_ROW", "worksheet contains a duplicate row reference")
            values: Dict[int, _CellValue] = {}
            for cell in row:
                if _local_name(cell.tag) != "c":
                    continue
                column, cell_row = _column_index(cell.attrib.get("r", ""))
                if cell_row != row_number or column in values:
                    raise KingdeeReaderError("XLSX_CELL_REFERENCE", "cell reference conflicts with its row")
                values[column] = _cell_value(cell, shared)
            rows[row_number] = values
        header_cells = rows.get(profile.header_row)
        if header_cells is None:
            raise KingdeeReaderError("LEDGER_HEADER_MISSING", "locked header row is missing")
        header_by_column = {
            column: value.text
            for column, value in sorted(header_cells.items())
            if value.text is not None and value.text != ""
        }
        actual_headers = tuple(header_by_column.values())
        if len(actual_headers) != len(set(actual_headers)):
            raise KingdeeReaderError("LEDGER_DUPLICATE_HEADER", "ledger header labels must be unique")
        if actual_headers != profile.expected_headers:
            raise KingdeeReaderError("LEDGER_SCHEMA_DRIFT", "ledger header sequence differs from the locked reader profile")
        column_by_header = {header: column for column, header in header_by_column.items()}
        field_columns = {field: column_by_header[header] for field, header in profile.column_bindings}
        physical = empty = 0
        records = []
        for row_number in sorted(rows):
            if row_number < profile.first_data_row:
                continue
            physical += 1
            if physical > profile.max_data_rows:
                raise KingdeeReaderError("LEDGER_ROW_LIMIT", "ledger exceeds the locked data-row ceiling")
            row_values = rows[row_number]
            bound = {field: row_values.get(column, _CellValue(None, "blank")) for field, column in field_columns.items()}
            if all(value.text is None or value.text.strip() == "" for value in bound.values()):
                empty += 1
                continue
            try:
                records.append(
                    _ledger_record(
                        row_number=row_number,
                        cells=bound,
                        selection=selection,
                        profile=profile,
                        money_profile=money_profile,
                        date_1904=date_1904,
                        sheet_ref=sheet_ref,
                    )
                )
            except KingdeeReaderError as exc:
                partial = KingdeeReaderControl(
                    physical_data_row_count=physical,
                    emitted_record_count=len(records),
                    empty_row_count=empty,
                    parse_failure_count=1,
                    exclusion_counts=(("EMPTY_ROW", empty), ("PARSE_FAILURE", 1)) if empty else (("PARSE_FAILURE", 1),),
                    debit=_amount_control(record.debit_minor for record in records),
                    credit=_amount_control(record.credit_minor for record in records),
                    balance=_amount_control(record.balance_minor for record in records),
                    row_conservation_delta=physical - len(records) - empty - 1,
                )
                partial.validate()
                raise KingdeeReaderError(
                    exc.code,
                    exc.message,
                    row_number=row_number,
                    column_id=exc.column_id,
                    partial_control=partial,
                ) from exc
    result_records = tuple(records)
    control = KingdeeReaderControl(
        physical_data_row_count=physical,
        emitted_record_count=len(result_records),
        empty_row_count=empty,
        parse_failure_count=0,
        exclusion_counts=(("EMPTY_ROW", empty),) if empty else (),
        debit=_amount_control(record.debit_minor for record in result_records),
        credit=_amount_control(record.credit_minor for record in result_records),
        balance=_amount_control(record.balance_minor for record in result_records),
        row_conservation_delta=physical - len(result_records) - empty,
    )
    control.validate()
    return result_records, control


def _hash_open_file(handle: BinaryIO) -> str:
    handle.seek(0)
    digest = hashlib.sha256()
    for block in iter(lambda: handle.read(1024 * 1024), b""):
        digest.update(block)
    handle.seek(0)
    return digest.hexdigest()


def read_kingdee_ledger(
    *,
    input_root: Path,
    selection: SourceSelection,
    reader_profile: KingdeeReaderProfile,
    security_profile: SecurityProfile,
    money_profile: MoneyProfile,
) -> KingdeeReaderResult:
    """Read one manifest-selected ledger after all digest/schema/security gates."""

    reader_profile.validate(require_active=True)
    if selection.slot_id != "general_ledger":
        raise KingdeeReaderError("LEDGER_SLOT_MISMATCH", "Kingdee reader accepts only the governed general_ledger slot")
    if selection.reader != reader_profile.reader_id or selection.reader_version != reader_profile.reader_version:
        raise KingdeeReaderError("LEDGER_READER_DRIFT", "manifest reader binding differs from the locked profile")
    if selection.schema_id != reader_profile.schema_id or selection.schema_fingerprint != reader_profile.schema_fingerprint:
        raise KingdeeReaderError("LEDGER_SCHEMA_BINDING_DRIFT", "manifest schema binding differs from the locked profile")
    suffix = Path(selection.private_relative_path).suffix.casefold()
    expected_kind = "xlsx" if suffix == ".xlsx" else "xls" if suffix == ".xls" else ""
    if not expected_kind:
        raise KingdeeReaderError("LEDGER_FILE_TYPE", "ledger source must be .xlsx or explicitly blocked legacy .xls")
    try:
        preflight = preflight_source_file(
            input_root,
            Path(selection.private_relative_path),
            expected_kind=expected_kind,
            profile=security_profile,
        )
    except FileSecurityError as exc:
        raise KingdeeReaderError(exc.code, exc.message) from exc
    if preflight.sha256 != selection.sha256:
        raise KingdeeReaderError("LEDGER_SOURCE_DIGEST_DRIFT", "preflight digest differs from the manifest selection")
    try:
        source_path = resolve_input_file(
            input_root,
            Path(selection.private_relative_path),
            max_bytes=security_profile.source_file_bytes_max,
        )
    except PathSafetyError as exc:
        raise KingdeeReaderError(exc.code, exc.message) from exc
    try:
        with source_path.open("rb") as handle:
            identity_before = os.fstat(handle.fileno())
            if not stat.S_ISREG(identity_before.st_mode) or identity_before.st_nlink != 1:
                raise KingdeeReaderError("LEDGER_SOURCE_IDENTITY", "ledger source must remain a single-link regular file")
            selected_identity = selection.identity
            if (
                identity_before.st_dev != selected_identity.device
                or identity_before.st_ino != selected_identity.inode
                or identity_before.st_size != selected_identity.size_bytes
                or identity_before.st_mtime_ns != selected_identity.mtime_ns
                or identity_before.st_nlink != selected_identity.link_count
            ):
                raise KingdeeReaderError(
                    "LEDGER_SELECTION_IDENTITY_DRIFT",
                    "ledger source identity differs from the formal manifest selection",
                )
            first_hash = _hash_open_file(handle)
            if first_hash != selection.sha256 or identity_before.st_size != preflight.size_bytes:
                raise KingdeeReaderError(
                    "LEDGER_SOURCE_CHANGED_AFTER_PREFLIGHT",
                    "ledger source changed after security preflight",
                )
            records, control = _parse_xlsx(
                handle,
                selection=selection,
                profile=reader_profile,
                security_profile=security_profile,
                money_profile=money_profile,
            )
            final_hash = _hash_open_file(handle)
            identity_after = os.fstat(handle.fileno())
    except KingdeeReaderError:
        raise
    except OSError as exc:
        code = exc.code if isinstance(exc, PathSafetyError) else "LEDGER_SOURCE_READ"
        message = exc.message if isinstance(exc, PathSafetyError) else "ledger source cannot be read"
        raise KingdeeReaderError(code, message) from exc
    identity_tuple_before = (
        identity_before.st_dev,
        identity_before.st_ino,
        identity_before.st_size,
        identity_before.st_mtime_ns,
        identity_before.st_nlink,
    )
    identity_tuple_after = (
        identity_after.st_dev,
        identity_after.st_ino,
        identity_after.st_size,
        identity_after.st_mtime_ns,
        identity_after.st_nlink,
    )
    if final_hash != selection.sha256 or identity_tuple_after != identity_tuple_before:
        raise KingdeeReaderError("LEDGER_SOURCE_CHANGED_DURING_PARSE", "ledger source changed while the reader was parsing")
    fingerprint = _digest(
        {
            "reader_id": reader_profile.reader_id,
            "reader_version": reader_profile.reader_version,
            "reader_profile_sha256": reader_profile.content_sha256,
            "schema_fingerprint": reader_profile.schema_fingerprint,
            "record_business_digests": sorted(record.normalized_business_digest for record in records),
        }
    )
    return KingdeeReaderResult(
        records=records,
        control=control,
        source_sha256=selection.sha256,
        reader_profile_sha256=reader_profile.content_sha256,
        schema_fingerprint=reader_profile.schema_fingerprint,
        business_fingerprint=fingerprint,
    )


def public_reader_summary(result: KingdeeReaderResult) -> Dict[str, Any]:
    """Aggregate-only public view: no path, file hash, cell text, account or amount."""

    result.control.validate()
    return {
        "schema_version": "kmfa.project_cost.public_reader_summary.v1",
        "reader_id": KINGDEE_READER_ID,
        "reader_version": KINGDEE_READER_VERSION,
        "status": "READER_PASS",
        "physical_data_row_count": result.control.physical_data_row_count,
        "emitted_record_count": result.control.emitted_record_count,
        "empty_row_count": result.control.empty_row_count,
        "parse_failure_count": result.control.parse_failure_count,
        "row_conservation_delta": result.control.row_conservation_delta,
    }
