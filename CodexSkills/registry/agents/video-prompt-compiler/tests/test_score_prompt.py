from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import score_prompt


class ScorePromptTests(unittest.TestCase):
    def test_good_industrial_prompt_is_ready_for_model_test(self):
        text = (
            "近景锁定镜头，机器人熔覆头沿固定夹持的钢制工件曲面匀速移动，"
            "工具中心线与表面保持稳定距离，熔池只在作用区域连续形成，少量颗粒向后落下。"
            "真实车间机械声，无配乐。最后熔覆头减速并停在工件右侧，工件几何、轴线与夹持保持不变。"
            "未验证的温度、硬度和寿命保持 UNKNOWN。"
        )
        result = score_prompt.score_prompt(text, "机器人熔覆工业镜头", preset="industrial", duration=8, model="Seedance 2.0")
        self.assertNotEqual(result["status"], "BLOCKED_BY_HARD_GATE")
        self.assertGreaterEqual(result["overall_structural_score_percent"], 75)
        self.assertEqual(result["native_model_evidence"], "NOT_RUN")

    def test_chinese_source_anchors_are_not_collapsed_into_one_token(self):
        text = (
            "机器人熔覆头沿钢制工件曲面匀速移动，近景镜头保持工件轴线稳定，"
            "最后机器人减速停止，真实车间环境声。"
        )
        result = score_prompt.score_prompt(text, "机器人熔覆工业镜头", preset="industrial", duration=8)
        self.assertGreaterEqual(result["dimensions"]["intent_fidelity"]["score_percent"], 75)

    def test_adjective_soup_is_blocked(self):
        result = score_prompt.score_prompt("高级感，电影感，科技感，震撼，8K masterpiece。", duration=5)
        self.assertEqual(result["status"], "BLOCKED_BY_HARD_GATE")

    def test_missing_constraint_is_blocked(self):
        result = score_prompt.score_prompt("产品缓慢旋转，最后停下。", hard_constraints=["Logo文字不得改变"])
        self.assertEqual(result["status"], "BLOCKED_BY_HARD_GATE")

    def test_non_applicable_dimensions_are_none(self):
        result = score_prompt.score_prompt("人物走到窗边，锁定镜头，环境声安静，最后停下。")
        self.assertIsNone(result["dimensions"]["industrial_physics"]["score_percent"])
        self.assertIsNone(result["dimensions"]["reference_role_clarity"]["score_percent"])

    def test_reference_roles_score_high_when_explicit(self):
        text = "Image 1 defines identity and clothing. Video 1 provides walking motion. The camera tracks slowly. The character walks and finally stops. Ambient street sound."
        result = score_prompt.score_prompt(text, route="reference_to_video", model="MiniMax H3")
        self.assertGreaterEqual(result["dimensions"]["reference_role_clarity"]["score_percent"], 90)

    def test_unverified_model_lowers_fit(self):
        result = score_prompt.score_prompt("人物缓慢走到窗边，锁定镜头，环境声安静，最后停下。", model="Vendor Video 9")
        self.assertEqual(result["dimensions"]["model_input_fit"]["score_percent"], 45)

    def test_score_scope_is_explicit(self):
        result = score_prompt.score_prompt("人物缓慢走到窗边，锁定镜头，环境声安静，最后停下。")
        self.assertEqual(result["scope"], "STRUCTURAL_SPECIFICATION_COVERAGE_ONLY")
        self.assertEqual(result["external_verifier"], "NOT_RUN")


if __name__ == "__main__":
    unittest.main()
