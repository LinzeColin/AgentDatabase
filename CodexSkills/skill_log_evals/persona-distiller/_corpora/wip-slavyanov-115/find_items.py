#!/usr/bin/env python3
"""Search archive.org metadata for candidate volumes, dump identifiers."""
import json, sys, urllib.parse, urllib.request, time

UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}

def search(q, rows=100):
    params = [('q', q), ('rows', str(rows)), ('page', '1'), ('output', 'json')]
    for f in ('identifier', 'title', 'year', 'language', 'volume', 'creator'):
        params.append(('fl[]', f))
    url = 'https://archive.org/advancedsearch.php?' + urllib.parse.urlencode(params)
    for attempt in range(3):
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90)
            return json.load(r)['response']
        except Exception as e:
            if attempt == 2:
                print('ERR', q, e, file=sys.stderr)
                return {'numFound': 0, 'docs': []}
            time.sleep(3)

QUERIES = [
 'mediatype:texts AND "electric welding" AND date:[1890-01-01 TO 1935-12-31]',
 'mediatype:texts AND title:(welding) AND date:[1890-01-01 TO 1935-12-31]',
 'mediatype:texts AND subject:(welding)',
 'mediatype:texts AND title:("elektrotechnische zeitschrift")',
 'mediatype:texts AND title:("dingler")',
 'mediatype:texts AND title:("scientific american supplement") AND date:[1890-01-01 TO 1900-12-31]',
 'mediatype:texts AND title:("engineering magazine") AND date:[1891-01-01 TO 1900-12-31]',
 'mediatype:texts AND title:("journal of the franklin institute") AND date:[1890-01-01 TO 1900-12-31]',
 'mediatype:texts AND title:("transactions of the american institute of electrical engineers")',
 'mediatype:texts AND title:("the iron age")',
 'mediatype:texts AND "arc welding" AND date:[1900-01-01 TO 1930-12-31]',
 'mediatype:texts AND ("Slavianoff" OR "Slawianoff" OR "Slavianov")',
 'mediatype:texts AND title:("electrical engineer")',
 'mediatype:texts AND title:("electrician")',
 'mediatype:texts AND title:("stahl und eisen")',
 'mediatype:texts AND title:("zeitschrift des vereines deutscher ingenieure")',
]

seen = {}
for q in QUERIES:
    r = search(q)
    print(f'{q}  -> {r["numFound"]}', file=sys.stderr)
    for d in r['docs']:
        i = d.get('identifier')
        if i and i not in seen:
            seen[i] = d

json.dump(seen, open('candidates.json', 'w'), ensure_ascii=False, indent=0)
print('total candidates', len(seen), file=sys.stderr)
