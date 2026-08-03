from __future__ import annotations

import ast
import json
import os
import tempfile
import unittest
from pathlib import Path

from helpers import ROOT, make_subject, write_json
from teleiosis_core.common import (
    TeleiosisError,
    atomic_write_text,
    iter_tree_files,
    redact,
    safe_relative_path,
    sha256_file,
    tree_digest,
)
from teleiosis_core.integrity import load_manifest
from teleiosis_core.workflow import init_run, status_run, submit_stage


class SecurityTests(unittest.TestCase):
    def test_all_python_sources_parse(self) -> None:
        parsed = 0
        for path in ROOT.rglob("*.py"):
            if any(part == "__pycache__" for part in path.parts):
                continue
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            parsed += 1
        self.assertGreater(parsed, 15)

    def test_release_tree_has_no_symlink_or_junk(self) -> None:
        files = list(iter_tree_files(ROOT, include_manifest=True))
        self.assertGreater(len(files), 80)
        self.assertFalse(any(path.is_symlink() for _, path in files))

    def test_locked_genesis_digest_is_exact(self) -> None:
        path = ROOT / "constitution/GENESIS_LOCKED.v0.0.0.1.zh-CN.md"
        self.assertEqual(sha256_file(path), "14ab08b9053db4ca87140e59a49f1de8105a718a87ec2d55590c6487c1a77086")

    def test_safe_relative_path_rejects_parent_escape(self) -> None:
        with self.assertRaises(TeleiosisError) as ctx:
            safe_relative_path("../escape")
        self.assertEqual(ctx.exception.code, "UNSAFE_PATH")

    def test_safe_relative_path_rejects_absolute_path(self) -> None:
        with self.assertRaises(TeleiosisError) as ctx:
            safe_relative_path("/tmp/escape")
        self.assertEqual(ctx.exception.code, "UNSAFE_PATH")

    def test_manifest_rejects_self_reference(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "MANIFEST.sha256").write_text("0" * 64 + "  0  MANIFEST.sha256\n", encoding="utf-8")
            with self.assertRaises(TeleiosisError) as ctx:
                load_manifest(root)
            self.assertEqual(ctx.exception.code, "MANIFEST_DUPLICATE")

    def test_atomic_write_refuses_symlink(self) -> None:
        if not hasattr(os, "symlink"):
            self.skipTest("symlink unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            target = base / "target.txt"
            target.write_text("owner\n", encoding="utf-8")
            link = base / "link.txt"
            os.symlink(target, link)
            with self.assertRaises(TeleiosisError) as ctx:
                atomic_write_text(link, "overwrite")
            self.assertEqual(ctx.exception.code, "SYMLINK_REFUSED")
            self.assertEqual(target.read_text(encoding="utf-8"), "owner\n")

    def test_redaction_masks_tokens_and_secret_keys(self) -> None:
        value = {"token": "sensitive", "message": "Bearer abcdefghijklmnopqrstuvwxyz"}
        redacted = redact(value)
        self.assertEqual(redacted["token"], "[REDACTED]")
        self.assertIn("[REDACTED]", redacted["message"])
        self.assertNotIn("abcdefghijklmnopqrstuvwxyz", redacted["message"])

    def test_tree_digest_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "b.txt").write_text("b\n", encoding="utf-8")
            (root / "a.txt").write_text("a\n", encoding="utf-8")
            first = tree_digest(root)
            second = tree_digest(root)
            self.assertEqual(first, second)

    def test_workspace_root_pollution_is_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            workspace = base / "run"
            init_run(make_subject(base / "subject"), workspace, "RUN-POLLUTION")
            (workspace / "unapproved.txt").write_text("x\n", encoding="utf-8")
            with self.assertRaises(TeleiosisError) as ctx:
                status_run(workspace)
            self.assertEqual(ctx.exception.code, "WORKSPACE_POLLUTION")

    def test_subject_and_workspace_cannot_be_nested(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            subject = make_subject(Path(tmp) / "subject")
            with self.assertRaises(TeleiosisError) as ctx:
                init_run(subject, subject / "run", "RUN-NESTED")
            self.assertEqual(ctx.exception.code, "NESTED_PATHS")

    def test_invalid_evidence_does_not_delete_existing_stage_evidence(self) -> None:
        from helpers import load_state, stage_result
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            workspace = base / "run"
            init_run(make_subject(base / "subject"), workspace, "RUN-EVIDENCE-ATOMIC")
            existing = workspace / ".teleiosis/evidence/stage-00"
            existing.mkdir()
            (existing / "owner.txt").write_text("keep\n", encoding="utf-8")
            state = load_state(workspace)
            missing = base / "missing.json"
            result = stage_result(workspace, state, status="EXECUTED", evidence_path=missing)
            write_json(workspace / "NEXT_STAGE.json", result)
            with self.assertRaises(TeleiosisError) as ctx:
                submit_stage(workspace, workspace / "NEXT_STAGE.json")
            self.assertEqual(ctx.exception.code, "EVIDENCE_FILE_INVALID")
            self.assertEqual((existing / "owner.txt").read_text(encoding="utf-8"), "keep\n")

    def test_run_state_never_records_credentials(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            workspace = base / "run"
            init_run(make_subject(base / "subject"), workspace, "RUN-NO-CREDS")
            environment = json.loads((workspace / ".teleiosis/environment.json").read_text(encoding="utf-8"))
            self.assertEqual(environment["credentials"], "not-recorded")
            self.assertNotIn("env", environment)


if __name__ == "__main__":
    unittest.main()
