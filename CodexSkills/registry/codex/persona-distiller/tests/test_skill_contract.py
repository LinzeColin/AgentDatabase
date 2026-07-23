from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from helpers import ROOT, create_target, populate_release_ready, run_script


class SkillContractTests(unittest.TestCase):
    def test_root_skill_frontmatter_and_explicit_invocation_contract(self) -> None:
        for rel in ['SKILL.md', 'templates/target/SKILL.md.tmpl']:
            text = (ROOT / rel).read_text(encoding='utf-8')
            self.assertTrue(text.startswith('---\n'))
            frontmatter = text.split('\n---\n', 1)[0].splitlines()[1:]
            keys = [line.split(':', 1)[0].strip() for line in frontmatter if ':' in line and not line.startswith(' ')]
            self.assertEqual(keys, ['name', 'description'])
        self.assertLessEqual(len((ROOT / 'SKILL.md').read_text().splitlines()), 500)
        self.assertIn('allow_implicit_invocation: false', (ROOT / 'agents/openai.yaml').read_text())
        self.assertIn('allow_implicit_invocation: false', (ROOT / 'templates/target/agents/openai.yaml.tmpl').read_text())

    def test_identity_registry_is_exact_seven_choice_contract(self) -> None:
        registry = json.loads((ROOT / 'registries/identity-families.json').read_text())
        self.assertEqual([item['number'] for item in registry['families']], list(range(1, 8)))
        self.assertEqual([item['zh'] for item in registry['families']], [
            '技术工程师', '创业经营家', '投资资本家', '开发设计家', '思想教育家', '政治法律家', '多重身份',
        ])

    def test_six_reviewer_harness_passes_both_rounds(self) -> None:
        for round_number in [1, 2]:
            payload = json.loads(run_script('review_harness.py', '--round', round_number).stdout)
            self.assertTrue(payload['passed'], payload)
            self.assertEqual(len(payload['reviews']), 6)
            self.assertIn('not six independently running models', payload['method'])

    def test_target_package_is_deterministic_for_unchanged_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = create_target(root)
            populate_release_ready(target, root / 'materials')
            out_a = root / 'a.zip'
            out_b = root / 'b.zip'
            run_script('package_target.py', target, '--output', out_a)
            run_script('package_target.py', target, '--output', out_b)
            self.assertEqual(hashlib.sha256(out_a.read_bytes()).hexdigest(), hashlib.sha256(out_b.read_bytes()).hexdigest())

    def test_packaged_target_installer_verifies_checksums_and_rejects_tamper(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = create_target(root)
            populate_release_ready(target, root / 'materials')
            package = root / 'target.zip'
            run_script('package_target.py', target, '--output', package)
            extract = root / 'extract'
            with zipfile.ZipFile(package) as archive:
                archive.extractall(extract)
            packaged = extract / target.name
            install_root = root / 'installed'
            installed = subprocess.run(
                [sys.executable, str(packaged / 'install.py'), '--root', str(install_root)],
                cwd=packaged, text=True, capture_output=True,
            )
            self.assertEqual(installed.returncode, 0, installed.stderr)
            payload = json.loads(installed.stdout)
            self.assertTrue(payload['verification']['verified'])
            self.assertTrue((install_root / target.name / 'SKILL.md').is_file())

            (packaged / 'facts.md').write_text('tampered', encoding='utf-8')
            tampered = subprocess.run(
                [sys.executable, str(packaged / 'install.py'), '--root', str(root / 'tampered-install')],
                cwd=packaged, text=True, capture_output=True,
            )
            self.assertNotEqual(tampered.returncode, 0)
            self.assertIn('checksum mismatch', tampered.stderr)

    def test_package_has_single_top_level_and_runtime_state_is_reset(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = create_target(root)
            populate_release_ready(target, root / 'materials')
            subprocess.run(
                [sys.executable, str(target / 'scripts/invocation_manager.py'), 'begin', '--identity', '1', '--task', 'internal run'],
                cwd=target, text=True, check=True, capture_output=True,
            )
            package = root / 'target.zip'
            run_script('package_target.py', target, '--output', package)
            with zipfile.ZipFile(package) as archive:
                names = archive.namelist()
                top_levels = {name.split('/', 1)[0] for name in names if name}
                self.assertEqual(top_levels, {target.name})
                state = json.loads(archive.read(f'{target.name}/runtime/state.json'))
                invocations = archive.read(f'{target.name}/runtime/invocations.jsonl').decode('utf-8')
                episodic = archive.read(f'{target.name}/memory/episodic.jsonl').decode('utf-8')
            self.assertEqual(state['last_serial'], 0)
            self.assertEqual(invocations, '')
            self.assertEqual(episodic, '')


if __name__ == '__main__':
    unittest.main()
