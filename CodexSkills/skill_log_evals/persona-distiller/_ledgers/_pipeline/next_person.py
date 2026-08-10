#!/usr/bin/env python3
"""Deterministic 'who is next' — derives done-state LIVE from the registry + Downloads,
so it can never drift from memory. Run at the start of every work session.

Usage:
  python3 next_person.py --registry-root <current-worktree>/CodexSkills/registry/codex/persona-distiller-group
(Defaults point at the worktree used for the calibration; pass --registry-root for a fresh worktree.)"""
import argparse, json, os, re, glob, pathlib

# ★★★★ 2026-08-10：**默认路径写死在另一个 worktree 上，实测已经失效。**
#   旧默认 `…/AgentDatabase/character-distillation-skill-reorganize-d57595/…` **不存在**，
#   于是 `registry_products` 打印成 **0**，而真值是 **101**——
#   [[empty-default-swallows-unknown]]：0 被读成「一个都没做」，真相是「没读到」。
#   队列与延后名单的旧默认在 `~/Downloads/蒸馏/`，**那不在 git 里**——
#   8-13 移交之后接手方拿不到，NEXT 会静默换一份底稿。
#   改法：**从本文件自己的位置推仓内路径**（本脚本就住在 `_ledgers/_pipeline/` 里），
#   仓内没有才退回旧路径，且**每次都打印实际用了哪一份**。
_HERE = pathlib.Path(__file__).resolve().parent          # …/_ledgers/_pipeline
_LEDGERS = _HERE.parent                                  # …/_ledgers
_SKILLS = _LEDGERS.parents[2]                            # …/CodexSkills

_FALLBACK_REG = "/Users/linzezhang/Documents/Codex/AgentDatabase/character-distillation-skill-reorganize-d57595/CodexSkills/registry/codex/persona-distiller-group"
DEF_DL = "/Users/linzezhang/Downloads/蒸馏"


def _pick(in_repo, fallback):
    """仓内优先；仓内没有才用旧路径。→ (路径, 是不是退回来的)"""
    return (str(in_repo), False) if pathlib.Path(in_repo).exists() else (str(fallback), True)


DEF_REG, _REG_FELL = _pick(_SKILLS / "registry/codex/persona-distiller-group", _FALLBACK_REG)
DEF_Q, _Q_FELL = _pick(_LEDGERS / "_蒸馏队列.json", "/Users/linzezhang/Downloads/蒸馏/_蒸馏队列.json")
DEF_DEFER, _D_FELL = _pick(_LEDGERS / "_延后名单.json", "/Users/linzezhang/Downloads/蒸馏/_延后名单.json")

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
        print("★ 因此下面的 registry_products 是 null，**不是 0**——"
              "读不到不等于一个都没有。用 --registry-root 指到真的那份。")
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
            # ★★★ 队列与名单的名字形式常常不同（队列 `William Paton` /
            #   名单 `William Andrew Paton`），`norm` 之后并不相等，
            #   于是**刚判完延后的人第二天又排回 NEXT**。实测撞到过。
            #   只认**显式写下的** aliases，**不做任何名字推断**——
            #   按词元包含去猜会把 `Charles Coffin` 与 GE 总裁 `Charles A. Coffin`
            #   认成同一个人（[[test-the-guard-against-this-persons-namesake]]）。
            for al in (item.get("aliases") or []):
                deferred.add(norm(al))

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
        # ★ 读不到就是 None，**不许写 0**（[[empty-default-swallows-unknown]]）
        "registry_products": len(idx.get("products", [])) if os.path.isfile(ti) else None,
        "★ 实际用的路径": {
            "registry": DEF_REG if a.registry_root == DEF_REG else a.registry_root,
            "queue": a.queue,
            "deferred": a.deferred,
            "★ 有没有退回仓外的旧路径": {
                "registry": _REG_FELL, "queue": _Q_FELL, "deferred": _D_FELL,
            },
        },
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
