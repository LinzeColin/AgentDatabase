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

# ★★★ v0.0.0.154：原先这里写死的是**某一个 worktree 的绝对路径**
#   （…/character-distillation-skill-reorganize-d57595/…）。
#   按铁律「谁开的谁收」，worktree 用完就要删——**删掉的那天这行就断了**，
#   而它断的方式是「找不到名册」，不是「报错说路径写死了」。
#   改成**相对本脚本**定位：本文件在 <skill>/references/pipeline/ 下，
#   兄弟包在 <skill>/../persona-distiller-group。
DEF_REG = os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "persona-distiller-group"))
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


def workspace_of(corp, name):
    """`_corpora/` 里有没有这个人的工作区。返回 (目录名, 已判轮次) 或 None。

    ★★★ 按**整段**比，不按子串比。子串版实测撞出假阳：
    `William D. Callister` 命中 `wip-lister-108`——`lister` 是 `callister` 的一部分。
    与同名护栏那次是同一个坑（抹平之后再查词边界，边界就没了）。
    """
    if not os.path.isdir(corp):
        return None
    slug = name.strip().lower().replace(" ", "-").replace(".", "").split("-")
    for d in sorted(os.listdir(corp)):
        if not d.startswith("wip-"):
            continue
        stem = d[4:].rsplit("-", 1)[0]
        # ★★★★ 复合姓：`wip-roberts-austen-135` 的 stem 是 `roberts-austen`，
        #   而 `William Chandler Roberts-Austen` 切成
        #   ['william','chandler','roberts','austen'] ——**整段比会漏掉他**。
        #   补法是允许 stem 命中**连续的若干段**；它仍挡得住 Callister 那个假阳，
        #   因为 `lister` 既不是 ['william','d','callister'] 的某一段，
        #   也不是其中任何一段连续的拼接。
        segs = [stem] if "-" not in stem else stem.split("-")
        n = len(segs)
        if stem and any(slug[i:i + n] == segs for i in range(len(slug) - n + 1)):
            rounds = []
            for _r, dirs, _f in os.walk(os.path.join(corp, d)):
                for x in dirs:
                    if x.startswith("round"):
                        rounds.append(x)
            return d, sorted(set(rounds))
    return None


def corpora_dir():
    # ★ 实测数出来的层数：references/pipeline → 上 5 级才到 CodexSkills。
    #   第一版写 4 级，路径不存在于是**静默什么都没找到**——「空默认值吞掉不知道」。
    return os.path.normpath(os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "..", "..", "..", "..",
        "skill_log_evals", "persona-distiller", "_corpora"))


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

    # ★★★★ v0.0.0.167：**「已开工」必须把人挡在 NEXT 之外**——正反两侧都要动。
    #   反例红了可能是红得凑巧，所以同一副骨架跑两遍：只差「有没有工作区」这一件事。
    import tempfile as _tf
    with _tf.TemporaryDirectory() as _d:
        _c = os.path.join(_d, "_corpora"); os.makedirs(_c)
        # ① 没有任何工作区 → 队首照选（正例必须是绿的）
        if workspace_of(_c, "Nikolai Slavyanov") is not None:
            fails.append("正对照失败：空语料区却报出工作区")
        # ② 建一个 wip-slavyanov-115 → 同一个人必须被认出来
        os.makedirs(os.path.join(_c, "wip-slavyanov-115", "round1"))
        got = workspace_of(_c, "Nikolai Slavyanov")
        if not got or got[0] != "wip-slavyanov-115" or got[1] != ["round1"]:
            fails.append(f"反向对照失败：建了工作区却没认出来（{got}）")
        # ③ ★ 复合姓：`wip-roberts-austen-135` vs `William Chandler Roberts-Austen`
        #    整段比会漏掉他——这是真实漏判，不是假想
        os.makedirs(os.path.join(_c, "wip-roberts-austen-135"))
        if not workspace_of(_c, "William Chandler Roberts-Austen"):
            fails.append("反向对照失败：复合姓 roberts-austen 没认出来")
        # ④ ★★ 而 Callister 的假阳必须仍然挡住（`lister` ⊂ `callister`）
        os.makedirs(os.path.join(_c, "wip-lister-108"))
        if workspace_of(_c, "William D. Callister"):
            fails.append("★★ 假阳复发：`lister` 又命中了 `callister`——词边界没了")
        # ⑤ 反向：把工作区目录挪走，同一个人必须变回「没开工」
        os.rename(os.path.join(_c, "wip-slavyanov-115"),
                  os.path.join(_c, "gone-slavyanov-115"))
        if workspace_of(_c, "Nikolai Slavyanov"):
            fails.append("反向对照失败：目录没了还报有工作区")
        # ⑥ ★★★ 语料区路径不存在 ≠「他没有工作区」——不许静默当成没有
        if workspace_of(os.path.join(_d, "根本不存在"), "Nikolai Slavyanov") is not None:
            fails.append("边界失败：路径不存在时应返回 None 并由调用方报告，而非编造命中")

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
    defer_warn = None
    if os.path.isfile(a.deferred):
        _dj = json.load(open(a.deferred, encoding="utf-8"))
        _dl = _dj.get("deferred", [])
        # ★★ 2026-08-04：`total` 是**手写的**，实测写着 17 而实际 30 条——差 13，
        #    从没有任何东西核过它。手写计数会漂，漂了没人知道。**读到就核一次。**
        _tt = _dj.get("total")
        if _tt is not None and _tt != len(_dl):
            defer_warn = (f"**`_延后名单.json` 的 `total` 写 {_tt}，实际 {len(_dl)} 条"
                          f"——差 {len(_dl) - _tt} 条。手写计数漂了。**")
        # ★ 重名也核一次：同一个人记两遍会让「已延后」多算
        _names = [norm(x.get("name", "")) for x in _dl]
        _dupes = sorted({n for n in _names if _names.count(n) > 1 and n})
        if _dupes:
            defer_warn = (defer_warn or "") + f"　**延后名单里有重名：{_dupes}**"
        for item in _dl:
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

    # ★★★★ v0.0.0.167：**「未动」这个词此前是假的。**
    #   排除源只有三个：名册 team-index、Downloads ZIP、`_延后名单.json`。
    #   **「已经有工作区」不在其中**——于是 7 个人反复被排成 NEXT：
    #     Adams #131（受阻待裁 ㉒）、Martens #134（受阻待裁 ㉕）、
    #     Bessemer #132 与 Sorby #133（**已记拒发，但漏写进 `_延后名单.json`**）、
    #     Mehl #137（通道受限）、Steinhardt #98（停在可续检查点）、Rosenhain #138（在做）。
    #   ★ v0.0.0.156 已经把 Adams 这件事逐字写在 existing_ws 的注释里，
    #     **但它只查 NEXT 一个人、只报不拦**，于是每跑一次都要人工绕一次。
    #     旁边那些「只报不改选择」的项都注明了「属用户裁定」，这一项没有——
    #     说明它不是决定，是没做完。
    #   ★★ 本件**不替用户排期**。它做的是另一件事：
    #     **处置没落进任何机器可读的文件时，拒绝给出 NEXT，并指名是谁缺。**
    #     「有工作区」是事实，不是判断；缺记录是数据缺口，不是排期策略。
    corp_dir = corpora_dir()
    started, truly_pending = [], []
    corp_missing = not os.path.isdir(corp_dir)
    for it in pending:
        ws = None if corp_missing else workspace_of(corp_dir, it["name"])
        if ws:
            started.append({"name": it["name"], "family_zh": it.get("family_zh"),
                            "目录": ws[0], "已判轮次": ws[1]})
        else:
            truly_pending.append(it)

    n_products = len(idx.get("products", [])) if os.path.isfile(ti) else 0
    counts = idx.get("category_counts", {}) if os.path.isfile(ti) else {}
    nxt, why = pick(truly_pending, counts, n_products,
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

    # ★★ v0.0.0.93：同族待办里，**有没有不需要探测的人**——排期效率的实话。
    #   实测：农林牧渔师队列 15 人，order=1 的 Borlaug（卒 2009）要先花一小时探测，
    #   而同族后面站着 Liebig / Mendel / Burbank / Pinchot 这些无争议的公有领域人物。
    #   ★ **本项只报，不改选择**——换人是排期策略，属用户裁定，不是我能顺手改的。
    same_family, no_probe = [], []
    if nxt:
        fam = nxt.get("family_zh")
        yrs = {}
        if os.path.isfile(a.years):
            try:
                yrs = {k: v for k, v in json.load(open(a.years, encoding="utf-8")).items()
                       if isinstance(v, dict) and v.get("source") and v.get("died")}
            except Exception:
                yrs = {}
        for it in pending:
            if it.get("family_zh") != fam or it["name"] == nxt["name"]:
                continue
            same_family.append(it["name"])
            rec = yrs.get(it["name"].strip().lower())
            if rec and rec["died"] < 1930:
                no_probe.append(f"{it['name']}（卒 {rec['died']}）")

    # ★★ v0.0.0.96：依据可行性分诊——**把探测的射程先缩一缩**。
    #   七次探测七次延后、每次 30–70 分钟；而有几次，依据的适用条件在开跑前就排除了大部分路。
    #   ★ 只用**卒年表里有出处的**生卒年；其余属性一律不知道 → 当作「还可能」，不许替人排除。
    # ★★★ v0.0.0.156：**「不在名册」被读成「没开工」——差点让我把 Adams 重做一遍。**
    #   本件判「做没做」看的是**入库**（registry_products）。而 Adams #131
    #   三轮判分全跑完、诚实 delta 首次转正 +0.0375，**卡在 strict 打包（待裁定 ㉒）**——
    #   他没入库，于是在这里与「从没碰过的人」长得一模一样，NEXT 又把他排了出来。
    #   ★ 「受阻待裁」与「没开工」是两种状态，**空默认值不许把它们并成一种**。
    #   判法：`_corpora/wip-*` 下有没有他的工作区。有就报出来，并说明它到哪一步了。
    existing_ws = None
    if nxt:
        corp = os.path.normpath(os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            # ★ 实测数出来的层数：references/pipeline → 上 5 级才到 CodexSkills。
            #   第一版写 4 级，路径不存在于是**静默什么都没找到**，报「没有——是新的」——
            #   又一次「空默认值吞掉不知道」。已加下面的存在性断言。
            "..", "..", "..", "..", "..",
            "skill_log_evals", "persona-distiller", "_corpora"))
        slug = nxt["name"].strip().lower().replace(" ", "-").replace(".", "")
        if not os.path.isdir(corp):
            # ★★ 路径找不到时**必须说出来**，不许静默当成「没有工作区」。
            existing_ws = {"★ 判不了": f"语料区路径不存在：{corp}——"
                                       "**这不等于「他没有工作区」**"}
        else:
            for d in sorted(os.listdir(corp)):
                if not d.startswith("wip-"):
                    continue
                # wip-<姓氏或 slug 片段>-<编号>
                stem = d[4:].rsplit("-", 1)[0]
                # ★★★ 按**整段**比，不按子串比。
                #   子串版实测撞出一个假阳：`William D. Callister` 命中 `wip-lister-108`
                #   ——`lister` 是 `callister` 的一部分。
                #   这与同名护栏那次是同一个坑（抹平之后再查词边界，边界就没了）。
                if stem and stem in slug.split("-"):
                    ws = os.path.join(corp, d)
                    rounds = []
                    for root, dirs, _f in os.walk(ws):
                        for x in dirs:
                            if x.startswith("round"):
                                rounds.append(x)
                    existing_ws = {
                        "目录": d,
                        "已判轮次": sorted(set(rounds)),
                        "★": ("**这个人已经有工作区了。** 「不在名册」只说明他没入库，"
                              "**不等于没开工**——受阻待裁与没开工是两种状态。"
                              "动手之前先去读那个工作区的判决书，别重做一遍。"),
                    }
                    break

    grounds_note = None
    if nxt:
        chk2 = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                             "..", "..", "scripts", "check_pd_grounds.py"))
        rec = None
        if os.path.isfile(a.years):
            try:
                rec = json.load(open(a.years, encoding="utf-8")).get(nxt["name"].strip().lower())
            except Exception:
                rec = None
        if not os.path.isfile(chk2):
            grounds_note = "**check_pd_grounds.py 不在——分诊未做（不是通过）**"
        elif not (rec and rec.get("source")):
            grounds_note = ("**卒年表里没有他（或没有出处）——分诊做不了**，"
                            "五条依据一条都不能排除；探测要按全射程跑")
        else:
            import importlib.util as _iu
            _s = _iu.spec_from_file_location("_pdg", chk2); _m = _iu.module_from_spec(_s)
            _s.loader.exec_module(_m)
            r = _m.feasible_grounds(born=rec.get("born"), died=rec.get("died"))
            grounds_note = r["**结论**"] + f"（依据卒年表：{rec.get('born')}–{rec.get('died')}）"
            # ★ 记录级 confidence 不能替字段级判断——用到 low 就说出来
            if rec.get("confidence") == "low":
                grounds_note += ("　★★ **该卒年记录标 `confidence: low`**——"
                                 "看清是哪个字段近似再用："
                                 + str(rec.get("source"))[:70])

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
        "队列中未动的": len(truly_pending),
        "队列中已延后的": deferred_in_q,
        # ★★★★ 第四种状态。此前它被并进「未动」，于是这些人反复被排成 NEXT。
        "队列中已开工但处置没落库的": len(started),
        **({"★★★ 这几个人有工作区，却既不在名册也不在延后名单": {
            "口径": ("**「有工作区」是事实，不是判断。** 处置（入库／延后／拒发／受阻待裁）"
                     "只要没进机器可读的文件，这个人就会被当成「从没碰过」。"
                     "实测漏的两个是 **Bessemer #132 与 Sorby #133——都已记拒发，"
                     "却只写在 `_决策台账.md` 的散文里，没进 `_延后名单.json`**。"),
            "要做的": ("每人补一条处置记录；`_延后名单.json` 目前同时收「延后」与「拒发」"
                       "（实测 32 + 5），补进去即可。**在那之前他们不参与 NEXT。**"),
            "名单": started,
        }} if started else {}),
        **({"★★ 语料区路径不存在，「已开工」判不了": corp_dir} if corp_missing else {}),
        **({"★★ 延后名单自身有问题": defer_warn} if defer_warn else {}),
        "★ 这个人要不要先跑可得性探测": probe_note or "**未核**",
        "★ 探测射程（依据可行性分诊）": grounds_note or "**未做**",
        "★ 同族待办里不需要探测的": (no_probe or
            f"**0 人**——同族还有 {len(same_family)} 人待办，但卒年表里没有他们的条目，"
            f"**这不等于他们都需要探测，是卒年未知**（见任务：给队列补生卒年）"),
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
        "★★ NEXT 是否已有工作区": existing_ws or "没有——是新的",
        "NEXT": nxt,
        "why": why,
        "family_counts_ascending": dict(sorted(counts.items(), key=lambda kv: kv[1])),
        "queue_order_next": pending[0] if pending else None,
        "upcoming": pending[:a.show],
    }, ensure_ascii=False, indent=1))
    return 0

if __name__ == "__main__":
    sys.exit(main())
