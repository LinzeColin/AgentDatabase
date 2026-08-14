#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""私有资产不许进公开仓 —— 推送前的判据。

为什么要有这份文件
------------------
2026-08-14：我把 `claude/character-distillation-skill-reorganize-d57595` 推上了
`LinzeColin/AgentDatabase`，**那是个 PUBLIC 仓**，随之上去的有
`_ledgers/_教训库/` 141 份 ＋ `文档/踩坑库/` 197 份，共 338 份 agent 教训。
仓自己的 `HANDOFF.md`（origin/main，来自 PR #9）早就写着这类资产不许进。
**我推之前没读那句。** 暴露约 12 分钟，已删分支。

规则本来在**文档里**，没有任何东西执行它。这份判据执行它。

★ 两条从这次踩出来的纪律：
  ① **扫描面不能只覆盖文档点名的那一个目录。** `HANDOFF.md` 只点了
     `_ledgers/_教训库/`，我按它扫完以为清了，实际还有**第二份副本**
     `文档/踩坑库/`（197 份，比第一份还多）。所以下面按**内容特征**兜底，
     不只按路径。[[a-gates-scan-set-is-smaller-than-reality]]
  ② **凭据形状会误报。** 教训文本里把 `-----BEGIN RSA PRIVATE KEY-----`
     当成「判据用的标记串」写进正文，5 处命中全是这个，**没有一处是真凭据**。
     报「N 处泄漏」之前必须把命中行打出来看。[[measurement-errors-all-point-the-same-way]]

用法
----
    python3 check_private_assets_not_public.py --self-test        # `--selftest` 亦可
    python3 check_private_assets_not_public.py --check            # 扫在册文件
    python3 check_private_assets_not_public.py --check --range origin/main..HEAD
"""
import argparse
import re
import subprocess
import sys

# ① 按路径：明确属于 private-only 的树
PRIVATE_PATH_PATTERNS = [
    re.compile(r"(^|/)_教训库/"),
    re.compile(r"(^|/)踩坑库/"),
    re.compile(r"(^|/)claude-memory/"),
    re.compile(r"(^|/)OPS/AGENT_ONBOARDING"),
]

# ② 按内容：基础设施细节。命中不等于必须拦，但必须**逐条打出来给人看**。
INFRA_PATTERNS = [
    ("内部域名", re.compile(r"[a-z0-9-]+\.linzezhang\.com")),
    ("主机/供应商", re.compile(r"\bOVH\b|\bovh\b")),
    ("服务器路径", re.compile(r"/usr/local/bin/[A-Za-z0-9._-]+")),
    ("Cloudflare 部署", re.compile(r"\bwrangler\b|\bCloudflare\b")),
    ("systemd 单元", re.compile(r"\bsystemctl\b|\.service\b")),
    ("ssh 细节", re.compile(r"\broot@|ssh -i |IdentityFile")),
]

# ③ 真凭据（严格；宽松写法会被教训文本里的标记串打中）
CREDENTIAL_PATTERNS = [
    ("GitHub PAT", re.compile(r"ghp_[A-Za-z0-9]{30,}")),
    ("GitHub fine-grained", re.compile(r"github_pat_[A-Za-z0-9_]{40,}")),
    ("OpenAI key", re.compile(r"sk-[A-Za-z0-9]{32,}")),
    ("AWS key id", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("私钥块", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
]
# 私钥块这一条**必然**被教训文本打中，所以命中后要看上下文：
# 同一行出现下列任一词，判为「在讲这个标记串」，不是泄漏。
# ★★ 2026-08-15 又被打中一次：我写来**解释这个缺陷**的台账正文
#   （「是一份测脱敏功能的**合成夹具**（`"private_key = " + "-----BEGIN …`」）
#   被判成真凭据。上一版的词表里没有「夹具／合成／脱敏」这几个词 ——
#   **说「这不是真凭据」时实际会用的词，和我当初想到的那几个不是一套。**
#   [[my-checkers-are-mis-cut-six-times-in-one-day]]
#
#   ★ 这是**放松**，代价要写明：真凭据若恰好落在「夹具」二字的邻行会被放过。
#     接受它的理由是另一侧代价更大（每写一次说明就要改一次判据），
#     并且自测里那条负对照始终在：**没有任何排除词的真凭据必须仍被抓到**。
MARKER_CONTEXT = re.compile(
    r"标记串|占位符|判据|检测|正则|pattern|placeholder|示例"
    r"|夹具|合成|假钥|脱敏|测试用|fixture|synthetic|redact")


def repo_is_public(remote="origin"):
    """现问 GitHub，不看文档。取不到返回 None（未判，不是「不是公开的」）。"""
    url = subprocess.run(["git", "remote", "get-url", remote],
                         capture_output=True, text=True).stdout.strip()
    m = re.search(r"[:/]([^/:]+/[^/]+?)(?:\.git)?$", url)
    if not m:
        return None, url
    slug = m.group(1)
    out = subprocess.run(["gh", "repo", "view", slug, "--json", "isPrivate"],
                         capture_output=True, text=True)
    if out.returncode != 0:
        return None, slug
    try:
        import json
        return (not json.loads(out.stdout)["isPrivate"]), slug
    except Exception:
        return None, slug


def repo_root():
    """★ 锚到仓根，**不许跟着 cwd 走**。

    `git ls-files` 只列 cwd 以下 —— 同一道门在子目录里跑就只看得见一小块，
    然后安安静静地绿。同型缺陷 2026-08-15 在 `check_corpus_not_in_git.py`
    上**实测到了**（仓根 15,251 个 / 502 语料 rc=1，`_pipeline/` 里 101 个 /
    0 语料 rc=**0**）。本文件是同一个代码形状，按机制一并修
    （这一处**没有单独实测**，两个 cwd 的对照跑超时了）。
    [[a-gates-scan-set-is-smaller-than-reality]]
    """
    out = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                         capture_output=True, text=True)
    return out.stdout.strip() or "."


def files_in(rng=None):
    root = repo_root()
    if rng:
        cmd = ["git", "-C", root, "diff", "--name-only", "-z", rng]
    else:
        cmd = ["git", "-C", root, "ls-files", "-z"]
    out = subprocess.run(cmd, capture_output=True).stdout
    return [p.decode("utf-8", "surrogateescape") for p in out.split(b"\0") if p]


SELF_NAME = "check_private_assets_not_public.py"


def scan(paths):
    by_path = [p for p in paths if any(r.search(p) for r in PRIVATE_PATH_PATTERNS)]
    infra, creds = {}, []
    skipped = set(by_path)
    remaining = [p for p in paths if p not in skipped]
    for p in remaining:
        # ★ 判据不扫自己。上面那三张模式表里就写着 `ssh -i`、`systemctl`、
        #   `-----BEGIN … PRIVATE KEY-----`，扫自己必然自报。
        #   第一版没写这一条，判据把自己报成「1 处真凭据 —— 不许推」。
        #   [[my-checkers-are-mis-cut-six-times-in-one-day]]
        if p.endswith(SELF_NAME):
            continue
        try:
            with open(p, "r", encoding="utf-8", errors="replace") as fh:
                lines = fh.read().splitlines()
        except (OSError, IsADirectoryError):
            continue
        text = "\n".join(lines)
        for label, rx in INFRA_PATTERNS:
            if rx.search(text):
                infra.setdefault(label, []).append(p)
        for label, rx in CREDENTIAL_PATTERNS:
            for i, line in enumerate(lines):
                if not rx.search(line):
                    continue
                # ★ 排除词要看**邻行**，不只看本行 —— 说明性文字常把
                #   「这是判据用的标记串」写在下一行，只看本行会误报。
                window = "\n".join(lines[max(0, i - 2):i + 3])
                if MARKER_CONTEXT.search(window):
                    continue
                creds.append((label, p, line.strip()[:120]))
    return by_path, infra, creds


def selftest():
    cases = [
        ("a/_教训库/x.md", True), ("文档/踩坑库/y.md", True),
        ("b/claude-memory/z.md", True), ("OPS/AGENT_ONBOARDING.md", True),
        ("CodexSkills/registry/codex/persona-distiller/SKILL.md", False),
        ("_ledgers/_pipeline/assign_lanes.py", False),
        ("_ledgers/_教训库改进记录.md", False),   # 不是目录，是同前缀的文件名
    ]
    bad = 0
    for p, want in cases:
        got = any(r.search(p) for r in PRIVATE_PATH_PATTERNS)
        if got != want:
            print("  ✗ %s 期望 %s 得 %s" % (p, want, got))
            bad += 1
    # ── 内容侧：三个正反例都在真文件上跑 scan()，不是在字符串上试正则 ──
    import os
    import tempfile
    checks = []
    with tempfile.TemporaryDirectory() as td:
        cwd = os.getcwd()
        os.chdir(td)
        try:
            # ① 真凭据、无排除词 → **必须抓到**（负对照：证明这把尺子还看得见）
            with open("leak.md", "w", encoding="utf-8") as fh:
                fh.write("deploy key:\nAKIAIOSFODNN7EXAMPLE\n")
            checks.append(("真凭据要抓到", len(scan(["leak.md"])[2]) == 1))

            # ② 同一个串，但邻行写明是标记串 → 不该报
            with open("talk.md", "w", encoding="utf-8") as fh:
                fh.write("下面这个：\n-----BEGIN RSA PRIVATE KEY-----\n它是判据里用的标记串。\n")
            checks.append(("讲标记串不该报", len(scan(["talk.md"])[2]) == 0))

            # ③ 判据自己 → 不该报（它的模式表里就写着那些串）
            with open(SELF_NAME, "w", encoding="utf-8") as fh:
                fh.write("AKIAIOSFODNN7EXAMPLE\nssh -i x\n")
            checks.append(("判据不扫自己", len(scan([SELF_NAME])[2]) == 0))
        finally:
            os.chdir(cwd)
    for name, ok in checks:
        if not ok:
            print("  ✗ %s" % name)
            bad += 1
    n = len(cases) + len(checks)
    print("自测 %d/%d" % (n - bad, n))
    return 1 if bad else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", "--selftest", dest="selftest", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--range", dest="rng", default=None,
                    help="只扫某个提交范围的改动，如 origin/main..HEAD")
    a = ap.parse_args()
    if not (a.selftest or a.check):
        ap.error("至少选一个：--selftest / --check")
    rc = 0
    if a.selftest:
        rc |= selftest()
    if a.check:
        pub, slug = repo_is_public()
        label = {True: "**PUBLIC**", False: "private", None: "**未判**（gh 取不到）"}[pub]
        print("  远端 %s → %s" % (slug, label))
        paths = files_in(a.rng)
        print("  扫描面：%d 个文件%s" % (len(paths), "（%s）" % a.rng if a.rng else "（全部在册）"))
        by_path, infra, creds = scan(paths)
        print("\n  ① 按路径判为 private-only：**%d 个**" % len(by_path))
        for p in by_path[:6]:
            print("       %s" % p)
        if len(by_path) > 6:
            print("       …… 另有 %d 个" % (len(by_path) - 6))
        print("\n  ② 基础设施细节（命中≠必须拦，逐类看）")
        for label2, ps in sorted(infra.items(), key=lambda x: -len(x[1])):
            print("       %-16s %4d 个文件，例：%s" % (label2, len(ps), ps[0]))
        if not infra:
            print("       无")
        print("\n  ③ 真凭据（已排除「在讲标记串」的行）：**%d 处**" % len(creds))
        for label2, p, line in creds[:10]:
            print("       ✗ %-18s %s\n         %s" % (label2, p, line))
        if pub and by_path:
            print("\n  ⇒ **公开仓 + private-only 资产 %d 个 —— 不许推。**" % len(by_path))
            rc |= 1
        elif creds:
            print("\n  ⇒ **有 %d 处真凭据 —— 不许推。**" % len(creds))
            rc |= 1
        else:
            print("\n  ⇒ 通过。")
    return rc


if __name__ == "__main__":
    sys.exit(main())
