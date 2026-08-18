#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`divergences: []` 意为「**没有检出**」，不是「专家一致」—— 本件守住「还检出得了」这件事。

`build_team_dossier.extract_divergences` 只认**全名或 slug 的精确出现**，
且只在 `divergence-map.md` 里**长度 ≥40 的段落**中找。它有三处会被静默打断：

1. 谁把 `divergence-map.md` 的段落切碎（每段 <40 字）⇒ 扫描面归零；
2. 谁改了 `canonical_name` 的写法（加中间名、改大小写外的形态）⇒ 精确匹配失配；
3. 谁重打了包而新包里没有 `divergence-map.md` ⇒ `divergence_text` 为空。

**三种都会让 `divergences` 恒为 `[]`，而下游读到的是「专家没有分歧」。**
[[zero-hit-gates-must-prove-they-can-hit]]｜[[empty-default-swallows-unknown]]

## 2026-08-18 实测（本件的由来）

用**权威抽取器**（不是我自己写的）跑全名册：

    102 人 ⇒ 5151 个配对；可互相点名的 **24 个 = 0.47%**
    24 个配对**全部同族**：software-developer 7、investor-capital-allocator 17，跨族 **0**

而路由的多样性配重要求同族第 2 人的 `base_score` 领先 **(0.08+0.025)/0.76 = 0.1382**
⇒ **同族第二人基本进不来**。两件事叠起来的后果，本件不判，只记在 SKILL.md：

    72 道 oracle 上，路由选出的队伍含可检出分歧对的 —— **0 / 72**
    同样大小的随机队伍（200 次重抽）—— 中位 **22 / 72（30.6%）**，200 次里 **0 次** ≤0
    ⇒ 不是碰巧没凑到，是**系统性地把它们分开**。

★ 本件**只守可检出配对数不掉**（回归地板 24）。改多样性配重会移动每一道任务选出的人，
  属「门、席位一概不动」——**不在本件射程内**。

用法：

    python3 check_divergence_pairs_survive_extraction.py
    python3 check_divergence_pairs_survive_extraction.py --baseline-pairs 999   # 看它红不红得了
    python3 check_divergence_pairs_survive_extraction.py --self-test
"""
from __future__ import annotations

import argparse
import collections
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent

BASELINE_PAIRS = 24        # 2026-08-18 实测，权威抽取器，102 人名册
BASELINE_ROSTER = 102      # 基线绑定的名册规模
MIN_NONEMPTY_RATE = 0.90   # divergence-map.md 非空的人占比；低于它 ⇒ 扫描面塌了 ⇒ rc=4


def _load():
    sys.path.insert(0, str(HERE))
    import build_team_dossier as B      # noqa: E402
    import route_team_moe as R          # noqa: E402
    root = R.default_registry_root()
    cards = R.read_json(root / "team-index.json").get("products", [])
    return B, R, root, cards


def harvest(B, root, cards) -> tuple[list[dict], int]:
    """→ (可喂给 extract_divergences 的成员列表, 取不到包的人数)。"""
    members, missing = [], 0
    for card in cards:
        slug = card.get("subject_slug")
        path = B.find_delivery(root, slug, card)
        if not path:
            missing += 1
            continue
        try:
            payload = B.read_persona_payload(path)
        except Exception:
            missing += 1
            continue
        members.append({
            "subject_slug": slug,
            "canonical_name": card.get("canonical_name"),
            "identity_family_id": card.get("identity_family_id") or card.get("registration_category"),
            "divergence_text": payload.get("divergence_text", ""),
        })
    return members, missing


def pair_set(B, members) -> set[tuple[str, str]]:
    """★ 注意 `extract_divergences` 会 **pop 掉** `divergence_text` —— 传副本进去。"""
    copies = [dict(m) for m in members]
    return {tuple(r["between"]) for r in B.extract_divergences(copies)}


def self_test() -> int:
    ok = True

    def chk(name, cond):
        nonlocal ok
        print("   %s %s" % ("✓" if cond else "✗", name))
        ok = ok and bool(cond)

    B, R, root, cards = _load()
    members, missing = harvest(B, root, cards)
    chk("① 取到名册且取得到包（%d 人，取不到 %d）" % (len(members), missing),
        len(members) >= 10 and missing == 0)
    nonempty = sum(1 for m in members if str(m["divergence_text"]).strip())
    chk("②★扫描面非空：divergence-map.md 非空 %d/%d" % (nonempty, len(members)),
        nonempty >= MIN_NONEMPTY_RATE * len(members))

    pairs = pair_set(B, members)
    chk("③ 现算配对数 == 基线 %d（现测 %d）" % (BASELINE_PAIRS, len(pairs)),
        len(pairs) == BASELINE_PAIRS)

    # ★★ 非退化：把 divergence_text 全清空（退化实现）⇒ 必须一个都检不出
    blank = [dict(m, divergence_text="") for m in members]
    chk("④★★退化对照：清空全部 divergence_text ⇒ 配对必须为 0（现测 %d）"
        % len(pair_set(B, blank)), len(pair_set(B, blank)) == 0)

    # ★★★ 反例：把段落切碎到 <40 字 ⇒ 也必须检不出（守住那条长度规则）
    chopped = [dict(m, divergence_text="\n\n".join(
        w for w in str(m["divergence_text"]).split() if w)[:2000]) for m in members]
    n_chop = len(pair_set(B, chopped))
    chk("⑤★★★反例：段落切碎到 <40 字 ⇒ 配对应显著减少（现测 %d < %d）"
        % (n_chop, BASELINE_PAIRS), n_chop < BASELINE_PAIRS)

    fam = {m["canonical_name"]: m["identity_family_id"] for m in members}
    cross = [p for p in pairs if fam.get(p[0]) != fam.get(p[1])]
    # ★ 第一版这里写的是 `len(pairs) == len(cross) + (len(pairs)-len(cross))` —— **恒等式，不是断言**。
    #   真正要守的是「族标签取得到」：取不到时 fam.get() 全是 None ⇒ 同族/跨族的划分整个失去意义。
    unknown = {n for p in pairs for n in p if fam.get(n) is None}
    chk("⑥ 每个配对里的人都取得到族标签（取不到的 %d 人）" % len(unknown), not unknown)
    chk("⑥b 族标签不止一种（现测 %d 种）—— 只有一种时「同族」这个概念是空的"
        % len(set(fam.values())), len(set(fam.values())) >= 2)
    chk("⑦ 地板可达：0 < BASELINE_PAIRS，且基线记着名册规模", BASELINE_PAIRS > 0 and BASELINE_ROSTER > 0)
    print("   —— self-test %s ——" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="可检出的分歧配对数不许掉")
    ap.add_argument("--baseline-pairs", type=int, default=None)
    ap.add_argument("--self-test", "--selftest", dest="selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return self_test()

    floor = BASELINE_PAIRS if a.baseline_pairs is None else a.baseline_pairs
    B, R, root, cards = _load()
    members, missing = harvest(B, root, cards)
    if missing:
        print("★ **未量，不是通过**（rc=4）—— %d 人的交付包取不到，配对数无从比较" % missing)
        return 4
    if len(members) != BASELINE_ROSTER and a.baseline_pairs is None:
        print("★ **未量，不是通过**（rc=4）—— 基线 %d 对是在 %d 人名册上测的，现在是 %d 人。"
              % (BASELINE_PAIRS, BASELINE_ROSTER, len(members)))
        return 4
    nonempty = sum(1 for m in members if str(m["divergence_text"]).strip())
    print("名册 **%d** 人；`divergence-map.md` 非空 **%d** 人（%.0f%%）"
          % (len(members), nonempty, 100 * nonempty / max(1, len(members))))
    if nonempty < MIN_NONEMPTY_RATE * len(members):
        print("★ **未量，不是通过**（rc=4）—— 扫描面塌了：非空率低于 %.0f%%" % (100 * MIN_NONEMPTY_RATE))
        return 4

    pairs = pair_set(B, members)
    n = len(members)
    total = n * (n - 1) // 2
    fam = {m["canonical_name"]: m["identity_family_id"] for m in members}
    cross = [p for p in pairs if fam.get(p[0]) != fam.get(p[1])]
    byfam = collections.Counter(fam.get(p[0]) for p in pairs if fam.get(p[0]) == fam.get(p[1]))

    print("可互相点名（全名或 slug 精确出现于 ≥40 字段落）的配对：**%d / %d = %.2f%%**"
          % (len(pairs), total, 100 * len(pairs) / max(1, total)))
    print("  同族 **%d**｜跨族 **%d**%s" % (len(pairs) - len(cross), len(cross),
          "　← **一个跨族的都没有**" if not cross else ""))
    print("  同族配对按族：%s" % dict(byfam))
    print("  ★ 而多样性配重要求同族第 2 人 base 领先 **0.1382** ⇒ **同族第二人基本进不来**。")
    print("    72 道 oracle 实测：队伍含可检出对的 **0/72**；同样大小的随机队伍中位 **22/72（30.6%)**")
    print("    （200 次重抽里 0 次 ≤0）⇒ **不是碰巧没凑到，是系统性分开**。此项本件不判，只披露。")

    print()
    if len(pairs) < floor:
        print("✗ **可检出配对数掉了**：%d < 地板 %d ⇒ 分歧检出正在静默失效" % (len(pairs), floor))
        return 1
    print("✓ 未低于地板：%d ≥ %d（**不代表分歧检得出来** —— 见上面的 0/72）" % (len(pairs), floor))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
