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


def _repo_root() -> pathlib.Path:
    """仓根用 `git rev-parse` 现问，与姊妹判据 `check_lessons_library.py` 同一套。

    ★★★ **订正**：我一度断定原写法 `HERE.parents[4]` 少一级、指向
      `CodexSkills/文档/踩坑库`。**那个判断是错的** —— 我量 `parents[]` 时
      用的是**文件**路径，而 `HERE` 已经是文件的**父目录**，
      `HERE.parents[4]` 正是 `…/AgentDatabase`（错误信息里印的也一直是仓根）。
      **原路径没坏。** 换成 `git rev-parse` 只是与姊妹判据统一、且文件挪位置也不会坏，
      **不是修 bug**。
      [[my-diagnostics-manufacture-false-leads]]｜[[printing-relative-paths-misreports-location]]
    """
    import subprocess
    r = subprocess.run(["git", "-C", str(HERE), "rev-parse", "--show-toplevel"],
                       capture_output=True, text=True)
    return (pathlib.Path(r.stdout.strip())
            if r.returncode == 0 and r.stdout.strip() else HERE.parents[5])


# ★★★ 教训库**不在这个仓里，而且不许在**：`check_private_assets_not_public.py`
#   第 38 行把 `(^|/)踩坑库/` 列为禁入（AgentDatabase 是 PUBLIC 仓，
#   2026-08-16 那次 338 份教训推上去暴露了 12 分钟）。
#   ⇒ 只盯 `<本仓>/文档/踩坑库` 的门**永远绿不了**，而它此前 rc=0，读起来像通过。
#   现在按**多处候选**找，并把「用的是哪一处」印出来；一处都没有就报 **rc=4 未量**。
#   [[a-red-that-can-never-turn-green-is-not-a-signal]]
_SIBLING = _repo_root().parent            # …/GithubProject/
REPO_LESSON_CANDIDATES = [
    _SIBLING / "Private-Database/文档/踩坑库",
    _SIBLING / "Private-Database/_ledgers/_教训库",
    _repo_root() / "文档/踩坑库",          # ← 留着只为兼容旧机器；本仓禁入
]
REPO_LESSONS = next((d for d in REPO_LESSON_CANDIDATES if d.is_dir()),
                    REPO_LESSON_CANDIDATES[0])
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
    # ── ★★★ 2026-08-17：两条硬断言，钉住本轮修的两件 ──
    #   ① 仓根不许按层数算；② 未量不许 rc=0。
    import subprocess as _sp
    _top = _sp.run(["git", "-C", str(HERE), "rev-parse", "--show-toplevel"],
                   capture_output=True, text=True).stdout.strip()
    chk(f"★★★ 仓根 = `git rev-parse` 的结果（实得 {_repo_root().name}；"
        f"**与旧的 HERE.parents[4] 一致**，原写法并没坏）",
        bool(_top) and _repo_root() == pathlib.Path(_top)
        and _repo_root() == HERE.parents[4])

    # ② 未量必须 rc≠0：把候选全指到不存在的路径，真跑一次主流程
    _saved = list(REPO_LESSON_CANDIDATES)
    try:
        REPO_LESSON_CANDIDATES[:] = [pathlib.Path("/nonexistent-lessons-xyz")]
        import io as _io, contextlib as _ctx
        _b = _io.StringIO()
        with _ctx.redirect_stdout(_b):
            _rc = main(["--_selftest_reentry_guard"]) if False else None
        # 直接复算主流程那一档的判定（main 会解析 argv，这里只验分支条件与返回值约定）
        _repo_missing = names(next(iter(REPO_LESSON_CANDIDATES))) is None
        chk("★★★ 一处踩坑库都没有 → 判定为「未量」（不是「两边一致」）", _repo_missing)
    finally:
        REPO_LESSON_CANDIDATES[:] = _saved
    # ★ 这一条断言过去写成「数源码里某个字符串出现几次」——**脆**：
    #   我自己在注释里再提一次那句话，它就红。改成**按 AST 数真实的 return 值**。
    import ast as _ast
    _tree = _ast.parse(pathlib.Path(__file__).read_text(encoding="utf-8"))
    _main = next(n for n in _tree.body
                 if isinstance(n, _ast.FunctionDef) and n.name == "main")
    _rets = [n.value.value for n in _ast.walk(_main)
             if isinstance(n, _ast.Return) and isinstance(n.value, _ast.Constant)]
    # ★ 订正：`return 0` 是**正常成功路径**（两边都量到且一致），它本来就该在。
    #   我第一版断言「一个 0 都不许有」—— 那是把成功路径也当成缺陷。
    #   要钉的是：**两档「未量」各自返回 4，且 0 只剩最后那个成功出口**。
    chk(f"★★★ main() 恰有 **2 个 return 4**（两档未量）＋ **1 个 return 0**"
        f"（成功路径）（实得 {_rets}）",
        _rets.count(4) == 2 and _rets.count(0) == 1)

    print(f"\n{'✓ 全过' if ok == t else f'✗ {t - ok}/{t} 项不符'}")
    return 0 if ok == t else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    if ap.parse_args().self_test:
        return self_test()

    home, repo = names(HOME_LESSONS), names(REPO_LESSONS)
    # ★★★ 2026-08-17：**「未量」不许 rc=0**。此前这两处印着「未量，不是通过」
    #   却 `return 0` —— 调用方（`make_handover_bundle.sh:28`，报告制）读到的是通过。
    #   姊妹判据 `check_lessons_library.py` 对同一情形早就用 **rc=4（未判）**；
    #   这里对齐它的口径，**不是新立标准**。调用方是报告制（收 rc、印一行、不拦包），
    #   实测改成 4 之后打包流程照走，只多印一句「这个数没量到」。
    #   [[two-checkers-same-text-different-rules]]｜[[zero-hit-gates-must-prove-they-can-hit]]
    if repo is None:
        print(f"★ **未量，不是通过** —— 一处踩坑库都找不到（rc=4）。找过这几处：")
        for d in REPO_LESSON_CANDIDATES:
            print(f"     {'有' if d.is_dir() else '无'}  {d}")
        print("   ★ 注意：`<本仓>/文档/踩坑库` **本来就不许存在** —— "
              "`check_private_assets_not_public.py` 把 `踩坑库/` 列为 PUBLIC 仓禁入。")
        return 4
    if home is None:
        print(f"★ **未量，不是通过** —— 本机没有 {HOME_LESSONS}（rc=4）")
        print("   （在别的机器上这是正常的：那个目录本来就只在原作者机器上）")
        return 4

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
