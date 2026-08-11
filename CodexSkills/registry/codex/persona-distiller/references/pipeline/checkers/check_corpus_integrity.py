#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**语料真伪门**：这个文件是语料，还是一张「取不到」的错误页？

## 它是被真实数据当场撞出来的

Jenner #104 抓源，48 个 URL 全部 `curl` 成功、全部有字节数，我据此报了
「**47 份、11 MB 一手为主的语料**」。**其中 4 份是 archive.org 的 HTML 错误页。**

| 文件 | 字节 | 真身 |
|---|---:|---|
| `McGillLibrary-osl_report-two-letters-edwar` | 146,097 | `<title>Internet Archive: Error</title>` |
| `jstor-106657` | 137,595 | `<title>Internet Archive: Page Not Found</title>` |
| `pam-3803` | 137,595 | 同上 |
| `india.history.resource.35308` | 137,595 | 同上 |

**146 KB 的「语料」**。一份 404 页比一本小册子还大——
**字节数是所有指标里最会骗人的那个：它对错误页和对真书一样有数。**

而它们**已经入了库**：`ingest.py` 收了，`source-ledger.jsonl` 记了 tier、算了校验和，
`primary_ratio` 把它们算进了分母。**归属门抓出了它们**——但报的是
「账本声称本人所著，文中查无归属证据」，**一个完全正确却完全误导的诊断**：
文中当然查无署名，因为文中根本不是那本书。

> 这是 RUNBOOK「报数前先跑一遍命令」的下一层：**我跑了命令。**
> 命令返回了 200，文件落了盘，字节数是四位数。
> **我没做的是打开来看一眼。**

## 判据四条

1. **HTML 文档** —— 开头 512 字节内出现 `<!DOCTYPE html`／`<html`。**硬拦。**
2. **明示的取不到** —— 出现 `404 Not Found`、`500 Internal Server Error`、
   `Page Not Found`、`Internet Archive: Error`、`Access Denied`、`Item not available`。**硬拦。**
3. **过短** —— 正文 < 2000 字节。**只报不拦**（真有极短的一手件，如单页布告）。
4. **可读字符占比过低** —— 字母数字加常见标点 < 55%，多半是二进制或彻底崩坏的 OCR。**只报不拦。**

## 射程（必须一起说）

- **它判「这是不是一份文档」，不判「这是不是这个人的文档」。**
  抓错了书、抓了同名者的书、抓了译本当原本——**本门一概看不见**，
  那是 `check_authorship.py` 与 `check_attribution_basis.py` 的事。
- 第 3、4 条**只报不拦**：OCR 质量差的真件确实存在（Jenner 那份 McGill 书信
  OCR 开头就是 `ie ie + t: 4 FROM BOUND BY MALTHY.O-%F ORD`，**但它是真的**）。
- **它不联网、不重取。** 它只看已经落盘的东西。

退出码：0 = 通过；1 = 有硬拦项；2 = 只有软报项；3 = 用法错误。
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

HTML_HEAD = re.compile(rb"<!DOCTYPE\s+html|<html[\s>]", re.I)
FETCH_FAIL = re.compile(
    r"404\s+Not\s+Found|500\s+Internal\s+Server\s+Error|502\s+Bad\s+Gateway"
    r"|Page\s+Not\s+Found|Internet\s+Archive:\s*Error|Access\s+Denied"
    r"|Item\s+not\s+available|The\s+item\s+is\s+not\s+available", re.I)
READABLE = re.compile(r"[A-Za-z0-9Ͱ-Ͽ一-鿿 .,;:!?'\"()\[\]\-—\n\r\t]")

MIN_BYTES = 2000
MIN_READABLE_RATIO = 0.55


def check_bytes(head: bytes, text: str, size: int) -> tuple[list[str], list[str]]:
    """→ (硬拦, 软报)"""
    hard, soft = [], []
    if HTML_HEAD.search(head[:512]):
        title = re.search(r"<title>([^<]{0,80})", text, re.I)
        hard.append(f"**是一张 HTML 页面，不是语料**"
                    + (f"（`<title>{title.group(1).strip()}`）" if title else ""))
    m = FETCH_FAIL.search(text[:4000])
    if m:
        hard.append(f"**正文里写着取不到**：`{m.group(0)}`")
    if size < MIN_BYTES:
        soft.append(f"过短：{size} 字节 < {MIN_BYTES}——**确认这是不是一份完整的件**")
    if text:
        ratio = len(READABLE.findall(text[:20000])) / min(len(text), 20000)
        if ratio < MIN_READABLE_RATIO:
            soft.append(f"可读字符占比 {ratio:.0%} < {MIN_READABLE_RATIO:.0%}"
                        f"——多半是二进制或彻底崩坏的 OCR")
    return hard, soft


def check_file(p: pathlib.Path) -> tuple[list[str], list[str]]:
    raw = p.read_bytes()
    return check_bytes(raw, raw.decode("utf-8", "replace"), len(raw))


# ── 负对照 ────────────────────────────────────────────────────────────
# ★ 真实样本：下面两条是 2026-08-02 抓 Jenner 语料时**实际落盘的文件开头**，
#   逐字复制，没有改动。它们当时都通过了 ingest 并进了 source-ledger。
REAL_IA_ERROR = '''<!DOCTYPE html>
<html lang="en">
<!-- __ _ _ _ __| |_ (_)__ _____
    / _` | '_/ _| ' \\| |\\ V / -_)
    \\__,_|_| \\__|_||_|_| \\_/\\___| -->
  <head data-release=b4aed820 data-node="www14.us.archive.org">
    <title>Internet Archive: Error</title>
'''
REAL_IA_404 = '''<!DOCTYPE html>
<html lang="en">
  <head data-release=-202631- data-node="ia601901.us.archive.org">
    <title>Internet Archive: Page Not Found</title>
'''
REAL_NGINX_500 = '''<html>
<head><title>500 Internal Server Error</title></head>
<body>
<center><h1>500 Internal Server Error</h1></center>
<hr><center>nginx</center>
</body>
</html>
'''
# ★ 真实样本：这一份 **OCR 烂到不像话，但它是真的**——
#   McGill 藏 1790 年 Jenner 书信的 djvu.txt 开头。**不许误杀。**
REAL_BAD_OCR = ('ie ie + t: 4 FROM BOUND BY MALTHY.O-%F ORD THE LIBRARY — a '
                'report and two letters of Edward Jenner and a letter of Mrs Jenner '
                'to the Rev. Mr. Ferryman, with observations on the cow pox and on '
                'the inoculation of the same, transcribed for the Osler Library. ') * 12


YEAR = re.compile(r"\b(1[5-9]\d{2}|20[0-2]\d)\b")


def year_mismatch(path: pathlib.Path) -> str:
    """文件名里的年份与扉页年份对不上 —— **只列不判**。

    ★ v0.0.0.43：本门的文件头一直写着自己看不见「抓错了书、抓了译本当原本」。
    这一条补上其中最便宜的一角：**文件名的年份不是版次年份。**

    Virchow #109 实测撞出：`cellularpath-1858-de-gutenberg` 的文件名写 1858，
    扉页写「**Vierte Auflage. Berlin, 1871**」——是第四版不是初版。
    我照文件名把它当初版写进了研究笔记，**从而把一句 1871 年才出现的拉丁公式
    （Omnis cellula e cellula）记到了 1858 年名下**；
    而 1858 初版（DTA 双录入全书 91.4 万字符）里那句拉丁话**一处都没有**。

    227 份里报出 15 处不符，其中 1 处是这种真错。**噪声不低，故只列不判。**
    """
    fn = set(YEAR.findall(path.parent.name)) or set(YEAR.findall(path.stem))
    if not fn:
        return ""
    try:
        head = path.read_text(encoding="utf-8", errors="replace")[:2500]
    except Exception:
        return ""
    tp = set(YEAR.findall(head))
    if not tp or (fn & tp):
        return ""
    return (f"文件名年份 {sorted(fn)} 与扉页年份 {sorted(tp)[:5]} 无交集"
            f"——**翻扉页核一次版次**")


def self_test() -> int:
    fails = []

    # ★ 真实样本 1–3：三张实际落盘的错误页 → 必须硬拦
    for name, sample in (("archive.org Error", REAL_IA_ERROR),
                         ("archive.org 404", REAL_IA_404),
                         ("nginx 500", REAL_NGINX_500)):
        b = sample.encode()
        hard, _ = check_bytes(b, sample, len(b))
        if not hard:
            fails.append(f"真实样本未抓出：{name}")

    # ★ 真实样本 4：OCR 极差的**真件** → 不许硬拦
    b = REAL_BAD_OCR.encode()
    hard, soft = check_bytes(b, REAL_BAD_OCR, len(b))
    if hard:
        fails.append(f"真实样本被误杀：OCR 差的真件不该硬拦，实得 {hard}")

    # 正对照：普通英文语料 → 0 报
    clean = ("An Inquiry into the Causes and Effects of the Variolae Vaccinae, "
             "a disease discovered in some of the western counties of England. ") * 40
    hard, soft = check_bytes(clean.encode(), clean, len(clean.encode()))
    if hard or soft:
        fails.append(f"正对照被误杀：干净语料却报 {hard + soft}")

    # 正对照：中文语料 → 0 报
    zh = "牛痘接种的原始记录与同时代反对者的小册子，逐页核对过页码与版次。" * 60
    hard, soft = check_bytes(zh.encode(), zh, len(zh.encode()))
    if hard or soft:
        fails.append(f"正对照被误杀：中文语料却报 {hard + soft}")

    # 边界：正文里提到「404」但不是错误页（软报也不该有硬拦）
    mention = ("The server returned 404 Not Found for three of the identifiers, "
               "which we recorded in the ledger rather than silently dropping. ") * 30
    hard, _ = check_bytes(mention.encode(), mention, len(mention.encode()))
    if not hard:
        fails.append("**已知缺口未复现**：正文谈论 404 会被误判——见文件末尾说明")

    # 软报：过短
    tiny = b"one page broadside"
    hard, soft = check_bytes(tiny, tiny.decode(), len(tiny))
    if hard or not soft:
        fails.append(f"过短应软报不应硬拦，实得 hard={hard} soft={soft}")

    # ★ 反向对照：关掉 HTML 判据，三张错误页必须**转绿**
    #   —— 证明抓住它们的确实是 HTML 判据，不是别的什么巧合。
    global HTML_HEAD, FETCH_FAIL
    sh, sf = HTML_HEAD, FETCH_FAIL
    try:
        HTML_HEAD = re.compile(rb"___IMPOSSIBLE_SENTINEL___")
        FETCH_FAIL = re.compile(r"___不可能出现___")
        still = [n for n, s in (("Error", REAL_IA_ERROR), ("404", REAL_IA_404),
                                ("500", REAL_NGINX_500))
                 if check_bytes(s.encode(), s, len(s.encode()))[0]]
    finally:
        HTML_HEAD, FETCH_FAIL = sh, sf
    if still:
        fails.append(f"反向对照失败：关掉 HTML 与取不到判据后 {still} 仍被硬拦——"
                     f"说明拦住它们的不是这两条判据")

    # ══════════════════════════════════════════════════════════════
    # ㉝ `check_file()` 本体 —— 2026-08-12 之前它一次也没被自测进入过
    # ══════════════════════════════════════════════════════════════
    #
    # 上面全部在打 `check_bytes()`（**给定字节该判什么**），那把尺子已被四条
    # 真实落盘样本钉死。而 `check_file()` 是**从磁盘到那把尺子之间的一段**：
    # 它决定读多少、怎么解码、`size` 是什么。三件事都能单独出错，而
    # `check_bytes` 那一层完全看不见。
    import tempfile as _tf
    print("\n── ㉝ check_file()（tempdir 上跑真文件）──")
    _d = pathlib.Path(_tf.mkdtemp())

    def _w(name, data):
        f = _d / name
        f.write_bytes(data if isinstance(data, bytes) else data.encode("utf-8"))
        return f

    h, s = check_file(_w("err.html.txt", REAL_IA_ERROR))
    _ok = bool(h) and "HTML" in h[0]
    print(f"  {'✓' if _ok else '✗'} ㉝a 真实落盘的 archive.org 错误页 → **硬拦**")
    fails.append("㉝a") if not _ok else None

    clean = ("Edward Jenner wrote to his friend in plain English about the "
             "inoculation of cowpox, and the results of that experiment. " * 40)
    h, s = check_file(_w("clean.txt", clean))
    _ok = not h and not s
    print(f"  {'✓' if _ok else '✗'} ㉝b 干净英文语料 → 0 硬 0 软（h={len(h)} s={len(s)}）")
    fails.append("㉝b") if not _ok else None

    h, s = check_file(_w("tiny.txt", "太短了。"))
    _ok = not h and any("过短" in x for x in s)
    print(f"  {'✓' if _ok else '✗'} ㉝c 过短 → **只软报不硬拦**（软报 {len(s)} 条）")
    fails.append("㉝c") if not _ok else None

    # ㉝d ★ 二进制／非 UTF-8：`check_file` 用 `decode("utf-8","replace")`，
    #    坏字节变成 U+FFFD——**它不在 `READABLE` 里**，所以可读占比会掉下来。
    #    这一条同时验「不许崩」与「判得出」。
    h, s = check_file(_w("bin.txt", bytes(range(0x80, 0x100)) * 40))
    _ok = any("可读字符占比" in x for x in s)
    print(f"  {'✓' if _ok else '✗'} ㉝d 非 UTF-8 字节流 → 不崩，且报「可读字符占比」低")
    fails.append("㉝d") if not _ok else None

    # ㉝e `size` 必须是**字节数**，不是解码后的字符数。
    #    一份 1200 字节的中文文件解码后只有 400 字符——按字符数判就会被
    #    「过短 <2000」误伤两次。造一份**字节数够而字符数不够**的样本钉住它。
    zh = "这是一份完整的中文语料，句子读起来很自然，标点也齐全。" * 20   # ≈1560 字节
    f = _w("zh.txt", zh)
    h, s = check_file(f)
    _ok = len(f.read_bytes()) > len(zh) and any("过短" in x and str(len(f.read_bytes())) in x
                                                for x in s)
    print(f"  {'✓' if _ok else '✗'} ㉝e `size` 是**字节数**不是字符数"
          f"（{len(zh)} 字 → {len(f.read_bytes())} 字节，报的是后者）")
    fails.append("㉝e") if not _ok else None

    # ★ 收口必须在**所有**断言之后。2026-08-12 第一版我把 ㉝ 块插在
    #   `if fails: return 1` 的**后面**——五条断言照跑照印 ✗，而**没人读它们**：
    #   四个变异体全部打出 ✗ 而 rc 仍是 0。
    #   `[[a-checker-nothing-calls-is-not-a-checker]]` 的微缩版，就在我自己手里。
    for f in fails:
        print(f"✗ {f}")
    if fails:
        print(f"负对照未通过：{len(fails)} 项")
        return 1
    print("负对照通过：**四条真实样本各自判对**"
          "（archive.org Error／404、nginx 500 三张实际落盘的错误页全部硬拦；"
          "**OCR 烂到不像话的真件未被误杀**）；英文与中文干净语料 0 报；"
          "过短只软报不硬拦；**已知缺口如实复现**（正文谈论 404 会被误判）；"
          "**关掉 HTML 与取不到判据后三张错误页全部转绿**（证明拦住它们的就是这两条）")
    return 0


def _year_self_test() -> int:
    """年份比对的负对照 + 三条反向对照。"""
    import tempfile
    print("\n══ 年份比对（v0.0.0.43）══")
    fail = 0
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)

        d1 = root / "cellularpath-1858-de-gutenberg"; d1.mkdir()
        f1 = d1 / "x.txt"
        f1.write_text("Vierte Auflage. Berlin, 1871. Verlag von August Hirschwald." * 3,
                      encoding="utf-8")
        got = bool(year_mismatch(f1))
        print(f"  {'✓ 抓到' if got else '✗ 漏掉'} 文件名 1858 而扉页 1871")
        fail += not got

        # 反向①：一致 → 不得报
        d2 = root / "oberschlesien-typhus-1848-de"; d2.mkdir()
        f2 = d2 / "x.txt"; f2.write_text("Berlin 1848. Druckerei." * 5, encoding="utf-8")
        print(f"  {'✓' if not year_mismatch(f2) else '✗'} 文件名与扉页同为 1848 → 不报")
        fail += bool(year_mismatch(f2))

        # 反向②：文件名无年份 → 不判
        d3 = root / "sectionstechnik-de"; d3.mkdir()
        f3 = d3 / "x.txt"; f3.write_text("Berlin 1877." * 5, encoding="utf-8")
        print(f"  {'✓' if not year_mismatch(f3) else '✗'} 文件名无年份 → 不判")
        fail += bool(year_mismatch(f3))

        # 反向③：扉页无年份 → 不判（否则大批期刊卷次会被误报）
        d4 = root / "archiv-bd01-1847-de"; d4.mkdir()
        f4 = d4 / "x.txt"; f4.write_text("ARCHIV fuer pathologische Anatomie." * 5,
                                         encoding="utf-8")
        print(f"  {'✓' if not year_mismatch(f4) else '✗'} 扉页无年份 → 不判"
              f"（否则 56 份期刊卷次会被误报）")
        fail += bool(year_mismatch(f4))
    print("  ✓ 年份比对负对照通过（4/4）" if not fail else f"  ✗ {fail} 项未过")
    return fail


def main() -> int:
    ap = argparse.ArgumentParser(description="语料真伪门：这是语料，还是一张取不到的错误页")
    ap.add_argument("paths", nargs="*", type=pathlib.Path,
                    help="语料文件或目录（目录则递归扫 *.txt/*.md）")
    ap.add_argument("--ledger", type=pathlib.Path,
                    help="source-ledger.jsonl —— 按 local_path 逐条核已入库的语料")
    ap.add_argument("--root", type=pathlib.Path, default=pathlib.Path("."),
                    help="配合 --ledger 使用，local_path 的基准目录")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return self_test() + _year_self_test()

    targets: list[pathlib.Path] = []
    if a.ledger:
        if not a.ledger.is_file():
            print(f"用法错误：{a.ledger} 不存在", file=sys.stderr)
            return 3
        for line in a.ledger.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            lp = rec.get("local_path")
            if lp:
                targets.append(a.root / lp)
    for p in a.paths:
        if p.is_dir():
            targets += sorted(q for q in p.rglob("*") if q.suffix in (".txt", ".md"))
        elif p.is_file():
            targets.append(p)
        else:
            print(f"用法错误：{p} 不存在", file=sys.stderr)
            return 3
    if not targets:
        print("用法错误：需要至少一个路径或 --ledger（或 --self-test）", file=sys.stderr)
        return 3

    hard_hits, soft_hits, missing = [], [], []
    year_hits = []
    for p in targets:
        if not p.is_file():
            missing.append(str(p))
            continue
        h, s = check_file(p)
        hard_hits += [(p.name, x) for x in h]
        soft_hits += [(p.name, x) for x in s]
        ym = year_mismatch(p)
        if ym:
            year_hits.append((p.name, ym))

    if a.json:
        print(json.dumps({"hard": [{"file": f, "problem": x} for f, x in hard_hits],
                          "soft": [{"file": f, "problem": x} for f, x in soft_hits],
                          "missing": missing, "scanned": len(targets)},
                         ensure_ascii=False, indent=1))
        return 1 if hard_hits else (2 if soft_hits else 0)

    print(f"扫了 {len(targets)} 份")
    if missing:
        print(f"\n✗ {len(missing)} 份**文件不存在**：")
        for m in missing[:10]:
            print(f"  - {m}")
    if hard_hits:
        print(f"\n✗ {len(hard_hits)} 份**不是语料**：\n")
        for f, x in hard_hits:
            print(f"  - {f}　{x}")
        print("\n  ↑ **它们有字节数、有校验和、能算进 primary_ratio。**"
              "\n  Jenner #104 那次，4 份错误页里最大的一份 146 KB——**比一本真小册子还大**。")
    if soft_hits:
        print(f"\n⚠ {len(soft_hits)} 份可疑（只报不拦）：\n")
        for f, x in soft_hits:
            print(f"  - {f}　{x}")
    if year_hits:
        print(f"\n⚠ {len(year_hits)} 份**文件名年份与扉页对不上**（只列不判，逐条翻扉页核）：\n")
        for f, x in year_hits[:20]:
            print(f"  - {f}　{x}")
        if len(year_hits) > 20:
            print(f"  …（另有 {len(year_hits) - 20} 份）")
        print("\n  ↑ **噪声不低**（扫本里常混入其他年份），但真错就藏在里面。"
              "\n  Virchow #109：`cellularpath-1858-de-gutenberg` 文件名写 1858、"
              "扉页写「Vierte Auflage. Berlin, 1871」，"
              "\n  照文件名写进研究笔记后，把一句 1871 年才出现的拉丁公式记到了 1858 年名下。")
    if not hard_hits and not soft_hits and not missing:
        print("✓ 每一份都是真文档（本门只判这一件事——**不判它是不是这个人的文档**）")
        return 0
    return 1 if (hard_hits or missing) else 2


if __name__ == "__main__":
    raise SystemExit(main())

# ── 已知缺口（写在这里让它可见，不假装没有）────────────────────────────
# 第 2 条按正文关键词判「取不到」，所以**一份正经讨论 HTTP 错误码的文档会被误判**。
# 负对照里有一条专门复现它。之所以不修：本门的服务对象是抓下来的历史语料，
# 那类文档在这个场景里不出现；而放宽判据会让真错误页漏网。
# **如果将来要蒸的人物写的就是网络工程，这条必须重做。**
