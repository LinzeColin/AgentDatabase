"""Pure cold-start reconstruction contract for Mechanism Task Pack M-069.

The module accepts only already-loaded public-safe objects and exact raw
digests. It has no filesystem, Git, network, clock, state, notification,
publisher, activation, or verifier capability.
"""

from __future__ import annotations

import copy
import hashlib
import re
from typing import Any, Dict, Mapping, NamedTuple, Optional, Sequence, Tuple

from CodexSkills.governance.tools.canonical_json import (
    canonical_digest,
    parse_json_bytes,
)


PROTOCOL_REVISION = (
    "urn:linzecolin:agentdatabase:skillops:protocol:cross-pack:v1"
)
TASK_PACK_REVISION = "v0.0.0.2"
TASK_PACK_TASK_COUNT = 69
FINAL_TASK_ID = "M-069"
M068_GIT_OBJECT_ID = (
    "sha1:e984ad6e8ed85b51bd2f8f5739f49dbc146eb8d7"
)
REVIEW_BASE_GIT_OBJECT_ID = (
    "sha1:1fb0f80a3f90bf1e1dfc41d04556f7088b004b2d"
)
CANDIDATE_BUNDLE_DIGEST = (
    "36f0c66dd54d36365700a13f614a8c9bfa9619fb7c532af77566a858175b835e"
)
EVIDENCE_INDEX_SCHEMA_ID = (
    "urn:linzecolin:agentdatabase:skillops:schema:"
    "mechanism-evidence-index:v1"
)
COLD_START_HANDOFF_SCHEMA_ID = (
    "urn:linzecolin:agentdatabase:skillops:schema:"
    "cold-start-handoff:v1"
)
EVIDENCE_INDEX_PATH = (
    "CodexSkills/governance/release/cold_start/evidence-index.json"
)
MACHINE_HANDOFF_PATH = (
    "CodexSkills/governance/release/cold_start/cold-start-handoff.json"
)
HUMAN_HANDOFF_PATH = "CodexSkills/HANDOFF.md"
CHANGELOG_PATH = "CodexSkills/CHANGELOG.md"
SELF_POINTER = "/artifact_digest"
INDEX_SELF_POINTER = "/index_digest"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GIT_OBJECT_RE = re.compile(r"^sha1:[0-9a-f]{40}$")


class EvidenceSpec(NamedTuple):
    code: str
    path: str
    source_git_object_id: str
    content_digest: str
    self_digest_pointer: Optional[str]
    semantic_digest: Optional[str]
    status: Optional[str]
    schema_version: Optional[str]


EVIDENCE_SPECS = (
    EvidenceSpec(
        "ACTIVATION_CONTROL",
        "CodexSkills/governance/activation/control-interface.json",
        "sha1:2091d89fc2cbd2ff8c82375a3820bb829d0fa96d",
        "8caf7e5dbb922714c3afa39040e55b8a83015ea0f02de153e19cc3010b0e0e1a",
        None,
        None,
        "DRAFT_NON_ACTIVE",
        None,
    ),
    EvidenceSpec(
        "ACTIVE_TREE_365D",
        "CodexSkills/governance/retention/git-active-tree-365d-readiness.json",
        "sha1:039f3844b36961f1d8432b9c0d86d6cda408f430",
        "91592f339854fb205993e96a67698d7b6ce8fc54afd3b226f3090dfd49ab86f2",
        "/artifact_digest",
        "0bb6c1fb335115785495805ed001d6747a311dd1cbee335547beccaf8501df88",
        "DRAFT_NON_ACTIVE_GIT_ACTIVE_TREE_365D_READY",
        "urn:linzecolin:agentdatabase:skillops:schema:"
        "git-active-tree-365d-readiness:v1",
    ),
    EvidenceSpec(
        "AUTO_RUNTIME_INTERFACE",
        "CodexSkills/registry/auto/runtime-interface.json",
        "sha1:1c829553996c792e46cedc4570b30545fba9e071",
        "3e91bf41c9550fa48264db3b72ee102b0acec65b883374d2735fbd7169801d9e",
        None,
        None,
        "DRAFT_NON_ACTIVE",
        None,
    ),
    EvidenceSpec(
        "BOUND_RESOLVER_INTERFACE",
        "CodexSkills/governance/registry/resolver-interface.json",
        "sha1:98e193e74991346d266bdd94ae720c32f25dfb47",
        "f83032d5cb8c9dda9c6e903bb9dc5bf4f2a5de8bd687beeb010047f9e6b3ba2a",
        "/artifact_digest",
        "d75e9b1d112b95d7ce0c5b9579140e78847ebc228b7347df7340e211522c0077",
        "DRAFT_NON_ACTIVE_TELEIOSIS_PARITY_MATERIALIZED",
        None,
    ),
    EvidenceSpec(
        "CANDIDATE_BUNDLE",
        "CodexSkills/governance/bundles/schema-bundle-manifest.v1.json",
        "sha1:5ee37d7499c62ec19381dac7eb95cb12743ad2d5",
        "66ad125629cab71739ff2bc266219f995f7a45998936ca720c6db678ee77e65a",
        "/bundle_digest",
        CANDIDATE_BUNDLE_DIGEST,
        None,
        "urn:linzecolin:agentdatabase:skillops:schema:"
        "schema-bundle-manifest:v1",
    ),
    EvidenceSpec(
        "CAPACITY_BUDGETS",
        "CodexSkills/governance/performance/performance-capacity-readiness.json",
        "sha1:9968a706dd729839efa707bf64ef893c44d324bd",
        "000154c32d895b35960cadbad80582c09121ee1103a31a63577ad8a6cf5b1a3d",
        "/artifact_digest",
        "9cd49a73c30729de3b0443e6a8024035cdc138a8e2d690f720def0d4400b881e",
        "DRAFT_NON_ACTIVE_PERFORMANCE_CAPACITY_BUDGETS_IMPLEMENTED_UNCALIBRATED",
        "urn:linzecolin:agentdatabase:skillops:schema:"
        "performance-capacity-readiness:v1",
    ),
    EvidenceSpec(
        "CONSUMER_CONFIG",
        "OpenAIDatabase/config/evaluation/skill_run_consumer.json",
        "sha1:91a12e48351be3ee05ec23ef61aec81056b02014",
        "189a47300fc1aa6012e87feb6184833cb717cdbe2b9dc9be6db89197f579939c",
        None,
        None,
        "DRAFT_NON_ACTIVE_CONSUMER_READY",
        None,
    ),
    EvidenceSpec(
        "EVALUATOR_PROTECTION",
        "CodexSkills/governance/release/evaluator-release-protection-readiness.json",
        "sha1:36ce92ddaf2f5cde5b027317e1aaf21bc0f019db",
        "344eaace3906bc03ede4520512887939c10fb37cea073ddbac306dccfd364f5f",
        "/artifact_digest",
        "b77cc4f395f4247b43fbeceee88ab34ccc2bae4ef5d2899a9932856b0cbebbb8",
        "DRAFT_NON_ACTIVE_EVALUATOR_RELEASE_POLICY_PROTECTION_READY",
        "urn:linzecolin:agentdatabase:skillops:schema:"
        "evaluator-release-protection-readiness:v1",
    ),
    EvidenceSpec(
        "FAILURE_TO_TEST",
        "CodexSkills/governance/evaluation/failure-to-test-readiness.json",
        "sha1:6cf5beae7c50c3fb860926df670dcc5fc33890e3",
        "ab243507d8384a849ea9488e1a6d717c87f12195b7397300658c83d2c6e3eaf6",
        "/artifact_digest",
        "0fd20eef7a9aad02fe5301f28a3bbd91ee352dc431f9832fd372601e1425c496",
        "DRAFT_NON_ACTIVE_FAILURE_TO_TEST_CONVERSION_READY_SHADOW_FIXTURE_ONLY",
        "urn:linzecolin:agentdatabase:skillops:schema:"
        "failure-to-test-readiness:v1",
    ),
    EvidenceSpec(
        "FRESHNESS_MONITOR",
        "CodexSkills/governance/monitoring/freshness-drift-readiness.json",
        "sha1:3d3c202ee629d79eadfb027da131e1afcb88a1f2",
        "416beacd6a72d3d5517211a3758452228bd445ab10fc887928b0575e2865d812",
        "/artifact_digest",
        "8864203d59f925f8f3110ff1e779ebdb19d26818a337de764596de2de1afa96d",
        "DRAFT_NON_ACTIVE_FRESHNESS_DRIFT_MONITOR_READY",
        "urn:linzecolin:agentdatabase:skillops:schema:"
        "freshness-drift-readiness:v1",
    ),
    EvidenceSpec(
        "GIT_HISTORY_DISCLOSURE",
        "CodexSkills/governance/retention/git-history-persistence-readiness.json",
        "sha1:9b8f20f3ab97a7ec06aedfbe53670569ac036f9b",
        "3cb7f9b6c5528f6c7415fa45c53da1fd38f2dbb7561f8d123b56769e96db567f",
        "/artifact_digest",
        "b94cfab93ad5383dda32b45506f267cf126c7400925fd4d371278bde392a007e",
        "DRAFT_NON_ACTIVE_GIT_HISTORY_PERSISTENCE_DISCLOSURE_READY",
        "urn:linzecolin:agentdatabase:skillops:schema:"
        "git-history-persistence-readiness:v1",
    ),
    EvidenceSpec(
        "MANAGED_RAW_72H",
        "CodexSkills/governance/retention/managed-raw-72h-readiness.json",
        "sha1:b023ac71c5c7852a95f4b87a56981fe7a42c32d9",
        "d60a71554ffbe4bde30fbd639e723086598df22b69b4ceee04b070dd4ddb6e0f",
        "/artifact_digest",
        "dad952d9df1523bb63765dc028a4f3609251834dcb52dfa06a085341f555f774",
        "DRAFT_NON_ACTIVE_MANAGED_RAW_72H_POLICY_READY",
        "urn:linzecolin:agentdatabase:skillops:schema:"
        "managed-raw-72h-readiness:v1",
    ),
    EvidenceSpec(
        "MIGRATION_CUTOVER",
        "CodexSkills/governance/migration/"
        "read-only-migration-cutover-readiness.json",
        "sha1:0b59768ed3697a1cd3c93afda70d96b9034f99ef",
        "839b363d904116d8657f78e10b53a1cd11c86f1d64f06064090e5a71b24ca02c",
        "/artifact_digest",
        "049809b3292f5591fc63f899c2172e67da66bb0a152998e04a341bda401d1228",
        "DRAFT_NON_ACTIVE_READ_ONLY_MIGRATION_CUTOVER_IMPLEMENTED_BLOCKED",
        "urn:linzecolin:agentdatabase:skillops:schema:"
        "read-only-migration-cutover-readiness:v1",
    ),
    EvidenceSpec(
        "MIRROR_INDEX",
        "CodexSkills/index.json",
        "sha1:75859023610301354d3e41e265a7a6b154a20a09",
        "f3932c7297668415469064086f5f98830a75077a1b03ee96bb57952dfd1d09bd",
        None,
        None,
        None,
        None,
    ),
    EvidenceSpec(
        "OPERATIONAL_DASHBOARD",
        "CodexSkills/governance/monitoring/operational-dashboard-readiness.json",
        "sha1:9f7cebdcdeae54c0732f73d8bf8ce11690f4145b",
        "342359e4194346b0b41cd75fd14bda456f3ec85fc9d8a59656cfa18a51188f12",
        "/artifact_digest",
        "9b565de75a721d670a623486d4410d7c3876db3c0d89fdebc999f4cb93fba580",
        "DRAFT_NON_ACTIVE_OPERATIONAL_DASHBOARD_READY_ALERTS_PRESENT",
        "urn:linzecolin:agentdatabase:skillops:schema:"
        "operational-dashboard-readiness:v1",
    ),
    EvidenceSpec(
        "PROMOTION_CONTROLLER",
        "CodexSkills/governance/promotion/controller-readiness.json",
        "sha1:3cc02c15359d5204ad34fc9c20edbc02ec3802f0",
        "d54d577bf53e155c1eb6215db388d9f7939f91e21d6af938242c49928b44d1ae",
        "/artifact_digest",
        "152afb30ca521bdbf6fe954f0afd408cc238119183d55b782c1ffcfdbadff53b",
        "DRAFT_NON_ACTIVE_PROMOTION_CONTROLLER_READY",
        "urn:linzecolin:agentdatabase:skillops:schema:"
        "promotion-controller-readiness:v1",
    ),
    EvidenceSpec(
        "PROTECTED_RAW_BOUNDARY",
        "CodexSkills/governance/retention/"
        "protected-local-managed-raw-readiness.json",
        "sha1:21235d49fca818b74677172711cfe279d2da68a6",
        "6376e6776b6f23cf45080f5d3a9191fcdf0238168032b14356da8b88dd45bef4",
        "/artifact_digest",
        "b7c1ba479d0a47b97cb00b0556b2bf5db5b035bc156c9ae4e3bdc71337707080",
        "DRAFT_NON_ACTIVE_PROTECTED_LOCAL_MANAGED_RAW_BOUNDARY_READY",
        "urn:linzecolin:agentdatabase:skillops:schema:"
        "protected-local-managed-raw-readiness:v1",
    ),
    EvidenceSpec(
        "PUBLIC_SAFE_QUEUE",
        "CodexSkills/governance/retention/"
        "public-safe-queue-lifecycle-readiness.json",
        "sha1:72fd98353fa7065e520067c221e8689435dffd4c",
        "cf7193aa6057647ad48dd7c74ce133faaa138a49311322d13599f8329525712f",
        "/artifact_digest",
        "96f9ba8496f3e6496924c5c7cfb2536c3aeb694eacef202758365046d2093373",
        "DRAFT_NON_ACTIVE_PUBLIC_SAFE_QUEUE_LIFECYCLE_READY",
        "urn:linzecolin:agentdatabase:skillops:schema:"
        "public-safe-queue-lifecycle-readiness:v1",
    ),
    EvidenceSpec(
        "REGISTRY_SNAPSHOT",
        "CodexSkills/registry/_global/registry-snapshot.v1.json",
        "sha1:98e193e74991346d266bdd94ae720c32f25dfb47",
        "ed5fb74fa88a2f1115a716be5e63f683d206c10d3d0a2005230d4c33d4c12c98",
        "/registry_snapshot_digest",
        "7b5a74bd459a4737299444b68439c1799ba8a2159032636a24a987113eee9d12",
        "REGISTERED",
        "urn:linzecolin:agentdatabase:skillops:schema:"
        "registry-snapshot:v1",
    ),
    EvidenceSpec(
        "RELEASE_FOUNDATION",
        "CodexSkills/governance/release/foundation-interface.json",
        "sha1:27d93b4ab24cbb88a35412fa969821bc46ae8674",
        "274ace52127491ed25687dd3c961eeb8594fe40ccff5543e5da6dfa209356c58",
        "/artifact_digest",
        "681ce19f993878d578b2d636dbede007cdf7acd7e73986e3253571b875f9e74b",
        "DRAFT_NON_ACTIVE_POLICY_RECONCILIATION_REQUIRED",
        "urn:linzecolin:agentdatabase:skillops:schema:"
        "release-foundation-interface:v1",
    ),
    EvidenceSpec(
        "REPRESENTATIVE_PILOTS",
        "CodexSkills/governance/pilots/"
        "three-representative-pilots-readiness.json",
        M068_GIT_OBJECT_ID,
        "3cd985ca1d9a96aa36d63928db074e68c1af65c6240cdd4ecec675cb95b5f8a6",
        "/artifact_digest",
        "19ce322a54343fc0640cdb58f023b51662530919f64c8a49c3cfc653de78df8e",
        "DRAFT_NON_ACTIVE_THREE_REPRESENTATIVE_PILOTS_"
        "SHADOW_COMPLETE_PRODUCTION_BLOCKED",
        "urn:linzecolin:agentdatabase:skillops:schema:"
        "three-representative-pilots-readiness:v1",
    ),
    EvidenceSpec(
        "ROLLBACK_CONTROLLER",
        "CodexSkills/governance/promotion/rollback-controller-readiness.json",
        "sha1:6d263e02ca6104abca5ae930b5eaa0944d8d5960",
        "9ecdbc1f5cd103d6420cdd2d81b4ab14e94ce50668c6fabfe96ba05a9fd22494",
        "/artifact_digest",
        "3cf47b465f46a458b2c16b57599462ca6638076cb32ab0e57ab2c86d6c41a93b",
        "DRAFT_NON_ACTIVE_ROLLBACK_REVOCATION_CONTROLLER_READY",
        "urn:linzecolin:agentdatabase:skillops:schema:"
        "rollback-controller-readiness:v1",
    ),
    EvidenceSpec(
        "VERSION_POLICY_V3_READINESS",
        "CodexSkills/governance/release/version_policy_v3/"
        "consumer-readiness.json",
        "sha1:0348e0bda8ca381bbdaca5d86a7c2ddfdc4b685f",
        "6866a2ca9485d57d065c4954e8452b567c37b738bc32397d17316dfceb623632",
        "/artifact_digest",
        "dec3be6196954320a24a5b9a87c39ac9c8a3ec530216a5b1650797f90046b532",
        "DRAFT_NON_ACTIVE_MECHANISM_CONSUMER_READY",
        "urn:linzecolin:agentdatabase:skillops:schema:"
        "version-policy-consumer-readiness:v1",
    ),
)

BLOCKER_CODES = (
    "ACTIVATION_CONTROL_INTERFACE_SEMANTIC_MISMATCH",
    "ACTIVE_TRUST_ABSENT",
    "AUTO_REGISTRY_MIRROR_SKILL_COUNT_DRIFT",
    "BOUND_REFERENCE_RESOLVER_RUNTIME_LOCAL_DRIFT",
    "EXTERNAL_GMAIL_STATE_READINESS_UNVERIFIED",
    "PRODUCTION_PILOTS_NOT_RUN",
    "SCHEDULE_AUTHORITY_UNRESOLVED",
)


class ColdStartReviewError(ValueError):
    """A cold-start input or reconstruction invariant failed closed."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _fail(code: str) -> None:
    raise ColdStartReviewError(code)


def _validate_spec_set() -> None:
    codes = [spec.code for spec in EVIDENCE_SPECS]
    paths = [spec.path for spec in EVIDENCE_SPECS]
    if codes != sorted(codes) or len(codes) != len(set(codes)):
        _fail("COLD_START_EVIDENCE_CODES_INVALID")
    if len(paths) != len(set(paths)):
        _fail("COLD_START_EVIDENCE_PATHS_DUPLICATE")
    for spec in EVIDENCE_SPECS:
        if (
            SHA256_RE.fullmatch(spec.content_digest) is None
            or GIT_OBJECT_RE.fullmatch(spec.source_git_object_id) is None
            or (
                spec.semantic_digest is not None
                and SHA256_RE.fullmatch(spec.semantic_digest) is None
            )
            or ((spec.self_digest_pointer is None) != (spec.semantic_digest is None))
        ):
            _fail("COLD_START_EVIDENCE_SPEC_INVALID:" + spec.code)


def build_evidence_index(
    raw_documents: Mapping[str, bytes],
) -> Mapping[str, Any]:
    """Reconstruct the exact public-safe evidence index."""

    _validate_spec_set()
    expected_codes = {spec.code for spec in EVIDENCE_SPECS}
    if (
        not isinstance(raw_documents, dict)
        or set(raw_documents) != expected_codes
    ):
        _fail("COLD_START_EVIDENCE_INPUT_SET_INCOMPLETE")
    entries = []
    for spec in EVIDENCE_SPECS:
        raw = raw_documents[spec.code]
        if not isinstance(raw, bytes):
            _fail("COLD_START_EVIDENCE_RAW_INVALID:" + spec.code)
        try:
            document = parse_json_bytes(raw)
        except Exception as exc:
            raise ColdStartReviewError(
                "COLD_START_EVIDENCE_JSON_INVALID:" + spec.code
            ) from exc
        if not isinstance(document, dict):
            _fail("COLD_START_EVIDENCE_DOCUMENT_INVALID:" + spec.code)
        if hashlib.sha256(raw).hexdigest() != spec.content_digest:
            _fail("COLD_START_EVIDENCE_RAW_DIGEST_MISMATCH:" + spec.code)
        if spec.self_digest_pointer is not None:
            if (
                document.get(spec.self_digest_pointer[1:])
                != spec.semantic_digest
                or canonical_digest(document, spec.self_digest_pointer)
                != spec.semantic_digest
            ):
                _fail("COLD_START_EVIDENCE_SELF_DIGEST_MISMATCH:" + spec.code)
        if spec.status is not None and document.get("status") != spec.status:
            _fail("COLD_START_EVIDENCE_STATUS_MISMATCH:" + spec.code)
        if (
            spec.schema_version is not None
            and document.get("schema_version") != spec.schema_version
        ):
            _fail("COLD_START_EVIDENCE_SCHEMA_MISMATCH:" + spec.code)
        if spec.code == "MIRROR_INDEX" and (
            document.get("schema") != "codex_skills_index.v2"
            or document.get("skill_instance_count") != 90
            or document.get("unique_slug_count") != 75
        ):
            _fail("COLD_START_MIRROR_INDEX_STATE_MISMATCH")
        if spec.code == "CONSUMER_CONFIG" and (
            document.get("schema_version")
            != "openai_database.skill_run_consumer.v2"
        ):
            _fail("COLD_START_CONSUMER_SCHEMA_MISMATCH")
        entries.append(
            {
                "evidence_code": spec.code,
                "canonical_path": spec.path,
                "verified_git_object_id": spec.source_git_object_id,
                "content_digest": spec.content_digest,
                "digest_basis": "RAW_BYTES",
                "self_digest_pointer": spec.self_digest_pointer,
                "artifact_digest": spec.semantic_digest,
                "status": spec.status,
                "schema_version": spec.schema_version,
                "owner_plane": (
                    "AUTO"
                    if spec.code
                    in ("AUTO_RUNTIME_INTERFACE", "MIRROR_INDEX")
                    else (
                        "CONSUMER"
                        if spec.code == "CONSUMER_CONFIG"
                        else "MECHANISM"
                    )
                ),
            }
        )
    value: Dict[str, Any] = {
        "schema_version": EVIDENCE_INDEX_SCHEMA_ID,
        "protocol_revision": PROTOCOL_REVISION,
        "task_pack_revision": TASK_PACK_REVISION,
        "status": "FINAL_MECHANISM_EVIDENCE_INDEX_NON_ACTIVE",
        "review_base": {
            "verified_git_object_id": REVIEW_BASE_GIT_OBJECT_ID,
        },
        "bundle_digest": CANDIDATE_BUNDLE_DIGEST,
        "entries": entries,
        "coverage": {
            "evidence_entry_count": len(entries),
            "task_pack_task_count": TASK_PACK_TASK_COUNT,
            "final_task_id": FINAL_TASK_ID,
            "chat_context_required": False,
            "repository_paths_unique": True,
            "source_objects_external_to_index": True,
            "production_readiness_claimed": False,
        },
        "index_digest": "0" * 64,
    }
    value["index_digest"] = canonical_digest(value, INDEX_SELF_POINTER)
    return value


def validate_evidence_index(
    value: Mapping[str, Any],
    raw_documents: Mapping[str, bytes],
) -> None:
    if value != build_evidence_index(raw_documents):
        _fail("COLD_START_EVIDENCE_INDEX_RECOMPUTATION_MISMATCH")


def build_handoff_core(index: Mapping[str, Any]) -> Mapping[str, Any]:
    """Build the state a new agent must recover without chat context."""

    if (
        not isinstance(index, dict)
        or index.get("schema_version") != EVIDENCE_INDEX_SCHEMA_ID
        or index.get("index_digest")
        != canonical_digest(index, INDEX_SELF_POINTER)
        or index.get("review_base", {}).get("verified_git_object_id")
        != REVIEW_BASE_GIT_OBJECT_ID
        or len(index.get("entries", ())) != len(EVIDENCE_SPECS)
    ):
        _fail("COLD_START_INDEX_NOT_TRUSTED")
    return {
        "status": (
            "DRAFT_NON_ACTIVE_MECHANISM_TASKPACK_RELEASE_REVIEW_"
            "COMPLETE_WITH_BLOCKERS"
        ),
        "phase": "MECHANISM_COLD_START_HANDOFF_RELEASE_REVIEW",
        "task_contract": {
            "implemented_task_ids": [FINAL_TASK_ID],
            "dependency_task_ids": ["M-068"],
            "task_pack_task_count": TASK_PACK_TASK_COUNT,
            "task_pack_last_task_id": FINAL_TASK_ID,
            "m070_exists_in_task_pack": False,
            "required_output_codes": [
                "VALIDATED_HANDOFF",
                "CHANGELOG",
                "EVIDENCE_INDEX",
            ],
            "done_gate": (
                "NEW_AGENT_RECONSTRUCTS_EXACT_STATE_WITHOUT_CHAT_CONTEXT"
            ),
            "done_gate_satisfied": True,
        },
        "source_trust": {
            "review_base": {
                "verified_git_object_id": REVIEW_BASE_GIT_OBJECT_ID,
            },
            "repository_self_report_is_not_trust_root": True,
            "evidence_index": {
                "canonical_path": EVIDENCE_INDEX_PATH,
                "artifact_digest": index["index_digest"],
            },
            "candidate": {
                "verified_git_object_id": (
                    "sha1:5ee37d7499c62ec19381dac7eb95cb12743ad2d5"
                ),
                "canonical_path": (
                    "CodexSkills/governance/bundles/"
                    "schema-bundle-manifest.v1.json"
                ),
                "bundle_digest": CANDIDATE_BUNDLE_DIGEST,
                "schema_count": 31,
                "policy_count": 5,
                "mode": "CANDIDATE",
            },
        },
        "current_state": {
            "mechanism_final_task_review_complete": True,
            "mechanism_production_ready": False,
            "active_trust_present": False,
            "version_file_present": False,
            "canonical_publication_permitted": False,
            "activation_permitted": False,
            "schedule_authority_resolved": False,
            "schedule_candidates_local": ["04:15", "05:30"],
            "registry_identity_count": 89,
            "registry_instance_count": 89,
            "registry_version_count": 89,
            "binding_eligible_version_count": 0,
            "repository_mirror_skill_instance_count": 90,
            "registry_mirror_parity": False,
            "pilot_count": 3,
            "shadow_pilot_cycle_count": 9,
            "production_pilots_executed": False,
            "external_gmail_state_ready": False,
            "auto_runtime_state_write_permitted": False,
        },
        "validation_baseline": {
            "targeted_m068_tests": {
                "tests_run": 20,
                "failures": 0,
                "errors": 0,
            },
            "complete_mechanism": {
                "tests_run": 307,
                "failures": 0,
                "errors": 0,
            },
            "schema_sets": {
                "base": 21,
                "candidate_compatible": 41,
                "version": 24,
                "repository_closure_before_m069": 85,
            },
            "candidate_trust": {"schemas": 31, "policies": 5},
            "consumer": {
                "tests_run": 23,
                "failures": 0,
                "errors": 0,
                "canonical_publication_permitted": False,
            },
            "auto_known_transition": {
                "tests_run": 200,
                "failures": 5,
                "errors": 20,
            },
            "fault_privacy_known_transition": [
                {
                    "seed": 271828,
                    "tests_run": 149,
                    "failures": 5,
                    "errors": 25,
                },
                {
                    "seed": 314159,
                    "tests_run": 149,
                    "failures": 5,
                    "errors": 25,
                },
            ],
        },
        "blocker_codes": list(BLOCKER_CODES),
        "release_decision": {
            "outcome": "STOP_BEFORE_OWNER_FRESH_VERIFIER",
            "owner_fresh_verifier_required": True,
            "verifier_called_during_development": False,
            "exact_next_action": "OWNER_SELECT_AND_RUN_FRESH_VERIFIER",
            "follow_on_mechanism_taskpack_phase_exists": False,
        },
        "nonmutation": {
            "auto_plane_unchanged": True,
            "openai_database_unchanged": True,
            "candidate_bundle_unchanged": True,
            "registry_unchanged": True,
            "source_roots_unchanged": True,
            "state_or_watermark_written": False,
            "notification_sent": False,
            "migration_executed": False,
            "canonical_artifact_published": False,
            "activation_executed": False,
            "automation_or_app_changed": False,
            "version_file_created": False,
        },
    }


def build_machine_handoff(
    index: Mapping[str, Any],
    human_handoff_digest: str,
    changelog_digest: str,
) -> Mapping[str, Any]:
    core = build_handoff_core(index)
    for value, code in (
        (human_handoff_digest, "COLD_START_HUMAN_HANDOFF_DIGEST_INVALID"),
        (changelog_digest, "COLD_START_CHANGELOG_DIGEST_INVALID"),
    ):
        if not isinstance(value, str) or SHA256_RE.fullmatch(value) is None:
            _fail(code)
    result: Dict[str, Any] = {
        "schema_version": COLD_START_HANDOFF_SCHEMA_ID,
        "protocol_revision": PROTOCOL_REVISION,
        "task_pack_revision": TASK_PACK_REVISION,
        "bundle_digest": CANDIDATE_BUNDLE_DIGEST,
        **copy.deepcopy(core),
        "documents": {
            "human_handoff": {
                "canonical_path": HUMAN_HANDOFF_PATH,
                "content_digest": human_handoff_digest,
                "digest_basis": "RAW_BYTES",
            },
            "changelog": {
                "canonical_path": CHANGELOG_PATH,
                "content_digest": changelog_digest,
                "digest_basis": "RAW_BYTES",
            },
            "machine_handoff": {
                "canonical_path": MACHINE_HANDOFF_PATH,
                "self_digest_pointer": SELF_POINTER,
            },
        },
        "artifact_digest": "0" * 64,
    }
    result["artifact_digest"] = canonical_digest(result, SELF_POINTER)
    return result


def validate_machine_handoff(
    value: Mapping[str, Any],
    index: Mapping[str, Any],
    human_handoff_digest: str,
    changelog_digest: str,
) -> None:
    if value != build_machine_handoff(
        index,
        human_handoff_digest,
        changelog_digest,
    ):
        _fail("COLD_START_HANDOFF_RECOMPUTATION_MISMATCH")
