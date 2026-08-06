#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**元检查器**：查「检查器自己有没有被验证过」。

## 为什么它排在全量分诊的第一位

RUNBOOK 第十八种：

> **规则：任何新写的检查器，交付前必须做一次负对照——
> 植入一个已知的坏样本，确认它真的报错。**
> **推论：没有负对照的检查器，其「全绿」不构成任何证据。**

这条推论一旦成立，它就**决定其余每一件检查器的结论算不算数**。
而这条规则本身此前**只是散文**——写在 RUNBOOK 里，靠执行者记得照做。
实测结果：12 件检查器里 **5 件从来没有负对照**，
另有 **1 件是硬门、负对照写了却跑不起来**。

**一个专门用来讲「没有负对照的检查器不算数」的项目，
自己有一半检查器没有负对照。** 这就是「记下来 ≠ 处理了」的样子。

## 三档判定

| 档 | 判据 | 含义 |
|---|---|---|
| `OK` | `--self-test` 独立可跑且退出码 0 | 结论可用 |
| `NOT-STANDALONE` | 有 `--self-test`，但还要求别的参数 | **负对照无法独立验证**——它依赖它本该独立于的那份数据 |
| `NO-SELFTEST` | 根本没有 `--self-test` | **其「全绿」不构成任何证据** |
| `FAILED` | 能跑但退出码非 0 | 负对照本身没过，结论一律不作数 |

**判据一律用退出码，不用输出串。** 七件检查器的通过标记各不相同
（`负对照通过` / `自测 5/5` / `✓ 无关文本被放过`），按串匹配必然漏判；
而且中文里「不通过」包含「通过」，v0.0.0.8 接线时已经踩过一次。

退出码：0 = 全部 OK；2 = 有 FAILED（硬）；3 = 用法错误。
**`NO-SELFTEST` 与 `NOT-STANDALONE` 只报不拦** —— 拦了会让 5 件既有检查器
当场把整条流水线堵死，违反「不因为过不了门而卡住流程」。
缺口计数逐次可见，不会被误当成通过。
"""
import re
import argparse
import ast
import json
import pathlib
import subprocess
import sys

OK = "OK"
FAILED = "FAILED"
NOT_STANDALONE = "NOT-STANDALONE"
NO_SELFTEST = "NO-SELFTEST"


def classify(path: pathlib.Path, timeout: int = 60) -> tuple[str, str]:
    """跑 `<checker> --self-test`，只按**退出码 + argparse 的报错形态**判。"""
    try:
        proc = subprocess.run([sys.executable, str(path), "--self-test"],
                              capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return FAILED, f"负对照超时（>{timeout}s）"
    err = (proc.stderr or "") + (proc.stdout or "")
    if proc.returncode == 0:
        return OK, (proc.stdout or "").strip().splitlines()[-1][:80] if proc.stdout.strip() else ""
    # argparse 的两种拒绝形态要分开——它们的含义完全不同。
    if "unrecognized arguments" in err and "--self-test" in err:
        return NO_SELFTEST, "没有 --self-test 参数"
    if "the following arguments are required" in err:
        # ★ 这里**不能**直接判成 NOT-STANDALONE。
        #   argparse 缺必填参数时**先报这一条就退出**，永远不会再报
        #   「unrecognized arguments: --self-test」——于是「压根没有 --self-test」
        #   与「有 --self-test 但还要别的参数」会落进同一个分支，含义天差地别。
        #   必须再问一次 `--help` 才能分开。
        #   （本缺陷是本检查器交付前被自己的普查结果抓到的：`grep` 说那几件
        #     源码里没有 self_test，分类器却报 NOT-STANDALONE。
        #     根因是我的负对照样本把 `--workspace` 写成了**可选**，
        #     而真实的检查器把它写成**必填**——**样本没覆盖真实形态**。）
        need = err.split("the following arguments are required:", 1)[1].strip()
        if not _has_flag(path, "--self-test"):
            return NO_SELFTEST, f"没有 --self-test（且必填：{need[:40]}）"
        return NOT_STANDALONE, f"--self-test 还要求：{need[:60]}"
    return FAILED, err.strip().splitlines()[-1][:100] if err.strip() else f"退出码 {proc.returncode}"


def _has_flag(path: pathlib.Path, flag: str) -> bool:
    """问 `--help`：这个参数到底存不存在。判源码文本会被注释与文档字符串骗到。"""
    try:
        proc = subprocess.run([sys.executable, str(path), "--help"],
                              capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired:
        return False
    return flag in (proc.stdout or "")


# ★ 真实样本夹具的标记（v0.0.0.25 新增，只报不拦）
#
# 2026-08-02 同一天里，我写的两件评分判据都**合成负对照全绿、真实数据一跑就错**：
#   ① 相关性错误评分器把三次「反驳『技术分析之父』」判成三次「主张」；
#   ② 未覆盖事实评分器把四条干净拒答判成「编造」
#      （拒答句在前、说明句在后，说明句里的 1940 被当成了婚期）。
# 两次都是**读原文**才发现的，不是判据自己发现的。
#
# 结论：**合成负对照挡不住真实数据。** 它只能证明判据在我想得到的形态上成立，
# 而判据出错的地方恰好是我想不到的形态。
#
# 因此本项普查「这件检查器的负对照里有没有至少一条来自真实产出的夹具」。
# **只报不拦**：既有检查器多数没有，硬拦会把它们一起拦下（与 NO-SELFTEST 同一条纪律）。
REAL_FIXTURE_MARKS = ("真实样本", "真实产出", "REAL_", "真实数据", "实测样本")


def _has_real_fixture(path: pathlib.Path) -> bool:
    """源码里有没有真实样本夹具的标记。

    **这一项只能判源码文本**——它问的是「有没有写下真实夹具」，
    没有别的可观测量。与 `_has_flag` 问 `--help` 不同，这里没有运行期证据可问。
    **射程必须一起说：贴个标记就能骗过它。** 它挡的是「压根没想过」，不是说谎。
    """
    try:
        src = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False
    return any(m in src for m in REAL_FIXTURE_MARKS)


def census(directory: pathlib.Path, exclude: set[str]) -> list[dict]:
    rows = []
    for path in sorted(directory.glob("check_*.py")):
        if path.name in exclude:
            continue
        verdict, detail = classify(path)
        rows.append({"checker": path.name, "verdict": verdict, "detail": detail,
                     "real_fixture": _has_real_fixture(path)})
    return rows


# ── 元负对照：本检查器自己也必须有负对照，否则它就是它自己在讲的那个问题 ──
FIXTURES = {
    "check_meta_ok.py": (
        "import argparse,sys\n"
        "p=argparse.ArgumentParser();p.add_argument('--self-test',action='store_true')\n"
        "a=p.parse_args()\n"
        "print('负对照通过（假的，只为测元检查器）')\n"
        "sys.exit(0)\n", OK),
    "check_meta_failing.py": (
        "import argparse,sys\n"
        "p=argparse.ArgumentParser();p.add_argument('--self-test',action='store_true')\n"
        "a=p.parse_args()\n"
        "print('负对照未过')\n"
        "sys.exit(2)\n", FAILED),
    "check_meta_none.py": (
        "import argparse\n"
        "p=argparse.ArgumentParser();p.add_argument('--workspace')\n"
        "p.parse_args()\n", NO_SELFTEST),
    # ★ 真实形态：**没有 --self-test，而且有必填参数**。
    #   这一档最初漏了，于是分类器把 6 件「压根没有负对照」的检查器
    #   误报成「有但不能独立跑」——两者的处置完全不同。
    #   **负对照的样本必须覆盖真实形态，否则它只验证了我想象的形态。**
    "check_meta_none_required.py": (
        "import argparse\n"
        "p=argparse.ArgumentParser()\n"
        "p.add_argument('--workspace',required=True)\n"
        "p.parse_args()\n", NO_SELFTEST),
    "check_meta_coupled.py": (
        "import argparse\n"
        "p=argparse.ArgumentParser()\n"
        "p.add_argument('--cache',required=True)\n"
        "p.add_argument('--self-test',action='store_true')\n"
        "p.parse_args()\n", NOT_STANDALONE),
}



def _code_only(text: str):
    """→ 只含**真代码**的可搜文本（丢掉注释与 docstring）；解析失败返回 None。

    注释在 AST 里本就不存在；docstring 要显式摘掉（`ast.get_docstring` 认得
    Module / ClassDef / FunctionDef / AsyncFunctionDef 四种）。
    **其余字符串常量一律保留**——真调用往往就写成 `run('check_x.py', ...)`。
    """
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return None
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = getattr(node, "body", None)
            if body and isinstance(body[0], ast.Expr) and isinstance(
                    getattr(body[0], "value", None), ast.Constant) and isinstance(
                    body[0].value.value, str):
                node.body = body[1:] or [ast.Pass()]
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            out.append(repr(node.value))
        elif isinstance(node, ast.Name):
            out.append(node.id)
        elif isinstance(node, ast.Attribute):
            out.append(node.attr)
        elif isinstance(node, ast.alias):
            out.append(node.name)
            if node.asname:
                out.append(node.asname)
    return "\n".join(out)


def duplicate_audit(directory: pathlib.Path, threshold: float = 0.12) -> dict:
    """★★★★ **有没有两件判据在做同一件事**——2026-08-06 新增。

    ## 撞出它的那一次

    我写了 `check_stance_density.py`，其中「第一人称怎么数」那一半
    **与 `check_first_person_density.py` 完全重复**：

    | | 两边都写着 |
    |---|---|
    | 裸 `\\bI\\b` 不可信 | 一个说「零件标号 `anvil I-I`」，一个说「化学式 `PbI₂`」 |
    | 要动词锚定 | `I have`／`I claim`／`I find` |
    | 要剥权利要求套语 | `What I claim`／`In testimony whereof` |
    | **撞出它的人物** | **都是 Coffin #130** |

    **我从头推了一遍它已经记着的东西，还漏掉了它有而我没有的第三类**
    （`DEICTIC`：`I have shown … in Fig. 2` 是他的字但不含主张）。

    ★ 这是「[[tool-existed-and-i-did-it-by-hand]]」当天的第三次，
      而前两次是**手工做了脚本能做的事**；**这次是写了一整个重复的判据**。

    ## 判法：比**正则字面量**的重合度，不比文件名也不比散文

    判据的身份在它的模式表里。取每件的正则常量（`re.compile` 的参数与
    形如 `r"\\b…"` 的字符串），切成 token 集合，两两算 Jaccard。

    ★★ **不比 docstring**：本项目的判据文件头都写得很长，
      主题词天然重合（「语料」「判据」「实测」），**比散文只会全是假阳**。
    ★ **不比文件名**：`check_quote_*` 有五件，各做各的。

    ## 阈值 0.12 是**拿立案案例定出来的**，不是拍的

    把 `check_stance_density` **借规则之前那一版**（提交 a8dc11e3）与
    `check_first_person_density` 放一起跑：

    | 阈值 | 立案案例 | 全库 465 个组合报出 |
    |---|---|---|
    | 0.34 | **抓不到** | 0 |
    | 0.20 | **抓不到** | 0 |
    | **0.12** | **抓到（0.166）** | **4 对** |

    ★★★ **信号很弱**（0.166 的重合度），4 对里立案案例排第 2。
    **所以它只报不拦，且必须人去读**——0.12 这个阈值离噪声不远。
    ★ 修好之后同一对**降到阈值以下**（现在是 import 不是复制），
      **这正是它该有的行为**。
    """
    import itertools
    import re
    # ★★★ **必须用 AST 取字符串常量，不能用正则去抠 `"…"`。**
    #   第一版用 `r'"((?:[^"\\]|\\.){6,})"'`，它**跨引号边界**把整段 docstring
    #   当成一个字面量抓走了——于是「共有的模式词」全是 `argparse`／`args`／`chk`
    #   这类 CLI 样板，**而它本该抓的那一对（stance_density × first_person_density）
    #   一条都没报**。判据在自己的立案案例上失败，就是没做完。
    TOK = re.compile(r"[A-Za-z]{3,}")
    LOOKS_RX = re.compile(r"\\[bswdWSD]|\[[^\]]{2,}\]|\(\?:")
    # CLI／Python 样板词——它们出现在每一件判据里，留着必然把所有对都拉到 0.4 上下
    STOP = {"self", "test", "true", "false", "none", "args", "argparse", "action",
            "store", "help", "type", "default", "print", "json", "path", "file",
            "dumps", "loads", "text", "utf", "errors", "replace", "encoding",
            "return", "def", "for", "not", "and", "the", "with", "str", "int"}
    sigs = {}
    for path in sorted(directory.glob("check_*.py")):
        # ★★ **本文件自排除。** 首跑它把自己与 `check_first_person_density` 报成
        #   0.142 重复——共有词是 `anvil`／`coffin`／`claim`／`desire`。
        #   **原因是我的自测夹具照抄了真实模式**（那是对的：正例要取自真实的那一对）。
        #   ★ 这个命中**是真的**——判据确实抓到了「有人复制了那些模式」，
        #     只是复制者是它自己的夹具。**记在这里，因为下一个人会重新纳闷一次。**
        if path.name == pathlib.Path(__file__).name:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        toks = set()
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Constant) and isinstance(node.value, str)):
                continue
            lit = node.value
            # 只收**看起来是正则**的常量：含转义类／字符组／非捕获组
            if len(lit) < 6 or not LOOKS_RX.search(lit):
                continue
            # ★★★ **用法示例串不是正则。** 首跑三对疑似里有两对全栽在这上面：
            #     `python3 check_semantic_residue.py --workspace <dir> [--extra a.json …]`
            #   那个 `[--extra …]` 的方括号被 `LOOKS_RX` 当成了字符组，
            #   于是 `python`／`workspace`／`runbook`／`dir` 成了「共有的模式词」。
            #   **判据的假阳源是它自己的取样规则，不是那两件判据。**
            if re.search(r"python3?\s|--[a-z]{2,}|\.py|RUNBOOK", lit):
                continue
            toks |= {t.lower() for t in TOK.findall(lit)} - STOP
        if len(toks) >= 8:
            sigs[path.name] = toks
    pairs = []
    for a, b in itertools.combinations(sorted(sigs), 2):
        sa, sb = sigs[a], sigs[b]
        j = len(sa & sb) / max(1, len(sa | sb))
        if j >= threshold:
            pairs.append({"甲": a, "乙": b, "重合度": round(j, 3),
                          "共有的模式词": sorted(sa & sb)[:14]})
    pairs.sort(key=lambda x: -x["重合度"])
    return {
        "比过的判据数": len(sigs),
        "**疑似重复**": pairs,
        "阈值": threshold,
        "★ 口径": ("**只报不拦。** 重合高不等于重复——`check_quote_*` 那五件"
                   "天生共用引文词表。**报出来是让人去读，不是自动判重。**"),
    }


def wiring_audit(directory: pathlib.Path) -> dict:
    """★★ **每件判据有没有生产调用方**——v0.0.0.91 新增。

    起因：2026-08-04 自查发现 **51 件判据里 7 件在生产代码里找不到任何调用方**，
    而三处所谓「被调用」实为**注释里的提及**。
    这是 v0.0.0.68「判据存在、自测全绿、文档反复引用，而从没被调用过」的复发。

    ★ **上一次是我用一个临时脚本查出来的——临时脚本不进任何门，下次照样长回来。**
    所以这一项收进元判据，跟着 `check_checkers` 一起跑。

    **只认代码里的调用**：搜 `<名>.py` 与带引号的 `<名>`，
    **排除判据自己、排除 `tests/`、排除 `references/pipeline/checkers/` 镜像**。

    ## ★★★ v0.0.0.139：那个「已知宽松处」真的漏了一件，代价是 18 份 holdout

    本函数原来在**整份文件的原文**里搜名字，于是**注释与文档字符串里的提及也算调用**。
    原注释写着「宁可漏报不误报，真出现时会像上次那样在人工复核里现形」。
    **它没有现形，是我给下一个人物找语料时随手 `ls` 撞见的。**

    `check_material_split.py` 的两处「调用」实为：
      · `scripts/check_contract_drift.py` 的一行注释
      · `scripts/check_holdout_overlap.py` 的文档字符串
    两处都在 `scripts/` 下，于是本审计报「无调用方 0 件」。
    真实后果：**45 份 holdout 里 18 份从未被隔离，6 个工作区，其中一人产物已做完。**

    **改法：用 AST 取「真代码」**——丢掉注释（AST 里本就没有）与**文档字符串**，
    只在剩下的字符串常量与标识符里搜。
    ★ 只丢 docstring，**不丢别的字符串常量**——`run('check_x.py', ...)` 那种
      正是靠字符串常量调用的，丢了会把真调用误判成没有。
    ★★ 解析失败时**退回原文搜索并单独列出**，不许静默当成通过。
    """
    root = directory.parent
    names = sorted(f.stem for f in directory.glob("check_*.py"))
    sources = {}
    for f in list(root.rglob("*.py")):
        s = str(f)
        if "/tests/" in s or "/checkers/" in s or "/_failed_checkers/" in s:
            continue
        try:
            sources[f] = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
    searchable, unparsed = {}, []
    for f, txt in sources.items():
        code = _code_only(txt)
        if code is None:
            unparsed.append(f.name)
            searchable[f] = txt              # 退回原文，但下面会单列出来
        else:
            searchable[f] = code
    dead = []
    for n in names:
        callers = [f for f, txt in searchable.items()
                   if f.stem != n and (f"{n}.py" in txt or f"'{n}'" in txt or f'"{n}"' in txt)]
        if not callers:
            dead.append(n)
    return {"判据件数": len(names), "**无生产调用方的**": len(dead), "名单": dead,
            "**解析失败退回原文搜索的**": sorted(unparsed)}


def selftest_touches_disk(directory: pathlib.Path) -> dict:
    """★ **自测有没有走过「从磁盘加载」这条路**——v0.0.0.100 新增。

    起因（2026-08-04，`check_probe_precondition`）：改完 `verdict()` 后**五条自测全过，
    真跑却是错的**。成因是 `load_years()` 会**筛掉**一类条目（在世的人，`died: null`），
    而自测**直接把构造好的字典喂给 `verdict()`，绕过了加载器**。

    ★★ **本项只报数，不判缺陷。** 30/51 这个数**不是 30 处缺陷**——
    多数加载器只是「读进来解析一下」，绕过它不丢什么。
    **真正有风险的是会做筛选的加载器**，而「有没有筛选」静态判不出来。

    所以这里给的是**一个提示**：`main()` 会读文件、而自测从不碰文件系统的那些，
    **值得在改动加载逻辑时补一条走完整路径的对照**。
    """
    import ast as _ast, re as _re
    rows = []
    for f in sorted(directory.glob("check_*.py")):
        src = f.read_text(encoding="utf-8", errors="ignore")
        try:
            tree = _ast.parse(src)
        except SyntaxError:
            continue
        fns = {n.name: n for n in _ast.walk(tree) if isinstance(n, _ast.FunctionDef)}
        st = fns.get("selftest") or fns.get("self_test")
        if not st:
            continue
        st_src = _ast.get_source_segment(src, st) or ""
        mn = fns.get("main")
        mn_src = (_ast.get_source_segment(src, mn) or "") if mn else ""
        reads = bool(_re.search(r"read_text|open\(|json\.load|is_file\(\)|glob\(|rglob\(", mn_src))
        touches = bool(_re.search(r"tempfile|TemporaryDirectory|NamedTemporary|write_text|mkdtemp", st_src))
        rows.append((f.stem, reads, touches))
    need = [n for n, r, tch in rows if r and not tch]
    return {"有自测的": len(rows),
            "main 读文件且自测碰文件系统的": sum(1 for _, r, tch in rows if r and tch),
            "**main 读文件而自测不碰文件系统的**": len(need),
            "名单": need}


def _selftest_duplicate_audit(bad: list) -> None:
    """★ `duplicate_audit` 的负对照——正例取自**真实的那一对**。"""
    import tempfile
    A = ('import re\n'
         'VERB = re.compile(r"\\bI (?:have|had|claim|find|found|prefer|desire|shown)\\b")\n'
         'BOILER = re.compile(r"(What I claim|In testimony whereof|Letters Patent)")\n'
         'NOISE = re.compile(r"\\banvil I-I\\b|\\bextensions I and J\\b")\n')
    B = ('import re\n'
         'FP = re.compile(r"\\bI (?:have|had|claim|find|found|prefer|desire|shown)\\b")\n'
         'BOIL = re.compile(r"(What I claim|In testimony whereof|Letters Patent)")\n'
         'JUNK = re.compile(r"\\banvil I-I\\b|\\bextensions I and J\\b")\n')
    C = ('import re\n'
         'YEARS = re.compile(r"\\b(?:18|19)\\d\\d\\b")\n'
         'PAGES = re.compile(r"\\bpp?\\.\\s*\\d+[-\u2013]\\d+\\b")\n'
         'ISBN = re.compile(r"\\bISBN[- ]?(?:10|13)?\\b")\n')
    def chk(label, ok):
        print(("  ✓ " if ok else "  ✗ ") + label)
        if not ok:
            bad.append("duplicate_audit：" + label)

    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        (root / "check_a.py").write_text(A, encoding="utf-8")
        (root / "check_b.py").write_text(B, encoding="utf-8")
        (root / "check_c.py").write_text(C, encoding="utf-8")
        r = duplicate_audit(root, threshold=0.12)
        pairs = {frozenset((p["甲"], p["乙"])) for p in r["**疑似重复**"]}
        chk("重复的两件被报出来",
            frozenset(("check_a.py", "check_b.py")) in pairs)
        chk("不相干的第三件不被牵连",
            not any("check_c.py" in p for p in pairs))
        # ★★ 反向对照：把 B 改成 import A（就像我实际的修法），**必须降到阈值以下**
        (root / "check_b.py").write_text(
            'import importlib.util, pathlib\n'
            '_m = None  # 借 check_a 的表，不再自备一份\n', encoding="utf-8")
        r2 = duplicate_audit(root, threshold=0.12)
        chk("改成引用之后不再报（**这正是它该有的行为**）",
            not r2["**疑似重复**"])


def self_test() -> int:
    import tempfile
    bad = []
    with tempfile.TemporaryDirectory() as tmp:
        d = pathlib.Path(tmp)
        for name, (src, _) in FIXTURES.items():
            (d / name).write_text(src, encoding="utf-8")
        rows = census(d, exclude=set())
        got = {r["checker"]: r["verdict"] for r in rows}
        for name, (_, want) in FIXTURES.items():
            actual = got.get(name)
            ok = actual == want
            print(f"  {'✓' if ok else '✗'} {name}: 期望 {want}，实得 {actual}")
            if not ok:
                bad.append(f"{name}: 期望 {want}，实得 {actual}")

        # 真实夹具探测的两向对照：上面五个假检查器都没有标记 → 必须全判 False
        if any(r["real_fixture"] for r in rows):
            bad.append("真实夹具探测误报：夹具源码里没有任何标记，却报有")
        (d / "check_meta_realfx.py").write_text(
            "# 真实样本：下面这条来自 2026-08-02 的实测产出\n"
            "import argparse,sys\n"
            "p=argparse.ArgumentParser();p.add_argument('--self-test',action='store_true')\n"
            "p.parse_args();print('ok');sys.exit(0)\n", encoding="utf-8")
        rows2 = {r["checker"]: r["real_fixture"] for r in census(d, exclude=set())}
        if not rows2.get("check_meta_realfx.py"):
            bad.append("真实夹具探测漏报：源码里有「真实样本」标记却报无")
    print("\n── duplicate_audit 负对照（正例取自真实的那一对）──")
    _selftest_duplicate_audit(bad)

    if bad:
        print("\n负对照未过：")
        for b in bad:
            print(f"  · {b}")
        return 2
    print(f"\n负对照通过（{len(FIXTURES)} 档各一例；真实夹具探测两向对照均过）")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("directory", nargs="?", help="检查器目录")
    ap.add_argument("--self-test", action="store_true", help="只跑内置元负对照")
    ap.add_argument("--json", action="store_true", help="输出 JSON 供门消费")
    a = ap.parse_args()

    if a.self_test:
        return self_test()
    if not a.directory:
        print("✗ 需要检查器目录（或只给 --self-test）", file=sys.stderr)
        return 3
    d = pathlib.Path(a.directory)
    if not d.is_dir():
        print(f"✗ 目录不存在：{d}", file=sys.stderr)
        return 3

    rows = census(d, exclude={pathlib.Path(__file__).name})
    if a.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        print(f"检查 {len(rows)} 件检查器有没有可用的负对照\n")
        for r in rows:
            mark = {OK: "✓", FAILED: "✗", NO_SELFTEST: "⚠", NOT_STANDALONE: "⚠"}[r["verdict"]]
            fx = "真实夹具" if r["real_fixture"] else "仅合成  "
            print(f"  {mark} {r['checker']:<32} {r['verdict']:<15} [{fx}] {r['detail']}")
        tally = {v: sum(1 for r in rows if r["verdict"] == v) for v in
                 (OK, FAILED, NOT_STANDALONE, NO_SELFTEST)}
        n_real = sum(1 for r in rows if r["real_fixture"])
        print(f"\n可用 {tally[OK]} / 未过 {tally[FAILED]}"
              f" / 不可独立验证 {tally[NOT_STANDALONE]} / 无负对照 {tally[NO_SELFTEST]}")
        print(f"负对照里含**真实样本**夹具的：{n_real} / {len(rows)}")
        if tally[NO_SELFTEST] or tally[NOT_STANDALONE]:
            print("\n**下面这些检查器的「全绿」不构成任何证据**（RUNBOOK 第十八种）：")
            for r in rows:
                if r["verdict"] in (NO_SELFTEST, NOT_STANDALONE):
                    print(f"  {r['checker']}  —— {r['detail']}")
        if n_real < len(rows):
            print("\n**下面这些检查器只有合成负对照**——只报不拦，但要知道它意味着什么：")
            print("  2026-08-02 一天之内，两件评分判据都是合成负对照全绿、真实数据一跑就错，")
            print("  且两次都是**读原文**才发现的。**合成负对照只证明判据在我想得到的形态上成立**，")
            print("  而它出错的地方恰好是我想不到的形态。")
            for r in rows:
                if not r["real_fixture"]:
                    print(f"  · {r['checker']}")
    # ★★★★ v0.0.0.172：**事故锚点**——今天删掉一个判据换来的一条。
    #   `check_refusal_without_substance` 自测 7 条全过（含 3 条反例），
    #   **拿 Rosenhain #138 两轮真答案一验，结果是反的**：
    #   该报的那一轮报 0 处，已改好的那一轮反而报 1 处。**当天删掉，没上线。**
    #   ★ 与上面那段「合成负对照只证明判据在我想得到的形态上成立」是同一件事，
    #     只是这次是**造判据的当天就撞上**，不是事后回查。
    #   判法：一件判据若**既不引具体人物编号、也不带实测数字**，
    #   那它很可能是想出来的而不是撞出来的。**只报不拦。**
    print("\n── 事故锚点（判据是撞出来的，还是想出来的）──")
    _NUMPAT = re.compile(r"\d+\.\d{3,4}|\d+/\d+|numFound|\b\d{2,}\s*(?:份|条|个|次)")
    _files = sorted(pathlib.Path(d).glob("check_*.py"))
    _noanchor = []
    for _p in _files:
        _doc = _p.read_text(encoding="utf-8", errors="replace")[:6000]
        if not (re.search(r"#\d{2,3}\b", _doc) or _NUMPAT.search(_doc)):
            _noanchor.append(_p.name)
    print(f"  判据 {len(_files)} 件，**既无人物编号也无实测数字的 {len(_noanchor)} 件**"
          + (f"：{_noanchor}" if _noanchor else "　✓"))
    if _noanchor:
        print("  ★ 请确认它们**在真数据上验过**——自测全过不等于有效，"
              "自测是造判据的人按自己的理解写的，真数据不是。")

    w = wiring_audit(d)
    print(f"\n── 接线审计 ──\n  判据 {w['判据件数']} 件，"
          f"**在生产代码里找不到调用方的 {w['**无生产调用方的**']} 件**")
    for n in w["名单"]:
        print(f"    · {n} —— **存在、可能自测全绿，而从没被调用过**")
    if w["名单"]:
        print("  ★ 这是 v0.0.0.68「第 9 次」那个坑；接线时必须**实跑一次**，"
              "看输出里真的出现了那一行。")

    dup = duplicate_audit(d)
    print(f"\n── 重复审计（有没有两件判据在做同一件事）──")
    print(f"  比过 {dup['比过的判据数']} 件（阈值 {dup['阈值']}），"
          f"**疑似重复 {len(dup['**疑似重复**'])} 对**")
    for pr in dup["**疑似重复**"]:
        print(f"    · {pr['重合度']:.3f}  {pr['甲']}  ×  {pr['乙']}")
        print(f"        共有的模式词：{'、'.join(pr['共有的模式词'][:8])}")
    if dup["**疑似重复**"]:
        print("  ★ **只报不拦，必须人去读**——阈值 0.12 离噪声不远；"
              "`check_quote_*` 那几件天生共用引文词表。")
    else:
        print("  ★ 0 对不等于「没有重复」——**本项只比正则字面量**，"
              "逻辑重复而模式不同的它看不见。")

    d2 = selftest_touches_disk(d.resolve())
    print(f"\n── 自测是否走过磁盘加载路径 ──")
    print(f"  有自测的 {d2['有自测的']} 件；"
          f"**main 读文件而自测不碰文件系统的 {d2['**main 读文件而自测不碰文件系统的**']} 件**")
    print("  ★ **这不是缺陷计数**——多数加载器只是读进来解析一下，绕过它不丢什么。")
    print("    真正有风险的是**会做筛选的加载器**（`check_probe_precondition.load_years` "
          "就丢掉过在世的人，自测因此全绿而真跑是错的）。")
    print("    **改动加载逻辑时，给那一件补一条走完整路径的对照。**")
    # ★★ v0.0.0.112：把那个笼统的数**收窄到真正有风险的子集**——
    #   `main` 会**遍历目录**（rglob/glob/iterdir）而自测完全不碰文件系统的那几件。
    #   风险是实证过的：`check_ocr_legibility` 第一版自测只喂字符串，
    #   main 却按 `<目录>/<目录名>.txt` 取文件，于是 **104 个目录只读了 52 个且一声不响**，
    #   而自测全绿。**字符串喂不出目录遍历的错。**
    import re as _re
    risky = []
    for _f in sorted(pathlib.Path(d).glob("check_*.py")):
        _t = _f.read_text(encoding="utf-8", errors="ignore")
        _i = max(_t.find("def self_test"), _t.find("def selftest"))
        _st = _t[_i:] if _i >= 0 else ""
        _st = _st[:_st.find("\ndef main")] if "\ndef main" in _st else _st
        if _re.search(r"\.(rglob|glob|iterdir)\(", _t) and not _re.search(
                r"tempfile|TemporaryDirectory|write_text|mkdir", _st):
            risky.append(_f.name)
    # ★★ 再往下走一步：**逐件读它取文件的方式**，把「风险」变成「已核」。
    #   我踩过的那个具体错法是「按目录名拼文件名」（`d / f"{d.name}.txt"`），
    #   它会漏掉所有不同名的文件。用通配 glob 的则没有这个问题。
    samename = []
    for _n in risky:
        _t = (pathlib.Path(d) / _n).read_text(encoding="utf-8", errors="ignore")
        if _re.search(r"/\s*f?[\"'][^\"']*\{[a-z_]*\.name\}[^\"']*[\"']", _t):
            samename.append(_n)
    print(f"  ★★ 其中**形状对得上**的（main 遍历目录、自测不碰盘）：**{len(risky)} 件**")
    for _n in risky:
        print(f"       {_n}")
    print(f"    ★★ 已逐件读过取文件方式：**{len(risky) - len(samename)}/{len(risky)} 用通配 glob**"
          f"（`*.txt`／`*.md`／`*.jsonl`／`*.json`），"
          f"**按目录名拼文件名的 {len(samename)} 件**{('：' + '、'.join(samename)) if samename else ''}。")
    print("    ★ 也就是说：**我踩过的那个具体错法，在这几件里一个都没有。**"
          "（另抽查 `check_ocr_language_death` 对 64 个 `src-*/<原名>.txt` 目录读满 64。）")
    print("    它仍是**测试覆盖的缺口**——自测测不出目录遍历的错；"
          "但**不是缺陷清单**，别把这几个名字当嫌疑人。")

    # ★★ v0.0.0.111：`VERIFICATION.md` 里那些可数的数，和仓库实况对不对得上。
    #   这份文件**自己预言过它会漂**（v0.0.0.76 的警示块），两个版本之后原样复发：
    #   判据写 51（真 54）、checksum 写 341（真 368）。**预言不是判据。**
    vc = pathlib.Path(d).resolve() / "check_verification_counts.py"
    proot = pathlib.Path(d).resolve().parent
    print("\n── VERIFICATION.md 的可数项（check_verification_counts）──")
    if not vc.is_file():
        print("  ⚠ check_verification_counts.py 不在，**未核（不是通过）**")
    else:
        r = subprocess.run([sys.executable, str(vc), str(proot)], capture_output=True, text=True)
        try:
            info = json.loads(r.stdout)
            n = info["**对不上的项数**"]
            unver = sum(1 for row in info["明细"] if "管不到" in str(row["判定"]))
            head = "✓ 比过的项全部一致" if not n else f"**对不上 {n} 项**"
            # ★ 「一致」与「没比」要写在同一行，否则 ✓ 会被读成「全清」
            print(f"  {head}；**另有 {unver} 项文中没写、本件管不到（不算通过）**")
            for row in info["明细"]:
                if row["判定"] != "✓":
                    print(f"    · {row['项']}：实况 {row['实况']}，文中 {row['文中']} —— {row['判定']}")
        except Exception as exc:
            print(f"  ⚠ 输出无法解析，**未核（不是通过）**：{exc}")

    # ★★ v0.0.0.109：抓到了、记进台账了、**却没进工作区**——同族的另一道。
    #   `check_corpus_presence` 比的是工作区自己的账本与磁盘，一份没被 ingest 的来源
    #   **在那个账本里也没有**，于是它报「齐的」。缺的那一层在上游的九列台账。
    #   实测：7 人共 16 份没进工作区，**其中 10 份是一手**
    #   （Barton 4 本日记、Blackwell 4 本日记 + 独一份手稿 + 独一份报刊撰文）。
    sb = pathlib.Path(d).resolve() / "check_staged_but_not_ingested.py"
    corp = pathlib.Path(d).resolve().parents[3] / "skill_log_evals" / "persona-distiller" / "_corpora"
    print("\n── 台账有、工作区没有（check_staged_but_not_ingested）──")
    if not sb.is_file():
        print("  ⚠ check_staged_but_not_ingested.py 不在，**未核（不是通过）**")
    elif not corp.is_dir():
        print(f"  ⚠ {corp} 不在，**未核（不是通过）**")
    else:
        r = subprocess.run([sys.executable, str(sb), str(corp)], capture_output=True, text=True)
        try:
            info = json.loads(r.stdout)
            n, prim = info["**有缺口的人物**"], info["**其中一手合计**"]
            print(f"  扫了 {info['扫了']} 个目录，**有缺口 {n} 人、共 {info['缺口合计']} 份，"
                  f"其中一手 {prim} 份**")
            for row in info["明细"]:
                if row["其中一手"]:
                    print(f"    ★ {row['人物']}：缺 {row['**没进工作区**']} 份，"
                          f"**一手 {row['其中一手']}** —— {'、'.join(row['清单'][:3])}…")
            unclear = info.get("★ 其中「说不清」的", [])
            if info["★ 两侧不齐备、没比的"]:
                print(f"  ★ 两侧不齐备、没比的 {len(info['★ 两侧不齐备、没比的'])} 个"
                      f"——**其中「说不清」的 {len(unclear)} 个**"
                      f"（其余是扁平布局／没走过抓源台账，成因已分类，不是未核）")
            for u in unclear:
                print(f"    ⚠ {u}")
        except Exception as exc:
            print(f"  ⚠ 输出无法解析，**未核（不是通过）**：{exc}")

    # ★ check_scan_reach 是同族元判据（「这道判据这次扫了几个单位？和该扫的一样多吗」），
    #   此前**从没被任何代码调用过**。它归这里管。
    # ★ 先取绝对路径：传进来的可能是相对的 `scripts/`，那样 .parent 会一路塌成 `.`
    dabs = d.resolve()
    sr = dabs / "check_scan_reach.py"
    root = dabs.parents[3] / "skill_log_evals" / "persona-distiller"
    print("\n── 语料射程审计（check_scan_reach）──")
    if not sr.is_file():
        print("  ⚠ check_scan_reach.py 不在，**射程未核（不是通过）**")
    elif not root.is_dir():
        print(f"  ⚠ 语料根 {root} 不在，**射程未核（不是通过）**")
    else:
        r = subprocess.run([sys.executable, str(sr), "--root", str(root)],
                           capture_output=True, text=True)
        for line in ((r.stdout or "") + (r.stderr or "")).splitlines()[-6:]:
            if line.strip():
                print("  " + line.strip())
    return 2 if any(r["verdict"] == FAILED for r in rows) else 0


if __name__ == "__main__":
    sys.exit(main())
