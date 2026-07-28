#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""【脚手架】32 条评测用例（16 套组 × 2）。每人复制一份，只填 put(...) 调用。

## 16 个套组（缺一个门就红）
known / boundary / voice / trajectory / contrast / fact-preservation / style-decoy /
task-completion / planning-fidelity / tool-use / capability-calibration / refusal-stop /
long-horizon / identity-routing / anonymous-fidelity / token-efficiency

## known 套组必须带 holdout_source_ids

**holdout 的抽取顺序**（RUNBOOK 第二十八、三十八种，两次踩坑换来的）：

    抓取 → 机械清洗 → 分层取样 → 【抽 holdout 并物理隔离】 → 通读 → 建工作区

- Maeda 一轮抽在**通读之后**——那篇我早已读过并摘录，等于自己给自己出题。
- Godin 一轮抽在**清洗之前**——抽中两个月度归档页，known 套组无题可出。
- 出题人（写 rubric 时）**必须**读 holdout，但那是在 claims 与文档**定稿冻结之后**。

## baseline 的写法

baseline 不是「写得平淡一点」，是**犯这个人物身上最典型的那种错**：
按名气答语料里没有的东西 / 把他转述他人的内容当成他的主张 / 混用两种语体。

⚠ **Maeda 一轮实测：两席给 baseline 的均值只有 0.055 与 0.009，delta 0.918 而门槛 0.07。**
**这道门实际上没在筛任何东西。** 下轮试把 baseline 改成
「**看起来合理但缺一个关键限定**」，让 delta 回到 0.15–0.35 的有信息量区间。

## 生成时断言
加粗成对闭合 / 无空加粗 / 无三连星号 / 引号内无省略号 /
rubric↔candidate 反查（rubric 写「答成 X 记为失败」而 candidate 恰是 X）/ 自指计数
"""
import collections, json, pathlib, re, sys

OUT = pathlib.Path(__file__).resolve().parent / "ws-XXXX/XXXX/evals/cases.jsonl"   # ← 改
PAYLOAD = pathlib.Path(__file__).resolve().parent / "judge_payload_XXXX.json"      # ← 改
HOLD = {}                                    # ← 每人填：别名 → src-xxxxxxxxxxxx

CASES = []


def put(suite, cid, prompt, rubric, cand, base, holdout=None):
    row = {"case_id": cid, "suite": suite, "prompt": prompt, "rubric": rubric}
    if holdout:
        row["holdout_source_ids"] = holdout
    CASES.append((row, cand, base))


# ── 自指计数判据（四次误报后定型，RUNBOOK 第三十种）────────────────
# 「一个数量级」「第一条」「两种写法」都曾被误判成条数声明。
# 补量词表是打地鼠（中文量词几百个，补不完），改判**句法角色**：
#   ① 声明在列表之前  ② 紧邻列表（40 字内）  ③ 同句内跟冒号或「如下」
# 找不到紧邻声明 = **「查不了」而不是「声明为 1」**。
_CN = {"一": 1, "两": 2, "二": 2, "三": 3, "四": 4, "五": 5,
       "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
_DECL = re.compile(r"([一两二三四五六七八九十]|\d+)\s*(?:条|点|项|个|处|种|步|方面|块|道|句|层|问)(?![个人月年])")
_ENUM = re.compile(r"\*\*第([一两二三四五六七八九十]|\d+)[、，,]?|"
                   r"\*\*([一两二三四五六七八九十]|\d+)[、，][^*]{2,}")


def _num(s):
    return _CN.get(s) or (int(s) if s and s.isdigit() else None)


def check(cid, text, label):
    assert text.count("**") % 2 == 0, ("加粗未闭合", cid, label)
    assert "****" not in text, ("空加粗", cid, label)
    assert "***" not in text.replace("****", ""), ("三连星号", cid, label)
    for seg in re.findall(r"「([^」]{20,})」", text):
        for mark in ("...", "…"):
            assert mark not in seg, (f"引号内含省略号（拼接的句子不是原句）{mark}", cid, label)
    marks_iter = list(_ENUM.finditer(text))
    if len(marks_iter) >= 2:
        first = marks_iter[0].start()
        W, LEAD = 40, 14
        decls = [m for m in _DECL.finditer(text)
                 if m.end() <= first and first - m.end() <= W
                 and re.search(r"^[^。！？\n]{0,%d}[：:]|^[^。！？\n]{0,%d}如下" % (LEAD, LEAD),
                               text[m.end():m.end() + LEAD + 2])]
        if decls:
            n = _num(decls[-1].group(1))
            marks = [x for x in (_num(m.group(1) or m.group(2)) for m in marks_iter) if x]
            # ★ 声明数必须 ≥2 才算数声明（Robertson #97，本族第 5 次误报）。
            #   这次触发的是「他能贡献的是很小的**一块**，而且是……那一套：」——
            #   「一块」是**部分量词**（一块/一套/一部分/一层），不是条数声明。
            #   没有人会写「以下一点：一、… 二、…」，所以「声明 1 而枚举 ≥2」
            #   在中文里**必然**是量词用法。这条不用维护量词表，也不动窗口参数。
            if n and n >= 2 and len(marks) >= 2:
                assert max(marks) == n, (f"自指计数不符：声明 {n}，枚举到 {max(marks)}", cid, label)


def main() -> int:
    rows, payload = [], []
    for row, cand, base in CASES:
        for txt, lab in ((row["rubric"], "rubric"), (cand, "candidate"), (base, "baseline")):
            check(row["case_id"], txt, lab)
        for m in re.finditer(r"答成「([^」]{4,40})」[^。]{0,26}记为失败", row["rubric"]):
            assert m.group(1) not in cand, ("candidate 踩中 rubric 明列的失败样例",
                                            row["case_id"], m.group(1))
        rows.append(row)
        payload.append({"case_id": row["case_id"], "prompt": row["prompt"],
                        "rubric": row["rubric"], "candidate": cand, "baseline": base})
    OUT.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    PAYLOAD.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    s = collections.Counter(r["suite"] for r in rows)
    bad = {k: v for k, v in s.items() if v != 2}
    print(f"用例 {len(rows)} 条 / 套组 {len(s)} 个 | 每组 2 条: {'✓' if not bad else '✗ '+str(bad)}")
    print(f"  known 带 holdout: {sum(1 for r in rows if r.get('holdout_source_ids'))} 条")
    assert len(s) == 16 and not bad, "套组数或每组条数不符"
    print("  ✓ 生成时断言全过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
