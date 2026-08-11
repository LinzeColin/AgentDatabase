#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
#171 Kelsen 语料落盘自检 v2。全部读回落盘文件现算。

v1 → v2 修了我自己两个缺陷（都是先看命中样本才发现的）：
  1) **语种关**：德语讹形族在法语件上只有 18 个 token 的分母，却算出 38.9%，
     差点把全批最干净的一件标成「不可做逐字引文」。→ 德语判据只对德语件跑；法语件用法语词对。
  2) **分母下限**：h→b 轴在 1922 合编卷上是 8/10 = 80%，分母只有 10。
     → 分母 < MIN_N 一律报 n/a(N=x)，不报比值。
"""
import collections, hashlib, json, os, re

RAW = "/Users/linzezhang/Documents/Codex/GithubProject/_scratch/agentdb-nasmyth-153/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-kelsen-171/raw"
MIN_N = 50          # 比值的最小分母，低于它报 n/a
GATE = 0.20         # 指令给的门：>20% 标「不可做逐字引文」

GENRE = {
    "staatslehre-dante-1905.txt":                   ("writings",   "1905", "ger"),
    "kommentar-reichsratswahlordnung-1907.txt":     ("decisions",  "1907", "ger"),
    "grundlegung-rechtssoziologie-1914.txt":        ("expression", "1914", "ger"),
    "rechtswissenschaft-norm-oder-kultur-1916.txt": ("expression", "1916", "ger"),
    "politische-weltanschauung-erziehung-1918.txt": ("expression", "1918", "ger"),
    "sozialismus-und-staat-1920.txt":               ("writings",   "1920", "ger"),
    "wesen-und-wert-der-demokratie-1920.txt":       ("writings",   "1920", "ger"),
    "staat-und-recht-1922.txt":                     ("expression", "1922", "ger"),
    "bundesverfassung-1920-coedited-1922.txt":      ("decisions",  "1922", "ger"),
    "allgemeine-staatslehre-1925.txt":              ("writings",   "1925", "ger"),
    "rapports-de-systeme-1926-fr.txt":              ("expression", "1926", "fre"),
    "problem-der-souveraenitaet-1928.txt":          ("writings",   "1928", "ger"),
}

FOREIGN_BLOCKS = {
    "staatslehre-dante-1905.txt":               [(0, 8, "IA『Digitized by the Internet Archive』告示")],
    "kommentar-reichsratswahlordnung-1907.txt": [(0, 97, "Google 扫描样板（英德双语使用条款）——★全文 6 个 wir 全在这里")],
    "allgemeine-staatslehre-1925.txt":          [(123, 129, "IA『Digitized by the Internet Archive』告示")],
    "bundesverfassung-1920-coedited-1922.txt":  [(20, 28, "IA『Digitized by the Internet Archive』告示")],
    "rapports-de-systeme-1926-fr.txt":          [(19, 95, "海牙学院编的 NOTICE BIOGRAPHIQUE + PUBLICATIONS（第三人称写他，非他的文字）")],
}

WB = r"(?<![A-Za-zÀ-ÿſ])%s(?![A-Za-zÀ-ÿſ])"
WORD = re.compile(r"[A-Za-zÀ-ÿſ]+")

# 德语：正形 / 指令点名的讹形 / 本轮实测形族（形状打印在产物里）
DE_PAIRS = {
    "nicht": ("nicht", "nidjt", r"n[iı][dcĉ][^\W\d_]{0,3}t"),
    "ist":   ("ist",   "ift",   r"[iı][fſj\[]t|ift|iſt|i\[t"),
    "und":   ("und",   "nnd",   r"[unm][nu][dbt]"),
    "sein":  ("sein",  "fein",  r"[sfſ]e[iı][nu]"),
}
DE_CLEAN = {"nicht": {"nicht"}, "ist": {"ist"}, "und": {"und"}, "sein": {"sein"}}
# 法语：同型的高频词对（本件排体是 Antiqua 拉丁字母，无长 s，无 Fraktur 讹形）
FR_PAIRS = {"est": ("est", "eft"), "dans": ("dans", "dana"), "pour": ("pour", "ponr"),
            "qui": ("qui", "qni"), "les": ("les", "lea"), "des": ("des", "dea"), "une": ("une", "nne")}

HB = [("ich", "icb"), ("nicht", "nicbt"), ("auch", "aucb"), ("sich", "sicb"),
      ("habe", "babe"), ("nach", "nacb"), ("durch", "durcb"), ("noch", "nocb")]

ICH_VAR = [r"icb", r"id\)", r"idj", r"id\}", r"idi", r"id\^", r"ic\^", r"id\]"]
WIR_VAR = [r"toir", r"ttir", r"roir", r"tvir", r"ttiir"]


def cnt(t, s):
    return len(re.findall("(?i)" + (WB % s), t))


def ratio(bad, total):
    if total < MIN_N:
        return None, "n/a(N=%d<%d)" % (total, MIN_N)
    return round(bad / total, 4), "%.1f%%" % (100.0 * bad / total)


def main():
    rows = []
    for d in sorted(os.listdir(RAW)):
        p = os.path.join(RAW, d)
        if not os.path.isdir(p):
            continue
        txt = [f for f in os.listdir(p) if f.endswith(".txt")][0]
        blob = open(os.path.join(p, txt), "rb").read()
        t = blob.decode("utf-8", errors="replace")
        lines = t.split("\n")
        src = json.load(open(os.path.join(p, "SOURCE.json"), encoding="utf-8"))
        genre, year, lang = GENRE[txt]

        drop, fbs = set(), []
        for a, b, why in FOREIGN_BLOCKS.get(txt, []):
            drop.update(range(a, min(b + 1, len(lines))))
            blk = "\n".join(lines[a:b + 1])
            fbs.append({"lines": [a, b], "why": why, "words": len(WORD.findall(blk)),
                        "ich": cnt(blk, "ich"), "wir": cnt(blk, "wir")})
        body = "\n".join(l for i, l in enumerate(lines) if i not in drop)
        w_all, w_body = len(WORD.findall(t)), len(WORD.findall(body))

        pairs, trig = {}, []
        n_bad = n_tot = f_bad = f_tot = 0
        maxnamed = maxfam = ("", 0.0)
        if lang == "ger":
            for k, (good, nb_form, shape) in DE_PAIRS.items():
                g, nb = cnt(t, re.escape(good)), cnt(t, re.escape(nb_form))
                fam = collections.Counter(m.group(0).lower() for m in
                                          re.finditer("(?i)" + (WB % ("(?:%s)" % shape)), t))
                fg = sum(v for kk, v in fam.items() if kk in DE_CLEAN[k])
                fb2 = sum(v for kk, v in fam.items() if kk not in DE_CLEAN[k])
                rn, rns = ratio(nb, g + nb)
                rf, rfs = ratio(fb2, fg + fb2)
                pairs[k] = {"shape": shape, "good": g, "named_bad_form": nb_form, "named_bad": nb,
                            "named_ratio": rn, "named_ratio_str": rns,
                            "family_good": fg, "family_bad": fb2,
                            "family_ratio": rf, "family_ratio_str": rfs,
                            "family_top": fam.most_common(8)}
                n_bad += nb; n_tot += g + nb; f_bad += fb2; f_tot += fg + fb2
                if rn and rn > maxnamed[1]: maxnamed = (k, rn)
                if rf and rf > maxfam[1]: maxfam = (k, rf)
        else:
            for k, (good, bad) in FR_PAIRS.items():
                g, b2 = cnt(t, re.escape(good)), cnt(t, re.escape(bad))
                r, rs = ratio(b2, g + b2)
                pairs[k] = {"good": g, "named_bad_form": bad, "named_bad": b2,
                            "named_ratio": r, "named_ratio_str": rs}
                n_bad += b2; n_tot += g + b2
                if r and r > maxnamed[1]: maxnamed = (k, r)
            f_bad, f_tot = n_bad, n_tot

        pn, pns = ratio(n_bad, n_tot)
        pf, pfs = ratio(f_bad, f_tot)
        longs = t.count("ſ"); s_all = len(re.findall(r"[sSſ]", t))
        pl, pls = ratio(longs, s_all)
        hb_g = sum(cnt(t, re.escape(a)) for a, _ in HB)
        hb_b = sum(cnt(t, re.escape(b)) for _, b in HB)
        ph, phs = ratio(hb_b, hb_g + hb_b)
        dia = len(re.findall(r"[äöüÄÖÜß]" if lang == "ger" else r"[éèêàçùôîïûÉÈÀÇ]", t))

        if pn and pn > GATE: trig.append("指令四对合池 %s" % pns)
        if maxnamed[1] > GATE: trig.append("指令四对单对最高 %s=%.1f%%" % (maxnamed[0], 100 * maxnamed[1]))
        if pf and pf > GATE: trig.append("实测形族合池 %s" % pfs)
        if maxfam[1] > GATE: trig.append("实测形族单对最高 %s=%.1f%%" % (maxfam[0], 100 * maxfam[1]))
        if pl and pl > GATE: trig.append("长s残留 %s" % pls)
        if ph and ph > GATE: trig.append("h→b 混淆 %s（★指令未写的轴，N=%d）" % (phs, hb_g + hb_b))
        if lang == "ger" and w_all > 5000 and dia / max(w_all, 1) * 1000 < 5:
            trig.append("变音符近乎全失（%.1f/千词，阈值 5.0）★指令未写的轴" % (1000.0 * dia / w_all))

        ich_s, wir_s = cnt(body, "ich"), cnt(body, "wir")
        ich_v = sum(cnt(body, v) for v in ICH_VAR)
        wir_v = sum(cnt(body, v) for v in WIR_VAR)
        rows.append({
            "src_dir": d, "file": txt, "ia_identifier": src["ia_identifier"],
            "genre": genre, "year": year, "lang": lang,
            "bytes": len(blob), "sha256": hashlib.sha256(blob).hexdigest(),
            "bytes_match_source_json": len(blob) == src["bytes"],
            "sha256_match_source_json": hashlib.sha256(blob).hexdigest() == src["sha256"],
            "ia_reported_size": int(src["ia_reported_size"]),
            "bytes_match_ia_reported": len(blob) == int(src["ia_reported_size"]),
            "lines": len(lines), "words_whole_file": w_all, "words_body": w_body,
            "foreign_blocks": fbs,
            "corruption": {"pairs": pairs,
                           "pooled_named": pn, "pooled_named_str": pns, "pooled_named_N": n_tot,
                           "pooled_family": pf, "pooled_family_str": pfs, "pooled_family_N": f_tot,
                           "max_named_pair": maxnamed, "max_family_pair": maxfam,
                           "long_s": longs, "long_s_ratio": pl, "long_s_ratio_str": pls,
                           "hb_good": hb_g, "hb_bad": hb_b, "hb_ratio": ph, "hb_ratio_str": phs,
                           "diacritics": dia, "diacritics_per_1k_words": round(1000.0 * dia / max(w_all, 1), 1)},
            "no_verbatim_quote": bool(trig), "trigger": trig,
            "first_person": {
                "ich_strict": ich_s, "wir_strict": wir_s,
                "ich_ocr_var": ich_v, "wir_ocr_var": wir_v,
                "ich_per_10k": round(10000.0 * ich_s / max(w_body, 1), 2),
                "wir_per_10k": round(10000.0 * wir_s / max(w_body, 1), 2),
                "ich_tol_per_10k": round(10000.0 * (ich_s + ich_v) / max(w_body, 1), 2),
                "wir_tol_per_10k": round(10000.0 * (wir_s + wir_v) / max(w_body, 1), 2),
                "je_fr": cnt(body, "je"), "nous_fr": cnt(body, "nous"),
            },
        })

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "measure2.json")
    json.dump(rows, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    print("落盘件数 %d / 计划 12\n" % len(rows))
    print("%-44s %-10s %4s %9s %9s %8s %8s %8s %7s %5s" %
          ("file", "genre", "lang", "bytes", "words", "指令池", "族池", "长s", "h→b", "禁引"))
    for r in rows:
        c = r["corruption"]
        print("%-44s %-10s %4s %9d %9d %8s %8s %8s %7s %5s" % (
            r["file"][:44], r["genre"], r["lang"], r["bytes"], r["words_whole_file"],
            c["pooled_named_str"], c["pooled_family_str"], c["long_s_ratio_str"],
            c["hb_ratio_str"], "禁" if r["no_verbatim_quote"] else "-"))
    print()
    for r in rows:
        if r["no_verbatim_quote"]:
            print("禁引  %-44s %s" % (r["file"][:44], "；".join(r["trigger"])))
    print("\nbytes/sha256 与 SOURCE.json 一致 %d/%d；bytes 与 IA 自报 size 一致 %d/%d" % (
        sum(1 for r in rows if r["bytes_match_source_json"] and r["sha256_match_source_json"]), len(rows),
        sum(1 for r in rows if r["bytes_match_ia_reported"]), len(rows)))

    print("\n—— 第一人称密度（每万词，分母＝扣掉非 Kelsen 块后的词数）——")
    print("%-44s %-10s %9s %8s %8s %8s %8s" % ("file", "genre", "words", "ich", "wir", "ich+讹", "wir+讹"))
    agg = collections.defaultdict(lambda: [0, 0, 0, 0, 0])
    for r in rows:
        fp = r["first_person"]
        print("%-44s %-10s %9d %8.2f %8.2f %8.2f %8.2f" % (
            r["file"][:44], r["genre"], r["words_body"], fp["ich_per_10k"], fp["wir_per_10k"],
            fp["ich_tol_per_10k"], fp["wir_tol_per_10k"]))
        a = agg[r["genre"]]
        a[0] += r["words_body"]; a[1] += fp["ich_strict"]; a[2] += fp["wir_strict"]
        a[3] += fp["ich_strict"] + fp["ich_ocr_var"]; a[4] += fp["wir_strict"] + fp["wir_ocr_var"]
    print("\n—— 按体裁汇总 ——")
    print("%-12s %9s %7s %7s %9s %9s %11s %11s" % ("genre", "words", "ich", "wir", "ich/万", "wir/万", "ich+讹/万", "wir+讹/万"))
    for g in ("writings", "expression", "decisions"):
        a = agg[g]
        print("%-12s %9d %7d %7d %9.2f %9.2f %11.2f %11.2f" % (
            g, a[0], a[1], a[2], 10000.0 * a[1] / a[0], 10000.0 * a[2] / a[0],
            10000.0 * a[3] / a[0], 10000.0 * a[4] / a[0]))
    print("->", out)


if __name__ == "__main__":
    main()
