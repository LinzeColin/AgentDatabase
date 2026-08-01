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

    def test_ocr_homoglyph_gate_has_a_working_negative_control(self) -> None:
        """没有负对照的检查器，其「全绿」不构成任何证据（RUNBOOK 第十八种）。"""
        completed = subprocess.run(
            [sys.executable, str(ROOT / 'scripts' / 'check_ocr_homoglyphs.py'), '--self-test'],
            cwd=str(ROOT), text=True, capture_output=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_verbatim_quote_check_cannot_see_ocr_homoglyphs(self) -> None:
        """回归：**逐字引文检查会说「找到了」**，因为脏字符在语料里确实存在。

        这正是 v0.0.0.17 立同形字门的理由——两件门查的是两回事：
        `check_verbatim_quotes` 回答「语料里有没有这句」，
        `check_ocr_homoglyphs` 回答「这句里的字符是不是真的」。
        本用例把这条分工钉死：**同形字门必须在引文层报错，且必须是它报的。**
        """
        sys.path.insert(0, str(ROOT / 'scripts'))
        try:
            import check_ocr_homoglyphs as gate
        finally:
            sys.path.pop(0)
        # `ТНЕ` 三个字母全是西里尔同形字——肉眼与 `THE` 无异
        dirty = 'It was never my thinking that made ТНЕ big money for me'
        self.assertIn(dirty, f'corpus … {dirty} … corpus',
                      '前提：这句在语料里逐字存在，所以逐字引文检查会放行')
        found = gate.scan_text(dirty)
        self.assertTrue(found['all_homoglyph'],
                        '同形字门必须抓出这句里的西里尔冒充字')
        clean = 'It was never my thinking that made the big money for me'
        self.assertFalse(gate.scan_text(clean)['all_homoglyph'],
                         '同一句的干净版本不许被误报')

    def test_own_voice_ratio_is_not_satisfied_by_reclassifying_tiers(self) -> None:
        """回归：`primary_ratio` 与「他的话有多少」量的不是一回事。

        Livermore #100 实测：532 份可用 train 里 530 份是同期报纸对他的报道，
        `primary_ratio = 0.9887`（deep 要 0.65，轻松通过），
        而 `own_voice_ratio = 0.0076`——**同一份语料，两个数差 130 倍**。

        本用例钉死一件事：**把 tier 全改成 P1 也不会让 own_voice_ratio 变大**。
        它只认账本 `author` 是不是这个人，不认 tier。
        """
        import tempfile
        sys.path.insert(0, str(ROOT / 'scripts'))
        try:
            import quality_check as qc
        finally:
            sys.path.pop(0)

        with tempfile.TemporaryDirectory() as td:
            target = Path(td)
            (target / 'raw').mkdir()
            (target / 'raw' / 'own.txt').write_text('x' * 100, encoding='utf-8')
            (target / 'raw' / 'about.txt').write_text('y' * 900, encoding='utf-8')
            meta = {'name': 'Jesse Lauriston Livermore'}

            def measure(tier_for_about: str) -> float:
                sources = [
                    {'source_id': 'src-a', 'local_path': 'raw/own.txt',
                     'author': 'Jesse L. Livermore', 'tier': 'P1', 'split': 'train'},
                    {'source_id': 'src-b', 'local_path': 'raw/about.txt',
                     'author': 'third-party newspaper report',
                     'tier': tier_for_about, 'split': 'train'},
                ]
                report = qc.Report(target, 'research', 'deep')
                qc.report_own_voice(report, target, meta, sources)
                return report.metrics['own_voice']['own_voice_ratio']

            self.assertAlmostEqual(measure('P2'), 0.1, places=4)
            self.assertAlmostEqual(measure('P1'), 0.1, places=4,
                                   msg='把第三方报道的 tier 改成 P1，own_voice_ratio 就变大了'
                                       '——那它又成了一个改标签就能满足的代理量')

    def test_self_authored_baseline_cannot_count_as_capability_evidence(self) -> None:
        """用户 2026-08-02 评分的机检对应物。

        本项目给每一件检查器都做了负对照，**唯独没有给产品本身做**。
        每个人物 eval 里的 `baseline` 是作者手写的稻草人——
        Livermore #100 第 2 轮 E 席原话：「候选/对照的分差被显著放大，
        不能当作能力证据」。本用例钉死：**缺字段与自撰稻草人一律不算能力证据**，
        而 `bare-model-run` 与 `prior-version` 算。
        """
        sys.path.insert(0, str(ROOT / 'scripts'))
        try:
            import check_baseline_provenance as gate
        finally:
            sys.path.pop(0)
        def ev(*sources):
            rows = [{'system': 'baseline', 'overall_score': 0.1,
                     **({'baseline_source': s} if s else {})} for s in sources]
            return gate.summarize(rows)['capability_evidence']
        self.assertTrue(ev('bare-model-run', 'bare-model-run'))
        self.assertTrue(ev('prior-version', 'prior-version'))
        self.assertFalse(ev('self-authored-strawman', 'self-authored-strawman'))
        self.assertFalse(ev(None, None), '缺 baseline_source 时不许沉默通过')
        self.assertFalse(ev('bare-model-run', 'self-authored-strawman'),
                         '混着来也不算——一条不可用就不能当能力证据')

    def test_baseline_provenance_gate_has_a_working_negative_control(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(ROOT / 'scripts' / 'check_baseline_provenance.py'), '--self-test'],
            cwd=str(ROOT), text=True, capture_output=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_activation_yield_cannot_be_gamed_by_adding_claim_markers(self) -> None:
        """回归：多挂几个 claim id 不能让「有效激活率」变好。

        Livermore #100 盲测实测：产物 payload_ratio 0.8351、裸模型 0.9868——
        产物每 6 行里有 1 行在谈自己的语料。若该指标能靠塞标记刷高，
        它就又成了一个改标签就能满足的代理量（第七十种）。
        """
        sys.path.insert(0, str(ROOT / 'scripts'))
        try:
            import check_activation_yield as gate
        finally:
            sys.path.pop(0)
        plain = '他在书中写道，买 500 股要先买 100 股。\n后面每一笔都必须比上一笔贵。\n'
        gamed = plain + ''.join(f'<!-- claim:clm-{i:012x} -->\n' for i in range(20))
        self.assertEqual(gate.analyse(plain)['payload_ratio'], 1.0)
        self.assertLess(gate.analyse(gamed)['payload_ratio'],
                        gate.analyse(plain)['payload_ratio'],
                        '塞入 claim 标记后 payload_ratio 必须下降')

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
