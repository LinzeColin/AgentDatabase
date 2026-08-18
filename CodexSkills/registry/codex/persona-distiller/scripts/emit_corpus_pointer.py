#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""语料指针清单 —— 语料移出仓之后，**仓里留下的就只有这一份**。

## 为什么有这件

2026-08-11 移交 GitHub 时量出来：本分支相对 `origin/main` 新增 **2742.6 MB**，
其中 **2711.6 MB 是语料**，产物 + 账本 + 判据 + 交接文档合起来只有 30.6 MB。
而 `origin/main` 上 8-10 新加的 pre-push 钩子上限是 **200 MB**，
它的注释里点名的就是这个分支。

决定：**语料另存，仓里只放指针。**

## ★★ 先量清楚「丢了能不能捞回来」，再决定指针要写多细

2071 行台账逐行分类（**这是实测，不是估计**）：

    ① 有 URL                    1993   73.5%
    ② 有档案条目号（可再取）        134    4.9%
    ③ 只有文字性 locator           507   18.7%
    ④ **什么坐标都没有**             79    2.9%

**① + ② = 78.4%，这是「丢了还能捞回来」的上界。**
剩下 21.6% 凭元数据取不回来——所以这份清单的职责**不只是**「怎么重抓」，
更是「**拿到别处存的那份之后，怎么证明它就是原来那份**」。

★★★ **上面这组数我先报错过一次，错法比数本身重要。**
第一版 `build()` 写的是 `glob("wip-*/workspaces/*/evidence/source-ledger.jsonl")`，
**漏了 10 份台账**（全库台账落在三种深度：5 段 27 份、6 段 6 份、2 段 4 份）。
于是我报出：

    工作区 24（真值 34）　台账 952 行（真值 2071）
    ① 有 URL 43.5%（真值 73.5%）　①+② 57.6%（真值 78.4%）
    ④ 什么坐标都没有 8.3%（真值 2.9%）

**而且这些错数我已经报给用户了**，还据此说过「1323.8 MB 的 raw/ 没有任何台账行」——
那 1323.8 MB 里绝大部分是**我自己没找到台账**，不是它们真的没登记。
★ 教训与 [[gates-cover-json-not-the-prose-users-read]] 同族：
**先猜路径形状、再去 glob，就会把「我没找到」报成「它不存在」。**
现在改用 `rglob`，不猜深度。

★ 另一处已改正的错话：我一度在给用户的选项里写「台账里有每份的 URL，需要时按台账重抓」，
当时只看了 `url` 字段（2.6%）——**而 73.5% 的链接藏在 `locator` 里**。
两次都是同一个毛病：**只看一个字段、只扫一种路径，就下全称结论。**

## 清单里放什么

每个工作区一条，逐份文件记：

- `source_id` / `local_path` / `original_name`
- `checksum`（台账里 **100% 齐**）与 `normalized_checksum`
- `bytes`（现算，不抄台账）
- `refetch`：`url` / `item` / `prose` / `none` —— 上面那四类
- 以及该行原本的 `locator`（有什么记什么，不美化）

**不写「怎么下载」**——那要 URL，而 URL 只有 43.5% 有。
**只写「怎么验」**——checksum 是齐的，验得了。

用法：

    python3 emit_corpus_pointer.py --corpora <_corpora 根> --out <清单.json>
    python3 emit_corpus_pointer.py --verify <清单.json> --corpora <_corpora 根>
    python3 emit_corpus_pointer.py --restore <工作区目录>        # 按指针取回
    python3 emit_corpus_pointer.py --self-test

退出码：0=成功　1=校验有出入／取回失败　2=自测未过　3=能取的都取到了，**但仍有取不回的**

## `--restore`：这件工具原本只会「产指针」和「验指针」，不会**用**指针

2026-08-18 实测：十一个工作区在 release 门上同时报 `research.ledger-file-missing`，
形状一模一样——语料被清掉了（本来也不进 git，`.gitignore:40 **/raw/**/*.txt`），
账本还在、产物还在、判据还在，**只有正文没了**，于是引文核查与覆盖率全在对着虚空算。
仓里当时有「检测」（`check_corpus_presence.py`）、有「产指针」（本件）、有「验指针」（本件
`--verify`），**唯独没有「照着指针取回来」那一步**——那一步一直是手工的。

★ 取回的两条 URL 来源，都是**仓里记过的事实**，不是猜出来的：
  ① `raw/_fetch-manifest.json` 的 `记录[].source_url`（当初真正用过的那条链接）
  ② 账本行里的任意 URL（`refetch_class` 已证实 73.5% 藏在 `locator` 而不是 `url`）
优先 ①——它是原次实际取用的链接；②只在 ① 没有该文件时才用。
**两条都取不到就如实记成「取不回」，不去按 identifier 拼下载路径**：
拼出来的链接下到的可能是另一个版次，而校验和会因此对不上，
届时分不清是「拼错了」还是「这份真的变了」。

★★ **校验不通过的字节一律不落盘。** 留在盘上的每一份都是校验和逐份对上的原件；
取回来对不上就删掉并计入「校验不符」——**绝不留一份「差不多的」冒充语料**
（[[name-match-is-not-content-match-in-backup]]）。
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import pathlib
import re
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

URL = re.compile(r"https?://[^\s\"')]+")
ITEM = re.compile(r"\bitem\s+[\w.\-]{6,}|\bark:/|\bdoi:|10\.\d{4,}/|hdl\.handle|\bMS\s?\d+|\bcatalog(?:ue)?\s+no")


def refetch_class(row: dict) -> str:
    """这一份**丢了能不能捞回来**。四档，按可操作性从强到弱。

    ★ 判据看的是**整行**里有没有 URL（`url` 字段只覆盖 2.6%，
      而 `locator` 里藏着 373 行的链接），不是只看 `url` 字段。
      只看一个字段会把 43.5% 报成 2.6%。
    """
    blob = json.dumps(row, ensure_ascii=False)
    loc = str(row.get("locator") or "")
    if URL.search(blob):
        return "url"
    if ITEM.search(loc):
        return "item"
    if loc.strip():
        return "prose"
    return "none"


def sha256_of(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def find_ledgers(corpora: pathlib.Path) -> list:
    """找**全部** `source-ledger.jsonl`，不猜深度。

    ★★ 2026-08-11：第一版写的是 `glob("wip-*/workspaces/*/evidence/...")`，
    **漏了 10 份台账**。实测全库台账落在三种深度上：

        相对 _corpora 的路径段数 → 份数：{5: 27, 6: 6, 2: 4}

    5 段是常规布局；**6 段是那 6 个「路径重了一层」的工作区**
    （`workspaces/<slug>/<slug>/`，HANDOFF 里专门记过）；
    2 段是直接落在 `wip-X/` 根下的。
    漏掉后果不是少几行——**1323.8 MB 的 raw/ 会被判成「台账没登记」**。
    """
    return sorted(corpora.rglob("source-ledger.jsonl"))


def build(corpora: pathlib.Path) -> dict:
    out = {"schema": "corpus-pointer/1", "workspaces": {}}
    tally = collections.Counter()
    for led in find_ledgers(corpora):
        ws_dir = led.parent.parent          # <ws>/evidence/source-ledger.jsonl → <ws>
        # ★ 键用**相对 _corpora 的路径**，不用目录名：
        #   双层嵌套的两级同名（clara-barton/clara-barton），只用名字会互相覆盖。
        ws = str(ws_dir.relative_to(corpora))
        items = []
        for line in led.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            lp = str(r.get("local_path") or "")
            f = (ws_dir / lp) if lp else None
            size = f.stat().st_size if (f and f.is_file()) else None
            cls = refetch_class(r)
            tally[cls] += 1
            items.append({
                "source_id": r.get("source_id"),
                "local_path": lp,
                "original_name": r.get("original_name"),
                "checksum": r.get("checksum"),
                "normalized_checksum": r.get("normalized_checksum"),
                "bytes": size,                       # ★ 现算，不抄台账
                "present": bool(size is not None),
                "split": r.get("split"),
                "tier": r.get("tier"),
                "refetch": cls,
                "locator": r.get("locator"),
            })
        out["workspaces"][ws] = {
            "ledger_rows": len(items),
            "present": sum(1 for i in items if i["present"]),
            "bytes_present": sum(i["bytes"] or 0 for i in items),
            "items": items,
        }
    out["tally_refetch"] = dict(tally)
    out["totals"] = {
        "workspaces": len(out["workspaces"]),
        "rows": sum(w["ledger_rows"] for w in out["workspaces"].values()),
        "present": sum(w["present"] for w in out["workspaces"].values()),
        "bytes_present": sum(w["bytes_present"] for w in out["workspaces"].values()),
    }
    return out


def verify(manifest: dict, corpora: pathlib.Path) -> int:
    """拿清单去核一棵语料树。**只报事实，不修任何东西。**"""
    miss = bad = ok = noc = 0
    problems = []
    for ws, w in manifest["workspaces"].items():
        base = corpora / ws           # ★ ws 现在就是相对 _corpora 的路径，不必再 glob
        if not base.is_dir():
            base = None
        if base is None:
            miss += w["ledger_rows"]
            problems.append((ws, "整个工作区不在", ""))
            continue
        for it in w["items"]:
            p = base / (it["local_path"] or "")
            if not it["local_path"] or not p.is_file():
                miss += 1
                problems.append((ws, "文件不在", it["local_path"] or "(无 local_path)"))
                continue
            want = it.get("checksum")
            if not want:
                noc += 1
                continue
            got = sha256_of(p)
            if got == want:
                ok += 1
            else:
                bad += 1
                problems.append((ws, "校验和对不上", f"{it['local_path']} 期望 {want[:12]} 实得 {got[:12]}"))
    print(f"核过 {ok + bad + miss + noc} 份：**校验通过 {ok}**，"
          f"校验和对不上 {bad}，文件不在 {miss}，台账无校验和 {noc}")
    for ws, kind, det in problems[:25]:
        print(f"  ⚠ {ws}　{kind}　{det}")
    if len(problems) > 25:
        print(f"  …另有 {len(problems) - 25} 条")
    if bad or miss:
        print("\n  ✗ **这棵语料树与清单不一致**——别拿它当原件用")
        return 1
    if not ok:
        print("\n  ⚠ **一份都没校验成功——本次未检查（不是通过）**")
        return 1
    print("\n  ✓ 清单里的每一份都在，且校验和逐份对上")
    return 0



def _urls_for(ws_dir: pathlib.Path, row: dict, fname: str) -> list:
    """这一份能从哪些**记录过的**链接取回。顺序即优先级，不含任何拼出来的链接。"""
    urls = []
    man = ws_dir / "raw" / "_fetch-manifest.json"
    if man.is_file():
        try:
            recs = json.loads(man.read_text(encoding="utf-8")).get("记录") or []
        except (ValueError, OSError):
            recs = []
        for r in recs:
            if str(r.get("file") or "") == fname and r.get("source_url"):
                urls.append(str(r["source_url"]))
    m = URL.search(json.dumps(row, ensure_ascii=False))
    if m and m.group(0) not in urls:
        urls.append(m.group(0))
    return urls


def restore(ws_dir: pathlib.Path, *, timeout: int = 180) -> int:
    """照账本把语料取回来，逐份核校验和。**核不过不落盘。**"""
    import urllib.request

    led = ws_dir / "evidence" / "source-ledger.jsonl"
    if not led.is_file():
        print(f"  ✗ 没有账本：{led} —— **本次未取回（不是没东西可取）**")
        return 1

    tally = collections.Counter()
    problems = []
    for line in led.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        lp = str(row.get("local_path") or "")
        want = str(row.get("checksum") or "")
        if not lp:
            tally["台账无 local_path"] += 1
            continue
        dst = ws_dir / lp
        if dst.is_file() and want and sha256_of(dst) == want:
            tally["已在"] += 1
            continue
        if not want:
            tally["台账无校验和·不取"] += 1
            problems.append((lp, "台账没有校验和，取回来也证不了是原件"))
            continue
        urls = _urls_for(ws_dir, row, pathlib.PurePosixPath(lp).name)
        if not urls:
            tally["取不回·无记录链接"] += 1
            continue
        got_ok = False
        last = ""
        for u in urls:
            try:
                req = urllib.request.Request(u, headers={"User-Agent": "persona-distiller/restore"})
                with urllib.request.urlopen(req, timeout=timeout) as f:
                    data = f.read()
            except Exception as e:                      # noqa: BLE001 —— 什么错都要记下来继续下一条
                last = f"{type(e).__name__}: {e}"[:80]
                continue
            if hashlib.sha256(data).hexdigest() == want:
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_bytes(data)                   # ★ 只有校验通过才落盘
                got_ok = True
                break
            last = f"校验和对不上（{len(data)} B）"
        if got_ok:
            tally["取回并校验通过"] += 1
        else:
            tally["取回失败"] += 1
            problems.append((lp, last or "所有记录链接都取不到"))

    total = sum(tally.values())
    print(f"  {ws_dir.name} —— 账本 {total} 行：" +
          "　".join(f"{k} {v}" for k, v in sorted(tally.items())))
    for lp, why in problems[:15]:
        print(f"   ✗ {lp[:52]:<52} {why}")
    if len(problems) > 15:
        print(f"   …另有 {len(problems) - 15} 条")

    if tally["取回失败"] or tally["台账无校验和·不取"]:
        return 1
    if tally["取不回·无记录链接"] or tally["台账无 local_path"]:
        print(f"  ⚠ **仍有 {tally['取不回·无记录链接'] + tally['台账无 local_path']} 份取不回**"
              f"——这不是「都齐了」，是射程到头了")
        return 3
    return 0



GALLICA_UA = ("persona-distiller/1.0 (public-domain corpus retrieval; "
               "https://github.com/LinzeColin/AgentDatabase)")

def decode_alto(raw: bytes) -> str:
    """★ 头里写 ISO-8859-1，字节却是 UTF-8 —— 先按 UTF-8 解，解不开才退 latin-1。"""
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("latin-1")

def page_text(raw: bytes) -> str | None:
    """从一页 ALTO 里抽正文；不是 ALTO 就返回 None（**不返回空串** —— 空串会被读成「这页没字」）。"""
    text = decode_alto(raw)
    # 去掉 XML 声明里的假编码，否则 ElementTree 会拿它再解一次
    text = re.sub(r'^<\?xml[^>]*\?>', '<?xml version="1.0"?>', text, count=1)
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return None
    # ★ 光「解得开」不够：`<html>…</html>` 也是合法 XML，抽不出 String 就会返回 ''，
    #   于是「这不是 ALTO」被读成「这页没字」。**根标签必须是 alto。**
    #   （这一条是本件自测的反对照当场逼出来的，不是想出来的。）
    if not root.tag.endswith("alto"):
        return None
    words = [el.get("CONTENT", "") for el in root.iter() if el.tag.endswith("String")]
    return " ".join(w for w in words if w)

def _http_get(url: str, timeout: int = 90) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": GALLICA_UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()

def fetch_book(ark: str, pages: range, delay: float = 4.0,
               log=print) -> tuple[list[str], int, int]:
    """按页取回。429 时退避 30／60／120 秒；仍失败就记这一页取不到，继续下一页。"""
    out: list[str] = []
    ok = bad = 0
    for page in pages:
        url = f"https://gallica.bnf.fr/RequestDigitalElement?O={ark}&E=ALTO&Deb={page}"
        text = None
        for attempt, backoff in enumerate((0, 30, 60, 120)):
            if backoff:
                time.sleep(backoff)
            try:
                text = page_text(_http_get(url))
                break
            except urllib.error.HTTPError as exc:
                if exc.code != 429 or attempt == 3:
                    log(f"   第 {page} 页 ✗ HTTP {exc.code}")
                    break
            except Exception as exc:                      # noqa: BLE001
                log(f"   第 {page} 页 ✗ {type(exc).__name__}")
                break
        if text is None:
            bad += 1
        else:
            ok += 1
            out.append(text)
        time.sleep(delay)
    return out, ok, bad

def self_test() -> int:
    n = [0]
    fail = 0

    def note(label, ok):
        n[0] += 1
        print(f"  {'✓' if ok else '✗'} {label}")

    print("══ 负对照 ══")
    # ① 四档分类：URL 藏在 locator 里也要认出来（只看 url 字段会把 43.5% 报成 2.6%）
    ok1 = refetch_class({"locator": "见 https://archive.org/details/foo"}) == "url"
    note("`locator` 里的链接算「有 URL」（不是只看 `url` 字段）", ok1)
    fail += not ok1

    ok1b = refetch_class({"url": "https://x/y"}) == "url"
    note("`url` 字段照样算", ok1b)
    fail += not ok1b

    ok2 = refetch_class({"locator": "item transactions-american-institute_1907_26, file p12"}) == "item"
    note("档案条目号算「可再取」", ok2)
    fail += not ok2

    ok3 = refetch_class({"locator": "第 12 卷第 3 章，题名页"}) == "prose"
    note("只有文字性 locator → prose", ok3)
    fail += not ok3

    # ★ **反对照**：什么都没有必须落到 none，不许被前三档顺手接走。
    ok4 = refetch_class({"locator": "", "source_id": "src-1"}) == "none"
    note("**反对照**：坐标为空 → none（不许静默升档）", ok4)
    fail += not ok4

    ok4b = refetch_class({"locator": None}) == "none"
    note("**反对照**：locator 是 null 也算 none", ok4b)
    fail += not ok4b

    # ② 校验：真改坏一个字节，必须报出来
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        ws = root / "wip-t-1" / "workspaces" / "tester"
        (ws / "raw" / "src-a").mkdir(parents=True)
        f = ws / "raw" / "src-a" / "x.txt"
        f.write_text("hello corpus", encoding="utf-8")
        (ws / "evidence").mkdir()
        row = {"source_id": "src-a", "local_path": "raw/src-a/x.txt",
               "original_name": "x.txt", "checksum": sha256_of(f),
               "locator": "https://example.org/x"}
        (ws / "evidence" / "source-ledger.jsonl").write_text(
            json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8")

        m = build(root)
        ok5 = m["totals"]["rows"] == 1 and m["totals"]["present"] == 1
        note("build 扫到 1 份且标为存在", ok5)
        fail += not ok5

        ok5b = verify(m, root) == 0
        note("**反对照**：没动过的树 → 校验通过（不是凡树皆红）", ok5b)
        fail += not ok5b

        f.write_text("hello corpuz", encoding="utf-8")     # 改一个字节
        ok6 = verify(m, root) == 1
        note("改一个字节 → 校验报错（退出 1）", ok6)
        fail += not ok6

        f.unlink()
        ok7 = verify(m, root) == 1
        note("文件删掉 → 报「文件不在」（退出 1）", ok7)
        fail += not ok7


    print("══ --restore 三档对照（走真取回路径，用 file:// 不出网）══")
    import tempfile

    def _mkws(root, body, ledger_checksum, with_url):
        src = root / "origin.txt"
        src.write_bytes(body)
        ws = root / "ws"
        (ws / "evidence").mkdir(parents=True)
        (ws / "raw").mkdir(parents=True)
        (ws / "evidence" / "source-ledger.jsonl").write_text(json.dumps(
            {"source_id": "src-x", "local_path": "raw/a.txt", "checksum": ledger_checksum},
            ensure_ascii=False) + "\n", encoding="utf-8")
        if with_url:
            (ws / "raw" / "_fetch-manifest.json").write_text(json.dumps(
                {"记录": [{"file": "a.txt", "source_url": src.as_uri(), "sha256": ledger_checksum}]},
                ensure_ascii=False), encoding="utf-8")
        return ws

    body = b"hello corpus, this is the one true original\n"
    good = hashlib.sha256(body).hexdigest()

    with tempfile.TemporaryDirectory() as td:
        ws = _mkws(pathlib.Path(td), body, good, True)
        rc = restore(ws)
        got = ws / "raw" / "a.txt"
        okA = rc == 0 and got.is_file() and got.read_bytes() == body
        note("正对照：校验和对上 ⇒ rc=0 且落盘字节与原件相同", okA)
        fail += not okA

    with tempfile.TemporaryDirectory() as td:
        ws = _mkws(pathlib.Path(td), body, "0" * 64, True)
        rc = restore(ws)
        okB = rc == 1 and not (ws / "raw" / "a.txt").exists()
        note("**反对照**：校验和对不上 ⇒ rc=1 且没有落盘（「下到什么存什么」的退化实现在此必红）", okB)
        fail += not okB

    with tempfile.TemporaryDirectory() as td:
        ws = _mkws(pathlib.Path(td), body, good, False)
        rc = restore(ws)
        okC = rc == 3 and not (ws / "raw" / "a.txt").exists()
        note("射程档：无记录链接 ⇒ rc=3（**「取不回」不许混成「都齐了」**）", okC)
        fail += not okC

    with tempfile.TemporaryDirectory() as td:
        ws = _mkws(pathlib.Path(td), body, good, False)
        (ws / "raw" / "_fetch-manifest.json").write_text(json.dumps(
            {"记录": [{"file": "a.txt", "identifier": "someIAitem", "sha256": good}]},
            ensure_ascii=False), encoding="utf-8")
        okD = restore(ws) == 3
        note("只有 identifier 没有链接 ⇒ 仍是「取不回」，**不去拼下载路径**", okD)
        fail += not okD


    print("══ 入口对照（**自测直接调函数会绕开 argparse**）══")
    with tempfile.TemporaryDirectory() as td:
        ws = _mkws(pathlib.Path(td), body, good, True)
        import contextlib, io
        buf = io.StringIO()
        argv_bak = sys.argv[:]
        sys.argv = ["emit_corpus_pointer.py", "--restore", str(ws)]
        try:
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                rc_main = main()
        except SystemExit as e:               # argparse 认不出旗标就在这里退出
            rc_main = f"argparse 拒收：{e}"
        finally:
            sys.argv = argv_bak
        okE = rc_main == 0 and (ws / "raw" / "a.txt").is_file()
        note(f"`--restore` 从 **main() 入口**走得通（实得 {rc_main!r}）", okE)
        fail += not okE


    print("══ Gallica ALTO 通道（.texteBrut 取不到时用它）══")
    body = ('<?xml version="1.0" encoding="ISO-8859-1" standalone="no"?>'
            '<alto xmlns="http://bibnum.bnf.fr/ns/alto_prod"><Layout>'
            '<String CONTENT="RÉSISTANCE"/><String CONTENT="de"/><String CONTENT="l\'air"/>'
            '</Layout></alto>').encode("utf-8")
    got = page_text(body)
    okG1 = got == "RÉSISTANCE de l'air"
    note(f"正对照：头谎报 ISO-8859-1 而字节是 UTF-8 ⇒ 解出 'RÉSISTANCE'（实得 {got!r}）", okG1)
    fail += not okG1

    moji = body.decode("latin-1")
    okG2 = "RÃ" in moji and "RÉSISTANCE" not in moji
    note("**反对照**：同一批字节按声明的 latin-1 解**必然**是 mojibake（证明上一条不是碰巧）", okG2)
    fail += not okG2

    # ★★ 这一档第一次是红的：`<html>…</html>` 也是合法 XML，ET 解得开、抽出 0 个 String
    #    ⇒ 返回 ''，于是「这不是 ALTO」被读成「这页没字」。加根标签断言才绿。
    okG3 = page_text(b"<html><body>Acces interdit</body></html>") is None
    note("**反对照**：网页外壳（合法 XML 但不是 ALTO）⇒ None 而不是 ''", okG3)
    fail += not okG3

    empty = ('<?xml version="1.0"?><alto xmlns="http://bibnum.bnf.fr/ns/alto_prod">'
             '<Layout/></alto>').encode("utf-8")
    okG4 = page_text(empty) == ""
    note("空白页（合法 ALTO、零个 String）⇒ '' —— 与「取不到」区分得开", okG4)
    fail += not okG4

    print(f"\n  ✓ 自测通过（{n[0]}/{n[0]}）" if not fail
          else f"\n  ✗ {fail}/{n[0]} 项未过——本件的输出不作数")
    return fail


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpora", type=pathlib.Path, help="_corpora 根目录")
    ap.add_argument("--out", type=pathlib.Path, help="清单落盘路径")
    ap.add_argument("--verify", type=pathlib.Path, help="拿这份清单去核 --corpora 那棵树")
    ap.add_argument("--gallica-alto", metavar="ARK",
                    help="从 Gallica 按 ALTO 逐页取一部书（.texteBrut 取不到时用这条）")
    ap.add_argument("--pages", default="1-40", help="配合 --gallica-alto，如 1-149")
    ap.add_argument("--out-text", type=pathlib.Path, help="--gallica-alto 的落盘路径")
    ap.add_argument("--delay", type=float, default=4.0, help="每页间隔秒数（Gallica 连发 3 个即 429）")
    ap.add_argument("--restore", type=pathlib.Path,
                    help="按账本+仓里记过的链接把语料取回该工作区（核不过不落盘）")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return 2 if self_test() else 0
    if a.gallica_alto:
        if not a.out_text:
            ap.error("--gallica-alto 须配 --out-text")
        lo, _, hi = a.pages.partition("-")
        texts, ok, bad = fetch_book(a.gallica_alto, range(int(lo), int(hi or lo) + 1), a.delay)
        body = "\n".join(texts)
        print(f"  {a.gallica_alto}：取到 {ok} 页，取不到 {bad} 页，共 {len(body.split())} 词")
        if not ok:
            print("  ✗ **一页都没取到 —— 这是「未取」，不是「没有正文」**")
            return 3
        a.out_text.write_text(body + "\n", encoding="utf-8")
        print(f"  ✓ 已写 {a.out_text}（{len(body.encode('utf-8'))} 字节）")
        return 1 if bad else 0
    if a.restore:
        return restore(a.restore)
    if not a.corpora:
        ap.error("须给 --corpora")

    if a.verify:
        return verify(json.loads(a.verify.read_text(encoding="utf-8")), a.corpora)

    m = build(a.corpora)
    t = m["totals"]
    print(f"工作区 {t['workspaces']} 个，台账 {t['rows']} 行，"
          f"文件在位 {t['present']} 份，合计 {t['bytes_present'] / 1048576:.1f} MB")
    tal = m["tally_refetch"]
    tot = sum(tal.values()) or 1
    print("「丢了能不能捞回来」：")
    for k, label in (("url", "① 有 URL"), ("item", "② 有档案条目号"),
                     ("prose", "③ 只有文字性 locator"), ("none", "④ **什么坐标都没有**")):
        v = tal.get(k, 0)
        print(f"   {label:<24} {v:4d}  {100 * v / tot:5.1f}%")
    up = (tal.get("url", 0) + tal.get("item", 0)) / tot
    print(f"   ★ ①+② = {100 * up:.1f}% —— **这是能捞回来的上界，不是保证**")
    if a.out:
        a.out.write_text(json.dumps(m, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"  ✓ 已写 {a.out}（{a.out.stat().st_size / 1048576:.1f} MB）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
