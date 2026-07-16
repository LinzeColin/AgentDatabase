from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
ATLASCTL = SCRIPTS / "atlasctl.py"
PACKAGE = SCRIPTS / "memory_atlas_cli"
VALIDATORS = ROOT / "apps/memory-atlas/scripts"

EXPECTED_MODULES = {
    "constants.py",
    "parser.py",
    "sync.py",
    "analyze.py",
    "build.py",
    "validate.py",
    "push.py",
    "apply.py",
    "dispatch.py",
    "runtime.py",
    "chatgpt_export_request.py",
    "chatgpt_export_state.py",
}

EXPECTED_EXPORTS = {
    "parse_args",
    "owner_daily_profile_contract",
    "run_profile",
    "chatgpt_contract",
    "codex_contract",
    "future_agent_contract",
    "run_sync",
    "run_build_atlas",
    "run_analyze",
    "final_audit_gate_plan",
    "compact_tail",
    "run_audit",
    "run_push",
    "run_generate_personalization_prompt",
    "run_chatgpt_deep_explore",
    "run_proposals",
    "run_apply",
    "run_chatgpt_export_request",
    "run_chatgpt_export_state",
    "run_stateful_chatgpt_export_request",
    "load_runtime_config",
    "execute_with_runtime",
    "main",
}

EXPECTED_DOMAIN_IMPORTS = {
    "OWNER_DAILY_STEP_IDS",
    "OwnerDailyContext",
    "OwnerDailyRunner",
    "build_owner_daily_profile_contract",
    "FOUR_LINE_GATES",
    "REQUIRED_R8_GATE_IDS",
    "AcceptanceHistoryError",
    "build_acceptance_summary",
}

STABLE_DRY_RUNS = {
    ("sync", "--source", "chatgpt", "--dry-run"):
        "d7f49a68e87dd7a9cb592c50db68e1b82a3662f2f09932e28209d5851ed8b3db",
    ("sync", "--source", "codex", "--dry-run"):
        "99d2ada2aba2d6c79b6de4096eba5d7132d95a5c94f3c2edffd7a68f3e15230b",
    ("sync", "--source", "future-agent", "--dry-run"):
        "9e6f64a060139420c38c9611048efa9848860135ca2fa514329f167de6118c75",
    ("build-atlas", "--dry-run"):
        "ec6fa449014356a6c810e08c45b197881c2e3f0a98d9ffe3e31d43fa3ed5660b",
    ("generate-personalization-prompt", "--dry-run"):
        "bd213ada43eb9aa8cf018a479a3bb56cf8bd3996abe98ce3c952967c34e8d9dc",
    ("chatgpt-deep-explore", "--dry-run"):
        "f1f02ce41232029e1711fdd787af4166cbf6bb036bedc75cb022d865dfd00f1a",
}


def load_atlasctl():
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location("atlasctl_modular_test", ATLASCTL)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class AtlasctlModularCliTests(unittest.TestCase):
    def test_required_responsibility_modules_exist(self) -> None:
        self.assertTrue(PACKAGE.is_dir(), "memory_atlas_cli package is missing")
        self.assertTrue((PACKAGE / "__init__.py").is_file())
        present = {path.name for path in PACKAGE.glob("*.py")}
        self.assertTrue(EXPECTED_MODULES.issubset(present), EXPECTED_MODULES - present)

    def test_atlasctl_is_a_thin_compatible_facade(self) -> None:
        source = ATLASCTL.read_text(encoding="utf-8")
        tree = ast.parse(source)
        local_functions = [node.name for node in tree.body if isinstance(node, ast.FunctionDef)]

        self.assertEqual(local_functions, ["main"])
        self.assertLessEqual(len(source.splitlines()), 100)
        self.assertNotIn("subprocess.run(", source)
        self.assertNotIn("add_subparsers(", source)

        module = load_atlasctl()
        self.assertTrue(EXPECTED_EXPORTS.issubset(set(module.__all__)))
        self.assertTrue(EXPECTED_DOMAIN_IMPORTS.issubset(set(module.__all__)))
        for name in EXPECTED_EXPORTS:
            self.assertTrue(callable(getattr(module, name)), name)
        for name in EXPECTED_DOMAIN_IMPORTS:
            self.assertTrue(hasattr(module, name), name)

    def test_parser_preserves_historical_command_surface(self) -> None:
        module = load_atlasctl()
        samples = {
            "run": ["run", "--profile", "owner-daily", "--dry-run"],
            "sync": ["sync", "--source", "chatgpt", "--dry-run"],
            "request-chatgpt-export": [
                "request-chatgpt-export",
                "--dry-run",
                "--cdp-endpoint",
                "http://127.0.0.1:9222",
            ],
            "chatgpt-export-state": ["chatgpt-export-state", "--inspect"],
            "build-atlas": ["build-atlas", "--dry-run"],
            "analyze": ["analyze", "--stage", "facets", "--dry-run"],
            "audit": ["audit", "--dry-run"],
            "push": ["push", "--dry-run"],
            "generate-personalization-prompt": ["generate-personalization-prompt", "--dry-run"],
            "chatgpt-deep-explore": ["chatgpt-deep-explore", "--dry-run"],
            "deep-explore": ["deep-explore", "--dry-run"],
            "proposals": ["proposals", "--dry-run"],
            "apply": ["apply", "--proposal", "proposal-fixture", "--dry-run"],
        }
        for command, argv in samples.items():
            with self.subTest(command=command):
                self.assertEqual(module.parse_args(argv).command, command)

    def test_moved_constants_still_resolve_from_the_database_root(self) -> None:
        module = load_atlasctl()
        self.assertEqual(module.ROOT, ROOT)
        executable_paths = {
            name: value
            for name, value in vars(module).items()
            if name.isupper() and isinstance(value, Path) and name != "ROOT"
        }
        self.assertGreaterEqual(len(executable_paths), 20)
        for name, path in executable_paths.items():
            with self.subTest(name=name):
                self.assertTrue(path.is_file(), f"{name} does not resolve to a file: {path}")

    def test_deterministic_dry_run_stdout_is_byte_compatible(self) -> None:
        for argv, expected_hash in STABLE_DRY_RUNS.items():
            with self.subTest(argv=argv):
                result = subprocess.run(
                    [sys.executable, str(ATLASCTL), *argv],
                    cwd=ROOT,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", errors="replace"))
                self.assertEqual(hashlib.sha256(result.stdout).hexdigest(), expected_hash)
                events = [json.loads(line) for line in result.stderr.splitlines()]
                self.assertEqual(len(events), 2)
                self.assertEqual([event["event"] for event in events], ["run_started", "run_finished"])
                self.assertEqual(events[-1]["status"], "SUCCEEDED")
                self.assertEqual(events[-1]["error_code"], "MA_OK")
                self.assertNotIn(result.stdout.strip(), result.stderr)

    def test_source_sensitive_validators_read_the_aggregate_runtime(self) -> None:
        stale_pattern = re.compile(
            r"const atlasctl(?:Source)?\s*=\s*readRepoFile\("
            r"(?:atlasctl(?:Script|Path)|[\"']scripts/atlasctl\.py[\"'])\);"
        )
        stale = []
        for path in sorted(VALIDATORS.glob("validate_memory_atlas_v1_2_*.cjs")):
            source = path.read_text(encoding="utf-8")
            if stale_pattern.search(source):
                stale.append(path.name)
        self.assertEqual(stale, [], f"single-file atlasctl source reads remain: {stale}")

    def test_aggregate_runtime_contains_facade_and_every_current_module(self) -> None:
        helper = VALIDATORS / "atlasctl_runtime_source.cjs"
        node_script = (
            f"const {{ readAtlasctlRuntimeSource }} = require({json.dumps(str(helper))});"
            f"process.stdout.write(readAtlasctlRuntimeSource({json.dumps(str(ROOT))}));"
        )
        aggregate = subprocess.run(
            ["node", "-e", node_script],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        ).stdout
        runtime_paths = [ATLASCTL, *sorted(PACKAGE.glob("*.py"))]
        expected = "\n".join(path.read_text(encoding="utf-8") for path in runtime_paths)

        self.assertEqual(aggregate, expected)
        for module_name in EXPECTED_MODULES:
            self.assertIn((PACKAGE / module_name).read_text(encoding="utf-8"), aggregate)


if __name__ == "__main__":
    unittest.main()
