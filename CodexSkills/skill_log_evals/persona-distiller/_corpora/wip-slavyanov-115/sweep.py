#!/usr/bin/env python3
"""Stage 1 funnel: for every candidate archive.org item, run search-inside for
   'Benardos' and 'Slavianoff'. Record hits."""
import json, os, sys, threading, queue, urllib.request, urllib.parse, time

UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
TERMS = ['Benardos', 'Slavianoff', 'Slawianoff']
cands = json.load(open('candidates.json', encoding='utf-8'))
ids = sorted(cands)
out_path = 'sweep_hits.jsonl'
done = set()
if os.path.exists(out_path):
    for ln in open(out_path, encoding='utf-8'):
        try:
            done.add(json.loads(ln)['id'])
        except Exception:
            pass
todo = [i for i in ids if i not in done]
print('todo', len(todo), 'done', len(done), file=sys.stderr)

lock = threading.Lock()
fout = open(out_path, 'a', encoding='utf-8')
q = queue.Queue()
for i in todo:
    q.put(i)

def get(url, timeout=45):
    r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout)
    return json.loads(r.read().decode('utf-8', 'replace'))

def worker():
    while True:
        try:
            ident = q.get_nowait()
        except queue.Empty:
            return
        rec = {'id': ident, 'hits': {}, 'err': None}
        try:
            m = get('https://archive.org/metadata/' + ident)
            srv, d = m.get('server'), m.get('dir')
            if not srv or not d:
                rec['err'] = 'nometa'
            else:
                for t in TERMS:
                    u = (f"https://{srv}/fulltext/inside.php?item_id={ident}&doc={ident}"
                         f"&path={urllib.parse.quote(d)}&q={urllib.parse.quote(t)}")
                    try:
                        r = get(u)
                        n = len(r.get('matches', []))
                        if n:
                            rec['hits'][t] = [x.get('text', '')[:300] for x in r['matches'][:6]]
                    except Exception as e:
                        rec.setdefault('term_err', {})[t] = str(e)[:80]
        except Exception as e:
            rec['err'] = str(e)[:120]
        with lock:
            fout.write(json.dumps(rec, ensure_ascii=False) + '\n')
            fout.flush()

ths = [threading.Thread(target=worker, daemon=True) for _ in range(6)]
[t.start() for t in ths]
[t.join() for t in ths]
print('done', file=sys.stderr)
