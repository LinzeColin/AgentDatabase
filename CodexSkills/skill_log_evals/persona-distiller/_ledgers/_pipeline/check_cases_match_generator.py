#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**重跑生成器，产物不许变** —— 抓「改了 jsonl 没改生成器」。

2026-08-13 的事故：出戏 rubric 与写反的次序，我直接改在 `evals/cases.jsonl` 上，
**生成器里还是旧文本**。后来为加题重跑了一次生成器 —— **四条修复当场回潮**，
其中一条是把次序写反的 `ff-voice-01`（那是评分标准，答对的人会被判错）。

★★ **必须在工作树干净时跑**（`git status` 无改动）——否则它会把「你正在做的改动」
   也读成「手改过」。判据自己会先检查这一条，不干净就直接说「未核验」。

用法：`python3 check_cases_match_generator.py`
      `python3 check_cases_match_generator.py --self-test`
→ 依次跑每个 `gen_cases_*.py`，再看 `git status` 里有没有 `cases.jsonl` 被改动。
**有改动 = 该文件被手改过，生成器没跟上。**
"""
import argparse
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                      capture_output=True, text=True).stdout.strip()


def changed_cases(status_out: str):
    """→ `git status --porcelain` 里被改动的 `evals/cases.jsonl` 行。

    ★★ 抽成纯函数**只为了能自测**：原来这段判断埋在 `main()` 里，
      静态检查看着有判据、而**没有任何用例走过它**——
      本项目已记过「自测不经过 main() 的判据，94/100 件如此」。
    ★ 只认**以 `evals/cases.jsonl` 结尾**的路径：`results.jsonl` 不是产物、
      `cases.jsonl.bak` 不是它、`…/evals/cases.jsonl` 在任何目录深度都算。
    """
    return [l.strip() for l in status_out.splitlines()
            if l.strip().endswith("evals/cases.jsonl")]


def self_test() -> int:
    ok = n = 0

    def chk(d, c):
        nonlocal ok, n
        n += 1
        ok += 1 if c else 0
        print(f"  {'✓' if c else '✗'} {d}")

    chk("★ 真形状：改动的 cases.jsonl 要被认出来",
        changed_cases(" M CodexSkills/x/_corpora/wip-a/workspaces/p/evals/cases.jsonl")
        == ["M CodexSkills/x/_corpora/wip-a/workspaces/p/evals/cases.jsonl"])
    chk("★ 反例：results.jsonl **不是**产物，不许认",
        changed_cases(" M a/evals/results.jsonl") == [])
    chk("★ 反例：备份文件不许认", changed_cases(" M a/evals/cases.jsonl.bak") == [])
    chk("★ 反例：同名但不在 evals/ 下的不许认", changed_cases(" M a/tmp/cases.jsonl") == [])
    chk("★ 干净的工作树 → 空", changed_cases("") == [])
    chk("★ 多行里只挑出 cases.jsonl（其余改动不当成缺陷）",
        len(changed_cases(" M a/evals/cases.jsonl\n M b/persona.md\n?? c/evals/cases.jsonl")) == 2)
    print(f"\n{'✓ 全过' if ok == n else f'✗ {n - ok}/{n} 项不符'}")
    return 0 if ok == n else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    if ap.parse_args().self_test:
        return self_test()
    dirty = subprocess.run(["git", "-c", "core.quotepath=false", "status", "--porcelain"],
                           capture_output=True, text=True, cwd=ROOT).stdout.strip()
    if dirty:
        print("★ 工作树不干净（%d 行改动）——**未核验，不是通过**。" % len(dirty.splitlines()))
        print("  先提交或暂存，再跑本件。")
        return 2
    gens = sorted(HERE.glob("gen_cases_*.py"))
    if not gens:
        print("★ 一个生成器都没找到——**未核验**，不是通过")
        return 1
    for g in gens:
        subprocess.run([sys.executable, str(g)], capture_output=True, cwd=str(HERE))
    out = subprocess.run(["git", "-c", "core.quotepath=false", "status", "--porcelain"],
                         capture_output=True, text=True, cwd=ROOT).stdout
    bad = changed_cases(out)
    print("跑过 %d 个生成器" % len(gens))
    if bad:
        print("\n★ 下列 cases.jsonl 被手改过（生成器没跟上）：")
        for l in bad:
            print("   ", l)
        print("\n⇒ 把改动写回对应的 gen_cases_*.py，再重跑。")
        return 1
    print("✅ 重跑生成器后产物逐字未变——生成器与产物同步")
    return 0


if __name__ == "__main__":
    sys.exit(main())
