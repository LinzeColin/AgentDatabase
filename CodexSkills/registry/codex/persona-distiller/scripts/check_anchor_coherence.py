#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""锚点内容一致性检查 —— 断言改了、渲染它的段落有没有跟着改（RUNBOOK 第六十种）。

## 与 `check_claim_anchors.py` 的分工

`check_claim_anchors.py` 查的是**引用关系**：锚点在不在、有没有孤儿、有没有幽灵。
这一件查的是**内容一致**：锚点之后的那段正文，讲的还是不是这条断言。

Robertson #97 实测抓到：`contradiction/否定注脚` 那条断言我按原文订正过
（从「他从未把两者并置讨论」改成「他一口气把三件事连说」），
`claims.jsonl` 改对了，而 `divergence-map.md` 里渲染它的整节还是旧文本——
**两处直接互相否定，而所有的门都是绿的**（锚点在、计数对、无孤儿）。

根因是生成器里 claim 正文与文档正文是两处独立的字面量，改一处不带动另一处。

## 判据：中文字符三元组覆盖率

`断言的三元组 ∩ 锚点后 WIN 字的三元组 / 断言的三元组`

**为什么是中文三元组而不是关键词**：第一版我用「英文引文片段 + 英文专有名词」当标记，
结果**中文正文渲染中文断言的地方全部误报**——
断言里的标记是 `New Zealand`，而正文写的是「新西兰」。
**判据用错了语言，就会把正常的当异常、把异常的埋进噪声里。**

换成三元组后：Robertson #97 的 43 处锚点覆盖率中位数 53.6%，
而那处真错是 1.1%，排最低第三位——**真问题浮到了顶上**。

## 阈值不是硬门

低覆盖率有合法情形：锚点所在小节是**指针段**（「见 persona.md 的对照表」），
或断言几乎全是英文引文而正文用中文转述。
所以本工具**只列不判**，但它列出的东西必须逐条看完——
Robertson #97 那一处如果按「都是中英混排的噪声」划掉，就漏了。
"""
import argparse, contextlib, io, json, pathlib, re, sys, tempfile

CJK = re.compile(r"[一-鿿]+")
STOP = set("的了是在和与不也都这那有为对从而其本条种个把被就要必须一二三四五六七八九十")
ANCHOR = re.compile(r"<!-- claim:(clm-[0-9a-f]{12}) -->")
WIN, LOW = 1400, 0.10


def grams(s: str, n: int = 3) -> set:
    out = set()
    for run in CJK.findall(s):
        run = "".join(c for c in run if c not in STOP)
        for i in range(len(run) - n + 1):
            out.add(run[i:i + n])
    return out


def check(ws: pathlib.Path) -> int:
    cl = {c["claim_id"]: c for c in
          (json.loads(l) for l in (ws / "evidence/claims.jsonl")
           .read_text(encoding="utf-8").splitlines() if l.strip())}
    rows = []
    for f in sorted(ws.glob("*.md")):
        t = f.read_text(encoding="utf-8")
        for m in ANCHOR.finditer(t):
            cid = m.group(1)
            if cid not in cl:
                print(f"  ✗ 幽灵锚点 {f.name} {cid}")
                return 2
            g = grams(cl[cid]["claim"])
            cov = len(g & grams(t[m.end():m.end() + WIN])) / max(1, len(g))
            rows.append((cov, f.name, cid))
    if not rows:
        print("✗ 没有找到任何锚点"); return 2
    rows.sort()
    med = rows[len(rows) // 2][0]
    low = [r for r in rows if r[0] < LOW]
    print(f"锚点 {len(rows)} 处，中文三元组覆盖率中位数 {med:.1%}\n")
    print(f"覆盖率最低的 {min(6, len(rows))} 处：")
    for cov, f, cid in rows[:6]:
        print(f"   {cov:6.1%}  {f:<22} {cid}")
        print(f"           {re.sub(chr(92)+'s+', ' ', cl[cid]['claim'])[:88]}…")
    print(f"\n低于 {LOW:.0%} 的 {len(low)} 处 —— **只列不判，须逐条看完**。")
    print("  合法情形：指针段（「见 X.md」）、断言几乎全是英文引文而正文用中文转述。")
    print("  不合法情形：断言改过而这一节没跟着改（RUNBOOK 第六十种）。")
    return 0


def self_test() -> int:
    """负对照：同义改写必须算高覆盖，互相否定的两段必须算低覆盖。"""
    a = "他在同一段话里把规则和它的失效条件连着说出来了"
    same = "这一段里他把规则连着失效条件一起说了出来，没有分开"
    opp = "外部报道对他的评价集中在业绩下滑那两年，没有涉及任何方法层面的内容"
    g = grams(a)
    c1 = len(g & grams(same)) / len(g)
    c2 = len(g & grams(opp)) / len(g)
    print("══ 负对照 ══")
    print(f"  {'✓' if c1 >= LOW else '✗'} 同义改写覆盖 {c1:.1%}（应 ≥{LOW:.0%}）")
    print(f"  {'✓' if c2 < LOW else '✗'} 无关文本覆盖 {c2:.1%}（应 <{LOW:.0%}）")
    missed = int(not (c1 >= LOW and c2 < LOW))

    # ══════════════════════════════════════════════════════════════
    # ㉑ ★★★ `check()` 本身 —— 2026-08-12 之前它一次也没被自测进入过
    # ══════════════════════════════════════════════════════════════
    #
    # 上面两条验的是 `grams()`（**配料**）：三元组这把尺子准不准。
    # 而 `check()` 才是**读工作区、找锚点、判幽灵、排序、划低覆盖那批**的那一段。
    # `check_selftest_reach` 把本件列在「验了配料、没验判决」的名单上——它是对的：
    # 尺子准，不代表拿尺子的手量对了东西。
    #
    # ★ 造夹具的顺序（[[counter-example-red-can-be-red-by-coincidence]]）：
    #   先把夹具喂给 `check()` 看它**报出东西**，再写断言；不是写完断言再去验。
    print("\n══ ㉑ check() 本体（tempdir 上跑真流程）══")

    def _ws(d: pathlib.Path, claims: list, docs: dict) -> pathlib.Path:
        (d / "evidence").mkdir(parents=True, exist_ok=True)
        (d / "evidence/claims.jsonl").write_text(
            "\n".join(json.dumps(c, ensure_ascii=False) for c in claims) + "\n", encoding="utf-8")
        for name, body in docs.items():
            (d / name).write_text(body, encoding="utf-8")
        return d

    def _run(claims, docs):
        with tempfile.TemporaryDirectory() as td:
            d = _ws(pathlib.Path(td), claims, docs)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = check(d)
            return rc, buf.getvalue()

    C1 = "clm-0123456789ab"
    C2 = "clm-ba9876543210"
    A1 = "他在同一段话里把规则和它的失效条件连着说出来了"
    SAME = "这一段里他把规则连着失效条件一起说了出来，没有分开讲"
    # ★ 这一对取自 Robertson #97 的真事故：断言按原文订正过，而渲染它的整节还是旧文本。
    A2 = "他一口气把三件事连着说完，中间没有停顿也没有分开讨论"
    STALE = "他从未把那两者并置讨论过，两个话题在他笔下始终各自独立出现"

    rc, out = _run([{"claim_id": C1, "claim": A1}],
                   {"a.md": f"<!-- claim:{C1} -->\n{SAME}\n"})
    ok = rc == 0 and "锚点 1 处" in out
    print(f"  {'✓' if ok else '✗'} ㉑a 正常工作区（1 处锚点、同义渲染）→ rc=0 且报出锚点数（rc={rc}）")
    missed += not ok

    rc, out = _run([{"claim_id": C1, "claim": A1}],
                   {"a.md": f"<!-- claim:{C2} -->\n{SAME}\n"})
    ok = rc == 2 and "幽灵锚点" in out
    print(f"  {'✓' if ok else '✗'} ㉑b 锚点指向不存在的断言 → **幽灵锚点**、rc=2（rc={rc}）")
    missed += not ok

    rc, out = _run([{"claim_id": C1, "claim": A1}], {"a.md": "正文里一个锚点都没有。\n"})
    ok = rc == 2 and "没有找到任何锚点" in out
    print(f"  {'✓' if ok else '✗'} ㉑c 一个锚点都没有 → rc=2，**不许静默报绿**（rc={rc}）")
    missed += not ok

    # ㉑d ★★★ 本件的立身之本：**断言改了、渲染它的段落没跟着改**。
    #   两条锚点一好一坏，坏的那条必须落进「低于 10%」那批，且排最低。
    rc, out = _run([{"claim_id": C1, "claim": A1}, {"claim_id": C2, "claim": A2}],
                   {"a.md": f"<!-- claim:{C1} -->\n{SAME}\n\n<!-- claim:{C2} -->\n{STALE}\n"})
    ok = rc == 0 and "低于 10% 的 1 处" in out and out.index(C2) < out.index(C1)
    print(f"  {'✓' if ok else '✗'} ㉑d **正文没跟着断言改** → 恰好 1 处低于 10%，且它排最低"
          f"（{'低于 10% 的 1 处' in out=}）")
    missed += not ok

    # ㉑e 反向：两条都同义渲染 ⇒ 低覆盖 0 处。**没有它，㉑d 可能只是「什么都报低」**。
    rc, out = _run([{"claim_id": C1, "claim": A1}, {"claim_id": C2, "claim": A2}],
                   {"a.md": f"<!-- claim:{C1} -->\n{SAME}\n\n<!-- claim:{C2} -->\n{A2}\n"})
    ok = rc == 0 and "低于 10% 的 0 处" in out
    print(f"  {'✓' if ok else '✗'} ㉑e 反向：两条都渲染对了 → 低覆盖 **0 处**"
          f"（否则 ㉑d 只是「什么都报低」）")
    missed += not ok

    # ㉑f 射程：锚点分布在**多份** .md 里，两份都要被扫到（`glob("*.md")` 而非只读一份）。
    rc, out = _run([{"claim_id": C1, "claim": A1}, {"claim_id": C2, "claim": A2}],
                   {"a.md": f"<!-- claim:{C1} -->\n{SAME}\n",
                    "b.md": f"<!-- claim:{C2} -->\n{STALE}\n"})
    ok = rc == 0 and "锚点 2 处" in out and "b.md" in out
    print(f"  {'✓' if ok else '✗'} ㉑f 射程：锚点散在两份 .md → 两份都扫到（锚点 2 处、点名 b.md）")
    missed += not ok

    print("\n  ✓ 全部通过" if not missed else
          f"\n  ✗ {missed} 条不合——本检查器已失效，不得依赖其结论")
    return 0 if not missed else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", type=pathlib.Path)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        sys.exit(self_test())
    if not a.workspace:
        ap.error("--workspace 必填（除非 --self-test）")
    sys.exit(check(a.workspace))
