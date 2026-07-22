from __future__ import annotations

import os
import hashlib
import tempfile
import unittest
from pathlib import Path

from CodexSkills.auto.runtime.core import AutoRuntimeError
from CodexSkills.auto.runtime.notification import (
    FakeNotificationTransport,
    RecipientMapping,
    TransactionalNotifier,
)
from CodexSkills.auto.runtime.publication import (
    GitBackend,
    PhysicalPublisher,
    PublicationArtifact,
    PublicationRequest,
    RemoteReadback,
    SHARED_GATES,
)
from CodexSkills.governance.tools.canonical_json import canonicalize_object

from runtime_helpers import CANDIDATE_DIGEST, clock, context, uid


def gates(value="PASS"):
    return {code: value for code in SHARED_GATES}


class FakeGitBackend(GitBackend):
    def __init__(self) -> None:
        self.head = "sha1:" + "a" * 40
        self.last_commit = "sha1:" + "b" * 40
        self.artifacts = ()
        self.cleaned = False
        self.changed_override = None
        self.transactions = {}
        self.fail_readback_once = False

    def remote_head(self):
        return self.head

    def create_worktree(self, expected_head, transaction_uid):
        self.expected = expected_head
        return Path("/virtual/skillops-worktree")

    def write_artifacts(self, worktree, artifacts):
        self.artifacts = tuple(artifacts)

    def changed_paths(self, worktree):
        if self.changed_override is not None:
            return self.changed_override
        return tuple(sorted(item.relative_path for item in self.artifacts))

    def commit(self, worktree, message, paths):
        self.message = message
        trailer = next(
            line for line in message.splitlines() if line.startswith("SkillOps-Auto-Transaction: ")
        )
        self.transactions[trailer.split(": ", 1)[1]] = (self.expected, self.last_commit)
        return self.last_commit

    def push(self, worktree, expected_head):
        if self.head != expected_head:
            raise AutoRuntimeError("REMOTE_HEAD_CHANGED")
        self.head = self.last_commit

    def readback(self, commit, artifacts):
        import hashlib

        if self.fail_readback_once:
            self.fail_readback_once = False
            raise RuntimeError("synthetic post-push crash")
        return RemoteReadback(
            commit,
            {item.relative_path: hashlib.sha256(item.payload).hexdigest() for item in artifacts},
            True,
        )

    def find_transaction(self, transaction_uid, expected_parent):
        observed = self.transactions.get(transaction_uid)
        if observed is None or observed[0] != expected_parent:
            return None
        return observed[1]

    def cleanup(self, worktree):
        self.cleaned = True


class RuntimeNotificationPublicationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.outbox = self.root / "outbox"
        self.outbox.mkdir(mode=0o700)
        self.mapping_path = self.root / "recipients.json"
        address = "owner" + "@" + "example.invalid"
        self.mapping_path.write_text(
            '{"schema_version":"skillops.private-recipient-mapping.v1",'
            '"mappings":[{"recipient_ref":"owner-primary","provider_target":"'
            + address
            + '"}]}',
            encoding="utf-8",
        )
        os.chmod(self.mapping_path, 0o600)
        self.mapping = RecipientMapping.load(self.mapping_path, "owner-primary")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def notifier(self, transport):
        return TransactionalNotifier(
            self.outbox,
            context().contract,
            CANDIDATE_DIGEST,
            clock(),
            transport,
        )

    def notify(self, transport, **extra):
        arguments = dict(
            notification_uid=uid("ntf", 1),
            auto_transaction_uid=uid("atx", 1),
            timing="PRE_WRITE",
            mapping=self.mapping,
            subject="SkillOps activation",
            body="Candidate activation transport request.",
            public_metadata={
                "impact": "MAJOR",
                "change_code": "ACTIVE_BUNDLE_CHANGE",
                "planned_action": "ACTIVATE",
                "affected_path_refs": ["CodexSkills/VERSION"],
                "evidence_digests": ["1" * 64],
            },
            entropy=(3).to_bytes(10, "big"),
        )
        arguments.update(extra)
        return self.notifier(transport).notify_major(**arguments)

    def test_recipient_mapping_requires_owner_only_permissions(self) -> None:
        os.chmod(self.mapping_path, 0o644)
        with self.assertRaisesRegex(AutoRuntimeError, "RECIPIENT_MAPPING_PERMISSIONS_TOO_BROAD"):
            RecipientMapping.load(self.mapping_path, "owner-primary")

    def test_planned_major_requires_provider_sent_not_owner_approval(self) -> None:
        outcome = self.notify(FakeNotificationTransport())
        self.assertTrue(outcome.planned_write_allowed)
        self.assertEqual(outcome.receipt["provider_status"], "SENT")
        self.assertFalse(outcome.receipt["approval_required"])
        self.assertFalse(outcome.receipt["owner_reply_required"])

    def test_provider_failure_blocks_planned_write(self) -> None:
        outcome = self.notify(FakeNotificationTransport("PROVIDER_TIMEOUT"))
        self.assertFalse(outcome.planned_write_allowed)
        self.assertEqual(outcome.receipt["provider_status"], "FAILED")
        self.assertEqual(outcome.receipt["failure_code"], "PROVIDER_TIMEOUT")

    def test_crash_after_send_reconciles_without_duplicate(self) -> None:
        transport = FakeNotificationTransport()

        def crash(stage):
            if stage == "AFTER_PROVIDER_SEND":
                raise RuntimeError("synthetic crash")

        with self.assertRaisesRegex(RuntimeError, "synthetic crash"):
            self.notify(transport, failpoint=crash)
        outcome = self.notify(transport)
        self.assertEqual(transport.send_count, 1)
        self.assertEqual(outcome.receipt["provider_status"], "SENT")

    def test_actual_provider_target_never_enters_public_receipt(self) -> None:
        outcome = self.notify(FakeNotificationTransport())
        serialized = canonicalize_object(outcome.receipt)
        self.assertNotIn(self.mapping.provider_target.encode("utf-8"), serialized)
        self.assertEqual(outcome.receipt["recipient_ref"], "owner-primary")

    def activation_request(self, backend, **changes):
        artifact = PublicationArtifact(
            "REGISTRY",
            "urn:linzecolin:agentdatabase:skillops:schema:artifact-envelope:v1",
            uid("env", 9),
            "CodexSkills/VERSION",
            b"v0.0.0.3\n",
        )
        data = dict(
            auto_transaction_uid=uid("atx", 9),
            authority="COORDINATED_ACTIVATION",
            trust_mode="CANDIDATE",
            expected_remote_head=backend.head,
            commit_message="Activate SkillOps candidate",
            artifacts=(artifact,),
            shared_gates=gates(),
            notification_provider_status="SENT",
            activation_envelope_verified=True,
            activation_envelope_digest="d" * 64,
            activation_artifact_digests={
                "CodexSkills/VERSION": hashlib.sha256(b"v0.0.0.3\n").hexdigest()
            },
        )
        data.update(changes)
        return PublicationRequest(**data)

    def publisher(self, backend):
        return PhysicalPublisher(
            context().contract,
            CANDIDATE_DIGEST,
            backend,
            trusted_mode="CANDIDATE",
        )

    def test_candidate_runtime_publication_is_impossible(self) -> None:
        backend = FakeGitBackend()
        request = self.activation_request(backend, authority="CANDIDATE_TEST")
        with self.assertRaisesRegex(AutoRuntimeError, "CANDIDATE_CANONICAL_PUBLICATION_FORBIDDEN"):
            self.publisher(backend).publish(request)
        self.assertFalse(backend.cleaned)

    def test_active_request_cannot_self_promote_candidate_context(self) -> None:
        backend = FakeGitBackend()
        request = self.activation_request(
            backend,
            authority="ACTIVE_RUNTIME",
            trust_mode="ACTIVE",
        )
        with self.assertRaisesRegex(AutoRuntimeError, "PUBLICATION_TRUST_CONTEXT_MISMATCH"):
            self.publisher(backend).publish(request)

    def test_activation_requires_real_sent_receipt_and_verified_envelope(self) -> None:
        backend = FakeGitBackend()
        with self.assertRaisesRegex(AutoRuntimeError, "ACTIVATION_MAJOR_NOTIFICATION_REQUIRED"):
            self.publisher(backend).publish(
                self.activation_request(backend, notification_provider_status="FAILED")
            )
        with self.assertRaisesRegex(AutoRuntimeError, "ACTIVATION_ENVELOPE_REQUIRED"):
            self.publisher(backend).publish(
                self.activation_request(backend, activation_envelope_verified=False)
            )

    def test_activation_publish_is_ff_only_and_remote_readback_verified(self) -> None:
        backend = FakeGitBackend()
        readback = self.publisher(backend).publish(self.activation_request(backend))
        self.assertTrue(readback.verified)
        self.assertEqual(backend.head, backend.last_commit)
        self.assertTrue(backend.cleaned)
        self.assertIn("SkillOps-Auto-Transaction", backend.message)

    def test_remote_race_and_path_drift_block_before_settlement(self) -> None:
        backend = FakeGitBackend()
        request = self.activation_request(backend)
        backend.head = "sha1:" + "c" * 40
        with self.assertRaisesRegex(AutoRuntimeError, "REMOTE_HEAD_CHANGED"):
            self.publisher(backend).publish(request)

        backend = FakeGitBackend()
        backend.changed_override = ("CodexSkills/VERSION", "outside.txt")
        with self.assertRaisesRegex(AutoRuntimeError, "PUBLICATION_CHANGED_PATH_SET_MISMATCH"):
            self.publisher(backend).publish(self.activation_request(backend))
        self.assertTrue(backend.cleaned)

    def test_push_success_crash_reconciles_exact_transaction_once(self) -> None:
        backend = FakeGitBackend()
        request = self.activation_request(backend)
        backend.fail_readback_once = True
        with self.assertRaisesRegex(RuntimeError, "synthetic post-push crash"):
            self.publisher(backend).publish(request)
        self.assertEqual(backend.head, backend.last_commit)
        recovered = self.publisher(backend).publish(request)
        self.assertTrue(recovered.verified)
        self.assertEqual(recovered.commit, backend.last_commit)

    def test_shared_privacy_gate_failure_blocks_all_lanes(self) -> None:
        backend = FakeGitBackend()
        failed = gates()
        failed["PRIVACY"] = "FAIL"
        with self.assertRaisesRegex(AutoRuntimeError, "PUBLICATION_SHARED_GATE_FAILED:PRIVACY"):
            self.publisher(backend).publish(
                self.activation_request(backend, shared_gates=failed)
            )


if __name__ == "__main__":
    unittest.main()
