"""Production Gmail API notification transport.

Credentials and the actual recipient mapping are loaded only from owner-only
files below the repo-external SkillOps state root.  The transport never logs or
returns either value.  A deterministic RFC822 Message-ID plus a private
payload-digest header provide provider-side lookup and crash reconciliation.
"""

from __future__ import annotations

import base64
import hashlib
import os
import re
import socket
import stat
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from email.message import EmailMessage
from email.policy import SMTP
from pathlib import Path
from typing import Any, Mapping, Optional

from CodexSkills.governance.tools.canonical_json import parse_json_bytes

from .core import AutoRuntimeError
from .notification import EMAIL_RE, NotificationTransport, ProviderResult


GMAIL_CONFIG_SCHEMA = "skillops.private-gmail-api-config.v1"
GMAIL_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
GMAIL_API_ORIGIN = "https://gmail.googleapis.com"
GMAIL_USER_ID = "me"
GMAIL_MESSAGE_ID_DOMAIN = "notification.skillops.invalid"
GMAIL_CORRELATION_HEADER = "X-SkillOps-Correlation-Digest"
GMAIL_PAYLOAD_HEADER = "X-SkillOps-Private-Payload-Digest"
GMAIL_PROVIDER_CODE = "GMAIL_API"
GMAIL_PREFLIGHT_QUERY_MESSAGE_ID = (
    "<skillops-query-capability-v1@notification.skillops.invalid>"
)
GMAIL_PREFLIGHT_QUERY = (
    "in:sent rfc822msgid:" + GMAIL_PREFLIGHT_QUERY_MESSAGE_ID
)
GMAIL_PREFLIGHT_QUERY_MAX_RESULTS = 1
GMAIL_SEND_SCOPES = {
    "https://mail.google.com/",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.send",
}
GMAIL_QUERY_SCOPES = {
    "https://mail.google.com/",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.readonly",
}
PRIVATE_NOTIFICATION_RELATIVE = Path("private") / "notification"
RECIPIENT_MAPPING_NAME = "recipient-mapping.v1.json"
GMAIL_CONFIG_NAME = "gmail-api.v1.json"
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
GMAIL_PROVIDER_MESSAGE_REF_RE = re.compile(r"^[A-Za-z0-9_-]{1,256}$")
SAFE_CONFIG_VALUE_RE = re.compile(r"^[^\x00-\x1f\x7f]{1,4096}$")
MAX_PROVIDER_RESPONSE_BYTES = 1024 * 1024


def _private_regular_file(path: Path, unavailable_code: str) -> bytes:
    try:
        info = os.lstat(str(path))
    except OSError as exc:
        raise AutoRuntimeError(unavailable_code) from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise AutoRuntimeError("GMAIL_PRIVATE_FILE_NOT_REGULAR")
    if stat.S_IMODE(info.st_mode) & 0o077:
        raise AutoRuntimeError("GMAIL_PRIVATE_FILE_PERMISSIONS_TOO_BROAD")
    try:
        payload = path.read_bytes()
    except OSError as exc:
        raise AutoRuntimeError(unavailable_code) from exc
    if not payload or len(payload) > 256 * 1024:
        raise AutoRuntimeError("GMAIL_PRIVATE_FILE_SIZE_INVALID")
    return payload


def _private_directory(path: Path, code: str) -> Path:
    try:
        info = os.lstat(str(path))
    except OSError as exc:
        raise AutoRuntimeError(code) from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise AutoRuntimeError("GMAIL_PRIVATE_DIRECTORY_NOT_REAL")
    if stat.S_IMODE(info.st_mode) & 0o077:
        raise AutoRuntimeError("GMAIL_PRIVATE_DIRECTORY_PERMISSIONS_TOO_BROAD")
    try:
        return path.resolve(strict=True)
    except OSError as exc:
        raise AutoRuntimeError(code) from exc


@dataclass(frozen=True)
class NotificationPathContract:
    """Exact repo-external locations; only relative refs are public/documented."""

    state_root: Path
    private_notification_root: Path
    outbox_path: Path
    recipient_mapping_path: Path
    gmail_config_path: Path

    @classmethod
    def resolve(
        cls,
        state_root: Path,
        *,
        repo_root: Optional[Path] = None,
    ) -> "NotificationPathContract":
        if not state_root.is_absolute():
            raise AutoRuntimeError("NOTIFICATION_STATE_ROOT_MUST_BE_ABSOLUTE")
        root = _private_directory(state_root, "NOTIFICATION_STATE_ROOT_UNAVAILABLE")
        if repo_root is not None:
            try:
                repository = repo_root.resolve(strict=True)
                common = Path(os.path.commonpath((str(root), str(repository))))
            except (OSError, ValueError) as exc:
                raise AutoRuntimeError("NOTIFICATION_REPOSITORY_ROOT_INVALID") from exc
            if common in {root, repository}:
                raise AutoRuntimeError("NOTIFICATION_STATE_ROOT_REPOSITORY_OVERLAP")
        private_root = _private_directory(
            root / PRIVATE_NOTIFICATION_RELATIVE,
            "NOTIFICATION_PRIVATE_ROOT_UNAVAILABLE",
        )
        outbox = _private_directory(
            root / "outbox",
            "NOTIFICATION_OUTBOX_UNAVAILABLE",
        )
        try:
            private_root.relative_to(root)
        except ValueError as exc:
            raise AutoRuntimeError("NOTIFICATION_PRIVATE_ROOT_ESCAPES_STATE") from exc
        return cls(
            root,
            private_root,
            outbox,
            private_root / RECIPIENT_MAPPING_NAME,
            private_root / GMAIL_CONFIG_NAME,
        )

    @staticmethod
    def public_refs() -> Mapping[str, str]:
        return {
            "gmail_config_ref": (
                "state-root/private/notification/" + GMAIL_CONFIG_NAME
            ),
            "recipient_mapping_ref": (
                "state-root/private/notification/" + RECIPIENT_MAPPING_NAME
            ),
        }


@dataclass(frozen=True)
class GmailApiConfig:
    client_id: str
    client_secret: str
    refresh_token: str
    required_scopes: tuple[str, ...]
    user_id: str = GMAIL_USER_ID

    @classmethod
    def load(cls, path: Path) -> "GmailApiConfig":
        raw = _private_regular_file(path, "GMAIL_CREDENTIAL_UNAVAILABLE")
        try:
            value = parse_json_bytes(raw)
        except Exception as exc:
            raise AutoRuntimeError("GMAIL_CREDENTIAL_JSON_INVALID") from exc
        required = {
            "schema_version",
            "client_id",
            "client_secret",
            "refresh_token",
            "required_scopes",
            "user_id",
        }
        if not isinstance(value, dict) or set(value) != required:
            raise AutoRuntimeError("GMAIL_CREDENTIAL_SHAPE_INVALID")
        if (
            value.get("schema_version") != GMAIL_CONFIG_SCHEMA
            or value.get("user_id") != GMAIL_USER_ID
        ):
            raise AutoRuntimeError("GMAIL_CREDENTIAL_CONTRACT_INVALID")
        for field in ("client_id", "client_secret", "refresh_token"):
            field_value = value.get(field)
            if (
                not isinstance(field_value, str)
                or not SAFE_CONFIG_VALUE_RE.fullmatch(field_value)
            ):
                raise AutoRuntimeError("GMAIL_CREDENTIAL_VALUE_INVALID")
        scopes = value.get("required_scopes")
        if (
            not isinstance(scopes, list)
            or not scopes
            or any(not isinstance(item, str) for item in scopes)
            or scopes != sorted(set(scopes))
            or not set(scopes).issubset(GMAIL_SEND_SCOPES | GMAIL_QUERY_SCOPES)
            or not set(scopes).intersection(GMAIL_SEND_SCOPES)
            or not set(scopes).intersection(GMAIL_QUERY_SCOPES)
        ):
            raise AutoRuntimeError("GMAIL_CREDENTIAL_SCOPE_CONTRACT_INVALID")
        return cls(
            client_id=value["client_id"],
            client_secret=value["client_secret"],
            refresh_token=value["refresh_token"],
            required_scopes=tuple(scopes),
        )


class GmailProviderError(RuntimeError):
    """Sanitized provider error that contains only an allowlisted code."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class GmailApiClient:
    """Minimal provider client interface used by production and deterministic tests."""

    def profile(self) -> Mapping[str, Any]:
        raise NotImplementedError

    def list_messages(self, query: str, max_results: int) -> Mapping[str, Any]:
        raise NotImplementedError

    def get_message_metadata(self, message_id: str) -> Mapping[str, Any]:
        raise NotImplementedError

    def send_raw_message(self, raw_message: str) -> Mapping[str, Any]:
        raise NotImplementedError


class StdlibGmailApiClient(GmailApiClient):
    """Gmail REST client with a refresh token and no runtime dependencies."""

    def __init__(self, config: GmailApiConfig, *, timeout_seconds: int = 20) -> None:
        if timeout_seconds < 1 or timeout_seconds > 60:
            raise AutoRuntimeError("GMAIL_TIMEOUT_RANGE_INVALID")
        self.config = config
        self.timeout_seconds = timeout_seconds
        self._access_token: Optional[str] = None

    def _open_json(
        self,
        request: urllib.request.Request,
        *,
        credential_request: bool = False,
    ) -> Mapping[str, Any]:
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                status_code = int(response.getcode())
                payload = response.read(MAX_PROVIDER_RESPONSE_BYTES + 1)
        except urllib.error.HTTPError as exc:
            if exc.code in {408, 425, 429} or exc.code >= 500:
                raise GmailProviderError("PROVIDER_TIMEOUT") from None
            if exc.code in {401, 403} or credential_request:
                raise GmailProviderError("CREDENTIAL_UNAVAILABLE") from None
            raise GmailProviderError("PROVIDER_REJECTED") from None
        except (urllib.error.URLError, TimeoutError, socket.timeout):
            raise GmailProviderError("PROVIDER_TIMEOUT") from None
        except OSError:
            raise GmailProviderError("PROVIDER_TIMEOUT") from None
        if status_code < 200 or status_code >= 300:
            raise GmailProviderError("PROVIDER_REJECTED")
        if len(payload) > MAX_PROVIDER_RESPONSE_BYTES:
            raise GmailProviderError("PROVIDER_REJECTED")
        try:
            value = parse_json_bytes(payload)
        except Exception:
            raise GmailProviderError("PROVIDER_REJECTED") from None
        if not isinstance(value, dict):
            raise GmailProviderError("PROVIDER_REJECTED")
        return value

    def _token(self) -> str:
        if self._access_token is not None:
            return self._access_token
        body = urllib.parse.urlencode(
            {
                "client_id": self.config.client_id,
                "client_secret": self.config.client_secret,
                "refresh_token": self.config.refresh_token,
                "grant_type": "refresh_token",
            }
        ).encode("ascii")
        request = urllib.request.Request(
            GMAIL_TOKEN_ENDPOINT,
            data=body,
            method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response = self._open_json(request, credential_request=True)
        token = response.get("access_token")
        token_type = response.get("token_type")
        scope_text = response.get("scope")
        observed_scopes = (
            set(scope_text.split())
            if isinstance(scope_text, str)
            else set()
        )
        if (
            not isinstance(token, str)
            or not SAFE_CONFIG_VALUE_RE.fullmatch(token)
            or token_type != "Bearer"
            or not set(self.config.required_scopes).issubset(observed_scopes)
            or not observed_scopes.intersection(GMAIL_SEND_SCOPES)
            or not observed_scopes.intersection(GMAIL_QUERY_SCOPES)
        ):
            raise GmailProviderError("CREDENTIAL_UNAVAILABLE")
        self._access_token = token
        return token

    def _gmail_json(
        self,
        method: str,
        path: str,
        *,
        query: Optional[Mapping[str, object]] = None,
        body: Optional[bytes] = None,
    ) -> Mapping[str, Any]:
        if not path.startswith("/gmail/v1/users/me/") and path != "/gmail/v1/users/me/profile":
            raise GmailProviderError("PROVIDER_REJECTED")
        url = GMAIL_API_ORIGIN + path
        if query:
            url += "?" + urllib.parse.urlencode(query, doseq=True)
        headers = {"Authorization": "Bearer " + self._token()}
        if body is not None:
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(
            url,
            data=body,
            method=method,
            headers=headers,
        )
        return self._open_json(request)

    def profile(self) -> Mapping[str, Any]:
        return self._gmail_json("GET", "/gmail/v1/users/me/profile")

    def list_messages(self, query: str, max_results: int) -> Mapping[str, Any]:
        return self._gmail_json(
            "GET",
            "/gmail/v1/users/me/messages",
            query={
                "q": query,
                "maxResults": max_results,
                "includeSpamTrash": "false",
            },
        )

    def get_message_metadata(self, message_id: str) -> Mapping[str, Any]:
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,256}", message_id):
            raise GmailProviderError("PROVIDER_REJECTED")
        return self._gmail_json(
            "GET",
            "/gmail/v1/users/me/messages/" + message_id,
            query={
                "format": "metadata",
                "metadataHeaders": [
                    "Message-ID",
                    GMAIL_CORRELATION_HEADER,
                    GMAIL_PAYLOAD_HEADER,
                ],
            },
        )

    def send_raw_message(self, raw_message: str) -> Mapping[str, Any]:
        from CodexSkills.governance.tools.canonical_json import canonicalize_object

        body = canonicalize_object({"raw": raw_message})
        return self._gmail_json(
            "POST",
            "/gmail/v1/users/me/messages/send",
            body=body,
        )


class GmailApiNotificationTransport(NotificationTransport):
    """Concrete Gmail provider transport with remote readback before `SENT`."""

    def __init__(
        self,
        config: GmailApiConfig,
        *,
        client: Optional[GmailApiClient] = None,
    ) -> None:
        self.config = config
        self.client = client if client is not None else StdlibGmailApiClient(config)

    @staticmethod
    def _correlation(idempotency_key: str) -> tuple[str, str, str]:
        parts = idempotency_key.rsplit(":", 1)
        if len(parts) != 2 or not HEX64_RE.fullmatch(parts[1]):
            raise AutoRuntimeError("GMAIL_IDEMPOTENCY_KEY_INVALID")
        payload_digest = parts[1]
        correlation_digest = hashlib.sha256(idempotency_key.encode("utf-8")).hexdigest()
        message_id = (
            "<skillops-" + correlation_digest + "@" + GMAIL_MESSAGE_ID_DOMAIN + ">"
        )
        return payload_digest, correlation_digest, message_id

    @staticmethod
    def _safe_receipt_ref(provider_message_id: str) -> str:
        return "gmail-" + hashlib.sha256(
            provider_message_id.encode("utf-8")
        ).hexdigest()[:24]

    @staticmethod
    def _headers(message: Mapping[str, Any]) -> Mapping[str, str]:
        payload = message.get("payload")
        rows = payload.get("headers") if isinstance(payload, dict) else None
        if not isinstance(rows, list):
            return {}
        output = {}
        for row in rows:
            if not isinstance(row, dict):
                continue
            name = row.get("name")
            value = row.get("value")
            if isinstance(name, str) and isinstance(value, str):
                output[name.lower()] = value.strip()
        return output

    @staticmethod
    def _validate_query_capability_response(
        response: Mapping[str, Any],
    ) -> None:
        allowed_keys = {
            "messages",
            "nextPageToken",
            "resultSizeEstimate",
        }
        if not isinstance(response, dict) or not set(response).issubset(
            allowed_keys
        ):
            raise AutoRuntimeError(
                "GMAIL_PREFLIGHT_QUERY_RESPONSE_INVALID"
            )
        estimate = response.get("resultSizeEstimate")
        if estimate is not None and (
            not isinstance(estimate, int)
            or isinstance(estimate, bool)
            or estimate < 0
        ):
            raise AutoRuntimeError(
                "GMAIL_PREFLIGHT_QUERY_RESPONSE_INVALID"
            )
        messages = response.get("messages", [])
        if (
            not isinstance(messages, list)
            or len(messages) > GMAIL_PREFLIGHT_QUERY_MAX_RESULTS
            or (
                isinstance(estimate, int)
                and estimate < len(messages)
            )
        ):
            raise AutoRuntimeError(
                "GMAIL_PREFLIGHT_QUERY_RESPONSE_INVALID"
            )
        for message in messages:
            if (
                not isinstance(message, dict)
                or set(message) != {"id", "threadId"}
                or not GMAIL_PROVIDER_MESSAGE_REF_RE.fullmatch(
                    str(message.get("id", ""))
                )
                or not GMAIL_PROVIDER_MESSAGE_REF_RE.fullmatch(
                    str(message.get("threadId", ""))
                )
            ):
                raise AutoRuntimeError(
                    "GMAIL_PREFLIGHT_QUERY_RESPONSE_INVALID"
                )
        next_page = response.get("nextPageToken")
        if next_page is not None and (
            not isinstance(next_page, str)
            or not SAFE_CONFIG_VALUE_RE.fullmatch(next_page)
        ):
            raise AutoRuntimeError(
                "GMAIL_PREFLIGHT_QUERY_RESPONSE_INVALID"
            )

    def _verify_message(
        self,
        provider_message_id: str,
        *,
        payload_digest: str,
        correlation_digest: str,
        rfc822_message_id: str,
    ) -> ProviderResult:
        message = self.client.get_message_metadata(provider_message_id)
        if message.get("id") != provider_message_id:
            return ProviderResult("UNKNOWN", failure_code="RECEIPT_UNVERIFIED")
        headers = self._headers(message)
        if (
            headers.get("message-id") != rfc822_message_id
            or headers.get(GMAIL_CORRELATION_HEADER.lower()) != correlation_digest
            or headers.get(GMAIL_PAYLOAD_HEADER.lower()) != payload_digest
        ):
            return ProviderResult("UNKNOWN", failure_code="RECEIPT_UNVERIFIED")
        return ProviderResult(
            "SENT",
            provider_receipt_ref=self._safe_receipt_ref(provider_message_id),
        )

    def preflight(self, provider_target: Optional[str] = None) -> Mapping[str, object]:
        try:
            profile = self.client.profile()
        except GmailProviderError as exc:
            raise AutoRuntimeError("GMAIL_PREFLIGHT_" + exc.code) from exc
        profile_address = profile.get("emailAddress")
        if not isinstance(profile_address, str) or not EMAIL_RE.fullmatch(profile_address):
            raise AutoRuntimeError("GMAIL_PREFLIGHT_PROFILE_INVALID")
        if (
            provider_target is not None
            and profile_address.casefold() != provider_target.casefold()
        ):
            raise AutoRuntimeError("GMAIL_PREFLIGHT_RECIPIENT_BINDING_MISMATCH")
        try:
            query_response = self.client.list_messages(
                GMAIL_PREFLIGHT_QUERY,
                GMAIL_PREFLIGHT_QUERY_MAX_RESULTS,
            )
        except GmailProviderError as exc:
            raise AutoRuntimeError(
                "GMAIL_PREFLIGHT_QUERY_" + exc.code
            ) from exc
        self._validate_query_capability_response(query_response)
        return {
            "provider_code": GMAIL_PROVIDER_CODE,
            "authenticated_profile_verified": True,
            "recipient_binding_verified": provider_target is not None,
            "recipient_mode": "OWNER_MAPPING",
            "query_endpoint_verified": True,
            "metadata_readback_verified": False,
            "send_performed": False,
        }

    def lookup(self, idempotency_key: str) -> ProviderResult:
        payload_digest, correlation_digest, rfc822_message_id = self._correlation(
            idempotency_key
        )
        query = "in:sent rfc822msgid:" + rfc822_message_id
        try:
            result = self.client.list_messages(query, 2)
            messages = result.get("messages", [])
            if messages is None:
                messages = []
            if not isinstance(messages, list) or len(messages) > 1:
                return ProviderResult("UNKNOWN", failure_code="RECEIPT_UNVERIFIED")
            if not messages:
                return ProviderResult("NOT_FOUND")
            selected = messages[0]
            provider_message_id = selected.get("id") if isinstance(selected, dict) else None
            if not isinstance(provider_message_id, str):
                return ProviderResult("UNKNOWN", failure_code="RECEIPT_UNVERIFIED")
            return self._verify_message(
                provider_message_id,
                payload_digest=payload_digest,
                correlation_digest=correlation_digest,
                rfc822_message_id=rfc822_message_id,
            )
        except GmailProviderError as exc:
            return ProviderResult("FAILED", failure_code=exc.code)

    def send(
        self,
        *,
        idempotency_key: str,
        provider_target: str,
        subject: str,
        body: str,
    ) -> ProviderResult:
        if not EMAIL_RE.fullmatch(provider_target):
            return ProviderResult("FAILED", failure_code="PROVIDER_REJECTED")
        if (
            not isinstance(subject, str)
            or not subject
            or len(subject) > 998
            or any(ord(character) < 32 or ord(character) == 127 for character in subject)
        ):
            return ProviderResult("FAILED", failure_code="PROVIDER_REJECTED")
        if (
            not isinstance(body, str)
            or not body
            or len(body.encode("utf-8")) > 256 * 1024
            or any(
                (ord(character) < 32 and character not in {"\n", "\t"})
                or ord(character) == 127
                for character in body
            )
        ):
            return ProviderResult("FAILED", failure_code="PROVIDER_REJECTED")
        payload_digest, correlation_digest, rfc822_message_id = self._correlation(
            idempotency_key
        )
        observed = self.lookup(idempotency_key)
        if observed.status == "SENT":
            return observed
        if observed.status in {"FAILED", "UNKNOWN"}:
            return observed
        if observed.status != "NOT_FOUND":
            return ProviderResult("UNKNOWN", failure_code="RECEIPT_UNVERIFIED")
        message = EmailMessage()
        message["From"] = provider_target
        message["To"] = provider_target
        message["Subject"] = subject
        message["Message-ID"] = rfc822_message_id
        message[GMAIL_CORRELATION_HEADER] = correlation_digest
        message[GMAIL_PAYLOAD_HEADER] = payload_digest
        message.set_content(body)
        raw_message = base64.urlsafe_b64encode(
            message.as_bytes(policy=SMTP)
        ).decode("ascii").rstrip("=")
        try:
            response = self.client.send_raw_message(raw_message)
            provider_message_id = response.get("id")
            if not isinstance(provider_message_id, str):
                return ProviderResult("UNKNOWN", failure_code="RECEIPT_UNVERIFIED")
            return self._verify_message(
                provider_message_id,
                payload_digest=payload_digest,
                correlation_digest=correlation_digest,
                rfc822_message_id=rfc822_message_id,
            )
        except GmailProviderError as exc:
            return ProviderResult("FAILED", failure_code=exc.code)
