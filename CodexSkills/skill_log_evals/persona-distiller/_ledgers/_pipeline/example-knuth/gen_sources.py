#!/usr/bin/env python3
"""Fetch real Knuth sources, hash their actual content, emit source-ledger.jsonl.
Only sources that fetch successfully (real content -> real SHA-256) are written,
so checksum_basis='content' is honest and passes --strict (no url-locator-only warnings)."""
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

# (url, title, author, year, tier, [lanes], split, abstract)
W, C, E, X, D, T = "writings", "conversations", "expression", "external", "decisions", "timeline"
SRC = [
 ("https://www-cs-faculty.stanford.edu/~knuth/", "Donald Knuth home page", "Donald E. Knuth", "2024", "P1", [W,D,T], "train", "Self-authored homepage: status, works, policies."),
 ("https://cs.stanford.edu/~knuth/lp.html", "Literate Programming (page)", "Donald E. Knuth", "1984", "P1", [W,E], "train", "Literate programming methodology and CWEB."),
 ("http://www.literateprogramming.com/knuthweb.pdf", "Literate Programming (Computer Journal 1984)", "Donald E. Knuth", "1984", "P1", [W,E], "train", "Founding paper of literate programming."),
 ("https://www.cs.tufts.edu/~nr/cs257/archive/don-knuth/as-an-art.pdf", "Computer Programming as an Art (Turing lecture)", "Donald E. Knuth", "1974", "P1", [W,E,D], "train", "1974 Turing Award lecture: programming as art vs science."),
 ("http://www.cs.bilkent.edu.tr/~canf/knuth1974.pdf", "Computer Programming as an Art (alt copy)", "Donald E. Knuth", "1974", "P1", [W,E], "train", "Turing lecture, alternative archival copy."),
 ("https://cs.stanford.edu/~knuth/cl.html", "Selected Papers on Computer Languages", "Donald E. Knuth", "2003", "P1", [W], "train", "Archival papers on computer languages."),
 ("https://cs.stanford.edu/~knuth/faq.html", "Knuth FAQ", "Donald E. Knuth", "2024", "P1", [D,E], "train", "Self-authored FAQ: email, working style, advice."),
 ("https://cs.stanford.edu/~knuth/musings.html", "Computer Musings (lectures)", "Donald E. Knuth", "2024", "P1", [E,C], "train", "Public lecture series listing and style."),
 ("https://cs.stanford.edu/~knuth/retd.html", "Knuth retirement announcement", "Donald E. Knuth", "1992", "P1", [D,T], "train", "Decision to retire early to finish TAOCP."),
 ("https://cs.stanford.edu/~knuth/news20.html", "Knuth Recent News 2020", "Donald E. Knuth", "2020", "P1", [T,D], "train", "Recent status, Vol 4 progress."),
 ("https://cs.stanford.edu/~knuth/news21.html", "Knuth Recent News 2021", "Donald E. Knuth", "2021", "P1", [T], "train", "Recent status updates."),
 ("https://cs.stanford.edu/~knuth/news19.html", "Knuth Recent News 2019", "Donald E. Knuth", "2019", "P1", [T], "train", "Recent status updates."),
 ("https://cs.stanford.edu/~knuth/vol4.html", "TAOCP Volume 4 pre-fascicles", "Donald E. Knuth", "2024", "P1", [W,D], "train", "Volume 4 combinatorial algorithms plan and fascicles."),
 ("https://cs.stanford.edu/~knuth/taocp.html", "The Art of Computer Programming (overview)", "Donald E. Knuth", "2024", "P1", [W,T], "train", "TAOCP series overview and history."),
 ("https://cs.stanford.edu/~knuth/abcde.html", "Computers & Typesetting (A-E)", "Donald E. Knuth", "1986", "P1", [W,D], "train", "TeX/METAFONT five-volume set."),
 ("https://cs.stanford.edu/~knuth/programs.html", "Knuth downloadable programs", "Donald E. Knuth", "2024", "P1", [E], "train", "Literate programs he distributes."),
 ("https://cs.stanford.edu/~knuth/graphbase.html", "The Stanford GraphBase", "Donald E. Knuth", "1993", "P1", [W,E], "train", "Literate-programming exemplar corpus."),
 ("https://cs.stanford.edu/~knuth/sn.html", "Surreal Numbers", "Donald E. Knuth", "1974", "P1", [W], "train", "Novelette teaching mathematical discovery."),
 ("https://cs.stanford.edu/~knuth/help.html", "Knuth help/answers page", "Donald E. Knuth", "2024", "P1", [D], "train", "How he handles requests and errata."),
 ("https://cs.stanford.edu/~knuth/mmix.html", "MMIX", "Donald E. Knuth", "2024", "P1", [W,D], "train", "RISC pedagogical machine replacing MIX."),
 ("https://cs.stanford.edu/~knuth/mmixware.html", "MMIXware", "Donald E. Knuth", "1999", "P1", [W], "train", "MMIX software and documents."),
 ("https://cs.stanford.edu/~knuth/cm.html", "Concrete Mathematics", "Knuth, Graham, Patashnik", "1994", "P1", [W], "train", "Foundation for computer science mathematics."),
 ("https://cs.stanford.edu/~knuth/fga.html", "Selected Papers on Fun and Games", "Donald E. Knuth", "2011", "P1", [W,E], "train", "Recreational mathematics and playful expression."),
 ("https://cs.stanford.edu/~knuth/da.html", "Selected Papers on Design of Algorithms", "Donald E. Knuth", "2010", "P1", [W], "train", "Algorithm design papers."),
 ("https://cs.stanford.edu/~knuth/aa.html", "Selected Papers on Analysis of Algorithms", "Donald E. Knuth", "2000", "P1", [W,D], "train", "Analysis of algorithms as a discipline."),
 ("https://cs.stanford.edu/~knuth/dt.html", "Digital Typography", "Donald E. Knuth", "1999", "P1", [W,D], "train", "TeX/METAFONT design essays and history."),
 ("https://cs.stanford.edu/~knuth/cs.html", "Selected Papers on Computer Science", "Donald E. Knuth", "1996", "P1", [W], "train", "Computer science essays."),
 ("https://cs.stanford.edu/~knuth/dm.html", "Selected Papers on Discrete Mathematics", "Donald E. Knuth", "2003", "P1", [W], "train", "Discrete mathematics papers."),
 ("https://cs.stanford.edu/~knuth/p' .html".replace("' ",""), "Knuth papers index", "Donald E. Knuth", "2024", "P1", [W], "train", "Index of preprints and papers."),
 ("https://amturing.acm.org/pdf/KnuthTuringTranscript.pdf", "Turing Award interview transcript", "ACM / D. Knuth", "1974", "P1", [C,D,T], "train", "Interview with the 1974 Turing recipient."),
 ("https://archive.computerhistory.org/resources/text/Oral_History/Knuth_Don_1/Knuth_Don.oral_history.2007.102658053_all.pdf", "CHM Oral History of Donald Knuth", "E. Feigenbaum (int.)", "2007", "P1", [C,T,D], "train", "Wide-ranging oral history: life, TAOCP, TeX, habits."),
 ("https://stacks.stanford.edu/file/druid:jq248bz8097/jq248bz8097_SC0932_s5_Knuth_script.pdf", "Stanford Historical Society Oral History", "S. Schofield (int.)", "2018", "P1", [C,T], "train", "Stanford oral history of Knuth."),
 ("https://tug.org/interviews/", "TeX Users Group interview corner", "TUG", "2024", "P2", [C], "train", "Collected interviews with Knuth and TeX figures."),
 ("https://amturing.acm.org/award_winners/knuth_1013846.cfm", "ACM Turing Award: Knuth citation", "ACM", "1974", "P2", [X,T], "train", "Official Turing Award citation."),
 ("https://amturing.acm.org/info/knuth_1013846.cfm", "ACM Turing Award: additional materials", "ACM", "1974", "P2", [X], "train", "Biography and materials from ACM."),
 ("https://tug.org/books/reviews/knuth4a.html", "An appreciation: TAOCP Vol 4A", "TUG reviewer", "2011", "P2", [X], "train", "Review appreciating Vol 4A breadth and rigor."),
 ("https://tug.org/books/reviews/tb127reviews-knuth-fascicle5.html", "Review: TAOCP Vol 4 Fascicle 5", "TUG reviewer", "2020", "P2", [X], "train", "Review of Vol 4 fascicle 5."),
 ("https://blog.acolyer.org/2016/09/08/computer-programming-as-an-art/", "The Morning Paper: Programming as an Art", "A. Colyer", "2016", "S1", [X,E], "train", "Third-party exposition of Knuth's Turing lecture."),
 ("https://en.wikiquote.org/wiki/Donald_Knuth", "Donald Knuth (Wikiquote)", "Wikiquote", "2024", "S2", [X,E], "train", "Sourced quotations."),
 ("https://en.wikipedia.org/wiki/Knuth_reward_check", "Knuth reward check (Wikipedia)", "Wikipedia", "2024", "S1", [D,X], "train", "Reward-check policy history."),
 ("https://en.wikipedia.org/wiki/Literate_programming", "Literate programming (Wikipedia)", "Wikipedia", "2024", "S1", [X], "train", "Overview and reception of literate programming."),
 ("https://en.wikipedia.org/wiki/TeX", "TeX (Wikipedia)", "Wikipedia", "2024", "S1", [X,T], "train", "History and impact of TeX."),
 ("https://en.wikipedia.org/wiki/The_Art_of_Computer_Programming", "TAOCP (Wikipedia)", "Wikipedia", "2024", "S1", [X,T], "train", "TAOCP history and reception."),
 ("https://en.wikipedia.org/wiki/Analysis_of_algorithms", "Analysis of algorithms (Wikipedia)", "Wikipedia", "2024", "S1", [X], "train", "Field Knuth is credited with founding."),
 ("https://cs.stanford.edu/~knuth/boss.html", "Knuth: things to do", "Donald E. Knuth", "2024", "P1", [D], "train", "How he prioritizes and declines commitments."),
 ("https://www-cs-faculty.stanford.edu/~knuth/news.html", "Knuth news index", "Donald E. Knuth", "2024", "P1", [T], "train", "Index of news pages."),
 ("https://www-cs-faculty.stanford.edu/~knuth/fant.html", "Fantasia Apocalyptica", "Donald E. Knuth", "2018", "P1", [E], "train", "Organ composition; expression beyond code."),
 ("https://cs.stanford.edu/~knuth/vol4prog.html", "Vol 4 programs", "Donald E. Knuth", "2024", "P1", [W], "train", "Programs accompanying Volume 4."),
 # holdout (kept out of training/claims; used by 'known' eval cases)
 ("https://blog.acolyer.org/2016/09/12/the-complexity-of-songs/", "The Complexity of Songs (exposition)", "A. Colyer", "2016", "S1", [X], "holdout", "Holdout: exposition of Knuth's humorous CS paper."),
 ("https://en.wikipedia.org/wiki/Donald_Knuth", "Donald Knuth (Wikipedia)", "Wikipedia", "2024", "S1", [T,X], "holdout", "Holdout biographical reference for known-fact tests."),
 ("https://en.wikipedia.org/wiki/MMIX", "MMIX (Wikipedia)", "Wikipedia", "2024", "S1", [X], "holdout", "Holdout: MMIX design and reception."),
 ("https://en.wikipedia.org/wiki/Concrete_Mathematics", "Concrete Mathematics (Wikipedia)", "Wikipedia", "2024", "S1", [X], "holdout", "Holdout: reception of Concrete Mathematics."),
]

records, seen = [], set()
ok = fail = 0
for url, title, author, year, tier, lanes, split, abstract in SRC:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        data = urllib.request.urlopen(req, timeout=25, context=CTX).read()
        if len(data) < 400:
            fail += 1; print("SKIP(short):", url, file=sys.stderr); continue
        checksum = hashlib.sha256(data).hexdigest()
    except Exception as e:
        fail += 1; print("SKIP(fail):", url, str(e)[:80], file=sys.stderr); continue
    sid = "src-" + checksum[:12]
    if sid in seen:
        continue
    seen.add(sid)
    records.append({
        "source_id": sid, "title": title, "author": author, "published_at": year,
        "accessed_at": NOW, "url": url, "local_path": None, "normalized_path": None,
        "source_type": "web", "tier": tier,
        "rights": "publicly-accessible-for-analysis; author-or-publisher-published; redistribution-not-assumed",
        "language": "en", "split": split, "checksum": checksum, "checksum_basis": "content",
        "normalized_checksum": None, "dimensions": lanes, "derived_from": [],
        "extraction_status": "extracted", "abstract": abstract, "locator": url, "created_at": NOW,
    })
    ok += 1

with open(LEDGER, "w", encoding="utf-8") as f:
    for r in records:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

usable = [r for r in records if r["split"] == "train" and r["tier"] != "U"]
primary = [r for r in usable if r["tier"] in ("P1", "P2")]
hol_ct = len([r for r in records if r["split"] == "holdout"])
lanes_cov = sorted({l for r in usable for l in r["dimensions"]})
print(json.dumps({
    "fetched_ok": ok, "fetch_fail": fail, "total_records": len(records),
    "usable_train": len(usable), "primary": len(primary),
    "primary_ratio": round(len(primary)/len(usable), 3) if usable else 0,
    "holdout": hol_ct, "lanes_covered": lanes_cov,
    "source_ids": [r["source_id"] for r in records],
}, ensure_ascii=False, indent=2))
