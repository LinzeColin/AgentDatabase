from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import route_request


class RouteRequestTests(unittest.TestCase):
    def route(self, text: str, duration: float | None = None, model: str | None = None, aspect: str | None = None):
        return route_request.route_request(text, "auto", model, duration, "auto", aspect)

    def test_industrial_footage_edit(self):
        result = self.route("我有十字轴激光熔覆的真实原片，帮我剪成40秒竖屏企业宣传视频")
        self.assertEqual(result.route, "footage_edit")
        self.assertEqual(result.primary_preset, "industrial")
        self.assertEqual(result.duration_seconds, 40)
        self.assertEqual(result.aspect_ratio, "9:16")
        self.assertEqual(result.recommended_output_mode, "director")
        self.assertIn("source_timecodes", result.required_ir_fields)
        self.assertIn("physics_ledger", result.required_ir_fields)

    def test_source_only_duration_is_not_reused_as_target(self):
        result = self.route("我有40秒真实素材，帮我剪辑成品牌短片")
        self.assertEqual(result.route, "footage_edit")
        self.assertEqual(result.source_duration_seconds, 40)
        self.assertIsNone(result.duration_seconds)

    def test_source_and_target_durations_in_chinese_footage_edit(self):
        result = self.route("把40秒竖屏真实工业素材剪成18秒品牌短片，保留原设备和工人")
        self.assertEqual(result.route, "footage_edit")
        self.assertEqual(result.source_duration_seconds, 40)
        self.assertEqual(result.duration_seconds, 18)
        self.assertEqual(result.recommended_output_mode, "director")

    def test_image_to_video(self):
        result = self.route("让这张设备照片动起来，镜头缓慢环绕", 5)
        self.assertEqual(result.route, "image_to_video")
        self.assertIn("preserve_from_image", result.required_ir_fields)
        self.assertIn("Runway Gen-4.5", result.model_candidates)

    def test_micro_performance(self):
        result = self.route("女生听到分手后克制地对视，眼泪不要立刻掉下来", 10, "Kling 3.0")
        self.assertEqual(result.primary_preset, "micro_performance")
        self.assertEqual(result.target_model, "Kling VIDEO 3.0")
        self.assertEqual(result.target_model_status, "ACTIVE_OFFICIAL")
        self.assertIn("reaction_timing", result.required_ir_fields)

    def test_true_3d(self):
        result = self.route("根据真实尺寸建立可测量CAD模型并做应力场仿真", 30)
        self.assertEqual(result.route, "true_3d_handoff")
        self.assertIn("Blender/CAD", result.model_candidates[0])
        self.assertTrue(any("engineering simulation" in warning for warning in result.warnings))

    def test_reference_reverse(self):
        result = self.route("拆解这个参考视频的提示词结构、运镜和微表情")
        self.assertEqual(result.route, "reference_reverse")
        self.assertEqual(result.recommended_output_mode, "reverse")

    def test_screenplay_route(self):
        result = self.route("把这个剧本转分镜并输出逐镜头视频prompt")
        self.assertEqual(result.route, "screenplay_to_shots")
        self.assertIn("character_bible", result.required_ir_fields)

    def test_prompt_optimize_route(self):
        result = self.route("优化这条 prompt，给我电影级版本")
        self.assertEqual(result.route, "prompt_optimize")
        self.assertIn("precision_candidate", result.required_ir_fields)

    def test_unknown_model_not_inferred(self):
        result = self.route("生成一个产品镜头", 6, "Seedance 2.5 Pro")
        self.assertEqual(result.target_model_status, "VERIFY_AT_RUNTIME")
        self.assertTrue(any("not a verified registry" in warning for warning in result.warnings))

    def test_retired_model_warns(self):
        result = self.route("生成一个人物镜头", 6, "Sora 2")
        self.assertEqual(result.target_model_status, "RETIRED_NON_DEFAULT")
        self.assertTrue(any("RETIRED_NON_DEFAULT" in warning for warning in result.warnings))

    def test_short_action_budget(self):
        result = self.route("生成一个机器人焊接镜头", 4)
        self.assertIn("1 primary subject action", result.action_budget)


if __name__ == "__main__":
    unittest.main()
