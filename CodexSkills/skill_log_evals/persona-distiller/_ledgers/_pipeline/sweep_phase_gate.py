#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把某一道门跑遍一批工作区，并**把口径印在每一行上**。

为什么要有它
------------
2026-08-17 我手工做了这件事（32 个未判分工作区跑 `--phase research`），
一天之内**同一份台账订正了四次，四次都是口径错**：

    ① 用 `re.findall` 的**出现次数**当工作区数
       —— `source-unclaimed` 报成 22 个工作区，真值 **4** 个
    ② 分母里混着 **7 个根本没被检查**的工作区（缺 SKILL.md ⇒ 拒检）
       —— 我据此发布「32/32 不通过」，真话是 25 个里 25 个
    ③ 把「**未核**」当成「违规」
       —— 22 个报 holdout 重合，真话是「定位不到正文，核不了」，全库真重合 **0** 条
    ④ 把 `warnings` 混进「错误码分布」
       —— `title-is-just-the-filename` 12 是**警告**不是硬错

四条都不是「不小心」，是**每次手写统计都要重新记住四条规矩**。
会重复的手工动作迟早会漏第 5 次。[[tool-existed-and-i-did-it-by-hand]]｜
[[counts-need-their-cutoff-stated]]｜[[every-requirement-needs-an-owner]]

它保证什么
----------
1. **单位**：按**工作区**去重计数，同时并列「出现次数」，两个数一起印；
2. **分母**：拒检的（`refused=true`）单列，**不进分母**，并印出它们是谁；
3. **严重度**：`errors` 与 `warnings` 分两张表，绝不合并；
4. **冻结**：`results.jsonl` 非空的按 ㊵ 跳过，并印出跳了几个；
5. **只读**：跑完自查 `git status --porcelain`，有写盘就**报红退出**。

用法
----
    python3 sweep_phase_gate.py --phase research            # 默认只跑未判分的
    python3 sweep_phase_gate.py --phase research --include-frozen
    python3 sweep_phase_gate.py --self-test

退出码：0 = 跑完（**门本身红不红不影响本工具的 rc**，它是统计器不是门）；
        2 = 跑的过程中有工作区被写盘（严重）；3 = 用法错误。
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent


def _repo_root(start: pathlib.Path) -> pathlib.Path:
    """往上找 `.git`，**不按层数写**。[[a-rule-in-a-doc-has-no-enforcer]]"""
    for cand in [start] + list(start.parents):
        if (cand / ".git").exists():
            return cand
    return start


ROOT = _repo_root(HERE)
QC = ROOT / "CodexSkills/registry/codex/persona-distiller/scripts/quality_check.py"
CORPORA = ROOT / "CodexSkills/skill_log_evals/persona-distiller/_corpora"


def is_scored(wip: pathlib.Path) -> bool:
    """㊵：`results.jsonl` 非空 = 已判分 = 冻结。**空文件不算已判分**。"""
    return any(p.stat().st_size > 0 for p in wip.rglob("results.jsonl"))


def workspaces(corpora: pathlib.Path, include_frozen: bool):
    """→ [(wip 名, 工作区目录, 是否冻结)]

    ★★★ 2026-08-17 修：**第一版自己写了 `wip-*/workspaces/*` 这个 glob，
    而仓里早有 `workspace_roots.iter_workspaces` 专门干这件事。**
    实测差别（54 vs 53，且不是差一个那么简单）：

      · **3 个我完全没看见** —— 它们不叫 `workspaces/`：
          wip-godin/ws-godin/seth-godin
          wip-jenner-104/ws-jenner/ws-jenner
          wip-steinhardt-98/ws-steinhardt/michael-steinhardt
      · **8 个是「名字重复一层」**（`wip-X/workspaces/Y/Y`），我指的是**外层**：
          barton／blackstone／fleming／holmes／nightingale／osler／sorby／virchow

    `iter_workspaces` 的判据是「**哪一级有 `evidence/source-ledger.jsonl`**」——
    按**标志文件**认，不按目录名认。[[tool-existed-and-i-did-it-by-hand]]｜
    [[a-gates-scan-set-is-smaller-than-reality]]
    """
    sys.path.insert(0, str(HERE))
    from workspace_roots import iter_workspaces  # noqa: E402

    out = []
    seen_wip = set()
    for ws in iter_workspaces(corpora):
        # wip 名 = 相对 corpora 的第一段
        try:
            wip_name = ws.resolve().relative_to(corpora.resolve()).parts[0]
        except ValueError:
            wip_name = ws.name
        wip = corpora / wip_name
        frozen = is_scored(wip)
        seen_wip.add(wip_name)
        if frozen and not include_frozen:
            out.append((wip_name, None, True))
            continue
        out.append((wip_name, ws, frozen))
    return out


def sweep(phase: str, corpora: pathlib.Path, include_frozen: bool, qc: pathlib.Path,
          progress: bool = False):
    """★ `progress=True` 时**逐个往 stderr 打一行**。

    第一版跑完才一次性打印 —— `--phase release --include-frozen`
    在本机实测**超过 12 分钟屏幕上一个字都没有**，看着像挂住了
    （本仓刚记过「macOS 没有 timeout，rc=127 长得像挂住」——
    我自己又造了一个「长得像挂住」的东西）。
    进度走 **stderr**，表格走 stdout，重定向到文件时互不污染。
    """
    frozen_skipped, refused, checked = [], [], []
    err_ws = collections.Counter(); err_occ = collections.Counter()
    warn_ws = collections.Counter(); warn_occ = collections.Counter()

    todo = workspaces(corpora, include_frozen)
    live = [x for x in todo if x[1] is not None]
    for idx, (name, ws, frozen) in enumerate(todo, 1):
        if ws is None:
            frozen_skipped.append(name)
            continue
        if progress:
            print("  [%d/%d] %s …" % (len(checked) + len(refused) + 1, len(live),
                                      name.replace("wip-", "")),
                  file=sys.stderr, flush=True)
        p = subprocess.run([sys.executable, str(qc), str(ws), "--phase", phase],
                           capture_output=True, text=True)
        try:
            data = json.loads(p.stdout)
        except Exception:
            refused.append((name, "输出不是 JSON —— **未核，不是通过**"))
            continue
        # ★ 用产品自己给的 `refused` 位，不靠猜错误码
        if data.get("refused"):
            refused.append((name, "缺 " + "／".join(data.get("missing_required") or ["?"])))
            continue
        checked.append(name)
        e = [x["code"] for x in data.get("errors", []) if isinstance(x, dict) and "code" in x]
        w = [x["code"] for x in data.get("warnings", []) if isinstance(x, dict) and "code" in x]
        err_occ.update(e); err_ws.update(set(e))
        warn_occ.update(w); warn_ws.update(set(w))
    return frozen_skipped, refused, checked, (err_ws, err_occ), (warn_ws, warn_occ)


def _table(title: str, ws_ct: collections.Counter, occ_ct: collections.Counter, denom: int):
    print("\n【%s】%d 种" % (title, len(ws_ct)))
    if not ws_ct:
        print("   （一条都没有）")
        return
    print("   %-44s %8s %8s %8s" % ("码", "工作区", "占分母", "出现次数"))
    for code, k in ws_ct.most_common():
        pct = ("%3.0f%%" % (100 * k / denom)) if denom else "**分母0**"
        print("   %-44s %8d %8s %8d" % (code, k, pct, occ_ct[code]))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--phase", default="research")
    ap.add_argument("--corpora", type=pathlib.Path, default=CORPORA)
    ap.add_argument("--quality-check", type=pathlib.Path, default=QC)
    ap.add_argument("--include-frozen", action="store_true",
                    help="连已判分的一起跑（默认按 ㊵ 跳过）")
    ap.add_argument("--quiet", action="store_true",
                    help="不往 stderr 打逐个进度（默认打 —— 全量跑一次要十几分钟）")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.quality_check.is_file():
        print("用法错误：找不到 %s —— **未核，不是通过**" % a.quality_check, file=sys.stderr)
        return 3
    if not a.corpora.is_dir():
        print("用法错误：找不到 %s —— **未核，不是通过**" % a.corpora, file=sys.stderr)
        return 3

    # ★★ 只读自查的**射程要圈到它可能写到的地方**，不是整个仓。
    #   第一版比对的是全仓 `git status --porcelain` —— 于是**只要有人在它跑的
    #   十几分钟里提交一次（比如我自己在另一个窗口），它就会误报
    #   「跑这一趟改动了工作树」rc=2**。负对照不能把别人的改动算到自己头上。
    #   [[negative-control-must-not-share-the-assumption]]
    #   圈到语料目录：那是本工具唯一可能被写到的地方（`quality_check` 不带
    #   `--write-report` 时不写盘，但**「不写盘」正是这里要证明的事**）。
    def _snapshot():
        return subprocess.run(["git", "status", "--porcelain", "--", str(a.corpora)],
                              cwd=str(ROOT), capture_output=True, text=True).stdout

    before = _snapshot()

    frozen, refused, checked, errs, warns = sweep(
        a.phase, a.corpora, a.include_frozen, a.quality_check, progress=not a.quiet)

    denom = len(checked)
    print("门：`quality_check.py --phase %s`" % a.phase)
    print("★ **口径**：下面所有比例的分母是「**真被检查的工作区数 = %d**」。" % denom)
    print("   冻结跳过（㊵，results.jsonl 非空）：%d 个" % len(frozen))
    print("   **拒检**（门没开机，一项检查都没跑）：%d 个" % len(refused))
    for n, why in refused:
        print("       · %-24s %s" % (n.replace("wip-", ""), why))
    print("   真被检查：%d 个" % denom)

    _table("硬错 errors", *errs, denom)
    _table("警告 warnings", *warns, denom)

    after = _snapshot()
    if after != before:
        print("\n✗✗ **跑这一趟改动了语料目录** —— 统计器必须只读。差异：", file=sys.stderr)
        for ln in set(after.splitlines()) - set(before.splitlines()):
            print("    %s" % ln, file=sys.stderr)
        return 2
    print("\n✓ 只读自查：`git status --porcelain -- %s` 跑前跑后一致（**0 处写盘**）\n"
          "  ★ 射程：只圈语料目录 —— 仓里别处的改动（比如同时在提交）不算它的账。"
          % a.corpora)
    return 0


def self_test() -> int:
    """正反各钉：拒检的不进分母；警告不混进硬错；出现次数与工作区数分开。"""
    import tempfile
    ok = True

    def chk(label, got, want):
        nonlocal ok
        if got != want:
            ok = False
            print("  ✗ %s：得到 %r，应为 %r" % (label, got, want))
        else:
            print("  ✓ %s" % label)

    with tempfile.TemporaryDirectory() as td:
        base = pathlib.Path(td)
        # 假 quality_check：按工作区名给出三种形态
        fake = base / "fake_qc.py"
        fake.write_text(
            "import json,sys\n"
            "t=sys.argv[1]\n"
            "if 'refuse' in t:\n"
            "    print(json.dumps({'passed':False,'refused':True,'checks_run':0,\n"
            "                      'missing_required':['SKILL.md'],\n"
            "                      'errors':[{'code':'target.invalid'}]}));sys.exit(1)\n"
            "if 'dup' in t:\n"
            "    print(json.dumps({'passed':False,\n"
            "                      'errors':[{'code':'E1'},{'code':'E1'},{'code':'E1'}],\n"
            "                      'warnings':[{'code':'W1'}]}));sys.exit(1)\n"
            "print(json.dumps({'passed':False,'errors':[{'code':'E1'}],\n"
            "                  'warnings':[{'code':'W1'},{'code':'W2'}]}));sys.exit(1)\n",
            encoding="utf-8")
        corp = base / "_corpora"
        for nm in ("wip-refuse-1", "wip-dup-2", "wip-plain-3", "wip-frozen-4"):
            ws = corp / nm / "workspaces" / "who"
            (ws / "evidence").mkdir(parents=True)
            # ★ 夹具必须带 `evidence/source-ledger.jsonl` —— `iter_workspaces`
            #   正是**按这个标志文件**认工作区的（不按目录名）。
            #   第一版夹具没有它，于是换用 iter_workspaces 之后**一个都发现不了**，
            #   自测当场从「全过」变成「扫到 0 个」。
            #   **夹具比实况薄，就测不出实况。**[[fixtures-cleaner-than-the-real-thing]]
            (ws / "evidence/source-ledger.jsonl").write_text(
                '{"source_id":"src-000000000000","split":"train"}\n', encoding="utf-8")
            if nm == "wip-frozen-4":
                (corp / nm / "results.jsonl").write_text('{"x":1}\n', encoding="utf-8")

        frozen, refused, checked, (ew, eo), (ww, wo) = sweep(
            "research", corp, include_frozen=False, qc=fake)

        chk("冻结的被跳过（㊵）", frozen, ["wip-frozen-4"])
        chk("拒检单列、**不进分母**", [n for n, _ in refused], ["wip-refuse-1"])
        chk("分母只含真被检查的", sorted(checked), ["wip-dup-2", "wip-plain-3"])
        # ★ 同一个码在一个工作区里出现 3 次 → 工作区数 2、出现次数 4
        chk("E1 的**工作区数**", ew["E1"], 2)
        chk("E1 的**出现次数**", eo["E1"], 4)
        chk("警告没混进硬错", "W1" in ew, False)
        chk("W1 的工作区数", ww["W1"], 2)
        chk("W2 只在一个工作区", ww["W2"], 1)

        # 反对照：把 refused 那一位拿掉，拒检的就会**混进分母**——本工具须依赖它
        fake2 = base / "fake_qc2.py"
        fake2.write_text(fake.read_text(encoding="utf-8").replace("'refused':True,", ""),
                         encoding="utf-8")
        _, refused2, checked2, _, _ = sweep("research", corp, False, fake2)
        chk("反对照：无 refused 位时拒检者会落进分母", (len(refused2), len(checked2)), (0, 3))

        # ★ 进度开关：正反各一。全量跑一次十几分钟，**屏幕上没有字就等于挂住**。
        import contextlib as _c, io as _io
        _e = _io.StringIO()
        with _c.redirect_stderr(_e):
            sweep("research", corp, False, fake, progress=True)
        on = len([l for l in _e.getvalue().splitlines() if l.strip()])
        _e2 = _io.StringIO()
        with _c.redirect_stderr(_e2):
            sweep("research", corp, False, fake, progress=False)
        off = len([l for l in _e2.getvalue().splitlines() if l.strip()])
        chk("progress=True 时逐个打进度（3 个活工作区 → 3 行）", on, 3)
        chk("progress=False 时 stderr 一行都没有", off, 0)

    print("自测：%s" % ("全过" if ok else "**有失败**"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
