"""Manifest-selected Kingdee ZIP bundle reader with explicit member dispositions."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import tempfile
import unicodedata
import zipfile
import zlib
from dataclasses import dataclass, replace
from pathlib import Path, PurePosixPath
from typing import Any, BinaryIO, Dict, Mapping, Optional, Sequence, Tuple

from ..config_io import GovernedConfigError, load_governed_yaml_mapping
from ..inventory import FileIdentity
from ..manifest import SourceSelection
from ..money import MoneyProfile
from ..paths import PathSafetyError, resolve_input_file
from ..security import (
    OLE_SIGNATURE,
    ZIP_SIGNATURES,
    FileSecurityError,
    SecurityProfile,
    preflight_source_file,
)
from .kingdee import (
    KINGDEE_READER_ID,
    KINGDEE_READER_VERSION,
    KingdeeLedgerRecord,
    KingdeeReaderControl,
    KingdeeReaderError,
    KingdeeReaderProfile,
    KingdeeReaderResult,
    read_kingdee_ledger,
)


BUNDLE_PROFILE_BYTES_MAX = 1024 * 1024
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SOURCE_ID_RE = re.compile(r"^src_[0-9a-f]{32}$")
EVIDENCE_REF_RE = re.compile(r"^evidence://sha256/[0-9a-f]{64}$")
ALLOWED_DISPOSITIONS = frozenset({"INCLUDE", "EXCLUDE_QUALIFIED_SCOPE"})
SUPPORTED_WORKBOOK_SUFFIXES = frozenset({".xlsx", ".xls"})
UNSUPPORTED_SPREADSHEET_SUFFIXES = frozenset(
    {".xlsm", ".xlsb", ".xltx", ".xltm", ".ods", ".csv", ".tsv", ".numbers"}
)


def _canonical_digest(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _text(value: Any, field: str, *, optional: bool = False) -> Optional[str]:
    if value is None and optional:
        return None
    if not isinstance(value, str) or not value or value != value.strip() or unicodedata.normalize("NFC", value) != value:
        raise KingdeeBundleError("BUNDLE_PROFILE_SCHEMA", "%s must be nonempty normalized text" % field)
    return value


def _strings(value: Any, field: str) -> Tuple[str, ...]:
    if not isinstance(value, (list, tuple)) or any(not isinstance(item, str) for item in value):
        raise KingdeeBundleError("BUNDLE_PROFILE_SCHEMA", "%s must be a string list" % field)
    result = tuple(value)
    if len(result) != len(set(result)):
        raise KingdeeBundleError("BUNDLE_PROFILE_SCHEMA", "%s must be unique" % field)
    for item in result:
        _text(item, field)
    return result


def _safe_member_path(value: str) -> str:
    _text(value, "member_path")
    if "\\" in value or "\x00" in value or value.startswith("/") or re.match(r"^[A-Za-z]:", value):
        raise KingdeeBundleError("BUNDLE_MEMBER_PATH", "bundle member path is unsafe")
    pure = PurePosixPath(value)
    if any(part in {"", ".", ".."} for part in pure.parts):
        raise KingdeeBundleError("BUNDLE_MEMBER_PATH", "bundle member path has an ambiguous component")
    if pure.suffix.casefold() not in SUPPORTED_WORKBOOK_SUFFIXES:
        raise KingdeeBundleError("BUNDLE_MEMBER_TYPE", "bundle profile may classify only XLSX or legacy XLS workbooks")
    return value


class KingdeeBundleError(ValueError):
    def __init__(self, code: str, message: str, *, member_ref: Optional[str] = None) -> None:
        super().__init__("%s: %s" % (code, message))
        self.code = code
        self.message = message
        self.member_ref = member_ref

    def as_dict(self) -> Dict[str, str]:
        result = {"code": self.code, "message": self.message}
        if self.member_ref is not None:
            result["member_ref"] = self.member_ref
        return result


@dataclass(frozen=True)
class KingdeeBundleMemberProfile:
    member_path: str
    member_sha256: str
    disposition: str
    exclusion_reason_code: Optional[str]
    reader_profile_id: Optional[str]
    evidence_ref: Optional[str]

    @property
    def member_ref(self) -> str:
        return "member_" + _canonical_digest(
            {"member_path": self.member_path, "member_sha256": self.member_sha256}
        )[:32]

    @property
    def suffix(self) -> str:
        return PurePosixPath(self.member_path).suffix.casefold()

    def validate(self, *, active: bool) -> None:
        _safe_member_path(self.member_path)
        if not SHA256_RE.fullmatch(self.member_sha256):
            raise KingdeeBundleError("BUNDLE_PROFILE_SCHEMA", "bundle member digest is invalid")
        if self.disposition not in ALLOWED_DISPOSITIONS:
            raise KingdeeBundleError("BUNDLE_PROFILE_SCHEMA", "bundle member disposition is not registered")
        if self.evidence_ref is not None and not EVIDENCE_REF_RE.fullmatch(self.evidence_ref):
            raise KingdeeBundleError("BUNDLE_PROFILE_EVIDENCE", "bundle member evidence is not hash-bound")
        if active and self.evidence_ref is None:
            raise KingdeeBundleError("BUNDLE_PROFILE_EVIDENCE", "every active bundle member requires evidence")
        if self.disposition == "INCLUDE":
            if self.exclusion_reason_code is not None:
                raise KingdeeBundleError("BUNDLE_PROFILE_SCHEMA", "included member cannot have an exclusion reason")
            if self.suffix == ".xlsx" and self.reader_profile_id is None:
                raise KingdeeBundleError("BUNDLE_PROFILE_SCHEMA", "included XLSX member requires a reader profile")
        else:
            if self.exclusion_reason_code is None or self.reader_profile_id is not None:
                raise KingdeeBundleError(
                    "BUNDLE_PROFILE_SCHEMA",
                    "scope-excluded member requires a reason and cannot claim a business reader",
                )


@dataclass(frozen=True)
class KingdeeBundleProfile:
    profile_id: str
    status: str
    schema_id: str
    bundle_source_sha256: str
    evidence_refs: Tuple[str, ...]
    members: Tuple[KingdeeBundleMemberProfile, ...]
    content_sha256: str

    @property
    def schema_fingerprint(self) -> str:
        return _canonical_digest(
            {
                "profile_id": self.profile_id,
                "schema_id": self.schema_id,
                "bundle_source_sha256": self.bundle_source_sha256,
                "evidence_refs": sorted(self.evidence_refs),
                "members": [
                    {
                        "member_ref": item.member_ref,
                        "disposition": item.disposition,
                        "exclusion_reason_code": item.exclusion_reason_code,
                        "reader_profile_id": item.reader_profile_id,
                        "evidence_ref": item.evidence_ref,
                    }
                    for item in sorted(self.members, key=lambda member: member.member_ref)
                ],
            }
        )

    def validate(self, *, require_active: bool = False) -> None:
        _text(self.profile_id, "profile_id")
        _text(self.schema_id, "schema_id")
        if self.status not in {"ACTIVE", "TEMPLATE_NOT_ACTIVE"}:
            raise KingdeeBundleError("BUNDLE_PROFILE_STATUS", "bundle profile status is not registered")
        if not SHA256_RE.fullmatch(self.bundle_source_sha256) or not SHA256_RE.fullmatch(self.content_sha256):
            raise KingdeeBundleError("BUNDLE_PROFILE_SCHEMA", "bundle profile digest is invalid")
        refs = _strings(self.evidence_refs, "evidence_refs")
        if refs != self.evidence_refs or any(not EVIDENCE_REF_RE.fullmatch(item) for item in refs):
            raise KingdeeBundleError("BUNDLE_PROFILE_EVIDENCE", "bundle evidence references must be hash-bound")
        if not isinstance(self.members, tuple) or not self.members:
            raise KingdeeBundleError("BUNDLE_PROFILE_SCHEMA", "bundle profile requires immutable member decisions")
        active = self.status == "ACTIVE"
        for member in self.members:
            member.validate(active=active)
        portable_paths = [unicodedata.normalize("NFKC", item.member_path).casefold() for item in self.members]
        if len(portable_paths) != len(set(portable_paths)):
            raise KingdeeBundleError("BUNDLE_PROFILE_CONFLICT", "bundle member decisions collide portably")
        if not any(item.disposition == "INCLUDE" for item in self.members):
            raise KingdeeBundleError("BUNDLE_PROFILE_INCOMPLETE", "bundle profile must include at least one approved workbook")
        if active and not refs:
            raise KingdeeBundleError("BUNDLE_PROFILE_EVIDENCE", "active bundle profile requires hash-bound evidence")
        if require_active and not active:
            raise KingdeeBundleError("BUNDLE_PROFILE_NOT_ACTIVE", "an ACTIVE bundle profile is required")

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any], *, content_sha256: Optional[str] = None) -> "KingdeeBundleProfile":
        expected = {
            "schema_version",
            "profile_id",
            "status",
            "schema_id",
            "bundle_source_sha256",
            "evidence_refs",
            "members",
        }
        if not isinstance(raw, Mapping) or set(raw) != expected or raw.get("schema_version") != "kmfa.project_cost.kingdee_bundle_profile.v1":
            raise KingdeeBundleError("BUNDLE_PROFILE_SCHEMA", "bundle profile fields differ from v1")
        raw_members = raw.get("members")
        if not isinstance(raw_members, list):
            raise KingdeeBundleError("BUNDLE_PROFILE_SCHEMA", "bundle members must be a list")
        members = []
        for item in raw_members:
            if not isinstance(item, Mapping) or set(item) != {
                "member_path",
                "member_sha256",
                "disposition",
                "exclusion_reason_code",
                "reader_profile_id",
                "evidence_ref",
            }:
                raise KingdeeBundleError("BUNDLE_PROFILE_SCHEMA", "bundle member fields differ from v1")
            members.append(
                KingdeeBundleMemberProfile(
                    member_path=_safe_member_path(item.get("member_path")),
                    member_sha256=_text(item.get("member_sha256"), "member_sha256") or "",
                    disposition=_text(item.get("disposition"), "disposition") or "",
                    exclusion_reason_code=_text(item.get("exclusion_reason_code"), "exclusion_reason_code", optional=True),
                    reader_profile_id=_text(item.get("reader_profile_id"), "reader_profile_id", optional=True),
                    evidence_ref=_text(item.get("evidence_ref"), "evidence_ref", optional=True),
                )
            )
        profile = cls(
            profile_id=_text(raw.get("profile_id"), "profile_id") or "",
            status=_text(raw.get("status"), "status") or "",
            schema_id=_text(raw.get("schema_id"), "schema_id") or "",
            bundle_source_sha256=_text(raw.get("bundle_source_sha256"), "bundle_source_sha256") or "",
            evidence_refs=_strings(raw.get("evidence_refs"), "evidence_refs"),
            members=tuple(members),
            content_sha256=content_sha256 or _canonical_digest(raw),
        )
        profile.validate()
        return profile

    @classmethod
    def from_yaml(cls, path: Path) -> "KingdeeBundleProfile":
        try:
            raw, file_hash = load_governed_yaml_mapping(path, max_bytes=BUNDLE_PROFILE_BYTES_MAX)
        except GovernedConfigError as exc:
            raise KingdeeBundleError(exc.code, exc.message) from exc
        return cls.from_mapping(raw, content_sha256=file_hash)


@dataclass(frozen=True)
class KingdeeBundleMemberResult:
    member_ref: str
    disposition: str
    exclusion_reason_code: Optional[str]
    security_status: str
    record_count: int
    reader_business_fingerprint: Optional[str]


@dataclass(frozen=True)
class KingdeeBundleControl:
    workbook_member_count: int
    included_member_count: int
    excluded_member_count: int
    xlsx_member_count: int
    legacy_xls_member_count: int
    emitted_record_count: int
    physical_data_row_count: int
    empty_row_count: int
    parse_failure_count: int
    row_conservation_delta: int

    def validate(self) -> None:
        if self.workbook_member_count != self.included_member_count + self.excluded_member_count:
            raise KingdeeBundleError("BUNDLE_MEMBER_CONSERVATION", "bundle member dispositions do not conserve")
        if self.row_conservation_delta != 0:
            raise KingdeeBundleError("BUNDLE_ROW_CONSERVATION", "included workbook rows do not conserve")


@dataclass(frozen=True)
class KingdeeBundleResult:
    records: Tuple[KingdeeLedgerRecord, ...]
    members: Tuple[KingdeeBundleMemberResult, ...]
    control: KingdeeBundleControl
    bundle_source_sha256: str
    bundle_profile_sha256: str
    business_fingerprint: str


def _hash_handle(handle: BinaryIO) -> str:
    handle.seek(0)
    digest = hashlib.sha256()
    for block in iter(lambda: handle.read(1024 * 1024), b""):
        digest.update(block)
    handle.seek(0)
    return digest.hexdigest()


def _validated_empty_scratch(input_root: Path, scratch_root: Path) -> Path:
    scratch = Path(scratch_root)
    if scratch.is_symlink() or not scratch.is_dir():
        raise KingdeeBundleError("BUNDLE_SCRATCH_UNSAFE", "bundle scratch must be an existing real directory")
    try:
        resolved = scratch.resolve(strict=True)
        raw = Path(input_root).resolve(strict=True)
    except OSError as exc:
        raise KingdeeBundleError("BUNDLE_SCRATCH_UNSAFE", "bundle scratch or input root cannot be resolved") from exc
    if resolved == raw or raw in resolved.parents or resolved in raw.parents:
        raise KingdeeBundleError("BUNDLE_SCRATCH_OVERLAP", "bundle scratch cannot overlap the read-only input root")
    try:
        if any(resolved.iterdir()):
            raise KingdeeBundleError("BUNDLE_SCRATCH_NOT_EMPTY", "bundle scratch must be exclusive and empty at run start")
    except OSError as exc:
        raise KingdeeBundleError("BUNDLE_SCRATCH_UNSAFE", "bundle scratch cannot be enumerated") from exc
    return resolved


def _derived_member_selection(
    *,
    scratch: Path,
    temporary: Path,
    container: SourceSelection,
    member: KingdeeBundleMemberProfile,
    reader_profile: KingdeeReaderProfile,
) -> SourceSelection:
    metadata = temporary.stat()
    source_id = "src_" + hashlib.sha256(
        ("kmfa-kingdee-bundle-member-v1\0" + container.source_id + "\0" + member.member_ref).encode("utf-8")
    ).hexdigest()[:32]
    return SourceSelection(
        slot_id="general_ledger",
        source_id=source_id,
        private_relative_path=temporary.relative_to(scratch).as_posix(),
        sha256=member.member_sha256,
        identity=FileIdentity(
            device=metadata.st_dev,
            inode=metadata.st_ino,
            size_bytes=metadata.st_size,
            mtime_ns=metadata.st_mtime_ns,
            link_count=metadata.st_nlink,
        ),
        reader=reader_profile.reader_id,
        reader_version=reader_profile.reader_version,
        logical_source_period=container.logical_source_period,
        schema_id=reader_profile.schema_id,
        schema_fingerprint=reader_profile.schema_fingerprint,
        selection_resolution_ref=container.selection_resolution_ref,
    )


def _copy_member(archive: zipfile.ZipFile, info: zipfile.ZipInfo, scratch: Path, suffix: str) -> Path:
    descriptor, name = tempfile.mkstemp(prefix="kingdee-member-", suffix=suffix, dir=str(scratch))
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as output, archive.open(info) as source:
            for block in iter(lambda: source.read(1024 * 1024), b""):
                output.write(block)
            output.flush()
            os.fsync(output.fileno())
    except Exception:
        if temporary.exists():
            temporary.unlink()
        raise
    return temporary


def read_kingdee_bundle(
    *,
    input_root: Path,
    selection: SourceSelection,
    bundle_profile: KingdeeBundleProfile,
    member_reader_profiles: Mapping[str, KingdeeReaderProfile],
    security_profile: SecurityProfile,
    money_profile: MoneyProfile,
    private_scratch_root: Path,
) -> KingdeeBundleResult:
    """Read every explicitly included workbook; any included legacy XLS blocks the slot."""

    bundle_profile.validate(require_active=True)
    if selection.slot_id != "general_ledger" or selection.reader != KINGDEE_READER_ID or selection.reader_version != KINGDEE_READER_VERSION:
        raise KingdeeBundleError("BUNDLE_SELECTION_READER", "bundle selection is not bound to the Kingdee v2 reader")
    if not SOURCE_ID_RE.fullmatch(selection.source_id):
        raise KingdeeBundleError("BUNDLE_SELECTION_LINEAGE", "bundle selection source reference is invalid")
    if Path(selection.private_relative_path).suffix.casefold() != ".zip":
        raise KingdeeBundleError("BUNDLE_SELECTION_TYPE", "Kingdee bundle source must use .zip")
    if (
        selection.sha256 != bundle_profile.bundle_source_sha256
        or selection.schema_id != bundle_profile.schema_id
        or selection.schema_fingerprint != bundle_profile.schema_fingerprint
    ):
        raise KingdeeBundleError("BUNDLE_SELECTION_DRIFT", "bundle source or schema binding differs from the active profile")
    scratch = _validated_empty_scratch(input_root, private_scratch_root)
    try:
        preflight = preflight_source_file(
            input_root,
            Path(selection.private_relative_path),
            expected_kind="zip",
            profile=security_profile,
            scratch_root=scratch,
        )
    except FileSecurityError as exc:
        raise KingdeeBundleError(exc.code, exc.message) from exc
    if preflight.sha256 != selection.sha256:
        raise KingdeeBundleError("BUNDLE_SOURCE_DIGEST_DRIFT", "bundle preflight digest differs from selection")
    try:
        source_path = resolve_input_file(
            input_root,
            Path(selection.private_relative_path),
            max_bytes=security_profile.source_file_bytes_max,
        )
    except PathSafetyError as exc:
        raise KingdeeBundleError(exc.code, exc.message) from exc
    profile_by_path = {item.member_path: item for item in bundle_profile.members}
    member_results = []
    ledger_records = []
    reader_controls = []
    try:
        with source_path.open("rb") as handle:
            before = os.fstat(handle.fileno())
            selected = selection.identity
            if (
                not stat.S_ISREG(before.st_mode)
                or before.st_nlink != 1
                or before.st_dev != selected.device
                or before.st_ino != selected.inode
                or before.st_size != selected.size_bytes
                or before.st_mtime_ns != selected.mtime_ns
                or before.st_nlink != selected.link_count
            ):
                raise KingdeeBundleError("BUNDLE_SELECTION_IDENTITY_DRIFT", "bundle file identity differs from selection")
            if _hash_handle(handle) != selection.sha256:
                raise KingdeeBundleError("BUNDLE_SOURCE_CHANGED_AFTER_PREFLIGHT", "bundle changed after preflight")
            with zipfile.ZipFile(handle) as archive:
                infos = {info.filename: info for info in archive.infolist() if not info.is_dir()}
                unsupported_spreadsheets = {
                    name
                    for name in infos
                    if PurePosixPath(name).suffix.casefold() in UNSUPPORTED_SPREADSHEET_SUFFIXES
                }
                if unsupported_spreadsheets:
                    raise KingdeeBundleError(
                        "BUNDLE_UNSUPPORTED_SPREADSHEET_MEMBER",
                        "archive contains a spreadsheet member without a locked R5 reader",
                    )
                workbook_paths = {
                    name for name in infos if PurePosixPath(name).suffix.casefold() in SUPPORTED_WORKBOOK_SUFFIXES
                }
                if workbook_paths != set(profile_by_path):
                    raise KingdeeBundleError(
                        "BUNDLE_MEMBER_INVENTORY_DRIFT",
                        "archive workbook members differ from the explicit bundle profile",
                    )
                for member in sorted(bundle_profile.members, key=lambda item: item.member_ref):
                    info = infos[member.member_path]
                    temporary = _copy_member(archive, info, scratch, member.suffix)
                    try:
                        with temporary.open("rb") as extracted:
                            signature = extracted.read(8)
                            extracted.seek(0)
                            member_digest = _hash_handle(extracted)
                        if member_digest != member.member_sha256:
                            raise KingdeeBundleError(
                                "BUNDLE_MEMBER_DIGEST_DRIFT",
                                "archive member digest differs from the explicit profile",
                                member_ref=member.member_ref,
                            )
                        if member.suffix == ".xls":
                            if signature != OLE_SIGNATURE:
                                raise KingdeeBundleError(
                                    "BUNDLE_MEMBER_TYPE_MISMATCH",
                                    "legacy XLS member signature is invalid",
                                    member_ref=member.member_ref,
                                )
                            if member.disposition == "INCLUDE":
                                raise KingdeeBundleError(
                                    "UNSUPPORTED_LEGACY_XLS_SLOT",
                                    "an included entity workbook requires the unavailable locked legacy XLS reader",
                                    member_ref=member.member_ref,
                                )
                            member_results.append(
                                KingdeeBundleMemberResult(
                                    member_ref=member.member_ref,
                                    disposition=member.disposition,
                                    exclusion_reason_code=member.exclusion_reason_code,
                                    security_status="LEGACY_XLS_SIGNATURE_ONLY_EXCLUDED_BY_EVIDENCE",
                                    record_count=0,
                                    reader_business_fingerprint=None,
                                )
                            )
                            continue
                        if signature[:4] not in ZIP_SIGNATURES:
                            raise KingdeeBundleError(
                                "BUNDLE_MEMBER_TYPE_MISMATCH",
                                "XLSX member signature is invalid",
                                member_ref=member.member_ref,
                            )
                        try:
                            member_preflight = preflight_source_file(
                                scratch,
                                Path(temporary.name),
                                expected_kind="xlsx",
                                profile=security_profile,
                            )
                        except FileSecurityError as exc:
                            raise KingdeeBundleError(exc.code, exc.message, member_ref=member.member_ref) from exc
                        if member_preflight.sha256 != member.member_sha256:
                            raise KingdeeBundleError(
                                "BUNDLE_MEMBER_DIGEST_DRIFT",
                                "member security preflight digest differs from its profile",
                                member_ref=member.member_ref,
                            )
                        if member.disposition == "EXCLUDE_QUALIFIED_SCOPE":
                            member_results.append(
                                KingdeeBundleMemberResult(
                                    member_ref=member.member_ref,
                                    disposition=member.disposition,
                                    exclusion_reason_code=member.exclusion_reason_code,
                                    security_status="PREFLIGHT_PASS_EXCLUDED_BY_EVIDENCE",
                                    record_count=0,
                                    reader_business_fingerprint=None,
                                )
                            )
                            continue
                        reader_profile = member_reader_profiles.get(member.reader_profile_id or "")
                        if reader_profile is None or reader_profile.profile_id != member.reader_profile_id:
                            raise KingdeeBundleError(
                                "BUNDLE_MEMBER_READER_PROFILE_MISSING",
                                "included XLSX member lacks its exact active reader profile",
                                member_ref=member.member_ref,
                            )
                        try:
                            reader_result = read_kingdee_ledger(
                                input_root=scratch,
                                selection=_derived_member_selection(
                                    scratch=scratch,
                                    temporary=temporary,
                                    container=selection,
                                    member=member,
                                    reader_profile=reader_profile,
                                ),
                                reader_profile=reader_profile,
                                security_profile=security_profile,
                                money_profile=money_profile,
                            )
                        except KingdeeReaderError as exc:
                            raise KingdeeBundleError(exc.code, exc.message, member_ref=member.member_ref) from exc
                        enriched = tuple(
                            replace(
                                record,
                                container_source_id=selection.source_id,
                                container_sha256=selection.sha256,
                                archive_member_ref=member.member_ref,
                            )
                            for record in reader_result.records
                        )
                        for record in enriched:
                            record.validate()
                        ledger_records.extend(enriched)
                        reader_controls.append(reader_result.control)
                        member_results.append(
                            KingdeeBundleMemberResult(
                                member_ref=member.member_ref,
                                disposition=member.disposition,
                                exclusion_reason_code=None,
                                security_status="PREFLIGHT_AND_READER_PASS",
                                record_count=len(enriched),
                                reader_business_fingerprint=reader_result.business_fingerprint,
                            )
                        )
                    finally:
                        if temporary.exists():
                            temporary.unlink()
            final_hash = _hash_handle(handle)
            after = os.fstat(handle.fileno())
    except KingdeeBundleError:
        raise
    except (OSError, EOFError, RuntimeError, NotImplementedError, zipfile.BadZipFile, zlib.error) as exc:
        raise KingdeeBundleError("BUNDLE_READ_FAILED", "bundle cannot be read safely") from exc
    identity_before = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_nlink)
    identity_after = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_nlink)
    if final_hash != selection.sha256 or identity_after != identity_before:
        raise KingdeeBundleError("BUNDLE_SOURCE_CHANGED_DURING_PARSE", "bundle changed during member processing")
    control = KingdeeBundleControl(
        workbook_member_count=len(bundle_profile.members),
        included_member_count=sum(item.disposition == "INCLUDE" for item in bundle_profile.members),
        excluded_member_count=sum(item.disposition == "EXCLUDE_QUALIFIED_SCOPE" for item in bundle_profile.members),
        xlsx_member_count=sum(item.suffix == ".xlsx" for item in bundle_profile.members),
        legacy_xls_member_count=sum(item.suffix == ".xls" for item in bundle_profile.members),
        emitted_record_count=len(ledger_records),
        physical_data_row_count=sum(item.physical_data_row_count for item in reader_controls),
        empty_row_count=sum(item.empty_row_count for item in reader_controls),
        parse_failure_count=sum(item.parse_failure_count for item in reader_controls),
        row_conservation_delta=sum(item.row_conservation_delta for item in reader_controls),
    )
    control.validate()
    business_fingerprint = _canonical_digest(
        {
            "bundle_profile_sha256": bundle_profile.content_sha256,
            "bundle_schema_fingerprint": bundle_profile.schema_fingerprint,
            "included_reader_fingerprints": sorted(
                item.reader_business_fingerprint for item in member_results if item.reader_business_fingerprint
            ),
            "member_dispositions": sorted(
                (item.member_ref, item.disposition, item.exclusion_reason_code) for item in member_results
            ),
        }
    )
    return KingdeeBundleResult(
        records=tuple(ledger_records),
        members=tuple(sorted(member_results, key=lambda item: item.member_ref)),
        control=control,
        bundle_source_sha256=selection.sha256,
        bundle_profile_sha256=bundle_profile.content_sha256,
        business_fingerprint=business_fingerprint,
    )


def public_bundle_summary(result: KingdeeBundleResult) -> Dict[str, Any]:
    result.control.validate()
    return {
        "schema_version": "kmfa.project_cost.public_kingdee_bundle_summary.v1",
        "reader_id": KINGDEE_READER_ID,
        "reader_version": KINGDEE_READER_VERSION,
        "status": "BUNDLE_READER_PASS",
        "workbook_member_count": result.control.workbook_member_count,
        "included_member_count": result.control.included_member_count,
        "excluded_member_count": result.control.excluded_member_count,
        "xlsx_member_count": result.control.xlsx_member_count,
        "legacy_xls_member_count": result.control.legacy_xls_member_count,
        "emitted_record_count": result.control.emitted_record_count,
        "physical_data_row_count": result.control.physical_data_row_count,
        "empty_row_count": result.control.empty_row_count,
        "parse_failure_count": result.control.parse_failure_count,
        "row_conservation_delta": result.control.row_conservation_delta,
    }
