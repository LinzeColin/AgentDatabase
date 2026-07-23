"""Public-safe builders for synthetic malicious and benign file fixtures."""

from __future__ import annotations

import stat
import struct
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Optional, Sequence, Tuple
from xml.sax.saxutils import escape


CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>
"""

ROOT_RELS = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>
"""

WORKBOOK_RELS = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>
"""


@dataclass(frozen=True)
class NumericCell:
    value: str


def _column_name(index: int) -> str:
    result = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        result = chr(65 + remainder) + result
    return result


def write_tabular_xlsx(
    path: Path,
    rows: Sequence[Sequence[object]],
    *,
    sheet_name: str = "Ledger",
    date_1904: bool = False,
) -> None:
    """Write a public synthetic value-only workbook without Office automation."""

    row_xml = []
    for row_index, row in enumerate(rows, start=1):
        cells = []
        for column_index, value in enumerate(row, start=1):
            if value is None:
                continue
            reference = "%s%d" % (_column_name(column_index), row_index)
            if isinstance(value, NumericCell):
                cells.append('<c r="%s"><v>%s</v></c>' % (reference, escape(value.value)))
            else:
                cells.append(
                    '<c r="%s" t="inlineStr"><is><t>%s</t></is></c>'
                    % (reference, escape(str(value)))
                )
        row_xml.append('<row r="%d">%s</row>' % (row_index, "".join(cells)))
    workbook = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<workbookPr date1904="%d"/>'
        '<sheets><sheet name="%s" sheetId="1" state="visible" r:id="rId1"/></sheets>'
        '</workbook>' % (1 if date_1904 else 0, escape(sheet_name))
    ).encode("utf-8")
    worksheet = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<sheetData>%s</sheetData></worksheet>' % "".join(row_xml)
    ).encode("utf-8")
    parts = {
        "[Content_Types].xml": CONTENT_TYPES.encode("utf-8"),
        "_rels/.rels": ROOT_RELS.encode("utf-8"),
        "xl/workbook.xml": workbook,
        "xl/_rels/workbook.xml.rels": WORKBOOK_RELS.encode("utf-8"),
        "xl/worksheets/sheet1.xml": worksheet,
    }
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in parts.items():
            archive.writestr(name, data)


def write_zip(
    path: Path,
    members: Sequence[Tuple[str, bytes]],
    *,
    compression: int = zipfile.ZIP_STORED,
) -> None:
    with zipfile.ZipFile(path, "w", compression=compression) as archive:
        for name, data in members:
            archive.writestr(name, data)


def write_special_member_zip(path: Path, name: str, file_type: int) -> None:
    info = zipfile.ZipInfo(name)
    info.create_system = 3
    info.external_attr = (file_type | 0o600) << 16
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(info, b"synthetic")


def mark_first_member_encrypted(path: Path) -> None:
    payload = bytearray(path.read_bytes())
    local = payload.find(b"PK\x03\x04")
    central = payload.find(b"PK\x01\x02")
    if local < 0 or central < 0:
        raise ValueError("synthetic ZIP structures were not found")
    local_flags = struct.unpack_from("<H", payload, local + 6)[0] | 0x1
    central_flags = struct.unpack_from("<H", payload, central + 8)[0] | 0x1
    struct.pack_into("<H", payload, local + 6, local_flags)
    struct.pack_into("<H", payload, central + 8, central_flags)
    path.write_bytes(payload)


def corrupt_stored_member_payload(path: Path, marker: bytes) -> None:
    payload = bytearray(path.read_bytes())
    offset = payload.find(marker)
    if offset < 0:
        raise ValueError("synthetic CRC marker was not found")
    payload[offset] ^= 0x01
    path.write_bytes(payload)


def write_xlsx(
    path: Path,
    *,
    formula: Optional[str] = None,
    sheet_state: str = "visible",
    image_only: bool = False,
    external_relationship: bool = False,
    include_vba: bool = False,
    macro_content_type: bool = False,
    include_connection: bool = False,
    include_external_link_part: bool = False,
    defined_name: Optional[Tuple[str, str]] = None,
    workbook_override: Optional[bytes] = None,
    omit_required: Iterable[str] = (),
    extra_parts: Optional[Dict[str, bytes]] = None,
) -> None:
    defined_names = ""
    if defined_name is not None:
        name, value = defined_name
        defined_names = "<definedNames><definedName name=\"%s\">%s</definedName></definedNames>" % (
            escape(name),
            escape(value),
        )
    workbook = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
        "<workbook xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\" "
        "xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\">"
        "<sheets><sheet name=\"Sheet1\" sheetId=\"1\" state=\"%s\" r:id=\"rId1\"/></sheets>%s</workbook>"
        % (escape(sheet_state), defined_names)
    ).encode("utf-8")
    if image_only:
        sheet = (
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
            "<worksheet xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\" "
            "xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\">"
            "<sheetData/><drawing r:id=\"rId1\"/></worksheet>"
        ).encode("utf-8")
    else:
        formula_xml = ""
        if formula is not None:
            formula_xml = "<f>%s</f>" % escape(formula)
        sheet = (
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
            "<worksheet xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\">"
            "<sheetData><row r=\"1\"><c r=\"A1\">%s<v>1</v></c></row></sheetData></worksheet>"
            % formula_xml
        ).encode("utf-8")
    content_types = CONTENT_TYPES
    if macro_content_type:
        content_types = content_types.replace(
            "</Types>",
            '<Override PartName="/xl/vbaProject.bin" ContentType="application/vnd.ms-office.vbaProject"/></Types>',
        )
    parts: Dict[str, bytes] = {
        "[Content_Types].xml": content_types.encode("utf-8"),
        "_rels/.rels": ROOT_RELS.encode("utf-8"),
        "xl/workbook.xml": workbook_override if workbook_override is not None else workbook,
        "xl/_rels/workbook.xml.rels": WORKBOOK_RELS.encode("utf-8"),
        "xl/worksheets/sheet1.xml": sheet,
    }
    if external_relationship:
        parts["xl/worksheets/_rels/sheet1.xml.rels"] = (
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
            "<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">"
            "<Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/image\" "
            "Target=\"https://invalid.example/image.png\" TargetMode=\"External\"/></Relationships>"
        ).encode("utf-8")
    if include_vba:
        parts["xl/vbaProject.bin"] = b"synthetic-vba-marker"
    if include_connection:
        parts["xl/connections.xml"] = b"<connections xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\"/>"
    if include_external_link_part:
        parts["xl/externalLinks/externalLink1.xml"] = b"<externalLink/>"
    if extra_parts:
        parts.update(extra_parts)
    for name in omit_required:
        parts.pop(name, None)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in parts.items():
            archive.writestr(name, data)
