from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
UPDATE = ROOT / "scripts/update_dynamic_profile.py"
VALIDATE = ROOT / "scripts/validate_dynamic_profile.py"
UPDATE_SPEC = importlib.util.spec_from_file_location(
    "dynamic_profile_update_under_test",
    UPDATE,
)
assert UPDATE_SPEC and UPDATE_SPEC.loader
update_module = importlib.util.module_from_spec(UPDATE_SPEC)
UPDATE_SPEC.loader.exec_module(update_module)


class DynamicProfileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        derived = self.root / "OpenAIDatabase/data/derived/behavior_intelligence"
        derived.mkdir(parents=True)
        self.source = derived / "low_value_loops.json"
        self.payload = {
            "schema_version": "memory_atlas_low_value_loops.v1",
            "generated_at": "2026-07-22T00:00:00Z",
            "loop_clusters": [
                {
                    "loop_type": "repeated_rework",
                    "event_count": 2,
                },
                {
                    "loop_type": "scope_creep",
                    "event_count": 3,
                },
            ],
        }
        self.write_payload()
        self.core = self.root / "OpenAIDatabase/data/derived/profile/CORE_PROFILE.md"
        self.core.parent.mkdir(parents=True)
        self.core.write_text(
            "# Core\n\n"
            "## High-weight Core Personalization\n\n"
            "- Prefer evidence-backed delivery.\n"
            "  - importance: high; confidence: high\n\n"
            "## End\n",
            encoding="utf-8",
        )
        self.recommendation = (
            self.root
            / "OpenAIDatabase/data/derived/codex/codex_agent_recommendations.json"
        )
        self.recommendation.parent.mkdir(parents=True)
        self.recommendation.write_text(
            json.dumps(
                {
                    "schema_version": "codex_agent_recommendations.v1",
                    "generated_at": "2026-07-22T00:00:00Z",
                    "memory": {
                        "current": [
                            {
                                "statement": "Prefer a deterministic profile view.",
                                "confidence": "high",
                                "evidence_count": 7,
                            }
                        ]
                    },
                    "meta_data": {"current": []},
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        raw = self.root / "OpenAIDatabase/data/raw"
        raw.mkdir(parents=True)
        (raw / "secret.txt").write_text("do not read this", encoding="utf-8")
        self.output = (
            self.root / "OpenAIDatabase/data/derived/profile/DYNAMIC_PROFILE.md"
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_payload(self) -> None:
        self.source.write_text(
            json.dumps(self.payload, ensure_ascii=False),
            encoding="utf-8",
        )

    def run_update(
        self,
        *,
        output: Path | None = None,
        check_only: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        command = [
            sys.executable,
            str(UPDATE),
            "--database-dir",
            str(self.root),
            "--output",
            str(output or self.output),
            "--now",
            "2026-07-22T12:00:00Z",
        ]
        if check_only:
            command.append("--check-only")
        return subprocess.run(command, text=True, capture_output=True)

    def run_validator(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(VALIDATE), "--profile", str(self.output)],
            text=True,
            capture_output=True,
        )

    def machine_plane(self) -> dict:
        content = self.output.read_text(encoding="utf-8")
        machine_text = content[4:].partition("\n---\n\n")[0]
        return json.loads(machine_text)

    def test_first_run_is_dual_plane_derived_only_and_valid(self) -> None:
        result = self.run_update()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"status": "CHANGED"', result.stdout)
        content = self.output.read_text(encoding="utf-8")
        self.assertIn("# Dynamic Personal Profile", content)
        self.assertNotIn("do not read this", content)
        machine = self.machine_plane()
        self.assertEqual(machine["input_mode"], "derived_only")
        self.assertFalse(machine["canonical_stable_profile_write"])
        self.assertEqual(machine["entry_count"], len(machine["entries"]))
        self.assertEqual(machine["entry_count"], 4)
        self.assertEqual(
            {
                entry["asset_candidate"]
                for entry in machine["entries"]
                if entry["type"] == "asset_candidate"
            },
            {"workflow"},
        )
        self.assertNotIn(
            "generated_at",
            " ".join(entry["statement"] for entry in machine["entries"]),
        )
        if os.name == "posix":
            self.assertEqual(stat.S_IMODE(self.output.stat().st_mode), 0o644)
        checked = self.run_validator()
        self.assertEqual(checked.returncode, 0, checked.stderr)

    def test_same_input_is_idempotent(self) -> None:
        first = self.run_update()
        self.assertEqual(first.returncode, 0, first.stderr)
        before = self.output.read_bytes()
        second = self.run_update()
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertIn("NO_CHANGE", second.stdout)
        self.assertEqual(before, self.output.read_bytes())

    def test_check_only_does_not_create_output(self) -> None:
        checked = self.run_update(check_only=True)
        self.assertEqual(checked.returncode, 0, checked.stderr)
        self.assertIn("WOULD_CHANGE", checked.stdout)
        self.assertFalse(self.output.exists())

    def test_missing_sources_stop_without_overwriting_previous_output(self) -> None:
        first = self.run_update()
        self.assertEqual(first.returncode, 0, first.stderr)
        before = self.output.read_bytes()
        for source in (self.source, self.core, self.recommendation):
            with self.subTest(source=source.name):
                payload = source.read_bytes()
                source.unlink()
                stopped = self.run_update()
                self.assertEqual(stopped.returncode, 2)
                self.assertIn("missing required derived source", stopped.stderr)
                self.assertEqual(before, self.output.read_bytes())
                source.write_bytes(payload)

    def test_invalid_json_stops_without_overwriting_previous_output(self) -> None:
        first = self.run_update()
        self.assertEqual(first.returncode, 0, first.stderr)
        before = self.output.read_bytes()
        self.source.write_text('{"broken":', encoding="utf-8")
        stopped = self.run_update()
        self.assertEqual(stopped.returncode, 2)
        self.assertIn("invalid JSON source", stopped.stderr)
        self.assertEqual(before, self.output.read_bytes())

    def test_source_read_error_stops_without_overwriting_previous_output(self) -> None:
        first = self.run_update()
        self.assertEqual(first.returncode, 0, first.stderr)
        before = self.output.read_bytes()
        real_read_bytes = Path.read_bytes

        def selective_read_bytes(path: Path) -> bytes:
            if path.resolve() == self.source.resolve():
                raise OSError("synthetic source read failure")
            return real_read_bytes(path)

        stdout = io.StringIO()
        stderr = io.StringIO()
        with (
            mock.patch.object(Path, "read_bytes", selective_read_bytes),
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
        ):
            returncode = update_module.main(
                [
                    "--database-dir",
                    str(self.root),
                    "--output",
                    str(self.output),
                    "--now",
                    "2026-07-22T12:00:00Z",
                ]
            )

        self.assertEqual(returncode, 2)
        self.assertIn("synthetic source read failure", stderr.getvalue())
        self.assertEqual(before, self.output.read_bytes())

    def test_existing_invalid_output_is_preserved(self) -> None:
        self.output.parent.mkdir(parents=True, exist_ok=True)
        self.output.write_text("invalid previous output\n", encoding="utf-8")
        before = self.output.read_bytes()
        stopped = self.run_update()
        self.assertEqual(stopped.returncode, 2)
        self.assertIn("existing output is invalid", stopped.stderr)
        self.assertEqual(before, self.output.read_bytes())

    def test_output_path_escape_is_rejected(self) -> None:
        escaped = self.root / "escaped.md"
        stopped = self.run_update(output=escaped)
        self.assertEqual(stopped.returncode, 2)
        self.assertIn("output must be", stopped.stderr)
        self.assertFalse(escaped.exists())

    @unittest.skipUnless(hasattr(os, "symlink"), "symlink support required")
    def test_allowlisted_symlink_source_is_rejected(self) -> None:
        outside = self.root / "outside.json"
        outside.write_text(
            json.dumps(self.payload, ensure_ascii=False),
            encoding="utf-8",
        )
        self.source.unlink()
        self.source.symlink_to(outside)
        stopped = self.run_update()
        self.assertEqual(stopped.returncode, 2)
        self.assertIn("symlink is forbidden", stopped.stderr)
        self.assertFalse(self.output.exists())

    def test_volatile_source_metadata_does_not_create_a_commit_candidate(self) -> None:
        first = self.run_update()
        self.assertEqual(first.returncode, 0, first.stderr)
        before = self.output.read_bytes()
        self.payload["generated_at"] = "2026-07-22T11:59:00Z"
        self.write_payload()
        second = self.run_update()
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertIn("NO_CHANGE", second.stdout)
        self.assertEqual(before, self.output.read_bytes())

    def test_exact_collectors_exclude_metadata_and_unscoped_markdown(self) -> None:
        self.core.write_text(
            "# Core\n\n"
            "## High-weight Core Personalization\n\n"
            "- Prefer evidence-backed delivery.\n"
            "  - importance: high; confidence: medium\n\n"
            "## Ignored Section\n\n"
            "- This unscoped bullet must not become a profile entry.\n",
            encoding="utf-8",
        )
        self.recommendation.write_text(
            json.dumps(
                {
                    "schema_version": "codex_agent_recommendations.v1",
                    "generated_at": "2026-07-22T00:00:00Z",
                    "memory": {
                        "current": [
                            {
                                "statement": "Prefer a deterministic profile view.",
                                "confidence": "high",
                                "evidence_count": 7,
                                "title": "Metadata title must not be emitted",
                            }
                        ]
                    },
                    "meta_data": {"current": []},
                    "top_topics": [
                        {"label": "Metadata topic must not be emitted", "count": 99}
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        result = self.run_update()
        self.assertEqual(result.returncode, 0, result.stderr)
        statements = " ".join(
            entry["statement"] for entry in self.machine_plane()["entries"]
        )
        self.assertIn("Prefer evidence-backed delivery.", statements)
        self.assertIn("Prefer a deterministic profile view.", statements)
        self.assertNotIn("unscoped bullet", statements)
        self.assertNotIn("Metadata title", statements)
        self.assertNotIn("Metadata topic", statements)

    def test_duplicate_json_key_is_rejected(self) -> None:
        self.source.write_text(
            '{"generated_at":"2026-07-22T00:00:00Z",'
            '"loop_clusters":[],"loop_clusters":[]}',
            encoding="utf-8",
        )
        stopped = self.run_update()
        self.assertEqual(stopped.returncode, 2)
        self.assertIn("invalid JSON source", stopped.stderr)
        self.assertFalse(self.output.exists())

    def test_validator_rejects_forbidden_evidence_and_human_drift(self) -> None:
        first = self.run_update()
        self.assertEqual(first.returncode, 0, first.stderr)
        content = self.output.read_text(encoding="utf-8")
        tampered = content.replace(
            "OpenAIDatabase/data/derived/behavior_intelligence/low_value_loops.json",
            "OpenAIDatabase/data/raw/secret.txt",
            1,
        )
        self.output.write_text(tampered, encoding="utf-8")
        forbidden = self.run_validator()
        self.assertNotEqual(forbidden.returncode, 0)
        self.assertIn("forbidden", forbidden.stderr)

        self.run_update()
        self.output.write_text(
            self.output.read_text(encoding="utf-8") + "human-only drift\n",
            encoding="utf-8",
        )
        drift = self.run_validator()
        self.assertNotEqual(drift.returncode, 0)
        self.assertIn("human plane", drift.stderr)

    def test_validator_rejects_windows_absolute_path_with_single_backslashes(self) -> None:
        first = self.run_update()
        self.assertEqual(first.returncode, 0, first.stderr)
        self.output.write_text(
            self.output.read_text(encoding="utf-8")
            + "\nLocal path: C:\\Users\\alice\\profile.txt\n",
            encoding="utf-8",
        )

        rejected = self.run_validator()

        self.assertNotEqual(rejected.returncode, 0)
        self.assertIn("forbidden content pattern", rejected.stderr)
        self.assertIn("[A-Za-z]", rejected.stderr)


if __name__ == "__main__":
    unittest.main()
