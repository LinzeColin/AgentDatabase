#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""候选答案母版 —— **每人照抄这一份，改三处即可。**

此前没有母版，每人各写一遍 `gen_XX_answers.py`。后果不是麻烦，是**规则只存在于副本里**：

- 长度约束（`MAX_AGG` / `MIN_SHORTER`）从 Virchow #109 起就在用，
  **一直是每份脚本里手抄的一段**——没有负对照、改一处不会同步到别处。
  v0.0.0.51 才把它落成 `check_answer_length_leak.py`。
- 各人物学到的纪律写在各自的文件头注释里，**下一个人看不到**。

本母版把两件事收拢：**长度规则调用共享判据**（不再手抄），
**纪律清单集中在这里**（下一个人照抄就带着走）。

## 纪律清单（前十人各用一次拒发换来）

- **Galen #101**：账本事实一条不写进人物答案（`fact` 里混进流水线自己的数就是这么来的）
- **Harvey #103 / Pasteur #106**：对手立场必指原文
- **Jenner #104 / Koch #107**：**引文逐字，讹字不代改**——
  `DoHors`／`WOQDVILLE` 顺手改正了再当逐字引文用，是伪造
- **Lister #108**：逐字引文必带可回原刊的坐标（读者拿什么去核）
- **Virchow #109**：文件名的年份不是版次年份；**把作业经历写进人物口吻是另一类错**
- **Osler #110**，四条，都用一轮换的：
  ① **归属依据里已握着的证据，第 1 轮就写进答案**——
     boundary 那条门本来够得着，我第 3 轮才补齐，补晚了；
  ② **流水线的内部量不许漏进人物答案**（「整体指标 0.399 在门槛 0.15 之上」）；
  ③ **人名没有一手依据就不报名字**——`check_unsourced_names` 现在会扫；
  ④ **同一处修改要改全**：「多处一致」这件事已经栽过四次，
     改完用 `check_shared_anchor` 看一眼跨题重复。

## 用法

    python3 gen_XX_answers.py            # 写出 XX_candidate.json 并跑长度门
"""
import json
import pathlib
import subprocess
import sys

# ── 改这三行即可 ──────────────────────────────────────────────
BASE_FILE = "XX_baseline_bare.json"     # {case_id: 基线答案}
OUT_FILE = "XX_candidate.json"          # 落盘的候选答案
CHECKER = "../../../../registry/codex/persona-distiller/scripts/check_answer_length_leak.py"
# ────────────────────────────────────────────────────────────

BASE = json.loads(pathlib.Path(BASE_FILE).read_text(encoding="utf-8"))
A: dict[str, str] = {}

# ══════════════════════════════════════════════════════════════
# 答案写在这里。**每条都要能一次被证伪**——
# 引文逐字、坐标齐全、推断标推断、没依据的说没依据。
# ══════════════════════════════════════════════════════════════

A["XX-known-01"] = (
    "**先给能一次证伪的那一句。**\n\n"
    "……")

# … 其余 31 条 …

# ══════════════════════════════════════════════════════════════
# 落盘 + 长度门。**规则不再手抄，调共享判据。**
# ══════════════════════════════════════════════════════════════
# **两个方向都要查。**只查一边时，母版自带的占位答案 `XX-known-01`
# 会跟着落盘——实测过一次：基线 32 条，落盘报「33 条已落盘」，
# 多出来的那条就是没删干净的占位。**多一条题号意味着占位没删或 id 写错了。**
missing = [k for k in BASE if k not in A]
extra = [k for k in A if k not in BASE]
if missing:
    raise SystemExit(f"**缺 {len(missing)} 条答案**：{missing[:6]}——"
                     "缺答案的题在盲判里等于送分，不许留空")
if extra:
    raise SystemExit(f"**多出 {len(extra)} 个题号**：{extra[:6]}——"
                     "占位没删，或者 case_id 写错了。**多的那条不会被判，但会误导你以为写全了。**")

out = pathlib.Path(OUT_FILE)
out.write_text(json.dumps(A, ensure_ascii=False, indent=1), encoding="utf-8")

script = pathlib.Path(__file__).resolve().parent / CHECKER
if not script.is_file():
    raise SystemExit(f"**长度判据不在：{script}**——"
                     "没跑成不是「没问题」，把路径改对再来")
proc = subprocess.run([sys.executable, str(script),
                       "--candidate", str(out), "--baseline", BASE_FILE],
                      capture_output=True, text=True)
print(proc.stdout.rstrip())
if proc.returncode != 0:
    # ★ **超了就重写，不打警告了事。**
    #   Lister #108 第 3 轮候选比基线长 +144%、32/32 全长，
    #   席 D：「长的一侧在 32/32 全部命中同一个系统——长度是完美泄题信号。」
    #   那一轮的 delta 因此分不清是内容挣的还是长度送的。
    out.unlink(missing_ok=True)
    raise SystemExit("**中止**——长度不许成为泄题信号；候选答案已删，改完再跑。")

print(f"✓ {len(A)} 条已落盘 → {OUT_FILE}")
