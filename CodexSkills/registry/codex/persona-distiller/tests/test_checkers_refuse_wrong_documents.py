#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""判据吃到**错文档**时，不许印肯定句。

为什么要有这份文件
------------------
2026-08-17 把「交叉喂错文档」这套测法先在 persona-distiller-group 上跑，
撞出 4 处「rc=0 还照样产出」；搬到本 skill 的 26 件吃文档判据上，
挑出 7 件 rc=0，其中 **3 件是真假绿**：

    check_rights_basis          ✓ 每一条公有领域声明都带得住的依据
    check_doc_command_shapes    ✓ 文档命令的参数形状与脚本一致
    check_evidence_is_per_claim ✓ 没有「填一次抄 N 遍」的证据字段

三句话在**空集上恒真**。而这不是合成案例：拿全部 60 份真账本跑
check_rights_basis，**23 份**此前都在印那句 ✓ 而其实零声明，
真正「有声明且全部有依据」的只有 4 份 —— 那道门的绿 23/27 是空的。

那次是我手工扫出来的。**手工扫出来的东西没有主人**，下一件新判据照样会
再犯一次。本件把那套扫法固定下来。
[[zero-hit-gates-must-prove-they-can-hit]]｜[[every-requirement-needs-an-owner]]

判据
----
喂一份与本判据毫不相干的 JSON，允许两种反应：

1. **拒答**（rc≠0）——最好；
2. rc=0 但**明说没核到**（「未核」「不是通过」「没读到」「无从比对」
   「什么也没查到」「不可信」之类）。

**不允许**的只有一种：rc=0 且印出肯定句（「✓ …一致」「✓ 每一条…」）。

★ 本件**印出实际跑到了几件**。扫描面为空或过小时自己报红 ——
  一件「跑了 0 个判据」的测试全绿，正是它要抓的那种病。
"""
import json
import pathlib
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
DIRISH = re.compile(r"root|dir|target|workdir|output|out$|corpora|workspace")
ARG = re.compile(r'add_argument\(\s*"(--[a-z0-9-]+)"[^)]*?type=pathlib\.Path'
                 r'|add_argument\(\s*"(--[a-z0-9-]+)"[^)]*?type=Path')
# 「我没核到」的各种说法。宁可宽——放宽只会让本判据**更难**报红，
# 而它要证明的是「一件都没有假绿」。[[loosen-only-the-exonerating-side]]
HONEST = re.compile(r"未核|不是通过|没读到|没扫到|无从比对|什么也没查到|不可信|"
                    r"都没有|本次未检查|一条.*都没|一个.*都没")
CLAIM = re.compile(r"✓")


def doc_args(path):
    src = path.read_text(encoding="utf-8", errors="replace")
    args = [(a or b) for a, b in ARG.findall(src)]
    return [a for a in args if not DIRISH.search(a.lstrip("-").replace("-", ""))]


class WrongDocumentTests(unittest.TestCase):
    def test_no_checker_affirms_on_a_wrong_document(self):
        with tempfile.TemporaryDirectory() as td:
            junk = pathlib.Path(td) / "junk.json"
            junk.write_text(json.dumps({"totally": "unrelated", "n": 1}),
                            encoding="utf-8")
            exercised, bad, skipped = [], [], []
            for p in sorted(SCRIPTS.glob("check_*.py")):
                docs = doc_args(p)
                if not docs:
                    continue
                cmd = [sys.executable, str(p)]
                for d in docs:
                    cmd += [d, str(junk)]
                r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(SCRIPTS))
                err = r.stderr or ""
                if "required" in err or "error:" in err:
                    skipped.append(p.name)      # 还需别的必填项，本件测不到
                    continue
                exercised.append(p.name)
                out = (r.stdout or "")
                if r.returncode == 0 and CLAIM.search(out) and not HONEST.search(out):
                    bad.append((p.name, next((l.strip() for l in out.splitlines()
                                              if "✓" in l), "")[:70]))

        print("扫描面：scripts/check_*.py 里吃文档的判据｜**实跑 %d 件**"
              "｜因还缺必填项测不到 %d 件" % (len(exercised), len(skipped)))
        if skipped:
            print("  测不到：%s" % "、".join(skipped))
        # ★ 空扫描面不算通过
        self.assertGreaterEqual(len(exercised), 8,
                                "只跑到 %d 件判据 —— 扫描面太小，本次不构成通过"
                                % len(exercised))
        if bad:
            for n, line in bad:
                print("  ✗ %-38s %s" % (n, line))
        self.assertEqual(bad, [], "有判据在错文档上印了肯定句：%s"
                         % [n for n, _ in bad])


if __name__ == "__main__":
    unittest.main(verbosity=0)
