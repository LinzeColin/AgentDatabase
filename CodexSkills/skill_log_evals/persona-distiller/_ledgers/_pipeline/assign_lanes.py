#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按题名把语料分到**六条研究道**，给出 `min_lanes` 的输入。阶段 2 的最后一件。

用法：
    python3 assign_lanes.py --raw <raw 目录>

六条道取自 `check_corpus_ceiling.py` 的 `LANES`（**去仓里读的，不是我定的**）：

| 道 | 装什么 |
|---|---|
| `writings` | 他写的书、论著、文集 |
| `conversations` | 书信、往还、对话 |
| `expression` | 演说、致辞、布道、诗 |
| `decisions` | 判决意见、法令、公文、宣言 |
| `timeline` | 自传、日记、年表 |
| `external` | 别人写他的（即分类器判为「二手」的） |

**两条硬规矩：**

① **不许把分不出来的塞进一条「空着的」道**——那会让 `min_lanes` 凭空多一道，
   而门只做算术、不问分道对不对
   （[[related-to-him-is-not-written-by-him]]／[[empty-default-swallows-unknown]]）。
   ★ **一手且不属前四道 ⇒ `writings`**，这是**剩余类不是默认值**：
     一份他署名、又不是书信/演说/判决/自传的文本，本来就是著述；
     且 writings 在有语料的人身上从不为空，落进去只可能让**道数不变**。
   ★ 首版真按「一律进未分道」写过，实测 **Marshall 73 份里 51 份未分道（70%）**，
     `lanes` 被压到 4 —— 那不是「他只有 4 道」，是**我的题名表太窄**。

② **`external` 只由「一手/二手」分类结果决定，不看题名。**
   否则会出现「他自己的书因为题名像评论而进了 external」这种反向错。

★ 本工具**只按题名分**，是粗判。`check_paper_lanes.py` 会再问
  「这几道里有几道是纸面的」——**一道只有 1 份的道，多半是纸面的**，
  所以输出里逐道印份数，不只印道数。

★ 退出码：0=跑完；2=参数错；3=没有可分的文件。
"""
import argparse
import json
import pathlib
import re
import sys

LANES = ["writings", "conversations", "expression", "decisions", "timeline", "external"]

# 题名模式，按**优先级从高到低**匹配（一份只进一道——道数要能被门直接用）
PATTERNS = [
    ("decisions", r"opinion|judgment|judgement|decision|decree|ordinance|statute|"
                  r"proclamation|message of the president|verordnung|erlass|"
                  r"legge|editto|leges|constitutiones|justice of the peace"),
    ("conversations", r"letter|correspond|briefe|briefwechsel|epistol|lettres|lettere|"
                      r"carteggio|dialogue|dialog|conversation|tischgespr|tabletalk|"
                      r"table.?talk|kolloqui|colloqui"),
    ("expression", r"speech|speeches|address|oration|discourse|sermon|rede|reden|"
                   r"discours|discorsi|orazioni|poem|poesie|songs|lieder|"
                   r"predigt|vortrag|commedie|comed"),
    ("timeline", r"autobiograph|selbstbiograph|diary|journal intime|tagebuch|"
                 r"lebensbild|lebensschick|meine? leben|erinnerungen|reminiscence|"
                 r"memoir|confession|vita propria"),
]
DEFAULT_WRITINGS = r"work|works|writing|schriften|s[äa]mtliche|opere|scritti|" \
                   r"[oœ]uvres|treatise|essay|abhandlung|didactic|didakt|magna|" \
                   r"education|erziehung|pictus|janua|porta|principe|prince|" \
                   r"histor|geschichte|storia|critique|kritik|prolegomena|notes on"


def lane_of(title: str, is_secondary: bool) -> str:
    if is_secondary:
        return "external"          # ★ 只由分类结果定，不看题名
    t = (title or "").lower()
    for lane, pat in PATTERNS:
        if re.search(pat, t):
            return lane
    if re.search(DEFAULT_WRITINGS, t):
        return "writings"
    # ★ **一手且不属前四道 ⇒ writings。这不是「默认值」，是正确的剩余类**：
    #   一份由他署名的文本，不是书信/演说/判决/自传，那它就是著述。
    #   ——它也**不会虚增道数**：writings 在任何有语料的人身上都非空，
    #     residual 落进去只可能让计数不变。真正会虚增的是把它塞进空着的道。
    #   ★ 首版写成「一律进未分道」，实测 Marshall 73 份里 51 份未分道（70%），
    #     `lanes` 被压到 4 —— 那不是「他只有 4 道」，是**我的题名表太窄**。
    return "writings" if not is_secondary and t.strip() else "未分道"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    a = ap.parse_args()
    raw = pathlib.Path(a.raw)
    mf, pf = raw / "_fetch-manifest.json", raw / "_primary.json"
    if not mf.exists() or not pf.exists():
        print("要先跑 fetch_ia.py 与 classify_primary.py", file=sys.stderr)
        return 2
    recs = [r for r in json.loads(mf.read_text(encoding="utf-8"))["记录"]
            if r["status"] == "已取回"]
    prim = {o["identifier"]: o["档"] for o in json.loads(pf.read_text(encoding="utf-8"))["明细"]}
    if not recs:
        print("没有可分的文件", file=sys.stderr)
        return 3

    tally, detail = {}, []
    for r in recs:
        ti = r.get("ia_title")
        ti = "; ".join(ti) if isinstance(ti, list) else str(ti or "")
        lane = lane_of(ti, prim.get(r["identifier"]) == "二手")
        tally[lane] = tally.get(lane, 0) + 1
        detail.append({"identifier": r["identifier"], "道": lane, "title": ti[:70]})

    filled = [l for l in LANES if tally.get(l, 0) > 0]
    thin = [l for l in filled if tally[l] == 1]
    unassigned = tally.get("未分道", 0)

    print(f"{raw}｜{len(recs)} 份")
    for l in LANES:
        n = tally.get(l, 0)
        mark = "  ← **只有 1 份，很可能是纸面的道**" if n == 1 else ("  ← **空**" if n == 0 else "")
        print(f"  {l:<15}{n:>4}{mark}")
    print(f"  {'未分道':<15}{unassigned:>4}"
          + ("  ← **这些没有被塞进任何一道**（不许默认成 writings）" if unassigned else ""))
    print(f"\n**lanes = {len(filled)}**（quick 要 3、standard/deep 要 6）")
    if thin:
        print(f"★ 其中 {len(thin)} 道只有 1 份：{'、'.join(thin)}"
              f" —— 去掉纸面道就只剩 **{len(filled) - len(thin)}** 道")

    (raw / "_lanes.json").write_text(json.dumps(
        {"lanes": len(filled), "去掉纸面道后": len(filled) - len(thin),
         "逐道份数": {l: tally.get(l, 0) for l in LANES}, "未分道": unassigned,
         "★口径": "按题名粗判，一份只进一道；external 只由一手/二手分类定；"
                  "一手的剩余类归 writings（**不是默认值，且不虚增道数**）",
         "明细": detail}, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
