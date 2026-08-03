#!/usr/bin/env python3
"""Download the real DjVuTXT derivative (name comes from the item metadata) for
   Russian-language archive.org candidates, then grep for Славянов/Бенардос."""
import json, os, re, sys, threading, queue, urllib.request, urllib.parse

UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
OUT = 'rustxt'
os.makedirs(OUT, exist_ok=True)
cands = json.load(open('rus_candidates.json', encoding='utf-8'))
ids = sorted(cands)
done = set()
if os.path.exists('rus_hits2.jsonl'):
    for ln in open('rus_hits2.jsonl', encoding='utf-8'):
        try:
            done.add(json.loads(ln)['id'])
        except Exception:
            pass
q = queue.Queue()
for i in ids:
    if i not in done:
        q.put(i)
lock = threading.Lock()
res = open('rus_hits2.jsonl', 'a', encoding='utf-8')

PATS = [('slav', re.compile(r'Славянов|Славяпов|Славяиов|Славянвв|Слав[яa]нов', re.I)),
        ('slav_loose', re.compile(r'Слав[яеa][нпи][оеа]в', re.I)),
        ('benard', re.compile(r'Бенардос|Бернардос|Венардос', re.I)),
        ('otlivka', re.compile(r'электрическ\w{0,4}\s{0,3}отливк', re.I)),
        ('svarka_dug', re.compile(r'вольтов\w*\s+дуг', re.I))]


def worker():
    while True:
        try:
            ident = q.get_nowait()
        except queue.Empty:
            return
        rec = {'id': ident}
        try:
            m = json.load(urllib.request.urlopen(
                urllib.request.Request('https://archive.org/metadata/' + ident, headers=UA), timeout=90))
            txts = [f['name'] for f in m.get('files', []) if f.get('format') == 'DjVuTXT']
            if not txts:
                rec['err'] = 'no-djvutxt'
            else:
                name = txts[0]
                p = os.path.join(OUT, ident + '.txt')
                if not os.path.exists(p):
                    u = f"https://archive.org/download/{ident}/{urllib.parse.quote(name)}"
                    b = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=240).read()
                    open(p, 'wb').write(b)
                t = open(p, encoding='utf-8', errors='replace').read()
                rec['chars'] = len(t)
                rec['file'] = name
                hits = {}
                for nm, pat in PATS:
                    f = pat.findall(t)
                    if f:
                        hits[nm] = len(f)
                rec['hits'] = hits
        except Exception as e:
            rec['err'] = str(e)[:120]
        with lock:
            res.write(json.dumps(rec, ensure_ascii=False) + '\n')
            res.flush()


ths = [threading.Thread(target=worker, daemon=True) for _ in range(6)]
[t.start() for t in ths]
[t.join() for t in ths]
print('done', file=sys.stderr)
