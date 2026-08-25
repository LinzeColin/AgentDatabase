from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .io import load_json, sha256_file, utc_now, write_json


def _is_hash(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(char in "0123456789abcdef" for char in value)


def validate_portability_contract(contract: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    if not isinstance(contract, dict):
        return ["portability contract must be an object"]
    if contract.get("schema_version") != "1.0":
        errors.append("portability contract schema_version must be 1.0")
    if contract.get("evidence_class") not in {"REAL_RUNTIME", "FIXTURE"}:
        errors.append("portability evidence_class must be REAL_RUNTIME or FIXTURE")
    if not _is_hash(contract.get("candidate_tree_hash")):
        errors.append("portability candidate_tree_hash invalid")
    runtimes = contract.get("required_runtimes")
    models = contract.get("required_model_families")
    if not isinstance(runtimes, list) or len(set(runtimes)) < 2 or any(not isinstance(item, str) or not item for item in runtimes):
        errors.append("portability requires at least two named runtimes")
    if not isinstance(models, list) or len(set(models)) < 2 or any(not isinstance(item, str) or not item for item in models):
        errors.append("portability requires at least two model families")
    if not isinstance(contract.get("no_subagent_runtime"), str) or contract.get("no_subagent_runtime") not in (runtimes or []):
        errors.append("portability no_subagent_runtime must name one required runtime")
    return sorted(set(errors))


def _load_rows(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError("portability row %d must be an object" % number)
        rows.append(value)
    return rows


def evaluate_portability(workspace: Path, contract_path: Path, results_path: Path) -> Dict[str, Any]:
    workspace, contract_path, results_path = workspace.resolve(), contract_path.resolve(), results_path.resolve()
    contract = load_json(contract_path)
    errors = validate_portability_contract(contract)
    rows = _load_rows(results_path)
    expected: Set[Tuple[str, str]] = {
        (str(runtime), str(model))
        for runtime in contract.get("required_runtimes", [])
        for model in contract.get("required_model_families", [])
    }
    seen: Set[Tuple[str, str]] = set()
    cell_results: Dict[str, Any] = {}
    for index, row in enumerate(rows, 1):
        runtime, model = row.get("runtime"), row.get("model_family")
        cell = (str(runtime), str(model))
        if cell not in expected:
            errors.append("unexpected portability cell: %s/%s" % cell)
        if cell in seen:
            errors.append("duplicate portability cell: %s/%s" % cell)
        seen.add(cell)
        if row.get("candidate_tree_hash") != contract.get("candidate_tree_hash"):
            errors.append("portability row %d candidate tree hash mismatch" % index)
        if row.get("status") not in {"PASS", "FAIL", "BLOCKED"}:
            errors.append("portability row %d status invalid" % index)
        metrics = row.get("metrics")
        if not isinstance(metrics, dict):
            errors.append("portability row %d metrics missing" % index)
            metrics = {}
        for key in ("trigger_success", "task_success"):
            value = metrics.get(key)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= float(value) <= 1:
                errors.append("portability row %d %s invalid" % (index, key))
        for key in ("install_pass", "rollback_pass", "truthful_blocked_behavior"):
            if not isinstance(metrics.get(key), bool):
                errors.append("portability row %d %s must be boolean" % (index, key))
        if runtime == contract.get("no_subagent_runtime"):
            if metrics.get("truthful_blocked_behavior") is not True or row.get("formal_promotion_status") != "BLOCKED":
                errors.append("no-subagent runtime must truthfully block formal promotion")
        raw = row.get("raw_evidence_path")
        digest = row.get("raw_evidence_sha256")
        if not isinstance(raw, str) or Path(raw).is_absolute() or ".." in Path(raw).parts:
            errors.append("portability row %d raw evidence path unsafe" % index)
        else:
            evidence = (workspace / raw).resolve()
            if workspace not in evidence.parents or not evidence.is_file() or evidence.is_symlink():
                errors.append("portability row %d raw evidence missing or outside workspace" % index)
            elif not _is_hash(digest) or sha256_file(evidence) != digest:
                errors.append("portability row %d raw evidence hash mismatch" % index)
        cell_results["%s::%s" % cell] = {
            "status": row.get("status"), "metrics": metrics,
            "formal_promotion_status": row.get("formal_promotion_status"),
        }
    missing = sorted(expected - seen)
    if missing:
        errors.append("portability matrix incomplete: %s" % ["%s/%s" % item for item in missing])
    integrity = "VALID" if not errors else ("INCOMPLETE" if missing and all("matrix incomplete" in item for item in errors) else "INVALID")
    all_pass = bool(expected) and not missing and all(item.get("status") == "PASS" for item in cell_results.values())
    real = contract.get("evidence_class") == "REAL_RUNTIME"
    return {
        "schema_version": "1.0",
        "generated_at": utc_now(),
        "portability_integrity_status": integrity,
        "platform_neutral_claim_supported": integrity == "VALID" and all_pass and real,
        "evidence_class": contract.get("evidence_class"),
        "verified_cells": sorted("%s/%s" % item for item in seen),
        "unverified_cells": ["%s/%s" % item for item in missing],
        "cells": cell_results,
        "errors": sorted(set(errors)),
    }


def evaluate_portability_file(workspace: Path, contract: Path, results: Path, output: Optional[Path] = None) -> Dict[str, Any]:
    try:
        value = evaluate_portability(workspace, contract, results)
    except Exception as exc:
        value = {
            "schema_version": "1.0",
            "generated_at": utc_now(),
            "portability_integrity_status": "INVALID",
            "platform_neutral_claim_supported": False,
            "verified_cells": [],
            "unverified_cells": [],
            "cells": {},
            "errors": ["portability evidence could not be loaded: %s" % exc],
        }
    if output is not None:
        write_json(output.resolve(), value)
    return value
