#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
#171 Kelsen 一手语料抓取。
- 并发恒为 1（串行，每件之间 sleep）
- 不花任何 API 钱（archive.org 公开 download 端点）
- 不碰付费墙、不绕访问控制
- ★ 落盘的 .txt 与 IA 服务端返回的字节**完全一致**，不加任何出处表头
  （本项目记档事故：我写的出处表头被当成正文，占全文 17.2%，还把烂 OCR 托过可读性门）
  出处信息一律写在同目录的 SOURCE.json 里。
"""
import hashlib, json, os, sys, time, urllib.parse, urllib.request

RAW = "/Users/linzezhang/Documents/Codex/GithubProject/_scratch/agentdb-nasmyth-153/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-kelsen-171/raw"
META = "/private/tmp/claude-501/-Users-linzezhang-Documents-Codex-AgentDatabase-interesting-franklin-988afc/c696b54c-ba7d-4598-8b2f-49420c27e567/scratchpad/ia_meta.json"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) persona-distiller-corpus-fetch/1 (serial, concurrency=1)"

# (IA identifier, 可读英文短名)
PLAN = [
    ("diestaatslehrede00kels",                         "staatslehre-dante-1905.txt"),
    ("kommentarzurste00kelsgoog",                      "kommentar-reichsratswahlordnung-1907.txt"),
    ("kelsen-eine-grundlegung-der-rechtssoziologie",   "grundlegung-rechtssoziologie-1914.txt"),
    ("kelsen-rechtswissenschaft-als-norm-oder-kultur", "rechtswissenschaft-norm-oder-kultur-1916.txt"),
    ("kelsen-politische-weltanschauung-und-erziehung", "politische-weltanschauung-erziehung-1918.txt"),
    ("sozialismusundst00kels",                         "sozialismus-und-staat-1920.txt"),
    ("vomwesenundwertd00kels",                         "wesen-und-wert-der-demokratie-1920.txt"),
    ("kelsen-staat-und-recht",                         "staat-und-recht-1922.txt"),
    ("diebundesverfass00kels",                         "bundesverfassung-1920-coedited-1922.txt"),
    ("allgemeinestaats00kels",                         "allgemeine-staatslehre-1925.txt"),
    ("kelsen-fr-les-rapports-de-systeme-",             "rapports-de-systeme-1926-fr.txt"),
    ("in.ernet.dli.2015.190098",                       "problem-der-souveraenitaet-1928.txt"),
]


def srcdir(ident):
    """src-<12位十六进制>：sha256(identifier) 前 12 位，可复算。"""
    return "src-" + hashlib.sha256(ident.encode("utf-8")).hexdigest()[:12]


def main():
    meta = json.load(open(META, encoding="utf-8"))
    ledger = []
    for i, (ident, short) in enumerate(PLAN, 1):
        m = meta[ident]
        txts = [t for t in m["txt_files"] if t["name"].endswith("_djvu.txt")]
        assert len(txts) == 1, (ident, txts)
        remote = txts[0]["name"]
        d = os.path.join(RAW, srcdir(ident))
        os.makedirs(d, exist_ok=True)
        dst = os.path.join(d, short)
        url = "https://archive.org/download/%s/%s" % (ident, urllib.parse.quote(remote))
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=300) as r:
            body = r.read()
            status = r.status
            final_url = r.geturl()
        with open(dst, "wb") as fh:
            fh.write(body)
        sha = hashlib.sha256(body).hexdigest()
        rec = {
            "n": i,
            "ia_identifier": ident,
            "src_dir": srcdir(ident),
            "filename": short,
            "remote_filename": remote,
            "download_url": url,
            "final_url": final_url,
            "http_status": status,
            "bytes": len(body),
            "sha256": sha,
            "ia_reported_size": txts[0]["size"],
            "ia_metadata_date_field": m.get("date"),
            "ia_title_field": m.get("title"),
            "ia_creator_field": m.get("creator"),
            "ia_publisher_field": m.get("publisher"),
            "ia_language_field": m.get("language"),
            "ia_contributor_field": m.get("contributor"),
            "ia_possible_copyright_status": m.get("possible-copyright-status"),
            "ia_licenseurl": m.get("licenseurl"),
            "ia_description": m.get("description"),
            "details_url": "https://archive.org/details/%s" % ident,
            "fetched_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "elapsed_s": round(time.time() - t0, 2),
            "note": "落盘 .txt 与 IA 返回字节完全一致，未加任何出处表头、未做任何 OCR 修改。",
        }
        with open(os.path.join(d, "SOURCE.json"), "w", encoding="utf-8") as fh:
            json.dump(rec, fh, ensure_ascii=False, indent=2)
        ledger.append(rec)
        print("[%2d/12] %-46s %8d B  sha256=%s  %.1fs" % (i, ident, len(body), sha[:16], rec["elapsed_s"]), flush=True)
        time.sleep(1.5)

    out = os.path.join(os.path.dirname(META), "fetch_ledger.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(ledger, fh, ensure_ascii=False, indent=2)
    print("ledger ->", out)


if __name__ == "__main__":
    main()
