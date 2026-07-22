"""Mode/Metric/basis-specific input sufficiency before source-body reads."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Tuple

import yaml

from .inventory import InventoryEntry, match_inventory_entries
from .manifest import InputManifest, ManifestError, validate_manifest_request
from .paths import PathSafetyError, atomic_output_directory
from .resolutions import (
    ALLOWED_RESOLUTIONS,
    EVIDENCE_REQUIRED,
    INSTRUCTION_REQUIRED,
    InputResolution,
    ResolutionError,
    validate_resolution_bindings,
)


VALID_MODES = frozenset({"inventory", "reference-replay", "calculate", "review", "restate"})
VALID_CLASSIFICATIONS = frozenset({"NON_WAIVABLE", "SCOPE_DEPENDENT", "OPTIONAL_PRESENTATION"})
VALID_OBSERVED_STATUSES = frozenset({"PRESENT", "MISSING", "CONFLICT", "UNSAFE", "NOT_IN_SCOPE"})
RESOLUTION_OPTION_NUMBERS = {
    "SUPPLIED": 1,
    "SCOPE_REDUCED": 2,
    "QUALIFIED_ALTERNATE_EVIDENCE": 3,
    "OMIT_OPTIONAL_PRESENTATION": 4,
    "BLOCKED": 5,
}
RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
EXPECTED_GLOBAL_REQUIREMENTS = frozenset(
    {"RUN_MODE", "PROJECT_SCOPE", "AS_OF_DATE", "METRIC_AND_BASIS", "RAW_ROOT_AND_MANIFEST", "SAFE_READ_AND_DIGEST", "OUTPUT_DIRECTORY"}
)
DEPENDENCY_FIELDS = frozenset(
    {
        "required_slots",
        "required_policy_refs",
        "required_basis_ids",
        "required_component_metrics",
        "conditional_component_metrics",
    }
)
EXPECTED_PAYROLL_INPUTS = frozenset(
    {
        "effective_dated_pay_component_registry",
        "payroll_period_control_total",
        "qualified_employee_identity",
        "approved_time_or_day_source",
        "project_entity_wbs_mapping",
        "allocation_and_residual_rule",
        "unallocated_payroll_pool",
    }
)
EXPECTED_PAYROLL_PROHIBITIONS = frozenset(
    {"guessed_pay_components", "inferred_day_rate", "historical_result_backsolve", "automatic_unallocated_spread"}
)


class InputGateError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__("%s: %s" % (code, message))
        self.code = code
        self.message = message


@dataclass(frozen=True)
class RequirementRule:
    requirement_id: str
    classification: str
    applies_to_modes: Tuple[str, ...]
    allowed_resolutions: Tuple[str, ...]


@dataclass(frozen=True)
class InputRequirements:
    rules: Tuple[RequirementRule, ...]
    mode_dependencies: Mapping[str, Mapping[str, Any]]
    metric_dependencies: Mapping[str, Mapping[str, Any]]
    no_response_is_permission: bool
    content_sha256: str

    @classmethod
    def from_yaml(cls, path: Path) -> "InputRequirements":
        data = _read_public_config(path, "input requirements")
        try:
            raw = yaml.safe_load(data.decode("utf-8"))
        except (UnicodeError, yaml.YAMLError) as exc:
            raise InputGateError("INPUT_REQUIREMENTS_PARSE", "input requirements are not valid UTF-8 YAML") from exc
        if not isinstance(raw, dict) or raw.get("schema_version") != "kmfa.project_cost.input_requirements.v1":
            raise InputGateError("INPUT_REQUIREMENTS_SCHEMA", "input requirements schema version is unsupported")
        expected_top_fields = {
            "schema_version",
            "default_output_directory",
            "missing_input_user_options",
            "resolution_policy",
            "global_requirements",
            "mode_dependencies",
            "metric_dependencies",
            "payroll_model",
        }
        if set(raw) != expected_top_fields or raw.get("default_output_directory") != "<private_runtime>/runs/<run_id>/outputs":
            raise InputGateError("INPUT_REQUIREMENTS_SCHEMA", "input requirement fields or default output contract drifted")
        if tuple(raw.get("missing_input_user_options", ())) != tuple(RESOLUTION_OPTION_NUMBERS):
            raise InputGateError("INPUT_RESOLUTION_OPTIONS_DRIFT", "missing-input options differ from the registered choices")
        raw_rules = raw.get("global_requirements")
        if not isinstance(raw_rules, list) or not raw_rules:
            raise InputGateError("INPUT_REQUIREMENTS_RULES", "global input requirements are missing")
        rules = []
        seen = set()
        for item in raw_rules:
            if not isinstance(item, dict):
                raise InputGateError("INPUT_REQUIREMENTS_RULE", "input requirement must be a mapping")
            requirement_id = _required_text(item.get("requirement_id"), "requirement_id")
            classification = _required_text(item.get("classification"), "classification")
            modes = _required_string_list(item.get("applies_to_modes"), "applies_to_modes")
            resolutions = _required_string_list(item.get("allowed_resolutions"), "allowed_resolutions")
            if (
                requirement_id in seen
                or classification not in VALID_CLASSIFICATIONS
                or not set(modes) <= VALID_MODES
                or not set(resolutions) <= ALLOWED_RESOLUTIONS.get(classification, frozenset())
            ):
                raise InputGateError("INPUT_REQUIREMENTS_RULE", "input requirement definition is invalid or duplicated")
            seen.add(requirement_id)
            rules.append(RequirementRule(requirement_id, classification, modes, resolutions))
        if seen != EXPECTED_GLOBAL_REQUIREMENTS:
            raise InputGateError("INPUT_REQUIREMENTS_RULES", "the mandatory global requirement set is incomplete")
        policy = raw.get("resolution_policy")
        if not isinstance(policy, dict) or set(policy) != {
            "explicit_user_instruction_required_for",
            "evidence_ref_required_for",
            "supplied_input_requires_rescan_to_present",
            "no_response_is_permission",
            "non_waivable_omission_allowed",
        }:
            raise InputGateError("INPUT_RESOLUTION_POLICY", "no-response policy must be explicit boolean")
        if (
            set(_required_string_list(policy.get("explicit_user_instruction_required_for"), "instruction choices"))
            != INSTRUCTION_REQUIRED
            or set(_required_string_list(policy.get("evidence_ref_required_for"), "evidence choices"))
            != EVIDENCE_REQUIRED
            or policy.get("supplied_input_requires_rescan_to_present") is not True
            or policy.get("no_response_is_permission") is not False
            or policy.get("non_waivable_omission_allowed") is not False
        ):
            raise InputGateError("INPUT_RESOLUTION_POLICY_RELAXED", "no response and non-waivable omission must remain forbidden")
        mode_dependencies = raw.get("mode_dependencies")
        metric_dependencies = raw.get("metric_dependencies")
        if not isinstance(mode_dependencies, dict) or not isinstance(metric_dependencies, dict):
            raise InputGateError("INPUT_DEPENDENCIES_INVALID", "mode and Metric dependencies are required")
        if set(mode_dependencies) != VALID_MODES:
            raise InputGateError("INPUT_DEPENDENCIES_INVALID", "mode dependency set is incomplete or unknown")
        validated_modes: Dict[str, Dict[str, Tuple[str, ...]]] = {}
        for mode_id, dependency in mode_dependencies.items():
            if not isinstance(dependency, dict) or set(dependency) != {"required_slots"}:
                raise InputGateError("INPUT_DEPENDENCIES_INVALID", "mode dependency fields are invalid")
            validated_modes[mode_id] = {
                "required_slots": _optional_string_list(dependency.get("required_slots"), "required_slots")
            }
        validated_metrics: Dict[str, Dict[str, Tuple[str, ...]]] = {}
        for metric_id, dependency in metric_dependencies.items():
            if not isinstance(metric_id, str) or not metric_id or not isinstance(dependency, dict):
                raise InputGateError("METRIC_DEPENDENCY_INVALID", "Metric dependency must be a named mapping")
            if not set(dependency) <= DEPENDENCY_FIELDS:
                raise InputGateError("METRIC_DEPENDENCY_INVALID", "Metric dependency contains unknown fields")
            validated_metrics[metric_id] = {
                field: _optional_string_list(dependency.get(field), field)
                for field in sorted(dependency)
            }
            required_components = set(validated_metrics[metric_id].get("required_component_metrics", ()))
            conditional_components = set(validated_metrics[metric_id].get("conditional_component_metrics", ()))
            if required_components & conditional_components:
                raise InputGateError("METRIC_DEPENDENCY_INVALID", "required and conditional components overlap")
        payroll = raw.get("payroll_model")
        if (
            not isinstance(payroll, dict)
            or set(payroll) != {"model_id", "classification", "required_inputs", "prohibited_defaults"}
            or payroll.get("model_id") != "FULLY_LOADED_EMPLOYER_COST_WITH_APPROVED_TIME"
            or payroll.get("classification") != "NON_WAIVABLE_WHEN_PAYROLL_IN_SCOPE"
            or set(_required_string_list(payroll.get("required_inputs"), "payroll required inputs"))
            != EXPECTED_PAYROLL_INPUTS
            or set(_required_string_list(payroll.get("prohibited_defaults"), "payroll prohibited defaults"))
            != EXPECTED_PAYROLL_PROHIBITIONS
        ):
            raise InputGateError("PAYROLL_INPUT_CONTRACT_RELAXED", "fully loaded payroll input contract drifted")
        return cls(
            rules=tuple(rules),
            mode_dependencies=validated_modes,
            metric_dependencies=validated_metrics,
            no_response_is_permission=False,
            content_sha256=hashlib.sha256(data).hexdigest(),
        )

    def rule_map(self) -> Dict[str, RequirementRule]:
        return {item.requirement_id: item for item in self.rules}


@dataclass(frozen=True)
class MetricComponentRule:
    metric_id: str
    basis_id: str
    sign: int


@dataclass(frozen=True)
class MetricRule:
    metric_id: str
    allowed_basis_ids: Tuple[str, ...]
    as_of_date_rule: str
    aggregation: str
    direction: str
    included_lifecycle_stages: Tuple[str, ...]
    components_by_basis: Mapping[str, Tuple[MetricComponentRule, ...]]


@dataclass(frozen=True)
class MetricCatalog:
    metrics: Tuple[MetricRule, ...]
    content_sha256: str

    @classmethod
    def from_yaml(cls, path: Path) -> "MetricCatalog":
        data = _read_public_config(path, "Metric catalog")
        try:
            raw = yaml.safe_load(data.decode("utf-8"))
        except (UnicodeError, yaml.YAMLError) as exc:
            raise InputGateError("METRIC_CATALOG_PARSE", "Metric catalog is not valid UTF-8 YAML") from exc
        if not isinstance(raw, dict) or raw.get("schema_version") != "kmfa.project_cost.metric_catalog.v2":
            raise InputGateError("METRIC_CATALOG_SCHEMA", "Metric catalog schema version is unsupported")
        raw_metrics = raw.get("metrics")
        if not isinstance(raw_metrics, dict) or not raw_metrics:
            raise InputGateError("METRIC_CATALOG_EMPTY", "Metric catalog cannot be empty")
        metrics = []
        for metric_id in sorted(raw_metrics):
            body = raw_metrics[metric_id]
            expected_fields = {
                "allowed_basis_ids",
                "as_of_date_rule",
                "aggregation",
                "direction",
                "included_lifecycle_stages",
                "components_by_basis",
            }
            if not isinstance(body, dict) or set(body) != expected_fields:
                raise InputGateError("METRIC_RULE_INVALID", "Metric rule must be a mapping")
            aggregation = _required_text(body.get("aggregation"), "aggregation")
            direction = _required_text(body.get("direction"), "direction")
            stages = _optional_string_list(body.get("included_lifecycle_stages"), "included_lifecycle_stages")
            raw_components = body.get("components_by_basis")
            if aggregation not in {"DIRECT", "DERIVED"} or not isinstance(raw_components, dict):
                raise InputGateError("METRIC_RULE_INVALID", "Metric aggregation or component mapping is invalid")
            if aggregation == "DIRECT" and direction not in {"COST", "REVENUE", "CASH_OUT", "CASH_IN", "REFERENCE"}:
                raise InputGateError("METRIC_RULE_INVALID", "direct Metric direction is not registered")
            if aggregation == "DIRECT" and (not stages or raw_components):
                raise InputGateError("METRIC_RULE_INVALID", "direct Metric requires lifecycle stages and no components")
            if aggregation == "DERIVED" and (stages or direction != "DERIVED" or not raw_components):
                raise InputGateError("METRIC_RULE_INVALID", "derived Metric requires basis-specific components")
            components: Dict[str, Tuple[MetricComponentRule, ...]] = {}
            for basis_id, component_rows in raw_components.items():
                basis_text = _required_text(basis_id, "component basis")
                if not isinstance(component_rows, list) or len(component_rows) < 2:
                    raise InputGateError("METRIC_COMPONENT_INVALID", "derived Metric requires at least two components")
                parsed_components = []
                for component in component_rows:
                    if not isinstance(component, dict) or set(component) != {"metric_id", "basis_id", "sign"}:
                        raise InputGateError("METRIC_COMPONENT_INVALID", "Metric component fields are invalid")
                    sign = component.get("sign")
                    if type(sign) is not int or sign not in {-1, 1}:
                        raise InputGateError("METRIC_COMPONENT_INVALID", "Metric component sign must be -1 or 1")
                    parsed_components.append(
                        MetricComponentRule(
                            metric_id=_required_text(component.get("metric_id"), "component metric_id"),
                            basis_id=_required_text(component.get("basis_id"), "component basis_id"),
                            sign=sign,
                        )
                    )
                components[basis_text] = tuple(parsed_components)
            metrics.append(
                MetricRule(
                    metric_id=_required_text(metric_id, "metric_id"),
                    allowed_basis_ids=_required_string_list(body.get("allowed_basis_ids"), "allowed_basis_ids"),
                    as_of_date_rule=_required_text(body.get("as_of_date_rule"), "as_of_date_rule"),
                    aggregation=aggregation,
                    direction=direction,
                    included_lifecycle_stages=stages,
                    components_by_basis=components,
                )
            )
        metric_map = {item.metric_id: item for item in metrics}
        for rule in metrics:
            if rule.aggregation == "DERIVED" and set(rule.components_by_basis) != set(rule.allowed_basis_ids):
                raise InputGateError("METRIC_COMPONENT_INVALID", "derived component bases must match allowed bases")
            for component_rows in rule.components_by_basis.values():
                for component in component_rows:
                    target = metric_map.get(component.metric_id)
                    if target is None or component.basis_id not in target.allowed_basis_ids:
                        raise InputGateError("METRIC_COMPONENT_INVALID", "derived component references an unknown Metric/basis")
        return cls(tuple(metrics), hashlib.sha256(data).hexdigest())

    def metric_map(self) -> Dict[str, MetricRule]:
        return {item.metric_id: item for item in self.metrics}


@dataclass(frozen=True)
class OperationRequest:
    run_id: str
    mode: Optional[str]
    requested_metrics: Tuple[str, ...]
    requested_basis_ids: Tuple[str, ...]
    project_selector: Tuple[Tuple[str, str], ...]
    as_of: Optional[str]
    input_root: Optional[str]
    manifest_path: Optional[str]
    output_dir: Optional[str]
    policy_refs: Tuple[Tuple[str, str], ...]
    resolution_path: Optional[str]
    prior_sufficiency_report_path: Optional[str]

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "OperationRequest":
        allowed = {
            "schema_version",
            "run_id",
            "mode",
            "requested_metrics",
            "requested_basis_ids",
            "project_selector",
            "as_of",
            "input_root",
            "manifest_path",
            "output_dir",
            "policy_refs",
            "resolution_path",
            "prior_sufficiency_report_path",
        }
        if set(raw) - allowed or raw.get("schema_version") != "kmfa.project_cost.operation_request.v1":
            raise InputGateError("REQUEST_SCHEMA_DRIFT", "operation request fields or schema version are unsupported")
        run_id = _required_text(raw.get("run_id"), "run_id")
        if not RUN_ID_RE.fullmatch(run_id):
            raise InputGateError("RUN_ID_INVALID", "run ID must be portable and non-sensitive")
        mode_raw = raw.get("mode")
        if mode_raw is not None and not isinstance(mode_raw, str):
            raise InputGateError("REQUEST_FIELD_INVALID", "mode must be text or null")
        selector_raw = raw.get("project_selector", {})
        if not isinstance(selector_raw, dict):
            raise InputGateError("REQUEST_FIELD_INVALID", "project selector must be a mapping")
        selector = []
        for key, value in selector_raw.items():
            selector.append((_required_text(key, "project selector key"), _required_text(value, "project selector value")))
        policy_raw = raw.get("policy_refs", {})
        if not isinstance(policy_raw, dict):
            raise InputGateError("REQUEST_FIELD_INVALID", "policy refs must be a mapping")
        policies = []
        for key, value in policy_raw.items():
            policies.append((_required_text(key, "policy ref key"), _required_text(value, "policy ref value")))
        return cls(
            run_id=run_id,
            mode=mode_raw.strip() if isinstance(mode_raw, str) and mode_raw.strip() else None,
            requested_metrics=_optional_string_list(raw.get("requested_metrics"), "requested_metrics"),
            requested_basis_ids=_optional_string_list(raw.get("requested_basis_ids"), "requested_basis_ids"),
            project_selector=tuple(sorted(selector)),
            as_of=_optional_text(raw.get("as_of"), "as_of"),
            input_root=_optional_text(raw.get("input_root"), "input_root"),
            manifest_path=_optional_text(raw.get("manifest_path"), "manifest_path"),
            output_dir=_optional_text(raw.get("output_dir"), "output_dir"),
            policy_refs=tuple(sorted(policies)),
            resolution_path=_optional_text(raw.get("resolution_path"), "resolution_path"),
            prior_sufficiency_report_path=_optional_text(
                raw.get("prior_sufficiency_report_path"), "prior_sufficiency_report_path"
            ),
        )

    def project_selector_dict(self) -> Dict[str, str]:
        return dict(self.project_selector)

    def policy_ref_map(self) -> Dict[str, str]:
        return dict(self.policy_refs)

    def binding_hash(self) -> str:
        payload = {
            "run_id": self.run_id,
            "mode": self.mode,
            "requested_metrics": list(self.requested_metrics),
            "requested_basis_ids": list(self.requested_basis_ids),
            "project_selector": dict(self.project_selector),
            "as_of": self.as_of,
            "input_root": self.input_root,
            "manifest_path": self.manifest_path,
            "output_dir": self.output_dir,
            "policy_refs": dict(self.policy_refs),
        }
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class RequirementItem:
    requirement_id: str
    classification: str
    observed_status: str
    allowed_resolutions: Tuple[str, ...]
    applies_to_metrics: Tuple[str, ...]
    expected_source_or_policy: Optional[str]
    evidence_ref: Optional[str]
    selected_resolution: Optional[str] = None
    resolution_evidence_refs: Tuple[str, ...] = ()
    user_instruction_ref: Optional[str] = None
    effect_on_scope_or_metrics: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        return {
            "requirement_id": self.requirement_id,
            "classification": self.classification,
            "observed_status": self.observed_status,
            "allowed_resolutions": list(self.allowed_resolutions),
            "applies_to_metrics": list(self.applies_to_metrics),
            "expected_source_or_policy": self.expected_source_or_policy,
            "evidence_ref": self.evidence_ref,
            "selected_resolution": self.selected_resolution,
            "resolution_evidence_refs": list(self.resolution_evidence_refs),
            "user_instruction_ref": self.user_instruction_ref,
            "effect_on_scope_or_metrics": self.effect_on_scope_or_metrics,
        }


@dataclass(frozen=True)
class InputSufficiencyReport:
    run_id: str
    request_hash: str
    mode: str
    requested_metrics: Tuple[str, ...]
    requested_basis_ids: Tuple[str, ...]
    output_dir: str
    overall_status: str
    items: Tuple[RequirementItem, ...]
    user_action_required: bool
    resolution_ref: Optional[str]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": "kmfa.project_cost.input_sufficiency_report.v1",
            "run_id": self.run_id,
            "request_hash": self.request_hash,
            "mode": self.mode,
            "requested_metrics": list(self.requested_metrics),
            "requested_basis_ids": list(self.requested_basis_ids),
            "output_dir": self.output_dir,
            "overall_status": self.overall_status,
            "items": [item.as_dict() for item in self.items],
            "user_action_required": self.user_action_required,
            "resolution_ref": self.resolution_ref,
        }


@dataclass(frozen=True)
class PublishedInputGateOutputs:
    output_dir: Path
    primary_output: Path
    output_index_json: Path
    output_index_md: Path
    run_seal: Path
    prompt_path: Optional[Path]
    resolution_path: Optional[Path]


def _read_public_config(path: Path, label: str) -> bytes:
    value = Path(path)
    try:
        metadata = value.lstat()
    except OSError as exc:
        raise InputGateError("CONFIG_UNAVAILABLE", "%s cannot be accessed" % label) from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        raise InputGateError("CONFIG_PATH_UNSAFE", "%s must be a single-link regular file" % label)
    if metadata.st_size > 1024 * 1024:
        raise InputGateError("CONFIG_TOO_LARGE", "%s exceeds the metadata size ceiling" % label)
    try:
        return value.read_bytes()
    except OSError as exc:
        raise InputGateError("CONFIG_UNREADABLE", "%s cannot be read" % label) from exc


def _required_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InputGateError("REQUEST_FIELD_INVALID", "%s must be nonempty text" % field)
    return value.strip()


def _optional_text(value: Any, field: str) -> Optional[str]:
    if value is None:
        return None
    return _required_text(value, field)


def _required_string_list(value: Any, field: str) -> Tuple[str, ...]:
    if not isinstance(value, list) or not value or any(not isinstance(item, str) or not item.strip() for item in value):
        raise InputGateError("REQUEST_FIELD_INVALID", "%s must be a nonempty string list" % field)
    result = tuple(item.strip() for item in value)
    if len(set(result)) != len(result):
        raise InputGateError("REQUEST_FIELD_INVALID", "%s cannot contain duplicates" % field)
    return result


def _optional_string_list(value: Any, field: str) -> Tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise InputGateError("REQUEST_FIELD_INVALID", "%s must be a string list" % field)
    result = tuple(item.strip() for item in value)
    if len(set(result)) != len(result):
        raise InputGateError("REQUEST_FIELD_INVALID", "%s cannot contain duplicates" % field)
    return result


def _contains(parent: Path, child: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def _reject_existing_symlink_components(path: Path) -> None:
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current = current / part
        if not current.exists() and not current.is_symlink():
            continue
        try:
            if stat.S_ISLNK(current.lstat().st_mode):
                raise InputGateError("OUTPUT_PATH_SYMLINK", "output path contains a symbolic-link component")
        except OSError as exc:
            raise InputGateError("OUTPUT_PATH_UNAVAILABLE", "output path metadata cannot be inspected") from exc


def resolve_operation_output_dir(
    request: OperationRequest,
    *,
    private_runtime_root: Path,
    repo_root: Path,
) -> Path:
    runtime = Path(private_runtime_root).resolve(strict=False)
    repo = Path(repo_root).resolve(strict=True)
    if request.output_dir is None:
        raw_target = runtime / "runs" / request.run_id / "outputs"
    else:
        raw_target = Path(request.output_dir)
        if not raw_target.is_absolute():
            raise InputGateError("OUTPUT_DIR_NOT_ABSOLUTE", "output directory must be absolute")
    if ".." in raw_target.parts or "\\" in str(raw_target) or "\x00" in str(raw_target):
        raise InputGateError("OUTPUT_DIR_UNSAFE", "output directory contains a forbidden component")
    # Resolve trusted host aliases such as macOS /var -> /private/var before
    # checking components; this does not relax containment or symlink checks.
    target = Path(os.path.realpath(os.path.abspath(str(raw_target))))
    _reject_existing_symlink_components(target)
    if target.exists():
        raise InputGateError("OUTPUT_DIR_EXISTS", "each run requires a new non-existing output directory")
    if request.input_root:
        raw_root = Path(request.input_root)
        try:
            raw_resolved = raw_root.resolve(strict=True)
        except OSError:
            raw_resolved = Path(os.path.abspath(str(raw_root)))
        if _contains(raw_resolved, target) or _contains(target, raw_resolved):
            raise InputGateError("OUTPUT_OVERLAPS_RAW", "output directory must not overlap the raw input root")
    if _contains(repo, target) and not _contains(runtime, target):
        raise InputGateError("OUTPUT_INSIDE_TRACKED_TREE", "repository outputs must remain under ignored private runtime")
    return target


def _rule_item(
    rule: RequirementRule,
    *,
    status: str,
    metrics: Sequence[str],
    expected: Optional[str],
    evidence: Optional[str] = None,
) -> RequirementItem:
    if status not in VALID_OBSERVED_STATUSES:
        raise InputGateError("OBSERVED_STATUS_INVALID", "input gate produced an unknown status")
    return RequirementItem(
        requirement_id=rule.requirement_id,
        classification=rule.classification,
        observed_status=status,
        allowed_resolutions=rule.allowed_resolutions,
        applies_to_metrics=tuple(sorted(metrics)),
        expected_source_or_policy=expected,
        evidence_ref=evidence,
    )


def _expand_metric_dependencies(
    requested_metrics: Sequence[str],
    requirements: InputRequirements,
) -> Tuple[str, ...]:
    expanded = set(requested_metrics)
    pending = list(requested_metrics)
    while pending:
        metric_id = pending.pop()
        dependency = requirements.metric_dependencies.get(metric_id, {})
        if not isinstance(dependency, dict):
            raise InputGateError("METRIC_DEPENDENCY_INVALID", "Metric dependency must be a mapping")
        components = list(dependency.get("required_component_metrics", [])) + list(
            dependency.get("conditional_component_metrics", [])
        )
        for component in components:
            if not isinstance(component, str):
                raise InputGateError("METRIC_DEPENDENCY_INVALID", "component Metric IDs must be text")
            if component not in expanded:
                expanded.add(component)
                pending.append(component)
    return tuple(sorted(expanded))


def _validate_catalog_dependencies(catalog: MetricCatalog, requirements: InputRequirements) -> None:
    catalog_ids = set(catalog.metric_map())
    dependency_ids = set(requirements.metric_dependencies)
    if catalog_ids != dependency_ids:
        raise InputGateError("METRIC_DEPENDENCY_CATALOG_DRIFT", "Metric catalog and input dependencies differ")
    for metric_id, dependency in requirements.metric_dependencies.items():
        component_ids = set(dependency.get("required_component_metrics", ())) | set(
            dependency.get("conditional_component_metrics", ())
        )
        if not component_ids <= catalog_ids or metric_id in component_ids:
            raise InputGateError("METRIC_DEPENDENCY_CATALOG_DRIFT", "Metric component dependency is unknown or recursive")


def _metric_basis_status(request: OperationRequest, catalog: MetricCatalog, requirements: InputRequirements) -> str:
    if not request.requested_metrics or not request.requested_basis_ids:
        return "MISSING"
    catalog_map = catalog.metric_map()
    basis_set = set(request.requested_basis_ids)
    for metric_id in request.requested_metrics:
        rule = catalog_map.get(metric_id)
        if rule is None or not (basis_set & set(rule.allowed_basis_ids)):
            return "CONFLICT"
        dependency = requirements.metric_dependencies.get(metric_id, {})
        required_basis = dependency.get("required_basis_ids", []) if isinstance(dependency, dict) else []
        if not set(required_basis).issubset(basis_set):
            return "MISSING"
    return "PRESENT"


def _slot_item(
    slot_id: str,
    *,
    manifest: Optional[InputManifest],
    inventory_entries: Sequence[InventoryEntry],
    applies_to_metrics: Sequence[str],
) -> RequirementItem:
    allowed = ("SUPPLIED", "QUALIFIED_ALTERNATE_EVIDENCE", "SCOPE_REDUCED", "BLOCKED")
    status = "MISSING"
    evidence = None
    if manifest is not None:
        slot = manifest.slot_map().get(slot_id)
        source_locks = slot.source_locks() if slot is not None else ()
        if (
            slot is None
            or not slot.private_patterns
            or not source_locks
            or slot.expected_schema_fingerprint is None
        ):
            status = "MISSING"
        else:
            candidates = match_inventory_entries(inventory_entries, slot.private_patterns)
            selected_groups = [
                [entry for entry in candidates if entry.source_id == source_lock.source_id]
                for source_lock in source_locks
            ]
            if any(len(group) != 1 for group in selected_groups):
                status = "CONFLICT"
            elif any(group[0].status == "UNSAFE" for group in selected_groups):
                status = "UNSAFE"
            else:
                status = "PRESENT"
                evidence = "manifest-slot:%s" % slot_id
    return RequirementItem(
        requirement_id="SLOT:%s" % slot_id,
        classification="NON_WAIVABLE",
        observed_status=status,
        allowed_resolutions=allowed,
        applies_to_metrics=tuple(sorted(applies_to_metrics)),
        expected_source_or_policy="manifest slot %s with one or more explicit sources and full digest locks" % slot_id,
        evidence_ref=evidence,
    )


def _policy_item(policy_id: str, *, request: OperationRequest, metrics: Sequence[str]) -> RequirementItem:
    reference = request.policy_ref_map().get(policy_id)
    return RequirementItem(
        requirement_id="POLICY:%s" % policy_id,
        classification="NON_WAIVABLE",
        observed_status="PRESENT" if reference else "MISSING",
        allowed_resolutions=("SUPPLIED", "QUALIFIED_ALTERNATE_EVIDENCE", "SCOPE_REDUCED", "BLOCKED"),
        applies_to_metrics=tuple(sorted(metrics)),
        expected_source_or_policy=policy_id,
        evidence_ref="policy-ref:%s" % policy_id if reference else None,
    )


def _apply_resolution(
    items: Sequence[RequirementItem],
    *,
    resolution: Optional[InputResolution],
    request: OperationRequest,
) -> Tuple[RequirementItem, ...]:
    if resolution is None:
        return tuple(items)
    item_map = {item.requirement_id: item for item in items}
    resolution_map = resolution.item_map()
    updated = []
    for item in items:
        chosen = resolution_map.get(item.requirement_id)
        if chosen is None:
            updated.append(item)
            continue
        if chosen.classification != item.classification or chosen.resolution not in item.allowed_resolutions:
            raise InputGateError("RESOLUTION_ITEM_CONFLICT", "resolution item conflicts with the current checklist")
        if chosen.resolution == "SCOPE_REDUCED" and set(chosen.affected_metrics) & set(request.requested_metrics):
            raise InputGateError(
                "SCOPE_REDUCTION_NOT_APPLIED",
                "scope-reduced Metrics still occur in the resulting operation request",
            )
        updated.append(
            replace(
                item,
                selected_resolution=chosen.resolution,
                resolution_evidence_refs=chosen.evidence_refs,
                user_instruction_ref=chosen.user_instruction_ref,
                effect_on_scope_or_metrics=chosen.effect_on_scope_or_metrics,
            )
        )
    for requirement_id, chosen in resolution_map.items():
        if requirement_id in item_map:
            continue
        if chosen.resolution != "SCOPE_REDUCED" or set(chosen.affected_metrics) & set(request.requested_metrics):
            raise InputGateError("RESOLUTION_REQUIREMENT_STALE", "resolution item is not in the resulting checklist")
        updated.append(
            RequirementItem(
                requirement_id=requirement_id,
                classification=chosen.classification,
                observed_status="NOT_IN_SCOPE",
                allowed_resolutions=tuple(sorted(ALLOWED_RESOLUTIONS[chosen.classification])),
                applies_to_metrics=chosen.affected_metrics,
                expected_source_or_policy=None,
                evidence_ref=None,
                selected_resolution=chosen.resolution,
                resolution_evidence_refs=chosen.evidence_refs,
                user_instruction_ref=chosen.user_instruction_ref,
                effect_on_scope_or_metrics=chosen.effect_on_scope_or_metrics,
            )
        )
    return tuple(sorted(updated, key=lambda item: item.requirement_id))


def _readiness(items: Sequence[RequirementItem], *, has_resolution: bool) -> str:
    if any(item.observed_status == "UNSAFE" for item in items):
        return "BLOCKED_NON_WAIVABLE"
    if any(item.selected_resolution == "BLOCKED" and item.classification == "NON_WAIVABLE" for item in items):
        return "BLOCKED_NON_WAIVABLE"
    unresolved = []
    for item in items:
        if item.observed_status in {"PRESENT", "NOT_IN_SCOPE"}:
            continue
        if item.selected_resolution == "OMIT_OPTIONAL_PRESENTATION" and item.classification == "OPTIONAL_PRESENTATION":
            continue
        if item.selected_resolution in {"SUPPLIED", "QUALIFIED_ALTERNATE_EVIDENCE"}:
            # A claimed supply/alternate is not sufficient until a rescan changes observed_status to PRESENT.
            unresolved.append(item)
            continue
        unresolved.append(item)
    if any(item.classification == "NON_WAIVABLE" for item in unresolved):
        return "NEEDS_SUPPLEMENT"
    if unresolved:
        return "NEEDS_EXPLICIT_HANDLING"
    documented = has_resolution and any(
        item.selected_resolution in {"SCOPE_REDUCED", "OMIT_OPTIONAL_PRESENTATION", "QUALIFIED_ALTERNATE_EVIDENCE"}
        for item in items
    )
    return "SUFFICIENT_WITH_DOCUMENTED_SCOPE" if documented else "SUFFICIENT"


def evaluate_input_sufficiency(
    request: OperationRequest,
    *,
    requirements: InputRequirements,
    metric_catalog: MetricCatalog,
    output_dir: Path,
    manifest: Optional[InputManifest],
    inventory_entries: Sequence[InventoryEntry],
    security_capability_present: bool,
    security_profile_id: Optional[str] = None,
    resolution: Optional[InputResolution] = None,
    prior_request_hash: Optional[str] = None,
    manifest_error_code: Optional[str] = None,
    inventory_error_code: Optional[str] = None,
    output_dir_error_code: Optional[str] = None,
) -> InputSufficiencyReport:
    """Evaluate metadata/config only. It never opens a raw source file body."""

    _validate_catalog_dependencies(metric_catalog, requirements)
    mode = request.mode if request.mode in VALID_MODES else "INVALID"
    rules = requirements.rule_map()
    items = []
    run_mode_rule = rules["RUN_MODE"]
    items.append(
        _rule_item(
            run_mode_rule,
            status="PRESENT" if mode != "INVALID" else "MISSING",
            metrics=request.requested_metrics,
            expected="one registered operating mode",
            evidence="request:mode" if mode != "INVALID" else None,
        )
    )
    applicable_mode = request.mode if request.mode in VALID_MODES else None
    if applicable_mode:
        for requirement_id in ("PROJECT_SCOPE", "AS_OF_DATE", "METRIC_AND_BASIS", "RAW_ROOT_AND_MANIFEST", "SAFE_READ_AND_DIGEST"):
            rule = rules[requirement_id]
            if applicable_mode not in rule.applies_to_modes:
                continue
            if requirement_id == "PROJECT_SCOPE":
                status = "PRESENT" if request.project_selector else "MISSING"
                expected, evidence = "explicit project/entity/WBS scope", "request:project-scope" if request.project_selector else None
            elif requirement_id == "AS_OF_DATE":
                try:
                    date.fromisoformat(request.as_of or "")
                    status = "PRESENT"
                except ValueError:
                    status = "MISSING"
                expected, evidence = "Metric-specific ISO as-of date", "request:as-of" if status == "PRESENT" else None
            elif requirement_id == "METRIC_AND_BASIS":
                status = _metric_basis_status(request, metric_catalog, requirements)
                expected, evidence = "registered Metric and compatible basis IDs", "request:metric-basis" if status == "PRESENT" else None
            elif requirement_id == "RAW_ROOT_AND_MANIFEST":
                status, evidence = "MISSING", None
                if manifest_error_code:
                    status = "CONFLICT"
                elif inventory_error_code:
                    status = "UNSAFE"
                elif request.input_root and request.manifest_path and manifest is not None:
                    try:
                        validate_manifest_request(
                            manifest,
                            mode=applicable_mode,
                            requested_metrics=request.requested_metrics,
                            requested_basis_ids=request.requested_basis_ids,
                            project_selector=request.project_selector_dict(),
                            as_of=request.as_of,
                        )
                        request_root = Path(request.input_root).resolve(strict=True)
                        manifest_root = Path(manifest.input_root).resolve(strict=True)
                        if request_root != manifest_root:
                            raise ManifestError("MANIFEST_ROOT_CONFLICT", "manifest input root differs from request")
                        status, evidence = "PRESENT", "manifest:%s" % manifest.manifest_id
                    except (ManifestError, OSError):
                        status = "CONFLICT"
                expected = "read-only raw root plus v3 explicit private manifest"
            else:
                if not security_capability_present or manifest is None:
                    status = "MISSING"
                elif security_profile_id is not None and manifest.security_profile_id != security_profile_id:
                    status = "CONFLICT"
                else:
                    status = "PRESENT"
                expected = "R2 file-security capability plus mandatory full-digest policy"
                evidence = "capability:POLICY-KMFA-FILE-SECURITY-001" if status == "PRESENT" else None
            items.append(
                _rule_item(
                    rule,
                    status=status,
                    metrics=request.requested_metrics,
                    expected=expected,
                    evidence=evidence,
                )
            )
    output_rule = rules["OUTPUT_DIRECTORY"]
    items.append(
        _rule_item(
            output_rule,
            status="CONFLICT" if output_dir_error_code else "PRESENT",
            metrics=request.requested_metrics,
            expected="new absolute private output directory outside raw sources",
            evidence="output:validated-private-destination" if output_dir_error_code is None else None,
        )
    )
    if applicable_mode and applicable_mode in {"reference-replay", "calculate", "restate"}:
        expanded_metrics = _expand_metric_dependencies(request.requested_metrics, requirements)
        required_slots = set()
        required_policies = set()
        mode_dependency = requirements.mode_dependencies.get(applicable_mode, {})
        if isinstance(mode_dependency, dict):
            required_slots.update(mode_dependency.get("required_slots", []))
        for metric_id in expanded_metrics:
            dependency = requirements.metric_dependencies.get(metric_id, {})
            if not isinstance(dependency, dict):
                raise InputGateError("METRIC_DEPENDENCY_INVALID", "Metric dependency must be a mapping")
            required_slots.update(dependency.get("required_slots", []))
            required_policies.update(dependency.get("required_policy_refs", []))
        for slot_id in sorted(required_slots):
            items.append(
                _slot_item(
                    slot_id,
                    manifest=manifest,
                    inventory_entries=inventory_entries,
                    applies_to_metrics=expanded_metrics,
                )
            )
        for policy_id in sorted(required_policies):
            items.append(_policy_item(policy_id, request=request, metrics=expanded_metrics))
    if resolution is not None:
        if manifest is None:
            raise InputGateError("RESOLUTION_WITHOUT_MANIFEST", "input resolution cannot bind without a manifest")
        if prior_request_hash is None:
            raise InputGateError("RESOLUTION_PRIOR_REPORT_REQUIRED", "input resolution requires the prior sufficiency report")
        try:
            validate_resolution_bindings(
                resolution,
                run_id=request.run_id,
                bound_request_hash=prior_request_hash,
                resulting_request_hash=request.binding_hash(),
                manifest_sha256=manifest.content_sha256,
                requirements_sha256=requirements.content_sha256,
            )
        except ResolutionError as exc:
            raise InputGateError(exc.code, exc.message) from exc
    resolved_items = _apply_resolution(items, resolution=resolution, request=request)
    overall = _readiness(resolved_items, has_resolution=resolution is not None)
    return InputSufficiencyReport(
        run_id=request.run_id,
        request_hash=request.binding_hash(),
        mode=mode,
        requested_metrics=request.requested_metrics,
        requested_basis_ids=request.requested_basis_ids,
        output_dir=str(Path(output_dir).absolute()),
        overall_status=overall,
        items=tuple(sorted(resolved_items, key=lambda item: item.requirement_id)),
        user_action_required=overall not in {"SUFFICIENT", "SUFFICIENT_WITH_DOCUMENTED_SCOPE"},
        resolution_ref=resolution.resolution_id if resolution else None,
    )


def render_missing_input_prompt(report: InputSufficiencyReport) -> Optional[str]:
    if not report.user_action_required:
        return None
    unresolved = [
        item
        for item in report.items
        if item.observed_status not in {"PRESENT", "NOT_IN_SCOPE"}
        and not (
            item.classification == "OPTIONAL_PRESENTATION"
            and item.selected_resolution == "OMIT_OPTIONAL_PRESENTATION"
        )
    ]
    lines = [
        "# 输入不足：需要一次明确处理",
        "",
        "| # | Requirement | Classification | Affected Metrics | Status | Allowed options |",
        "| ---: | --- | --- | --- | --- | --- |",
    ]
    for number, item in enumerate(unresolved, 1):
        options = ",".join(str(RESOLUTION_OPTION_NUMBERS[value]) for value in item.allowed_resolutions)
        metrics = ",".join(item.applies_to_metrics) or "NONE"
        lines.append(
            "| %d | `%s` | `%s` | `%s` | `%s` | `%s` |"
            % (number, item.requirement_id, item.classification, metrics, item.observed_status, options)
        )
    lines.extend(
        [
            "",
            "选项：1 补充输入（推荐）；2 缩小受影响范围；3 提供合格替代证据；4 省略仅属可选展示；5 保持 BLOCKED，停止正式计算并保留诊断。",
            "",
            "请按 `编号=选项` 明确选择并附必要证据；未回复不构成授权，非可豁免门禁不能选择 4。",
        ]
    )
    return "\n".join(lines) + "\n"


def _write_sync(path: Path, data: bytes) -> None:
    with path.open("xb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def publish_input_gate_outputs(
    report: InputSufficiencyReport,
    *,
    resolution: Optional[InputResolution] = None,
) -> PublishedInputGateOutputs:
    """Atomically publish report, compact prompt, absolute indexes, and detached seal."""

    output_dir = Path(report.output_dir)
    prompt = render_missing_input_prompt(report)
    result_status = "NEEDS_USER_INPUT" if report.user_action_required else "INPUT_SUFFICIENT"
    if resolution is not None:
        try:
            resolution.validate()
        except ResolutionError as exc:
            raise InputGateError(exc.code, exc.message) from exc
        if report.run_id != resolution.run_id or report.resolution_ref != resolution.resolution_id:
            raise InputGateError("RESOLUTION_REPORT_MISMATCH", "report and input resolution bindings differ")
    elif report.resolution_ref is not None:
        raise InputGateError("RESOLUTION_ARTIFACT_REQUIRED", "resolved report requires its exact input-resolution artifact")
    try:
        with atomic_output_directory(output_dir.parent, output_dir.name) as temporary:
            report_path = temporary / "input_sufficiency_report.json"
            _write_sync(
                report_path,
                (json.dumps(report.as_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"),
            )
            prompt_path = None
            if prompt is not None:
                prompt_path = temporary / "missing_input_prompt.md"
                _write_sync(prompt_path, prompt.encode("utf-8"))
            resolution_path = None
            if resolution is not None:
                resolution_path = temporary / "input_resolution.json"
                _write_sync(
                    resolution_path,
                    (json.dumps(resolution.as_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
                        "utf-8"
                    ),
                )
            final_report = output_dir / report_path.name
            final_prompt = output_dir / prompt_path.name if prompt_path else None
            final_resolution = output_dir / resolution_path.name if resolution_path else None
            index_json_path = temporary / "output_index.json"
            index_md_path = temporary / "OUTPUT_INDEX.md"
            seal_path = temporary / "run_seal.sha256"
            files = [
                {
                    "path": str(final_report),
                    "artifact_type": "INPUT_SUFFICIENCY_REPORT",
                    "sha256": _sha256_file(report_path),
                }
            ]
            if prompt_path:
                files.append(
                    {
                        "path": str(final_prompt),
                        "artifact_type": "MISSING_INPUT_PROMPT",
                        "sha256": _sha256_file(prompt_path),
                    }
                )
            if resolution_path:
                files.append(
                    {
                        "path": str(final_resolution),
                        "artifact_type": "INPUT_RESOLUTION",
                        "sha256": _sha256_file(resolution_path),
                    }
                )
            index_payload = {
                "schema_version": "kmfa.project_cost.input_gate_output_index.v1",
                "run_id": report.run_id,
                "result_status": result_status,
                "output_dir": str(output_dir),
                "primary_output": str(final_report),
                "output_index_json": str(output_dir / "output_index.json"),
                "output_index_md": str(output_dir / "OUTPUT_INDEX.md"),
                "run_seal": str(output_dir / "run_seal.sha256"),
                "files": files,
                "final_financial_workbook_generated": False,
            }
            _write_sync(
                index_json_path,
                (json.dumps(index_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"),
            )
            md_lines = [
                "# Input gate output index",
                "",
                "RESULT_STATUS: `%s`" % result_status,
                "",
                "OUTPUT_DIR: `%s`" % output_dir,
                "",
                "PRIMARY_OUTPUT: `%s`" % final_report,
                "",
                "OUTPUT_INDEX: `%s`" % (output_dir / "OUTPUT_INDEX.md"),
                "",
                "No financial workbook was generated by this input-gate-only operation.",
            ]
            if final_prompt is not None:
                md_lines.extend(["", "MISSING_INPUT_PROMPT: `%s`" % final_prompt])
            if final_resolution is not None:
                md_lines.extend(["", "INPUT_RESOLUTION: `%s`" % final_resolution])
            _write_sync(index_md_path, ("\n".join(md_lines) + "\n").encode("utf-8"))
            sealed_files = sorted(
                [report_path, index_json_path, index_md_path]
                + ([prompt_path] if prompt_path else [])
                + ([resolution_path] if resolution_path else []),
                key=lambda path: path.name,
            )
            seal_text = "".join("%s  %s\n" % (_sha256_file(path), path.name) for path in sealed_files)
            _write_sync(seal_path, seal_text.encode("ascii"))
    except PathSafetyError as exc:
        raise InputGateError(exc.code, exc.message) from exc
    return PublishedInputGateOutputs(
        output_dir=output_dir,
        primary_output=output_dir / "input_sufficiency_report.json",
        output_index_json=output_dir / "output_index.json",
        output_index_md=output_dir / "OUTPUT_INDEX.md",
        run_seal=output_dir / "run_seal.sha256",
        prompt_path=output_dir / "missing_input_prompt.md" if prompt is not None else None,
        resolution_path=output_dir / "input_resolution.json" if resolution is not None else None,
    )


def output_locator(
    *,
    result_status: str,
    outputs: PublishedInputGateOutputs,
    next_step: str,
) -> str:
    return "\n".join(
        [
            "RESULT_STATUS: %s" % result_status,
            "OUTPUT_DIR: %s" % outputs.output_dir,
            "PRIMARY_OUTPUT: %s" % outputs.primary_output,
            "OUTPUT_INDEX: %s" % outputs.output_index_md,
            "NEXT_STEP: %s" % next_step,
        ]
    )


def verify_detached_seal(output_dir: Path) -> bool:
    """Verify a non-recursive seal without allowing traversal or self-hashing."""

    root = Path(output_dir)
    seal = root / "run_seal.sha256"
    try:
        lines = seal.read_text(encoding="ascii").splitlines()
    except (OSError, UnicodeError):
        return False
    if not lines:
        return False
    seen = set()
    for line in lines:
        parts = line.split("  ", 1)
        if len(parts) != 2:
            return False
        expected, name = parts
        if not re.fullmatch(r"[0-9a-f]{64}", expected):
            return False
        if name in seen or name == "run_seal.sha256" or "/" in name or "\\" in name or name in {"", ".", ".."}:
            return False
        seen.add(name)
        path = root / name
        if not path.is_file() or path.is_symlink() or _sha256_file(path) != expected:
            return False
    expected_names = {path.name for path in root.iterdir() if path.is_file() and path.name != "run_seal.sha256"}
    return seen == expected_names
