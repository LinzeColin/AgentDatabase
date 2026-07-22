#!/usr/bin/env python3
"""Fail-closed offline validator for the SkillOps Mechanism contract.

The artifact never selects its own schema.  A caller supplies a trusted schema
ID and, for contextual artifacts, the externally pinned bundle digest.  Bundle
bootstrap likewise starts from a verified Git object plus an expected digest;
repository self-reporting is never a trust root.
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import hashlib
import importlib.metadata
import ipaddress
import json
import math
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterable, Iterator, List, Mapping, Optional, Sequence, Tuple

from canonical_json import (
    CanonicalizationError,
    canonical_digest,
    canonicalize_object,
    parse_json_bytes,
    verify_self_digest,
    verify_vendor,
)

try:
    from jsonschema import Draft202012Validator, FormatChecker
    from referencing import Registry, Resource
    from referencing.exceptions import NoSuchResource, Unresolvable
except ImportError as exc:  # pragma: no cover - exercised by startup gate in deployment
    Draft202012Validator = None  # type: ignore[assignment]
    FormatChecker = None  # type: ignore[assignment]
    Registry = None  # type: ignore[assignment]
    Resource = None  # type: ignore[assignment]
    NoSuchResource = None  # type: ignore[assignment]
    Unresolvable = None  # type: ignore[assignment]
    _DEPENDENCY_IMPORT_ERROR: Optional[ImportError] = exc
else:
    _DEPENDENCY_IMPORT_ERROR = None


GOVERNANCE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = GOVERNANCE_DIR.parents[1]
INTERFACE_PATH = GOVERNANCE_DIR / "draft-interface.json"
CANONICAL_MANIFEST_PATH = (
    "CodexSkills/governance/bundles/schema-bundle-manifest.v1.json"
)
SCHEMA_PREFIX = "urn:linzecolin:agentdatabase:skillops:schema:"
PROTOCOL = "urn:linzecolin:agentdatabase:skillops:protocol:cross-pack:v1"
JSON_SCHEMA = "https://json-schema.org/draft/2020-12/schema"
MANIFEST_SCHEMA_ID = SCHEMA_PREFIX + "schema-bundle-manifest:v1"
EXPECTED_SCHEMA_SELF_POINTERS = {
    SCHEMA_PREFIX + "common-definitions:v1": None,
    SCHEMA_PREFIX + "skill-binding:v1": None,
    SCHEMA_PREFIX + "public-value-policy:v1": None,
    SCHEMA_PREFIX + "source-material-policy:v1": None,
    SCHEMA_PREFIX + "retention-policy:v2": None,
    SCHEMA_PREFIX + "notification-policy:v1": None,
    SCHEMA_PREFIX + "version-policy:v2": None,
    SCHEMA_PREFIX + "skill-identity:v1": None,
    SCHEMA_PREFIX + "skill-instance:v1": None,
    SCHEMA_PREFIX + "skill-version:v1": None,
    SCHEMA_PREFIX + "identity-lineage-event:v1": "/event_digest",
    SCHEMA_PREFIX + "eval-profile:v1": None,
    SCHEMA_PREFIX + "eval-run:v1": "/eval_run_digest",
    SCHEMA_PREFIX + "scorecard:v1": "/scorecard_digest",
    SCHEMA_PREFIX + "promotion-evidence-bundle:v1": "/evidence_bundle_digest",
    SCHEMA_PREFIX + "promotion-decision:v1": "/decision_digest",
    SCHEMA_PREFIX + "iteration-transition:v1": "/transition_digest",
    SCHEMA_PREFIX + "skill-passport:v1": "/passport_digest",
    SCHEMA_PREFIX + "capability-graph:v1": "/graph_digest",
    SCHEMA_PREFIX + "artifact-envelope:v1": "/envelope_digest",
    MANIFEST_SCHEMA_ID: "/bundle_digest",
    SCHEMA_PREFIX + "source-inventory:v1": "/inventory_digest",
    SCHEMA_PREFIX + "public-run-event:v2": "/event_digest",
    SCHEMA_PREFIX + "source-coverage-receipt:v1": "/receipt_digest",
    SCHEMA_PREFIX + "auto-receipt:v2": "/receipt_digest",
    SCHEMA_PREFIX + "publication-manifest:v1": "/manifest_digest",
    SCHEMA_PREFIX + "notification-receipt:v3": "/receipt_digest",
    SCHEMA_PREFIX + "retention-receipt:v2": "/receipt_digest",
    SCHEMA_PREFIX + "migration-receipt:v2": "/receipt_digest",
}
AUTO_PUBLIC_SCHEMA_IDS = {
    SCHEMA_PREFIX + "source-inventory:v1",
    SCHEMA_PREFIX + "public-run-event:v2",
    SCHEMA_PREFIX + "source-coverage-receipt:v1",
    SCHEMA_PREFIX + "auto-receipt:v2",
    SCHEMA_PREFIX + "publication-manifest:v1",
    SCHEMA_PREFIX + "notification-receipt:v3",
    SCHEMA_PREFIX + "retention-receipt:v2",
    SCHEMA_PREFIX + "migration-receipt:v2",
}
AUTO_PRIVATE_SCHEMA_IDS = {
    SCHEMA_PREFIX + "public-queue-envelope:v2",
    SCHEMA_PREFIX + "watermark:v2",
    SCHEMA_PREFIX + "lock-state:v1",
    SCHEMA_PREFIX + "raw-segment:v2",
}
EXPECTED_POLICY_IDS = {
    "urn:linzecolin:agentdatabase:skillops:policy:public-value:v1",
    "urn:linzecolin:agentdatabase:skillops:policy:source-material:v1",
    "urn:linzecolin:agentdatabase:skillops:policy:retention:v2",
    "urn:linzecolin:agentdatabase:skillops:policy:notification:v1",
    "urn:linzecolin:agentdatabase:skillops:policy:version:v2",
}
EVAL_DIMENSION_CODES = {
    "EFFICIENCY",
    "MAINTAINABILITY",
    "NEGATIVE_CAPABILITY",
    "OUTCOME",
    "RELIABILITY",
    "ROUTING",
    "SAFETY_GOVERNANCE",
}
CORE_HARD_GATE_CODES = {
    "CRITICAL_CORRECTNESS",
    "MAJOR_NOTIFICATION_SENT",
    "OPTIMIZER_EVALUATOR_ISOLATED",
    "PERMISSION_BOUNDARY",
    "PROVENANCE_LICENSE_RESOLVED",
    "PUBLIC_PRIVACY",
    "REPLAYABLE",
    "ROLLBACK_AVAILABLE",
}
CAUSAL_MATRIX_CELLS = {"BASELINE", "MODEL_EFFECT", "SKILL_EFFECT", "INTERACTION"}
ALLOWED_FORMATS = {
    "utc-z-timestamp-v1",
    "calendar-date-v1",
    "repo-relative-posix-path-v1",
}
FORBIDDEN_SCHEMA_KEYWORDS = {
    "$anchor",
    "$dynamicAnchor",
    "$dynamicRef",
    "$recursiveAnchor",
    "$recursiveRef",
    "patternProperties",
    "unevaluatedProperties",
}
SCHEMA_ID_RE = re.compile(
    r"^urn:linzecolin:agentdatabase:skillops:schema:"
    r"[a-z0-9][a-z0-9-]*:v[1-9][0-9]*$"
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GIT_OBJECT_RE = re.compile(r"^(sha1):([0-9a-f]{40})$|^(sha256):([0-9a-f]{64})$")
UTC_RE = re.compile(
    r"^[0-9]{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01])T"
    r"(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]\.[0-9]{6}Z$"
)
DATE_RE = re.compile(
    r"^[0-9]{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01])$"
)
EMAIL_RE = re.compile(
    r"(?<![A-Za-z0-9.!#$%&'*+/=?^_`{|}~-])"
    r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+"
)
PHONE_CANDIDATE_RE = re.compile(r"(?<!\w)\+?[0-9][0-9 .()/-]{7,}[0-9](?!\w)")
IPV4_CANDIDATE_RE = re.compile(
    r"(?<![A-Za-z0-9_.])(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?![A-Za-z0-9_.])"
)
ABSOLUTE_PATH_RE = re.compile(
    r"(?:^|[\s='\"])(?:/(?!/)[^\s'\"]+|"
    r"[A-Za-z]:[\\/][^\s'\"]+)"
)
URI_CREDENTIAL_RE = re.compile(r"[A-Za-z][A-Za-z0-9+.-]*://[^/@\s:]+:[^/@\s]+@")
SECRET_TOKEN_RES = (
    re.compile(r"\b(?:sk|rk|pk)-(?:live|test|proj)?-?[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{16,}\b", re.IGNORECASE),
)
SAFE_STRUCTURED_TOKEN_RE = re.compile(
    r"^(?:"
    r"urn:linzecolin:agentdatabase:skillops:[a-z0-9:-]+|"
    r"[a-z][a-z0-9]{1,11}_[0-7][0-9A-HJKMNP-TV-Z]{25}|"
    r"(?:sha1:[0-9a-f]{40}|sha256:[0-9a-f]{64})"
    r")$"
)
ENUM_CODE_RE = re.compile(r"^[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*$")
PUBLIC_REF_RE = re.compile(r"^[a-z][a-z0-9-]{2,63}$")


class ContractError(ValueError):
    """The input violates a frozen Mechanism contract."""


@dataclasses.dataclass(frozen=True)
class ContractBundle:
    schemas: Mapping[str, Any]
    registry: Any
    format_checker: Any
    self_digest_pointers: Mapping[str, Optional[str]]
    policies: Mapping[str, Any]
    protocol_revision: str


@dataclasses.dataclass(frozen=True)
class TrustTuple:
    verified_git_object_id: str
    expected_bundle_digest: str
    canonical_manifest_path: str
    mode: str


def _release_tuple(value: str) -> Tuple[int, ...]:
    match = re.match(r"^([0-9]+(?:\.[0-9]+)*)", value)
    if not match:
        raise ContractError(f"DEPENDENCY_VERSION_UNPARSEABLE:{value}")
    return tuple(int(part) for part in match.group(1).split("."))


def capability_gate() -> Mapping[str, str]:
    """Refuse unprovisioned or untested runtimes; never install at runtime."""
    if _DEPENDENCY_IMPORT_ERROR is not None:
        raise ContractError(f"DEPENDENCY_MISSING:{_DEPENDENCY_IMPORT_ERROR.name}")
    if not ((3, 9) <= sys.version_info[:2] < (3, 14)):
        raise ContractError(
            f"PYTHON_VERSION_UNSUPPORTED:{sys.version_info.major}.{sys.version_info.minor}"
        )
    versions = {
        "jsonschema": importlib.metadata.version("jsonschema"),
        "referencing": importlib.metadata.version("referencing"),
    }
    if not ((4, 25, 1) <= _release_tuple(versions["jsonschema"]) < (5,)):
        raise ContractError(f"JSONSCHEMA_VERSION_UNSUPPORTED:{versions['jsonschema']}")
    if not ((0, 36, 2) <= _release_tuple(versions["referencing"]) < (1,)):
        raise ContractError(f"REFERENCING_VERSION_UNSUPPORTED:{versions['referencing']}")
    return {
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        **versions,
    }


def strict_load(path: Path) -> Any:
    try:
        return parse_json_bytes(path.read_bytes())
    except OSError as exc:
        raise ContractError(f"FILE_READ_FAILED:{path}:{exc}") from exc
    except CanonicalizationError as exc:
        raise ContractError(f"STRICT_JSON_REJECTED:{path}:{exc}") from exc


def _walk(value: Any, path: Tuple[Any, ...] = ()) -> Iterator[Tuple[Tuple[Any, ...], Any]]:
    yield path, value
    if isinstance(value, dict):
        for key, child in value.items():
            yield from _walk(child, path + (key,))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk(child, path + (index,))


def _display_path(path: Iterable[Any]) -> str:
    parts = [str(part) for part in path]
    return "$" if not parts else "$/" + "/".join(parts)


def _decode_pointer(pointer: str) -> List[str]:
    if pointer == "":
        return []
    if not pointer.startswith("/") or "%" in pointer:
        raise ContractError(f"REF_FRAGMENT_NOT_PLAIN_JSON_POINTER:{pointer}")
    result: List[str] = []
    for raw_token in pointer[1:].split("/"):
        token: List[str] = []
        index = 0
        while index < len(raw_token):
            if raw_token[index] != "~":
                token.append(raw_token[index])
                index += 1
                continue
            if index + 1 >= len(raw_token) or raw_token[index + 1] not in "01":
                raise ContractError(f"REF_POINTER_ESCAPE_INVALID:{pointer}")
            token.append("~" if raw_token[index + 1] == "0" else "/")
            index += 2
        result.append("".join(token))
    return result


def _resolve_pointer(document: Any, pointer: str, ref_value: str) -> None:
    current = document
    for token in _decode_pointer(pointer):
        if isinstance(current, dict) and token in current:
            current = current[token]
        elif isinstance(current, list) and token.isdigit() and int(token) < len(current):
            current = current[int(token)]
        else:
            raise ContractError(f"REF_POINTER_NOT_FOUND:{ref_value}")


def _lint_schema_document(
    schema_id: str,
    document: Any,
    all_schemas: Mapping[str, Any],
) -> None:
    if not isinstance(document, dict):
        raise ContractError(f"SCHEMA_ROOT_NOT_OBJECT:{schema_id}")
    if document.get("$schema") != JSON_SCHEMA:
        raise ContractError(f"SCHEMA_DIALECT_MISMATCH:{schema_id}")
    if document.get("$id") != schema_id or not SCHEMA_ID_RE.fullmatch(schema_id):
        raise ContractError(f"SCHEMA_ID_INVALID:{schema_id}")
    if schema_id != SCHEMA_PREFIX + "common-definitions:v1" and document.get("type") != "object":
        raise ContractError(f"SCHEMA_ROOT_OBJECT_REQUIRED:{schema_id}")
    for path, node in _walk(document):
        if not isinstance(node, dict):
            continue
        if path and "$id" in node:
            raise ContractError(f"NESTED_SCHEMA_ID_FORBIDDEN:{schema_id}:{_display_path(path)}")
        forbidden = sorted(FORBIDDEN_SCHEMA_KEYWORDS.intersection(node))
        if forbidden:
            raise ContractError(
                f"SCHEMA_REBINDING_KEYWORD_FORBIDDEN:{schema_id}:"
                f"{_display_path(path)}:{','.join(forbidden)}"
            )
        if node.get("type") == "object" and node.get("additionalProperties") is not False:
            raise ContractError(f"OPEN_OBJECT_SCHEMA_FORBIDDEN:{schema_id}:{_display_path(path)}")
        if node.get("type") == "object":
            declared = set(node.get("properties", {}))

            def conditional_fields(constraint: Any) -> set:
                fields = set()
                if isinstance(constraint, dict):
                    properties = constraint.get("properties")
                    if isinstance(properties, dict):
                        fields.update(properties)
                    required = constraint.get("required")
                    if isinstance(required, list):
                        fields.update(item for item in required if isinstance(item, str))
                    for key, child in constraint.items():
                        if key != "properties":
                            fields.update(conditional_fields(child))
                elif isinstance(constraint, list):
                    for child in constraint:
                        fields.update(conditional_fields(child))
                return fields

            referenced = set()
            for keyword in ("allOf", "anyOf", "oneOf", "if", "then", "else", "not"):
                if keyword in node:
                    referenced.update(conditional_fields(node[keyword]))
            undeclared = referenced.difference(declared)
            if undeclared:
                raise ContractError(
                    f"CONDITIONAL_FIELD_UNDECLARED:{schema_id}:{_display_path(path)}:"
                    f"{','.join(sorted(undeclared))}"
                )
        if "format" in node and node["format"] not in ALLOWED_FORMATS:
            raise ContractError(
                f"UNKNOWN_FORMAT_FORBIDDEN:{schema_id}:{_display_path(path)}:{node['format']}"
            )
        if "$ref" not in node:
            continue
        ref_value = node["$ref"]
        if not isinstance(ref_value, str):
            raise ContractError(f"REF_NOT_STRING:{schema_id}:{_display_path(path)}")
        base, separator, fragment = ref_value.partition("#")
        if "#" in fragment:
            raise ContractError(f"REF_FRAGMENT_INVALID:{ref_value}")
        if base:
            if not SCHEMA_ID_RE.fullmatch(base):
                raise ContractError(f"REF_URI_FORBIDDEN:{ref_value}")
            if base not in all_schemas:
                raise ContractError(f"REF_SCHEMA_UNKNOWN:{ref_value}")
            target = all_schemas[base]
        else:
            target = document
        if separator:
            _resolve_pointer(target, fragment, ref_value)


def lint_schema_documents(schemas: Mapping[str, Any]) -> None:
    capability_gate()
    if not schemas:
        raise ContractError("SCHEMA_SET_EMPTY")
    if len(schemas) != len(set(schemas)):
        raise ContractError("SCHEMA_ID_DUPLICATE")
    for schema_id in sorted(schemas, key=lambda value: value.encode("ascii")):
        _lint_schema_document(schema_id, schemas[schema_id], schemas)
        try:
            Draft202012Validator.check_schema(schemas[schema_id])
        except Exception as exc:
            raise ContractError(f"SCHEMA_META_INVALID:{schema_id}:{exc}") from exc


def _format_checker() -> Any:
    capability_gate()
    checker = FormatChecker()

    @checker.checks("utc-z-timestamp-v1")
    def utc_z_timestamp(value: object) -> bool:
        if not isinstance(value, str) or UTC_RE.fullmatch(value) is None:
            return False
        try:
            parsed = dt.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
        except ValueError:
            return False
        return parsed.strftime("%Y-%m-%dT%H:%M:%S.%fZ") == value

    @checker.checks("calendar-date-v1")
    def calendar_date(value: object) -> bool:
        if not isinstance(value, str) or DATE_RE.fullmatch(value) is None:
            return False
        try:
            parsed = dt.datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            return False
        return parsed.strftime("%Y-%m-%d") == value

    @checker.checks("repo-relative-posix-path-v1")
    def repo_relative_path(value: object) -> bool:
        return is_repo_relative_posix_path(value)

    return checker


def is_repo_relative_posix_path(value: object) -> bool:
    if not isinstance(value, str) or not value or len(value.encode("utf-8")) > 4096:
        return False
    if value.startswith("/") or value.endswith("/") or "\\" in value:
        return False
    if any(ord(char) < 0x20 or ord(char) == 0x7F for char in value):
        return False
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        return False
    return PurePosixPath(value).as_posix() == value


def build_registry(schemas: Mapping[str, Any]) -> Tuple[Any, Any]:
    lint_schema_documents(schemas)

    def no_network_retrieve(uri: str) -> Any:
        raise NoSuchResource(ref=uri)

    registry = Registry(retrieve=no_network_retrieve).with_resources(
        (schema_id, Resource.from_contents(document))
        for schema_id, document in schemas.items()
    )
    return registry, _format_checker()


def load_schema_directories(directories: Sequence[Path]) -> Mapping[str, Any]:
    if not directories:
        raise ContractError("SCHEMA_DIRECTORY_REQUIRED")
    schemas: Dict[str, Any] = {}
    seen_files = 0
    for directory in directories:
        if not directory.is_dir():
            raise ContractError(f"SCHEMA_DIRECTORY_INVALID:{directory}")
        for path in sorted(directory.rglob("*.schema.json"), key=lambda item: item.as_posix()):
            if not path.is_file() or path.is_symlink():
                raise ContractError(f"SCHEMA_FILE_NOT_REGULAR:{path}")
            document = strict_load(path)
            if not isinstance(document, dict) or not isinstance(document.get("$id"), str):
                raise ContractError(f"SCHEMA_FILE_ID_MISSING:{path}")
            schema_id = document["$id"]
            if schema_id in schemas:
                raise ContractError(f"SCHEMA_ID_DUPLICATE:{schema_id}")
            schemas[schema_id] = document
            seen_files += 1
    if not seen_files:
        raise ContractError("SCHEMA_DIRECTORY_SET_EMPTY")
    return schemas


def _schema_errors(
    instance: Any,
    schema: Any,
    registry: Any,
    format_checker: Any,
) -> List[str]:
    try:
        errors = list(
            Draft202012Validator(
                schema,
                registry=registry,
                format_checker=format_checker,
            ).iter_errors(instance)
        )
    except Unresolvable as exc:
        raise ContractError(f"SCHEMA_REFERENCE_UNRESOLVABLE:{exc}") from exc
    return [
        f"{_display_path(error.absolute_path)}:{error.message}"
        for error in sorted(errors, key=lambda item: tuple(str(p) for p in item.absolute_path))
    ]


def _ensure_sorted_unique(items: Sequence[Any], key_name: str, code: str) -> None:
    keys = [item[key_name] if isinstance(item, dict) else item for item in items]
    expected = sorted(keys, key=lambda value: str(value).encode("utf-8"))
    if keys != expected or len(keys) != len(set(keys)):
        raise ContractError(f"{code}:SORTED_UNIQUE_REQUIRED")


def _ensure_unique(items: Sequence[Any], key_name: str, code: str) -> None:
    keys = [item[key_name] if isinstance(item, dict) else item for item in items]
    if len(keys) != len(set(keys)):
        raise ContractError(f"{code}:UNIQUE_REQUIRED")


def _parse_utc(value: str) -> dt.datetime:
    try:
        return dt.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError as exc:
        raise ContractError(f"UTC_TIMESTAMP_INVALID:{value}") from exc


def semantic_validate(schema_id: str, instance: Any) -> None:
    name = schema_id[len(SCHEMA_PREFIX):].rsplit(":v", 1)[0]
    if name == "eval-profile":
        weights = instance["dimension_weights_bps"]
        _ensure_sorted_unique(weights, "dimension_code", "EVAL_DIMENSION_ORDER")
        if {item["dimension_code"] for item in weights} != EVAL_DIMENSION_CODES:
            raise ContractError("EVAL_DIMENSION_SET_INCOMPLETE")
        if sum(item["weight_bps"] for item in weights) != 10000:
            raise ContractError("EVAL_WEIGHT_SUM_NOT_10000")
        _ensure_sorted_unique(instance["hard_gate_codes"], "", "EVAL_HARD_GATE_ORDER")
        if set(instance["hard_gate_codes"]) != CORE_HARD_GATE_CODES:
            raise ContractError("EVAL_HARD_GATE_SET_INCOMPLETE")
        if _parse_utc(instance["updated_at"]) < _parse_utc(instance["created_at"]):
            raise ContractError("EVAL_PROFILE_TIME_ORDER_INVALID")
    elif name == "eval-run":
        if _parse_utc(instance["finished_at"]) < _parse_utc(instance["started_at"]):
            raise ContractError("EVAL_TIME_ORDER_INVALID")
    elif name == "scorecard":
        _ensure_sorted_unique(instance["hard_gates"], "gate_code", "HARD_GATE_ORDER")
        _ensure_sorted_unique(instance["dimensions"], "dimension_code", "SCORE_DIMENSION_ORDER")
        if {item["gate_code"] for item in instance["hard_gates"]} != CORE_HARD_GATE_CODES:
            raise ContractError("SCORE_HARD_GATE_SET_INCOMPLETE")
        if {item["dimension_code"] for item in instance["dimensions"]} != EVAL_DIMENSION_CODES:
            raise ContractError("SCORE_DIMENSION_SET_INCOMPLETE")
        if any(not gate["passed"] for gate in instance["hard_gates"]) and instance["promotion_eligible"]:
            raise ContractError("FAILED_HARD_GATE_CANNOT_PROMOTE")
        if instance["critical_incident_count"] != len(instance["critical_incident_evidence_digests"]):
            raise ContractError("CRITICAL_INCIDENT_COUNT_MISMATCH")
        if instance["critical_incident_count"] and instance["promotion_eligible"]:
            raise ContractError("CRITICAL_INCIDENT_CANNOT_PROMOTE")
        if instance["freshness_state"] != "FRESH" and instance["promotion_eligible"]:
            raise ContractError("STALE_OR_UNKNOWN_EVIDENCE_CANNOT_PROMOTE")
        if instance["freshness_state"] == "FRESH" and instance["freshness_valid_until"] is None:
            raise ContractError("FRESHNESS_DEADLINE_REQUIRED")
        for stratum, result in instance["routing_results"].items():
            if result["correct_count"] > result["sample_count"]:
                raise ContractError(f"ROUTING_CORRECT_COUNT_EXCEEDS_SAMPLE:{stratum}")
        calibration = instance["judge_calibration"]
        if calibration["state"] == "NOT_USED" and any(
            calibration[field] is not None
            for field in ("agreement_bps", "bias_bps", "drift_bps", "evidence_digest")
        ):
            raise ContractError("JUDGE_NOT_USED_MUST_HAVE_NULL_METRICS")
        if calibration["state"] == "CALIBRATED" and any(
            calibration[field] is None
            for field in ("agreement_bps", "bias_bps", "drift_bps", "evidence_digest")
        ):
            raise ContractError("JUDGE_CALIBRATION_EVIDENCE_REQUIRED")
    elif name == "promotion-evidence-bundle":
        if instance["notification_required"] != (instance["notification_receipt_digest"] is not None):
            raise ContractError("NOTIFICATION_RECEIPT_REQUIREMENT_MISMATCH")
        _ensure_sorted_unique(instance["causal_matrix"], "cell", "CAUSAL_MATRIX_ORDER")
        if {cell["cell"] for cell in instance["causal_matrix"]} != CAUSAL_MATRIX_CELLS:
            raise ContractError("CAUSAL_MATRIX_INCOMPLETE")
        if instance["hard_gates_passed"] and any(
            cell["status"] != "PASS" for cell in instance["causal_matrix"]
        ):
            raise ContractError("HARD_GATES_PASS_REQUIRES_COMPLETE_CAUSAL_MATRIX")
        if instance["rollback_target_version_uid"] == instance["candidate_skill_version_uid"]:
            raise ContractError("EVIDENCE_ROLLBACK_TARGET_CANNOT_EQUAL_CANDIDATE")
    elif name == "promotion-decision":
        if instance["major_change"] and instance["notification_receipt_digest"] is None:
            raise ContractError("MAJOR_CHANGE_NOTIFICATION_RECEIPT_REQUIRED")
        if instance["major_change"] != (instance["impact"] == "MAJOR"):
            raise ContractError("MAJOR_CHANGE_IMPACT_MISMATCH")
        if instance["action"] == "PROMOTE" and instance["resulting_champion_version_uid"] is None:
            raise ContractError("PROMOTE_RESULTING_CHAMPION_REQUIRED")
        if instance["action"] == "PROMOTE" and not instance["hard_gates_passed"]:
            raise ContractError("PROMOTE_REQUIRES_HARD_GATES")
        if instance["action"] in {"PROMOTE", "ROLLBACK", "REVOKE"} and instance["rollback_target_version_uid"] is None:
            raise ContractError("ROLLBACK_TARGET_REQUIRED")
        if instance["major_change"] and not instance["emergency_containment"]:
            if instance["notification_mode"] != "PRE_WRITE_SENT":
                raise ContractError("PLANNED_MAJOR_PRE_WRITE_NOTIFICATION_REQUIRED")
        if instance["emergency_containment"]:
            if instance["notification_receipt_digest"] is None:
                raise ContractError("EMERGENCY_NOTIFICATION_RECEIPT_REQUIRED")
            if instance["notification_mode"] != "POST_CONTAINMENT_SENT":
                raise ContractError("EMERGENCY_POST_CONTAINMENT_NOTIFICATION_REQUIRED")
        elif not instance["major_change"] and instance["notification_mode"] != "NOT_REQUIRED":
            raise ContractError("NON_MAJOR_NOTIFICATION_MODE_INVALID")
        if instance["action"] == "PROMOTE":
            if instance["from_status"] != "CHALLENGER" or instance["to_status"] != "CHAMPION":
                raise ContractError("PROMOTION_LIFECYCLE_TRANSITION_INVALID")
            if instance["resulting_champion_version_uid"] != instance["candidate_skill_version_uid"]:
                raise ContractError("PROMOTION_CHAMPION_MUST_EQUAL_CANDIDATE")
        if instance["rollback_target_version_uid"] == instance["candidate_skill_version_uid"]:
            raise ContractError("ROLLBACK_TARGET_CANNOT_EQUAL_CANDIDATE")
    elif name == "iteration-transition":
        if instance["from_skill_version_uid"] == instance["to_skill_version_uid"]:
            raise ContractError("ITERATION_VERSION_MUST_CHANGE")
        if instance["phase"] == "SHADOW" and instance["side_effect_budget"] != 0:
            raise ContractError("SHADOW_SIDE_EFFECT_BUDGET_MUST_BE_ZERO")
    elif name == "skill-identity":
        if _parse_utc(instance["updated_at"]) < _parse_utc(instance["created_at"]):
            raise ContractError("IDENTITY_TIME_ORDER_INVALID")
    elif name == "skill-instance":
        if _parse_utc(instance["last_seen_at"]) < _parse_utc(instance["first_seen_at"]):
            raise ContractError("INSTANCE_TIME_ORDER_INVALID")
        if instance["moved_from_instance_uid"] == instance["skill_instance_uid"]:
            raise ContractError("INSTANCE_CANNOT_MOVE_FROM_SELF")
        if instance["forked_from_instance_uid"] == instance["skill_instance_uid"]:
            raise ContractError("INSTANCE_CANNOT_FORK_FROM_SELF")
        provenance = instance["provenance"]
        if (
            provenance["license_state"] != "KNOWN_ALLOWED"
            or provenance["trust_tier"] in {"UNVERIFIED", "QUARANTINED"}
        ) and instance["lifecycle_status"] not in {"DISCOVERED", "QUARANTINED", "UNKNOWN"}:
            raise ContractError("UNRESOLVED_PROVENANCE_MUST_QUARANTINE")
    elif name == "skill-version":
        if instance["trust_tier"] in {"UNVERIFIED", "QUARANTINED"} and instance[
            "lifecycle_status"
        ] not in {"DISCOVERED", "QUARANTINED", "UNKNOWN"}:
            raise ContractError("UNTRUSTED_VERSION_MUST_QUARANTINE")
    elif name == "skill-passport":
        provenance = instance["provenance"]
        if (
            provenance["license_state"] != "KNOWN_ALLOWED"
            or provenance["trust_tier"] in {"UNVERIFIED", "QUARANTINED"}
        ) and instance["lifecycle_status"] == "CHAMPION":
            raise ContractError("UNTRUSTED_PASSPORT_CANNOT_BE_CHAMPION")
    elif name == "capability-graph":
        if instance["node_count"] != len(instance["nodes"]):
            raise ContractError("GRAPH_NODE_COUNT_MISMATCH")
        if instance["edge_count"] != len(instance["edges"]):
            raise ContractError("GRAPH_EDGE_COUNT_MISMATCH")
        _ensure_sorted_unique(instance["nodes"], "uid", "GRAPH_NODE_ORDER")
        edge_keys = [
            (edge["from_uid"], edge["to_uid"], edge["edge_type"])
            for edge in instance["edges"]
        ]
        if edge_keys != sorted(edge_keys) or len(edge_keys) != len(set(edge_keys)):
            raise ContractError("GRAPH_EDGE_ORDER:SORTED_UNIQUE_REQUIRED")
        node_uids = {node["uid"] for node in instance["nodes"]}
        if any(edge["from_uid"] not in node_uids or edge["to_uid"] not in node_uids for edge in instance["edges"]):
            raise ContractError("GRAPH_EDGE_ENDPOINT_UNKNOWN")
    elif name == "schema-bundle-manifest":
        if instance["schema_count"] != len(instance["schemas"]):
            raise ContractError("MANIFEST_SCHEMA_COUNT_MISMATCH")
        if instance["policy_count"] != len(instance["policies"]):
            raise ContractError("MANIFEST_POLICY_COUNT_MISMATCH")
        _ensure_sorted_unique(instance["schemas"], "id", "MANIFEST_SCHEMA_ORDER")
        _ensure_sorted_unique(instance["policies"], "id", "MANIFEST_POLICY_ORDER")
        if any(entry["id"].startswith(SCHEMA_PREFIX) is False for entry in instance["schemas"]):
            raise ContractError("MANIFEST_SCHEMA_ID_NAMESPACE_INVALID")
    elif name == "public-value-policy":
        _ensure_unique(instance["detectors"], "code", "PUBLIC_DETECTOR_CODE")
        _ensure_unique(instance["detectors"], "kind", "PUBLIC_DETECTOR_KIND")
        expected_kinds = {
            "EMAIL", "PHONE_NUMBER", "IP_ADDRESS", "ABSOLUTE_PATH",
            "SECRET_TOKEN", "PRIVATE_KEY", "URI_CREDENTIAL",
            "HIGH_ENTROPY_FREE_STRING",
        }
        if {entry["kind"] for entry in instance["detectors"]} != expected_kinds:
            raise ContractError("PUBLIC_DETECTOR_SET_INCOMPLETE")
    elif name == "source-material-policy":
        _ensure_unique(instance["exclusions"], "rule_id", "SOURCE_EXCLUSION_RULE")
        patterns = {entry["pattern"] for entry in instance["exclusions"]}
        if not {".git", ".git/**", "**/.git", "**/.git/**"}.issubset(patterns):
            raise ContractError("VCS_METADATA_EXCLUSIONS_INCOMPLETE")


def validate_instance(
    bundle: ContractBundle,
    instance: Any,
    expected_schema_id: str,
    *,
    expected_bundle_digest: Optional[str] = None,
    public: bool = False,
    verify_digest: bool = True,
) -> None:
    if expected_schema_id not in bundle.schemas:
        raise ContractError(f"TRUSTED_SCHEMA_ID_UNKNOWN:{expected_schema_id}")
    schema = bundle.schemas[expected_schema_id]
    errors = _schema_errors(instance, schema, bundle.registry, bundle.format_checker)
    if errors:
        raise ContractError(f"SCHEMA_VALIDATION_FAILED:{expected_schema_id}:{' | '.join(errors)}")
    root_properties = schema.get("properties", {}) if isinstance(schema, dict) else {}
    contextual = "bundle_digest" in root_properties and expected_schema_id != MANIFEST_SCHEMA_ID
    if contextual:
        if expected_bundle_digest is None:
            raise ContractError("EXPECTED_BUNDLE_DIGEST_REQUIRED")
        if not SHA256_RE.fullmatch(expected_bundle_digest):
            raise ContractError("EXPECTED_BUNDLE_DIGEST_INVALID")
        if instance.get("bundle_digest") != expected_bundle_digest:
            raise ContractError("CONTEXT_BUNDLE_DIGEST_MISMATCH")
    pointer = bundle.self_digest_pointers.get(expected_schema_id)
    if verify_digest and pointer:
        try:
            matches = verify_self_digest(instance, pointer)
        except CanonicalizationError as exc:
            raise ContractError(f"SELF_DIGEST_INVALID:{expected_schema_id}:{exc}") from exc
        if not matches:
            raise ContractError(f"SELF_DIGEST_MISMATCH:{expected_schema_id}:{pointer}")
    semantic_validate(expected_schema_id, instance)
    if public:
        scan_public_value(instance, bundle.policies)


def _entropy(value: str) -> float:
    frequencies: Dict[str, int] = {}
    for char in value:
        frequencies[char] = frequencies.get(char, 0) + 1
    size = len(value)
    return -sum((count / size) * math.log2(count / size) for count in frequencies.values())


def scan_public_value(value: Any, policies: Mapping[str, Any]) -> None:
    public_policy = policies.get(
        "urn:linzecolin:agentdatabase:skillops:policy:public-value:v1"
    )
    if not isinstance(public_policy, dict):
        raise ContractError("PUBLIC_VALUE_POLICY_NOT_TRUSTED")
    forbidden = set(public_policy["forbidden_field_names"])
    allowed_entropy = set(public_policy["allowed_high_entropy_field_names"])
    max_length = public_policy["max_public_string_length"]

    def visit(node: Any, path: Tuple[Any, ...], field_name: Optional[str]) -> None:
        if isinstance(node, dict):
            for key, child in node.items():
                if key.lower() in forbidden:
                    raise ContractError(f"PUBLIC_FORBIDDEN_FIELD:{_display_path(path + (key,))}")
                visit(child, path + (key,), key)
            return
        if isinstance(node, list):
            for index, child in enumerate(node):
                visit(child, path + (index,), field_name)
            return
        if not isinstance(node, str):
            return
        if len(node) > max_length:
            raise ContractError(f"PUBLIC_STRING_TOO_LONG:{_display_path(path)}")
        if EMAIL_RE.search(node):
            raise ContractError(f"PUBLIC_EMAIL_BLOCK:{_display_path(path)}")
        for candidate in IPV4_CANDIDATE_RE.finditer(node):
            try:
                ipaddress.ip_address(candidate.group())
            except ValueError:
                continue
            raise ContractError(f"PUBLIC_IP_ADDRESS_BLOCK:{_display_path(path)}")
        for candidate in PHONE_CANDIDATE_RE.finditer(node):
            digit_count = sum(char.isdigit() for char in candidate.group())
            if 9 <= digit_count <= 15:
                raise ContractError(f"PUBLIC_PHONE_NUMBER_BLOCK:{_display_path(path)}")
        if field_name != "self_digest_pointer" and ABSOLUTE_PATH_RE.search(node):
            raise ContractError(f"PUBLIC_ABSOLUTE_PATH_BLOCK:{_display_path(path)}")
        if "-----BEGIN " in node and "PRIVATE KEY-----" in node:
            raise ContractError(f"PUBLIC_PRIVATE_KEY_BLOCK:{_display_path(path)}")
        if URI_CREDENTIAL_RE.search(node):
            raise ContractError(f"PUBLIC_URI_CREDENTIAL_BLOCK:{_display_path(path)}")
        if any(pattern.search(node) for pattern in SECRET_TOKEN_RES):
            raise ContractError(f"PUBLIC_SECRET_TOKEN_BLOCK:{_display_path(path)}")
        if field_name in allowed_entropy:
            if not SHA256_RE.fullmatch(node):
                raise ContractError(f"PUBLIC_APPROVED_DIGEST_MALFORMED:{_display_path(path)}")
            return
        if SHA256_RE.fullmatch(node):
            raise ContractError(f"PUBLIC_HIGH_ENTROPY_FREE_STRING_BLOCK:{_display_path(path)}")
        if field_name is not None and field_name.endswith("path") and is_repo_relative_posix_path(node):
            return
        enum_field = field_name is not None and (
            "code" in field_name
            or field_name in {
                "action", "actor", "binding_state", "compatibility", "edge_type",
                "event_type", "freshness_state", "kind", "lifecycle_status",
                "mode", "node_type", "phase", "reason", "risk_tier", "stage",
                "state", "status", "surface_class",
            }
        )
        public_ref_field = field_name is not None and (
            field_name.endswith("_ref") or field_name in {"owner_ref", "recipient_ref"}
        )
        if (
            SAFE_STRUCTURED_TOKEN_RE.fullmatch(node)
            or (enum_field and ENUM_CODE_RE.fullmatch(node))
            or (public_ref_field and PUBLIC_REF_RE.fullmatch(node))
            or node.startswith("https://")
        ):
            return
        token_like = len(node) >= 32 and re.fullmatch(r"[A-Za-z0-9._~+/=-]+", node)
        if token_like and _entropy(node) >= 4.0:
            raise ContractError(f"PUBLIC_HIGH_ENTROPY_FREE_STRING_BLOCK:{_display_path(path)}")

    visit(value, (), None)


def _repo_path(relative: str) -> Path:
    if not is_repo_relative_posix_path(relative):
        raise ContractError(f"REPO_PATH_INVALID:{relative}")
    path = REPO_ROOT.joinpath(*relative.split("/"))
    try:
        path.resolve().relative_to(REPO_ROOT.resolve())
    except ValueError as exc:
        raise ContractError(f"REPO_PATH_ESCAPES_ROOT:{relative}") from exc
    return path


def _entry_order(entries: Sequence[Any], code: str) -> None:
    _ensure_sorted_unique(entries, "id", code)


def load_draft_contract() -> ContractBundle:
    capability_gate()
    verify_vendor()
    interface = strict_load(INTERFACE_PATH)
    if interface.get("status") != "DRAFT_NON_ACTIVE" or interface.get("activation_forbidden") is not True:
        raise ContractError("DRAFT_STATUS_INVALID")
    if interface.get("protocol_revision") != PROTOCOL:
        raise ContractError("PROTOCOL_REVISION_MISMATCH")
    schema_entries = interface.get("mechanism_schema_entries")
    policy_entries = interface.get("mechanism_policy_entries")
    if not isinstance(schema_entries, list) or len(schema_entries) != 21:
        raise ContractError("DRAFT_SCHEMA_COUNT_INVALID")
    if interface.get("mechanism_schema_count") != len(schema_entries):
        raise ContractError("DRAFT_SCHEMA_COUNT_MISMATCH")
    if not isinstance(policy_entries, list) or len(policy_entries) != 5:
        raise ContractError("DRAFT_POLICY_COUNT_INVALID")
    if interface.get("mechanism_policy_count") != len(policy_entries):
        raise ContractError("DRAFT_POLICY_COUNT_MISMATCH")
    _entry_order(schema_entries, "DRAFT_SCHEMA_ENTRY_ORDER")
    _entry_order(policy_entries, "DRAFT_POLICY_ENTRY_ORDER")
    schemas: Dict[str, Any] = {}
    pointers: Dict[str, Optional[str]] = {}
    for entry in schema_entries:
        schema_id = entry["id"]
        if entry.get("owner_plane") != "MECHANISM":
            raise ContractError(f"DRAFT_SCHEMA_OWNER_MISMATCH:{schema_id}")
        path = _repo_path(entry["relative_path"])
        document = strict_load(path)
        if document.get("$id") != schema_id or entry["schema_version"] != schema_id:
            raise ContractError(f"DRAFT_SCHEMA_ID_MISMATCH:{schema_id}")
        actual = hashlib.sha256(canonicalize_object(document)).hexdigest()
        if actual != entry["schema_sha256"]:
            raise ContractError(f"DRAFT_SCHEMA_DIGEST_MISMATCH:{schema_id}")
        schemas[schema_id] = document
        pointers[schema_id] = entry["self_digest_pointer"]
        if EXPECTED_SCHEMA_SELF_POINTERS.get(schema_id) != entry["self_digest_pointer"]:
            raise ContractError(f"DRAFT_SELF_DIGEST_POINTER_MISMATCH:{schema_id}")
    if set(schemas) != set(EXPECTED_SCHEMA_SELF_POINTERS).difference(AUTO_PUBLIC_SCHEMA_IDS):
        raise ContractError("DRAFT_MECHANISM_SCHEMA_SET_MISMATCH")
    auto_contracts = interface.get("auto_public_schema_contracts_required_for_complete_bundle")
    if not isinstance(auto_contracts, list):
        raise ContractError("DRAFT_AUTO_PUBLIC_CONTRACTS_MISSING")
    _entry_order(auto_contracts, "DRAFT_AUTO_PUBLIC_CONTRACT_ORDER")
    if {entry.get("id") for entry in auto_contracts} != AUTO_PUBLIC_SCHEMA_IDS:
        raise ContractError("DRAFT_AUTO_PUBLIC_SCHEMA_SET_MISMATCH")
    for entry in auto_contracts:
        if entry.get("owner_plane") != "AUTO":
            raise ContractError(f"DRAFT_AUTO_SCHEMA_OWNER_MISMATCH:{entry.get('id')}")
        if entry.get("self_digest_pointer") != EXPECTED_SCHEMA_SELF_POINTERS[entry["id"]]:
            raise ContractError(f"DRAFT_AUTO_SELF_DIGEST_POINTER_MISMATCH:{entry['id']}")
    if set(interface.get("auto_private_schema_ids_excluded_from_shared_bundle", [])) != AUTO_PRIVATE_SCHEMA_IDS:
        raise ContractError("DRAFT_AUTO_PRIVATE_SCHEMA_SET_MISMATCH")
    complete = interface.get("complete_bundle_contract", {})
    if (
        complete.get("schema_count") != len(EXPECTED_SCHEMA_SELF_POINTERS)
        or complete.get("policy_count") != len(EXPECTED_POLICY_IDS)
        or complete.get("extra_schema_ids_allowed") is not False
        or complete.get("auto_private_schemas_included") is not False
    ):
        raise ContractError("DRAFT_COMPLETE_BUNDLE_CONTRACT_MISMATCH")
    binding_contract = interface.get("binding_contract", {})
    if (
        binding_contract.get("schema_id") != SCHEMA_PREFIX + "skill-binding:v1"
        or binding_contract.get("run_event_states") != ["BOUND", "UNKNOWN"]
        or set(binding_contract.get("bound_eval_eligible_surfaces", []))
        != {"CODEX_AUTOMATION", "CODEX_CLI"}
        or binding_contract.get("published_event_mutation") != "FORBIDDEN_SUPERSEDE_ONLY"
    ):
        raise ContractError("DRAFT_BINDING_CONTRACT_MISMATCH")
    actor_role_contract = interface.get("actor_role_contract", {})
    if (
        actor_role_contract.get("allowed_codes")
        != ["USER", "AUTOMATION", "SUBAGENT", "CLI", "UNKNOWN"]
        or actor_role_contract.get("unknown_semantics")
        != "OBSERVED_ACTOR_ROLE_NOT_PROVABLE"
        or actor_role_contract.get("initial_unknown_surfaces") != ["AGENTS", "CLAUDE"]
        or actor_role_contract.get("unknown_is_binding_state") is not False
        or actor_role_contract.get("unknown_legacy_code_allowed") is not False
        or actor_role_contract.get("legacy_thread_source_missing_treatment") != "UNMAPPED"
    ):
        raise ContractError("DRAFT_ACTOR_ROLE_CONTRACT_MISMATCH")
    public_value_contract = interface.get("public_value_contract", {})
    if (
        public_value_contract.get("approved_auto_public_sha256_fields")
        != [
            "adapter_schema_digest",
            "included_tree_digest",
            "mapping_policy_digest",
            "supersedes_event_digest",
        ]
        or public_value_contract.get("approved_value_shape") != "LOWERCASE_SHA256_HEX_64"
        or public_value_contract.get("generic_digest_field_substitution_allowed") is not False
    ):
        raise ContractError("DRAFT_PUBLIC_VALUE_CONTRACT_MISMATCH")
    baseline = interface.get("run_surface_baseline_contract", {})
    breakdown = baseline.get("mapped_breakdown", [])
    unmapped_reasons = baseline.get("unmapped_reasons", [])
    if not isinstance(breakdown, list) or not isinstance(unmapped_reasons, list):
        raise ContractError("DRAFT_RUN_SURFACE_BASELINE_SHAPE_INVALID")
    observed_breakdown = {
        (item.get("surface_class"), item.get("actor_role"), item.get("count"))
        for item in breakdown
        if isinstance(item, dict)
    }
    expected_breakdown = {
        ("CODEX_AUTOMATION", "AUTOMATION", 46),
        ("CODEX_CLI", "CLI", 8),
        ("CODEX_DESKTOP", "SUBAGENT", 329),
        ("CODEX_DESKTOP", "USER", 176),
    }
    if (
        baseline.get("action") != "BASELINE_ESTABLISHED_NO_HISTORICAL_BACKFILL"
        or baseline.get("input_count") != 577
        or baseline.get("mapped_count") != 559
        or baseline.get("unmapped_count") != 18
        or baseline.get("policy_excluded_count") != 0
        or baseline.get("quarantined_count") != 0
        or baseline.get("coverage_state") != "UNKNOWN"
        or observed_breakdown != expected_breakdown
        or unmapped_reasons != [{"reason_code": "LEGACY_THREAD_SOURCE_MISSING", "count": 18}]
        or sum(item.get("count", -1) for item in breakdown if isinstance(item, dict)) != 559
        or sum(item.get("count", -1) for item in unmapped_reasons if isinstance(item, dict)) != 18
        or baseline.get("historical_public_run_events") != 0
        or baseline.get("post_cutover_windows_only") is not True
    ):
        raise ContractError("DRAFT_RUN_SURFACE_BASELINE_MISMATCH")
    consumer = interface.get("consumer_first_contract", {})
    if (
        consumer.get("target_path") != "OpenAIDatabase/data/run_logs/skills_runs/"
        or consumer.get("target_schema_id") != SCHEMA_PREFIX + "public-run-event:v2"
        or consumer.get("owner_plane") != "MECHANISM"
        or consumer.get("must_land_before_canonical_publish") is not True
    ):
        raise ContractError("DRAFT_CONSUMER_FIRST_CONTRACT_MISMATCH")
    registry, checker = build_registry(schemas)
    policies: Dict[str, Any] = {}
    bundle = ContractBundle(schemas, registry, checker, pointers, policies, PROTOCOL)
    for entry in policy_entries:
        if entry.get("owner_plane") != "MECHANISM":
            raise ContractError(f"DRAFT_POLICY_OWNER_MISMATCH:{entry.get('id')}")
        policy = strict_load(_repo_path(entry["relative_path"]))
        actual = hashlib.sha256(canonicalize_object(policy)).hexdigest()
        if actual != entry["policy_sha256"]:
            raise ContractError(f"DRAFT_POLICY_DIGEST_MISMATCH:{entry['id']}")
        if policy.get("policy_id") != entry["id"] or policy.get("schema_version") != entry["schema_id"]:
            raise ContractError(f"DRAFT_POLICY_BINDING_MISMATCH:{entry['id']}")
        validate_instance(bundle, policy, entry["schema_id"], verify_digest=False)
        policies[entry["id"]] = policy
    if set(policies) != EXPECTED_POLICY_IDS:
        raise ContractError("DRAFT_POLICY_SET_MISMATCH")
    vectors = strict_load(GOVERNANCE_DIR / "test_vectors" / "canonicalization-v1.json")
    vectors_digest = hashlib.sha256(canonicalize_object(vectors)).hexdigest()
    if vectors_digest != interface["canonicalization"]["test_vectors_digest"]:
        raise ContractError("TEST_VECTOR_DIGEST_MISMATCH")
    if _repo_path(CANONICAL_MANIFEST_PATH).exists():
        raise ContractError("ACTIVE_OR_CANDIDATE_MANIFEST_FORBIDDEN_IN_M0A")
    if (REPO_ROOT / "CodexSkills" / "VERSION").exists():
        raise ContractError("ACTIVE_VERSION_FORBIDDEN_IN_M0A")
    return ContractBundle(schemas, registry, checker, pointers, policies, PROTOCOL)


def _git(repo_root: Path, args: Sequence[str], *, binary: bool = False) -> Any:
    process = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        text=not binary,
    )
    if process.returncode != 0:
        stderr = process.stderr.decode("utf-8", "replace") if binary else process.stderr
        raise ContractError(f"GIT_READ_FAILED:{' '.join(args)}:{stderr.strip()}")
    return process.stdout


def _git_blob(repo_root: Path, object_id: str, relative_path: str) -> bytes:
    if not is_repo_relative_posix_path(relative_path):
        raise ContractError(f"TRUSTED_BUNDLE_PATH_INVALID:{relative_path}")
    return _git(repo_root, ["show", f"{object_id}:{relative_path}"], binary=True)


def _trusted_entry_shape(
    entries: Any,
    required_fields: Iterable[str],
    code: str,
) -> List[Mapping[str, Any]]:
    if not isinstance(entries, list) or not entries:
        raise ContractError(f"{code}_ENTRIES_INVALID")
    required = set(required_fields)
    shaped: List[Mapping[str, Any]] = []
    paths: List[str] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict) or not required.issubset(entry):
            raise ContractError(f"{code}_ENTRY_SHAPE_INVALID:{index}")
        if not isinstance(entry["id"], str) or not isinstance(entry["relative_path"], str):
            raise ContractError(f"{code}_ENTRY_TYPE_INVALID:{index}")
        shaped.append(entry)
        paths.append(entry["relative_path"])
    if len(paths) != len(set(paths)):
        raise ContractError(f"{code}_PATH_DUPLICATE")
    _entry_order(shaped, f"{code}_ENTRY_ORDER")
    return shaped


def load_trusted_bundle(repo_root: Path, trust: TrustTuple) -> ContractBundle:
    """Build an offline registry only after the external trust tuple verifies."""
    capability_gate()
    match = GIT_OBJECT_RE.fullmatch(trust.verified_git_object_id)
    if not match:
        raise ContractError("TRUST_GIT_OBJECT_ID_INVALID")
    algorithm = match.group(1) or match.group(3)
    object_id = match.group(2) or match.group(4)
    if not SHA256_RE.fullmatch(trust.expected_bundle_digest):
        raise ContractError("TRUST_EXPECTED_BUNDLE_DIGEST_INVALID")
    if trust.canonical_manifest_path != CANONICAL_MANIFEST_PATH:
        raise ContractError("TRUST_CANONICAL_MANIFEST_PATH_MISMATCH")
    if trust.mode not in {"CANDIDATE", "ACTIVE"}:
        raise ContractError("TRUST_MODE_INVALID")
    observed_format = _git(repo_root, ["rev-parse", "--show-object-format"]).strip()
    if observed_format != algorithm:
        raise ContractError(f"TRUST_GIT_ALGORITHM_MISMATCH:{algorithm}:{observed_format}")
    _git(repo_root, ["cat-file", "-e", f"{object_id}^{{commit}}"])
    manifest = parse_json_bytes(
        _git_blob(repo_root, object_id, trust.canonical_manifest_path)
    )
    if not isinstance(manifest, dict):
        raise ContractError("TRUST_MANIFEST_ROOT_INVALID")
    if manifest.get("bundle_digest") != trust.expected_bundle_digest:
        raise ContractError("TRUST_MANIFEST_SELF_REPORT_MISMATCH")
    if canonical_digest(manifest, "/bundle_digest") != trust.expected_bundle_digest:
        raise ContractError("TRUST_MANIFEST_DIGEST_MISMATCH")
    if manifest.get("schema_version") != MANIFEST_SCHEMA_ID:
        raise ContractError("TRUST_MANIFEST_SCHEMA_ID_MISMATCH")
    if manifest.get("protocol_revision") != PROTOCOL:
        raise ContractError("TRUST_MANIFEST_PROTOCOL_MISMATCH")
    schema_entries = _trusted_entry_shape(
        manifest.get("schemas"),
        {
            "id", "owner_plane", "relative_path", "schema_version",
            "schema_sha256", "compatibility", "self_digest_pointer",
        },
        "TRUST_SCHEMA",
    )
    policy_entries = _trusted_entry_shape(
        manifest.get("policies"),
        {
            "id", "owner_plane", "relative_path", "schema_id",
            "policy_sha256", "compatibility",
        },
        "TRUST_POLICY",
    )
    if manifest.get("schema_count") != len(schema_entries):
        raise ContractError("TRUST_MANIFEST_SCHEMA_COUNT_MISMATCH")
    if manifest.get("policy_count") != len(policy_entries):
        raise ContractError("TRUST_MANIFEST_POLICY_COUNT_MISMATCH")
    schema_ids = {entry["id"] for entry in schema_entries}
    if schema_ids != set(EXPECTED_SCHEMA_SELF_POINTERS):
        raise ContractError("TRUST_COMPLETE_SCHEMA_SET_MISMATCH")
    if schema_ids.intersection(AUTO_PRIVATE_SCHEMA_IDS):
        raise ContractError("TRUST_AUTO_PRIVATE_SCHEMA_INCLUDED")
    if {entry["id"] for entry in policy_entries} != EXPECTED_POLICY_IDS:
        raise ContractError("TRUST_POLICY_SET_MISMATCH")
    schemas: Dict[str, Any] = {}
    pointers: Dict[str, Optional[str]] = {}
    for entry in schema_entries:
        schema_id = entry["id"]
        expected_owner = "AUTO" if schema_id in AUTO_PUBLIC_SCHEMA_IDS else "MECHANISM"
        if entry["owner_plane"] != expected_owner:
            raise ContractError(f"TRUST_SCHEMA_OWNER_MISMATCH:{schema_id}")
        if entry["self_digest_pointer"] != EXPECTED_SCHEMA_SELF_POINTERS[schema_id]:
            raise ContractError(f"TRUST_SELF_DIGEST_POINTER_MISMATCH:{schema_id}")
        expected_prefix = (
            "CodexSkills/auto/schemas/public/"
            if expected_owner == "AUTO"
            else "CodexSkills/governance/schemas/"
        )
        if not entry["relative_path"].startswith(expected_prefix):
            raise ContractError(f"TRUST_SCHEMA_PATH_OWNER_MISMATCH:{schema_id}")
        document = parse_json_bytes(_git_blob(repo_root, object_id, entry["relative_path"]))
        if not isinstance(document, dict):
            raise ContractError(f"TRUST_SCHEMA_ROOT_INVALID:{schema_id}")
        if document.get("$id") != schema_id or entry["schema_version"] != schema_id:
            raise ContractError(f"TRUST_SCHEMA_BINDING_MISMATCH:{schema_id}")
        if hashlib.sha256(canonicalize_object(document)).hexdigest() != entry["schema_sha256"]:
            raise ContractError(f"TRUST_SCHEMA_DIGEST_MISMATCH:{schema_id}")
        schemas[schema_id] = document
        pointers[schema_id] = entry["self_digest_pointer"]
    registry, checker = build_registry(schemas)
    policies: Dict[str, Any] = {}
    bundle = ContractBundle(schemas, registry, checker, pointers, policies, PROTOCOL)
    if MANIFEST_SCHEMA_ID not in schemas:
        raise ContractError("TRUST_MANIFEST_SCHEMA_NOT_IN_BUNDLE")
    validate_instance(
        bundle,
        manifest,
        MANIFEST_SCHEMA_ID,
        expected_bundle_digest=trust.expected_bundle_digest,
    )
    for entry in policy_entries:
        if entry["owner_plane"] != "MECHANISM":
            raise ContractError(f"TRUST_POLICY_OWNER_MISMATCH:{entry['id']}")
        if not entry["relative_path"].startswith("CodexSkills/governance/policies/"):
            raise ContractError(f"TRUST_POLICY_PATH_OWNER_MISMATCH:{entry['id']}")
        policy = parse_json_bytes(_git_blob(repo_root, object_id, entry["relative_path"]))
        if not isinstance(policy, dict):
            raise ContractError(f"TRUST_POLICY_ROOT_INVALID:{entry['id']}")
        if policy.get("policy_id") != entry["id"] or policy.get("schema_version") != entry["schema_id"]:
            raise ContractError(f"TRUST_POLICY_BINDING_MISMATCH:{entry['id']}")
        if hashlib.sha256(canonicalize_object(policy)).hexdigest() != entry["policy_sha256"]:
            raise ContractError(f"TRUST_POLICY_DIGEST_MISMATCH:{entry['id']}")
        validate_instance(bundle, policy, entry["schema_id"], verify_digest=False)
        policies[entry["id"]] = policy
    final_bundle = ContractBundle(schemas, registry, checker, pointers, policies, PROTOCOL)
    vector_path = "CodexSkills/governance/test_vectors/canonicalization-v1.json"
    vectors = parse_json_bytes(_git_blob(repo_root, object_id, vector_path))
    if hashlib.sha256(canonicalize_object(vectors)).hexdigest() != manifest["test_vectors_digest"]:
        raise ContractError("TRUST_TEST_VECTOR_DIGEST_MISMATCH")
    scan_public_value(manifest, policies)
    return final_bundle


def _main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("capability")
    commands.add_parser("lint-draft")
    lint_set = commands.add_parser("lint-schema-set")
    lint_set.add_argument("--schema-dir", type=Path, action="append", required=True)
    validate = commands.add_parser("validate")
    validate.add_argument("--instance", type=Path, required=True)
    validate.add_argument("--schema-id", required=True)
    validate.add_argument("--expected-bundle-digest")
    validate.add_argument("--public", action="store_true")
    scan = commands.add_parser("scan-public")
    scan.add_argument("--instance", type=Path, required=True)
    trusted = commands.add_parser("trust-bundle")
    trusted.add_argument("--repo-root", type=Path, required=True)
    trusted.add_argument("--verified-git-object-id", required=True)
    trusted.add_argument("--expected-bundle-digest", required=True)
    trusted.add_argument("--canonical-manifest-path", required=True)
    trusted.add_argument("--mode", choices=("CANDIDATE", "ACTIVE"), required=True)
    args = parser.parse_args(argv)
    if args.command == "capability":
        print(json.dumps(capability_gate(), sort_keys=True, separators=(",", ":")))
        return 0
    if args.command == "lint-draft":
        bundle = load_draft_contract()
        print(f"MECHANISM_DRAFT_VALID schemas={len(bundle.schemas)} policies={len(bundle.policies)}")
        return 0
    if args.command == "lint-schema-set":
        schemas = load_schema_directories(args.schema_dir)
        build_registry(schemas)
        print(f"SCHEMA_SET_VALID schemas={len(schemas)}")
        return 0
    if args.command == "validate":
        bundle = load_draft_contract()
        validate_instance(
            bundle,
            strict_load(args.instance),
            args.schema_id,
            expected_bundle_digest=args.expected_bundle_digest,
            public=args.public,
        )
        print("ARTIFACT_VALID")
        return 0
    if args.command == "scan-public":
        bundle = load_draft_contract()
        scan_public_value(strict_load(args.instance), bundle.policies)
        print("PUBLIC_VALUE_VALID")
        return 0
    trust = TrustTuple(
        args.verified_git_object_id,
        args.expected_bundle_digest,
        args.canonical_manifest_path,
        args.mode,
    )
    bundle = load_trusted_bundle(args.repo_root, trust)
    print(f"TRUSTED_BUNDLE_VALID schemas={len(bundle.schemas)} policies={len(bundle.policies)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(_main())
    except (ContractError, CanonicalizationError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
