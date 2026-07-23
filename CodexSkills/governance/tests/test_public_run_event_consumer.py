from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TOOLS_DIR = REPO_ROOT / "CodexSkills" / "governance" / "tools"
sys.path.insert(0, str(TOOLS_DIR))

from canonical_json import canonical_digest, canonicalize_object  # noqa: E402
from validate_mechanism import TrustTuple, load_trusted_bundle  # noqa: E402
from validate_public_run_event import (  # noqa: E402
    PublicRunEventError,
    parse_canonical_public_run_event,
)


CANDIDATE_GIT_OBJECT = "sha1:899a4374bc02f5e18444fea7404864df7b118adf"
CANDIDATE_DIGEST = (
    "fd1df66e240695bd376803423bd09f9f341f7542f74a6ed92b0f79b0af4dc5e1"
)
MANIFEST_PATH = "CodexSkills/governance/bundles/schema-bundle-manifest.v1.json"
SCHEMA_ID = "urn:linzecolin:agentdatabase:skillops:schema:public-run-event:v2"
PROTOCOL = "urn:linzecolin:agentdatabase:skillops:protocol:cross-pack:v1"
T0 = "2026-07-23T00:00:00.000000Z"
T1 = "2026-07-23T00:01:00.000000Z"
DIGEST = "b" * 64
SECOND_DIGEST = "c" * 64


def uid(prefix: str, discriminator: str = "0") -> str:
    return f"{prefix}_{discriminator}{'0' * 25}"


def seal(value: dict) -> dict:
    result = copy.deepcopy(value)
    result["event_digest"] = "0" * 64
    result["event_digest"] = canonical_digest(result, "/event_digest")
    return result


def event(*, bound: bool = False) -> dict:
    value = {
        "schema_version": SCHEMA_ID,
        "protocol_revision": PROTOCOL,
        "bundle_digest": CANDIDATE_DIGEST,
        "event_uid": uid("evt"),
        "run_uid": uid("run"),
        "event_type": "RUN_OBSERVED",
        "occurred_at": T1,
        "surface_class": "CODEX_CLI" if bound else "CODEX_AUTOMATION",
        "actor_role": "CLI" if bound else "AUTOMATION",
        "adapter_id": "run-observer-adapter",
        "adapter_version": "2.0.0",
        "adapter_schema_digest": DIGEST,
        "mapping_policy_id": (
            "urn:linzecolin:agentdatabase:skillops:policy:run-mapping:v1"
        ),
        "mapping_policy_digest": SECOND_DIGEST,
        "trigger_kind": "MANUAL",
        "run_status": "SUCCESS",
        "model_ref": "gpt-5-6-sol",
        "reasoning_effort": "ULTRA",
        "metrics": {
            "duration_ms": 1000,
            "tool_call_count": 2,
            "input_tokens": None,
            "output_tokens": None,
            "token_usage_status": "UNAVAILABLE",
        },
        "binding_state": "BOUND" if bound else "UNKNOWN",
        "redaction": {
            "policy_snapshot_digest": DIGEST,
            "unknown_fields_dropped": 0,
            "omitted_category_codes": [],
            "post_serialization_scan_passed": True,
        },
        "immutable": True,
        "event_digest": "0" * 64,
    }
    if bound:
        value["skill_ref"] = {
            "skill_identity_uid": uid("ski"),
            "skill_instance_uid": uid("skinst"),
            "skill_version_uid": uid("skv"),
            "content_digest": DIGEST,
            "tree_digest": SECOND_DIGEST,
            "version_record_digest": DIGEST,
            "registry_snapshot_digest": SECOND_DIGEST,
        }
        value["controlled_invocation"] = {
            "invocation_uid": uid("inv"),
            "invocation_envelope_digest": DIGEST,
            "surface_class": "CODEX_CLI",
            "observed_at": T0,
            "evidence_type": "CONTROLLED_INVOCATION_EXACT_VERSION",
        }
    else:
        value["unknown_reason_code"] = "MAPPING_NOT_PROVABLE"
    return seal(value)


class PublicRunEventConsumerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bundle = load_trusted_bundle(
            REPO_ROOT,
            TrustTuple(
                CANDIDATE_GIT_OBJECT,
                CANDIDATE_DIGEST,
                MANIFEST_PATH,
                "CANDIDATE",
            ),
        )

    def parse(self, value: dict):
        return parse_canonical_public_run_event(
            self.bundle,
            canonicalize_object(value),
            expected_bundle_digest=CANDIDATE_DIGEST,
        )

    def test_unknown_and_exact_bound_events_pass_shared_consumer(self) -> None:
        self.assertEqual(self.parse(event())["binding_state"], "UNKNOWN")
        self.assertEqual(self.parse(event(bound=True))["binding_state"], "BOUND")

    def test_noncanonical_record_is_rejected_before_schema_acceptance(self) -> None:
        value = event()
        raw = json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        self.assertNotEqual(raw, canonicalize_object(value))
        with self.assertRaisesRegex(
            PublicRunEventError,
            "RUN_EVENT_RECORD_NOT_RFC8785_JCS",
        ):
            parse_canonical_public_run_event(
                self.bundle,
                raw,
                expected_bundle_digest=CANDIDATE_DIGEST,
            )

    def test_duplicate_keys_are_rejected_before_schema_acceptance(self) -> None:
        raw = (
            b'{"event_uid":"evt_00000000000000000000000000",'
            b'"event_uid":"evt_10000000000000000000000000"}'
        )
        with self.assertRaisesRegex(
            ValueError,
            "DUPLICATE_KEY:event_uid",
        ):
            parse_canonical_public_run_event(
                self.bundle,
                raw,
                expected_bundle_digest=CANDIDATE_DIGEST,
            )

    def test_consumer_rejects_cross_field_drift_after_valid_digest(self) -> None:
        bad = event(bound=True)
        bad["controlled_invocation"]["surface_class"] = "CODEX_AUTOMATION"
        bad = seal(bad)
        with self.assertRaisesRegex(
            PublicRunEventError,
            "RUN_EVENT_CONTROLLED_SURFACE_MISMATCH",
        ):
            self.parse(bad)

        bad_tokens = event()
        bad_tokens["metrics"]["input_tokens"] = 10
        bad_tokens = seal(bad_tokens)
        with self.assertRaisesRegex(
            PublicRunEventError,
            "RUN_EVENT_UNMEASURED_TOKENS_MUST_BE_NULL",
        ):
            self.parse(bad_tokens)

    def test_consumer_rejects_future_invocation_and_self_correction(self) -> None:
        future_invocation = event(bound=True)
        future_invocation["controlled_invocation"]["observed_at"] = (
            "2026-07-23T00:02:00.000000Z"
        )
        with self.assertRaisesRegex(
            PublicRunEventError,
            "RUN_EVENT_INVOCATION_EVIDENCE_AFTER_EVENT",
        ):
            self.parse(seal(future_invocation))

        self_correction = event(bound=True)
        self_correction["event_type"] = "BINDING_CORRECTION"
        self_correction["supersedes_event_uid"] = self_correction["event_uid"]
        self_correction["supersedes_event_digest"] = SECOND_DIGEST
        with self.assertRaisesRegex(
            PublicRunEventError,
            "RUN_EVENT_CANNOT_SUPERSEDE_SELF",
        ):
            self.parse(seal(self_correction))

    def test_measured_tokens_require_both_values(self) -> None:
        measured = event()
        measured["metrics"].update(
            {
                "input_tokens": 100,
                "output_tokens": 20,
                "token_usage_status": "MEASURED",
            }
        )
        self.assertEqual(
            self.parse(seal(measured))["metrics"]["input_tokens"],
            100,
        )

        measured["metrics"]["output_tokens"] = None
        with self.assertRaisesRegex(
            PublicRunEventError,
            "RUN_EVENT_TOKEN_MEASUREMENT_STATE_MISMATCH",
        ):
            self.parse(seal(measured))


if __name__ == "__main__":
    unittest.main()
