#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**版本绑定门**：本 skill 的版本号有没有盖在它产出的东西上。

## 触发本检查器的实例（可自行复现）

```
git show --stat --name-only --format="" 024b9a9e -- \
    CodexSkills/registry/codex/persona-distiller-group/
```

输出**只有一个文件**：`VERSION`。也就是说——

> **本 skill 的整个 v0.0.0.8，就是那一行字符串从 `v0.0.0.7` 改成 `v0.0.0.8`。**

那次提交的标题写的是人物侧的改进（「内容层检查进入发布门 + 版本号建立单一真源」），
团队侧的版本号是被顺手带上去的。团队侧此前**只有 1 处版本声明位**，
所以「各处一致」从来不是被检查出来的结论，而是**无处可比**。

`team-index.json`（99 人的那份产物）此前带 `schema_version`，
不带生成它的 skill 版本。**拿到一份有问题的索引，无从判断它出自哪个版本。**

## 判据

| # | 判据 | 为什么它不是代理量 |
|---|---|---|
| 1 | `VERSION` 存在且非空 | 读不到就抛，**不返回 `unknown`**——`unknown` 会让下游一致性比对恒等成立 |
| 2 | `manifest.json:version` == `VERSION` | 机读声明位，调用方与打包脚本读的是它 |
| 3 | `team-index.json:generator_version` == `VERSION` | 版本号**随产物走** |

★ 第 3 条与人物侧那条**被推翻的**判据（曾要求两个 skill 的 `VERSION` 完全相等）
必须区分清楚，否则很容易再犯一次同样的错：

- 旧判据宣称「这些人是用 vX 蒸出来的」，而**把 group 的 VERSION 改一下就能满足**——
  一个人也没重蒸，门却变绿。它测的是代理量（RUNBOOK 第七十种），
  实际后果是自 v0.0.0.9 起发行 bundle 一次也构建不出来。
- 本判据宣称的只是「这份 team-index 是 vX 生成的」。让它变绿的唯一方式，
  就是**真的用 vX 重新生成一次**——而重新生成恰好就是该断言的全部内容。
  **断言与使其为真的动作重合，才不是代理量。**

## 与它相邻的两件事（本检查器**不**负责，别指望它）

- 「99 个人是用哪个 distiller 版本蒸的」——那是人物侧的 `distilled_with`，
  由 `persona-distiller/scripts/check_distillation_freshness.py` 管，**默认只报不拦**。
- 「索引内容是否陈旧」——由 `registry_core.validate_registry` 的
  「重新构建后逐字段比对」负责。本检查器只管版本号这三处对不对得上。

退出码：0 = 绑定完好；1 = 有不一致；3 = 用法错误。
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from registry_core import check_version_binding, default_registry_root  # noqa: E402


def _fixture(root: pathlib.Path, *, version: str = "v0.0.0.9",
             manifest_version: object = "__same__",
             stamped: object = "__same__",
             admission: object = "__absent__",
             drop_manifest: bool = False) -> pathlib.Path:
    """造一份最小 registry 根目录。三个哨兵值 `__same__` 表示「与 VERSION 一致」。"""
    root.mkdir(parents=True, exist_ok=True)
    (root / "VERSION").write_text(version + "\n", encoding="utf-8")
    if not drop_manifest:
        mv = version if manifest_version == "__same__" else manifest_version
        payload = {"name": "persona-distiller-group"}
        if mv is not None:
            payload["version"] = mv
        (root / "manifest.json").write_text(
            json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    index: dict = {"schema_version": "3.0", "generated": True, "products": []}
    sv = version if stamped == "__same__" else stamped
    if sv is not None:
        index["generator_version"] = sv
    (root / "team-index.json").write_text(
        json.dumps(index, ensure_ascii=False), encoding="utf-8")
    # ★ 第四处声明位（2026-08-18 新增）。`__absent__` = 不造这个文件 ——
    #   用来钉住「文件不在时不许报错」。
    if admission != "__absent__":
        av = version if admission == "__same__" else admission
        payload: dict = {"summary": {}}
        if av is not None:
            payload["source_generator_version"] = av
        (root / "expert-fleet-admission.json").write_text(
            json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return root


def self_test() -> int:
    failures: list[str] = []
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)

        # 正对照：三处一致 → 一条都不许报。
        good = _fixture(tmp / "good")
        errs = check_version_binding(good)
        if errs:
            failures.append(f"正对照应当无报，实际 {len(errs)} 条：{errs}")

        # 负对照，逐类植入已知坏样本。
        cases = [
            ("manifest 版本落后", _fixture(tmp / "b1", manifest_version="v0.0.0.8"), "manifest.json"),
            ("缺 manifest 机读声明", _fixture(tmp / "b2", drop_manifest=True), "缺机读版本声明"),
            ("manifest 无 version 字段", _fixture(tmp / "b3", manifest_version=None), "manifest.json"),
            # ★★★ 第四处声明位的负对照（本件的由来：它实测漂了 13 个版本没人提醒）
            ("准入名册版本落后", _fixture(tmp / "adm1", admission="v0.0.0.32"),
             "expert-fleet-admission.json"),
            ("准入名册无 source_generator_version", _fixture(tmp / "adm2", admission=None),
             "缺 source_generator_version"),
            ("产物没盖版本号", _fixture(tmp / "b4", stamped=None), "缺 generator_version"),
            ("产物盖的是旧版本", _fixture(tmp / "b5", stamped="v0.0.0.7"), "generator_version"),
            ("VERSION 为空", _fixture(tmp / "b6", version=""), "VERSION 文件为空"),
        ]
        for label, fixture, want in cases:
            blob = " ".join(check_version_binding(fixture))
            if want not in blob:
                failures.append(f"负对照未被抓出：{label}（缺 {want!r}）｜实报：{blob or '（无）'}")

        # 反向对照：`unknown` **不许**当成合法版本蒙混过关。
        # 这是本检查器最容易被"修好"的方向——让读不到时返回 unknown，
        # 于是三处都是 unknown、比对恒等成立、门全绿而版本号根本不存在。
        sneaky = _fixture(tmp / "b7", version="unknown", stamped="unknown", manifest_version="unknown")
        (sneaky / "VERSION").write_text("unknown\n", encoding="utf-8")
        if check_version_binding(sneaky):
            failures.append("反向对照失败：三处同为字面量时不该报错（判据只管一致性，不管取值）")
        # 但 VERSION 缺失时必须抛，而不是退化成 unknown。
        missing = tmp / "b8"
        missing.mkdir()
        blob = " ".join(check_version_binding(missing))
        if "缺 VERSION 文件" not in blob:
            failures.append(f"反向对照失败：VERSION 缺失时应报「缺 VERSION 文件」，实报：{blob or '（无）'}")

    for f in failures:
        print(f"✗ {f}")
    if failures:
        print(f"负对照未通过：{len(failures)} 项")
        return 1
    print("负对照通过：正对照 0 报，坏样本 6 类全部抓出，"
          "且 VERSION 缺失不会退化成 unknown")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="版本绑定门：VERSION / manifest.json / team-index.json 三处必须同值")
    ap.add_argument("--registry-root", type=pathlib.Path, default=None,
                    help="团队 registry 根目录（默认：本脚本的上级目录）")
    ap.add_argument("--self-test", action="store_true", help="跑负对照，不读真实树")
    ap.add_argument("--json", action="store_true", help="机读输出")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    root = (args.registry_root or default_registry_root()).expanduser().resolve()
    if not root.is_dir():
        print(f"用法错误：{root} 不是目录", file=sys.stderr)
        return 3

    errors = check_version_binding(root)
    if args.json:
        print(json.dumps({"root": str(root), "errors": errors}, ensure_ascii=False, indent=2))
        return 1 if errors else 0

    if not errors:
        version = (root / "VERSION").read_text(encoding="utf-8").strip()
        print(f"✓ 版本绑定完好：VERSION / manifest.json / team-index.json 三处同为 {version}")
        return 0
    print(f"\n✗ 版本绑定 {len(errors)} 条不一致：\n")
    for e in errors:
        print(f"  - {e}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
