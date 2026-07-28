#!/usr/bin/env python3
"""Deterministic 'who is next' — derives done-state LIVE from the registry + Downloads,
so it can never drift from memory. Run at the start of every work session.

Usage:
  python3 next_person.py --registry-root <current-worktree>/CodexSkills/registry/codex/persona-distiller-group
(Defaults point at the worktree used for the calibration; pass --registry-root for a fresh worktree.)"""
import argparse, json, os, re, glob

DEF_REG = "/Users/linzezhang/Documents/Codex/AgentDatabase/character-distillation-skill-reorganize-d57595/CodexSkills/registry/codex/persona-distiller-group"
DEF_DL = "/Users/linzezhang/Downloads/蒸馏"
DEF_Q = "/Users/linzezhang/Downloads/蒸馏/_蒸馏队列.json"
DEF_DEFER = "/Users/linzezhang/Downloads/蒸馏/_延后名单.json"

def norm(s):
    return re.sub(r'[^a-z0-9]', '', s.lower())

def slugify(s):
    s = s.lower()
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return s

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry-root", default=DEF_REG)
    ap.add_argument("--downloads", default=DEF_DL)
    ap.add_argument("--queue", default=DEF_Q)
    ap.add_argument("--deferred", default=DEF_DEFER)
    ap.add_argument("--show", type=int, default=6)
    a = ap.parse_args()

    done_norm, done_slug = set(), set()
    # 1) registry (authoritative once pushed to main; on a fresh worktree run `git pull` first)
    ti = os.path.join(a.registry_root, "team-index.json")
    if os.path.isfile(ti):
        idx = json.load(open(ti, encoding="utf-8"))
        for p in idx.get("products", []):
            for token in re.split(r'[/|]', str(p.get("canonical_name", ""))):
                if token.strip():
                    done_norm.add(norm(token))
            if p.get("subject_slug"):
                done_slug.add(p["subject_slug"].lower())
    else:
        print("WARN: team-index.json not found at", ti)
    # 2) Downloads ZIPs (local snapshot, incl. not-yet-registered)
    for f in glob.glob(os.path.join(a.downloads, "*.zip")):
        base = os.path.basename(f).lower()
        m = re.split(r'-persona-distillation', base)
        if m and m[0]:
            done_slug.add(m[0].strip('-'))

    # 因证据不足延后的人物：跳过但不出队，补足来源后从 _延后名单.json 删掉即可恢复
    deferred = set()
    if os.path.isfile(a.deferred):
        for item in json.load(open(a.deferred, encoding="utf-8")).get("deferred", []):
            deferred.add(norm(item.get("name", "")))

    q = json.load(open(a.queue, encoding="utf-8"))["queue"]
    pending, done_in_q, deferred_in_q = [], 0, 0
    for item in q:
        if norm(item["name"]) in done_norm or slugify(item["name"]) in done_slug:
            done_in_q += 1
        elif norm(item["name"]) in deferred:
            deferred_in_q += 1
        else:
            pending.append(item)

    print(json.dumps({
        "registry_products": len(idx.get("products", [])) if os.path.isfile(ti) else 0,
        "downloads_zips": len(glob.glob(os.path.join(a.downloads, "*.zip"))),
        "queue_total": len(q),
        "queue_done": done_in_q,
        "queue_pending": len(pending),
        "queue_deferred": deferred_in_q,
        "NEXT": pending[0] if pending else None,
        "upcoming": pending[:a.show],
    }, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
