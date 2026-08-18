#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次运行产出的收据，必须说得出**是哪个版本跑的**。

## 它守的那件事（2026-08-18 实测 @v0.0.0.47）

把编排器 `run_team_pipeline.py` **真跑一次**（我一整天都在直调每一步），
读它产的四份文件：

    route-plan.json / team-dossier.json / execution-contract.json / run-receipt.json

**没有一份**能回答「这是哪个版本的 skill 跑的」——
文中出现的 `v0.0.0.1` 是**人物交付包**的版本，不是本 skill 的。

而仓内产物是有出身的：`team-index.json:generator_version`、
`expert-fleet-admission.json:source_generator_version`（后者本轮刚补进版本绑定门）。

⇒ **仓内产物有出身，运行产物没有** —— 而运行产物才是宿主真去执行、
用户出了问题会拿来对质的那一份。**收据存在的全部意义就是「这次跑了什么」。**

★ 只给**收据**加（它是这次运行的记录）。route-plan / dossier / contract 有各自的
  消费者与 schema，本轮不动，**但那三份仍然带不出版本号** —— 这句照实写在 CHANGELOG 里。
"""
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
PIPELINE = ROOT / "scripts" / "run_team_pipeline.py"
TASK = "为一个遗留微服务代码库设计测试策略与重构方案"


class RunReceiptCarriesItsVersion(unittest.TestCase):

    def _run(self):
        td = tempfile.mkdtemp()
        r = subprocess.run([sys.executable, str(PIPELINE), "--task", TASK, "--workdir", td],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return json.loads((pathlib.Path(td) / "run-receipt.json").read_text(encoding="utf-8"))

    def test_receipt_carries_the_generator_version(self):
        receipt = self._run()
        self.assertIn("generator_version", receipt,
                      "收据不带版本号 ⇒ 出了问题无从归因是哪个版本跑的")
        self.assertEqual(receipt["generator_version"],
                         (ROOT / "VERSION").read_text(encoding="utf-8").strip())

    def test_it_never_degrades_to_unknown(self):
        """★★ 读不到 VERSION 时要写 `None`，**不许写 "unknown"** ——
        `unknown` 会让下游一致性比对恒等成立（人物侧 v0.0.0.14 的原话）。"""
        # ★★★ 第一版这里直接扫源码文本，被**我自己写的那句注释**（「不写 "unknown"」）
        #   绊倒了 —— 断言分不清注释和代码。**判据要 key 在代码上，不要 key 在措辞上。**
        #   改成先用 tokenize 把注释剥掉再扫。[[checkers-must-key-on-a-closed-set-not-on-wording]]
        import io
        import tokenize
        raw = PIPELINE.read_text(encoding="utf-8")
        code = "".join(
            tok.string if tok.type != tokenize.COMMENT else ""
            for tok in tokenize.generate_tokens(io.StringIO(raw).readline))
        # ★ tokenize 会把 token 之间的空白也去掉（`_gen = None` → `_gen=None`），
        #   所以两边都去空白再比 —— 否则断言会因为**排版**而假红。
        flat = "".join(code.split())
        self.assertNotIn('"unknown"', flat,
                         "**代码里**出现了 unknown 兜底 ⇒ 会把「不知道」伪装成一致")
        self.assertIn("_gen=None", flat, "读不到时应当落到 None")

    def test_the_orchestrator_still_writes_all_four_files(self):
        """★ 本件跑的是**编排器**（不是直调三步）—— 四份产物一个都不能少。"""
        td = tempfile.mkdtemp()
        r = subprocess.run([sys.executable, str(PIPELINE), "--task", TASK, "--workdir", td],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        got = {p.name for p in pathlib.Path(td).glob("*.json")}
        for name in ("route-plan.json", "team-dossier.json",
                     "execution-contract.json", "run-receipt.json"):
            self.assertIn(name, got)

    def test_receipt_lists_the_files_it_claims(self):
        """★★★ 收据里的 `files` 必须**真的都在** —— 一张列着不存在文件的收据比没有更坏。"""
        td = tempfile.mkdtemp()
        subprocess.run([sys.executable, str(PIPELINE), "--task", TASK, "--workdir", td],
                       capture_output=True, text=True)
        wd = pathlib.Path(td)
        receipt = json.loads((wd / "run-receipt.json").read_text(encoding="utf-8"))
        for name in receipt.get("files", []):
            self.assertTrue((wd / name).is_file(), "收据列了 %s 但它不在" % name)


if __name__ == "__main__":
    unittest.main(verbosity=2)
