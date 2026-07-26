"""Pure M-065 read-only migration/cutover contract.

The module validates source completeness, pre/post source immutability,
source-target file/type/digest/link parity, dual-read equivalence, a bounded
command/syscall audit, and a new-commit-only rollback contract.  It accepts
immutable objects only.  It has no filesystem, Git, network, state, lock,
publisher, migration, copy, move, truncate, delete, or activation capability.
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
OBSERVATION_SCHEMA_ID = SCHEMA_PREFIX + "read-only-migration-observation:v1"
PLAN_SCHEMA_ID = SCHEMA_PREFIX + "read-only-cutover-plan:v1"
OBSERVATION_SELF_POINTER = "/evidence_bundle_digest"
PLAN_SELF_POINTER = "/evidence_bundle_digest"
CANDIDATE_BUNDLE_DIGEST = (
    "36f0c66dd54d36365700a13f614a8c9bfa9619fb7c532af77566a858175b835e"
)

SOURCE_CLASSES = ("AGENTS", "CLAUDE", "CODEX", "CODEX_SYSTEM")
SOURCE_STATES = ("COMPLETE", "EMPTY", "ERROR", "MISSING")
QUERY_STATES = ("COMPLETE", "ERROR", "MISSING")
DECISIONS = ("BLOCKED", "CUTOVER_ELIGIBLE")
CUTOVER_MODE = "SHADOW_ONLY"

AUDIT_COUNTER_FIELDS = (
    "protected_delete_count",
    "protected_move_count",
    "protected_truncate_count",
    "protected_write_count",
    "protected_chmod_count",
    "protected_chown_count",
    "target_delete_count",
)
SNAPSHOT_COUNT_FIELDS = (
    "file_count",
    "byte_count",
    "regular_file_count",
    "symlink_count",
)
SNAPSHOT_DIGEST_FIELDS = ("tree_digest", "link_digest")
SNAPSHOT_FIELDS = SNAPSHOT_COUNT_FIELDS + SNAPSHOT_DIGEST_FIELDS

FIXED_ROLLBACK_CONTRACT = {
    "mode": "NEW_COMMIT_ONLY",
    "baseline_git_object_required": True,
    "previous_read_route_retained": True,
    "path_map_retained": True,
    "source_evidence_retained": True,
    "receipt_evidence_retained": True,
    "watermark_state_backup_required": True,
    "local_source_deletion_permitted": False,
    "history_rewrite_permitted": False,
    "rebase_permitted": False,
    "force_push_permitted": False,
}

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GIT_OBJECT_RE = re.compile(r"^(?:sha1:[0-9a-f]{40}|sha256:[0-9a-f]{64})$")
REF_RE = re.compile(r"^[a-z][a-z0-9-]{2,63}$")
UID_RE = re.compile(r"^[a-z][a-z0-9]{1,11}_[0-7][0-9A-HJKMNP-TV-Z]{25}$")


class ReadOnlyCutoverError(ValueError):
    """One M-065 invariant failed closed."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _fail(code: str) -> None:
    raise ReadOnlyCutoverError(code)


def _require_exact_keys(
    value: Any,
    required: Sequence[str],
    code: str,
) -> Mapping[str, Any]:
    if not isinstance(value, dict) or set(value) != set(required):
        _fail(code)
    return value


def _require_nonnegative(value: Any, code: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 0
        or value > 9007199254740991
    ):
        _fail(code)
    return value


def _validate_snapshot(value: Any, code: str) -> Mapping[str, Any]:
    snapshot = _require_exact_keys(value, SNAPSHOT_FIELDS, code)
    for field in SNAPSHOT_COUNT_FIELDS:
        _require_nonnegative(snapshot[field], code + ":" + field)
    for field in SNAPSHOT_DIGEST_FIELDS:
        if (
            not isinstance(snapshot[field], str)
            or SHA256_RE.fullmatch(snapshot[field]) is None
        ):
            _fail(code + ":" + field)
    if snapshot["file_count"] != (
        snapshot["regular_file_count"] + snapshot["symlink_count"]
    ):
        _fail(code + ":COUNT_CLOSURE")
    if snapshot["file_count"] == 0:
        _fail(code + ":EMPTY")
    return snapshot


def _snapshot_equal(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    return all(left[field] == right[field] for field in SNAPSHOT_FIELDS)


def _source_blockers(
    sources: Any,
) -> Tuple[Tuple[Mapping[str, Any], ...], set[str]]:
    if not isinstance(sources, list) or len(sources) != len(SOURCE_CLASSES):
        _fail("MIGRATION_SOURCE_SET_INVALID")
    normalized = []
    blockers: set[str] = set()
    observed_classes = []
    observed_refs = []
    for row in sources:
        if not isinstance(row, dict):
            _fail("MIGRATION_SOURCE_ROW_INVALID")
        required = {"source_class", "source_ref", "state"}
        state = row.get("state")
        if state == "COMPLETE":
            required.update(
                {"pre_snapshot", "post_snapshot", "target_snapshot"}
            )
        else:
            required.add("reason_code")
        if set(row) != required:
            _fail("MIGRATION_SOURCE_ROW_FIELDS_INVALID")
        source_class = row["source_class"]
        if source_class not in SOURCE_CLASSES:
            _fail("MIGRATION_SOURCE_CLASS_INVALID")
        source_ref = row["source_ref"]
        if not isinstance(source_ref, str) or REF_RE.fullmatch(source_ref) is None:
            _fail("MIGRATION_SOURCE_REF_INVALID")
        if state not in SOURCE_STATES:
            _fail("MIGRATION_SOURCE_STATE_INVALID")
        observed_classes.append(source_class)
        observed_refs.append(source_ref)
        if state != "COMPLETE":
            reason = row["reason_code"]
            if (
                not isinstance(reason, str)
                or not reason
                or not re.fullmatch(r"[A-Z][A-Z0-9_]{2,95}", reason)
            ):
                _fail("MIGRATION_SOURCE_REASON_INVALID")
            blockers.add("SOURCE_" + state + "_" + source_class)
        else:
            pre = _validate_snapshot(
                row["pre_snapshot"],
                "MIGRATION_PRE_SNAPSHOT_INVALID:" + source_class,
            )
            post = _validate_snapshot(
                row["post_snapshot"],
                "MIGRATION_POST_SNAPSHOT_INVALID:" + source_class,
            )
            target = _validate_snapshot(
                row["target_snapshot"],
                "MIGRATION_TARGET_SNAPSHOT_INVALID:" + source_class,
            )
            if not _snapshot_equal(pre, post):
                blockers.add("PROTECTED_SOURCE_MUTATION_" + source_class)
            if not _snapshot_equal(pre, target):
                blockers.add("SOURCE_TARGET_PARITY_MISMATCH_" + source_class)
        normalized.append(copy.deepcopy(row))
    if tuple(sorted(observed_classes)) != SOURCE_CLASSES:
        _fail("MIGRATION_SOURCE_CLASS_CLOSURE_INVALID")
    if len(set(observed_refs)) != len(observed_refs):
        _fail("MIGRATION_SOURCE_REF_DUPLICATE")
    normalized.sort(key=lambda row: row["source_class"])
    return tuple(normalized), blockers


def _history_blockers(
    rows: Any,
) -> Tuple[Tuple[Mapping[str, Any], ...], set[str]]:
    if not isinstance(rows, list) or len(rows) != len(SOURCE_CLASSES):
        _fail("HISTORICAL_PATH_PARITY_SET_INVALID")
    normalized = []
    blockers: set[str] = set()
    observed = []
    for row in rows:
        item = _require_exact_keys(
            row,
            (
                "source_class",
                "predecessor_git_object_id",
                "source_tree_git_object_id",
                "target_tree_git_object_id",
                "target_path_present",
                "tree_object_equal",
            ),
            "HISTORICAL_PATH_PARITY_ROW_INVALID",
        )
        if item["source_class"] not in SOURCE_CLASSES:
            _fail("HISTORICAL_PATH_SOURCE_CLASS_INVALID")
        observed.append(item["source_class"])
        for field in (
            "predecessor_git_object_id",
            "source_tree_git_object_id",
            "target_tree_git_object_id",
        ):
            if (
                not isinstance(item[field], str)
                or GIT_OBJECT_RE.fullmatch(item[field]) is None
            ):
                _fail("HISTORICAL_PATH_GIT_OBJECT_INVALID:" + field)
        for field in ("target_path_present", "tree_object_equal"):
            if not isinstance(item[field], bool):
                _fail("HISTORICAL_PATH_BOOL_INVALID:" + field)
        if not item["target_path_present"]:
            blockers.add(
                "HISTORICAL_TARGET_PATH_MISSING_" + item["source_class"]
            )
        if not item["tree_object_equal"]:
            blockers.add(
                "HISTORICAL_TREE_PARITY_MISMATCH_" + item["source_class"]
            )
        normalized.append(copy.deepcopy(item))
    if tuple(sorted(observed)) != SOURCE_CLASSES:
        _fail("HISTORICAL_PATH_SOURCE_CLASS_CLOSURE_INVALID")
    normalized.sort(key=lambda row: row["source_class"])
    return tuple(normalized), blockers


def _query_blockers(
    queries: Any,
) -> Tuple[Tuple[Mapping[str, Any], ...], set[str]]:
    if not isinstance(queries, list):
        _fail("DUAL_READ_QUERY_SET_INVALID")
    normalized = []
    blockers: set[str] = set()
    refs = []
    if not queries:
        blockers.add("DUAL_READ_EVIDENCE_MISSING")
    for row in queries:
        if not isinstance(row, dict):
            _fail("DUAL_READ_QUERY_ROW_INVALID")
        state = row.get("state")
        required = {"query_ref", "state"}
        if state == "COMPLETE":
            required.update(("old_view", "new_view"))
        else:
            required.add("reason_code")
        if set(row) != required:
            _fail("DUAL_READ_QUERY_FIELDS_INVALID")
        query_ref = row["query_ref"]
        if not isinstance(query_ref, str) or REF_RE.fullmatch(query_ref) is None:
            _fail("DUAL_READ_QUERY_REF_INVALID")
        refs.append(query_ref)
        if state not in QUERY_STATES:
            _fail("DUAL_READ_QUERY_STATE_INVALID")
        if state != "COMPLETE":
            reason = row["reason_code"]
            if (
                not isinstance(reason, str)
                or re.fullmatch(r"[A-Z][A-Z0-9_]{2,95}", reason) is None
            ):
                _fail("DUAL_READ_QUERY_REASON_INVALID")
            blockers.add(
                "DUAL_READ_"
                + state
                + "_"
                + query_ref.upper().replace("-", "_")
            )
        else:
            for view_name in ("old_view", "new_view"):
                view = _require_exact_keys(
                    row[view_name],
                    ("record_count", "evidence_digest"),
                    "DUAL_READ_VIEW_INVALID:" + view_name,
                )
                _require_nonnegative(
                    view["record_count"],
                    "DUAL_READ_RECORD_COUNT_INVALID",
                )
                if (
                    not isinstance(view["evidence_digest"], str)
                    or SHA256_RE.fullmatch(view["evidence_digest"]) is None
                ):
                    _fail("DUAL_READ_RESULT_DIGEST_INVALID")
            if row["old_view"] != row["new_view"]:
                blockers.add(
                    "DUAL_READ_RESULT_MISMATCH_"
                    + query_ref.upper().replace("-", "_")
                )
        normalized.append(copy.deepcopy(row))
    if len(refs) != len(set(refs)):
        _fail("DUAL_READ_QUERY_REF_DUPLICATE")
    normalized.sort(key=lambda row: row["query_ref"])
    return tuple(normalized), blockers


def _audit_blockers(audit: Any) -> Tuple[Mapping[str, Any], set[str]]:
    item = _require_exact_keys(
        audit,
        (
            "mode",
            *AUDIT_COUNTER_FIELDS,
            "forbidden_command_observed",
            "audit_complete",
        ),
        "MIGRATION_AUDIT_FIELDS_INVALID",
    )
    if item["mode"] not in {
        "STATIC_CAPABILITY_AUDIT",
        "CONTROLLED_SYSCALL_AND_COMMAND_AUDIT",
    }:
        _fail("MIGRATION_AUDIT_MODE_INVALID")
    if not isinstance(item["audit_complete"], bool):
        _fail("MIGRATION_AUDIT_COMPLETENESS_INVALID")
    if not isinstance(item["forbidden_command_observed"], bool):
        _fail("MIGRATION_AUDIT_FORBIDDEN_COMMAND_FLAG_INVALID")
    blockers: set[str] = set()
    if not item["audit_complete"]:
        blockers.add("MIGRATION_AUDIT_INCOMPLETE")
    if item["forbidden_command_observed"]:
        blockers.add("FORBIDDEN_COMMAND_OBSERVED")
    for field in AUDIT_COUNTER_FIELDS:
        count = _require_nonnegative(
            item[field],
            "MIGRATION_AUDIT_COUNTER_INVALID:" + field,
        )
        if count:
            blockers.add("NONZERO_" + field.upper())
    return copy.deepcopy(item), blockers


def build_observation(
    *,
    observation_uid: str,
    baseline_git_object_id: str,
    sources: Sequence[Mapping[str, Any]],
    historical_path_parity: Sequence[Mapping[str, Any]],
    dual_read_queries: Sequence[Mapping[str, Any]],
    mutation_audit: Mapping[str, Any],
    delete_budget: int = 0,
) -> Mapping[str, Any]:
    """Normalize and self-digest one public-safe M-065 observation."""

    if not isinstance(observation_uid, str) or UID_RE.fullmatch(observation_uid) is None:
        _fail("MIGRATION_OBSERVATION_UID_INVALID")
    if (
        not isinstance(baseline_git_object_id, str)
        or GIT_OBJECT_RE.fullmatch(baseline_git_object_id) is None
    ):
        _fail("MIGRATION_BASELINE_GIT_OBJECT_INVALID")
    normalized_sources, source_blockers = _source_blockers(list(sources))
    normalized_history, history_blockers = _history_blockers(
        list(historical_path_parity)
    )
    normalized_queries, query_blockers = _query_blockers(
        list(dual_read_queries)
    )
    normalized_audit, audit_blockers = _audit_blockers(mutation_audit)
    _require_nonnegative(delete_budget, "MIGRATION_DELETE_BUDGET_INVALID")
    blockers = (
        source_blockers | history_blockers | query_blockers | audit_blockers
    )
    if delete_budget != 0:
        blockers.add("DELETE_BUDGET_NONZERO")
    value: Dict[str, Any] = {
        "schema_version": OBSERVATION_SCHEMA_ID,
        "protocol_revision": PROTOCOL_REVISION,
        "bundle_digest": CANDIDATE_BUNDLE_DIGEST,
        "observation_uid": observation_uid,
        "owner_plane": "MECHANISM",
        "status": "DRAFT_NON_ACTIVE",
        "baseline_git_object_id": baseline_git_object_id,
        "sources": list(normalized_sources),
        "historical_path_parity": list(normalized_history),
        "dual_read_queries": list(normalized_queries),
        "mutation_audit": normalized_audit,
        "delete_budget": delete_budget,
        "local_data_mutation_performed": any(
            code.startswith(
                ("NONZERO_", "PROTECTED_SOURCE_MUTATION_")
            )
            for code in blockers
        ),
        "derived_blocker_codes": sorted(blockers),
        "evidence_bundle_digest": "0" * 64,
    }
    value["evidence_bundle_digest"] = canonical_digest(
        value,
        OBSERVATION_SELF_POINTER,
    )
    validate_observation(value)
    return value


def _recomputed_blockers(value: Mapping[str, Any]) -> Tuple[str, ...]:
    _, source_blockers = _source_blockers(value["sources"])
    _, history_blockers = _history_blockers(
        value["historical_path_parity"]
    )
    _, query_blockers = _query_blockers(value["dual_read_queries"])
    _, audit_blockers = _audit_blockers(value["mutation_audit"])
    blockers = (
        source_blockers | history_blockers | query_blockers | audit_blockers
    )
    if value["delete_budget"] != 0:
        blockers.add("DELETE_BUDGET_NONZERO")
    return tuple(sorted(blockers))


def validate_observation(value: Mapping[str, Any]) -> None:
    """Recompute every security-relevant M-065 observation fact."""

    required = (
        "schema_version",
        "protocol_revision",
        "bundle_digest",
        "observation_uid",
        "owner_plane",
        "status",
        "baseline_git_object_id",
        "sources",
        "historical_path_parity",
        "dual_read_queries",
        "mutation_audit",
        "delete_budget",
        "local_data_mutation_performed",
        "derived_blocker_codes",
        "evidence_bundle_digest",
    )
    item = _require_exact_keys(value, required, "MIGRATION_OBSERVATION_FIELDS_INVALID")
    if (
        item["schema_version"] != OBSERVATION_SCHEMA_ID
        or item["protocol_revision"] != PROTOCOL_REVISION
        or item["bundle_digest"] != CANDIDATE_BUNDLE_DIGEST
        or item["owner_plane"] != "MECHANISM"
        or item["status"] != "DRAFT_NON_ACTIVE"
    ):
        _fail("MIGRATION_OBSERVATION_CONTEXT_INVALID")
    if not isinstance(item["observation_uid"], str) or UID_RE.fullmatch(
        item["observation_uid"]
    ) is None:
        _fail("MIGRATION_OBSERVATION_UID_INVALID")
    if not isinstance(item["baseline_git_object_id"], str) or GIT_OBJECT_RE.fullmatch(
        item["baseline_git_object_id"]
    ) is None:
        _fail("MIGRATION_BASELINE_GIT_OBJECT_INVALID")
    _require_nonnegative(item["delete_budget"], "MIGRATION_DELETE_BUDGET_INVALID")
    blockers = _recomputed_blockers(item)
    if item["derived_blocker_codes"] != list(blockers):
        _fail("MIGRATION_BLOCKER_RECOMPUTATION_MISMATCH")
    expected_mutation = any(
        code.startswith(("NONZERO_", "PROTECTED_SOURCE_MUTATION_"))
        for code in blockers
    )
    if item["local_data_mutation_performed"] is not expected_mutation:
        _fail("MIGRATION_MUTATION_FLAG_MISMATCH")
    if item["evidence_bundle_digest"] != canonical_digest(
        item,
        OBSERVATION_SELF_POINTER,
    ):
        _fail("MIGRATION_OBSERVATION_DIGEST_MISMATCH")


def derive_cutover_plan(
    observation: Mapping[str, Any],
    *,
    plan_uid: str,
    dependency_blocker_codes: Sequence[str] = (),
) -> Mapping[str, Any]:
    """Derive the only allowed shadow plan; caller decisions are ignored."""

    validate_observation(observation)
    if not isinstance(plan_uid, str) or UID_RE.fullmatch(plan_uid) is None:
        _fail("CUTOVER_PLAN_UID_INVALID")
    dependency_blockers = []
    for code in dependency_blocker_codes:
        if (
            not isinstance(code, str)
            or re.fullmatch(r"[A-Z][A-Z0-9_]{2,127}", code) is None
        ):
            _fail("CUTOVER_DEPENDENCY_BLOCKER_INVALID")
        dependency_blockers.append(code)
    if len(dependency_blockers) != len(set(dependency_blockers)):
        _fail("CUTOVER_DEPENDENCY_BLOCKER_DUPLICATE")
    blockers = sorted(
        set(observation["derived_blocker_codes"]) | set(dependency_blockers)
    )
    decision = "CUTOVER_ELIGIBLE" if not blockers else "BLOCKED"
    value: Dict[str, Any] = {
        "schema_version": PLAN_SCHEMA_ID,
        "protocol_revision": PROTOCOL_REVISION,
        "bundle_digest": CANDIDATE_BUNDLE_DIGEST,
        "plan_uid": plan_uid,
        "owner_plane": "MECHANISM",
        "status": "DRAFT_NON_ACTIVE",
        "observation_ref": {
            "observation_uid": observation["observation_uid"],
            "evidence_digest": observation["evidence_bundle_digest"],
        },
        "decision": decision,
        "cutover_mode": CUTOVER_MODE,
        "parity_complete": not any(
            code.startswith(("SOURCE_", "PROTECTED_SOURCE_", "HISTORICAL_"))
            for code in blockers
        ),
        "dual_read_complete": not any(
            code.startswith("DUAL_READ_") for code in blockers
        ),
        "zero_local_mutation_verified": not any(
            code.startswith(
                ("NONZERO_", "PROTECTED_SOURCE_MUTATION_")
            )
            or code
            in {
                "MIGRATION_AUDIT_INCOMPLETE",
                "FORBIDDEN_COMMAND_OBSERVED",
                "DELETE_BUDGET_NONZERO",
            }
            for code in blockers
        ),
        "delete_budget": 0,
        "current_cutover_permitted": False,
        "blocker_codes": blockers,
        "rollback_contract": copy.deepcopy(FIXED_ROLLBACK_CONTRACT),
        "evidence_bundle_digest": "0" * 64,
    }
    value["evidence_bundle_digest"] = canonical_digest(
        value,
        PLAN_SELF_POINTER,
    )
    validate_cutover_plan(value, observation)
    return value


def validate_cutover_plan(
    value: Mapping[str, Any],
    observation: Mapping[str, Any],
) -> None:
    """Reject self-consistent plan drift or caller-authorized cutover claims."""

    validate_observation(observation)
    required = (
        "schema_version",
        "protocol_revision",
        "bundle_digest",
        "plan_uid",
        "owner_plane",
        "status",
        "observation_ref",
        "decision",
        "cutover_mode",
        "parity_complete",
        "dual_read_complete",
        "zero_local_mutation_verified",
        "delete_budget",
        "current_cutover_permitted",
        "blocker_codes",
        "rollback_contract",
        "evidence_bundle_digest",
    )
    item = _require_exact_keys(value, required, "CUTOVER_PLAN_FIELDS_INVALID")
    if (
        item["schema_version"] != PLAN_SCHEMA_ID
        or item["protocol_revision"] != PROTOCOL_REVISION
        or item["bundle_digest"] != CANDIDATE_BUNDLE_DIGEST
        or item["owner_plane"] != "MECHANISM"
        or item["status"] != "DRAFT_NON_ACTIVE"
        or item["cutover_mode"] != CUTOVER_MODE
        or item["current_cutover_permitted"] is not False
        or item["delete_budget"] != 0
    ):
        _fail("CUTOVER_PLAN_CONTEXT_INVALID")
    if item["decision"] not in DECISIONS:
        _fail("CUTOVER_PLAN_DECISION_INVALID")
    if not isinstance(item["plan_uid"], str) or UID_RE.fullmatch(
        item["plan_uid"]
    ) is None:
        _fail("CUTOVER_PLAN_UID_INVALID")
    if item["observation_ref"] != {
        "observation_uid": observation["observation_uid"],
        "evidence_digest": observation["evidence_bundle_digest"],
    }:
        _fail("CUTOVER_OBSERVATION_BINDING_MISMATCH")
    if item["rollback_contract"] != FIXED_ROLLBACK_CONTRACT:
        _fail("CUTOVER_ROLLBACK_CONTRACT_INVALID")
    blockers = item["blocker_codes"]
    if (
        not isinstance(blockers, list)
        or blockers != sorted(set(blockers))
        or any(
            not isinstance(code, str)
            or re.fullmatch(r"[A-Z][A-Z0-9_]{2,127}", code) is None
            for code in blockers
        )
    ):
        _fail("CUTOVER_BLOCKER_SET_INVALID")
    observation_blockers = set(observation["derived_blocker_codes"])
    if not observation_blockers.issubset(set(blockers)):
        _fail("CUTOVER_OBSERVATION_BLOCKER_DROPPED")
    expected_decision = "CUTOVER_ELIGIBLE" if not blockers else "BLOCKED"
    if item["decision"] != expected_decision:
        _fail("CUTOVER_DECISION_RECOMPUTATION_MISMATCH")
    expected_parity = not any(
        code.startswith(("SOURCE_", "PROTECTED_SOURCE_", "HISTORICAL_"))
        for code in blockers
    )
    expected_dual = not any(code.startswith("DUAL_READ_") for code in blockers)
    expected_zero = not any(
        code.startswith(("NONZERO_", "PROTECTED_SOURCE_MUTATION_"))
        or code
        in {
            "MIGRATION_AUDIT_INCOMPLETE",
            "FORBIDDEN_COMMAND_OBSERVED",
            "DELETE_BUDGET_NONZERO",
        }
        for code in blockers
    )
    if (
        item["parity_complete"] is not expected_parity
        or item["dual_read_complete"] is not expected_dual
        or item["zero_local_mutation_verified"] is not expected_zero
    ):
        _fail("CUTOVER_DERIVED_FACT_MISMATCH")
    if item["evidence_bundle_digest"] != canonical_digest(
        item,
        PLAN_SELF_POINTER,
    ):
        _fail("CUTOVER_PLAN_DIGEST_MISMATCH")


__all__ = [
    "AUDIT_COUNTER_FIELDS",
    "CANDIDATE_BUNDLE_DIGEST",
    "DECISIONS",
    "FIXED_ROLLBACK_CONTRACT",
    "OBSERVATION_SCHEMA_ID",
    "OBSERVATION_SELF_POINTER",
    "PLAN_SCHEMA_ID",
    "PLAN_SELF_POINTER",
    "PROTOCOL_REVISION",
    "ReadOnlyCutoverError",
    "SOURCE_CLASSES",
    "SNAPSHOT_FIELDS",
    "build_observation",
    "derive_cutover_plan",
    "validate_cutover_plan",
    "validate_observation",
]
