from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from helpers import make_namesake_gate, run_script


def candidate(name: str, uid: str, evidence_level: str = 'low') -> dict[str, object]:
    return {
        'canonical_name': name,
        'subject_uid': uid,
        'identity_category': '材料建工师',
        'occupation_or_role': '研究员',
        'professional_background': '组织、时代、地区与核心专业经历的低证据测试摘要',
        'application_scenarios': ['技术方案评审'],
        'key_capabilities': ['证据化比较方案'],
        'distinguishing_basis': '权威来源中的组织与时间线特征',
        'authoritative_sources': [{'locator': 'https://example.test/authority'}],
        'evidence_level': evidence_level,
    }


class NamesakeGateTests(unittest.TestCase):
    def test_no_candidate_is_unverified_not_ready(self) -> None:
        """**0 个候选不是「没有同名风险」，是「没核」。**

        本条原名 `test_no_candidate_is_ready_and_does_not_block`，断言 0 候选 → `ready`。
        那条断言**没有写任何理由**，它锁住的是缺陷而不是决定：

        全库回查 32 份同名产物，**9 份是 0 候选却 ready**——
        Koch #107／Lister #108／Pasteur #106／Semmelweis #105／Fleming #111／
        Blackwell #118／DeBakey #119／Benardos #128／**Thomson #129**。

        ★ Thomson 正是那次同名事故的人物：GE 总裁 Charles A. Coffin
        被当成焊接发明人的署名放行。**他的同名门就是在 0 候选下报的 ready。**

        护栏只比姓、本来就挡不住同姓者；再让「没喂候选」也算通过，这道门形同虚设。
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            empty = root / 'empty-candidates.json'
            empty.write_text('[]', encoding='utf-8')
            gate = root / 'gate.json'
            result = run_script('namesake_gate.py', '--name', 'Unknown Person',
                                '--candidates-file', empty, '--output', gate,
                                check=False)
            self.assertEqual(result.returncode, 4)
            payload = json.loads(gate.read_text(encoding='utf-8'))
            self.assertEqual(payload['status'], 'unverified')
            self.assertEqual(payload['resolution'], 'none')
            self.assertIsNone(payload['selected_subject_uid'])

    def test_single_candidate_still_ready(self) -> None:
        """★ 反向对照：**修完之后单一候选必须照旧过**，否则等于把门焊死。"""
        with tempfile.TemporaryDirectory() as tmp:
            gate = make_namesake_gate(Path(tmp), 'Unknown Person')
            payload = json.loads(gate.read_text(encoding='utf-8'))
            self.assertEqual(payload['status'], 'ready')
            self.assertEqual(payload['resolution'], 'single')

    def test_single_low_evidence_candidate_binds_without_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidates = root / 'candidates.json'
            candidates.write_text(json.dumps([candidate('One Person', 'person-1111111111111111')]), encoding='utf-8')
            gate = root / 'gate.json'
            result = run_script('namesake_gate.py', '--name', 'One Person', '--candidates-file', candidates, '--output', gate)
            self.assertEqual(result.returncode, 0)
            payload = json.loads(gate.read_text(encoding='utf-8'))
            self.assertEqual(payload['resolution'], 'single')
            self.assertEqual(payload['selected_subject_uid'], 'person-1111111111111111')
            self.assertEqual(payload['candidates'][0]['evidence_level'], 'low')

    def test_multiple_candidates_block_and_emit_all_cards(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidates = root / 'candidates.json'
            candidates.write_text(json.dumps([
                candidate('Same Name A', 'person-aaaaaaaaaaaaaaaa'),
                candidate('Same Name B', 'person-bbbbbbbbbbbbbbbb'),
            ]), encoding='utf-8')
            gate = root / 'gate.json'
            result = run_script(
                'namesake_gate.py', '--name', 'Same Name', '--candidates-file', candidates, '--output', gate, check=False,
            )
            self.assertEqual(result.returncode, 3)
            payload = json.loads(gate.read_text(encoding='utf-8'))
            self.assertEqual(payload['status'], 'blocked')
            self.assertEqual(payload['resolution'], 'multiple')
            self.assertEqual([item['label'] for item in payload['candidates']], ['A', 'B'])
            self.assertEqual(len(payload['candidate_cards']), 2)
            self.assertIn('人物与身份', payload['candidate_cards'][0])
            self.assertIn('专业背景', payload['candidate_cards'][0])
            self.assertIn('应用价值', payload['candidate_cards'][0])
            self.assertIn('区分依据', payload['candidate_cards'][0])


if __name__ == '__main__':
    unittest.main()
