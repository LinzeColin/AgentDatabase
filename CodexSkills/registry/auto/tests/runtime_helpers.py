from __future__ import annotations

import datetime as dt
import copy
import dataclasses
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType

from CodexSkills.registry.auto.runtime.bootstrap import (
    CONTROL_INTERFACE_PATH,
    CONTROL_MODE,
    ControlTrustTuple,
    bootstrap_runtime,
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


CANDIDATE_GIT_OBJECT = "sha1:5ee37d7499c62ec19381dac7eb95cb12743ad2d5"
CANDIDATE_DIGEST = "36f0c66dd54d36365700a13f614a8c9bfa9619fb7c532af77566a858175b835e"
MANIFEST_PATH = "CodexSkills/governance/bundles/schema-bundle-manifest.v1.json"
CONTROL_GIT_OBJECT = "sha1:66d5bafadca508cad825b4ce49a42e81e8b66ef7"
CONTROL_INTERFACE_RAW_SHA256 = (
    "86e4d625bdab87261a39c949883d4108"
    "22e25e0222dbab6a333d171ce420c614"
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
def context():
    return bootstrap_runtime(REPO_ROOT, trust(), control_trust())


@lru_cache(maxsize=1)
def control_synced_context():
    current = context()
    interface = copy.deepcopy(dict(current.control_interface))
    interface["transition_contract"][
        "auto_runtime_integration_complete"
    ] = True
    return dataclasses.replace(
        current,
        control_interface=MappingProxyType(interface),
    )


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
