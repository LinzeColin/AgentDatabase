#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 CONTACT 季刊 PDF 里切出**他署名的那一篇**。

CONTACT 是他基金会的刊物，每期 16 页、十来位作者。整期灌库会把他的
约 5000 字埋在别人的六万字里；所以必须切片。但切片本身是个陷阱——

## 上一版（`ms_contact.py`）切错在哪

```python
BY_HIM = re.compile(r'(?:by|—|-)\s*MICHAEL\s+H?\.?\s*STEINHARDT\b', re.I)
```

1. **`—` / `-` 两个候选会命中别人文章里的拉引归属**（「— Michael Steinhardt」）。
   从那里往前切 12000 字，切出来的是别人的整篇文章。
2. **停止判据只认「行尾 by 某某」**，而 CONTACT 的作者标识是文末**身份行**
   （`Adam Bronfman is Managing Director of The Samuel Bronfman Foundation`），
   于是一路吞过去。实测四份切片里，三份末尾署着 Lynn Schusterman /
   Adam Bronfman / Simon Greer，另一份是 HUC-JIR 的人。
3. **切片从 `m.end()` 开始，署名本身被扔掉**——落盘文件里查不到任何归属证据，
   而文件名是 `ms_*`、灌库时挂 `--author "Michael Steinhardt"`。
   两步就把别人的文章洗成他的话。其中一句「我小时候父亲教我的第一课是：
   慈善是我们付给这世界的房租」会被写成他与其父 Sol 的家世——
   那是 Lynn Schusterman 的父亲。

## 这一版的三条改法

- 起点**只认真署名**：`by MICHAEL H. STEINHARDT`，不认破折号拉引。
- 终点认**身份行**（`<某人> is Chair/President/Director/Rabbi…`），
  这才是刊物型 PDF 的作者标识形态。
- **署名留在正文里**——证据必须随文件落盘，好让 `check_authorship.py` 复核。

落盘后仍要过 `check_authorship.py`；这个脚本只负责切，不负责判。
"""
import json
import os
import re
import socket
import ssl
import sys
import time
import urllib.request

socket.setdefaulttimeout(60)
WORK = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(WORK, "contact_out")
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")

# 起点：真署名。**不含破折号拉引**。
BY_HIM = re.compile(r"\bby\s+MICHAEL\s+H?\.?\s*STEINHARDT\b", re.I)
# 终点候选一：别人的身份行（刊物作者标识的实际形态）
OTHER_ROLE = re.compile(
    r"\b([A-Z][a-z]{1,20}(?: [A-Z][a-z.']{1,20}){0,3}) is (?:the |a |an )?"
    r"(Chair|Chairman|President|Managing Director|Executive Director|Director|"
    r"Rabbi|Professor|founder|co-founder|CEO|Vice President|Editor)\b")
# 终点候选二：别人的署名
OTHER_BY = re.compile(
    r"\bby\s+((?!MICHAEL\s+H?\.?\s*STEINHARDT)[A-Z][A-Za-z.\-]+"
    r"(?:\s+[A-Z][A-Za-z.\-]+){1,3})\b")
# 终点候选三：他自己的文末身份行（正常结束）
HIS_SIG = re.compile(
    r"Michael\s+H?\.?\s*Steinhardt\s+is\s+(?:the\s+)?(Chairman|Founder|Chair)", re.I)

JUNK = re.compile(r"[^\x09\x0a\x0d\x20-\x7e -ɏ‐-›]")


def pdf_pages(raw: bytes, tag: str) -> list:
    p = os.path.join("/tmp", f"c2_{tag}.pdf")
    with open(p, "wb") as fh:
        fh.write(raw)
    try:
        import pypdf
        r = pypdf.PdfReader(p)
        out = []
        for pg in r.pages:
            try:
                out.append(pg.extract_text() or "")
            except Exception:
                out.append("")
        return out
    finally:
        os.remove(p)


def clean(t: str) -> str:
    t = re.sub(r"[ \t]+", " ", t)
    return re.sub(r"\n\s*\n+", "\n\n", t).strip()


def slice_his(pages: list):
    """返回 (正文, 说明)。正文**包含**署名行。

    ★ **按页切，不按扁平流切。** 实测 2009 春季刊第 3 页的文本流是：

        SPRING 2009 3 | Speculation about our economic future… （正文，整页）
        … but we Jews are no strangers to long odds. ■
        Michael H. Steinhardt is Chairman of The Steinhardt Foundation…  （他的文末身份行）
        THELandscape AHEAD by MICHAEL H. STEINHARDT                      （标题＋署名）

    也就是**正文在前、署名被排在页面文本流的最末**——版面上标题在页首，
    内容流里却最后吐出来。上一版从署名往「后」切 14000 字，
    切到的必然是**下一篇别人的文章**，还给它冠上了他的署名当证据。
    正确的做法是认页：含真署名的那一页（及其续页）整页是他的。

    另外两处不能误认：第 2 页刊头有 `Michael H. Steinhardt Chairman`
    （版权页职衔，不是署名），第 16 页有 `— MICHAEL H. STEINHARDT`
    （拉引归属）。判据只认 `by MICHAEL H. STEINHARDT`，两者都不会命中。
    """
    hit = [i for i, t in enumerate(pages) if BY_HIM.search(t or "")]
    if not hit:
        return None, "no-byline"
    out = []
    for i in hit:
        t = clean(pages[i] or "")
        # 同页若另有别人的身份行在前，从它之后起算（防同页两篇）
        starts = [m.end() for m in OTHER_ROLE.finditer(t)
                  if not re.search(r"steinhardt", m.group(1), re.I)]
        byline_at = BY_HIM.search(t).start()
        starts = [s for s in starts if s < byline_at - 900]
        if starts:
            t = t[max(starts):].strip()
        # 续页：只在**本页没有他的文末身份行**时才接。
        # 身份行 = 「他的文章到此为止」。2013 夏季刊第 3 页有身份行，
        # 第 4 页同主题同人称但归属两可——不确定时不接：
        # 误接的代价是把别人的话记成他的（正是本脚本在修的病），
        # 不接的代价只是短一点，而门要的是**源数**不是字数。
        nxt = i + 1
        if nxt < len(pages) and not HIS_SIG.search(t):
            n = clean(pages[nxt] or "")
            if n and not BY_HIM.search(n) and not OTHER_ROLE.search(n) \
                    and not OTHER_BY.search(n) and nxt not in hit:
                t = t + "\n\n" + n
        if len(t) >= 900:
            out.append(t)
    if not out:
        return None, "byline-but-short"
    return clean("\n\n".join(out)), f"pages({','.join(str(i+1) for i in hit)})"


def main() -> int:
    items = json.load(open(sys.argv[1], encoding="utf-8"))
    log_path = sys.argv[2]
    try:
        log = json.load(open(log_path))
    except Exception:
        log = {}
    os.makedirs(OUT, exist_ok=True)

    for it in items:
        key = it["key"]
        if log.get(key, {}).get("ok"):
            print("SKIP", key)
            continue
        try:
            req = urllib.request.Request(it["url"], headers={"User-Agent": UA})
            raw = urllib.request.urlopen(req, timeout=55, context=CTX).read(60_000_000)
        except Exception as e:
            log[key] = {"ok": False, "err": str(e)[:90]}
            print("FAIL", key, str(e)[:60])
            continue
        if raw[:4] != b"%PDF":
            log[key] = {"ok": False, "err": "not-pdf"}
            print("FAIL", key, "not-pdf")
            continue
        try:
            pages = pdf_pages(raw, key)
        except Exception as e:
            log[key] = {"ok": False, "err": "pdf:" + str(e)[:70]}
            print("FAIL", key, str(e)[:50])
            continue
        text, how = slice_his(pages)
        if not text:
            log[key] = {"ok": False, "err": how}
            print("MISS", key, how)
            json.dump(log, open(log_path, "w"), indent=1)
            continue
        if len(JUNK.findall(text)) / max(1, len(text)) > 0.05:
            log[key] = {"ok": False, "err": "junk"}
            print("REJECT(junk)", key)
            continue
        fn = f"ms_{it['year']}_contact_{it['slug']}.txt"
        with open(os.path.join(OUT, fn), "w", encoding="utf-8") as fh:
            fh.write(f"SOURCE_URL: {it['url']}\n\n{text}\n")
        log[key] = {"ok": True, "file": fn, "len": len(text), "how": how}
        print(f"OK  {fn:52s} {len(text):6d}  {how}")
        json.dump(log, open(log_path, "w"), indent=1)
        time.sleep(0.8)
    print(json.dumps({"landed": sum(1 for v in log.values() if v.get("ok"))}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
