from __future__ import annotations

import datetime as dt
import hashlib
import re
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType

from CodexSkills.registry.auto.runtime.bootstrap import (
    BootstrapContext,
    CONTROL_INTERFACE_PATH,
    CONTROL_MODE,
    ControlTrustTuple,
    _git_blob,
    _split_git_object,
)
from CodexSkills.registry.auto.runtime.core import (
    FakeClock,
    PROTOCOL,
    SCHEMA_PREFIX,
    canonical_with_digest,
    format_utc,
    new_uid,
)
from CodexSkills.governance.tools.validate_mechanism import TrustTuple
from CodexSkills.governance.tools.canonical_json import parse_json_bytes
from CodexSkills.registry.auto.tools.validate_auto import (
    load_trusted_auto_contract,
)


CANDIDATE_GIT_OBJECT = "sha1:5ee37d7499c62ec19381dac7eb95cb12743ad2d5"
CANDIDATE_DIGEST = "36f0c66dd54d36365700a13f614a8c9bfa9619fb7c532af77566a858175b835e"
MANIFEST_PATH = "CodexSkills/governance/bundles/schema-bundle-manifest.v1.json"
CONTROL_GIT_OBJECT = "sha1:00c4a52d177898b1999b87b29ddb480e89908729"
CONTROL_INTERFACE_RAW_SHA256 = (
    "31602443a685cc12a1eebd51ea8e0801"
    "ffd399c16a33186c372b7b81e8e46409"
)
FIXED_NOW = dt.datetime(2026, 7, 23, 0, 0, 0, tzinfo=dt.timezone.utc)
REPO_ROOT = Path(__file__).resolve().parents[4]


def trust(mode: str = "CANDIDATE", digest: str = CANDIDATE_DIGEST) -> TrustTuple:
    return TrustTuple(CANDIDATE_GIT_OBJECT, digest, MANIFEST_PATH, mode)


def control_trust(
    *,
    object_id: str = CONTROL_GIT_OBJECT,
    raw_digest: str = CONTROL_INTERFACE_RAW_SHA256,
) -> ControlTrustTuple:
    return ControlTrustTuple(
        object_id,
        raw_digest,
        CONTROL_INTERFACE_PATH,
        CONTROL_MODE,
    )


@lru_cache(maxsize=1)
def final_contract():
    """Load final 31/5 content without claiming current control binding."""

    return load_trusted_auto_contract(REPO_ROOT, trust())


@lru_cache(maxsize=1)
def synthetic_bound_context():
    """Test-only historical control fixture; never a production bootstrap."""

    object_id = _split_git_object(
        REPO_ROOT,
        CONTROL_GIT_OBJECT,
        "TEST_HISTORICAL_CONTROL",
    )
    raw = _git_blob(REPO_ROOT, object_id, CONTROL_INTERFACE_PATH)
    if hashlib.sha256(raw).hexdigest() != CONTROL_INTERFACE_RAW_SHA256:
        raise AssertionError("TEST_HISTORICAL_CONTROL_DIGEST_MISMATCH")
    interface = parse_json_bytes(raw)
    return BootstrapContext(
        trust(),
        control_trust(),
        final_contract(),
        MappingProxyType({}),
        MappingProxyType(interface),
    )


@lru_cache(maxsize=1)
def context():
    """Compatibility alias for tests that only consume the final contract."""

    return synthetic_bound_context()


def expected_stale_control_failure_pattern() -> str:
    """Return the one exact production failure expected for the stale tuple."""

    object_id = _split_git_object(
        REPO_ROOT,
        CONTROL_GIT_OBJECT,
        "TEST_HISTORICAL_CONTROL",
    )
    historical = _git_blob(
        REPO_ROOT,
        object_id,
        CONTROL_INTERFACE_PATH,
    )
    local = REPO_ROOT.joinpath(
        *CONTROL_INTERFACE_PATH.split("/")
    ).read_bytes()
    code = (
        "BOOTSTRAP_AUTO_RUNTIME_INTERFACE_LOCAL_DRIFT"
        if local == historical
        else "BOOTSTRAP_CONTROL_INTERFACE_LOCAL_DRIFT"
    )
    return rf"^{re.escape(code)}$"


def clock() -> FakeClock:
    return FakeClock(FIXED_NOW)


def uid(prefix: str, number: int = 0) -> str:
    return new_uid(prefix, FIXED_NOW, number.to_bytes(10, "big"))


def auto_receipt(number: int = 1):
    return canonical_with_digest(
        {
            "schema_version": SCHEMA_PREFIX + "auto-receipt:v2",
            "protocol_revision": PROTOCOL,
            "bundle_digest": CANDIDATE_DIGEST,
            "receipt_uid": uid("ar", number),
            "auto_transaction_uid": uid("atx", number),
            "trigger_kind": "MANUAL",
            "started_at": format_utc(FIXED_NOW),
            "finished_at": format_utc(FIXED_NOW),
            "execution_profile": {
                "model_ref": "gpt-5-6-sol",
                "reasoning_effort": "XHIGH",
            },
            "final_action": "NONE",
            "overall_status": "NO_CHANGE",
            "settled_lanes": [],
            "lane_results": [
                {
                    "lane": "REGISTRY",
                    "status": "NO_CHANGE",
                    "input_count": 0,
                    "published_count": 0,
                    "quarantined_count": 0,
                },
                {
                    "lane": "RUN_LOG",
                    "status": "NO_CHANGE",
                    "input_count": 0,
                    "published_count": 0,
                    "quarantined_count": 0,
                },
            ],
            "reason_codes": ["NO_CHANGES"],
            "receipt_digest": "0" * 64,
        },
        "receipt_digest",
    )
