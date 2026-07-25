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
    def test_no_candidate_is_ready_and_does_not_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            gate = make_namesake_gate(Path(tmp), 'Unknown Person')
            payload = json.loads(gate.read_text(encoding='utf-8'))
            self.assertEqual(payload['status'], 'ready')
            self.assertEqual(payload['resolution'], 'none')
            self.assertIsNone(payload['selected_subject_uid'])

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
