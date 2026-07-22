from __future__ import annotations

import datetime as dt
from functools import lru_cache
from pathlib import Path

from CodexSkills.auto.runtime.bootstrap import bootstrap_runtime
from CodexSkills.auto.runtime.core import (
    FakeClock,
    PROTOCOL,
    SCHEMA_PREFIX,
    canonical_with_digest,
    format_utc,
    new_uid,
)
from CodexSkills.governance.tools.validate_mechanism import TrustTuple


CANDIDATE_GIT_OBJECT = "sha1:4b1e1a318c8f9e1014839a8a3a46e057679c4b6b"
CANDIDATE_DIGEST = "fd1df66e240695bd376803423bd09f9f341f7542f74a6ed92b0f79b0af4dc5e1"
MANIFEST_PATH = "CodexSkills/governance/bundles/schema-bundle-manifest.v1.json"
FIXED_NOW = dt.datetime(2026, 7, 23, 0, 0, 0, tzinfo=dt.timezone.utc)
REPO_ROOT = Path(__file__).resolve().parents[3]


def trust(mode: str = "CANDIDATE", digest: str = CANDIDATE_DIGEST) -> TrustTuple:
    return TrustTuple(CANDIDATE_GIT_OBJECT, digest, MANIFEST_PATH, mode)


@lru_cache(maxsize=1)
def context():
    return bootstrap_runtime(REPO_ROOT, trust())


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
