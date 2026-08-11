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


def _one_ledger_per_workspace(root: pathlib.Path,
                              corpora: pathlib.Path | None = None) -> list[str]:
    """**一个工作区只许有一份 `source-ledger.jsonl`。**

    ## 撞出它的那一次（2026-08-12）

    `check_scan_reach` 报：**该扫 42 个、实际扫了 42 个**——计数对上，
    **而集合不同**：少扫 2 个工作区根、多扫它们的 `evidence` 子目录。
    若那道判据只比计数，`42 = 42` 会一直是绿的
    （[[two-errors-cancelled-so-the-gate-stayed-green]]）。

    根因：Blackstone #169 与 Holmes #170 各有**两份**账本
    （`<ws>/evidence/` 与 `<ws>/_corpus/`），触发了
    `check_corpus_presence.scan()` 的「一个目录里多份账本 ⇒ 它是容器不是工作区」
    规则，于是把 `evidence` 当成了单位名。

    ★ **那条规则本身是对的**（它是为「`--root` 传成上级目录时 17 个工作区被
      collapse 成一行、然后报绿」那次事故立的）。错的是不该有两份账本。

    ★★ 两份**内容不同、不是副本**：Holmes 是 14 条 vs 16 条，
      且共有的 14 条逐条也不同；多出的两条是生涯尾段卷次，**被引 0 次**。

    → 本条只报**新出现的**：已知的那两个已判过分，重出账本等于改动被评分的东西，
      按红线不动，因此列入豁免名单。
    """
    KNOWN = {
        "wip-blackstone-169/workspaces/william-blackstone/william-blackstone",
        "wip-holmes-170/workspaces/oliver-wendell-holmes-jr/oliver-wendell-holmes-jr",
    }
    # ★ `corpora` 可注入**只为让自测碰得到这段逻辑**：默认值与原来逐字相同。
    #   2026-08-12 发现本函数与 `_verification_counts` 在 `--self-test` 里
    #   **两条都只走「路径不存在 → 返回 []」**，于是「正对照 0 报」对它们毫无意义，
    #   负对照更是一条都没有 —— [[empty-default-swallows-unknown]] 的原样。
    if corpora is None:
        corpora = root.parent.parent.parent / "skill_log_evals/persona-distiller/_corpora"
    if not corpora.is_dir():
        return []
    out = []
    seen: dict[str, list[str]] = {}
    for led in corpora.rglob("source-ledger.jsonl"):
        ws = led.parent.parent if led.parent.name in {"evidence", "_corpus"} else led.parent
        seen.setdefault(str(ws.relative_to(corpora)), []).append(led.parent.name)
    for ws, dirs in sorted(seen.items()):
        if len(dirs) > 1 and ws not in KNOWN:
            out.append(f"[一个工作区两份账本] {ws} —— 账本在 {sorted(dirs)}；"
                       "**判据会把它当成容器并下沉**，单位名会变成子目录名，"
                       "于是「扫了几个」对得上而「扫的是谁」是错的。"
                       "已知豁免（已判过分、不动）：Blackstone #169、Holmes #170")

    # ★★★ 2026-08-12 第二种形态：**同一个人物有两份 `claims.jsonl`，且内容不同。**
    #   撞出它的是核 #95「Koch 41 条压在一对源上」时：
    #   `wip-koch-107/claims.jsonl` 与 `.../evidence/claims.jsonl` 都是 46 条、
    #   **而 5 条的 `source_ids` 不同**——外层那份缺了后来补上的第三个来源
    #   `src-c8bca1856b9e`。判据读的是 `evidence/` 那份（权威），
    #   所以判决不受影响；**危险的是人**：照外层那份数，同一个问题会多算 3 条。
    #   全库实测 **6 个人物**有两份且**六对内容全都不同**
    #   （jenner-104 / koch-107 / lister-108 / osler-110 / pasteur-106 / virchow-109）。
    #   ⇒ 与上面那条同一个病：**一个人物的同一份东西，仓里有两个版本，而没人说哪个算数。**
    CLAIMS_KNOWN = {
        "wip-jenner-104", "wip-koch-107", "wip-lister-108",
        "wip-osler-110", "wip-pasteur-106", "wip-virchow-109",
    }
    per: dict[str, list[str]] = {}
    for cl in corpora.rglob("claims.jsonl"):
        per.setdefault(cl.relative_to(corpora).parts[0], []).append(
            str(cl.relative_to(corpora)))
    for person, files in sorted(per.items()):
        if len(files) > 1 and person not in CLAIMS_KNOWN:
            out.append(f"[一个人物两份 claims.jsonl] {person} —— {sorted(files)}；"
                       "**权威的是 `<工作区>/evidence/claims.jsonl`**，另一份是陈旧快照。"
                       "判据读权威那份、判决不受影响，**而人照另一份数就会得到不同的数**。"
                       "已知 6 个已存在的在豁免名单里（都已判过分，不动）。")
    return out


def _selftest_reach(root: pathlib.Path) -> list[str]:
    """**判据的自测有没有走到它自己的判定函数**（`check_selftest_reach.py`）。

    接在这里的理由：必读与 HANDOFF 都写着「**改完判据跑那道漂移门就够**」，
    而本条正是「改完判据」之后最该问的一句。同门的另外两条（一区两账本、自报数字）
    也都是这个性质——这道门实际上已经是「**改完判据之后的那一道**」。

    ★ 成本：全扫 89 件约 10 秒（本门原本 5.3 秒）。量过才接的，不是拍脑袋。
    """
    mod = root / "scripts" / "check_selftest_reach.py"
    if not mod.is_file():
        return []
    import subprocess
    r = subprocess.run([sys.executable, str(mod)], capture_output=True, text=True,
                       cwd=str(root))
    if r.returncode == 0:
        return []
    if "新出现" not in (r.stdout or ""):
        return [f"[自测射程] check_selftest_reach 跑不起来（rc={r.returncode}）："
                f"{(r.stderr or r.stdout)[:160]}"]
    lines = [l.strip() for l in (r.stdout or "").splitlines() if "从没被自测进入" in l]
    return ["[自测射程] **新出现「验了配料、没验判决」的自测**：" + "；".join(lines)
            + " —— **跑 `scripts/check_selftest_reach.py` 看全表**"]


def _paper_lanes(root: pathlib.Path) -> list[str]:
    """**纸面道**：某道的全部支撑都来自「一条同时挂多道」的源（`check_paper_lanes.py`）。

    与本门另外三条同性质——都是「改完判据/加完人物之后最该问的一句」。
    ★ 成本：全扫 43 份账本约 1 秒。
    """
    mod = root / "scripts" / "check_paper_lanes.py"
    if not mod.is_file():
        return []
    import subprocess
    r = subprocess.run([sys.executable, str(mod)], capture_output=True, text=True, cwd=str(root))
    if r.returncode == 0:
        return []
    if "新出现" not in (r.stdout or ""):
        return [f"[纸面道] check_paper_lanes 跑不起来（rc={r.returncode}）："
                f"{(r.stderr or r.stdout)[:160]}"]
    lines = [l.strip() for l in (r.stdout or "").splitlines() if "**新增**" in l]
    return ["[纸面道] **新出现工作区有「纸面道」**（该道没有一条专属的源）：" + "；".join(lines)
            + " —— **跑 `scripts/check_paper_lanes.py` 看全表**"]


def _verification_counts(root: pathlib.Path) -> list[str]:
    """**VERIFICATION.md 里能机械数出来的量，必须与实况相等。**

    2026-08-12：`check_checkers` 报它有 **5 项**对不上，全是当天的工作造成的陈旧
    （判据 87→89、脚本 125→130、checksum 465→474、
    待裁定速览表 35 行→37 行、条数「三十五」→「三十七」）。
    **其中两条是新登记的待裁定 ㊲㊳ 只进了正文没进速览表**——
    接手的人先看的就是那张表，会**漏掉当天最新的两条**。

    ★ 这一件此前 `quality_check` 与本门**都不跑它**（今天逐条查过调用方，
      六件里只有它两条例行路径都空）——[[a-checker-nothing-calls-is-not-a-checker]]。

    ★★ 它**只报不改**是有意的：对不上时不知道该改哪边（文档陈旧 还是 仓库真少了东西），
      那是人的判断。本门也只把它的结论转述出来，不替它决定。
    """
    mod = root / "scripts" / "check_verification_counts.py"
    if not mod.is_file():
        return []
    import subprocess
    import json as _j
    r = subprocess.run([sys.executable, str(mod)], capture_output=True, text=True, cwd=str(root))
    try:
        d = _j.loads(r.stdout)
    except Exception:
        return [f"[自报数字] check_verification_counts 跑不起来（rc={r.returncode}）："
                f"{(r.stderr or r.stdout)[:160]}"]
    n = d.get("**对不上的项数**", 0)
    if not n:
        return []
    bad = [x for x in d.get("明细", []) if "对不上" in str(x.get("判定", ""))]
    return [f"[自报数字] VERIFICATION.md **{n} 项与实况对不上**："
            + "；".join(f"{x['项']} 实况 {x['实况']} 文中 {x['文中']}" for x in bad)
            + " —— **跑 `scripts/check_verification_counts.py` 看全表**"]


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


def _checksums_fresh(root: pathlib.Path) -> tuple[list[str], list[str]]:
    """`checksums.sha256` 与磁盘现状对不对得上。

    ## ★★★ 为什么把这一条塞进**漂移门**，而不是留给全量自检

    2026-08-11：我改了 `scripts/quality_check.py`、它的镜像、以及一份 references 文档，
    **`--self-test` 全绿、本门（漂移）全绿、9 件判据逐件自测全绿**，
    而 `checksums.sha256` 没重算——**71 个测试里 4 个红**，
    全量自检才报出 `release checksum verification failed`。

    差别在**跑的频率**：改完判据我必跑这道漂移门（本会话跑了五六次），
    而全量自检要两分多钟，我不会每次都跑。**把检查放到有流量的那条路上。**

    ★ 只报**内容对不上**与**清单里有而磁盘没有**两类；
      「磁盘有而清单没有」交给 `build_manifest` 与全量自检，
      因为工作中途新建文件是常态，在这里报会天天误报。
    """
    import hashlib
    f = root / "checksums.sha256"
    if not f.is_file():
        return [], ["[发布清单] checksums.sha256 不在——**未核（不是通过）**"]
    bad, missing = [], []
    for line in f.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or "  " not in line:
            continue
        digest, rel = line.split("  ", 1)
        target = root / rel
        if not target.is_file():
            missing.append(rel)
            continue
        h = hashlib.sha256()
        with open(target, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        if h.hexdigest() != digest:
            bad.append(rel)
    out = []
    if bad:
        out.append("[发布清单] **checksums.sha256 与磁盘对不上 %d 个文件**："
                   "%s —— 改了随包分发的文件却没重算清单。"
                   "**跑 `scripts/build_manifest.py`，不要手写校验和。**"
                   % (len(bad), bad[:5]))
    if missing:
        out.append("[发布清单] 清单里有而磁盘上没有 %d 个：%s" % (len(missing), missing[:5]))
    return out, []


def check(root: pathlib.Path) -> tuple[list[str], list[str]]:
    """→ (漂移清单, 跳过说明)。"""
    problems: list[str] = []
    skipped: list[str] = []

    _cs_bad, _cs_skip = _checksums_fresh(root)
    problems.extend(_cs_bad)
    skipped.extend(_cs_skip)

    problems.extend(_one_ledger_per_workspace(root))
    problems.extend(_verification_counts(root))
    problems.extend(_selftest_reach(root))
    problems.extend(_paper_lanes(root))

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

    # --- B2b. ★★★ 2026-08-10：**镜像里不叫 `check_` 的那些，从来没被比过。**
    #   上面两行的射程是 `glob("check_*.py")`，而镜像目录里还躺着十几个**流程工具**：
    #   `assemble_judge_results.py`（**算 delta 的就是它**）、`build_blind_payload.py`、
    #   `ingest.py`、`declare_source_dedup.py`、`finalize_release.py`……
    #   实测：**5 个已经漂了**，`assemble_judge_results.py` 镜像比脚本少 **11.5 KB**。
    #   而本项目出过的最贵一次事故正是它的前身：
    #   「同一处除以 10 做了两遍，三轮 delta 全差一个数量级」。
    #   ★ 收件人照镜像跑，拿到的会是另一套数——**而漂移门一直报「无漂移」**。
    #   与 B2 同一句话：「同一件东西两份拷贝，改一处另一处继续活着」，
    #   **只是这一批连查都没查过。**
    for mirror in sorted((root / "references/pipeline/checkers").glob("*.py")):
        if mirror.name.startswith("check_"):
            continue                       # 上面 B2 已经比过
        twin = root / "scripts" / mirror.name
        if not twin.is_file():
            continue
        if mirror.read_bytes() != twin.read_bytes():
            problems.append(
                f"[流程工具镜像] {mirror.name} 两处不一致"
                f"（镜像 {len(mirror.read_bytes())} 字节 / 脚本 {len(twin.read_bytes())} 字节）"
                f"——**跑的是 scripts/ 那份，装出去的是 references/ 那份**；"
                f"收件人照镜像跑会拿到另一套结果")

    # --- B3. ★★★★ 镜像**逐字节相同还不够，得起得来** ---
    #   2026-08-10 实测：我给两件判据加了 `from common import corpus_body`，
    #   `cp` 过去之后**字节完全相同**，本件报「无合同漂移」——
    #   而镜像目录里**没有 `common.py`**，那两件加上依赖它的第三件
    #   一律 `ModuleNotFoundError`，**镜像里三件判据当场就是死的**。
    #   同时发现 `package_target.py` / `quality_check.py` 在镜像里**一直**起不来
    #   （缺 `delivery_builder` / `ledger`），**在我今天动它之前就是坏的**。
    #   ★ 字节比对只回答「两份一不一样」，**不回答「这一份跑不跑得起来」**。
    #   ★★ 抓到它的不是读代码，是**逐个真跑**（而且不能接管道——退出码会被吃掉）。
    #   这里只做**导入**：执行顶层 import，不跑 main，82 件约几秒。
    #   ★★★★ 2026-08-11 把这条边界量了一遍：镜像树 **86 件 `check_*.py` 各跑 `--self-test`**，
    #     **85 件过、1 件不过**——`check_holdout_mention.py`。
    #     它**导入是成功的**（不缺模块），坏在 main 里：
    #         tmpl_root = Path(__file__).resolve().parent.parent / "templates" / "target"
    #     在 `scripts/` 下解析成 `<包根>/templates/target`（**存在，32 项**）；
    #     在 `references/pipeline/checkers/` 下解析成 `references/templates/target`（**不存在**）。
    #     → **模板读到 0 行，自测失败；而本件因为只做导入，看不见它。**
    #   ★ 这不是本件漏了，是**它声明过的边界**——但边界现在有了具名实例与数字：
    #     「不跑 main」漏掉的**实测就是 1/86**，而那 1 件恰是 holdout 提及门。
    #   ★★ 要补这一层，成本是把 86 件的 `--self-test` 都跑一遍（分钟级，不是秒级）；
    #     `finalize_release` 里已有全量 pytest，**别在这里重复造**。
    #     完整测量与两个候选修法（各剩一个未消风险）见
    #     `_ledgers/_镜像树跑不跑得起来-2026-08-11.md`。
    #   ★★★ 两档，不要混：
    #     `check_*.py` 起不来 = **漏**（它们本该在镜像里就能跑）
    #     打包链的 `package_target.py` / `delivery_builder.py` 起不来 = **按设计如此**，
    #       它们 import 的 `registry_core` 住在**兄弟技能** `persona-distiller-group/scripts/`，
    #       镜像永远不该把别的技能的模块拷进来。**列出来但不算漂移。**
    CROSS_SKILL_OK = {"package_target.py", "delivery_builder.py"}
    mirror_dir = root / "references/pipeline/checkers"
    if mirror_dir.is_dir():
        dead, by_design = [], []
        for f in sorted(mirror_dir.glob("*.py")):
            #   ★★★★ 路径**必须用绝对路径**。第一版写 `str(f)`（相对我的 cwd）
            #     配 `cwd=mirror_dir`，Python 报「can't open file」而不是
            #     ModuleNotFoundError，于是我的判断一个都没命中——
            #     **99 个文件全"通过"，而它一个都没真的打开过。**
            #     那句「真跑 99 个，起不来 0 个」我写进了两条提交，是假的。
            r = subprocess.run(
                [sys.executable, "-c",
                 "import importlib.util,sys,pathlib;"
                 "p=pathlib.Path(sys.argv[1]);"
                 "sys.path.insert(0,str(p.parent));"
                 "s=importlib.util.spec_from_file_location('m',p);"
                 "m=importlib.util.module_from_spec(s);s.loader.exec_module(m)",
                 str(f.resolve())],
                capture_output=True, text=True, cwd=str(mirror_dir))
            err = r.stderr.strip().splitlines()[-1] if r.stderr.strip() else ""
            if "can't open file" in err or "No such file" in err:
                problems.append(f"[检查器镜像·**自检失灵**] {f.name} 连打开都没打开——"
                                f"路径传错了，**这一轮的「全绿」不作数**：{err}")
                continue
            if "ModuleNotFoundError" in err or "ImportError" in err:
                (by_design if f.name in CROSS_SKILL_OK else dead).append((f.name, err))
        for name, err in dead:
            problems.append(
                f"[检查器镜像·**起不来**] {name}：{err}"
                f"——★ 字节与 scripts/ 一致**不代表它能跑**；镜像少的多半是它 import 的模块")
        for name, err in by_design:
            skipped.append(f"[检查器镜像] {name} 起不来是**按设计如此**（跨技能依赖 registry_core）：{err}")

    # --- B4. ★★★★ 2026-08-11：**教训库索引也是一份会漂的产物，而它是给接手方读的。**
    #   `_ledgers/_教训库/_索引.md` 原本手写，**写完当天就漂了**：
    #   头部写「113 份」而目录里 115，条目摘要停在两版之前
    #   （`a-checker-nothing-calls` 索引写「第三批」，正文已是第六批）。
    #   已改成 `_生成索引.py` 现算。★ 但**生成器没有调用方就还是会漂**——
    #   下一个人改完教训文件不会记得跑它。[[a-checker-nothing-calls-is-not-a-checker]]
    #   ★★ 这里只跑 `--check`（只报不写），漂了就报出来，**不替人改文件**。
    idx_gen = root.parent.parent.parent / "skill_log_evals/persona-distiller/_ledgers/_教训库/_生成索引.py"
    if not idx_gen.is_file():
        skipped.append(f"[教训库索引] 找不到 {idx_gen.name}，**未核验**（不是通过）")
    else:
        r = subprocess.run([sys.executable, str(idx_gen), "--check"],
                           capture_output=True, text=True)
        if r.returncode == 1:
            problems.append(
                f"[教训库索引] **`_索引.md` 已漂**——{r.stdout.strip().lstrip('✗ ')}。"
                f"接手方读的就是这份索引，跑 `python3 {idx_gen.name}` 重生成")
        elif r.returncode != 0:
            problems.append(f"[教训库索引·**自检失灵**] 生成器跑不起来（rc={r.returncode}）："
                            f"{(r.stderr.strip().splitlines() or [''])[-1]}"
                            f"——**这一轮的「无漂移」不作数**")

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

        # ── D. `_verification_counts`（2026-08-12 接进本门）────────────────────
        # ★ 补这一组的起因：接完线才发现它在自测里**只走「文件不存在 → 返回 []」**，
        #   于是上面那句「正对照 0 报」对它一个字都不成立，负对照更是一条没有。
        #   ⇒ [[empty-default-swallows-unknown]]：`[]` 被读成「没问题」。
        stub = clean / "scripts" / "check_verification_counts.py"
        stub.parent.mkdir(parents=True, exist_ok=True)

        def _stub(body: str) -> list[str]:
            stub.write_text(body, encoding="utf-8")
            return _verification_counts(clean)

        # D1 负对照：被调判据报「对不上」→ 本门必须转述，且要带上项名与两个数
        got = _stub("print('''{\"**对不上的项数**\": 1, \"明细\": ["
                    "{\"项\": \"判据件数\", \"实况\": 89, \"文中\": \"[77]\", \"判定\": \"对不上\"}]}''')\n")
        if not (got and "[自报数字]" in got[0] and "判据件数" in got[0]
                and "89" in got[0] and "77" in got[0]):
            failures.append(f"负对照未被抓出：D1·自报数字对不上（实得 {got}）")

        # D2 正对照：报 0 项 → 本门不许报（否则每次提交都在喊狼来了）
        if _stub("print('{\"**对不上的项数**\": 0, \"明细\": []}')\n"):
            failures.append("误报：D2·被调判据报 0 项，本门却仍然报了")

        # D3 ★★ **最容易漏的一条**：被调判据自己崩了 / 吐的不是 JSON。
        #   此时既不能当成「0 项」放行，也不能连门一起崩——必须**报出来**。
        #   同族教训 [[untested-fallback-branches-only-fire-on-their-machine]]：
        #   没走过的兜底分支，只在别人机器上发作。
        got = _stub("import sys; sys.stderr.write('boom\\n'); sys.exit(3)\n")
        if not (got and "跑不起来" in got[0]):
            failures.append(f"负对照未被抓出：D3·被调判据崩掉时静默放行（实得 {got}）")
        got = _stub("print('这不是 JSON')\n")
        if not (got and "跑不起来" in got[0]):
            failures.append(f"负对照未被抓出：D3b·被调判据吐非 JSON 时静默放行（实得 {got}）")
        stub.unlink()

        # ── E. `_one_ledger_per_workspace`（同日接进本门，同样从没被夹具驱动过）──
        corp = tmp / "corpora"
        for rel, dirs in (
            ("wip-x-001/workspaces/alice/alice", ["evidence"]),            # E2 正：一份
            ("wip-y-002/workspaces/bob/bob", ["evidence", "_corpus"]),     # E1 负：两份
            # E3 正：**已判过分的两个在豁免名单里**，重出账本才是更大的破坏
            ("wip-holmes-170/workspaces/oliver-wendell-holmes-jr/oliver-wendell-holmes-jr",
             ["evidence", "_corpus"]),
        ):
            for d in dirs:
                p = corp / rel / d
                p.mkdir(parents=True, exist_ok=True)
                (p / "source-ledger.jsonl").write_text("{}\n", encoding="utf-8")
        got = _one_ledger_per_workspace(clean, corpora=corp)
        blob = " ".join(got)
        if "wip-y-002" not in blob:
            failures.append(f"负对照未被抓出：E1·一个工作区两份账本（实得 {got}）")
        if "wip-x-001" in blob:
            failures.append("误报：E2·只有一份账本的工作区被当成两份")
        if "wip-holmes-170" in blob:
            failures.append("误报：E3·豁免名单里的 Holmes #170 仍被报出")

    for f in failures:
        print(f"✗ {f}")
    if failures:
        print(f"负对照未通过：{len(failures)} 项")
        return 1
    # ★ 这句原写「坏样本 **5 类**全部抓出」——那 5 指的是 `want` 那个元组。
    #   2026-08-12 加了 D（自报数字 4 条）与 E（一区两账本 3 条）之后它就少报了，
    #   而**没有任何东西会提醒它**。改成点名分组，不写数：
    #   数一旦手写，每加一条负对照就陈旧一次 [[self-reported-numbers-must-be-computed]]。
    print("负对照通过：正对照 0 报；A 版本三轴 / B2 检查器镜像 / C1 输入合同 / C2 陈旧族数 / "
          "D 自报数字（含**被调判据崩掉不许静默放行**）/ E 一个工作区两份账本（含豁免名单）"
          "各组坏样本全部抓出，钉住的 builder 版本未被误伤")
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
