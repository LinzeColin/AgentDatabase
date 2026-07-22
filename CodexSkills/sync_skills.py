#!/usr/bin/env python3
"""本机 Skill → GitHub 全量镜像同步引擎。

把本机所有来源的 skill（OpenAI 官方、Anthropic、自建、下载）全量镜像到
`LinzeColin/AgentDatabase` 的 `CodexSkills/`，重建索引，提交并推送。

    python3 sync_skills.py             # 正式同步
    python3 sync_skills.py --dry-run   # 只报告差异，不写不推
    python3 sync_skills.py --no-push   # 提交但不推送

设计要点
--------
1. **凭据硬门**：推送前扫描全部待提交内容，命中任何凭据值就**中止**，
   绝不把密钥推进公开仓。这是无人值守运行时最重要的一道闸。
2. **删除传播**：本机删掉的 skill，镜像里也删掉，保证 GitHub 永远等于本机现状。
3. **按来源分目录**：四个来源里有 14 个重名（其中 `agent-reach` 内容还不同），
   拍平会互相覆盖，所以用 `<来源>/<skill>/` 命名空间。
4. **幂等**：没有变化就不产生提交。
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

# ---------------------------------------------------------------- 配置

HOME = os.path.expanduser("~")

# 本机全部 skill 来源。新增来源时加在这里即可。
SOURCES = {
    "codex":        {"path": f"{HOME}/.codex/skills",         "label": "Codex 用户 Skill（自建 / 下载 / GitHub）"},
    "codex-system": {"path": f"{HOME}/.codex/skills/.system", "label": "Codex 系统 Skill（OpenAI 官方，Apache-2.0）"},
    "claude":       {"path": f"{HOME}/.claude/skills",        "label": "Claude Skill（Anthropic 侧）"},
    "agents":       {"path": f"{HOME}/.agents/skills",        "label": "Agent Skill（跨工具通用目录）"},
}

REPO = "LinzeColin/AgentDatabase"
MIRROR_DIRNAME = "CodexSkills"

EXCLUDE_DIRS = {".git", "__pycache__", "node_modules", ".venv", ".mypy_cache", ".pytest_cache"}
EXCLUDE_FILES = {".DS_Store", "Thumbs.db"}
MAX_FILE_BYTES = 95 * 1024 * 1024          # GitHub 单文件 100MB 硬限，留余量

# 凭据「值」模式。只匹配真实形态，避免把「不要写 api_key」这类句子误判。
CRED_PATTERNS = {
    "OpenAI 密钥":    re.compile(rb"sk-[A-Za-z0-9]{20,}"),
    "Anthropic 密钥": re.compile(rb"sk-ant-[A-Za-z0-9_-]{20,}"),
    "GitHub 令牌":    re.compile(rb"\b(ghp|gho|ghu|ghs)_[A-Za-z0-9]{20,}|\bgithub_pat_[A-Za-z0-9_]{20,}"),
    "AWS 密钥":       re.compile(rb"\bAKIA[0-9A-Z]{16}\b"),
    "Slack 令牌":     re.compile(rb"\bxox[baprs]-[A-Za-z0-9-]{10,}"),
    "私钥":           re.compile(rb"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "JWT":            re.compile(rb"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    "Google 密钥":    re.compile(rb"\bAIza[A-Za-z0-9_-]{35}\b"),
}

CATEGORY = {
    "前端与视觉": ["beautiful-html-templates", "html-anything", "canvas-design", "frontend-slides",
                   "theme-factory", "awesome-design-md", "awesome-design-systems", "guizang-ppt-skill",
                   "graphify", "image-enhancer", "imagegen"],
    "GSAP 动画": ["gsap-core", "gsap-frameworks", "gsap-performance", "gsap-plugins", "gsap-react",
                  "gsap-scrolltrigger", "gsap-skills", "gsap-timeline", "gsap-utils"],
    "代码分析（GitNexus）": ["gitnexus-cli", "gitnexus-debugging", "gitnexus-exploring", "gitnexus-guide",
                             "gitnexus-impact-analysis", "gitnexus-pdg-query", "gitnexus-pr-review",
                             "gitnexus-refactoring", "gitnexus-taint-analysis"],
    "工程与交付": ["verifier", "webapp-testing", "mcp-builder", "use-railway", "video-replica",
                   "goal-to-delivery-sop", "domain-dual-plane", "output-skill", "codex-dev-orchestrator",
                   "impeccable", "review-agent", "plugin-creator", "skill-creator", "skill-installer",
                   "skill-github-sync"],
    "学习与知识": ["study-project-orchestrator", "book-to-skill", "last30days", "chronicle",
                   "grill-me", "openai-docs"],
    "业务流程": ["km-bid-scout", "km-bid-discover", "km-bid-qualify", "km-bid-brief", "km-bid-evidence",
                 "km-bid-adjudicate", "km-bid-audit", "km-bid-evolve", "km-bid-lifecycle",
                 "project-cost-table-skill", "gongzi-fafang-biaozhun", "hongquan-main-contract-dws",
                 "info-fee-update", "serenity-skill"],
    "协作与通讯": ["dws", "internal-comms", "agent-reach"],
    "其他": ["codex-encrypted-backup", "gpt-tasteskill", "hatch-pet"],
}

# ---------------------------------------------------------------- 工具


def log(msg):
    print(msg, flush=True)


def run(cmd, cwd=None, check=True):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if check and p.returncode != 0:
        raise RuntimeError(f"命令失败 {' '.join(cmd)}\n{p.stdout}\n{p.stderr}")
    return p


def repo_root():
    """镜像目录的父仓库根。脚本自身位于 <repo>/CodexSkills/。"""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def walk_files(base):
    """遍历一个 skill 目录，按排除规则产出 (相对路径, 绝对路径)。"""
    for root, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for f in files:
            if f in EXCLUDE_FILES:
                continue
            full = os.path.join(root, f)
            if os.path.islink(full):
                continue
            yield os.path.relpath(full, base), full


def skill_digest(base):
    h = hashlib.sha256()
    for rel, full in sorted(walk_files(base)):
        h.update(rel.encode())
        try:
            h.update(open(full, "rb").read())
        except Exception:
            pass
    return h.hexdigest()


def parse_frontmatter(path):
    try:
        text = open(path, encoding="utf-8", errors="ignore").read()
    except Exception:
        return None, None
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, flags=re.S)
    if not m:
        h = re.search(r"^#\s+(.+)$", text, flags=re.M)
        return (h.group(1).strip() if h else None), None
    fm = m.group(1)
    name = re.search(r'^name:\s*"?(.*?)"?\s*$', fm, flags=re.M)
    desc = re.search(r"^description:\s*(.*?)(?=\n[a-zA-Z_-]+:|\Z)", fm, flags=re.S | re.M)
    d = desc.group(1).strip() if desc else None
    if d:
        d = re.sub(r"^[>|][-+]?\d*\s*", "", d)                 # YAML 块标量标记
        d = re.sub(r"\s*\n\s*", " ", d).strip().strip('"').strip("'").strip()
    return (name.group(1).strip() if name else None), d


# ---------------------------------------------------------------- 盘点


def inventory():
    """扫描全部来源，返回 {(source, slug): 本机绝对路径}。"""
    inv = {}
    for src, meta in SOURCES.items():
        base = meta["path"]
        if not os.path.isdir(base):
            log(f"  · {src}: 目录不存在，跳过（{base}）")
            continue
        names = sorted(
            d for d in os.listdir(base)
            if os.path.isdir(os.path.join(base, d)) and not d.startswith(".")
        )
        for n in names:
            inv[(src, n)] = os.path.join(base, n)
        log(f"  · {src}: {len(names)} 个")
    return inv


# ---------------------------------------------------------------- 镜像


def mirror(inv, mirror_root, dry_run=False):
    """把本机 skill 镜像进仓库，并传播删除。返回变更摘要。"""
    added, updated, removed, skipped_big = [], [], [], []

    want = {f"{src}/{slug}" for src, slug in inv}
    have = set()
    if os.path.isdir(mirror_root):
        for src in SOURCES:
            sd = os.path.join(mirror_root, src)
            if os.path.isdir(sd):
                have |= {f"{src}/{d}" for d in os.listdir(sd)
                         if os.path.isdir(os.path.join(sd, d))}

    # 删除传播：本机没有了，镜像也删掉
    for gone in sorted(have - want):
        removed.append(gone)
        if not dry_run:
            shutil.rmtree(os.path.join(mirror_root, gone), ignore_errors=True)

    for (src, slug), localpath in sorted(inv.items()):
        rel = f"{src}/{slug}"
        dest = os.path.join(mirror_root, rel)
        before = skill_digest(dest) if os.path.isdir(dest) else None

        if dry_run:
            after = skill_digest(localpath)
        else:
            if os.path.isdir(dest):
                shutil.rmtree(dest)
            os.makedirs(dest, exist_ok=True)
            for r, full in walk_files(localpath):
                try:
                    if os.path.getsize(full) > MAX_FILE_BYTES:
                        skipped_big.append(f"{rel}/{r}")
                        continue
                except OSError:
                    continue
                target = os.path.join(dest, r)
                os.makedirs(os.path.dirname(target), exist_ok=True)
                shutil.copy2(full, target)
            after = skill_digest(dest)

        if before is None:
            added.append(rel)
        elif before != after:
            updated.append(rel)

    return {"added": added, "updated": updated, "removed": removed, "skipped_big": skipped_big}


# ---------------------------------------------------------------- 凭据硬门


def credential_gate(mirror_root):
    """扫描镜像内容。命中即返回明细 —— 调用方必须据此中止。"""
    hits = []
    for root, dirs, files in os.walk(mirror_root):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for f in files:
            p = os.path.join(root, f)
            try:
                if os.path.getsize(p) > 20 * 1024 * 1024:
                    continue
                data = open(p, "rb").read()
            except Exception:
                continue
            for label, pat in CRED_PATTERNS.items():
                if pat.search(data):
                    hits.append((os.path.relpath(p, mirror_root), label))
    return hits


# ---------------------------------------------------------------- 索引


def build_index(mirror_root):
    skills = []
    for src in SOURCES:
        sd = os.path.join(mirror_root, src)
        if not os.path.isdir(sd):
            continue
        for slug in sorted(os.listdir(sd)):
            d = os.path.join(sd, slug)
            if not os.path.isdir(d):
                continue
            name, desc = parse_frontmatter(os.path.join(d, "SKILL.md"))
            n = size = 0
            for root, dirs, fs in os.walk(d):
                dirs[:] = [x for x in dirs if x not in EXCLUDE_DIRS]
                for f in fs:
                    n += 1
                    try:
                        size += os.path.getsize(os.path.join(root, f))
                    except Exception:
                        pass
            skills.append({
                "slug": slug,
                "source": src,
                "name": name or slug,
                "description": desc or "",
                "category": next((c for c, v in CATEGORY.items() if slug in v), "其他"),
                "entry": f"{src}/{slug}/SKILL.md",
                "file_count": n,
                "size_bytes": size,
            })

    with open(os.path.join(mirror_root, "index.json"), "w", encoding="utf-8") as f:
        json.dump({
            "schema": "codex_skills_index.v2",
            "sources": {k: v["label"] for k, v in SOURCES.items()},
            "skill_instance_count": len(skills),
            "unique_slug_count": len({s["slug"] for s in skills}),
            "skills": skills,
        }, f, ensure_ascii=False, indent=2)

    total = sum(s["size_bytes"] for s in skills)
    uniq = len({s["slug"] for s in skills})
    raw = "https://raw.githubusercontent.com/" + REPO + "/main/" + MIRROR_DIRNAME
    out = [
        "# CodexSkills",
        "",
        f"本机全部 Skill 的仓库镜像：**{len(skills)} 份实例 / {uniq} 个不同名字**，"
        f"{sum(s['file_count'] for s in skills)} 个文件，约 {total/1048576:.0f} MB。",
        "",
        "**由 `sync_skills.py` 自动生成，请勿手工编辑本文件。**",
        "",
        "## 来源",
        "",
        "| 目录 | 本机路径 | 说明 |",
        "|---|---|---|",
    ]
    for k, v in SOURCES.items():
        cnt = len([s for s in skills if s["source"] == k])
        out.append(f"| `{k}/` | `{v['path'].replace(HOME, '~')}` | {v['label']}（{cnt} 个） |")
    out += [
        "",
        "有多个 skill 在不同来源里重名（其中 `agent-reach` 两处内容还不同），"
        "所以镜像按来源分目录，**不拍平**。",
        "",
        "## 给 LLM / Agent 的用法",
        "",
        "```bash",
        "# 1. 读机器索引，按 description 匹配需求",
        f"curl -s {raw}/index.json",
        "",
        "# 2. 只拉命中的那一个入口，不要整仓 clone",
        f"curl -s {raw}/<source>/<slug>/SKILL.md",
        "```",
        "",
        "把用户请求与 `index.json` 里各 skill 的 `description` 做匹配，命中就读它的 `entry`，"
        "再按 `SKILL.md` 的指示按需读该目录下的参考文件。**不要一次性加载全部 skill。**",
        "",
        "## 同步",
        "",
        "本目录由本机镜像而来，排除嵌套 `.git`、`.DS_Store`、`__pycache__`、`node_modules` "
        f"和超过 {MAX_FILE_BYTES // 1048576}MB 的文件。**同步方向永远是本机 → 仓库**，"
        "本机删掉的 skill 镜像里也会删掉。",
        "",
        "```bash",
        "python3 CodexSkills/sync_skills.py            # 正式同步",
        "python3 CodexSkills/sync_skills.py --dry-run  # 只看差异",
        "```",
        "",
        "推送前有一道**凭据硬门**：扫到任何密钥、令牌或私钥就中止，绝不自动推进公开仓。",
        "",
    ]
    for cat in CATEGORY:
        rows = [s for s in skills if s["category"] == cat]
        if not rows:
            continue
        out += [f"## {cat}（{len(rows)}）", "", "| Skill | 来源 | 何时使用 |", "|---|---|---|"]
        for s in sorted(rows, key=lambda x: (x["slug"], x["source"])):
            d = s["description"].replace("|", "\\|")
            if len(d) > 260:
                d = d[:260].rstrip() + "…"
            out.append(f"| [`{s['slug']}`]({s['entry']}) | `{s['source']}` | {d or '（未填写描述）'} |")
        out.append("")

    listed = {x for v in CATEGORY.values() for x in v}
    orphan = sorted({s["slug"] for s in skills} - listed)
    if orphan:
        out += ["## ⚠️ 未归类", "",
                "下列 skill 不在 `sync_skills.py` 的分类表里，已归入「其他」，请补分类：", ""]
        out += [f"- `{s}`" for s in orphan] + [""]

    open(os.path.join(mirror_root, "README.md"), "w", encoding="utf-8").write("\n".join(out))
    return len(skills), uniq, orphan


# ---------------------------------------------------------------- 主流程


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="只报告差异，不写不提交不推送")
    ap.add_argument("--no-push", action="store_true", help="提交但不推送")
    args = ap.parse_args()

    root = repo_root()
    mirror_root = os.path.join(root, MIRROR_DIRNAME)

    log("=== 1/6 盘点本机 skill ===")
    inv = inventory()
    if not inv:
        log("没有找到任何 skill，中止（这多半是路径问题，不是真的没有）。")
        return 2
    log(f"  合计 {len(inv)} 份实例 / {len({s for _, s in inv})} 个不同名字")

    log("\n=== 2/6 镜像与删除传播 ===")
    ch = mirror(inv, mirror_root, dry_run=args.dry_run)
    for k, label in [("added", "新增"), ("updated", "修改"), ("removed", "删除")]:
        if ch[k]:
            log(f"  {label} {len(ch[k])}：")
            for x in ch[k][:20]:
                log(f"    - {x}")
            if len(ch[k]) > 20:
                log(f"    …… 另有 {len(ch[k]) - 20} 个")
    if ch["skipped_big"]:
        log(f"  ⚠️ 因超过 {MAX_FILE_BYTES // 1048576}MB 被跳过 {len(ch['skipped_big'])} 个文件：")
        for x in ch["skipped_big"][:10]:
            log(f"    - {x}")
    if not any(ch[k] for k in ("added", "updated", "removed")):
        log("  本机与仓库一致，无变化")

    if args.dry_run:
        log("\n--dry-run：到此为止，未写入任何内容。")
        return 0

    log("\n=== 3/6 凭据硬门 ===")
    hits = credential_gate(mirror_root)
    if hits:
        log(f"  ✗ 命中 {len(hits)} 处，**已中止，未提交未推送**：")
        for p, label in hits[:30]:
            log(f"    - [{label}] {p}")
        log("\n  处理方式：从对应 skill 里删掉凭据（改用环境变量或外部配置），再重跑同步。")
        log("  仓库是公开的，这道门不允许绕过。")
        return 1
    log("  ✓ 0 命中")

    log("\n=== 4/6 重建索引 ===")
    n, uniq, orphan = build_index(mirror_root)
    log(f"  index.json / README.md 已生成：{n} 份实例 / {uniq} 个名字")
    if orphan:
        log(f"  ⚠️ {len(orphan)} 个 skill 未归类，已在 README 末尾列出：{orphan}")

    log("\n=== 5/6 提交 ===")
    run(["git", "add", "-A", MIRROR_DIRNAME], cwd=root)
    st = run(["git", "status", "--porcelain", MIRROR_DIRNAME], cwd=root).stdout.strip()
    if not st:
        log("  无差异，不产生提交")
        return 0

    parts = []
    for k, label in [("added", "新增"), ("updated", "更新"), ("removed", "删除")]:
        if ch[k]:
            parts.append(f"{label} {len(ch[k])}")
    subject = "chore(skills): 同步本机 Skill 到仓库" + ("（" + "，".join(parts) + "）" if parts else "")
    body = [subject, "", f"来源：{'、'.join(SOURCES)}", f"实例 {n} 份 / 名字 {uniq} 个", ""]
    for k, label in [("added", "新增"), ("updated", "更新"), ("removed", "删除")]:
        if ch[k]:
            body.append(f"{label}：")
            body += [f"  - {x}" for x in ch[k]]
            body.append("")
    body.append("凭据扫描：0 命中。由 CodexSkills/sync_skills.py 自动执行。")
    run(["git", "commit", "-q", "-m", "\n".join(body)], cwd=root)
    sha = run(["git", "rev-parse", "--short", "HEAD"], cwd=root).stdout.strip()
    log(f"  已提交 {sha}")

    log("\n=== 6/6 推送 ===")
    if args.no_push:
        log("  --no-push：已跳过")
        return 0
    run(["git", "fetch", "origin", "--quiet"], cwd=root, check=False)
    local_base = run(["git", "rev-parse", "HEAD~1"], cwd=root).stdout.strip()
    remote = run(["git", "rev-parse", "origin/main"], cwd=root).stdout.strip()
    if remote != local_base:
        log("  ✗ 远端已变化，未推送。请先 `git pull --rebase origin main` 再重跑。")
        return 1
    run(["git", "push", "origin", "HEAD:main"], cwd=root)
    log(f"  已推送到 {REPO} main")
    log(f"\n完成。索引：https://github.com/{REPO}/blob/main/{MIRROR_DIRNAME}/README.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
