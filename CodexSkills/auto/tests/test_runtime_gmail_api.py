from __future__ import annotations

import base64
import json
import os
import tempfile
import unittest
from email.parser import BytesParser
from email.policy import default
from pathlib import Path
from unittest import mock

from CodexSkills.auto.runtime.core import (
    AutoRuntimeError,
    atomic_write_json,
    format_utc,
    read_json,
)
from CodexSkills.auto.runtime.gmail_api import (
    GMAIL_CONFIG_SCHEMA,
    GmailApiClient,
    GmailApiConfig,
    GmailApiNotificationTransport,
    GmailProviderError,
    NotificationPathContract,
    StdlibGmailApiClient,
)
from CodexSkills.auto.runtime.notification import (
    FakeNotificationTransport,
    RecipientMapping,
    TransactionalNotifier,
    render_major_email,
)
from CodexSkills.auto.runtime.roots import prepare_state_root
from CodexSkills.auto.runtime.state import StateLayout
from CodexSkills.governance.tools.canonical_json import canonicalize_object

from runtime_helpers import CANDIDATE_DIGEST, REPO_ROOT, clock, context, uid


class FakeGmailApiClient(GmailApiClient):
    def __init__(self) -> None:
        self.messages = {}
        self.send_count = 0
        self.ambiguous = False
        self.failure_code = None

    def _raise_if_failed(self):
        if self.failure_code is not None:
            raise GmailProviderError(self.failure_code)

    def profile(self):
        self._raise_if_failed()
        return {"emailAddress": "owner@example.invalid", "messagesTotal": 1}

    def list_messages(self, query, max_results):
        self._raise_if_failed()
        matches = []
        expected = query.removeprefix("in:sent rfc822msgid:")
        for message_id, message in self.messages.items():
            headers = {
                row["name"].lower(): row["value"]
                for row in message["payload"]["headers"]
            }
            if headers.get("message-id") == expected:
                matches.append({"id": message_id})
        if self.ambiguous and matches:
            matches.append({"id": "duplicate-provider-message"})
        return {"messages": matches[:max_results], "resultSizeEstimate": len(matches)}

    def get_message_metadata(self, message_id):
        self._raise_if_failed()
        return self.messages.get(message_id, {"id": message_id, "payload": {"headers": []}})

    def send_raw_message(self, raw_message):
        self._raise_if_failed()
        self.send_count += 1
        padded = raw_message + "=" * (-len(raw_message) % 4)
        parsed = BytesParser(policy=default).parsebytes(
            base64.urlsafe_b64decode(padded.encode("ascii"))
        )
        provider_message_id = "provider-message-" + str(self.send_count)
        headers = []
        for name in (
            "Message-ID",
            "X-SkillOps-Correlation-Digest",
            "X-SkillOps-Private-Payload-Digest",
        ):
            headers.append({"name": name, "value": str(parsed[name])})
        self.messages[provider_message_id] = {
            "id": provider_message_id,
            "payload": {"headers": headers},
        }
        return {"id": provider_message_id, "threadId": "private-thread"}


class FakeHttpResponse:
    def __init__(self, value, status=200):
        self.payload = json.dumps(value, separators=(",", ":")).encode("utf-8")
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, _kind, _value, _traceback):
        return False

    def getcode(self):
        return self.status

    def read(self, limit):
        return self.payload[:limit]


class GmailApiTransportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name)
        self.source = self.base / "source"
        self.source.mkdir()
        prepared = prepare_state_root(
            self.base / "state",
            repo_root=REPO_ROOT,
            protected_roots=[self.source],
        )
        self.layout = StateLayout.create(prepared)
        self.paths = NotificationPathContract.resolve(
            prepared,
            repo_root=REPO_ROOT,
        )
        self.mapping_path = self.paths.recipient_mapping_path
        self.config_path = self.paths.gmail_config_path
        address = "owner" + "@" + "example.invalid"
        self.mapping_path.write_text(
            '{"schema_version":"skillops.private-recipient-mapping.v1",'
            '"mappings":[{"recipient_ref":"owner-primary","provider_target":"'
            + address
            + '"}]}',
            encoding="utf-8",
        )
        os.chmod(self.mapping_path, 0o600)
        self.config_path.write_text(
            '{"schema_version":"' + GMAIL_CONFIG_SCHEMA + '",'
            '"client_id":"test-client",'
            '"client_secret":"test-secret",'
            '"refresh_token":"test-refresh",'
            '"required_scopes":['
            '"https://www.googleapis.com/auth/gmail.readonly",'
            '"https://www.googleapis.com/auth/gmail.send"],'
            '"user_id":"me"}',
            encoding="utf-8",
        )
        os.chmod(self.config_path, 0o600)
        self.mapping = RecipientMapping.load(self.mapping_path, "owner-primary")
        self.config = GmailApiConfig.load(self.config_path)
        self.client = FakeGmailApiClient()
        self.transport = GmailApiNotificationTransport(
            self.config,
            client=self.client,
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def metadata(self):
        return {
            "impact": "MAJOR",
            "change_code": "ACTIVE_BUNDLE_CHANGE",
            "planned_action": "ACTIVATE",
            "affected_path_refs": ["CodexSkills/VERSION"],
            "evidence_digests": ["1" * 64],
            "rollback_target_ref": "sha1:" + "2" * 40,
        }

    def notify(self, transport=None, failpoint=None):
        rendered = render_major_email(
            srv_revision="v0.0.0.3",
            auto_transaction_uid=uid("atx", 1),
            observed_at=format_utc(clock().now()),
            remote_baseline="sha1:" + "2" * 40,
            public_metadata=self.metadata(),
        )
        notifier = TransactionalNotifier(
            self.layout.outbox,
            context().contract,
            CANDIDATE_DIGEST,
            clock(),
            transport or self.transport,
        )
        return notifier.notify_major(
            notification_uid=uid("ntf", 1),
            auto_transaction_uid=uid("atx", 1),
            timing="PRE_WRITE",
            mapping=self.mapping,
            subject=rendered.subject,
            body=rendered.body,
            public_metadata=self.metadata(),
            entropy=(7).to_bytes(10, "big"),
            failpoint=failpoint,
        )

    def test_external_path_contract_and_owner_only_files(self) -> None:
        refs = self.paths.public_refs()
        self.assertEqual(
            refs["gmail_config_ref"],
            "state-root/private/notification/gmail-api.v1.json",
        )
        self.assertNotIn(str(self.base), canonicalize_object(refs).decode("utf-8"))
        os.chmod(self.config_path, 0o644)
        with self.assertRaisesRegex(
            AutoRuntimeError,
            "GMAIL_PRIVATE_FILE_PERMISSIONS_TOO_BROAD",
        ):
            GmailApiConfig.load(self.config_path)

    def test_state_root_cannot_contain_repository(self) -> None:
        fake_repository = self.paths.state_root / "nested-repository"
        fake_repository.mkdir()
        with self.assertRaisesRegex(
            AutoRuntimeError,
            "NOTIFICATION_STATE_ROOT_REPOSITORY_OVERLAP",
        ):
            NotificationPathContract.resolve(
                self.paths.state_root,
                repo_root=fake_repository,
            )

    def test_preflight_returns_only_sanitized_capability(self) -> None:
        capability = self.transport.preflight(self.mapping.provider_target)
        self.assertEqual(capability["provider_code"], "GMAIL_API")
        self.assertTrue(capability["recipient_binding_verified"])
        serialized = canonicalize_object(capability)
        self.assertNotIn(self.mapping.provider_target.encode("utf-8"), serialized)
        self.assertNotIn(self.config.client_secret.encode("utf-8"), serialized)

    def test_preflight_requires_authenticated_profile_to_match_owner_mapping(self) -> None:
        with self.assertRaisesRegex(
            AutoRuntimeError,
            "GMAIL_PREFLIGHT_RECIPIENT_BINDING_MISMATCH",
        ):
            self.transport.preflight("different@example.invalid")

    def test_stdlib_client_refreshes_with_required_scopes_and_bearer_header(self) -> None:
        responses = [
            FakeHttpResponse(
                {
                    "access_token": "private-access-token",
                    "token_type": "Bearer",
                    "scope": " ".join(self.config.required_scopes),
                }
            ),
            FakeHttpResponse(
                {
                    "emailAddress": "owner@example.invalid",
                    "messagesTotal": 1,
                }
            ),
        ]
        with mock.patch(
            "CodexSkills.auto.runtime.gmail_api.urllib.request.urlopen",
            side_effect=responses,
        ) as opened:
            profile = StdlibGmailApiClient(self.config).profile()
        self.assertEqual(profile["messagesTotal"], 1)
        token_request = opened.call_args_list[0].args[0]
        profile_request = opened.call_args_list[1].args[0]
        self.assertEqual(token_request.full_url, "https://oauth2.googleapis.com/token")
        self.assertEqual(token_request.get_method(), "POST")
        self.assertNotIn(self.config.client_secret, profile_request.full_url)
        self.assertEqual(
            profile_request.get_header("Authorization"),
            "Bearer private-access-token",
        )

    def test_stdlib_client_rejects_token_without_query_scope(self) -> None:
        response = FakeHttpResponse(
            {
                "access_token": "private-access-token",
                "token_type": "Bearer",
                "scope": "https://www.googleapis.com/auth/gmail.send",
            }
        )
        with mock.patch(
            "CodexSkills.auto.runtime.gmail_api.urllib.request.urlopen",
            return_value=response,
        ):
            with self.assertRaisesRegex(
                GmailProviderError,
                "CREDENTIAL_UNAVAILABLE",
            ):
                StdlibGmailApiClient(self.config).profile()

    def test_send_requires_provider_metadata_readback(self) -> None:
        outcome = self.notify()
        self.assertTrue(outcome.planned_write_allowed)
        self.assertEqual(outcome.receipt["provider_status"], "SENT")
        self.assertRegex(outcome.receipt["provider_receipt_ref"], r"^gmail-[0-9a-f]{24}$")
        self.assertEqual(self.client.send_count, 1)
        public = canonicalize_object(outcome.receipt)
        self.assertNotIn(self.mapping.provider_target.encode("utf-8"), public)

    def test_crash_after_send_recovers_by_rfc822_lookup_without_duplicate(self) -> None:
        def crash(stage):
            if stage == "AFTER_PROVIDER_SEND":
                raise RuntimeError("synthetic post-provider crash")

        with self.assertRaisesRegex(RuntimeError, "synthetic post-provider crash"):
            self.notify(failpoint=crash)
        recovered = self.notify()
        self.assertTrue(recovered.planned_write_allowed)
        self.assertEqual(self.client.send_count, 1)

    def test_sent_outbox_is_provider_reverified_before_reuse(self) -> None:
        self.notify()
        self.client.failure_code = "PROVIDER_TIMEOUT"
        observed = self.notify()
        self.assertFalse(observed.planned_write_allowed)
        self.assertEqual(observed.receipt["provider_status"], "FAILED")
        self.assertEqual(self.client.send_count, 1)

    def test_outbox_tamper_is_rejected_before_provider_call(self) -> None:
        self.notify()
        entry_path = self.layout.outbox / (uid("ntf", 1) + ".json")
        entry = dict(read_json(entry_path))
        entry["status"] = "PENDING"
        atomic_write_json(entry_path, entry)
        before = self.client.send_count
        with self.assertRaisesRegex(
            AutoRuntimeError,
            "NOTIFICATION_OUTBOX_DIGEST_MISMATCH",
        ):
            self.notify()
        self.assertEqual(self.client.send_count, before)

    def test_ambiguous_lookup_never_sends_again(self) -> None:
        self.notify()
        self.client.ambiguous = True
        entry = self.layout.outbox / (uid("ntf", 1) + ".json")
        entry.unlink()
        outcome = self.notify()
        self.assertFalse(outcome.planned_write_allowed)
        self.assertEqual(outcome.receipt["provider_status"], "UNKNOWN")
        self.assertEqual(self.client.send_count, 1)

    def test_provider_failure_during_lookup_blocks_without_send(self) -> None:
        self.client.failure_code = "PROVIDER_TIMEOUT"
        outcome = self.notify()
        self.assertFalse(outcome.planned_write_allowed)
        self.assertEqual(outcome.receipt["provider_status"], "FAILED")
        self.assertEqual(outcome.receipt["failure_code"], "PROVIDER_TIMEOUT")
        self.assertEqual(self.client.send_count, 0)

    def test_header_injection_is_rejected_before_send(self) -> None:
        result = self.transport.send(
            idempotency_key=uid("ntf", 1) + ":" + "1" * 64,
            provider_target=self.mapping.provider_target,
            subject="Unsafe\nBcc: injected@example.invalid",
            body="body",
        )
        self.assertEqual(result.status, "FAILED")
        self.assertEqual(result.failure_code, "PROVIDER_REJECTED")
        self.assertEqual(self.client.send_count, 0)

    def test_template_rejects_invalid_calendar_timestamp(self) -> None:
        with self.assertRaisesRegex(AutoRuntimeError, "UTC_TIMESTAMP_INVALID"):
            render_major_email(
                srv_revision="v0.0.0.3",
                auto_transaction_uid=uid("atx", 1),
                observed_at="2026-02-30T01:02:03.000000Z",
                remote_baseline="sha1:" + "2" * 40,
                public_metadata=self.metadata(),
            )

    def test_header_mismatch_never_becomes_sent(self) -> None:
        self.notify()
        message = next(iter(self.client.messages.values()))
        for header in message["payload"]["headers"]:
            if header["name"] == "X-SkillOps-Private-Payload-Digest":
                header["value"] = "f" * 64
        entry = self.layout.outbox / (uid("ntf", 1) + ".json")
        entry.unlink()
        outcome = self.notify()
        self.assertFalse(outcome.planned_write_allowed)
        self.assertEqual(outcome.receipt["provider_status"], "UNKNOWN")
        self.assertEqual(self.client.send_count, 1)

    def test_non_not_found_lookup_never_invokes_fake_send(self) -> None:
        class UnknownLookupFake(FakeNotificationTransport):
            def lookup(self, idempotency_key):
                from CodexSkills.auto.runtime.notification import ProviderResult

                return ProviderResult("UNKNOWN", failure_code="RECEIPT_UNVERIFIED")

        transport = UnknownLookupFake()
        outcome = self.notify(transport=transport)
        self.assertFalse(outcome.planned_write_allowed)
        self.assertEqual(transport.send_count, 0)


if __name__ == "__main__":
    unittest.main()
