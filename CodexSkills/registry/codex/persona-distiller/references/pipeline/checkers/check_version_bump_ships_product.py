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


def audit(root, since):
    """回溯：两条轴各自的提交数与交集。"""
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

        if fails:
            for f in fails:
                print("✗ " + f)
            return 1
        print("✓ 自测 3 例全过（只升版=拦；升版+出货=放；只动账面≠出货）")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    sys.exit(main())
