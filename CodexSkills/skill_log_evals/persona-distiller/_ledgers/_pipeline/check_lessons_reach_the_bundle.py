#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_lessons_reach_the_bundle.py —— **写在 `~/.claude/` 里的教训进不了交付包**

## 抓到它的那一次

2026-08-14 早上，移交包已经打好、8 项验收全过。我顺手数了一下三处教训库：

    本机 ~/.claude/…/memory/   169 条   ← **不在任何 git 仓里**
    文档/踩坑库/（在包里）      174 条
    Private-Database origin    141 条

三个数都很接近，看着像同一批东西。逐条 `comm` 之后才发现
**有 5 条只存在于第一处**——`git-ls-files-quotes-non-ascii-paths`、
`zero-hit-gates-must-prove-they-can-hit`、`the-field-that-says-who-must-act`、
`code-that-only-ever-ran-with-n-equals-one`、`claims-my-own-next-delivery-falsifies`。

`~/.claude/` 随本机、随套餐消失。**移交的全部价值就是这些教训**，
而其中 5 条本来一条都到不了接手方手里，且没有任何东西会喊一声。

★ 这不是「集合比实况小」，是**集合根本不在交付面里**：
  判据全绿、包能 clone、8 项验收全过——因为**没有一项在问这个**。
  [[a-checker-nothing-calls-is-not-a-checker]] 的上游形态：
  不是判据没人调，是**这件事根本没有判据**。

## 本件怎么判

比对两个目录的**文件名集合**（`name:` 就是文件名，两边同源）：

- 只在 `~/.claude/` 里的 → **会随本机消失**，逐条印出来
- 只在 `文档/踩坑库/` 里的 → 正常（索引文件、直接写进仓的），只报数

## 和 `check_lessons_library.py` 的分工（**它俩不打架，是一对**）

`check_lessons_library.py` 文件头明写着**它不去比对 `~/.claude/`**，理由完全正确：
收件人机器上没那个目录，拿它当**硬门**就是一道在别人机器上永远红的门。
所以它只判**仓内三者自洽**（README 首行 ＝ 索引条数 ＝ 文件数），**rc 会红**。

本件补的正是它有意留下的那一格：**仓外还有没有该进来而没进来的**。
代价是**永远不许硬拦** —— 见下。
⇒ 一句话：**它判「仓里自不自洽」，本件判「该进仓的进来没有」。自洽答不了完整。**

## 它有意不做的事

- **不自动复制**。带过来要顺手改索引行、要判是不是改了名的同一条
  （`filters-make-rows-vanish` 就是同一条在两边叫不同名字），机器判不了。
- **rc 恒为 0**。别的机器上 `~/.claude/` 那个目录压根不存在，
  硬拦会造出一道**永远变不绿的红**。[[a-red-that-can-never-turn-green-is-not-a-signal]]
- 目录不存在时印「**未量，不是通过**」——[[empty-default-swallows-unknown]]。

## 用法

    python3 check_lessons_reach_the_bundle.py
    python3 check_lessons_reach_the_bundle.py --self-test
"""
import argparse
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO_LESSONS = HERE.parents[4] / "文档/踩坑库"
HOME_LESSONS = (pathlib.Path.home() / ".claude/projects"
                / "-Users-linzezhang-Documents-Codex-GithubProject-AgentDatabase/memory")
# 索引/汇总类，不是教训本身。
# ★★ `README.md` 一开始漏在这里，于是本件报「仓里 179 条」而
#    `check_lessons_library.py` 报「178 个」——**同一个目录、两件判据、两个口径**，
#    而且这个 179 已经被我写进过提交说明。[[two-checkers-same-text-different-rules]]
#    差额只在分母上（README 只在仓侧，落进「只在仓里的」那一格，
#    「只在本机的 0 条」这个结论不受影响）——**但错的数照样是错的**。
#    这里的三个名字必须与 check_lessons_library.py 的 META 一致。
NOT_A_LESSON = {"MEMORY.md", "00-索引.md", "README.md"}


def names(d: pathlib.Path) -> set:
    """目录里的教训文件名集合。**目录不存在时返回 None，不是空集**。"""
    if not d.is_dir():
        return None
    return {p.name for p in d.glob("*.md") if p.name not in NOT_A_LESSON}


def compare(home, repo):
    """→ (只在本机的, 只在仓里的)。**纯函数**，两边都必须是集合。"""
    return sorted(home - repo), sorted(repo - home)


def self_test() -> int:
    import tempfile
    ok = t = 0

    def chk(d, c):
        nonlocal ok, t
        t += 1
        ok += 1 if c else 0
        print(f"  {'✓' if c else '✗'} {d}")

    only_h, only_r = compare({"a.md", "b.md"}, {"b.md", "c.md"})
    chk(f"★ 只在本机的挑得出来（实得 {only_h}）", only_h == ["a.md"])
    chk(f"★ 只在仓里的也挑得出来（实得 {only_r}）", only_r == ["c.md"])
    chk("★ 两边一样 → 两边都空", compare({"a.md"}, {"a.md"}) == ([], []))
    with tempfile.TemporaryDirectory() as td:
        D = pathlib.Path(td)
        (D / "x.md").write_text("x", encoding="utf-8")
        (D / "MEMORY.md").write_text("i", encoding="utf-8")
        (D / "00-索引.md").write_text("i", encoding="utf-8")
        (D / "README.md").write_text("i", encoding="utf-8")
        chk(f"★★ 索引类不算教训（实得 {names(D)}）", names(D) == {"x.md"})
        # ★★ 口径必须与 check_lessons_library.py 的 META 逐字一致，否则两件判据
        #    对同一个目录会报出两个数（真发生过：179 vs 178）
        try:
            sys.path.insert(0, str(HERE))
            from check_lessons_library import META as _M
            chk(f"★★ **与 check_lessons_library 的口径逐字一致**（对方 {sorted(_M)}）",
                NOT_A_LESSON == _M | {"MEMORY.md"})
        except Exception as e:                                    # noqa: BLE001
            chk(f"★★ 口径对齐**未判**（导入不了对方：{e}）—— 未量，不是通过", False)
        chk("★★ **目录不存在返回 None，不是空集** —— 空集会被读成「两边一致」",
            names(D / "没有这个目录") is None)
    print(f"\n{'✓ 全过' if ok == t else f'✗ {t - ok}/{t} 项不符'}")
    return 0 if ok == t else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    if ap.parse_args().self_test:
        return self_test()

    home, repo = names(HOME_LESSONS), names(REPO_LESSONS)
    if repo is None:
        print(f"★ **未量，不是通过** —— 找不到仓里的踩坑库：{REPO_LESSONS}")
        return 0
    if home is None:
        print(f"★ **未量，不是通过** —— 本机没有 {HOME_LESSONS}")
        print("   （在别的机器上这是正常的：那个目录本来就只在原作者机器上）")
        return 0

    only_h, only_r = compare(home, repo)
    print(f"★★ **教训库覆盖面**：本机 `~/.claude/` **{len(home)}** 条｜"
          f"仓里（＝包里）**{len(repo)}** 条｜两边都有 {len(home & repo)} 条")
    print(f"   ⇒ **只在本机、进不了包的 {len(only_h)} 条**；只在仓里的 {len(only_r)} 条（正常）")
    if only_h:
        print("\n❗ 下面这些**随本机/套餐消失**，接手方一条也看不到 —— 逐条决定要不要带进仓：")
        for n in only_h:
            print(f"     {n}")
        print("   ★ 带过来要顺手加 `文档/踩坑库/00-索引.md` 一行；"
              "先看是不是**改了名的同一条**（有过这种：filters-make-rows-vanish）")
    else:
        print("\n✅ 本机没有任何一条是包外独有的")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
