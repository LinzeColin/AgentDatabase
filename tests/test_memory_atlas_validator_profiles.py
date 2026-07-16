from __future__ import annotations

import importlib.util
import io
import json
import re
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
WORKTREE_ROOT = ROOT.parent
APP = ROOT / "apps/memory-atlas"
PACKAGE = APP / "package.json"
CONFIG = ROOT / "config/memory_atlas_validator_profiles.json"
RUNNER = ROOT / "scripts/memory_atlas_validator_profiles.py"
LEGACY_LOOKUP = ROOT / "scripts/memory_atlas_legacy_commands.py"
DELIVERY_TASKS = ROOT / "docs/governance/delivery_tasks.yaml"
PUBLIC_PROFILES = ("fast", "sync", "ui", "release")
PUBLIC_SCRIPT_NAMES = {f"validate:{profile}" for profile in PUBLIC_PROFILES}
EXPECTED_SCRIPT_COMMANDS = {
    f"validate:{profile}": f"python3 ../../scripts/memory_atlas_validator_profiles.py --profile {profile}"
    for profile in PUBLIC_PROFILES
}


def load_runner_module():
    if not RUNNER.is_file():
        raise AssertionError(f"validator profile runner is missing: {RUNNER}")
    spec = importlib.util.spec_from_file_location("memory_atlas_validator_profiles_test", RUNNER)
    if spec is None or spec.loader is None:
        raise AssertionError("validator profile runner cannot be imported")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def fixture_payload(*, fast_steps: list[dict[str, object]] | None = None, max_output_chars: int = 64):
    passing = {
        "id": "pass",
        "command": ["@python", "-c", "print('ok')"],
        "cwd": "database",
        "timeout_seconds": 5,
        "critical": True,
    }
    profiles = {}
    for profile in PUBLIC_PROFILES:
        steps = fast_steps if profile == "fast" and fast_steps is not None else [passing | {"id": f"{profile}_pass"}]
        profiles[profile] = {
            "description_zh": f"{profile} fixture",
            "steps": steps,
        }
    return {
        "schema_version": "memory_atlas.validator_profiles.v1_2_1_s04_p3_t1",
        "result_schema_version": "memory_atlas.validator_profile_result.v1_2_1_s04_p3_t1",
        "public_profiles": list(PUBLIC_PROFILES),
        "max_output_chars_per_stream": max_output_chars,
        "profiles": profiles,
    }


class PublicProfileContractTests(unittest.TestCase):
    def test_package_exposes_exactly_four_validation_profiles(self) -> None:
        package = json.loads(PACKAGE.read_text(encoding="utf-8"))
        validate_scripts = {
            name: command
            for name, command in package["scripts"].items()
            if name.startswith("validate:")
        }

        self.assertEqual(set(validate_scripts), PUBLIC_SCRIPT_NAMES)
        self.assertEqual(validate_scripts, EXPECTED_SCRIPT_COMMANDS)
        self.assertEqual(len(package["scripts"]), 8)

    def test_canonical_config_maps_all_profiles_to_real_critical_steps(self) -> None:
        self.assertTrue(CONFIG.is_file(), f"validator profile config is missing: {CONFIG}")
        payload = json.loads(CONFIG.read_text(encoding="utf-8"))

        self.assertEqual(payload["public_profiles"], list(PUBLIC_PROFILES))
        self.assertEqual(list(payload["profiles"]), list(PUBLIC_PROFILES))
        self.assertEqual(payload["schema_version"], "memory_atlas.validator_profiles.v1_2_1_s04_p3_t1")
        self.assertGreaterEqual(payload["max_output_chars_per_stream"], 1_000)
        for profile, contract in payload["profiles"].items():
            with self.subTest(profile=profile):
                self.assertTrue(contract["description_zh"])
                self.assertTrue(contract["steps"])
                step_ids = [step["id"] for step in contract["steps"]]
                self.assertEqual(len(step_ids), len(set(step_ids)))
                for step in contract["steps"]:
                    self.assertIs(type(step["timeout_seconds"]), int)
                    self.assertGreater(step["timeout_seconds"], 0)
                    self.assertIs(step["critical"], True)
                    self.assertIn(step["cwd"], {"worktree", "database", "app"})
                    self.assertIsInstance(step["command"], list)
                    self.assertTrue(step["command"])
                    self.assertTrue(all(isinstance(value, str) and value for value in step["command"]))

        self.assertEqual(
            {step["id"] for step in payload["profiles"]["ui"]["steps"]},
            {
                "frontend_build",
                "public_raw_build_isolation",
                "semantic_readability",
                "home_multiviewport",
                "visual_models",
                "visual_workflows",
                "command_workflows",
                "proposal_e2e",
                "owner_daily_e2e",
                "canvas_visual",
                "canvas_performance",
                "privacy_accessibility",
                "obsidian_graph",
                "visual_semantics",
            },
        )
        fast_step_ids = {step["id"] for step in payload["profiles"]["fast"]["steps"]}
        self.assertIn("raw_isolation", fast_step_ids)
        self.assertIn("push_size_guard", fast_step_ids)
        push_size_step = next(
            step for step in payload["profiles"]["fast"]["steps"] if step["id"] == "push_size_guard"
        )
        self.assertEqual(
            push_size_step["command"],
            ["@python", "scripts/atlasctl.py", "audit", "--check", "push-size", "--push-scope", "staged"],
        )
        sync_unit_tests = next(
            step for step in payload["profiles"]["sync"]["steps"] if step["id"] == "sync_unit_tests"
        )
        self.assertIn(
            "tests.test_memory_atlas_raw_contract_fixtures",
            sync_unit_tests["command"],
        )
        self.assertIn(
            "tests.test_memory_atlas_codex_source_discovery",
            sync_unit_tests["command"],
        )
        self.assertIn(
            "tests.test_memory_atlas_codex_scheduler",
            sync_unit_tests["command"],
        )
        self.assertIn(
            "tests.test_memory_atlas_codex_restore_proof",
            sync_unit_tests["command"],
        )
        self.assertIn(
            "tests.test_memory_atlas_chatgpt_export_request",
            sync_unit_tests["command"],
        )
        self.assertIn(
            "tests.test_memory_atlas_chatgpt_export_state",
            sync_unit_tests["command"],
        )
        ui_isolation = next(
            step for step in payload["profiles"]["ui"]["steps"] if step["id"] == "public_raw_build_isolation"
        )
        self.assertEqual(
            ui_isolation["command"],
            ["@python", "scripts/atlasctl.py", "audit", "--check", "raw-isolation", "--require-built-dist"],
        )
        self.assertEqual(
            [step["id"] for step in payload["profiles"]["release"]["steps"]],
            ["final_audit"],
        )

    def test_canonical_config_passes_strict_loader(self) -> None:
        module = load_runner_module()

        config = module.load_validator_profile_config(ROOT)

        self.assertEqual(tuple(config.public_profiles), PUBLIC_PROFILES)
        self.assertEqual(tuple(config.profiles), PUBLIC_PROFILES)
        self.assertIs(config.commands_audited, True)

    def test_stage9_validators_register_through_ui_profile_not_legacy_aliases(self) -> None:
        validators = {
            "validate_stage9_obsidian_iteration.cjs": (
                "obsidian_graph",
                "validate:stage9-obsidian",
                ["src/features/assets/ObsidianGraph.tsx"],
            ),
            "validate_stage9_visual_semantics.cjs": (
                "visual_semantics",
                "validate:stage9-visual-semantics",
                [
                    "src/features/overview/HomeOverviewView.tsx",
                    "src/features/assets/TimelineView.tsx",
                    "src/shared/atlas/previewWeatherModels.ts",
                    "src/shared/atlas/memoryRiverModels.ts",
                ],
            ),
        }
        for filename, (step_id, legacy_alias, runtime_paths) in validators.items():
            with self.subTest(validator=filename):
                source = (APP / "scripts" / filename).read_text(encoding="utf-8")
                self.assertIn("memory_atlas_validator_profiles.json", source)
                self.assertIn(step_id, source)
                self.assertNotIn(f'packageSource.includes(\'"{legacy_alias}"', source)
                for runtime_path in runtime_paths:
                    self.assertIn(runtime_path, source)
                if filename == "validate_stage9_obsidian_iteration.cjs":
                    self.assertGreaterEqual(source.count('page.locator(\'[data-nav-view="obsidian"]\')'), 2)
                    self.assertIn('page.locator(\'[data-nav-view="galaxy"]\')', source)
                    self.assertIn("__memoryAtlasGalaxyDebugTargets", source)
                    self.assertNotIn("canvasBox.width / 2", source)
                    self.assertNotIn('name: /Obsidian 图谱/', source)
                if filename == "validate_stage9_visual_semantics.cjs":
                    self.assertIn('page.locator(\'[data-nav-view="galaxy"]\')', source)
                    self.assertNotIn('name: /银河星云/', source)

    def test_current_execution_surfaces_only_call_public_profile_aliases(self) -> None:
        sources = {
            str(DELIVERY_TASKS.relative_to(ROOT)): DELIVERY_TASKS.read_text(encoding="utf-8"),
            str((ROOT / "config/atlasctl_script_migrations.json").relative_to(ROOT)): (
                ROOT / "config/atlasctl_script_migrations.json"
            ).read_text(encoding="utf-8"),
        }
        sources.update(
            {
                str(path.relative_to(ROOT)): path.read_text(encoding="utf-8")
                for path in sorted((ROOT / "scripts").glob("*.py"))
                if path != LEGACY_LOOKUP
            }
        )
        alias_pattern = re.compile(
            r"\b(?:npm|pnpm)\b[^\r\n]*?\brun\s+(validate:[A-Za-z0-9._:-]+)"
        )

        invalid_aliases = {
            source_name: sorted(
                {
                    match.group(1)
                    for match in alias_pattern.finditer(source)
                    if match.group(1) not in PUBLIC_SCRIPT_NAMES
                }
                | (
                    {
                        alias
                        for alias in re.findall(r"validate:[A-Za-z0-9._:-]+", source)
                        if alias not in PUBLIC_SCRIPT_NAMES
                    }
                    if source_name.startswith("scripts/")
                    else set()
                )
            )
            for source_name, source in sources.items()
        }
        invalid_aliases = {
            source_name: aliases
            for source_name, aliases in invalid_aliases.items()
            if aliases
        }

        self.assertEqual(invalid_aliases, {})
        legacy_lookup_source = LEGACY_LOOKUP.read_text(encoding="utf-8")
        self.assertNotIn("subprocess", legacy_lookup_source)
        self.assertNotIn("os.system", legacy_lookup_source)
        self.assertIn('"execution_supported": False', legacy_lookup_source)
        self.assertIn("REQUIRED_MIGRATED_CALLERS", legacy_lookup_source)
        self.assertIn(
            "node OpenAIDatabase/apps/memory-atlas/scripts/validate_stage7_privacy_accessibility.cjs",
            sources[str(DELIVERY_TASKS.relative_to(ROOT))],
        )


class ValidatorProfileRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = load_runner_module()

    def config_from(self, payload: dict[str, object]):
        return self.module.ValidatorProfileConfig.from_mapping(payload, Path("fixture.json"))

    def test_success_runs_every_step_and_returns_machine_summary(self) -> None:
        config = self.config_from(
            fixture_payload(
                fast_steps=[
                    {
                        "id": "first",
                        "command": ["@python", "-c", "print('first')"],
                        "cwd": "database",
                        "timeout_seconds": 5,
                        "critical": True,
                    },
                    {
                        "id": "second",
                        "command": ["@python", "-c", "print('second')"],
                        "cwd": "app",
                        "timeout_seconds": 5,
                        "critical": True,
                    },
                ]
            )
        )

        result = self.module.run_validator_profile(config, "fast", ROOT)

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["profile"], "fast")
        self.assertEqual(result["step_count"], 2)
        self.assertEqual(result["completed_count"], 2)
        self.assertEqual(result["failed_count"], 0)
        self.assertEqual(result["skipped_critical_count"], 0)
        self.assertEqual([step["status"] for step in result["steps"]], ["PASS", "PASS"])
        self.assertEqual(
            result["safety"],
            {
                "shell": False,
                "commands_audited": False,
                "remote_push": None,
                "raw_mutation": None,
            },
        )

    def test_canonical_loader_rejects_commands_outside_audited_policy(self) -> None:
        unsafe_commands = (
            ["git", "push", "origin", "main"],
            ["@python", "scripts/atlasctl.py", "apply", "--proposal", "x"],
            ["npx", "wrangler", "deploy"],
            ["@python", "scripts/atlasctl.py", "sync", "--source", "chatgpt"],
        )
        canonical = json.loads(CONFIG.read_text(encoding="utf-8"))

        for command in unsafe_commands:
            with self.subTest(command=command), tempfile.TemporaryDirectory() as temporary:
                payload = json.loads(json.dumps(canonical))
                payload["profiles"]["fast"]["steps"][0]["command"] = command
                path = Path(temporary) / "profiles.json"
                path.write_text(json.dumps(payload), encoding="utf-8")

                with self.assertRaisesRegex(
                    self.module.ValidatorProfileConfigError,
                    "audited safety policy",
                ):
                    self.module.load_validator_profile_config(ROOT, path)

    def test_bounded_tail_never_retains_full_child_output(self) -> None:
        tail = self.module._BoundedByteTail(max_chars=64)

        tail.append(b"x" * 2_000_000)

        self.assertLessEqual(tail.buffered_bytes, 256)
        self.assertEqual(tail.text(), "x" * 64)

    def test_large_stdout_and_stderr_are_drained_without_unbounded_result(self) -> None:
        config = self.config_from(
            fixture_payload(
                max_output_chars=64,
                fast_steps=[
                    {
                        "id": "large_failure",
                        "command": [
                            "@python",
                            "-c",
                            (
                                "import sys; "
                                "sys.stdout.write('a' * 2_000_000); "
                                "sys.stderr.write('b' * 2_000_000); "
                                "raise SystemExit(9)"
                            ),
                        ],
                        "cwd": "database",
                        "timeout_seconds": 10,
                        "critical": True,
                    }
                ],
            )
        )

        result = self.module.run_validator_profile(config, "fast", ROOT)

        self.assertEqual(result["steps"][0]["status"], "FAIL")
        self.assertEqual(result["steps"][0]["stdout_tail"], "a" * 64)
        self.assertEqual(result["steps"][0]["stderr_tail"], "b" * 64)

    def test_critical_failure_stops_later_steps_and_bounds_diagnostics(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            marker = Path(temporary) / "must-not-run"
            config = self.config_from(
                fixture_payload(
                    max_output_chars=64,
                    fast_steps=[
                        {
                            "id": "failure",
                            "command": [
                                "@python",
                                "-c",
                                "import sys; print('x' * 200, file=sys.stderr); raise SystemExit(7)",
                            ],
                            "cwd": "database",
                            "timeout_seconds": 5,
                            "critical": True,
                        },
                        {
                            "id": "forbidden_later_step",
                            "command": [
                                "@python",
                                "-c",
                                f"from pathlib import Path; Path({str(marker)!r}).write_text('ran')",
                            ],
                            "cwd": "database",
                            "timeout_seconds": 5,
                            "critical": True,
                        },
                    ],
                )
            )

            result = self.module.run_validator_profile(config, "fast", ROOT)

            self.assertEqual(result["status"], "FAIL")
            self.assertEqual(result["completed_count"], 0)
            self.assertEqual(result["failed_count"], 1)
            self.assertEqual(result["skipped_critical_count"], 1)
            self.assertEqual(result["steps"][0]["exit_code"], 7)
            self.assertLessEqual(len(result["steps"][0]["stderr_tail"]), 64)
            self.assertFalse(marker.exists())

    def test_timeout_fails_closed(self) -> None:
        config = self.config_from(
            fixture_payload(
                fast_steps=[
                    {
                        "id": "timeout",
                        "command": ["@python", "-c", "import time; time.sleep(2)"],
                        "cwd": "database",
                        "timeout_seconds": 1,
                        "critical": True,
                    }
                ]
            )
        )

        result = self.module.run_validator_profile(config, "fast", ROOT)

        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["steps"][0]["status"], "TIMEOUT")
        self.assertIsNone(result["steps"][0]["exit_code"])

    @unittest.skipUnless(sys.platform != "win32", "POSIX process-group regression")
    def test_timeout_terminates_descendant_processes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            marker = Path(temporary) / "descendant-must-not-survive"
            descendant = (
                "import time; from pathlib import Path; "
                f"time.sleep(1.5); Path({str(marker)!r}).write_text('survived')"
            )
            parent = (
                "import subprocess, sys, time; "
                f"subprocess.Popen([sys.executable, '-c', {descendant!r}]); "
                "time.sleep(10)"
            )
            config = self.config_from(
                fixture_payload(
                    fast_steps=[
                        {
                            "id": "timeout_tree",
                            "command": ["@python", "-c", parent],
                            "cwd": "database",
                            "timeout_seconds": 1,
                            "critical": True,
                        }
                    ]
                )
            )

            result = self.module.run_validator_profile(config, "fast", ROOT)
            time.sleep(2)

            self.assertEqual(result["steps"][0]["status"], "TIMEOUT")
            self.assertFalse(marker.exists())

    @unittest.skipUnless(sys.platform != "win32", "POSIX process-group regression")
    def test_timeout_cleanup_permission_error_still_returns_one_machine_json(self) -> None:
        config = self.config_from(
            fixture_payload(
                fast_steps=[
                    {
                        "id": "timeout_permission_error",
                        "command": ["@python", "-c", "import time; time.sleep(3)"],
                        "cwd": "database",
                        "timeout_seconds": 1,
                        "critical": True,
                    }
                ]
            )
        )
        stdout = io.StringIO()
        stderr = io.StringIO()

        with mock.patch.object(self.module, "load_validator_profile_config", return_value=config):
            with mock.patch.object(
                self.module.os,
                "killpg",
                side_effect=PermissionError(1, "operation not permitted"),
            ):
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    returncode = self.module.main(["--profile", "fast"])

        payload = json.loads(stdout.getvalue())
        self.assertEqual(returncode, 1)
        self.assertEqual(payload["status"], "FAIL")
        self.assertEqual(payload["steps"][0]["status"], "TIMEOUT")
        self.assertIn("process cleanup warning", payload["steps"][0]["stderr_tail"])
        self.assertNotIn("Traceback", stdout.getvalue() + stderr.getvalue())

    def test_launch_error_returns_one_machine_json_result(self) -> None:
        config = self.config_from(
            fixture_payload(
                fast_steps=[
                    {
                        "id": "missing_binary",
                        "command": ["definitely_missing_memory_atlas_binary_123"],
                        "cwd": "database",
                        "timeout_seconds": 5,
                        "critical": True,
                    }
                ]
            )
        )
        stdout = io.StringIO()
        stderr = io.StringIO()

        with mock.patch.object(self.module, "load_validator_profile_config", return_value=config):
            with redirect_stdout(stdout), redirect_stderr(stderr):
                returncode = self.module.main(["--profile", "fast"])

        payload = json.loads(stdout.getvalue())
        self.assertEqual(returncode, 1)
        self.assertEqual(payload["status"], "FAIL")
        self.assertEqual(payload["steps"][0]["status"], "LAUNCH_ERROR")
        self.assertIsNone(payload["steps"][0]["exit_code"])
        self.assertNotIn("Traceback", stdout.getvalue() + stderr.getvalue())

    def test_plan_mode_never_executes_children(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            marker = Path(temporary) / "plan-must-not-write"
            config = self.config_from(
                fixture_payload(
                    fast_steps=[
                        {
                            "id": "planned",
                            "command": [
                                "@python",
                                "-c",
                                f"from pathlib import Path; Path({str(marker)!r}).write_text('ran')",
                            ],
                            "cwd": "database",
                            "timeout_seconds": 5,
                            "critical": True,
                        }
                    ]
                )
            )

            result = self.module.run_validator_profile(config, "fast", ROOT, plan_only=True)

            self.assertEqual(result["status"], "PLAN")
            self.assertEqual(result["planned_count"], 1)
            self.assertEqual(result["steps"][0]["status"], "PLANNED")
            self.assertFalse(marker.exists())

    def test_invalid_contracts_and_unknown_profile_fail_closed(self) -> None:
        payload = fixture_payload()
        payload["unexpected"] = True
        with self.assertRaisesRegex(self.module.ValidatorProfileConfigError, "keys"):
            self.config_from(payload)

        payload = fixture_payload()
        payload["profiles"]["fast"]["steps"][0]["command"] = "python -c pass"
        with self.assertRaisesRegex(self.module.ValidatorProfileConfigError, "command"):
            self.config_from(payload)

        config = self.config_from(fixture_payload())
        with self.assertRaisesRegex(self.module.ValidatorProfileConfigError, "unknown profile"):
            self.module.build_profile_plan(config, "legacy-stage", ROOT)

    def test_symlink_config_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            target = directory / "config.json"
            target.write_text(json.dumps(fixture_payload()), encoding="utf-8")
            symlink = directory / "symlink.json"
            symlink.symlink_to(target)

            with self.assertRaisesRegex(self.module.ValidatorProfileConfigError, "symlink"):
                self.module.load_validator_profile_config(ROOT, symlink)

    def test_cli_unknown_profile_returns_two_and_json(self) -> None:
        result = subprocess.run(
            [sys.executable, str(RUNNER), "--profile", "legacy-stage"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 2)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "REJECTED")
        self.assertEqual(payload["error_code"], "VALIDATOR_PROFILE_INVALID")
        self.assertNotIn(str(ROOT), result.stdout)


if __name__ == "__main__":
    unittest.main()
