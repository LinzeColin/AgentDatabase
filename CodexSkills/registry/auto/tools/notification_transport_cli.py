#!/usr/bin/env python3
"""Fail-closed production Gmail transport entrypoint for SkillOps Auto."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence


AUTO_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = AUTO_DIR.parents[2]
sys.path.insert(0, str(REPO_ROOT))

from CodexSkills.registry.auto.runtime.bootstrap import (
    ControlTrustTuple,
    bootstrap_runtime,
    require_control_synced_runtime,
)
from CodexSkills.registry.auto.runtime.core import AutoRuntimeError, SystemClock
from CodexSkills.registry.auto.runtime.gmail_api import (
    GmailApiConfig,
    GmailApiNotificationTransport,
    NotificationPathContract,
)
from CodexSkills.registry.auto.runtime.notification import (
    RecipientMapping,
    TransactionalNotifier,
    render_major_email,
)
from CodexSkills.registry.auto.tools.validate_auto import TrustTuple
from CodexSkills.governance.tools.canonical_json import (
    canonicalize_object,
    parse_json_bytes,
)


def _trust(args: argparse.Namespace) -> TrustTuple:
    return TrustTuple(
        args.verified_git_object_id,
        args.expected_bundle_digest,
        args.canonical_manifest_path,
        args.mode,
    )


def _control_trust(args: argparse.Namespace) -> ControlTrustTuple:
    return ControlTrustTuple(
        args.verified_control_git_object_id,
        args.expected_control_interface_raw_sha256,
        args.canonical_control_interface_path,
        args.control_mode,
    )


def _private_public_metadata(path: Path):
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise AutoRuntimeError("NOTIFICATION_METADATA_UNAVAILABLE") from exc
    if not raw or len(raw) > 256 * 1024:
        raise AutoRuntimeError("NOTIFICATION_METADATA_SIZE_INVALID")
    try:
        value = parse_json_bytes(raw)
    except Exception as exc:
        raise AutoRuntimeError("NOTIFICATION_METADATA_INVALID") from exc
    if not isinstance(value, dict):
        raise AutoRuntimeError("NOTIFICATION_METADATA_ROOT_INVALID")
    return value


def _reject_activation_bypass(metadata) -> None:
    if metadata.get("planned_action") == "ACTIVATE":
        raise AutoRuntimeError(
            "ACTIVATION_HANDSHAKE_ENTRYPOINT_REQUIRED"
        )


def _components(
    args: argparse.Namespace,
    *,
    state_write_requested: bool,
):
    context = bootstrap_runtime(
        args.repo_root,
        _trust(args),
        _control_trust(args),
    )
    if state_write_requested:
        require_control_synced_runtime(context)
    paths = NotificationPathContract.resolve(
        args.state_root,
        repo_root=args.repo_root,
    )
    policy = context.contract.shared.policies.get(
        "urn:linzecolin:agentdatabase:skillops:policy:notification:v1"
    )
    if not isinstance(policy, dict) or not isinstance(policy.get("recipient_ref"), str):
        raise AutoRuntimeError("NOTIFICATION_POLICY_NOT_TRUSTED")
    mapping = RecipientMapping.load(paths.recipient_mapping_path, policy["recipient_ref"])
    config = GmailApiConfig.load(paths.gmail_config_path)
    transport = GmailApiNotificationTransport(config)
    return context, paths, mapping, transport


def _common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--state-root", type=Path, required=True)
    parser.add_argument("--verified-git-object-id", required=True)
    parser.add_argument("--expected-bundle-digest", required=True)
    parser.add_argument("--canonical-manifest-path", required=True)
    parser.add_argument("--mode", choices=("CANDIDATE", "ACTIVE"), required=True)
    parser.add_argument("--verified-control-git-object-id", required=True)
    parser.add_argument(
        "--expected-control-interface-raw-sha256",
        required=True,
    )
    parser.add_argument(
        "--canonical-control-interface-path",
        required=True,
    )
    parser.add_argument(
        "--control-mode",
        choices=("DRAFT_NON_ACTIVE_CONTROL",),
        required=True,
    )


def main(argv: Sequence[str] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    preflight = commands.add_parser("preflight")
    _common(preflight)
    notify = commands.add_parser("notify-major")
    _common(notify)
    notify.add_argument("--notification-uid", required=True)
    notify.add_argument("--auto-transaction-uid", required=True)
    notify.add_argument("--timing", choices=("PRE_WRITE", "POST_CONTAINMENT"), required=True)
    notify.add_argument("--srv-revision", required=True)
    notify.add_argument("--observed-at", required=True)
    notify.add_argument("--remote-baseline", required=True)
    notify.add_argument("--public-metadata-file", type=Path, required=True)
    args = parser.parse_args(argv)

    context, paths, mapping, transport = _components(
        args,
        state_write_requested=args.command != "preflight",
    )
    capability = transport.preflight(mapping.provider_target)
    if args.command == "preflight":
        refs = paths.public_refs()
        print(
            "GMAIL_TRANSPORT_PREFLIGHT_OK "
            f"provider={capability['provider_code']} "
            f"recipient_ref={mapping.recipient_ref} "
            "query_endpoint=VERIFIED "
            "metadata_readback=PENDING_REAL_SEND "
            f"mapping_ref={refs['recipient_mapping_ref']} "
            f"config_ref={refs['gmail_config_ref']}"
        )
        return 0

    metadata = _private_public_metadata(args.public_metadata_file)
    _reject_activation_bypass(metadata)
    rendered = render_major_email(
        srv_revision=args.srv_revision,
        auto_transaction_uid=args.auto_transaction_uid,
        observed_at=args.observed_at,
        remote_baseline=args.remote_baseline,
        public_metadata=metadata,
    )
    notifier = TransactionalNotifier(
        paths.outbox_path,
        context.contract,
        args.expected_bundle_digest,
        SystemClock(),
        transport,
    )
    outcome = notifier.notify_major(
        notification_uid=args.notification_uid,
        auto_transaction_uid=args.auto_transaction_uid,
        timing=args.timing,
        mapping=mapping,
        subject=rendered.subject,
        body=rendered.body,
        public_metadata=metadata,
    )
    sys.stdout.buffer.write(canonicalize_object(outcome.receipt) + b"\n")
    return 0 if outcome.planned_write_allowed else 3


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AutoRuntimeError as exc:
        print(exc.code, file=sys.stderr)
        raise SystemExit(2)
