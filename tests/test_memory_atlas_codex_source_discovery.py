from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from memory_atlas_cli.codex_source_discovery import (  # noqa: E402
    CODEX_DISCOVERY_CONTRACT_PATH,
    EXPECTED_REGISTRY_CANDIDATES,
    EXPECTED_REGISTRY_RAW_PATHS,
    SCHEMA_VERSION,
    CodexRootSelection,
    CodexSourceDiscoveryError,
    build_codex_source_discovery,
    discover_codex_sources,
    load_codex_source_discovery_contract,
    resolve_codex_home,
    validate_codex_source_discovery_contract,
)
from memory_atlas_cli.credential_exclusion import (  # noqa: E402
    load_credential_exclusion_contract,
)
from memory_atlas_cli.source_registry import (  # noqa: E402
    load_source_registry,
    sync_source_map,
)


BODY_SENTINEL = "SOURCE_BODY_SENTINEL_93F1"


def write_bytes(path: Path, payload: bytes = b"fixture\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def make_codex_fixture(parent: Path, name: str = "codex-home") -> Path:
    root = parent / name
    root.mkdir(parents=True)
    write_bytes(root / "session_index.jsonl", f"{BODY_SENTINEL}\n".encode())
    write_bytes(root / "sessions/2026/active-a.jsonl")
    write_bytes(root / "sessions/active-b.jsonl")
    write_bytes(root / "archived_sessions/archive-a.jsonl")
    write_bytes(root / "history.jsonl")
    write_bytes(root / "transcription-history.jsonl")
    write_bytes(root / "log/client.jsonl")
    write_bytes(root / "logs/server.JSONL")
    write_bytes(root / "logs_2.sqlite", b"sqlite-root\n")
    write_bytes(root / "sqlite/logs_2.sqlite", b"sqlite-nested\n")

    write_bytes(root / "auth.json", f"{BODY_SENTINEL}-auth\n".encode())
    write_bytes(root / "config.toml", f"{BODY_SENTINEL}-config\n".encode())
    write_bytes(root / "installation_id", f"{BODY_SENTINEL}-installation\n".encode())
    write_bytes(root / "private_keys/key.pem", f"{BODY_SENTINEL}-key\n".encode())
    write_bytes(root / "mcp-oauth-locks/provider.lock", f"{BODY_SENTINEL}-oauth\n".encode())
    write_bytes(root / "browser/Login Data", f"{BODY_SENTINEL}-browser\n".encode())
    write_bytes(root / "sessions/cookies.jsonl", f"{BODY_SENTINEL}-cookie\n".encode())
    write_bytes(root / "sessions/private_keys/hidden.jsonl", f"{BODY_SENTINEL}-hidden\n".encode())
    return root


def file_evidence(root: Path) -> dict[str, tuple[int, int, str]]:
    evidence: dict[str, tuple[int, int, str]] = {}
    for path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file()):
        metadata = path.stat()
        evidence[path.relative_to(root).as_posix()] = (
            metadata.st_size,
            metadata.st_mtime_ns,
            hashlib.sha256(path.read_bytes()).hexdigest(),
        )
    return evidence


class CodexSourceDiscoveryTests(unittest.TestCase):
    def registered_codex_source(self) -> dict:
        return sync_source_map(load_source_registry(ROOT))["codex"]

    def test_canonical_contract_and_registry_define_one_portable_allowlist(self) -> None:
        contract = load_codex_source_discovery_contract(ROOT)
        source = self.registered_codex_source()

        self.assertEqual(contract["schema_version"], SCHEMA_VERSION)
        self.assertEqual(contract["task_id"], "S07-P1-T1")
        self.assertEqual(contract["source_id"], "codex")
        self.assertEqual(
            source["discovery"]["contract_ref"],
            CODEX_DISCOVERY_CONTRACT_PATH.as_posix(),
        )
        self.assertEqual(source["discovery"]["candidates"], EXPECTED_REGISTRY_CANDIDATES)
        self.assertEqual(source["raw_paths"], EXPECTED_REGISTRY_RAW_PATHS)
        self.assertIs(contract["credential_exclusions"]["allowlist_only"], True)
        self.assertIs(contract["credential_exclusions"]["source_content_read"], False)
        self.assertIs(contract["safety"]["local_absolute_path_in_output"], False)
        self.assertEqual(contract["phase_boundary"]["next_task"], "S07-P1-T2")

        mutated = copy.deepcopy(contract)
        mutated["credential_exclusions"]["blocked_path_segments"].pop()
        with self.assertRaises(CodexSourceDiscoveryError):
            validate_codex_source_discovery_contract(mutated)

    def test_contract_io_failure_uses_a_path_free_reason_code(self) -> None:
        with (
            mock.patch(
                "memory_atlas_cli.codex_source_discovery.os.read",
                side_effect=OSError("fixture read failure"),
            ),
            self.assertRaises(CodexSourceDiscoveryError) as raised,
        ):
            load_codex_source_discovery_contract(ROOT)

        self.assertEqual(raised.exception.code, "discovery_contract_unreadable")

    def test_candidate_precedence_is_operator_then_memory_env_then_codex_env_then_home(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir)
            operator = make_codex_fixture(parent, "operator")
            memory_env = make_codex_fixture(parent, "memory-env")
            codex_env = make_codex_fixture(parent, "codex-env")
            home = parent / "home"
            default = make_codex_fixture(home, ".codex")
            environment = {
                "MEMORY_ATLAS_CODEX_HOME": str(memory_env),
                "CODEX_HOME": str(codex_env),
            }

            cases = (
                (operator, environment, operator, "operator_argument", "--codex-home"),
                (None, environment, memory_env, "environment_variable", "MEMORY_ATLAS_CODEX_HOME"),
                (None, {"CODEX_HOME": str(codex_env)}, codex_env, "environment_variable", "CODEX_HOME"),
                (None, {}, default, "home_relative", ".codex"),
            )
            for explicit, env, expected, kind, name in cases:
                with self.subTest(kind=kind, name=name):
                    selected = resolve_codex_home(
                        self.registered_codex_source(),
                        operator_codex_home=explicit,
                        environ=env,
                        home=home,
                    )
                    self.assertIsNotNone(selected)
                    self.assertEqual(selected.path, expected.resolve())
                    self.assertEqual(selected.candidate_kind, kind)
                    self.assertEqual(selected.candidate_name, name)

    def test_explicit_invalid_root_fails_closed_without_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir)
            valid = make_codex_fixture(parent, "valid")
            home = parent / "home"
            make_codex_fixture(home, ".codex")
            missing = parent / "missing"
            symlink = parent / "linked"
            symlink.symlink_to(valid, target_is_directory=True)
            cases = (
                (Path("relative/codex"), {}, "codex_home_must_be_absolute"),
                (Path("/invalid\0codex"), {}, "codex_home_stat_failed"),
                (missing, {}, "configured_codex_home_missing"),
                (symlink, {}, "codex_home_symlink_rejected"),
                (None, {"MEMORY_ATLAS_CODEX_HOME": str(missing)}, "configured_codex_home_missing"),
                (None, {"CODEX_HOME": "relative/codex"}, "codex_home_must_be_absolute"),
            )
            for explicit, environment, reason in cases:
                with self.subTest(reason=reason), self.assertRaises(CodexSourceDiscoveryError) as raised:
                    resolve_codex_home(
                        self.registered_codex_source(),
                        operator_codex_home=explicit,
                        environ=environment,
                        home=home,
                    )
                self.assertEqual(raised.exception.code, reason)

    def test_missing_default_root_returns_not_found_instead_of_guessing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir) / "home"
            home.mkdir()

            selected = resolve_codex_home(
                self.registered_codex_source(),
                environ={},
                home=home,
            )

        self.assertIsNone(selected)

    def test_discovery_reads_metadata_only_and_excludes_credentials(self) -> None:
        contract = load_codex_source_discovery_contract(ROOT)
        credential_contract = load_credential_exclusion_contract(ROOT)
        with tempfile.TemporaryDirectory() as temp_dir:
            root = make_codex_fixture(Path(temp_dir))
            before = file_evidence(root)
            selection = CodexRootSelection(root, "operator_argument", "--codex-home")
            blocked_read = AssertionError("source content read")
            with (
                mock.patch("builtins.open", side_effect=blocked_read),
                mock.patch.object(Path, "read_bytes", side_effect=blocked_read),
                mock.patch.object(Path, "read_text", side_effect=blocked_read),
                mock.patch("os.open", side_effect=blocked_read),
                mock.patch("os.read", side_effect=blocked_read),
            ):
                inventory = discover_codex_sources(selection, contract, credential_contract)
            result = build_codex_source_discovery(ROOT, operator_codex_home=root, environ={})
            repeated = build_codex_source_discovery(ROOT, operator_codex_home=root, environ={})
            after = file_evidence(root)

        self.assertEqual(len(inventory.files), 10)
        self.assertEqual({item.source_kind for item in inventory.files}, {
            "session_index",
            "active_sessions",
            "archived_sessions",
            "history",
            "jsonl_logs",
            "sqlite_logs",
        })
        self.assertFalse(any("cookies" in item.relative_path for item in inventory.files))
        self.assertFalse(any("private_keys" in item.relative_path for item in inventory.files))
        self.assertEqual(result["source_root"], "[CODEX_HOME]")
        self.assertEqual(result["eligible_file_count"], 10)
        self.assertEqual(result["eligible_source_kind_count"], 6)
        self.assertGreaterEqual(result["credential_exclusions"]["existing_excluded_entry_count"], 8)
        self.assertEqual(result["source_metadata_sha256"], repeated["source_metadata_sha256"])
        self.assertEqual(before, after)
        serialized = json.dumps(result, ensure_ascii=False, sort_keys=True)
        self.assertNotIn(str(root), serialized)
        self.assertNotIn(BODY_SENTINEL, serialized)

    def test_eligible_symlink_fails_closed_without_touching_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir)
            root = make_codex_fixture(parent)
            outside = parent / "outside.jsonl"
            write_bytes(outside, f"{BODY_SENTINEL}-outside\n".encode())
            (root / "sessions/linked.jsonl").symlink_to(outside)
            before = file_evidence(parent)

            with self.assertRaises(CodexSourceDiscoveryError) as raised:
                build_codex_source_discovery(ROOT, operator_codex_home=root, environ={})
            after = file_evidence(parent)

        self.assertEqual(raised.exception.code, "eligible_source_symlink_rejected")
        self.assertEqual(before, after)

    def test_atlasctl_audit_passes_without_paths_body_or_source_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = make_codex_fixture(Path(temp_dir))
            before = file_evidence(root)
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "atlasctl.py"),
                    "audit",
                    "--check",
                    "codex-source-discovery",
                    "--database-dir",
                    str(ROOT),
                    "--codex-home",
                    str(root),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            after = file_evidence(root)

        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(payload["check"], "codex-source-discovery")
        self.assertIs(payload["safety"]["source_content_read"], False)
        self.assertIs(payload["safety"]["writes_files"], False)
        self.assertEqual(before, after)
        self.assertNotIn(temp_dir, result.stdout + result.stderr)
        self.assertNotIn(BODY_SENTINEL, result.stdout + result.stderr)

    def test_atlasctl_invalid_root_is_path_free_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            missing = Path(temp_dir) / "missing"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "atlasctl.py"),
                    "audit",
                    "--check",
                    "codex-source-discovery",
                    "--database-dir",
                    str(ROOT),
                    "--codex-home",
                    str(missing),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(payload["status"], "FAIL_CLOSED")
        self.assertEqual(payload["reason"], "configured_codex_home_missing")
        self.assertNotIn(temp_dir, result.stdout + result.stderr)
        self.assertNotIn("Traceback", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
