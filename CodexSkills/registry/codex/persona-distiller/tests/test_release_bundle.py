from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import pathlib
import unittest
import zipfile
from pathlib import Path

from helpers import ROOT, run_script


_VER = (pathlib.Path(__file__).resolve().parent.parent / 'VERSION')\
       .read_text(encoding='utf-8').strip()


class ReleaseBundleTests(unittest.TestCase):
    def test_complete_release_is_one_deterministic_zip_and_installs_both_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = root / "first.zip"
            second = root / "second.zip"
            run_script("build_release_bundle.py", "--output", first)
            run_script("build_release_bundle.py", "--output", second)
            self.assertEqual(
                hashlib.sha256(first.read_bytes()).hexdigest(),
                hashlib.sha256(second.read_bytes()).hexdigest(),
            )
            self.assertEqual(sorted(path.suffix for path in root.iterdir()), [".zip", ".zip"])
            extract = root / "extract"
            # ★ 两边必须同口径。原来这里数的是**所有版本**（v*.zip），
            #   而下面的断言只数 v0.0.0.1——同一人物有 v2 时（Soros、Icahn）就对不上，
            #   库存一增加测试必红。改为只数 v0.0.0.1，与断言一致。
            expected_deliveries = len(
                list(
                    (ROOT.parent / "persona-distiller-group").glob(
                        "*/**/versions/*/*-persona-distillation-delivery-v0.0.0.1.zip"
                    )
                )
            )
            with zipfile.ZipFile(first) as archive:
                names = archive.namelist()
                top_levels = {name.split("/", 1)[0] for name in names if name}
                self.assertEqual(top_levels, {f"PersonaDistiller-Final-{_VER}"})
                self.assertFalse(any(name.endswith(".zip.sha256") for name in names))
                self.assertEqual(
                    len(
                        [
                            name
                            for name in names
                            if "/persona-distiller-group/" in name
                            and name.endswith("-persona-distillation-delivery-v0.0.0.1.zip")
                        ]
                    ),
                    expected_deliveries,
                )
                archive.extractall(extract)
            package = extract / f"PersonaDistiller-Final-{_VER}"
            manifest = json.loads((package / "PACKAGE_MANIFEST.json").read_text())
            self.assertTrue(manifest["single_archive_only"])
            self.assertFalse(manifest["person_name_constraints"])
            install_root = root / "skills"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(package / "install.py"),
                    "--root",
                    str(install_root),
                ],
                cwd=package,
                text=True,
                capture_output=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            result = json.loads(completed.stdout)
            self.assertTrue(result["installed_validation"]["builder_passed"])
            self.assertTrue(result["installed_validation"]["group_passed"])
            for name in ("persona-distiller", "persona-distiller-group"):
                self.assertTrue((install_root / name / "SKILL.md").is_file())
                self.assertEqual(
                    (install_root / name / "VERSION").read_text().strip(),
                    _VER,
                )

    def test_complete_release_installer_rejects_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_zip = root / "release.zip"
            run_script("build_release_bundle.py", "--output", package_zip)
            extract = root / "extract"
            with zipfile.ZipFile(package_zip) as archive:
                archive.extractall(extract)
            package = extract / f"PersonaDistiller-Final-{_VER}"
            (package / "README.md").write_text("tampered\n", encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(package / "install.py"),
                    "--root",
                    str(root / "skills"),
                ],
                cwd=package,
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("checksum mismatch", completed.stderr)


if __name__ == "__main__":
    unittest.main()
