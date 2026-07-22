"""Fail-closed current-source reconstruction preflight and blocked production run.

This module is deliberately independent from reference replay.  It verifies a
private current-source contract, checks current metadata and selected source
digests, then hands an explicit input-sufficiency result to the normal
generation boundary.  It never loads an expected-block contract; that belongs
to the separate regression harness.
"""

from __future__ import annotations

import hashlib
import json
import re
import stat
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Tuple

from .generation import GeneratedRun, RunGenerationRequest, SourceLineage, generate_run_artifacts
from .input_gate import InputSufficiencyReport, RequirementItem
from .inventory import InventoryEntry, InventoryError, scan_inventory_metadata, verify_source_file
from .security import SecurityProfile
from .statuses import CalculationStatus, GenerationStatus


SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SOURCE_ID_RE = re.compile(r"^src_[0-9a-f]{32}$")
SLOT_ID_RE = re.compile(r"^[a-z][a-z0-9_]{1,63}$")
RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
CONTRACT_BYTES_MAX = 2 * 1024 * 1024
CURRENT_METRICS = ("COST_POSTED_ACTUAL",)
CURRENT_BASIS_IDS = ("GL_RECOGNIZED_COGS", "JOB_COST_INCURRED")
PROHIBITED_CALCULATE_SLOT_IDS = frozenset(
    {
        "reference_reports",
        "reference_report",
        "reference_pdf",
        "reference_baseline",
        "replay_baseline",
    }
)


@dataclass(frozen=True)
class RequirementSpec:
    expected_source_or_policy: str
    status_blockers: Mapping[str, str]


CURRENT_REQUIREMENT_SPECS: Mapping[str, RequirementSpec] = {
    "CURRENT_INPUT_MANIFEST_V3": RequirementSpec(
        "v3 explicit private manifest with source/schema/digest locks",
        {
            "MISSING": "CURRENT_INPUT_MANIFEST_V3_MISSING",
            "CONFLICT": "CURRENT_INPUT_MANIFEST_V3_CONFLICT",
            "UNSAFE": "CURRENT_INPUT_MANIFEST_V3_UNSAFE",
        },
    ),
    "PROJECT_IDENTITY_EVIDENCE": RequirementSpec(
        "qualified legal-entity/project/WBS identity evidence",
        {
            "MISSING": "PROJECT_IDENTITY_EVIDENCE_MISSING",
            "CONFLICT": "PROJECT_IDENTITY_EVIDENCE_CONFLICT",
            "UNSAFE": "PROJECT_IDENTITY_EVIDENCE_UNSAFE",
        },
    ),
    "KINGDEE_READER_PROFILE": RequirementSpec(
        "active hash-bound Kingdee reader profile",
        {
            "MISSING": "KINGDEE_READER_PROFILE_MISSING",
            "CONFLICT": "KINGDEE_READER_PROFILE_CONFLICT",
            "UNSAFE": "KINGDEE_READER_PROFILE_UNSAFE",
        },
    ),
    "ACCOUNTING_BASIS_POLICY": RequirementSpec(
        "effective 5001/6401/WIP bridge and period-close policy",
        {
            "MISSING": "ACCOUNTING_BASIS_POLICY_MISSING",
            "CONFLICT": "ACCOUNTING_BASIS_POLICY_CONFLICT",
            "UNSAFE": "ACCOUNTING_BASIS_POLICY_UNSAFE",
        },
    ),
    "PAYROLL_AND_TIME_SOURCE": RequirementSpec(
        "approved payroll component source and qualified project time/day source",
        {
            "MISSING": "PAYROLL_AND_TIME_SOURCE_MISSING",
            "CONFLICT": "PAYROLL_AND_TIME_SOURCE_CONFLICT",
            "UNSAFE": "PAYROLL_AND_TIME_SOURCE_UNSAFE",
        },
    ),
    "FULLY_LOADED_PAYROLL_POLICY": RequirementSpec(
        "effective fully loaded employer-cost allocation policy",
        {
            "MISSING": "FULLY_LOADED_PAYROLL_POLICY_MISSING",
            "CONFLICT": "FULLY_LOADED_PAYROLL_POLICY_CONFLICT",
            "UNSAFE": "FULLY_LOADED_PAYROLL_POLICY_UNSAFE",
        },
    ),
    "PROJECT_TAX_POLICY_OR_DIRECT_LEDGER": RequirementSpec(
        "approved project-tax policy or directly attributable governed tax ledger",
        {
            "MISSING": "PROJECT_TAX_POLICY_OR_DIRECT_LEDGER_MISSING",
            "CONFLICT": "PROJECT_TAX_POLICY_OR_DIRECT_LEDGER_CONFLICT",
            "UNSAFE": "PROJECT_TAX_POLICY_OR_DIRECT_LEDGER_UNSAFE",
        },
    ),
    "CAPITAL_INTEREST_POLICY": RequirementSpec(
        "effective capital-occupation interest formula, basis and rate evidence",
        {
            "MISSING": "CAPITAL_INTEREST_POLICY_MISSING",
            "CONFLICT": "CAPITAL_INTEREST_POLICY_CONFLICT",
            "UNSAFE": "CAPITAL_INTEREST_POLICY_UNSAFE",
        },
    ),
    "PAYMENT_PROJECT_MAPPING": RequirementSpec(
        "deterministic approved payment-to-project mapping evidence",
        {
            "MISSING": "PAYMENT_PROJECT_MAPPING_MISSING",
            "CONFLICT": "PAYMENT_PROJECT_MAPPING_CONFLICT",
            "UNSAFE": "PAYMENT_PROJECT_MAPPING_UNSAFE",
        },
    ),
}


class CurrentReconstructionError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__("%s: %s" % (code, message))
        self.code = code
        self.message = message


@dataclass(frozen=True)
class ContractSource:
    slot_id: str
    source_id: str
    private_relative_path: str
    sha256: str


@dataclass(frozen=True)
class ContractRequirement:
    requirement_id: str
    observed_status: str
    evidence_ref: Optional[str]


@dataclass(frozen=True)
class CurrentSourceContract:
    contract_id: str
    input_root: str
    as_of: str
    project_count: int
    metadata_fingerprint: str
    entry_count: int
    total_size_bytes: int
    unsafe_entry_count: int
    task_pack_manifest_sha256: str
    drift_review_sha256: str
    selected_sources: Tuple[ContractSource, ...]
    requirements: Tuple[ContractRequirement, ...]
    calculate_boundary: Mapping[str, bool]
    content_sha256: str

    def requirement_map(self) -> Dict[str, ContractRequirement]:
        return {item.requirement_id: item for item in self.requirements}


@dataclass(frozen=True)
class CurrentReconstructionRequest:
    run_id: str
    as_of: str
    input_root: Path
    contract_path: Path
    contract_sha256: str
    output_dir: Path
    module_root: Path

    def validate(self) -> None:
        if not RUN_ID_RE.fullmatch(self.run_id):
            raise CurrentReconstructionError("RUN_ID_INVALID", "run ID must be portable and non-sensitive")
        try:
            date.fromisoformat(self.as_of)
        except (TypeError, ValueError) as exc:
            raise CurrentReconstructionError("AS_OF_INVALID", "as-of must be a canonical ISO date") from exc
        if not SHA256_RE.fullmatch(self.contract_sha256):
            raise CurrentReconstructionError("CONTRACT_HASH_INVALID", "contract SHA256 must be lowercase hex")
        input_root = Path(self.input_root)
        if input_root.is_symlink() or not input_root.is_dir():
            raise CurrentReconstructionError("INPUT_ROOT_INVALID", "input root must be an existing non-symlink directory")
        output = Path(self.output_dir)
        if not output.is_absolute() or output.exists() or not output.parent.is_dir():
            raise CurrentReconstructionError("OUTPUT_DIR_INVALID", "output must be a new absolute path with an existing parent")
        try:
            resolved_input = input_root.resolve(strict=True)
            resolved_output_parent = output.parent.resolve(strict=True)
            if resolved_output_parent == resolved_input or resolved_input in resolved_output_parent.parents:
                raise CurrentReconstructionError("OUTPUT_OVERLAPS_INPUT", "output must remain outside the raw input root")
        except OSError as exc:
            raise CurrentReconstructionError("PATH_RESOLUTION_FAILED", "input/output roots cannot be resolved") from exc
        module = Path(self.module_root)
        if not module.is_dir() or not (module / "config" / "security_limits.yml").is_file():
            raise CurrentReconstructionError("MODULE_ROOT_INVALID", "module root is missing governed configuration")


@dataclass(frozen=True)
class CurrentReconstructionRun:
    generated: GeneratedRun
    blocker_codes: Tuple[str, ...]
    contract_sha256: str
    metadata_fingerprint: str

    def locator_text(self) -> str:
        return self.generated.locator_text()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _stable_json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def metadata_fingerprint(entries: Iterable[InventoryEntry]) -> str:
    """Fingerprint exact current metadata without opening any source body."""

    rows = []
    for entry in sorted(entries, key=lambda item: item.source_id):
        # Full private preparation upgrades SAFE_METADATA to VERIFIED after
        # hashing.  The production preflight intentionally remains metadata
        # first; normalize the equivalent safe states so the fingerprint binds
        # file identity rather than the preparation phase label.
        normalized_status = "SAFE_METADATA" if entry.status == "VERIFIED" else entry.status
        rows.append(
            {
                "source_id": entry.source_id,
                "entry_kind": entry.entry_kind,
                "status": normalized_status,
                "device": entry.identity.device,
                "inode": entry.identity.inode,
                "size_bytes": entry.identity.size_bytes,
                "mtime_ns": entry.identity.mtime_ns,
                "link_count": entry.identity.link_count,
                "error_code": None if normalized_status == "SAFE_METADATA" else entry.error_code,
            }
        )
    return _sha256_bytes(_stable_json_bytes(rows))


def _read_contract_bytes(path: Path, expected_sha256: str) -> bytes:
    value = Path(path)
    try:
        metadata = value.lstat()
    except OSError as exc:
        raise CurrentReconstructionError("CONTRACT_UNAVAILABLE", "current-source contract cannot be accessed") from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        raise CurrentReconstructionError("CONTRACT_PATH_UNSAFE", "contract must be a single-link regular file")
    if metadata.st_size > CONTRACT_BYTES_MAX:
        raise CurrentReconstructionError("CONTRACT_TOO_LARGE", "contract exceeds its metadata size ceiling")
    try:
        data = value.read_bytes()
    except OSError as exc:
        raise CurrentReconstructionError("CONTRACT_UNREADABLE", "current-source contract cannot be read") from exc
    if _sha256_bytes(data) != expected_sha256:
        raise CurrentReconstructionError("CURRENT_SOURCE_CONTRACT_HASH_DRIFT", "contract digest differs from the sealed binding")
    return data


def _required_text(mapping: Mapping[str, Any], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise CurrentReconstructionError("CONTRACT_FIELD_INVALID", "%s must be nonempty text" % key)
    return value.strip()


def _required_sha(mapping: Mapping[str, Any], key: str) -> str:
    value = _required_text(mapping, key)
    if not SHA256_RE.fullmatch(value):
        raise CurrentReconstructionError("CONTRACT_FIELD_INVALID", "%s must be lowercase SHA256" % key)
    return value


def load_current_source_contract(path: Path, expected_sha256: str) -> CurrentSourceContract:
    data = _read_contract_bytes(path, expected_sha256)
    try:
        raw = json.loads(data)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise CurrentReconstructionError("CONTRACT_PARSE", "current-source contract is not valid UTF-8 JSON") from exc
    expected_top = {
        "schema_version",
        "classification",
        "contract_id",
        "input_root",
        "as_of",
        "scope",
        "source_snapshot",
        "selected_sources",
        "evidence_requirements",
        "calculate_source_boundary",
    }
    if not isinstance(raw, dict) or set(raw) != expected_top:
        raise CurrentReconstructionError("CONTRACT_SCHEMA_DRIFT", "current-source contract fields drifted")
    if raw.get("schema_version") != "kmfa.project_cost.current_source_contract.private.v1":
        raise CurrentReconstructionError("CONTRACT_SCHEMA_DRIFT", "current-source contract schema is unsupported")
    if raw.get("classification") != "PRIVATE_RUNTIME_DO_NOT_COMMIT":
        raise CurrentReconstructionError("CONTRACT_CLASSIFICATION_INVALID", "contract must remain private runtime data")
    scope = raw.get("scope")
    snapshot = raw.get("source_snapshot")
    boundary = raw.get("calculate_source_boundary")
    if not isinstance(scope, dict) or set(scope) != {"project_count", "requested_metrics", "requested_basis_ids"}:
        raise CurrentReconstructionError("CONTRACT_SCOPE_INVALID", "current-source scope fields drifted")
    if scope.get("requested_metrics") != list(CURRENT_METRICS) or sorted(scope.get("requested_basis_ids", [])) != list(CURRENT_BASIS_IDS):
        raise CurrentReconstructionError("CONTRACT_SCOPE_INVALID", "current regression must cover both actual-cost bases")
    project_count = scope.get("project_count")
    if type(project_count) is not int or project_count <= 0:
        raise CurrentReconstructionError("CONTRACT_SCOPE_INVALID", "project count must be a positive integer")
    expected_snapshot = {
        "metadata_fingerprint",
        "entry_count",
        "total_size_bytes",
        "unsafe_entry_count",
        "task_pack_manifest_sha256",
        "drift_review_sha256",
        "drift_classification",
        "snapshot_overwritten",
    }
    if not isinstance(snapshot, dict) or set(snapshot) != expected_snapshot:
        raise CurrentReconstructionError("CONTRACT_SNAPSHOT_INVALID", "source snapshot fields drifted")
    if snapshot.get("drift_classification") != "OUT_OF_SCOPE_INVENTORY_DRIFT_REVIEWED" or snapshot.get("snapshot_overwritten") is not False:
        raise CurrentReconstructionError("SOURCE_DRIFT_REVIEW_REQUIRED", "source drift must be reviewed without snapshot overwrite")
    for key in ("entry_count", "total_size_bytes", "unsafe_entry_count"):
        if type(snapshot.get(key)) is not int or snapshot[key] < 0:
            raise CurrentReconstructionError("CONTRACT_SNAPSHOT_INVALID", "%s must be a nonnegative integer" % key)
    expected_boundary = {"baseline_values_allowed", "report_line_items_allowed", "replay_adapters_allowed"}
    if (
        not isinstance(boundary, dict)
        or set(boundary) != expected_boundary
        or any(value is not False for value in boundary.values())
    ):
        raise CurrentReconstructionError("CALCULATE_SOURCE_BOUNDARY_RELAXED", "calculate cannot access replay/reference facts")
    source_rows = raw.get("selected_sources")
    if not isinstance(source_rows, list):
        raise CurrentReconstructionError("CONTRACT_SOURCE_INVALID", "selected_sources must be a list")
    sources = []
    for row in source_rows:
        if not isinstance(row, dict) or set(row) != {"slot_id", "source_id", "private_relative_path", "sha256"}:
            raise CurrentReconstructionError("CONTRACT_SOURCE_INVALID", "selected source fields drifted")
        slot_id = _required_text(row, "slot_id")
        source_id = _required_text(row, "source_id")
        relative = _required_text(row, "private_relative_path")
        sha256 = _required_sha(row, "sha256")
        if not SLOT_ID_RE.fullmatch(slot_id) or slot_id in PROHIBITED_CALCULATE_SLOT_IDS:
            raise CurrentReconstructionError("PROHIBITED_CALCULATE_SOURCE", "selected source belongs to a calculate-prohibited slot")
        if not SOURCE_ID_RE.fullmatch(source_id) or Path(relative).is_absolute() or ".." in Path(relative).parts or "\\" in relative:
            raise CurrentReconstructionError("CONTRACT_SOURCE_INVALID", "selected source locator or ID is unsafe")
        if relative.casefold().endswith(".pdf"):
            raise CurrentReconstructionError("PROHIBITED_CALCULATE_SOURCE", "PDF report sources cannot enter calculate")
        sources.append(ContractSource(slot_id, source_id, relative, sha256))
    if len({item.source_id for item in sources}) != len(sources):
        raise CurrentReconstructionError("CONTRACT_SOURCE_DUPLICATE", "selected source IDs must be unique")
    if not sources:
        raise CurrentReconstructionError("CONTRACT_SOURCE_EMPTY", "current-source contract must bind calculate sources")
    requirement_rows = raw.get("evidence_requirements")
    if not isinstance(requirement_rows, list):
        raise CurrentReconstructionError("CONTRACT_REQUIREMENT_INVALID", "evidence requirements must be a list")
    requirements = []
    for row in requirement_rows:
        if not isinstance(row, dict) or set(row) != {"requirement_id", "observed_status", "evidence_ref"}:
            raise CurrentReconstructionError("CONTRACT_REQUIREMENT_INVALID", "requirement fields drifted")
        requirement_id = _required_text(row, "requirement_id")
        status_value = _required_text(row, "observed_status")
        evidence_ref = row.get("evidence_ref")
        if requirement_id not in CURRENT_REQUIREMENT_SPECS or status_value not in {"PRESENT", "MISSING", "CONFLICT", "UNSAFE"}:
            raise CurrentReconstructionError("CONTRACT_REQUIREMENT_INVALID", "requirement ID or status is unsupported")
        if evidence_ref is not None and (not isinstance(evidence_ref, str) or not evidence_ref.strip()):
            raise CurrentReconstructionError("CONTRACT_REQUIREMENT_INVALID", "evidence_ref must be null or nonempty text")
        requirements.append(ContractRequirement(requirement_id, status_value, evidence_ref.strip() if evidence_ref else None))
    if {item.requirement_id for item in requirements} != set(CURRENT_REQUIREMENT_SPECS) or len(requirements) != len(CURRENT_REQUIREMENT_SPECS):
        raise CurrentReconstructionError("CONTRACT_REQUIREMENT_SET_DRIFT", "current-source requirement set is incomplete or duplicated")
    as_of = _required_text(raw, "as_of")
    try:
        date.fromisoformat(as_of)
    except ValueError as exc:
        raise CurrentReconstructionError("CONTRACT_AS_OF_INVALID", "contract as-of must be canonical ISO") from exc
    return CurrentSourceContract(
        contract_id=_required_text(raw, "contract_id"),
        input_root=_required_text(raw, "input_root"),
        as_of=as_of,
        project_count=project_count,
        metadata_fingerprint=_required_sha(snapshot, "metadata_fingerprint"),
        entry_count=snapshot["entry_count"],
        total_size_bytes=snapshot["total_size_bytes"],
        unsafe_entry_count=snapshot["unsafe_entry_count"],
        task_pack_manifest_sha256=_required_sha(snapshot, "task_pack_manifest_sha256"),
        drift_review_sha256=_required_sha(snapshot, "drift_review_sha256"),
        selected_sources=tuple(sorted(sources, key=lambda item: (item.slot_id, item.source_id))),
        requirements=tuple(sorted(requirements, key=lambda item: item.requirement_id)),
        calculate_boundary=dict(boundary),
        content_sha256=_sha256_bytes(data),
    )


def blocker_codes_for_requirements(requirements: Sequence[ContractRequirement]) -> Tuple[str, ...]:
    blockers = []
    for item in requirements:
        if item.observed_status == "PRESENT":
            continue
        blocker = CURRENT_REQUIREMENT_SPECS[item.requirement_id].status_blockers.get(item.observed_status)
        if blocker is None:
            raise CurrentReconstructionError("REQUIREMENT_STATUS_UNMAPPED", "blocking requirement status has no public code")
        blockers.append(blocker)
    return tuple(sorted(blockers))


def _report_item(
    requirement_id: str,
    *,
    observed_status: str,
    expected: str,
    evidence_ref: Optional[str],
) -> RequirementItem:
    return RequirementItem(
        requirement_id=requirement_id,
        classification="NON_WAIVABLE",
        observed_status=observed_status,
        allowed_resolutions=("SUPPLIED", "QUALIFIED_ALTERNATE_EVIDENCE", "SCOPE_REDUCED", "BLOCKED"),
        applies_to_metrics=CURRENT_METRICS,
        expected_source_or_policy=expected,
        evidence_ref=evidence_ref,
    )


def _request_hash(
    request: CurrentReconstructionRequest,
    *,
    contract_sha256: str,
    observed_metadata_fingerprint: str,
) -> str:
    payload = {
        "run_id": request.run_id,
        "mode": "calculate",
        "as_of": request.as_of,
        "requested_metrics": list(CURRENT_METRICS),
        "requested_basis_ids": list(CURRENT_BASIS_IDS),
        "input_root": str(Path(request.input_root).resolve(strict=True)),
        "output_dir": str(Path(request.output_dir)),
        "current_source_contract_sha256": contract_sha256,
        "observed_metadata_fingerprint": observed_metadata_fingerprint,
    }
    return _sha256_bytes(_stable_json_bytes(payload))


def recompute_current_request_hash(
    *,
    run_id: str,
    as_of: str,
    input_root: Path,
    output_dir: Path,
    contract_sha256: str,
    observed_metadata_fingerprint: str,
) -> str:
    request = CurrentReconstructionRequest(
        run_id=run_id,
        as_of=as_of,
        input_root=input_root,
        contract_path=Path("unused"),
        contract_sha256=contract_sha256,
        output_dir=output_dir,
        module_root=Path("unused"),
    )
    return _request_hash(
        request,
        contract_sha256=contract_sha256,
        observed_metadata_fingerprint=observed_metadata_fingerprint,
    )


def _config_hash(module_root: Path) -> str:
    digest = hashlib.sha256()
    for relative in (
        "config/input_requirements.yml",
        "config/metric_catalog.yml",
        "config/security_limits.yml",
        "config/status_codes.yml",
    ):
        path = Path(module_root) / relative
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _version(module_root: Path) -> str:
    value = (Path(module_root) / "VERSION").read_text(encoding="utf-8").strip()
    if not value:
        raise CurrentReconstructionError("VERSION_UNAVAILABLE", "module version is empty")
    return value


def run_current_source_reconstruction(request: CurrentReconstructionRequest) -> CurrentReconstructionRun:
    """Run the production current-source gate; a normal business block is returned, not hidden."""

    request.validate()
    contract = load_current_source_contract(request.contract_path, request.contract_sha256)
    resolved_input = Path(request.input_root).resolve(strict=True)
    try:
        contract_root = Path(contract.input_root).resolve(strict=True)
    except OSError as exc:
        raise CurrentReconstructionError("CONTRACT_INPUT_ROOT_UNAVAILABLE", "contract input root is unavailable") from exc
    if contract_root != resolved_input:
        raise CurrentReconstructionError("CONTRACT_INPUT_ROOT_CONFLICT", "run input root differs from the sealed current-source contract")
    if contract.as_of != request.as_of:
        raise CurrentReconstructionError("CONTRACT_AS_OF_CONFLICT", "run as-of differs from the sealed current-source contract")

    try:
        inventory = scan_inventory_metadata(resolved_input)
    except InventoryError as exc:
        raise CurrentReconstructionError(exc.code, exc.message) from exc
    observed_fingerprint = metadata_fingerprint(inventory)
    observed_size = sum(item.identity.size_bytes for item in inventory)
    observed_unsafe = sum(item.status == "UNSAFE" for item in inventory)
    dynamic_requirements = []
    metadata_exact = (
        observed_fingerprint == contract.metadata_fingerprint
        and len(inventory) == contract.entry_count
        and observed_size == contract.total_size_bytes
        and observed_unsafe == contract.unsafe_entry_count
    )
    dynamic_requirements.append(
        _report_item(
            "CURRENT_SOURCE_METADATA_FINGERPRINT" if metadata_exact else "CURRENT_SOURCE_METADATA_DRIFT_REVIEW_REQUIRED",
            observed_status="PRESENT" if metadata_exact else "CONFLICT",
            expected="exact reviewed current metadata snapshot; drift requires a new review and contract",
            evidence_ref="current-contract:metadata" if metadata_exact else None,
        )
    )

    entry_map = {item.source_id: item for item in inventory}
    verified_sources = []
    digest_drift = False
    for locked in contract.selected_sources:
        entry = entry_map.get(locked.source_id)
        if entry is None or entry.relative_path != locked.private_relative_path:
            digest_drift = True
            continue
        try:
            verified = verify_source_file(resolved_input, entry)
        except InventoryError:
            digest_drift = True
            continue
        if verified.sha256 != locked.sha256:
            digest_drift = True
            continue
        verified_sources.append((locked, verified))
    digest_exact = not digest_drift and len(verified_sources) == len(contract.selected_sources)
    dynamic_requirements.append(
        _report_item(
            "CURRENT_SELECTED_SOURCE_DIGEST_LOCKS" if digest_exact else "CURRENT_SELECTED_SOURCE_HASH_DRIFT",
            observed_status="PRESENT" if digest_exact else "CONFLICT",
            expected="every selected calculate source matches its full SHA256 lock",
            evidence_ref="current-contract:selected-source-locks" if digest_exact else None,
        )
    )
    dynamic_requirements.extend(
        (
            _report_item(
                "CURRENT_SOURCE_CONTRACT",
                observed_status="PRESENT",
                expected="hash-bound private current-source contract",
                evidence_ref="current-contract:%s" % contract.contract_id,
            ),
            _report_item(
                "ACTUAL_COST_BASIS_PAIR",
                observed_status="PRESENT",
                expected="JOB_COST_INCURRED and GL_RECOGNIZED_COGS requested separately",
                evidence_ref="request:both-cost-bases",
            ),
            _report_item(
                "CALCULATE_DATA_FLOW_ISOLATION",
                observed_status="NOT_IN_SCOPE",
                expected="baseline values, report line items and replay adapters unavailable to calculate",
                evidence_ref="contract:calculate-source-boundary",
            ),
        )
    )

    contract_items = []
    contract_blockers = blocker_codes_for_requirements(contract.requirements)
    for item in contract.requirements:
        spec = CURRENT_REQUIREMENT_SPECS[item.requirement_id]
        report_id = (
            item.requirement_id
            if item.observed_status == "PRESENT"
            else spec.status_blockers[item.observed_status]
        )
        contract_items.append(
            _report_item(
                report_id,
                observed_status=item.observed_status,
                expected=spec.expected_source_or_policy,
                evidence_ref=item.evidence_ref,
            )
        )
    all_items = tuple(sorted((*dynamic_requirements, *contract_items), key=lambda item: item.requirement_id))
    dynamic_blockers = tuple(
        sorted(
            item.requirement_id
            for item in dynamic_requirements
            if item.observed_status not in {"PRESENT", "NOT_IN_SCOPE"}
        )
    )
    blocker_codes = tuple(sorted((*contract_blockers, *dynamic_blockers)))
    if not blocker_codes:
        raise CurrentReconstructionError(
            "CURRENT_R11_EXPECTATION_STALE",
            "current evidence is no longer blocked; retire this regression contract and run the governed calculate pipeline",
        )
    has_conflict_or_unsafe = any(item.observed_status in {"CONFLICT", "UNSAFE"} for item in all_items)
    overall_status = "BLOCKED_NON_WAIVABLE" if has_conflict_or_unsafe else "NEEDS_SUPPLEMENT"
    request_hash = _request_hash(
        request,
        contract_sha256=contract.content_sha256,
        observed_metadata_fingerprint=observed_fingerprint,
    )
    report = InputSufficiencyReport(
        run_id=request.run_id,
        request_hash=request_hash,
        mode="calculate",
        requested_metrics=CURRENT_METRICS,
        requested_basis_ids=CURRENT_BASIS_IDS,
        output_dir=str(Path(request.output_dir)),
        overall_status=overall_status,
        items=all_items,
        user_action_required=True,
        resolution_ref=None,
    )
    lineage = tuple(
        SourceLineage(
            source_slot_id=locked.slot_id,
            opaque_source_id=locked.source_id,
            source_sha256=verified.sha256,
            reader_version="DIGEST_ONLY_READER_NOT_ACTIVATED",
            schema_fingerprint=_sha256_bytes(
                ("kmfa.current-source.schema-not-evaluated.v1\0" + locked.slot_id).encode("utf-8")
            ),
            logical_source_period=request.as_of,
        )
        for locked, verified in verified_sources
    )
    generation_request = RunGenerationRequest(
        run_id=request.run_id,
        request_hash=request_hash,
        mode="calculate",
        as_of=request.as_of,
        output_dir=Path(request.output_dir),
        input_report=report,
        metric_batch=None,
        facts=(),
        source_lineage=lineage,
        review_tasks=(),
        security_profile=SecurityProfile.from_yaml(Path(request.module_root) / "config" / "security_limits.yml"),
        workbook_runtime=None,
        code_version=_version(request.module_root),
        config_hash=_config_hash(request.module_root),
    )
    generated = generate_run_artifacts(generation_request)
    if generated.status_planes.calculation_status != CalculationStatus.BLOCKED_SOURCE:
        raise CurrentReconstructionError("CURRENT_CALCULATION_NOT_BLOCKED", "current-source gate did not expose BLOCKED_SOURCE")
    if generated.status_planes.generation_status != GenerationStatus.BLOCKED_DIAGNOSTICS_GENERATED:
        raise CurrentReconstructionError("CURRENT_GENERATION_STATUS_INVALID", "current-source block produced a final-looking status")
    try:
        diagnostics = json.loads(generated.primary_output.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CurrentReconstructionError("CURRENT_DIAGNOSTICS_UNREADABLE", "published blocked diagnostics cannot be verified") from exc
    if tuple(diagnostics.get("blocker_codes", ())) != blocker_codes:
        raise CurrentReconstructionError("CURRENT_BLOCKER_SET_DRIFT", "published blocker set differs from the independently derived set")
    return CurrentReconstructionRun(
        generated=generated,
        blocker_codes=blocker_codes,
        contract_sha256=contract.content_sha256,
        metadata_fingerprint=observed_fingerprint,
    )
