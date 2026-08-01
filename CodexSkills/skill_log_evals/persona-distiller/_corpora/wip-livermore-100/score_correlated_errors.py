#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""相关性错误 / 共同幻觉：三次独立作答**错得一不一样**。

## 这是伪共识检测缺的那一半

动态伪共识测的是**措辞分散**，而措辞分散与共同幻觉完全兼容——
三次作答若从同一基础模型继承同一处事实错误，会用三套词把它说三遍，
分散度指标反而显示「高度独立」。

**要测共同幻觉，必须有对错标准。** 本脚本用 6 道 ground-truth 事实题，
答案全部来自本工作区**逐字核验过**的语料。

## 两个数

- **准确率**：答对几题。
- **★ 错误重合率**：在**至少一次答错**的题上，三次是不是**错成同一个样子**。
  这才是「共同幻觉」的操作化定义——**不是「都错了」，是「错得一样」。**

三次独立采样若彼此错法不同，说明错误是随机的；
若三次错向同一个方向，说明错误来自共享的先验，**采样再多也不会互相纠正**。

## 判据的射程

对错用**关键词命中**判定（`right_marker` / `wrong_marker`），不是语义判定。
它会漏掉换了说法的正确答案，也会漏掉换了说法的错误答案。
**所以准确率是下界，错误重合率是粗估。** 逐题原文一并打印，供人工复核。
"""
import itertools, json, pathlib, sys

def verdict(ans: str, spec: dict) -> str:
    a = ans.lower()
    hit_w = [m for m in spec["wrong_marker"] if m.lower() in a]
    hit_r = [m for m in spec["right_marker"] if m.lower() in a]
    if hit_r and not hit_w: return "对"
    if hit_w and not hit_r: return "错:" + hit_w[0]
    if hit_r and hit_w:     return "混:" + hit_w[0]
    return "未命中"

def main() -> int:
    SP = pathlib.Path(__file__).resolve().parent
    key = json.loads((SP/"ground_truth_key.json").read_text(encoding="utf-8"))
    groups = {"裸模型": ["gt_bare1","gt_bare2","gt_bare3"],
              "产物":   ["gt_prod1","gt_prod2","gt_prod3"]}
    out = {}
    for gname, files in groups.items():
        runs = []
        for f in files:
            p = SP/f"{f}.json"
            if not p.is_file():
                print(f"缺 {f}.json，跳过 {gname}"); runs = None; break
            runs.append(json.loads(p.read_text(encoding="utf-8")))
        if runs is None: continue
        right = 0; total = 0; err_tasks = 0; coincide = 0; detail = []
        for g, spec in key.items():
            vs = [verdict(str(r.get(g,"")), spec) for r in runs]
            total += 3; right += sum(1 for v in vs if v == "对")
            bad = [v for v in vs if v.startswith(("错","混"))]
            if bad:
                err_tasks += 1
                # 错得一样 = 所有错项的错误标记相同，且错项数 ≥2
                marks = {v.split(":",1)[1] for v in bad}
                if len(bad) >= 2 and len(marks) == 1: coincide += 1
            detail.append((g, vs))
        out[gname] = {"准确率": round(right/total,4), "答对": right, "总数": total,
                      "有错的题": err_tasks, "错得一样的题": coincide,
                      "错误重合率": round(coincide/err_tasks,4) if err_tasks else None}
        print(f"\n=== {gname} ===")
        print(f"  准确率 {right}/{total} = {right/total:.4f}")
        print(f"  有错的题 {err_tasks} ｜ 其中三次错成同一样 {coincide}"
              + (f" → **错误重合率 {coincide/err_tasks:.4f}**" if err_tasks else ""))
        for g, vs in detail: print(f"    {g}  {vs}")
    if len(out) == 2:
        b, p = out["裸模型"], out["产物"]
        print("\n★ 对比")
        print(f"  准确率      裸模型 {b['准确率']:.4f} → 产物 {p['准确率']:.4f}"
              f"　（{p['准确率']-b['准确率']:+.4f}）")
        if b["错误重合率"] is not None and p["错误重合率"] is not None:
            print(f"  错误重合率  裸模型 {b['错误重合率']:.4f} → 产物 {p['错误重合率']:.4f}"
                  f"　（{p['错误重合率']-b['错误重合率']:+.4f}）")
        elif p["有错的题"] == 0:
            print("  产物侧 0 题出错——**共同幻觉在这 6 题上未出现**（但 6 题是小样本）")
    (SP/"correlated_error_result.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0

if __name__ == "__main__":
    sys.exit(main())
