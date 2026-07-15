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
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from memory_atlas_cli import raw_isolation  # noqa: E402


RAW_ISOLATED_CI = os.environ.get("MEMORY_ATLAS_RAW_ISOLATED") == "1"


def canonical_contract() -> dict:
    return json.loads((ROOT / raw_isolation.CONFIG_PATH).read_text(encoding="utf-8"))


def run(command: list[str], *, cwd: Path, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
    )


class RawIsolationTests(unittest.TestCase):
    def test_canonical_isolation_audit_covers_search_routes_ci_and_frontend(self) -> None:
        result = raw_isolation.audit_raw_isolation(ROOT, ci_checkout=RAW_ISOLATED_CI)

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["task_id"], "S06-P3-T1")
        self.assertEqual(result["search"]["default_worktree_raw_path_count"], 0)
        self.assertEqual(result["search"]["default_database_raw_path_count"], 0)
        self.assertGreater(result["search"]["tracked_raw_path_count"], 0)
        if RAW_ISOLATED_CI:
            self.assertEqual(result["search"]["explicit_raw_path_count"], 0)
        else:
            self.assertEqual(
                result["search"]["explicit_raw_path_count"],
                result["search"]["tracked_raw_path_count"],
            )
        self.assertTrue(result["codex_routing"]["runtime_enforced"])
        self.assertGreater(result["codex_routing"]["route_count"], 0)
        self.assertEqual(result["frontend"]["blocked_raw_probe_count"], 2)
        self.assertEqual(result["frontend"]["safe_probe_count"], 2)
        self.assertFalse(result["raw_content_read"])
        self.assertFalse(result["raw_mutation"])
        self.assertFalse(result["remote_push"])

    def test_atlasctl_exposes_raw_isolation_audit(self) -> None:
        command = [sys.executable, "scripts/atlasctl.py", "audit", "--check", "raw-isolation"]
        if RAW_ISOLATED_CI:
            command.append("--ci-checkout")
        result = run(command, cwd=ROOT)

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(payload["check"], "raw-isolation")

    def test_contract_rejects_every_isolation_plane_drift(self) -> None:
        mutations = {
            "topology": lambda value: value["repository_topologies"].pop(),
            "raw root": lambda value: value["forbidden_raw_roots"].pop(),
            "search": lambda value: value["search"].update({"explicit_override": ["rg"]}),
            "Codex": lambda value: value["codex_routing"].update({"all_routes_default_excluded": False}),
            "CI": lambda value: value["ci"]["root_sparse_checkout_patterns"].pop(),
            "frontend": lambda value: value["frontend"].update({"server_fs_strict": False}),
            "boundary": lambda value: value["boundaries"].update({"raw_mutation": True}),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                payload = canonical_contract()
                mutate(payload)
                with self.assertRaises(raw_isolation.RawIsolationError):
                    raw_isolation.validate_raw_isolation_contract(payload)

    def test_route_config_rejects_required_and_conditional_raw_paths(self) -> None:
        route_config = json.loads(
            (ROOT / "config/context_sources/resource_routes.json").read_text(encoding="utf-8")
        )
        contract = canonical_contract()
        self.assertGreater(len(raw_isolation.validate_route_config_isolation(route_config, contract)), 0)

        mutations = {
            "required": lambda value: value["routes"][0]["read_order"].append(
                "data/public_raw/chatgpt/transcript.json"
            ),
            "conditional": lambda value: value["routes"][0].setdefault("conditional_resources", []).append(
                {"path": "data/raw_archives/chatgpt/manifest.json", "condition": "unsafe"}
            ),
            "missing contract": lambda value: value.pop("raw_isolation_contract_ref"),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                payload = copy.deepcopy(route_config)
                mutate(payload)
                with self.assertRaises(raw_isolation.RawIsolationError):
                    raw_isolation.validate_route_config_isolation(payload, contract)

    def test_project_ci_contract_remains_valid_in_a_standalone_checkout(self) -> None:
        contract = canonical_contract()
        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary) / "recovered-memory-atlas"
            checkout = Path(temporary) / "standalone-checkout"
            (database / ".github/workflows").mkdir(parents=True)
            (database / ".github/workflows/ci.yml").write_bytes(
                (ROOT / ".github/workflows/ci.yml").read_bytes()
            )
            (database / ".rgignore").write_bytes((ROOT / ".rgignore").read_bytes())
            (database / "scripts").mkdir()
            (database / "scripts/atlasctl.py").write_text("pass\n", encoding="utf-8")
            for relative in ("data/public_raw/chatgpt/message.json", "data/raw_archives/chatgpt/part.000"):
                path = database / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("raw\n", encoding="utf-8")

            topology, worktree = raw_isolation._repository_topology(database)
            result = raw_isolation._audit_ci(database, contract)
            self.assertEqual(run(["git", "init", "-q"], cwd=database).returncode, 0)
            self.assertEqual(run(["git", "config", "user.name", "Raw Isolation Test"], cwd=database).returncode, 0)
            self.assertEqual(run(["git", "config", "user.email", "raw-isolation@example.invalid"], cwd=database).returncode, 0)
            self.assertEqual(run(["git", "add", "."], cwd=database).returncode, 0)
            self.assertEqual(run(["git", "commit", "-qm", "fixture"], cwd=database).returncode, 0)
            self.assertEqual(
                run(["git", "clone", "-q", "--no-checkout", str(database), str(checkout)], cwd=Path(temporary)).returncode,
                0,
            )
            sparse = run(
                ["git", "sparse-checkout", "set", "--no-cone", "--stdin"],
                cwd=checkout,
                input_text="\n".join(contract["ci"]["project_sparse_checkout_patterns"]) + "\n",
            )
            self.assertEqual(sparse.returncode, 0, sparse.stderr)
            self.assertEqual(run(["git", "checkout", "-q"], cwd=checkout).returncode, 0)
            self.assertTrue((checkout / "scripts/atlasctl.py").is_file())
            self.assertFalse((checkout / "data/public_raw").exists())
            self.assertFalse((checkout / "data/raw_archives").exists())

        self.assertEqual(topology, "standalone_openaidatabase")
        self.assertEqual(worktree, database)
        self.assertIsNone(result["root_workflow"])
        self.assertTrue(result["project_workflow"]["runtime_audit"])

    def test_root_ci_sparse_patterns_keep_explicit_raw_search_then_remove_raw_from_checkout(self) -> None:
        patterns = canonical_contract()["ci"]["root_sparse_checkout_patterns"]
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            source = base / "source"
            checkout = base / "checkout"
            files = {
                ".rgignore": (ROOT.parent / ".rgignore").read_text(encoding="utf-8"),
                ".github/workflows/openai-database-ci.yml": "name: test\n",
                "scripts/lean_governance.py": "pass\n",
                "governance/projects.yaml": "projects: []\n",
                "OpenAIDatabase/.rgignore": (ROOT / ".rgignore").read_text(encoding="utf-8"),
                "OpenAIDatabase/scripts/atlasctl.py": "pass\n",
                "OpenAIDatabase/data/public_raw/chatgpt/message.json": "raw\n",
                "OpenAIDatabase/data/raw_archives/chatgpt/part.000": "archive\n",
            }
            for relative, content in files.items():
                path = source / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
            self.assertEqual(run(["git", "init", "-q"], cwd=source).returncode, 0)
            self.assertEqual(run(["git", "config", "user.name", "Raw Isolation Test"], cwd=source).returncode, 0)
            self.assertEqual(run(["git", "config", "user.email", "raw-isolation@example.invalid"], cwd=source).returncode, 0)
            self.assertEqual(run(["git", "add", "."], cwd=source).returncode, 0)
            self.assertEqual(run(["git", "commit", "-qm", "fixture"], cwd=source).returncode, 0)
            default_search = run(["rg", "--files", "OpenAIDatabase"], cwd=source)
            explicit_search = run(
                [
                    "rg",
                    "--no-ignore",
                    "--files",
                    "OpenAIDatabase/data/public_raw",
                    "OpenAIDatabase/data/raw_archives",
                ],
                cwd=source,
            )
            self.assertEqual(default_search.returncode, 0, default_search.stderr)
            self.assertNotIn("data/public_raw", default_search.stdout)
            self.assertNotIn("data/raw_archives", default_search.stdout)
            self.assertEqual(explicit_search.returncode, 0, explicit_search.stderr)
            self.assertEqual(len(explicit_search.stdout.splitlines()), 2)
            self.assertEqual(run(["git", "clone", "-q", "--no-checkout", str(source), str(checkout)], cwd=base).returncode, 0)
            sparse = run(
                ["git", "sparse-checkout", "set", "--no-cone", "--stdin"],
                cwd=checkout,
                input_text="\n".join(patterns) + "\n",
            )
            self.assertEqual(sparse.returncode, 0, sparse.stderr)
            checked_out = run(["git", "checkout", "-q"], cwd=checkout)
            self.assertEqual(checked_out.returncode, 0, checked_out.stderr)
            self.assertTrue((checkout / "OpenAIDatabase/scripts/atlasctl.py").is_file())
            self.assertTrue((checkout / "scripts/lean_governance.py").is_file())
            self.assertTrue((checkout / "governance/projects.yaml").is_file())
            self.assertFalse((checkout / "OpenAIDatabase/data/public_raw").exists())
            self.assertFalse((checkout / "OpenAIDatabase/data/raw_archives").exists())

    def test_dist_audit_rejects_raw_path_components_and_byte_identical_raw_files(self) -> None:
        contract = canonical_contract()
        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary) / "OpenAIDatabase"
            dist = database / "apps/memory-atlas/dist"
            dist.mkdir(parents=True)
            raw_bytes = b"fixture raw body\n"
            ledger = database / "control/raw_hash_ledger.jsonl"
            ledger.parent.mkdir(parents=True)
            ledger.write_text(
                json.dumps({"sha256": hashlib.sha256(raw_bytes).hexdigest()}) + "\n",
                encoding="utf-8",
            )
            ledger_config = database / "config/data_sources/raw_ledger.json"
            ledger_config.parent.mkdir(parents=True)
            ledger_config.write_text(
                json.dumps({"ledger": {"path": "control/raw_hash_ledger.jsonl"}}),
                encoding="utf-8",
            )
            asset = dist / "assets/index.js"
            asset.parent.mkdir(parents=True)
            asset.write_bytes(b"export {};\n")
            result = raw_isolation._audit_dist(database, contract, dist)
            self.assertEqual(result["raw_hash_collision_count"], 0)

            leaked = dist / "public_raw/leak.json"
            leaked.parent.mkdir()
            leaked.write_bytes(b"{}\n")
            with self.assertRaisesRegex(raw_isolation.RawIsolationError, "raw path component"):
                raw_isolation._audit_dist(database, contract, dist)

            leaked.unlink()
            leaked.parent.rmdir()
            asset.write_bytes(raw_bytes)
            with self.assertRaisesRegex(raw_isolation.RawIsolationError, "byte-identical public raw"):
                raw_isolation._audit_dist(database, contract, dist)

    def test_ci_checkout_mode_fails_when_raw_roots_are_materialized(self) -> None:
        if RAW_ISOLATED_CI:
            self.skipTest("the real CI checkout correctly omits raw roots")
        contract = canonical_contract()
        with patch.dict(os.environ, {"MEMORY_ATLAS_RAW_ISOLATED": "1"}):
            with self.assertRaisesRegex(raw_isolation.RawIsolationError, "materialized raw roots"):
                raw_isolation._audit_search(ROOT, contract, ci_checkout=True)


if __name__ == "__main__":
    unittest.main()
