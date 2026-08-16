#!/usr/bin/env python3
"""**文档里给的命令，参数形状与脚本对不对得上。**

## 撞出它的那一次（2026-08-12）

`HANDOFF.md` 的「怎么跑」第 ③ 条写着：

    python3 scripts/init_target.py --name "<人名>" --identity <identity.json> ...

而 `--identity` 要的是**族号 1-12 或族名**（`--help`：`single primary identity, 1-12 or name`）。
**接手方按文档敲的第一条建工作区命令就会失败。**

★ 那条错**不是读文档发现的，是真跑 #172 时撞出来的**。
  文档写了多久没人知道——因为没有任何东西在核「文档里的命令跑不跑得通」。

## 它查两件事

1. **文档用到的选项，脚本里有没有**（`--foo` 在不在 `add_argument` 里）；
2. ★ **文档给的值的形状，与选项的类型对不对得上**——
   文档写 `<xxx.json>` / `<xxx目录>` / `<xxx.zip>` 这种**路径形状**，
   而脚本那个选项**既没有 `type=pathlib.Path`、help 里也不提「路径」**，就是可疑。

★★ **第 2 条才是关键**：`--identity` 是**存在的**，第 1 条查不出它。
  只有比「值的形状」才抓得到。

## 它**不**做的事

- 不真跑命令（跑一遍要建工作区、要语料）；
- 不查位置参数的顺序（那要读 `parse_args` 之后的用法）；
- **只报不拦**：文档里的占位符本来就是给人读的，措辞会有出入。

## 已知的两个误报（留在这里，免得下一个人以为是新问题）

| 配对 | 为什么不是问题 |
|---|---|
| `--key <盲态key.json>` → `assemble_judge_results.py` | help 明写「盲判 key 的**路径**」，代码 `pathlib.Path(a.key)`；只是没在 argparse 里声明类型 |
| `--filter <文件名子串>` → `propose_title_from_titlepage.py` | 那是**子串**不是路径；「文件」二字撞上了正则 |

⇒ 所以本件把 **help 里提到「路径」** 也算作「有路径类型」，上面第一条因此不再报。
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

ROOT_DEFAULT = pathlib.Path(__file__).resolve().parent.parent

# 值的形状像路径
PATHY = re.compile(r"(\.json|\.zip|\.md|\.txt|目录|路径|dir\b|file\b)")
# 但这些词出现在占位符里时**不是**路径（撞过的误报）
NOT_PATHY = re.compile(r"(子串|片段|前缀|后缀|名的一部分)")


def _decl_of(sources: dict, opt: str) -> tuple[str, str] | None:
    """→ (脚本名, add_argument(...) 的声明片段)。取第一个匹配。"""
    pat = re.compile(r"add_argument\(\s*['\"]" + re.escape(opt) + r"['\"](.*?)\)\s*\n", re.S)
    for name, src in sources.items():
        m = pat.search(src)
        if m:
            return name, m.group(1)
    return None


def _commands(doc_text: str) -> list[tuple[str, str]]:
    """→ [(脚本文件名, 该条命令的全文)]。**按命令行切**，不是把整篇的选项混在一起。

    ★ 这一步是 2026-08-12 写完第一版后立刻修的：第一版对每个 `--opt` 去
      **全库找第一个含它的脚本**，于是 `--output <护栏结果.json>`（属 `namesake_gate.py`）
      被拿去比 `check_handoff_commands.py`，报出 4 条假的不符。
      **判据自己犯了它要查的那个病：比的不是同一件东西。**
    """
    out = []
    # 一条命令可能跨行（行尾 `\`）
    joined = re.sub(r"\\\s*\n\s*", " ", doc_text)
    for line in joined.splitlines():
        m = re.search(r"python3\s+(\S*?([A-Za-z_][A-Za-z0-9_]*\.py))", line)
        if m:
            out.append((m.group(2), line))
    return out


def scan(doc_text: str, sources: dict) -> dict:
    missing, shape = [], []
    seen = set()
    pairs = []
    for script, line in _commands(doc_text):
        for opt, placeholder in re.findall(
                r"(--[a-z0-9-]+)\s+([<\"'][^\s>\"']*[>\"']?)", line):
            pairs.append((script, opt, placeholder))
    for script, opt, placeholder in pairs:
        if (script, opt, placeholder) in seen:
            continue
        seen.add((script, opt, placeholder))
        found = _decl_of({script: sources[script]} if script in sources else {}, opt)
        if found is None:
            missing.append({"脚本": script, "选项": opt, "占位符": placeholder,
                            "★": ("**这个脚本里没有这个选项**"
                                  if script in sources else
                                  f"**找不到脚本 {script}**（可能是文档里的相对路径写法变了）")})
            continue
        name, decl = found
        looks_path = bool(PATHY.search(placeholder)) and not NOT_PATHY.search(placeholder)
        # ★ 判「这个选项收不收路径」要**放宽**，否则报出的是「脚本没声明类型」而不是「文档写错」。
        #   2026-08-12 第二版实测：只看 `type=Path` 或 help 含「路径」，会报出 4 条——
        #   `--workspace <工作区目录>`（help「人物工作区（含 evals/cases.jsonl）」）、
        #   `--candidate <候选答案.json>`（help「{case_id: 候选答案} 的 JSON」）等——
        #   **这些文档都是对的**，只是脚本没写 `type=pathlib.Path`。
        #   ⇒ 本件要抓的是**文档写错**，不是**声明不够精确**。所以 help 里只要出现
        #     工作区／目录／文件／JSON／路径／dir／file 这类词，就认它收路径。
        #   ★ 反验：`--identity` 的 help 是 `single primary identity, 1-12 or name`，
        #     **一个都不含**，所以那个真实的坑仍然抓得到。
        has_path = bool(re.search(
            r"(Path|type=pathlib|路径|工作区|目录|文件|JSON|json|dir\b|file\b|\.zip)", decl))
        if looks_path and not has_path:
            shape.append({"选项": opt, "占位符": placeholder, "脚本": name,
                          "声明": decl.strip()[:110],
                          "★": "**文档给的是路径形状，而这个选项既无 Path 类型、help 也不提路径**"})
    return {"检查的配对": len(seen),
            "**文档用了而脚本没有的选项**": missing,
            "**值的形状对不上的**": shape}


def check(root: pathlib.Path, doc: pathlib.Path) -> int:
    if not doc.is_file():
        print(f"· 找不到 {doc}——**未核（不是通过）**")
        return 0
    text = doc.read_text(encoding="utf-8", errors="replace")
    # 只看「怎么跑」那一节；找不到就整篇（并说出来）
    i = text.find("## 3. 怎么跑")
    j = text.find("## 4.", i + 1) if i >= 0 else -1
    if i >= 0 and j > i:
        text, scope = text[i:j], "「## 3. 怎么跑」那一节"
    else:
        scope = "**整篇**（没找到「## 3. 怎么跑」小节）"
    # ★★ 射程：**不能只扫本技能目录**。必读里那条
    #   `python3 .../persona-distiller-group/scripts/validate_group.py --registry-root <…>`
    #   属于**同级的另一个技能**，只扫 persona-distiller 会把它报成「找不到脚本」——
    #   而文档是对的。**今天已经栽过一次射程漏扫**（check_paper_lanes 的 glob 只认一层）。
    roots = [root]
    sibling = root.parent / "persona-distiller-group"
    if sibling.is_dir():
        roots.append(sibling)
    # ★★★ 2026-08-14 第三处同形：START-HERE 给收件人的重建命令是
    #   `fetch_ia.py --ids-file … --out … --skip-existing`，而 `fetch_ia.py` 住在
    #   `skill_log_evals/persona-distiller/_ledgers/_pipeline/`——**不在本技能目录下**。
    #   只扫技能目录会把它报成「找不到脚本」，**而文档是对的**（三个参数手工核过都在）。
    #   与上面那条兄弟技能同一个病：**判据扫的集合比实况小**。
    pipeline = root.parent.parent.parent / "skill_log_evals/persona-distiller/_ledgers/_pipeline"
    if pipeline.is_dir():
        roots.append(pipeline)
    sources = {}
    for r in roots:
        for f in sorted(r.rglob("*.py")):
            try:
                sources.setdefault(f.name, f.read_text(encoding="utf-8", errors="ignore"))
            except OSError:
                continue
    res = scan(text, sources)
    print(f"扫的范围：{scope}｜脚本 {len(sources)} 份｜检查了 {res['检查的配对']} 个「选项+占位符」配对")
    bad = res["**文档用了而脚本没有的选项**"] + res["**值的形状对不上的**"]
    for x in bad:
        print(f"  ✗ {x['选项']} {x['占位符']}"
              + (f" → {x['脚本']}" if "脚本" in x else "") + f"　{x['★']}")
        if "声明" in x:
            print(f"      声明：{x['声明']}")
    if bad:
        print(f"\n**{len(bad)} 条对不上**——**只报不拦**：占位符是给人读的，措辞会有出入，"
              "**逐条读了再改**。")
        return 1
    # ★★ 同上：**0 个配对时「一致」恒真**。实测喂无关文档 → 照印 ✓、rc=0。
    if not res["检查的配对"]:
        print("\n⚠ **一个「选项+占位符」配对都没扫到 —— 本次未核，不是通过。**")
        return 0
    print("\n✓ 全部 **%d** 个配对的参数形状与脚本一致" % res["检查的配对"])
    return 0


def self_test() -> int:
    bad = []
    SRC = {
        # 只收族号，没有 Path、help 也不提路径 —— 正是 --identity 那个坑
        "init_target.py": "ap.add_argument('--identity', required=True, "
                          "help='single primary identity, 1-12 or name.')\n",
        # 有 Path 类型
        "namesake_gate.py": "ap.add_argument('--output', type=pathlib.Path, help='写结果')\n",
        # 没有 Path 但 help 说了「路径」—— 不该报（`--key` 那个误报）
        "assemble.py": 'ap.add_argument("--key", help="盲判 key 的路径；默认取 round-dir")\n',
    }

    def one(doc):
        return scan(doc, SRC)

    # A ★ 回归 2026-08-12 那个真实的坑
    r = one("python3 scripts/init_target.py --identity <identity.json> --output <x.json>")
    hit = [x["选项"] for x in r["**值的形状对不上的**"]]
    if hit != ["--identity"]:
        bad.append(f"A·`--identity <identity.json>` 未被判为形状不符（实得 {hit}）")

    # B 正对照：改成族号就不许报
    r = one("python3 scripts/init_target.py --identity 7 --output <x.json>")
    if r["**值的形状对不上的**"]:
        bad.append(f"B·`--identity 7` 不该报（实得 {r['**值的形状对不上的**']}）")

    # C ★ 误报防线一：help 里提到「路径」的，不许报
    r = one('python3 scripts/assemble.py --key <盲态key.json>')
    if r["**值的形状对不上的**"]:
        bad.append("C·help 写了「路径」的 --key 被误报")

    # D ★ 误报防线二：「子串」不是路径
    SRC2 = dict(SRC, propose="ap.add_argument('--filter', help='文件名的一部分')\n")
    r = scan("python3 x.py --filter <文件名子串>", SRC2)
    if r["**值的形状对不上的**"]:
        bad.append("D·「文件名子串」被当成路径")

    # E 选项根本不存在 → 归到另一栏
    r = one("python3 x.py --nonexistent-flag <x.json>")
    if [x["选项"] for x in r["**文档用了而脚本没有的选项**"]] != ["--nonexistent-flag"]:
        bad.append("E·文档用了而脚本没有的选项未被抓出")

    # F ★★ 真跑一遍 `check()`（今天立的规矩：自测要走到判定函数）
    import contextlib
    import io
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td) / "skill"
        (root / "scripts").mkdir(parents=True)
        (root / "scripts" / "init_target.py").write_text(SRC["init_target.py"], encoding="utf-8")
        doc = pathlib.Path(td) / "H.md"
        doc.write_text("## 3. 怎么跑\n\npython3 scripts/init_target.py --identity <identity.json>\n\n## 4. 下一节\n",
                       encoding="utf-8")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = check(root, doc)
        out = buf.getvalue()
        if rc != 1 or "--identity" not in out:
            bad.append(f"F·check() 没抓到（rc={rc}）")
        if "怎么跑" not in out:
            bad.append("F′·check() 没说清扫的是哪一节")
        # F″ 文档不存在 → 明说「未核」
        buf2 = io.StringIO()
        with contextlib.redirect_stdout(buf2):
            check(root, pathlib.Path(td) / "nope.md")
        if "未核" not in buf2.getvalue():
            bad.append("F″·文档不存在时没有明说「未核（不是通过）」")

    for b in bad:
        print(f"✗ {b}")
    if bad:
        print(f"负对照未过：{len(bad)} 项")
        return 1
    print("负对照通过：A 回归真实的坑｜B 正对照｜C help 提路径不误报｜"
          "D「子串」不误报｜E 选项不存在｜F **真跑 check() 并说清范围**")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="文档里给的命令，参数形状与脚本对不对得上")
    ap.add_argument("--root", type=pathlib.Path, default=ROOT_DEFAULT)
    ap.add_argument("--doc", type=pathlib.Path, default=None,
                    help="默认找 worktree 根的 HANDOFF.md")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.doc:
        return check(a.root, a.doc)
    # ★ 默认扫**三份**：START-HERE、HANDOFF 与 `_每次开工必读.md`——
    #   接手方读的是这三份（START-HERE 是入口），只核一份等于三分之一条防线。
    wt = ROOT_DEFAULT.parent.parent.parent.parent
    # ★★ 2026-08-14 加上 START-HERE.md：**它才是收件人最先读的那一份**（移交入口）。
    #   原注释写「接手方读的就是这两份」——那句话在 START-HERE 存在之后就不成立了。
    docs = [wt / "START-HERE.md",
            wt / "HANDOFF.md",
            (ROOT_DEFAULT.parent.parent.parent
             / "skill_log_evals/persona-distiller/_ledgers/_每次开工必读.md")]
    rc = 0
    for d in docs:
        print(f"── {d.name}")
        rc = max(rc, check(a.root, d))
        print()
    return rc


if __name__ == "__main__":
    sys.exit(main())
