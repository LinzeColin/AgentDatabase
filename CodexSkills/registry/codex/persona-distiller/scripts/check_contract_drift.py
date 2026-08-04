#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**合同漂移门**：查「对外声明的版本与输入合同，是不是同一份」。

## 触发本检查器的实例

v0.0.0.13 的公开树里，同一个 skill 同时对外声明了 **7 个不同的版本号**：

| 位置 | 值 | 离发布脚本的距离 |
|---|---|---|
| `CodexSkills/registry/index.json` | `0.0.0.4` | 最远 |
| `registry.yaml`（registry 索引指向的机读入口） | `0.0.0.5` | |
| `VERIFICATION.md` / `handoff.md` / `PACKAGE_MANIFEST.json` | `v0.0.0.5` | |
| `README.md` | `v0.0.0.6` | |
| `SKILL.md` 正文首个小节标题 | `v0.0.0.7` | |
| `VERSION` / `manifest.json` | `v0.0.0.13` | 最近 |

**衰减是单调的：离发布脚本越远的地方越旧。** 原因不是有人偷懒，
而是 `self_check.py` 的版本校验**只比 `VERSION` 与 `manifest.json` 两处**——
v0.0.0.8 说「版本已建立单一真源」，实际建立的是**两点之间的一致**，
剩下六处从来没有人查。**只覆盖 2/8 的单一真源，不是单一真源。**

## 比版本更严重的一类：输入合同自相矛盾

`SKILL.md` 的 metadata（调用方读的那份）写：

> Required inputs are the target person's name and one identity family
> **or weighted multi-identity selection**

而同一个文件的正文写：

> `身份`：十二个主身份之一（单一主身份；**多重身份已移除**）

`registry.yaml` 更把已被删除的 `多重身份` 目录列为 `persistent_output`。
**这不是文件名不统一，是对调用方的输入合同产生冲突**——
按 metadata 传「加权多身份」的调用方，会被正文的门直接拒绝，
而 metadata 正是调用方唯一会读的那份。

## 三个轴，不能互相顶替

| 轴 | 真源 | 写法约定 |
|---|---|---|
| `skill_version` | `VERSION` 文件 | `v0.0.0.N` |
| `builder_version`（交付合同） | `scripts/persona_registry.BUILDER_VERSION` | `v0.0.0.N`，**故意长期钉住**，不跟随 skill 升版 |
| `product_version`（人物产物） | 每个 canonical 人物独立 | 裸写 `0.0.0.1..0.0.0.999`，**不带 `v`** |

本检查器**依赖「builder 带 `v`、product 不带 `v`」这条既有书写约定**
来把两者分开（README 的版本三分小节已明确这一点）。
若将来有人把人物版本写成 `v0.0.0.1`，本检查器会误报——
那时应当修书写约定，而不是放宽本判据。

**一行里同时出现两个轴的版本号，本身就算漂移。** 不是误报：
README 原来那行「v0.0.0.6 将身份分类……交付合同仍为 v0.0.0.5」
正是读者把两个轴搞混的来源。

退出码：0 = 无漂移；1 = 有漂移；3 = 用法错误。
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

ROOT_DEFAULT = pathlib.Path(__file__).resolve().parent.parent

# 历史文档：里面的旧版本号是**事实记录**，不是当前声明，一律不查。
HISTORICAL = (
    "CHANGELOG.md",
    "task-pack/",
    "audit/",
    "references/ledgers/",
    "references/pipeline/",
)

VER_RE = re.compile(r"v0\.0\.0\.\d+")            # 带 v = skill 或 builder 轴
ANY_VER_RE = re.compile(r"v?0\.0\.0\.\d+")

# 「多重身份」词族——出现在 metadata（输入合同）里即为冲突。
#
# 判据是**出现即报**，不是「肯定提供才报」。看起来过严，但更严的那条才可机检：
# 想区分「提供加权多身份」与「加权多身份已移除」，得用字符串去认否定语气，
# 而「正则写窄 → 命中为 0 → 断言不存在」是 RUNBOOK 里复发过十二次的失败模式。
# 代价只是 description 里不能写否定句——那句话本来就该放正文，
# metadata 只负责说清**能传什么**。
MULTI_IDENTITY = ("multi-identity", "multi identity", "weighted multi", "多重身份")

# 声明族数的陈旧写法。真源是 registries/identity-families.json 的条目数。
STALE_FAMILY_COUNT = ("seven-family", "seven family", "七类", "七个身份", "6+1", "7+1")

# 只在这些「当前声明」文件里查族数与多身份词族。
CONTRACT_DOCS = (
    "README.md", "SKILL.md", "VERIFICATION.md", "handoff.md",
    "CONTRIBUTING.md", "SECURITY.md", "ROADMAP.md", "registry.yaml",
    "manifest.json", "PACKAGE_MANIFEST.json",
)


def norm(v: str | None) -> str | None:
    """去掉可选的前导 `v`。registry.yaml 与 index.json 历史上不带 `v`，
    强行统一字面量会动到消费方，语义比较即可。"""
    if v is None:
        return None
    v = str(v).strip()
    return v[1:] if v.startswith("v") else v


def _json(path: pathlib.Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _first_line(path: pathlib.Path) -> str:
    try:
        return path.read_text(encoding="utf-8").splitlines()[0]
    except Exception:
        return ""


def collect_skill_version_sites(root: pathlib.Path) -> list[tuple[str, str | None, str]]:
    """→ [(位置, 声明值, 说明)]。值为 None = 该位置不存在（跳过，不算漂移）。"""
    sites: list[tuple[str, str | None, str]] = []

    m = _json(root / "manifest.json") or {}
    sites.append(("manifest.json:version", m.get("version"), "机读"))

    pm = _json(root / "PACKAGE_MANIFEST.json") or {}
    sites.append(("PACKAGE_MANIFEST.json:version", pm.get("version"), "机读"))
    kind = (pm.get("distribution") or {}).get("kind")
    if kind:
        found = VER_RE.search(kind)
        sites.append(("PACKAGE_MANIFEST.json:distribution.kind",
                      found.group(0) if found else None, "机读"))

    reg = root / "registry.yaml"
    if reg.is_file():
        text = reg.read_text(encoding="utf-8")
        # identity: 块下的 version 行（registry/index.json 指向的机读入口）
        found = re.search(r"^identity:\n(?:[ \t]+.*\n)*?[ \t]+version:[ \t]*(\S+)",
                          text, re.MULTILINE)
        sites.append(("registry.yaml:identity.version",
                      found.group(1) if found else None, "机读·registry 入口"))

    # 仓内的 registry 总索引。skill 被单独安装时不存在 → 跳过。
    idx = root.parent.parent / "index.json"
    if idx.is_file():
        data = _json(idx) or {}
        for entry in (data.get("skills") or []):
            if entry.get("skill_id") == root.name:
                sites.append((f"{idx.name}:skills[{root.name}].version",
                              entry.get("version"), "机读·总索引"))
                break

    for doc in ("README.md", "VERIFICATION.md", "handoff.md"):
        p = root / doc
        if p.is_file():
            found = VER_RE.search(_first_line(p))
            sites.append((f"{doc}:首行标题", found.group(0) if found else None, "人读"))

    return sites


def scan_builder_lines(root: pathlib.Path) -> list[tuple[str, int, str, list[str]]]:
    """扫描声称在讲交付合同的行，取出其中带 `v` 的版本号。"""
    hits: list[tuple[str, int, str, list[str]]] = []
    for name in CONTRACT_DOCS:
        p = root / name
        if not p.is_file():
            continue
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            low = line.lower()
            if not ("builder_version" in low or "delivery contract" in low
                    or "交付合同" in line or "delivery_contract" in low):
                continue
            found = VER_RE.findall(line)
            if found:
                hits.append((name, i, line.strip(), found))
    return hits


def scan_mixed_axis_lines(root: pathlib.Path, skill_v: str, builder_v: str) -> list[tuple[str, int, str]]:
    """一行里同时出现两个不同轴的版本号 → 读者必然搞混。"""
    if norm(skill_v) == norm(builder_v):
        return []
    out = []
    for name in CONTRACT_DOCS:
        p = root / name
        if not p.is_file():
            continue
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            found = {norm(x) for x in VER_RE.findall(line)}
            if norm(skill_v) in found and norm(builder_v) in found:
                out.append((name, i, line.strip()))
    return out


def read_frontmatter_description(skill_md: pathlib.Path) -> str:
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    fm = text[3:end if end > 0 else len(text)]
    out, capturing = [], False
    for line in fm.splitlines():
        if line.startswith("description:"):
            capturing = True
            out.append(line.split(":", 1)[1])
        elif capturing and (line.startswith(" ") or line.startswith("\t")):
            out.append(line)
        elif capturing:
            break
    return " ".join(out)


def check(root: pathlib.Path) -> tuple[list[str], list[str]]:
    """→ (漂移清单, 跳过说明)。"""
    problems: list[str] = []
    skipped: list[str] = []

    # ★★ v0.0.0.94 新增第四条比对：**CHANGELOG 的最高条目必须等于 VERSION**。
    #   实测背景：2026-08-04 一天写了 v0.0.0.84–94 十一条 CHANGELOG，
    #   而 VERSION 一直停在 v0.0.0.83——**落后 11 格，三轴比对全绿**，
    #   因为它只比 VERSION↔manifest（两处都是 83），**比不到 CHANGELOG**。
    #   「单一真源」若不把记录变更的那份算进去，就管不住这种漂移。
    def _changelog_top(root):
        f = root / "CHANGELOG.md"
        if not f.is_file():
            return None, "CHANGELOG.md 不在——**未核（不是通过）**"
        ns = [int(m.group(1)) for m in
              re.finditer(r"^## v0\.0\.0\.(\d+)", f.read_text(encoding="utf-8"), re.M)]
        return (max(ns) if ns else None), (None if ns else "CHANGELOG 里一条版本条目都没有——**未核**")

    ver_file = root / "VERSION"
    if not ver_file.is_file():
        return [f"缺 VERSION 文件（真源不存在）：{ver_file}"], skipped
    skill_v = ver_file.read_text(encoding="utf-8").strip()

    # --- A0. CHANGELOG 的最高条目 vs VERSION（v0.0.0.94 新增的第四条轴）---
    top, why = _changelog_top(root)
    if why:
        skipped.append(f"CHANGELOG：{why}")
    else:
        import re as _re
        m = _re.match(r"v?0\.0\.0\.(\d+)", skill_v)
        if not m:
            skipped.append(f"VERSION 认不出形状：{skill_v!r}")
        elif int(m.group(1)) != top:
            problems.append(
                f"[changelog] VERSION = {skill_v}，而 CHANGELOG 最高条目是 v0.0.0.{top}"
                f"——**差 {abs(top - int(m.group(1)))} 格**。"
                f"记录变更的那一份也是版本真源；不比它，就管不住『写了条目忘了升版』。")

    # --- A. skill_version 单一真源 ---
    for where, value, kind in collect_skill_version_sites(root):
        if value is None:
            skipped.append(f"{where}（{kind}）：该位置无版本声明")
            continue
        if norm(value) != norm(skill_v):
            problems.append(
                f"[skill_version] {where}（{kind}）= {value!r}，"
                f"真源 VERSION = {skill_v!r}")

    # --- B. builder_version 单一真源 ---
    builder_v = None
    sys.path.insert(0, str(root / "scripts"))
    try:
        import persona_registry  # type: ignore
        builder_v = getattr(persona_registry, "BUILDER_VERSION", None)
    except Exception as exc:  # pragma: no cover - 环境问题，如实报出
        skipped.append(f"[builder_version] 取不到真源 persona_registry.BUILDER_VERSION：{exc}")
    finally:
        sys.path.pop(0)

    if builder_v:
        for name, lineno, line, found in scan_builder_lines(root):
            bad = [f for f in found if norm(f) != norm(builder_v)]
            if bad:
                problems.append(
                    f"[builder_version] {name}:{lineno} 讲交付合同却写 {bad}，"
                    f"真源 BUILDER_VERSION = {builder_v!r}｜{line[:70]}")
        for name, lineno, line in scan_mixed_axis_lines(root, skill_v, builder_v):
            problems.append(
                f"[轴混写] {name}:{lineno} 同一行同时出现 skill_version 与 "
                f"builder_version，读者必然搞混｜{line[:70]}")

    # --- B2. 检查器镜像：scripts/ 与 references/pipeline/checkers/ 必须逐字节相同 ---
    #
    # 这两处各有一份同名检查器，**而真正把门的是 `scripts/` 那份**
    #   （`quality_check.py` 用 `Path(__file__).parent / 'check_authorship.py'` 加载）。
    # 实测（Godin #99 当场撞到）：`check_semantic_residue.py` 早已分叉——
    # Robertson #97 补的「祈使禁止族」只落在 `references/` 那份，
    # **门跑的一直是没修过的旧版**。改进做了，门没拿到，而两边各自 `--self-test` 全绿。
    #
    # 这是第二十二种的又一形态：同一件东西两份拷贝，改一处另一处继续活着。
    # ★★ v0.0.0.68：**只存在于一侧的判据，此前被静默跳过。**
    #
    #   `if not twin.is_file(): continue` —— 这一行让四件只在镜像里的判据
    #   （check_anchor_coherence / check_holdout_overlap / check_material_split /
    #   check_verbatim_quotes）**从未被报出来**，而它们在 `scripts/` 里根本不存在，
    #   于是**一次都没有运行过**。其中 `check_holdout_overlap` 自称硬门。
    #
    #   这正是本段注释上面写的那句话的另一半：
    #   「同一件东西两份拷贝，改一处另一处继续活着」——
    #   **还有一种是「只存在一处」，而把门的恰好是没有它的那一处。**
    mirrors = sorted((root / "references/pipeline/checkers").glob("check_*.py"))
    scripts_side = sorted((root / "scripts").glob("check_*.py"))
    only_mirror = {m.name for m in mirrors} - {s.name for s in scripts_side}
    only_scripts = {s.name for s in scripts_side} - {m.name for m in mirrors}
    for name in sorted(only_mirror):
        problems.append(
            f"[检查器镜像] {name} **只在 references/pipeline/checkers/ 里，scripts/ 没有**"
            f"——**把门的是 scripts/ 那份，所以这件判据一次都没跑过**")
    for name in sorted(only_scripts):
        problems.append(
            f"[检查器镜像] {name} **只在 scripts/ 里，references/ 没有**"
            f"——镜像缺件，装出去的包会少这一件")
    for mirror in mirrors:
        twin = root / "scripts" / mirror.name
        if not twin.is_file():
            continue
        if mirror.read_bytes() != twin.read_bytes():
            problems.append(
                f"[检查器镜像] {mirror.name} 在 scripts/ 与 references/pipeline/checkers/ "
                f"两处不一致——**把门的是 scripts/ 那份**，改了 references/ 不会生效")

    # --- C. 身份输入合同 ---
    fam_file = root / "registries" / "identity-families.json"
    fam = _json(fam_file) or {}
    families = fam.get("families") or []
    if not families:
        skipped.append(f"[身份] 读不到族真源 {fam_file}")
    else:
        n = len(families)
        zh_names = {f.get("zh") for f in families if f.get("zh")}

        skill_md = root / "SKILL.md"
        if skill_md.is_file():
            desc = read_frontmatter_description(skill_md).lower()
            raw_desc = read_frontmatter_description(skill_md)
            for token in MULTI_IDENTITY:
                if token in desc or token in raw_desc:
                    problems.append(
                        f"[输入合同] SKILL.md metadata 的 description 出现 {token!r}——"
                        f"正文已规定单一主身份、多重身份已移除。"
                        f"metadata 是调用方唯一会读的那份，冲突直接落到调用方头上")
                    break

        for name in CONTRACT_DOCS:
            p = root / name
            if not p.is_file() or any(h in name for h in HISTORICAL):
                continue
            for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                for token in STALE_FAMILY_COUNT:
                    if token in line:
                        problems.append(
                            f"[身份] {name}:{i} 写 {token!r}，"
                            f"而族真源 {fam_file.name} 有 {n} 族｜{line.strip()[:70]}")
                        break

        reg = root / "registry.yaml"
        if reg.is_file():
            text = reg.read_text(encoding="utf-8")
            group = root.parent / "persona-distiller-group"
            for zh in re.findall(r"[一-鿿]{2,6}(?:师|家)", text):
                if zh in zh_names:
                    continue
                if group.is_dir() and not (group / zh).is_dir():
                    problems.append(
                        f"[身份] registry.yaml 列出的身份目录 {zh!r} "
                        f"既不在族真源里，磁盘上也不存在")

    return problems, skipped


# --------------------------------------------------------------------------
# 负对照：植入已知坏样本，确认真的报错。没有负对照的检查器，全绿不构成证据。
# --------------------------------------------------------------------------
def _fixture(tmp: pathlib.Path, *, drift: bool) -> pathlib.Path:
    root = tmp / "skill"
    (root / "scripts").mkdir(parents=True)
    (root / "registries").mkdir(parents=True)
    (root / "VERSION").write_text("v0.0.0.13\n", encoding="utf-8")
    (root / "scripts" / "persona_registry.py").write_text(
        'BUILDER_VERSION = "v0.0.0.5"\n', encoding="utf-8")
    (root / "registries" / "identity-families.json").write_text(json.dumps(
        {"families": [{"id": f"f{i}", "zh": f"族{i}师"} for i in range(12)]},
        ensure_ascii=False), encoding="utf-8")

    good_v, desc_extra, fam_line = "v0.0.0.13", "", "十二个单一主身份"
    if drift:
        good_v, desc_extra, fam_line = "v0.0.0.6", " or weighted multi-identity selection", "seven-family registry"

    (root / "manifest.json").write_text(json.dumps({"version": good_v}), encoding="utf-8")
    (root / "PACKAGE_MANIFEST.json").write_text(json.dumps(
        {"version": good_v, "distribution": {"kind": f"repository-customized-{good_v}"}}),
        encoding="utf-8")
    (root / "README.md").write_text(
        f"# Persona Distiller {good_v}\n\n{fam_line}\n"
        "- `builder_version`（交付合同格式）：v0.0.0.5\n", encoding="utf-8")
    (root / "registry.yaml").write_text(
        "identity:\n  skill_id: persona-distiller\n"
        f"  version: {good_v}\n  entry: SKILL.md\n", encoding="utf-8")
    (root / "SKILL.md").write_text(
        "---\nname: persona-distiller\n"
        f"description: Required inputs are the name and one identity family{desc_extra}.\n"
        "---\n\n# 正文\n", encoding="utf-8")
    return root


def self_test() -> int:
    failures = []
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)

        clean = _fixture(tmp / "a", drift=False)
        problems, _ = check(clean)
        if problems:
            failures.append(f"正对照应当无漂移，实际报出 {len(problems)} 条：{problems[:3]}")

        dirty = _fixture(tmp / "b", drift=True)
        problems, _ = check(dirty)
        blob = " ".join(problems)
        # 镜像分叉的负对照
        (dirty / "scripts").mkdir(exist_ok=True)
        (dirty / "references/pipeline/checkers").mkdir(parents=True, exist_ok=True)
        (dirty / "scripts" / "check_x.py").write_text("A\n", encoding="utf-8")
        (dirty / "references/pipeline/checkers" / "check_x.py").write_text("B\n", encoding="utf-8")
        problems, _ = check(dirty)
        blob = " ".join(problems)
        if "[检查器镜像]" not in blob:
            failures.append("负对照未被抓出：B2·检查器两处镜像分叉")

        for want, label in (
            ("manifest.json:version", "A·机读版本漂移"),
            ("README.md:首行标题", "A·人读标题漂移"),
            ("registry.yaml:identity.version", "A·registry 入口漂移"),
            ("[输入合同]", "C1·metadata 多身份与正文冲突"),
            ("seven-family", "C2·陈旧族数声明"),
        ):
            if want not in blob:
                failures.append(f"负对照未被抓出：{label}（缺 {want!r}）")

        # 反向：正对照里那条合法的 builder v0.0.0.5 不许被误判成漂移
        problems, _ = check(clean)
        if any("builder_version" in p for p in problems):
            failures.append("误报：故意钉住的 builder_version v0.0.0.5 被当成漂移")

    for f in failures:
        print(f"✗ {f}")
    if failures:
        print(f"负对照未通过：{len(failures)} 项")
        return 1
    print("负对照通过：正对照 0 报，坏样本 5 类全部抓出，钉住的 builder 版本未被误伤")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="合同漂移门：版本单一真源 + 身份输入合同一致性")
    ap.add_argument("--root", type=pathlib.Path, default=ROOT_DEFAULT,
                    help="skill 根目录（默认：本脚本的上级目录）")
    ap.add_argument("--self-test", action="store_true", help="跑负对照，不读真实树")
    ap.add_argument("--json", action="store_true", help="机读输出")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    root = args.root.resolve()
    if not root.is_dir():
        print(f"用法错误：{root} 不是目录", file=sys.stderr)
        return 3

    problems, skipped = check(root)

    if args.json:
        print(json.dumps({"root": str(root), "problems": problems, "skipped": skipped},
                         ensure_ascii=False, indent=2))
        return 1 if problems else 0

    for s in skipped:
        print(f"· 跳过 {s}")
    if not problems:
        print("✓ 无合同漂移：版本三轴各自单一真源，身份输入合同与正文一致")
        return 0
    print(f"\n✗ 合同漂移 {len(problems)} 条：\n")
    for p in problems:
        print(f"  - {p}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
