#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""抓源台账生成 —— **把每人一份的 `build_*_ledger.py` 收成共享件**。

## 为什么收

本件的逻辑已经手写过两遍（Barton #117、Blackwell #118），形状完全一样，
只有数据不同。而今天刚在 `assemble_*_results.py` 上付过一次代价：
**每人一份的临时脚本不在 `scripts/` 下、不进任何门、没有自测**，
Blackwell 那次「除以 10 做两遍」就是这么活下来的。

**规矩是：出现第 2 个人要用同一段逻辑时就收成共享件，不要复制一份改三个变量。**

## 它做什么

调用方给一张**纯数据**表（每份来源一条），本件负责：

1. **落盘**：`raw/<短名>/<短名>.txt`，并按 sha256 去重
   （同一份下了两次会被跳过并报出，不是静默合并）
2. **写 9 列台账**：格式照 `_corpora/_next/LEDGER_FORMAT.md`，
   制表符分隔、第 7 列分档不许空、第 8 列归属标记恰好一个、第 9 列以 `lane=` 开头
3. **自检**：分档只许 P1/P2/S1/S2/U；道只许六条之一；归属标记恰好一个；
   短名与目录名一致——**任一条不过就退出，不写半份台账**
4. **报计量**：分档分布、道分布、**一手去重后的份数**
   （P2 是重复见证，计入 primary 但必须让人一眼看出去重后是多少）

## 它不做什么

- **不判档**。分档由调用方给，本件只校验取值合法。
  「不许在入库环节把 S1 提成 P1」那条纪律**属于调用方**，本件管不了。
- **不判道**。同上。
- **不判「该不该合并」**。sha256 相同的直接跳过；**内容高度重合但字节不同的只报不拦**
  ——单篇文章被收进合集、同一本书的两个扫描源，都是**真实关系**不是错误。
"""
import argparse
import hashlib
import json
import pathlib
import re
import shutil
import sys
import zlib

TIERS = {"P1", "P2", "S1", "S2", "U"}
# ★★ v0.0.0.94：权利依据必须**具名**，不许只写「公有领域」或留空。
#   起因（2026-08-04 全量实测）：102 个交付包 7,629 条来源记录里，
#   `rights` 明说公有领域的只有 585 条（7.7%）；医疗护理师 13 个工作区里
#   **8 个一条依据都没记**。★ 但那多半是**记录缺口不是权利问题**
#   （Jenner 18 世纪、Koch/Virchow 19 世纪印本，按 1929 年前出版显然成立）。
#   这一条只管**记录口径**——权利口径本身是待裁定 ⑧，本件不替它下结论。
RIGHTS_GROUNDS = {
    "sec105":          "17 U.S.C. §105 联邦职务作品（须有在职证据）",
    "notice1909":      "1909 年法：1978 年前出版且无版权标记（须报核验强度）",
    "pre1929":         "1929 年前出版，版权已过期",
    "congressional":   "国会记录/听证，GPO 印无标记",
    "unpublished_303": "17 U.S.C. §303 未刊作品：卒年+70，下限 2003-01-01",
    "publicly-accessible": "公开可读、无付费墙、未绕过访问控制——**这不是公有领域**",
    "other":           "以上都不是，须在 rights_note 里写清",
}
LANES = {"writings", "conversations", "expression", "external", "decisions", "timeline"}
ATTRIB = {"HIS-OWN", "CO-AUTHORED", "THIRD-PARTY", "ATTRIBUTION-UNCLEAR", "OTHER-INVENTOR"}
EXTRA_MARKS = {"POSTHUMOUS", "TRANSLATION", "DUPLICATE-SCAN", "OCR-POOR", "FULL-PAGE-SCAN"}


_WORD = re.compile(r"[a-z0-9\u4e00-\u9fff]+")
_SHINGLE, _SAMPLE = 8, 6


def _shingles(text: str) -> set:
    """8-gram，crc32 确定性采样 1/6。**不能用内建 `hash()`**——它逐进程随机。"""
    w = _WORD.findall(text.lower())
    return {s for i in range(len(w) - _SHINGLE + 1)
            for s in [" ".join(w[i:i + _SHINGLE])]
            if zlib.crc32(s.encode()) % _SAMPLE == 0}


def near_duplicates(paths: dict, thr: float = 0.50) -> list:
    """★★ **sha256 抓不到扫描件与再版的塌缩**（v0.0.0.102）。

    起因：袁隆平 #123 实测两份同源 JPRS 扫描件——
    **精确子串比对完全零命中**，而 8-gram containment 给 **0.773**／**0.676**
    （两次 OCR 结果不同，归一化长度 154,679 vs 155,771）。

    拿 Blackwell #118 的真语料回验，**sha256 一对都没抓到，而这里抓到 4 对**：

    ```
    0.837  essays-medical-sociology-v2-1902 ↔ essays-v2-1902-ia   ← 同一本书的两个来源
    0.808  essays-medical-sociology-v1-1902 ↔ essays-v1-1902-ia
    0.767  decay-municipal-govt-1885 ↔ essays-…-v2-1902           ← 单篇被收进该卷
    0.636  counsel-to-parents-1878   ↔ essays-…-v1-1902
    ```

    **分母取较短一侧**（containment 不是 Jaccard）——一篇短文完全落在一大卷里时，
    Jaccard 会被卷的长度稀释到看不见。

    ★ **只报不拦**：单篇收进合集、两个扫描源，都是**真实关系**。
    判「该不该并成一条」是调用方的事，本件只保证它**不会静默**。
    """
    sig = {}
    for short, path in paths.items():
        try:
            sig[short] = _shingles(path.read_text(encoding="utf-8", errors="ignore"))
        except OSError:
            continue
    names = sorted(sig)
    out = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            sa, sb = sig[a], sig[b]
            small = min(len(sa), len(sb))
            if not small:
                continue
            c = len(sa & sb) / small
            if c >= thr:
                out.append((round(c, 3), a, b))
    return sorted(out, reverse=True)


_LONG_S = "ſ"          # ſ —— Fraktur 长 s
_LS_RATE = 1e-4             # 出现率高于此视为「保留长 s 的那一版 OCR」


def ocr_variant_pairs(paths: dict, min_rate: float = _LS_RATE) -> list:
    """★★ **`near_duplicates` 的射程边界**（v0.0.0.104）——它在这类配对上会**整体归零**。

    起因：Liebig #124 清点时实测，**同一本书**（Liebig–Reuning 书信集）的两份独立扫描件
    containment = **0.0000，交集 0 个 shingle**；Kohut 传记两扫描件 0.0003。

    机理已定位到字符级：Google 扫描件里 `ſ` 出现 **0** 次（OCR 把它归一成 s），
    Toronto 扫描件出现 **14,367** 次（保留原字形）。而 `_WORD` 是 `[a-z0-9…]+`，
    **`ſ` 不在字符类里，它被当成分隔符**——于是 `waſſer` 切成 `wa`+`er`，
    `wasser` 是一个词。德文 8 词窗口几乎必含至少一个长 s，**逐窗全灭**。

    ★ 所以既有那条记忆「同源 OCR 精确匹配零命中、shingle 给 0.77」**只覆盖 Antiqua**。
    **Fraktur + 跨供应商时 shingle 自己也归零**，必须叠一层书目判重。
    Liebig 补上 6 对书目重复后，来源数 68 → 62。

    本件**不修**那个失效（改分词会动到已量过的所有人物），只**把失效说出来**：
    报出「这两份的长 s 出现率差一个量级以上」的配对，
    **在这些配对上 `near_duplicates` 的 0 分不可采信**。
    """
    rate = {}
    for short, path in paths.items():
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if text:
            rate[short] = text.count(_LONG_S) / len(text)
    names = sorted(rate)
    out = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            hi, lo = max(rate[a], rate[b]), min(rate[a], rate[b])
            if hi >= min_rate and lo < min_rate / 10:
                out.append((round(hi, 6), round(lo, 6), a, b))
    return sorted(out, reverse=True)


def independent_count(paths: dict, thr: float = 0.70) -> dict:
    """★ **「几份来源」与「几份独立来源」不是同一个数**（v0.0.0.103）。

    门数的是**份数**（deep ≥45）。而 Blackwell #118 实测 95 份里：

    ```
    阈值 0.50 → 独立 **69**／95　　0.70 → **77**／95　　0.85 → **91**／95
    最大的一组 11 份：《Essays》第二卷 + 该卷各篇的单行本 + 各篇的手稿 + 该卷的 IA 扫描
    ```

    **她在任何阈值下都还够 45，所以结论没变**——但**贴着门槛的人身上，这个差会决定过不过**。

    把 containment ≥ thr 的连成连通分量，分量数就是独立来源数。
    ★ **本件不替你选阈值**：三个都报，**因为哪个才算「同一份」是判断不是计算**。
    """
    nd = near_duplicates(paths, thr=thr)
    par = {k: k for k in paths}

    def find(x):
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x

    for _, a, b in nd:
        ra, rb = find(a), find(b)
        if ra != rb:
            par[ra] = rb
    groups = {}
    for k in paths:
        groups.setdefault(find(k), []).append(k)
    multi = {k: v for k, v in groups.items() if len(v) > 1}
    return {"阈值": thr, "落盘份数": len(paths), "**独立来源**": len(groups),
            "被合并的份数": sum(len(v) for v in multi.values()) - len(multi),
            "最大的一组": sorted(max(multi.values(), key=len)) if multi else []}


def validate(rows: list) -> list:
    """→ 问题列表；空表示都合法。**任一条不过，调用方就不该写台账。**"""
    bad, seen = [], set()
    for i, r in enumerate(rows):
        w = f"第 {i+1} 条（{r.get('short') or '无短名'}）"
        if not r.get("short"):
            bad.append(f"{w}：**短名为空**")
        elif r["short"] in seen:
            bad.append(f"{w}：**短名重复**")
        else:
            seen.add(r["short"])
        if r.get("tier") not in TIERS:
            bad.append(f"{w}：分档 `{r.get('tier')}` 不在 {sorted(TIERS)} 里")
        if r.get("lane") not in LANES:
            bad.append(f"{w}：道 `{r.get('lane')}` 不在六条道里")
        marks = set(str(r.get("mark") or "").split())
        n = len(marks & ATTRIB)
        if n != 1:
            bad.append(f"{w}：归属标记要**恰好一个**，实得 {n}（`{r.get('mark')}`）")
        if marks - ATTRIB - EXTRA_MARKS:
            bad.append(f"{w}：认不得的标记 {sorted(marks - ATTRIB - EXTRA_MARKS)}")
        if not str(r.get("why") or "").strip():
            bad.append(f"{w}：**第 9 列的依据为空**——不写依据等于没有依据")
        # ★ 权利依据必须具名。**「公有领域」是结论不是依据。**
        g = r.get("rights_ground")
        if not g:
            bad.append(f"{w}：**没写权利依据 `rights_ground`**——"
                       f"只许 {sorted(RIGHTS_GROUNDS)}；"
                       f"「公有领域」是结论不是依据，写它不算")
        elif g not in RIGHTS_GROUNDS:
            bad.append(f"{w}：权利依据 `{g}` 不具名，只许 {sorted(RIGHTS_GROUNDS)}")
        elif g == "other" and not str(r.get("rights_note") or "").strip():
            bad.append(f"{w}：`rights_ground=other` 必须在 `rights_note` 里写清是什么")
    return bad


def row_line(r: dict) -> str:
    """→ 一行 9 列台账。第 9 列以 `lane=` 开头，权利依据以 ` RIGHTS=` 附在末尾。"""
    note = f"lane={r['lane']}. {r['why']}"
    g = r.get("rights_ground")
    if g:
        note += f" RIGHTS={g}"
        if r.get("rights_note"):
            note += f"（{r['rights_note']}）"
    elif r.get("rights"):                      # 兼容旧调用方的自由文本
        note += f" RIGHTS={r['rights']}"
    return "\t".join([r["short"], r.get("url", ""), r.get("title", ""), str(r.get("year", "")),
                      r.get("locator", ""), r.get("lang", "en"), r["tier"], r["mark"], note])


def build(rows: list, src_dir: pathlib.Path, raw_dir: pathlib.Path, header: str,
          copy_files: bool = True) -> dict:
    """落盘 + 写台账 → 计量。**校验不过就抛，不写半份。**

    ★★ `copy_files=False`（CLI `--no-copy`，v0.0.0.108）：**只写台账，不复制正文**。

    起因：Liebig #124 的 `raw/` 里**每份存了两遍**、42 MB——
    本件写 `<short>/<short>.txt`，而 `ingest.py` 又写了一份 `src-XXXX/<原名>.txt`。
    两者都是「把语料落进工作区」，同时跑就是双份。

    **`ingest.py` 才是落文件的那一步**（`init_target` 打印的 `next` 里就是它，
    它还要算归一化文本、校验和、split）。本件的独有产出是**九列台账 TSV**。
    所以流水线该是：本件 `--no-copy` 出台账 → `ingest` 落文件。

    ★ 默认仍是 `True`——**已有调用方的行为不变**，要省那一份得显式说。
    """
    problems = validate(rows)
    if problems:
        raise SystemExit("✗ **台账校验未过，一行都没写**：\n  " + "\n  ".join(problems[:12]))

    raw_dir.mkdir(parents=True, exist_ok=True)
    lines, seen_sha, copied, skipped = [f"# {header}"], {}, 0, 0
    for r in rows:
        src = src_dir / r["file"]
        if not src.is_file():
            print(f"  ✗ 源文件不在：{r['file']}"); skipped += 1; continue
        sha = hashlib.sha256(src.read_bytes()).hexdigest()
        if sha in seen_sha:
            print(f"  ⚠ **{r['short']} 与 {seen_sha[sha]} 逐位相同，跳过**（同一份下了两次）")
            skipped += 1; continue
        seen_sha[sha] = r["short"]
        if copy_files:
            d = raw_dir / r["short"]; d.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, d / f"{r['short']}.txt")
        copied += 1
        lines.append(row_line(r))

    (raw_dir / "_ids.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # ★★ sha256 之外再看一次内容塌缩——只报不拦
    landed = {r["short"]: raw_dir / r["short"] / f"{r['short']}.txt" for r in rows
              if (raw_dir / r["short"] / f"{r['short']}.txt").is_file()}
    nd = near_duplicates(landed)
    if nd:
        print(f"  ⚠ **内容高度重合的 {len(nd)} 对**（sha256 抓不到；**只报不拦**）：")
        for c, a, b in nd[:8]:
            print(f"      {c:.3f}  {a} ↔ {b}")
        print("      ★ 单篇被收进合集、同一本书的两个扫描源，都是**真实关系**——"
              "由你判要不要并成一条，本件只保证它不静默。")
        print("  ★★ **「几份来源」与「几份独立来源」不是同一个数**——三个阈值都报，"
              "因为哪个才算「同一份」是判断不是计算：")
        for _thr in (0.50, 0.70, 0.85):
            _ic = independent_count(landed, thr=_thr)
            print(f"      阈值 {_thr:.2f} → 独立来源 **{_ic['**独立来源**']}** / "
                  f"{_ic['落盘份数']}（合并掉 {_ic['被合并的份数']} 份）")
        print("      ★ 门数的是**份数**（deep ≥45）。**贴着门槛的人身上，这个差会决定过不过。**")
    ov = ocr_variant_pairs(landed)
    if ov:
        print(f"  ⚠⚠ **{len(ov)} 对文件的长 s（ſ）出现率差一个量级以上**——"
              "这是两条不同的 OCR 管线（一条归一成 s，一条保留原字形）：")
        for hi, lo, a, b in ov[:6]:
            print(f"      {hi:.5f} vs {lo:.5f}   {a} ↔ {b}")
        print("      ★★ **在这些配对上，上面那个 containment 分数不可采信**——"
              "`ſ` 不在分词字符类里，被当成分隔符，德文 8 词窗口逐窗全灭，"
              "**同一本书也会得 0.0000**（Liebig #124 实测）。**这类重复只能靠书目判**。")
    body = lines[1:]
    tiers, lanes = {}, {}
    for l in body:
        c = l.split("\t")
        tiers[c[6]] = tiers.get(c[6], 0) + 1
        ln = c[8].split(".")[0].replace("lane=", "")
        lanes[ln] = lanes.get(ln, 0) + 1
    p1, p2 = tiers.get("P1", 0), tiers.get("P2", 0)
    grounds = {}
    for r in rows:
        g = r.get("rights_ground") or "（未写）"
        grounds[g] = grounds.get(g, 0) + 1
    return {("落盘" if copy_files else "**登记（未复制正文）**"): copied, "跳过": skipped, "台账行数": len(body), "权利依据": grounds,
            "分档": tiers, "道": lanes,
            "一手（P1+P2）": p1 + p2, "其中 P2 重复见证": p2, "**去重后一手**": p1}


# ══════════════════ 自测 ══════════════════

def selftest() -> int:
    import tempfile
    fails = []

    def chk(label, cond):
        print(("  ✓ " if cond else "  ✗ ") + label)
        if not cond:
            fails.append(label)

    ok = {"short": "a", "file": "a.txt", "tier": "P1", "mark": "HIS-OWN",
          "lane": "writings", "why": "扉页署名", "rights_ground": "pre1929"}

    print("── 正向：合法的一条不报 ──")
    chk("一条不报", not validate([ok]))

    print("── 反向对照 ①：分档不在白名单 → 报出 ──")
    chk("tier=P9 报出", any("分档" in p for p in validate([dict(ok, tier="P9")])))

    print("── 反向对照 ②：道不在六条里 → 报出 ──")
    chk("lane=misc 报出", any("六条道" in p for p in validate([dict(ok, lane="misc")])))

    print("── ★ 反向对照 ③：归属标记两个或零个都要报 ──")
    chk("两个 → 报出",
        any("恰好一个" in p for p in validate([dict(ok, mark="HIS-OWN THIRD-PARTY")])))
    chk("零个 → 报出", any("恰好一个" in p for p in validate([dict(ok, mark="POSTHUMOUS")])))
    chk("一个 + 附加标记 → **不报**（DUPLICATE-SCAN 是合法附加）",
        not validate([dict(ok, mark="HIS-OWN DUPLICATE-SCAN")]))

    print("── ★ 反向对照 ④：第 9 列依据为空 → 报出（不写依据等于没有依据）──")
    chk("why 为空 → 报出", any("依据为空" in p for p in validate([dict(ok, why="  ")])))

    print("── 反向对照 ⑤：短名重复 → 报出 ──")
    chk("两条同短名 → 报出", any("短名重复" in p for p in validate([ok, dict(ok, file="b.txt")])))

    print("── ★★ 反向对照 ⑩：sha256 抓不到的塌缩，shingle 要抓到（v0.0.0.102）──")
    base = "the quick brown fox jumps over the lazy dog and then runs far away again today " * 12
    import tempfile as _tf
    with _tf.TemporaryDirectory() as _d:
        _r = pathlib.Path(_d)
        (_r / "a.txt").write_text(base, encoding="utf-8")
        (_r / "b.txt").write_text(base.replace("lazy", "1azy"), encoding="utf-8")   # OCR 式差异
        (_r / "c.txt").write_text("completely different words here nothing shared at all " * 12,
                                  encoding="utf-8")
        nd = near_duplicates({"a": _r / "a.txt", "b": _r / "b.txt", "c": _r / "c.txt"})
        pairs = {(x[1], x[2]) for x in nd}
        chk(f"**OCR 式差异（lazy→1azy）被抓到**：{nd[:1]}", ("a", "b") in pairs)
        chk("★ 不相干的两份**不报**", ("a", "c") not in pairs and ("b", "c") not in pairs)
        import hashlib as _h
        chk("★★ 而它们的 sha256 **不同**——这正是 sha256 抓不到的那一类",
            _h.sha256((_r/"a.txt").read_bytes()).hexdigest()
            != _h.sha256((_r/"b.txt").read_bytes()).hexdigest())

    print("── ★★ 反向对照 ⑪：独立来源数（v0.0.0.103）──")
    with _tf.TemporaryDirectory() as _d:
        _r = pathlib.Path(_d)
        # ★ 夹具必须是**不重复**的文本：重复短语去重后剩不了几个 8-gram，
        #   再按 1/6 采样就几乎为空——第一版就栽在这，三条断言全红。
        _b2 = " ".join(f"w{i:04d}" for i in range(600))
        (_r / "x.txt").write_text(_b2, encoding="utf-8")
        (_r / "y.txt").write_text(_b2.replace("w0100", "wO100"), encoding="utf-8")  # OCR 式差异
        (_r / "z.txt").write_text(" ".join(f"q{i:04d}" for i in range(600)), encoding="utf-8")
        _ic = independent_count({"x": _r/"x.txt", "y": _r/"y.txt", "z": _r/"z.txt"})
        chk(f"3 份 → **独立 {_ic['**独立来源**']}**（x/y 同源合成一组）", _ic["**独立来源**"] == 2)
        chk(f"被合并 {_ic['被合并的份数']} 份", _ic["被合并的份数"] == 1)
        chk(f"最大的一组 {_ic['最大的一组']}", set(_ic["最大的一组"]) == {"x", "y"})
    _ic2 = independent_count({})
    chk("空输入不崩，独立来源 0", _ic2["**独立来源**"] == 0)

    print("── ★★ 反向对照 ⑫：shingle 在跨 OCR 管线的长 s 上**自己归零**（v0.0.0.104）──")
    with _tf.TemporaryDirectory() as _d:
        _r = pathlib.Path(_d)
        # 同一段德文，两条 OCR 管线：一条保留 ſ，一条归一成 s。**内容完全一样**。
        _de = " ".join(f"waſſer{i:03d} und daſ feld beſteht aus ſtoff{i:03d}" for i in range(120))
        (_r / "keep.txt").write_text(_de, encoding="utf-8")
        (_r / "norm.txt").write_text(_de.replace("ſ", "s"), encoding="utf-8")
        _pair = {"keep": _r / "keep.txt", "norm": _r / "norm.txt"}
        _nd = near_duplicates(_pair, thr=0.01)
        chk(f"**同一段文字，shingle 判为不重复**（这正是那个失效）：{_nd}", not _nd)
        _ov = ocr_variant_pairs(_pair)
        chk(f"★ 而本件把这一对**报了出来**：{_ov}", len(_ov) == 1)
        # ★ 非空对照：同管线的两份不许被误报
        (_r / "keep2.txt").write_text(_de.replace("feld", "fe1d"), encoding="utf-8")
        chk("★ 同管线的两份（都保留 ſ）**不报**",
            not ocr_variant_pairs({"keep": _r / "keep.txt", "keep2": _r / "keep2.txt"}))
        chk("★★ 而同管线那一对 shingle **抓得到**——证明失效只出在跨管线",
            near_duplicates({"keep": _r / "keep.txt", "keep2": _r / "keep2.txt"}, thr=0.01))

    print("── ★★ 反向对照 ⑨：权利依据必须具名（v0.0.0.94）──")
    chk("不写 rights_ground → 报出",
        any("没写权利依据" in p for p in
            validate([{k: v for k, v in ok.items() if k != "rights_ground"}])))
    chk("**写「公有领域」不算依据** → 报出",
        any("不具名" in p for p in validate([dict(ok, rights_ground="公有领域")])))
    chk("rights_ground=other 但没写 rights_note → 报出",
        any("写清是什么" in p for p in validate([dict(ok, rights_ground="other")])))
    chk("other + note → 不报",
        not validate([dict(ok, rights_ground="other", rights_note="馆方书面授权，件号 X")]))
    chk("**publicly-accessible 是合法取值**（它不是 PD，但记录口径认它）",
        not validate([dict(ok, rights_ground="publicly-accessible")]))

    print("── ★★ 反向对照 ⑥：校验不过时**一行都不写** ──")
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d); (root / "src").mkdir(); (root / "src" / "a.txt").write_bytes(b"x")
        raw = root / "raw"
        try:
            build([dict(ok, tier="P9")], root / "src", raw, "h")
            wrote = True
        except SystemExit:
            wrote = False
        chk("抛出且 `raw/_ids.txt` 不存在", not wrote and not (raw / "_ids.txt").exists())

    print("── ★ 反向对照 ⑦：逐位相同的两份只落一份，且**报出来**不静默 ──")
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d); s = root / "src"; s.mkdir()
        (s / "a.txt").write_bytes(b"same"); (s / "b.txt").write_bytes(b"same")
        info = build([ok, dict(ok, short="b", file="b.txt")], s, root / "raw", "h")
        chk(f"落盘 {info['落盘']} 份、跳过 {info['跳过']} 份、台账 {info['台账行数']} 行",
            info["落盘"] == 1 and info["跳过"] == 1 and info["台账行数"] == 1)

    print("── ★ 反向对照 ⑧：P2 计入一手，但去重后的数要单独报 ──")
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d); s = root / "src"; s.mkdir()
        for n in "abc":
            (s / f"{n}.txt").write_bytes(n.encode())
        info = build([ok,
                      dict(ok, short="b", file="b.txt", tier="P2", mark="HIS-OWN DUPLICATE-SCAN"),
                      dict(ok, short="c", file="c.txt", tier="S1", mark="THIRD-PARTY")],
                     s, root / "raw", "h")
        chk(f"一手 {info['一手（P1+P2）']}、其中 P2 {info['其中 P2 重复见证']}、"
            f"去重后 {info['**去重后一手**']}",
            info["一手（P1+P2）"] == 2 and info["**去重后一手**"] == 1)

    print(f"\n{'✓ 自测全过' if not fails else f'✗ **{len(fails)} 项未过**'}")
    return 0 if not fails else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rows", help="纯数据的 JSON 数组，每条含 short/file/tier/mark/lane/why 等")
    ap.add_argument("--src", help="源文件所在目录")
    ap.add_argument("--raw", help="要写入的 raw/ 目录")
    ap.add_argument("--header", default="corpus ledger", help="台账首行注释")
    ap.add_argument("--no-copy", action="store_true",
                    help="**只写台账，不复制正文**——落文件交给 `ingest.py`，"
                         "否则同一份会在 raw/ 里存两遍（Liebig #124 实测 42 MB）")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return selftest()
    if not (a.rows and a.src and a.raw):
        ap.error("要么 --self-test，要么给齐 --rows/--src/--raw")

    rows = json.loads(pathlib.Path(a.rows).read_text(encoding="utf-8"))
    info = build(rows, pathlib.Path(a.src), pathlib.Path(a.raw), a.header,
                 copy_files=not a.no_copy)
    for k, v in info.items():
        print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
