#!/usr/bin/env python3
"""Product Reality Lab helper CLI.

The CLI initializes machine-readable run ledgers, validates their internal
consistency, evaluates readiness, indexes evidence, and prepares a strictly
non-adjudicative handoff for an independent verifier.

It intentionally uses only the Python standard library.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import shutil
import sys
import tempfile
import uuid
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable

SCHEMA_VERSION = "0.1.0"
READINESS_CALCULATION_VERSION = "0.2.1"
DIMENSIONS = (
    "surface",
    "state",
    "transition",
    "role",
    "data",
    "fault",
    "oracle",
    "evidence",
)
ALLOWED_STATUSES = {
    "READY_FOR_VERIFIER",
    "MORE_EVIDENCE_REQUIRED",
    "FIELD_VALIDATION_PENDING",
    "BLOCKED",
}
OPEN_DEFECT_STATUSES = {
    "OPEN",
    "TRIAGED",
    "FIX_IN_PROGRESS",
    "FIXED_UNVERIFIED",
}
REQUIRED_WORKSPACE_FILES = (
    "run_contract.json",
    "surface_graph.json",
    "inventory_diff.json",
    "journey_state_graph.json",
    "fault_graph.json",
    "oracle_catalog.json",
    "competitor_evidence.json",
    "provenance_ledger.json",
    "test_matrix.json",
    "coverage_ledger.json",
    "defect_ledger.json",
    "poka_yoke_audit.json",
    "field_experiment.json",
    "field_feedback.json",
    "residual_risk.md",
    "evidence/index.json",
)


class PRLError(RuntimeError):
    """Raised for actionable Product Reality Lab errors."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PRLError(f"Missing required file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise PRLError(f"Invalid JSON in {path}: line {exc.lineno}, column {exc.colno}: {exc.msg}") from exc
    if not isinstance(data, dict):
        raise PRLError(f"Expected JSON object in {path}")
    return data


def atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def template_root() -> Path:
    return skill_root() / "templates"


def new_run_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"PRL-{stamp}-{uuid.uuid4().hex[:8]}"


def replace_run_id(value: Any, run_id: str) -> Any:
    if isinstance(value, dict):
        return {key: replace_run_id(item, run_id) for key, item in value.items()}
    if isinstance(value, list):
        return [replace_run_id(item, run_id) for item in value]
    if value == "RUN-REPLACE":
        return run_id
    return value


def initialize_workspace(
    workspace: Path,
    subject_name: str,
    subject_ref: str,
    subject_kind: str = "commit",
    owner: str = "OWNER_REQUIRED",
    field_required: bool = False,
    force: bool = False,
) -> str:
    workspace = workspace.resolve()
    if workspace.exists() and any(workspace.iterdir()) and not force:
        raise PRLError(f"Workspace is not empty: {workspace}. Use --force only for a disposable directory.")
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "evidence").mkdir(parents=True, exist_ok=True)

    run_id = new_run_id()
    mappings = {
        "run_contract.template.json": "run_contract.json",
        "surface_graph.template.json": "surface_graph.json",
        "inventory_diff.template.json": "inventory_diff.json",
        "journey_state_graph.template.json": "journey_state_graph.json",
        "fault_graph.template.json": "fault_graph.json",
        "oracle_catalog.template.json": "oracle_catalog.json",
        "competitor_evidence.template.json": "competitor_evidence.json",
        "provenance_ledger.template.json": "provenance_ledger.json",
        "test_matrix.template.json": "test_matrix.json",
        "coverage_ledger.template.json": "coverage_ledger.json",
        "defect_ledger.template.json": "defect_ledger.json",
        "poka_yoke_audit.template.json": "poka_yoke_audit.json",
        "field_experiment.template.json": "field_experiment.json",
        "field_feedback.template.json": "field_feedback.json",
        "evidence_index.template.json": "evidence/index.json",
    }

    for source_name, destination_name in mappings.items():
        data = load_json(template_root() / source_name)
        data = replace_run_id(data, run_id)
        destination = workspace / destination_name
        atomic_write_json(destination, data)

    run_contract_path = workspace / "run_contract.json"
    run_contract = load_json(run_contract_path)
    run_contract["created_at"] = utc_now()
    run_contract["subject"]["name"] = subject_name
    run_contract["subject"]["ref"] = subject_ref
    run_contract["subject"]["kind"] = subject_kind
    run_contract["authorization"]["owner"] = owner
    run_contract["field_validation_required"] = field_required
    atomic_write_json(run_contract_path, run_contract)

    coverage = load_json(workspace / "coverage_ledger.json")
    coverage["gates"]["field_validation_required"] = field_required
    atomic_write_json(workspace / "coverage_ledger.json", coverage)

    field = load_json(workspace / "field_experiment.json")
    field["required"] = field_required
    atomic_write_json(workspace / "field_experiment.json", field)

    residual_template = (template_root() / "residual_risk.template.md").read_text(encoding="utf-8")
    residual = residual_template.replace("RUN-REPLACE", run_id).replace("Subject: REPLACE", f"Subject: {subject_name} ({subject_ref})")
    (workspace / "residual_risk.md").write_text(residual, encoding="utf-8")
    return run_id


def parse_expiry(value: str) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def count_open_defects(defect_ledger: dict[str, Any], severity: str) -> int:
    return sum(
        1
        for defect in defect_ledger.get("defects", [])
        if defect.get("severity") == severity and defect.get("status") in OPEN_DEFECT_STATUSES
    )


def indexed_ids(
    items: Any,
    key: str,
    label: str,
    errors: list[str],
) -> tuple[set[str], dict[str, dict[str, Any]]]:
    """Return unique IDs and objects while recording malformed/duplicate IDs."""
    ids: set[str] = set()
    by_id: dict[str, dict[str, Any]] = {}
    if not isinstance(items, list):
        errors.append(f"{label}_NOT_ARRAY")
        return ids, by_id
    for item in items:
        if not isinstance(item, dict):
            errors.append(f"{label}_ITEM_NOT_OBJECT")
            continue
        value = item.get(key)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{label}_MISSING_ID")
            continue
        if value in ids:
            errors.append(f"{label}_DUPLICATE_ID:{value}")
            continue
        ids.add(value)
        by_id[value] = item
    return ids, by_id


def actual_field_validation_complete(field_experiment: dict[str, Any]) -> bool:
    """Field completion must be evidenced by a completed FIELD_OBSERVED experiment."""
    return any(
        experiment.get("status") == "COMPLETED"
        and experiment.get("evidence_class") == "FIELD_OBSERVED"
        and bool(experiment.get("evidence_refs"))
        for experiment in field_experiment.get("experiments", [])
        if isinstance(experiment, dict)
    )


def validate_workspace(workspace: Path, verify_evidence_hashes: bool = True) -> tuple[list[str], list[str]]:
    workspace = workspace.resolve()
    errors: list[str] = []
    warnings: list[str] = []

    for rel in REQUIRED_WORKSPACE_FILES:
        if not (workspace / rel).is_file():
            errors.append(f"MISSING_FILE:{rel}")

    if errors:
        return errors, warnings

    json_paths = [path for path in workspace.rglob("*.json") if path.is_file()]
    parsed: dict[Path, dict[str, Any]] = {}
    for path in json_paths:
        try:
            parsed[path] = load_json(path)
        except PRLError as exc:
            errors.append(f"JSON:{exc}")

    if errors:
        return errors, warnings

    run_contract = parsed[workspace / "run_contract.json"]
    run_id = run_contract.get("run_id")
    if not run_id:
        errors.append("RUN_CONTRACT:run_id is required")
    if run_contract.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"RUN_CONTRACT:schema_version must be {SCHEMA_VERSION}")

    subject = run_contract.get("subject", {})
    if not subject.get("name") or subject.get("name") == "REPLACE":
        errors.append("RUN_CONTRACT:subject.name must be set")
    if not subject.get("ref") or subject.get("ref") == "REPLACE":
        errors.append("RUN_CONTRACT:subject.ref must be set")
    owner = run_contract.get("authorization", {}).get("owner", "")
    if not owner or owner in {"REPLACE", "OWNER_REQUIRED"}:
        errors.append("RUN_CONTRACT:authorization.owner is not finalized")

    for path, data in parsed.items():
        if path.name.endswith(".schema.json"):
            continue
        if "run_id" in data and data.get("run_id") != run_id:
            errors.append(f"RUN_ID_MISMATCH:{path.relative_to(workspace)}")
        if "schema_version" in data and data.get("schema_version") != SCHEMA_VERSION:
            errors.append(
                f"SCHEMA_VERSION_MISMATCH:{path.relative_to(workspace)}:{data.get('schema_version')}"
            )
        status = data.get("status")
        if status is not None and path.name != "verifier_intake.json" and status in {"PASS", "VERIFIED", "PRODUCTION_READY"}:
            errors.append(f"FORBIDDEN_VERDICT:{path.relative_to(workspace)}:{status}")

    def find_forbidden_verdicts(value: Any, label: str) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                child_label = f"{label}.{key}"
                if key == "status" and child in {"PASS", "VERIFIED", "PRODUCTION_READY"}:
                    errors.append(f"FORBIDDEN_NESTED_VERDICT:{child_label}:{child}")
                else:
                    find_forbidden_verdicts(child, child_label)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                find_forbidden_verdicts(child, f"{label}[{index}]")

    for path, data in parsed.items():
        if path.name != "verifier_intake.json":
            find_forbidden_verdicts(data, path.relative_to(workspace).as_posix())

    coverage = parsed[workspace / "coverage_ledger.json"]
    dimensions = coverage.get("dimensions", {})
    waiver_items = coverage.get("waivers", [])
    if not isinstance(waiver_items, list):
        errors.append("WAIVERS_NOT_ARRAY")
        waiver_items = []
    waiver_ids, _waivers_by_id = indexed_ids(waiver_items, "id", "WAIVER", errors)
    today = datetime.now(timezone.utc).date()

    for waiver in waiver_items:
        wid = waiver.get("id", "<missing>")
        expiry = parse_expiry(str(waiver.get("expires_at", "")))
        if expiry is None:
            errors.append(f"WAIVER_INVALID_EXPIRY:{wid}")
        elif expiry < today:
            errors.append(f"WAIVER_EXPIRED:{wid}:{expiry.isoformat()}")
        for required in ("scope", "reason", "owner", "compensating_control"):
            if not waiver.get(required):
                errors.append(f"WAIVER_MISSING_FIELD:{wid}:{required}")
        if not waiver.get("evidence_refs"):
            errors.append(f"WAIVER_WITHOUT_EVIDENCE:{wid}")

    for name in DIMENSIONS:
        dim = dimensions.get(name)
        if not isinstance(dim, dict):
            errors.append(f"COVERAGE_MISSING_DIMENSION:{name}")
            continue
        fields = ("critical_total", "critical_covered", "critical_waived", "noncritical_total", "noncritical_covered")
        for field in fields:
            value = dim.get(field)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                errors.append(f"COVERAGE_INVALID_NUMBER:{name}:{field}")
        total = dim.get("critical_total", 0)
        covered = dim.get("critical_covered", 0)
        waived = dim.get("critical_waived", 0)
        if covered + waived > total:
            errors.append(f"COVERAGE_OVERCOUNT:{name}:{covered}+{waived}>{total}")
        if dim.get("noncritical_covered", 0) > dim.get("noncritical_total", 0):
            errors.append(f"NONCRITICAL_COVERAGE_OVERCOUNT:{name}")
        listed_waivers = dim.get("waiver_ids", [])
        if waived > 0 and not listed_waivers:
            errors.append(f"COVERAGE_WAIVER_WITHOUT_ID:{name}")
        unknown = [wid for wid in listed_waivers if wid not in waiver_ids]
        if unknown:
            errors.append(f"COVERAGE_UNKNOWN_WAIVER:{name}:{','.join(sorted(unknown))}")

        items = dim.get("items")
        if not isinstance(items, list):
            errors.append(f"COVERAGE_ITEMS_NOT_ARRAY:{name}")
            continue
        seen_item_ids: set[str] = set()
        derived = {
            "critical_total": 0,
            "critical_covered": 0,
            "critical_waived": 0,
            "noncritical_total": 0,
            "noncritical_covered": 0,
        }
        derived_refs: set[str] = set()
        derived_waivers: set[str] = set()
        for item in items:
            if not isinstance(item, dict):
                errors.append(f"COVERAGE_ITEM_NOT_OBJECT:{name}")
                continue
            item_id = item.get("item_id")
            if not isinstance(item_id, str) or not item_id.strip():
                errors.append(f"COVERAGE_ITEM_MISSING_ID:{name}")
                continue
            if item_id in seen_item_ids:
                errors.append(f"COVERAGE_ITEM_DUPLICATE_ID:{name}:{item_id}")
                continue
            seen_item_ids.add(item_id)
            if not isinstance(item.get("source_ref"), str) or not item.get("source_ref", "").strip():
                errors.append(f"COVERAGE_ITEM_MISSING_SOURCE_REF:{name}:{item_id}")
            critical = item.get("critical")
            status = item.get("status")
            refs = item.get("evidence_refs")
            waiver_id = item.get("waiver_id")
            if not isinstance(critical, bool):
                errors.append(f"COVERAGE_ITEM_INVALID_CRITICAL:{name}:{item_id}")
                continue
            if status not in {"UNCOVERED", "COVERED", "WAIVED"}:
                errors.append(f"COVERAGE_ITEM_INVALID_STATUS:{name}:{item_id}:{status}")
                continue
            if not isinstance(refs, list) or any(not isinstance(ref, str) or not ref for ref in refs):
                errors.append(f"COVERAGE_ITEM_INVALID_EVIDENCE_REFS:{name}:{item_id}")
                refs = []
            derived_refs.update(refs)
            if critical:
                derived["critical_total"] += 1
                if status == "COVERED":
                    derived["critical_covered"] += 1
                elif status == "WAIVED":
                    derived["critical_waived"] += 1
            else:
                derived["noncritical_total"] += 1
                if status == "COVERED":
                    derived["noncritical_covered"] += 1
            if status == "COVERED" and not refs:
                errors.append(f"COVERAGE_ITEM_COVERED_WITHOUT_EVIDENCE:{name}:{item_id}")
            if status == "WAIVED":
                if not isinstance(waiver_id, str) or waiver_id not in waiver_ids:
                    errors.append(f"COVERAGE_ITEM_INVALID_WAIVER:{name}:{item_id}:{waiver_id}")
                else:
                    derived_waivers.add(waiver_id)
            elif waiver_id not in {None, ""}:
                errors.append(f"COVERAGE_ITEM_WAIVER_ON_NONWAIVED:{name}:{item_id}")

        for field, expected in derived.items():
            if dim.get(field) != expected:
                errors.append(
                    f"COVERAGE_DERIVED_COUNT_MISMATCH:{name}:{field}:"
                    f"ledger={dim.get(field)}:actual={expected}"
                )
        if set(dim.get("evidence_refs", [])) != derived_refs:
            errors.append(f"COVERAGE_DERIVED_EVIDENCE_MISMATCH:{name}")
        if set(listed_waivers) != derived_waivers:
            errors.append(f"COVERAGE_DERIVED_WAIVER_MISMATCH:{name}")

    defects = parsed[workspace / "defect_ledger.json"]
    seen_defects: set[str] = set()
    for defect in defects.get("defects", []):
        defect_id = defect.get("defect_id")
        if not defect_id:
            errors.append("DEFECT_MISSING_ID")
        elif defect_id in seen_defects:
            errors.append(f"DEFECT_DUPLICATE_ID:{defect_id}")
        else:
            seen_defects.add(defect_id)
        if defect.get("status") == "DUPLICATE" and not defect.get("duplicate_of"):
            errors.append(f"DEFECT_DUPLICATE_WITHOUT_PARENT:{defect_id}")
        if defect.get("severity") in {"P0", "P1"} and not defect.get("evidence_refs"):
            errors.append(f"DEFECT_HIGH_SEVERITY_WITHOUT_EVIDENCE:{defect_id}")

    gates = coverage.get("gates", {})
    actual_p0 = count_open_defects(defects, "P0")
    actual_p1 = count_open_defects(defects, "P1")
    if gates.get("open_p0") != actual_p0:
        errors.append(f"GATE_DEFECT_COUNT_MISMATCH:P0:ledger={gates.get('open_p0')}:actual={actual_p0}")
    if gates.get("open_p1") != actual_p1:
        errors.append(f"GATE_DEFECT_COUNT_MISMATCH:P1:ledger={gates.get('open_p1')}:actual={actual_p1}")

    inventory = parsed[workspace / "inventory_diff.json"]
    if gates.get("unwaived_inventory_diff") != inventory.get("unwaived_count"):
        errors.append(
            "GATE_INVENTORY_DIFF_MISMATCH:"
            f"ledger={gates.get('unwaived_inventory_diff')}:actual={inventory.get('unwaived_count')}"
        )

    field = parsed[workspace / "field_experiment.json"]
    contract_field = bool(run_contract.get("field_validation_required"))
    if bool(field.get("required")) != contract_field:
        errors.append("FIELD_REQUIRED_MISMATCH:run_contract_vs_field_experiment")
    if bool(gates.get("field_validation_required")) != contract_field:
        errors.append("FIELD_REQUIRED_MISMATCH:run_contract_vs_coverage")
    actual_field_complete = actual_field_validation_complete(field)
    if bool(gates.get("field_validation_complete")) != actual_field_complete:
        errors.append(
            "FIELD_COMPLETE_DERIVATION_MISMATCH:"
            f"ledger={bool(gates.get('field_validation_complete'))}:actual={actual_field_complete}"
        )

    evidence_index = parsed[workspace / "evidence/index.json"]
    evidence_ids: set[str] = set()
    evidence_by_id: dict[str, dict[str, Any]] = {}
    evidence_paths: set[str] = set()
    for artifact in evidence_index.get("artifacts", []):
        evidence_id = artifact.get("evidence_id")
        rel_path = artifact.get("path")
        if not evidence_id or evidence_id in evidence_ids:
            errors.append(f"EVIDENCE_DUPLICATE_OR_MISSING_ID:{evidence_id}")
        else:
            evidence_ids.add(evidence_id)
            evidence_by_id[evidence_id] = artifact
        if not rel_path or rel_path in evidence_paths:
            errors.append(f"EVIDENCE_DUPLICATE_OR_MISSING_PATH:{rel_path}")
            continue
        rel = Path(rel_path)
        if rel.is_absolute() or ".." in rel.parts or not rel.parts or rel.parts[0] != "evidence":
            errors.append(f"EVIDENCE_PATH_OUTSIDE_ROOT:{rel_path}")
            continue
        evidence_paths.add(rel_path)
        absolute = workspace / rel_path
        if not absolute.is_file():
            errors.append(f"EVIDENCE_FILE_MISSING:{rel_path}")
            continue
        if absolute.is_symlink():
            errors.append(f"EVIDENCE_SYMLINK_FORBIDDEN:{rel_path}")
        expected_hash = artifact.get("sha256")
        if not isinstance(expected_hash, str) or len(expected_hash) != 64 or any(
            char not in "0123456789abcdef" for char in expected_hash.lower()
        ):
            errors.append(f"EVIDENCE_INVALID_SHA256:{rel_path}")
        elif verify_evidence_hashes and sha256_file(absolute) != expected_hash:
            errors.append(f"EVIDENCE_HASH_MISMATCH:{rel_path}")
        if artifact.get("subject_ref") != subject.get("ref"):
            errors.append(f"EVIDENCE_SUBJECT_REF_MISMATCH:{rel_path}")
        if artifact.get("evidence_class") not in {"SYNTHETIC", "CONTROLLED_HUMAN", "FIELD_OBSERVED"}:
            errors.append(f"EVIDENCE_INVALID_CLASS:{rel_path}:{artifact.get('evidence_class')}")
        if not artifact.get("tool"):
            errors.append(f"EVIDENCE_TOOL_MISSING:{rel_path}")
        if not artifact.get("created_at"):
            errors.append(f"EVIDENCE_CREATED_AT_MISSING:{rel_path}")

    def check_evidence_ref(label: str, ref: Any) -> None:
        if ref in {None, ""}:
            return
        if not isinstance(ref, str):
            errors.append(f"EVIDENCE_REF_NOT_STRING:{label}")
            return
        if ref not in evidence_ids and not (workspace / ref).is_file():
            errors.append(f"UNKNOWN_EVIDENCE_REF:{label}:{ref}")

    def walk_evidence_refs(value: Any, label: str) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                child_label = f"{label}.{key}"
                if key == "evidence_refs":
                    if not isinstance(child, list):
                        errors.append(f"EVIDENCE_REFS_NOT_ARRAY:{child_label}")
                    else:
                        for ref in child:
                            check_evidence_ref(child_label, ref)
                elif key == "evidence_ref" or key.endswith("_evidence_ref"):
                    check_evidence_ref(child_label, child)
                else:
                    walk_evidence_refs(child, child_label)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk_evidence_refs(child, f"{label}[{index}]")

    for path, data in parsed.items():
        if path == workspace / "evidence/index.json":
            continue
        walk_evidence_refs(data, path.relative_to(workspace).as_posix())

    surface = parsed[workspace / "surface_graph.json"]
    surface_node_ids, surface_nodes = indexed_ids(surface.get("nodes"), "id", "SURFACE_NODE", errors)
    surface_edge_ids, surface_edges = indexed_ids(surface.get("edges"), "id", "SURFACE_EDGE", errors)

    journey = parsed[workspace / "journey_state_graph.json"]
    state_ids, states = indexed_ids(journey.get("states"), "id", "JOURNEY_STATE", errors)
    transition_ids, transitions = indexed_ids(
        journey.get("transitions"), "id", "JOURNEY_TRANSITION", errors
    )

    fault_graph = parsed[workspace / "fault_graph.json"]
    steady_state_ids, steady_states = indexed_ids(
        fault_graph.get("steady_states"), "id", "STEADY_STATE", errors
    )
    fault_ids, faults = indexed_ids(fault_graph.get("faults"), "id", "FAULT", errors)
    fault_experiment_ids, fault_experiments = indexed_ids(
        fault_graph.get("experiments"), "id", "FAULT_EXPERIMENT", errors
    )

    oracle_catalog = parsed[workspace / "oracle_catalog.json"]
    oracle_ids, oracles = indexed_ids(
        oracle_catalog.get("oracles"), "oracle_id", "ORACLE", errors
    )

    test_matrix = parsed[workspace / "test_matrix.json"]
    test_ids, tests = indexed_ids(test_matrix.get("tests"), "test_id", "TEST", errors)

    for edge_id, edge in surface_edges.items():
        if edge.get("from") not in surface_node_ids:
            errors.append(f"SURFACE_EDGE_UNKNOWN_FROM:{edge_id}:{edge.get('from')}")
        if edge.get("to") not in surface_node_ids:
            errors.append(f"SURFACE_EDGE_UNKNOWN_TO:{edge_id}:{edge.get('to')}")
        for oracle_id in edge.get("oracle_ids", []):
            if oracle_id not in oracle_ids:
                errors.append(f"SURFACE_EDGE_UNKNOWN_ORACLE:{edge_id}:{oracle_id}")

    for transition_id, transition in transitions.items():
        if transition.get("from") not in state_ids:
            errors.append(f"JOURNEY_TRANSITION_UNKNOWN_FROM:{transition_id}:{transition.get('from')}")
        if transition.get("to") not in state_ids:
            errors.append(f"JOURNEY_TRANSITION_UNKNOWN_TO:{transition_id}:{transition.get('to')}")
        recovery = transition.get("recovery_transition_id")
        if recovery and recovery not in transition_ids:
            errors.append(f"JOURNEY_TRANSITION_UNKNOWN_RECOVERY:{transition_id}:{recovery}")
        for oracle_id in transition.get("oracle_ids", []):
            if oracle_id not in oracle_ids:
                errors.append(f"JOURNEY_TRANSITION_UNKNOWN_ORACLE:{transition_id}:{oracle_id}")

    for experiment_id, experiment in fault_experiments.items():
        if experiment.get("fault_id") not in fault_ids:
            errors.append(f"FAULT_EXPERIMENT_UNKNOWN_FAULT:{experiment_id}:{experiment.get('fault_id')}")
        if experiment.get("steady_state_id") not in steady_state_ids:
            errors.append(
                f"FAULT_EXPERIMENT_UNKNOWN_STEADY_STATE:{experiment_id}:{experiment.get('steady_state_id')}"
            )
        if experiment.get("status") in {"OBSERVED_EXPECTED", "OBSERVED_DEVIATION"} and not experiment.get(
            "evidence_refs"
        ):
            errors.append(f"FAULT_EXPERIMENT_OBSERVED_WITHOUT_EVIDENCE:{experiment_id}")
        if experiment.get("status") not in {
            "PLANNED", "RUNNING", "OBSERVED_EXPECTED", "OBSERVED_DEVIATION", "ABORTED", "ROLLED_BACK", "WAIVED"
        }:
            errors.append(f"FAULT_EXPERIMENT_INVALID_STATUS:{experiment_id}:{experiment.get('status')}")

    for steady_state_id, steady_state in steady_states.items():
        for oracle_id in steady_state.get("oracle_ids", []):
            if oracle_id not in oracle_ids:
                errors.append(f"STEADY_STATE_UNKNOWN_ORACLE:{steady_state_id}:{oracle_id}")

    known_targets = (
        surface_node_ids
        | surface_edge_ids
        | state_ids
        | transition_ids
        | steady_state_ids
        | fault_ids
        | fault_experiment_ids
    )
    for test_id, test in tests.items():
        if not isinstance(test.get("critical"), bool):
            errors.append(f"TEST_INVALID_CRITICAL:{test_id}")
        target_refs = test.get("target_ids", [])
        if not isinstance(target_refs, list) or not target_refs:
            errors.append(f"TEST_TARGETS_EMPTY_OR_INVALID:{test_id}")
        else:
            for target_id in target_refs:
                if target_id not in known_targets:
                    errors.append(f"TEST_UNKNOWN_TARGET:{test_id}:{target_id}")
        oracle_refs = test.get("oracle_ids", [])
        if not isinstance(oracle_refs, list) or not oracle_refs:
            errors.append(f"TEST_ORACLES_EMPTY_OR_INVALID:{test_id}")
        else:
            for oracle_id in oracle_refs:
                if oracle_id not in oracle_ids:
                    errors.append(f"TEST_UNKNOWN_ORACLE:{test_id}:{oracle_id}")
        status = test.get("status")
        if status not in {
            "NOT_RUN",
            "RUNNING",
            "OBSERVED_EXPECTED",
            "OBSERVED_DEVIATION",
            "BLOCKED",
            "WAIVED",
        }:
            errors.append(f"TEST_INVALID_STATUS:{test_id}:{status}")
        if status in {"OBSERVED_EXPECTED", "OBSERVED_DEVIATION"} and not test.get("evidence_refs"):
            errors.append(f"TEST_OBSERVED_WITHOUT_EVIDENCE:{test_id}")
        negative = bool(test.get("negative_control", False))
        effective = bool(test.get("negative_control_effective", False))
        if effective and not negative:
            errors.append(f"TEST_NEGATIVE_CONTROL_EFFECTIVE_WITHOUT_FLAG:{test_id}")
    for oracle_id, oracle in oracles.items():
        if not isinstance(oracle.get("critical"), bool):
            errors.append(f"ORACLE_INVALID_CRITICAL:{oracle_id}")

    roles = {
        role
        for node in surface_nodes.values()
        for role in node.get("roles", [])
        if isinstance(role, str) and role
    } | {
        state.get("role")
        for state in states.values()
        if isinstance(state.get("role"), str) and state.get("role")
    }
    data_conditions = {
        test.get("data_condition")
        for test in tests.values()
        if isinstance(test.get("data_condition"), str) and test.get("data_condition")
    }
    dimension_sources: dict[str, set[str]] = {
        "surface": surface_node_ids,
        "state": state_ids,
        "transition": transition_ids,
        "role": roles,
        "data": data_conditions,
        "fault": fault_ids,
        "oracle": oracle_ids,
        "evidence": evidence_ids,
    }
    source_objects: dict[str, dict[str, dict[str, Any]]] = {
        "surface": surface_nodes,
        "state": states,
        "transition": transitions,
        "fault": faults,
        "oracle": oracles,
    }
    for name in DIMENSIONS:
        dim = dimensions.get(name, {})
        coverage_items = dim.get("items", []) if isinstance(dim, dict) else []
        item_sources = {
            item.get("source_ref")
            for item in coverage_items
            if isinstance(item, dict) and isinstance(item.get("source_ref"), str)
        }
        missing = dimension_sources[name] - item_sources
        extra = item_sources - dimension_sources[name]
        if missing:
            errors.append(f"COVERAGE_INVENTORY_MISSING:{name}:{','.join(sorted(missing))}")
        if extra:
            errors.append(f"COVERAGE_INVENTORY_UNKNOWN:{name}:{','.join(sorted(extra))}")
        if name in source_objects:
            objects = source_objects[name]
            for item in coverage_items:
                if not isinstance(item, dict):
                    continue
                source_ref = item.get("source_ref")
                source_object = objects.get(source_ref)
                if source_object is not None and item.get("critical") != bool(source_object.get("critical")):
                    errors.append(f"COVERAGE_CRITICALITY_MISMATCH:{name}:{source_ref}")

    poka_yoke = parsed[workspace / "poka_yoke_audit.json"]
    _poka_ids, poka_actions = indexed_ids(
        poka_yoke.get("actions"), "action_id", "POKA_YOKE_ACTION", errors
    )
    for action_id, action in poka_actions.items():
        if not isinstance(action.get("critical"), bool):
            errors.append(f"POKA_YOKE_INVALID_CRITICAL:{action_id}")
        if action.get("status") not in {
            "NOT_RUN", "RUNNING", "OBSERVED_EXPECTED", "OBSERVED_DEVIATION", "BLOCKED", "WAIVED"
        }:
            errors.append(f"POKA_YOKE_INVALID_STATUS:{action_id}:{action.get('status')}")
        if action.get("status") in {"OBSERVED_EXPECTED", "OBSERVED_DEVIATION"} and not action.get(
            "evidence_refs"
        ):
            errors.append(f"POKA_YOKE_OBSERVED_WITHOUT_EVIDENCE:{action_id}")
        if action.get("status") == "WAIVED":
            if action.get("waiver_id") not in waiver_ids:
                errors.append(f"POKA_YOKE_INVALID_WAIVER:{action_id}:{action.get('waiver_id')}")
        elif action.get("waiver_id") not in {None, ""}:
            errors.append(f"POKA_YOKE_WAIVER_ON_NONWAIVED:{action_id}")

    field_experiment_ids, field_experiments = indexed_ids(
        field.get("experiments"), "experiment_id", "FIELD_EXPERIMENT", errors
    )
    for experiment_id, experiment in field_experiments.items():
        if experiment.get("status") == "COMPLETED" and not experiment.get("evidence_refs"):
            errors.append(f"FIELD_EXPERIMENT_COMPLETED_WITHOUT_EVIDENCE:{experiment_id}")
        experiment_class = experiment.get("evidence_class")
        if experiment_class in {"CONTROLLED_HUMAN", "FIELD_OBSERVED"}:
            for ref in experiment.get("evidence_refs", []):
                artifact = evidence_by_id.get(ref)
                if artifact is not None and artifact.get("evidence_class") != experiment_class:
                    errors.append(
                        f"FIELD_EXPERIMENT_EVIDENCE_CLASS_MISMATCH:{experiment_id}:{ref}:"
                        f"declared={experiment_class}:actual={artifact.get('evidence_class')}"
                    )
    field_feedback = parsed[workspace / "field_feedback.json"]
    if actual_field_complete:
        if field_feedback.get("evidence_class") != "FIELD_OBSERVED":
            errors.append("FIELD_FEEDBACK_NOT_FIELD_OBSERVED")
        if not field_feedback.get("decision"):
            errors.append("FIELD_FEEDBACK_DECISION_EMPTY")
        if not field_feedback.get("evidence_refs"):
            errors.append("FIELD_FEEDBACK_EVIDENCE_EMPTY")
        for ref in field_feedback.get("evidence_refs", []):
            artifact = evidence_by_id.get(ref)
            if artifact is not None and artifact.get("evidence_class") != "FIELD_OBSERVED":
                errors.append(
                    f"FIELD_FEEDBACK_EVIDENCE_CLASS_MISMATCH:{ref}:{artifact.get('evidence_class')}"
                )

    competitor = parsed[workspace / "competitor_evidence.json"]
    _competitor_ids, competitor_refs = indexed_ids(
        competitor.get("references"), "competitor_id", "COMPETITOR", errors
    )
    source_ids: set[str] = set()
    for competitor_id, reference in competitor_refs.items():
        sources = reference.get("sources", [])
        if not isinstance(sources, list) or not sources:
            errors.append(f"COMPETITOR_WITHOUT_SOURCES:{competitor_id}")
            continue
        for source in sources:
            if not isinstance(source, dict):
                errors.append(f"COMPETITOR_SOURCE_NOT_OBJECT:{competitor_id}")
                continue
            source_id = source.get("source_id")
            if not isinstance(source_id, str) or not source_id:
                errors.append(f"COMPETITOR_SOURCE_MISSING_ID:{competitor_id}")
            elif source_id in source_ids:
                errors.append(f"COMPETITOR_SOURCE_DUPLICATE_ID:{source_id}")
            else:
                source_ids.add(source_id)
            if source.get("public_or_authorized") is not True:
                errors.append(f"COMPETITOR_SOURCE_NOT_AUTHORIZED:{competitor_id}:{source_id}")
            if not source.get("evidence_ref"):
                errors.append(f"COMPETITOR_SOURCE_WITHOUT_EVIDENCE:{competitor_id}:{source_id}")

    _benchmark_ids, benchmark_tasks = indexed_ids(
        competitor.get("benchmark_tasks"), "task_id", "BENCHMARK_TASK", errors
    )
    for task_id, task in benchmark_tasks.items():
        for required in ("task", "starting_state", "inputs", "metrics", "results", "evidence_refs"):
            value = task.get(required)
            if required not in task or value is None or value == "" or value == []:
                errors.append(f"BENCHMARK_TASK_MISSING_FIELD:{task_id}:{required}")

    _decision_ids, decisions = indexed_ids(
        competitor.get("decisions"), "decision_id", "COMPETITOR_DECISION", errors
    )
    for decision_id, decision in decisions.items():
        if decision.get("decision") not in {"ADOPT", "ADAPT", "DIFFERENTIATE", "REJECT", "DEFER"}:
            errors.append(f"COMPETITOR_DECISION_INVALID:{decision_id}:{decision.get('decision')}")
        for required in ("capability", "rationale", "owner", "evidence_refs"):
            if not decision.get(required):
                errors.append(f"COMPETITOR_DECISION_MISSING_FIELD:{decision_id}:{required}")

    provenance = parsed[workspace / "provenance_ledger.json"]
    _provenance_ids, provenance_items = indexed_ids(
        provenance.get("items"), "id", "PROVENANCE_ITEM", errors
    )
    for provenance_id, item in provenance_items.items():
        review_status = item.get("review_status")
        if review_status not in {"PENDING", "APPROVED", "REJECTED"}:
            errors.append(f"PROVENANCE_INVALID_REVIEW_STATUS:{provenance_id}:{review_status}")
            continue
        if review_status == "APPROVED":
            if not item.get("evidence_refs"):
                errors.append(f"PROVENANCE_APPROVED_WITHOUT_EVIDENCE:{provenance_id}")
            for required in ("allowed_use_basis", "reviewer", "reviewed_at"):
                if not item.get(required):
                    errors.append(f"PROVENANCE_APPROVED_MISSING_FIELD:{provenance_id}:{required}")
        elif review_status == "REJECTED":
            for required in ("reviewer", "reviewed_at"):
                if not item.get(required):
                    errors.append(f"PROVENANCE_REJECTED_MISSING_FIELD:{provenance_id}:{required}")
            if item.get("modified_files"):
                errors.append(f"PROVENANCE_REJECTED_STILL_MODIFIED:{provenance_id}")

    env = run_contract.get("environment", {})
    authorization = run_contract.get("authorization", {})
    high_risk_enabled = any(
        bool(authorization.get(key))
        for key in ("active_security_allowed", "load_allowed", "chaos_allowed", "destructive_actions_allowed")
    )
    if env.get("risk_tier") == "R4" and high_risk_enabled:
        if not env.get("rollback_procedure"):
            errors.append("R4_HIGH_RISK_WITHOUT_ROLLBACK_PROCEDURE")
        if not authorization.get("notes"):
            warnings.append("R4_HIGH_RISK_AUTHORIZATION_NOTES_EMPTY")

    return sorted(set(errors)), sorted(set(warnings))


def evaluate_readiness(workspace: Path) -> dict[str, Any]:
    workspace = workspace.resolve()
    errors, warnings = validate_workspace(workspace)
    if errors:
        return {
            "status": "BLOCKED",
            "run_id": None,
            "errors": errors,
            "warnings": warnings,
            "gaps": ["Workspace validation failed"],
            "dimensions": {},
        }

    contract = load_json(workspace / "run_contract.json")
    coverage = load_json(workspace / "coverage_ledger.json")
    evidence_index = load_json(workspace / "evidence/index.json")
    surface = load_json(workspace / "surface_graph.json")
    journey = load_json(workspace / "journey_state_graph.json")
    fault_graph = load_json(workspace / "fault_graph.json")
    oracle_catalog = load_json(workspace / "oracle_catalog.json")
    test_matrix = load_json(workspace / "test_matrix.json")
    competitor = load_json(workspace / "competitor_evidence.json")
    provenance = load_json(workspace / "provenance_ledger.json")
    poka_yoke = load_json(workspace / "poka_yoke_audit.json")
    gaps: list[str] = []
    dimension_results: dict[str, Any] = {}

    valid_waivers = {waiver.get("id") for waiver in coverage.get("waivers", [])}
    for name in DIMENSIONS:
        dim = coverage["dimensions"][name]
        total = dim["critical_total"]
        covered = dim["critical_covered"]
        waived = dim["critical_waived"]
        evidence_refs = dim.get("evidence_refs", [])
        closure = (covered + waived) / total if total else 0.0
        dimension_results[name] = {
            "critical_total": total,
            "critical_covered": covered,
            "critical_waived": waived,
            "critical_closure_ratio": round(closure, 6),
            "noncritical_total": dim["noncritical_total"],
            "noncritical_covered": dim["noncritical_covered"],
        }
        if total == 0:
            gaps.append(f"{name}:critical inventory is empty")
        elif covered + waived != total:
            gaps.append(f"{name}:critical closure {covered}+{waived}/{total}")
        if total > 0 and not evidence_refs:
            gaps.append(f"{name}:no evidence references")
        if waived > 0:
            listed = set(dim.get("waiver_ids", []))
            if not listed or not listed.issubset(valid_waivers):
                gaps.append(f"{name}:waiver accounting invalid")

    gates = coverage["gates"]
    gate_expectations = {
        "open_p0": 0,
        "open_p1": 0,
        "unwaived_inventory_diff": 0,
        "unresolved_contradictions": 0,
    }
    for key, expected in gate_expectations.items():
        if gates.get(key) != expected:
            gaps.append(f"gate:{key}={gates.get(key)} expected {expected}")

    if gates.get("consecutive_deep_runs_without_new_p0_p1", 0) < 2:
        gaps.append("gate:need at least two consecutive deep runs without new P0/P1")
    if not gates.get("subject_stable", False):
        gaps.append("gate:subject is not stable")
    if not gates.get("rollback_verified", False):
        gaps.append("gate:rollback/recovery is not verified")
    if not evidence_index.get("artifacts"):
        gaps.append("evidence:index is empty")

    tests = [item for item in test_matrix.get("tests", []) if isinstance(item, dict)]
    successful_critical_tests = [
        item
        for item in tests
        if item.get("critical") and item.get("status") == "OBSERVED_EXPECTED"
    ]
    critical_targets = {
        item.get("id")
        for item in surface.get("nodes", [])
        if isinstance(item, dict) and item.get("critical") and item.get("id")
    } | {
        item.get("id")
        for item in journey.get("states", [])
        if isinstance(item, dict) and item.get("critical") and item.get("id")
    } | {
        item.get("id")
        for item in journey.get("transitions", [])
        if isinstance(item, dict) and item.get("critical") and item.get("id")
    } | {
        item.get("id")
        for item in fault_graph.get("faults", [])
        if isinstance(item, dict) and item.get("critical") and item.get("id")
    }
    tested_targets = {
        target
        for test in successful_critical_tests
        for target in test.get("target_ids", [])
        if isinstance(target, str)
    }
    missing_targets = critical_targets - tested_targets
    if missing_targets:
        gaps.append("test-matrix:critical targets without successful test: " + ",".join(sorted(missing_targets)))

    critical_oracles = {
        item.get("oracle_id"): item
        for item in oracle_catalog.get("oracles", [])
        if isinstance(item, dict) and item.get("critical") and item.get("oracle_id")
    }
    tested_oracles = {
        oracle_id
        for test in successful_critical_tests
        for oracle_id in test.get("oracle_ids", [])
        if isinstance(oracle_id, str)
    }
    missing_oracles = set(critical_oracles) - tested_oracles
    if missing_oracles:
        gaps.append("oracle:critical oracles without successful test: " + ",".join(sorted(missing_oracles)))
    non_independent_oracles = {
        oracle_id
        for oracle_id, oracle in critical_oracles.items()
        if not oracle.get("independent_from_generator")
    }
    if non_independent_oracles:
        gaps.append("oracle:critical oracles are not independent: " + ",".join(sorted(non_independent_oracles)))
    oracle_without_evidence = {
        oracle_id
        for oracle_id, oracle in critical_oracles.items()
        if not oracle.get("evidence_refs")
    }
    if oracle_without_evidence:
        gaps.append("oracle:critical oracles lack evidence: " + ",".join(sorted(oracle_without_evidence)))

    unfinished_critical_tests = {
        item.get("test_id", "<missing>")
        for item in tests
        if item.get("critical") and item.get("status") not in {"OBSERVED_EXPECTED", "WAIVED"}
    }
    if unfinished_critical_tests:
        gaps.append("test-matrix:critical tests incomplete: " + ",".join(sorted(unfinished_critical_tests)))
    effective_negative_controls = {
        item.get("test_id", "<missing>")
        for item in tests
        if item.get("critical")
        and item.get("negative_control")
        and item.get("negative_control_effective")
        and item.get("evidence_refs")
    }
    if critical_targets and not effective_negative_controls:
        gaps.append("test-matrix:no effective negative control proves the critical suite can fail")

    poka_actions = [item for item in poka_yoke.get("actions", []) if isinstance(item, dict)]
    critical_poka_actions = [item for item in poka_actions if item.get("critical")]
    if not critical_poka_actions:
        gaps.append("poka-yoke:no high-loss operation audit recorded")
    else:
        incomplete_poka = {
            item.get("action_id", "<missing>")
            for item in critical_poka_actions
            if item.get("status") not in {"OBSERVED_EXPECTED", "WAIVED"}
            or (item.get("status") == "OBSERVED_EXPECTED" and not item.get("evidence_refs"))
        }
        if incomplete_poka:
            gaps.append("poka-yoke:audits incomplete: " + ",".join(sorted(incomplete_poka)))

    pending_provenance = sorted(
        item.get("id", "<missing>")
        for item in provenance.get("items", [])
        if isinstance(item, dict) and item.get("review_status") == "PENDING"
    )
    if pending_provenance:
        gaps.append("provenance:pending reviews: " + ",".join(pending_provenance))

    if contract.get("competitor_research_required", True):
        references = [item for item in competitor.get("references", []) if isinstance(item, dict)]
        classes = {item.get("class") for item in references}
        if len(references) < 3:
            gaps.append("competitor:need at least three evidence-backed reference products/workarounds")
        if "OSS_ANALOGUE" not in classes:
            gaps.append("competitor:missing open-source analogue")
        if not classes.intersection({"DIRECT", "ADJACENT", "SUBSTITUTE"}):
            gaps.append("competitor:missing direct/adjacent/substitute reference")
        if not competitor.get("benchmark_tasks"):
            gaps.append("competitor:no same-task benchmark recorded")
        if not competitor.get("decisions"):
            gaps.append("competitor:no adopt/reject/differentiate decision recorded")

    field_required = bool(gates.get("field_validation_required"))
    field_complete = bool(gates.get("field_validation_complete"))
    field_gap = field_required and not field_complete
    non_field_gaps = [gap for gap in gaps if not gap.startswith("field:")]
    if field_gap:
        gaps.append("field:required validation is incomplete")

    if not gaps:
        status = "READY_FOR_VERIFIER"
    elif field_gap and not non_field_gaps:
        status = "FIELD_VALIDATION_PENDING"
    else:
        status = "MORE_EVIDENCE_REQUIRED"

    if status not in ALLOWED_STATUSES:
        raise PRLError(f"Internal invalid status: {status}")

    return {
        "status": status,
        "run_id": contract.get("run_id"),
        "subject": contract.get("subject"),
        "errors": [],
        "warnings": warnings,
        "gaps": gaps,
        "dimensions": dimension_results,
        "gates": copy.deepcopy(gates),
        "field_validation": {"required": field_required, "complete": field_complete},
    }


def evidence_kind(path: Path) -> str:
    suffix = path.suffix.lower()
    return {
        ".json": "json",
        ".log": "log",
        ".txt": "text",
        ".md": "markdown",
        ".png": "screenshot",
        ".jpg": "screenshot",
        ".jpeg": "screenshot",
        ".webm": "video",
        ".zip": "archive",
        ".html": "report",
        ".xml": "report",
    }.get(suffix, "artifact")


def index_evidence(workspace: Path, evidence_class: str, tool: str) -> dict[str, Any]:
    workspace = workspace.resolve()
    contract = load_json(workspace / "run_contract.json")
    evidence_dir = workspace / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    index_path = evidence_dir / "index.json"
    existing_by_path: dict[str, dict[str, Any]] = {}
    if index_path.is_file():
        try:
            existing_index = load_json(index_path)
            existing_by_path = {
                item.get("path"): item
                for item in existing_index.get("artifacts", [])
                if isinstance(item, dict) and isinstance(item.get("path"), str)
            }
        except PRLError:
            existing_by_path = {}
    artifacts: list[dict[str, Any]] = []
    for path in sorted(evidence_dir.rglob("*")):
        if not path.is_file() or path.name == "index.json" or path.name.endswith(".tmp"):
            continue
        if path.is_symlink():
            raise PRLError(f"Evidence symlinks are forbidden: {path}")
        relative = path.relative_to(workspace).as_posix()
        digest = sha256_file(path)
        identity_digest = hashlib.sha256(f"{relative}\0{digest}".encode("utf-8")).hexdigest()
        evidence_id = f"EV-{identity_digest[:16]}"
        previous = existing_by_path.get(relative, {})
        unchanged = previous.get("sha256") == digest
        artifacts.append({
            "evidence_id": evidence_id,
            "path": relative,
            "sha256": digest,
            "kind": evidence_kind(path),
            "created_at": previous.get("created_at") if unchanged else utc_now(),
            "subject_ref": contract["subject"]["ref"],
            "tool": previous.get("tool", tool) if unchanged else tool,
            "evidence_class": previous.get("evidence_class", evidence_class) if unchanged else evidence_class,
        })
    index = {
        "schema_version": SCHEMA_VERSION,
        "run_id": contract["run_id"],
        "artifacts": artifacts,
    }
    atomic_write_json(index_path, index)
    return index


def coverage_item_id(dimension: str, source_ref: str) -> str:
    digest = hashlib.sha256(f"{dimension}:{source_ref}".encode("utf-8")).hexdigest()[:12]
    return f"COV-{dimension.upper()}-{digest}"


def recalculate_dimension(dimension: dict[str, Any]) -> None:
    items = [item for item in dimension.get("items", []) if isinstance(item, dict)]
    dimension["critical_total"] = sum(1 for item in items if item.get("critical") is True)
    dimension["critical_covered"] = sum(
        1 for item in items if item.get("critical") is True and item.get("status") == "COVERED"
    )
    dimension["critical_waived"] = sum(
        1 for item in items if item.get("critical") is True and item.get("status") == "WAIVED"
    )
    dimension["noncritical_total"] = sum(1 for item in items if item.get("critical") is False)
    dimension["noncritical_covered"] = sum(
        1 for item in items if item.get("critical") is False and item.get("status") == "COVERED"
    )
    dimension["evidence_refs"] = sorted(
        {
            ref
            for item in items
            for ref in item.get("evidence_refs", [])
            if isinstance(ref, str) and ref
        }
    )
    dimension["waiver_ids"] = sorted(
        {
            item.get("waiver_id")
            for item in items
            if item.get("status") == "WAIVED" and isinstance(item.get("waiver_id"), str)
        }
    )


def build_inventory(workspace: Path) -> dict[str, dict[str, dict[str, Any]]]:
    """Build dimension inventories with criticality and evidence derivation."""
    surface = load_json(workspace / "surface_graph.json")
    journey = load_json(workspace / "journey_state_graph.json")
    fault_graph = load_json(workspace / "fault_graph.json")
    oracle_catalog = load_json(workspace / "oracle_catalog.json")
    test_matrix = load_json(workspace / "test_matrix.json")
    evidence_index = load_json(workspace / "evidence/index.json")

    inventory: dict[str, dict[str, dict[str, Any]]] = {name: {} for name in DIMENSIONS}

    for node in surface.get("nodes", []):
        if not isinstance(node, dict) or not node.get("id"):
            continue
        inventory["surface"][node["id"]] = {
            "critical": bool(node.get("critical")),
            "evidence_refs": list(node.get("evidence_refs", [])),
        }
        for role in node.get("roles", []):
            if not isinstance(role, str) or not role:
                continue
            current = inventory["role"].setdefault(role, {"critical": False, "evidence_refs": []})
            current["critical"] = current["critical"] or bool(node.get("critical"))
            current["evidence_refs"] = sorted(set(current["evidence_refs"]) | set(node.get("evidence_refs", [])))

    for state in journey.get("states", []):
        if not isinstance(state, dict) or not state.get("id"):
            continue
        inventory["state"][state["id"]] = {
            "critical": bool(state.get("critical")),
            "evidence_refs": list(state.get("evidence_refs", [])),
        }
        role = state.get("role")
        if isinstance(role, str) and role:
            current = inventory["role"].setdefault(role, {"critical": False, "evidence_refs": []})
            current["critical"] = current["critical"] or bool(state.get("critical"))
            current["evidence_refs"] = sorted(set(current["evidence_refs"]) | set(state.get("evidence_refs", [])))

    for transition in journey.get("transitions", []):
        if not isinstance(transition, dict) or not transition.get("id"):
            continue
        inventory["transition"][transition["id"]] = {
            "critical": bool(transition.get("critical")),
            "evidence_refs": list(transition.get("evidence_refs", [])),
        }

    fault_evidence: dict[str, set[str]] = {}
    for experiment in fault_graph.get("experiments", []):
        if not isinstance(experiment, dict) or not experiment.get("fault_id"):
            continue
        fault_evidence.setdefault(experiment["fault_id"], set()).update(experiment.get("evidence_refs", []))
    for fault in fault_graph.get("faults", []):
        if not isinstance(fault, dict) or not fault.get("id"):
            continue
        inventory["fault"][fault["id"]] = {
            "critical": bool(fault.get("critical")),
            "evidence_refs": sorted(fault_evidence.get(fault["id"], set())),
        }

    for oracle in oracle_catalog.get("oracles", []):
        if not isinstance(oracle, dict) or not oracle.get("oracle_id"):
            continue
        inventory["oracle"][oracle["oracle_id"]] = {
            "critical": bool(oracle.get("critical")),
            "evidence_refs": list(oracle.get("evidence_refs", [])),
        }

    for test in test_matrix.get("tests", []):
        if not isinstance(test, dict):
            continue
        condition = test.get("data_condition")
        if isinstance(condition, str) and condition:
            current = inventory["data"].setdefault(condition, {"critical": False, "evidence_refs": []})
            current["critical"] = current["critical"] or bool(test.get("critical"))
            current["evidence_refs"] = sorted(set(current["evidence_refs"]) | set(test.get("evidence_refs", [])))

    critical_evidence: set[str] = set()
    for dimension_name in ("surface", "state", "transition", "role", "data", "fault", "oracle"):
        for source in inventory[dimension_name].values():
            if source.get("critical"):
                critical_evidence.update(source.get("evidence_refs", []))
    for test in test_matrix.get("tests", []):
        if isinstance(test, dict) and test.get("critical"):
            critical_evidence.update(test.get("evidence_refs", []))
    for artifact in evidence_index.get("artifacts", []):
        if not isinstance(artifact, dict) or not artifact.get("evidence_id"):
            continue
        evidence_id = artifact["evidence_id"]
        inventory["evidence"][evidence_id] = {
            "critical": evidence_id in critical_evidence,
            "evidence_refs": [evidence_id],
        }
    return inventory


def sync_coverage_inventory(workspace: Path, auto_cover_evidenced: bool = False) -> dict[str, int]:
    """Reconcile item-level coverage against the current catalogs without hiding removals."""
    workspace = workspace.resolve()
    coverage = load_json(workspace / "coverage_ledger.json")
    inventory = build_inventory(workspace)
    counts: dict[str, int] = {}
    for name in DIMENSIONS:
        dimension = coverage["dimensions"][name]
        existing = {
            item.get("source_ref"): item
            for item in dimension.get("items", [])
            if isinstance(item, dict) and isinstance(item.get("source_ref"), str)
        }
        items: list[dict[str, Any]] = []
        for source_ref, source in sorted(inventory[name].items()):
            previous = existing.get(source_ref, {})
            refs = sorted(
                {
                    ref
                    for ref in list(previous.get("evidence_refs", [])) + list(source.get("evidence_refs", []))
                    if isinstance(ref, str) and ref
                }
            )
            status = previous.get("status", "UNCOVERED")
            waiver_id = previous.get("waiver_id")
            if status == "COVERED" and not refs:
                status = "UNCOVERED"
            if auto_cover_evidenced and refs and status != "WAIVED":
                status = "COVERED"
            item = {
                "item_id": previous.get("item_id") or coverage_item_id(name, source_ref),
                "source_ref": source_ref,
                "critical": bool(source.get("critical")),
                "status": status,
                "evidence_refs": refs,
                "waiver_id": waiver_id if status == "WAIVED" else None,
                "notes": previous.get("notes", ""),
            }
            items.append(item)
        dimension["items"] = items
        recalculate_dimension(dimension)
        counts[name] = len(items)
    atomic_write_json(workspace / "coverage_ledger.json", coverage)
    return counts


def create_handoff(workspace: Path) -> Path:
    workspace = workspace.resolve()
    readiness = evaluate_readiness(workspace)
    if readiness["status"] != "READY_FOR_VERIFIER":
        raise PRLError(
            "Cannot create verifier handoff. Current status: "
            f"{readiness['status']}; gaps: {readiness.get('gaps', [])}"
        )
    contract = load_json(workspace / "run_contract.json")
    coverage = load_json(workspace / "coverage_ledger.json")
    evidence_index = load_json(workspace / "evidence/index.json")
    residual = workspace / "residual_risk.md"
    if not residual.is_file():
        raise PRLError("Missing residual_risk.md")

    intake = {
        "schema_version": SCHEMA_VERSION,
        "status": "READY_FOR_VERIFIER",
        "generated_at": utc_now(),
        "run_id": contract["run_id"],
        "subject": contract["subject"],
        "run_contract_sha256": sha256_file(workspace / "run_contract.json"),
        "coverage_status": readiness["dimensions"],
        "evidence_index_sha256": sha256_file(workspace / "evidence/index.json"),
        "open_p0": 0,
        "open_p1": 0,
        "field_validation": readiness["field_validation"],
        "waivers": coverage.get("waivers", []),
        "residual_risk_ref": "residual_risk.md",
        "tool_manifest": contract.get("tool_manifest", []),
        "model_manifest": contract.get("model_manifest", []),
        "readiness_calculation_version": READINESS_CALCULATION_VERSION,
    }
    output = workspace / "verifier_intake.json"
    atomic_write_json(output, intake)
    return output


def populate_selftest_ready_workspace(workspace: Path) -> None:
    evidence_file = workspace / "evidence" / "selftest.txt"
    evidence_file.write_text("Product Reality Lab self-test evidence.\n", encoding="utf-8")
    index = index_evidence(workspace, "SYNTHETIC", "prl-selftest")
    evidence_id = index["artifacts"][0]["evidence_id"]

    contract = load_json(workspace / "run_contract.json")
    contract["authorization"]["owner"] = "selftest-owner"
    atomic_write_json(workspace / "run_contract.json", contract)

    graph = load_json(workspace / "surface_graph.json")
    graph["nodes"] = [{
        "id": "NODE-1", "kind": "task", "name": "selftest", "source_visibility": True,
        "runtime_visibility": True, "critical": True, "roles": ["selftest"], "flags": [],
        "evidence_refs": [evidence_id], "waiver_id": None,
    }]
    graph["edges"] = [{
        "id": "EDGE-1", "from": "NODE-1", "to": "NODE-1", "action": "assert",
        "critical": True, "destructive": False, "preconditions": [], "side_effects": [],
        "oracle_ids": ["ORACLE-1"], "evidence_refs": [evidence_id], "waiver_id": None,
    }]
    atomic_write_json(workspace / "surface_graph.json", graph)

    journey = load_json(workspace / "journey_state_graph.json")
    journey["states"] = [{
        "id": "STATE-1", "task": "selftest", "critical": True, "role": "selftest",
        "auth": "test", "tenant": "test", "flags": [], "fixture": "fixture:selftest",
        "browser_device": "cli", "locale_timezone": "zh-CN/Australia-Sydney",
        "world_state_digest": "selftest-world", "evidence_refs": [evidence_id],
    }]
    journey["transitions"] = [{
        "id": "TRANS-1", "from": "STATE-1", "to": "STATE-1", "action": "assert",
        "critical": True, "failure_mode": "selftest assertion fails", "recovery_transition_id": "TRANS-1",
        "oracle_ids": ["ORACLE-1"], "evidence_refs": [evidence_id],
    }]
    atomic_write_json(workspace / "journey_state_graph.json", journey)

    fault = load_json(workspace / "fault_graph.json")
    fault["steady_states"] = [{
        "id": "STEADY-1", "claim": "selftest remains observable", "oracle_ids": ["ORACLE-1"],
        "evidence_refs": [evidence_id],
    }]
    fault["faults"] = [{
        "id": "FAULT-1", "class": "negative-control", "target": "NODE-1", "critical": True,
        "expected_effect": "oracle detects the injected failure", "expected_recovery": "fixture reset",
    }]
    fault["experiments"] = [{
        "id": "FEXP-1", "fault_id": "FAULT-1", "steady_state_id": "STEADY-1",
        "blast_radius": "disposable selftest", "abort": "stop process", "rollback": "recreate temp directory",
        "status": "OBSERVED_EXPECTED", "evidence_refs": [evidence_id],
    }]
    atomic_write_json(workspace / "fault_graph.json", fault)

    oracle = load_json(workspace / "oracle_catalog.json")
    oracle["oracles"] = [{
        "oracle_id": "ORACLE-1", "type": "deterministic-invariant", "claim": "selftest evidence exists",
        "independent_from_generator": True, "procedure": "hash and re-read the evidence file",
        "expected": "hash matches index", "critical": True, "evidence_refs": [evidence_id],
    }]
    atomic_write_json(workspace / "oracle_catalog.json", oracle)

    matrix = load_json(workspace / "test_matrix.json")
    matrix["tests"] = [{
        "test_id": "TEST-1", "requirement_or_claim": "selftest catalogs are evidence-backed",
        "risk": "false readiness", "target_ids": ["NODE-1", "STATE-1", "TRANS-1", "FAULT-1"],
        "data_condition": "fixture:selftest", "fault_condition": "negative-control",
        "action_sequence": ["create evidence", "index evidence", "validate hash"],
        "oracle_ids": ["ORACLE-1"], "priority": 1.0, "adapter": "stdlib-selftest",
        "critical": True, "status": "OBSERVED_EXPECTED", "negative_control": True,
        "negative_control_effective": True, "evidence_refs": [evidence_id], "defect_ids": [],
    }]
    atomic_write_json(workspace / "test_matrix.json", matrix)

    poka = load_json(workspace / "poka_yoke_audit.json")
    poka["actions"] = [{
        "action_id": "PY-1", "name": "create verifier handoff", "loss_if_wrong": "false release confidence",
        "critical": True,
        "defenses": [{"type": "readiness gate", "control": "handoff rejects incomplete runs"}],
        "attack_cases": [{"case": "manually inflate counters", "expected": "derived-count validation blocks"}],
        "status": "OBSERVED_EXPECTED", "evidence_refs": [evidence_id], "defect_ids": [],
    }]
    atomic_write_json(workspace / "poka_yoke_audit.json", poka)

    competitor = load_json(workspace / "competitor_evidence.json")
    competitor["references"] = [
        {
            "competitor_id": "COMP-DIRECT", "name": "direct reference", "class": "DIRECT",
            "sources": [{"source_id": "SRC-DIRECT", "url": "https://example.invalid/direct",
                         "source_type": "selftest fixture", "accessed_at": utc_now(),
                         "public_or_authorized": True, "claim": "direct reference exists",
                         "evidence_excerpt_or_summary": "selftest only", "confidence": 1.0,
                         "evidence_ref": evidence_id}],
            "capabilities": ["benchmark"], "known_pain_points": [],
        },
        {
            "competitor_id": "COMP-ADJACENT", "name": "adjacent reference", "class": "ADJACENT",
            "sources": [{"source_id": "SRC-ADJACENT", "url": "https://example.invalid/adjacent",
                         "source_type": "selftest fixture", "accessed_at": utc_now(),
                         "public_or_authorized": True, "claim": "adjacent reference exists",
                         "evidence_excerpt_or_summary": "selftest only", "confidence": 1.0,
                         "evidence_ref": evidence_id}],
            "capabilities": ["workflow"], "known_pain_points": [],
        },
        {
            "competitor_id": "COMP-OSS", "name": "open-source analogue", "class": "OSS_ANALOGUE",
            "sources": [{"source_id": "SRC-OSS", "url": "https://example.invalid/oss",
                         "source_type": "selftest fixture", "accessed_at": utc_now(),
                         "public_or_authorized": True, "claim": "OSS reference exists",
                         "evidence_excerpt_or_summary": "selftest only", "confidence": 1.0,
                         "evidence_ref": evidence_id}],
            "capabilities": ["provenance"], "known_pain_points": [],
        },
    ]
    competitor["benchmark_tasks"] = [{
        "task_id": "BENCH-1", "task": "validate an evidence-backed run",
        "starting_state": "initialized run", "inputs": {"subject": "selftest"},
        "metrics": ["readiness integrity"], "results": {"selftest": "expected"},
        "evidence_refs": [evidence_id],
    }]
    competitor["decisions"] = [{
        "decision_id": "DEC-1", "capability": "evidence ledger", "decision": "ADOPT",
        "rationale": "preserves independent verifier boundary", "owner": "selftest-owner",
        "evidence_refs": [evidence_id],
    }]
    atomic_write_json(workspace / "competitor_evidence.json", competitor)

    provenance = load_json(workspace / "provenance_ledger.json")
    provenance["items"] = [{
        "id": "OSS-1", "source": "selftest fixture", "version_or_commit": "selftest",
        "license": "NONE-SYNTHETIC", "copyright_or_notice": "synthetic selftest fixture",
        "use": "exercise provenance validation", "modified_files": [],
        "allowed_use_basis": "generated fixture", "review_status": "APPROVED",
        "reviewer": "selftest-reviewer", "reviewed_at": utc_now(),
        "evidence_refs": [evidence_id],
    }]
    atomic_write_json(workspace / "provenance_ledger.json", provenance)

    sync_coverage_inventory(workspace, auto_cover_evidenced=True)
    coverage = load_json(workspace / "coverage_ledger.json")
    coverage["gates"]["consecutive_deep_runs_without_new_p0_p1"] = 2
    coverage["gates"]["field_validation_complete"] = False
    atomic_write_json(workspace / "coverage_ledger.json", coverage)


def run_selftest() -> None:
    with tempfile.TemporaryDirectory(prefix="prl-selftest-") as temp:
        workspace = Path(temp) / "run"
        initialize_workspace(workspace, "selftest", "selftest-ref", owner="selftest-owner")
        initial = evaluate_readiness(workspace)
        if initial["status"] != "MORE_EVIDENCE_REQUIRED":
            raise PRLError(f"Selftest expected initial MORE_EVIDENCE_REQUIRED, got {initial['status']}")
        populate_selftest_ready_workspace(workspace)
        errors, _warnings = validate_workspace(workspace)
        if errors:
            raise PRLError(f"Selftest validation failed: {errors}")
        readiness = evaluate_readiness(workspace)
        if readiness["status"] != "READY_FOR_VERIFIER":
            raise PRLError(f"Selftest expected READY_FOR_VERIFIER, got {readiness}")
        handoff = create_handoff(workspace)
        intake = load_json(handoff)
        if intake.get("status") != "READY_FOR_VERIFIER":
            raise PRLError("Selftest handoff status mismatch")
    print(json.dumps({"selftest": "ok", "skill_version": "0.0.0.3"}, ensure_ascii=False))


def print_json(data: dict[str, Any]) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="prl", description="Product Reality Lab run helper")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="Initialize a Reality Lab workspace")
    init.add_argument("--workspace", required=True, type=Path)
    init.add_argument("--subject-name", required=True)
    init.add_argument("--subject-ref", required=True)
    init.add_argument("--subject-kind", default="commit", choices=["commit", "deployment", "artifact", "workspace", "other"])
    init.add_argument("--owner", default="OWNER_REQUIRED")
    init.add_argument("--field-required", action="store_true")
    init.add_argument("--force", action="store_true")

    validate = sub.add_parser("validate", help="Validate workspace consistency")
    validate.add_argument("--workspace", required=True, type=Path)
    validate.add_argument("--skip-evidence-hash", action="store_true")

    score = sub.add_parser("score", help="Evaluate non-adjudicative readiness")
    score.add_argument("--workspace", required=True, type=Path)

    index = sub.add_parser("index-evidence", help="Hash and index files under evidence/")
    index.add_argument("--workspace", required=True, type=Path)
    index.add_argument("--evidence-class", default="SYNTHETIC", choices=["SYNTHETIC", "CONTROLLED_HUMAN", "FIELD_OBSERVED"])
    index.add_argument("--tool", default="unspecified")

    sync = sub.add_parser("sync-coverage", help="Reconcile item-level coverage with product catalogs")
    sync.add_argument("--workspace", required=True, type=Path)
    sync.add_argument(
        "--auto-cover-evidenced",
        action="store_true",
        help="Mark catalog items covered only when they already carry indexed evidence references",
    )

    handoff = sub.add_parser("handoff", help="Create verifier_intake.json only when ready")
    handoff.add_argument("--workspace", required=True, type=Path)

    sub.add_parser("selftest", help="Run an isolated built-in self-test")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        if args.command == "init":
            run_id = initialize_workspace(
                args.workspace,
                args.subject_name,
                args.subject_ref,
                subject_kind=args.subject_kind,
                owner=args.owner,
                field_required=args.field_required,
                force=args.force,
            )
            print_json({"status": "MORE_EVIDENCE_REQUIRED", "run_id": run_id, "workspace": str(args.workspace.resolve()), "next_action": "Complete run_contract.json and inventory the product surface."})
            return 0
        if args.command == "validate":
            errors, warnings = validate_workspace(args.workspace, verify_evidence_hashes=not args.skip_evidence_hash)
            print_json({"valid": not errors, "errors": errors, "warnings": warnings})
            return 0 if not errors else 2
        if args.command == "score":
            print_json(evaluate_readiness(args.workspace))
            return 0
        if args.command == "index-evidence":
            result = index_evidence(args.workspace, args.evidence_class, args.tool)
            print_json({"indexed": len(result["artifacts"]), "index": str((args.workspace / "evidence/index.json").resolve())})
            return 0
        if args.command == "sync-coverage":
            counts = sync_coverage_inventory(
                args.workspace,
                auto_cover_evidenced=args.auto_cover_evidenced,
            )
            print_json({
                "status": "MORE_EVIDENCE_REQUIRED",
                "workspace": str(args.workspace.resolve()),
                "inventory_counts": counts,
                "next_action": "Review item-level coverage statuses, evidence references, and waivers before scoring.",
            })
            return 0
        if args.command == "handoff":
            output = create_handoff(args.workspace)
            print_json({"status": "READY_FOR_VERIFIER", "output": str(output.resolve()), "next_action": "Invoke verifier in an independent adjudication context."})
            return 0
        if args.command == "selftest":
            run_selftest()
            return 0
        parser.error(f"Unknown command: {args.command}")
    except PRLError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 4
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
