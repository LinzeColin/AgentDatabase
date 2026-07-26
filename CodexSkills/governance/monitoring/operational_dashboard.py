"""Pure M-067 operational dashboard and actionable-alert projection.

The projection consumes four immutable, self-digested Mechanism readiness
objects plus their externally pinned evidence links.  It derives the health,
privacy, freshness, retention, and capacity views; callers cannot supply view
status, alert severity, owner, action, or evidence links.

The module has no clock, filesystem, Git, network, notification, state,
publisher, renderer, or activation capability.
"""

from __future__ import annotations

import copy
import re
from typing import Any, Dict, Mapping, Sequence, Tuple

from CodexSkills.governance.tools.canonical_json import canonical_digest


SCHEMA_PREFIX = "urn:linzecolin:agentdatabase:skillops:schema:"
PROTOCOL_REVISION = (
    "urn:linzecolin:agentdatabase:skillops:protocol:cross-pack:v1"
)
ALERT_SCHEMA_ID = SCHEMA_PREFIX + "actionable-operational-alert:v1"
DASHBOARD_SCHEMA_ID = SCHEMA_PREFIX + "operational-dashboard:v1"
SELF_POINTER = "/artifact_digest"
CANDIDATE_BUNDLE_DIGEST = (
    "36f0c66dd54d36365700a13f614a8c9bfa9619fb7c532af77566a858175b835e"
)

SOURCE_CODES = ("CAPACITY", "FRESHNESS", "MANAGED_RAW", "ACTIVE_TREE")
VIEW_CODES = ("HEALTH", "PRIVACY", "FRESHNESS", "RETENTION", "CAPACITY")
CATEGORIES = ("PRIVACY", "FRESHNESS", "RETENTION", "CAPACITY")
SEVERITIES = ("INFO", "WARNING", "CRITICAL")
OWNERS = ("AUTO", "MECHANISM")
ACTIONS = (
    "BIND_ACTIVE_TREE_EXECUTOR_AND_VALIDATE_LEDGER",
    "BIND_MANAGED_RAW_EXECUTOR_AND_CERTIFY_RUNTIME",
    "CAPTURE_REAL_COLD_WARM_CAPACITY_BASELINES",
    "DISABLE_PERSISTENT_MANAGED_RAW_DEFAULT",
    "REGISTER_EVALUATED_VERSION_AND_RUN_FRESHNESS_MONITOR",
)
VIEW_STATES = ("OK", "WARNING", "CRITICAL")

SOURCE_SCHEMA_IDS = {
    "FRESHNESS": (
        SCHEMA_PREFIX + "freshness-drift-readiness:v1"
    ),
    "MANAGED_RAW": (
        SCHEMA_PREFIX + "managed-raw-72h-readiness:v1"
    ),
    "ACTIVE_TREE": (
        SCHEMA_PREFIX + "git-active-tree-365d-readiness:v1"
    ),
    "CAPACITY": (
        SCHEMA_PREFIX + "performance-capacity-readiness:v1"
    ),
}

ALERT_UIDS = {
    "FRESHNESS": "alr_01ARZ3NDEKTSV4RRFFQ69G5FA1",
    "PRIVACY": "alr_01ARZ3NDEKTSV4RRFFQ69G5FA2",
    "RETENTION": "alr_01ARZ3NDEKTSV4RRFFQ69G5FA3",
    "CAPACITY": "alr_01ARZ3NDEKTSV4RRFFQ69G5FA4",
}

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GIT_OBJECT_RE = re.compile(r"^sha1:[0-9a-f]{40}$")
UID_RE = re.compile(r"^[a-z][a-z0-9]{1,11}_[0-7][0-9A-HJKMNP-TV-Z]{25}$")
REPO_PATH_RE = re.compile(r"^[A-Za-z0-9._/-]+$")

SOURCE_FIELDS = (
    "evidence_code",
    "verified_git_object_id",
    "canonical_path",
    "content_digest",
    "artifact_digest",
    "status",
)
ALERT_FIELDS = (
    "schema_version",
    "alert_uid",
    "category",
    "severity",
    "owner",
    "action_code",
    "evidence_link_codes",
    "blocking",
    "artifact_digest",
)
VIEW_FIELDS = (
    "view_code",
    "status",
    "fact_codes",
    "alert_uids",
    "evidence_link_codes",
)
DASHBOARD_FIELDS = (
    "schema_version",
    "protocol_revision",
    "bundle_digest",
    "dashboard_uid",
    "owner_plane",
    "status",
    "source_evidence",
    "views",
    "alerts",
    "summary",
    "artifact_digest",
)


class OperationalDashboardError(ValueError):
    """One dashboard source, owner/action, or evidence-link gate failed."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _fail(code: str) -> None:
    raise OperationalDashboardError(code)


def _exact_fields(
    value: Mapping[str, Any],
    fields: Sequence[str],
    code: str,
) -> None:
    if set(value) != set(fields):
        _fail(code)


def _digest(value: Any, code: str) -> str:
    if not isinstance(value, str) or SHA256_RE.fullmatch(value) is None:
        _fail(code)
    return value


def _validate_source_document(
    code: str,
    value: Mapping[str, Any],
) -> None:
    if code not in SOURCE_CODES or not isinstance(value, dict):
        _fail("DASHBOARD_SOURCE_DOCUMENT_INVALID:" + code)
    if value.get("schema_version") != SOURCE_SCHEMA_IDS[code]:
        _fail("DASHBOARD_SOURCE_SCHEMA_INVALID:" + code)
    digest = _digest(
        value.get("artifact_digest"),
        "DASHBOARD_SOURCE_DIGEST_INVALID:" + code,
    )
    if digest != canonical_digest(value, SELF_POINTER):
        _fail("DASHBOARD_SOURCE_SELF_DIGEST_MISMATCH:" + code)
    if value.get("owner_plane") != "MECHANISM":
        _fail("DASHBOARD_SOURCE_OWNER_INVALID:" + code)
    if not isinstance(value.get("status"), str):
        _fail("DASHBOARD_SOURCE_STATUS_INVALID:" + code)


def _validate_evidence(
    source_documents: Mapping[str, Mapping[str, Any]],
    evidence_links: Sequence[Mapping[str, Any]],
) -> Tuple[Mapping[str, Any], ...]:
    if set(source_documents) != set(SOURCE_CODES):
        _fail("DASHBOARD_SOURCE_SET_INCOMPLETE")
    for code in SOURCE_CODES:
        _validate_source_document(code, source_documents[code])
    if not isinstance(evidence_links, (list, tuple)):
        _fail("DASHBOARD_EVIDENCE_LINKS_INVALID")
    ordered = tuple(copy.deepcopy(list(evidence_links)))
    if [item.get("evidence_code") for item in ordered] != list(SOURCE_CODES):
        _fail("DASHBOARD_EVIDENCE_ORDER_OR_SET_INVALID")
    for link in ordered:
        if not isinstance(link, dict):
            _fail("DASHBOARD_EVIDENCE_LINK_INVALID")
        _exact_fields(
            link,
            SOURCE_FIELDS,
            "DASHBOARD_EVIDENCE_FIELDS_INVALID",
        )
        code = link["evidence_code"]
        if (
            not isinstance(link["verified_git_object_id"], str)
            or GIT_OBJECT_RE.fullmatch(
                link["verified_git_object_id"]
            )
            is None
        ):
            _fail("DASHBOARD_EVIDENCE_GIT_OBJECT_INVALID:" + code)
        path = link["canonical_path"]
        if (
            not isinstance(path, str)
            or REPO_PATH_RE.fullmatch(path) is None
            or path.startswith("/")
            or ".." in path.split("/")
        ):
            _fail("DASHBOARD_EVIDENCE_PATH_INVALID:" + code)
        _digest(
            link["content_digest"],
            "DASHBOARD_EVIDENCE_CONTENT_DIGEST_INVALID:" + code,
        )
        _digest(
            link["artifact_digest"],
            "DASHBOARD_EVIDENCE_ARTIFACT_DIGEST_INVALID:" + code,
        )
        source = source_documents[code]
        if (
            link["artifact_digest"] != source["artifact_digest"]
            or link["status"] != source["status"]
        ):
            _fail("DASHBOARD_EVIDENCE_SOURCE_MISMATCH:" + code)
    return ordered


def _alert(
    category: str,
    severity: str,
    owner: str,
    action_code: str,
    evidence_codes: Sequence[str],
) -> Mapping[str, Any]:
    if (
        category not in CATEGORIES
        or severity not in SEVERITIES
        or owner not in OWNERS
        or action_code not in ACTIONS
    ):
        _fail("DASHBOARD_ALERT_ENUM_INVALID")
    if not evidence_codes or any(
        code not in SOURCE_CODES for code in evidence_codes
    ):
        _fail("DASHBOARD_ALERT_EVIDENCE_MISSING")
    value: Dict[str, Any] = {
        "schema_version": ALERT_SCHEMA_ID,
        "alert_uid": ALERT_UIDS[category],
        "category": category,
        "severity": severity,
        "owner": owner,
        "action_code": action_code,
        "evidence_link_codes": sorted(set(evidence_codes)),
        "blocking": severity == "CRITICAL",
        "artifact_digest": "0" * 64,
    }
    value["artifact_digest"] = canonical_digest(value, SELF_POINTER)
    return value


def _derive_alerts(
    sources: Mapping[str, Mapping[str, Any]],
) -> Tuple[Mapping[str, Any], ...]:
    alerts = []
    freshness = sources["FRESHNESS"]
    if not (
        freshness.get("nonmutation", {}).get(
            "monitor_execution_permitted"
        )
        is True
        and freshness.get("registry_observation", {}).get(
            "real_monitor_execution_permitted"
        )
        is True
    ):
        alerts.append(
            _alert(
                "FRESHNESS",
                "WARNING",
                "MECHANISM",
                "REGISTER_EVALUATED_VERSION_AND_RUN_FRESHNESS_MONITOR",
                ("FRESHNESS",),
            )
        )

    managed_raw = sources["MANAGED_RAW"].get(
        "managed_raw_policy_contract",
        {},
    )
    if managed_raw.get("persistent_managed_raw_default_enabled") is True:
        alerts.append(
            _alert(
                "PRIVACY",
                "CRITICAL",
                "MECHANISM",
                "DISABLE_PERSISTENT_MANAGED_RAW_DEFAULT",
                ("MANAGED_RAW",),
            )
        )
    elif not (
        managed_raw.get("production_certification_status") == "GRANTED"
        and managed_raw.get("real_execution_permitted") is True
    ):
        alerts.append(
            _alert(
                "PRIVACY",
                "CRITICAL",
                "AUTO",
                "BIND_MANAGED_RAW_EXECUTOR_AND_CERTIFY_RUNTIME",
                ("MANAGED_RAW",),
            )
        )

    active_tree = sources["ACTIVE_TREE"].get("active_tree_contract", {})
    if not (
        active_tree.get("auto_executor_integration_status") == "BOUND"
        and active_tree.get("real_execution_permitted") is True
    ):
        alerts.append(
            _alert(
                "RETENTION",
                "CRITICAL",
                "AUTO",
                "BIND_ACTIVE_TREE_EXECUTOR_AND_VALIDATE_LEDGER",
                ("ACTIVE_TREE",),
            )
        )

    capacity = sources["CAPACITY"].get("calibration_state", {})
    if not (
        capacity.get("state") == "CALIBRATED"
        and capacity.get("production_sla_proven") is True
        and isinstance(capacity.get("real_profile_count"), int)
        and not isinstance(capacity.get("real_profile_count"), bool)
        and capacity["real_profile_count"] > 0
        and capacity.get("cold_cache_baseline_verified") is True
        and capacity.get("warm_cache_baseline_verified") is True
    ):
        alerts.append(
            _alert(
                "CAPACITY",
                "WARNING",
                "MECHANISM",
                "CAPTURE_REAL_COLD_WARM_CAPACITY_BASELINES",
                ("CAPACITY",),
            )
        )
    return tuple(sorted(alerts, key=lambda item: item["alert_uid"]))


def _view_status(alerts: Sequence[Mapping[str, Any]]) -> str:
    severities = {alert["severity"] for alert in alerts}
    if "CRITICAL" in severities:
        return "CRITICAL"
    if "WARNING" in severities:
        return "WARNING"
    return "OK"


def build_dashboard(
    source_documents: Mapping[str, Mapping[str, Any]],
    evidence_links: Sequence[Mapping[str, Any]],
) -> Mapping[str, Any]:
    """Derive all views and alerts from immutable source evidence."""

    sources = copy.deepcopy(dict(source_documents))
    evidence = _validate_evidence(sources, evidence_links)
    alerts = _derive_alerts(sources)
    by_category = {
        code: [
            alert for alert in alerts if alert["category"] == code
        ]
        for code in CATEGORIES
    }
    views = [
        {
            "view_code": "HEALTH",
            "status": _view_status(alerts),
            "fact_codes": [
                "SOURCE_EVIDENCE_CLOSURE_COMPLETE",
                (
                    "OPERATIONAL_ALERTS_PRESENT"
                    if alerts
                    else "NO_OPERATIONAL_ALERTS"
                ),
            ],
            "alert_uids": [alert["alert_uid"] for alert in alerts],
            "evidence_link_codes": list(SOURCE_CODES),
        },
    ]
    view_facts = {
        "PRIVACY": [
            (
                "PERSISTENT_MANAGED_RAW_DEFAULT_DISABLED"
                if sources["MANAGED_RAW"][
                    "managed_raw_policy_contract"
                ]["persistent_managed_raw_default_enabled"]
                is False
                else "PERSISTENT_MANAGED_RAW_DEFAULT_ENABLED"
            ),
            (
                "MANAGED_RAW_RUNTIME_CERTIFIED"
                if not by_category["PRIVACY"]
                else "MANAGED_RAW_RUNTIME_NOT_CERTIFIED"
            ),
        ],
        "FRESHNESS": [
            (
                "FRESHNESS_MONITOR_EXECUTION_READY"
                if not by_category["FRESHNESS"]
                else "FRESHNESS_MONITOR_EXECUTION_NOT_READY"
            )
        ],
        "RETENTION": [
            (
                "ACTIVE_TREE_EXECUTOR_BOUND"
                if not by_category["RETENTION"]
                else "ACTIVE_TREE_EXECUTOR_NOT_BOUND"
            )
        ],
        "CAPACITY": [
            (
                "CAPACITY_BASELINE_CALIBRATED"
                if not by_category["CAPACITY"]
                else "CAPACITY_BASELINE_UNCALIBRATED"
            ),
            "SILENT_SAMPLING_FORBIDDEN",
        ],
    }
    evidence_by_view = {
        "PRIVACY": ["MANAGED_RAW"],
        "FRESHNESS": ["FRESHNESS"],
        "RETENTION": ["ACTIVE_TREE"],
        "CAPACITY": ["CAPACITY"],
    }
    for code in ("PRIVACY", "FRESHNESS", "RETENTION", "CAPACITY"):
        views.append(
            {
                "view_code": code,
                "status": _view_status(by_category[code]),
                "fact_codes": view_facts[code],
                "alert_uids": [
                    alert["alert_uid"] for alert in by_category[code]
                ],
                "evidence_link_codes": evidence_by_view[code],
            }
        )
    critical_count = sum(
        alert["severity"] == "CRITICAL" for alert in alerts
    )
    warning_count = sum(
        alert["severity"] == "WARNING" for alert in alerts
    )
    value: Dict[str, Any] = {
        "schema_version": DASHBOARD_SCHEMA_ID,
        "protocol_revision": PROTOCOL_REVISION,
        "bundle_digest": CANDIDATE_BUNDLE_DIGEST,
        "dashboard_uid": "dsh_01ARZ3NDEKTSV4RRFFQ69G5FAV",
        "owner_plane": "MECHANISM",
        "status": (
            "DRAFT_NON_ACTIVE_ALERTS_PRESENT"
            if alerts
            else "DRAFT_NON_ACTIVE_NO_ALERTS"
        ),
        "source_evidence": list(evidence),
        "views": views,
        "alerts": list(alerts),
        "summary": {
            "view_count": len(views),
            "alert_count": len(alerts),
            "critical_count": critical_count,
            "warning_count": warning_count,
            "info_count": len(alerts) - critical_count - warning_count,
            "production_dashboard_ready": False,
            "notification_sent": False,
        },
        "artifact_digest": "0" * 64,
    }
    value["artifact_digest"] = canonical_digest(value, SELF_POINTER)
    return value


def validate_dashboard(
    value: Mapping[str, Any],
    source_documents: Mapping[str, Mapping[str, Any]],
    evidence_links: Sequence[Mapping[str, Any]],
) -> None:
    """Reject self-consistent caller changes to alert ownership or action."""

    if not isinstance(value, dict):
        _fail("DASHBOARD_INVALID")
    _exact_fields(value, DASHBOARD_FIELDS, "DASHBOARD_FIELDS_INVALID")
    if value != build_dashboard(source_documents, evidence_links):
        _fail("DASHBOARD_DERIVATION_MISMATCH")
    if (
        not isinstance(value["dashboard_uid"], str)
        or UID_RE.fullmatch(value["dashboard_uid"]) is None
    ):
        _fail("DASHBOARD_UID_INVALID")
    seen_alerts = set()
    for alert in value["alerts"]:
        _exact_fields(alert, ALERT_FIELDS, "DASHBOARD_ALERT_FIELDS_INVALID")
        if (
            not isinstance(alert["alert_uid"], str)
            or UID_RE.fullmatch(alert["alert_uid"]) is None
            or alert["alert_uid"] in seen_alerts
        ):
            _fail("DASHBOARD_ALERT_UID_INVALID")
        seen_alerts.add(alert["alert_uid"])
        if alert["artifact_digest"] != canonical_digest(
            alert,
            SELF_POINTER,
        ):
            _fail("DASHBOARD_ALERT_DIGEST_MISMATCH")
        if not alert["owner"] or not alert["action_code"]:
            _fail("DASHBOARD_ALERT_OWNER_ACTION_MISSING")
        if not alert["evidence_link_codes"]:
            _fail("DASHBOARD_ALERT_EVIDENCE_MISSING")
    for view in value["views"]:
        _exact_fields(view, VIEW_FIELDS, "DASHBOARD_VIEW_FIELDS_INVALID")
        if (
            view["view_code"] not in VIEW_CODES
            or view["status"] not in VIEW_STATES
            or not view["evidence_link_codes"]
        ):
            _fail("DASHBOARD_VIEW_INVALID")
    if value["artifact_digest"] != canonical_digest(value, SELF_POINTER):
        _fail("DASHBOARD_DIGEST_MISMATCH")


__all__ = [
    "ACTIONS",
    "ALERT_SCHEMA_ID",
    "CANDIDATE_BUNDLE_DIGEST",
    "DASHBOARD_SCHEMA_ID",
    "OperationalDashboardError",
    "PROTOCOL_REVISION",
    "SELF_POINTER",
    "SOURCE_CODES",
    "SOURCE_SCHEMA_IDS",
    "VIEW_CODES",
    "build_dashboard",
    "validate_dashboard",
]
