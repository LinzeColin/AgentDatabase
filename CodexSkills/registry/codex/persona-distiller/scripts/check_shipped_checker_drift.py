#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**交付包里有两棵判据树，而它们不一样。**

## 事实（现算，不是回忆）

`PACKAGE_MANIFEST.json` 同时收录两处：

    scripts/                        106 条
    references/pipeline/checkers/    85 条

两处**同名的有 81 件**，其中 **16 件内容不同**。而这不是「有意的两个版本」——
git 历史显示后者单纯陈旧：

    quality_check.py                 scripts 77 次提交（08-10）／包内副本 32 次（08-05）
    assemble_judge_results.py        scripts 10 次（08-10）／包内副本 8 次（08-06）
    check_version_bump_ships_product scripts  2 次（08-06）／包内副本 1 次（08-05）

## 后果不是「重复」，是**装出去的那份带着已经修好的缺陷**

实测两例：

- 包内 `assemble_judge_results.read_seat` 遇到冻结评委指令要求的
  `A_score`/`B_score` 形状 **抛 KeyError**，而 `scripts/` 那份读得出。
  → 拿包内那份汇总，**整席会丢**。
- 包内 `check_version_bump_ships_product.py --self-test` **退出码 2（自测不过）**，
  而 `scripts/` 那份是 0。**一件自己都测不过的判据被装进了交付包。**

## 为什么要一件判据而不是「记得同步」

「记得同步」已经失效了：两处从 08-05 起就在分叉，没有任何一处报过声。
[[stale-artifacts-from-my-machine-leak-into-the-build]]、
[[a-checker-nothing-calls-is-not-a-checker]]。

## 口径：**只报不拦，但绝不静默**

本件**不替人决定哪一棵是权威**（那要改交付契约，属用户裁定）。
它只保证一件事：**分叉了就有人说话，而且说的是件数与件名，不是「大概同步一下」。**

    python3 check_shipped_checker_drift.py <skill 根目录>
    python3 check_shipped_checker_drift.py <skill 根目录> --json
    python3 check_shipped_checker_drift.py --self-test
"""
import argparse
import hashlib
import json
import pathlib
import sys

LIVE = "scripts"
SHIPPED = "references/pipeline/checkers"


def digest(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def compare(root: pathlib.Path, live=LIVE, shipped=SHIPPED) -> dict:
    a, b = root / live, root / shipped
    if not a.is_dir() or not b.is_dir():
        # ★ 两棵树只要缺一棵，就不是「没有漂移」，是**没得比**。
        return {"★ 未核（不是通过）": f"{a} 或 {b} 不在——两棵树没得比"}
    an = {f.name for f in a.glob("*.py")}
    bn = {f.name for f in b.glob("*.py")}
    both = sorted(an & bn)
    drift = [n for n in both if digest(a / n) != digest(b / n)]
    return {
        "两处同名的": len(both),
        "**内容不同的**": len(drift),
        "不同的件名": drift,
        f"只在 {live}/": sorted(an - bn),
        f"只在 {shipped}/": sorted(bn - an),
        "★★ 口径": f"**本件不判哪一棵是权威**（那要改交付契约）。"
                    f"「内容不同的 = 0」才叫没有漂移；非 0 就是**装出去的那份与在跑的那份不一样**。",
    }


def selftest() -> int:
    import tempfile                                              # noqa: PLC0415
    fails = []

    def chk(label, cond):
        print(("  ✓ " if cond else "  ✗ ") + label)
        if not cond:
            fails.append(label)

    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        (root / LIVE).mkdir(parents=True)
        (root / SHIPPED).mkdir(parents=True)
        for d in (LIVE, SHIPPED):
            (root / d / "same.py").write_text("print(1)\n", encoding="utf-8")
        print("── 正例：两处逐字节相同 → 漂移 0 ──")
        r = compare(root)
        chk(f"同名 {r['两处同名的']} 件、不同 {r['**内容不同的**']} 件", r["**内容不同的**"] == 0)

        print("── ★★ 反例①：改一个字节就必须红 ──")
        (root / SHIPPED / "same.py").write_text("print(2)\n", encoding="utf-8")
        r2 = compare(root)
        chk(f"不同 {r2['**内容不同的**']} 件，件名 {r2['不同的件名']}",
            r2["**内容不同的**"] == 1 and r2["不同的件名"] == ["same.py"])

        print("── ★★ 反例②：只在一侧的文件要单列，不许混进「相同」 ──")
        (root / LIVE / "only_live.py").write_text("x=1\n", encoding="utf-8")
        (root / SHIPPED / "only_shipped.py").write_text("x=1\n", encoding="utf-8")
        r3 = compare(root)
        chk(f"只在 {LIVE}/ 的 {r3[f'只在 {LIVE}/']}；只在 {SHIPPED}/ 的 {r3[f'只在 {SHIPPED}/']}",
            r3[f"只在 {LIVE}/"] == ["only_live.py"]
            and r3[f"只在 {SHIPPED}/"] == ["only_shipped.py"]
            and r3["两处同名的"] == 1)

        print("── ★★★ 反例③：**缺一棵树不许报成「没有漂移」** ──")
        r4 = compare(root / "nowhere")
        chk("缺树 → 印「未核（不是通过）」，且不出 `**内容不同的**` 这个字段",
            "★ 未核（不是通过）" in r4 and "**内容不同的**" not in r4)

    print(f"\n{'✓ 自测全过' if not fails else f'✗ **{len(fails)} 项未过**'}")
    return 0 if not fails else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", nargs="?", help="skill 根目录（含 scripts/ 与 references/）")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return selftest()
    if not a.root:
        ap.error("给 skill 根目录，或 --self-test")

    r = compare(pathlib.Path(a.root))
    if a.json:
        print(json.dumps(r, ensure_ascii=False))
        return 1 if r.get("**内容不同的**") else 0
    if "★ 未核（不是通过）" in r:
        print("⚠ " + r["★ 未核（不是通过）"])
        return 0
    n = r["**内容不同的**"]
    print(f"两处同名 {r['两处同名的']} 件；**内容不同 {n} 件**")
    if n:
        print("\n✗ **装出去的那份与在跑的那份不一样**：")
        for x in r["不同的件名"]:
            print(f"  · {x}")
    else:
        print("✓ 两棵树逐件相同")
    for k in (f"只在 {LIVE}/", f"只在 {SHIPPED}/"):
        if r[k]:
            print(f"★ {k}：{len(r[k])} 件（**这不算漂移，但也不是「都有」**）")
    print("\n" + r["★★ 口径"])
    return 1 if n else 0


if __name__ == "__main__":
    sys.exit(main())
