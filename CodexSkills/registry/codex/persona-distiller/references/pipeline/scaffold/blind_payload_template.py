#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""盲判载荷母版 —— **每人照抄这一份，改三个文件名即可。**

此前没有母版，每人各写一遍 `build_XX_blind.py`，
于是**两条缺陷跟着复制了八个人**，两席在 Lister #108 三轮里共报了四次：

## 缺陷一：`case_id` 把期望行为写在题号上

`jl-refusal-stop-01` / `jl-style-decoy-02` / `jl-identity-routing-01`…
**题号直接告诉评委这题该拒答、该拒绝概括、该说不在范围内。**

> 席 D：「`case_id` 已把期望行为写进名字，照此类目搭建的一侧先占结构便宜；
>        这份盲判并不盲。」
> 席 E：「第七项 rubric 反向作弊无 rubric 可查，我改按 case_id 泄题看——
>        `refusal-stop`／`style-decoy`／`token-efficiency` 直接写在 id 里，
>        两侧都在照名字表演。」

本母版发给评委的是**不透明编号** `q-01`…`q-32`，套组归属只留在 key 里。

## 缺陷二：报了 A/B 侧的长度差，那不是该看的数

候选被 `sha256 % 2` 均分到两侧，**A/B 均长必然接近**——那是分配方式的产物，
不是「两个系统长度对等」。Lister 三轮实测：

| | A/B 侧差（此前报的） | **候选比基线长（该报的）** |
|---|---:|---:|
| 第 1 轮 | 5.5% | **73%** |
| 第 2 轮 | 0.8% | **109%** |
| 第 3 轮 | 8.7% | **144%** |

逐题 delta 与长度比的相关 r 从 +0.193 升到 +0.391；
**64 题里候选没有一道不比基线长**——数据内部没有长度对照。
席 D：「长的一侧在 32/32 全部命中同一个系统——长度是完美泄题信号。」

本母版**必报候选/基线的均长比**，并在超过 30% 时打出显著警告。

## 还没解决的（写在这里，免得下一个人以为它已经解决了）

- **长度混杂本身没有对照。** 要真正分开长度与质量，需要一个**长度对齐的基线**
  （让裸模型也写到同样长度）。那会改变对照的定义，**影响已入库的一百多人**，
  故属用户决定，不在本母版内自行更改。
- 席 D 另指出：约 12/32 是书目性问题（刊在哪、几期、卷首是不是你写的），
  **有语料的一侧必胜**。这部分是出题设计带来的差，不宜完全记作人物质量差。
  出题时留意配比。

用法（把 `XX` 换成人物缩写）：

    python3 build_XX_blind.py round1
    python3 build_XX_blind.py round2      # 会强制校验 A/B 映射与第 1 轮一致
"""
import hashlib
import json
import pathlib
import sys

# ── 改这三行即可 ──────────────────────────────────────────────
CAND = "XX_candidate.json"        # {case_id: 候选答案}
BASE = "XX_baseline_bare.json"    # {case_id: 基线答案}
PREFIX = "XX"                     # 落盘文件名前缀
# ────────────────────────────────────────────────────────────

OUT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "round1")
OUT.mkdir(parents=True, exist_ok=True)

cand = json.loads(pathlib.Path(CAND).read_text(encoding="utf-8"))
base = json.loads(pathlib.Path(BASE).read_text(encoding="utf-8"))
cases = {json.loads(l)["case_id"]: json.loads(l)["prompt"]
         for l in pathlib.Path("cases.jsonl").read_text(encoding="utf-8").splitlines()
         if l.strip()}

payload, key = [], {}
for i, cid in enumerate(sorted(cases), 1):
    if cid not in cand or cid not in base:
        raise SystemExit(f"缺答案：{cid}")
    flip = int(hashlib.sha256(cid.encode()).hexdigest(), 16) % 2
    A, Bv = (cand[cid], base[cid]) if flip == 0 else (base[cid], cand[cid])
    # ★ 发给评委的是不透明编号；真 case_id 与套组只留在 key 里。
    opaque = f"q-{i:02d}"
    key[opaque] = {"A": "candidate" if flip == 0 else "baseline",
                   "B": "baseline" if flip == 0 else "candidate",
                   "case_id": cid}
    payload.append({"case_id": opaque, "question": cases[cid], "A": A, "B": Bv})

(OUT / f"{PREFIX}_blind_payload.json").write_text(
    json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
(OUT / f"{PREFIX}_blind_key.json").write_text(
    json.dumps(key, ensure_ascii=False, indent=1), encoding="utf-8")

r1 = pathlib.Path("round1") / f"{PREFIX}_blind_key.json"
if OUT.name != "round1" and r1.is_file():
    if json.loads(r1.read_text(encoding="utf-8")) != key:
        raise SystemExit("★ A/B 映射与第 1 轮不一致——中止（轮次之间不可比）")
    print("A/B 映射与第 1 轮逐条一致 ✅")

n = len(cases)
lc = sum(len(cand[c]) for c in cases) / n
lb = sum(len(base[c]) for c in cases) / n
ratio = (lc - lb) / max(lb, 1) * 100
print(f"{n} 对；A 侧是候选的题数 {sum(1 for v in key.values() if v['A'] == 'candidate')}")
print(f"★ **候选均长 {lc:.0f}，基线均长 {lb:.0f}——候选比基线长 {ratio:+.0f}%**")
print("  （A/B 两侧的均长差**不是**该看的数：候选被均分到两侧，"
      "两侧接近是分配方式的产物）")
if abs(ratio) >= 30:
    print(f"  ⚠ **长度混杂显著（{ratio:+.0f}%）。** 给评委的提示里必须报这个真实比值，"
          "并要求他们在报告里说明长度对判断的影响。\n"
          "    这批数据分不开长度与质量——delta 不得据此支持「比裸模型强」。")
print("★ 题号已改为不透明编号 q-01…（套组归属只在 key 里）——"
      "两席在 Lister #108 三轮里共四次指出 case_id 泄题。")
