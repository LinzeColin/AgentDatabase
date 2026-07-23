#!/usr/bin/env python3
"""Build/check deterministic Auto activation-handshake interface evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


AUTO_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = AUTO_DIR.parents[2]
OUTPUT = AUTO_DIR / "runtime-interface.json"
CANDIDATE_GIT_OBJECT = "sha1:899a4374bc02f5e18444fea7404864df7b118adf"
CANDIDATE_BUNDLE_DIGEST = "2704ed797c843f969965db600747abcdcd217550522e6479aab6817ef5a86ef5"
CANDIDATE_MANIFEST_PATH = "CodexSkills/governance/bundles/schema-bundle-manifest.v1.json"


def _files():
    paths = sorted((AUTO_DIR / "runtime").glob("*.py"))
    paths.extend(
        [
            AUTO_DIR / "tools" / "activation_handshake_cli.py",
            AUTO_DIR / "tools" / "build_runtime_interface.py",
            AUTO_DIR / "tools" / "notification_transport_cli.py",
            AUTO_DIR / "tools" / "run_fault_suite.py",
            AUTO_DIR / "tools" / "runtime_preflight.py",
            AUTO_DIR / "tools" / "validate_auto.py",
        ]
    )
    return sorted(paths, key=lambda path: path.relative_to(REPO_ROOT).as_posix())


def build():
    artifacts = []
    for path in _files():
        relative = path.relative_to(REPO_ROOT).as_posix()
        artifacts.append(
            {
                "artifact_digest": hashlib.sha256(path.read_bytes()).hexdigest(),
                "relative_path": relative,
            }
        )
    return {
        "activation_caller_assertions_forbidden": [
            "activation_artifact_digests",
            "activation_envelope_verified",
            "notification_provider_status",
            "shared_gate_status_map",
        ],
        "activation_control_baseline_git_object_id": (
            "sha1:6769eba64badac04a131bfa00dbb0e1a353ccae0"
        ),
        "activation_control_baseline_interface_raw_sha256": (
            "24af49e7f3c0ecac85154a2a9741d9d8"
            "ceb16368224cbf7900eceac9fe66e0f7"
        ),
        "activation_control_interface_path": (
            "CodexSkills/governance/activation/control-interface.json"
        ),
        "activation_control_mode": "DRAFT_NON_ACTIVE_CONTROL",
        "activation_control_trust_tuple_repo_external_only": True,
        "activation_forbidden_without_coordinated_m0c": True,
        "activation_handshake_entrypoint": (
            "CodexSkills/registry/auto/tools/activation_handshake_cli.py"
        ),
        "activation_instance_created": False,
        "activation_settlement_recomputed_before_publish": True,
        "au_040_daily_jsonl_shard_complete": False,
        "candidate_bundle_digest": CANDIDATE_BUNDLE_DIGEST,
        "candidate_git_object_id": CANDIDATE_GIT_OBJECT,
        "candidate_manifest_path": CANDIDATE_MANIFEST_PATH,
        "canonical_publication_permitted": False,
        "capability_gate_precedes_state_write": True,
        "consumer_first_gate_satisfied": False,
        "consumer_first_owner_plane": "MECHANISM",
        "external_gmail_ready_gate_satisfied": False,
        "fault_test_rounds_required": 2,
        "manual_and_scheduled_same_orchestrator": True,
        "module_artifacts": artifacts,
        "module_count": len(artifacts),
        "m0c_b_permitted": False,
        "next_phase": "MECHANISM_CONSUMER_FIRST_PHASE",
        "notification_actual_recipient_repo_external": True,
        "notification_credentials_repo_external": True,
        "notification_external_path_contract": {
            "gmail_config_ref": (
                "state-root/private/notification/gmail-api.v1.json"
            ),
            "recipient_mapping_ref": (
                "state-root/private/notification/recipient-mapping.v1.json"
            ),
        },
        "notification_production_transport": "GMAIL_API_V1",
        "notification_provider_lookup": (
            "RFC822_MESSAGE_ID_AND_PRIVATE_PAYLOAD_DIGEST"
        ),
        "notification_provider_readback_required": True,
        "notification_public_recipient_ref_only": True,
        "notification_send_entrypoint": (
            "CodexSkills/registry/auto/tools/activation_handshake_cli.py"
        ),
        "notification_test_transport_production_forbidden": True,
        "os_local_scheduler_or_daemon_used": False,
        "persistent_managed_raw_default_enabled": False,
        "protocol_revision": "urn:linzecolin:agentdatabase:skillops:protocol:cross-pack:v1",
        "remote_readback_precedes_watermark": True,
        "schedule": {
            "daily_local_time": "04:15",
            "late_start_rejected": False,
            "sunday_forced_full": True,
            "timezone": "Australia/Sydney",
        },
        "shared_bundle_schema_count": 29,
        "shared_policy_count": 5,
        "state_root_repo_external": True,
        "status": "DRAFT_NON_ACTIVE",
        "trust_tuple_repo_external_only": True,
    }


def render(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--write", action="store_true")
    modes.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = render(build())
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_bytes() != expected:
            print("AUTO_RUNTIME_INTERFACE_MISMATCH")
            return 2
        print(
            "AUTO_RUNTIME_INTERFACE_BYTE_EQUIVALENT "
            f"raw_sha256={hashlib.sha256(expected).hexdigest()}"
        )
        return 0
    OUTPUT.write_bytes(expected)
    print(
        "AUTO_RUNTIME_INTERFACE_GENERATED_OK "
        f"raw_sha256={hashlib.sha256(expected).hexdigest()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
