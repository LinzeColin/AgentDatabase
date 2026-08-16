#!/usr/bin/env python3
"""Append more real, fetchable Knuth sources to reach >=45 usable train."""
import hashlib, json, sys, urllib.request, ssl
from datetime import datetime, timezone
# ★★ 2026-08-17：原先这里写死一条**别的会话的 scratchpad 绝对路径**
#   （`/private/tmp/claude-501/-Users-…-character-distillation-skill-reorganize-d57595/…`），
#   而那条路径**早已不存在**。RUNBOOK 让操作者「照 example-knuth/ 抄」——
#   抄到的是一个指向死路径的脚本：它看起来像真路径，不像 `<WORKSPACE>` 那样
#   一眼可见要替换，于是**会静默写到别处或直接崩**。
#   ⇒ 改成从 argv/环境变量取，缺了就**明确报错**，不给默认值。
import os as _os, sys as _sys
_T = (_sys.argv[1] if len(_sys.argv) > 1 else _os.environ.get("PD_TARGET"))
if not _T:
    _sys.exit("用法：%s <工作区目录>（或设环境变量 PD_TARGET）——本脚本是**样例模板**，不带默认路径。" % _sys.argv[0])
TARGET = _T

LEDGER = TARGET + "/evidence/source-ledger.jsonl"
NOW = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
CTX = ssl.create_default_context(); CTX.check_hostname = False; CTX.verify_mode = ssl.CERT_NONE
UA = "Mozilla/5.0 (research; persona-distiller)"
W, C, E, X, D, T = "writings", "conversations", "expression", "external", "decisions", "timeline"
MORE = [
 ("https://cs.stanford.edu/~knuth/news22.html", "Knuth Recent News 2022", "Donald E. Knuth", "2022", "P1", [T], "train", "Status and Vol 4B publication."),
 ("https://cs.stanford.edu/~knuth/news23.html", "Knuth Recent News 2023", "Donald E. Knuth", "2023", "P1", [T], "train", "Recent status."),
 ("https://cs.stanford.edu/~knuth/news18.html", "Knuth Recent News 2018", "Donald E. Knuth", "2018", "P1", [T], "train", "Recent status."),
 ("https://cs.stanford.edu/~knuth/news17.html", "Knuth Recent News 2017", "Donald E. Knuth", "2017", "P1", [T], "train", "Recent status."),
 ("https://cs.stanford.edu/~knuth/cweb.html", "CWEB system", "Donald E. Knuth", "2024", "P1", [W,E], "train", "CWEB literate-programming system."),
 ("https://cs.stanford.edu/~knuth/preprints.html", "Knuth recent preprints", "Donald E. Knuth", "2024", "P1", [W], "train", "Recent preprints and papers."),
 ("https://en.wikipedia.org/wiki/METAFONT", "METAFONT (Wikipedia)", "Wikipedia", "2024", "S1", [X,T], "train", "Font description system by Knuth."),
 ("https://en.wikipedia.org/wiki/CWEB", "CWEB (Wikipedia)", "Wikipedia", "2024", "S1", [X], "train", "Literate programming system reception."),
 ("https://en.wikipedia.org/wiki/Knuth%E2%80%93Morris%E2%80%93Pratt_algorithm", "Knuth-Morris-Pratt (Wikipedia)", "Wikipedia", "2024", "S1", [X,D], "train", "String search algorithm co-devised by Knuth."),
 ("https://en.wikipedia.org/wiki/Computer_Modern", "Computer Modern (Wikipedia)", "Wikipedia", "2024", "S1", [X], "train", "Typeface family designed with METAFONT."),
 ("https://en.wikipedia.org/wiki/Dancing_Links", "Dancing Links (Wikipedia)", "Wikipedia", "2024", "S1", [X,D], "train", "Knuth's Algorithm X / DLX technique."),
 ("https://en.wikipedia.org/wiki/Surreal_number", "Surreal number (Wikipedia)", "Wikipedia", "2024", "S1", [X], "train", "Concept Knuth named and popularized."),
 ("https://cs.stanford.edu/~knuth/news16.html", "Knuth Recent News 2016", "Donald E. Knuth", "2016", "P1", [T], "train", "Recent status."),
 ("https://cs.stanford.edu/~knuth/news15.html", "Knuth Recent News 2015", "Donald E. Knuth", "2015", "P1", [T], "train", "Recent status."),
]
existing = [json.loads(l) for l in open(LEDGER, encoding="utf-8") if l.strip()]
have_ids = {r["source_id"] for r in existing}; have_urls = {r["url"] for r in existing}
added = 0
for url, title, author, year, tier, lanes, split, abstract in MORE:
    if url in have_urls: continue
    try:
        data = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=25, context=CTX).read()
        if len(data) < 400: raise ValueError("short")
        checksum = hashlib.sha256(data).hexdigest()
    except Exception as e:
        print("SKIP:", url, str(e)[:70], file=sys.stderr); continue
    sid = "src-" + checksum[:12]
    if sid in have_ids: continue
    have_ids.add(sid); have_urls.add(url)
    existing.append({"source_id": sid, "title": title, "author": author, "published_at": year,
        "accessed_at": NOW, "url": url, "local_path": None, "normalized_path": None, "source_type": "web",
        "tier": tier, "rights": "publicly-accessible-for-analysis; author-or-publisher-published; redistribution-not-assumed",
        "language": "en", "split": split, "checksum": checksum, "checksum_basis": "content",
        "normalized_checksum": None, "dimensions": lanes, "derived_from": [], "extraction_status": "extracted",
        "abstract": abstract, "locator": url, "created_at": NOW})
    added += 1
with open(LEDGER, "w", encoding="utf-8") as f:
    for r in existing: f.write(json.dumps(r, ensure_ascii=False) + "\n")
usable = [r for r in existing if r["split"] == "train" and r["tier"] != "U"]
primary = [r for r in usable if r["tier"] in ("P1", "P2")]
print(json.dumps({"added": added, "total": len(existing), "usable_train": len(usable),
    "primary": len(primary), "primary_ratio": round(len(primary)/len(usable), 3),
    "holdout": len([r for r in existing if r["split"]=="holdout"])}, ensure_ascii=False, indent=2))
