from __future__ import annotations

import json
import subprocess
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GROUP = ROOT.parent / 'persona-distiller-group'


class GroupContractTests(unittest.TestCase):
    def test_exact_identity_folders_and_registry_validation(self) -> None:
        expected = [
            '技术工程师', '创业经营家', '投资资本家', '开发设计家',
            '思想教育家', '政治法律家', '多重身份',
        ]
        manifests = sorted(
            path.parent.name
            for path in GROUP.glob('*/_category.json')
        )
        self.assertEqual(sorted(expected), manifests)
        completed = subprocess.run(
            [sys.executable, str(GROUP / 'scripts/validate_group.py')],
            cwd=GROUP,
            text=True,
            capture_output=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertTrue(json.loads(completed.stdout)['passed'])

    def test_three_legacy_deliveries_preserve_runtime_hashes(self) -> None:
        expected = {
            'beth-wilkinson': 'e0a30abd20dc8740bc35fd21840ff62d2492ffc64fb1b59ced4525a0e66e9802',
            'evan-r-chesler': 'cc97e267284eec2799656d1e357caa2b676b43e44e64449e285c1a4056becefd',
            'theodore-v-wells-jr': '462a320084a6ba73388a7133a8627f39cd13b2696adfbf3b8598c280e3a4197a',
        }
        for slug, runtime_hash in expected.items():
            subject = GROUP / '政治法律家' / slug
            registration = json.loads((subject / 'registration.json').read_text(encoding='utf-8'))
            self.assertEqual(len(registration['versions']), 1)
            version = registration['versions'][0]
            self.assertEqual(version['product_version'], '0.0.0.1')
            self.assertEqual(version['runtime_sha256'], runtime_hash)
            self.assertEqual(version['delivery_contract_status'], 'legacy-normalized-v0.0.0.5')
            artifacts = list((subject / 'versions/0.0.0.1').glob('*.zip'))
            self.assertEqual(len(artifacts), 1)
            with zipfile.ZipFile(artifacts[0]) as archive:
                names = archive.namelist()
                self.assertEqual(
                    len([name for name in names if '/runtime/' in name and name.endswith('.zip')]),
                    1,
                )
                self.assertTrue(any(name.endswith('/team-card.json') for name in names))
                self.assertTrue(any(name.endswith('/audit/verification.json') for name in names))

    def test_legal_task_routes_ready_team_with_isolated_controls(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(GROUP / 'scripts/route_team.py'),
                '--task',
                '为重大商事诉讼分析证据、证人、庭审策略、谈判和法律风险',
                '--size',
                '8',
            ],
            cwd=GROUP,
            text=True,
            capture_output=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        plan = json.loads(completed.stdout)
        self.assertEqual(plan['status'], 'ready')
        self.assertEqual(plan['inferred_identity'], '政治法律家')
        self.assertEqual(plan['actual_size'], 8)
        role_ids = {role['role_id'] for role in plan['selected_roles']}
        self.assertTrue({
            'counterevidence-analyst',
            'independent-reviewer',
            'decision-judge',
        }.issubset(role_ids))
        persona_roles = [
            role for role in plan['selected_roles']
            if role['role_type'] == 'persona-solver'
        ]
        self.assertGreaterEqual(len(persona_roles), 1)
        self.assertLessEqual(
            len(persona_roles),
            plan['requested_size'] - len(plan['control_roles']),
        )
        self.assertEqual(
            len({role['subject_uid'] for role in persona_roles}),
            len(persona_roles),
        )

    def test_irrelevant_task_does_not_fabricate_persona_roster(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(GROUP / 'scripts/route_team.py'),
                '--task',
                '制定南极磷虾养殖场的兽医麻醉剂量与病原体隔离方案',
            ],
            cwd=GROUP,
            text=True,
            capture_output=True,
        )
        self.assertEqual(completed.returncode, 3)
        plan = json.loads(completed.stdout)
        self.assertEqual(plan['status'], 'insufficient_roster')
        self.assertEqual(plan['selected_roles'], [])

    def test_new_operator_deliveries_are_available_to_routing(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(GROUP / 'scripts/route_team.py'),
                '--task',
                '为零售企业设计低价、库存周转、门店集群、物流密度、供应链和一线客户反馈的扩张战略',
                '--size',
                '8',
            ],
            cwd=GROUP,
            text=True,
            capture_output=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        plan = json.loads(completed.stdout)
        self.assertEqual(plan['status'], 'ready')
        self.assertEqual(plan['inferred_identity'], '创业经营家')
        selected = {
            role['canonical_name']
            for role in plan['selected_roles']
            if role['role_type'] == 'persona-solver'
        }
        self.assertTrue({
            'Anne Mulcahy',
            'Tim Cook',
            '路易斯·郭士纳 / Louis V. Gerstner Jr.',
        }.issubset(selected))

    def test_new_software_deliveries_are_available_to_routing(self) -> None:
        tasks = (
            (
                'Design a software engineering review covering TDD, refactoring, '
                'evolutionary architecture, Python SQLite CLI, coding-agent prompt '
                'injection, AI/ML evaluation monitoring feedback loops, distributed '
                'systems API type design and technical teaching',
                '14',
            ),
            (
                '评审软件架构、微服务与单体取舍、重构技术债、遗留系统渐进迁移、'
                '持续集成、领域语言和模块边界',
                '10',
            ),
        )
        selected: set[str] = set()
        for task, size in tasks:
            completed = subprocess.run(
                [
                    sys.executable,
                    str(GROUP / 'scripts/route_team.py'),
                    '--task',
                    task,
                    '--size',
                    size,
                ],
                cwd=GROUP,
                text=True,
                capture_output=True,
            )
            self.assertEqual(
                completed.returncode,
                0,
                completed.stdout + completed.stderr,
            )
            plan = json.loads(completed.stdout)
            self.assertEqual(plan['status'], 'ready')
            selected.update(
                role['canonical_name']
                for role in plan['selected_roles']
                if role['role_type'] == 'persona-solver'
            )
        self.assertTrue({
            'Barbara Liskov',
            'Chip Huyen',
            'Kent Beck',
            'Martin Fowler / 马丁·福勒',
            'Simon Willison',
        }.issubset(selected), selected)

    def test_human_views_register_required_card_fields(self) -> None:
        readme = (GROUP / 'README.md').read_text(encoding='utf-8')
        route = (GROUP / 'CANONICAL-ROOT-ROUTE.md').read_text(encoding='utf-8')
        index = json.loads((GROUP / 'team-index.json').read_text(encoding='utf-8'))
        products = index['products']
        self.assertIn(f'当前唯一登记：**{len(products)} 个人物**', readme)
        for category, count in index['category_counts'].items():
            self.assertIn(f'| `{category}/` | {count} |', readme)
        self.assertIn(f'| **总计** | **{len(products)}** |', readme)
        for product in products:
            self.assertIn(product['canonical_name'], readme)
            self.assertIn(product['canonical_name'], route)
        for header in (
            '选入原因', '最值得蒸馏的特点', '对用户的利益/帮助', '应用场景', '关键能力',
        ):
            self.assertIn(header, readme)


if __name__ == '__main__':
    unittest.main()
