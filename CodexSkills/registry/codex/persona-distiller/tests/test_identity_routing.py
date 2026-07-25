from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from helpers import create_target, make_namesake_gate, run_script, run_target_script


class IdentityRoutingTests(unittest.TestCase):
    def test_menu_contains_exactly_twelve_single_families(self) -> None:
        menu = run_script('identity.py', 'menu').stdout.strip()
        expected = [
            '1 材料建工师', '2 软件开发师', '3 艺术设计师', '4 创业经营师',
            '5 投资资本师', '6 思想教育师', '7 政治法律师', '8 客户营销师',
            '9 建造采购师', '10 财务合规师', '11 医疗护理师', '12 农林牧渔师',
        ]
        self.assertEqual(menu.split('｜'), expected)

    def test_single_aliases_resolve_to_canonical_families(self) -> None:
        cases = {
            '焊接': 'technical-engineer',
            '软件': 'software-developer',
            '设计': 'art-designer',
            'CEO': 'entrepreneur-operator',
            '投资': 'investor-capital-allocator',
            '教练': 'thinker-educator',
            '法官': 'political-legal',
            '营销': 'customer-marketing',
            '招投标': 'construction-procurement',
            '审计': 'finance-compliance',
            '临床': 'healthcare-nursing',
            '农业': 'agriculture-fishery',
        }
        for alias, expected in cases.items():
            with self.subTest(alias=alias):
                payload = json.loads(run_script('identity.py', 'parse', '--spec', alias).stdout)
                self.assertEqual(payload['mode'], 'single')
                self.assertEqual(payload['primary'], expected)
                self.assertEqual(payload['weights'], {expected: 1.0})

    def test_all_twelve_numbers_resolve_to_single(self) -> None:
        for number in range(1, 13):
            with self.subTest(number=number):
                payload = json.loads(run_script('identity.py', 'parse', '--spec', str(number)).stdout)
                self.assertEqual(payload['mode'], 'single')
                self.assertEqual(payload['weights'], {payload['primary']: 1.0})

    def test_weighted_selection_is_rejected(self) -> None:
        for spec in ('1:70+4:30', '技术工程师=0.7,思想教育=0.3', '{"1": 0.4, "6": 0.6}'):
            with self.subTest(spec=spec):
                failed = run_script('identity.py', 'parse', '--spec', spec, check=False)
                self.assertNotEqual(failed.returncode, 0)
                self.assertIn('多重身份已移除', failed.stderr)

    def test_private_target_uses_single_identity_and_requires_consent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            gate = make_namesake_gate(root, 'Private Mentor')
            blocked = run_script(
                'init_target.py', '--name', 'Private Mentor', '--slug', 'private-mentor',
                '--identity', '6', '--subject-origin', 'private', '--workspace', root,
                '--namesake-gate', gate,
            )
            self.assertEqual(json.loads(blocked.stdout)['status'], 'blocked-consent')

            target = root / 'private-mentor'
            run_script(
                'init_target.py', '--name', 'Private Mentor', '--slug', 'private-mentor',
                '--identity', '6', '--subject-origin', 'private', '--workspace', root,
                '--consent-authority', 'documented-owner-consent',
                '--retention-policy', 'delete raw after 30 days', '--force',
                '--namesake-gate', gate,
            )
            meta = json.loads((target / 'meta.json').read_text())
            self.assertEqual(meta['status'], 'draft')
            self.assertEqual(meta['identity_selection']['mode'], 'single')

    def test_fictional_and_historical_origins_use_single_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for origin in ['fictional', 'historical']:
                gate = make_namesake_gate(root, f'{origin} target')
                created = run_script(
                    'init_target.py', '--name', f'{origin} target', '--slug', f'{origin}-target',
                    '--identity', '1', '--subject-origin', origin, '--workspace', root,
                    '--namesake-gate', gate,
                )
                self.assertEqual(json.loads(created.stdout)['status'], 'draft')

    def test_runtime_router_uses_distilled_facets_without_user_identity_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = create_target(Path(tmp), identity='1')
            plan = json.loads(run_target_script(
                target, 'runtime_router.py', 'plan', '--task', '请诊断代码架构并复盘故障',
            ).stdout)
            self.assertIn('research-problem-solving', plan['scenarios'])
            self.assertIn('identity-facets/technical-engineer.md', plan['load_files'])
            self.assertFalse(plan['identity_route']['user_selection_required'])
            self.assertEqual(plan['identity_route']['strategy'], 'automatic-task-routing')
            self.assertFalse(any('/raw/' in item or 'references/research/' in item for item in plan['load_files']))
            rejected = run_target_script(
                target, 'runtime_router.py', 'plan', '--identity', '1', '--task', 'x', check=False,
            )
            self.assertNotEqual(rejected.returncode, 0)

    def test_empty_scenario_uses_identity_prior_without_user_scene_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = create_target(Path(tmp), identity='5')
            plan = json.loads(run_target_script(
                target, 'runtime_router.py', 'plan', '--task', '请处理这件事'
            ).stdout)
            self.assertEqual(plan['route_basis']['primary_basis'], 'distilled-identity-prior')
            self.assertEqual(plan['scenarios'][0], 'investment-business')
            self.assertIn('scenario-adapters/investment-business.md', plan['load_files'])

    def test_route_plan_automates_identity_and_disables_invocation_versions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = create_target(Path(tmp), identity='2')
            route = json.loads((target / 'route-manifest.json').read_text())
            self.assertEqual(route['runtime_identity_routing']['mode'], 'automatic')
            self.assertFalse(route['runtime_identity_routing']['user_selection_required'])
            self.assertFalse(route['runtime_invocation_versioning']['enabled'])
            self.assertEqual(route['product_release_versioning']['scope'], 'per-canonical-person')
            self.assertEqual(route['product_release_versioning']['maximum'], '0.0.0.999')


if __name__ == '__main__':
    unittest.main()
