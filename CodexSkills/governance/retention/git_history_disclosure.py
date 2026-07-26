"""Pure M-064 Git-history persistence disclosure contract.

The contract distinguishes ordinary removal from a later Git current tree
from hard erasure.  It validates fixed operator and user disclosures and
rejects affirmative claims that Git history, forks, clones, caches, archives,
or provider backups were permanently erased.

This module receives immutable objects and bytes only.  It has no filesystem,
Git, network, state, queue, lock, publisher, deletion, history-rewrite, or
repository-rotation capability.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any, Dict, Mapping, Sequence, Tuple

from CodexSkills.governance.tools.canonical_json import canonical_digest


SCHEMA_PREFIX = "urn:linzecolin:agentdatabase:skillops:schema:"
PROTOCOL_REVISION = (
    "urn:linzecolin:agentdatabase:skillops:protocol:cross-pack:v1"
)
DISCLOSURE_SCHEMA_ID = (
    SCHEMA_PREFIX + "git-history-persistence-disclosure:v1"
)
DISCLOSURE_SELF_POINTER = "/artifact_digest"
RETENTION_POLICY_ID = (
    "urn:linzecolin:agentdatabase:skillops:policy:retention:v3"
)
RETENTION_POLICY_SHA256 = (
    "bcad1e50a847e040d1350ca2fd977503b4ae642deabd727266e9dbbd26acb7ce"
)
ACTIVE_TREE_RETENTION_SECONDS = 365 * 24 * 60 * 60
MAX_DISCLOSURE_SURFACE_BYTES = 512 * 1024

OPERATOR_DISCLOSURE_EN = (
    "The 365-day rule governs full-fidelity artifacts in the Git current "
    "tree only. After the strict boundary, an eligible shard may be removed "
    "from a later current tree, while Git history, forks, clones, caches, "
    "archives, and provider backups can retain the bytes indefinitely."
)
OPERATOR_DISCLOSURE_ZH = (
    "365 天规则只约束 Git 当前树中的全保真工件。严格超过边界后，符合条件的 "
    "shard 可以从后续当前树移除，但 Git 历史、fork、clone、cache、archive "
    "和服务商备份仍可能无限期保留这些字节。"
)
USER_DISCLOSURE_EN = (
    "A retention receipt proves only the audited current-tree transition. "
    "It does not prove permanent deletion, removal from Git history or other "
    "copies, or irrecoverability."
)
USER_DISCLOSURE_ZH = (
    "retention receipt 只证明经审计的当前树转换；它不证明永久删除、不证明已从 "
    "Git 历史或其他副本移除，也不证明数据不可恢复。"
)
HARD_ERASURE_DISCLOSURE_EN = (
    "This mechanism never claims hard deletion. Hard erasure would require "
    "a separate owner-authorized MAJOR design for repository rotation or "
    "private storage, and still cannot guarantee deletion of third-party "
    "copies outside the owner's control."
)
HARD_ERASURE_DISCLOSURE_ZH = (
    "本机制绝不声称完成硬删除。硬擦除必须另行取得 Owner 授权，并以 MAJOR "
    "级方案设计仓库轮换或私有存储；即便如此，也不能保证删除 Owner 控制范围外"
    "的第三方副本。"
)

REQUIRED_MARKDOWN_HEADINGS = (
    "# Git-history persistence disclosure / Git 历史持久性披露",
    "## Operator disclosure / 操作方披露",
    "## User disclosure / 用户披露",
    "## Hard-erasure boundary / 硬擦除边界",
)
REQUIRED_DISCLOSURE_TEXT = (
    OPERATOR_DISCLOSURE_EN,
    OPERATOR_DISCLOSURE_ZH,
    USER_DISCLOSURE_EN,
    USER_DISCLOSURE_ZH,
    HARD_ERASURE_DISCLOSURE_EN,
    HARD_ERASURE_DISCLOSURE_ZH,
)

_POSITIVE_HARD_ERASURE_PATTERNS: Tuple[Tuple[str, re.Pattern[str]], ...] = (
    (
        "HARD_DELETION_COMPLETION_CLAIM",
        re.compile(
            r"\bhard[- ]delet(?:ion|e)\s+(?:is\s+)?"
            r"(?:complete|completed|done|guaranteed)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "PERMANENT_DELETION_COMPLETION_CLAIM",
        re.compile(
            r"\b(?:is|are|was|were|has been|have been)\s+"
            r"permanently deleted\b",
            re.IGNORECASE,
        ),
    ),
    (
        "GIT_HISTORY_ERASURE_CLAIM",
        re.compile(
            r"\b(?:is|are|was|were|has been|have been)\s+"
            r"(?:erased|removed|purged)\s+from\s+git\s+history\b",
            re.IGNORECASE,
        ),
    ),
    (
        "ALL_COPY_REMOVAL_CLAIM",
        re.compile(
            r"\bremoved\s+from\s+all\s+"
            r"(?:forks|clones|caches|archives|backups|copies)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "IRRECOVERABILITY_CLAIM",
        re.compile(
            r"\b(?:is|are|was|were)\s+irrecoverable\b|"
            r"\bcannot\s+be\s+recovered\b",
            re.IGNORECASE,
        ),
    ),
    (
        "ZH_PERMANENT_DELETION_CLAIM",
        re.compile(r"已永久删除|永久删除(?:已经|已)?完成|已彻底删除"),
    ),
    (
        "ZH_GIT_HISTORY_ERASURE_CLAIM",
        re.compile(r"已从\s*Git\s*历史(?:中)?(?:清除|删除|移除)"),
    ),
    (
        "ZH_ALL_COPY_REMOVAL_CLAIM",
        re.compile(
            r"已从所有(?:\s*fork|\s*clone|\s*cache|\s*archive|"
            r"备份|副本)(?:中)?(?:清除|删除|移除)"
        ),
    ),
    (
        "ZH_IRRECOVERABILITY_CLAIM",
        re.compile(r"(?<!不证明数据)(?:无法恢复|不可恢复)"),
    ),
)


class GitHistoryDisclosureError(ValueError):
    """The M-064 disclosure or a scanned user surface failed closed."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _fail(code: str) -> None:
    raise GitHistoryDisclosureError(code)


def _validate_repo_path(path: Any) -> str:
    if (
        not isinstance(path, str)
        or not path
        or path.startswith("/")
        or path.endswith("/")
        or "\\" in path
        or any(ord(char) < 0x20 or ord(char) == 0x7F for char in path)
    ):
        _fail("DISCLOSURE_SURFACE_PATH_INVALID")
    parts = path.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        _fail("DISCLOSURE_SURFACE_PATH_INVALID")
    return path


def _decode_surface(path: str, raw: Any) -> str:
    _validate_repo_path(path)
    if (
        not isinstance(raw, bytes)
        or not raw
        or len(raw) > MAX_DISCLOSURE_SURFACE_BYTES
        or raw.startswith(b"\xef\xbb\xbf")
        or b"\r" in raw
    ):
        _fail("DISCLOSURE_SURFACE_FRAMING_INVALID:" + path)
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise GitHistoryDisclosureError(
            "DISCLOSURE_SURFACE_UTF8_INVALID:" + path
        ) from exc
    if any(
        (ord(char) < 0x20 and char not in "\n\t") or ord(char) == 0x7F
        for char in text
    ):
        _fail("DISCLOSURE_SURFACE_CONTROL_CHARACTER:" + path)
    return text


def validate_disclosure_surface(path: str, raw: bytes) -> None:
    """Reject affirmative hard-erasure claims on one bounded UTF-8 surface."""

    text = _decode_surface(path, raw)
    for code, pattern in _POSITIVE_HARD_ERASURE_PATTERNS:
        if pattern.search(text):
            _fail(code + ":" + path)


def disclosure_surface_digest(path: str, raw: bytes) -> str:
    """Validate a surface and return its content digest for test evidence."""

    validate_disclosure_surface(path, raw)
    return hashlib.sha256(raw).hexdigest()


def build_disclosure() -> Mapping[str, Any]:
    """Build the fixed, public-safe M-064 disclosure object."""

    value: Dict[str, Any] = {
        "schema_version": DISCLOSURE_SCHEMA_ID,
        "protocol_revision": PROTOCOL_REVISION,
        "artifact_uid": "ghd_00000000000000000000000000",
        "owner_plane": "MECHANISM",
        "status": "DRAFT_NON_ACTIVE",
        "audiences": ["OPERATOR", "USER"],
        "active_tree_contract": {
            "scope": "GIT_CURRENT_TREE_ONLY",
            "full_fidelity_retention_seconds": (
                ACTIVE_TREE_RETENTION_SECONDS
            ),
            "eligibility_condition": (
                "NOW_STRICTLY_GREATER_THAN_RETENTION_NOT_BEFORE"
            ),
            "ordinary_removal_effect": (
                "REMOVES_EXACT_BYTES_FROM_SUCCESSOR_CURRENT_TREE_ONLY"
            ),
        },
        "persistence_contract": {
            "git_history_may_retain_bytes_indefinitely": True,
            "forks_may_retain_bytes_indefinitely": True,
            "clones_may_retain_bytes_indefinitely": True,
            "caches_may_retain_bytes_indefinitely": True,
            "archives_may_retain_bytes_indefinitely": True,
            "provider_backups_may_retain_bytes_indefinitely": True,
            "third_party_copy_deletion_guaranteed": False,
        },
        "receipt_contract": {
            "proves_current_tree_transition_only": True,
            "proves_git_history_erasure": False,
            "proves_other_copy_erasure": False,
            "proves_irrecoverability": False,
        },
        "hard_erasure_contract": {
            "hard_deletion_claimed": False,
            "automatic_history_rewrite_permitted": False,
            "repository_rotation_performed": False,
            "private_storage_rotation_performed": False,
            "future_design_required": (
                "OWNER_AUTHORIZED_MAJOR_REPOSITORY_ROTATION_OR_PRIVATE_STORAGE"
            ),
        },
        "disclosures": {
            "operator_en": OPERATOR_DISCLOSURE_EN,
            "operator_zh_cn": OPERATOR_DISCLOSURE_ZH,
            "user_en": USER_DISCLOSURE_EN,
            "user_zh_cn": USER_DISCLOSURE_ZH,
            "hard_erasure_en": HARD_ERASURE_DISCLOSURE_EN,
            "hard_erasure_zh_cn": HARD_ERASURE_DISCLOSURE_ZH,
        },
        "retention_policy": {
            "policy_id": RETENTION_POLICY_ID,
            "policy_snapshot_digest": RETENTION_POLICY_SHA256,
        },
        "self_digest_pointer": DISCLOSURE_SELF_POINTER,
        "artifact_digest": "0" * 64,
    }
    value["artifact_digest"] = canonical_digest(
        value,
        DISCLOSURE_SELF_POINTER,
    )
    validate_disclosure(value)
    return value


def validate_disclosure(value: Mapping[str, Any]) -> None:
    """Enforce semantic truth independently from a self-consistent schema."""

    if not isinstance(value, Mapping):
        _fail("DISCLOSURE_ROOT_INVALID")
    if value.get("schema_version") != DISCLOSURE_SCHEMA_ID:
        _fail("DISCLOSURE_SCHEMA_VERSION_INVALID")
    if value.get("protocol_revision") != PROTOCOL_REVISION:
        _fail("DISCLOSURE_PROTOCOL_INVALID")
    if value.get("owner_plane") != "MECHANISM":
        _fail("DISCLOSURE_OWNER_INVALID")
    if value.get("status") != "DRAFT_NON_ACTIVE":
        _fail("DISCLOSURE_STATUS_INVALID")
    if value.get("audiences") != ["OPERATOR", "USER"]:
        _fail("DISCLOSURE_AUDIENCES_INVALID")
    active = value.get("active_tree_contract")
    if (
        not isinstance(active, Mapping)
        or active.get("scope") != "GIT_CURRENT_TREE_ONLY"
        or active.get("full_fidelity_retention_seconds")
        != ACTIVE_TREE_RETENTION_SECONDS
        or active.get("eligibility_condition")
        != "NOW_STRICTLY_GREATER_THAN_RETENTION_NOT_BEFORE"
        or active.get("ordinary_removal_effect")
        != "REMOVES_EXACT_BYTES_FROM_SUCCESSOR_CURRENT_TREE_ONLY"
    ):
        _fail("DISCLOSURE_ACTIVE_TREE_CONTRACT_INVALID")
    persistence = value.get("persistence_contract")
    required_true = (
        "git_history_may_retain_bytes_indefinitely",
        "forks_may_retain_bytes_indefinitely",
        "clones_may_retain_bytes_indefinitely",
        "caches_may_retain_bytes_indefinitely",
        "archives_may_retain_bytes_indefinitely",
        "provider_backups_may_retain_bytes_indefinitely",
    )
    if (
        not isinstance(persistence, Mapping)
        or any(persistence.get(key) is not True for key in required_true)
        or persistence.get("third_party_copy_deletion_guaranteed")
        is not False
    ):
        _fail("DISCLOSURE_PERSISTENCE_CONTRACT_INVALID")
    receipt = value.get("receipt_contract")
    if (
        not isinstance(receipt, Mapping)
        or receipt.get("proves_current_tree_transition_only") is not True
        or receipt.get("proves_git_history_erasure") is not False
        or receipt.get("proves_other_copy_erasure") is not False
        or receipt.get("proves_irrecoverability") is not False
    ):
        _fail("DISCLOSURE_RECEIPT_CONTRACT_INVALID")
    hard = value.get("hard_erasure_contract")
    if (
        not isinstance(hard, Mapping)
        or hard.get("hard_deletion_claimed") is not False
        or hard.get("automatic_history_rewrite_permitted") is not False
        or hard.get("repository_rotation_performed") is not False
        or hard.get("private_storage_rotation_performed") is not False
        or hard.get("future_design_required")
        != "OWNER_AUTHORIZED_MAJOR_REPOSITORY_ROTATION_OR_PRIVATE_STORAGE"
    ):
        _fail("DISCLOSURE_HARD_ERASURE_CONTRACT_INVALID")
    expected_disclosures = {
        "operator_en": OPERATOR_DISCLOSURE_EN,
        "operator_zh_cn": OPERATOR_DISCLOSURE_ZH,
        "user_en": USER_DISCLOSURE_EN,
        "user_zh_cn": USER_DISCLOSURE_ZH,
        "hard_erasure_en": HARD_ERASURE_DISCLOSURE_EN,
        "hard_erasure_zh_cn": HARD_ERASURE_DISCLOSURE_ZH,
    }
    if value.get("disclosures") != expected_disclosures:
        _fail("DISCLOSURE_TEXT_INVALID")
    policy = value.get("retention_policy")
    if (
        not isinstance(policy, Mapping)
        or policy.get("policy_id") != RETENTION_POLICY_ID
        or policy.get("policy_snapshot_digest") != RETENTION_POLICY_SHA256
    ):
        _fail("DISCLOSURE_RETENTION_POLICY_INVALID")
    if value.get("self_digest_pointer") != DISCLOSURE_SELF_POINTER:
        _fail("DISCLOSURE_SELF_POINTER_INVALID")
    if value.get("artifact_digest") != canonical_digest(
        value,
        DISCLOSURE_SELF_POINTER,
    ):
        _fail("DISCLOSURE_SELF_DIGEST_INVALID")


def render_disclosure_markdown() -> bytes:
    """Render the canonical bilingual operator/user disclosure."""

    lines: Sequence[str] = (
        REQUIRED_MARKDOWN_HEADINGS[0],
        "",
        "Status: **DRAFT_NON_ACTIVE**",
        "",
        REQUIRED_MARKDOWN_HEADINGS[1],
        "",
        OPERATOR_DISCLOSURE_EN,
        "",
        OPERATOR_DISCLOSURE_ZH,
        "",
        REQUIRED_MARKDOWN_HEADINGS[2],
        "",
        USER_DISCLOSURE_EN,
        "",
        USER_DISCLOSURE_ZH,
        "",
        REQUIRED_MARKDOWN_HEADINGS[3],
        "",
        HARD_ERASURE_DISCLOSURE_EN,
        "",
        HARD_ERASURE_DISCLOSURE_ZH,
        "",
        "A future hard-erasure design is out of scope for M-064.",
        "",
    )
    raw = "\n".join(lines).encode("utf-8")
    validate_disclosure_markdown(raw)
    return raw


def validate_disclosure_markdown(raw: bytes) -> None:
    """Require every canonical bilingual statement exactly once."""

    path = (
        "CodexSkills/governance/retention/"
        "GIT_HISTORY_PERSISTENCE_DISCLOSURE.md"
    )
    text = _decode_surface(path, raw)
    validate_disclosure_surface(path, raw)
    for heading in REQUIRED_MARKDOWN_HEADINGS:
        if text.count(heading) != 1:
            _fail("DISCLOSURE_MARKDOWN_HEADING_INVALID:" + heading)
    for disclosure in REQUIRED_DISCLOSURE_TEXT:
        if text.count(disclosure) != 1:
            _fail("DISCLOSURE_MARKDOWN_TEXT_INVALID")
