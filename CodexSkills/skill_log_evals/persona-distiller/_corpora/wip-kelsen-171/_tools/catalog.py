#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""与编目记录对照：K10plus SRU 逐 PPN 查（串行，无 token，不花钱）。"""
import json, re, sys, time, urllib.parse, urllib.request

PPN = {
    "diestaatslehrede00kels":                         ["146748832"],
    "kommentarzurste00kelsgoog":                      ["377334669"],
    "kelsen-eine-grundlegung-der-rechtssoziologie":   ["39473713X"],
    "sozialismusundst00kels":                         ["138477094"],
    "vomwesenundwertd00kels":                         ["019970889"],
    "diebundesverfass00kels":                         ["066037980", "140516891"],
    "allgemeinestaats00kels":                         ["021386498"],
    "kelsen-fr-les-rapports-de-systeme-":             ["394725883"],
    "in.ernet.dli.2015.190098":                       ["141182563", "019970358"],
}
UA = "Mozilla/5.0 persona-distiller-corpus-fetch/1 (serial, concurrency=1)"
BASE = ("https://sru.k10plus.de/gvk?version=1.1&operation=searchRetrieve"
        "&query=pica.ppn%%3D%s&maximumRecords=1&recordSchema=marcxml")

out = {}
for ident, ppns in PPN.items():
    out[ident] = []
    for ppn in ppns:
        url = BASE % urllib.parse.quote(ppn)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=90) as r:
                xml = r.read().decode("utf-8", errors="replace")
        except Exception as e:
            out[ident].append({"ppn": ppn, "error": repr(e)})
            print("%-46s %-11s ERROR %r" % (ident[:46], ppn, e), flush=True)
            time.sleep(1.5); continue
        f008 = re.search(r'<(?:\w+:)?controlfield tag="008">([^<]*)<', xml)
        def sub(tag, code):
            m = re.search(r'<(?:\w+:)?datafield tag="%s".*?code="%s">(.*?)</' % (tag, code), xml, re.S)
            return re.sub(r"\s+", " ", m.group(1)).strip() if m else None
        rec = {
            "ppn": ppn,
            "008_date1": f008.group(1)[7:11] if f008 else None,
            "245a": sub("245", "a"), "245b": sub("245", "b"), "245c": sub("245", "c"),
            "250a": sub("250", "a"),
            "260a": sub("260", "a") or sub("264", "a"),
            "260b": sub("260", "b") or sub("264", "b"),
            "260c": sub("260", "c") or sub("264", "c"),
            "300a": sub("300", "a"),
            "numberOfRecords": (re.search(r"<\w*:?numberOfRecords>(\d+)<", xml) or [None, "?"])[1],
        }
        out[ident].append(rec)
        print("%-46s %-11s 008=%s  245a=%.44s | 260c=%s | 250=%s" %
              (ident[:46], ppn, rec["008_date1"], rec["245a"] or "-", rec["260c"], rec["250a"]), flush=True)
        time.sleep(1.5)

p = sys.argv[1]
json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("->", p)
