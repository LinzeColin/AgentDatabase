#!/usr/bin/env python3
"""Deterministic 'who is next' — derives done-state LIVE from the registry + Downloads,
so it can never drift from memory. Run at the start of every work session.

Usage:
  python3 next_person.py --registry-root <current-worktree>/CodexSkills/registry/codex/persona-distiller-group
(Defaults point at the worktree used for the calibration; pass --registry-root for a fresh worktree.)"""
import argparse, json, os, re, sys, glob, pathlib

# ★★★★ 2026-08-10：**默认路径写死在另一个 worktree 上，实测已经失效。**
#   旧默认 `…/AgentDatabase/character-distillation-skill-reorganize-d57595/…` **不存在**，
#   于是 `registry_products` 打印成 **0**，而真值是 **101**——
#   [[empty-default-swallows-unknown]]：0 被读成「一个都没做」，真相是「没读到」。
#   队列与延后名单的旧默认在 `~/Downloads/蒸馏/`，**那不在 git 里**——
#   8-13 移交之后接手方拿不到，NEXT 会静默换一份底稿。
#   改法：**从本文件自己的位置推仓内路径**（本脚本就住在 `_ledgers/_pipeline/` 里），
#   仓内没有才退回旧路径，且**每次都打印实际用了哪一份**。
_HERE = pathlib.Path(__file__).resolve().parent


def _find_up(start, *names):
    """从 start 向上找第一个含有全部 names 的目录。→ 找到的目录，或 None。

    ★★★★ **不许按层数推。** 本脚本有两份副本：
      `CodexSkills/skill_log_evals/persona-distiller/_ledgers/_pipeline/next_person.py`
      `CodexSkills/registry/codex/persona-distiller/references/pipeline/next_person.py`
    层级完全不同。第一版按前者写死 `parents[2]`，
    **而 HANDOFF 让接手方跑的是后者**——在干净检出里一跑，
    三份路径全部退回仓外（`~/Downloads/`、一个不存在的 worktree）。
    [[verifying-single-commands-is-not-verifying-the-chain]]：**要在收件人的布局里跑。**
    """
    p = start
    for _ in range(12):
        if all((p / n).exists() for n in names):
            return p
        if p.parent == p:
            break
        p = p.parent
    return None


_SKILLS = _find_up(_HERE, "registry", "skill_log_evals") or _find_up(_HERE, "CodexSkills")
if _SKILLS is not None and (_SKILLS / "CodexSkills").exists():
    _SKILLS = _SKILLS / "CodexSkills"
_LEDGERS = (_SKILLS / "skill_log_evals/persona-distiller/_ledgers") if _SKILLS else None

_FALLBACK_REG = "/Users/linzezhang/Documents/Codex/AgentDatabase/character-distillation-skill-reorganize-d57595/CodexSkills/registry/codex/persona-distiller-group"
DEF_DL = "/Users/linzezhang/Downloads/蒸馏"


def _pick(in_repo, fallback):
    """仓内优先；仓内没有才用旧路径。→ (路径, 是不是退回来的)"""
    if in_repo is not None and pathlib.Path(in_repo).exists():
        return str(in_repo), False
    return str(fallback), True


DEF_REG, _REG_FELL = _pick(_SKILLS / "registry/codex/persona-distiller-group" if _SKILLS else None,
                           _FALLBACK_REG)
DEF_Q, _Q_FELL = _pick(_LEDGERS / "_蒸馏队列.json" if _LEDGERS else None,
                       "/Users/linzezhang/Downloads/蒸馏/_蒸馏队列.json")
DEF_DEFER, _D_FELL = _pick(_LEDGERS / "_延后名单.json" if _LEDGERS else None,
                           "/Users/linzezhang/Downloads/蒸馏/_延后名单.json")
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

    # ★★★ 2026-08-10：**第三种状态原来没有落脚处** —— 「做完了但没出货」。
    #   `done` 认的是 registry（出货了），`deferred` 认的是延后名单，
    #   而**卡在待裁定的人两处都不在**，于是永远排在 NEXT 最前面。
    #   实测：`upcoming` 只有 6 个，**其中 4 个已经有工作区**——
    #   Adams（卡 ㉒）、Martens（卡 ㉕）、Roberts-Austen（卡 ㉕），
    #   **还有当天刚做完的 Cicero**。下一个 agent 会被派去重做。
    #   判别依据取**磁盘上有没有工作区**：`_corpora/wip-*/workspaces/<slug>/`。
    #   ★ 它们**不静默丢掉**，单列成一栏打印出来（[[empty-default-swallows-unknown]]）。
    #   ★★ slug 对不上时**不许靠名字推断**（同姓者那条教训）。
    #     改读工作区自己 `meta.json` 里**声明的** `name`／`normalized_name`——
    #     那是数据，不是猜测。实测：队列写 `Cicero`、工作区 slug 是
    #     `marcus-tullius-cicero`，只比 slug 会漏掉当天刚做完的人。
    worked = {}
    _corp = os.path.join(os.path.dirname(os.path.dirname(a.queue)), "_corpora")
    for ws in glob.glob(os.path.join(_corp, "wip-*", "workspaces", "*")):
        if not os.path.isdir(ws):
            continue
        tag = os.path.basename(os.path.dirname(os.path.dirname(ws)))
        worked[os.path.basename(ws)] = tag
        mj = os.path.join(ws, "meta.json")
        if os.path.isfile(mj):
            try:
                md = json.load(open(mj, encoding="utf-8"))
            except Exception:
                continue
            for k in ("name", "normalized_name", "slug"):
                v = md.get(k)
                if v:
                    worked[slugify(str(v))] = tag
                    worked[norm(str(v))] = tag
            # ★ 队列名与工作区正式名不同时（队列 `Cicero` / 工作区 `Marcus Tullius Cicero`），
            #   **由工作区自己在 meta.json 里声明 `aliases`**——声明的才认，一律不推断。
            for al in (md.get("aliases") or []):
                worked[slugify(str(al))] = tag
                worked[norm(str(al))] = tag

    # ★ 生卒年记在**另一个台账** `_卒年.json` 里（204 条，带 Wikidata 出处），**不在队列里**。
    #   NEXT 原来不读它，于是报出人名时看不到年份，判「够不够得着 PD 分界」要另跑一步。
    #   ★★ **只打印，不据此过滤**：PD-only 规则的射程是待裁定 ㉜，
    #   把它写进 NEXT 等于替人定了一条没裁定的政策（延后名单里已有 75 条挂着 `pd_scope_pending`）。
    _years = {}
    _yp = os.path.join(os.path.dirname(a.queue), "_卒年.json")
    if os.path.isfile(_yp):
        try:
            for k, v in json.load(open(_yp, encoding="utf-8")).items():
                if isinstance(v, dict) and v.get("born"):
                    _years[norm(v.get("name") or k)] = (v.get("born"), v.get("died"))
        except Exception:
            pass

    def _withyears(item):
        yr = _years.get(norm(item["name"]))
        return {**item, "生卒": f"{yr[0]}–{yr[1]}" if yr else "**卒年台账里没有**"} if item else item

    q = json.load(open(a.queue, encoding="utf-8"))["queue"]
    pending, done_in_q, deferred_in_q = [], 0, 0
    worked_not_shipped = []
    for item in q:
        if norm(item["name"]) in done_norm or slugify(item["name"]) in done_slug:
            done_in_q += 1
        elif norm(item["name"]) in deferred:
            deferred_in_q += 1
        elif slugify(item["name"]) in worked or norm(item["name"]) in worked:
            worked_not_shipped.append({**item, "工作区": worked.get(slugify(item["name"]))
                                       or worked.get(norm(item["name"]))})
        else:
            pending.append(item)

    #   ★★★★ 2026-08-11（Shewhart #165 撞出）：**队列名与 registry 名差一个中名首字母，
    #     于是刚入库的人第二天又排回 NEXT。** 实测：registry 是 `Walter A. Shewhart`
    #     （产物侧的规范名，题名页作 `WALTER ANDREW SHEWHART`），队列写的是 `Walter Shewhart`，
    #     `norm()` 去标点后仍是两个不同的串 → 判不出他已完成 → **NEXT 指着一个刚入库的人**。
    #
    #   ★★ **修法不是把匹配放宽到「忽略中名」**——那正是 Coffin #130 的陷阱：
    #     `Charles L. Coffin`（焊接发明人）与 `Charles A. Coffin`（GE 首任总裁）
    #     **首尾名相同、中名不同，是两个人**。放宽会把他们并成一个。
    #
    #   → 只**响亮地报出来**，让人去核，**不替人决定他们是不是同一个**。
    def _fl(s):
        toks = [x for x in re.split(r'[^A-Za-z0-9]+', s) if x]
        return (norm(toks[0]), norm(toks[-1])) if len(toks) >= 2 else None
    _done_fl = {}
    if os.path.isfile(ti):
        for _p in idx.get("products", []):
            for _tok in (_p.get("canonical_name"), _p.get("display_name"), _p.get("name")):
                if _tok and _fl(_tok):
                    _done_fl.setdefault(_fl(_tok), []).append(_tok)
    _suspect = []
    for _it in pending:
        _k = _fl(_it["name"])
        if _k and _k in _done_fl:
            _suspect.append({"队列里写的": _it["name"], "registry 里的": _done_fl[_k],
                             "★": "**首尾名相同而全名不同**——可能是同一个人（中名首字母之差），"
                                  "也可能是同名者。**去核，不要自动并。**"})
    if _suspect:
        print("★★★ **有人排在 NEXT，而 registry 里存在首尾名相同的产物** —— "
              "多半是队列名少了中名首字母，但 Coffin 那种同姓同名不同中名的也长这样：",
              file=sys.stderr)
        for _s in _suspect:
            print("    " + json.dumps(_s, ensure_ascii=False), file=sys.stderr)

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
        # ★ 做完了但没出货、也没记延后的——**多半卡在待裁定**。
        #   它们**已经排除出 NEXT**，但必须在这里被看见，否则就成了没人管的一批。
        "★ 已做但未出货（不进 NEXT，去看它卡在哪）": worked_not_shipped,
        "NEXT": _withyears(pending[0]) if pending else None,
        "upcoming": [_withyears(x) for x in pending[:a.show]],
    }, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
