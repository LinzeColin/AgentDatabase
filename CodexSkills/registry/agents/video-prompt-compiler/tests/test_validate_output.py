from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import validate_output


class ValidateOutputTests(unittest.TestCase):
    def codes(self, text: str, route="text_to_video", preset="cinematic", duration=8, model=None, input_mode=None, constraints=None):
        return {item.code: item.level for item in validate_output.validate(text, route, preset, duration, model, input_mode, constraints or [])}

    def test_good_industrial_prompt(self):
        text = (
            "近景锁定镜头，机器人熔覆头沿固定夹持的钢制工件曲面匀速移动，"
            "工具中心线与表面保持稳定距离，熔池只在作用区域连续形成，少量颗粒向后落下。"
            "深灰车间环境，真实机械声。最后机器人停在工件右侧，工件结构和轴线始终保持不变。"
        )
        codes = self.codes(text, preset="industrial", duration=8)
        self.assertNotIn("INDUSTRIAL_NO_RELATION", codes)
        self.assertNotIn("INDUSTRIAL_NO_INVARIANT", codes)
        self.assertNotIn("INDUSTRIAL_NO_MATERIAL_RESPONSE", codes)
        self.assertNotIn("NO_END_STATE", codes)

    def test_i2v_requires_preserve(self):
        codes = self.codes("镜头缓慢推近，人物转头看向窗外，最后停下。", route="image_to_video", duration=5)
        self.assertEqual(codes.get("I2V_NO_PRESERVE"), "ERROR")

    def test_reference_requires_roles(self):
        codes = self.codes("参考这些素材生成一个人物走路镜头，最后停下。", route="reference_to_video")
        self.assertEqual(codes.get("REFERENCE_ROLE_MISSING"), "ERROR")

    def test_video_edit_requires_delta(self):
        codes = self.codes("保留原视频的人物和运镜，让画面更好看，最后停在人物特写。", route="video_edit", duration=8)
        self.assertEqual(codes.get("V2V_NO_DELTA"), "ERROR")

    def test_edit_requires_timecode(self):
        codes = self.codes("使用素材制作宣传片，最后放Logo和旁白。", route="footage_edit", duration=30)
        self.assertEqual(codes.get("EDIT_NO_TIMECODE"), "ERROR")

    def test_camera_conflict(self):
        codes = self.codes("锁定镜头，同时使用强烈手持跟拍人物，人物走到门口后最后停下。", duration=5)
        self.assertEqual(codes.get("CAMERA_CONFLICT"), "ERROR")

    def test_adjective_soup(self):
        codes = self.codes("高级感，电影感，科技感，震撼，8K masterpiece。", duration=5)
        self.assertEqual(codes.get("ADJECTIVE_SOUP"), "ERROR")

    def test_micro_performance_warns_without_gaze(self):
        codes = self.codes("人物低声说话，呼吸变慢，肩膀下沉，最后后退停下。", preset="micro_performance", duration=10)
        self.assertEqual(codes.get("PERFORMANCE_NO_GAZE"), "WARNING")

    def test_hailuo_character_limit(self):
        text = "人物走向窗边，最后停下。" + "细节" * 1000
        codes = self.codes(text, model="Hailuo 2.3")
        self.assertEqual(codes.get("HAILUO_PROMPT_LIMIT"), "ERROR")

    def test_ltx_word_budget(self):
        text = " ".join(["subject moves slowly"] * 80) + " finally settles"
        codes = self.codes(text, model="LTX-2")
        self.assertEqual(codes.get("LTX_WORD_BUDGET"), "WARNING")

    def test_h3_full_reference_schema(self):
        codes = self.codes("Image 1 defines the character. The character walks and finally stops.", route="reference_to_video", model="MiniMax H3", input_mode="full_reference")
        self.assertEqual(codes.get("H3_FULL_REFERENCE_SCHEMA"), "ERROR")

    def test_constraint_drop_is_error(self):
        codes = self.codes("人物走到窗边，最后停下。", constraints=["Logo文字不得改变"])
        self.assertEqual(codes.get("CONSTRAINT_DROPPED"), "ERROR")

    def test_retired_model_is_error(self):
        codes = self.codes("人物走到窗边，最后停下。", model="Sora 2")
        self.assertEqual(codes.get("RETIRED_MODEL"), "ERROR")


if __name__ == "__main__":
    unittest.main()
