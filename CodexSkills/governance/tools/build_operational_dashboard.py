#!/usr/bin/env python3
"""Build/check non-active Mechanism M-067 operational dashboard evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from CodexSkills.governance.monitoring.operational_dashboard import (  # noqa: E402
    ACTIONS,
    ALERT_SCHEMA_ID,
    CANDIDATE_BUNDLE_DIGEST,
    DASHBOARD_SCHEMA_ID,
    PROTOCOL_REVISION,
    SELF_POINTER,
    SOURCE_CODES,
    VIEW_CODES,
    build_dashboard,
    validate_dashboard,
)
from CodexSkills.governance.tools import (  # noqa: E402
    build_performance_capacity_budgets as performance_builder,
)
from CodexSkills.governance.tools.canonical_json import (  # noqa: E402
    canonical_digest,
    parse_json_bytes,
)
from CodexSkills.governance.tools.validate_au040_semantic_acceptance import (  # noqa: E402
    load_au040_acceptance,
)
from CodexSkills.governance.tools.validate_mechanism import (  # noqa: E402
    ContractBundle,
    ContractError,
    build_registry,
    scan_public_value,
    validate_instance,
)


GOVERNANCE_DIR = REPO_ROOT / "CodexSkills" / "governance"
MONITORING_DIR = GOVERNANCE_DIR / "monitoring"
SCHEMA_DIR = MONITORING_DIR / "schemas"
COMPONENT_PATH = MONITORING_DIR / "operational_dashboard.py"
DASHBOARD_PATH = MONITORING_DIR / "operational-dashboard.json"
MARKDOWN_PATH = MONITORING_DIR / "OPERATIONAL_DASHBOARD.md"
READINESS_PATH = MONITORING_DIR / "operational-dashboard-readiness.json"
ALERT_SCHEMA_PATH = (
    SCHEMA_DIR / "actionable-operational-alert.schema.json"
)
DASHBOARD_SCHEMA_PATH = (
    SCHEMA_DIR / "operational-dashboard.schema.json"
)
READINESS_SCHEMA_PATH = (
    SCHEMA_DIR / "operational-dashboard-readiness.schema.json"
)
VERSION_PATH = REPO_ROOT / "CodexSkills" / "VERSION"

READINESS_SCHEMA_ID = (
    "urn:linzecolin:agentdatabase:skillops:"
    "schema:operational-dashboard-readiness:v1"
)
NEXT_PHASE = "MECHANISM_THREE_REPRESENTATIVE_PILOTS"
CANDIDATE_GIT_OBJECT = (
    "sha1:5ee37d7499c62ec19381dac7eb95cb12743ad2d5"
)
CANDIDATE_MANIFEST_PATH = (
    "CodexSkills/governance/bundles/schema-bundle-manifest.v1.json"
)
CANDIDATE_MANIFEST_RAW_SHA256 = (
    "66ad125629cab71739ff2bc266219f995f7a45998936ca720c6db678ee77e65a"
)

SOURCE_CONTRACTS = {
    "CAPACITY": {
        "verified_git_object_id": (
            "sha1:9968a706dd729839efa707bf64ef893c44d324bd"
        ),
        "canonical_path": (
            "CodexSkills/governance/performance/"
            "performance-capacity-readiness.json"
        ),
        "content_digest": (
            "000154c32d895b35960cadbad80582c09121ee1103a31a63577ad8a6cf5b1a3d"
        ),
        "artifact_digest": (
            "9cd49a73c30729de3b0443e6a8024035cdc138a8e2d690f720def0d4400b881e"
        ),
        "status": (
            "DRAFT_NON_ACTIVE_PERFORMANCE_CAPACITY_BUDGETS_"
            "IMPLEMENTED_UNCALIBRATED"
        ),
    },
    "FRESHNESS": {
        "verified_git_object_id": (
            "sha1:3d3c202ee629d79eadfb027da131e1afcb88a1f2"
        ),
        "canonical_path": (
            "CodexSkills/governance/monitoring/"
            "freshness-drift-readiness.json"
        ),
        "content_digest": (
            "416beacd6a72d3d5517211a3758452228bd445ab10fc887928b0575e2865d812"
        ),
        "artifact_digest": (
            "8864203d59f925f8f3110ff1e779ebdb19d26818a337de764596de2de1afa96d"
        ),
        "status": "DRAFT_NON_ACTIVE_FRESHNESS_DRIFT_MONITOR_READY",
    },
    "MANAGED_RAW": {
        "verified_git_object_id": (
            "sha1:b023ac71c5c7852a95f4b87a56981fe7a42c32d9"
        ),
        "canonical_path": (
            "CodexSkills/governance/retention/"
            "managed-raw-72h-readiness.json"
        ),
        "content_digest": (
            "d60a71554ffbe4bde30fbd639e723086598df22b69b4ceee04b070dd4ddb6e0f"
        ),
        "artifact_digest": (
            "dad952d9df1523bb63765dc028a4f3609251834dcb52dfa06a085341f555f774"
        ),
        "status": "DRAFT_NON_ACTIVE_MANAGED_RAW_72H_POLICY_READY",
    },
    "ACTIVE_TREE": {
        "verified_git_object_id": (
            "sha1:039f3844b36961f1d8432b9c0d86d6cda408f430"
        ),
        "canonical_path": (
            "CodexSkills/governance/retention/"
            "git-active-tree-365d-readiness.json"
        ),
        "content_digest": (
            "91592f339854fb205993e96a67698d7b6ce8fc54afd3b226f3090dfd49ab86f2"
        ),
        "artifact_digest": (
            "0bb6c1fb335115785495805ed001d6747a311dd1cbee335547beccaf8501df88"
        ),
        "status": "DRAFT_NON_ACTIVE_GIT_ACTIVE_TREE_365D_READY",
    },
}

REF = (
    "urn:linzecolin:agentdatabase:skillops:"
    "schema:common-definitions:v1#/$defs/"
)


class OperationalDashboardBuildError(ValueError):
    """M-067 evidence cannot be rebuilt without weakening a gate."""


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _render(value: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _load(raw: bytes, code: str) -> Mapping[str, Any]:
    try:
        value = parse_json_bytes(raw)
    except Exception as exc:
        raise OperationalDashboardBuildError(code) from exc
    if not isinstance(value, dict):
        raise OperationalDashboardBuildError(code)
    return value


def _git_blob(tagged_object: str, relative_path: str) -> bytes:
    if tagged_object.count(":") != 1:
        raise OperationalDashboardBuildError(
            "M067_GIT_OBJECT_INVALID"
        )
    algorithm, object_id = tagged_object.split(":", 1)
    if algorithm != "sha1" or len(object_id) != 40:
        raise OperationalDashboardBuildError(
            "M067_GIT_OBJECT_INVALID"
        )
    process = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "show", object_id + ":" + relative_path],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=20,
        check=False,
    )
    if process.returncode != 0:
        raise OperationalDashboardBuildError(
            "M067_GIT_BLOB_UNAVAILABLE:" + relative_path
        )
    return process.stdout


def _current(relative_path: str) -> bytes:
    path = REPO_ROOT.joinpath(*relative_path.split("/"))
    if not path.is_file() or path.is_symlink():
        raise OperationalDashboardBuildError(
            "M067_CURRENT_FILE_INVALID:" + relative_path
        )
    return path.read_bytes()


def _source_documents() -> Tuple[
    Mapping[str, Mapping[str, Any]],
    Sequence[Mapping[str, Any]],
]:
    documents = {}
    links = []
    for code in SOURCE_CODES:
        contract = SOURCE_CONTRACTS[code]
        raw = _git_blob(
            contract["verified_git_object_id"],
            contract["canonical_path"],
        )
        if (
            _sha256(raw) != contract["content_digest"]
            or _current(contract["canonical_path"]) != raw
        ):
            raise OperationalDashboardBuildError(
                "M067_SOURCE_RAW_DRIFT:" + code
            )
        value = _load(raw, "M067_SOURCE_JSON_INVALID:" + code)
        if (
            value.get("artifact_digest") != contract["artifact_digest"]
            or value.get("artifact_digest")
            != canonical_digest(value, "/artifact_digest")
            or value.get("status") != contract["status"]
        ):
            raise OperationalDashboardBuildError(
                "M067_SOURCE_CONTRACT_INVALID:" + code
            )
        documents[code] = value
        links.append({"evidence_code": code, **contract})
    return documents, links


def _ref(name: str) -> Mapping[str, str]:
    return {"$ref": REF + name}


def _closed(
    properties: Mapping[str, Any],
    required: Optional[Sequence[str]] = None,
) -> Mapping[str, Any]:
    return {
        "additionalProperties": False,
        "properties": dict(properties),
        "required": list(properties if required is None else required),
        "type": "object",
    }


def build_alert_schema() -> Mapping[str, Any]:
    return {
        "$id": ALERT_SCHEMA_ID,
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        **_closed(
            {
                "schema_version": {"const": ALERT_SCHEMA_ID},
                "alert_uid": _ref("typed_uid"),
                "category": {
                    "enum": [
                        "PRIVACY",
                        "FRESHNESS",
                        "RETENTION",
                        "CAPACITY",
                    ]
                },
                "severity": {
                    "enum": ["INFO", "WARNING", "CRITICAL"]
                },
                "owner": {"enum": ["AUTO", "MECHANISM"]},
                "action_code": {"enum": list(ACTIONS)},
                "evidence_link_codes": {
                    "items": {"enum": list(SOURCE_CODES)},
                    "minItems": 1,
                    "type": "array",
                    "uniqueItems": True,
                },
                "blocking": {"type": "boolean"},
                "artifact_digest": _ref("sha256"),
            }
        ),
        "title": "Mechanism M-067 actionable operational alert",
    }


def build_dashboard_schema() -> Mapping[str, Any]:
    source = _closed(
        {
            "evidence_code": {"enum": list(SOURCE_CODES)},
            "verified_git_object_id": _ref("git_object_id"),
            "canonical_path": _ref("repo_relative_posix_path"),
            "content_digest": _ref("sha256"),
            "artifact_digest": _ref("sha256"),
            "status": _ref("enum_code"),
        }
    )
    view = _closed(
        {
            "view_code": {"enum": list(VIEW_CODES)},
            "status": {"enum": ["OK", "WARNING", "CRITICAL"]},
            "fact_codes": {
                "items": _ref("enum_code"),
                "minItems": 1,
                "type": "array",
                "uniqueItems": True,
            },
            "alert_uids": {
                "items": _ref("typed_uid"),
                "type": "array",
                "uniqueItems": True,
            },
            "evidence_link_codes": {
                "items": {"enum": list(SOURCE_CODES)},
                "minItems": 1,
                "type": "array",
                "uniqueItems": True,
            },
        }
    )
    summary = _closed(
        {
            "view_count": _ref("nonnegative_count"),
            "alert_count": _ref("nonnegative_count"),
            "critical_count": _ref("nonnegative_count"),
            "warning_count": _ref("nonnegative_count"),
            "info_count": _ref("nonnegative_count"),
            "production_dashboard_ready": {"type": "boolean"},
            "notification_sent": {"type": "boolean"},
        }
    )
    return {
        "$id": DASHBOARD_SCHEMA_ID,
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        **_closed(
            {
                "schema_version": {"const": DASHBOARD_SCHEMA_ID},
                "protocol_revision": {"const": PROTOCOL_REVISION},
                "bundle_digest": {"const": CANDIDATE_BUNDLE_DIGEST},
                "dashboard_uid": _ref("typed_uid"),
                "owner_plane": {"const": "MECHANISM"},
                "status": {
                    "enum": [
                        "DRAFT_NON_ACTIVE_ALERTS_PRESENT",
                        "DRAFT_NON_ACTIVE_NO_ALERTS",
                    ]
                },
                "source_evidence": {
                    "items": source,
                    "maxItems": 4,
                    "minItems": 4,
                    "type": "array",
                },
                "views": {
                    "items": view,
                    "maxItems": 5,
                    "minItems": 5,
                    "type": "array",
                },
                "alerts": {
                    "items": {"$ref": ALERT_SCHEMA_ID},
                    "maxItems": 4,
                    "type": "array",
                },
                "summary": summary,
                "artifact_digest": _ref("sha256"),
            }
        ),
        "title": "Mechanism M-067 operational dashboard",
    }


def _extend_bundle(
    base: ContractBundle,
    additions: Mapping[str, Mapping[str, Any]],
    pointers: Mapping[str, str],
) -> ContractBundle:
    schemas = dict(base.schemas)
    self_pointers = dict(base.self_digest_pointers)
    for schema_id, schema in additions.items():
        if schema_id in schemas:
            raise OperationalDashboardBuildError(
                "M067_SCHEMA_REBIND_FORBIDDEN:" + schema_id
            )
        schemas[schema_id] = schema
        self_pointers[schema_id] = pointers[schema_id]
    try:
        registry, checker = build_registry(schemas)
    except ContractError as exc:
        raise OperationalDashboardBuildError(
            "M067_SCHEMA_CLOSURE_INVALID:" + str(exc)
        ) from exc
    return ContractBundle(
        schemas=schemas,
        registry=registry,
        format_checker=checker,
        self_digest_pointers=self_pointers,
        policies=base.policies,
        protocol_revision=base.protocol_revision,
    )


def _candidate_plus_performance() -> ContractBundle:
    acceptance = load_au040_acceptance()
    documents = performance_builder._documents()
    additions = {
        performance_builder.PROFILE_SCHEMA_ID: _load(
            documents[performance_builder.PROFILE_SCHEMA_PATH],
            "M067_M066_PROFILE_SCHEMA_INVALID",
        ),
        performance_builder.BUDGET_SCHEMA_ID: _load(
            documents[performance_builder.BUDGET_SCHEMA_PATH],
            "M067_M066_BUDGET_SCHEMA_INVALID",
        ),
        performance_builder.READINESS_SCHEMA_ID: _load(
            documents[performance_builder.READINESS_SCHEMA_PATH],
            "M067_M066_READINESS_SCHEMA_INVALID",
        ),
    }
    for path in (
        performance_builder.PROFILE_SCHEMA_PATH,
        performance_builder.BUDGET_SCHEMA_PATH,
        performance_builder.READINESS_SCHEMA_PATH,
    ):
        if path.read_bytes() != documents[path]:
            raise OperationalDashboardBuildError(
                "M067_M066_GENERATED_BYTE_DRIFT:" + str(path)
            )
    return _extend_bundle(
        acceptance.bundle,
        additions,
        {
            performance_builder.PROFILE_SCHEMA_ID: (
                performance_builder.PROFILE_SELF_POINTER
            ),
            performance_builder.BUDGET_SCHEMA_ID: (
                performance_builder.BUDGET_SELF_POINTER
            ),
            performance_builder.READINESS_SCHEMA_ID: "/artifact_digest",
        },
    )


def _descriptor(
    schema_id: str,
    path: str,
    raw: bytes,
    schema_digest: str,
) -> Mapping[str, Any]:
    return {
        "schema_version": schema_id,
        "canonical_path": path,
        "content_digest": _sha256(raw),
        "schema_sha256": schema_digest,
        "self_digest_pointer": SELF_POINTER,
    }


def render_dashboard_markdown(
    dashboard: Mapping[str, Any],
) -> bytes:
    link_targets = {
        "CAPACITY": (
            "../performance/performance-capacity-readiness.json"
        ),
        "FRESHNESS": "freshness-drift-readiness.json",
        "MANAGED_RAW": (
            "../retention/managed-raw-72h-readiness.json"
        ),
        "ACTIVE_TREE": (
            "../retention/git-active-tree-365d-readiness.json"
        ),
    }
    lines = [
        "# SkillOps operational dashboard",
        "",
        "Status: **" + dashboard["status"] + "**",
        "",
        "This is a deterministic, non-active evidence projection. It is not "
        "live telemetry and does not send notifications.",
        "",
        "## Views",
        "",
        "| View | Status | Evidence |",
        "|---|---|---|",
    ]
    for view in dashboard["views"]:
        links = ", ".join(
            "[" + code + "](" + link_targets[code] + ")"
            for code in view["evidence_link_codes"]
        )
        lines.append(
            "| "
            + view["view_code"]
            + " | "
            + view["status"]
            + " | "
            + links
            + " |"
        )
    lines.extend(
        [
            "",
            "## Actionable alerts",
            "",
            "| Severity | Category | Owner | Action | Evidence |",
            "|---|---|---|---|---|",
        ]
    )
    for alert in dashboard["alerts"]:
        links = ", ".join(
            "[" + code + "](" + link_targets[code] + ")"
            for code in alert["evidence_link_codes"]
        )
        lines.append(
            "| "
            + alert["severity"]
            + " | "
            + alert["category"]
            + " | "
            + alert["owner"]
            + " | `"
            + alert["action_code"]
            + "` | "
            + links
            + " |"
        )
    lines.extend(
        [
            "",
            "Every alert above has an accountable owner, one fixed action "
            "code, and at least one digest-bound evidence link.",
            "",
        ]
    )
    return "\n".join(lines).encode("utf-8")


def _build_readiness(
    dashboard: Mapping[str, Any],
    markdown: bytes,
    alert_schema: Mapping[str, Any],
    dashboard_schema: Mapping[str, Any],
) -> Mapping[str, Any]:
    alert_schema_raw = _render(alert_schema)
    dashboard_schema_raw = _render(dashboard_schema)
    dashboard_raw = _render(dashboard)
    source_trust = {
        "candidate_bundle": {
            "verified_git_object_id": CANDIDATE_GIT_OBJECT,
            "bundle_digest": CANDIDATE_BUNDLE_DIGEST,
            "canonical_path": CANDIDATE_MANIFEST_PATH,
            "artifact_digest": CANDIDATE_MANIFEST_RAW_SHA256,
            "expected_mode": "CANDIDATE",
            "schema_count": 31,
            "policy_count": 5,
        },
        "operational_sources": [
            {"evidence_code": code, **SOURCE_CONTRACTS[code]}
            for code in SOURCE_CODES
        ],
        "repository_self_report_is_not_trust_root": True,
    }
    value: Dict[str, Any] = {
        "schema_version": READINESS_SCHEMA_ID,
        "protocol_revision": PROTOCOL_REVISION,
        "status": (
            "DRAFT_NON_ACTIVE_OPERATIONAL_DASHBOARD_READY_ALERTS_PRESENT"
        ),
        "owner_plane": "MECHANISM",
        "source_trust": source_trust,
        "implementation_contract": {
            "component_path": (
                "CodexSkills/governance/monitoring/"
                "operational_dashboard.py"
            ),
            "content_digest": _sha256(COMPONENT_PATH.read_bytes()),
            "capability_mode": "PURE_IMMUTABLE_OBJECTS_ONLY",
            "alert_schema": _descriptor(
                ALERT_SCHEMA_ID,
                (
                    "CodexSkills/governance/monitoring/schemas/"
                    "actionable-operational-alert.schema.json"
                ),
                alert_schema_raw,
                canonical_digest(alert_schema),
            ),
            "dashboard_schema": _descriptor(
                DASHBOARD_SCHEMA_ID,
                (
                    "CodexSkills/governance/monitoring/schemas/"
                    "operational-dashboard.schema.json"
                ),
                dashboard_schema_raw,
                canonical_digest(dashboard_schema),
            ),
            "dashboard": {
                "canonical_path": (
                    "CodexSkills/governance/monitoring/"
                    "operational-dashboard.json"
                ),
                "content_digest": _sha256(dashboard_raw),
                "artifact_digest": dashboard["artifact_digest"],
            },
            "human_dashboard": {
                "canonical_path": (
                    "CodexSkills/governance/monitoring/"
                    "OPERATIONAL_DASHBOARD.md"
                ),
                "content_digest": _sha256(markdown),
            },
            "views": list(VIEW_CODES),
            "every_alert_owner_required": True,
            "every_alert_action_required": True,
            "every_alert_evidence_link_required": True,
            "caller_alert_fields_accepted": False,
            "live_telemetry_capability_present": False,
            "notification_transport_capability_present": False,
            "state_capability_present": False,
            "publisher_capability_present": False,
        },
        "current_projection": {
            **dashboard["summary"],
            "artifact_digest": dashboard["artifact_digest"],
            "source_evidence_count": len(dashboard["source_evidence"]),
            "freshness_runtime_ready": False,
            "managed_raw_runtime_certified": False,
            "active_tree_executor_bound": False,
            "capacity_calibrated": False,
        },
        "nonmutation": {
            "auto_plane_unchanged": True,
            "openai_database_unchanged": True,
            "candidate_bundle_unchanged": True,
            "real_telemetry_collected": False,
            "notification_sent": False,
            "state_write_permitted": False,
            "canonical_publication_permitted": False,
            "activation_forbidden": True,
            "version_file_created": False,
        },
        "task_contract": {
            "dependency_task_ids": ["M-058", "M-061", "M-063", "M-066"],
            "implemented_task_ids": ["M-067"],
            "pending_task_ids": ["M-068"],
            "required_output_code": (
                "HEALTH_PRIVACY_FRESHNESS_RETENTION_CAPACITY_VIEWS"
            ),
            "done_gate": "EVERY_ALERT_HAS_OWNER_ACTION_EVIDENCE_LINK",
        },
        "schema_closure_count": 37,
        "policy_count": 5,
        "production_dashboard_ready": False,
        "next_phase": NEXT_PHASE,
        "self_digest_pointer": SELF_POINTER,
        "task_pack_revision": "v0.0.0.2",
        "artifact_digest": "0" * 64,
    }
    value["artifact_digest"] = canonical_digest(value, SELF_POINTER)
    return value


def build_readiness_schema(
    readiness: Mapping[str, Any],
) -> Mapping[str, Any]:
    properties = {
        key: {"const": value}
        for key, value in readiness.items()
        if key != "artifact_digest"
    }
    properties["artifact_digest"] = _ref("sha256")
    return {
        "$id": READINESS_SCHEMA_ID,
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        **_closed(properties),
        "title": "Mechanism M-067 operational dashboard readiness",
    }


def _documents() -> Mapping[Path, bytes]:
    sources, links = _source_documents()
    dashboard = build_dashboard(sources, links)
    validate_dashboard(dashboard, sources, links)
    markdown = render_dashboard_markdown(dashboard)
    alert_schema = build_alert_schema()
    dashboard_schema = build_dashboard_schema()
    readiness = _build_readiness(
        dashboard,
        markdown,
        alert_schema,
        dashboard_schema,
    )
    readiness_schema = build_readiness_schema(readiness)

    base = _candidate_plus_performance()
    contract = _extend_bundle(
        base,
        {
            ALERT_SCHEMA_ID: alert_schema,
            DASHBOARD_SCHEMA_ID: dashboard_schema,
            READINESS_SCHEMA_ID: readiness_schema,
        },
        {
            ALERT_SCHEMA_ID: SELF_POINTER,
            DASHBOARD_SCHEMA_ID: SELF_POINTER,
            READINESS_SCHEMA_ID: SELF_POINTER,
        },
    )
    if len(contract.schemas) != 37 or len(contract.policies) != 5:
        raise OperationalDashboardBuildError(
            "M067_SCHEMA_OR_POLICY_COUNT_INVALID"
        )
    validate_instance(
        contract,
        dashboard,
        DASHBOARD_SCHEMA_ID,
        expected_bundle_digest=CANDIDATE_BUNDLE_DIGEST,
        verify_digest=True,
        public=True,
    )
    for alert in dashboard["alerts"]:
        validate_instance(
            contract,
            alert,
            ALERT_SCHEMA_ID,
            expected_bundle_digest=CANDIDATE_BUNDLE_DIGEST,
            verify_digest=True,
            public=True,
        )
    validate_instance(
        contract,
        readiness,
        READINESS_SCHEMA_ID,
        expected_bundle_digest=CANDIDATE_BUNDLE_DIGEST,
        verify_digest=True,
        public=True,
    )
    scan_public_value(dashboard, contract.policies)
    scan_public_value(readiness, contract.policies)
    return {
        ALERT_SCHEMA_PATH: _render(alert_schema),
        DASHBOARD_SCHEMA_PATH: _render(dashboard_schema),
        READINESS_SCHEMA_PATH: _render(readiness_schema),
        DASHBOARD_PATH: _render(dashboard),
        MARKDOWN_PATH: markdown,
        READINESS_PATH: _render(readiness),
    }


def _write() -> None:
    for path, raw in _documents().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)


def _check() -> None:
    for path, expected in _documents().items():
        if not path.is_file() or path.is_symlink():
            raise OperationalDashboardBuildError(
                "M067_GENERATED_FILE_INVALID:" + str(path)
            )
        if path.read_bytes() != expected:
            raise OperationalDashboardBuildError(
                "M067_GENERATED_BYTE_DRIFT:" + str(path)
            )
    if VERSION_PATH.exists():
        raise OperationalDashboardBuildError(
            "M067_VERSION_MUST_REMAIN_ABSENT"
        )


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.write:
            _write()
        else:
            _check()
        dashboard = _load(
            _documents()[DASHBOARD_PATH],
            "M067_DASHBOARD_INVALID",
        )
        print(
            "OPERATIONAL_DASHBOARD_OK "
            "views="
            + str(dashboard["summary"]["view_count"])
            + " alerts="
            + str(dashboard["summary"]["alert_count"])
            + " critical="
            + str(dashboard["summary"]["critical_count"])
            + " every_alert_actionable=true production_ready=false"
        )
        return 0
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
