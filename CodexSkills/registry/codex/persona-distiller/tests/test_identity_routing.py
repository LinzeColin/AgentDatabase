from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from helpers import create_target, run_script, run_target_script


class IdentityRoutingTests(unittest.TestCase):
    def test_menu_contains_exactly_six_main_plus_multi(self) -> None:
        menu = run_script('identity.py', 'menu').stdout.strip()
        expected = [
            '1 技术工程师', '2 创业经营家', '3 投资资本家', '4 开发设计家',
            '5 思想教育家', '6 政治法律家', '7 多重身份',
        ]
        self.assertEqual(menu.split('｜'), expected)

    def test_single_aliases_resolve_to_canonical_families(self) -> None:
        cases = {
            '科学家': 'technical-engineer',
            'CEO': 'entrepreneur-operator',
            '投资人': 'investor-capital-allocator',
            '导演': 'developer-designer',
            '教练': 'thinker-educator',
            '法官': 'political-legal',
        }
        for alias, expected in cases.items():
            with self.subTest(alias=alias):
                payload = json.loads(run_script('identity.py', 'parse', '--spec', alias).stdout)
                self.assertEqual(payload['mode'], 'single')
                self.assertEqual(payload['primary'], expected)
                self.assertEqual(payload['weights'], {expected: 1.0})

    def test_weighted_multi_normalizes_percent_and_fraction(self) -> None:
        payload = json.loads(run_script('identity.py', 'parse', '--spec', '1:70+4:30').stdout)
        self.assertEqual(payload['mode'], 'multi')
        self.assertAlmostEqual(sum(payload['weights'].values()), 1.0)
        self.assertEqual(payload['primary'], 'technical-engineer')
        self.assertEqual(payload['weights']['technical-engineer'], 0.7)
        payload_json = json.loads(run_script('identity.py', 'parse', '--spec', '{"技术工程师": 0.4, "思想教育家": 0.6}').stdout)
        self.assertEqual(payload_json['primary'], 'thinker-educator')

    def test_multi_menu_item_alone_is_rejected(self) -> None:
        failed = run_script('identity.py', 'parse', '--spec', '7', check=False)
        self.assertNotEqual(failed.returncode, 0)
        self.assertIn('至少两个', failed.stderr)

    def test_private_target_requires_weighted_multi_and_consent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            single = run_script(
                'init_target.py', '--name', 'Private Mentor', '--slug', 'private-mentor',
                '--identity', '5', '--subject-origin', 'private', '--workspace', root,
                check=False,
            )
            self.assertNotEqual(single.returncode, 0)
            self.assertIn('multi-identity', single.stderr)

            blocked = run_script(
                'init_target.py', '--name', 'Private Mentor', '--slug', 'private-mentor',
                '--identity', '1:40+5:60', '--subject-origin', 'private', '--workspace', root,
            )
            self.assertEqual(json.loads(blocked.stdout)['status'], 'blocked-consent')

            target = root / 'private-mentor'
            run_script(
                'init_target.py', '--name', 'Private Mentor', '--slug', 'private-mentor',
                '--identity', '1:40+5:60', '--subject-origin', 'private', '--workspace', root,
                '--consent-authority', 'documented-owner-consent', '--retention-policy', 'delete raw after 30 days', '--force',
            )
            self.assertEqual(json.loads((target / 'meta.json').read_text())['status'], 'draft')


    def test_fictional_and_historical_origins_use_multi_identity_route(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for origin in ['fictional', 'historical']:
                failed = run_script(
                    'init_target.py', '--name', f'{origin} target', '--slug', f'{origin}-target',
                    '--identity', '1', '--subject-origin', origin, '--workspace', root,
                    check=False,
                )
                self.assertNotEqual(failed.returncode, 0)
                self.assertIn('multi-identity', failed.stderr)
                created = run_script(
                    'init_target.py', '--name', f'{origin} target', '--slug', f'{origin}-target',
                    '--identity', '1:70+5:30', '--subject-origin', origin, '--workspace', root,
                )
                self.assertEqual(json.loads(created.stdout)['status'], 'draft')
                # Remove before the next origin reuses a distinct slug only for clarity.

    def test_runtime_router_loads_selected_facets_and_infers_scenario(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = create_target(Path(tmp), identity='1:60+4:40')
            menu = run_target_script(target, 'runtime_router.py', 'menu').stdout
            self.assertIn('请选择本次身份', menu)
            plan = json.loads(run_target_script(
                target, 'runtime_router.py', 'plan', '--identity', '1:70+4:30',
                '--task', '请诊断代码架构并评审产品设计',
            ).stdout)
            self.assertIn('research-problem-solving', plan['scenarios'])
            self.assertIn('identity-facets/technical-engineer.md', plan['load_files'])
            self.assertIn('identity-facets/developer-designer.md', plan['load_files'])
            self.assertFalse(any('/raw/' in item or 'references/research/' in item for item in plan['load_files']))


    def test_empty_scenario_uses_identity_prior_without_user_scene_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = create_target(Path(tmp), identity='3')
            plan = json.loads(run_target_script(
                target, 'runtime_router.py', 'plan', '--identity', '3', '--task', '请处理这件事'
            ).stdout)
            self.assertEqual(plan['route_basis']['primary_basis'], 'identity-prior')
            self.assertEqual(plan['scenarios'][0], 'investment-business')
            self.assertIn('scenario-adapters/investment-business.md', plan['load_files'])

    def test_route_plan_has_identity_gate_and_runtime_version_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = create_target(Path(tmp), identity='2')
            route = json.loads((target / 'route-manifest.json').read_text())
            self.assertTrue(route['runtime_identity_gate']['required_each_substantive_invocation'])
            self.assertFalse(route['runtime_identity_gate']['aborted_gate_consumes_version'])
            self.assertEqual(route['runtime_versioning']['format'], '0.0.0.N')
            self.assertTrue(route['runtime_versioning']['failed_runs_consume_serial'])


if __name__ == '__main__':
    unittest.main()
