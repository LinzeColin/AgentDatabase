#!/usr/bin/env python3
"""Production two-stage activation notification and publication entrypoint."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence


AUTO_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = AUTO_DIR.parents[1]
sys.path.insert(0, str(REPO_ROOT))

from CodexSkills.auto.runtime.activation import (  # noqa: E402
    ActivationControlTrustTuple,
    ActivationHandshake,
)
from CodexSkills.auto.runtime.bootstrap import bootstrap_runtime  # noqa: E402
from CodexSkills.auto.runtime.core import (  # noqa: E402
    AutoRuntimeError,
    SystemClock,
    format_utc,
)
from CodexSkills.auto.runtime.gmail_api import (  # noqa: E402
    GmailApiConfig,
    GmailApiNotificationTransport,
    NotificationPathContract,
)
from CodexSkills.auto.runtime.notification import (  # noqa: E402
    RecipientMapping,
    TransactionalNotifier,
    render_major_email,
)
from CodexSkills.auto.runtime.publication import (  # noqa: E402
    PhysicalPublisher,
    PublicationArtifact,
    PublicationRequest,
    SubprocessGitBackend,
)
from CodexSkills.auto.runtime.roots import prepare_state_root  # noqa: E402
from CodexSkills.auto.runtime.state import (  # noqa: E402
    SingleFlightLock,
    StateLayout,
)
from CodexSkills.auto.tools.validate_auto import TrustTuple  # noqa: E402
from CodexSkills.governance.tools.canonical_json import (  # noqa: E402
    canonicalize_object,
)


def _candidate_trust(args: argparse.Namespace) -> TrustTuple:
    return TrustTuple(
        args.verified_candidate_git_object_id,
        args.expected_bundle_digest,
        args.canonical_manifest_path,
        args.candidate_mode,
    )


def _control_trust(
    args: argparse.Namespace,
) -> ActivationControlTrustTuple:
    return ActivationControlTrustTuple(
        args.verified_control_git_object_id,
        args.expected_control_interface_raw_sha256,
        args.canonical_control_interface_path,
        args.control_mode,
    )


def _context_and_handshake(args: argparse.Namespace):
    context = bootstrap_runtime(
        args.repo_root,
        _candidate_trust(args),
    )
    handshake = ActivationHandshake(
        args.repo_root,
        context,
        _control_trust(args),
    )
    return context, handshake


def _prepare_lock(
    args: argparse.Namespace,
    context,
    owner_run_uid: str,
):
    prepared = prepare_state_root(
        args.state_root,
        repo_root=args.repo_root,
        protected_roots=(args.artifact_root,),
    )
    layout = StateLayout.create(prepared)
    clock = SystemClock()
    lock = SingleFlightLock(
        layout,
        context.contract,
        args.expected_bundle_digest,
        clock,
    )
    acquired = lock.acquire(owner_run_uid)
    if acquired.status != "ACQUIRED" or acquired.state is None:
        raise AutoRuntimeError(
            "ACTIVATION_SINGLE_FLIGHT_NOT_ACQUIRED:"
            + acquired.status
        )
    return prepared, layout, clock, lock, acquired.state


def _notification_components(
    args: argparse.Namespace,
    context,
    prepared: Path,
):
    paths = NotificationPathContract.resolve(
        prepared,
        repo_root=args.repo_root,
    )
    policy = context.contract.shared.policies.get(
        "urn:linzecolin:agentdatabase:skillops:policy:notification:v1"
    )
    if (
        not isinstance(policy, dict)
        or not isinstance(policy.get("recipient_ref"), str)
    ):
        raise AutoRuntimeError("NOTIFICATION_POLICY_NOT_TRUSTED")
    mapping = RecipientMapping.load(
        paths.recipient_mapping_path,
        policy["recipient_ref"],
    )
    config = GmailApiConfig.load(paths.gmail_config_path)
    transport = GmailApiNotificationTransport(config)
    transport.preflight(mapping.provider_target)
    return paths, mapping, transport


def _notify_intent(args: argparse.Namespace) -> int:
    context, handshake = _context_and_handshake(args)
    verified = handshake.verify_intent_root(
        args.artifact_root,
        args.intent_repo_path,
        args.expected_remote_head,
    )
    observed_remote_head = SubprocessGitBackend(
        args.repo_root,
        args.artifact_root,
    ).remote_head()
    if observed_remote_head != verified.expected_remote_head:
        raise AutoRuntimeError(
            "ACTIVATION_NOTIFICATION_REMOTE_HEAD_CHANGED"
        )
    prepared, _layout, clock, lock, lock_state = _prepare_lock(
        args,
        context,
        verified.auto_transaction_uid,
    )
    outcome = None
    try:
        paths, mapping, transport = _notification_components(
            args,
            context,
            prepared,
        )
        observed_at = format_utc(clock.now())
        rendered = render_major_email(
            srv_revision=verified.target_srv_revision,
            auto_transaction_uid=verified.auto_transaction_uid,
            observed_at=observed_at,
            remote_baseline=verified.expected_remote_head,
            public_metadata=verified.notification_metadata,
        )
        notifier = TransactionalNotifier(
            paths.outbox_path,
            context.contract,
            args.expected_bundle_digest,
            clock,
            transport,
        )
        outcome = notifier.notify_major(
            notification_uid=verified.notification_uid,
            auto_transaction_uid=verified.auto_transaction_uid,
            timing="PRE_WRITE",
            mapping=mapping,
            subject=rendered.subject,
            body=rendered.body,
            public_metadata=verified.notification_metadata,
        )
    finally:
        lock.release(
            verified.auto_transaction_uid,
            str(lock_state["state_digest"]),
        )
    assert outcome is not None
    sys.stdout.buffer.write(canonicalize_object(outcome.receipt))
    return 0 if outcome.planned_write_allowed else 3


def _publish_settlement(args: argparse.Namespace) -> int:
    context, handshake = _context_and_handshake(args)
    verified = handshake.verify_settlement_root(
        args.artifact_root,
        args.settlement_repo_path,
        args.expected_remote_head,
    )
    _prepared, _layout, _clock, lock, lock_state = _prepare_lock(
        args,
        context,
        verified.auto_transaction_uid,
    )
    readback = None
    try:
        artifacts = tuple(
            PublicationArtifact(path, verified.payloads[path])
            for path in verified.artifact_paths
        )
        publisher = PhysicalPublisher(
            context.contract,
            args.expected_bundle_digest,
            SubprocessGitBackend(args.repo_root, args.scratch_root),
            trusted_mode="CANDIDATE",
            lock=lock,
            activation_handshake=handshake,
        )
        readback = publisher.publish(
            PublicationRequest(
                auto_transaction_uid=verified.auto_transaction_uid,
                authority="COORDINATED_ACTIVATION",
                trust_mode="CANDIDATE",
                expected_remote_head=verified.expected_remote_head,
                commit_message=(
                    "Activate SkillOps candidate through verified settlement"
                ),
                artifacts=artifacts,
                lock_owner_run_uid=verified.auto_transaction_uid,
                lock_state_digest=str(lock_state["state_digest"]),
                activation_settlement_repo_path=(
                    verified.settlement_repo_path
                ),
            )
        )
    finally:
        lock.release(
            verified.auto_transaction_uid,
            str(lock_state["state_digest"]),
        )
    assert readback is not None
    sys.stdout.buffer.write(
        canonicalize_object(
            {
                "artifact_digests": dict(readback.artifact_digests),
                "commit": readback.commit,
                "verified": readback.verified,
            }
        )
        + b"\n"
    )
    return 0


def _common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--state-root", type=Path, required=True)
    parser.add_argument("--expected-remote-head", required=True)
    parser.add_argument(
        "--verified-candidate-git-object-id",
        required=True,
    )
    parser.add_argument("--expected-bundle-digest", required=True)
    parser.add_argument("--canonical-manifest-path", required=True)
    parser.add_argument(
        "--candidate-mode",
        choices=("CANDIDATE",),
        required=True,
    )
    parser.add_argument(
        "--verified-control-git-object-id",
        required=True,
    )
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
    notify = commands.add_parser("notify-intent")
    _common(notify)
    notify.add_argument("--intent-repo-path", required=True)
    publish = commands.add_parser("publish-settlement")
    _common(publish)
    publish.add_argument("--settlement-repo-path", required=True)
    publish.add_argument("--scratch-root", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "notify-intent":
        return _notify_intent(args)
    return _publish_settlement(args)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AutoRuntimeError as exc:
        print(exc.code, file=sys.stderr)
        raise SystemExit(2)
