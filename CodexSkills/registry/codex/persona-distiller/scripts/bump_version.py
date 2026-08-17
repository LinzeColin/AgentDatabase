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


# ── 产物侧 / 工具侧分类 ────────────────────────────────────────────────
# ★★★ 2026-08-04 裁定：**判据落地算工具改动，不动版本号**；只有产物侧变化才升版。
#   理由是「兼容下限 = 当前版本末位 − 10」——每升一版，全部存量产物就往
#   「不适配」推一格，**产物一个字没改却因为尺子在跑而变老**。
#
# **这条裁定此前只写在 CHANGELOG 与 VERIFICATION 的正文里，没有执行者。**
#   两次实况，同一个版本号：
#     2026-08-17 ①  跑 `bump_version.py v0.0.0.155` → 读到 CHANGELOG 开头那段裁定 → 还原 6 处
#     2026-08-17 ②  又跑 `bump_version.py v0.0.0.155` → 靠漂移门报红才回头查 → 还原 8 处
#   第一次是**碰巧读到**，第二次是**碰巧红了**。两次都不是流程接住的。
#   [[a-rule-in-a-doc-has-no-enforcer]]｜[[my-pre-push-ritual-has-only-one-guard]]
#
# 下面的射程按**实测**定：那两次之间改的 90 个文件逐个分类，
#   scripts/tests 41、references（`example-knuth/` 就在这下面）43、发布元数据 5、
#   SKILL.md 1（内容是「这件判据会写盘」的告诫，实质也是工具侧）——**产物侧 0**。
TOOL_SIDE_PREFIXES = ("scripts/", "tests/", "references/")
RELEASE_META = frozenset({
    "VERSION", "CHANGELOG.md", "VERIFICATION.md", "README.md", "handoff.md",
    "manifest.json", "registry.yaml", "checksums.sha256", "PACKAGE_MANIFEST.json",
    "index.json", "team-index.json",
})


def classify(rel_paths) -> tuple[list[str], list[str], list[str]]:
    """→ (工具侧, 发布元数据, **可能是产物侧**)。纯函数，不碰磁盘。

    ★ 第三档故意叫「**可能是**产物侧」——本函数不替人判断，
      它只把「不在已知工具侧射程里」的挑出来交给人看。
      把判断权收进代码，下一个没见过的目录就会被静默归成工具侧。
    """
    tool, meta, product = [], [], []
    for p in rel_paths:
        p = p.strip()
        if not p:
            continue
        if p.startswith(TOOL_SIDE_PREFIXES):
            tool.append(p)
        elif p in RELEASE_META:          # 只认**顶层**那几个名字，不按文件名到处匹配
            meta.append(p)
        else:
            product.append(p)
    return tool, meta, product


def changed_since(root: pathlib.Path, version: str) -> tuple[list[str], str | None]:
    """→ (自 `version` 落版以来改过的 skill 内相对路径, 未量的理由)。

    含**已提交**（落版提交..HEAD）与**未提交**（工作区）两部分——
    升版通常是在有待提交改动时跑的，只看已提交会漏掉本次要发的东西。
    """
    def git(*a):
        return subprocess.run(("git", "-C", str(root)) + a, capture_output=True, text=True)

    pre = git("rev-parse", "--show-prefix")
    if pre.returncode != 0:
        return [], "不在 git 工作树里（%s）" % (pre.stderr.strip()[:80] or "rev-parse 失败")
    prefix = pre.stdout.strip()                       # 形如 CodexSkills/registry/codex/persona-distiller/
    # ★ pathspec 相对**当前目录**，而 `-C root` 已经把当前目录换成 root ——
    #   写 `prefix + "VERSION"` 会解析成 root/CodexSkills/…/VERSION（不存在），
    #   `git log` 安静地返回 0 行。**靠「未量 ≠ 空清单」那条守卫当场接住的**：
    #   若失败时返回 `[]`，上层会读成「0 个改动 ⇒ 没有产物侧 ⇒ 拒绝」——
    #   **正确的结论，错误的理由**，而且下次真有产物侧改动时同样会拒。
    #   [[empty-default-swallows-unknown]]
    log = git("log", "--format=%H", "-S", version, "--", "VERSION")
    if log.returncode != 0 or not log.stdout.strip():
        return [], "找不到 %s 的落版提交（git log -S 无结果）" % version
    base = log.stdout.strip().splitlines()[-1]        # ★ 最后一行＝最早那个＝引入它的那次
    out = []
    for r in (git("diff", "--name-only", base + "..HEAD"), git("status", "--porcelain")):
        if r.returncode != 0:
            return [], "取不到改动清单：%s" % r.stderr.strip()[:80]
        for line in r.stdout.splitlines():
            p = line[3:] if len(line) > 3 and line[2] == " " else line   # porcelain 的两列状态
            if " -> " in p:                       # 改名：只取新名
                p = p.split(" -> ", 1)[1]
            p = p.strip().strip('"')
            if p.startswith(prefix):
                out.append(p[len(prefix):])
    return sorted(set(out)), None


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


def self_test() -> int:
    bad, n = [], [0]

    def chk(lbl, ok):
        n[0] += 1
        print(("  ✓ " if ok else "  ✗ ") + lbl)
        if not ok:
            bad.append(lbl)

    # ★★★ 用**真实那 90 个文件的形状**做正负例，不编夹具
    #   [[fixtures-are-clean-because-i-wrote-them]]
    t, m, p = classify([
        "scripts/check_contract_drift.py", "tests/test_release_bundle.py",
        "references/pipeline/RUNBOOK.md", "references/pipeline/example-knuth/facts.md",
        "VERSION", "CHANGELOG.md", "checksums.sha256", "SKILL.md",
    ])
    chk("★★★ 正例：scripts/ tests/ references/ 都归工具侧（3 个）", len(t) == 4)
    chk("★★ 正例：`example-knuth/` 在 references 下 ⇒ 工具侧，**不是产物**",
        "references/pipeline/example-knuth/facts.md" in t)
    chk("★★ 正例：VERSION/CHANGELOG/checksums 归发布元数据", len(m) == 3)
    chk("★★★ 正例：`SKILL.md` 归「**可能是**产物侧」⇒ 交给人判，不替人归成工具侧",
        p == ["SKILL.md"])
    chk("★★★ 负例（**这一天的真实情况**）：只有工具侧+元数据 ⇒ product 为空 ⇒ 该拒绝",
        classify(["scripts/a.py", "references/b.md", "VERSION"])[2] == [])
    chk("★★★ 正例：真改了人物产物（`example-persona/` 这类不在射程里的）⇒ 报到产物侧 ⇒ 放行",
        classify(["builder/families.json"])[2] == ["builder/families.json"])
    chk("★ 空输入不炸，也不把空当成「有产物」", classify([]) == ([], [], []))
    chk("★ 空串与空白行被跳过", classify(["", "  ", "\n"]) == ([], [], []))
    chk("★★ `scriptsX/` 不算 scripts/（前缀要带斜杠）",
        classify(["scriptsX/a.py"])[2] == ["scriptsX/a.py"])
    chk("★★ 顶层同名才算元数据；深处的 `README.md` 归产物侧交给人看",
        classify(["some/dir/README.md"])[2] == ["some/dir/README.md"])
    # changed_since 在非 git 目录下必须报「未量」而不是报空（空会被读成「没改动」）
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        paths, why = changed_since(pathlib.Path(td), "v0.0.0.1")
        chk("★★★ 非 git 树 ⇒ 返回**未量的理由**，不返回空清单（空会被读成「没改动」）",
            paths == [] and bool(why))
    print("\n自测 %d 项，不符 %d 项" % (n[0], len(bad)))
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="把新发布号盖到全部对外声明位并自查")
    ap.add_argument("new_version", nargs="?", help="形如 v0.0.0.15")
    ap.add_argument("--root", type=pathlib.Path, default=ROOT)
    ap.add_argument("--anyway", metavar="理由",
                    help="跳过「配不配升版」前置。**必须写理由**——"
                         "指明哪个文件是产物侧。理由会印进输出，请一并写进 CHANGELOG。")
    ap.add_argument("--self-test", "--selftest", dest="selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return self_test()
    if not args.new_version:
        print("用法错误：缺版本号（或用 --self-test）", file=sys.stderr)
        return 3

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

    # ★★★ 第二道前置：**这批改动配不配升版**（同样一个字节都不写）。
    #   见文件上方 TOOL_SIDE_PREFIXES 处那段裁定与两次实况。
    if old != new and not args.anyway:
        changed, why = changed_since(root, old)
        if why:
            print("★ **未量，不是通过**（rc=4）—— 判不出这批改动是工具侧还是产物侧：%s" % why,
                  file=sys.stderr)
            print("  升版前必须知道这个。要绕过：--anyway '<理由>'。**一个字节都没写。**",
                  file=sys.stderr)
            return 4
        tool, meta, product = classify(changed)
        print("自 %s 落版以来改了 **%d** 个文件："
              "工具侧 %d｜发布元数据 %d｜**可能是产物侧 %d**"
              % (old, len(changed), len(tool), len(meta), len(product)))
        if not product:
            print("\n✗ **拒绝升版**：这批改动里**一个产物侧文件都没有**。", file=sys.stderr)
            print("  2026-08-04 裁定：判据落地算工具改动，**不动版本号**——", file=sys.stderr)
            print("  兼容下限 = 版本末位 − 10，每升一版，全部存量产物就往「不适配」推一格，",
                  file=sys.stderr)
            print("  **产物一个字没改却因为尺子在跑而变老**。", file=sys.stderr)
            print("\n  ★ 这个错在 2026-08-17 一天里犯了**两次**，都是这个版本号，", file=sys.stderr)
            print("    一次靠碰巧读到 CHANGELOG、一次靠漂移门报红才回头 —— 所以有了本道前置。",
                  file=sys.stderr)
            print("\n  ★★ 该做的是：在 CHANGELOG 的 `## 工具改动（不升版）` 一节里记一条。",
                  file=sys.stderr)
            print("  确实要升（例如改了 SKILL.md 里真正影响产出的指令）："
                  "`--anyway '<写清哪个文件是产物侧>'`", file=sys.stderr)
            return 5

        # ★★★ 「可能是产物侧」**不等于**「是产物侧」——不许在这里替人放行。
        #   第一版写成「product 非空 ⇒ 放行」，当场就给了错答案：
        #   那 90 个文件里唯一落进这一档的是 `SKILL.md`，而它那次的改动是
        #   **3 行「这件判据会写盘」的告诫**，实质是工具侧 —— 于是守卫照样放行，
        #   等于没建。分类器判不出这个差别，**也不该假装判得出**。
        #   ⇒ 两条路都停在人这里，只是措辞不同。[[checker-blindspot-read-as-defect]]
        print("\n✗ **暂不升版**：有 %d 个文件不在已知工具侧射程里，"
              "**判不出它们是不是产物侧**：" % len(product), file=sys.stderr)
        for p in product[:12]:
            print("     · %s" % p, file=sys.stderr)
        if len(product) > 12:
            print("     …另 %d 个" % (len(product) - 12), file=sys.stderr)
        print("\n  判别问的是：**这个改动会让蒸出来的人物产物不一样吗？**", file=sys.stderr)
        print("    会  ⇒ 产物侧，该升版：`--anyway '<哪个文件、怎么影响产出>'`", file=sys.stderr)
        print("    不会 ⇒ 工具侧，记进 CHANGELOG 的 `## 工具改动（不升版）` 一节。",
              file=sys.stderr)
        print("  ★ 2026-08-17 的实况：唯一落进这一档的是 `SKILL.md`，"
              "改的是 3 行「本判据会写盘」的告诫 ⇒ **工具侧，没升版**。", file=sys.stderr)
        return 5
    elif args.anyway:
        print("★ 已用 `--anyway` 跳过「配不配升版」前置，理由：%s" % args.anyway)

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
