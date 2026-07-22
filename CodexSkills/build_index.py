#!/usr/bin/env python3
"""从每个 skill 的 SKILL.md frontmatter 重建索引。

用法（在 CodexSkills/ 目录下）：
    python3 build_index.py

产出：
    README.md    人读索引：分类 + 名称 + 何时使用
    index.json   机器读索引：供 Agent 检索与自动加载

skill 有增删改时重跑本脚本，保证索引不漂移。
"""

import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)

# 分类：只影响 README 的排版与阅读顺序，不改变任何 skill 内容
CATEGORY = {
    "前端与视觉": [
        "beautiful-html-templates", "html-anything", "canvas-design", "frontend-slides",
        "theme-factory", "awesome-design-md", "awesome-design-systems", "guizang-ppt-skill",
        "graphify", "image-enhancer",
    ],
    "GSAP 动画": [
        "gsap-core", "gsap-frameworks", "gsap-performance", "gsap-plugins", "gsap-react",
        "gsap-scrolltrigger", "gsap-skills", "gsap-timeline", "gsap-utils",
    ],
    "工程与交付": [
        "verifier", "webapp-testing", "mcp-builder", "use-railway", "video-replica",
        "goal-to-delivery-sop", "domain-dual-plane", "output-skill",
    ],
    "学习与知识": [
        "study-project-orchestrator", "book-to-skill", "last30days", "chronicle",
    ],
    "业务流程": [
        "km-bid-scout", "km-bid-discover", "km-bid-qualify", "km-bid-brief", "km-bid-evidence",
        "km-bid-adjudicate", "km-bid-audit", "km-bid-evolve", "km-bid-lifecycle",
        "project-cost-table-skill", "gongzi-fafang-biaozhun", "hongquan-main-contract-dws",
        "info-fee-update", "serenity-skill",
    ],
    "协作与通讯": [
        "dws", "internal-comms", "agent-reach",
    ],
    "其他": [
        "codex-encrypted-backup", "gpt-tasteskill", "hatch-pet",
    ],
}


def parse_frontmatter(path):
    """取 SKILL.md 的 YAML frontmatter 里的 name 与 description。"""
    try:
        text = open(path, encoding="utf-8", errors="ignore").read()
    except Exception:
        return None, None
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, flags=re.S)
    if not m:
        # 没有 frontmatter：退回用第一个标题当名字
        h = re.search(r"^#\s+(.+)$", text, flags=re.M)
        return (h.group(1).strip() if h else None), None
    fm = m.group(1)
    name = re.search(r'^name:\s*"?(.*?)"?\s*$', fm, flags=re.M)
    desc = re.search(r'^description:\s*(.*?)(?=\n[a-zA-Z_-]+:|\Z)', fm, flags=re.S | re.M)
    d = desc.group(1).strip() if desc else None
    if d:
        # YAML 折叠/字面块标记（> 或 | 及其 chomping 后缀）不属于描述正文
        d = re.sub(r"^[>|][-+]?\d*\s*", "", d)
        d = re.sub(r"\s*\n\s*", " ", d).strip().strip('"').strip("'").strip()
    return (name.group(1).strip() if name else None), d


skills = []
for slug in sorted(os.listdir(".")):
    if not os.path.isdir(slug):
        continue
    sk = os.path.join(slug, "SKILL.md")
    if not os.path.exists(sk):
        continue
    name, desc = parse_frontmatter(sk)
    files = sum(len(f) for _, _, f in os.walk(slug))
    size = 0
    for root, _, fs in os.walk(slug):
        for f in fs:
            try:
                size += os.path.getsize(os.path.join(root, f))
            except Exception:
                pass
    cat = next((c for c, v in CATEGORY.items() if slug in v), "其他")
    skills.append({
        "slug": slug,
        "name": name or slug,
        "description": desc or "",
        "category": cat,
        "entry": f"{slug}/SKILL.md",
        "file_count": files,
        "size_bytes": size,
    })

# ---- index.json ----
with open("index.json", "w", encoding="utf-8") as f:
    json.dump({
        "schema": "codex_skills_index.v1",
        "source": "~/.codex/skills",
        "skill_count": len(skills),
        "skills": skills,
    }, f, ensure_ascii=False, indent=2)

# ---- README.md ----
total = sum(s["size_bytes"] for s in skills)
out = [
    "# CodexSkills",
    "",
    f"本机 Codex Skill 的仓库镜像，共 **{len(skills)} 个** skill、"
    f"{sum(s['file_count'] for s in skills)} 个文件、约 {total/1048576:.0f} MB。",
    "",
    "每个 skill 是一个目录，入口固定为 `<skill>/SKILL.md`，其 YAML frontmatter 的 "
    "`description` 字段说明何时该触发它。",
    "",
    "## 给 LLM / Agent 的用法",
    "",
    "```bash",
    "# 1. 先读机器索引，挑出要用的 skill",
    "curl -s https://raw.githubusercontent.com/LinzeColin/AgentDatabase/main/CodexSkills/index.json",
    "",
    "# 2. 只拉那一个 skill 的入口，不要整仓 clone",
    "curl -s https://raw.githubusercontent.com/LinzeColin/AgentDatabase/main/CodexSkills/<slug>/SKILL.md",
    "```",
    "",
    "选择方式：把用户请求与 `index.json` 里各 skill 的 `description` 做匹配，命中就读它的 "
    "`entry`，再按 `SKILL.md` 里的指示按需读该目录下的参考文件。**不要一次性加载全部 skill。**",
    "",
    "## 同步方向",
    "",
    "本目录由本机 `~/.codex/skills/` 镜像而来，排除了嵌套 `.git`、`.DS_Store`、"
    "`__pycache__` 与 `node_modules`。skill 有增删改后，重跑 `python3 build_index.py` "
    "重建索引，避免索引与实际内容漂移。",
    "",
]
for cat in list(CATEGORY) + ["其他"]:
    rows = [s for s in skills if s["category"] == cat]
    if not rows:
        continue
    out += [f"## {cat}（{len(rows)}）", "", "| Skill | 何时使用 |", "|---|---|"]
    for s in sorted(rows, key=lambda x: x["slug"]):
        d = s["description"].replace("|", "\\|")
        if len(d) > 300:
            d = d[:300].rstrip() + "…"
        out.append(f"| [`{s['slug']}`]({s['slug']}/SKILL.md) | {d or '（该 skill 未填写描述）'} |")
    out.append("")

# 分类完整性自检：任何未归类的 skill 都必须显式暴露，不能被静默吞掉
listed = {x for v in CATEGORY.values() for x in v}
orphan = sorted({s["slug"] for s in skills} - listed)
if orphan:
    out += ["## ⚠️ 未归类", "",
            "下列 skill 不在 `build_index.py` 的分类表里，已归入「其他」，请补分类：", ""]
    out += [f"- `{s}`" for s in orphan] + [""]

open("README.md", "w", encoding="utf-8").write("\n".join(out))
print(f"已生成 index.json 与 README.md：{len(skills)} 个 skill")
if orphan:
    print(f"⚠️ 未归类 {len(orphan)} 个：{orphan}")
