from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Dict, Iterable, Mapping, Optional

import yaml

from project_cost_table.inventory import source_id_for_relative_path


SCHEMA_FINGERPRINT = "1" * 64


def write_source(root: Path, relative_path: str, content: bytes = b"synthetic-public-test") -> Path:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def slot_mapping(relative_path: str, *, required_for: Iterable[str] = ("calculate",)) -> Dict[str, object]:
    return {
        "reader": "synthetic_reader_v1",
        "reader_version": "1.0.0",
        "missing_behavior": "BLOCKED_SOURCE",
        "required_for": list(required_for),
        "private_patterns": [relative_path],
        "logical_source_period": "2000-01",
        "expected_schema_id": "schema.synthetic.v1",
        "expected_schema_fingerprint": SCHEMA_FINGERPRINT,
        "selected_source_id": source_id_for_relative_path(relative_path),
        "selected_sha256": None,
        "selected_sources": [],
        "selection_resolution_ref": None,
    }


def manifest_mapping(
    raw_root: Path,
    slot_files: Mapping[str, str],
    *,
    metric_id: str = "COST_PAID",
    accounting_basis_id: str = "CASH_VERIFIED",
    requested_basis_ids: Optional[Iterable[str]] = None,
) -> Dict[str, object]:
    slots = {}
    for slot_id, relative_path in slot_files.items():
        slot = slot_mapping(relative_path)
        slot["selected_sha256"] = hashlib.sha256((raw_root / relative_path).read_bytes()).hexdigest()
        slots[slot_id] = slot
    return {
        "schema_version": "kmfa.project_cost.input_manifest.v3",
        "manifest_id": "MANIFEST-SYNTHETIC-R3",
        "input_root": str(raw_root.resolve()),
        "read_only": True,
        "base_currency": "CNY",
        "as_of": "2000-01-31",
        "project_selector": {"project_code": "SYNTHETIC-PROJECT"},
        "metric_id": metric_id,
        "accounting_basis_id": accounting_basis_id,
        "requested_basis_ids": list(requested_basis_ids or [accounting_basis_id]),
        "security_profile_id": "LOCAL-FILE-SECURITY-V1",
        "selection_policy": {
            "explicit_private_manifest_required": True,
            "fail_on_multiple_without_decision": True,
            "fail_on_missing_required": True,
            "full_digest_required_for_final_run": True,
            "mtime_is_authority": False,
            "never_mutate_sources": True,
            "input_sufficiency_required_before_source_body_read": True,
        },
        "slots": slots,
    }


def write_manifest(path: Path, mapping: Mapping[str, object]) -> Path:
    path.write_text(yaml.safe_dump(dict(mapping), allow_unicode=True, sort_keys=False), encoding="utf-8")
    return path


def operation_request_mapping(
    *,
    run_id: str,
    mode: str,
    output_dir: Path,
    raw_root: Optional[Path] = None,
    manifest_path: Optional[Path] = None,
    metrics: Iterable[str] = (),
    basis_ids: Iterable[str] = (),
    policy_refs: Optional[Mapping[str, str]] = None,
) -> Dict[str, object]:
    return {
        "schema_version": "kmfa.project_cost.operation_request.v1",
        "run_id": run_id,
        "mode": mode,
        "requested_metrics": list(metrics),
        "requested_basis_ids": list(basis_ids),
        "project_selector": {"project_code": "SYNTHETIC-PROJECT"} if mode != "inventory" else {},
        "as_of": "2000-01-31" if mode in {"reference-replay", "calculate", "restate"} else None,
        "input_root": str(raw_root.resolve()) if raw_root else None,
        "manifest_path": str(manifest_path.resolve()) if manifest_path else None,
        "output_dir": str(output_dir),
        "policy_refs": dict(policy_refs or {}),
        "resolution_path": None,
        "prior_sufficiency_report_path": None,
    }
