#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_runbook_trees_agree.py —— **两棵 `_pipeline` 文档树里的同名文档必须逐字节一致**

## 抓到它的那一次（2026-08-17）

RUNBOOK 有两份，标题、目的句完全相同，而**内容差了 794 行**：

    评测侧  `_ledgers/_pipeline/RUNBOOK.md`                     3434 行
    随包    `registry/codex/persona-distiller/references/pipeline/RUNBOOK.md`  4190 行
    行重合 Jaccard 0.806

**而 `_每次开工必读.md` 第 28、365 行明写「严格走 `_pipeline/RUNBOOK.md` 的 12 步」
—— 指的正是缺 794 行的那一份。**

缺掉的都是硬换来的操作规则，逐块列：

| 行数 | 内容 |
|---:|---|
| 245 | 排期前的第二道前置：一手规模探测（**代价三人**） |
| 441 | 第七十种：门测的是**代理量**，而代理量可以在属性不成立时被满足 |
|  32 | 一份材料里混着别人写的层——**已撞两次，是模式不是个案** |
|  27 | 1b. 拿这个人物**自己的**同名者去打一遍护栏——**真的喂进去**，不是读代码判断 |
|  25 | 第 5 问（Blackstone #169 换来的）：一手材料取不取得出可核逐字串 |
|  11 | **阈值按 profile 分档，不是一套通用值**（Thomson #129 的门槛被记成 0.07，真值 0.03） |
|   8 | 必读 4.1–4.4 的拆解 |
|   5 | `run_tests.py` 并行跑 14 件 |

⇒ **每个照必读做事的 agent，读到的是薄的那份。**
两份当天（2026-08-17）都被改过，分别由不同提交 —— **漂移正在进行中**。

## 为什么现有的漂移判据管不着

`registry/.../scripts/check_contract_drift.py` 的镜像模型是**同一个 skill 根内**的
`scripts/` ↔ `references/pipeline/checkers/`，它接受**一个** root，
跨不到 `skill_log_evals/` 那棵树。⇒ 这一对**从来没有执行者**。
[[a-rule-in-a-doc-has-no-enforcer]]｜[[one-requirement-two-consumers]]

## 本件只判**同名**的，单边文件只印不拦

单边是有正当理由的（实测三例）：

    评测侧独有  BASELINE-PROMPT-FROZEN-v1.md   冻结的基线 prompt，天然属评测侧
    评测侧独有  README-抓源到阶段2.md          描述 `_pipeline/` 自己那十件工具
    随包独有    抓源坑位清单.md                284 行，**被引 6 次** —— ★ 但照必读做事的人看不到它

⇒ 单边一律**只印不拦**，并把「随包独有」单独标出来提醒。
[[a-red-that-can-never-turn-green-is-not-a-signal]]

退出码：0＝同名文档全部一致；1＝有不一致；4＝有一棵树不在（未量）。
"""
import argparse
import difflib
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent          # …/_ledgers/_pipeline
EVAL_SIDE = HERE
SHIPPED = HERE.parents[2] / "registry/codex/persona-distiller/references/pipeline"
# ★ HERE.parents: [0]=_ledgers [1]=persona-distiller [2]=skill_log_evals …
#   实际要的是 CodexSkills/，即 parents[3]。**这一行我第一次写错了一级**，
#   靠下面「树不存在 ⇒ rc=4 未量」的守卫当场接住，没有变成一次假绿。
SHIPPED = HERE.parents[3] / "registry/codex/persona-distiller/references/pipeline"

#: ★★★★★ 2026-08-18 扩射程：**`_ledgers/` ↔ `references/ledgers/` 这一对此前无人管**。
#   实测那天：`_每次开工必读.md` —— **每个 agent 被要求首先读的那份** ——
#   两份**真分叉**：评测侧 815 行 / 随包 1037 行，标题层面
#   **评测侧独有 18 节、随包独有 46 节、共有 35 节**。
#   而本地流程让人读的是**评测侧**那份 ⇒ 照必读做事的人看不到那 46 节。
#   同族还有 3 对：`_决策台账.md`（真分叉，且随包那份写着**已被推翻**的「并发恒为 1」）、
#   `_额度台账.md`、`_迭代输入_下一轮.md`（后两者随包是严格超集）。
#   四对已全部合并（每次都做「严格超集：两份原文的每一非空行都还在」验证，0 行丢失）。
#   ⇒ 接进本件，**下次分叉当场红**。
#   [[the-tree-and-the-zip-can-both-be-self-consistent-and-differ]]
LEDGER_EVAL = HERE.parent
LEDGER_SHIP = HERE.parents[3] / "registry/codex/persona-distiller/references/ledgers"


# ★★★ 射程按**实测**定：递归比两棵树，同名 38 份里 22 一致、16 不同，
#   而不同的**几乎全在 `checkers/`（13 份）** —— 那是**另一套工具**，
#   12 个同名文件做的是不同的事，**本就不该相同**，不能拿来当漂移。
#   一致的分布：example-knuth 8、scaffold 6、顶层 5、judge_prompts 1 …
#   ⇒ 只管**顶层 .md** 与下面这三个**确认过是真镜像**的子目录。
MIRROR_SUBDIRS = ("judge_prompts", "example-knuth", "scaffold")
NOT_MIRROR = ("checkers",)          # 同名不同事，实测 13/15 不同


# ★ 2026-08-17 加：顶层 `*.py` 也比。随包顶层只有 **4 个** .py，
#   全部也在评测侧且 4/4 逐字节相同（评测侧另有 75 个单边件，只印不拦）。
#   起因：`next_person.py` 两份分叉 —— 各带对方没有的功能
#   （评测侧 `iter_workspaces` + Shewhart 同名检测；随包兜底校验 + 分族配重），
#   当天输出恰好一致，**数据一变就会给出不同答案**。已合并。
TOP_PATTERNS = ("*.md", "*.py")


def compare(a_dir: pathlib.Path, b_dir: pathlib.Path, pattern=TOP_PATTERNS,
            subdirs: tuple = MIRROR_SUBDIRS):
    """→ (同名不一致的, 同名一致的, 只在 a 的, 只在 b 的)。纯函数式，不写盘。

    ★ 顶层只比 `pattern`；`subdirs` 里的**所有文件**都比（那三个目录是真镜像）。
    """
    pats = (pattern,) if isinstance(pattern, str) else pattern
    a = {p.name: p for pat in pats for p in a_dir.glob(pat)}
    b = {p.name: p for pat in pats for p in b_dir.glob(pat)}
    for d in subdirs:
        for src, dst in ((a_dir / d, a), (b_dir / d, b)):
            if src.is_dir():
                for f in src.rglob("*"):
                    if f.is_file():
                        dst[d + "/" + f.relative_to(src).as_posix()] = f
    same, diff = [], []
    for n in sorted(set(a) & set(b)):
        (same if a[n].read_bytes() == b[n].read_bytes() else diff).append(n)
    return diff, same, sorted(set(a) - set(b)), sorted(set(b) - set(a))


def self_test() -> int:
    import tempfile
    bad, n = [], [0]

    def chk(lbl, ok):
        n[0] += 1
        print(("  ✓ " if ok else "  ✗ ") + lbl)
        if not ok:
            bad.append(lbl)

    with tempfile.TemporaryDirectory() as td:
        A, B = pathlib.Path(td) / "a", pathlib.Path(td) / "b"
        A.mkdir(); B.mkdir()
        (A / "same.md").write_text("x\n", encoding="utf-8")
        (B / "same.md").write_text("x\n", encoding="utf-8")
        (A / "drift.md").write_text("x\n", encoding="utf-8")
        (B / "drift.md").write_text("x\ny\n", encoding="utf-8")
        (A / "only-a.md").write_text("q\n", encoding="utf-8")
        (B / "only-b.md").write_text("q\n", encoding="utf-8")
        for d in ("judge_prompts", "checkers"):
            (A / d).mkdir(); (B / d).mkdir()
        (A / "judge_prompts" / "seat.md").write_text("v1\n", encoding="utf-8")
        (B / "judge_prompts" / "seat.md").write_text("v2\n", encoding="utf-8")   # 真镜像，要报
        (A / "checkers" / "x.py").write_text("v1\n", encoding="utf-8")
        (B / "checkers" / "x.py").write_text("v2\n", encoding="utf-8")           # 另一套工具，不报
        d, s, oa, ob = compare(A, B)
        # ★ 断言用**包含**不用全等 —— 加了镜像子目录后 diff 里不止一项；
        #   第一版写死 `== ["drift.md"]`，扩展射程后三条断言当场全红（**是断言写死了，不是代码错**）。
        chk("★★★ 正例：同名而内容不同 ⇒ 报出来", "drift.md" in d)
        chk("★★ 负例：同名且逐字节一致 ⇒ 不报", s == ["same.md"])
        chk("★★ 单边文件分别归到两侧，**不进 diff**",
            oa == ["only-a.md"] and ob == ["only-b.md"] and "only-a.md" not in d)
        chk("★ 差一个字节就算不同（不做「差不多」判断）",
            "drift.md" in compare(A, B)[0])
        (B / "drift.md").write_text("x\n", encoding="utf-8")
        chk("★★★ 改一致之后就不报了（**反例实验**：判据能从红转绿）",
            "drift.md" not in compare(A, B)[0])
        chk("★★★ **`judge_prompts/` 是真镜像 ⇒ 不同就报**（评委指令，v0.0.0.137 那次就是它漂了）",
            "judge_prompts/seat.md" in compare(A, B)[0])
        chk("★★★ **`checkers/` 不是镜像 ⇒ 同名不同事，不许报**（实测 13/15 本就不同）",
            not any(k.startswith("checkers/") for k in compare(A, B)[0]))
        chk("★ 两侧都空 ⇒ 四个列表都空（由调用方判未量，不在这里当通过）",
            compare(pathlib.Path(td), pathlib.Path(td), ("*.nope",), ()) == ([], [], [], []))
    print("\n自测 %d 项，不符 %d 项" % (n[0], len(bad)))
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", "--selftest", dest="selftest", action="store_true")
    if ap.parse_args().selftest:
        return self_test()

    print("扫描面：")
    print("  评测侧（必读指的就是这一棵）：%s" % EVAL_SIDE)
    print("  随包                        ：%s" % SHIPPED)
    for d, who in ((EVAL_SIDE, "评测侧"), (SHIPPED, "随包")):
        if not d.is_dir():
            print("\n★ **未量，不是通过**（rc=4）—— %s 那棵树不在：%s" % (who, d))
            return 4

    diff, same, only_a, only_b = compare(EVAL_SIDE, SHIPPED)
    # ★ 第二对：`_ledgers/` ↔ `references/ledgers/`（只比同名，单边只印不拦）
    if LEDGER_EVAL.is_dir() and LEDGER_SHIP.is_dir():
        d2, s2, _oa2, ob2 = compare(LEDGER_EVAL, LEDGER_SHIP, ("*.md",), ())
        print("\n第二对（台账）：`%s` ↔ `%s`" % (LEDGER_EVAL.name, LEDGER_SHIP.name))
        print("  同名 **%d** 份：一致 %d｜**不一致 %d**" % (len(d2) + len(s2), len(s2), len(d2)))
        for n_ in s2:
            print("   ✓ %s" % n_)
        if ob2:
            print("  · 只在**随包**（只印不拦）：%s" % "、".join(ob2[:6]))
            print("    ★ 提醒：必读指的是**评测侧**那棵树 —— 只在随包的，照必读做事的人看不到。")
        diff = diff + ["（台账）" + x for x in d2]
        same = same + s2
    else:
        print("\n★ 第二对（台账）**未量** —— 目录不在：%s / %s"
              % (LEDGER_EVAL, LEDGER_SHIP))
    if not (diff or same):
        print("\n★ **未量，不是通过**（rc=4）—— 两侧没有任何同名 .md，扫描面是空的")
        return 4

    print("\n同名文档 **%d** 份：一致 %d｜**不一致 %d**" % (len(diff) + len(same), len(same), len(diff)))
    for n in same:
        print("   ✓ %s" % n)
    if only_a:
        print("\n· 只在**评测侧**（只印不拦）：%s" % "、".join(only_a))
    if only_b:
        print("· 只在**随包**（只印不拦）：%s" % "、".join(only_b))
        print("  ★ 提醒：`_每次开工必读.md` 指的是**评测侧**那棵树 ——")
        print("    只在随包的文档，照必读做事的人**看不到**。")

    if not diff:
        print("\n✓ 同名文档全部逐字节一致")
        return 0
    print("\n✗ **同名而内容不同 %d 份**：" % len(diff))
    for n in diff:
        a = (EVAL_SIDE / n).read_text(encoding="utf-8", errors="replace").splitlines()
        b = (SHIPPED / n).read_text(encoding="utf-8", errors="replace").splitlines()
        sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
        ins = sum(j2 - j1 for t, i1, i2, j1, j2 in sm.get_opcodes() if t in ("insert", "replace"))
        dele = sum(i2 - i1 for t, i1, i2, j1, j2 in sm.get_opcodes() if t in ("delete", "replace"))
        print("     %-28s 评测侧 %d 行｜随包 %d 行｜随包多 %d 行、评测侧多 %d 行"
              % (n, len(a), len(b), ins, dele))
    print("\n  ★ 处置：**先逐块读，别直接覆盖** —— 两边都可能有对方没有的真内容。")
    print("    2026-08-17 那次：随包多 794 行（含「代价三人」的一手规模探测 245 行），")
    print("    而评测侧多 35 行（当天新加的 run_checks / sweep 两节）。")
    print("    合并后要验**结果是两者的严格超集**（每一非空行都还在），有意丢弃的逐条写明理由。")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
