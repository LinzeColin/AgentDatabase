#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""语料不进 git —— **唯一一份**「什么算语料」的判据。

为什么要有这份文件
------------------
2026-08-14 pre-push 钩子拦下 **2,250 MB**，其中 **1,993 MB 是语料正文**。
根因不是「忘了写规则」，是规则**只活在 .gitignore 里、而且写错了两个维度**：

  ① 按层数写 —— `*/*/raw/*.txt`（两层）、`*/workspaces/*/raw/*.txt`（三层），
     两条都盖不住一层的 `wip-koch-107/raw/`，也盖不住 `raw/src-XXXX/` 再套一层的
     Adams #131（3,773 份）。
  ② 放错树 —— 规则在 `_corpora/.gitignore`，而语料还落在 `_ledgers/_corpora/`。

.gitignore 只在**加文件时**起作用，它不会回答「现在仓里有没有语料」。
这份判据回答那个问题，并且和 .gitignore **必须逐条一致** —— 两把尺子迟早对不上。
[[i-built-a-second-ruler-while-the-authoritative-one-sat-in-scripts]]

用法
----
    python3 check_corpus_not_in_git.py --self-test     # 正反例（`--selftest` 亦可）
    python3 check_corpus_not_in_git.py --check         # 扫全仓，rc=1 表示有语料在册
    python3 check_corpus_not_in_git.py --agree         # 核 .gitignore ⇄ 本判据是否一致

★ 取路径一律 `-z`。`git ls-files` / `ls-tree` 给非 ASCII 路径**加引号**，
  不带 `-z` 时路径结尾多一个 `"`，按扩展名判会整批漏掉。
  本判据第一版就是这样多报了 154 个「误挡」。
  [[git-ls-files-quotes-non-ascii-paths]]
"""
import argparse
import posixpath
import subprocess
import sys

# 与 persona-distiller/.gitignore 一一对应；改这里必须同步改那里，并跑 --agree。
CORPUS_EXT = (".txt", ".xml", ".pdf", ".djvu", ".html", ".htm", ".tar.gz", ".zip")
ARCHIVE_EXT = (".tar.gz", ".tgz", ".zip")
# raw/ 下这几个是**指针**，必须留下 —— 重建语料全靠它们
RAW_KEEP_PREFIX = ("_ids", "_fetch-manifest")


def is_corpus(path):
    """path 为仓相对路径（str）。True = 语料/抓取暂存，不该进 git。"""
    if "/_corpora/" not in path:
        return False
    base = posixpath.basename(path)
    low = path.lower()

    # ① raw/ 下的正文（任意层数）
    if "/raw/" in path:
        if base.startswith(RAW_KEEP_PREFIX):
            return False
        if low.endswith(CORPUS_EXT):
            return True

    # ② 归一化正文（raw 的派生副本，体量与 raw 同级）
    if "/references/sources/" in path or "/references/holdout/" in path:
        if base.startswith(RAW_KEEP_PREFIX) or base.endswith((".json", ".jsonl")):
            return False
        if low.endswith(CORPUS_EXT):
            return True

    # ③ 抓取暂存区
    if "/_fetch-staging" in path:
        if base.startswith(RAW_KEEP_PREFIX) or base.endswith((".json", ".jsonl")):
            return False
        if low.endswith(CORPUS_EXT):
            return True

    # ④ 复算出来的语料副本（校验和对不上那批）
    #    ★ 只判正文 —— 同目录的 README.md 是「55 份 sha256 无一相同」的唯一记录，
    #      第一版把整个目录判成语料，会连那份记录一起删掉。
    if "/_rederived_checksum_mismatch/" in path and low.endswith(CORPUS_EXT):
        return True

    # ⑤ 打包好的语料归档 —— 一个 .tar.gz 就是几百份正文
    if low.endswith(ARCHIVE_EXT):
        return True

    return False


# ── 正反例 ──────────────────────────────────────────────────────────────
POSITIVE = [
    "x/_corpora/wip-koch-107/raw/A.txt",                          # 一层（旧规则漏的）
    "x/_corpora/probe-adams-131/raw/src-0001/B.txt",              # raw 下再套一层
    "x/_corpora/w/x/raw/C.txt",                                   # 两层
    "x/_corpora/w/workspaces/x/raw/D.txt",                        # 三层
    "x/_corpora/w/workspaces/x/references/sources/s1/E.normalized.txt",
    "x/_corpora/w/workspaces/x/x/references/holdout/s2/F.normalized.txt",
    "x/_corpora/wip-sorby-133/_fetch-staging/raw-source-layers/G.txt",
    "x/_corpora/wip-x/_fetch-staging-2/H.txt",
    "x/_corpora/wip-galen-101/raw/ncbi_wt300_pdf.html",
    "x/_corpora/wip-galen-101/_rederived_checksum_mismatch/galen_tlg092_grc.txt",
    "x/_ledgers/_corpora/livermore-100/verified-by-checksum/raw/src-1/jl_1909.txt",
    "x/_ledgers/_corpora/livermore-100/corpus_newspapers_541.tar.gz",
]
NEGATIVE = [
    "x/_corpora/wip-koch-107/raw/_ids-rebuild.txt",               # 指针
    "x/_corpora/wip-koch-107/raw/_ids-final.txt",                 # 指针（通配要盖住）
    "x/_corpora/wip-koch-107/raw/_fetch-manifest.json",           # 指针
    "x/_corpora/w/workspaces/x/evidence/claims.jsonl",
    "x/_corpora/w/workspaces/x/evidence/source-ledger.jsonl",
    "x/_corpora/w/workspaces/x/persona.md",
    "x/_corpora/w/meta.json",
    "x/_corpora/wip-galen-101/_rederived_checksum_mismatch/README.md",   # ★ 唯一的记录
    "x/_ledgers/_pipeline/assign_lanes.py",
    "CodexSkills/registry/codex/persona-distiller/SKILL.md",
    "OpenAIDatabase/data/public_raw/codex/x.jsonl",
]


def selftest():
    bad = []
    for p in POSITIVE:
        if not is_corpus(p):
            bad.append(("正例漏判", p))
    for p in NEGATIVE:
        if is_corpus(p):
            bad.append(("反例误判", p))
    for kind, p in bad:
        print("  ✗ %s: %s" % (kind, p))
    n = len(POSITIVE) + len(NEGATIVE)
    print("自测 %d/%d" % (n - len(bad), n))
    return 1 if bad else 0


def tracked_paths():
    out = subprocess.run(["git", "ls-files", "-z"], capture_output=True).stdout
    return [p.decode("utf-8", "surrogateescape") for p in out.split(b"\0") if p]


def check():
    """仓里现在有没有语料在册。"""
    paths = tracked_paths()
    hits = [p for p in paths if is_corpus(p)]
    print("  在册 %d 个文件，其中判为语料 **%d 个**" % (len(paths), len(hits)))
    for p in hits[:15]:
        print("    ✗ %s" % p)
    if len(hits) > 15:
        print("    …… 另有 %d 个" % (len(hits) - 15))
    if hits:
        print("\n  ⇒ 语料在册。剥离办法见 `_ledgers/_语料剥离-1993MB-2026-08-14.md`。")
        return 1
    print("  ⇒ 0 个语料在册。")
    return 0


def agree():
    """.gitignore 与本判据必须逐条一致 —— 一致才叫一把尺子。"""
    paths = tracked_paths()
    drop = [p for p in paths if is_corpus(p)]
    keep = [p for p in paths if not is_corpus(p)]

    def ignored(batch, extra=()):
        if not batch:
            return b""
        data = b"\0".join(p.encode("utf-8", "surrogateescape") for p in batch)
        return subprocess.run(
            ["git", "check-ignore", "--no-index", "-z", "--stdin", *extra],
            input=data, capture_output=True).stdout

    ig_d = set(x.decode("utf-8", "surrogateescape") for x in ignored(drop).split(b"\0") if x)
    missed = [p for p in drop if p not in ig_d]

    # 被 .gitignore 挡住却判为「该进仓」的，只有**来自本 skill 的规则**才算不一致；
    # 仓根的 `*.zip`、vendored 的 graphify-out/ 与本判据无关。
    ig_k = [x.decode("utf-8", "surrogateescape") for x in ignored(keep).split(b"\0") if x]
    over = []
    if ig_k:
        f = ignored(sorted(ig_k), ("-v",)).split(b"\0")
        for i in range(0, len(f) - 3, 4):
            src = f[i].decode("utf-8", "surrogateescape")
            if "persona-distiller" in src:
                over.append((src, f[i + 2].decode("utf-8", "surrogateescape"),
                             f[i + 3].decode("utf-8", "surrogateescape")))

    print("  判据「是语料」%6d 个 → .gitignore 挡住 %6d 个，**漏网 %d**"
          % (len(drop), len(ig_d), len(missed)))
    print("  判据「该进仓」%6d 个 → 被本 skill 的规则误挡 **%d**" % (len(keep), len(over)))
    for p in missed[:10]:
        print("    ✗ 漏网：%s" % p)
    for src, pat, p in over[:10]:
        print("    ✗ 误挡：%s  ← %s（%s）" % (p, src, pat))
    ok = not missed and not over
    print("  ⇒ %s" % ("两把尺子一致" if ok else "**不一致 —— 改了一边没改另一边**"))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", "--selftest", dest="selftest", action="store_true", help="跑正反例")
    ap.add_argument("--check", action="store_true", help="扫全仓：有没有语料在册")
    ap.add_argument("--agree", action="store_true", help="核 .gitignore 与本判据是否一致")
    a = ap.parse_args()
    if not (a.selftest or a.check or a.agree):
        ap.error("至少选一个：--selftest / --check / --agree")
    rc = 0
    if a.selftest:
        rc |= selftest()
    if a.check:
        rc |= check()
    if a.agree:
        rc |= agree()
    return rc


if __name__ == "__main__":
    sys.exit(main())
