#!/usr/bin/env python3
"""HANDOFF.md 里写的命令，收件人照抄能不能跑通。

## 为什么要有这个判据

`HANDOFF.md` §3 是接手方的**主要操作参考**。2026-08-11 实测：那张表里
`python3 scripts/namesake_gate.py <人名>` —— 而工具要的是 `--name <人名>`，
**照抄就是 `error: the following arguments are required: --name`**。

§7 声称「已经在干净检出里验过」，但验的是 4 条（文件在不在、产物计数、
必读文件、next_person），**§3 那张表的 10 条命令一条都没跑过**。
——这正是 `verifying-single-commands-is-not-verifying-the-chain`：
单步都绿不等于收件人照着走得通。

镜像树有 `check_contract_drift` 管着；**文档与工具之间此前没有任何守卫**。

## 它怎么判

对 HANDOFF.md 里每一条 `python3 <某.py> …`：

1. 脚本文件在不在（路径按文档自己的 `cd` 解析）
2. 文档给的 `--flag` 工具认不认（跑 `--help` 取真实签名，不猜）
3. 工具**必填**的 flag，文档给没给
4. 文档给的位置参数个数，工具收不收得下
5. 文档用 `…`/`...` 省略了参数 —— **照抄跑不通**，单独报一类

★ 不改任何东西，只报。★ 不执行被检查的命令本体，只跑它的 `--help`。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

# 文档里的占位符：`<workspace>` `<ws>` `<人名>` `<c.json>`
_PLACEHOLDER = re.compile(r"^<[^>]*>$")
# 省略号：`…` 或 `...`（★ 表格里两种都出现过）
_ELIDED = {"…", "...", "..", "．．．"}

# 正文里举例用的假脚本名（`python3 x.py | tail` 那种），不是真命令
_PLACEHOLDER_SCRIPTS = {"x.py", "y.py", "foo.py", "bar.py", "script.py", "某.py"}

# ★★ 表格单元格里的 `|` 是被反斜杠转义的：`--phase research\|synthesis\|release`
#    先把 `\|` 还原成 `|`，再按真正的表格分隔符切；顺序反了就会把命令腰斩。
_ESCAPED_PIPE = "\x00ESCPIPE\x00"


def _split_table_cells(line: str) -> list[str]:
    """把一行 Markdown 表格切成单元格，保留被转义的 `|`。"""
    protected = line.replace(r"\|", _ESCAPED_PIPE)
    cells = protected.split("|")
    return [c.replace(_ESCAPED_PIPE, "|") for c in cells]


def _strip_md(s: str) -> str:
    """去掉行内代码反引号、粗体标记、行首列表符与 ★ 注记。"""
    s = s.strip()
    s = re.sub(r"^[\s>*\-+]+", "", s)
    s = s.replace("**", "").replace("`", "")
    return s.strip()


def _code_spans_or_whole(s: str) -> list[str]:
    """正文里**只认反引号里的东西**是命令。

    ★ 2026-08-11 实测：`python3 scripts/check_handoff_commands.py`（在仓根跑…）
      —— `_strip_md` 把反引号剥掉之后，后面那句中文正文被整段读成了 4 个位置参数。
      行内代码跨度本来就是「这是一条命令」的标记，剥掉它等于把标记扔了。
    """
    spans = re.findall(r"`([^`]+)`", s)
    if spans:
        return [x.strip() for x in spans]
    return [_strip_md(s)]


def extract_invocations(text: str) -> list[dict]:
    """从 HANDOFF 正文里抽出所有 `python3 x.py …` 调用。

    两个来源：Markdown 表格单元格、``` 代码块。
    同时跟踪最近一次 `cd <path>`，用来解析相对路径。
    """
    out: list[dict] = []
    cwd_rel = ""

    # ★★ 反斜杠续行必须先拼起来。不拼的话 2026-08-11 实测两种坏法同时发生：
    #    `python3 x.py \` 的那个 `\` 被当成一个位置参数（假报 extra-positional），
    #    而下一行真正的 `--task ...` 根本没进视野（假报 missing-required-flag）。
    #    ——两个报错都指向同一条命令，却都是我自己的解析制造的。
    # ★★★ 而代码块结束时**挂着的续行要冲刷出来，不能丢**：
    #    直接丢的那一版，`python3 x.py \` 后面紧跟 ``` 的写法会被整条吞掉，
    #    于是一条参数不全的命令**静默通过**——`empty-default-swallows-unknown` 的又一形态。
    logical: list[tuple] = []       # (起始行号, 文本, 是否在代码块内)
    pending: list[str] = []
    pending_lineno = 0
    in_fence = False

    def _flush():
        nonlocal pending, pending_lineno
        if pending:
            logical.append((pending_lineno, " ".join(pending), in_fence))
            pending, pending_lineno = [], 0

    for lineno, raw in enumerate(text.splitlines(), 1):
        stripped = raw.strip()
        if stripped.startswith("```"):
            _flush()
            in_fence = not in_fence
            continue
        if stripped.endswith("\\"):
            if not pending:
                pending_lineno = lineno
            pending.append(stripped[:-1])
            continue
        if pending:
            pending.append(stripped)
            _flush()
            continue
        logical.append((lineno, raw, in_fence))
    _flush()

    for lineno, raw, in_fence in logical:
        stripped = raw.strip()
        # ★★ `cd` 的作用域**到下一个标题为止**。
        #   2026-08-11 实测：§3 的 `cd CodexSkills/registry/codex/persona-distiller`
        #   一直漏到 200 行外的 §4，把那里写的**仓根相对路径**拼成了
        #   `.../persona-distiller/CodexSkills/registry/...`，于是一个**真实存在**的判据
        #   被报成 missing-file。读者不会这样读文档，判据也不该这样读。
        #   ★ 不用「仓根兜底」解决——那会把「cd 之后那个目录里确实没有」也一起放过。
        #   ★★★ 只在 `#`/`##` 上重置，**`###` 子节不重置**——
        #   §3 的 `cd` 本来就该管到它自己的子节；一刀切到 `######` 会把
        #   §3 里 `### 清重复源` 那条本来正确的命令反过来报成 missing-file。
        #   （改判据当场造出的新误报，是 `checker-blindspot-read-as-defect` 的同一形状。）
        if not in_fence and re.match(r"^#{1,2}\s", stripped):
            cwd_rel = ""
        pieces: list[str]
        if in_fence:
            pieces = [_strip_md(raw)]
        elif stripped.startswith("|"):
            pieces = []
            for c in _split_table_cells(raw):
                pieces.extend(_code_spans_or_whole(c))
        else:
            pieces = _code_spans_or_whole(raw)

        for piece in pieces:
            if not piece:
                continue
            m_cd = re.match(r"^cd\s+([^\s&;]+)\s*$", piece)
            if m_cd:
                cand = m_cd.group(1)
                # 只认仓内相对路径；`~/...` 这种绝对路径不当作后续调用的基准
                if not cand.startswith(("~", "/")):
                    cwd_rel = cand
                continue
            # 一行里可能有两条命令（`a.py … / b.py …`），先按 `python3` 切开再逐条解析
            for chunk in re.split(r"(?=\bpython3?\s)", piece)[1:]:
                m = re.match(r"python3?\s+(\S+\.py)(.*)$", chunk)
                if not m:
                    continue
                script = m.group(1)
                if Path(script).name.lower() in _PLACEHOLDER_SCRIPTS:
                    continue  # ★ `x.py` 这种是正文里举例用的，不是真命令
                tail = m.group(2)
                # ★ 管道/分隔符处截断：`python3 x.py | tail` 里的 `tail` 不是参数。
                #   （这条正文讲的正是「接管道会吞掉退出码」，判据自己却把 `tail` 读成了参数。）
                tail = re.split(r"\s(?:\|\||&&|\||;)\s", tail)[0]
                # ★★ shell 引号：`--verify-title "TITLE AS PRINTED"` 是**一个**参数。
                #   naive split 会把它读成两个位置参数，于是假报 extra-positional。
                try:
                    args = shlex.split(tail)
                except ValueError:
                    args = tail.split()
                out.append(
                    {
                        "line": lineno,
                        "cwd_rel": cwd_rel,
                        "script": script,
                        "args": args,
                        "raw": piece,
                    }
                )
    return out


def tool_signature(path: Path, sub: str = "") -> dict:
    """跑 `--help`，取真实签名。不猜、不 import。

    ★★ 支持 argparse 子命令：`raw_archive_manifest.py audit --database-dir .`
      的 `--database-dir` **只挂在子解析器上**，顶层 `--help` 里根本没有它。
      不跟进子命令就会把它报成 unknown-flag ——
      2026-08-11 `--all` 实测一次报出 5 条这样的假阳。
    """
    try:
        p = subprocess.run(
            [sys.executable, str(path)] + ([sub] if sub else []) + ["--help"],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "why": f"--help 跑不起来：{exc}"}
    help_text = (p.stdout or "") + (p.stderr or "")
    if p.returncode != 0 or "usage:" not in help_text:
        first = help_text.strip().splitlines()[:3]
        return {"ok": False, "why": "--help 退出码 %d：%s" % (p.returncode, " / ".join(first))}

    all_flags = set(re.findall(r"--[A-Za-z][A-Za-z0-9-]*", help_text))

    # usage 块 = 从 `usage:` 到第一个空行
    m = re.search(r"^usage:(.*?)(?:\n\s*\n|\Z)", help_text, re.S | re.M)
    usage = m.group(1) if m else ""
    usage = " ".join(usage.split())
    # 去掉所有 [...]（可选项），要处理嵌套：`[--include-report PATH[=RELATIVE_NAME]]`
    prev = None
    while prev != usage:
        prev = usage
        usage = re.sub(r"\[[^\[\]]*\]", " ", usage)

    # ★★ argparse 的**互斥必选组**长这样：`(--local-runtime X | --local-runtime-env Y)`
    #   —— 给其中**一个**就满足。把组内两个都算成必填，会对一条完全正确的命令
    #   报 missing-required-flag（2026-08-11 `--all` 的最后一处假阳就是它）。
    either_groups: list = []
    for g in re.findall(r"\(([^()]*)\)", usage):
        flags = set(re.findall(r"--[A-Za-z][A-Za-z0-9-]*", g))
        if len(flags) >= 2:
            either_groups.append(flags)
    usage = re.sub(r"\([^()]*\)", " ", usage)

    toks = usage.split()
    if toks and toks[0].endswith(".py"):
        toks = toks[1:]

    required_flags: set[str] = set()
    positionals: list[str] = []
    i = 0
    while i < len(toks):
        t = toks[i]
        if t.startswith("--"):
            required_flags.add(t)
            # 紧跟的大写 token 是它的 metavar，吃掉
            if i + 1 < len(toks) and re.match(r"^[A-Z][A-Z0-9_]*", toks[i + 1]):
                i += 1
        elif t.startswith("-"):
            pass
        elif re.match(r"^[a-z][a-z0-9_]*$", t):
            positionals.append(t)
        i += 1

    # `{generate,audit}` 这种 token = 子命令集合
    subs: set = set()
    for t in toks:
        m_sub = re.match(r"^\{([^}]+)\}$", t)
        if m_sub:
            subs |= {x.strip() for x in m_sub.group(1).split(",") if x.strip()}
    if subs:
        positionals = [x for x in positionals if x not in subs]

    return {
        "ok": True,
        "all_flags": all_flags,
        "required_flags": required_flags,
        "positionals": positionals,
        "subcommands": subs,
        "either_groups": either_groups,
    }


def check(handoff: Path, repo_root: Path, extra_bases=None) -> list[dict]:
    """extra_bases 只在 --all 里给。

    ★ 2026-08-11 实测：`--all` 扫到 `OpenAIDatabase/docs/remediation/…/HANDOFF.md`，
      里面写的 `scripts/privacy_guard.py` 是相对**那个子项目根**说的，
      而我按「文档所在目录」解析 → **5 处全是假报**，5 个脚本都在
      `OpenAIDatabase/scripts/` 下好好的。
      —— 一个报 5 条假的判据，人学会的是忽略它。
    ★★ 只在 `--all` 里放宽；默认路径（仓根那份 HANDOFF）不给 extra_bases，
      免得重演「兜底把真缺失也一起放过」。
    """
    text = handoff.read_text(encoding="utf-8")
    findings: list[dict] = []
    sig_cache: dict[str, dict] = {}

    for inv in extract_invocations(text):
        primary = repo_root / inv["cwd_rel"] if inv["cwd_rel"] else repo_root
        target = (primary / inv["script"]).resolve()
        if not target.is_file():
            for b in (extra_bases or []):
                cand = (b / inv["cwd_rel"] / inv["script"]).resolve() if inv["cwd_rel"] \
                    else (b / inv["script"]).resolve()
                if cand.is_file():
                    target = cand
                    break

        if not target.is_file():
            findings.append(
                {
                    "kind": "missing-file",
                    "line": inv["line"],
                    "script": inv["script"],
                    "detail": "文档说在 %s 下，实际不存在" % (inv["cwd_rel"] or "<仓根>"),
                    "raw": inv["raw"],
                }
            )
            continue

        args = inv["args"]
        if any(a in _ELIDED for a in args):
            findings.append(
                {
                    "kind": "elided",
                    "line": inv["line"],
                    "script": inv["script"],
                    "detail": "文档用省略号带过参数——收件人照抄跑不通",
                    "raw": inv["raw"],
                }
            )
            continue

        key = str(target)
        if key not in sig_cache:
            sig_cache[key] = tool_signature(target)
        sig = sig_cache[key]
        if not sig["ok"]:
            findings.append(
                {
                    "kind": "help-broken",
                    "line": inv["line"],
                    "script": inv["script"],
                    "detail": sig["why"],
                    "raw": inv["raw"],
                }
            )
            continue

        # ★ 文档第一个位置参数正好是子命令 → 换成子解析器的签名再比
        first_pos = next((a for a in args if not a.startswith("-")), None)
        if first_pos and first_pos in sig.get("subcommands", set()):
            sub_key = key + "\0" + first_pos
            if sub_key not in sig_cache:
                sig_cache[sub_key] = tool_signature(target, first_pos)
            if sig_cache[sub_key]["ok"]:
                sig = sig_cache[sub_key]
                args = [a for a in args if a != first_pos]

        doc_flags = {a.split("=")[0] for a in args if a.startswith("--")}
        # 位置参数 = 既不是 flag、也不是紧跟 flag 的取值
        doc_positionals: list[str] = []
        expect_value = False
        for a in args:
            if a.startswith("--"):
                expect_value = "=" not in a
                continue
            if expect_value:
                expect_value = False
                continue
            doc_positionals.append(a)

        for f in sorted(doc_flags - sig["all_flags"]):
            findings.append(
                {
                    "kind": "unknown-flag",
                    "line": inv["line"],
                    "script": inv["script"],
                    "detail": "文档给了 %s，工具不认（工具认的：%s）"
                    % (f, " ".join(sorted(sig["all_flags"])[:12])),
                    "raw": inv["raw"],
                }
            )

        for grp in sig.get("either_groups", []):
            if not (grp & doc_flags):
                findings.append(
                    {
                        "kind": "missing-required-flag",
                        "line": inv["line"],
                        "script": inv["script"],
                        "detail": "工具要求 %s **至少给一个**，文档一个都没给"
                        % " 或 ".join(sorted(grp)),
                        "raw": inv["raw"],
                    }
                )

        for f in sorted(sig["required_flags"] - doc_flags):
            findings.append(
                {
                    "kind": "missing-required-flag",
                    "line": inv["line"],
                    "script": inv["script"],
                    "detail": "工具**必填** %s，文档没给——照抄直接报错" % f,
                    "raw": inv["raw"],
                }
            )

        if len(doc_positionals) > len(sig["positionals"]):
            findings.append(
                {
                    "kind": "extra-positional",
                    "line": inv["line"],
                    "script": inv["script"],
                    "detail": "文档给了 %d 个位置参数（%s），工具只收 %d 个（%s）"
                    % (
                        len(doc_positionals),
                        " ".join(doc_positionals),
                        len(sig["positionals"]),
                        " ".join(sig["positionals"]) or "无",
                    ),
                    "raw": inv["raw"],
                }
            )

    return findings


# --------------------------------------------------------------------------
# 自测
# --------------------------------------------------------------------------

_FAKE_NAMED = """#!/usr/bin/env python3
import argparse
p = argparse.ArgumentParser()
p.add_argument('--name', required=True)
p.add_argument('--output')
p.parse_args()
"""

_FAKE_POSITIONAL = """#!/usr/bin/env python3
import argparse
p = argparse.ArgumentParser()
p.add_argument('target')
p.add_argument('--phase', choices=['research', 'synthesis', 'release'])
p.parse_args()
"""


_FAKE_EITHER = """#!/usr/bin/env python3
import argparse
p = argparse.ArgumentParser()
g = p.add_mutually_exclusive_group(required=True)
g.add_argument('--local-runtime')
g.add_argument('--local-runtime-env')
p.add_argument('--pages-candidate', required=True)
p.parse_args()
"""

_FAKE_SUBCMD = """#!/usr/bin/env python3
import argparse
p = argparse.ArgumentParser()
sp = p.add_subparsers(dest='cmd', required=True)
a = sp.add_parser('audit')
a.add_argument('--database-dir')
g = sp.add_parser('generate')
g.add_argument('--out', required=True)
p.parse_args()
"""


def self_test() -> int:
    cases = [
        # (说明, HANDOFF 片段, 期望的 kind 集合)
        (
            "① 正例：文档与工具一致",
            "| 同名护栏 | `python3 named.py --name <人名>` |",
            set(),
        ),
        (
            "② ★ 反例：工具要 --name，文档写成位置参数（Grotius 2026-08-11 实撞）",
            "| 同名护栏 | `python3 named.py <人名>` |",
            {"missing-required-flag", "extra-positional"},
        ),
        (
            "③ 反例：文档给了工具不认的 flag",
            "| x | `python3 named.py --nmae <人名>` |",
            {"unknown-flag", "missing-required-flag"},
        ),
        (
            "④ 反例：省略号——照抄跑不通",
            "| 打包 | `python3 named.py …` |",
            {"elided"},
        ),
        (
            "⑤ 反例：脚本根本不在",
            "| x | `python3 nope.py --name <人名>` |",
            {"missing-file"},
        ),
        (
            "⑥ ★ 正例：表格单元格里 `\\|` 转义过的取值不能把命令腰斩",
            r"| 三道主门 | `python3 positional.py <ws> --phase research\|synthesis\|release` |",
            set(),
        ),
        (
            "⑦ ★★ ⑥ 的正对照：同一行改成错 flag 必须红——"
            "否则 ⑥ 的绿可能是「转义管道把后半截整个丢了」",
            r"| 三道主门 | `python3 positional.py <ws> --phaze research\|synthesis\|release` |",
            {"unknown-flag"},
        ),
        (
            "⑧ 正例：代码块里的 cd 会改变后续相对路径解析",
            "```bash\ncd sub\npython3 named.py --name X\n```",
            set(),
        ),
        (
            "⑨ ★ 反例：同上，但 cd 之后那个目录里没有这个脚本",
            "```bash\ncd sub\npython3 positional.py foo\n```",
            {"missing-file"},
        ),
        (
            "⑩ ★★ 正例：反斜杠续行要拼起来（不拼则 `\\` 被当位置参数 + 真参数看不见）",
            "```bash\npython3 named.py \\\n  --name X\n```",
            set(),
        ),
        (
            "⑪ ★★ ⑩ 的正对照：续行里放个错 flag 必须报 unknown-flag。"
            "若报的是 missing-required-flag，说明第二行被整个丢掉了，⑩ 的绿就是假的",
            "```bash\npython3 named.py \\\n  --nmae X --name Y\n```",
            {"unknown-flag"},
        ),
        (
            "⑬ ★★ 正例：`cd` 不许漏过标题——标题之后的仓根相对路径要按仓根解析",
            "```bash\ncd sub\n```\n\n## 另一节\n\n```bash\npython3 positional.py foo\n```",
            set(),
        ),
        (
            "⑭ ★★ ⑬ 的正对照：同一节内（无标题）则 cd 仍然有效，必须报 missing-file",
            "```bash\ncd sub\npython3 positional.py foo\n```",
            {"missing-file"},
        ),
        (
            "⑮ ★★ 正例：`###` 子节**不**重置 cd——同一节内的子标题下命令仍按 cd 解析",
            "```bash\ncd sub\n```\n\n### 子节\n\n```bash\npython3 named.py --name X\n```",
            set(),
        ),
        (
            "⑯ ★★ ⑮ 的正对照：同样在 `###` 子节下，换成 sub/ 里没有的脚本必须红——"
            "否则 ⑮ 的绿可能是「根本没去解析」",
            "```bash\ncd sub\n```\n\n### 子节\n\n```bash\npython3 positional.py foo\n```",
            {"missing-file"},
        ),
        (
            "⑰ ★★ 正例：正文里反引号包住的命令，后面跟中文正文不许被读成参数",
            "跑一遍 `python3 named.py --name X`（在仓根跑，别接管道）。",
            set(),
        ),
        (
            "⑱ ★★ ⑰ 的正对照：反引号**里**放个错 flag 必须红——"
            "否则 ⑰ 的绿可能是「反引号里的东西压根没被解析」",
            "跑一遍 `python3 named.py --nmae X --name Y`（在仓根跑）。",
            {"unknown-flag"},
        ),
        (
            "⑲ ★★ 正例（--all 语义）：给了祖先目录做候选基准时，"
            "子项目根下的脚本要找得到",
            "```bash\npython3 named.py --name X\n```",
            set(),
        ),
        (
            "⑳ ★★ 正例：子命令的 flag 只挂在子解析器上，顶层 --help 看不见——要跟进去",
            "`python3 subcmd.py audit --database-dir .`",
            set(),
        ),
        (
            "㉑ ★★ ⑳ 的正对照：子命令里放个**该子命令没有**的 flag 必须红——"
            "否则 ⑳ 的绿可能是「子命令一来就不检查了」",
            "`python3 subcmd.py audit --out X`",
            {"unknown-flag"},
        ),
        (
            "㉒ ★★ 子命令**自己**的必填项也要看得见",
            "`python3 subcmd.py generate`",
            {"missing-required-flag"},
        ),
        (
            "㉓ ★★ 正例：互斥必选组给**一个**就够，不许报另一个缺失",
            "`python3 either.py --local-runtime X --pages-candidate Y`",
            set(),
        ),
        (
            "㉔ ★★ ㉓ 的正对照：互斥组**一个都不给**必须红",
            "`python3 either.py --pages-candidate Y`",
            {"missing-required-flag"},
        ),
        (
            "㉕ ★ 组外的必填项不受影响，照旧要报",
            "`python3 either.py --local-runtime X`",
            {"missing-required-flag"},
        ),
        (
            "⑫ ★ 反例：续行跨过代码块结尾时不许把后面的正文吞进来",
            "```bash\npython3 named.py \\\n```\n随便一句正文",
            {"missing-required-flag"},
        ),
    ]

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "named.py").write_text(_FAKE_NAMED, encoding="utf-8")
        (root / "positional.py").write_text(_FAKE_POSITIONAL, encoding="utf-8")
        (root / "subcmd.py").write_text(_FAKE_SUBCMD, encoding="utf-8")
        (root / "either.py").write_text(_FAKE_EITHER, encoding="utf-8")
        (root / "sub").mkdir()
        (root / "sub" / "named.py").write_text(_FAKE_NAMED, encoding="utf-8")

        failed = 0
        for label, snippet, expect in cases:
            doc = root / "H.md"
            doc.write_text(snippet + "\n", encoding="utf-8")
            got = {f["kind"] for f in check(doc, root)}
            ok = got == expect
            if not ok:
                failed += 1
            print("%s %s" % ("PASS" if ok else "**FAIL**", label))
            if not ok:
                print("     期望 %s，实得 %s" % (sorted(expect) or "无", sorted(got) or "无"))

    print("\n自测 %d/%d 通过" % (len(cases) - failed, len(cases)))
    return 1 if failed else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--handoff", help="要扫的文档路径（默认 = 仓根的 HANDOFF.md）")
    ap.add_argument("--all", action="store_true",
                    help="扫 git 里所有 HANDOFF.md/handoff.md")
    ap.add_argument("--repo-root", help="相对路径的解析基准（默认 = HANDOFF.md 所在目录）")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return self_test()

    repo = _git_root(Path(__file__).resolve().parent)

    if a.handoff:
        targets = [Path(a.handoff)]
    elif a.all:
        if repo is None:
            print("不在 git 仓里，--all 用不了", file=sys.stderr)
            return 2
        targets = _tracked_handoffs(repo)
    else:
        # ★★★ 默认只认**仓根**那一份 —— 接手方读的就是它。
        # 2026-08-11 实测：原来的「从 scripts/ 往上找第一个 HANDOFF.md」在 macOS 上
        # 命中了同目录的 `handoff.md`（大小写不敏感），扫了一份 85 行的**别的**文档，
        # 报了 2 处 finding 而仓根那份 554 行**一个字都没看**。
        # ——`gate-green-but-pointed-at-wrong-artifact` 第 28 次。
        if repo is None:
            print("不在 git 仓里，请用 --handoff 指定", file=sys.stderr)
            return 2
        targets = [repo / "HANDOFF.md"]

    total = 0
    report = []
    for handoff in targets:
        if not handoff.is_file():
            print("**没有这份文件**：%s" % handoff, file=sys.stderr)
            return 2
        repo_root = Path(a.repo_root) if a.repo_root else handoff.parent
        extra = None
        if a.all and repo is not None:
            # 文档所在目录往上一直到仓根，都当候选基准
            extra = []
            cur = handoff.parent
            while True:
                extra.append(cur)
                if cur == repo or cur.parent == cur:
                    break
                cur = cur.parent
        findings = check(handoff, repo_root, extra)
        total += len(findings)
        report.append({"handoff": str(handoff), "findings": findings})

    if a.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1 if total else 0

    for item in report:
        print("\n扫 %s" % item["handoff"])
        print("   （相对路径基准 = 该文件所在目录）")
        if not item["findings"]:
            print("   ✓ 文档里的命令全部与工具的真实签名对得上")
            continue
        for f in item["findings"]:
            print("\n   [%s] 第 %d 行  %s" % (f["kind"], f["line"], f["script"]))
            print("     %s" % f["detail"])
            print("     文档原文：%s" % f["raw"][:160])
    print("\n共 %d 处（扫了 %d 份文档）" % (total, len(report)))
    return 1 if total else 0


def _git_root(start: Path):
    for p in [start, *start.parents]:
        if (p / ".git").exists():
            return p
    return None


def _tracked_handoffs(repo: Path) -> list[Path]:
    """git 里跟踪着的 HANDOFF.md / handoff.md，全都扫。

    ★ 用 `-c core.quotepath=false`，否则中文路径会被转义成 \\346\\... 而 open 不到。
    """
    p = subprocess.run(
        ["git", "-c", "core.quotepath=false", "ls-files", "-z"],
        cwd=str(repo), capture_output=True, text=True,
    )
    out = []
    for rel in p.stdout.split("\0"):
        if rel and Path(rel).name.lower() == "handoff.md":
            out.append(repo / rel)
    return sorted(out)


if __name__ == "__main__":
    raise SystemExit(main())
