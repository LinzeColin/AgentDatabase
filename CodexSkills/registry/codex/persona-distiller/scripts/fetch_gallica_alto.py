#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**Gallica 的正文取得到，只是不在 `.texteBrut` 那个口子上。**

## 为什么有这件

2026-08-18 上午的记录对 Eiffel #142 的结论是「Gallica 书目命中 14 条，
**但 `.texteBrut` 取不到正文**（三种形式返回逐字节相同的 50212 B 网页外壳）⇒ 仍不解锁」。

当天晚上换一个口子实测：`RequestDigitalElement?O=<ark>&E=ALTO&Deb=<页>`
**返回真 ALTO XML**（`<alto xmlns="http://bibnum.bnf.fr/ns/alto_prod">`，含逐词 `CONTENT`）。
1907《Recherches expérimentales sur la résistance de l'air》149 页，
抽样第 25／40 页各得 388／308 词法文正文。

⇒ 原结论要收窄成：**`.texteBrut` 取不到 ≠ Gallica 取不到。**
   同族教训：[[named-the-resource-class-then-never-searched-it]]。

## ★★ 两个必须处理的坑

### ① 声明的编码是假的

ALTO 的 XML 头写 `encoding="ISO-8859-1"`，**而字节是 UTF-8**。
按声明解会得到 `RÃSISTANCE DE L'AIR`（该是 `RÉSISTANCE`）。
本件先把整份字节按 UTF-8 解一次；解不开才退回 latin-1。
**不这么做，取回来的每一个重音字母都是坏的**，而逐字引文判据会照单全收
（[[regex-must-clear-the-corpus-language]]）。

### ② 限速真实存在

连发 3 个请求即 `HTTP 429 Too Many Requests`。默认间隔 4 秒，
429 时退避 30／60／120 秒。**这不是绕限流，是按它的节奏取**：
Gallica 是免费公共数字图书馆，其 API 本就要求带 UA；
挡住裸 `curl` 的是机器人过滤器，不是权利或授权边界
（详见 `_ledgers/_403不是一种东西-Gallica那条是UA过滤-2026-08-18.md`）。

## 用法

    python3 fetch_gallica_alto.py <ark> --out <文件.txt> [--pages 1-149] [--delay 4]
    python3 fetch_gallica_alto.py --self-test

退出码：0=取全　1=有页取不到　2=自测未过　3=一页都没取到（**未取，不是「没有正文」**）
"""
from __future__ import annotations

import argparse
import re
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

UA = ("persona-distiller/1.0 (public-domain corpus retrieval; "
      "https://github.com/LinzeColin/AgentDatabase)")
FRENCH_FUNCTION_WORDS = re.compile(
    r"\b(?:qui|dans|pour|nous|cette|avec|sur|les|des|est)\b", re.IGNORECASE)


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


def fetch(url: str, timeout: int = 90) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
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
                text = page_text(fetch(url))
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
    n = fail = 0

    def note(label: str, cond: bool) -> None:
        nonlocal n, fail
        n += 1
        fail += (not cond)
        print(f"  {'✓' if cond else '✗'} {label}")

    # ① 正对照：UTF-8 字节 + 谎报 ISO-8859-1 的头 ⇒ 必须解出正确重音字母
    body = ('<?xml version="1.0" encoding="ISO-8859-1" standalone="no"?>'
            '<alto xmlns="http://bibnum.bnf.fr/ns/alto_prod"><Layout><String CONTENT="RÉSISTANCE"/>'
            '<String CONTENT="de"/><String CONTENT="l\'air"/></Layout></alto>').encode("utf-8")
    got = page_text(body)
    note(f"正对照：头谎报 ISO-8859-1 而字节是 UTF-8 ⇒ 解出 'RÉSISTANCE'（实得 {got!r}）",
         got == "RÉSISTANCE de l'air")

    # ② **反对照**：若按声明的 latin-1 解，必然得到 mojibake —— 这一档保证上面那条不是碰巧
    mojibake = body.decode("latin-1")
    note("反对照：同一批字节按声明的 latin-1 解**必然**是 mojibake（证明 ① 不是碰巧）",
         "RÃ" in mojibake and "RÉSISTANCE" not in mojibake)

    # ③ **反对照**：不是 ALTO 的东西必须返回 None，不许返回空串
    note("反对照：网页外壳（非 ALTO）⇒ None 而不是 ''（空串会被读成「这页没字」）",
         page_text(b"<html><body>Acces interdit</body></html>") is None)

    # ④ 空 ALTO（真的没字的一页）返回空串，与 ③ 区分开
    empty = ('<?xml version="1.0"?><alto xmlns="http://bibnum.bnf.fr/ns/alto_prod">'
             '<Layout/></alto>').encode("utf-8")
    note("空白页（合法 ALTO、零个 String）⇒ '' —— 与「取不到」区分得开", page_text(empty) == "")

    print(f"\n  {'✓ 自测通过' if not fail else f'✗ {fail} 项未过'}（{n - fail}/{n}）")
    return fail


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("ark", nargs="?")
    ap.add_argument("--out")
    ap.add_argument("--pages", default="1-40", help="如 1-149")
    ap.add_argument("--delay", type=float, default=4.0)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return 2 if self_test() else 0
    if not a.ark or not a.out:
        ap.error("须给 <ark> 与 --out")

    lo, _, hi = a.pages.partition("-")
    pages = range(int(lo), int(hi or lo) + 1)
    texts, ok, bad = fetch_book(a.ark, pages, a.delay)
    body = "\n".join(texts)
    hits = len(FRENCH_FUNCTION_WORDS.findall(body))
    print(f"  {a.ark}：取到 {ok} 页，取不到 {bad} 页，共 {len(body.split())} 词，法文虚词 {hits}")
    if not ok:
        print("  ✗ **一页都没取到 —— 这是「未取」，不是「没有正文」**")
        return 3
    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write(body + "\n")
    print(f"  ✓ 已写 {a.out}（{len(body.encode('utf-8'))} 字节）")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
