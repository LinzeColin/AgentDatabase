#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""并发恒为 1：串行拉取 IA metadata，只看有哪些纯文本文件可下。不花任何 API 钱。"""
import json, sys, time, urllib.request

IDS = [
    "diestaatslehrede00kels",
    "kommentarzurste00kelsgoog",
    "kelsen-eine-grundlegung-der-rechtssoziologie",
    "kelsen-rechtswissenschaft-als-norm-oder-kultur",
    "kelsen-politische-weltanschauung-und-erziehung",
    "sozialismusundst00kels",
    "vomwesenundwertd00kels",
    "kelsen-staat-und-recht",
    "diebundesverfass00kels",
    "allgemeinestaats00kels",
    "kelsen-fr-les-rapports-de-systeme-",
    "in.ernet.dli.2015.190098",
    "diestaatslehred00kelsgoog",
]

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) persona-distiller-corpus-fetch/1 (serial, concurrency=1)"

out = {}
for i, ident in enumerate(IDS):
    url = "https://archive.org/metadata/%s" % ident
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            data = json.load(r)
    except Exception as e:
        out[ident] = {"error": repr(e)}
        print("[%2d] %-50s ERROR %r" % (i + 1, ident, e), flush=True)
        time.sleep(1.0)
        continue
    md = data.get("metadata", {})
    files = data.get("files", [])
    txts = [
        {"name": f.get("name"), "size": f.get("size"), "format": f.get("format"), "sha1": f.get("sha1")}
        for f in files
        if str(f.get("name", "")).lower().endswith(".txt")
    ]
    out[ident] = {
        "date": md.get("date"),
        "year": md.get("year"),
        "title": md.get("title"),
        "creator": md.get("creator"),
        "publisher": md.get("publisher"),
        "language": md.get("language"),
        "description": md.get("description"),
        "possible-copyright-status": md.get("possible-copyright-status"),
        "licenseurl": md.get("licenseurl"),
        "imagecount": md.get("imagecount"),
        "scanningcentre": md.get("scanningcentre"),
        "sponsor": md.get("sponsor"),
        "contributor": md.get("contributor"),
        "identifier-access": md.get("identifier-access"),
        "collection": md.get("collection"),
        "txt_files": txts,
    }
    print("[%2d] %-50s date=%-12s txt=%s" % (i + 1, ident, md.get("date"), [t["name"] for t in txts]), flush=True)
    time.sleep(1.0)

p = sys.argv[1]
with open(p, "w", encoding="utf-8") as fh:
    json.dump(out, fh, ensure_ascii=False, indent=2)
print("written ->", p)
