#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""升版必须出货——判据落地不动版本号。

## 这条规矩不是我定的

2026-08-04 用户裁定：

| | 旧 | 新 |
|---|---|---|
| 升版条件 | 落一件判据就升 | **只有产物侧变化才升**（入库／发行／已入库产物被修） |
| 判据落地 | 算一次发行 | **算工具改动，不动版本号** |

理由是「兼容下限 = 当前版本末位 − 10」：**每升一版，全部存量产物就往
「不适配」里推一格**。产物一个字没改，却因为尺子在跑而全部变「老」。

## 规矩生效之后我照做了吗——没有，而且是完整反过来的

自 2026-08-04 起（v0.0.0.81 … v0.0.0.154，用 git 实测，不是凭印象）：

| | |
|---|---|
| 往 CHANGELOG 加了 `## v0.0.0.N` 标题的提交 | **41** |
| 其中碰了产物侧的 | **0** |
| 真正碰了产物侧（`<族>/<人>/…`）的提交 | **5**（全是 Carver #127） |
| 其中升了版的 | **0** |

**两条轴完全不相交。** 升版的从不出货，出货的从不升版。

后果可以指到具体一个人：Carver #127 是**昨天**才入库的最新产物，
`distilled_with = v0.0.0.132`；今天版本走到 154，兼容下限 144——
**他一个字节没改，一天之内就掉到下限之外**。
`check_distillation_freshness` 现在报 **达标 0 / 107**。

★ 所以这不是历史包袱。**在当前节奏下，新产物出生一天就过期。**

## 它判什么

**只有一个方向算违规**：

- **升了版却没出货** → 违规。判据／工具改动不该动版本号。
- **出了货却没升技能版** → **只提示，不判违规**。

★ 第二个方向是我第一版写错的地方，写完当场自查出来的。
用户的原话是「**只有**产物侧变化才升」——那是**给升版加的必要条件**，
不是「产物一动就必须升」。而且产物另有**自己的版本轴**
（每人 0.0.0.1 … 0.0.0.999）：被我报成「出了货却没升版」的 5 次里，
有 3 次提交标题白纸黑字写着「产物 v0.0.0.2」「v0.0.0.4」——
**产物版本升了，只是技能版本没动，那完全合规。**
按违规去判就是造一个永远变不绿的红（[[a-red-that-can-never-turn-green-is-not-a-signal]]）。

「产物侧」的判法**只认 `persona-distiller-group/<族>/<人>/…`**（路径 ≥7 段）。
★ 实测校准过：该 registry 根下的 `README.md` / `team-index.json` /
`CANONICAL-ROOT-ROUTE.md` 是**登记簿的账面**，不是产物本身——
按「碰了这个 registry 就算出货」去数会得到 6，逐个打开看只有 5 个是真的。
（同一个坑记在 [[read-the-hits-before-reporting-the-rate]]。）

## 用法

    # 判当前工作树 + 暂存区（提交前用）
    python3 check_version_bump_ships_product.py

    # 判某一次提交
    python3 check_version_bump_ships_product.py --commit HEAD

    # 回溯审计：规矩生效以来两条轴各走了多少
    python3 check_version_bump_ships_product.py --audit --since 2026-08-04

退出码：0 = 无违规；1 = 有违规；2 = 用不了 git／找不到仓。
"""

import argparse
import os
import re
import subprocess
import sys

CHANGELOG_REL = "CodexSkills/registry/codex/persona-distiller/CHANGELOG.md"
GROUP_REL = "CodexSkills/registry/codex/persona-distiller-group"

# 产物侧最小段数：CodexSkills/registry/codex/persona-distiller-group/<族>/<人>/<文件>
# = 4 + 1 + 1 + 1 = 7 段。少于这个的是登记簿账面，不是产物。
PRODUCT_MIN_SEGMENTS = 7

VERSION_HEADING = re.compile(r"^\+## v0\.0\.0\.(\d+)")


def git(args, cwd, check=True):
    """跑 git，返回 stdout。★ -c 必须写在子命令之前。"""
    proc = subprocess.run(
        ["git", "-c", "core.quotepath=false"] + args,
        cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if check and proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode("utf-8", "replace").strip())
    return proc.stdout.decode("utf-8", "replace")


def repo_root(start):
    try:
        return git(["rev-parse", "--show-toplevel"], start).strip()
    except Exception:
        return None


def is_product_path(path):
    """只认 <族>/<人>/… 那一层。登记簿根下的账面文件不算出货。"""
    p = path.strip().strip('"')
    if not p.startswith(GROUP_REL + "/"):
        return False
    return len(p.split("/")) >= PRODUCT_MIN_SEGMENTS


def added_versions(diff_text):
    """从 diff 里取出新增的版本标题号。"""
    out = []
    for line in diff_text.splitlines():
        m = VERSION_HEADING.match(line)
        if m:
            out.append("v0.0.0." + m.group(1))
    return out


def inspect(root, commit=None):
    """返回 (新增版本号列表, 碰到的产物侧路径列表, 全部改动路径数)。"""
    if commit:
        names = git(["show", "--name-only", "--format=", commit], root)
        diff = git(["show", "--format=", "-U0", commit, "--", CHANGELOG_REL], root)
    else:
        # 工作树 + 暂存区，相对 HEAD
        names = git(["diff", "HEAD", "--name-only"], root)
        diff = git(["diff", "HEAD", "-U0", "--", CHANGELOG_REL], root)
    paths = [p for p in names.splitlines() if p.strip()]
    return added_versions(diff), [p for p in paths if is_product_path(p)], len(paths)


_MAXAGE = re.compile(r"--max-age=(\d+)")
_GARBAGE = "zzz-not-a-date-zzz"


def since_parsed(root, since):
    """git 认不认这个日期。**问 git，不用正则猜。**

    `git rev-parse --since=X` 从不报错：认不出时它**悄悄退到「此刻」**。
    所以把 `X` 与一个已知垃圾串各解析一遍——**两个结果相同就说明 X 没被认出来**。

    ★ 第一版我用 `^\\d{4}-\\d{2}-\\d{2}$` 猜，当场误伤了 `30 years ago`
      （git 认得，本件自测自己就在用）。**判据不许用正则去猜别的工具的行为。**
    """
    def _age(s):
        m = _MAXAGE.search(git(["rev-parse", f"--since={s}"], root, check=False))
        return int(m.group(1)) if m else None
    a, g = _age(since), _age(_GARBAGE)
    if a is None or g is None:
        return True                       # 问不出来就别拦（宁可漏，不可误杀）
    return abs(a - g) > 2                 # 与「此刻」不同 ⇒ 真被解析了


def audit(root, since):
    """回溯：两条轴各自的提交数与交集。

    ★★ 2026-08-12：**`git log --since` 解析不了的日期不会报错，会悄悄退到「此刻」。**
    本机 git 2.39.5 实测（`git rev-parse --since=X` 给出的 `--max-age`）：

    | `--since` | 解析成 |
    |---|---|
    | `2026-08-04` / `2099-01-01` / `30 years ago` | 各自对应的时刻（正常） |
    | `3000-01-01`（年份超出表示范围） | **此刻** |
    | `not-a-date` / `tomorrow` | **此刻** |

    退到「此刻」之后数出来的是几，取决于提交时间与运行时间差几秒——
    可能是全部，也可能是零。**无论哪种，报告印的那句「自 X 起」都是假的，
    而没有任何提示。** 这一点我第一次也说错了：写成「直接扫全部历史」，
    而实测 `not-a-date` 在临时仓上得到的是 3/0，不是 3/1。
    ⇒ 所以先问一句 git 认不认（见 `since_parsed`），不认就喊一声再继续。
    """
    if not since_parsed(root, since):
        print(f"⚠ `--since {since}` **git 解析不了**——它不报错，而是悄悄退到「此刻」。"
              f"下面的计数不是「自该日起」的（可能全部、也可能是零，看差几秒）", file=sys.stderr)
    bumps, ships = [], []
    heads = git(["log", "--since", since, "--format=%H", "--", CHANGELOG_REL], root)
    for c in heads.split():
        d = git(["show", "--format=", "-U0", c, "--", CHANGELOG_REL], root)
        if added_versions(d):
            bumps.append(c)
    gl = git(["log", "--since", since, "--format=%H", "--", GROUP_REL], root)
    for c in gl.split():
        names = git(["show", "--name-only", "--format=", c, "--", GROUP_REL], root)
        if any(is_product_path(p) for p in names.splitlines() if p.strip()):
            ships.append(c)
    return bumps, ships


def subject(root, c):
    return git(["log", "-1", "--format=%s", c], root).strip()


def main():
    ap = argparse.ArgumentParser(
        description="升版必须出货：判据落地不动版本号（2026-08-04 用户裁定）")
    ap.add_argument("--root", default=".", help="仓内任意路径")
    ap.add_argument("--commit", help="判某一次提交，默认判工作树+暂存区")
    ap.add_argument("--audit", action="store_true", help="回溯审计两条轴")
    ap.add_argument("--since", default="2026-08-04", help="审计起点（规矩生效日）")
    # ★★★ **负对照写了却跑不到——是元判据抓出来的。**
    #   `selftest()` 早就写好（造临时仓跑三种情形），但 `main()` 里没有这个参数，
    #   于是 `check_checkers` 一直报 NO-SELFTEST：
    #   **「没有负对照的检查器，其『全绿』不构成任何证据」——它自己就是那个样子。**
    #   这与元判据文件头记的第 6 种（「是硬门、负对照写了却跑不起来」）同形。
    ap.add_argument("--self-test", action="store_true", help="只跑内置负对照，不读本仓")
    args = ap.parse_args()

    if args.self_test:
        return selftest()

    root = repo_root(os.path.abspath(args.root))
    if not root:
        print("✗ 不在 git 仓里，判不了", file=sys.stderr)
        return 2

    if args.audit:
        bumps, ships = audit(root, args.since)
        both = set(bumps) & set(ships)
        print(f"自 {args.since} 起（规矩生效日）")
        print(f"  升了版的提交      {len(bumps):>4}")
        print(f"  真出货的提交      {len(ships):>4}")
        print(f"  **两者交集**      {len(both):>4}")
        bad_bump = [c for c in bumps if c not in both]
        bad_ship = [c for c in ships if c not in both]
        if bad_bump:
            print(f"\n升了版却没出货 {len(bad_bump)} 次（判据／工具改动不该动版本号）：")
            for c in bad_bump[:8]:
                print(f"  · {c[:8]} {subject(root, c)[:56]}")
            if len(bad_bump) > 8:
                print(f"  …… 另有 {len(bad_bump) - 8} 次")
        if bad_ship:
            print(f"\n（提示，不算违规）出了货而技能版本没动 {len(bad_ship)} 次——")
            print("  产物另有自己的版本轴（每人 0.0.0.1…），下面几次多半是升在那条轴上：")
            for c in bad_ship[:8]:
                print(f"  · {c[:8]} {subject(root, c)[:56]}")
        if not bad_bump:
            print("\n✓ 没有「升了版却没出货」")
        return 1 if bad_bump else 0

    vers, prods, total = inspect(root, args.commit)
    where = args.commit or "工作树+暂存区"
    bad = False

    if vers and not prods:
        bad = True
        print(f"✗ **升了版却没出货**（{where}）")
        print(f"  新增版本标题：{'、'.join(vers)}")
        print(f"  改动 {total} 个文件，产物侧 **0** 个")
        print("  → 2026-08-04 裁定：判据落地算工具改动，**不动版本号**。")
        print("     每升一版，全部存量产物就往「不适配」推一格"
              "（兼容下限 = 当前版本末位 − 10）。")
    if prods and not vers:
        print(f"（提示，不算违规）出了货而技能版本没动（{where}）：")
        for p in prods[:6]:
            print(f"  · {p}")
        if len(prods) > 6:
            print(f"  …… 另有 {len(prods) - 6} 个")
        print("  → 产物有自己的版本轴（每人 0.0.0.1…）。技能版本不动是合规的；"
              "\n     裁定只说「**只有**产物侧变化才准升技能版」，没说产物一动就必须升。")
    if not bad:
        if vers and prods:
            print(f"✓ 升版 {'、'.join(vers)} 同时出货 {len(prods)} 个产物文件")
        else:
            print(f"✓ 既没升版也没出货，无需对齐（{where}，改动 {total} 个文件）")
    return 1 if bad else 0


def selftest():
    """造一个临时仓，把三种情形各跑一遍。

    ★ 真实历史里**从来没有过**「既升版又出货」的提交（交集 0），
    所以「过」的那一支只能靠人造样本证明——不造就等于没测过绿的那一半。
    """
    import tempfile, shutil
    tmp = tempfile.mkdtemp(prefix="bumpguard-")
    try:
        def w(rel, text):
            fp = os.path.join(tmp, rel)
            os.makedirs(os.path.dirname(fp), exist_ok=True)
            with open(fp, "w", encoding="utf-8") as f:
                f.write(text)

        git(["init", "-q", tmp], tmp)
        git(["config", "user.email", "t@t"], tmp)
        git(["config", "user.name", "t"], tmp)
        w(CHANGELOG_REL, "# Changelog\n")
        git(["add", "-A"], tmp); git(["commit", "-qm", "base"], tmp)

        prod = GROUP_REL + "/农林牧渔师/somebody/registration.json"
        ledger = GROUP_REL + "/team-index.json"
        fails = []

        # ① 只升版，不出货 → 必须判违规
        w(CHANGELOG_REL, "# Changelog\n\n## v0.0.0.99\n")
        w("CodexSkills/registry/codex/persona-distiller/scripts/x.py", "# tool\n")
        git(["add", "-A"], tmp); git(["commit", "-qm", "bump only"], tmp)
        v, pr, _ = inspect(tmp, "HEAD")
        if not (v and not pr):
            fails.append("① 只升版没出货：应判违规，实得 v=%s prod=%s" % (v, pr))

        # ② 升版 + 出货 → 必须放行
        w(CHANGELOG_REL, "# Changelog\n\n## v0.0.0.100\n\n## v0.0.0.99\n")
        w(prod, "{}\n")
        git(["add", "-A"], tmp); git(["commit", "-qm", "bump and ship"], tmp)
        v, pr, _ = inspect(tmp, "HEAD")
        if not (v and pr):
            fails.append("② 升版且出货：应放行，实得 v=%s prod=%s" % (v, pr))

        # ③ 只碰登记簿账面 → **不算出货**（这一条是拿真实历史校准出来的）
        w(CHANGELOG_REL, "# Changelog\n\n## v0.0.0.101\n\n## v0.0.0.100\n")
        w(ledger, "{}\n")
        git(["add", "-A"], tmp); git(["commit", "-qm", "bump + ledger only"], tmp)
        v, pr, _ = inspect(tmp, "HEAD")
        if pr:
            fails.append("③ 只动 team-index.json：不该算出货，实得 prod=%s" % (pr,))
        if not v:
            fails.append("③ 应当仍认出升了版")

        # ══════════════════════════════════════════════════════════════
        # ㉜ `audit()` / `repo_root()` / `subject()`
        #    —— 2026-08-12 之前这三个从没被自测进入过
        # ══════════════════════════════════════════════════════════════
        #
        # 上面三例打的是 `inspect()`（**单个提交升没升版、碰没碰产物**）。
        # 而 `audit()` 是**回溯那一路**——它给出「41 次升版 / 0 次出货」这个数，
        # 也就是本件 docstring 里那张表的全部依据。它此前一次没被自测跑过。
        # 上面这个临时仓恰好造出了三种提交，正好用来验它。

        # ㉜a `repo_root()`：仓内任意子目录都要能回到仓根
        sub = os.path.join(tmp, os.path.dirname(CHANGELOG_REL))
        got = repo_root(sub)
        if not got or os.path.realpath(got) != os.path.realpath(tmp):
            fails.append("㉜a repo_root 从子目录回不到仓根：%s（应 %s）" % (got, tmp))

        # ㉜a′ 不在仓里 → 返回 None（**不许崩，也不许返回一个看着像的路径**）
        outside = tempfile.mkdtemp(prefix="notarepo-")
        try:
            if repo_root(outside) is not None and os.path.realpath(
                    repo_root(outside)) == os.path.realpath(outside):
                fails.append("㉜a′ 非仓目录应返回 None 或仓外根，实得 %s" % repo_root(outside))
        finally:
            shutil.rmtree(outside, ignore_errors=True)

        # ㉜b `audit()`：三个提交里 **3 次升版、1 次出货**，交集只有那一次
        bumps, ships = audit(tmp, "30 years ago")
        if len(bumps) != 3:
            fails.append("㉜b audit 的升版轴应数到 3 次，实得 %d" % len(bumps))
        if len(ships) != 1:
            fails.append("㉜b audit 的出货轴应数到 1 次（只有 ② 碰了产物），实得 %d" % len(ships))
        if len(set(bumps) & set(ships)) != 1:
            fails.append("㉜b 两轴交集应为 1（② 既升版又出货），实得 %d"
                         % len(set(bumps) & set(ships)))

        # ㉜c ★★ **只动 team-index.json 的那次不许进出货轴**——
        #    这是本件最容易被写宽的一格：账面文件也在 GROUP_REL 下面。
        third = git(["log", "--format=%H", "-1", "--grep", "ledger only"], tmp).strip()
        if third and third in ships:
            fails.append("㉜c 只动登记簿账面的提交**混进了出货轴**")

        # ㉜d `subject()`：拿得到提交标题（报告里靠它让人认出是哪一次）
        if third and "ledger only" not in subject(tmp, third):
            fails.append("㉜d subject 取不到提交标题：%r" % subject(tmp, third))

        # ㉜e 反向：`--since` 收得够紧时两轴都应为空——
        #    没有它，㉜b 可能只是「什么都数得到」。
        # ★ 第一版我写的是 `3000-01-01`，**两轴照样是 3/1**——
        #   git 表示不了那个年份，于是**静默忽略这个参数、扫了全部历史**。
        #   我差点把它读成「判据没生效」。用 `2099-01-01` 才真过滤。
        b2, s2 = audit(tmp, "2099-01-01")
        if b2 or s2:
            fails.append("㉜e --since 收紧到 2099 后两轴应为空，实得 %d/%d" % (len(b2), len(s2)))

        # ㉜f ★★ 上面那件事本身要落成断言：**解析不了的 --since 会静默扫全部历史**，
        #    所以本件必须先喊一声。这里验它确实喊了（并且不改变行为）。
        import contextlib as _ctx, io as _io
        _err = _io.StringIO()
        with _ctx.redirect_stderr(_err):
            b3, s3 = audit(tmp, "not-a-date")
        if "git 解析不了" not in _err.getvalue():
            fails.append("㉜f git 解析不了的 --since 必须先告警，实得 %r" % _err.getvalue())
        # ★ 反向之二：`30 years ago` git 是认的，**不许误伤**
        #   （第一版守卫用正则猜 YYYY-MM-DD，当场把它误报了）
        _err3 = _io.StringIO()
        with _ctx.redirect_stderr(_err3):
            audit(tmp, "30 years ago")
        if _err3.getvalue().strip():
            fails.append("㉜f″ `30 years ago` git 认得，不该告警，实得 %r" % _err3.getvalue())
        # ★ 只断言「喊了」与「没崩」。**不断言条数**——退到「此刻」之后
        #   数出来是几取决于提交时间与运行时间差几秒（实测 3/0，我一度以为该是 3/1）。
        #   把不稳定的量写进断言，就是造一个会随机变红的判据。
        if b3 is None or s3 is None:
            fails.append("㉜f 告警之后仍应正常返回两轴")
        # 反向：合法日期不许喊
        _err2 = _io.StringIO()
        with _ctx.redirect_stderr(_err2):
            audit(tmp, "2026-08-04")
        if _err2.getvalue().strip():
            fails.append("㉜f′ 合法日期不该告警，实得 %r" % _err2.getvalue())

        if fails:
            for f in fails:
                print("✗ " + f)
            return 1
        print("✓ 自测 3 例全过（只升版=拦；升版+出货=放；只动账面≠出货）")
        print("✓ ㉜ audit/repo_root/subject 八条全过（回溯两轴 3/1、交集 1、"
              "账面不算出货、--since 收紧到 2099 后两轴为空、"
              "**git 解析不了的日期先告警**、`30 years ago` 不误伤）")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    sys.exit(main())
