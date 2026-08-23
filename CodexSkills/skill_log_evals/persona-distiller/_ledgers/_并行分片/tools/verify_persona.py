#!/usr/bin/env python3
"""
T3 单人入库核验助手：给一个已登记的 slug，核验产物是否完整合格。

用法：python3 verify_persona.py <slug> [--count-only]
输出：commit / team-card / readiness / subject_uid / 族目录 / 切片 status / validate_group 结果
"""
import json, os, re, subprocess, sys, pathlib

REPO = "/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase-T3"
GROUP = "CodexSkills/registry/codex/persona-distiller-group"
SLICE = os.path.join(REPO, "CodexSkills/skill_log_evals/persona-distiller/_ledgers/_并行分片/T3-451-604.json")

def sh(cmd):
    return subprocess.run(cmd, cwd=REPO, shell=True, capture_output=True, text=True)

def main():
    slug = sys.argv[1]
    only = "--count-only" in sys.argv

    n = sh("git ls-files 'CodexSkills/registry/codex/persona-distiller-group/*/*/team-card.json' | wc -l").stdout.strip()
    if only:
        print("在册数(worktree):", n, "| 主树基线 117")
        return

    # 1) 找该 slug 的注册目录
    regs = sh(f"find {GROUP} -maxdepth 2 -type d -name '{slug}'").stdout.strip().splitlines()
    print("注册目录:", regs if regs else "❌ 未找到")
    if not regs:
        return
    reg = regs[0]
    tc = os.path.join(reg, "team-card.json")
    if os.path.exists(tc):
        d = json.load(open(tc))
        print("  readiness:", d.get("readiness"), "| subject_uid:", d.get("subject_uid"),
              "| 版本:", d.get("latest_product_version"))
    else:
        print("  ❌ 缺 team-card.json")

    # 2) 切片 JSON 该人 status
    d = json.load(open(SLICE))
    row = next((p for p in d["people"] if p["name"] in slug.replace("-", " ") or
                re.search(slug.replace("-", ""), p["name"].replace(" ", "").lower(), re.I)), None)
    if row:
        print("切片 status:", row["no"], row["name"], "→", row["status"])

    # 3) 最近 3 个提交
    log = sh("git log --oneline -3").stdout.strip().splitlines()
    print("最近提交:")
    for l in log:
        print("  ", l)

    # 4) validate_group
    v = sh(f"python3 {GROUP}/scripts/validate_group.py")
    try:
        vd = json.loads(v.stdout)
        print("validate_group:", "passed" if vd.get("passed") else "FAILED",
              "| products:", vd.get("products"), "| errors:", len(vd.get("errors", [])))
    except Exception:
        print("validate_group 输出无法解析:", v.stdout[:200])

if __name__ == "__main__":
    main()
