"""Fail-closed file, ZIP, OOXML, XLS, PDF, and spreadsheet-text preflight."""

from __future__ import annotations

import hashlib
import os
import re
import stat
import tempfile
import unicodedata
import zipfile
import zlib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Dict, List, Mapping, Optional, Tuple
from xml.etree import ElementTree as ET

import yaml

from .paths import PathSafetyError, resolve_input_file


ZIP_SIGNATURES = (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")
OLE_SIGNATURE = bytes.fromhex("D0CF11E0A1B11AE1")
PDF_SIGNATURE = b"%PDF-"
DANGEROUS_TEXT_PREFIXES = frozenset("=+-@\t\r\n")
MACRO_EXTENSIONS = frozenset({".xlsm", ".xltm", ".xlam"})


class SecurityProfileError(RuntimeError):
    """Raised when security limits are missing or internally inconsistent."""


class FileSecurityError(ValueError):
    def __init__(self, code: str, message: str, *, member: Optional[str] = None, report: Any = None) -> None:
        super().__init__("%s: %s" % (code, message))
        self.code = code
        self.message = message
        self.member = member
        self.report = report

    def as_dict(self, *, include_sensitive: bool = False) -> Dict[str, Any]:
        result: Dict[str, Any] = {"code": self.code, "message": self.message}
        if self.member is not None:
            result["member_ref"] = hashlib.sha256(
                self.member.encode("utf-8", errors="surrogatepass")
            ).hexdigest()[:16]
            if include_sensitive:
                result["member"] = self.member
        return result


@dataclass(frozen=True)
class SecurityProfile:
    profile_id: str
    source_file_bytes_max: int
    archive_member_count_max: int
    archive_total_uncompressed_bytes_max: int
    archive_single_member_bytes_max: int
    archive_compression_ratio_max: int
    archive_nested_depth_max: int
    xml_single_part_bytes_max: int
    allowed_zip_compression_methods: Tuple[int, ...]
    legacy_xls_policy: str
    macro_enabled_ooxml_policy: str
    formula_cell_policy: str
    external_relationship_policy: str

    @classmethod
    def from_mapping(cls, config: Mapping[str, Any]) -> "SecurityProfile":
        if config.get("schema_version") != "kmfa.project_cost.security_limits.v1":
            raise SecurityProfileError("unsupported security profile schema")
        integer_fields = (
            "source_file_bytes_max",
            "archive_member_count_max",
            "archive_total_uncompressed_bytes_max",
            "archive_single_member_bytes_max",
            "archive_compression_ratio_max",
            "archive_nested_depth_max",
            "xml_single_part_bytes_max",
        )
        policy_fields = (
            "profile_id",
            "legacy_xls_policy",
            "macro_enabled_ooxml_policy",
            "formula_cell_policy",
            "external_relationship_policy",
        )
        if any(type(config.get(field)) is not int for field in integer_fields):
            raise SecurityProfileError("security ceiling fields must use exact integer types")
        if any(not isinstance(config.get(field), str) for field in policy_fields):
            raise SecurityProfileError("security profile policy fields must use exact string types")
        raw_methods = config.get("allowed_zip_compression_methods")
        if not isinstance(raw_methods, list) or any(type(item) is not int for item in raw_methods):
            raise SecurityProfileError("ZIP compression methods must be an integer list")
        try:
            methods = tuple(raw_methods)
            profile = cls(
                profile_id=config["profile_id"],
                source_file_bytes_max=config["source_file_bytes_max"],
                archive_member_count_max=config["archive_member_count_max"],
                archive_total_uncompressed_bytes_max=config["archive_total_uncompressed_bytes_max"],
                archive_single_member_bytes_max=config["archive_single_member_bytes_max"],
                archive_compression_ratio_max=config["archive_compression_ratio_max"],
                archive_nested_depth_max=config["archive_nested_depth_max"],
                xml_single_part_bytes_max=config["xml_single_part_bytes_max"],
                allowed_zip_compression_methods=methods,
                legacy_xls_policy=config["legacy_xls_policy"],
                macro_enabled_ooxml_policy=config["macro_enabled_ooxml_policy"],
                formula_cell_policy=config["formula_cell_policy"],
                external_relationship_policy=config["external_relationship_policy"],
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise SecurityProfileError("invalid security profile fields") from exc
        numeric = (
            profile.source_file_bytes_max,
            profile.archive_member_count_max,
            profile.archive_total_uncompressed_bytes_max,
            profile.archive_single_member_bytes_max,
            profile.archive_compression_ratio_max,
            profile.archive_nested_depth_max,
            profile.xml_single_part_bytes_max,
        )
        if not profile.profile_id or any(value <= 0 for value in numeric):
            raise SecurityProfileError("security ceilings must be positive")
        if set(methods) != {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}:
            raise SecurityProfileError("only stored and deflated ZIP members are supported")
        expected_policies = {
            "legacy_xls_policy": "BLOCK_UNTIL_LOCKED_READER",
            "macro_enabled_ooxml_policy": "BLOCK",
            "formula_cell_policy": "BLOCK_UNTIL_GOVERNED_CACHED_VALUE_READER",
            "external_relationship_policy": "BLOCK",
        }
        if any(getattr(profile, field) != expected for field, expected in expected_policies.items()):
            raise SecurityProfileError("security policies cannot be relaxed in product 0.2.0")
        if profile.archive_single_member_bytes_max > profile.archive_total_uncompressed_bytes_max:
            raise SecurityProfileError("single-member ceiling cannot exceed total ceiling")
        return profile

    @classmethod
    def from_yaml(cls, path: Path) -> "SecurityProfile":
        try:
            value = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, yaml.YAMLError) as exc:
            raise SecurityProfileError("cannot load security profile") from exc
        if not isinstance(value, dict):
            raise SecurityProfileError("security profile must be a mapping")
        return cls.from_mapping(value)


@dataclass(frozen=True)
class ZipPreflightReport:
    sha256: str
    member_count: int
    total_uncompressed_bytes: int
    nested_archive_candidate_count: int
    recursive_member_count: int
    recursive_total_uncompressed_bytes: int
    crc_verified: bool


@dataclass(frozen=True)
class OoxmlFinding:
    code: str
    severity: str


@dataclass(frozen=True)
class OoxmlPreflightReport:
    sha256: str
    archive_member_count: int
    formula_cell_count: int
    dde_formula_count: int
    hidden_sheet_count: int
    very_hidden_sheet_count: int
    named_range_count: int
    image_only_sheet_count: int
    findings: Tuple[OoxmlFinding, ...]

    @property
    def blocker_codes(self) -> Tuple[str, ...]:
        return tuple(item.code for item in self.findings if item.severity == "BLOCK")


@dataclass(frozen=True)
class SourceFileReport:
    expected_kind: str
    sha256: str
    size_bytes: int
    status: str
    structured_data_allowed: bool


@dataclass
class _ArchiveBudget:
    member_count: int = 0
    total_uncompressed_bytes: int = 0


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _file_identity(path: Path) -> Tuple[int, int, int, int]:
    metadata = path.stat()
    return (metadata.st_dev, metadata.st_ino, metadata.st_size, metadata.st_mtime_ns)


def _capture_source(path: Path) -> Tuple[Tuple[int, int, int, int], str]:
    try:
        return _file_identity(path), _sha256(path)
    except OSError as exc:
        raise FileSecurityError("SOURCE_UNREADABLE", "source cannot be read for identity and digest") from exc


def _assert_source_unchanged(
    path: Path,
    *,
    expected_identity: Tuple[int, int, int, int],
    expected_sha256: str,
) -> None:
    try:
        unchanged = _file_identity(path) == expected_identity and _sha256(path) == expected_sha256
    except OSError:
        unchanged = False
    if not unchanged:
        raise FileSecurityError(
            "SOURCE_CHANGED_DURING_PREFLIGHT",
            "source identity or digest changed while security gates were running",
        )


def _safe_member_name(name: str) -> str:
    if not name or "\x00" in name or "\\" in name:
        raise FileSecurityError("UNSAFE_ARCHIVE_PATH", "archive member path is empty or non-portable", member=name)
    if name.startswith("/") or name.startswith("//") or re.match(r"^[A-Za-z]:", name):
        raise FileSecurityError("ABSOLUTE_ARCHIVE_PATH", "absolute or drive archive path is forbidden", member=name)
    trimmed = name[:-1] if name.endswith("/") else name
    components = trimmed.split("/")
    if not trimmed or any(component in ("", ".", "..") for component in components):
        raise FileSecurityError("ARCHIVE_PATH_TRAVERSAL", "archive path has an ambiguous component", member=name)
    normalized = "/".join(unicodedata.normalize("NFKC", component).casefold() for component in components)
    return normalized


def _resolve_source(root: Path, candidate: Path, profile: SecurityProfile) -> Path:
    try:
        return resolve_input_file(root, candidate, max_bytes=profile.source_file_bytes_max)
    except PathSafetyError as exc:
        raise FileSecurityError(exc.code, exc.message) from exc


def _validated_scratch(scratch_root: Optional[Path]) -> Optional[Path]:
    if scratch_root is None:
        return None
    value = Path(scratch_root)
    if value.is_symlink() or not value.is_dir():
        raise FileSecurityError("UNSAFE_PRIVATE_SCRATCH", "nested archive scratch must be an existing real directory")
    return value.resolve()


def _inspect_open_archive(
    archive: zipfile.ZipFile,
    *,
    profile: SecurityProfile,
    depth: int,
    scratch_root: Optional[Path],
    budget: _ArchiveBudget,
) -> Tuple[int, int, int]:
    if depth > profile.archive_nested_depth_max:
        raise FileSecurityError("ARCHIVE_NESTING_DEPTH", "nested archive depth exceeds the security ceiling")
    infos = archive.infolist()
    if len(infos) > profile.archive_member_count_max:
        raise FileSecurityError("ARCHIVE_MEMBER_LIMIT", "archive member count exceeds the security ceiling")
    normalized_targets = set()
    local_total = 0
    nested_infos: List[zipfile.ZipInfo] = []
    for info in infos:
        normalized = _safe_member_name(info.filename)
        if normalized in normalized_targets:
            raise FileSecurityError(
                "DUPLICATE_ARCHIVE_TARGET",
                "archive members collide after portable normalization",
                member=info.filename,
            )
        normalized_targets.add(normalized)
        if info.flag_bits & 0x1:
            raise FileSecurityError("ENCRYPTED_ARCHIVE_MEMBER", "encrypted members are forbidden", member=info.filename)
        unix_mode = (info.external_attr >> 16) & 0xFFFF
        file_type = stat.S_IFMT(unix_mode)
        if file_type == stat.S_IFLNK:
            raise FileSecurityError("SYMLINK_ARCHIVE_MEMBER", "symlink members are forbidden", member=info.filename)
        if file_type not in (0, stat.S_IFREG, stat.S_IFDIR):
            raise FileSecurityError("SPECIAL_ARCHIVE_MEMBER", "special-device members are forbidden", member=info.filename)
        if info.compress_type not in profile.allowed_zip_compression_methods:
            raise FileSecurityError("UNSUPPORTED_COMPRESSION", "ZIP compression method is not approved", member=info.filename)
        if info.file_size > profile.archive_single_member_bytes_max:
            raise FileSecurityError("ARCHIVE_MEMBER_SIZE_LIMIT", "member exceeds the security ceiling", member=info.filename)
        ratio = info.file_size / max(info.compress_size, 1)
        if ratio > profile.archive_compression_ratio_max:
            raise FileSecurityError("ARCHIVE_COMPRESSION_RATIO", "member exceeds the compression-ratio ceiling", member=info.filename)
        local_total += info.file_size
        if local_total > profile.archive_total_uncompressed_bytes_max:
            raise FileSecurityError("ARCHIVE_TOTAL_SIZE_LIMIT", "archive exceeds the total size ceiling")
        budget.member_count += 1
        budget.total_uncompressed_bytes += info.file_size
        if budget.member_count > profile.archive_member_count_max:
            raise FileSecurityError("ARCHIVE_RECURSIVE_MEMBER_LIMIT", "archive tree exceeds the member ceiling")
        if budget.total_uncompressed_bytes > profile.archive_total_uncompressed_bytes_max:
            raise FileSecurityError("ARCHIVE_RECURSIVE_TOTAL_SIZE_LIMIT", "archive tree exceeds the expanded-size ceiling")
        suffix = PurePosixPath(info.filename.rstrip("/")).suffix.casefold()
        if suffix == ".xlsm":
            raise FileSecurityError("NESTED_MACRO_ENABLED_OOXML", "macro-enabled workbooks are blocked inside archives")
        if suffix in {".zip", ".xlsx"}:
            nested_infos.append(info)
    corrupt_member = archive.testzip()
    if corrupt_member is not None:
        raise FileSecurityError("ARCHIVE_CRC_FAILURE", "archive member CRC verification failed", member=corrupt_member)

    nested_count = 0
    for info in nested_infos:
        if scratch_root is None:
            raise FileSecurityError(
                "NESTED_ARCHIVE_SCRATCH_REQUIRED",
                "nested archive verification requires an explicit private scratch directory",
                member=info.filename,
            )
        if depth >= profile.archive_nested_depth_max:
            raise FileSecurityError("ARCHIVE_NESTING_DEPTH", "nested archive depth exceeds the security ceiling")
        descriptor, temporary_name = tempfile.mkstemp(
            prefix="nested-preflight-",
            suffix=PurePosixPath(info.filename).suffix,
            dir=str(scratch_root),
        )
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as output, archive.open(info) as source:
                for block in iter(lambda: source.read(1024 * 1024), b""):
                    output.write(block)
                output.flush()
                os.fsync(output.fileno())
            with temporary.open("rb") as handle:
                if handle.read(4) not in ZIP_SIGNATURES:
                    raise FileSecurityError(
                        "NESTED_ARCHIVE_SIGNATURE",
                        "nested archive extension does not match its signature",
                        member=info.filename,
                    )
            with zipfile.ZipFile(temporary) as nested:
                _, _, descendants = _inspect_open_archive(
                    nested,
                    profile=profile,
                    depth=depth + 1,
                    scratch_root=scratch_root,
                    budget=budget,
                )
            nested_count += 1 + descendants
        finally:
            if temporary.exists():
                temporary.unlink()
    return len(infos), local_total, nested_count


def preflight_zip(
    root: Path,
    candidate: Path,
    *,
    profile: SecurityProfile,
    scratch_root: Optional[Path] = None,
) -> ZipPreflightReport:
    path = _resolve_source(root, candidate, profile)
    scratch = _validated_scratch(scratch_root)
    identity_before, digest_before = _capture_source(path)
    try:
        with path.open("rb") as handle:
            signature = handle.read(4)
        if signature not in ZIP_SIGNATURES:
            raise FileSecurityError("TYPE_SIGNATURE_MISMATCH", "expected a ZIP-family signature")
        with zipfile.ZipFile(path) as archive:
            budget = _ArchiveBudget()
            member_count, total_uncompressed, nested_count = _inspect_open_archive(
                archive,
                profile=profile,
                depth=0,
                scratch_root=scratch,
                budget=budget,
            )
    except FileSecurityError:
        raise
    except (OSError, EOFError, RuntimeError, NotImplementedError, zipfile.BadZipFile, zlib.error) as exc:
        raise FileSecurityError("INVALID_ARCHIVE", "archive cannot be safely verified") from exc
    _assert_source_unchanged(path, expected_identity=identity_before, expected_sha256=digest_before)
    return ZipPreflightReport(
        sha256=digest_before,
        member_count=member_count,
        total_uncompressed_bytes=total_uncompressed,
        nested_archive_candidate_count=nested_count,
        recursive_member_count=budget.member_count,
        recursive_total_uncompressed_bytes=budget.total_uncompressed_bytes,
        crc_verified=True,
    )


def _read_xml_part(archive: zipfile.ZipFile, name: str, profile: SecurityProfile) -> ET.Element:
    try:
        info = archive.getinfo(name)
    except KeyError as exc:
        raise FileSecurityError("OOXML_REQUIRED_PART_MISSING", "required OOXML part is missing", member=name) from exc
    if info.file_size > profile.xml_single_part_bytes_max:
        raise FileSecurityError("XML_PART_SIZE_LIMIT", "OOXML XML part exceeds the security ceiling", member=name)
    try:
        data = archive.read(info)
    except (OSError, EOFError, RuntimeError, NotImplementedError, zipfile.BadZipFile, zlib.error) as exc:
        raise FileSecurityError("INVALID_OOXML_ARCHIVE", "OOXML part cannot be read safely", member=name) from exc
    upper = data.upper()
    if b"<!DOCTYPE" in upper or b"<!ENTITY" in upper:
        raise FileSecurityError("XML_DTD_FORBIDDEN", "DTD and entity declarations are forbidden", member=name)
    try:
        return ET.fromstring(data)
    except ET.ParseError as exc:
        raise FileSecurityError("INVALID_OOXML_XML", "OOXML XML part is malformed", member=name) from exc


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def inspect_ooxml(root: Path, candidate: Path, *, profile: SecurityProfile) -> OoxmlPreflightReport:
    path = _resolve_source(root, candidate, profile)
    if path.suffix.casefold() in MACRO_EXTENSIONS:
        raise FileSecurityError("MACRO_ENABLED_EXTENSION", "macro-enabled OOXML extensions are blocked")
    if path.suffix.casefold() != ".xlsx":
        raise FileSecurityError("TYPE_EXTENSION_MISMATCH", "OOXML workbook must use the .xlsx extension")
    zip_report = preflight_zip(root, path, profile=profile)
    identity_after_zip_preflight = _file_identity(path)
    findings: List[OoxmlFinding] = []
    finding_keys = set()

    def add(code: str, severity: str = "BLOCK") -> None:
        key = (code, severity)
        if key not in finding_keys:
            finding_keys.add(key)
            findings.append(OoxmlFinding(code=code, severity=severity))

    formula_count = 0
    dde_count = 0
    hidden_count = 0
    very_hidden_count = 0
    named_range_count = 0
    image_only_count = 0
    try:
        archive_context = zipfile.ZipFile(path)
    except (OSError, EOFError, RuntimeError, NotImplementedError, zipfile.BadZipFile) as exc:
        raise FileSecurityError("INVALID_OOXML_ARCHIVE", "OOXML package cannot be reopened safely") from exc
    with archive_context as archive:
        names = archive.namelist()
        required = ("[Content_Types].xml", "_rels/.rels", "xl/workbook.xml")
        for name in required:
            if name not in names:
                raise FileSecurityError("OOXML_REQUIRED_PART_MISSING", "required OOXML part is missing", member=name)
        lowered_names = [name.casefold() for name in names]
        active_prefixes = (
            "xl/activex/",
            "xl/embeddings/",
            "xl/macrosheets/",
            "xl/externallinks/",
            "xl/querytables/",
        )
        if any(name == "xl/vbaproject.bin" or name.startswith(active_prefixes) for name in lowered_names):
            add("OOXML_ACTIVE_CONTENT_PART")
        if "xl/connections.xml" in lowered_names:
            add("OOXML_DATA_CONNECTION")

        content_types = _read_xml_part(archive, "[Content_Types].xml", profile)
        for node in content_types.iter():
            content_type = node.attrib.get("ContentType", "").casefold()
            if any(token in content_type for token in ("macroenabled", "vbaproject", "activex", "oleobject")):
                add("OOXML_ACTIVE_CONTENT_TYPE")

        for name in names:
            if not name.casefold().endswith(".rels"):
                continue
            root_node = _read_xml_part(archive, name, profile)
            for relationship in root_node.iter():
                if _local_name(relationship.tag) != "Relationship":
                    continue
                mode = relationship.attrib.get("TargetMode", "").casefold()
                relation_type = relationship.attrib.get("Type", "").casefold()
                if mode == "external":
                    add("OOXML_EXTERNAL_RELATIONSHIP")
                if any(token in relation_type for token in ("externalLink".casefold(), "oleobject", "package", "connections")):
                    add("OOXML_ACTIVE_RELATIONSHIP")

        workbook = _read_xml_part(archive, "xl/workbook.xml", profile)
        for node in workbook.iter():
            local = _local_name(node.tag)
            if local == "sheet":
                state = node.attrib.get("state", "visible").casefold()
                hidden_count += state == "hidden"
                very_hidden_count += state == "veryhidden"
            elif local == "definedName":
                named_range_count += 1
                defined_name = node.attrib.get("name", "").casefold()
                defined_value = node.text or ""
                if "auto_open" in defined_name or "auto_close" in defined_name:
                    add("OOXML_AUTORUN_DEFINED_NAME")
                if re.search(r"(?i)\bDDE\s*\(|\|[^!]+!", defined_value):
                    add("OOXML_DDE_DEFINED_NAME")
        if hidden_count:
            add("OOXML_HIDDEN_SHEETS", "WARN")
        if very_hidden_count:
            add("OOXML_VERY_HIDDEN_SHEETS", "WARN")
        if named_range_count:
            add("OOXML_NAMED_RANGES", "WARN")

        for name in names:
            lowered = name.casefold()
            if not (lowered.startswith("xl/worksheets/") and lowered.endswith(".xml")):
                continue
            worksheet = _read_xml_part(archive, name, profile)
            cells = 0
            drawings = 0
            for node in worksheet.iter():
                local = _local_name(node.tag)
                if local == "c":
                    cells += 1
                elif local in ("drawing", "legacyDrawing"):
                    drawings += 1
                elif local == "f":
                    formula_count += 1
                    formula = node.text or ""
                    if re.search(r"(?i)\bDDE\s*\(|\|[^!]+!", formula):
                        dde_count += 1
            if drawings and cells == 0:
                image_only_count += 1
        if formula_count:
            add("OOXML_FORMULA_CELLS")
        if dde_count:
            add("OOXML_DDE_FORMULA")
        if image_only_count:
            add("OOXML_IMAGE_ONLY_SHEET")
    _assert_source_unchanged(
        path,
        expected_identity=identity_after_zip_preflight,
        expected_sha256=zip_report.sha256,
    )
    return OoxmlPreflightReport(
        sha256=zip_report.sha256,
        archive_member_count=zip_report.member_count,
        formula_cell_count=formula_count,
        dde_formula_count=dde_count,
        hidden_sheet_count=hidden_count,
        very_hidden_sheet_count=very_hidden_count,
        named_range_count=named_range_count,
        image_only_sheet_count=image_only_count,
        findings=tuple(findings),
    )


def require_safe_ooxml(root: Path, candidate: Path, *, profile: SecurityProfile) -> OoxmlPreflightReport:
    report = inspect_ooxml(root, candidate, profile=profile)
    if report.blocker_codes:
        raise FileSecurityError(
            "OOXML_BLOCKED",
            "OOXML contains blocking active or ambiguous content: %s" % ",".join(report.blocker_codes),
            report=report,
        )
    return report


def _preflight_pdf(path: Path) -> None:
    size = path.stat().st_size
    with path.open("rb") as handle:
        handle.seek(max(0, size - 4096))
        tail = handle.read()
    if b"%%EOF" not in tail:
        raise FileSecurityError("PDF_EOF_MISSING", "PDF end-of-file marker is missing")
    active_pattern = re.compile(
        rb"/(?:JAVASCRIPT|JS|OPENACTION|AA|LAUNCH|EMBEDDEDFILE|RICHMEDIA|XFA|URI)(?![A-Z])"
    )
    encrypted_pattern = re.compile(rb"/ENCRYPT(?![A-Z])")
    carry = b""
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            searchable = (carry + block).upper()
            if encrypted_pattern.search(searchable):
                raise FileSecurityError("PDF_ENCRYPTED", "encrypted PDF input is blocked")
            if active_pattern.search(searchable):
                raise FileSecurityError("PDF_ACTIVE_CONTENT", "PDF active or external content is blocked")
            carry = searchable[-64:]


def preflight_source_file(
    root: Path,
    candidate: Path,
    *,
    expected_kind: str,
    profile: SecurityProfile,
    scratch_root: Optional[Path] = None,
) -> SourceFileReport:
    path = _resolve_source(root, candidate, profile)
    expected = expected_kind.casefold()
    with path.open("rb") as handle:
        signature = handle.read(8)
    if expected == "xlsx":
        if path.suffix.casefold() in MACRO_EXTENSIONS:
            raise FileSecurityError("MACRO_ENABLED_EXTENSION", "macro-enabled OOXML extensions are blocked")
        if path.suffix.casefold() != ".xlsx" or signature[:4] not in ZIP_SIGNATURES:
            raise FileSecurityError("TYPE_SIGNATURE_MISMATCH", "expected an .xlsx ZIP-family file")
        report = require_safe_ooxml(root, path, profile=profile)
        return SourceFileReport("xlsx", report.sha256, path.stat().st_size, "PREFLIGHT_PASS", True)
    if expected == "zip":
        if path.suffix.casefold() != ".zip" or signature[:4] not in ZIP_SIGNATURES:
            raise FileSecurityError("TYPE_SIGNATURE_MISMATCH", "expected a ZIP archive")
        report = preflight_zip(root, path, profile=profile, scratch_root=scratch_root)
        return SourceFileReport("zip", report.sha256, path.stat().st_size, "PREFLIGHT_PASS", False)
    if expected == "xls":
        if path.suffix.casefold() != ".xls" or signature != OLE_SIGNATURE:
            raise FileSecurityError("TYPE_SIGNATURE_MISMATCH", "expected a legacy OLE XLS file")
        raise FileSecurityError("UNSUPPORTED_LEGACY_XLS", "legacy XLS requires a locked read-only reader")
    if expected == "pdf":
        if path.suffix.casefold() != ".pdf" or not signature.startswith(PDF_SIGNATURE):
            raise FileSecurityError("TYPE_SIGNATURE_MISMATCH", "expected a PDF signature")
        identity_before, digest_before = _capture_source(path)
        try:
            _preflight_pdf(path)
        except FileSecurityError:
            raise
        except OSError as exc:
            raise FileSecurityError("PDF_PREFLIGHT_IO", "PDF cannot be read safely") from exc
        _assert_source_unchanged(path, expected_identity=identity_before, expected_sha256=digest_before)
        return SourceFileReport("pdf", digest_before, path.stat().st_size, "CONTAINER_PREFLIGHT_PASS", False)
    raise FileSecurityError("UNSUPPORTED_EXPECTED_TYPE", "expected file type is not registered")


def escape_spreadsheet_text(value: str) -> str:
    """Neutralize untrusted text while leaving numeric values to numeric writers."""

    if not isinstance(value, str):
        raise TypeError("escape_spreadsheet_text accepts text only")
    if not value or value.startswith("'"):
        return value
    stripped = value.lstrip(" \t\r\n")
    if value[0] in DANGEROUS_TEXT_PREFIXES or (stripped and stripped[0] in "=+-@"):
        return "'" + value
    return value
