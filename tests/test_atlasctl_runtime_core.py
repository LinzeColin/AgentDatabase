from __future__ import annotations

import hashlib
import importlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from argparse import Namespace
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
ATLASCTL = SCRIPTS / "atlasctl.py"
DEFAULT_CONFIG = ROOT / "config/atlasctl_runtime.json"
CHATGPT_DRY_RUN_SHA256 = "4feb8ebf94a708cba956ac55fe5bed08397dc7d33225b92be63032560a096bf8"


def load_runtime():
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    return importlib.import_module("memory_atlas_cli.runtime")


def valid_config(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": "memory_atlas_cli_runtime_config.v1_2_1_s04_p2_t2",
        "machine_log_destination": "stderr",
        "emit_started_event": True,
        "exception_detail": "type_only",
    }
    payload.update(overrides)
    return payload


def write_config(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def json_events(raw: str) -> list[dict[str, object]]:
    return [json.loads(line) for line in raw.splitlines() if line.startswith("{")]


def load_atlasctl():
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location("atlasctl_runtime_test", ATLASCTL)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class RuntimeCoreUnitTests(unittest.TestCase):
    def test_default_config_loads_strict_runtime_contract(self) -> None:
        runtime = load_runtime()
        config = runtime.load_runtime_config()

        self.assertEqual(config.source_path, DEFAULT_CONFIG)
        self.assertEqual(config.machine_log_destination, "stderr")
        self.assertTrue(config.emit_started_event)
        self.assertEqual(config.exception_detail, "type_only")

    def test_config_loader_rejects_untrusted_shapes(self) -> None:
        runtime = load_runtime()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            cases: list[tuple[str, object]] = [
                ("unknown.json", valid_config(extra=True)),
                ("missing.json", {"schema_version": valid_config()["schema_version"]}),
                ("wrong-type.json", valid_config(emit_started_event=1)),
                ("wrong-schema.json", valid_config(schema_version="unsupported")),
                ("wrong-destination.json", valid_config(machine_log_destination="file")),
                ("wrong-detail.json", valid_config(exception_detail="message")),
                ("array.json", []),
            ]
            for name, payload in cases:
                with self.subTest(name=name):
                    path = base / name
                    write_config(path, payload)
                    with self.assertRaises(runtime.RuntimeConfigError):
                        runtime.load_runtime_config(path)

            oversized = base / "oversized.json"
            oversized.write_bytes(b"x" * (runtime.MAX_RUNTIME_CONFIG_BYTES + 1))
            with self.assertRaises(runtime.RuntimeConfigError):
                runtime.load_runtime_config(oversized)

            target = base / "target.json"
            write_config(target, valid_config())
            symlink = base / "linked.json"
            symlink.symlink_to(target)
            with self.assertRaises(runtime.RuntimeConfigError):
                runtime.load_runtime_config(symlink)

            malformed = base / "malformed.json"
            malformed.write_bytes(b"{")
            with self.assertRaises(runtime.RuntimeConfigError):
                runtime.load_runtime_config(malformed)

            non_utf8 = base / "non-utf8.json"
            non_utf8.write_bytes(b"\xff")
            with self.assertRaises(runtime.RuntimeConfigError):
                runtime.load_runtime_config(non_utf8)

            with self.assertRaises(runtime.RuntimeConfigError):
                runtime.load_runtime_config(base / "absent.json")
            with self.assertRaises(runtime.RuntimeConfigError):
                runtime.load_runtime_config(base)

    def test_runtime_session_separates_business_stdout_from_machine_jsonl(self) -> None:
        runtime = load_runtime()
        machine = io.StringIO()
        human = io.StringIO()
        args = Namespace(command="sync", dry_run=True)

        def runner(_args: Namespace) -> int:
            print('{"status":"PASS"}')
            return 0

        with redirect_stdout(human):
            result = runtime.execute_with_runtime(
                args,
                runner,
                config=runtime.RuntimeConfig.from_mapping(valid_config(), DEFAULT_CONFIG),
                machine_stream=machine,
                clock=lambda: datetime(2026, 7, 13, tzinfo=timezone.utc),
                run_id_factory=lambda: "run-fixed",
            )

        self.assertEqual(result, 0)
        self.assertEqual(human.getvalue(), '{"status":"PASS"}\n')

        events = json_events(machine.getvalue())
        self.assertEqual([event["event"] for event in events], ["run_started", "run_finished"])
        self.assertEqual([event["status"] for event in events], ["RUNNING", "SUCCEEDED"])
        self.assertEqual(events[-1]["error_code"], "MA_OK")
        self.assertEqual(events[-1]["exit_code"], 0)
        self.assertEqual({event["run_id"] for event in events}, {"run-fixed"})
        self.assertNotIn("status\":\"PASS", machine.getvalue())

    def test_runtime_state_rejects_illegal_transitions(self) -> None:
        runtime = load_runtime()
        state = runtime.RuntimeState(run_id="run-state", command="sync", dry_run=True)

        with self.assertRaises(runtime.RuntimeStateError):
            state.transition(runtime.RunStatus.SUCCEEDED)
        state.transition(runtime.RunStatus.RUNNING)
        state.transition(runtime.RunStatus.SUCCEEDED)
        with self.assertRaises(runtime.RuntimeStateError):
            state.transition(runtime.RunStatus.RUNNING)

    def test_exit_codes_map_to_stable_terminal_states(self) -> None:
        runtime = load_runtime()
        config = runtime.RuntimeConfig.from_mapping(valid_config(), DEFAULT_CONFIG)
        for exit_code, status, error_code in (
            (2, "FAIL_CLOSED", "MA_FAIL_CLOSED"),
            (3, "FAILED", "MA_COMMAND_FAILED"),
            (6, "FAILED", "MA_COMMAND_FAILED"),
        ):
            with self.subTest(exit_code=exit_code):
                machine = io.StringIO()
                result = runtime.execute_with_runtime(
                    Namespace(command="sync", dry_run=False),
                    lambda _args, code=exit_code: code,
                    config=config,
                    machine_stream=machine,
                    run_id_factory=lambda: "run-code",
                )
                event = json_events(machine.getvalue())[-1]
                self.assertEqual(result, exit_code)
                self.assertEqual(event["status"], status)
                self.assertEqual(event["error_code"], error_code)
                self.assertEqual(event["exit_code"], exit_code)

    def test_exception_event_exposes_type_only_and_reraises(self) -> None:
        runtime = load_runtime()
        machine = io.StringIO()

        def runner(_args: Namespace) -> int:
            raise ValueError("private /Users/example/token=do-not-log")

        with self.assertRaisesRegex(ValueError, "do-not-log"):
            runtime.execute_with_runtime(
                Namespace(command="audit", dry_run=False),
                runner,
                config=runtime.RuntimeConfig.from_mapping(valid_config(), DEFAULT_CONFIG),
                machine_stream=machine,
                run_id_factory=lambda: "run-error",
            )

        event = json_events(machine.getvalue())[-1]
        self.assertEqual(event["event"], "run_failed")
        self.assertEqual(event["status"], "FAILED")
        self.assertEqual(event["error_code"], "MA_UNHANDLED_EXCEPTION")
        self.assertEqual(event["exception_type"], "ValueError")
        self.assertNotIn("do-not-log", machine.getvalue())
        self.assertNotIn("/Users/", machine.getvalue())

    def test_logging_off_emits_nothing(self) -> None:
        runtime = load_runtime()
        machine = io.StringIO()
        config = runtime.RuntimeConfig.from_mapping(
            valid_config(machine_log_destination="off"), DEFAULT_CONFIG
        )
        result = runtime.execute_with_runtime(
            Namespace(command="build-atlas", dry_run=True),
            lambda _args: 0,
            config=config,
            machine_stream=machine,
        )
        self.assertEqual(result, 0)
        self.assertEqual(machine.getvalue(), "")

    def test_started_event_can_be_disabled_without_losing_terminal_event(self) -> None:
        runtime = load_runtime()
        machine = io.StringIO()
        config = runtime.RuntimeConfig.from_mapping(
            valid_config(emit_started_event=False), DEFAULT_CONFIG
        )
        result = runtime.execute_with_runtime(
            Namespace(command="build-atlas", dry_run=True),
            lambda _args: 0,
            config=config,
            machine_stream=machine,
        )
        events = json_events(machine.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual([event["event"] for event in events], ["run_finished"])

    def test_machine_log_transport_failure_never_changes_business_result(self) -> None:
        runtime = load_runtime()
        human = io.StringIO()

        class BrokenMachineStream(io.StringIO):
            def write(self, value: str) -> int:
                raise BrokenPipeError("machine log transport unavailable")

        def successful_runner(_args: Namespace) -> int:
            print('{"status":"PASS"}')
            return 0

        with redirect_stdout(human):
            result = runtime.execute_with_runtime(
                Namespace(command="sync", dry_run=True),
                successful_runner,
                config=runtime.RuntimeConfig.from_mapping(valid_config(), DEFAULT_CONFIG),
                machine_stream=BrokenMachineStream(),
            )
        self.assertEqual(result, 0)
        self.assertEqual(human.getvalue(), '{"status":"PASS"}\n')

        class TerminalBrokenMachineStream(io.StringIO):
            def __init__(self) -> None:
                super().__init__()
                self.write_count = 0

            def write(self, value: str) -> int:
                self.write_count += 1
                if self.write_count == 2:
                    raise BrokenPipeError("terminal machine log unavailable")
                return super().write(value)

        human = io.StringIO()
        with redirect_stdout(human):
            result = runtime.execute_with_runtime(
                Namespace(command="sync", dry_run=True),
                successful_runner,
                config=runtime.RuntimeConfig.from_mapping(valid_config(), DEFAULT_CONFIG),
                machine_stream=TerminalBrokenMachineStream(),
            )
        self.assertEqual(result, 0)
        self.assertEqual(human.getvalue(), '{"status":"PASS"}\n')

        def failing_runner(_args: Namespace) -> int:
            raise ValueError("original business failure")

        with self.assertRaisesRegex(ValueError, "original business failure"):
            runtime.execute_with_runtime(
                Namespace(command="audit", dry_run=False),
                failing_runner,
                config=runtime.RuntimeConfig.from_mapping(valid_config(), DEFAULT_CONFIG),
                machine_stream=BrokenMachineStream(),
            )


class RuntimeCoreCliTests(unittest.TestCase):
    def run_cli(self, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[bytes]:
        merged_env = os.environ.copy()
        if env:
            merged_env.update(env)
        return subprocess.run(
            [sys.executable, str(ATLASCTL), *args],
            cwd=ROOT,
            capture_output=True,
            check=False,
            env=merged_env,
        )

    def test_cli_default_preserves_stdout_hash_and_emits_machine_jsonl(self) -> None:
        result = self.run_cli("sync", "--source", "chatgpt", "--dry-run")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(hashlib.sha256(result.stdout).hexdigest(), CHATGPT_DRY_RUN_SHA256)
        events = json_events(result.stderr.decode("utf-8"))
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0]["event"], "run_started")
        self.assertEqual(events[1]["event"], "run_finished")
        self.assertEqual(events[1]["error_code"], "MA_OK")
        self.assertTrue(all(event["command"] == "sync" for event in events))

    def test_cli_config_override_off_restores_empty_stderr(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "runtime.json"
            write_config(config_path, valid_config(machine_log_destination="off"))
            result = self.run_cli(
                "sync",
                "--source",
                "chatgpt",
                "--dry-run",
                env={"MEMORY_ATLAS_RUNTIME_CONFIG": str(config_path)},
            )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(hashlib.sha256(result.stdout).hexdigest(), CHATGPT_DRY_RUN_SHA256)
        self.assertEqual(result.stderr, b"")

    def test_invalid_config_fails_closed_without_stdout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "runtime.json"
            write_config(config_path, valid_config(extra=True))
            result = self.run_cli(
                "sync",
                "--source",
                "chatgpt",
                "--dry-run",
                env={"MEMORY_ATLAS_RUNTIME_CONFIG": str(config_path)},
            )

        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, b"")
        events = json_events(result.stderr.decode("utf-8"))
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event"], "run_rejected")
        self.assertEqual(events[0]["error_code"], "MA_CONFIG_INVALID")
        self.assertNotIn(str(config_path), result.stderr.decode("utf-8"))

    def test_argument_error_preserves_usage_and_adds_machine_code(self) -> None:
        result = self.run_cli()

        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, b"")
        stderr = result.stderr.decode("utf-8")
        self.assertIn("usage: atlasctl", stderr)
        events = json_events(stderr)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event"], "run_rejected")
        self.assertEqual(events[0]["error_code"], "MA_ARGUMENT_INVALID")

    def test_direct_main_preserves_argparse_system_exit(self) -> None:
        module = load_atlasctl()
        stderr = io.StringIO()
        with self.assertRaises(SystemExit) as raised, redirect_stderr(stderr):
            module.main([])
        self.assertEqual(raised.exception.code, 2)
        self.assertIn("usage:", stderr.getvalue())
        self.assertEqual(json_events(stderr.getvalue())[0]["error_code"], "MA_ARGUMENT_INVALID")

    def test_bootstrap_rejection_uses_safe_fallback_when_runtime_logging_is_off(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "runtime.json"
            write_config(config_path, valid_config(machine_log_destination="off"))
            result = self.run_cli(env={"MEMORY_ATLAS_RUNTIME_CONFIG": str(config_path)})

        self.assertEqual(result.returncode, 2)
        events = json_events(result.stderr.decode("utf-8"))
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["error_code"], "MA_ARGUMENT_INVALID")


if __name__ == "__main__":
    unittest.main()
