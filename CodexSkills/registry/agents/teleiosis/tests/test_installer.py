from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from helpers import ROOT
from teleiosis_core.common import TeleiosisError
from teleiosis_core.installer import default_skills_root, install, rollback
from teleiosis_core.integrity import verify_release


class InstallerTests(unittest.TestCase):
    def make_v3(self, root: Path, *, genesis: bool = True) -> Path:
        target = root / "teleiosis"
        target.mkdir(parents=True)
        (target / "VERSION").write_text("v0.0.0.3\n", encoding="utf-8")
        if genesis:
            locked = target / "constitution/GENESIS_LOCKED.v0.0.0.1.zh-CN.md"
            locked.parent.mkdir(parents=True)
            locked.write_bytes((ROOT / "constitution/GENESIS_LOCKED.v0.0.0.1.zh-CN.md").read_bytes())
        return target

    def test_fresh_install_and_strict_verify(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skills = Path(tmp) / "skills"
            result = install(skills_root=skills, source=ROOT)
            self.assertEqual(result["status"], "INSTALLED")
            self.assertEqual(verify_release(skills / "teleiosis", strict=True)["status"], "PASS")

    def test_idempotent_install(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skills = Path(tmp) / "skills"
            install(skills_root=skills, source=ROOT)
            result = install(skills_root=skills, source=ROOT)
            self.assertEqual(result["status"], "ALREADY_INSTALLED")
            self.assertTrue(result["verified"])

    def test_idempotent_install_allows_unmanaged_noncolliding_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skills = Path(tmp) / "skills"
            install(skills_root=skills, source=ROOT)
            (skills / "teleiosis/owner-note.txt").write_text("保留\n", encoding="utf-8")
            result = install(skills_root=skills, source=ROOT)
            self.assertEqual(result["status"], "ALREADY_INSTALLED")
            self.assertTrue((skills / "teleiosis/owner-note.txt").is_file())

    def test_dry_run_has_no_target_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skills = Path(tmp) / "skills"
            result = install(skills_root=skills, source=ROOT, dry_run=True)
            self.assertEqual(result["status"], "DRY_RUN_READY")
            self.assertFalse((skills / "teleiosis").exists())

    def test_v3_upgrade_preserves_unknown_noncolliding_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skills = Path(tmp) / "skills"
            target = self.make_v3(skills)
            (target / "legacy-owner-note.txt").write_text("不可丢失\n", encoding="utf-8")
            result = install(skills_root=skills, source=ROOT)
            self.assertEqual(result["status"], "INSTALLED")
            self.assertEqual((target / "VERSION").read_text(encoding="utf-8").strip(), "v0.0.0.5")
            self.assertEqual((target / "legacy-owner-note.txt").read_text(encoding="utf-8"), "不可丢失\n")
            self.assertIn("legacy-owner-note.txt", result["preserved_unknown_files"])

    def test_v3_ordinary_collision_uses_v5_and_keeps_backup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skills = Path(tmp) / "skills"
            target = self.make_v3(skills)
            (target / "README.md").write_text("旧说明\n", encoding="utf-8")
            result = install(skills_root=skills, source=ROOT)
            self.assertNotEqual((target / "README.md").read_text(encoding="utf-8"), "旧说明\n")
            backup = Path(result["backup"])
            self.assertEqual((backup / "README.md").read_text(encoding="utf-8"), "旧说明\n")

    def test_v4_upgrade_is_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skills = Path(tmp) / "skills"
            target = self.make_v3(skills)
            (target / "VERSION").write_text("v0.0.0.4\n", encoding="utf-8")
            (target / "v4-owner-note.txt").write_text("保留\n", encoding="utf-8")
            result = install(skills_root=skills, source=ROOT)
            self.assertEqual(result["status"], "INSTALLED")
            self.assertEqual((target / "VERSION").read_text(encoding="utf-8").strip(), "v0.0.0.5")
            self.assertEqual((target / "v4-owner-note.txt").read_text(encoding="utf-8"), "保留\n")

    def test_unknown_executable_collision_blocks_without_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skills = Path(tmp) / "skills"
            target = self.make_v3(skills)
            collision = target / "scripts/teleiosis.py"
            collision.parent.mkdir(parents=True)
            collision.write_text("raise SystemExit('owner')\n", encoding="utf-8")
            before = collision.read_bytes()
            with self.assertRaises(TeleiosisError) as ctx:
                install(skills_root=skills, source=ROOT)
            self.assertEqual(ctx.exception.code, "UNKNOWN_EXECUTABLE_COLLISION")
            self.assertEqual(collision.read_bytes(), before)
            self.assertEqual((target / "VERSION").read_text(encoding="utf-8").strip(), "v0.0.0.3")

    def test_wrong_genesis_blocks_without_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skills = Path(tmp) / "skills"
            target = self.make_v3(skills, genesis=False)
            locked = target / "constitution/GENESIS_LOCKED.v0.0.0.1.zh-CN.md"
            locked.parent.mkdir(parents=True)
            locked.write_text("篡改\n", encoding="utf-8")
            with self.assertRaises(TeleiosisError) as ctx:
                install(skills_root=skills, source=ROOT)
            self.assertEqual(ctx.exception.code, "TARGET_GENESIS_MISMATCH")
            self.assertEqual((target / "VERSION").read_text(encoding="utf-8").strip(), "v0.0.0.3")

    def test_higher_version_is_not_downgraded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skills = Path(tmp) / "skills"
            target = skills / "teleiosis"
            target.mkdir(parents=True)
            (target / "VERSION").write_text("v0.0.0.6\n", encoding="utf-8")
            with self.assertRaises(TeleiosisError) as ctx:
                install(skills_root=skills, source=ROOT)
            self.assertEqual(ctx.exception.code, "HIGHER_VERSION_REFUSED")

    def test_unrecognized_version_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skills = Path(tmp) / "skills"
            target = skills / "teleiosis"
            target.mkdir(parents=True)
            (target / "VERSION").write_text("legacy\n", encoding="utf-8")
            with self.assertRaises(TeleiosisError) as ctx:
                install(skills_root=skills, source=ROOT)
            self.assertEqual(ctx.exception.code, "TARGET_VERSION_UNSUPPORTED")

    def test_upgrade_can_be_rolled_back_exactly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skills = Path(tmp) / "skills"
            target = self.make_v3(skills)
            (target / "legacy.txt").write_text("v3\n", encoding="utf-8")
            result = install(skills_root=skills, source=ROOT)
            rolled = rollback(Path(result["receipt"]))
            self.assertEqual(rolled["status"], "ROLLED_BACK")
            self.assertEqual((target / "VERSION").read_text(encoding="utf-8").strip(), "v0.0.0.3")
            self.assertEqual((target / "legacy.txt").read_text(encoding="utf-8"), "v3\n")

    def test_fresh_install_receipt_cannot_fake_rollback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skills = Path(tmp) / "skills"
            result = install(skills_root=skills, source=ROOT)
            with self.assertRaises(TeleiosisError) as ctx:
                rollback(Path(result["receipt"]))
            self.assertEqual(ctx.exception.code, "ROLLBACK_NO_BACKUP")

    def test_symlink_target_is_refused(self) -> None:
        if not hasattr(os, "symlink"):
            self.skipTest("symlink unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            skills = base / "skills"
            skills.mkdir()
            elsewhere = base / "elsewhere"
            elsewhere.mkdir()
            os.symlink(elsewhere, skills / "teleiosis", target_is_directory=True)
            with self.assertRaises(TeleiosisError) as ctx:
                install(skills_root=skills, source=ROOT)
            self.assertEqual(ctx.exception.code, "TARGET_NOT_DIRECTORY")

    def test_symlink_skills_root_is_refused(self) -> None:
        if not hasattr(os, "symlink"):
            self.skipTest("symlink unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            real = base / "real"
            real.mkdir()
            link = base / "skills"
            os.symlink(real, link, target_is_directory=True)
            with self.assertRaises(TeleiosisError) as ctx:
                install(skills_root=link, source=ROOT)
            self.assertEqual(ctx.exception.code, "SKILLS_ROOT_SYMLINK")

    def test_nested_install_path_is_refused(self) -> None:
        with self.assertRaises(TeleiosisError) as ctx:
            install(skills_root=ROOT / "nested-skills", source=ROOT, dry_run=True)
        self.assertEqual(ctx.exception.code, "NESTED_PATHS")

    def test_codex_home_changes_default_user_root(self) -> None:
        with mock.patch.dict(os.environ, {"CODEX_HOME": "/tmp/example-codex-home"}, clear=False):
            self.assertEqual(default_skills_root(False), Path("/tmp/example-codex-home/skills"))


if __name__ == "__main__":
    unittest.main()
