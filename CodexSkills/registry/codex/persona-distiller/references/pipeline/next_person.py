#!/usr/bin/env python3
"""Deterministic 'who is next' — derives done-state LIVE from the registry + Downloads,
so it can never drift from memory. Run at the start of every work session.

Usage:
  python3 next_person.py --registry-root <current-worktree>/CodexSkills/registry/codex/persona-distiller-group
(Defaults point at the worktree used for the calibration; pass --registry-root for a fresh worktree.)

## 分族配重（counterweight）——**默认开，不是选项**

队列的 `priority` 是**按语料可取得性**排的，不是按名册需要排的。
照它取，名册会单向漂移。实测（100 人时）：

    软件开发师 34 ｜ 投资资本师 21 ｜ 材料建工师 15 ｜ 建造采购师 12
    ...
    **医疗护理师 0** ｜ 农林牧渔师 1 ｜ 客户营销师 1 ｜ 艺术设计师 1 ｜ 财务合规师 1

而此时 `NEXT` 与 `upcoming` **前六名全是材料建工师**（已 15 人，第三大族）。
医疗护理师有 21 个候选，**全部 priority 11（最末）**——按原顺序永远轮不到，
名册会稳定停在「11 族 + 一个空族」。

判据：**每 `--round` 人一轮，轮首那一格留给「最少的族」。**

    slot = registry_products % round
    slot == 0 且最少族有待办 → 从最少族取（该族 order 最小者）
    否则                    → 按队列原顺序取

轮首而不是轮尾：**轮被打断也已经补过了。** 轮尾会让「这轮没做完」等价于「这轮没配重」。

`--no-counterweight` 复现漂移行为，仅供负对照；**日常不要用它。**
"""
import argparse, json, os, re, glob, subprocess, sys

DEF_REG = "/Users/linzezhang/Documents/Codex/AgentDatabase/character-distillation-skill-reorganize-d57595/CodexSkills/registry/codex/persona-distiller-group"
DEF_DL = "/Users/linzezhang/Downloads/蒸馏"
DEF_Q = "/Users/linzezhang/Downloads/蒸馏/_蒸馏队列.json"
DEF_DEFER = "/Users/linzezhang/Downloads/蒸馏/_延后名单.json"
DEF_YEARS = "/Users/linzezhang/Downloads/蒸馏/_卒年.json"   # ★ 可以不存在

def norm(s):
    return re.sub(r'[^a-z0-9]', '', s.lower())

def slugify(s):
    s = s.lower()
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return s


def pick(pending, category_counts, products_done, round_size=5, counterweight=True,
         deferred_counts=None):
    """选出 NEXT，并说明**为什么是它**。

    返回 `(item, why)`。`why` 一律写进输出——**看不见理由的排期等于没有排期。**

    `deferred_counts`（可选）是每族的延后人数。**它只进 `why`，不参与排序。**

    ★★ 为什么不参与排序：医疗护理师实测「已入库 0 人、已延后 19 人」，
    而那 19 人里 **13 人（68%）是语料齐、全流程走完、卡在判分**——
    判分是**全局**的一步，不是这一族的属性。
    按延后数给族降权，等于**把全局问题归给一个族**，是误判。

    所以配重照旧只看名册人数（名册确实是 0，指向它没错），
    但输出里**必须带上延后数**，否则「没排过」和「排了 19 个全被挡」长得一样。
    """
    deferred_counts = deferred_counts or {}
    if not pending:
        return None, {"mode": "empty", "reason": "队列无待办"}
    slot = products_done % round_size if round_size else 1
    if not counterweight:
        return pending[0], {"mode": "queue-order",
                            "reason": "**配重被关掉**（--no-counterweight），按队列原顺序"}
    if slot != 0:
        return pending[0], {"mode": "queue-order", "slot": slot,
                            "reason": f"本轮第 {slot + 1} 格，配重只占轮首那一格"}
    if not category_counts:
        return pending[0], {"mode": "queue-order",
                            "reason": "读不到 category_counts，**无法配重**——按原顺序，且此处已报告"}

    # 最少的族优先；同数按族名排，保证确定性。**只挑真有待办的族**，
    # 否则一个已凑满 50 人的空队列族会把配重永久卡死在它身上。
    have = {i["family_zh"] for i in pending}
    ranked = sorted((c, f) for f, c in category_counts.items() if f in have)
    if not ranked:
        return pending[0], {"mode": "queue-order",
                            "reason": "最少族在队列里已无待办，按原顺序"}
    least_n, least_f = ranked[0]
    if least_n >= category_counts.get(pending[0]["family_zh"], 10**9):
        return pending[0], {"mode": "queue-order", "slot": 0,
                            "reason": f"队首族「{pending[0]['family_zh']}」已是最少之一，无需配重"}
    cand = min((i for i in pending if i["family_zh"] == least_f),
               key=lambda i: (i.get("priority", 99), i.get("order", 99)))
    nd = deferred_counts.get(least_f, 0)
    why = {
        "mode": "counterweight", "slot": 0,
        "least_family": least_f, "least_count": least_n,
        "least_family_deferred": nd,
        "displaced": pending[0]["name"],
        "displaced_family": pending[0]["family_zh"],
        "displaced_family_count": category_counts.get(pending[0]["family_zh"]),
        "reason": (f"轮首配重：名册里「{least_f}」只有 {least_n} 人，"
                   f"而队列原本要给「{pending[0]['family_zh']}」（已 "
                   f"{category_counts.get(pending[0]['family_zh'])} 人）再加一个"),
    }
    if nd and not least_n:
        why["★★ 这一族入库 0 人，但已延后 %d 人" % nd] = (
            f"**配重仍指向它是对的**——名册确实 0 人。但「没排过」与「排了 {nd} 个全被挡」"
            f"在这个数上长得一样。**再排一个人不会自动改变这一点**："
            f"先看那 {nd} 人卡在抓源还是卡在判分。"
            f"（医疗护理师实测：19 人里 13 人语料齐、流程走完，卡的是判分。）")
    return cand, why


# ── 负对照 ────────────────────────────────────────────────────────────
def self_test():
    fails = []
    counts = {"软件开发师": 34, "材料建工师": 15, "医疗护理师": 0, "农林牧渔师": 1}
    q = [{"name": "Slavyanov", "family_zh": "材料建工师", "priority": 3, "order": 1},
         {"name": "Benardos", "family_zh": "材料建工师", "priority": 3, "order": 2},
         {"name": "Hippocrates", "family_zh": "医疗护理师", "priority": 11, "order": 1},
         {"name": "Galen", "family_zh": "医疗护理师", "priority": 11, "order": 2},
         {"name": "Salatin2", "family_zh": "农林牧渔师", "priority": 9, "order": 1}]

    # 负对照 1：轮首必须把 0 人族提上来
    it, why = pick(q, counts, 100)
    if it["name"] != "Hippocrates" or why["mode"] != "counterweight":
        fails.append(f"负对照 1 失败：轮首未配重，选了 {it['name']}（{why['mode']}）")

    # ★ 反向对照：关掉配重必须复现漂移——否则这个开关什么也没做
    it2, why2 = pick(q, counts, 100, counterweight=False)
    if it2["name"] != "Slavyanov":
        fails.append(f"反向对照失败：关掉配重后没有复现漂移，选了 {it2['name']}")
    if it["name"] == it2["name"]:
        fails.append("反向对照失败：开与关选出同一个人，**配重是装饰**")

    # ★★ 反向对照：**延后数不许改变选择**——判分是全局的一步，不是某一族的属性
    it_a, why_a = pick(q, counts, 100)
    it_b, why_b = pick(q, counts, 100, deferred_counts={f: 99 for f in counts})
    if it_a["name"] != it_b["name"] or why_a["mode"] != why_b["mode"]:
        fails.append(f"反向对照失败：**延后数改变了选择**（{it_a['name']} → {it_b['name']}）——"
                     "按延后数给族降权就是把全局问题归给一个族")
    # 而它必须**报出来**，否则「没排过」与「排了 19 个全被挡」长得一样
    if not any("已延后" in k for k in why_b):
        fails.append("反向对照失败：延后数没有出现在 why 里，等于没报")
    if any("已延后" in k for k in why_a):
        fails.append("反向对照失败：没给延后数时**不该**凭空报一条")

    # 正对照：非轮首不许配重（它是 1/5，不是每次）
    for slot in (1, 2, 3, 4):
        it3, why3 = pick(q, counts, 100 + slot)
        if it3["name"] != "Slavyanov" or why3["mode"] != "queue-order":
            fails.append(f"正对照失败：slot {slot} 不该配重，却选了 {it3['name']}")

    # 边界：最少族在队列里已无待办 → 退到次少的族，不许崩、不许空转
    q_no_med = [i for i in q if i["family_zh"] != "医疗护理师"]
    it4, why4 = pick(q_no_med, counts, 100)
    if it4["name"] != "Salatin2" or why4["mode"] != "counterweight":
        fails.append(f"边界失败：最少族无待办时未退到次少族，选了 {it4['name']}")

    # 边界：队首本身就是最少族 → 不重复配重，按原顺序
    it5, why5 = pick([q[2], q[0]], counts, 100)
    if it5["name"] != "Hippocrates":
        fails.append(f"边界失败：队首已是最少族时选了 {it5['name']}")

    # 边界：读不到 category_counts → 报告并退回原顺序，**不许静默**
    it6, why6 = pick(q, {}, 100)
    if it6["name"] != "Slavyanov" or "无法配重" not in why6["reason"]:
        fails.append("边界失败：缺 category_counts 时未显式报告")

    for f in fails:
        print(f"✗ {f}")
    if fails:
        print(f"负对照未通过：{len(fails)} 项")
        return 1
    print("负对照通过：轮首把 0 人族提上来；**关掉配重确实复现漂移**（证明它不是装饰）；"
          "非轮首 4 格均不配重；最少族无待办时退到次少族；队首已是最少族时不重复；"
          "缺 category_counts 时显式报告而非静默；\n      **延后数只报不排序**（两次定向变异实测：改成按延后数排序、或只换同族的人，两条断言各自命中）")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry-root", default=DEF_REG)
    ap.add_argument("--downloads", default=DEF_DL)
    ap.add_argument("--queue", default=DEF_Q)
    ap.add_argument("--deferred", default=DEF_DEFER)
    ap.add_argument("--years", default=DEF_YEARS,
                    help="_卒年.json（**没有 source 的条目不作数**）")
    ap.add_argument("--show", type=int, default=6)
    ap.add_argument("--round", type=int, default=5, help="每轮人数；轮首那一格留给配重")
    ap.add_argument("--no-counterweight", action="store_true",
                    help="复现分族漂移，**仅供负对照**")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return self_test()

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
    deferred, deferred_by_family = set(), {}
    if os.path.isfile(a.deferred):
        for item in json.load(open(a.deferred, encoding="utf-8")).get("deferred", []):
            deferred.add(norm(item.get("name", "")))
            f = item.get("family_zh")
            if f:
                # ★ 按**族**数延后人数。只进 why，不参与排序——见 pick() 的说明。
                deferred_by_family[f] = deferred_by_family.get(f, 0) + 1

    q = json.load(open(a.queue, encoding="utf-8"))["queue"]
    pending, done_in_q, deferred_in_q = [], 0, 0
    for item in q:
        if norm(item["name"]) in done_norm or slugify(item["name"]) in done_slug:
            done_in_q += 1
        elif norm(item["name"]) in deferred:
            deferred_in_q += 1
        else:
            pending.append(item)

    n_products = len(idx.get("products", [])) if os.path.isfile(ti) else 0
    counts = idx.get("category_counts", {}) if os.path.isfile(ti) else {}
    nxt, why = pick(pending, counts, n_products,
                    round_size=a.round, counterweight=not a.no_counterweight,
                    deferred_counts=deferred_by_family)

    # ★★ v0.0.0.91：NEXT 这个人要不要先跑可得性探测——**在排期那一刻就说**。
    #   check_probe_precondition 此前**从未被任何代码调用过**（51 件判据里 7 件如此）。
    #   它的默认方向是安全那一边：**卒年不知道就要探**，不许替人猜。
    probe_note = None
    if nxt:
        chk = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "..", "..", "scripts", "check_probe_precondition.py")
        chk = os.path.normpath(chk)
        if os.path.isfile(chk):
            corpora = os.path.normpath(os.path.join(
                os.path.dirname(chk), "..", "..", "..", "..",
                "skill_log_evals", "persona-distiller", "_corpora"))
            argv = [sys.executable, chk, "--queue", a.queue,
                    "--corpora", corpora, "--name", nxt["name"]]
            if os.path.isfile(a.years):
                argv += ["--years", a.years]
            r = subprocess.run(argv, capture_output=True, text=True)
            out = ((r.stdout or "") + (r.stderr or "")).splitlines()
            probe_note = [l for l in out if l.strip()][-4:] or [
                "**判据没有输出——未核（不是通过）**"]
        else:
            probe_note = ["**check_probe_precondition.py 不在——未核（不是通过）**"]

    print(json.dumps({
        # ★★ 下面四个 queue_* 数的是**队列这一群**，不是「做了多少人」。
        #   实测：名册 100 人、队列 216 人，**两边都有的只有 7 人**——
        #   名册里 93 人是在队列之外做的。
        #   所以 `queue_done` 曾被读成「只做了 9 人」，而真实入库是 `registry_products`。
        #   标签因此改成自带口径，不再让人从名字去猜它数的是什么。
        "名册已入库人数": n_products,
        "downloads_zips": len(glob.glob(os.path.join(a.downloads, "*.zip"))),
        "队列总数": len(q),
        "队列中已入库的": done_in_q,
        "队列中未动的": len(pending),
        "队列中已延后的": deferred_in_q,
        "★ 这个人要不要先跑可得性探测": probe_note or "**未核**",
        "★这两群不是同一群": (
            f"名册 {n_products} 人 vs 队列 {len(q)} 人，**只有 {done_in_q} 人重合**"
            "（重合数随归一化算法而变，另一种算法给出 7）。"
            "**配重按名册的族人数排序，候选只从队列的未动条目里取。**"
            "队列空了的族会自动退出排序（`have` 只收 pending 里出现过的族），"
            "**但只要还剩哪怕一条未动条目，名册 0 人的族就会一直置顶——"
            "哪怕剩下的那几条全都做不了。**"
            "医疗护理师正是如此：队列 21 人已延后 18，"
            "剩下 3 人（DeBakey 卒 2008／Gawande 在世／Farmer 卒 2022）全部在版权保护期内。"),
        # ★ 队列条目只有 name/family_zh/family_id/priority/order —— **没有生卒年**。
        #   于是「卒于 1930 年后的人物排期前先跑可得性探测」这条规矩
        #   （Henderson #113 的教训）在排期这一步执行不了：
        #   NEXT 给出来时，没有任何字段能提示要先探版权。
        #   已因此付出三次代价：Henderson（本人续展到 2034/2050）、
        #   Watson（在世）、DeBakey（卒于 2008）——三次都是排到了才发现。
        #   在队列加字段之前（那属用户决定），至少让它每次都提醒。
        "★排期前必做": (
            "**本队列不含生卒年。** 动手之前先查 NEXT 这个人的生卒年："
            "卒于 1930 年后（或在世）的，**必须先跑公有领域可得性探测**，"
            "不要直接开抓。已因此延后：Henderson #113（本人续展至 2034/2050）、"
            "Watson #116（在世，无到期日）、DeBakey #119（卒于 2008）。"),
        "NEXT": nxt,
        "why": why,
        "family_counts_ascending": dict(sorted(counts.items(), key=lambda kv: kv[1])),
        "queue_order_next": pending[0] if pending else None,
        "upcoming": pending[:a.show],
    }, ensure_ascii=False, indent=1))
    return 0

if __name__ == "__main__":
    sys.exit(main())
