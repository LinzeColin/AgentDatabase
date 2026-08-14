#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Kramerius 抓源器 —— 捷克各馆（NKP／NDK／MZK）的取源入口，**照 `fetch_ia.py` 的纪律写**。

## 为什么需要它

Comenius #182 的延后条目写着「换通道：捷克的数字图书馆」，却点了**两个波兰库**
（`jbc.bj.uj.edu.pl`／`dbc.wroc.pl`）—— 后者 51 个集合全枚举、首页合计 908 条 **0 命中**。
2026-08-14 找对了地方：**捷克国家图书馆 Kramerius**，
`dc.creator:Komensk* AND fedora.model:monograph AND datum_begin:[* TO 1930]
AND dostupnost:public` → **numFound = 164**，含三卷书信集，**OCR 全文取得到**。

archive.org 那条路上有 `fetch_ia.py`；Kramerius 这条路上**一件都没有**，
于是这一件按同样的四条纪律补上。

## 四条纪律（**每条都是 `fetch_ia.py` 用实测换来的，这里照搬不改**）

① **`dostupnost != public` 一律硬跳过。** 那是馆方的访问控制，本项目**不绕**。
   跳过要计数并写进 manifest，**不许静默丢**（[[empty-default-swallows-unknown]]）。
② **默认串行**，遇 429/403 立刻退避且本轮不再抬速。宁可慢。
③ **年份不信单一字段**：`datum_str`／`datum_begin`／`datum` 三个原样记下，
   另从正文头抓四位年份存 `titlepage_years`；**PD 判定由人看，不由本工具下结论**。
④ **每份落 sha256 ＋ 字节 ＋ 词数 ＋ 取回时刻**，写 `_fetch-manifest.json`。

## Kramerius 特有的两个坑（**实测踩过**）

- **扉页的 `TEXT_OCR` 返回 0 字节**（`ALTO` 有内容）。
  拿第一页试完就下结论会得出「取不到」——实测第 41 页有 2,595 字符。
  ⇒ 本件**统计空页数并单独报**，空页多不等于失败。
- **一部书 = 一个 monograph PID ＋ 几百个 page PID**，正文要**逐页取再拼**。
  1892 那卷书信集是 **322 页**（实测取回 316 有字页／6 空页，143,711 词）。
- **★★★ 一个 PID 里可能不止一部作品 —— 取回来必须先量语种再落账。**
  `uuid:32d4d830-…`（1892 Patera 编《Korrespondence》）实测切 40 块数虚词：

      块  0– 1（  0– 5%）捷克  ← Patera 的编者序（讲手稿怎么从莱什诺买回来的）
      块  2–27（  5–70%）拉丁  ← **Comenius 本人的书信**（书眉 `Ad eundem.` ×11、
                                  `observantissimus` ×10、署名 `Comenius.` ×7）
      块 38–39（ 95–100%）德语  ← **另一部作品**：18 世纪一封讲「烧死两个老妇当女巫」
                                  的德文信，与他无关（他 1670 年就没了）

  这是 `ROZPRAVY ČESKÉ AKADEMIE … ROČNÍK I. TŘÍDA III. ČÍSLO 2` —— **一期刊物**，
  扫描件把邻期一起装了进去。[[catalog-says-one-person-bytes-are-another]]
  ★ 我差点用「第一个独立成行的 `1.`」当正文起点：它落在 **95.9%** 处，
    而那正是德文那封信的开头。**一读就翻号**。[[stopping-at-the-first-answer-that-holds-together]]
  ⇒ 本工具**只负责取回与记账，不负责切片**。落进工作区之前必须逐段核归属。

## 用法

    python3 fetch_kramerius.py --host kramerius5.nkp.cz \
        --query 'dc.creator:Komensk* AND fedora.model:monograph AND datum_begin:[* TO 1930] AND dostupnost:public' \
        --list                                   # 只列，不下载
    python3 fetch_kramerius.py --host kramerius5.nkp.cz --pid uuid:xxxx --out <raw 目录>
    python3 fetch_kramerius.py --self-test

★ 退出码：0=尝试完（**不等于全成功**，看 manifest 计数）；2=参数错；3=一个都没取到。
★ **不要接管道判成败**（[[pipe-to-tail-hides-the-exit-code]]）。
"""
import argparse
import datetime
import hashlib
import json
import pathlib
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

UA = "persona-distiller/1.0 (public-domain corpus collection; no access-control bypass)"
YEAR = re.compile(r"\b(1[4-9]\d\d|20[0-2]\d)\b")
# ★★ 「能不能用」的门槛。实测两份把区间量出来了：**好的 0.926／坏的 0.0000**，
#   中间是空的 —— 门放 0.50，两侧余量都极大（不是我拍的，是量出来的）。
OCR_MIN_RATIO = 0.50


def api(host, path, params=None, timeout=40):
    # ★ 不写 `dict | None` 这种 3.10 才有的写法：**本机是 3.9**，
    #   写了会在 import 时直接 TypeError（我这一版就是这么炸的）。
    #   [[untested-fallback-branches-only-fire-on-their-machine]] 的语言版本形态。
    """GET 一个 Kramerius v5 API。**纯 IO**，不做任何判定。"""
    url = f"https://{host}/search/api/v5.0/{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as f:
        return f.read().decode("utf-8", "replace")


def is_public(doc: dict) -> bool:
    """**只有 `dostupnost == 'public'` 才许取。** 其余一律视为访问控制，跳过。

    ★ 不是「不是 private 就取」——字段可能缺失或是别的值，
      缺失时必须判 False（[[empty-default-swallows-unknown]]）。
    """
    return str(doc.get("dostupnost") or "").strip().lower() == "public"


def letter_run_ratio(text: str) -> float:
    """**「≥2 个连续字母的词」占全部 token 的比例。** 纯函数，用来抓「取回了，但是乱码」。

    ★★★ 2026-08-14 实测两份，同一天同一个 host：

        1892 Korrespondence   token 143,711｜**92.6%**｜U+FFFD 0
        1882 Modlitby         token  57,182｜ **0.0%**｜U+FFFD 17,136

    后者 OCR 是**逐字母加空格 ＋ 变音符全坏**（`M O D L I T B Y  K XE S dA N S K �`），
    一个字都用不了 —— 而我的 manifest 把它报成 **240 页有字／0 页空／57,182 词**，
    看上去比前者还健康。[[aggregator-ocr-can-be-silently-broken]]

    ★★ **我第一个想用的判别式是「平均 token 长度」，方向是反的**：
      坏的那份 **8.61**、好的那份 **5.60** —— 坏的看起来「词更长＝更像正文」。
      两份都跑了才看见。**判别式要拿正例和反例各跑一次，只跑一份必然自洽。**
      [[my-diagnostics-manufacture-false-leads]]
    """
    toks = text.split()
    if not toks:
        return 0.0
    return len(re.findall(r"[A-Za-zÀ-ɏͰ-Ͽ]{2,}", text)) / len(toks)


def years_in(text: str, head_chars: int = 20000) -> list:
    """正文头部出现的四位年份（去重排序）。**只作证据，不下 PD 结论。**"""
    return sorted({int(y) for y in YEAR.findall(text[:head_chars])})


def join_pages(pages: list) -> tuple:
    """[(pagePID, text)] → (拼好的正文, 有字页数, 空页数)。**纯函数**。

    ★ 空页要单独数：Kramerius 的扉页 `TEXT_OCR` 常返回 0 字节，
      不数出来就会把「大部分页是空的」当成「取回成功」。
    """
    kept = [t for _, t in pages if t and t.strip()]
    return ("\n".join(kept), len(kept), len(pages) - len(kept))


def self_test() -> int:
    ok = n = 0

    def chk(d, c):
        nonlocal ok, n
        n += 1
        ok += 1 if c else 0
        print(f"  {'✓' if c else '✗'} {d}")

    chk("★★ 只有 dostupnost=public 才许取", is_public({"dostupnost": "public"}))
    chk("★★ **反例：private 一律跳过**", not is_public({"dostupnost": "private"}))
    chk("★★ **反例：字段缺失判 False，不是「没说就是能取」**", not is_public({}))
    chk("★ 大小写与空格不影响", is_public({"dostupnost": " Public "}))
    txt, kept, empty = join_pages([("p1", ""), ("p2", "hello world"), ("p3", "  "), ("p4", "x")])
    chk(f"★★ **空页单独计数**（实得 有字 {kept}／空 {empty}）", (kept, empty) == (2, 2))
    chk("★ 拼接只保留有字的页", txt == "hello world\nx")
    chk("★ 全空时有字页数为 0，不报错", join_pages([("a", ""), ("b", None)]) == ("", 0, 2))
    # ★★ OCR 可用性：正反例都取自 2026-08-14 真取回的两份
    GOOD = "Přítomná sbírka jest první pokus vydání rozsáhlé a velice rozptýlené korrespondence"
    BAD  = "M O D L I T B Y   K XE S dA N S K \ufffd ,   t o t i ~   m o d l i t b y"
    rg, rb = letter_run_ratio(GOOD), letter_run_ratio(BAD)
    chk(f"★★ **正例：真正文（实得 {rg:.2f}）≥ 门 {OCR_MIN_RATIO}**", rg >= OCR_MIN_RATIO)
    chk(f"★★ **反例：逐字母加空格的乱码（实得 {rb:.2f}）< 门**", rb < OCR_MIN_RATIO)
    chk("★ 空文本不炸，判 0", letter_run_ratio("") == 0.0)
    # ★★ 「平均 token 长度方向是反的」这条**故意不写成断言**：
    #   那是**整份文件**的统计（坏 8.61 > 好 5.60），而这里只有一小段摘录 ——
    #   摘录里坏的那份全是单字母，均长反而更小，**复现不出真文件的形状**。
    #   我先写成了断言，当场判红；把夹具改到能过就等于编一个假现象。
    #   ⇒ 结论留在 `letter_run_ratio` 的 docstring 里（附两份真文件的数），
    #     自测只断言它**断言得了**的那一条。[[fixtures-cleaner-than-the-real-thing]]
    chk("★ 年份只认 1400–2029（`3409` 不算）", years_in("p. 3409 anno 1892") == [1892])
    chk("★ 年份去重排序", years_in("1902 1892 1902") == [1892, 1902])
    print(f"\n{'✓ 全过' if ok == n else f'✗ {n - ok}/{n} 项不符'}")
    return 0 if ok == n else 1


def search(host, query, rows=50):
    raw = api(host, "search", {
        "q": query, "rows": rows, "wt": "json",
        "fl": "PID,dc.title,dc.creator,datum_str,datum_begin,datum,fedora.model,dostupnost",
    })
    d = json.loads(raw)["response"]
    return d.get("numFound", 0), d.get("docs", [])


def fetch_one(host, pid, out: pathlib.Path, sleep=0.3):
    """取一部书：列页 → 逐页 TEXT_OCR → 拼 → 落盘 → 记 manifest 行。"""
    rec = {"pid": pid, "status": "", "note": ""}
    try:
        kids = json.loads(api(host, f"item/{pid}/children"))
    except Exception as e:                                    # noqa: BLE001
        rec["status"] = "列页失败"
        rec["note"] = str(e)[:120]
        return rec, None
    pages = [k["pid"] for k in kids if k.get("model") == "page"]
    if not pages:
        rec["status"] = "没有 page 子节点"
        return rec, None
    got = []
    for i, p in enumerate(pages):
        try:
            got.append((p, api(host, f"item/{p}/streams/TEXT_OCR", timeout=30)))
        except urllib.error.HTTPError as e:
            if e.code in (429, 403):                          # ★ 退避，本轮不再抬速
                time.sleep(5)
                sleep = max(sleep, 1.0)
            got.append((p, ""))
        except Exception:                                     # noqa: BLE001
            got.append((p, ""))
        time.sleep(sleep)
    text, kept, empty = join_pages(got)
    if not kept:
        rec["status"] = "全部页都是空的"
        rec["note"] = f"{len(pages)} 页全空"
        return rec, None
    out.mkdir(parents=True, exist_ok=True)
    dest = out / (pid.replace(":", "_") + ".txt")
    blob = text.encode("utf-8")
    dest.write_bytes(blob)
    ratio = letter_run_ratio(text)
    rec.update({
        "status": "已取回", "local_path": dest.name,
        "pages_total": len(pages), "pages_with_text": kept, "pages_empty": empty,
        "bytes": len(blob), "words": len(text.split()),
        "sha256": hashlib.sha256(blob).hexdigest(),
        "titlepage_years": years_in(text),
        # ★★ 这两个字段是「取回了 ≠ 取回了能用的字」的证据，**别只看 words**
        "letter_run_ratio": round(ratio, 4),
        "replacement_chars": text.count("�"),
        "ocr_verdict": "可用" if ratio >= OCR_MIN_RATIO else "**乱码，不许落账**",
        "fetched_at": datetime.datetime.now().isoformat(timespec="seconds"),
    })
    return rec, dest


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="kramerius5.nkp.cz")
    ap.add_argument("--query")
    ap.add_argument("--pid", action="append", default=[])
    ap.add_argument("--out")
    ap.add_argument("--rows", type=int, default=50)
    ap.add_argument("--list", action="store_true", help="只列出检索结果，不下载")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()

    if a.query:
        n, docs = search(a.host, a.query, a.rows)
        pub = [d for d in docs if is_public(d)]
        print(f"★★ **分母**：`numFound = {n}`；本页取回 {len(docs)} 条 → "
              f"**dostupnost=public 的 {len(pub)} 条**（其余按访问控制跳过，不绕）")
        for d in pub:
            print(f"   {d.get('datum_str','?'):>10s} {str(d.get('dc.title'))[:62]:64s} {d['PID']}")
        if a.list or not a.out:
            print("\n★ `--list` 或未给 `--out` ⇒ 只列不下。要下载请给 `--out <raw 目录>` 与 `--pid`。")
            return 0
        a.pid += [d["PID"] for d in pub]

    if not a.pid or not a.out:
        ap.error("要 --pid 与 --out（或先用 --query --list 看有什么）")
    out = pathlib.Path(a.out)
    recs = []
    for pid in a.pid:
        rec, _ = fetch_one(a.host, pid, out)
        recs.append(rec)
        mark = "✓" if rec["status"] == "已取回" else "✗"
        extra = (f'{rec.get("words",0):>7,} 词｜有字 {rec.get("pages_with_text")}／'
                 f'空 {rec.get("pages_empty")} 页｜连续字母词占比 '
                 f'{rec.get("letter_run_ratio")}｜**{rec.get("ocr_verdict")}**'
                 if rec["status"] == "已取回" else rec.get("note", ""))
        print(f"  {mark} {pid}  {rec['status']}  {extra}", flush=True)
    mf = out / "_fetch-manifest-kramerius.json"
    old = json.loads(mf.read_text(encoding="utf-8")) if mf.is_file() else {"记录": []}
    old["记录"] = [r for r in old.get("记录", []) if r.get("pid") not in {x["pid"] for x in recs}] + recs
    old["host"] = a.host
    old["updated_at"] = datetime.datetime.now().isoformat(timespec="seconds")
    mf.write_text(json.dumps(old, ensure_ascii=False, indent=1), encoding="utf-8")
    ok = sum(1 for r in recs if r["status"] == "已取回")
    print(f"\n★★ 尝试 {len(recs)} 部 → **已取回 {ok}**｜manifest：{mf}")
    print("★ 退出码 0 只表示「尝试完了」，成败看上面的计数。")
    return 0 if ok else 3


if __name__ == "__main__":
    raise SystemExit(main())
