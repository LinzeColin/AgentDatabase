from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from memory_atlas_cli.credential_exclusion import (  # noqa: E402
    BLOCKED_ACCOUNT_CONTROL_CATEGORIES,
    CREDENTIAL_CONTRACT_PATH,
    CREDENTIAL_SCHEMA_VERSION,
    CredentialExclusionError,
    POLICY_ID,
    forbidden_public_raw_path_match,
    load_credential_exclusion_contract,
    validate_credential_exclusion_contract,
)
from memory_atlas_cli.source_registry import load_source_registry  # noqa: E402
from privacy_guard import (  # noqa: E402
    credential_exclusion_hits,
    high_risk_secret_hits,
    redact_credentials_in_text,
    scan_repo_privacy,
)
from public_raw_sanitizer import sanitize_public_text, sanitize_public_value  # noqa: E402


def canonical_contract() -> dict:
    return json.loads((ROOT / CREDENTIAL_CONTRACT_PATH).read_text(encoding="utf-8"))


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")


class CredentialExclusionContractTests(unittest.TestCase):
    def test_canonical_contract_has_exact_identity_and_account_control_boundary(self) -> None:
        contract = load_credential_exclusion_contract(ROOT)

        self.assertEqual(contract["schema_version"], CREDENTIAL_SCHEMA_VERSION)
        self.assertEqual(contract["task_id"], "S06-P1-T3")
        self.assertEqual(contract["policy_id"], POLICY_ID)
        self.assertEqual(
            contract["blocked_account_control_categories"],
            list(BLOCKED_ACCOUNT_CONTROL_CATEGORIES),
        )
        self.assertIs(contract["public_raw_policy"]["plaintext_transcript_allowed"], True)
        self.assertIs(contract["public_raw_policy"]["ordinary_transcript_blocked"], False)
        self.assertIs(contract["public_raw_policy"]["broad_privacy_redaction"], False)
        self.assertIs(contract["enforcement"]["source_bytes_mutated"], False)
        self.assertIs(contract["enforcement"]["credential_value_echo"], False)

    def test_contract_rejects_broad_redaction_category_and_enforcement_drift(self) -> None:
        mutations = []
        broad_redaction = copy.deepcopy(canonical_contract())
        broad_redaction["public_raw_policy"]["broad_privacy_redaction"] = True
        mutations.append(broad_redaction)
        missing_category = copy.deepcopy(canonical_contract())
        missing_category["blocked_account_control_categories"].pop()
        mutations.append(missing_category)
        mutating_scan = copy.deepcopy(canonical_contract())
        mutating_scan["enforcement"]["source_bytes_mutated"] = True
        mutations.append(mutating_scan)

        for payload in mutations:
            with self.subTest(payload=payload), self.assertRaises(CredentialExclusionError):
                validate_credential_exclusion_contract(payload)

    def test_source_registry_activates_one_canonical_contract_for_every_source(self) -> None:
        registry = load_source_registry(ROOT)

        self.assertEqual(
            registry["sync_contract"]["credential_exclusion_ref"],
            CREDENTIAL_CONTRACT_PATH.as_posix(),
        )
        for source in registry["sync_sources"]:
            self.assertEqual(
                source["credential_exclusions"],
                {
                    "policy": POLICY_ID,
                    "contract_ref": CREDENTIAL_CONTRACT_PATH.as_posix(),
                    "status": "active",
                },
            )

    def test_public_raw_preserves_ordinary_transcript_and_safe_placeholders(self) -> None:
        transcript = (
            "Contact owner@example.com or +61 412 345 678. Discuss password policy, "
            "token budget, and cookie recipes. api_key=not_configured; your_token=redacted; "
            "pwd=\"working directory\"."
        )

        sanitized, counts = sanitize_public_text(transcript)

        self.assertEqual(sanitized, transcript)
        self.assertEqual(counts, {})
        structured = {
            "email": "owner@example.com",
            "phone": "+61 412 345 678",
            "password": "not_configured",
            "pwd": "/workspace/project",
            "cookie": "chocolate chip recipe",
        }
        self.assertEqual(sanitize_public_value(structured), (structured, {}))

    def test_all_seven_account_control_categories_are_detected_without_value_echo(self) -> None:
        begin_private = "-----BEGIN " + "PRIVATE KEY-----"
        end_private = "-----END " + "PRIVATE KEY-----"
        credential_values = {
            "api_keys": "api_key=" + "ApiValue123456789",
            "cookies": "cookie: sid=" + "CookieValue123456",
            "session_tokens": "session_token=" + "SessionValue123456",
            "passwords": "password=\"" + "Password Value 123456" + "\"",
            "private_keys": begin_private + "\n" + "A" * 32 + "\n" + end_private,
            "oauth_tokens": "access_token=" + "OauthValue12345678",
            "browser_credential_store": "login_data=" + "EncryptedVault123456",
        }
        transcript = "\n".join(credential_values.values())

        hits = credential_exclusion_hits(transcript, "fixture.jsonl")
        sanitized, counts = redact_credentials_in_text(transcript)
        serialized_hits = json.dumps(hits, ensure_ascii=False, sort_keys=True)

        self.assertEqual({hit["category"] for hit in hits}, set(BLOCKED_ACCOUNT_CONTROL_CATEGORIES))
        self.assertEqual(set(counts), set(BLOCKED_ACCOUNT_CONTROL_CATEGORIES))
        self.assertEqual(sanitized.count("[REDACTED_CREDENTIAL]"), 7)
        for value in credential_values.values():
            self.assertNotIn(value, sanitized)
            self.assertNotIn(value, serialized_hits)
        self.assertNotIn("ApiValue123456789", serialized_hits)

        structured = {
            "api_key": "ApiValue123456789",
            "cookie": "sid=CookieValue123456",
            "session_token": "SessionValue123456",
            "password": "Password Value 123456",
            "private_key": "PrivateMaterial123456",
            "access_token": "OauthValue12345678",
            "login_data": {"encrypted": "EncryptedVault123456"},
        }
        sanitized_structured, structured_counts = sanitize_public_value(structured)
        repeated_structured, repeated_counts = sanitize_public_value(sanitized_structured)

        self.assertEqual(set(structured_counts), set(BLOCKED_ACCOUNT_CONTROL_CATEGORIES))
        self.assertTrue(
            all(value == "[REDACTED_CREDENTIAL]" for value in sanitized_structured.values())
        )
        self.assertEqual(repeated_structured, sanitized_structured)
        self.assertEqual(repeated_counts, {})

        pwd_assignment = "pwd=\"" + "Password Value 123456" + "\""
        pwd_sanitized, pwd_counts = sanitize_public_text(pwd_assignment)
        self.assertEqual(pwd_sanitized, "[REDACTED_CREDENTIAL]")
        self.assertEqual(pwd_counts, {"passwords": 1})

    def test_credential_like_paths_are_blocked_but_conversation_paths_are_allowed(self) -> None:
        contract = canonical_contract()
        blocked = (
            "chatgpt/.env",
            "codex/Login Data.sqlite",
            "agents/reviewer/id_rsa",
            "agents/reviewer/export.p12",
        )
        allowed = (
            "chatgpt/conversation.abc123.json",
            "codex/sessions/session.abc123.part-0001.jsonl",
        )

        self.assertTrue(all(forbidden_public_raw_path_match(path, contract) for path in blocked))
        self.assertTrue(all(forbidden_public_raw_path_match(path, contract) is None for path in allowed))

        with tempfile.TemporaryDirectory() as temp_dir:
            database = Path(temp_dir)
            write_json(database / CREDENTIAL_CONTRACT_PATH, contract)
            (database / ".gitignore").write_text(
                "*.zip\ndata/raw/\ndata/raw_encrypted/\ndata/private_imports/\n",
                encoding="utf-8",
            )
            staged_path = database / "data/public_raw/codex/.env"
            staged_path.parent.mkdir(parents=True, exist_ok=True)
            staged_path.write_text("ordinary fixture without a credential value\n", encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=database, check=True)
            subprocess.run(
                ["git", "add", "-f", ".gitignore", CREDENTIAL_CONTRACT_PATH.as_posix(), staged_path.relative_to(database).as_posix()],
                cwd=database,
                check=True,
            )

            staged_scan = scan_repo_privacy(database)

        self.assertEqual(staged_scan["status"], "FAIL")
        self.assertEqual(staged_scan["credential_like_path_hit_count"], 1)
        self.assertEqual(staged_scan["credential_like_path_hits"][0]["pattern"], ".env")

    def test_large_public_raw_scan_does_not_skip_or_mutate_source_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database = Path(temp_dir)
            relative = "data/public_raw/codex/large.jsonl"
            path = database / relative
            credential = "password=" + "LargeFixtureSecret123456"
            payload = ("ordinary transcript " * 70_000 + credential).encode("utf-8")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
            before = hashlib.sha256(path.read_bytes()).hexdigest()

            hits = high_risk_secret_hits(database, [relative])
            after = hashlib.sha256(path.read_bytes()).hexdigest()

        self.assertGreater(len(payload), 1_000_000)
        self.assertEqual(hits, [{"path": relative, "pattern": "passwords"}])
        self.assertEqual(after, before)

    def test_invalid_contract_cli_fails_closed_without_path_traceback_or_secret_echo(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database = Path(temp_dir)
            invalid = canonical_contract()
            invalid["public_raw_policy"]["broad_privacy_redaction"] = True
            write_json(database / CREDENTIAL_CONTRACT_PATH, invalid)

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "privacy_guard.py"),
                    "--database-dir",
                    str(database),
                    "--scan-only",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(payload["status"], "FAIL_CLOSED")
        self.assertEqual(payload["error"], "credential_exclusion_contract_invalid")
        self.assertNotIn(temp_dir, result.stdout + result.stderr)
        self.assertNotIn("Traceback", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
