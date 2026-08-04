#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""升版之后的收尾**按固定顺序**跑一遍——因为顺序错了会得到假红。

## 为什么有这件

2026-08-04 一天之内**三次**把 `pytest` 跑在 `build_manifest.py` 之前，
每次都得到同一批假红：

```
FAILED test_release_bundle …… checksum mismatch: VERIFICATION.md
FAILED test_skill_contract  …… VERIFICATION.md 首行标题 ≠ VERSION
FAILED test_package_install_migrate（三条）
```

**产物没问题，是我改完文档没重建清单就去跑测试。**
三次里有一次我还照着假红去查了别的地方。

## 正确顺序（本件强制）

```
1. build_manifest.py          ← **必须在所有文件改动之后**（它算 checksums）
2. pytest                     ← 依赖 1
3. check_contract_drift.py    ← 版本三轴单一真源
4. check_verification_counts.py ← VERIFICATION.md 里的可数项 vs 实况
```

★ **`bump_version.py` 不在这里面**——它要先跑，且跑完还要人去写 CHANGELOG 与
VERIFICATION 的正文。本件是**写完正文之后**的那一步。

★ **任一步失败就停**，不往下跑。后面几步在前一步失败时给出的信息是误导性的。

## 它不做什么

- **不改任何内容**：不写 CHANGELOG、不改 VERIFICATION 正文、不升版号。
  那些都要人来判断写什么。
- **不 git add／commit。**
"""
import argparse
import json
import pathlib
import subprocess
import sys

STEPS = [
    ("重建清单与校验和", ["build_manifest.py"], "**必须在所有文件改动之后**——它算 checksums"),
    ("全量测试", ["-m", "pytest", "-q"], "依赖上一步；顺序反了会得到一批假红"),
    ("合同漂移", ["check_contract_drift.py"], "版本三轴各自单一真源"),
    ("VERIFICATION 可数项", ["check_verification_counts.py", "."], "文中的数 vs 仓库实况"),
]


def run_all(root: pathlib.Path, verbose: bool = False) -> int:
    scripts = root / "scripts"
    for i, (title, argv, why) in enumerate(STEPS, 1):
        cmd = ([sys.executable] + argv if argv[0].startswith("-")
               else [sys.executable, str(scripts / argv[0])] + argv[1:])
        print(f"\n── {i}/{len(STEPS)} {title} ──　（{why}）")
        r = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
        out = ((r.stdout or "") + (r.stderr or "")).strip()
        tail = "\n".join(out.splitlines()[-4:])
        print("  " + tail.replace("\n", "\n  ") if tail else "  （无输出）")
        if r.returncode != 0:
            print(f"\n✗ **第 {i} 步「{title}」未过（退出码 {r.returncode}），就此停下。**")
            print("  ★ 不继续往下跑——后面几步在这一步失败时给出的信息是误导性的。")
            return r.returncode
    print("\n✓ 四步全过")
    return 0


def self_test() -> int:
    global STEPS                 # ★ 必须在函数最开头声明，不能等到用过之后
    ok = True

    def chk(msg, cond):
        nonlocal ok
        ok = ok and bool(cond)
        print(("  ✓ " if cond else "  ✗ ") + msg)

    print("── 顺序本身就是判据：清单必须排在测试之前 ──")
    names = [s[0] for s in STEPS]
    chk(f"{names}", names.index("重建清单与校验和") < names.index("全量测试"))
    print("── ★★ 反向对照：任一步失败就停，不往下跑 ──")
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        (root / "scripts").mkdir()
        (root / "scripts" / "build_manifest.py").write_text(
            "import sys; print('boom'); sys.exit(3)", encoding="utf-8")
        # 后面几步的脚本**故意不建** —— 若它继续往下跑就会因「文件不存在」而报别的错
        rc = run_all(root)
        chk(f"第 1 步退出码 3 → run_all 返回 {rc}", rc == 3)
    print("── ★ 空 STEPS 不崩（射程边界）──")
    _bak, STEPS = STEPS, []
    try:
        with tempfile.TemporaryDirectory() as d:
            chk("空表返回 0", run_all(pathlib.Path(d)) == 0)
    finally:
        STEPS = _bak
    print("\n" + ("✓ 自测全过" if ok else "✗ 自测未过"))
    return 0 if ok else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", nargs="?", default=".", help="persona-distiller 根目录")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    return run_all(pathlib.Path(a.root).resolve())


if __name__ == "__main__":
    sys.exit(main())
