"""Pure append-only promotion controller for Task Pack M-056.

The controller validates an externally trusted contract bundle, a
content-addressed Registry snapshot, evaluation artifacts, a promotion
evidence bundle, and promotion decisions.  It returns immutable replay views
and canonical decision bytes.  It never writes Registry state, ledgers, Git,
VERSION, notifications, or public artifacts.

Rollback and revocation remain a separate M-057 phase.  Supplying either
action here fails closed instead of silently applying incomplete semantics.
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import re
import sys
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple


GOVERNANCE_TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
if str(GOVERNANCE_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(GOVERNANCE_TOOLS_DIR))

from CodexSkills.governance.tools.canonical_json import (  # noqa: E402
    canonical_digest,
    canonicalize_object,
)
from CodexSkills.governance.tools.validate_mechanism import (  # noqa: E402
    ContractBundle,
    ContractError,
    validate_instance,
)


SCHEMA_PREFIX = "urn:linzecolin:agentdatabase:skillops:schema:"
PROTOCOL_REVISION = (
    "urn:linzecolin:agentdatabase:skillops:protocol:cross-pack:v1"
)
REGISTRY_SNAPSHOT_SCHEMA_ID = SCHEMA_PREFIX + "registry-snapshot:v1"
SKILL_IDENTITY_SCHEMA_ID = SCHEMA_PREFIX + "skill-identity:v1"
SKILL_INSTANCE_SCHEMA_ID = SCHEMA_PREFIX + "skill-instance:v1"
SKILL_VERSION_SCHEMA_ID = SCHEMA_PREFIX + "skill-version:v1"
EVAL_RUN_SCHEMA_ID = SCHEMA_PREFIX + "eval-run:v1"
SCORECARD_SCHEMA_ID = SCHEMA_PREFIX + "scorecard:v1"
PROMOTION_EVIDENCE_SCHEMA_ID = (
    SCHEMA_PREFIX + "promotion-evidence-bundle:v1"
)
PROMOTION_DECISION_SCHEMA_ID = SCHEMA_PREFIX + "promotion-decision:v1"

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
UTC_Z_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


class PromotionControllerError(ValueError):
    """A promotion ledger or evidence invariant failed closed."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclasses.dataclass(frozen=True)
class VersionContext:
    """Immutable Registry facts needed by the promotion controller."""

    skill_version_uid: str
    skill_instance_uid: str
    skill_identity_uid: str
    lifecycle_status: str
    trust_tier: str
    srv_revision: str
    version_record_digest: str


@dataclasses.dataclass(frozen=True)
class PromotionRegistryView:
    """Normalized, immutable Registry closure."""

    registry_snapshot_digest: str
    identity_uids: Tuple[str, ...]
    instance_bindings: Tuple[Tuple[str, str], ...]
    versions: Tuple[VersionContext, ...]
    base_champions: Tuple[Tuple[str, str], ...]
    challenger_version_uids: Tuple[str, ...]


@dataclasses.dataclass(frozen=True)
class PromotionLedgerView:
    """Deterministic result of replaying append-only promotion decisions."""

    decision_uids: Tuple[str, ...]
    decision_digests: Tuple[str, ...]
    champion_by_scope: Tuple[Tuple[str, str], ...]
    terminal_candidate_version_uids: Tuple[str, ...]
    last_decided_at: Optional[str]
    ledger_digest: str
    promote_count: int
    reject_count: int


@dataclasses.dataclass(frozen=True)
class PromotionAppendResult:
    """Canonical append record plus the post-append replay view."""

    canonical_decision_bytes: bytes
    decision_digest: str
    predecessor_ledger_digest: str
    ledger_view: PromotionLedgerView


def _fail(code: str) -> None:
    raise PromotionControllerError(code)


def _strict_mapping(value: Any, code: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        _fail(code)
    return value


def _strict_sequence(value: Any, code: str) -> Sequence[Any]:
    if not isinstance(value, list):
        _fail(code)
    return value


def _exact_keys(
    value: Mapping[str, Any],
    expected: Sequence[str],
    code: str,
) -> None:
    if set(value) != set(expected):
        _fail(code)


def _sorted_unique(values: Sequence[str], code: str) -> None:
    if (
        any(not isinstance(value, str) for value in values)
        or list(values)
        != sorted(values, key=lambda value: value.encode("utf-8"))
        or len(values) != len(set(values))
    ):
        _fail(code)


def _timestamp(value: str, code: str) -> dt.datetime:
    try:
        return dt.datetime.strptime(value, UTC_Z_FORMAT)
    except (TypeError, ValueError) as exc:
        raise PromotionControllerError(code) from exc


def _validate_artifact(
    bundle: ContractBundle,
    value: Mapping[str, Any],
    schema_id: str,
    expected_bundle_digest: str,
    code: str,
) -> None:
    try:
        validate_instance(
            bundle,
            value,
            schema_id,
            expected_bundle_digest=expected_bundle_digest,
            public=True,
        )
    except ContractError as exc:
        raise PromotionControllerError(code + ":" + str(exc)) from exc


def _wrapper_record(
    wrapper: Any,
    digest_field: str,
    code: str,
) -> Tuple[Mapping[str, Any], str]:
    shaped = _strict_mapping(wrapper, code + "_WRAPPER_INVALID")
    _exact_keys(
        shaped,
        ("record", digest_field),
        code + "_WRAPPER_FIELDS_INVALID",
    )
    record = _strict_mapping(
        shaped["record"],
        code + "_RECORD_INVALID",
    )
    observed = shaped[digest_field]
    if (
        not isinstance(observed, str)
        or not SHA256_RE.fullmatch(observed)
        or canonical_digest(record) != observed
    ):
        _fail(code + "_RECORD_DIGEST_MISMATCH")
    return record, observed


def build_registry_view(
    bundle: ContractBundle,
    snapshot: Mapping[str, Any],
    *,
    expected_bundle_digest: str,
    expected_registry_snapshot_digest: str,
) -> PromotionRegistryView:
    """Validate Registry identity/instance/version closure without mutation."""

    root = _strict_mapping(snapshot, "PROMOTION_REGISTRY_ROOT_INVALID")
    if (
        root.get("schema_version") != REGISTRY_SNAPSHOT_SCHEMA_ID
        or root.get("protocol_revision") != PROTOCOL_REVISION
        or root.get("bundle_digest") != expected_bundle_digest
        or root.get("status") != "REGISTERED"
    ):
        _fail("PROMOTION_REGISTRY_CONTEXT_INVALID")
    if (
        not SHA256_RE.fullmatch(expected_registry_snapshot_digest)
        or root.get("registry_snapshot_digest")
        != expected_registry_snapshot_digest
        or canonical_digest(root, "/registry_snapshot_digest")
        != expected_registry_snapshot_digest
    ):
        _fail("PROMOTION_REGISTRY_SNAPSHOT_DIGEST_MISMATCH")

    identities_raw = _strict_sequence(
        root.get("identities"),
        "PROMOTION_REGISTRY_IDENTITIES_INVALID",
    )
    instances_raw = _strict_sequence(
        root.get("instances"),
        "PROMOTION_REGISTRY_INSTANCES_INVALID",
    )
    versions_raw = _strict_sequence(
        root.get("versions"),
        "PROMOTION_REGISTRY_VERSIONS_INVALID",
    )
    counts = _strict_mapping(
        root.get("counts"),
        "PROMOTION_REGISTRY_COUNTS_INVALID",
    )
    for field, observed in (
        ("identity_count", len(identities_raw)),
        ("instance_count", len(instances_raw)),
        ("version_count", len(versions_raw)),
    ):
        if (
            isinstance(counts.get(field), bool)
            or counts.get(field) != observed
        ):
            _fail("PROMOTION_REGISTRY_" + field.upper() + "_MISMATCH")

    identities: Dict[str, Mapping[str, Any]] = {}
    for wrapper in identities_raw:
        record, _ = _wrapper_record(
            wrapper,
            "artifact_digest",
            "PROMOTION_IDENTITY",
        )
        _validate_artifact(
            bundle,
            record,
            SKILL_IDENTITY_SCHEMA_ID,
            expected_bundle_digest,
            "PROMOTION_IDENTITY_CONTRACT_INVALID",
        )
        uid = record["skill_identity_uid"]
        if uid in identities:
            _fail("PROMOTION_IDENTITY_UID_DUPLICATE")
        _sorted_unique(
            record["instance_uids"],
            "PROMOTION_IDENTITY_INSTANCE_ORDER_INVALID",
        )
        identities[uid] = record

    instances: Dict[str, Mapping[str, Any]] = {}
    for wrapper in instances_raw:
        record, _ = _wrapper_record(
            wrapper,
            "artifact_digest",
            "PROMOTION_INSTANCE",
        )
        _validate_artifact(
            bundle,
            record,
            SKILL_INSTANCE_SCHEMA_ID,
            expected_bundle_digest,
            "PROMOTION_INSTANCE_CONTRACT_INVALID",
        )
        uid = record["skill_instance_uid"]
        if uid in instances:
            _fail("PROMOTION_INSTANCE_UID_DUPLICATE")
        if record["skill_identity_uid"] not in identities:
            _fail("PROMOTION_INSTANCE_IDENTITY_UNKNOWN")
        _sorted_unique(
            record["version_uids"],
            "PROMOTION_INSTANCE_VERSION_ORDER_INVALID",
        )
        instances[uid] = record

    versions: Dict[str, VersionContext] = {}
    for wrapper in versions_raw:
        record, record_digest = _wrapper_record(
            wrapper,
            "version_record_digest",
            "PROMOTION_VERSION",
        )
        _validate_artifact(
            bundle,
            record,
            SKILL_VERSION_SCHEMA_ID,
            expected_bundle_digest,
            "PROMOTION_VERSION_CONTRACT_INVALID",
        )
        uid = record["skill_version_uid"]
        if uid in versions:
            _fail("PROMOTION_VERSION_UID_DUPLICATE")
        instance_uid = record["skill_instance_uid"]
        if instance_uid not in instances:
            _fail("PROMOTION_VERSION_INSTANCE_UNKNOWN")
        identity_uid = instances[instance_uid]["skill_identity_uid"]
        versions[uid] = VersionContext(
            skill_version_uid=uid,
            skill_instance_uid=instance_uid,
            skill_identity_uid=identity_uid,
            lifecycle_status=record["lifecycle_status"],
            trust_tier=record["trust_tier"],
            srv_revision=record["srv_revision"],
            version_record_digest=record_digest,
        )

    expected_instances: Dict[str, set[str]] = {
        identity_uid: set() for identity_uid in identities
    }
    for instance_uid, record in instances.items():
        expected_instances[record["skill_identity_uid"]].add(instance_uid)
    for identity_uid, record in identities.items():
        if set(record["instance_uids"]) != expected_instances[identity_uid]:
            _fail("PROMOTION_IDENTITY_INSTANCE_CLOSURE_MISMATCH")

    expected_versions: Dict[str, set[str]] = {
        instance_uid: set() for instance_uid in instances
    }
    for version in versions.values():
        expected_versions[version.skill_instance_uid].add(
            version.skill_version_uid
        )
    for instance_uid, record in instances.items():
        if set(record["version_uids"]) != expected_versions[instance_uid]:
            _fail("PROMOTION_INSTANCE_VERSION_CLOSURE_MISMATCH")

    champions: Dict[str, str] = {}
    challengers = []
    for version in versions.values():
        if version.lifecycle_status == "CHAMPION":
            if version.skill_identity_uid in champions:
                _fail("PROMOTION_REGISTRY_MULTIPLE_CHAMPIONS_PER_SCOPE")
            instance = instances[version.skill_instance_uid]
            identity = identities[version.skill_identity_uid]
            if (
                instance["lifecycle_status"] != "CHAMPION"
                or identity["lifecycle_status"] != "CHAMPION"
            ):
                _fail("PROMOTION_REGISTRY_CHAMPION_LIFECYCLE_INCOHERENT")
            champions[version.skill_identity_uid] = (
                version.skill_version_uid
            )
        elif version.lifecycle_status == "CHALLENGER":
            challengers.append(version.skill_version_uid)

    return PromotionRegistryView(
        registry_snapshot_digest=expected_registry_snapshot_digest,
        identity_uids=tuple(
            sorted(identities, key=lambda value: value.encode("ascii"))
        ),
        instance_bindings=tuple(
            sorted(
                (
                    (uid, record["skill_identity_uid"])
                    for uid, record in instances.items()
                ),
                key=lambda item: item[0].encode("ascii"),
            )
        ),
        versions=tuple(
            sorted(
                versions.values(),
                key=lambda item: item.skill_version_uid.encode("ascii"),
            )
        ),
        base_champions=tuple(
            sorted(
                champions.items(),
                key=lambda item: item[0].encode("ascii"),
            )
        ),
        challenger_version_uids=tuple(
            sorted(challengers, key=lambda value: value.encode("ascii"))
        ),
    )


def _version_map(
    registry_view: PromotionRegistryView,
) -> Dict[str, VersionContext]:
    return {
        version.skill_version_uid: version
        for version in registry_view.versions
    }


def promotion_ledger_digest(
    registry_snapshot_digest: str,
    decision_digests: Sequence[str],
) -> str:
    """Bind one ordered decision history to one exact Registry snapshot."""

    if (
        not isinstance(registry_snapshot_digest, str)
        or not SHA256_RE.fullmatch(registry_snapshot_digest)
        or any(
            not isinstance(value, str) or not SHA256_RE.fullmatch(value)
            for value in decision_digests
        )
    ):
        _fail("PROMOTION_LEDGER_DIGEST_INPUT_INVALID")
    return canonical_digest(
        {
            "decision_digests": list(decision_digests),
            "domain": "SKILLOPS_PROMOTION_LEDGER_V1",
            "protocol_revision": PROTOCOL_REVISION,
            "registry_snapshot_digest": registry_snapshot_digest,
        }
    )


def _artifact_map(
    bundle: ContractBundle,
    values: Mapping[str, Mapping[str, Any]],
    *,
    schema_id: str,
    digest_field: str,
    expected_bundle_digest: str,
    code: str,
) -> Dict[str, Mapping[str, Any]]:
    if not isinstance(values, dict):
        _fail(code + "_MAP_INVALID")
    result: Dict[str, Mapping[str, Any]] = {}
    for digest, value in values.items():
        if (
            not isinstance(digest, str)
            or not SHA256_RE.fullmatch(digest)
            or not isinstance(value, dict)
        ):
            _fail(code + "_MAP_ENTRY_INVALID")
        _validate_artifact(
            bundle,
            value,
            schema_id,
            expected_bundle_digest,
            code + "_CONTRACT_INVALID",
        )
        if value.get(digest_field) != digest:
            _fail(code + "_MAP_DIGEST_KEY_MISMATCH")
        result[digest] = value
    return result


def _reference_digests(
    refs: Sequence[Mapping[str, Any]],
    expected_schema_id: str,
    code: str,
) -> Tuple[str, ...]:
    keys = []
    digests = []
    for ref in refs:
        if not isinstance(ref, dict):
            _fail(code + "_REF_INVALID")
        if ref.get("schema_id") != expected_schema_id:
            _fail(code + "_SCHEMA_ID_INVALID")
        key = (
            ref.get("schema_id"),
            ref.get("artifact_uid"),
            ref.get("artifact_digest"),
        )
        keys.append(key)
        digests.append(ref.get("artifact_digest"))
    if (
        any(not isinstance(value, str) for value in digests)
        or keys != sorted(keys)
        or len(keys) != len(set(keys))
    ):
        _fail(code + "_REF_ORDER_INVALID")
    return tuple(digests)


def _validate_evidence_closure(
    bundle: ContractBundle,
    registry_view: PromotionRegistryView,
    evidence: Mapping[str, Any],
    scorecards_by_digest: Mapping[str, Mapping[str, Any]],
    eval_runs_by_digest: Mapping[str, Mapping[str, Any]],
    expected_bundle_digest: str,
) -> bool:
    """Return whether the dereferenced evidence is promotion-eligible."""

    versions = _version_map(registry_view)
    candidate_uid = evidence["candidate_skill_version_uid"]
    baseline_uid = evidence["baseline_skill_version_uid"]
    if candidate_uid not in versions or baseline_uid not in versions:
        _fail("PROMOTION_EVIDENCE_VERSION_UNKNOWN")
    candidate = versions[candidate_uid]
    baseline = versions[baseline_uid]
    if candidate.skill_identity_uid != baseline.skill_identity_uid:
        _fail("PROMOTION_EVIDENCE_VERSION_SCOPE_MISMATCH")
    if evidence["rollback_target_version_uid"] != baseline_uid:
        _fail("PROMOTION_EVIDENCE_BASELINE_ROLLBACK_MISMATCH")

    all_scorecards = _artifact_map(
        bundle,
        scorecards_by_digest,
        schema_id=SCORECARD_SCHEMA_ID,
        digest_field="scorecard_digest",
        expected_bundle_digest=expected_bundle_digest,
        code="PROMOTION_SCORECARD",
    )
    all_eval_runs = _artifact_map(
        bundle,
        eval_runs_by_digest,
        schema_id=EVAL_RUN_SCHEMA_ID,
        digest_field="eval_run_digest",
        expected_bundle_digest=expected_bundle_digest,
        code="PROMOTION_EVAL_RUN",
    )
    scorecard_ref_digests = _reference_digests(
        evidence["scorecard_refs"],
        SCORECARD_SCHEMA_ID,
        "PROMOTION_SCORECARD",
    )
    eval_ref_digests = _reference_digests(
        evidence["eval_run_refs"],
        EVAL_RUN_SCHEMA_ID,
        "PROMOTION_EVAL_RUN",
    )
    if (
        not set(scorecard_ref_digests).issubset(all_scorecards)
        or not set(eval_ref_digests).issubset(all_eval_runs)
    ):
        _fail("PROMOTION_EVIDENCE_REFERENCE_CLOSURE_MISMATCH")
    scorecards = {
        digest: all_scorecards[digest]
        for digest in scorecard_ref_digests
    }
    eval_runs = {
        digest: all_eval_runs[digest]
        for digest in eval_ref_digests
    }
    for ref in evidence["scorecard_refs"]:
        if (
            scorecards[ref["artifact_digest"]]["scorecard_uid"]
            != ref["artifact_uid"]
        ):
            _fail("PROMOTION_SCORECARD_UID_MISMATCH")
    for ref in evidence["eval_run_refs"]:
        if (
            eval_runs[ref["artifact_digest"]]["eval_run_uid"]
            != ref["artifact_uid"]
        ):
            _fail("PROMOTION_EVAL_RUN_UID_MISMATCH")

    matrix_by_digest: Dict[str, Mapping[str, Any]] = {}
    for cell in evidence["causal_matrix"]:
        digest = cell["eval_run_digest"]
        if digest in matrix_by_digest:
            _fail("PROMOTION_CAUSAL_EVAL_RUN_REUSED")
        matrix_by_digest[digest] = cell
    if set(matrix_by_digest) != set(eval_runs):
        _fail("PROMOTION_CAUSAL_EVAL_RUN_CLOSURE_MISMATCH")

    expected_cells = {
        "BASELINE": (
            baseline_uid,
            evidence["baseline_model_snapshot_digest"],
        ),
        "MODEL_EFFECT": (
            baseline_uid,
            evidence["candidate_model_snapshot_digest"],
        ),
        "SKILL_EFFECT": (
            candidate_uid,
            evidence["baseline_model_snapshot_digest"],
        ),
        "INTERACTION": (
            candidate_uid,
            evidence["candidate_model_snapshot_digest"],
        ),
    }
    eval_by_uid: Dict[str, Mapping[str, Any]] = {}
    all_eval_passed = True
    for digest, run in eval_runs.items():
        cell = matrix_by_digest[digest]
        expected_version_uid, expected_model_digest = expected_cells[
            cell["cell"]
        ]
        run_version = versions.get(run["skill_version_uid"])
        if run_version is None:
            _fail("PROMOTION_EVAL_RUN_VERSION_UNKNOWN")
        if (
            cell["skill_version_uid"] != expected_version_uid
            or run["skill_version_uid"] != expected_version_uid
            or cell["model_snapshot_digest"] != expected_model_digest
            or canonical_digest(run["model_snapshot"])
            != expected_model_digest
            or run["status"] != cell["status"]
            or run["skill_version_record_digest"]
            != run_version.version_record_digest
        ):
            _fail("PROMOTION_CAUSAL_MATRIX_BINDING_MISMATCH")
        if (
            run["environment_fingerprint_digest"]
            != evidence["environment_fingerprint_digest"]
            or run["tool_manifest_digest"]
            != evidence["tool_manifest_digest"]
            or run["dataset_manifest_digests"]
            != evidence["dataset_manifest_digests"]
            or run["evaluator_manifest_digests"]
            != evidence["evaluator_manifest_digests"]
            or run["rubric_digest"] != evidence["rubric_digest"]
            or run["policy_snapshot_digest"]
            != evidence["policy_snapshot_digest"]
        ):
            _fail("PROMOTION_EVAL_RUN_CONTEXT_MISMATCH")
        if run["eval_run_uid"] in eval_by_uid:
            _fail("PROMOTION_EVAL_RUN_UID_DUPLICATE")
        eval_by_uid[run["eval_run_uid"]] = run
        all_eval_passed = all_eval_passed and run["status"] == "PASS"

    all_scorecards_eligible = True
    all_hard_gates_passed = True
    for scorecard in scorecards.values():
        run = eval_by_uid.get(scorecard["eval_run_uid"])
        if run is None:
            _fail("PROMOTION_SCORECARD_EVAL_RUN_UNKNOWN")
        if (
            scorecard["skill_version_uid"] != candidate_uid
            or scorecard["skill_version_record_digest"]
            != candidate.version_record_digest
            or scorecard["model_snapshot_digest"]
            != evidence["candidate_model_snapshot_digest"]
            or scorecard["environment_fingerprint_digest"]
            != evidence["environment_fingerprint_digest"]
            or scorecard["dataset_manifest_digests"]
            != evidence["dataset_manifest_digests"]
            or scorecard["evaluator_manifest_digests"]
            != evidence["evaluator_manifest_digests"]
            or run["skill_version_uid"] != candidate_uid
            or scorecard["eval_profile_uid"] != run["eval_profile_uid"]
            or scorecard["eval_profile_digest"]
            != run["eval_profile_digest"]
            or _timestamp(
                scorecard["evaluated_at"],
                "PROMOTION_SCORECARD_TIMESTAMP_INVALID",
            )
            < _timestamp(
                run["finished_at"],
                "PROMOTION_EVAL_RUN_TIMESTAMP_INVALID",
            )
        ):
            _fail("PROMOTION_SCORECARD_CONTEXT_MISMATCH")
        scorecard_gates_passed = all(
            gate["passed"] for gate in scorecard["hard_gates"]
        )
        all_hard_gates_passed = (
            all_hard_gates_passed and scorecard_gates_passed
        )
        all_scorecards_eligible = (
            all_scorecards_eligible
            and scorecard["promotion_eligible"]
            and scorecard_gates_passed
            and scorecard["critical_incident_count"] == 0
            and scorecard["freshness_state"] == "FRESH"
        )

    promotable = (
        all_hard_gates_passed
        and all_scorecards_eligible
        and all_eval_passed
        and all(cell["status"] == "PASS" for cell in matrix_by_digest.values())
    )
    if evidence["hard_gates_passed"] != promotable:
        _fail("PROMOTION_EVIDENCE_ELIGIBILITY_CLAIM_MISMATCH")
    return promotable


def replay_promotion_ledger(
    bundle: ContractBundle,
    registry_view: PromotionRegistryView,
    *,
    evidence_by_digest: Mapping[str, Mapping[str, Any]],
    scorecards_by_digest: Mapping[str, Mapping[str, Any]],
    eval_runs_by_digest: Mapping[str, Mapping[str, Any]],
    decisions: Sequence[Mapping[str, Any]],
    expected_bundle_digest: str,
) -> PromotionLedgerView:
    """Replay an append-only CHAMPION/REJECT ledger deterministically."""

    if bundle.protocol_revision != PROTOCOL_REVISION:
        _fail("PROMOTION_BUNDLE_PROTOCOL_MISMATCH")
    versions = _version_map(registry_view)
    champions = dict(registry_view.base_champions)
    evidences = _artifact_map(
        bundle,
        evidence_by_digest,
        schema_id=PROMOTION_EVIDENCE_SCHEMA_ID,
        digest_field="evidence_bundle_digest",
        expected_bundle_digest=expected_bundle_digest,
        code="PROMOTION_EVIDENCE",
    )

    decision_uids = []
    decision_digests = []
    terminal_candidates = set()
    previous_time: Optional[dt.datetime] = None
    last_decided_at: Optional[str] = None
    promote_count = 0
    reject_count = 0
    used_evidence_digests = set()

    for raw_decision in decisions:
        decision = _strict_mapping(
            raw_decision,
            "PROMOTION_DECISION_ROOT_INVALID",
        )
        _validate_artifact(
            bundle,
            decision,
            PROMOTION_DECISION_SCHEMA_ID,
            expected_bundle_digest,
            "PROMOTION_DECISION_CONTRACT_INVALID",
        )
        action = decision["action"]
        if action in {"ROLLBACK", "REVOKE"}:
            _fail("PROMOTION_ROLLBACK_REVOCATION_PHASE_REQUIRED")
        if action not in {"PROMOTE", "REJECT"}:
            _fail("PROMOTION_ACTION_UNSUPPORTED")

        decision_uid = decision["promotion_decision_uid"]
        decision_digest = decision["decision_digest"]
        if decision_uid in decision_uids:
            _fail("PROMOTION_DECISION_UID_DUPLICATE")
        if decision_digest in decision_digests:
            _fail("PROMOTION_DECISION_DIGEST_DUPLICATE")
        decided_at = _timestamp(
            decision["decided_at"],
            "PROMOTION_DECISION_TIMESTAMP_INVALID",
        )
        if previous_time is not None and decided_at <= previous_time:
            _fail("PROMOTION_LEDGER_TIME_ORDER_INVALID")
        previous_time = decided_at
        last_decided_at = decision["decided_at"]

        evidence_digest = decision["evidence_bundle_digest"]
        evidence = evidences.get(evidence_digest)
        if evidence is None:
            _fail("PROMOTION_DECISION_EVIDENCE_UNKNOWN")
        if evidence_digest in used_evidence_digests:
            _fail("PROMOTION_EVIDENCE_REUSED")
        used_evidence_digests.add(evidence_digest)

        candidate_uid = decision["candidate_skill_version_uid"]
        candidate = versions.get(candidate_uid)
        if candidate is None:
            _fail("PROMOTION_CANDIDATE_VERSION_UNKNOWN")
        if candidate_uid in terminal_candidates:
            _fail("PROMOTION_CANDIDATE_ALREADY_DECIDED")
        if (
            candidate.lifecycle_status != "CHALLENGER"
            or candidate.trust_tier
            not in {"LOCAL_TRUSTED", "PINNED_UPSTREAM"}
            or decision["from_status"] != "CHALLENGER"
            or decision["srv_revision"] != candidate.srv_revision
        ):
            _fail("PROMOTION_CANDIDATE_NOT_ELIGIBLE")
        scope_uid = candidate.skill_identity_uid
        current_champion_uid = champions.get(scope_uid)
        if candidate_uid == current_champion_uid:
            _fail("PROMOTION_CANDIDATE_ALREADY_CHAMPION")

        baseline_uid = evidence["baseline_skill_version_uid"]
        rollback_uid = evidence["rollback_target_version_uid"]
        baseline = versions.get(baseline_uid)
        rollback = versions.get(rollback_uid)
        if baseline is None or rollback is None:
            _fail("PROMOTION_ROLLBACK_VERSION_UNKNOWN")
        if (
            baseline_uid != rollback_uid
            or baseline.skill_identity_uid != scope_uid
            or rollback.skill_identity_uid != scope_uid
            or evidence["candidate_skill_version_uid"] != candidate_uid
            or decision["rollback_target_version_uid"] != rollback_uid
        ):
            _fail("PROMOTION_DECISION_SCOPE_OR_ROLLBACK_MISMATCH")
        if current_champion_uid is not None and rollback_uid != current_champion_uid:
            _fail("PROMOTION_ROLLBACK_NOT_CURRENT_CHAMPION")
        if (
            decision["previous_champion_version_uid"]
            != current_champion_uid
        ):
            _fail("PROMOTION_PREVIOUS_CHAMPION_MISMATCH")

        promotable = _validate_evidence_closure(
            bundle,
            registry_view,
            evidence,
            scorecards_by_digest,
            eval_runs_by_digest,
            expected_bundle_digest,
        )
        if (
            decision["candidate_model_snapshot_digest"]
            != evidence["candidate_model_snapshot_digest"]
            or decision["baseline_model_snapshot_digest"]
            != evidence["baseline_model_snapshot_digest"]
            or decision["hard_gates_passed"]
            != evidence["hard_gates_passed"]
            or decision["known_risk_codes"]
            != evidence["known_risk_codes"]
        ):
            _fail("PROMOTION_DECISION_EVIDENCE_CLAIM_MISMATCH")
        _sorted_unique(
            decision["known_risk_codes"],
            "PROMOTION_RISK_CODE_ORDER_INVALID",
        )
        _sorted_unique(
            decision["reason_codes"],
            "PROMOTION_REASON_CODE_ORDER_INVALID",
        )

        expected_notification = decision["impact"] == "MAJOR"
        if (
            decision["major_change"] != expected_notification
            or evidence["notification_required"] != expected_notification
            or decision["notification_receipt_digest"]
            != evidence["notification_receipt_digest"]
            or decision["emergency_containment"]
        ):
            _fail("PROMOTION_NOTIFICATION_OR_EMERGENCY_SEMANTICS_INVALID")

        if action == "PROMOTE":
            if (
                not promotable
                or decision["stage"] != "CHAMPION"
                or decision["to_status"] != "CHAMPION"
                or decision["resulting_champion_version_uid"]
                != candidate_uid
            ):
                _fail("PROMOTION_GATE_BYPASS_FORBIDDEN")
            champions[scope_uid] = candidate_uid
            promote_count += 1
        else:
            if (
                decision["stage"] != "REJECTED"
                or decision["to_status"] != "QUARANTINED"
                or decision["resulting_champion_version_uid"]
                != current_champion_uid
            ):
                _fail("PROMOTION_REJECT_TRANSITION_INVALID")
            reject_count += 1

        if len(champions.values()) != len(set(champions.values())):
            _fail("PROMOTION_MULTIPLE_CHAMPIONS_PER_SCOPE")
        terminal_candidates.add(candidate_uid)
        decision_uids.append(decision_uid)
        decision_digests.append(decision_digest)

    if set(evidences) != used_evidence_digests:
        _fail("PROMOTION_UNUSED_EVIDENCE_FORBIDDEN")
    if decisions:
        referenced_scorecards = {
            ref["artifact_digest"]
            for evidence in evidences.values()
            for ref in evidence["scorecard_refs"]
        }
        referenced_eval_runs = {
            ref["artifact_digest"]
            for evidence in evidences.values()
            for ref in evidence["eval_run_refs"]
        }
        if (
            set(scorecards_by_digest) != referenced_scorecards
            or set(eval_runs_by_digest) != referenced_eval_runs
        ):
            _fail("PROMOTION_UNUSED_EVALUATION_ARTIFACT_FORBIDDEN")
    elif scorecards_by_digest or eval_runs_by_digest:
        _fail("PROMOTION_EVALUATION_ARTIFACT_WITHOUT_DECISION")

    return PromotionLedgerView(
        decision_uids=tuple(decision_uids),
        decision_digests=tuple(decision_digests),
        champion_by_scope=tuple(
            sorted(
                champions.items(),
                key=lambda item: item[0].encode("ascii"),
            )
        ),
        terminal_candidate_version_uids=tuple(
            sorted(
                terminal_candidates,
                key=lambda value: value.encode("ascii"),
            )
        ),
        last_decided_at=last_decided_at,
        ledger_digest=promotion_ledger_digest(
            registry_view.registry_snapshot_digest,
            decision_digests,
        ),
        promote_count=promote_count,
        reject_count=reject_count,
    )


def append_promotion_decision(
    bundle: ContractBundle,
    registry_view: PromotionRegistryView,
    *,
    evidence_by_digest: Mapping[str, Mapping[str, Any]],
    scorecards_by_digest: Mapping[str, Mapping[str, Any]],
    eval_runs_by_digest: Mapping[str, Mapping[str, Any]],
    existing_decisions: Sequence[Mapping[str, Any]],
    decision: Mapping[str, Any],
    expected_predecessor_ledger_digest: str,
    expected_bundle_digest: str,
) -> PromotionAppendResult:
    """Validate a successor event and return immutable append material."""

    combined = tuple(existing_decisions) + (decision,)
    view = replay_promotion_ledger(
        bundle,
        registry_view,
        evidence_by_digest=evidence_by_digest,
        scorecards_by_digest=scorecards_by_digest,
        eval_runs_by_digest=eval_runs_by_digest,
        decisions=combined,
        expected_bundle_digest=expected_bundle_digest,
    )
    predecessor_ledger_digest = promotion_ledger_digest(
        registry_view.registry_snapshot_digest,
        view.decision_digests[:-1],
    )
    if (
        not isinstance(expected_predecessor_ledger_digest, str)
        or predecessor_ledger_digest
        != expected_predecessor_ledger_digest
    ):
        _fail("PROMOTION_PREDECESSOR_LEDGER_DIGEST_MISMATCH")
    return PromotionAppendResult(
        canonical_decision_bytes=canonicalize_object(decision),
        decision_digest=decision["decision_digest"],
        predecessor_ledger_digest=predecessor_ledger_digest,
        ledger_view=view,
    )
