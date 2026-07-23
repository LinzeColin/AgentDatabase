from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from helpers import create_target, populate_release_ready, run_script


class PackageInstallMigrateTests(unittest.TestCase):
    def test_package_excludes_raw_and_holdout_bodies(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = create_target(root)
            populate_release_ready(target, root / 'materials')
            output = root / 'target.zip'
            run_script('package_target.py', target, '--output', output)
            with zipfile.ZipFile(output) as archive:
                names = archive.namelist()
            self.assertTrue(any(name.endswith('/PACKAGE_MANIFEST.json') for name in names))
            self.assertFalse(any('/raw/' in name for name in names))
            self.assertFalse(any('/references/holdout/' in name for name in names))
            self.assertFalse(any('/references/sources/' in name for name in names))
            self.assertTrue(any(name.endswith('/install.py') for name in names))
            self.assertTrue(any(name.endswith('/checksums.sha256') for name in names))

    def test_successful_registration_advances_only_that_persons_next_product_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = create_target(root)
            populate_release_ready(target, root / 'materials')
            registry = root / 'registry'
            skill_root = Path(__file__).resolve().parents[1]
            registry.mkdir()
            for category in ('技术工程', '企业领导', '金融投资', '软开设计', '思想教育', '政治法律', '多重身份'):
                shutil.copytree(skill_root / category, registry / category)
            shutil.copy2(skill_root / 'persona-registry-index.json', registry / 'persona-registry-index.json')
            first = root / 'first.zip'
            run_script('package_target.py', target, '--output', first, '--registry-root', registry)
            with zipfile.ZipFile(first) as archive:
                first_manifest = json.loads(archive.read(f'{target.name}/PACKAGE_MANIFEST.json'))
            self.assertEqual(first_manifest['product_version'], '0.0.0.1')
            run_script('register_persona.py', first, '--registry-root', registry)

            second = root / 'second.zip'
            run_script('package_target.py', target, '--output', second, '--registry-root', registry)
            with zipfile.ZipFile(second) as archive:
                second_manifest = json.loads(archive.read(f'{target.name}/PACKAGE_MANIFEST.json'))
            self.assertEqual(second_manifest['product_version'], '0.0.0.2')
            self.assertTrue(json.loads(run_script(
                'validate_persona_registry.py', '--registry-root', registry,
            ).stdout)['passed'])

    def test_installer_copy_backup_status_and_uninstall(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / 'persona-distiller'
            run_script('install.py', 'install', '--target', 'path', '--path', destination)
            self.assertTrue((destination / 'SKILL.md').is_file())
            skill_root = Path(__file__).resolve().parents[1]
            registered_artifacts = sorted(skill_root.glob('*/**/versions/**/*.zip'))
            self.assertTrue(registered_artifacts)
            for artifact in registered_artifacts:
                self.assertTrue((destination / artifact.relative_to(skill_root)).is_file())
            status = run_script('install.py', 'status', '--target', 'path', '--path', destination)
            self.assertTrue(json.loads(status.stdout)['valid'])
            run_script('install.py', 'install', '--target', 'path', '--path', destination, '--force')
            backups = list(destination.parent.glob(destination.name + '.backup-*'))
            self.assertTrue(backups)
            uninstalled = run_script('install.py', 'uninstall', '--target', 'path', '--path', destination, '--force')
            self.assertFalse(destination.exists())
            self.assertIsNotNone(json.loads(uninstalled.stdout)['backup'])

    def test_codex_default_is_dot_codex_and_duplicate_source_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fake_home = Path(tmp)
            environment = dict(os.environ, HOME=str(fake_home))
            command = [
                sys.executable,
                str(Path(__file__).resolve().parents[1] / 'scripts' / 'install.py'),
                'install',
                '--dry-run',
            ]
            first = subprocess.run(command, text=True, capture_output=True, env=environment)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(
                Path(json.loads(first.stdout)['destination']),
                fake_home / '.codex' / 'skills' / 'persona-distiller',
            )
            duplicate = fake_home / '.agents' / 'skills' / 'persona-distiller'
            duplicate.mkdir(parents=True)
            second = subprocess.run(command, text=True, capture_output=True, env=environment)
            self.assertEqual(second.returncode, 2)
            self.assertIn('conflicting source exists', second.stderr)

    def test_dot_migration_is_quarantined_and_optionally_promoted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = create_target(root)
            legacy = root / 'legacy-dot'
            legacy.mkdir()
            (legacy / 'persona.md').write_text('# Old Persona\nLegacy model.\n', encoding='utf-8')
            (legacy / 'work.md').write_text('# Old Work\nLegacy process.\n', encoding='utf-8')
            result = run_script('migrate_legacy.py', legacy, target, '--from', 'auto', '--promote')
            payload = json.loads(result.stdout)
            self.assertEqual(payload['kind'], 'dot')
            self.assertIn('unverified candidate', (target / 'persona.md').read_text(encoding='utf-8'))
            self.assertTrue((Path(payload['destination']) / 'migration-report.md').is_file())

    def test_self_check_without_recursive_test_run(self) -> None:
        completed = run_script('self_check.py', '--skip-tests')
        payload = json.loads(completed.stdout)
        self.assertTrue(payload['passed'], payload)


if __name__ == '__main__':
    unittest.main()
