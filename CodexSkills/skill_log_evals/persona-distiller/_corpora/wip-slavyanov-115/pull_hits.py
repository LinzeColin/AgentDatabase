#!/usr/bin/env python3
"""For every sweep hit, pull the full DjVuTXT and report where the name lands."""
import json, os, re, sys, threading, queue, urllib.request, urllib.parse

UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
OUT = 'lattxt'
os.makedirs(OUT, exist_ok=True)

hits = []
for ln in open('sweep_hits.jsonl', encoding='utf-8'):
    d = json.loads(ln)
    if d.get('hits'):
        hits.append(d['id'])
hits = sorted(set(hits))
print('hit items', len(hits), file=sys.stderr)

NAME = re.compile(r'Slav[ij]?an+o[fw]+|Slaw[ij]?an+o[fw]+|Slavianov|Slawianow|Slavjanov', re.I)
BEN = re.compile(r'Benardos|Bernardos|Benardo|Olszewski|Olzewski', re.I)

q = queue.Queue()
for i in hits:
    q.put(i)
lock = threading.Lock()
out = open('lat_detail.jsonl', 'a', encoding='utf-8')
seen = set()
if os.path.exists('lat_detail.jsonl'):
    for ln in open('lat_detail.jsonl', encoding='utf-8'):
        try:
            seen.add(json.loads(ln)['id'])
        except Exception:
            pass


def worker():
    while True:
        try:
            ident = q.get_nowait()
        except queue.Empty:
            return
        if ident in seen:
            continue
        rec = {'id': ident}
        try:
            m = json.load(urllib.request.urlopen(
                urllib.request.Request('https://archive.org/metadata/' + ident, headers=UA), timeout=90))
            md = m.get('metadata', {})
            rec['title'] = md.get('title')
            rec['year'] = md.get('year') or md.get('date')
            rec['volume'] = md.get('volume')
            rec['language'] = md.get('language')
            txts = [f['name'] for f in m.get('files', []) if f.get('format') == 'DjVuTXT']
            if not txts:
                rec['err'] = 'no-djvutxt'
            else:
                p = os.path.join(OUT, ident + '.txt')
                if not os.path.exists(p):
                    u = f"https://archive.org/download/{ident}/{urllib.parse.quote(txts[0])}"
                    b = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=300).read()
                    open(p, 'wb').write(b)
                lines = open(p, encoding='utf-8', errors='replace').read().split('\n')
                rec['lines'] = len(lines)
                nm = [i for i, l in enumerate(lines, 1) if NAME.search(l)]
                bn = [i for i, l in enumerate(lines, 1) if BEN.search(l)]
                rec['name_lines'] = nm[:60]
                rec['ben_lines'] = bn[:60]
                rec['name_ctx'] = [{'ln': i, 'txt': ' '.join(lines[max(0, i - 3):i + 3])[:400]} for i in nm[:12]]
        except Exception as e:
            rec['err'] = str(e)[:150]
        with lock:
            out.write(json.dumps(rec, ensure_ascii=False) + '\n')
            out.flush()


ths = [threading.Thread(target=worker, daemon=True) for _ in range(4)]
[t.start() for t in ths]
[t.join() for t in ths]
print('done', file=sys.stderr)
