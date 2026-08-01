#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""动态伪共识：三个人物之间的一致率，与同一裸模型采样三次的一致率相比。

## 判据

对每道题，分别算两组的**组内两两相似度**：

- `persona_group` = {人物1, 人物2, 人物3} 的答案
- `bare_group`    = 裸模型独立采样三次的答案

若 `persona_mean ≈ bare_mean`，说明**这三个人物提供的分散程度，
与「同一个模型说三遍」没有区别**——即用户所说的
「结构化视角差异，不是真正独立的认知」。

## 这个度量的射程（必须一起说）

它用的是**词汇重叠**（中文双字词 + 英文词的 Jaccard），
**不是语义一致**。两个答案可以用词很不同而结论相同，反之亦然。

因此它只回答：**这三份文本有多像。**
「三人是否得出同一个结论」由盲判席另行回答——两者不可互相替代。

**用词汇度量的理由是它可复现、不引入第二个模型的判断。**
把它当唯一证据是错的；不给它、只给模型判断也是错的。
"""
import itertools
import json
import pathlib
import re
import sys

TOKEN = re.compile(r"[a-zA-Z]{3,}|[一-鿿]{2}")


def toks(t: str) -> set:
    return set(TOKEN.findall(t.lower()))


def jac(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if a and b else 0.0


def group_mean(answers: list) -> float:
    """一组答案的组内两两相似度均值。"""
    ts = [toks(a) for a in answers]
    pairs = [jac(x, y) for x, y in itertools.combinations(ts, 2)]
    return sum(pairs) / len(pairs) if pairs else 0.0


def main() -> int:
    SP = pathlib.Path(__file__).resolve().parent
    L = lambda n: json.loads((SP / n).read_text(encoding="utf-8"))
    persona = [L(f"ans_p{i}.json") for i in (1, 2, 3)]
    bare = [L(f"ans_bare{i}.json") for i in (1, 2, 3)]
    tasks = sorted(persona[0])

    rows = []
    for t in tasks:
        p = group_mean([g[t] for g in persona])
        b = group_mean([g[t] for g in bare])
        rows.append((t, p, b))
    P = sum(r[1] for r in rows) / len(rows)
    B = sum(r[2] for r in rows) / len(rows)

    print("动态伪共识（词汇重叠口径）")
    print(f"  三人物组内一致率均值   {P:.4f}")
    print(f"  裸模型三次采样一致率   {B:.4f}")
    print(f"  差               {P - B:+.4f}")
    print()
    print("  逐题（人物组 / 裸模型组 / 差）：")
    for t, p, b in rows:
        flag = "  ← 人物组更趋同" if p > b else ""
        print(f"    {t}  {p:.4f} / {b:.4f} = {p - b:+.4f}{flag}")
    print()
    if P >= B:
        print("  ★ 判读：三个人物之间的措辞分散**不高于**同一模型说三遍。")
        print("     按用户所提的口径，这一组**未提供可测量的独立信号**。")
    else:
        print(f"  ★ 判读：人物组比裸模型组分散 {B - P:.4f}——存在可测量的差异化，")
        print("     但**词汇分散不等于认知独立**，结论一致性由盲判席另行回答。")
    json.dump({"persona_intra_mean": round(P, 4), "bare_intra_mean": round(B, 4),
               "diff": round(P - B, 4),
               "per_task": [{"task": t, "persona": round(p, 4), "bare": round(b, 4)} for t, p, b in rows],
               "口径": "中文双字词 + 英文词的 Jaccard；**测词汇重叠不测语义一致**"},
              open(SP / "pseudo_consensus_result.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
