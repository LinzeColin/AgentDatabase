#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""升版：把新的 skill 发布号一次盖到全部对外声明位，然后自查漂移。

## 为什么需要它

`check_contract_drift.py` 能抓出漏改的位置，但**抓出来之后还得手工改 7 个文件**。
v0.0.0.15 这次升版，我自己就连着漏了两轮：先漏 `registry.yaml` 与 `index.json`，
补完又漏 README / VERIFICATION / handoff 三个标题——**门每次都抓到了，
但「抓到」和「不再发生」是两件事**。会重复 7 次的手工动作，迟早会漏第 8 次。

本脚本只做机械替换，判据仍归 `check_contract_drift.py`：
改完自动跑一遍，不通过就以非零退出码告诉你哪里还没对上。

**它不动 `builder_version`（交付合同）**——那个轴是故意钉住的，不随发布号移动。

退出码：0 = 升版并自查通过；1 = 改完仍有漂移；3 = 用法错误。
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
VERSION_RE = re.compile(r"^v\d+\.\d+\.\d+\.\d+$")


def _today() -> str:
    """发布日期取**本机当天**。放成独立函数是为了让自测能替换它。"""
    import datetime
    return datetime.date.today().isoformat()


def bare(version: str) -> str:
    return version[1:] if version.startswith("v") else version


def rewrite_title(path: pathlib.Path, new: str) -> bool:
    """只改第 1 行标题里的版本号，正文里的历史版本标记一律不碰。

    **按形态替换，不按「旧值」替换。** 首版写成 `line.replace(old, new)`，
    于是 `VERSION` 已被手工改过、只剩文档没跟上时 `old == new`，
    替换成了空操作——工具报「已改 4 处」而门当场报 3 条漂移。
    修复动作本身要能修复「修了一半的状态」，否则它只在理想路径上有用。
    """
    if not path.is_file():
        return False
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    if not lines:
        return False
    replaced = re.sub(r"v\d+\.\d+\.\d+\.\d+", new, lines[0], count=1)
    if replaced == lines[0]:
        return False
    lines[0] = replaced
    path.write_text("".join(lines), encoding="utf-8")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description="把新发布号盖到全部对外声明位并自查")
    ap.add_argument("new_version", help="形如 v0.0.0.15")
    ap.add_argument("--root", type=pathlib.Path, default=ROOT)
    args = ap.parse_args()

    new = args.new_version.strip()
    if not VERSION_RE.match(new):
        print(f"用法错误：版本号应形如 v0.0.0.15，得到 {new!r}", file=sys.stderr)
        return 3
    root = args.root.resolve()
    version_file = root / "VERSION"
    if not version_file.is_file():
        print(f"用法错误：{version_file} 不存在", file=sys.stderr)
        return 3

    # ★★ **动笔之前先确认下游在。** 2026-08-17 拿团队 skill 的副本实跑，
    #   本工具**写了一半才失败**：VERSION 与 manifest.version 已盖成新号，
    #   而末尾 `build_manifest.py` 不存在 → 报错 rc=1 退出 ——
    #   留下一棵「版本位改了一半」的树，比完全没跑**更糟**。
    #   [[a-step-that-runs-after-the-write-changes-nothing]] 的反面：
    #   **为失败准备的报错，挡不住「已经写坏了才报错」。**
    #   ⇒ 前置检查，缺一个就 rc=3 并且**一个字节都不写**。
    missing = [n for n in ("build_manifest.py", "check_contract_drift.py")
               if not (root / "scripts" / n).is_file()]
    if missing:
        print("用法错误：%s 下缺少 %s —— **本工具不在这个 root 上跑**，"
              "一个字节都没写。" % (root, "、".join(missing)), file=sys.stderr)
        print("  （本工具末尾要靠它们重建清单并自查；缺了就会写一半再失败。）",
              file=sys.stderr)
        return 3

    old = version_file.read_text(encoding="utf-8").strip()
    if old == new:
        print(f"版本号已经是 {new}，不重复写")
    touched: list[str] = []

    version_file.write_text(new + "\n", encoding="utf-8")
    touched.append("VERSION")

    manifest_path = root / "manifest.json"
    if manifest_path.is_file():
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        data["version"] = new
        # ★ `released_at` 此前**没有任何主人**：2026-08-17 逐版本对照 git 首次提交日，
        #   团队 skill 的 manifest 里它是个**恒定值**（14 个版本 0 个对得上），
        #   而 CHANGELOG 有 git 真值可比的 9 个全对。[[every-requirement-needs-an-owner]]
        #   ⇒ 升版时一并盖新。**只在字段本来就存在时才写**，不给没有它的 root 凭空造字段。
        #   ★★ **只在真的换号时才盖。** 我写完第一版就用它跑了一次「同号自查」
        #   （v0.0.0.154 → v0.0.0.154），它照样把发布日盖成了当天 ——
        #   而 v0.0.0.154 的 git 首次提交日是 **2026-08-14**，当天不是发布日。
        #   **空升版不是发布**：一个只为自查而跑的空转，不许改写发布事实。
        #   我因此当场造了一个假值（2026-07-23 → 2026-08-17，两个都不对），
        #   被自己的核对抓住。[[a-step-that-runs-after-the-write-changes-nothing]]
        if "released_at" in data and old != new:
            data["released_at"] = _today()
        manifest_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8")
        touched.append("manifest.json")

    # registry.yaml 与 index.json 历史上不带 `v` 前缀，保持各自的书写形态。
    registry_path = root / "registry.yaml"
    if registry_path.is_file():
        text = registry_path.read_text(encoding="utf-8")
        updated, count = re.subn(
            r"(^identity:\n(?:[ \t]+.*\n)*?[ \t]+version:[ \t]*)\S+",
            lambda m: m.group(1) + bare(new), text, count=1, flags=re.MULTILINE)
        if count:
            registry_path.write_text(updated, encoding="utf-8")
            touched.append("registry.yaml")

    index_path = root.parent.parent / "index.json"
    if index_path.is_file():
        data = json.loads(index_path.read_text(encoding="utf-8"))
        for entry in data.get("skills") or []:
            if entry.get("skill_id") == root.name:
                entry["version"] = bare(new)
        index_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                              encoding="utf-8")
        touched.append("registry/index.json")

    # ★ 团队 skill 专有的第三个版本位。此前本工具不认识它 ——
    #   于是拿 --root 指向团队 skill 时，VERSION 与 manifest 盖了新号
    #   而 `generator_version` 留在旧号上，**升版反而制造漂移**。
    team_index = root / "team-index.json"
    if team_index.is_file():
        data = json.loads(team_index.read_text(encoding="utf-8"))
        if "generator_version" in data:
            data["generator_version"] = new
            team_index.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                                  encoding="utf-8")
            touched.append("team-index.json（generator_version）")

    # ★ **VERIFICATION.md 不在这里**，这是本工具的一条硬边界。
    #
    #   它是**验证记录**，不是标签：正文写的是某一次实跑的逐项结果。
    #   把它的标题改成新版本号而正文还是上一次的，比标题陈旧**更糟**——
    #   陈旧标题一眼看得出，改过标题的旧正文会冒充当前复验。
    #   v0.0.0.16 升版时本工具就这么干过一次（正文仍写着 PARTIAL、
    #   bundle 构不出来、97 人、59 用例，而那三件当时都已不成立）。
    #
    #   正确的压力来自另一头：`check_contract_drift.py` 仍然要求
    #   它的标题等于 VERSION——**于是你必须真的重跑验证并重写正文**，
    #   而不是让一个改名工具替你把它变绿。
    for name in ("README.md", "handoff.md"):
        if rewrite_title(root / name, new):
            touched.append(f"{name}（首行标题）")

    print(f"{old} → {new}，已改 {len(touched)} 处：")
    for item in touched:
        print(f"  · {item}")

    # PACKAGE_MANIFEST.json 与 checksums 由生成器负责，这里顺手跑一遍。
    build = subprocess.run([sys.executable, str(root / "scripts" / "build_manifest.py")],
                           cwd=str(root), capture_output=True, text=True)
    if build.returncode != 0:
        print("✗ build_manifest.py 失败：" + (build.stderr or "").strip()[:200], file=sys.stderr)
        return 1
    print("  · PACKAGE_MANIFEST.json / checksums.sha256（由 build_manifest.py 重建）")

    print("\n⚠ VERIFICATION.md **未改**——它是验证记录不是标签。\n"
          "  请真的重跑一遍验证并重写正文，然后自己把标题改成新版本号。\n"
          "  下面的自查会因此报它漂移，那是有意的。\n")
    print("自查（判据归 check_contract_drift.py，本脚本只做替换）：")
    drift = subprocess.run([sys.executable, str(root / "scripts" / "check_contract_drift.py")],
                           cwd=str(root), capture_output=True, text=True)
    print((drift.stdout or "").rstrip())
    if drift.returncode != 0:
        print("\n↑ 还有位置没盖到。CHANGELOG 与 skill_log_evals 记录仍需手写，"
              "本脚本不代写升版理由。", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
