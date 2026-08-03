#!/usr/bin/env python3
"""Cut the Slavianoff / Benardos passages out of the Latin-script volume OCR on
   archive.org and write them as corpus files + boundary records."""
import json, os, re, sys

sys.path.insert(0, '/Users/linzezhang/Documents/Codex/AgentDatabase/character-distillation-skill-reorganize-d57595/CodexSkills/skill_log_evals/persona-distiller/_corpora/wip-slavyanov-115')
import ingest

BOUND = {}
NAME = re.compile(r'Slav[ij]?an+o[fw]+|Slaw[ij]?an+o[fw]+|Benardos|Bernardos', re.I)

ITEMS = [
 ('etz-1895-lohmann-slavianoff-giessverfahren', 'bub_gb_F4gxAQAAMAAJ', 113361, 114383,
  'A. Lohmann, «Das Slavianoff\'sche elektrische Giessverfahren», Elektrotechnische Zeitschrift (Berlin), Bd. 16, Heft 22, 30. Mai 1895, S. 325–330.',
  'ETZ Jahrgang 1895 (archive.org item bub_gb_F4gxAQAAMAAJ), Zeilen 113361–114383 von 265556. Seitenzahl 330 ist am Seitenumbruch (Zeile 114360) lesbar; der Bereich S. 325–330 wird durch die NYPL-Bibliographie von 1913 bestätigt, die ebenfalls im Korpus liegt.'),
 ('stahl-eisen-1895-vdmi-lohmann-vortrag', 'bub_gb_o63mAAAAMAAJ', 8480, 8672,
  '«Verein deutscher Maschinen-Ingenieure» — Bericht über den Vortrag von Ingenieur A. Lohmann (Firma Julius Pintsch, Berlin) über das von Nicolai Slavianoff erfundene elektrische Giessverfahren, Stahl und Eisen (Düsseldorf), Jahrgang 1895.',
  'Stahl und Eisen 1895 (archive.org item bub_gb_o63mAAAAMAAJ), Zeilen 8480–8672 von 121427. Der Kolumnentitel Zeile 8436 ist auf «Ai Stahl und Eisen.» verstümmelt — die Seitenzahl war NICHT lesbar und wird deshalb nicht angegeben.'),
 ('stahl-eisen-1895-vdmi-lohmann-vortrag-DUPSCAN', 'bub_gb_gIA3AQAAMAAJ', 8582, 8775,
  'Dasselbe wie oben: Bericht über Lohmanns Vortrag vor dem Verein deutscher Maschinen-Ingenieure, Stahl und Eisen 1895 — zweiter, unabhängiger Scan desselben Jahrgangs.',
  'Stahl und Eisen 1895, zweiter Scan (archive.org item bub_gb_gIA3AQAAMAAJ), Zeilen 8582–8775 von 112906'),
 ('stahl-eisen-1892-patentanmeldung-slawianoff', 'bub_gb_JyvOAAAAMAAJ', 14805, 14840,
  'Patentbericht («Patent-Anmeldungen»), Stahl und Eisen 1892: «30. Juni 1892: … Kl. 31, S 5591. Verfahren und Vorrichtung zum Schmelzen mittels Elektricität. Nicolaus Slawianoff in St. Petersburg.»',
  'Stahl und Eisen 1892 (archive.org item bub_gb_JyvOAAAAMAAJ), Zeilen 14805–14840 von 93016'),
 ('stahl-eisen-1892-patentanmeldung-slawianoff-DUPSCAN', 'bub_gb_SC1OAAAAYAAJ', 14860, 14895,
  'Derselbe Patentbericht, Stahl und Eisen 1892 — zweiter, unabhängiger Scan desselben Jahrgangs.',
  'Stahl und Eisen 1892, zweiter Scan (archive.org item bub_gb_SC1OAAAAYAAJ), Zeilen 14860–14895 von 90427'),
 ('stahl-eisen-1896-perm-kanonenwerk', 'bub_gb_Uq7mAAAAMAAJ', 59690, 59730,
  'Bericht über das Permsche Kanonenwerk, Stahl und Eisen 1896: «Das bekannte Löth- und Schweifsverfahren, welches von dem ehemaligen Inspector der Hütte Slawianoff erfunden worden ist, wird hier in grofsem Mafsstabe zur Anwendung gebracht», mit Angabe der beiden Dynamomaschinen.',
  'Stahl und Eisen 1896 (archive.org item bub_gb_Uq7mAAAAMAAJ), Zeilen 59690–59730 von 105751'),
 ('zvdi-1897-zeitschriftenschau-slavianoff', 'bub_gb_Xgo-AQAAMAAJ', 31763, 31776,
  'Zeitschriftenschau «Metallurgie — Anwendung der elektrischen Erhitzung in der Metallurgie», Zeitschrift des Vereines Deutscher Ingenieure, Jahrgang 1897: verweist auf die «Schmelzvorrichtungen von Slavianoff».',
  'ZVDI 1897 (archive.org item bub_gb_Xgo-AQAAMAAJ), Zeilen 31763–31776 von 307215 — sehr kurzer Eintrag'),
 ('stahl-eisen-1903-anzeige-patent-slavianoff', 'bub_gb_LrTmAAAAMAAJ', 140135, 140165,
  'Geschäftsanzeige, Stahl und Eisen 1903: Reparaturen an Schieberkästen, Pleuelstangen, Schiffsschrauben, Ventilgehäusen «mittels des elektrischen Giefsverfahrens Patent Slavianoff».',
  'Stahl und Eisen 1903 (archive.org item bub_gb_LrTmAAAAMAAJ), Zeilen 140135–140165 von 143735'),
 ('stahl-eisen-1904-schweissverfahren-uebersicht', 'bub_gb_3sfmAAAAMAAJ', 121205, 121245,
  'Übersicht der Schweifsverfahren, Stahl und Eisen 1904: Reihenfolge «Benardos, Slavianoff, Coffin, Bettini, Lagrange-Hoho … Zerener … Thomson».',
  'Stahl und Eisen 1904 (archive.org item bub_gb_3sfmAAAAMAAJ), Zeilen 121205–121245 von 133150'),
 ('stahl-eisen-1908-schweissverfahren-liste', 'bub_gb_PZ7mAAAAMAAJ', 173100, 173140,
  'Vortragsankündigung/-bericht über «die wichtigsten Schweifsverfahren und ihre Ergebnisse», Stahl und Eisen 1908, mit «b) das elektrische Gießverfahren nach Slavianoff» als eigener Punkt neben der Lichtbogenschweifsung.',
  'Stahl und Eisen 1908 (archive.org item bub_gb_PZ7mAAAAMAAJ), Zeilen 173100–173140 von 189123'),
 ('nypl-1913-list-works-electric-welding', 'listworksrelati00deptgoog', 1, 4641,
  'New York Public Library, «List of Works Relating to Electric Welding» (1913) — annotierte Bibliographie; enthält u. a. den Nachweis von A. Lohmanns Aufsatz in Stahl und Eisen v.15, 1. Jan. 1895, S. 42–43 und des ETZ-Aufsatzes v.16, 30. Mai 1895, S. 325–330, sowie Hefters Vergleich der Verfahren Slavianoff/Benardos (Z. Elektrochem. v.6, 1899, S. 286–292).',
  'ganzes Heft, archive.org item listworksrelati00deptgoog, 4641 Zeilen — als bibliographischer Prüfstein aufgenommen'),
 ('applied-electrochem-welding-1917-craver', 'appliedelectroc00cravgoog', 5430, 5520,
  'J. W. Craver (Hrsg.), «Applied Electrochemistry and Welding» (1917): Aufzählung der Lichtbogen-Systeme Thomson, Zerener, Benardos, Slavianoff, LaGrange-Hoho und Beschreibung, worin sich das Slavianoff-System unterscheidet.',
  'archive.org item appliedelectroc00cravgoog, Zeilen 5430–5520 von 16137'),
 ('applied-electrochem-welding-1917-craver-history', 'appliedelectroc00cravgoog', 6720, 6900,
  'Dasselbe Buch, historischer Abschnitt: «The men who have done most to perfect electric-arc-welding processes are De Meritens, Bernardos, Olszewsky, Coffin, Zerener, Slavianoff, Howard …».',
  'archive.org item appliedelectroc00cravgoog, Zeilen 6720–6900 von 16137'),
 ('spot-and-arc-welding-1920-bare-electrode', 'SpotAndArcWelding', 8440, 8490,
  '«Spot and arc welding» (1920), Abschnitt «Covered Versus Bare Electrodes»: «The bare-metal electrode process was introduced about 1895 by a Russian named Slavianoff.»',
  'archive.org item SpotAndArcWelding, Zeilen 8440–8490 von 17463 — die Jahresangabe 1895 in dieser Quelle widerspricht den russischen Quellen (1888/1890) und ist deshalb bewusst mit aufgenommen'),
 ('viall-electric-welding-1921-arc-processes', 'electricwelding00vialrich', 405, 500,
  'Ethan Viall, «Electric Welding» (1921): Aufzählung «the Zerner, the Bernardos, the Slavianoff and the Strohmenger-Slaughter processes» mit Beschreibung des Kohlestab-Verfahrens von de Meritens/Bernardos.',
  'archive.org item electricwelding00vialrich, Zeilen 405–500 von 22709'),
 ('us-shipping-board-1918-slavianoff-system', 'reporttouniteds00corpgoog', 26185, 26320,
  '«Report to the United States Shipping Board, Emergency Fleet Corporation, on electric welding and its application in United States of America to ship construction» (1918): «Of the various radically different systems of electric arc welding, it is believed that the Slavianoff system alone merits serious consideration for general work.»',
  'archive.org item reporttouniteds00corpgoog, Zeilen 26185–26320 von 29537'),
 ('hamilton-electric-welding-1918', 'electricweldingc00hamiuoft', 8500, 8650,
  'A. E. Hamilton u. a., «Electric Welding: a comprehensive treatise on the practice of the various resistance, arc and thermit processes» (1918) — Abschnitt über das Slavianoff-Verfahren.',
  'archive.org item electricweldingc00hamiuoft, Zeilen 8500–8650 von (siehe Datei)'),
 ('wanamaker-electric-arc-welding-1921', 'electricarcweldi00wanarich', 735, 800,
  'H. Wanamaker, «Electric Arc Welding» (1921) — Abschnitt, in dem die Lichtbogenverfahren nach ihren Erfindern benannt werden.',
  'archive.org item electricarcweldi00wanarich, Zeilen 735–800'),
 ('carpenter-electric-welding-1920', 'electricwelding00carpgoog', 905, 960,
  '«Electric Welding and Welding Appliances» (1920) — Abschnitt zu den Lichtbogenverfahren einschliesslich Slavianoff.',
  'archive.org item electricwelding00carpgoog, Zeilen 905–960'),
 ('bennett-electric-welding-1914', 'electricwelding00bennrich', 225, 265,
  '«Electric welding» (c1914) — früheste englischsprachige Buchnennung im Korpus.',
  'archive.org item electricwelding00bennrich, Zeilen 225–265'),
 ('railway-electrical-engineer-slavianoff', 'railwayelectrica05unse', 41055, 41145,
  '«Railway Electrical Engineer», offizielles Organ der Association of Railway Electrical Engineers — Abschnitt zum Slavianoff-Verfahren im Eisenbahnausbesserungswerk.',
  'archive.org item railwayelectrica05unse, Zeilen 41055–41145'),
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
        ingest.log('FAIL %s window %d-%d contains no name hit — NOT written' % (short, a, b))
        continue
    url = 'https://archive.org/details/%s' % ident
    ingest.write(short, seg, source, url, where,
                 'archive.org DjVuTXT OCR of the printed volume, cut to the lines given in `where`')
    BOUND[short] = {
        'archive_item': ident,
        'full_text_url': url,
        'start_line': a, 'end_line': b, 'total_lines': len(lines),
        'start_evidence': lines[a - 1].strip()[:170],
        'end_evidence': lines[b - 1].strip()[:170],
        'name_hits_in_window': len(NAME.findall(seg)),
    }

json.dump(BOUND, open('bound_lat.json', 'w'), ensure_ascii=False, indent=1)
print('boundaries written', len(BOUND))
