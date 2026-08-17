#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""在册产物里，有多少人有**盲测 delta 证据**？—— 现算，不看散文。

为什么要有这份文件
------------------
Owner 的评分写着「**已证实的决策增益：不足 40%**」。这是个可以直接测的数，
而此前没有任何东西在测它。2026-08-17 现算的结果是 **2%**：

    在册产物 102 人
      ├ 有诚实 delta 读数的：**2**（Carver +0.3791、Shewhart +0.1822）
      └ 没有的：**100（98%）**

三个互相独立的方向核过，结论一致：

1. `collect_honest_delta.py`（「诚实 delta 的唯一口径」）扫 `_corpora`，
   26 个工作区有判分读数、23 个带 baseline 臂 —— 其中**只有 2 个**能对应到在册产物。
2. **102 份 `registration.json` 里含 `delta` 字样的：0 份。**
3. **102 份 `team-card.json` 同样不带 delta。**

★★ 注意「有判分读数」的那 23 人**大多不是在册产物** —— 他们是
**拒发／延后**的候选（判了分、没过门、没入册）。所以那批读数的分布
（均值 +0.0624、35% 为负）**不是已发货产物的分布**，两者不能混为一谈。
[[counts-need-their-cutoff-stated]]

## 这个数能说什么、不能说什么

**能说**：仓里对 100/102 个在册产物**没有任何盲测 delta 证据**。
任何「这些人物比裸模型强」的说法，对其中 98% 都没有仓内证据支撑。

**不能说**：不能断言「它们从没被测过」。95 个在册产物在 `_corpora` 里
**连工作区都没有** —— 语料本来就不进 git，可能测过而读数没留下来。
但**证据要留在仓里，不是留在某次终端会话里**：留不下来的读数，
对今天要做判断的人等于不存在。
[[evidence-must-live-in-the-repo-not-the-terminal]]｜[[corpus-lives-outside-git-verify-the-pointers]]

用法
----
    python3 check_registered_products_have_delta_evidence.py --self-test
    python3 check_registered_products_have_delta_evidence.py \\
        --registry-root <persona-distiller-group> --corpora <_corpora>

本件**只报数，不设阈值**，永远 rc=0 —— 阈值与结论由 Owner 定。
"""
import argparse
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent


def workspace_key(name: str) -> str:
    """`wip-carver-127` -> `carver`；`wip-godin` -> `godin`。

    只在末段是**纯数字**时才剥掉它 —— 早期我用 `rsplit("-",1)[0]` 无条件剥，
    会把 `wip-roberts-austen` 削成 `wip-roberts`。
    """
    stem = name[4:] if name.startswith("wip-") else name
    parts = stem.rsplit("-", 1)
    return parts[0] if len(parts) == 2 and parts[1].isdigit() else stem


def products(registry_root: pathlib.Path) -> list[dict]:
    return json.loads((registry_root / "team-index.json").read_text(encoding="utf-8"))["products"]


def delta_readings(corpora: pathlib.Path) -> tuple[dict[str, float], dict[str, float]]:
    """跑权威口径 `collect_honest_delta.py`，不自己重实现。返回 (干净, 污染)。

    仓里已经有这把尺子；再造一把只会得到第二个不一致的数。
    [[i-built-a-second-ruler-while-the-authoritative-one-sat-in-scripts]]
    """
    import subprocess
    tool = None
    for cand in (HERE.parents[3] / "registry/codex/persona-distiller/scripts/collect_honest_delta.py",):
        if cand.is_file():
            tool = cand
            break
    if tool is None:
        raise SystemExit("✗ 找不到权威口径 collect_honest_delta.py —— **不自己重实现**，停")
    def _run(extra):
        out = subprocess.run([sys.executable, str(tool), str(corpora), "--json"] + extra,
                             capture_output=True, text=True)
        if out.returncode != 0:
            raise SystemExit("✗ 权威口径跑失败 rc=%d：%s" % (out.returncode, out.stderr.strip()[:300]))
        data = json.loads(out.stdout[out.stdout.find("{"):])["人物"]
        got = {}
        for name, row in data.items():
            base = (row.get("臂") or {}).get("baseline")
            if isinstance(base, (int, float)):
                got[workspace_key(name)] = float(base)
        return got

    # ★★ **干净的和污染的必须分开报。**
    #   权威口径默认**只标记不剔除**「看过 rubric 才写基线」的读数。
    #   本件第一版直接用了默认值，于是把 3 个污染读数算进「有证据」，
    #   报出 5/102 = 5% —— 而站得住的是 **2/102 = 2%**。
    #   那 3 个值是 +0.8013 / +0.7393 / +0.7350，**高得离谱本身就是污染的特征**。
    #   [[implausibly-good-result-is-a-defect-report]]｜[[self-report-is-not-evidence]]
    all_readings = _run([])
    clean = _run(["--exclude-tainted"])
    tainted = {k: v for k, v in all_readings.items() if k not in clean}
    return clean, tainted


def selftest() -> int:
    bad = []
    cases = [("wip-carver-127", "carver"), ("wip-godin", "godin"),
             ("wip-roberts-austen", "roberts-austen"), ("carver-127", "carver"),
             ("wip-nightingale-112", "nightingale")]
    for raw, want in cases:
        got = workspace_key(raw)
        if got != want:
            bad.append("workspace_key(%r) = %r，应为 %r" % (raw, got, want))
    # ★ 反对照：末段不是数字时**不许**剥
    if workspace_key("wip-roberts-austen") == "wip-roberts":
        bad.append("★ 末段非数字也被剥掉了")
    for b in bad:
        print("  ✗ " + b)
    print("自测 %d/%d" % (len(cases) + 1 - len(bad), len(cases) + 1))
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--registry-root")
    ap.add_argument("--corpora")
    ap.add_argument("--self-test", "--selftest", dest="selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not (a.registry_root and a.corpora):
        ap.error("要 --registry-root 与 --corpora，或只跑 --self-test")

    root = pathlib.Path(a.registry_root).resolve()
    corp = pathlib.Path(a.corpora).resolve()

    # ★★ 先印扫描面 —— 2026-08-17 同一天四次「我选了一个扫描面当成全世界」。
    print("扫描面：")
    print("  在册名册：%s/team-index.json" % root)
    print("  语料根　：%s" % corp)
    print("  delta 口径：persona-distiller/scripts/collect_honest_delta.py（**权威口径，不重实现**）")

    prods = products(root)
    deltas, tainted = delta_readings(corp)
    # ★ 2026-08-17：这一行原写「语料工作区 %d 个」而数的是 `corp.glob("wip-*")`
    #   —— 那是 **wip 目录数（75）**，不是**工作区数（54）**。
    #   两者差 21：22 个 wip 目录**根本没有 workspaces/**，另有 3 个工作区
    #   藏在 `ws-*/` 这类不叫 `workspaces` 的名字下。
    #   **标签写的是 A，数的是 B** —— 同日已因这一族订正五次。
    #   改法：两个数都印，各自贴对标签；工作区数走**权威发现**
    #   `workspace_roots.iter_workspaces`（按 `evidence/source-ledger.jsonl` 认，
    #   不按目录名），不再自己 glob。[[counts-need-their-cutoff-stated]]
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    try:
        from workspace_roots import iter_workspaces
        n_ws = len(iter_workspaces(corp))
    except Exception as exc:                                    # noqa: BLE001
        n_ws = "**未核（%s）**" % type(exc).__name__
    print("  在册 %d 人｜wip 目录 %d 个｜**工作区 %s 个**（权威发现）｜"
          "baseline 臂读数：干净 %d 个＋**污染 %d 个**"
          % (len(prods), len(list(corp.glob("wip-*"))), n_ws, len(deltas), len(tainted)))
    print("  （污染＝已知「看过 rubric 才写基线」；权威口径默认只标记不剔除，本件**分开报**）")

    with_delta, without = [], []
    for p in prods:
        slug = p["subject_slug"]
        hit = next((k for k in deltas if k and k in slug), None)
        (with_delta if hit else without).append((slug, deltas.get(hit)))

    n = len(prods)
    print("\n══ 在册产物的盲测 delta 证据")
    print("   有：**%d / %d = %.0f%%**" % (len(with_delta), n, 100 * len(with_delta) / max(n, 1)))
    for slug, d in sorted(with_delta, key=lambda x: -(x[1] or 0)):
        print("     ✓ %-34s %+.4f" % (slug, d))
    print("   无：**%d / %d = %.0f%%**" % (len(without), n, 100 * len(without) / max(n, 1)))

    # 污染读数单列 —— 它们**不算证据**，但要看得见，否则下一个人会重新把它们算进去
    t_hit = [(p["subject_slug"], tainted[k]) for p in prods
             for k in tainted if k and k in p["subject_slug"]]
    if t_hit:
        print("\n   ★★ 另有 **%d** 个在册产物**只有污染读数**（看过 rubric 才写基线）——"
              " **不计入上面的「有」**：" % len(t_hit))
        for slug, d in sorted(t_hit, key=lambda x: -x[1]):
            print("     ✗ %-34s %+.4f  ← 高得离谱本身就是污染的特征" % (slug, d))
        print("     ⇒ 若把它们算进去会报成 %d/%d = %.0f%%，**那个数不成立**。"
              % (len(with_delta) + len(t_hit), n, 100 * (len(with_delta) + len(t_hit)) / n))

    # 第二、第三个方向 —— 一个方向的结论不写进结案
    regs = list(root.rglob("registration.json"))
    cards = list(root.rglob("team-card.json"))
    reg_hit = sum(1 for r in regs if "delta" in r.read_text(encoding="utf-8").lower())
    card_hit = sum(1 for c in cards if "delta" in c.read_text(encoding="utf-8").lower())
    print("\n   交叉核（不同来源，应当一致）：")
    print("     registration.json %3d 份，含 delta 字样 **%d** 份" % (len(regs), reg_hit))
    print("     team-card.json    %3d 份，含 delta 字样 **%d** 份" % (len(cards), card_hit))

    # 有读数的那批 ≠ 已发货的那批，必须分开说
    unshipped = [k for k in deltas if not any(k in p["subject_slug"] for p in prods)]
    print("\n   ★ 有 delta 读数但**不在册**的：**%d** 个 —— 他们是拒发／延后的候选。"
          % len(unshipped))
    print("     ⇒ 那批读数的分布**不是已发货产物的分布**，两者不许混为一谈。")
    print("\n   ★ 射程：本件证明的是「**仓里没有证据**」，不是「从没测过」。")
    print("     语料不进 git；测过而读数没留下来，对今天要做判断的人等于不存在。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
