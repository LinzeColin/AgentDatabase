#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给台账分 holdout —— 盲判的密封面。

用法：
    python3 assign_holdout.py --workspace <ws> --raw <raw> [--frac 0.15] [--apply]

不带 `--apply` 只印方案，**不动台账**。

## 规则（三条，缺一不可）

① **只选「内容上不与任何别的源重合」的份 —— 而「重合」要用判据自己那把尺子量。**

   ★★ 首版用 `dedup_corpus.py` 的簇当代理（整份文档 min-hash Jaccard ≥0.55），
   选出 11 份，跑 `check_holdout_overlap` 的结果是：

       ✗ **非样板的连续逐字段 13265 处 ≥ 50（最长 1079 词）**
         ——多到无法逐段避开，该 holdout 必须换掉。

   **两把尺子量的不是一回事**：dedup 量**整份**的相似度，
   overlap 门量**最长连续逐字段**。林肯的语料是好几套互相重印的全集，
   整份 Jaccard 不到 0.55，而里面同一批书信讲词**逐字一样**。
   ⇒ 本工具改用**同一把尺子**：按「这一份有多大比例的 k 词片在别处也出现」排序，
     取最低的几份。**代理指标会骗人，用判据自己的量。**

② **逐道按比例取，不许集中在一道。**
   一道全被密封会让那条道在研究阶段直接消失。

③ **一手（P1/P2）优先。** 二手密封起来测不出「他会不会说这些」。

④ ★★ **已经在研究稿里引用过的源，一份都不能密封。**
   研究稿会印出它的 `source_id` 与引文正文——密封它等于把 holdout 正文
   摊在研究方读得到的文件里，这正是 `check_holdout_mention` 要抓的东西。
   实测：首版方案把 `src-3176773929d7`（02-conversations 的 O-2）与
   `src-32716caed453`（03-expression 的 O-1）都选了进去。

⑤ ★ **不许抽空一条道。** 每道至少留 1 份在 train。
   实测：Lincoln 的 `timeline` 只有 1 份，而 `max(1, 总数×比例)` 把它整条抽走了——
   那条道会在研究稿里凭空消失（[[empty-default-swallows-unknown]] 的又一形态：
   「这道没有源」与「这道被我密封了」在下游看起来一模一样）。

★ **不猜、不凑数**：候选不够就少分几份并**把缺口印出来**，
  **绝不为了达到 `--frac` 去放宽 ①**
  （[[no-blocking-on-gate-shortfall]]：达不到就写台账继续，但不放宽判据）。

★★ 分完**必须重跑** `check_holdout_overlap`；本工具只写 `split`，不自证清白。

★ 退出码：0=有方案；2=参数错；3=**一份合格候选都没有**（要换源，不是调这里）。
"""
import argparse
import collections
import hashlib
import json
import pathlib
import re
import sys

WS = re.compile(r"\s+")
K = 25          # k 词片；overlap 门看 ≥50 词的连续段，25 足以侦测且更严
SAMPLE = 5      # 抽样率 1/5，**按哈希值抽**（见 shingles 的注释：按位置抽会漏 4/5）


def shingles(text: str) -> set:
    """k 词片的**按哈希值抽样**（不是按位置）。

    ★★★ 首版写的是 `for i in range(0, …, 5)` —— **按位置每 5 个取一个**。
    那是错的：两份文档若在共享段上的**起始偏移模 5 不同**，
    采样到的 k 词片**一个都不会重合**，哪怕它们逐字相同。
    漏报概率 4/5。

    实测（Kant #179，2026-08-12）：按位置抽样算出**中位重合率 0.0%**，
    据此选的 11 份 holdout 送进 `check_holdout_overlap`，
    结果是 **503 处 ≥50 词的连续逐字段，最长 3096 词**。
    **一个 3096 词的逐字段，在我的指标里是 0%。**

    ⇒ 改为**按哈希值抽样**（`h % SAMPLE == 0`）：同一段文字无论落在哪个偏移上，
      被抽中的那些 k 词片都一样，**与对齐无关**。抽样率不变，漏报没了。
    """
    w = WS.sub(" ", text).lower().split()
    out = set()
    for i in range(max(1, len(w) - K + 1)):
        h = hashlib.blake2b(" ".join(w[i:i + K]).encode(), digest_size=8).digest()
        if h[0] % SAMPLE == 0:          # ★ 按值抽样，与位置无关
            out.add(h)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--raw", required=True)
    ap.add_argument("--frac", type=float, default=0.15)
    ap.add_argument("--max-overlap", type=float, default=0.05,
                    help="允许的逐字片重合率上限（默认 5%%）")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    ws, raw = pathlib.Path(a.workspace), pathlib.Path(a.raw)
    led = ws / "evidence" / "source-ledger.jsonl"
    ded = raw / "_dedup.json"
    if not led.is_file() or not ded.is_file():
        print("缺 source-ledger.jsonl 或 _dedup.json", file=sys.stderr)
        return 2

    recs = [json.loads(l) for l in led.read_text(encoding="utf-8").splitlines() if l.strip()]
    clusters = json.loads(ded.read_text(encoding="utf-8")).get("重复簇", [])
    in_cluster = {i for cl in clusters for i in cl}

    # ④ 研究稿里已经出现过的 source_id —— 一份都不能密封
    cited = set()
    rd = ws / "references" / "research"
    if rd.is_dir():
        for f in rd.glob("*.md"):
            body = f.read_text(encoding="utf-8", errors="replace")
            # Scope 节是台账的机械投影，**不算「引用过」**；只看它之后的部分
            k = body.find("## Source-linked observations")
            if k >= 0:
                for r in recs:
                    if r["source_id"] in body[k:]:
                        cited.add(r["source_id"])

    def ident(r):
        return r["locator"].split()[-1]

    base = [r for r in recs
            if not r.get("derived_from")
            and ident(r) not in in_cluster
            and r.get("tier") in ("P1", "P2")
            and r["source_id"] not in cited]              # ④
    if not base:
        print("**一份合格候选都没有**", file=sys.stderr)
        return 3

    # ① 用判据那把尺子：算每一份「有多少 k 词片在别处也出现」
    sk = {}
    for r in recs:
        f = raw / pathlib.Path(r["local_path"]).name
        if f.is_file():
            sk[r["source_id"]] = shingles(f.read_text(encoding="utf-8", errors="replace"))
    overlap = {}
    for r in base:
        mine = sk.get(r["source_id"]) or set()
        if not mine:
            overlap[r["source_id"]] = 1.0
            continue
        others = set()
        for o in recs:
            if o["source_id"] != r["source_id"]:
                others |= sk.get(o["source_id"], set())
        overlap[r["source_id"]] = len(mine & others) / len(mine)
    cand = [r for r in base if overlap[r["source_id"]] <= a.max_overlap]
    print(f"★ 逐字片重合率：候选 {len(base)} 份里 ≤{a.max_overlap:.0%} 的有 **{len(cand)}** 份"
          f"（中位 {sorted(overlap.values())[len(overlap) // 2]:.1%}）")
    if not cand:
        lo = min(overlap.values())
        print(f"**没有一份的逐字片重合率 ≤{a.max_overlap:.0%}**（最低 {lo:.1%}）——"
              "这批语料出不了干净的 holdout，**正解是换源，不是调这里的阈值**。",
              file=sys.stderr)
        return 3
    if not cand:
        print("**一份合格候选都没有** —— 每一份都与别的源内容重合。"
              "正解是换源，不是放宽本工具的规则。", file=sys.stderr)
        return 3

    by_lane = collections.defaultdict(list)
    for r in cand:
        by_lane[(r.get("dimensions") or ["?"])[0]].append(r)
    lane_total = collections.Counter((r.get("dimensions") or ["?"])[0] for r in recs)

    picked, gaps = [], []
    for lane, rows in sorted(by_lane.items()):
        # ⑤ 至少给这条道留 1 份在 train
        want = min(max(1, round(lane_total[lane] * a.frac)), lane_total[lane] - 1)
        if want <= 0:
            gaps.append(f"**{lane} 只有 {lane_total[lane]} 份，全部留 train**（不抽空任何一道）")
            continue
        rows.sort(key=lambda r: (overlap[r["source_id"]], r["source_id"]))  # 重合最低的优先
        take = rows[:want]
        picked += take
        if len(take) < want:
            gaps.append(f"{lane} 想取 {want} 只有 {len(take)}")
    # 一道都没候选的，单独报
    for lane, n in lane_total.items():
        if lane not in by_lane:
            gaps.append(f"**{lane} 一份合格候选都没有**（{n} 份全在重复簇里或全是二手）")

    print(f"台账 {len(recs)} 条｜研究稿已引用 {len(cited)} 条（**排除**）｜"
          f"合格候选 {len(cand)} 条｜拟密封 {len(picked)} 条（目标 {a.frac:.0%}）")
    print(f"{'道':<16}{'总数':>5}{'候选':>5}{'拟取':>5}")
    for lane in sorted(lane_total):
        print(f"{lane:<16}{lane_total[lane]:>5}{len(by_lane.get(lane, [])):>5}"
              f"{sum(1 for p in picked if (p.get('dimensions') or [''])[0] == lane):>5}")
    if gaps:
        print("⚠️ 缺口（**没有放宽规则去补**）：" + "；".join(gaps))
    print("\n拟密封：" + "、".join(p["source_id"] for p in picked))

    if not a.apply:
        print("\n（未加 --apply，台账未改）")
        return 0

    ids = {p["source_id"] for p in picked}
    for r in recs:
        r["split"] = "holdout" if r["source_id"] in ids else "train"
    led.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in recs) + "\n",
                   encoding="utf-8")
    print(f"\n已写回台账：holdout {len(ids)} 条、train {len(recs) - len(ids)} 条")
    print("★ **现在必须重跑 check_holdout_overlap 与 emit_lane_scope**"
          "（Scope 节只投影 train，密封的要从研究稿里消失）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
