#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""语义残留扫描 —— 按事实的因果／归属方向查，不按被改掉的那句话查。

## 为什么需要这个（RUNBOOK 第十六种）

Jesse Vincent #94：同一个「文章催生了 Prophet」的因果错误，在产物里有四份，
措辞各不相同（据此推出／据此动手／催生／并据此做了）。
按被改掉的原句做字符串扫描，只抓到前两份；后两份一份靠评委、一份靠语义模式。

## 两个反向陷阱（都在同一轮踩过，都必须防）

① **订正后的文本必然提到那个概念**——「跨模型**不是**他的做法」会命中「跨模型…做法」。
   不做否定语境豁免，误报会淹没真命中（本轮 8 命中里 7 个是误报，
   唯一的真命中差点被当噪声划掉）。
② **模式写窄会把真事实误判为伪造**。核 `double-ESC` 时 grep `double[\s\-]?esc` 得 0，
   差点删掉一个真引文——原文是 `double- ESC`（HTML 转文本留下的空格）。
   **所以本脚本只用于查「错误说法是否残留」，不用于证明「某说法不存在」。**

③ **baseline 字段里本来就该有错误**——那是故意写差的对照答案，
   评测靠它证明候选优于平庸解。不排除 baseline，每个人物都会误报，
   而**一个天天喊狼来了的检查，等于没有检查**。

## 负对照（`--self-test`，RUNBOOK 第十八种）

本脚本是**硬门**，而它有一个特有的失效方式：**否定语境豁免可能吃掉真命中**。
Jesse Vincent #94 第一版报 8 处，其中 7 处是订正本身（误报），
唯一的真命中（`boundaries.md`）差点被当噪声划掉——
换句话说，**豁免调松一点就会漏掉那唯一有价值的一条**。

所以负对照要测两件事，缺一不可：
  ① 植入一句典型的「残留」，必须抓到；
  ② 植入一句「订正后的否定表述」，必须豁免掉（否则误报会淹没真命中）。

实测：2/2 通过。**改动 NEG 正则或 WIN 窗口后必须重跑**——
这两个参数一动，①②的平衡就变了，而变坏了不会有任何报错。

用法：
    python3 check_semantic_residue.py --workspace <dir> [--extra a.json b.json] --rules rules.json
    python3 check_semantic_residue.py --self-test          # 只跑负对照，不需要 workspace
rules.json 形如 {"规则名": "正则"}；正则匹配的应是**错误的语义方向**。
"""
import argparse, json, pathlib, re, sys

# 命中点邻近若出现这些词，说明该处是在否定／限定该说法，不算残留
# 命中点邻近若出现这些词，说明该处是在否定／限定／反驳该说法，不算残留。
# ★「其实是／看起来像／假象／取样」这一组是 Salatin #95 补的——
#   当时产物在**反驳**「他近年高产」，而反驳句里必然要复述那个说法，
#   旧词表挡不住，于是报了 2 处误报。
NEG = re.compile(r"(不是|不得|不算|并非|非其|早于|已做|已经做了|明说|归于|其本人|"
                 r"一手|须|记为失败|不可|而不是|并不|无关|区别|切割|"
                 r"其实|实际上|看起来像|假象|取样|答不了|查不了|推不出|"
                 # ★「写反了／最初写的是／被推翻」这一组是 Salatin #95 补的——
                 #   研究车道的职责之一就是**记录被推翻的判断**，
                 #   它必须复述旧说法才能说清改了什么。不豁免就会把订正记录本身报成残留。
                 r"写反了|最初写|原本写|被推翻|已订正|订正为|改成|是错的|是假的|证明是假|事后证明|不成立|"
                 # ★「不要／不许／禁止／勿／切忌／别写成」这一组是 Robertson #97 补的——
                 #   旧词表只有**否定断言**族（不是／并非／不算），没有**祈使禁止**族。
                 #   而 boundaries.md / decision-policy.md 的职责恰恰是**把错误说法原样引出来再禁止它**
                 #   （「不要合并成「看空所以退出」」）。缺这一族，边界文档越尽责误报越多。
                 r"不要|不许|不应|禁止|勿|切忌|别写|误写|误判|错误的?说法|常见错误|容易被写成|最容易写错)")
WIN = 90  # 否定语境窗口（单侧字符数）

# 这些 JSON 字段按设计就含错误说法（baseline 是故意写差的对照答案），一律不扫
SKIP_FIELDS = {"baseline", "baseline_answer", "decoy", "wrong_answer"}


def scannable(path: pathlib.Path) -> str:
    """结构化文件按字段筛后再拼回文本；纯文本原样返回。

    只做一层：把 baseline 一类「按设计含错误」的字段剔掉，其余字段拼成一个串。
    偏移量因此不等于原文偏移——报告里只用它区分同名命中，不用于定位。
    """
    raw = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix not in (".json", ".jsonl"):
        return raw
    try:
        objs = ([json.loads(l) for l in raw.splitlines() if l.strip()]
                if path.suffix == ".jsonl" else json.loads(raw))
    except (json.JSONDecodeError, ValueError):
        return raw  # 解析不了就整份扫，宁可误报不可漏报
    out = []

    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k in SKIP_FIELDS:
                    continue
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
        elif isinstance(o, str):
            out.append(o)

    walk(objs)
    return "\n".join(out)


def judge(texts: dict, pat: str, neg_exempt: bool = True) -> tuple:
    """**本件的判定函数**：一条规则扫过全部文本 → `([命中…], 被豁免的处数)`。

    ★★ 2026-08-12 从 `main()` 里提到模块级。原因不是整洁，是**自测重写了一份旧版**：
    `self_test()` 里那段 `rx.search` + `NEG.search` 与这里**不是同一套判定**——
    它**没有剥 Markdown 强调符那一步**。也就是说下面这个真实漏判

        「此说是**错的**」

    ——`**` 插在「是」与「错的」之间，把豁免词「是错的」整词打断，
    于是一条**明确写着被推翻**的历史引用会被当成残留。
    这个修法**只在 `main()` 里**，而自测验的是没修的那一版：
    删掉下面那行 `re.sub`，旧自测照样全绿。

    ★ 这里原先举的例子是「事后证明是**假的**」，**它不承力**——
      `事后证明` 自己就在 `NEG` 里，剥不剥强调符都会被豁免。
      2026-08-12 补自测时靠变异测试当场发现（删掉 `re.sub` 仍是一条都没红），已换。

    ⇒ [[a-checker-nothing-calls-is-not-a-checker]] 的同族：
      **自测必须调被保证的那段真代码**，抄一份等于没测。
    """
    rx, hits, exempted = re.compile(pat), [], 0
    for f, t in texts.items():
        for m in rx.finditer(t):
            ctx = t[max(0, m.start() - WIN):m.end() + WIN]
            # ★ 先剥 Markdown 强调符再匹配否定语境（见 docstring 里的真实漏判）。
            #   与第三十种同源：**判据依赖字面连续，而排版会切断字面。**
            ctx = re.sub(r"[*_`~]+", "", ctx)
            if neg_exempt and NEG.search(ctx):
                exempted += 1
                continue
            name = getattr(f, "name", str(f))
            hits.append((name, m.start(), m.group(0)[:70]))
    return hits, exempted


# (规则, 应被抓到的残留句, 应被豁免的订正句)
SELF_TEST = [
    (r"(长文|该文|这篇文章)[^。\n]{0,40}(催生|据此|促成)[^。\n]{0,25}(Prophet|P2P)",
     "2009 年那篇长文催生了 P2P 数据库 Prophet。",
     "2009 年那篇长文提到 P2P 数据库 Prophet，但该项目早于该文，不是那篇文章催生的。"),
    (r"第三方[^。\n]{0,30}120,?000",
     "第三方在不同时点引为 27,000／120,000／186,000。",
     "120,000 是其本人一手数字，不是第三方；第三方给的是 27,000 与 186K。"),
    # ★ Robertson #97 加：**祈使禁止族**。第三条负对照专门盯这一族——
    #   残留句是陈述（该抓），订正句是把同一说法引出来加以禁止（该豁免）。
    #   加这一条之前，边界文档里每一句「不要写成 X」都会被报成残留。
    (r"看空所以(退出|清盘)",
     "他看空所以退出，把资本还给了投资人。",
     "三层必须分开，不要合并成「看空所以退出」——他自陈退出理由是不懂这个市场。"),
]


def self_test() -> int:
    """两向负对照：残留必须抓到，订正后的否定表述必须豁免。"""
    print("══ 负对照（**跑真 `judge()`，不再抄一份判定逻辑**）══")
    fail = 0
    for pat, residue, corrected in SELF_TEST:
        caught = bool(judge({"残留.md": residue}, pat)[0])
        exempted = not judge({"订正.md": corrected}, pat)[0]
        print(f"  {'✓' if caught else '✗'} 抓到残留: 「{residue[:44]}…」")
        print(f"  {'✓' if exempted else '✗'} 豁免订正: 「{corrected[:44]}…」")
        fail += (not caught) + (not exempted)

    # ══════════════════════════════════════════════════════════════
    # ㉙ `judge()` 与 `scannable()`/`walk()`
    #    —— 2026-08-12 之前这三个从没被自测进入过
    # ══════════════════════════════════════════════════════════════
    print("\n── ㉙a **Markdown 强调符打断豁免词**（真实漏判，此前无自测）──")
    # `**` 插在「是」与「错的」之间 → 豁免词整词被切断 →
    # 一条明确写着被推翻的历史引用会被当成残留。
    #
    # ★★ 2026-08-12 造夹具时的一处更正：第一版我照抄了 docstring 里的
    #   「事后证明是**假的**」，而**变异测试当场证明它不承力**——
    #   `事后证明` 自己就在 `NEG` 里，剥不剥强调符都会被豁免。
    #   删掉那行 `re.sub` 重跑，自测**一条都没红**。
    #   换成下面这句（不剥时 `NEG` 零命中、剥后才命中 `是错的`）才验得成。
    #   ⇒ [[counter-example-red-can-be-red-by-coincidence]]：
    #     **夹具要让被验的那一步成为唯一的承力点**，否则「绿」什么也没证明。
    _P = r"看空所以(退出|清盘)"
    _MD = "他看空所以退出，此说是**错的**。"
    _ok = not judge({"a.md": _MD}, _P)[0]
    print(f"  {'✓' if _ok else '✗'} ㉙a 「是**错的**」（星号插在豁免词中间）→ **仍被豁免**")
    fail += not _ok
    # 反向：同一句去掉否定语境 ⇒ 必须报。否则上面只是「什么都不报」。
    _ok = bool(judge({"a.md": "他看空所以退出，把资本还给了投资人。"}, _P)[0])
    print(f"  {'✓' if _ok else '✗'} ㉙a′ 反向：去掉否定语境 → **仍要报**（不是什么都不报）")
    fail += not _ok

    print("── ㉙b `--no-neg-exempt`：关掉豁免要能把它们全放回来 ──")
    _h, _e = judge({"a.md": _MD}, _P, neg_exempt=False)
    _ok = len(_h) == 1 and _e == 0
    print(f"  {'✓' if _ok else '✗'} 关掉豁免 → 命中 {len(_h)}、豁免计数 {_e}"
          f"（**用它复核豁免有没有吃掉真命中**）")
    fail += not _ok

    print("── ㉙c `scannable()`：baseline 一类字段按设计不扫 ──")
    import tempfile as _tf
    _d = pathlib.Path(_tf.mkdtemp())
    _RES = "他看空所以退出，把资本还给了投资人。"
    (_d / "p.json").write_text(json.dumps(
        {"candidate": "他自陈不懂这个市场。", "baseline": _RES}, ensure_ascii=False),
        encoding="utf-8")
    _t = scannable(_d / "p.json")
    _ok = "不懂这个市场" in _t and _RES not in _t
    print(f"  {'✓' if _ok else '✗'} `baseline` 字段被剔掉、`candidate` 留下"
          f"（baseline 是**故意写差的对照答案**，扫它必然误报）")
    fail += not _ok

    # ㉙d `walk()` 要递归进嵌套 dict/list——否则深层正文整片扫不到
    (_d / "n.jsonl").write_text(json.dumps(
        {"rows": [{"text": _RES}], "meta": {"note": "别的"}}, ensure_ascii=False) + "\n",
        encoding="utf-8")
    _t = scannable(_d / "n.jsonl")
    _ok = _RES in _t and "别的" in _t
    print(f"  {'✓' if _ok else '✗'} ㉙d `walk()` 递归进 list/dict（深层正文也要被扫到）")
    fail += not _ok

    # ㉙e ★ 解析不了的 JSON **整份照扫**（宁可误报不可漏报）——这条口径要钉住
    (_d / "bad.json").write_text("{not json at all " + _RES, encoding="utf-8")
    _t = scannable(_d / "bad.json")
    _ok = _RES in _t
    print(f"  {'✓' if _ok else '✗'} ㉙e JSON 解析不了 → **整份照扫**（宁可误报不可漏报）")
    fail += not _ok

    # ㉙f ★ 射程声明：`.md` 原样返回，**里面的 `baseline:` 字样不会被剔掉**。
    #    这不是缺陷、是射程——写成断言，免得下一个人以为 md 里也筛过。
    (_d / "x.md").write_text("baseline: " + _RES, encoding="utf-8")
    _ok = _RES in scannable(_d / "x.md")
    print(f"  {'✓' if _ok else '✗'} ㉙f 射程：`.md` 原样返回，**md 里的 baseline 字样不筛**")
    fail += not _ok

    print(f"\n  ✓ 负对照通过" if not fail
          else f"\n  ✗ {fail} 项未过——本检查器已失效，其「0 残留」不构成证据")
    return fail


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true", help="只跑负对照")
    ap.add_argument("--workspace", type=pathlib.Path)
    ap.add_argument("--extra", nargs="*", default=[], type=pathlib.Path)
    ap.add_argument("--rules", type=pathlib.Path)
    ap.add_argument("--no-neg-exempt", action="store_true",
                    help="关闭否定语境豁免——用于核查豁免本身是否吃掉了真命中")
    a = ap.parse_args()
    if a.self_test:
        return 1 if self_test() else 0
    if not a.workspace or not a.rules:
        ap.error("--workspace 与 --rules 必填（除非用 --self-test）")

    rules = json.loads(a.rules.read_text(encoding="utf-8"))
    files = sorted(set(list(a.workspace.rglob("*.md")) + list(a.workspace.rglob("*.jsonl"))
                       + list(a.workspace.rglob("*.json")) + list(a.extra)))
    texts = {f: scannable(f) for f in files}

    total, exempted = 0, 0
    for name, pat in rules.items():
        hits, ex = judge(texts, pat, neg_exempt=not a.no_neg_exempt)
        exempted += ex
        print(f"  {'✓' if not hits else '✗'} {name}: {len(hits)}")
        for fn, pos, s in hits[:4]:
            print(f"        {fn}@{pos}: {s}")
        total += len(hits)

    print(f"\n扫描 {len(files)} 个文件 / {len(rules)} 条规则")
    print(f"否定语境豁免 {exempted} 处" + ("" if a.no_neg_exempt else "（用 --no-neg-exempt 复核）"))
    print("✓ 0 语义残留" if not total else f"✗ {total} 处残留")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
