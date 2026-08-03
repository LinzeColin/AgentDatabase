#!/usr/bin/env python3
"""Second batch of Latin-script extracts (Benardos-side boundary material and
   duplicate scans)."""
import json, os, re, sys

sys.path.insert(0, '/Users/linzezhang/Documents/Codex/AgentDatabase/character-distillation-skill-reorganize-d57595/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-slavyanov-115')
import ingest

BOUND = json.load(open('bound_lat.json', encoding='utf-8'))
NAME = re.compile(r'Slav[ij]?an+o[fw]+|Slaw[ij]?an+o[fw]+|Benardos|Bernardos', re.I)

ITEMS = [
 ('stahl-eisen-1894-muehlhaeuser-benardos-verfahren', 'bub_gb_fC9OAAAAYAAJ', 37530, 37800,
  'F. C. Mühlhäuser (Ingenieur in Remscheid), «Das Benardossche elektrische Schmelzverfahren», Stahl und Eisen (Düsseldorf), Jahrgang 1894.',
  'Stahl und Eisen 1894 (archive.org item bub_gb_fC9OAAAAYAAJ), Zeilen 37530–37800 von 166603. Seitenzahl im Kolumnentitel nicht lesbar, daher nicht angegeben.'),
 ('stahl-eisen-1888-de-patent-43194-benardos', 'bub_gb_bXw3AQAAMAAJ', 71145, 71185,
  'Patentbericht, Stahl und Eisen 1888: «Kl. 48, Nr. 43194, vom 23. September 1887. Nicolas de Benardos in St. Petersburg. Löthen von Gusseisen mittels des elektrischen Lichtbogens.»',
  'Stahl und Eisen 1888 (archive.org item bub_gb_bXw3AQAAMAAJ), Zeilen 71145–71185 von 82504'),
 ('stahl-eisen-1908-schweissverfahren-liste-DUPSCAN', 'bub_gb_RztOAAAAYAAJ', 171180, 171220,
  'Dieselbe Vortragsübersicht der Schweifsverfahren, Stahl und Eisen 1908 — zweiter, unabhängiger Scan desselben Jahrgangs.',
  'Stahl und Eisen 1908, zweiter Scan (archive.org item bub_gb_RztOAAAAYAAJ), Zeilen 171180–171220 von 179294'),
 ('hamilton-oberg-1918-processes-overview', 'electricwelding00obergoog', 400, 640,
  'Douglas T. Hamilton & Erik Oberg, "Electric Welding" (Industrial Press, 1918), opening chapter: "The Slavianoff process is sometimes not considered as a distinct method, but merely as a development of the Bernardos process."',
  'archive.org item electricwelding00obergoog, lines 400-640 of 14732 — a different section of the same book from hamilton-electric-welding-1918'),
 ('hamilton-electric-welding-1918-DUPSCAN', 'electricweldingc00hamirich', 8110, 8260,
  'Douglas T. Hamilton & Erik Oberg, "Electric Welding" (1918) — second, independent scan of the same book.',
  'archive.org item electricweldingc00hamirich, lines 8110-8260 of 12490'),
 ('viall-electric-welding-1921-DUPSCAN', 'gri_33125000707469', 425, 520,
  'Ethan Viall, "Electric Welding" (McGraw-Hill, 1921, First Edition Third Impression) — Franklin Institute Library copy, second independent scan.',
  'archive.org item gri_33125000707469, lines 425-520 of 21837; the title leaf at lines 12-38 carries "First Edition / Third Impression / McGRAW-HILL ... 1921"'),
 ('viall-electric-welding-1921-DUPSCAN2', 'bwb_S0-BGD-555', 510, 600,
  'Ethan Viall, "Electric Welding" (McGraw-Hill, 1921) — third independent scan of the same book.',
  'archive.org item bwb_S0-BGD-555, lines 510-600 of 19143; title leaf at lines 38-50'),
 ('viall-electric-welding-1921-contents', 'electricwelding019468mbp', 110, 140,
  'Ethan Viall, "Electric Welding" (1921) — chapter-contents leaf listing "The Zerner, the Bernardos, the Slavianoff, the Strohmenger-Slaughter and the LaGrange-Hoho Processes".',
  'archive.org item electricwelding019468mbp, lines 110-140 of 30106'),
 ('wanamaker-pennington-1921-DUPSCAN', 'electricarcweld01penngoog', 885, 960,
  'Ernest Wanamaker & Harry R. Pennington, "Electric Arc Welding" (1921) — second independent scan.',
  'archive.org item electricarcweld01penngoog, lines 885-960 of 18996'),
 ('railway-electrical-engineer-v6-1914-slavianoff', 'railwayelectrica06unse', 13160, 13240,
  'Railway Electrical Engineer (Chicago), vol. 6 — passage distinguishing the carbon-arc process from "the Slavianoff process … drawing the arc between the job and a piece of the filling material".',
  'archive.org item railwayelectrica06unse, lines 13160-13240 of 67328. The nearest legible issue line is "August, 1914." at line 13148, so the passage sits in the August 1914 issue.'),
 ('etz-1927-din-schweiss-terminologie', 'elektrotechnisch4816unse', 164875, 164925,
  'Elektrotechnische Zeitschrift Bd. 48 (1927) — Wiedergabe der DIN-Schweißbenennungen; «Slavianoff» erscheint dort als eigene Bezeichnung neben der Lichtbogenschweißung nach Bernardos und Zerener.',
  'ETZ v.48:1-6 (1927) (archive.org item elektrotechnisch4816unse), Zeilen 164875–164925 von 227285 — OCR stark beschädigt (Fraktur)'),
]

for short, ident, a, b, source, where in ITEMS:
    p = 'lattxt/%s.txt' % ident
    if not os.path.exists(p):
        ingest.log('FAIL %s missing %s' % (short, p))
        continue
    lines = open(p, encoding='utf-8', errors='replace').read().split('\n')
    b = min(b, len(lines))
    seg = '\n'.join(lines[a - 1:b])
    if not NAME.search(seg):
        ingest.log('FAIL %s window %d-%d has no name hit — NOT written' % (short, a, b))
        continue
    url = 'https://archive.org/details/%s' % ident
    ingest.write(short, seg, source, url, where,
                 'archive.org DjVuTXT OCR of the printed volume, cut to the lines given in `where`')
    BOUND[short] = {
        'archive_item': ident, 'full_text_url': url,
        'start_line': a, 'end_line': b, 'total_lines': len(lines),
        'start_evidence': lines[a - 1].strip()[:170],
        'end_evidence': lines[b - 1].strip()[:170],
        'name_hits_in_window': len(NAME.findall(seg)),
    }

json.dump(BOUND, open('bound_lat.json', 'w'), ensure_ascii=False, indent=1)
print('boundaries now', len(BOUND))
