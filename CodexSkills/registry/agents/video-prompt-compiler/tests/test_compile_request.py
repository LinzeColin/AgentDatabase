from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import compile_request


class CompileRequestTests(unittest.TestCase):
    def test_builds_ir_scaffold(self):
        ir = compile_request.build_ir("生成8秒竖屏工业镜头：机器人沿工件表面焊接", model="Seedance 2.0")
        self.assertEqual(ir["ir_version"], "0.2")
        self.assertEqual(ir["status"], "IR_SCAFFOLD")
        self.assertEqual(ir["production"]["duration_seconds"], 8)
        self.assertEqual(ir["production"]["aspect_ratio"], "9:16")
        self.assertIsNotNone(ir["scene_ir"]["physics_ledger"])

    def test_preserves_hard_constraints(self):
        ir = compile_request.build_ir("产品缓慢旋转", hard_constraints=["Logo文字不得改变", "只用一个镜头"])
        locked = ir["constraint_ledger"]["locked_facts"]
        self.assertIn("Logo文字不得改变", locked)
        self.assertIn("只用一个镜头", locked)

    def test_quotes_become_exact_content(self):
        ir = compile_request.build_ir("她低声说“别走”，然后停下")
        self.assertIn("别走", ir["scene_ir"]["audio"]["dialogue"])
        self.assertTrue(any("Exact quoted content: 别走" == item for item in ir["constraint_ledger"]["locked_facts"]))

    def test_reference_route_marks_missing_assets(self):
        ir = compile_request.build_ir("参考这个视频的动作和运镜，换成另一个人物")
        self.assertIn("required_asset_roles_and_identifiers", ir["constraint_ledger"]["unknowns"])

    def test_asset_roles_are_preserved(self):
        assets = [{"id": "Image1", "type": "image", "role": "identity"}]
        ir = compile_request.build_ir("参考图片生成视频", route="reference_to_video", assets=assets)
        self.assertEqual(ir["assets"][0]["role"], "identity")

    def test_footage_edit_preserves_source_and_target_durations(self):
        ir = compile_request.build_ir("把40秒真实工业素材剪成18秒品牌短片")
        self.assertEqual(ir["production"]["method"], "footage_edit")
        self.assertEqual(ir["production"]["source_duration_seconds"], 40)
        self.assertEqual(ir["production"]["duration_seconds"], 18)
        self.assertIn("Source media duration: 40 seconds", ir["constraint_ledger"]["locked_facts"])
        self.assertIn("Target duration: 18 seconds", ir["constraint_ledger"]["locked_facts"])

    def test_candidate_plan_has_two_branches(self):
        ir = compile_request.build_ir("做一个克制的产品广告")
        self.assertIn("precision_branch", ir["candidate_plan"])
        self.assertIn("expressive_branch", ir["candidate_plan"])
        self.assertTrue(ir["candidate_plan"]["selector"]["hard_gates_first"])

    def test_evidence_defaults_not_run(self):
        ir = compile_request.build_ir("生成一个镜头")
        self.assertEqual(ir["evidence"]["native_model_generation"], "NOT_RUN")
        self.assertEqual(ir["evidence"]["external_verifier"], "NOT_RUN")


if __name__ == "__main__":
    unittest.main()
