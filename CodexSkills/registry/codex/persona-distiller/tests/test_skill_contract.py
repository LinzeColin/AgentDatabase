from __future__ import annotations

import hashlib
import io
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

    def test_identity_registry_is_exact_twelve_choice_contract(self) -> None:
        registry = json.loads((ROOT / 'registries/identity-families.json').read_text())
        self.assertEqual([item['number'] for item in registry['families']], list(range(1, 13)))
        self.assertEqual([item['zh'] for item in registry['families']], [
            '材料建工师', '软件开发师', '艺术设计师', '创业经营师', '投资资本师', '思想教育师',
            '政治法律师', '客户营销师', '建造采购师', '财务合规师', '医疗护理师', '农林牧渔师',
        ])

    def test_declared_version_has_exactly_one_source_of_truth(self) -> None:
        """回归：v0.0.0.13 时公开树同时声明了 7 个不同的版本号。

        根因是 self_check 的版本校验只比 VERSION 与 manifest.json 两处，
        另外六处（registry.yaml、registry/index.json、PACKAGE_MANIFEST.json、
        README、VERIFICATION、handoff）从来没人查，离发布脚本越远越旧。
        """
        completed = subprocess.run(
            [sys.executable, str(ROOT / 'scripts' / 'check_contract_drift.py'), '--json'],
            cwd=str(ROOT), text=True, capture_output=True,
        )
        payload = json.loads(completed.stdout)
        self.assertEqual(payload['problems'], [], payload['problems'])
        self.assertEqual(completed.returncode, 0)

    def test_contract_drift_gate_has_a_working_negative_control(self) -> None:
        """没有负对照的检查器，其「全绿」不构成任何证据（RUNBOOK 第十八种）。"""
        completed = subprocess.run(
            [sys.executable, str(ROOT / 'scripts' / 'check_contract_drift.py'), '--self-test'],
            cwd=str(ROOT), text=True, capture_output=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_skill_metadata_does_not_offer_removed_multi_identity_input(self) -> None:
        """metadata 是调用方唯一会读的那份；它与正文冲突时，冲突落到调用方头上。"""
        text = (ROOT / 'SKILL.md').read_text(encoding='utf-8')
        description = text.split('\n---\n', 1)[0]
        for token in ['multi-identity', 'multi identity', 'weighted multi', '多重身份']:
            self.assertNotIn(token, description)
        self.assertIn('多重身份已移除', text)

    def test_every_registered_persona_records_its_distiller_version(self) -> None:
        """原判据用一个包级数字冒充「每人一条记录」，改一个文件就能骗过。"""
        registry = ROOT.parent / 'persona-distiller-group'
        records = sorted(registry.glob('*/*/registration.json'))
        self.assertTrue(records)
        missing = []
        for path in records:
            for entry in json.loads(path.read_text(encoding='utf-8')).get('versions') or []:
                if not entry.get('distilled_with') or not entry.get('distilled_with_source'):
                    missing.append(path.parent.name)
        self.assertEqual(missing, [], f'这些人没有 distilled_with 记录: {missing[:10]}')

    def test_distillation_freshness_floor_is_current_minus_ten(self) -> None:
        """用户裁定：下限 = 当前版本末位 − 10（v0.0.0.98 → 0.0.0.88）。"""
        sys.path.insert(0, str(ROOT / 'scripts'))
        from check_distillation_freshness import floor_for, parse_version
        self.assertEqual(floor_for(parse_version('v0.0.0.98')), parse_version('v0.0.0.88'))
        self.assertEqual(floor_for(parse_version('v0.0.0.15')), parse_version('v0.0.0.5'))
        # 末位不足 10 时夹到 1，不得出现 0 或负数档
        self.assertEqual(floor_for(parse_version('v0.0.0.3')), parse_version('v0.0.0.1'))

    def test_freshness_gate_reports_but_does_not_block(self) -> None:
        """裁定是「下限以下不重蒸」——所以默认必须只报不拦，否则发行会被自己堵死。"""
        completed = subprocess.run(
            [sys.executable, str(ROOT / 'scripts' / 'check_distillation_freshness.py'), '--json'],
            cwd=str(ROOT), text=True, capture_output=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        report = json.loads(completed.stdout)
        self.assertEqual(report['total'],
                         report['at_or_above_floor'] + report['below_floor'] + report['unknown'])

    def test_freshness_gate_has_a_working_negative_control(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(ROOT / 'scripts' / 'check_distillation_freshness.py'), '--self-test'],
            cwd=str(ROOT), text=True, capture_output=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_delivery_manifest_stamps_distiller_version_from_version_file(self) -> None:
        """蒸馏版本必须**随产物走**——登记可能比蒸馏晚，那时的 VERSION 已经不是它。"""
        sys.path.insert(0, str(ROOT / 'scripts'))
        import delivery_builder
        self.assertEqual(delivery_builder.DISTILLER_VERSION,
                         (ROOT / 'VERSION').read_text(encoding='utf-8').strip())

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
                top = archive.namelist()[0].split('/', 1)[0]
            packaged = extract / top
            install_root = root / 'installed'
            installed = subprocess.run(
                [sys.executable, str(packaged / 'install.py'), '--root', str(install_root)],
                cwd=packaged, text=True, capture_output=True,
            )
            self.assertEqual(installed.returncode, 0, installed.stderr)
            payload = json.loads(installed.stdout)
            self.assertTrue(payload['delivery_verification']['verified'])
            self.assertTrue((install_root / target.name / 'SKILL.md').is_file())

            (packaged / 'team-card.json').write_text('tampered', encoding='utf-8')
            tampered = subprocess.run(
                [sys.executable, str(packaged / 'install.py'), '--root', str(root / 'tampered-install')],
                cwd=packaged, text=True, capture_output=True,
            )
            self.assertNotEqual(tampered.returncode, 0)
            self.assertIn('checksum mismatch', tampered.stderr)

    def test_package_has_single_top_level_product_version_and_unnumbered_runtime_reset(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = create_target(root)
            populate_release_ready(target, root / 'materials')
            subprocess.run(
                [
                    sys.executable,
                    str(target / 'scripts/runtime_recorder.py'),
                    'record',
                    '--status',
                    'completed',
                    '--task',
                    'internal run',
                ],
                cwd=target, text=True, check=True, capture_output=True,
            )
            package = root / 'target.zip'
            run_script('package_target.py', target, '--output', package)
            with zipfile.ZipFile(package) as archive:
                names = archive.namelist()
                top_levels = {name.split('/', 1)[0] for name in names if name}
                self.assertEqual(len(top_levels), 1)
                top = next(iter(top_levels))
                delivery_manifest = json.loads(archive.read(f'{top}/delivery-manifest.json'))
                runtime_path = f"{top}/{delivery_manifest['runtime']['path']}"
                runtime_bytes = archive.read(runtime_path)
                self.assertEqual(len([name for name in names if '/runtime/' in name and name.endswith('.zip')]), 1)
                self.assertFalse(any(name.endswith('.zip.sha256') for name in names))
            with zipfile.ZipFile(io.BytesIO(runtime_bytes)) as runtime_archive:
                meta = json.loads(runtime_archive.read(f'{target.name}/meta.json'))
                manifest = json.loads(runtime_archive.read(f'{target.name}/PACKAGE_MANIFEST.json'))
                invocations = runtime_archive.read(f'{target.name}/runtime/invocations.jsonl').decode('utf-8')
                episodic = runtime_archive.read(f'{target.name}/memory/episodic.jsonl').decode('utf-8')
                runtime_names = runtime_archive.namelist()
                self.assertFalse(any('/runtime/runs/' in name for name in runtime_names))
                self.assertFalse(any(name.endswith('/runtime/state.json') for name in runtime_names))
            self.assertEqual(meta['product_version'], '0.0.0.1')
            self.assertEqual(manifest['product_version'], '0.0.0.1')
            self.assertFalse(meta['runtime_invocation_versioning'])
            self.assertEqual(invocations, '')
            self.assertEqual(episodic, '')


if __name__ == '__main__':
    unittest.main()
