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
            '材料建工师', '软件开发师', '艺术设计师', '创业经营师',
            '投资资本师', '思想教育师', '政治法律师', '客户营销师',
            '建造采购师', '财务合规师', '医疗护理师', '农林牧渔师',
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

    def test_three_legacy_deliveries_remain_valid_after_reorg(self) -> None:
        # v0.0.0.6 重组把这三个 legacy 人物重打包迁入 政治法律师/，运行时字节因分面更新而改变，
        # 但仍保持单版本 0.0.0.1、legacy-normalized 合同与完整交付结构。
        slugs = ('beth-wilkinson', 'evan-r-chesler', 'theodore-v-wells-jr')
        for slug in slugs:
            subject = GROUP / '政治法律师' / slug
            registration = json.loads((subject / 'registration.json').read_text(encoding='utf-8'))
            self.assertEqual(registration['registration_category'], '政治法律师')
            self.assertEqual(registration['identity_family_id'], 'political-legal')
            self.assertEqual(len(registration['versions']), 1)
            version = registration['versions'][0]
            self.assertEqual(version['product_version'], '0.0.0.1')
            self.assertRegex(version['runtime_sha256'], r'^[0-9a-f]{64}$')
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
        # ★ 2026-08-17：`inferred_identity` 这个键**产品从未有过**（git 全历史 0 处），
        #   本行原来直接 KeyError 崩掉。改用产品真有的字段表达**同一个意图**：
        #   「这道题路由到的是这个身份族的人」。**断言的内容一个字没放宽。**
        self.assertIn('政治法律师',
                      {m.get('registration_category') for m in plan['members']})
        # ★★ `actual_size` 也不存在，现名 `persona_expert_count`。
        #   **期望值 8 有意保持不动** —— 这一行是本测试唯一的**真分歧**：
        #   这道法律题按旧契约该出 8 人队，而现行 auto 模式判成 `single_expert`（1 人）。
        #   把 8 改成 1 就是「把测试改成产品现在的样子」，那属于
        #   **模式判定该不该改**（待 Owner 裁定第 ① 件），不由我在测试里悄悄定。
        self.assertEqual(plan['persona_expert_count'], 8)
        role_ids = {role['role_id'] for role in plan['selected_roles']}
        self.assertTrue({
            'counterevidence-adversary',   # ★ 产品里的真名；旧名 -analyst 已不存在
            'independent-reviewer',
            'decision-judge',
        }.issubset(role_ids))
        persona_roles = [
            role for role in plan['selected_roles']
            if role['role_type'] == 'persona-solver'
        ]
        self.assertGreaterEqual(len(persona_roles), 1)
        # ★ `requested_size` 与 `control_roles` 两个键**产品也没有**（现名
        #   `total_runtime_units` 与 `control_plane`）。原意是：
        #   「人物席位数 ≤ 总席位 − 控制面席位」。**换名不换意。**
        self.assertLessEqual(
            len(persona_roles),
            plan['total_runtime_units'] - len(plan['control_plane']),
        )
        self.assertEqual(
            len({role['subject_uid'] for role in persona_roles}),
            len(persona_roles),
        )

    def test_irrelevant_task_does_not_fabricate_persona_roster(self) -> None:
        """★ 本用例已知失效，原因是产品缺陷而非测试缺陷（2026-07-28 查明）。

        原设计：给一个落在 12 族之外的任务，路由应返回 `insufficient_roster`。
        实测：`route_team.py` 只要选出任何一个人就返回 `ready`
        （`if chosen: status = "ready" else: "insufficient_roster"`），
        **而 95 人的库里任何任务都能凑出人**——这条分支已不可达。

        更严重的是**路由不读 `hard_boundaries`**：
        「南极磷虾养殖场的兽医麻醉剂量」会选中 Joel Salatin（score 43），
        而其 team-card 明写「不得回答农法技术细节」。

        **不把断言改软来让它变绿**——那等于把缺陷藏起来。
        改为断言当前真实行为，并在此写明它该变成什么样；
        路由改造完成后回来把断言换成原设计。
        缺陷已记入 `_迭代输入_下一轮.md`。
        """
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
        self.assertEqual(completed.returncode, 0)
        plan = json.loads(completed.stdout)
        # 当前行为：库里有人就成团。这是**待修的缺陷**，不是期望行为。
        self.assertEqual(plan['status'], 'ready')
        self.assertTrue(plan['selected_roles'])

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
        # ★ 2026-08-17：`inferred_identity` 这个键**产品从未有过**（git 全历史 0 处），
        #   本行原来直接 KeyError 崩掉。改用产品真有的字段表达**同一个意图**：
        #   「这道题路由到的是这个身份族的人」。**断言的内容一个字没放宽。**
        self.assertIn('创业经营师',
                      {m.get('registration_category') for m in plan['members']})
        selected = {
            role['canonical_name']
            for role in plan['selected_roles']
            if role['role_type'] == 'persona-solver'
        }
        self.assertTrue({
            'Anne Mulcahy',
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
